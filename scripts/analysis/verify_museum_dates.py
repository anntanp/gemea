#!/usr/bin/env python3
"""
Purpose:  Verify that Museum (sparte006) objects lack date fields in the raw DDB EDM JSON,
          confirming the 2.2% date-coverage finding from the parquet analysis.
          Checks each of the five date sources used by prescan.py:
            1. ProvidedCHO.date          → unknown_event
            2. ProvidedCHO.created       → creation
            3. ProvidedCHO.issued        → publication
            4. LIDO events → TimeSpan    → creation  (LIDO_CREATED URIs)
            5. LIDO events → TimeSpan    → publication (LIDO_ISSUED URIs)
Usage:    python scripts/analysis/verify_museum_dates.py --json PATH
Inputs:   <items-all>.json  — list of DDB EDM cortex records (or any JSON array of records)
Outputs:  data/processed/museum_date_field_coverage.csv
Dependencies: stdlib only
Assumptions: Run from the gemea/ project root. JSON is a top-level array of record dicts.
"""

import argparse
import csv
import json
from pathlib import Path

LIDO_CREATED: frozenset[str] = frozenset({
    "http://terminology.lido-schema.org/lido00012",
    "http://terminology.lido-schema.org/eventType/creation",
    "http://terminology.lido-schema.org/lido00007",
})
LIDO_ISSUED: frozenset[str] = frozenset({
    "http://terminology.lido-schema.org/lido00228",
    "http://terminology.lido-schema.org/eventType/publication",
})

MUSEUM_SPARTE = "sparte006"


def coerce_list(val) -> list:
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def has_field(cho: dict, key: str) -> bool:
    val = cho.get(key)
    if val is None:
        return False
    if isinstance(val, str):
        return bool(val.strip())
    if isinstance(val, dict):
        return bool(val.get("$", "").strip() or val.get("resource", "").strip())
    if isinstance(val, list):
        return any(has_field({"_": v}, "_") if not isinstance(v, str) else bool(v.strip())
                   for v in val)
    return False


def has_lido_dates(rdf: dict, lido_uris: frozenset[str]) -> bool:
    events = coerce_list(rdf.get("Event"))
    ts_map = {
        t["about"]: t for t in coerce_list(rdf.get("TimeSpan"))
        if isinstance(t, dict) and t.get("about")
    }
    cho = rdf.get("ProvidedCHO") or {}
    if isinstance(cho, list):
        cho = cho[0] if cho else {}

    event_map = {
        e["about"]: e for e in events
        if isinstance(e, dict) and e.get("about")
    }
    for hm in coerce_list(cho.get("hasMet")):
        if not isinstance(hm, dict):
            continue
        ev_ref = hm.get("resource")
        if not ev_ref:
            continue
        ev = event_map.get(ev_ref, {})
        ht = ev.get("hasType") or {}
        ht_uri = ht.get("resource") if isinstance(ht, dict) else None
        if ht_uri not in lido_uris:
            continue
        oc = ev.get("occuredAt") or ev.get("occurredAt")
        if not oc:
            continue
        ts_ref = oc.get("resource") if isinstance(oc, dict) else oc
        if isinstance(ts_ref, str) and ts_ref in ts_map:
            ts = ts_map[ts_ref]
            if ts.get("begin") or ts.get("end") or ts.get("prefLabel"):
                return True
    return False


def is_museum(record: dict) -> bool:
    rdf = (record.get("edm") or {}).get("RDF") or {}
    for c in coerce_list(rdf.get("Concept")):
        if isinstance(c, dict) and MUSEUM_SPARTE in (c.get("about") or ""):
            return True
    return False


def check_record(record: dict) -> dict[str, bool]:
    rdf = (record.get("edm") or {}).get("RDF") or {}
    cho = rdf.get("ProvidedCHO") or {}
    if isinstance(cho, list):
        cho = cho[0] if cho else {}

    return {
        "has_dc_date":       has_field(cho, "date"),
        "has_dc_created":    has_field(cho, "created"),
        "has_dc_issued":     has_field(cho, "issued"),
        "has_lido_creation": has_lido_dates(rdf, LIDO_CREATED),
        "has_lido_issued":   has_lido_dates(rdf, LIDO_ISSUED),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, type=Path,
                        help="Path to DDB EDM cortex JSON file (array of records)")
    parser.add_argument("--all-sectors", action="store_true",
                        help="Report for all sectors, not just Museum")
    args = parser.parse_args()

    out_path = Path("data/processed/museum_date_field_coverage.csv")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading {args.json} …")
    records = []
    with open(args.json, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    print(f"  {len(records):,} records total")

    museum = [r for r in records if is_museum(r)]
    target = museum if not args.all_sectors else records
    label  = "Museum (sparte006)" if not args.all_sectors else "all sectors"
    print(f"  {len(museum):,} Museum records" + (f" — using all {len(target):,}" if args.all_sectors else ""))

    if not target:
        print("No Museum records found — check that the JSON contains sparte006 objects.")
        return

    fields = ["has_dc_date", "has_dc_created", "has_dc_issued", "has_lido_creation", "has_lido_issued"]
    counts = {f: 0 for f in fields}
    has_any = 0

    for rec in target:
        result = check_record(rec)
        if any(result.values()):
            has_any += 1
        for f in fields:
            if result[f]:
                counts[f] += 1

    n = len(target)
    rows = []
    source_labels = {
        "has_dc_date":       "ProvidedCHO.date (→ unknown_event)",
        "has_dc_created":    "ProvidedCHO.created (→ creation)",
        "has_dc_issued":     "ProvidedCHO.issued (→ publication)",
        "has_lido_creation": "LIDO event → TimeSpan (creation URIs)",
        "has_lido_issued":   "LIDO event → TimeSpan (publication URIs)",
    }
    for f in fields:
        rows.append({
            "sector_filter": label,
            "date_source": source_labels[f],
            "field_key": f,
            "n_records": n,
            "n_with_field": counts[f],
            "pct": f"{counts[f] / n * 100:.2f}%",
        })
    rows.append({
        "sector_filter": label,
        "date_source": "ANY date field",
        "field_key": "has_any",
        "n_records": n,
        "n_with_field": has_any,
        "pct": f"{has_any / n * 100:.2f}%",
    })

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["sector_filter","date_source","field_key","n_records","n_with_field","pct"])
        w.writeheader()
        w.writerows(rows)

    print(f"\nResults for {label} ({n:,} records):")
    for r in rows:
        print(f"  {r['date_source']:50s}  {r['n_with_field']:>6,} / {n:,}  ({r['pct']})")
    print(f"\nCSV saved → {out_path}")


if __name__ == "__main__":
    main()

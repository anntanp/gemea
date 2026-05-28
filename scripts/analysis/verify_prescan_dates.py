#!/usr/bin/env python3
"""
Purpose:  Confirm the prescan.py date extraction algorithm is correct for Museum objects.
          Runs the exact extraction chain (scalar_str → parse_dc_date → normalize_date)
          on Museum records from the goethe-faust JSON, then reports per-source yield.
          Also prints raw field values from the first N Museum objects to verify key names.
Usage:    python scripts/analysis/verify_prescan_dates.py --json PATH [--sample N]
Inputs:   <items>.json or <items>.jsonl — DDB EDM cortex records
Outputs:  data/processed/prescan_date_yield_museum.csv
Dependencies: stdlib only
Assumptions: Run from the gemea/ project root.
"""

import argparse
import csv
import json
import re
from pathlib import Path

# ── replicate prescan extraction logic exactly ────────────────────────────────

_QUALIFIER_RE = re.compile(r'\([^)]*\)')

LIDO_CREATED: frozenset[str] = frozenset({
    "http://terminology.lido-schema.org/lido00012",
    "http://terminology.lido-schema.org/eventType/creation",
    "http://terminology.lido-schema.org/lido00007",
})
LIDO_ISSUED: frozenset[str] = frozenset({
    "http://terminology.lido-schema.org/lido00228",
    "http://terminology.lido-schema.org/eventType/publication",
})


def coerce_list(val) -> list:
    if val is None:
        return []
    return val if isinstance(val, list) else [val]


def _scalar_str(val):
    if val is None:
        return None
    if isinstance(val, str):
        return val or None
    if isinstance(val, dict):
        return val.get("$") or None
    if isinstance(val, list):
        for item in val:
            result = _scalar_str(item)
            if result:
                return result
    return None


def _scalar_values(val) -> list[str]:
    if val is None:
        return []
    if isinstance(val, str):
        return [val] if val else []
    if isinstance(val, dict):
        v = val.get("$") or ""
        return [v] if v else []
    if isinstance(val, list):
        out: list[str] = []
        for item in val:
            out.extend(_scalar_values(item))
        return out
    return []


def normalize_date(s: str) -> list[str]:
    s = s.strip()
    if "/" in s:
        parts = s.split("/", 1)
        return [normalize_date(p)[0] for p in parts]
    if len(s) == 8 and s.isdigit():
        return [f"{s[:4]}-{s[4:6]}-{s[6:]}"]
    return [s]


def _parse_dc_date(raw: str):
    if not raw:
        return None
    clean = _QUALIFIER_RE.sub("", raw).strip().strip("[]").strip()
    if not clean:
        return None
    vals = normalize_date(clean)
    return vals[0] if vals else None


def _lido_dates_present(rdf: dict, cho: dict, lido_uris: frozenset[str]) -> bool:
    events = coerce_list(rdf.get("Event"))
    ts_map = {
        t["about"]: t for t in coerce_list(rdf.get("TimeSpan"))
        if isinstance(t, dict) and t.get("about")
    }
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
        if isinstance(c, dict) and "sparte006" in (c.get("about") or ""):
            return True
    return False


def extract_dates(record: dict) -> dict:
    """Run prescan's exact date extraction and return per-source results."""
    rdf = (record.get("edm") or {}).get("RDF") or {}
    cho = rdf.get("ProvidedCHO") or {}
    if isinstance(cho, list):
        cho = cho[0] if cho else {}

    results = {
        "raw_date_field":    cho.get("date"),        # raw value for inspection
        "raw_created_field": cho.get("created"),
        "raw_issued_field":  cho.get("issued"),
    }

    # source 1: ProvidedCHO.date → unknown_event
    dc_date_raw = _scalar_str(cho.get("date"))
    normed = _parse_dc_date(dc_date_raw) if dc_date_raw else None
    results["dc_date_present"]   = dc_date_raw is not None
    results["dc_date_extracted"] = normed is not None
    results["dc_date_value"]     = normed

    # source 2: ProvidedCHO.created → creation
    created_vals = _scalar_values(cho.get("created"))
    results["dc_created_extracted"] = len(created_vals) > 0
    results["dc_created_values"]    = created_vals

    # source 3: ProvidedCHO.issued → publication
    issued_vals = _scalar_values(cho.get("issued"))
    results["dc_issued_extracted"] = len(issued_vals) > 0
    results["dc_issued_values"]    = issued_vals

    # sources 4+5: LIDO events via TimeSpan
    results["lido_creation_extracted"]  = _lido_dates_present(rdf, cho, LIDO_CREATED)
    results["lido_published_extracted"] = _lido_dates_present(rdf, cho, LIDO_ISSUED)

    results["has_any"] = any([
        results["dc_date_extracted"],
        results["dc_created_extracted"],
        results["dc_issued_extracted"],
        results["lido_creation_extracted"],
        results["lido_published_extracted"],
    ])
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True, type=Path)
    parser.add_argument("--sample", type=int, default=5,
                        help="Number of Museum objects to print raw field values for (default: 5)")
    args = parser.parse_args()

    print(f"Loading {args.json} …")
    records = []
    with open(args.json, encoding="utf-8") as f:
        first = f.read(1)
        f.seek(0)
        if first == "[":
            records = json.load(f)
        else:
            for line in f:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    print(f"  {len(records):,} records total")

    museum = [r for r in records if is_museum(r)]
    print(f"  {len(museum):,} Museum (sparte006) records")

    if not museum:
        print("No Museum records found.")
        return

    # ── raw field inspection ──────────────────────────────────────────────────
    print(f"\nRaw date field values for first {args.sample} Museum objects:")
    for i, rec in enumerate(museum[:args.sample]):
        rdf = (rec.get("edm") or {}).get("RDF") or {}
        cho = rdf.get("ProvidedCHO") or {}
        if isinstance(cho, list):
            cho = cho[0] if cho else {}
        obj_id = (rec.get("properties") or {}).get("item-id", "?")
        print(f"  [{i+1}] {obj_id}")
        print(f"       cho.date    = {repr(cho.get('date'))}")
        print(f"       cho.created = {repr(cho.get('created'))}")
        print(f"       cho.issued  = {repr(cho.get('issued'))}")

    # ── aggregate extraction yield ────────────────────────────────────────────
    counts = {
        "dc_date_present":          0,
        "dc_date_extracted":        0,
        "dc_date_stripped_to_empty": 0,   # present but normalized away
        "dc_created_extracted":     0,
        "dc_issued_extracted":      0,
        "lido_creation_extracted":  0,
        "lido_published_extracted": 0,
        "has_any":                  0,
    }
    for rec in museum:
        r = extract_dates(rec)
        for k in counts:
            if k == "dc_date_stripped_to_empty":
                if r["dc_date_present"] and not r["dc_date_extracted"]:
                    counts[k] += 1
            elif r.get(k):
                counts[k] += 1

    n = len(museum)
    print(f"\nExtraction yield for {n:,} Museum records:")
    rows = []
    labels = {
        "dc_date_present":           "ProvidedCHO.date present (non-empty)",
        "dc_date_extracted":         "ProvidedCHO.date → date extracted (→ unknown_event)",
        "dc_date_stripped_to_empty": "  └─ present but stripped to empty by _parse_dc_date",
        "dc_created_extracted":      "ProvidedCHO.created → date extracted (→ creation)",
        "dc_issued_extracted":       "ProvidedCHO.issued → date extracted (→ publication)",
        "lido_creation_extracted":   "LIDO event → TimeSpan → creation",
        "lido_published_extracted":  "LIDO event → TimeSpan → publication",
        "has_any":                   "ANY date extracted",
    }
    for k, label in labels.items():
        c = counts[k]
        pct = f"{c / n * 100:.2f}%"
        print(f"  {label:55s}  {c:>6,} / {n:,}  ({pct})")
        rows.append({"metric": label, "key": k, "n_museum": n, "count": c, "pct": pct})

    out = Path("data/processed/prescan_date_yield_museum.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["metric", "key", "n_museum", "count", "pct"])
        w.writeheader()
        w.writerows(rows)
    print(f"\nCSV saved → {out}")


if __name__ == "__main__":
    main()

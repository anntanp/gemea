#!/usr/bin/env python3
# Purpose:      Inspect ProvidedCHO fields in a cortex JSON source (s2.sqlite or
#               a JSON array file like items-excerpt-1000.json) to verify Parquet
#               column mappings (§5 of export-s2-plan.md)
# Usage:        python3 sample_s2_fields.py sqlite <path/to/s2.sqlite>
#               python3 sample_s2_fields.py json   <path/to/items.json>
#               python3 sample_s2_fields.py sqlite <path/to/s2.sqlite> --field <name>
#               python3 sample_s2_fields.py json   <path/to/items.json> --field <name>
# Inputs:       SQLite file (objs table, bufgz column) or JSON array file
# Outputs:      stdout
#               default: ProvidedCHO, Aggregation, Event[0], TimeSpan, view.item.fields
#                        for the first record
#               --field <name>: scan all records, report which contain that
#                        ProvidedCHO field and show sample values
# Dependencies: standard library only
# Assumptions:  SQLite: at least one row with non-null bufgz; JSON: top-level array

import argparse
import gzip
import json
import sqlite3
import sys
from pathlib import Path


def show(label, value):
    print(f"\n=== {label} ===")
    print(json.dumps(value, indent=2, ensure_ascii=False))


def iter_records(source_type, path):
    """Yield (uid, data_dict) from sqlite or json source."""
    if source_type == "sqlite":
        db = sqlite3.connect(path)
        for uid, _ts, blob in db.execute(
            "SELECT * FROM objs WHERE bufgz IS NOT NULL"
        ):
            yield uid, json.loads(gzip.decompress(blob))
    else:
        for item in json.load(open(path, encoding="utf-8")):
            yield item["properties"]["item-id"], item


def cmd_sample(source_type, path):
    """Print key sections of the first record."""
    for uid, data in iter_records(source_type, path):
        rdf = data["edm"]["RDF"]
        print(f"uid: {uid}")
        show("ProvidedCHO", rdf.get("ProvidedCHO", {}))
        show("Aggregation", rdf.get("Aggregation", {}))
        events = rdf.get("Event") or []
        show("Event[0]", events[0] if events else {})
        show("TimeSpan", rdf.get("TimeSpan", {}))
        show("view.item.fields",
             data.get("view", {}).get("item", {}).get("fields", []))
        break


def cmd_timespan(source_type, path):
    """Scan all records for Event.occuredAt → TimeSpan chains and print samples."""
    hits = []
    total = 0
    for uid, data in iter_records(source_type, path):
        total += 1
        rdf = data.get("edm", {}).get("RDF", {}) or {}
        events = rdf.get("Event") or []
        if isinstance(events, dict):
            events = [events]
        # build TimeSpan lookup by about
        ts_list = rdf.get("TimeSpan") or []
        if isinstance(ts_list, dict):
            ts_list = [ts_list]
        ts_map = {t["about"]: t for t in ts_list if isinstance(t, dict) and t.get("about")}
        for ev in events:
            oc = ev.get("occuredAt")
            if not oc:
                continue
            if isinstance(oc, dict):
                ts_ref = oc.get("resource") or oc.get("$")
            elif isinstance(oc, list):
                ts_ref = oc[0] if oc else None
            else:
                ts_ref = oc
            if not ts_ref or not isinstance(ts_ref, str):
                continue
            ts = ts_map.get(ts_ref, {})
            hits.append({
                "uid": uid,
                "hasType": (ev.get("hasType") or {}).get("resource"),
                "occuredAt": oc,
                "TimeSpan": ts,
            })

    print(f"Event.occuredAt present in {len(hits)} events across {total} records\n")
    for h in hits[:10]:
        print(f"uid: {h['uid']}")
        print(f"  hasType:   {h['hasType']}")
        print(f"  occuredAt: {h['occuredAt']}")
        print(f"  TimeSpan:  {json.dumps(h['TimeSpan'], ensure_ascii=False)}")
        print()


def cmd_field(source_type, path, field):
    """Scan all records and report which have ProvidedCHO.<field>."""
    hits = []
    total = 0
    for uid, data in iter_records(source_type, path):
        total += 1
        cho = data.get("edm", {}).get("RDF", {}).get("ProvidedCHO", {}) or {}
        if field in cho and cho[field] is not None:
            hits.append((uid, cho[field]))

    print(f"Field '{field}' present in {len(hits)}/{total} records\n")
    for uid, val in hits[:10]:
        print(f"  {uid}  {str(val)[:120]}")
    if len(hits) > 10:
        print(f"  ... ({len(hits) - 10} more)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_type", choices=["sqlite", "json"])
    parser.add_argument("path")
    parser.add_argument("--field", help="ProvidedCHO field to scan across all records")
    parser.add_argument("--timespan", action="store_true",
                        help="Scan all records for Event.occuredAt → TimeSpan chains")
    args = parser.parse_args()

    if not Path(args.path).exists():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    if args.field:
        cmd_field(args.source_type, args.path, args.field)
    elif args.timespan:
        cmd_timespan(args.source_type, args.path)
    else:
        cmd_sample(args.source_type, args.path)


if __name__ == "__main__":
    main()

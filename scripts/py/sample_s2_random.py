#!/usr/bin/env python3
# Purpose:      Draw a random sample of N records from s2.sqlite using IDs from
#               a text file, and save the decompressed JSON blobs to a JSON array file
# Usage:        python3 sample_s2_random.py <ids.txt> <s2.sqlite> <output.json> [--n 1000]
# Inputs:       ids.txt    — one DDB object ID per line
#               s2.sqlite  — table objs, column bufgz (gzip-compressed JSON)
# Outputs:      output.json — JSON array of N decompressed record blobs
# Dependencies: standard library only
# Assumptions:  IDs in ids.txt are a superset of IDs in s2.sqlite

import argparse
import gzip
import json
import random
import sqlite3
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ids_file")
    parser.add_argument("sqlite_file")
    parser.add_argument("output_file")
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    for p in (args.ids_file, args.sqlite_file):
        if not Path(p).exists():
            print(f"ERROR: not found: {p}", file=sys.stderr)
            sys.exit(1)

    print(f"Reading IDs from {args.ids_file} ...", flush=True)
    with open(args.ids_file) as f:
        all_ids = [line.strip() for line in f if line.strip()]
    print(f"  {len(all_ids):,} IDs total")

    random.seed(args.seed)
    sample_ids = set(random.sample(all_ids, min(args.n * 3, len(all_ids))))
    print(f"  Sampling {len(sample_ids):,} candidate IDs (3× to account for missing rows)")

    db = sqlite3.connect(args.sqlite_file)
    records = []
    placeholders = ",".join("?" * len(sample_ids))
    for uid, _ts, blob in db.execute(
        f"SELECT * FROM objs WHERE uid IN ({placeholders}) AND bufgz IS NOT NULL",
        list(sample_ids),
    ):
        records.append(json.loads(gzip.decompress(blob)))
        if len(records) >= args.n:
            break

    print(f"  Retrieved {len(records):,} records from SQLite")

    with open(args.output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=None)

    print(f"Written → {args.output_file}")


if __name__ == "__main__":
    main()

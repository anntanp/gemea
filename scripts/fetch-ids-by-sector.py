#!/usr/bin/env python3
"""
fetch-ids-by-sector.py
======================
Fetch DDB object IDs from the Solr API filtered by sector and digitalisat flag.
Uses cursor-based pagination (cursorMark) to bypass Solr's maxResultWindow limit,
which blocks offset-based pagination (start=N) beyond ~10,000 results.
Writes one ID per line. Supports resuming an interrupted run via a state file.

Input
-----
  DDB Solr API (live, requires network access):
    https://api.deutsche-digitale-bibliothek.de/search/index/search/select

Output
------
  data/ids_<sector>_<digitalisat|no_digitalisat>.txt
  data/ids_<sector>_<digitalisat|no_digitalisat>.cursor  (resume state, deleted on completion)

Usage
-----
    python scripts/fetch-ids-by-sector.py --sector sec_02 --digitalisat true
    python scripts/fetch-ids-by-sector.py --sector sec_02 --digitalisat false
    python scripts/fetch-ids-by-sector.py --sector sec_02 --digitalisat true --batch-size 100

Arguments
---------
  --sector        One of sec_01 .. sec_07 (required)
  --digitalisat   true or false (required)
  --batch-size    IDs per request (default: 10000)

Dependencies
------------
  Python 3.8+ stdlib only (urllib, argparse, pathlib, time)

Assumptions
-----------
  The Solr API is reachable and returns JSON.
  The `id` field is unique and sortable (required for cursorMark).
  Resume works by reading the saved cursorMark from the state file.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.deutsche-digitale-bibliothek.de/search/index/search/select"
DELAY = 0.5  # seconds between requests


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch DDB IDs by sector and digitalisat flag.")
    parser.add_argument("--sector", required=True,
                        choices=[f"sec_0{i}" for i in range(1, 8)],
                        help="Sector filter (sec_01 .. sec_07)")
    parser.add_argument("--digitalisat", required=True, choices=["true", "false"],
                        help="Digitalisat filter")
    parser.add_argument("--batch-size", type=int, default=10_000,
                        help="IDs per request (default: 10000)")
    return parser.parse_args()


def build_url(sector: str, digitalisat: str, cursor: str, rows: int) -> str:
    # cursorMark requires a sort on a unique field; id is unique in DDB Solr.
    parts = [
        ("q", "*:*"),
        ("fl", "id"),
        ("rows", rows),
        ("fq", f"sector_fct:{sector}"),
        ("fq", f"digitalisat:{digitalisat}"),
        ("sort", "id asc"),
        ("cursorMark", cursor),
        ("wt", "json"),
    ]
    return f"{API}?{urllib.parse.urlencode(parts)}"


def fetch(url: str, retries: int = 5) -> dict:
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504):
                wait = 2 ** attempt
                print(f"  HTTP {e.code} — retrying in {wait}s...", file=sys.stderr)
                if attempt == retries:
                    raise
                time.sleep(wait)
            else:
                raise
        except (urllib.error.URLError, OSError) as e:
            wait = 2 ** attempt
            print(f"  Attempt {attempt}/{retries} failed: {e}. Retrying in {wait}s...", file=sys.stderr)
            if attempt == retries:
                raise
            time.sleep(wait)


def main():
    args = parse_args()
    project = Path(__file__).resolve().parent.parent
    data_dir = project / "data"
    data_dir.mkdir(exist_ok=True)

    suffix = "digitalisat" if args.digitalisat == "true" else "no_digitalisat"
    output = data_dir / f"ids_{args.sector}_{suffix}.txt"
    state_file = data_dir / f"ids_{args.sector}_{suffix}.cursor"

    # Resume: read saved cursor and count already-fetched IDs
    cursor = "*"
    fetched = 0
    if state_file.exists() and output.exists():
        cursor = state_file.read_text().strip()
        fetched = sum(1 for line in output.read_text().splitlines() if line.strip())
        print(f"Resuming from cursor (already fetched: {fetched} IDs).")
    elif output.exists():
        # Output exists but no cursor — restart cleanly
        output.unlink()

    # First batch (also discovers total)
    url = build_url(args.sector, args.digitalisat, cursor, args.batch_size)
    print(f"Fetching batch (cursor={'*' if cursor == '*' else cursor[:20] + '...'}, rows={args.batch_size}) ...")
    print(f"  {url}")
    data = fetch(url)
    total = data["response"]["numFound"]
    print(f"Total matching: {total}")

    ids = [doc["id"] for doc in data["response"]["docs"]]
    next_cursor = data.get("nextCursorMark", cursor)

    mode = "a" if fetched else "w"
    with open(output, mode, encoding="utf-8") as f:
        f.write("\n".join(ids))
        if ids:
            f.write("\n")

    fetched += len(ids)
    state_file.write_text(next_cursor)
    print(f"  Saved {len(ids)} IDs (total so far: {fetched}/{total})")

    # Remaining batches
    while next_cursor != cursor and fetched < total:
        cursor = next_cursor
        time.sleep(DELAY)
        url = build_url(args.sector, args.digitalisat, cursor, args.batch_size)
        print(f"Fetching batch (fetched so far: {fetched}/{total}) ...")
        data = fetch(url)
        ids = [doc["id"] for doc in data["response"]["docs"]]
        next_cursor = data.get("nextCursorMark", cursor)

        if not ids:
            print("Empty batch — stopping.")
            break

        with open(output, "a", encoding="utf-8") as f:
            f.write("\n".join(ids) + "\n")

        fetched += len(ids)
        state_file.write_text(next_cursor)
        print(f"  Saved {len(ids)} IDs (total so far: {fetched}/{total})")

    state_file.unlink(missing_ok=True)
    print(f"\nDone. {fetched} IDs written to {output}")


if __name__ == "__main__":
    main()

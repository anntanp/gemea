#!/usr/bin/env python3
# Purpose: Export UIDs from the errors table of a download SQLite DB, grouped by status code.
# Usage:   python export_error_uids.py <path/to/s1.sqlite>
# Inputs:  SQLite file with table: errors(uid TEXT, timestamp TEXT, status_code INTEGER)
# Outputs: ids-s1-<status_code>.txt per distinct status code, in the same directory as the DB
# Dependencies: stdlib only
# Assumptions: errors.uid is non-null; duplicate UIDs are preserved as-is

import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


def main(db_path: Path) -> None:
    with sqlite3.connect(db_path) as con:
        rows = con.execute("SELECT uid, status_code FROM errors").fetchall()

    by_code: dict[int, list[str]] = defaultdict(list)
    for uid, code in rows:
        by_code[code].append(uid)

    for code, uids in sorted(by_code.items()):
        out_path = db_path.parent / f"ids-s1-{code}.txt"
        with open(out_path, "w", encoding="utf-8") as f:
            for uid in uids:
                f.write(f"{uid}\n")

    total = sum(len(v) for v in by_code.values())
    print(f"\nSummary — {db_path.name}")
    print(f"  Total errors : {total}")
    print(f"  Status codes : {len(by_code)}")
    for code, uids in sorted(by_code.items()):
        pct = len(uids) / total * 100
        print(f"    {code}  {len(uids):>6}  ({pct:.1f}%)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path/to/s1.sqlite>", file=sys.stderr)
        sys.exit(1)
    db = Path(sys.argv[1])
    if not db.is_file():
        print(f"Error: {db} is not a file", file=sys.stderr)
        sys.exit(1)
    main(db)

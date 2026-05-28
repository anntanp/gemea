#!/usr/bin/env python3
# Purpose:   Delete rows from objs table whose uid is NOT in a given ID list.
# Usage:     python3 prune_sqlite_by_ids.py <db.sqlite> <ids.txt>
# Inputs:    <db.sqlite>  — SQLite file with table objs, column uid
#            <ids.txt>    — one uid per line; rows not in this list are deleted
# Outputs:   Modifies db.sqlite in-place; prints count of deleted rows.
# Dependencies: stdlib only
# Assumptions: IDs file is UTF-8, one ID per line, may have blank lines.

import sqlite3
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <db.sqlite> <ids.txt>", file=sys.stderr)
        sys.exit(1)

    db_path = Path(sys.argv[1])
    ids_path = Path(sys.argv[2])

    if not db_path.exists():
        print(f"Error: {db_path} not found", file=sys.stderr)
        sys.exit(1)
    if not ids_path.exists():
        print(f"Error: {ids_path} not found", file=sys.stderr)
        sys.exit(1)

    keep_ids = {line.strip() for line in ids_path.read_text(encoding="utf-8").splitlines() if line.strip()}
    print(f"Loaded {len(keep_ids):,} IDs to keep.")

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    cur.execute("SELECT COUNT(*) FROM objs")
    total_before = cur.fetchone()[0]
    print(f"Rows before: {total_before:,}")

    # Load all IDs into a temp table to avoid huge IN(...) literals.
    cur.execute("CREATE TEMPORARY TABLE keep_ids (uid TEXT PRIMARY KEY)")
    cur.executemany("INSERT OR IGNORE INTO keep_ids VALUES (?)", ((uid,) for uid in keep_ids))
    con.commit()

    cur.execute("DELETE FROM objs WHERE uid NOT IN (SELECT uid FROM keep_ids)")
    deleted = cur.rowcount
    con.commit()

    cur.execute("SELECT COUNT(*) FROM objs")
    total_after = cur.fetchone()[0]

    con.execute("VACUUM")
    con.close()

    print(f"Deleted:     {deleted:,}")
    print(f"Rows after:  {total_after:,}")


if __name__ == "__main__":
    main()

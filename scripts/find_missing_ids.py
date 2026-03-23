#!/usr/bin/env python3
"""
Find object IDs present in a text file but missing from an SQLite3 source table.

Usage:   python find_missing_ids.py <sqlite_file> <ids_file> <output_file>
Inputs:  sqlite_file  — path to SQLite3 database with a `source` table (read-only ok)
         ids_file     — text file with one object ID per line
         output_file  — path for the resulting list of missing IDs
Output:  text file with one missing ID per line
Dependencies: stdlib only (sqlite3, shutil, tempfile)
"""

import sqlite3
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 4:
        print("Usage: python find_missing_ids.py <sqlite_file> <ids_file> <output_file>")
        sys.exit(1)

    sqlite_path, ids_path, output_path = sys.argv[1], sys.argv[2], sys.argv[3]

    ids = {line.strip() for line in Path(ids_path).read_text().splitlines() if line.strip()}
    print(f"IDs in {ids_path}: {len(ids)}")

    with sqlite3.connect(sqlite_path) as con:
        existing = {row[0] for row in con.execute("SELECT id FROM source")}
    print(f"IDs in source table: {len(existing)}")

    missing = sorted(ids - existing)
    print(f"Missing (to download): {len(missing)}")

    Path(output_path).write_text("\n".join(missing) + "\n")
    print(f"Written to {output_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env bash
# Purpose:      Report row counts and bufgz coverage for one or more s*.sqlite files
# Usage:        bash scripts/sh/check_sqlite_coverage.sh [s1.sqlite s2.sqlite ...]
#               If no arguments given, checks all data/sqlite/s*.sqlite files
# Inputs:       data/sqlite/s*.sqlite
# Outputs:      stdout — total rows, non-null bufgz, null bufgz, coverage %
# Dependencies: Python venv with standard library only
# Assumptions:  Run from project root; .venv exists

set -euo pipefail
cd "$(dirname "$0")/../.."

source .venv/bin/activate

if [[ $# -gt 0 ]]; then
    FILES=("$@")
else
    FILES=(data/sqlite/s*.sqlite)
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "ERROR: no sqlite files found" >&2
    exit 1
fi

python3 - "${FILES[@]}" <<'EOF'
import sqlite3, sys
from pathlib import Path

files = sys.argv[1:]
print(f"{'File':<30} {'Total':>12} {'With bufgz':>12} {'NULL bufgz':>12} {'Coverage':>10}")
print("-" * 80)
for f in files:
    db = sqlite3.connect(f)
    total    = db.execute("SELECT count(*) FROM objs").fetchone()[0]
    non_null = db.execute("SELECT count(*) FROM objs WHERE bufgz IS NOT NULL").fetchone()[0]
    null     = total - non_null
    pct      = 100 * non_null / total if total else 0
    print(f"{Path(f).name:<30} {total:>12,} {non_null:>12,} {null:>12,} {pct:>9.1f}%")
    db.close()
EOF

#!/usr/bin/env bash
# Purpose:      Smoke-test export_s2.py against the 1000-record JSON sample
# Usage:        bash scripts/sh/smoke_test_export_s2.sh
# Inputs:       data/processed/s2_sample_1000.json
#               scripts/py/export_s2.py
# Outputs:      stdout — errors, NT byte count, meta fields, first NT lines
# Dependencies: Python venv with pyoxigraph, pyarrow
# Assumptions:  Run from project root; .venv exists

set -euo pipefail
cd "$(dirname "$0")/../.."

source .venv/bin/activate

python3 - <<'EOF'
import json, sys, traceback
sys.path.insert(0, "scripts/py")
from export_s2 import record_to_triples, extract_meta

data = json.load(open("data/processed/s2_sample_1000.json"))

# check first 50 records for errors
errors = 0
for i, record in enumerate(data[:50]):
    try:
        record_to_triples(record)
        extract_meta(record)
    except Exception as e:
        print(f"Record {i} ERROR: {e}")
        traceback.print_exc()
        errors += 1

print(f"Errors in first 50 records: {errors}")
print()

# detailed output for first record
sample = data[0]
nt    = record_to_triples(sample)
meta  = extract_meta(sample)

print(f"NT bytes for record 0: {len(nt):,}")
print()
print("Meta:")
print(json.dumps(meta, indent=2, ensure_ascii=False))
print()
print("First 15 NT lines:")
for line in nt.decode("utf-8").split("\n")[:15]:
    print(line)
EOF

#!/usr/bin/env python3
"""
Purpose:  Inspect all ProvidedCHO keys present in a cortex JSON items file,
          with frequency counts and sample values. Used to confirm field names
          for date (dcterms:created, dcterms:issued) and other ProvidedCHO fields.
Usage:    python scripts/analysis/inspect_cho_keys.py <items.json>
          python scripts/analysis/inspect_cho_keys.py \
              /path/to/items-excerpt-1000.json
Inputs:   cortex JSON file — array of item objects with edm.RDF.ProvidedCHO
Outputs:  data/processed/cho_keys.csv   (key, count, sample_value)
          stdout summary
Dependencies: pandas
Assumptions: Run from the gemea/ project root.
"""

import json
import sys
import csv
from collections import Counter, defaultdict
from pathlib import Path

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <items.json>", file=sys.stderr)
    sys.exit(1)

JSON_PATH = Path(sys.argv[1])
CSV_OUT   = Path("data/processed/cho_keys.csv")
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

print(f"Loading {JSON_PATH} …")
with open(JSON_PATH) as f:
    data = json.load(f)

items = data if isinstance(data, list) else list(data.values())
print(f"  {len(items):,} items")

key_counts  = Counter()
key_samples = defaultdict(list)   # key → up to 3 non-null sample values

for item in items:
    cho = item.get("edm", {}).get("RDF", {}).get("ProvidedCHO") or {}
    for k, v in cho.items():
        key_counts[k] += 1
        if len(key_samples[k]) < 3 and v not in (None, "", [], {}):
            key_samples[k].append(str(v)[:120])

# ── CSV ────────────────────────────────────────────────────────────────────────
rows = sorted(key_counts.items(), key=lambda x: -x[1])
with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["key", "count", "sample"])
    for k, n in rows:
        w.writerow([k, n, " | ".join(key_samples[k])])
print(f"CSV saved → {CSV_OUT}")

# ── stdout ─────────────────────────────────────────────────────────────────────
print()
print(f"{'key':<30} {'count':>6}  sample")
print("-" * 90)
for k, n in rows:
    sample = key_samples[k][0] if key_samples[k] else ""
    print(f"{k:<30} {n:>6}  {sample[:55]}")

# ── highlight date fields ──────────────────────────────────────────────────────
print()
print("Date / time fields:")
date_keys = [k for k in key_counts if any(
    t in k.lower() for t in ("date", "creat", "issu", "time", "begin", "end", "temporal")
)]
for k in date_keys:
    print(f"  {k}: count={key_counts[k]}, samples={key_samples[k]}")

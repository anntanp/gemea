#!/usr/bin/env python3
"""
Purpose:  Search for any occurrence of "created" key anywhere in the cortex
          JSON structure (not just ProvidedCHO) to locate dcterms:created.
Usage:    python scripts/analysis/inspect_created_field.py <items.json>
Inputs:   cortex JSON file — array of item objects
Outputs:  data/processed/created_field_locations.csv
          stdout summary
Dependencies: none
Assumptions: Run from the gemea/ project root.
"""

import json
import sys
import csv
from pathlib import Path

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <items.json>", file=sys.stderr)
    sys.exit(1)

JSON_PATH = Path(sys.argv[1])
CSV_OUT   = Path("data/processed/created_field_locations.csv")
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)


def find_key(obj, target: str, path: str = ""):
    """Recursively find all paths where target key appears."""
    results = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            current = f"{path}.{k}" if path else k
            if k == target:
                results.append((current, str(v)[:120]))
            results.extend(find_key(v, target, current))
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:5]):  # limit list depth
            results.extend(find_key(v, target, f"{path}[{i}]"))
    return results


print(f"Loading {JSON_PATH} …")
with open(JSON_PATH) as f:
    data = json.load(f)

items = data if isinstance(data, list) else list(data.values())
print(f"  {len(items):,} items")

hits = {}   # path → list of sample values
hit_counts = {}

for item in items:
    for path, val in find_key(item, "created"):
        hit_counts[path] = hit_counts.get(path, 0) + 1
        if path not in hits:
            hits[path] = []
        if len(hits[path]) < 3:
            hits[path].append(val)

with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["path", "count", "sample"])
    for path, count in sorted(hit_counts.items(), key=lambda x: -x[1]):
        w.writerow([path, count, " | ".join(hits[path])])

print(f"CSV saved → {CSV_OUT}")
print()

if not hit_counts:
    print("'created' key not found anywhere in the JSON structure.")
else:
    print(f"{'path':<60} {'count':>6}  sample")
    print("-" * 100)
    for path, count in sorted(hit_counts.items(), key=lambda x: -x[1]):
        sample = hits[path][0] if hits[path] else ""
        print(f"{path:<60} {count:>6}  {sample[:35]}")

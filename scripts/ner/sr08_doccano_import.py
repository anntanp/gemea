#!/usr/bin/env python3
# Purpose: Extract 'title' and 'spans' fields from sr08_gold_prefilled.jsonl for Doccano import
# Usage: python sr08_doccano_import.py
# Input: data/annotation/sr08_gold_prefilled.jsonl
# Output: data/annotation/sr08-doccano-import.jsonl
# Dependencies: none (stdlib only)

import json
from pathlib import Path

INPUT = Path(__file__).parent.parent / "data/annotation/sr08_gold_prefilled.jsonl"
OUTPUT = Path(__file__).parent.parent / "data/annotation/sr08-doccano-import.jsonl"

with INPUT.open() as fin, OUTPUT.open("w") as fout:
    for line in fin:
        record = json.loads(line)
        labels = [[s["start"], s["end"], s["label"]] for s in record["spans"]]
        out = {"text": record["title"], "label": labels}
        fout.write(json.dumps(out, ensure_ascii=False) + "\n")

print(f"Written to {OUTPUT}")

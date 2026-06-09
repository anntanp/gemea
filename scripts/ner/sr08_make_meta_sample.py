#!/usr/bin/env python3
# Purpose:      Generate a 10-record Doccano import sample with meta (htype + DDB URL) for UI verification
# Usage:        python scripts/ner/sr08_make_meta_sample.py
# Inputs:       data/annotation/doccano/export-20260608-1221/maria.jsonl
#               data/annotation/sr08_gold_sample.csv
#               data/schema/ddbedm-htype.csv
# Outputs:      data/annotation/doccano/export-20260608-1221/sr08_meta_sample_10.jsonl
# Dependencies: pandas
# Assumptions:  Doccano id (1-indexed) == row index + 1 in sr08_gold_sample.csv (verified by title match)

import json
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[2]

MARIA  = BASE / "data/annotation/doccano/export-20260608-1221/maria.jsonl"
SAMPLE = BASE / "data/annotation/sr08_gold_sample.csv"
HTYPE  = BASE / "data/schema/ddbedm-htype.csv"
OUTPUT = BASE / "data/annotation/doccano/export-20260608-1221/sr08_meta_sample_10.jsonl"

# "Monograph" is the English label in 3 records; maps to htype_021 (Monografie)
MONOGRAPH_FALLBACK = "htype_021 (Monografie)"


def build_htype_lookup(path: Path) -> dict:
    df = pd.read_csv(path)
    return {row["label_de"]: f"{row['htype_code']} ({row['label_de']})"
            for _, row in df.iterrows()}


def derive_htype(type_str, lookup: dict):
    if not isinstance(type_str, str):
        return None
    last = type_str.split("|")[-1].strip()
    if last == "Monograph":
        return MONOGRAPH_FALLBACK
    return lookup.get(last)


def main():
    lookup = build_htype_lookup(HTYPE)
    sample_df = pd.read_csv(SAMPLE).reset_index(drop=True)

    with open(MARIA, encoding="utf-8") as f:
        doccano = [json.loads(line) for line in f]

    # Preflight: count and title alignment for all records
    if len(doccano) != len(sample_df):
        sys.exit(f"Record count mismatch: {len(doccano)} doccano vs {len(sample_df)} sample rows")
    for i, (rec, (_, row)) in enumerate(zip(doccano, sample_df.iterrows())):
        if rec["text"].strip() != str(row["title"]).strip():
            raise ValueError(f"Title mismatch at index {i}:\n  doccano: {rec['text']!r}\n  sample:  {row['title']!r}")

    # First 10 records + first null-htype record (if not already in 0–9)
    base = list(range(10))
    null_idx = next(
        (i for i, (_, row) in enumerate(sample_df.iterrows()) if not isinstance(row["dc_type"], str)),
        None,
    )
    indices = base if (null_idx is None or null_idx < 10) else base + [null_idx]

    out = []
    for i in indices:
        rec = dict(doccano[i])
        row = sample_df.iloc[i]
        rec["meta"] = {
            "htype": derive_htype(row["dc_type"], lookup),
            "url": row["ddb_link"],
        }
        out.append(rec)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    print(f"Wrote {len(out)} records → {OUTPUT}")
    for rec in out:
        print(f"  id={rec['id']:3d}  htype={str(rec['meta']['htype']):<30s}  {rec['text'][:55]}")


if __name__ == "__main__":
    import sys
    main()

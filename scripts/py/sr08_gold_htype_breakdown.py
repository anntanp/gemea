"""
Purpose:  Compute percentage breakdown of hierarchy_type values in the SR-08 gold set,
          with human-readable labels joined from the htype reference CSV.
Usage:    python scripts/py/sr08_gold_htype_breakdown.py
Inputs:   data/annotation/sr08_gold_sample.csv
          data/out/s2/s2_meta.parquet  (columns: obj_id, hierarchy_type)
          /Users/mta/Documents/claude/goethe-faust/data/htype.csv
Outputs:  data/processed/ner/sr08_gold_htype_breakdown.csv
Dependencies: pandas, pyarrow
Assumptions: obj_id is the join key in both files.
"""

import pandas as pd

GOLD_CSV   = "data/annotation/sr08_gold_sample.csv"
META_PQ    = "data/out/s2/s2_meta.parquet"
HTYPE_CSV  = "/Users/mta/Documents/claude/goethe-faust/data/htype.csv"
OUT_CSV    = "data/processed/ner/sr08_gold_htype_breakdown.csv"

gold = pd.read_csv(GOLD_CSV, usecols=["obj_id"])
print(f"Gold set: {len(gold):,} records")

meta = pd.read_parquet(META_PQ, columns=["obj_id", "hierarchy_type"])
merged = gold.merge(meta, on="obj_id", how="left")

n_missing = merged["hierarchy_type"].isna().sum()
if n_missing:
    print(f"Warning: {n_missing} gold records not found in s2_meta")

counts = merged["hierarchy_type"].value_counts(dropna=False)
pct    = (counts / len(merged) * 100).round(2)

result = pd.DataFrame({"hierarchy_type": counts.index, "n": counts.values, "pct": pct.values})

htype_labels = pd.read_csv(HTYPE_CSV, usecols=["htype_code", "label_en"])
result = result.merge(htype_labels, left_on="hierarchy_type", right_on="htype_code", how="left")
result = result.drop(columns=["htype_code"])

result.to_csv(OUT_CSV, index=False)
print(f"\nhierarchy_type breakdown (n={len(merged)}):\n")
print(result.to_string(index=False))
print(f"\nSaved → {OUT_CSV}")

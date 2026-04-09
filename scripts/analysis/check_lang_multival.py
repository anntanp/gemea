#!/usr/bin/env python3
"""
Purpose:  Report what fraction of DDB Sector 2 objects have multi-value lang entries.
Usage:    python scripts/analysis/check_lang_multival.py
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  stdout
Dependencies: pandas, pyarrow
Assumptions: Run from the gemea/ project root.
"""

import pandas as pd
from pathlib import Path

PARQUET = Path("data/out/s2/s2_meta.parquet")

df = pd.read_parquet(PARQUET, columns=["obj_id", "lang"])
total = len(df)


def code_count(val) -> int:
    if isinstance(val, list):
        return len([v for v in val if str(v).strip()])
    if isinstance(val, str) and val.strip():
        return len(val.split())
    return 0


df["n_codes"] = df["lang"].apply(code_count)

n_zero  = int((df["n_codes"] == 0).sum())
n_one   = int((df["n_codes"] == 1).sum())
n_multi = int((df["n_codes"] >  1).sum())

print(f"Total objects : {total:>12,}")
print(f"No lang (null): {n_zero:>12,}  ({n_zero  / total * 100:.2f}%)")
print(f"Single lang   : {n_one:>12,}  ({n_one   / total * 100:.2f}%)")
print(f"Multi lang    : {n_multi:>12,}  ({n_multi / total * 100:.2f}%)")

# distribution of multi-value counts
if n_multi:
    print()
    print("Multi-value breakdown (n_codes → count):")
    breakdown = df[df["n_codes"] > 1]["n_codes"].value_counts().sort_index()
    for k, v in breakdown.items():
        print(f"  {k} codes : {v:>10,}  ({v / total * 100:.3f}%)")

# sample
print()
print("Sample multi-value lang entries:")
sample = df[df["n_codes"] > 1][["obj_id", "lang"]].head(10)
for _, r in sample.iterrows():
    print(f"  {r.obj_id}  {r.lang!r}")

#!/usr/bin/env python3
# Purpose:      Check how often dc:creator and dc:contributor are present in DF_DE_TITLES,
#               overall and broken down by era. Validates the claim that person metadata
#               is "usually present" and that NER PERSON extraction is a fallback.
# Usage:        python3 scripts/sr08_check_agent_coverage.py
# Input:        data/DF_DE_TITLES_20240125b.pkl
# Output:       stdout summary table
# Dependencies: pandas, numpy
# Assumptions:  sr08_sample_gold.py era derivation logic (dates col, same bins)

import pandas as pd
import numpy as np

PKL = "data/DF_DE_TITLES_20240125b.pkl"

df = pd.read_pickle(PKL)
print(f"Total records: {len(df):,}\n")

# A field is "present" if it is non-null, non-empty, and not a placeholder
def is_present(col):
    s = col.astype(str).str.strip()
    return col.notna() & ~s.isin(["", "nan", "None", "[]", "{}"])

creator    = is_present(df["dc_creator"])
contributor = is_present(df["dc_contributor"])
either     = creator | contributor

print("Overall:")
print(f"  dc_creator present:      {creator.sum():>8,}  ({100*creator.mean():.1f}%)")
print(f"  dc_contributor present:  {contributor.sum():>8,}  ({100*contributor.mean():.1f}%)")
print(f"  Either present:          {either.sum():>8,}  ({100*either.mean():.1f}%)")
print(f"  Both absent:             {(~either).sum():>8,}  ({100*(~either).mean():.1f}%)")

# Era breakdown
df["era"] = pd.cut(
    pd.to_numeric(df["dates"], errors="coerce"),
    bins=[-np.inf, 1700, 1800, 1900, np.inf],
    labels=["pre-1700", "1700-1800", "19th-c", "modern"],
    right=False,
)
df["era"] = df["era"].cat.add_categories("unknown").fillna("unknown")

print("\nBy era (% with either dc:creator or dc:contributor present):")
summary = df.groupby("era", observed=False).apply(
    lambda g: pd.Series({
        "records":       len(g),
        "either_%":      round(100 * either[g.index].mean(), 1),
        "both_absent_%": round(100 * (~either[g.index]).mean(), 1),
    }),
    include_groups=False,
)
print(summary.to_string())

OUT = "data/processed/sr08_agent_coverage_by_era.csv"
summary.to_csv(OUT)
print(f"\nSaved to {OUT}")

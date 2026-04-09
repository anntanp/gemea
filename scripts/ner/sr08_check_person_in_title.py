#!/usr/bin/env python3
# Purpose:      Check how often a person name appears in the title string (ner_person col),
#               broken down by era. Validates whether NER PERSON extraction is useful
#               for modern vs. pre-1700 records independently of dc:creator availability.
# Usage:        python3 scripts/sr08_check_person_in_title.py
# Input:        data/DF_DE_TITLES_20240125b.pkl
# Output:       stdout summary table
# Dependencies: pandas, numpy
# Assumptions:  ner_person col contains NER-detected person spans (non-empty = person found)

import pandas as pd
import numpy as np

PKL = "data/DF_DE_TITLES_20240125b.pkl"

df = pd.read_pickle(PKL)
print(f"Total records: {len(df):,}\n")

# Inspect ner_person values
print("ner_person sample (first 10 non-null):")
sample = df.loc[df["ner_person"].notna(), "ner_person"].head(10)
print(sample.to_string())
print()

# A person is detected if ner_person is non-null, non-empty, not placeholder
def is_present(col):
    s = col.astype(str).str.strip()
    return col.notna() & ~s.isin(["", "nan", "None", "[]", "{}"])

person_in_title = is_present(df["ner_person"])

print(f"ner_person present overall: {person_in_title.sum():,} ({100*person_in_title.mean():.1f}%)\n")

# Era breakdown
df["era"] = pd.cut(
    pd.to_numeric(df["dates"], errors="coerce"),
    bins=[-np.inf, 1700, 1800, 1900, np.inf],
    labels=["pre-1700", "1700-1800", "19th-c", "modern"],
    right=False,
)
df["era"] = df["era"].cat.add_categories("unknown").fillna("unknown")

print("ner_person present by era:")
summary = df.groupby("era", observed=False).apply(
    lambda g: pd.Series({
        "records":           len(g),
        "person_in_title_%": round(100 * person_in_title[g.index].mean(), 1),
    }),
    include_groups=False,
)
print(summary.to_string())

OUT = "data/processed/sr08_person_in_title_by_era.csv"
summary.to_csv(OUT)
print(f"\nSaved to {OUT}")

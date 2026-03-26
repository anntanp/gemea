#!/usr/bin/env python3
# Purpose:      Compute actual corpus cell sizes (era × silver_tier) from DF_DE_TITLES.
#               Replaces the round-number allocation targets in sr08_gold-set-composition.md §2.2
#               with counts derived from the actual corpus.
# Usage:        python3 scripts/sr08_corpus_cell_sizes.py
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
#               data/processed/isbd_field_ratings.csv
# Outputs:      data/processed/sr08_corpus_cell_sizes.csv  — era × tier counts and percentages
# Dependencies: pandas, numpy
# Assumptions:  isbd_field_ratings.csv has obj_id and silver_tier columns;
#               era derivation uses same bins as sr08_sample_gold.py

import pandas as pd
import numpy as np

PKL     = "data/DF_DE_TITLES_20240125b.pkl"
RATINGS = "data/processed/isbd_field_ratings.csv"
OUT     = "data/processed/sr08_corpus_cell_sizes.csv"

df = pd.read_pickle(PKL)
ratings = pd.read_csv(RATINGS, usecols=["obj_id", "silver_tier"])
df = df.merge(ratings, on="obj_id", how="left")
df["silver_tier"] = df["silver_tier"].fillna(0).astype(int).astype(str)

df["era"] = pd.cut(
    pd.to_numeric(df["dates"], errors="coerce"),
    bins=[-np.inf, 1700, 1800, 1900, np.inf],
    labels=["pre-1700", "1700-1800", "19th-c", "modern"],
    right=False,
)
df["era"] = df["era"].cat.add_categories("unknown").fillna("unknown")

total = len(df)

# Crosstab: counts
counts = df.groupby(["era", "silver_tier"], observed=False).size().unstack(fill_value=0)
counts.columns = [f"tier-{c}" for c in counts.columns]
counts["total"] = counts.sum(axis=1)

# Percentage of corpus total
pct = (counts / total * 100).round(1)
pct.columns = [f"{c}_%" for c in pct.columns]

result = pd.concat([counts, pct], axis=1).sort_index()

print(f"Total records: {total:,}\n")
print("Cell sizes (era × silver_tier):")
print(counts.to_string())
print()
print("As % of corpus total:")
print(pct.to_string())

result.to_csv(OUT)
print(f"\nSaved to {OUT}")

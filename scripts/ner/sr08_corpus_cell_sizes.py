#!/usr/bin/env python3
# Purpose:      Compute actual corpus cell sizes (era × silver_tier) from DF_DE_TITLES.
#               Replaces the round-number allocation targets in sr08_gold-set-composition.md §2.2
#               with counts derived from the actual corpus.
# Usage:        python3 scripts/ner/sr08_corpus_cell_sizes.py [--data PATH] [--ratings PATH] [--output PATH]
# Inputs:       data/processed/de_titles_tokenized.parquet  (or pkl)
#               data/processed/ner/sr01_isbd_field_ratings.csv
# Outputs:      data/processed/ner/sr08_corpus_cell_sizes.csv  — era × tier counts and percentages
# Dependencies: pandas, numpy
# Assumptions:  sr01_isbd_field_ratings.csv has obj_id and silver_tier columns;
#               era derivation uses same bins as sr08_sample_gold.py

import argparse
import pickle
from pathlib import Path

import pandas as pd
import numpy as np

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / "data" / "processed" / "de_titles_tokenized.parquet"
RATINGS = ROOT / "data" / "processed" / "ner" / "sr01_isbd_field_ratings.csv"
OUT     = ROOT / "data" / "processed" / "ner" / "sr08_corpus_cell_sizes.csv"


def load_data(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=["obj_id", "dates"])
    with open(path, "rb") as f:
        return pickle.load(f)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute corpus cell sizes (era × silver_tier)."
    )
    parser.add_argument("--data",    type=Path, default=DATA,    help="Corpus path (parquet or pkl)")
    parser.add_argument("--ratings", type=Path, default=RATINGS, help="SR-01 field ratings CSV")
    parser.add_argument("--output",  type=Path, default=OUT,     help="Output CSV path")
    args = parser.parse_args()

    df = load_data(args.data)
    ratings = pd.read_csv(args.ratings, usecols=["obj_id", "silver_tier"])
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

    args.output.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(args.output)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()

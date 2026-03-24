#!/usr/bin/env python3
# Purpose:      SR-08 — Draw the ~500-record stratified gold sample for NER annotation.
#               Samples from DF_DE_TITLES by era × silver_tier × dc_type, with
#               oversampling of Leichenpredigt and Einblattdruck (highest-risk genres).
#               Output is a CSV ready for import into an annotation tool.
# Usage:        python3 scripts/sr08_sample_gold.py [--data PATH] [--ratings PATH]
#                   [--output PATH] [--seed INT]
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
#               data/processed/isbd_field_ratings.csv
# Outputs:      data/annotation/sr08_gold_sample.csv
# Dependencies: pandas, numpy
# Assumptions:  isbd_field_ratings.csv exists (run sr01_rate_isbd_fields.py first).
#               data/annotation/ is created if it does not exist.

import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
RATINGS = ROOT / "data" / "processed" / "isbd_field_ratings.csv"
OUTPUT  = ROOT / "data" / "annotation" / "sr08_gold_sample.csv"
DDB_URL = "https://www.deutsche-digitale-bibliothek.de/item/{}"

# ── Stratification ─────────────────────────────────────────────────────────────

# Target draw per (era, silver_tier): (era, tier, n)
STRATA = [
    ("modern",    "2",  20), ("modern",    "1",  40), ("modern",    "0",  20),
    ("19th-c",    "2",  15), ("19th-c",    "1",  30), ("19th-c",    "0",  15),
    ("1700-1800", "2",  10), ("1700-1800", "1",  20), ("1700-1800", "0",  30),
    ("pre-1700",  "2",   5), ("pre-1700",  "1",  15), ("pre-1700",  "0",  80),
]

# dc_type values to oversample (up to N each, tier-0 and tier-1 only)
OVERSAMPLE_TYPES = [("Leichenpredigt", 50), ("Einblattdruck", 50)]


def derive_era(dates_numeric: pd.Series) -> pd.Series:
    """Map numeric year to era label; NaN → 'unknown'."""
    era = pd.cut(
        dates_numeric,
        bins=[-np.inf, 1700, 1800, 1900, np.inf],
        labels=["pre-1700", "1700-1800", "19th-c", "modern"],
        right=False,
    )
    return era.cat.add_categories("unknown").fillna("unknown")


def load_data(data_path: Path, ratings_path: Path) -> pd.DataFrame:
    print(f"Loading corpus from {data_path} ...")
    with open(data_path, "rb") as f:
        df = pickle.load(f)

    print(f"Loading ratings from {ratings_path} ...")
    ratings = pd.read_csv(ratings_path, usecols=["obj_id", "silver_tier"])

    df = df.merge(ratings, on="obj_id", how="left")
    # Records absent from ratings (shouldn't happen, but be safe) → tier 0
    df["silver_tier"] = df["silver_tier"].fillna(0).astype(int).astype(str)

    df["year_num"] = pd.to_numeric(df["dates"], errors="coerce")
    df["era"] = derive_era(df["year_num"])

    return df


def draw_sample(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    frames = []

    # ── Stratified draw ────────────────────────────────────────────────────────
    for era, tier, n in STRATA:
        pool = df[(df["era"] == era) & (df["silver_tier"] == tier)]
        k = min(n, len(pool))
        if k == 0:
            print(f"  WARNING: no records for era={era} tier={tier}")
            continue
        if k < n:
            print(f"  WARNING: era={era} tier={tier} — only {k} available (wanted {n})")
        frames.append(pool.sample(n=k, random_state=int(rng.integers(1_000_000))))

    # ── dc_type oversampling ───────────────────────────────────────────────────
    for dc_type, n in OVERSAMPLE_TYPES:
        pool = df[
            df["dc_type"].str.contains(dc_type, na=False) &
            df["silver_tier"].isin(["0", "1"])
        ]
        k = min(n, len(pool))
        if k == 0:
            print(f"  WARNING: no records for dc_type={dc_type}")
            continue
        frames.append(pool.sample(n=k, random_state=int(rng.integers(1_000_000))))

    gold = (
        pd.concat(frames)
        .drop_duplicates(subset=["obj_id"])
        .sample(frac=1, random_state=seed)
        .reset_index(drop=True)
    )
    return gold


def print_summary(df: pd.DataFrame) -> None:
    print(f"\nGold sample: {len(df)} records")

    print("\nEra × tier breakdown:")
    breakdown = (
        df.groupby(["era", "silver_tier"], observed=True)
        .size()
        .unstack(fill_value=0)
        .reindex(["pre-1700", "1700-1800", "19th-c", "modern", "unknown"])
    )
    print(breakdown.to_string())

    print("\nTop dc_types:")
    print(df["dc_type"].value_counts().head(10).to_string())


def main() -> None:
    parser = argparse.ArgumentParser(description="SR-08: draw stratified NER gold sample")
    parser.add_argument("--data",    type=Path, default=DATA,    help="path to corpus pkl")
    parser.add_argument("--ratings", type=Path, default=RATINGS, help="path to ratings CSV")
    parser.add_argument("--output",  type=Path, default=OUTPUT,  help="output CSV path")
    parser.add_argument("--seed",    type=int,  default=42,      help="global RNG seed")
    args = parser.parse_args()

    df = load_data(args.data, args.ratings)
    gold = draw_sample(df, args.seed)

    # Keep only the columns needed for annotation
    keep = ["obj_id", "title", "dates", "dc_type", "silver_tier", "era", "all_tokens"]
    keep = [c for c in keep if c in gold.columns]
    gold = gold[keep].copy()
    gold["ddb_link"] = gold["obj_id"].apply(DDB_URL.format)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    gold.to_csv(args.output, index=False)
    print_summary(gold)
    print(f"\nWritten to {args.output}")


if __name__ == "__main__":
    main()

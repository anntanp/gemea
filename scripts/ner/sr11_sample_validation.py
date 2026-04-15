#!/usr/bin/env python3
# Purpose:      SR-11 T11.1a — Sample 50 pre-1750 tier-0 records for manual prompt
#               validation. Stratified by dc_type (Leichenpredigt, Einblattdruck
#               oversampled; remainder split across Monografie and other types).
#               Excludes all SR-08 gold sample obj_ids.
#               Outputs a JSONL file with empty spans ready for manual annotation.
#
# Usage:        python3 scripts/ner/sr11_sample_validation.py
#                   [--data PATH]       # default: data/processed/de_titles_tokenized.parquet
#                   [--ratings PATH]    # default: data/processed/ner/sr01_isbd_field_ratings.csv
#                   [--gold PATH]       # default: data/annotation/sr08_gold_sample.csv
#                   [--output PATH]     # default: data/annotation/sr11_prompt_validation_manual.jsonl
#                   [--n INT]           # total records to sample (default: 50)
#                   [--seed INT]        # random seed (default: 42)
#
# Inputs:       data/processed/de_titles_tokenized.parquet  (or pkl)
#               data/processed/ner/sr01_isbd_field_ratings.csv
#               data/annotation/sr08_gold_sample.csv
# Outputs:      data/annotation/sr11_prompt_validation_manual.jsonl
#
# NOTE:         dc_type in de_titles_tokenized.parquet must carry the DDB genre/form
#               values (Leichenpredigt, Einblattdruck, Monografie) for TARGET_TYPES
#               filtering to work. This requires the correct dc:type / edm:hasType
#               field to be exported in export_s2.py. Parquet is being regenerated.
#
# Dependencies: pandas, numpy
# Assumptions:  sr01_isbd_field_ratings.csv exists (run sr01_rate_isbd_fields.py first).
#               sr08_gold_sample.csv exists (SR-08 complete).

import argparse
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


def load_corpus(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=["obj_id", "title", "dc_type", "dates"])
    with open(path, "rb") as f:
        return pickle.load(f)

ROOT    = Path(__file__).parent.parent.parent
DATA    = ROOT / "data" / "processed" / "de_titles_tokenized.parquet"
RATINGS = ROOT / "data" / "processed" / "ner" / "sr01_isbd_field_ratings.csv"
GOLD    = ROOT / "data" / "annotation" / "sr08_gold_sample.csv"
OUTPUT  = ROOT / "data" / "annotation" / "sr11_prompt_validation_manual.jsonl"
DDB_URL = "https://www.deutsche-digitale-bibliothek.de/item/{}"

# Pre-1750 eras (Phase 2 target domain)
PRE_1750_ERAS = {"pre-1700", "1700-1800"}

# Phase 2 target dc_types with explicit counts (must sum to <= n).
# Remainder (n - sum) drawn from non-Kapitel/Abschnitt/Band types only.
# dc_type values (Leichenpredigt, Einblattdruck, Monografie) come from
# dc:type / edm:hasType in the DDB EDM export — requires regenerated parquet.
TARGET_TYPES = [
    ("Leichenpredigt", 15),
    ("Einblattdruck",  15),
    ("Monografie",     15),
]
REMAINDER_EXCLUDE = {"Kapitel", "Abschnitt", "Band"}
REMAINDER_N = 5


def derive_era(dates_numeric: pd.Series) -> pd.Series:
    era = pd.cut(
        dates_numeric,
        bins=[-np.inf, 1700, 1800, 1900, np.inf],
        labels=["pre-1700", "1700-1800", "19th-c", "modern"],
        right=False,
    )
    return era.cat.add_categories("unknown").fillna("unknown")


def load_pool(data_path: Path, ratings_path: Path, gold_path: Path) -> pd.DataFrame:
    print(f"Loading corpus from {data_path} ...")
    df = load_corpus(data_path)

    print(f"Loading ratings from {ratings_path} ...")
    ratings = pd.read_csv(ratings_path, usecols=["obj_id", "silver_tier"])
    df = df.merge(ratings, on="obj_id", how="left")
    df["silver_tier"] = df["silver_tier"].fillna(0).astype(int).astype(str)

    df["year_num"] = pd.to_numeric(df["dates"], errors="coerce")
    df["era"] = derive_era(df["year_num"])

    # Exclude SR-08 gold sample
    gold_ids = set(pd.read_csv(gold_path, usecols=["obj_id"])["obj_id"])
    n_before = len(df)
    df = df[~df["obj_id"].isin(gold_ids)]
    print(f"Excluded {n_before - len(df)} SR-08 gold obj_ids")

    # Filter: pre-1750 tier-0 only
    pool = df[df["era"].isin(PRE_1750_ERAS) & (df["silver_tier"] == "0")].copy()
    print(f"Pre-1750 tier-0 pool (after exclusions): {len(pool):,} records")
    return pool


def draw_sample(pool: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    sampled_ids: set = set()
    frames = []

    # Draw Phase 2 target dc_types explicitly
    for dc_type, target in TARGET_TYPES:
        sub = pool[
            pool["dc_type"].str.contains(dc_type, na=False) &
            ~pool["obj_id"].isin(sampled_ids)
        ]
        k = min(target, len(sub))
        if k == 0:
            print(f"  WARNING: no records for dc_type={dc_type}")
            continue
        if k < target:
            print(f"  WARNING: dc_type={dc_type} — only {k} available (wanted {target})")
        drawn = sub.sample(n=k, random_state=int(rng.integers(1_000_000)))
        frames.append(drawn)
        sampled_ids.update(drawn["obj_id"])

    # Fill remainder from non-sub-work types (exclude Kapitel, Abschnitt, Band)
    rest = pool[
        ~pool["obj_id"].isin(sampled_ids) &
        ~pool["dc_type"].isin(REMAINDER_EXCLUDE)
    ]
    k = min(REMAINDER_N, len(rest))
    if k < REMAINDER_N:
        print(f"  WARNING: remainder pool only {k} records (wanted {REMAINDER_N})")
    drawn = rest.sample(n=k, random_state=int(rng.integers(1_000_000)))
    frames.append(drawn)

    sample = pd.concat(frames).drop_duplicates(subset="obj_id")
    return sample


def to_jsonl(sample: pd.DataFrame, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        for _, row in sample.iterrows():
            record = {
                "obj_id":            row["obj_id"],
                "title":             row["title"],
                "dates":             str(row.get("dates", "")),
                "dc_type":           str(row.get("dc_type", "")),
                "silver_tier":       row["silver_tier"],
                "era":               row["era"],
                "ddb_link":          DDB_URL.format(row["obj_id"]),
                "spans":             [],
                "annotation_status": "manual",
                "annotator":         "",
                "annotation_date":   "",
                "notes":             "",
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SR-11 T11.1a: sample 50 pre-1750 tier-0 records for prompt validation"
    )
    parser.add_argument("--data",    type=Path, default=DATA)
    parser.add_argument("--ratings", type=Path, default=RATINGS)
    parser.add_argument("--gold",    type=Path, default=GOLD)
    parser.add_argument("--output",  type=Path, default=OUTPUT)
    parser.add_argument("--n",       type=int,  default=50)
    parser.add_argument("--seed",    type=int,  default=42)
    args = parser.parse_args()

    pool   = load_pool(args.data, args.ratings, args.gold)
    sample = draw_sample(pool, args.n, args.seed)

    # Print dc_type distribution of sample
    print(f"\nSample size: {len(sample)}")
    print("dc_type distribution:")
    for dc_type, count in sample["dc_type"].value_counts().items():
        print(f"  {dc_type:<25} {count}")
    print("era distribution:")
    for era, count in sample["era"].value_counts().items():
        print(f"  {era:<25} {count}")

    to_jsonl(sample, args.output)
    print(f"\nOutput written to {args.output}")
    print("Next step (T11.1b): annotate spans manually in the JSONL file.")


if __name__ == "__main__":
    main()

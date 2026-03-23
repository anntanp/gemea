#!/usr/bin/env python3
# Purpose:      Sample 200 heuristic-tier records from isbd_field_ratings.csv and
#               present each title with its detected field flags for manual false-positive
#               review. Writes a review sheet (CSV) pre-filled with detected flags;
#               reviewer adds a 'fp_fields' column listing any fields that are false
#               positives, and 'notes' for comments.
# Usage:        python3 scripts/validate_heuristic_fields.py [--ratings PATH]
#                   [--data PATH] [--output PATH] [--n N] [--seed N]
# Inputs:       data/processed/isbd_field_ratings.csv — output of rate_isbd_fields.py
#               data/DF_DE_TITLES_20240125b.pkl        — for DDB URL construction
# Outputs:      data/processed/heuristic_validation_sample.csv — review sheet
# Dependencies: pandas
# Assumptions:  isbd_field_ratings.csv exists (run rate_isbd_fields.py first).
#               Heuristic tier = silver_tier 1 records with has_dot_dash == False.

import argparse
import pickle
from pathlib import Path

import pandas as pd

ROOT            = Path(__file__).parent.parent
RATINGS_DEFAULT = ROOT / "data" / "processed" / "isbd_field_ratings.csv"
DATA_DEFAULT    = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_DEFAULT  = ROOT / "data" / "processed" / "heuristic_validation_sample.csv"
DDB_ITEM_URL    = "https://ddb.de/item/{}"

# Heuristic-only field flags (those that can produce false positives without `. -`)
HEURISTIC_FIELDS = [
    "f_other_title",     # ` :` fires on non-ISBD colons
    "f_person",          # ` /` fires on fractions / paths
    "f_person_compound", # ` / ... ;` — compound SoR check
    "f_parallel",        # ` =` fires on equality signs
    "f_edition",         # edition keywords — generally reliable but worth checking
    "f_year",            # 4-digit year fires on non-publication years
    "f_publisher",       # Verlag/Press keyword — low recall, but check precision
    "f_series",          # parenthetical + digit — generally reliable
    "f_volume",          # volume keyword — generally reliable
]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample heuristic-tier records for manual false-positive review."
    )
    parser.add_argument("--ratings", type=Path, default=RATINGS_DEFAULT,
                        help="Path to isbd_field_ratings.csv (default: %(default)s)")
    parser.add_argument("--data",    type=Path, default=DATA_DEFAULT,
                        help="Path to DF_DE_TITLES pkl, used only for dc_type column "
                             "if present (default: %(default)s)")
    parser.add_argument("--output",  type=Path, default=OUTPUT_DEFAULT,
                        help="Path to output review sheet (default: %(default)s)")
    parser.add_argument("--n",       type=int, default=200,
                        help="Number of records to sample (default: %(default)s)")
    parser.add_argument("--seed",    type=int, default=42,
                        help="Random seed for reproducibility (default: %(default)s)")
    args = parser.parse_args()

    # --- Load ratings ---
    print(f"Loading ratings from {args.ratings} ...")
    ratings = pd.read_csv(args.ratings, low_memory=False)
    print(f"  {len(ratings):,} total records")

    # --- Select heuristic-tier records (silver_tier >= 1, has_dot_dash == False) ---
    heuristic = ratings[
        (ratings["has_dot_dash"] == False) &
        (ratings["silver_tier"] >= 1)
    ].copy()
    print(f"  {len(heuristic):,} heuristic-tier records (silver_tier≥1, no area separator)")

    if len(heuristic) == 0:
        raise ValueError("No heuristic-tier records found. Check ratings file.")

    # --- Stratified sample: one record per detected field flag where possible ---
    # Sample proportionally from each dominant detected field to cover all flag types
    n = min(args.n, len(heuristic))
    per_field = max(1, n // len(HEURISTIC_FIELDS))
    parts = []
    seen_ids = set()

    for field in HEURISTIC_FIELDS:
        if field not in heuristic.columns:
            continue
        pool = heuristic[(heuristic[field] == 1) & (~heuristic["obj_id"].isin(seen_ids))]
        take = min(per_field, len(pool))
        if take > 0:
            sampled = pool.sample(n=take, random_state=args.seed)
            parts.append(sampled)
            seen_ids.update(sampled["obj_id"].tolist())

    # Top up to n with any remaining heuristic records not yet selected
    remaining_needed = n - len(seen_ids)
    if remaining_needed > 0:
        leftover = heuristic[~heuristic["obj_id"].isin(seen_ids)]
        if len(leftover) > 0:
            extra = leftover.sample(n=min(remaining_needed, len(leftover)),
                                    random_state=args.seed)
            parts.append(extra)

    sample = pd.concat(parts, ignore_index=True).head(n)

    # --- Optionally join dc_type from the PKL for context ---
    if args.data.exists():
        try:
            print(f"Loading dc_type from {args.data} ...")
            with open(args.data, "rb") as f:
                df_full = pickle.load(f)
            if "dc_type" in df_full.columns:
                sample = sample.merge(
                    df_full[["obj_id", "dc_type"]].drop_duplicates("obj_id"),
                    on="obj_id", how="left"
                )
        except Exception as e:
            print(f"  Warning: could not load PKL ({e}); skipping dc_type join")

    # --- Build review sheet ---
    sample["ddb_url"] = sample["obj_id"].apply(DDB_ITEM_URL.format)

    # Reviewer columns (blank — to be filled in)
    sample["fp_fields"] = ""   # comma-separated list of field names that are false positives
    sample["notes"]     = ""   # free-text notes

    # Column order: context first, then flags, then reviewer columns
    flag_cols   = [c for c in HEURISTIC_FIELDS if c in sample.columns]
    meta_cols   = ["obj_id", "ddb_url", "title"]
    if "dc_type" in sample.columns:
        meta_cols.append("dc_type")
    meta_cols  += ["silver_tier", "n_fields", "has_dot_dash"]
    review_cols = ["fp_fields", "notes"]

    out_cols = meta_cols + flag_cols + review_cols
    out_cols = [c for c in out_cols if c in sample.columns]
    sample = sample[out_cols]

    # --- Write ---
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False)
    print(f"\nWrote {len(sample)} records → {args.output}")

    # --- Summary ---
    print(f"\nField flag counts in sample:")
    print(f"  {'Field':<20}  {'Flagged':>7}  {'%':>6}")
    print(f"  {'-'*38}")
    for field in flag_cols:
        n_flagged = sample[field].sum()
        print(f"  {field:<20}  {n_flagged:>7}  {n_flagged/len(sample)*100:>5.1f}%")

    print(f"""
Review instructions:
  1. Open {args.output}
  2. For each row, check whether the detected field flags are correct given the title string
  3. In 'fp_fields', list any field names that are FALSE POSITIVES (comma-separated)
     e.g. "f_other_title,f_year"  if both fired incorrectly
  4. Leave 'fp_fields' blank if all detected flags are correct
  5. Use 'notes' for observations (e.g. "year is a page number, not publication year")
""")


if __name__ == "__main__":
    main()

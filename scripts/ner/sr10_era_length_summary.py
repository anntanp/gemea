# Purpose:      Summarise title-length distribution (short/medium/long, median)
#               per gold-set era stratum (pre-1700, 1700-1800, 19th-c, modern, unknown).
#               Uses the same year-resolution logic and length thresholds as
#               sr10_analyse_title_lengths.py. Era strata match sr08_corpus_cell_sizes.csv.
# Usage:        python scripts/sr10_era_length_summary.py
#               python scripts/sr10_era_length_summary.py --data PATH --output PATH
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
# Outputs:      data/processed/sr10_era_length_summary.csv
# Dependencies: pandas
# Assumptions:  'all_tokens' = spaCy token count incl. stopwords and punctuation.
#               'dates' column is a string year (e.g. '1931') or NaN.
#               Era boundaries: pre-1700 (<1700), 1700-1800 (1700-1799),
#               19th-c (1800-1899), modern (>=1900), unknown (no year).

import re
import argparse
import pickle
from pathlib import Path

import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
DATA_PATH  = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_PATH = ROOT / "data" / "processed" / "sr10_era_length_summary.csv"

SHORT_MAX  = 4
MEDIUM_MAX = 14

YEAR_RE = re.compile(r"\b(?:1[4-9]\d{2}|20[012]\d)\b")

ERA_ORDER = ["pre-1700", "1700-1800", "19th-c", "modern", "unknown"]


def year_from_title(title: str):
    m = list(YEAR_RE.finditer(str(title)))
    return int(m[-1].group()) if m else None


def assign_era(year):
    if year is None:
        return "unknown"
    if year < 1700:
        return "pre-1700"
    if year < 1800:
        return "1700-1800"
    if year < 1900:
        return "19th-c"
    return "modern"


def median(series):
    s = series.sort_values()
    return int(s.iloc[len(s) // 2]) if len(s) else None


def main(data_path: Path, output_path: Path) -> None:
    print(f"Loading {data_path} ...")
    with open(data_path, "rb") as f:
        df = pickle.load(f)
    print(f"Shape: {df.shape}")

    # Resolve year
    def resolve_year(row):
        if pd.notna(row["dates"]) and str(row["dates"]).strip():
            try:
                y = int(str(row["dates"]).strip()[:4])
                if 1400 <= y <= 2029:
                    return y
            except ValueError:
                pass
        return year_from_title(row["title"])

    print("Resolving years ...")
    df["year"] = df.apply(resolve_year, axis=1)
    df["era"] = df["year"].apply(assign_era)

    # Compute per-era stats
    rows = []
    for era in ERA_ORDER:
        sub = df[df["era"] == era]["all_tokens"]
        n = len(sub)
        short  = (sub <= SHORT_MAX).sum()
        medium = ((sub > SHORT_MAX) & (sub <= MEDIUM_MAX)).sum()
        long   = (sub > MEDIUM_MAX).sum()
        rows.append({
            "era":           era,
            "records":       n,
            "short_n":       int(short),
            "medium_n":      int(medium),
            "long_n":        int(long),
            "short_pct":     round(100 * short  / n, 1) if n else None,
            "medium_pct":    round(100 * medium / n, 1) if n else None,
            "long_pct":      round(100 * long   / n, 1) if n else None,
            "median_all_tokens": median(sub),
        })

    out = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    print(f"\nSaved: {output_path}")

    # Print table
    print(f"\n{'Era':<12}  {'Records':>9}  {'Short%':>7}  {'Medium%':>8}  {'Long%':>6}  {'Median':>6}")
    print("-" * 62)
    for r in rows:
        if r["records"] == 0:
            print(f"{r['era']:<12}  {r['records']:>9,}  {'—':>7}  {'—':>8}  {'—':>6}  {'—':>6}")
        else:
            print(f"{r['era']:<12}  {r['records']:>9,}  {r['short_pct']:>6.1f}%  "
                  f"{r['medium_pct']:>7.1f}%  {r['long_pct']:>5.1f}%  {r['median_all_tokens']:>6}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    main(args.data, args.output)

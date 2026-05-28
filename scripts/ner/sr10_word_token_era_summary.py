#!/usr/bin/env python3
"""
Compute whitespace word-token counts per era from de_titles_tokenized.parquet.

Purpose:  Produce per-era median word count (whitespace split) to replace the
          BPE-token median in the workshop slide deck era stratification table.
Usage:    python scripts/ner/sr10_word_token_era_summary.py
Inputs:   data/processed/de_titles_tokenized.parquet
Outputs:  data/processed/ner/sr10_word_token_era_summary.csv
Dependencies: pandas, pyarrow
Assumptions:
  - Era assignment uses the first element of the `dates` list column.
  - Whitespace split (.split()) is used as the word tokenizer.
  - Unknown-year records are excluded from era totals.
"""

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
DATA_IN  = ROOT / "data" / "processed" / "de_titles_tokenized.parquet"
DATA_OUT = ROOT / "data" / "processed" / "ner" / "sr10_word_token_era_summary.csv"


def assign_era(dates_val) -> str:
    if not dates_val:
        return "unknown"
    yr = dates_val[0] if isinstance(dates_val, list) else dates_val
    try:
        yr = int(yr)
    except (ValueError, TypeError):
        return "unknown"
    if yr < 1700:
        return "pre-1700"
    if yr < 1800:
        return "1700-1800"
    if yr < 1900:
        return "19th-c"
    return "modern"


def main() -> None:
    print(f"Reading {DATA_IN} …", flush=True)
    df = pd.read_parquet(DATA_IN, columns=["title", "dates"], engine="pyarrow")
    print(f"  {len(df):,} rows loaded", flush=True)

    df["word_count"] = df["title"].str.split().str.len()
    df["era"] = df["dates"].apply(assign_era)

    era_order = ["pre-1700", "1700-1800", "19th-c", "modern", "unknown"]
    result = (
        df.groupby("era")["word_count"]
        .agg(
            records="count",
            median="median",
            mean="mean",
            p25=lambda x: x.quantile(0.25),
            p75=lambda x: x.quantile(0.75),
            p90=lambda x: x.quantile(0.90),
        )
        .reindex(era_order)
        .reset_index()
    )
    result = result.rename(columns={"era": "era", "records": "n_records"})

    DATA_OUT.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(DATA_OUT, index=False)
    print(f"\nSaved → {DATA_OUT}\n")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()

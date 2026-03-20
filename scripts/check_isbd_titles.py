#!/usr/bin/env python3
"""
Purpose:  Load data/DF_DE_TITLES_20240125b.pkl, extract title column(s),
          and report how many titles contain ISBD punctuation marks.
Usage:    python3 check_isbd_titles.py [--data PATH]
Inputs:   DF_DE_TITLES_20240125b.pkl — pandas DataFrame
Outputs:  Console summary with pattern breakdown and sample titles
Dependencies: pandas
Assumptions:  DataFrame has a column containing title strings;
              script auto-detects the title column by name heuristic.
"""

import re
import argparse
import pickle
from collections import Counter
from pathlib import Path

import pandas as pd

DATA_DEFAULT = Path(__file__).parent.parent / "data" / "DF_DE_TITLES_20240125b.pkl"

# ISBD punctuation patterns
# Each tuple: (label, signal, compiled regex)
ISBD_PATTERNS = [
    ("space-slash",   "Statement of responsibility ( / )", re.compile(r" /")),
    ("space-colon",   "Other title information ( : )",     re.compile(r" :")),
    ("space-equals",  "Parallel title ( = )",              re.compile(r" =")),
    ("space-semi",    "Subsequent SoR / series ( ; )",     re.compile(r" ;")),
    ("ellipsis",      "Ellipsis / truncation (… or ...)",  re.compile(r"\.\.\.|…")),
    ("sq-brackets",   "Supplied / inferred data ([ ])",    re.compile(r"\[.+?\]")),
    ("trailing-dot",  "Area-end period (.)",               re.compile(r"[^.]\.$")),
]


def detect_title_column(df: pd.DataFrame) -> str:
    """Return the first column whose name looks like a title field."""
    candidates = [c for c in df.columns if re.search(r"title|titel|name", c, re.I)]
    if candidates:
        return candidates[0]
    raise ValueError(
        f"Cannot detect title column. Available columns: {list(df.columns)}"
    )


def check_isbd(title: str) -> list[str]:
    """Return list of ISBD pattern labels found in title."""
    if not isinstance(title, str):
        return []
    return [label for label, _, pat in ISBD_PATTERNS if pat.search(title)]


def main(data_path: Path) -> None:
    print(f"Loading {data_path} ...")
    with open(data_path, "rb") as f:
        df = pickle.load(f)

    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")

    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}\n")

    col = detect_title_column(df)
    print(f"Using title column: '{col}'\n")

    titles = df[col].dropna().astype(str).tolist()
    total_titles = len(titles)
    empty = (df[col].isna() | (df[col].astype(str).str.strip() == "")).sum()

    # Analyse
    pattern_counts: Counter = Counter()
    flagged: list[tuple[str, list[str]]] = []

    for title in titles:
        hits = check_isbd(title)
        if hits:
            flagged.append((title, hits))
            pattern_counts.update(hits)

    n_flagged = len(flagged)
    pct = n_flagged / total_titles * 100 if total_titles else 0

    print(f"Rows total:           {len(df):>8}")
    print(f"Empty / null titles:  {empty:>8}")
    print(f"Titles analysed:      {total_titles:>8}")
    print(f"Titles with ISBD:     {n_flagged:>8}  ({pct:.1f}%)")
    print()
    print("Pattern breakdown:")
    print(f"  {'Pattern':<16}  {'Signal':<40}  {'Count':>7}  {'%':>6}")
    print("  " + "-" * 74)
    for label, signal, _ in ISBD_PATTERNS:
        n = pattern_counts[label]
        p = n / total_titles * 100 if total_titles else 0
        print(f"  {label:<16}  {signal:<40}  {n:>7}  {p:>5.1f}%")

    print()
    print("Sample flagged titles (up to 20):")
    for title, hits in flagged[:20]:
        print(f"  [{', '.join(hits)}]  {title!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check ISBD punctuation in DF_DE_TITLES pkl."
    )
    parser.add_argument("--data", type=Path, default=DATA_DEFAULT)
    args = parser.parse_args()
    main(args.data)

#!/usr/bin/env python3
# Purpose:      SR-05 — Sample 200 records where the title ends with a trailing period
#               and classify each into:
#                 ISBD_CLOSE  — genuine ISBD area-close (record ends with a complete
#                               bibliographic string; the period is structural)
#                 ABBREV      — period is part of an abbreviation (Hrsg., Bd., Nr., etc.)
#                 ORDINAL     — period follows a digit (ordinal number, e.g. "1.")
#                 SENTENCE    — period ends a natural-language sentence (not structural)
#                 OTHER       — none of the above
#               Applies automated heuristic classification and writes a review sheet for
#               manual verification. A companion script (evaluate_trailing_period.py)
#               computes precision/recall against the manual true_class column.
# Usage:        python3 scripts/validate_trailing_period.py [--data PATH] [--n N] [--seed N]
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
# Outputs:      data/processed/sr05_trailing_period_sample.csv
# Dependencies: pandas, re
# Assumptions:  DataFrame has 'title' and 'obj_id' columns.

import argparse
import pickle
import re
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
DATA   = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT = ROOT / "data" / "processed" / "sr05_trailing_period_sample.csv"

DDB_URL = "https://ddb.de/item/{}"

# German abbreviations that commonly appear at the end of title strings.
# A trailing period is noise if the string ends with one of these tokens.
ABBREV_RE = re.compile(
    r"(?i)\b("
    r"Hrsg|Hg|Verf|bearb|erg|erw|verb|überarb|Aufl|Ausg|Bd|Bde|Bdn|Teil|Teile|"
    r"Nr|Nrn|Jg|Jgg|H|Heft|Vol|Vols|"
    r"Dr|Prof|St|Abb|Tab|Fig|Taf|"
    r"u\.a|usw|bzw|etc|vgl|enth|ink|inkl|"
    r"Kl|Fol|qu|illustr|ill|"
    r"ca|ca\.|approx|"
    r"Jan|Feb|Mär|Mar|Apr|Mai|Jun|Jul|Aug|Sep|Okt|Oct|Nov|Dez|Dec|"
    r"Mo|Di|Mi|Do|Fr|Sa|So"
    r")\.$",
    re.UNICODE,
)

# Ends with digit + period (ordinal)
ORDINAL_RE = re.compile(r"\d\.$")

# Has structural ISBD markers in addition to trailing period — likely ISBD_CLOSE
STRUCTURAL_RE = re.compile(r"\. -")


def classify(title: str) -> str:
    t = title.strip()
    if not t.endswith("."):
        return "NO_PERIOD"
    if ABBREV_RE.search(t):
        return "ABBREV"
    if ORDINAL_RE.search(t):
        return "ORDINAL"
    if STRUCTURAL_RE.search(t):
        return "ISBD_CLOSE"
    # Heuristic for sentence-end: title is long and ends in a lowercase or
    # common sentence-terminating word
    words = t.rstrip(".").split()
    if len(words) >= 6:
        return "SENTENCE"
    return "OTHER"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default=DATA)
    parser.add_argument("--n", type=int, default=200)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    print("Loading data…")
    with open(args.data, "rb") as f:
        df = pickle.load(f)

    # Pool: titles that end with a period (strip whitespace first)
    pool = df[df["title"].str.strip().str.endswith(".", na=False)].copy()
    print(f"Pool: {len(pool):,} titles end with '.'  ({len(pool)/len(df)*100:.1f}% of corpus)")

    sample = pool.sample(n=min(args.n, len(pool)), random_state=args.seed)

    sample = sample[["obj_id", "title"]].copy()
    sample["ddb_url"]         = sample["obj_id"].apply(DDB_URL.format)
    sample["heuristic_class"] = sample["title"].apply(classify)
    sample["true_class"]      = ""   # reviewer fills in: ISBD_CLOSE / ABBREV / ORDINAL / SENTENCE / OTHER
    sample["notes"]           = ""

    sample.to_csv(OUTPUT, index=False)
    print(f"Wrote {len(sample)} rows to {OUTPUT}")

    dist = sample["heuristic_class"].value_counts()
    print("\nHeuristic class distribution:")
    for cls, cnt in dist.items():
        print(f"  {cls:<15} {cnt:>4}  ({cnt/len(sample)*100:.0f}%)")


if __name__ == "__main__":
    main()

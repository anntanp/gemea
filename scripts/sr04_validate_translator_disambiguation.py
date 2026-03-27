#!/usr/bin/env python3
# Purpose:      Sample 100 f_person-flagged records from sr01_isbd_field_ratings.csv and
#               apply the translator keyword heuristic to split PERSON (author) from
#               TRANSLATOR. Writes a review sheet for manual validation of heuristic
#               precision (SR-04).
# Usage:        python3 scripts/sr04_validate_translator_disambiguation.py [--ratings PATH]
#                   [--output PATH] [--n N] [--seed N]
# Inputs:       data/processed/sr01_isbd_field_ratings.csv — output of rate_isbd_fields.py
# Outputs:      data/processed/sr04_translator_validation_sample.csv — review sheet
# Dependencies: pandas
# Assumptions:  sr01_isbd_field_ratings.csv exists (run sr01_rate_isbd_fields.py first).

import re
import argparse
from pathlib import Path

import pandas as pd

ROOT            = Path(__file__).parent.parent
RATINGS_DEFAULT = ROOT / "data" / "processed" / "sr01_isbd_field_ratings.csv"
OUTPUT_DEFAULT  = ROOT / "data" / "processed" / "sr04_translator_validation_sample.csv"
DDB_ITEM_URL    = "https://ddb.de/item/{}"

# Translator keywords — matched case-insensitively anywhere after ' /'
# Pattern: look for these in the SoR string (text following ' /')
TRANSLATOR_RE = re.compile(
    r"(?i)\b(?:"
    r"über(?:s(?:etzt|etzung|\.)?|tragen(?:en)?)"   # übersetzt, Übers., Übersetzung, übertragen
    r"|aus dem \w+(?:ischen|en|schen)?"              # aus dem Deutschen, aus dem Englischen
    r"|transl(?:ated|ation|\.)?"                     # transl., translated, translation
    r"|hrsg(?:\.|eben)?"                             # Hrsg. (editor — PERSON, not translator, but common FP)
    r"|ed(?:ited|itor|\.)?"                          # ed., edited by
    r"|bearb(?:\.|eitet)?"                           # bearb. (Bearbeitung — adaptor)
    r")\b"
)

# Editor keywords — distinct from translator but also not 'author'
EDITOR_RE = re.compile(
    r"(?i)\b(?:hrsg(?:\.|eben)?|herausgegeben|hg\.|ed(?:ited|itor|\.)?|bearbeitet von)\b"
)


def extract_sor(title: str) -> str:
    """Return the text after the first ' /' in the title, or empty string."""
    idx = title.find(" /")
    return title[idx + 2:].strip() if idx >= 0 else ""


def classify_sor(title: str) -> str:
    """
    Classify the SoR segment as:
      TRANSLATOR  — translator keyword matched
      EDITOR      — editor keyword matched (and no translator keyword)
      PERSON      — no keyword matched; assumed author
      NONE        — no ' /' found
    """
    sor = extract_sor(title)
    if not sor:
        return "NONE"
    if TRANSLATOR_RE.search(sor):
        return "TRANSLATOR"
    if EDITOR_RE.search(sor):
        return "EDITOR"
    return "PERSON"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sample f_person records for TRANSLATOR/PERSON disambiguation review (SR-04)."
    )
    parser.add_argument("--ratings", type=Path, default=RATINGS_DEFAULT)
    parser.add_argument("--output",  type=Path, default=OUTPUT_DEFAULT)
    parser.add_argument("--n",       type=int,  default=100)
    parser.add_argument("--seed",    type=int,  default=42)
    args = parser.parse_args()

    print(f"Loading {args.ratings} ...")
    ratings = pd.read_csv(args.ratings, low_memory=False)
    print(f"  {len(ratings):,} total records")

    # f_person = 1 and heuristic tier (no area separator)
    pool = ratings[(ratings["f_person"] == 1) & (ratings["has_dot_dash"] == False)].copy()
    print(f"  {len(pool):,} heuristic f_person records")

    n = min(args.n, len(pool))
    sample = pool.sample(n=n, random_state=args.seed).copy()

    # Apply heuristic classification
    sample["sor_text"]       = sample["title"].apply(extract_sor)
    sample["heuristic_class"] = sample["title"].apply(classify_sor)

    # Stratify summary
    counts = sample["heuristic_class"].value_counts()
    print(f"\nHeuristic classification in sample (n={n}):")
    for cls, cnt in counts.items():
        print(f"  {cls:<12} {cnt:>4}  ({100*cnt/n:.1f}%)")

    # Reviewer columns
    sample["ddb_url"]        = sample["obj_id"].apply(DDB_ITEM_URL.format)
    sample["true_class"]     = ""   # reviewer fills in: TRANSLATOR / EDITOR / PERSON / OTHER
    sample["notes"]          = ""

    # Column order
    out_cols = [
        "obj_id", "ddb_url", "title", "sor_text", "heuristic_class",
        "silver_tier", "n_fields",
        "true_class", "notes",
    ]
    out_cols = [c for c in out_cols if c in sample.columns]
    sample = sample[out_cols]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sample.to_csv(args.output, index=False)
    print(f"\nWrote {len(sample)} records → {args.output}")
    print(f"""
Review instructions:
  1. Open {args.output}
  2. For each row, check the title and sor_text (text after ' /')
  3. In 'true_class', enter one of: TRANSLATOR / EDITOR / PERSON / OTHER
     - TRANSLATOR: the SoR names a translator
     - EDITOR: the SoR names an editor or adaptor (Hrsg., bearb.)
     - PERSON: the SoR names an author / creator
     - OTHER: the ' /' is not a SoR at all (false positive from SR-03)
  4. Compare true_class to heuristic_class to assess precision
  5. Use 'notes' for observations
""")


if __name__ == "__main__":
    main()

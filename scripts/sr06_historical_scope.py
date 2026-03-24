#!/usr/bin/env python3
# Purpose:      SR-06 — Estimate what proportion of historical (pre-1800) tier-0 records
#               are Latin or Early Modern German, to inform NER model selection and
#               gold set design. Samples 200 records from two strata:
#                 - Leichenpredigt|Monografie (funerary sermons, almost all pre-1750)
#                 - Monografie with dates < 1800
#               Applies a heuristic classifier (LATIN / EARLY_MODERN_DE / GERMAN / OTHER)
#               and writes a review sheet for manual verification.
# Usage:        python3 scripts/sr06_historical_scope.py [--data PATH] [--ratings PATH]
#                   [--n N] [--seed N]
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
#               data/processed/isbd_field_ratings.csv
# Outputs:      data/processed/sr06_historical_sample.csv
# Dependencies: pandas, re
# Assumptions:  isbd_field_ratings.csv exists (run sr01_rate_isbd_fields.py first).

import argparse
import pickle
import re
from pathlib import Path

import pandas as pd

ROOT    = Path(__file__).parent.parent
DATA    = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
RATINGS = ROOT / "data" / "processed" / "isbd_field_ratings.csv"
OUTPUT  = ROOT / "data" / "processed" / "sr06_historical_sample.csv"
DDB_URL = "https://ddb.de/item/{}"

# ── Language heuristics ────────────────────────────────────────────────────────

# Latin indicators: distinctive Latin words and endings unlikely in German.
LATIN_WORDS = re.compile(
    r"\b("
    r"Anno|Domini|Christi|Jesu|Dei|Deo|Domino|"
    r"sive|seu|vel|atque|nec|dum|quod|quae|quem|quibus|"
    r"filius|filii|filia|filiae|filium|"
    r"oratio|orationis|dissertatio|dissertatione|"
    r"praeses|respondens|moderante|praeside|"
    r"doctor|doctore|professore|"
    r"academiae|academia|universitatis|"
    r"venerabilis|reverendus|amplissimus|clarissimus|"
    r"opera|operi|auctoris|auctore"
    r")\b",
    re.IGNORECASE,
)
# Latin morphological endings on content words (avoid false positives on German -us names)
LATIN_ENDINGS = re.compile(r"\b\w{5,}(orum|ibus|atio|tione|tatis|tate|eram|erunt)\b")

# Early Modern German spelling markers
EARLY_MODERN_DE = re.compile(
    r"\b("
    r"vnd|vnnd|vndt|vnndt|"         # und variants
    r"sey|seyn|seind|"               # sein variants
    r"derer|deren|"                  # genitive article variants
    r"deß|deß|auff|"                 # historical orthography
    r"Gott(?:es|es)|Christi|"       # religious German
    r"Jungfrau|Jungfraw|"
    r"Herr(?:n|en)|"
    r"Bürger|Bürgern"
    r")\b"
    r"|[ck]h\w+",                    # -kh- / -ch- historical clusters
    re.IGNORECASE,
)


def classify_language(title: str, year: float) -> tuple[str, str]:
    """Return (heuristic_class, notes)."""
    t = str(title)

    latin_word_hits = LATIN_WORDS.findall(t)
    latin_ending_hits = LATIN_ENDINGS.findall(t)
    total_latin = len(latin_word_hits) + len(latin_ending_hits)

    if total_latin >= 2:
        evidence = ", ".join((latin_word_hits + latin_ending_hits)[:4])
        return "LATIN", f"Latin indicators: {evidence}"

    if total_latin == 1:
        evidence = (latin_word_hits + latin_ending_hits)[0]
        # Single hit — ambiguous; lean on year
        if not pd.isna(year) and year < 1600:
            return "LATIN", f"Single Latin indicator ({evidence}) + pre-1600 year"

    early_hits = EARLY_MODERN_DE.findall(t)
    if early_hits or (not pd.isna(year) and year < 1700):
        note = f"Early modern markers: {early_hits[:3]}" if early_hits else f"Year {int(year)} < 1700"
        return "EARLY_MODERN_DE", note

    if not pd.isna(year) and year < 1800:
        return "GERMAN", f"Year {int(year)}, no early modern markers"

    return "OTHER", "no historical signal"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",    default=DATA)
    parser.add_argument("--ratings", default=RATINGS)
    parser.add_argument("--n",       type=int, default=200)
    parser.add_argument("--seed",    type=int, default=42)
    args = parser.parse_args()

    print("Loading data…")
    with open(args.data, "rb") as f:
        df = pickle.load(f)

    ratings = pd.read_csv(args.ratings, usecols=["obj_id", "silver_tier"])
    df = df.merge(ratings, on="obj_id", how="left")

    # Numeric year
    df["year_num"] = pd.to_numeric(df["dates"], errors="coerce")

    # Stratum A: Leichenpredigt
    leichen = df[df["dc_type"].str.contains("Leichenpredigt", na=False)]

    # Stratum B: Monografie pre-1800 (excluding Leichenpredigt)
    mono_pre1800 = df[
        (df["dc_type"] == "Monografie") & (df["year_num"] < 1800)
    ]

    print(f"Stratum A — Leichenpredigt:        {len(leichen):>8,}  "
          f"(tier-0: {(leichen.silver_tier == 0).sum():,})")
    print(f"Stratum B — Monografie pre-1800:   {len(mono_pre1800):>8,}  "
          f"(tier-0: {(mono_pre1800.silver_tier == 0).sum():,})")

    # Sample equally from each stratum (n//2 each)
    n_each = args.n // 2
    sample_a = leichen.sample(n=min(n_each, len(leichen)),
                              random_state=args.seed).copy()
    sample_b = mono_pre1800.sample(n=min(n_each, len(mono_pre1800)),
                                   random_state=args.seed).copy()

    sample_a["stratum"] = "Leichenpredigt"
    sample_b["stratum"] = "Monografie_pre1800"

    sample = pd.concat([sample_a, sample_b], ignore_index=True)

    cols = ["obj_id", "title", "dc_type", "dates", "silver_tier", "stratum"]
    sample = sample[cols].copy()
    sample["ddb_url"] = sample["obj_id"].apply(DDB_URL.format)

    results = sample.apply(
        lambda r: classify_language(r["title"], pd.to_numeric(r["dates"], errors="coerce")),
        axis=1,
    )
    sample["heuristic_class"] = [r[0] for r in results]
    sample["notes"]            = [r[1] for r in results]
    sample["true_class"]       = ""   # reviewer fills: LATIN / EARLY_MODERN_DE / GERMAN / OTHER

    sample.to_csv(OUTPUT, index=False)
    print(f"\nWrote {len(sample)} rows → {OUTPUT}")

    print("\nHeuristic class distribution (overall):")
    dist = sample["heuristic_class"].value_counts()
    for cls, cnt in dist.items():
        print(f"  {cls:<20} {cnt:>4}  ({cnt/len(sample)*100:.0f}%)")

    print("\nBy stratum:")
    print(sample.groupby(["stratum", "heuristic_class"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()

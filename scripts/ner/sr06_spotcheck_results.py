#!/usr/bin/env python3
# Purpose:      SR-06 — Print spot-check tables from sr06_historical_evaluated.csv:
#               true LATIN records, LATIN false-positive patterns, EARLY_MODERN_DE
#               false-positive patterns, and per-stratum true-class distribution.
# Usage:        python3 scripts/sr06_spotcheck_results.py [--evaluated PATH]
# Inputs:       data/processed/sr06_historical_evaluated.csv
# Outputs:      stdout
# Dependencies: pandas

import argparse
from pathlib import Path

import pandas as pd

ROOT      = Path(__file__).parent.parent
EVALUATED = ROOT / "data" / "processed" / "sr06_historical_evaluated.csv"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evaluated", default=EVALUATED)
    args = parser.parse_args()

    df = pd.read_csv(args.evaluated)

    # ── True LATIN records ────────────────────────────────────────────────────
    print("=== True LATIN records ===")
    latin = df[df["true_class"] == "LATIN"]
    for _, r in latin.iterrows():
        print(f"  [{r['stratum']}]  {r['dates']}")
        print(f"  {str(r['title'])[:120]}")
        print(f"  evidence: {r['true_notes']}")
        print()

    # ── LATIN false positives — grouped by triggering pattern ─────────────────
    print("=== LATIN false positives (heuristic=LATIN, true≠LATIN) ===")
    fps = df[(df["heuristic_class"] == "LATIN") & (df["true_class"] != "LATIN")]
    for _, r in fps.iterrows():
        trigger = r["notes"]
        print(f"  trigger: {str(trigger)[:80]}")
        print(f"  true:    {r['true_class']}")
        print(f"  title:   {str(r['title'])[:100]}")
        print()

    # ── EARLY_MODERN_DE false positives ──────────────────────────────────────
    print("=== EARLY_MODERN_DE false positives (heuristic=EARLY_MODERN_DE, true=GERMAN) ===")
    em_fps = df[(df["heuristic_class"] == "EARLY_MODERN_DE") & (df["true_class"] == "GERMAN")]
    for _, r in em_fps.iterrows():
        print(f"  trigger: {str(r['notes'])[:80]}")
        print(f"  title:   {str(r['title'])[:100]}")
        print()

    # ── Per-stratum true-class distribution ───────────────────────────────────
    print("=== Per-stratum true-class distribution ===")
    print(df.groupby(["stratum", "true_class"]).size().unstack(fill_value=0).to_string())
    print()

    # ── Year distribution of true GERMAN records ──────────────────────────────
    print("=== Year distribution of true GERMAN records ===")
    df["year_num"] = pd.to_numeric(df["dates"], errors="coerce")
    german = df[df["true_class"] == "GERMAN"]
    bins = [0, 1600, 1650, 1700, 1750, 1800]
    labels = ["pre-1600", "1600-1650", "1650-1700", "1700-1750", "1750-1800"]
    german_copy = german.copy()
    german_copy["decade"] = pd.cut(german_copy["year_num"], bins=bins, labels=labels, right=False)
    print(german_copy["decade"].value_counts().sort_index().to_string())


if __name__ == "__main__":
    main()

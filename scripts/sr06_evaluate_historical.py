#!/usr/bin/env python3
# Purpose:      SR-06 — Evaluate heuristic accuracy for historical/Latin title classification.
#               Applies a stricter true-class annotation to sr06_historical_sample.csv,
#               computes per-class precision/recall vs. the heuristic, and writes a
#               confusion-matrix summary to stdout.
# Usage:        python3 scripts/sr06_evaluate_historical.py [--sample PATH] [--out PATH]
# Inputs:       data/processed/sr06_historical_sample.csv
# Outputs:      data/processed/sr06_historical_evaluated.csv (with true_class filled)
# Dependencies: pandas, re
# Assumptions:  sr06_historical_scope.py has been run first.
#
# True-class annotation rationale
# --------------------------------
# The heuristic in sr06_historical_scope.py uses a 2-hit threshold for LATIN and
# year < 1700 as a fallback for EARLY_MODERN_DE.  Some terms ("Christi", "Anno",
# "Doctor") appear in both Latin and German religious texts, so a single hit is
# unreliable. The true-class annotator applies stricter rules:
#
#   LATIN         — ≥2 *unambiguous* Latin grammar/structural words (sive, seu,
#                   vel, atque, dum, quod, quae, quibus, filius, filii, filia,
#                   oratio, dissertatio, praeses, respondens, academiae,
#                   universitatis, auctoris), OR ≥2 Latin endings (-orum, -ibus,
#                   -atio, -tione, -tatis, -tate, -eram, -erunt), OR 1 grammar
#                   word + 1 ending.  "Christi"/"Anno"/"Doctor" alone do NOT
#                   qualify; they require a second unambiguous signal.
#
#   EARLY_MODERN_DE — explicit early-modern spelling markers (vnd, seyn, seind,
#                   deß, auff, Jungfraw, etc.) OR year < 1650.  Year 1650-1699
#                   without markers → GERMAN (more conservative than heuristic's
#                   year < 1700 threshold).
#
#   GERMAN        — year < 1800, no strong Latin or early-modern markers.
#   OTHER         — no historical signal (year missing or ≥ 1800).

import argparse
import re
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
SAMPLE = ROOT / "data" / "processed" / "sr06_historical_sample.csv"
OUTPUT = ROOT / "data" / "processed" / "sr06_historical_evaluated.csv"

# ── True-class annotation patterns ────────────────────────────────────────────

# Unambiguous Latin grammar / structural words (not shared with German)
LATIN_GRAMMAR = re.compile(
    r"\b("
    r"sive|seu|vel|atque|nec(?!\w)|dum\b|quod|quae|quem|quibus|"
    r"filius|filii|filia|filiae|filium|"
    r"oratio|orationis|dissertatio|dissertatione|"
    r"praeses|respondens|moderante|praeside|"
    r"academiae|academia|universitatis|"
    r"venerabilis|reverendus|amplissimus|clarissimus|"
    r"opera\b|operi|auctoris|auctore"
    r")\b",
    re.IGNORECASE,
)

# Ambiguous Latin content words (also used in German religious/academic text)
LATIN_CONTENT = re.compile(
    r"\b(Anno|Domini|Christi|Jesu|Dei|Deo|Domino|doctor|doctore|professore)\b",
    re.IGNORECASE,
)

# Latin morphological endings on content words
LATIN_ENDINGS = re.compile(r"\b\w{5,}(orum|ibus|atio|tione|tatis|tate|eram|erunt)\b")

# Explicit early-modern German spelling markers (not year-based)
EARLY_MODERN_MARKERS = re.compile(
    r"\b("
    r"vnd|vnnd|vndt|vnndt|"
    r"sey\b|seyn\b|seind\b|"
    r"derer|deß|auff|"
    r"Jungfrau|Jungfraw|"
    r"Bürger(?:in|n|meister)?"
    r")\b"
    r"|[ck]h\w{3,}",          # -kh-/-ch- historical clusters (min 4 chars to avoid noise)
    re.IGNORECASE,
)


def true_class(title: str, year: float) -> tuple[str, str]:
    """Stricter true-class annotation — see module docstring."""
    t = str(title)

    grammar_hits  = LATIN_GRAMMAR.findall(t)
    content_hits  = LATIN_CONTENT.findall(t)
    ending_hits   = LATIN_ENDINGS.findall(t)

    n_grammar = len(grammar_hits)
    n_content = len(content_hits)
    n_ending  = len(ending_hits)

    # LATIN: need ≥2 unambiguous grammar words, OR ≥2 endings,
    #        OR 1 grammar + 1 ending,  OR 3+ total signals including content
    is_latin = (
        n_grammar >= 2
        or n_ending >= 2
        or (n_grammar >= 1 and n_ending >= 1)
        or (n_grammar + n_content + n_ending >= 3 and n_grammar + n_ending >= 1)
    )
    if is_latin:
        evidence = (grammar_hits + ending_hits + content_hits)[:4]
        return "LATIN", f"True LATIN: {', '.join(str(e) for e in evidence)}"

    # EARLY_MODERN_DE: requires explicit spelling markers, OR year < 1650
    marker_hits = EARLY_MODERN_MARKERS.findall(t)
    if marker_hits:
        return "EARLY_MODERN_DE", f"Spelling markers: {[m for m in marker_hits if m][:3]}"
    if not pd.isna(year) and year < 1650:
        return "EARLY_MODERN_DE", f"Year {int(year)} < 1650 (no explicit markers)"

    # GERMAN: year < 1800, no strong signals
    if not pd.isna(year) and year < 1800:
        return "GERMAN", f"Year {int(year)}, no early-modern markers"

    return "OTHER", "no historical signal"


def confusion_matrix(df: pd.DataFrame) -> pd.DataFrame:
    classes = sorted(set(df["heuristic_class"]) | set(df["true_class"]))
    mat = pd.DataFrame(0, index=classes, columns=classes)
    for _, row in df.iterrows():
        mat.loc[row["true_class"], row["heuristic_class"]] += 1
    mat.index.name   = "true \\ heuristic"
    return mat


def per_class_metrics(df: pd.DataFrame) -> pd.DataFrame:
    classes = sorted(set(df["heuristic_class"]) | set(df["true_class"]))
    rows = []
    for cls in classes:
        tp = ((df["heuristic_class"] == cls) & (df["true_class"] == cls)).sum()
        fp = ((df["heuristic_class"] == cls) & (df["true_class"] != cls)).sum()
        fn = ((df["heuristic_class"] != cls) & (df["true_class"] == cls)).sum()
        prec   = tp / (tp + fp) if (tp + fp) > 0 else float("nan")
        recall = tp / (tp + fn) if (tp + fn) > 0 else float("nan")
        f1     = 2 * prec * recall / (prec + recall) if (prec + recall) > 0 else float("nan")
        rows.append({"class": cls, "TP": tp, "FP": fp, "FN": fn,
                     "precision": round(prec, 3), "recall": round(recall, 3),
                     "F1": round(f1, 3)})
    return pd.DataFrame(rows).set_index("class")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default=SAMPLE)
    parser.add_argument("--out",    default=OUTPUT)
    args = parser.parse_args()

    df = pd.read_csv(args.sample)
    df["year_num"] = pd.to_numeric(df["dates"], errors="coerce")

    results = df.apply(
        lambda r: true_class(r["title"], r["year_num"]), axis=1
    )
    df["true_class"]   = [r[0] for r in results]
    df["true_notes"]   = [r[1] for r in results]

    df.to_csv(args.out, index=False)
    print(f"Wrote {len(df)} rows → {args.out}\n")

    # ── Overall agreement ─────────────────────────────────────────────────────
    n = len(df)
    n_agree = (df["heuristic_class"] == df["true_class"]).sum()
    print(f"Overall agreement: {n_agree}/{n}  ({n_agree/n*100:.1f}%)\n")

    # ── Confusion matrix ──────────────────────────────────────────────────────
    print("Confusion matrix (rows = true, cols = heuristic):")
    print(confusion_matrix(df).to_string())
    print()

    # ── Per-class metrics ─────────────────────────────────────────────────────
    print("Per-class metrics:")
    print(per_class_metrics(df).to_string())
    print()

    # ── Heuristic-only distribution (for reference) ───────────────────────────
    print("Heuristic class distribution:")
    for cls, cnt in df["heuristic_class"].value_counts().items():
        print(f"  {cls:<20} {cnt:>4}  ({cnt/n*100:.0f}%)")
    print()

    # ── True-class distribution ───────────────────────────────────────────────
    print("True class distribution:")
    for cls, cnt in df["true_class"].value_counts().items():
        print(f"  {cls:<20} {cnt:>4}  ({cnt/n*100:.0f}%)")
    print()

    # ── Discrepancies ─────────────────────────────────────────────────────────
    disc = df[df["heuristic_class"] != df["true_class"]][
        ["obj_id", "title", "heuristic_class", "true_class", "notes", "true_notes", "stratum"]
    ]
    if len(disc):
        print(f"Discrepancies ({len(disc)} rows):")
        for _, row in disc.iterrows():
            print(f"\n  [{row['stratum']}]  heuristic={row['heuristic_class']} → true={row['true_class']}")
            print(f"  title:       {str(row['title'])[:120]}")
            print(f"  heuristic:   {row['notes']}")
            print(f"  true:        {row['true_notes']}")
    else:
        print("No discrepancies — perfect agreement.")


if __name__ == "__main__":
    main()

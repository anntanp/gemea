#!/usr/bin/env python3
# Purpose:      SR-05 — Annotate sr05_trailing_period_sample.csv with true_class and notes.
#               Applies rule-based classification to determine whether each trailing
#               period is a genuine ISBD area-close or a noise source.
#
#               true_class values:
#                 ISBD_CLOSE  — period is a structural ISBD area-close marker (appears
#                               after a complete bibliographic description area)
#                 ABBREV      — period belongs to a German/Latin abbreviation token
#                 ORDINAL     — period follows an ordinal number (digit or Roman numeral)
#                 NATURAL     — period ends a natural-language sentence or chapter title
#                 NOISE       — index entry, single word, fragment, page reference
#
# Usage:        python3 scripts/sr05_trailing_period_review.py [--input PATH] [--output PATH]
# Inputs:       data/processed/sr05_trailing_period_sample.csv
# Outputs:      data/processed/sr05_trailing_period_sample.csv (true_class + notes filled)
# Dependencies: pandas, re

import re
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "data" / "processed" / "sr05_trailing_period_sample.csv"
OUTPUT = INPUT  # overwrite in place

# ── Pattern library ────────────────────────────────────────────────────────────

# Structural: `. -` area separator present → ISBD_CLOSE
STRUCTURAL_RE = re.compile(r"\. -")

# Publication area close: ends with 4-digit year + optional whitespace + period
# e.g. "London : Verlag, 1900." or "1923."
YEAR_CLOSE_RE = re.compile(r"\b1[4-9]\d{2}\s*\.$|20[012]\d\s*\.$")

# Abbreviation list (word must immediately precede final period)
ABBREV_WORDS = {
    "hrsg", "hg", "hgg", "verf", "bearb", "erg", "erw", "verb", "überarb",
    "aufl", "ausg", "bd", "bde", "bdn", "teil", "teile",
    "nr", "nrn", "jg", "jgg", "heft", "vol", "vols", "no",
    "dr", "prof", "st", "abb", "tab", "fig", "taf",
    "usw", "bzw", "etc", "vgl", "enth", "inkl", "incl",
    "ill", "illustr", "ca",
    "jan", "feb", "mär", "mar", "apr", "mai", "jun",
    "jul", "aug", "sep", "okt", "oct", "nov", "dez", "dec",
}

def last_token(title: str) -> str:
    """Return the last whitespace-separated token before the trailing period."""
    t = title.strip().rstrip(".")
    parts = t.split()
    return parts[-1].lower().rstrip(".") if parts else ""

# Roman numeral ordinal at end: e.g. "XXI.", "IV.", "Trinitatis. - ..."
ROMAN_RE = re.compile(r"\b[IVXLCDM]+\.$", re.IGNORECASE)

# Arabic digit ordinal at end: "No. 27.", "§ 3.", "3.", "1915."
# (but exclude 4-digit year which is handled by YEAR_CLOSE_RE)
DIGIT_ORD_RE = re.compile(r"\b(?!\d{4}\b)\d+\.$")

# Noise patterns: single-word entries, index terms, page refs
NOISE_RE = re.compile(
    r"^\s*\w+\.\s*$"                        # single word: "Inhalt.", "Vorerinnerung."
    r"|^\s*\d+[-–]\d+.*\.$"                 # page range: "783-784, Vorwort."
    r"|^\s*[§¶]\s*\d+"                       # paragraph marker
)

# Sentence indicator: contains a verb-like suffix or is clearly prose
# Simple proxy: ≥8 tokens and does NOT contain ` :` or ` /` or ` =`
def looks_like_sentence(title: str) -> bool:
    tokens = title.split()
    has_isbd = re.search(r" :|  /| =", title)
    return len(tokens) >= 8 and not has_isbd

# ── Classifier ─────────────────────────────────────────────────────────────────

def classify(title: str) -> tuple[str, str]:
    """Return (true_class, notes)."""
    t = title.strip()

    if not t.endswith("."):
        return "NO_PERIOD", "title does not end with period"

    # 1. Structural tier (has `. -`) → always ISBD_CLOSE
    if STRUCTURAL_RE.search(t):
        return "ISBD_CLOSE", "contains `. -` area separator"

    # 2. Ends with year — but only if paired with ` :` or ` /` (ISBD title area markers),
    #    suggesting a complete bibliographic description. A bare year at the end of a
    #    string is more often a date expression (newspaper issue date, event date, etc.)
    #    than a publication area close.
    if YEAR_CLOSE_RE.search(t) and re.search(r" :|  /", t):
        return "ISBD_CLOSE", "trailing period after year with ISBD title-area markers"
    if YEAR_CLOSE_RE.search(t):
        return "NATURAL", "date expression ending with year — not publication area close"

    # 3. Known abbreviation as last token
    lt = last_token(t)
    if lt in ABBREV_WORDS:
        return "ABBREV", f"trailing abbreviation token: {lt}."

    # 4. Roman numeral ordinal
    if ROMAN_RE.search(t):
        return "ORDINAL", "trailing Roman numeral ordinal"

    # 5. Arabic digit ordinal (non-year)
    if DIGIT_ORD_RE.search(t):
        return "ORDINAL", "trailing Arabic numeral ordinal"

    # 6. Noise: single-word entry, page reference, fragment
    if NOISE_RE.match(t):
        return "NOISE", "single-word or fragment entry"

    # 7. Long natural-language string
    if looks_like_sentence(t):
        return "NATURAL", "long prose string (≥8 tokens, no ISBD markers)"

    # 8. Shorter strings without clear signal → NATURAL (chapter title / heading)
    return "NATURAL", "short title or heading ending with period"


def main():
    df = pd.read_csv(INPUT)
    results = df["title"].apply(lambda t: classify(str(t)))
    df["true_class"] = [r[0] for r in results]
    df["notes"]      = [r[1] for r in results]
    df.to_csv(OUTPUT, index=False)
    print(f"Annotated {len(df)} rows → {OUTPUT}")

    dist = df["true_class"].value_counts()
    total = len(df)
    print("\nTrue class distribution:")
    for cls, cnt in dist.items():
        print(f"  {cls:<15} {cnt:>4}  ({cnt/total*100:.0f}%)")

    tp_isbd = (df["true_class"] == "ISBD_CLOSE").sum()
    fp = total - tp_isbd
    print(f"\nFP rate (non-ISBD_CLOSE / total): {fp}/{total} = {fp/total*100:.0f}%")
    print(f"TP rate (ISBD_CLOSE): {tp_isbd}/{total} = {tp_isbd/total*100:.0f}%")


if __name__ == "__main__":
    main()

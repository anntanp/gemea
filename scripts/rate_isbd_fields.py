#!/usr/bin/env python3
# Purpose:      Rate each DDB title string for the likely presence of bibliographic fields
#               (TITLE, OTHER_TITLE, PERSON, PARALLEL_TITLE, EDITION, PUBLISHER, PLACE,
#               YEAR, SERIES, VOLUME) using ISBD punctuation rules. Assigns a silver_tier
#               to each record for NER training data selection. Optionally writes N
#               concrete examples per ISBD pattern for documentation.
# Usage:        python3 scripts/rate_isbd_fields.py [--data PATH] [--output PATH]
#                   [--examples N] [--batch-size N]
# Inputs:       data/DF_DE_TITLES_20240125b.pkl — DataFrame with obj_id + title columns
# Outputs:      data/processed/isbd_field_ratings.csv — field flags + silver_tier per record
#               data/processed/isbd_examples.csv       — N examples per pattern (--examples)
# Dependencies: pandas
# Assumptions:  DataFrame has 'obj_id' and 'title' columns.
#               data/processed/ directory will be created if absent.

import re
import argparse
import pickle
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT = Path(__file__).parent.parent
DATA_DEFAULT = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_DEFAULT = ROOT / "data" / "processed" / "isbd_field_ratings.csv"
EXAMPLES_DEFAULT = ROOT / "data" / "processed" / "isbd_examples.csv"
DDB_ITEM_URL = "https://ddb.de/item/{}"

# ---------------------------------------------------------------------------
# Pre-compiled regex patterns
# ---------------------------------------------------------------------------

# ISBD area separator ". -" (space · period · space · hyphen · space)
RE_AREA_SEP = re.compile(r"\. - ")

# Title-area signals (applied to area[0] for structural; whole string for heuristic)
RE_OTHER_TITLE = re.compile(r" :")   # subtitle / other title information
RE_PERSON      = re.compile(r" /")   # statement of responsibility
RE_PARALLEL    = re.compile(r" =")   # parallel title (often a translation)

# Edition keywords (case-insensitive)
RE_EDITION = re.compile(
    r"(?i)\b(?:\d+\.?\s*)?"
    r"(?:Aufl(?:age)?|Ausg(?:abe)?|[Ee]d(?:ition)?|[Rr]ev(?:ised)?|"
    r"überarb(?:eitet)?|[Ee]rw(?:eiterte)?|[Vv]erb(?:esserte)?|"
    r"Neuausg(?:abe)?|neu\s*bearb)"
    r"\b"
)

# Year: 1400–2029 (broad range for historical DDB items)
RE_YEAR = re.compile(r"\b(?:1[4-9]\d{2}|20[012]\d)\b")

# Publication imprint: " : " separating place from publisher
RE_IMPRINT = re.compile(r"\w.+ : \w")

# Publisher hint for heuristic tier (whole-string)
RE_PUBLISHER_HINT = re.compile(r"(?i)\bVerlag\b|\bPress\b|\bEditore\b")

# Compound SoR: " /" followed by content then " ;" outside parentheses
# Distinguishes "Titel / Autor A ; Autor B" (SoR) from "(Series ; Bd. 3)" (series)
RE_PERSON_COMPOUND = re.compile(r" /[^(]+;")

# Series: parenthetical block containing a semicolon + digit (Series ; N)
RE_SERIES = re.compile(r"\([^)]+;\s*[^)]*\d[^)]*\)")
# Simpler series: any substantial parenthetical at end of string (≥5 chars)
RE_SERIES_SIMPLE = re.compile(r"\([^)]{5,}\)\s*$")

# Volume / part indicators
RE_VOLUME = re.compile(
    r"(?i)\b(?:Bd(?:e)?|Teil|Tl|Vol|Heft|Nr|Lfg|Lieferung|Band)\.\s*\d+"
)

# Ellipsis / truncation (for examples output only)
RE_ELLIPSIS = re.compile(r"\.\.\.|…")

# Square brackets: supplied / inferred data (for examples output only)
RE_BRACKETS = re.compile(r"\[.+?\]")

# Trailing area-end period (for examples output only)
RE_TRAILING_DOT = re.compile(r"[^.]\.$")

# ---------------------------------------------------------------------------
# Field columns (output schema)
# ---------------------------------------------------------------------------

FIELD_COLS = [
    "f_title",            # always 1
    "f_other_title",      # ` :` — subtitle / other title info
    "f_person",           # ` /` — statement of responsibility
    "f_person_compound",  # ` / ... ;` — compound SoR (multiple contributors)
    "f_parallel",         # ` =` — parallel title / translation
    "f_edition",          # edition keyword
    "f_place",            # place of publication
    "f_publisher",        # publisher name
    "f_year",             # publication year
    "f_series",           # series block
    "f_volume",           # volume / part number
]

# ISBD patterns used for example sampling (label → pattern, description)
EXAMPLE_PATTERNS = [
    ("space_colon",    RE_OTHER_TITLE,    "Other title information ( : )"),
    ("space_slash",    RE_PERSON,         "Statement of responsibility ( / )"),
    ("space_equals",   RE_PARALLEL,       "Parallel title ( = )"),
    ("space_semi",        re.compile(r" ;"),  "Subsequent SoR / series ( ; )"),
    ("person_compound",   RE_PERSON_COMPOUND, "Compound SoR ( / ... ; )"),
    ("ellipsis",       RE_ELLIPSIS,       "Ellipsis / truncation (… or ...)"),
    ("sq_brackets",    RE_BRACKETS,       "Supplied / inferred data ([ ])"),
    ("trailing_dot",   RE_TRAILING_DOT,   "Area-end period (.)"),
    ("area_sep",       RE_AREA_SEP,       "Area separator (. -)"),
    ("year",           RE_YEAR,           "Publication year"),
    ("edition",        RE_EDITION,        "Edition statement"),
    ("series",         RE_SERIES,         "Series (parenthetical + semicolon)"),
    ("volume",         RE_VOLUME,         "Volume / part number"),
]

# ---------------------------------------------------------------------------
# Rating logic — fully vectorised
# ---------------------------------------------------------------------------

def rate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ISBD-based field detection to a DataFrame with 'obj_id' and 'title'.
    Returns a new DataFrame with field flags, n_fields, has_dot_dash, silver_tier.

    Two-tier detection:
      Structural (has_dot_dash=True): split on '. -'; parse each area specifically.
      Heuristic  (has_dot_dash=False): whole-string patterns; more conservative.
    """
    titles = df["title"].fillna("").astype(str)

    out = pd.DataFrame({"obj_id": df["obj_id"], "title": df["title"]})

    # --- Structural flag ---
    out["has_dot_dash"] = titles.str.contains(RE_AREA_SEP, regex=True, na=False)

    # --- f_title: always present ---
    out["f_title"] = 1

    # --- Title-area signals ---
    # For structural records, limit to the portion before the first ". -"
    title_area = titles.str.split(r"\. - ", n=1, regex=True).str[0]
    rest_area  = titles.str.split(r"\. - ", n=1, regex=True).str[1].fillna("")

    structural = out["has_dot_dash"]

    # OTHER_TITLE: " :" in title area (structural) or whole string (heuristic)
    out["f_other_title"] = (
        structural  & title_area.str.contains(RE_OTHER_TITLE, regex=True, na=False) |
        ~structural & titles.str.contains(RE_OTHER_TITLE, regex=True, na=False)
    ).astype(int)

    # PERSON: " /" in title area (structural) or whole string (heuristic)
    out["f_person"] = (
        structural  & title_area.str.contains(RE_PERSON, regex=True, na=False) |
        ~structural & titles.str.contains(RE_PERSON, regex=True, na=False)
    ).astype(int)

    # PERSON_COMPOUND: " / ... ;" outside parentheses — compound SoR
    # Fires on "Titel / Autor A ; Autor B" but not "(Series ; Bd. 3)"
    # Applied to title_area (structural) or whole string (heuristic)
    out["f_person_compound"] = (
        structural  & title_area.str.contains(RE_PERSON_COMPOUND, regex=True, na=False) |
        ~structural & titles.str.contains(RE_PERSON_COMPOUND, regex=True, na=False)
    ).astype(int)

    # PARALLEL: " =" in title area (structural) or whole string (heuristic)
    out["f_parallel"] = (
        structural  & title_area.str.contains(RE_PARALLEL, regex=True, na=False) |
        ~structural & titles.str.contains(RE_PARALLEL, regex=True, na=False)
    ).astype(int)

    # --- Manifestation-area signals ---

    # EDITION: keyword in rest_area (structural) or whole string (heuristic)
    out["f_edition"] = (
        structural  & rest_area.str.contains(RE_EDITION, regex=True, na=False) |
        ~structural & titles.str.contains(RE_EDITION, regex=True, na=False)
    ).astype(int)

    # YEAR: in rest_area (structural) or whole string (heuristic)
    out["f_year"] = (
        structural  & rest_area.str.contains(RE_YEAR, regex=True, na=False) |
        ~structural & titles.str.contains(RE_YEAR, regex=True, na=False)
    ).astype(int)

    # PLACE + PUBLISHER: imprint " : " pattern in rest_area (structural only)
    # For heuristic: publisher hint keyword ("Verlag" etc.) → publisher only
    has_imprint      = structural & rest_area.str.contains(RE_IMPRINT, regex=True, na=False)
    has_pub_hint     = ~structural & titles.str.contains(RE_PUBLISHER_HINT, regex=True, na=False)

    out["f_place"]     = has_imprint.astype(int)
    out["f_publisher"] = (has_imprint | has_pub_hint).astype(int)

    # SERIES: parenthetical with semicolon+digit in rest_area (structural)
    #         or whole string (heuristic — same pattern but more conservative)
    out["f_series"] = (
        structural  & rest_area.str.contains(RE_SERIES, regex=True, na=False) |
        ~structural & titles.str.contains(RE_SERIES, regex=True, na=False)
    ).astype(int)

    # VOLUME: part/volume keyword anywhere
    out["f_volume"] = titles.str.contains(RE_VOLUME, regex=True, na=False).astype(int)

    # --- Summary ---
    out["n_fields"] = out[FIELD_COLS].sum(axis=1)

    # --- Silver tier ---
    manifestation = out[["f_edition", "f_place", "f_publisher", "f_year", "f_series"]].any(axis=1)

    tier2 = out["has_dot_dash"] & (out["f_person"] == 1) & manifestation
    tier1 = ~tier2 & ((out["n_fields"] >= 3) | ((out["f_person"] == 1) & (out["f_year"] == 1)))

    out["silver_tier"] = 0
    out.loc[tier1, "silver_tier"] = 1
    out.loc[tier2, "silver_tier"] = 2

    return out


# ---------------------------------------------------------------------------
# Example sampling
# ---------------------------------------------------------------------------

def sample_examples(rated: pd.DataFrame, n: int) -> pd.DataFrame:
    """
    For each ISBD pattern, sample up to n records that match it.
    Returns a DataFrame with obj_id, title, ddb_url, pattern_label, pattern_desc,
    and all f_* columns.
    """
    rows = []
    titles = rated["title"].fillna("").astype(str)

    for label, pattern, desc in EXAMPLE_PATTERNS:
        mask = titles.str.contains(pattern, regex=True, na=False)
        sample = rated[mask].head(n).copy()
        sample["pattern_label"] = label
        sample["pattern_desc"]  = desc
        rows.append(sample)

    examples = pd.concat(rows, ignore_index=True)
    examples["ddb_url"] = examples["obj_id"].apply(DDB_ITEM_URL.format)
    # Reorder for readability
    front = ["pattern_label", "pattern_desc", "obj_id", "ddb_url", "title"]
    rest  = [c for c in examples.columns if c not in front]
    return examples[front + rest]


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def print_summary(rated: pd.DataFrame) -> None:
    total = len(rated)

    print(f"\n{'='*60}")
    print(f"  ISBD Field Ratings — Summary")
    print(f"{'='*60}")
    print(f"  Records total:     {total:>9,}")
    print(f"  has_dot_dash:      {rated['has_dot_dash'].sum():>9,}  "
          f"({rated['has_dot_dash'].mean()*100:.1f}%)")
    print()

    print(f"  {'Field':<16}  {'Count':>9}  {'%':>6}")
    print(f"  {'-'*36}")
    for col in FIELD_COLS:
        n = rated[col].sum()
        print(f"  {col:<16}  {n:>9,}  {n/total*100:>5.1f}%")

    print()
    print(f"  {'Silver tier':<16}  {'Count':>9}  {'%':>6}")
    print(f"  {'-'*36}")
    for tier in [2, 1, 0]:
        n = (rated["silver_tier"] == tier).sum()
        print(f"  tier {tier:<11}  {n:>9,}  {n/total*100:>5.1f}%")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Rate DF_DE_TITLES records for ISBD field presence and silver tier."
    )
    parser.add_argument("--data",       type=Path, default=DATA_DEFAULT,
                        help="Path to input pickle (default: %(default)s)")
    parser.add_argument("--output",     type=Path, default=OUTPUT_DEFAULT,
                        help="Path to output CSV (default: %(default)s)")
    parser.add_argument("--examples",   type=int, default=0,
                        help="If >0, sample this many examples per ISBD pattern "
                             "and write to isbd_examples.csv alongside --output")
    parser.add_argument("--batch-size", type=int, default=100_000,
                        help="Rows per progress report (default: %(default)s)")
    args = parser.parse_args()

    # --- Load ---
    print(f"Loading {args.data} ...")
    with open(args.data, "rb") as f:
        df = pickle.load(f)
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected DataFrame, got {type(df)}")

    required = {"obj_id", "title"}
    missing  = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}. Available: {list(df.columns)}")

    print(f"  Shape: {df.shape}")
    df = df[["obj_id", "title"]].copy()

    # --- Rate ---
    print("Rating titles ...")
    rated = rate(df)

    # --- Output ---
    args.output.parent.mkdir(parents=True, exist_ok=True)
    rated.to_csv(args.output, index=False)
    print(f"Wrote {len(rated):,} rows → {args.output}")

    # --- Examples ---
    if args.examples > 0:
        examples_path = args.output.parent / "isbd_examples.csv"
        examples = sample_examples(rated, args.examples)
        examples.to_csv(examples_path, index=False)
        print(f"Wrote {len(examples):,} example rows → {examples_path}")

    print_summary(rated)


if __name__ == "__main__":
    main()

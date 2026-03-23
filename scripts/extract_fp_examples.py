"""
Purpose:  Extract illustrative false-positive (and false-negative) examples from the
          heuristic validation sample CSV, grouped by category, for paste into a
          markdown note.
Usage:    python scripts/extract_fp_examples.py
Inputs:   data/processed/heuristic_validation_sample.csv
Outputs:  stdout (structured text)
Dependencies: pandas
Assumptions:  CSV schema matches validate_heuristic_fields.py output.
"""

import pandas as pd
import textwrap

CSV_PATH = "data/processed/heuristic_validation_sample.csv"

FLAG_COLS = [
    "f_other_title", "f_person", "f_person_compound",
    "f_parallel", "f_edition", "f_year",
    "f_publisher", "f_series", "f_volume",
]


def active_flags(row):
    return [c for c in FLAG_COLS if row.get(c) == 1]


def print_examples(header, rows, n=3):
    print(f"\n{'='*70}")
    print(header)
    print('='*70)
    shown = 0
    for _, row in rows.iterrows():
        flags = active_flags(row)
        print(f"\nTitle    : {row['title']}")
        print(f"URL      : {row['ddb_url']}")
        print(f"Flags    : {', '.join(flags) if flags else '(none)'}")
        print(f"fp_fields: {row['fp_fields']}")
        print(f"Notes    : {row['notes']}")
        shown += 1
        if shown >= n:
            break
    if shown == 0:
        print("  (no matching rows found)")


def main():
    df = pd.read_csv(CSV_PATH)
    # Normalise flag columns to int (CSV may read as float due to NaN neighbours)
    for c in FLAG_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

    # ------------------------------------------------------------------ #
    # 1. f_parallel FP
    # ------------------------------------------------------------------ #
    # "= Jg.", "= Bd.", "= N.F.", "= Quartal", volume-part labels
    parallel_fp = df[
        (df["f_parallel"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_parallel", na=False))
    ]
    print_examples("1. f_parallel FP — serial enumeration / volume-part labels", parallel_fp)

    # ------------------------------------------------------------------ #
    # 2. f_edition FP
    # ------------------------------------------------------------------ #
    edition_fp = df[
        (df["f_edition"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_edition", na=False))
    ]
    print_examples("2. f_edition FP — newspaper issue date labels", edition_fp)

    # ------------------------------------------------------------------ #
    # 3. f_person FP
    # ------------------------------------------------------------------ #
    person_fp = df[
        (df["f_person"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_person", na=False))
    ]
    print_examples("3. f_person FP — single-letter suffixes / region / supplement / date sep", person_fp)

    # ------------------------------------------------------------------ #
    # 4. f_person_compound FP
    # ------------------------------------------------------------------ #
    pcomp_fp = df[
        (df["f_person_compound"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_person_compound", na=False))
    ]
    print_examples("4. f_person_compound FP — corporate body SoR or volume number after ';'", pcomp_fp)

    # ------------------------------------------------------------------ #
    # 5. f_year FP
    # ------------------------------------------------------------------ #
    year_fp = df[
        (df["f_year"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_year", na=False))
    ]
    print_examples("5. f_year FP — founding years, life dates, manuscript ranges, composition dates", year_fp)

    # ------------------------------------------------------------------ #
    # 6. f_other_title FP
    # ------------------------------------------------------------------ #
    ot_fp = df[
        (df["f_other_title"] == 1) &
        (df["fp_fields"].notna()) &
        (df["fp_fields"].str.contains("f_other_title", na=False))
    ]
    print_examples("6. f_other_title FP — catalog-field separators or life-date colons", ot_fp)

    # ------------------------------------------------------------------ #
    # 7. Pre-1750 false negative for f_person
    #    f_person = 0, title starts with person name + credentials pattern
    # ------------------------------------------------------------------ #
    EARLY_MODERN_KEYWORDS = [
        r"Churfürstl\.", r"Hochfürstl\.", r"Wohlehrwürdigen",
        r"Tractate", r"Leichenpredigt", r"Disputatio",
        r"\bDoctor\b", r"\bPfarrer\b", r"\bAdepti\b", r"\bProfessor\b",
        r"\bvon\b.*\bDoctor\b", r"Wohlehrwürd",
        r"Chur-", r"Fürstl\.", r"Rath\b",
        r"(?:Anno|anno)\s+\d{3,4}",
        r"Traktat", r"Tractat", r"Predig", r"Sermon",
        r"\bM\.\s+[A-Z][a-z]",   # "M. Firstname" (Magister)
        r"\bD\.\s+[A-Z][a-z]",   # "D. Firstname" (Doctor)
        r"[A-Z][a-z]+\s+[A-Z][a-z]+\s*,\s*(?:Doctor|Professor|Pfarrer|Magister|Pastor|Prediger|Secretarius|Rath|Bürgermeister)",
    ]
    pattern = "|".join(EARLY_MODERN_KEYWORDS)
    fn_mask = (
        (df["f_person"] == 0) &
        df["title"].str.contains(pattern, regex=True, na=False)
    )
    fn_rows = df[fn_mask]

    print(f"\n{'='*70}")
    print("7. Pre-1750 false negative for f_person — author name BEFORE main title")
    print('='*70)
    shown = 0
    for _, row in fn_rows.iterrows():
        print(f"\nTitle    : {row['title']}")
        print(f"URL      : {row['ddb_url']}")
        shown += 1
        if shown >= 10:
            print(f"\n  ... ({len(fn_rows) - shown} more rows match)")
            break
    if shown == 0:
        print("  (no matching rows found — widen keyword list or check CSV coverage)")

    print(f"\n\nTotal rows in CSV: {len(df)}")
    print(f"Rows with any fp_fields set: {df['fp_fields'].notna().sum()}")


if __name__ == "__main__":
    main()

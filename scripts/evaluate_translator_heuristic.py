#!/usr/bin/env python3
# Purpose:      Evaluate the translator keyword heuristic (SR-04) against manual
#               true_class annotations in translator_validation_sample.csv.
#               Prints precision, recall, F1 for TRANSLATOR and EDITOR detection,
#               and a confusion matrix heuristic_class vs true_class.
# Usage:        python3 scripts/evaluate_translator_heuristic.py [--input PATH]
# Inputs:       data/processed/translator_validation_sample.csv — annotated review sheet
# Outputs:      stdout — precision/recall/F1 table + confusion matrix
# Dependencies: pandas
# Assumptions:  true_class column is fully annotated (no blank rows).

import argparse
import sys

import pandas as pd


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    return precision, recall, f1


def evaluate(df: pd.DataFrame) -> None:
    all_classes = sorted(
        set(df["heuristic_class"].unique()) | set(df["true_class"].unique())
    )

    # --- Per-class P/R/F1 for TRANSLATOR and EDITOR ---
    print("=" * 60)
    print("Per-class precision / recall / F1")
    print("=" * 60)
    print(f"{'Class':<12}  {'P':>6}  {'R':>6}  {'F1':>6}  {'TP':>4}  {'FP':>4}  {'FN':>4}")
    print("-" * 60)

    for target in ("TRANSLATOR", "EDITOR"):
        tp = ((df["heuristic_class"] == target) & (df["true_class"] == target)).sum()
        fp = ((df["heuristic_class"] == target) & (df["true_class"] != target)).sum()
        fn = ((df["heuristic_class"] != target) & (df["true_class"] == target)).sum()
        p, r, f1 = precision_recall_f1(tp, fp, fn)
        print(f"{target:<12}  {p:>6.3f}  {r:>6.3f}  {f1:>6.3f}  {tp:>4}  {fp:>4}  {fn:>4}")

    print()

    # --- Confusion matrix: rows = true_class, cols = heuristic_class ---
    print("=" * 60)
    print("Confusion matrix  (rows=true_class, cols=heuristic_class)")
    print("=" * 60)

    matrix = pd.crosstab(
        df["true_class"],
        df["heuristic_class"],
        rownames=["true \\ heuristic"],
        colnames=[""],
    )
    # Ensure all classes appear in both axes
    matrix = matrix.reindex(index=all_classes, columns=all_classes, fill_value=0)
    print(matrix.to_string())
    print()

    # --- False-negative summary: heuristic PERSON that are actually TRANSLATOR or EDITOR ---
    print("=" * 60)
    print("False negatives: heuristic=PERSON but true=TRANSLATOR or EDITOR")
    print("=" * 60)

    fn_mask = (df["heuristic_class"] == "PERSON") & (
        df["true_class"].isin(["TRANSLATOR", "EDITOR"])
    )
    fn_rows = df[fn_mask][["obj_id", "true_class", "sor_text", "notes"]]

    total_translator_true = (df["true_class"] == "TRANSLATOR").sum()
    total_editor_true = (df["true_class"] == "EDITOR").sum()
    fn_translator = ((df["heuristic_class"] == "PERSON") & (df["true_class"] == "TRANSLATOR")).sum()
    fn_editor = ((df["heuristic_class"] == "PERSON") & (df["true_class"] == "EDITOR")).sum()

    print(
        f"TRANSLATOR missed: {fn_translator} / {total_translator_true} true TRANSLATOR rows"
    )
    print(
        f"EDITOR missed:     {fn_editor} / {total_editor_true} true EDITOR rows"
    )
    print(f"Total missed:      {fn_mask.sum()}")

    if fn_mask.sum() > 0:
        print()
        print("Detail:")
        for _, row in fn_rows.iterrows():
            print(
                f"  [{row['true_class']}] {row['obj_id'][:16]}...  sor: {row['sor_text'][:60]}"
            )
            if pd.notna(row["notes"]) and row["notes"]:
                print(f"         note: {row['notes']}")

    print()

    # --- Class distribution summary ---
    print("=" * 60)
    print("Class distribution (true_class)")
    print("=" * 60)
    counts = df["true_class"].value_counts().sort_index()
    for cls, n in counts.items():
        print(f"  {cls:<12}  {n:>4}")
    print(f"  {'TOTAL':<12}  {len(df):>4}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate SR-04 translator heuristic against manual annotations."
    )
    parser.add_argument(
        "--input",
        default="data/processed/translator_validation_sample.csv",
        help="Path to annotated CSV (default: data/processed/translator_validation_sample.csv)",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype=str)

    # Drop rows with blank true_class
    blank_mask = df["true_class"].isna() | (df["true_class"].str.strip() == "")
    if blank_mask.any():
        n_blank = blank_mask.sum()
        print(
            f"WARNING: {n_blank} row(s) with blank true_class dropped from evaluation.",
            file=sys.stderr,
        )
        df = df[~blank_mask].copy()

    if df.empty:
        print("ERROR: No annotated rows to evaluate.", file=sys.stderr)
        sys.exit(1)

    evaluate(df)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Purpose:      SR-09 — Sanity check: evaluate NuNER Zero on tier-2 pre-filled records
#               using ISBD-derived silver spans as pseudo-gold.
#               Computes exact span match precision, recall, and F1 per label.
#               See notes/ner/sr09_nunerzero-tier2-sanity.md for design rationale.
#
# Usage:        python3 scripts/sr09_eval_nunerzero_tier2.py
#                   [--input PATH]         # default: data/annotation/sr08_gold_prefilled.jsonl
#                   [--output PATH]        # default: data/processed/sr09_nunerzero_tier2_results.csv
#                   [--detail PATH]        # optional: per-record JSONL with predictions + gold
#                   [--threshold FLOAT]    # NuNER Zero score threshold (default: 0.5)
#                   [--model STR]          # HuggingFace model ID (default: numind/NuNER-Zero)
#
# Inputs:       data/annotation/sr08_gold_prefilled.jsonl  (status == "pre-filled")
# Outputs:      data/processed/sr09_nunerzero_tier2_results.csv
#               (optional) per-record detail JSONL
#
# Dependencies: gliner, pandas
# Assumptions:  sr08_prefill_spans.py has been run and sr08_gold_prefilled.jsonl exists.
#               NuNER Zero is a GLiNER-based model; gliner package must be installed.

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "data" / "annotation" / "sr08_gold_prefilled.jsonl"
OUTPUT = ROOT / "data" / "processed" / "sr09_nunerzero_tier2_results.csv"

# Named prompt sets for experimentation.
# "default"    — generic; baseline run.
# "catalog"    — field-aware; describes the span's role in the bibliographic record.
# "structural" — boundary-aware; explicitly references ISBD separators.
PROMPT_SETS: dict[str, dict[str, str]] = {
    "default": {
        "TITLE":       "title of a book, work, or publication",
        "OTHER_TITLE": "subtitle or other title information",
        "PERSON":      "person name or author name",
    },
    "catalog": {
        "TITLE":       "main title field in a library catalog record, all text before any subtitle or author",
        "OTHER_TITLE": "subtitle field in a library catalog record, all text after the colon separator",
        "PERSON":      "author statement field in a library catalog record, all text after the slash separator",
    },
    "structural": {
        "TITLE":       "complete main title of a book, ending before ' : ' subtitle or ' / ' author",
        "OTHER_TITLE": "complete subtitle of a book between ' : ' and ' / ' or end of title area",
        "PERSON":      "complete author or editor statement after ' / ' in a bibliographic title string",
    },
}


# ── Evaluation helpers ──────────────────────────────────────────────────────────

def span_key(span: dict) -> tuple:
    """Canonical key for exact span match: (start, end, label)."""
    return (span["start"], span["end"], span["label"])


def compute_f1(tp: int, fp: int, fn: int) -> dict:
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall    = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1        = (2 * precision * recall / (precision + recall)
                 if (precision + recall) > 0 else 0.0)
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(precision, 4),
            "recall":    round(recall,    4),
            "f1":        round(f1,        4)}


def evaluate(records: list[dict], predictions: list[list[dict]]) -> dict:
    """
    Compute per-label exact-span-match P/R/F1.

    records:     list of gold records (each has a 'spans' list)
    predictions: parallel list of predicted span lists
    Returns:     {label: {TP, FP, FN, precision, recall, f1}}
    """
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})

    for gold_rec, pred_spans in zip(records, predictions):
        gold_set = {span_key(s) for s in gold_rec["spans"]}
        pred_set = {span_key(s) for s in pred_spans}

        for key in gold_set | pred_set:
            label = key[2]
            if key in gold_set and key in pred_set:
                counts[label]["tp"] += 1
            elif key in pred_set:
                counts[label]["fp"] += 1
            else:
                counts[label]["fn"] += 1

    return {label: compute_f1(**c) for label, c in counts.items()}


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SR-09: NuNER Zero tier-2 sanity check")
    parser.add_argument("--input",     type=Path,  default=INPUT)
    parser.add_argument("--output",    type=Path,  default=OUTPUT)
    parser.add_argument("--detail",    type=Path,  default=None,
                        help="Optional JSONL path for per-record predictions")
    parser.add_argument("--threshold", type=float, default=0.5,
                        help="NuNER Zero score threshold (default: 0.5)")
    parser.add_argument("--model",     type=str,   default="numind/NuNer_Zero",
                        help="HuggingFace model ID")
    parser.add_argument("--prompts",   type=str,   default="default",
                        choices=list(PROMPT_SETS.keys()),
                        help="Named prompt set to use (default / catalog / structural)")
    args = parser.parse_args()

    label_prompts   = PROMPT_SETS[args.prompts]
    prompt_to_label = {v: k for k, v in label_prompts.items()}

    # ── Load tier-2 pre-filled records ─────────────────────────────────────────
    records = []
    with open(args.input, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if r.get("annotation_status") == "pre-filled":
                records.append(r)

    print(f"Tier-2 pre-filled records: {len(records)}")
    if not records:
        print("No tier-2 records found. Run sr08_prefill_spans.py first.")
        return

    print(f"Prompt set: {args.prompts}")
    for label, prompt in label_prompts.items():
        print(f"  {label}: {prompt!r}")

    # ── Load model ─────────────────────────────────────────────────────────────
    print(f"\nLoading model: {args.model} ...")
    from gliner import GLiNER  # imported here so the rest of the script is importable
    model = GLiNER.from_pretrained(args.model)

    prompts = list(label_prompts.values())

    # ── Run inference ──────────────────────────────────────────────────────────
    print(f"Running inference (threshold={args.threshold}) ...")
    all_predictions: list[list[dict]] = []

    for rec in records:
        raw = model.predict_entities(rec["title"], prompts, threshold=args.threshold)
        # Normalise: map prompt string back to our label name
        pred_spans = []
        for ent in raw:
            label = prompt_to_label.get(ent["label"])
            if label is None:
                continue  # unexpected label; skip
            pred_spans.append({
                "start": ent["start"],
                "end":   ent["end"],
                "label": label,
                "text":  ent["text"],
                "score": round(ent["score"], 4),
            })
        all_predictions.append(pred_spans)

    # ── Diagnose first 3 records ────────────────────────────────────────────────
    print("\n── Offset diagnostic (first 3 records) ────────────────────────────────────")
    for rec, pred in zip(records[:3], all_predictions[:3]):
        print(f"\n  title : {rec['title']!r}")
        print(f"  gold  : {[(s['start'], s['end'], s['label'], s['text']) for s in rec['spans']]}")
        print(f"  pred  : {[(s['start'], s['end'], s['label'], s['text']) for s in pred]}")

    # ── Evaluate ────────────────────────────────────────────────────────────────
    results = evaluate(records, all_predictions)

    print("\n── Results (exact span match, tier-2 silver pseudo-gold) ─────────────────")
    rows = []
    for label in ["TITLE", "OTHER_TITLE", "PERSON"]:
        if label in results:
            m = results[label]
            print(f"  {label:<15}  P={m['precision']:.3f}  R={m['recall']:.3f}  "
                  f"F1={m['f1']:.3f}  (TP={m['tp']} FP={m['fp']} FN={m['fn']})")
            rows.append({"label": label, **m})
        else:
            print(f"  {label:<15}  — (no instances)")

    print(f"\n  Records evaluated: {len(records)}")
    print(f"  Prompt set: {args.prompts}")
    print(f"  Threshold: {args.threshold}")
    print(f"  Model: {args.model}")

    # ── Save results CSV ────────────────────────────────────────────────────────
    args.output.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(rows)
    df["prompts"]   = args.prompts
    df["threshold"] = args.threshold
    df["model"]     = args.model
    df["n_records"] = len(records)
    df.to_csv(args.output, index=False)
    print(f"\nResults written to {args.output}")

    # ── Optional per-record detail ──────────────────────────────────────────────
    if args.detail:
        args.detail.parent.mkdir(parents=True, exist_ok=True)
        with open(args.detail, "w", encoding="utf-8") as f:
            for rec, pred in zip(records, all_predictions):
                f.write(json.dumps({
                    "obj_id":    rec["obj_id"],
                    "title":     rec["title"],
                    "era":       rec["era"],
                    "gold":      rec["spans"],
                    "predicted": pred,
                }, ensure_ascii=False) + "\n")
        print(f"Per-record detail written to {args.detail}")


if __name__ == "__main__":
    main()

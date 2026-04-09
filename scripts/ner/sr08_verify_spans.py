#!/usr/bin/env python3
# Purpose:      SR-08 — Spot-check pre-filled annotation spans in sr08_gold_prefilled.jsonl.
#               Verifies that span character offsets match the extracted text, and prints
#               3 examples each of 'pre-filled' and 'partial' records for manual review.
# Usage:        python3 scripts/sr08_verify_spans.py [--input PATH] [--n N]
# Inputs:       data/annotation/sr08_gold_prefilled.jsonl
# Outputs:      stdout — offset verification results + example spans
# Dependencies: —
# Assumptions:  sr08_prefill_spans.py has already been run.

import argparse
import json
from pathlib import Path

ROOT  = Path(__file__).parent.parent
INPUT = ROOT / "data" / "annotation" / "sr08_gold_prefilled.jsonl"


def main() -> None:
    parser = argparse.ArgumentParser(description="SR-08: verify pre-filled span offsets")
    parser.add_argument("--input", type=Path, default=INPUT, help="prefilled JSONL")
    parser.add_argument("--n",     type=int,  default=3,     help="examples per status")
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as f:
        records = [json.loads(line) for line in f]

    # ── Offset integrity check (all records) ──────────────────────────────────
    errors = []
    for rec in records:
        title = rec["title"]
        for span in rec["spans"]:
            extracted = title[span["start"]: span["end"]]
            if extracted != span["text"]:
                errors.append({
                    "obj_id":   rec["obj_id"],
                    "label":    span["label"],
                    "expected": span["text"],
                    "got":      extracted,
                })

    total = len(records)
    span_count = sum(len(r["spans"]) for r in records)
    print(f"Records: {total}  |  Total spans: {span_count}")
    if errors:
        print(f"\nOFFSET ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  {e['obj_id']}  [{e['label']}]  expected '{e['expected']}'  got '{e['got']}'")
    else:
        print("Offset check: all spans OK ✓")

    # ── Sample display ─────────────────────────────────────────────────────────
    for status in ("pre-filled", "partial"):
        examples = [r for r in records if r["annotation_status"] == status][: args.n]
        print(f"\n{'─'*60}")
        print(f"STATUS: {status.upper()}  (showing {len(examples)} of {sum(1 for r in records if r['annotation_status']==status)})")
        print(f"{'─'*60}")
        for rec in examples:
            print(f"\n  obj_id : {rec['obj_id']}")
            print(f"  era    : {rec['era']}  tier: {rec['silver_tier']}")
            print(f"  title  : {rec['title'][:120]}")
            if rec["spans"]:
                for s in rec["spans"]:
                    print(f"    [{s['label']:<12}] '{s['text'][:80]}'")
            else:
                print("    (no spans)")


if __name__ == "__main__":
    main()

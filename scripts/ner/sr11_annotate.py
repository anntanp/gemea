#!/usr/bin/env python3
# Purpose:      SR-11 T11.1b — Interactive annotation helper for manual span labeling.
#               Loads sr11_prompt_validation_manual.jsonl, presents each unannotated
#               title, and writes spans back using Inline Bracketed input format.
#               Resumes automatically from the first unannotated record.
#
# Usage:        python3 scripts/sr11_annotate.py
#                   [--input PATH]   # default: data/annotation/sr11_prompt_validation_manual.jsonl
#                   [--all]          # re-annotate already-annotated records too
#
# Input format (at each prompt):
#   Type spans in Inline Bracketed format, e.g.:
#     [D. Johann Gerhard, Pastoris zu Jena | PERSON] [Erklärung der Historien | TITLE]
#   Commands:
#     <Enter>   — mark as annotated with no spans (title has no extractable entities)
#     s         — skip this record (leave unannotated, revisit later)
#     q         — quit and save progress
#     ?         — show label reference
#
# Inputs:       data/annotation/sr11_prompt_validation_manual.jsonl
# Outputs:      data/annotation/sr11_prompt_validation_manual.jsonl (updated in place)
#
# Dependencies: none (stdlib only)
# Assumptions:  sr11_sample_validation.py has been run.

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "data" / "annotation" / "sr11_prompt_validation_manual.jsonl"

VALID_LABELS  = {"TITLE", "OTHER_TITLE", "PERSON"}
BRACKET_RE    = re.compile(r"\[(.+?)\s*\|\s*([A-Z_]+)\]")

LABEL_HELP = """
Labels:
  TITLE       — main work title; primary intellectual content identifier
  OTHER_TITLE — subtitle or alternative title (after "Das ist:", "oder", ":", "nämlich")
  PERSON      — author/editor and their credentials, titles, role descriptions

Pre-1750 rule: author name + credentials appear BEFORE the main title.
  Include in PERSON span: degree (D., M., Lic.), full name, role ("Pfarrers zu X").
  Stop PERSON span at the first content noun of the title.

Example:
  [D. Johann Gerhard, Professoris zu Jena | PERSON] [Erklärung der Historien des Leidens | TITLE]
"""


# ── Parsing ─────────────────────────────────────────────────────────────────

def parse_brackets(raw: str, title: str) -> tuple[list[dict], list[str]]:
    """
    Parse Inline Bracketed annotation string into span dicts with character offsets.
    Returns (spans, errors). Errors is empty on success.
    """
    spans  = []
    errors = []
    search_start = 0  # advance after each match to handle duplicate text correctly

    for m in BRACKET_RE.finditer(raw):
        text  = m.group(1).strip()
        label = m.group(2).strip().upper()

        if label not in VALID_LABELS:
            errors.append(f"Unknown label '{label}' — must be one of {sorted(VALID_LABELS)}")
            continue

        idx = title.find(text, search_start)
        if idx == -1:
            # Try from start (span may appear before a previous span)
            idx = title.find(text)
        if idx == -1:
            errors.append(f"Span text not found in title: {text!r}")
            continue

        spans.append({"start": idx, "end": idx + len(text), "label": label, "text": text})
        search_start = idx + len(text)

    return spans, errors


# ── Display ─────────────────────────────────────────────────────────────────

def display_record(rec: dict, idx: int, total: int) -> None:
    era     = rec.get("era", "?")
    dc_type = rec.get("dc_type", "?")
    title   = rec["title"]
    link    = rec.get("ddb_link", "")

    print()
    print(f"─── Record {idx}/{total}  [{era}  {dc_type}] ───────────────────────────")
    print(f"  {title}")
    if link:
        print(f"  {link}")
    print()


# ── Main loop ────────────────────────────────────────────────────────────────

def load_records(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def save_records(records: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def annotate(records: list[dict], reannot: bool) -> list[dict]:
    total     = len(records)
    to_do     = [i for i, r in enumerate(records)
                 if reannot or r.get("annotation_status") != "done"]
    remaining = len(to_do)

    if not to_do:
        print("All records already annotated. Use --all to re-annotate.")
        return records

    print(f"\n{remaining} records to annotate ({total - remaining} already done).")
    print("Enter spans in Inline Bracketed format, or: s=skip  q=quit  ?=help  <Enter>=no entities\n")

    today = date.today().isoformat()

    for pos, rec_idx in enumerate(to_do, 1):
        rec = records[rec_idx]
        display_record(rec, pos, remaining)

        while True:
            try:
                raw = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nInterrupted — saving progress.")
                return records

            if raw == "q":
                print("Quitting — saving progress.")
                return records

            if raw == "s":
                print("  Skipped.")
                break

            if raw == "?":
                print(LABEL_HELP)
                continue

            # Empty input = no entities
            if raw == "":
                rec["spans"]             = []
                rec["annotation_status"] = "done"
                rec["annotator"]         = "human"
                rec["annotation_date"]   = today
                print("  Marked as annotated (no entities).")
                break

            spans, errors = parse_brackets(raw, rec["title"])

            if errors:
                for err in errors:
                    print(f"  ERROR: {err}")
                print("  Please re-enter.")
                continue

            if not spans:
                print("  No brackets parsed — check format. (Press Enter for no entities.)")
                continue

            # Confirm
            print("  Parsed spans:")
            for s in spans:
                print(f"    [{s['start']}:{s['end']}]  {s['label']:<15}  {s['text']!r}")
            confirm = input("  Accept? [Y/n/e=edit] ").strip().lower()
            if confirm in ("", "y"):
                rec["spans"]             = spans
                rec["annotation_status"] = "done"
                rec["annotator"]         = "human"
                rec["annotation_date"]   = today
                break
            elif confirm == "e":
                continue  # re-enter
            else:
                print("  Discarded — please re-enter.")
                continue

    return records


def main() -> None:
    parser = argparse.ArgumentParser(
        description="SR-11 T11.1b: interactive annotation helper"
    )
    parser.add_argument("--input", type=Path, default=INPUT)
    parser.add_argument("--all",   action="store_true",
                        help="Re-annotate already-annotated records")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"Input not found: {args.input}")
        print("Run sr11_sample_validation.py first.")
        sys.exit(1)

    records = load_records(args.input)
    records = annotate(records, reannot=args.all)
    save_records(records, args.input)

    done  = sum(1 for r in records if r.get("annotation_status") == "done")
    total = len(records)
    print(f"\nSaved. {done}/{total} records annotated.")


if __name__ == "__main__":
    main()

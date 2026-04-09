#!/usr/bin/env python3
# Purpose:      SR-08 — Pre-fill NER annotation spans for the gold sample using ISBD
#               rules. Tier-2 and tier-1 records (non-pre-1700) get auto-extracted
#               TITLE / OTHER_TITLE / PERSON spans; pre-1700 and tier-0 records are
#               left empty and flagged for manual annotation.
#
#               Three annotation statuses:
#                 pre-filled  — tier-2 (structural '. -'); high confidence
#                 partial     — tier-1 (heuristic ' /' or ' :'); verify before accepting
#                 manual      — pre-1700 or tier-0; must annotate from scratch
#
# Usage:        python3 scripts/sr08_prefill_spans.py [--input PATH] [--output PATH]
#                   [--queue PATH]
# Inputs:       data/annotation/sr08_gold_sample.csv
# Outputs:      data/annotation/sr08_gold_prefilled.jsonl  — all records + pre-filled spans
#               data/annotation/sr08_manual_queue.csv      — manual records sorted by priority
# Dependencies: pandas
# Assumptions:  sr08_sample_gold.py has already been run.

import argparse
import json
import re
from pathlib import Path

import pandas as pd

ROOT   = Path(__file__).parent.parent
INPUT  = ROOT / "data" / "annotation" / "sr08_gold_sample.csv"
OUTPUT = ROOT / "data" / "annotation" / "sr08_gold_prefilled.jsonl"
QUEUE  = ROOT / "data" / "annotation" / "sr08_manual_queue.csv"

# ISBD separators (same as rate_isbd_fields.py)
RE_AREA_SEP = re.compile(r"\. - ")


# ── Span extraction ────────────────────────────────────────────────────────────

def _find(text: str, sub: str, start: int = 0) -> int:
    """Return index of sub in text starting at start, or -1."""
    return text.find(sub, start)


def extract_spans(title: str, era: str, silver_tier: str) -> tuple[list[dict], str]:
    """
    Return (spans, status).

    spans: list of {"start": int, "end": int, "label": str, "text": str}
           Character offsets into the original title string.
    status: "pre-filled" | "partial" | "manual"
    """
    # ── Rules that suppress auto-extraction ──────────────────────────────────
    if era == "pre-1700":
        # Author-before-title structure: ' / ' does not signal PERSON here.
        # Must be annotated manually following sr08 §4 guidelines.
        return [], "manual"

    if silver_tier == "0":
        # No ISBD signals detected; nothing to pre-fill.
        return [], "manual"

    spans = []

    # ── Split off manifestation area (' . - ') ────────────────────────────────
    area_match = RE_AREA_SEP.search(title)
    if area_match:
        title_area = title[: area_match.start()]   # everything before first '. -'
        status = "pre-filled"
    else:
        title_area = title
        status = "partial"    # heuristic tier: accept but verify

    # ── PERSON: text after ' / ' within title area ────────────────────────────
    sor_sep = _find(title_area, " / ")
    if sor_sep != -1:
        sor_start = sor_sep + 3           # skip ' / '
        sor_text  = title_area[sor_start:].rstrip()
        if sor_text:
            # Find the exact position in the full title string
            full_start = _find(title, sor_text, sor_sep)
            if full_start != -1:
                spans.append({
                    "start": full_start,
                    "end":   full_start + len(sor_text),
                    "label": "PERSON",
                    "text":  sor_text,
                })
        title_area = title_area[:sor_sep]  # drop SoR from title part

    # ── OTHER_TITLE: text after ' : ' in title part ───────────────────────────
    ot_sep = _find(title_area, " : ")
    if ot_sep != -1:
        ot_start = ot_sep + 3             # skip ' : '
        ot_text  = title_area[ot_start:].rstrip()
        if ot_text:
            full_start = _find(title, ot_text, ot_sep)
            if full_start != -1:
                spans.append({
                    "start": full_start,
                    "end":   full_start + len(ot_text),
                    "label": "OTHER_TITLE",
                    "text":  ot_text,
                })
        title_area = title_area[:ot_sep]  # drop subtitle from title part

    # ── TITLE: what remains of title_area ─────────────────────────────────────
    main_title = title_area.strip()
    if main_title:
        full_start = _find(title, main_title)
        if full_start != -1:
            spans.append({
                "start": full_start,
                "end":   full_start + len(main_title),
                "label": "TITLE",
                "text":  main_title,
            })

    # Sort by offset for readability
    spans.sort(key=lambda s: s["start"])

    return spans, status


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="SR-08: pre-fill annotation spans")
    parser.add_argument("--input",  type=Path, default=INPUT,  help="gold sample CSV")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="output JSONL")
    parser.add_argument("--queue",  type=Path, default=QUEUE,  help="manual queue CSV")
    args = parser.parse_args()

    df = pd.read_csv(args.input, dtype={"silver_tier": str})

    records = []
    status_counts: dict[str, int] = {"pre-filled": 0, "partial": 0, "manual": 0}

    for _, row in df.iterrows():
        title = str(row.get("title", "") or "")
        era   = str(row.get("era",   "unknown"))
        tier  = str(row.get("silver_tier", "0"))

        spans, status = extract_spans(title, era, tier)
        status_counts[status] += 1

        records.append({
            "obj_id":       row["obj_id"],
            "title":        title,
            "dates":        row.get("dates", ""),
            "dc_type":      row.get("dc_type", ""),
            "silver_tier":  tier,
            "era":          era,
            "ddb_link":     row.get("ddb_link", ""),
            "spans":        spans,
            "annotation_status": status,
            "annotator":    "",
            "annotation_date": "",
            "notes":        "",
        })

    # ── Write JSONL ────────────────────────────────────────────────────────────
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ── Write manual queue CSV (sorted: pre-1700 tier-0 first) ────────────────
    manual_df = pd.DataFrame(
        [r for r in records if r["annotation_status"] == "manual"],
    )
    if not manual_df.empty:
        ERA_ORDER = {"pre-1700": 0, "1700-1800": 1, "19th-c": 2, "modern": 3, "unknown": 4}
        manual_df["_era_ord"] = manual_df["era"].map(ERA_ORDER).fillna(9)
        manual_df = manual_df.sort_values(["_era_ord", "silver_tier"]).drop(columns="_era_ord")
        manual_df[["obj_id", "title", "dates", "dc_type", "silver_tier", "era", "ddb_link"]].to_csv(
            args.queue, index=False
        )

    # ── Summary ────────────────────────────────────────────────────────────────
    total = len(records)
    print(f"Total records:  {total}")
    print(f"  pre-filled:   {status_counts['pre-filled']}  (tier-2, non-pre-1700; accept with review)")
    print(f"  partial:      {status_counts['partial']}  (tier-1, non-pre-1700; verify each span)")
    print(f"  manual:       {status_counts['manual']}  (pre-1700 or tier-0; annotate from scratch)")
    print(f"\nAnnotation queue written to {args.queue}")
    print(f"Full JSONL written to        {args.output}")

    print("\nManual queue breakdown:")
    if not manual_df.empty:
        print(manual_df.groupby(["era", "silver_tier"]).size().to_string())


if __name__ == "__main__":
    main()

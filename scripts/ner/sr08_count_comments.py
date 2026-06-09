#!/usr/bin/env python3
# Purpose:      Count and list all annotator comments in a Doccano export directory
# Usage:        python scripts/ner/sr08_count_comments.py \
#                   --export-dir data/annotation/doccano/export-20260608-1221
# Inputs:       all *.jsonl files in --export-dir (skips dummy.doccano.jsonl, ann.jsonl)
# Outputs:      data/processed/ner/sr08_comments_<export>.csv  (one row per comment)
#               stdout summary
# Dependencies: none (stdlib only)
# Assumptions:  Filename stem = annotator name; Comments field is a list of strings

import argparse
import csv
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
# Skip non-annotator files: template, adjudicated, enriched outputs, and test samples
SKIP_NAMES    = {"dummy.doccano.jsonl", "ann.jsonl"}
SKIP_SUFFIXES = (".meta.jsonl",)
SKIP_PREFIXES = ("sr08_",)


def collect_comments(export_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for jsonl_file in sorted(export_dir.glob("*.jsonl")):
        name = jsonl_file.name
        if (name in SKIP_NAMES
                or any(name.endswith(s) for s in SKIP_SUFFIXES)
                or any(name.startswith(p) for p in SKIP_PREFIXES)):
            continue
        annotator = jsonl_file.stem
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                for comment in rec.get("Comments", []):
                    rows.append({
                        "annotator": annotator,
                        "doc_id":    rec["id"],
                        "text":      rec["text"][:80],
                        "comment":   comment,
                    })
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Count and list comments in a Doccano export")
    parser.add_argument("--export-dir", required=True, help="Path to Doccano export directory")
    args = parser.parse_args()

    export_dir = Path(args.export_dir)
    if not export_dir.is_dir():
        sys.exit(f"Not a directory: {export_dir}")

    rows = collect_comments(export_dir)

    # Write CSV
    export_name = export_dir.name
    out_path = BASE / f"data/processed/ner/sr08_comments_{export_name}.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["annotator", "doc_id", "text", "comment"])
        writer.writeheader()
        writer.writerows(rows)

    # Summary
    from collections import Counter
    by_annotator = Counter(r["annotator"] for r in rows)
    print(f"Total comments: {len(rows)}")
    print(f"Saved to: {out_path}\n")
    print(f"{'Annotator':<15} {'Comments':>8}")
    print("-" * 25)
    for annotator, count in sorted(by_annotator.items(), key=lambda x: -x[1]):
        print(f"{annotator:<15} {count:>8}")
    print()
    print("Detail:")
    for r in rows:
        print(f"  [{r['annotator']}] doc_id={r['doc_id']}  {r['comment']}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Purpose:      Verify that sr08_add_meta_to_export.py preserved all annotations and comments
#               exactly; fail fast with a diff on any discrepancy
# Usage:        python scripts/ner/sr08_verify_meta_export.py \
#                   --original data/annotation/doccano/export-20260608-1221/maria.jsonl \
#                   --enriched data/annotation/doccano/export-20260608-1221/maria.meta.jsonl
# Inputs:       --original: annotator JSONL before enrichment
#               --enriched: annotator JSONL after sr08_add_meta_to_export.py
# Outputs:      stdout pass/fail report; exits 1 on any failure
# Dependencies: none (stdlib only)
# Assumptions:  Both files are UTF-8 JSONL; one JSON object per line

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ANNOTATION_FIELDS = ("id", "text", "label", "Comments")
META_URL_PREFIX   = "https://www.deutsche-digitale-bibliothek.de/item/"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    """Load all records from a JSONL file."""
    records = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                sys.exit(f"JSON parse error in {path} line {lineno}: {exc}")
    return records


def check_counts(original: list, enriched: list) -> list[str]:
    """Return error list if record counts differ."""
    if len(original) != len(enriched):
        return [f"Record count mismatch: original={len(original)}, enriched={len(enriched)}"]
    return []


def check_annotation_fields(
    orig: dict[str, Any],
    enr: dict[str, Any],
    idx: int,
) -> list[str]:
    """Return errors for any annotation field that changed between orig and enr."""
    errors: list[str] = []
    for field in ANNOTATION_FIELDS:
        if field not in orig and field not in enr:
            continue
        if field not in enr:
            errors.append(f"  record[{idx}] id={orig.get('id')}: field '{field}' missing from enriched")
            continue
        if field not in orig:
            errors.append(f"  record[{idx}] id={orig.get('id')}: field '{field}' unexpectedly added")
            continue
        if orig[field] != enr[field]:
            errors.append(
                f"  record[{idx}] id={orig.get('id')}: '{field}' changed\n"
                f"    original: {json.dumps(orig[field], ensure_ascii=False)}\n"
                f"    enriched: {json.dumps(enr[field], ensure_ascii=False)}"
            )
    return errors


def check_meta(enr: dict[str, Any], idx: int) -> list[str]:
    """Return errors if meta field is missing or malformed."""
    errors: list[str] = []
    doc_id = enr.get("id", f"index {idx}")

    if "meta" not in enr:
        errors.append(f"  record[{idx}] id={doc_id}: 'meta' field missing from enriched")
        return errors

    meta = enr["meta"]
    if not isinstance(meta, dict):
        errors.append(f"  record[{idx}] id={doc_id}: 'meta' is not a dict: {meta!r}")
        return errors

    # htype: null or "htype_NNN (label)"
    if "htype" not in meta:
        errors.append(f"  record[{idx}] id={doc_id}: meta missing 'htype' key")
    elif meta["htype"] is not None:
        htype = meta["htype"]
        if not isinstance(htype, str) or not htype.startswith("htype_"):
            errors.append(f"  record[{idx}] id={doc_id}: invalid htype value: {htype!r}")

    # url: must be a DDB item URL
    if "url" not in meta:
        errors.append(f"  record[{idx}] id={doc_id}: meta missing 'url' key")
    elif not isinstance(meta["url"], str) or not meta["url"].startswith(META_URL_PREFIX):
        errors.append(f"  record[{idx}] id={doc_id}: invalid url: {meta['url']!r}")

    return errors


def verify(original_path: Path, enriched_path: Path) -> int:
    """Run all checks; return number of failures."""
    original = load_jsonl(original_path)
    enriched = load_jsonl(enriched_path)

    all_errors: list[str] = []

    count_errors = check_counts(original, enriched)
    all_errors.extend(count_errors)
    if count_errors:
        # Can't do per-record checks if counts differ
        _report(all_errors)
        return len(all_errors)

    for idx, (orig, enr) in enumerate(zip(original, enriched)):
        all_errors.extend(check_annotation_fields(orig, enr, idx))
        all_errors.extend(check_meta(enr, idx))

    _report(all_errors)
    return len(all_errors)


def _report(errors: list[str]) -> None:
    if errors:
        print(f"FAIL — {len(errors)} error(s):", file=sys.stderr)
        for err in errors:
            print(err, file=sys.stderr)
    else:
        print("PASS — all annotation fields and meta are intact")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify that sr08_add_meta_to_export.py preserved all annotations and comments"
    )
    parser.add_argument(
        "--original", required=True,
        help="Annotator JSONL before enrichment",
    )
    parser.add_argument(
        "--enriched", required=True,
        help="Annotator JSONL produced by sr08_add_meta_to_export.py",
    )
    args = parser.parse_args()

    failures = verify(Path(args.original), Path(args.enriched))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()

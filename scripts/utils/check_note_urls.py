#!/usr/bin/env python3
# Purpose:      Check all DDB item URLs in a markdown note for HTTP errors and suggest
#               live replacement examples drawn from sr01_isbd_examples.csv.
# Usage:        python3 scripts/check_note_urls.py [--note PATH] [--examples PATH] [--patch]
# Inputs:       notes/ner/sr01_isbd-applicability.md  (default --note)
#               data/processed/sr01_isbd_examples.csv (default --examples)
# Outputs:      stdout — broken URLs with candidate replacements
#               with --patch: writes replacements directly into the note
# Dependencies: stdlib only (urllib, csv, re, argparse)
# Assumptions:  DDB items resolve at https://www.deutsche-digitale-bibliothek.de/item/<ID>
#               The note uses the short form https://ddb.de/item/<ID>
#               Replacement candidates come from the examples CSV (same corpus).

import argparse
import csv
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Set

BASE_URL = "https://www.deutsche-digitale-bibliothek.de/item/"
SHORT_URL_RE = re.compile(r"https?://(?:www\.)?ddb\.de/item/([A-Z0-9]+)")

# Field flags ordered by specificity: first flag that is '1' is used as the
# primary pattern key when searching for same-category replacements.
PATTERN_FLAGS = [
    "f_publisher",
    "f_series",
    "f_volume",
    "f_parallel",
    "f_edition",
    "f_person_compound",
    "f_person",
    "f_year",
    "f_other_title",
]

_OPENER = urllib.request.build_opener(
    urllib.request.HTTPRedirectHandler(),
)
_OPENER.addheaders = [("User-Agent", "GeMeA-URL-Checker/1.0")]


def check_id(id_: str, retries: int = 1) -> int:
    """Return HTTP status code for a DDB item ID. Returns 0 on connection error."""
    url = BASE_URL + id_
    for attempt in range(retries + 1):
        try:
            with _OPENER.open(url, timeout=10) as resp:
                return resp.status
        except urllib.error.HTTPError as e:
            return e.code
        except Exception:
            if attempt < retries:
                time.sleep(1)
    return 0


def extract_ids(text: str) -> List[str]:
    """Return DDB item IDs in order of appearance, deduplicated."""
    seen: Set[str] = set()
    ids: List[str] = []
    for m in SHORT_URL_RE.finditer(text):
        id_ = m.group(1)
        if id_ not in seen:
            seen.add(id_)
            ids.append(id_)
    return ids


def load_examples(path: Path) -> List[Dict]:
    with path.open() as f:
        return list(csv.DictReader(f))


def primary_flag(row: Dict) -> Optional[str]:
    """Return the first set flag for a CSV row, or None."""
    for flag in PATTERN_FLAGS:
        if row.get(flag) == "1":
            return flag
    return None


def find_replacements(
    broken_id: str,
    all_rows: List[Dict],
    in_use: Set[str],
    n: int = 3,
) -> List[Dict]:
    """
    Find up to n live replacement candidates sharing the same primary flag as
    broken_id. If broken_id is absent from the CSV, all rows are candidates.
    """
    target_flag: Optional[str] = None
    for row in all_rows:
        if row["obj_id"] == broken_id:
            target_flag = primary_flag(row)
            break

    candidates = [
        r for r in all_rows
        if r["obj_id"] != broken_id
        and r["obj_id"] not in in_use
        and (target_flag is None or r.get(target_flag) == "1")
    ]

    results: List[Dict] = []
    for row in candidates:
        if len(results) >= n:
            break
        time.sleep(0.3)
        status = check_id(row["obj_id"])
        if status == 200:
            results.append(row)
            in_use.add(row["obj_id"])

    return results


def patch_note(text: str, replacements: Dict[str, Dict]) -> str:
    """
    Replace each broken DDB ID in text with the first candidate ID and update
    the backtick-quoted title cell in the same pipe-delimited table row.
    """
    for broken_id, row in replacements.items():
        new_id = row["obj_id"]
        new_title = row["title"][:80].rstrip()
        short_broken = f"https://ddb.de/item/{broken_id}"
        short_new = f"https://ddb.de/item/{new_id}"

        text = text.replace(short_broken, short_new)

        # After URL replacement the row now contains short_new; update the title cell.
        lines = text.split("\n")
        updated = []
        for line in lines:
            if short_new in line and line.strip().startswith("|"):
                line = re.sub(r"`[^`]+`", f"`{new_title}`", line, count=1)
            updated.append(line)
        text = "\n".join(updated)

    return text


def main() -> None:
    parser = argparse.ArgumentParser(description="Check DDB URLs in a note for 404s.")
    parser.add_argument(
        "--note",
        default="notes/ner/sr01_isbd-applicability.md",
        help="Markdown note to check (relative to repo root)",
    )
    parser.add_argument(
        "--examples",
        default="data/processed/sr01_isbd_examples.csv",
        help="Examples CSV with DDB item records",
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Write the first replacement candidate into the note in place",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).parent.parent
    note_path = repo_root / args.note
    examples_path = repo_root / args.examples

    if not note_path.exists():
        sys.exit(f"Note not found: {note_path}")
    if not examples_path.exists():
        sys.exit(f"Examples CSV not found: {examples_path}")

    note_text = note_path.read_text()
    all_rows = load_examples(examples_path)

    ids = extract_ids(note_text)
    in_use = set(ids)

    print(f"Checking {len(ids)} DDB item IDs in {args.note} …\n", flush=True)

    broken: List[str] = []
    for id_ in ids:
        time.sleep(0.3)
        status = check_id(id_)
        mark = "OK" if status == 200 else f"BROKEN ({status})"
        print(f"  [{mark}] {id_}", flush=True)
        if status != 200:
            broken.append(id_)

    if not broken:
        print("\nAll URLs live — nothing to do.")
        return

    print(f"\n{len(broken)} broken URL(s). Finding replacements …\n", flush=True)

    patch_map: Dict[str, Dict] = {}

    for id_ in broken:
        candidates = find_replacements(id_, all_rows, in_use)
        if not candidates:
            print(f"  {id_}: no replacement found")
            continue

        print(f"  {id_} → replace with one of:")
        for c in candidates:
            flag = primary_flag(c) or "?"
            print(f"    [{flag}] {c['obj_id']}  {c['title'][:70]}")
        patch_map[id_] = candidates[0]

    if args.patch and patch_map:
        patched = patch_note(note_text, patch_map)
        note_path.write_text(patched)
        print(f"\nPatched {len(patch_map)} URL(s) in {args.note}")
    elif patch_map:
        print("\nRe-run with --patch to apply the first candidate automatically.")


if __name__ == "__main__":
    main()

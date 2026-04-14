#!/usr/bin/env python3
# Purpose:      Rewrite old GeMeA HTTPS minted URIs to urn:edm: URNs in .nt files
#               Old: <https://gemea.fiz-karlsruhe.de/edm/Agent/XXXXX>
#               New: <urn:edm:Agent:XXXXX>
# Usage:        python3 rewrite_nt_uris.py <folder> [--dry-run]
# Inputs:       folder — directory containing .nt files (searched recursively)
# Outputs:      .nt files rewritten in-place; originals backed up as .nt.bak
# Dependencies: standard library only
# Assumptions:  Minted URIs follow the pattern https://gemea.fiz-karlsruhe.de/edm/<Class>/<id>

import argparse
import re
import sys
from pathlib import Path

OLD_PREFIX = "https://gemea.fiz-karlsruhe.de/edm/"
PATTERN    = re.compile(r"https://gemea\.fiz-karlsruhe\.de/edm/([A-Za-z]+)/([A-Za-z0-9]+)")


def rewrite(match: re.Match) -> str:
    return f"urn:edm:{match.group(1)}:{match.group(2)}"


def process_file(path: Path, dry_run: bool) -> int:
    text = path.read_text(encoding="utf-8")
    new_text, count = PATTERN.subn(rewrite, text)
    if count == 0:
        return 0
    if not dry_run:
        path.with_suffix(".nt.bak").write_bytes(path.read_bytes())
        path.write_text(new_text, encoding="utf-8")
    return count


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", help="Directory containing .nt files")
    parser.add_argument("--dry-run", action="store_true", help="Report changes without writing")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"ERROR: not a directory: {folder}", file=sys.stderr)
        sys.exit(1)

    nt_files = sorted(folder.rglob("*.nt"))
    if not nt_files:
        print("No .nt files found.")
        return

    total_files = 0
    total_replacements = 0
    for path in nt_files:
        count = process_file(path, args.dry_run)
        if count:
            tag = "[dry-run] " if args.dry_run else ""
            print(f"{tag}{path}  ({count:,} replacements)")
            total_files += 1
            total_replacements += count

    print(f"\n{'Would rewrite' if args.dry_run else 'Rewrote'} {total_files} file(s), "
          f"{total_replacements:,} URI(s) total.")
    if not args.dry_run and total_files:
        print("Originals backed up as .nt.bak")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# Purpose:      Convert a JSON-LD file (plain or gzip-compressed) to N-Triples
# Usage:        python3 jsonld_to_nt.py <input.jsonld[.gz]> <output.nt>
# Inputs:       JSON-LD file, optionally gzip-compressed (.jsonld or .jsonld.gz)
# Outputs:      N-Triples file (.nt)
# Dependencies: rdflib  (pip install rdflib)
# Assumptions:  Input is valid JSON-LD; output path is writable;
#               ~4–6x uncompressed file size of RAM available

import gzip
import sys
from pathlib import Path

import rdflib


def convert(input_path: Path, output_path: Path) -> int:
    """Parse JSON-LD and serialize to N-Triples. Returns triple count."""
    g = rdflib.Graph()

    opener = gzip.open if input_path.suffix == ".gz" else open
    with opener(input_path, "rt", encoding="utf-8") as f:
        g.parse(f, format="json-ld")

    g.serialize(destination=str(output_path), format="nt", encoding="utf-8")
    return len(g)


def main() -> None:
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.jsonld[.gz]> <output.nt>", file=sys.stderr)
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Parsing {input_path} ...", flush=True)
    n = convert(input_path, output_path)
    print(f"Written {n:,} triples → {output_path}")


if __name__ == "__main__":
    main()

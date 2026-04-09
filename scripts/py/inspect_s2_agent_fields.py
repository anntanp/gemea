#!/usr/bin/env python3
# Purpose:      Inspect creator/contributor/publisher field structure in s2 sample
#               to identify literal-only, resource-only, and both (label+URI) entries
# Usage:        python3 inspect_s2_agent_fields.py <sample.json>
# Inputs:       sample.json — JSON array of cortex records (e.g. s2_sample_1000.json)
# Outputs:      stdout — counts and examples per field and value pattern
# Dependencies: standard library only
# Assumptions:  ProvidedCHO fields use DDB cortex dict format ($ / resource / lang)

import json
import sys
from pathlib import Path


FIELDS = ("creator", "contributor", "publisher")


def inspect(path: str) -> None:
    data = json.loads(Path(path).read_text())
    print(f"Records: {len(data):,}\n")

    for field in FIELDS:
        examples: dict[str, list] = {
            "literal_only": [],
            "resource_only": [],
            "both": [],
            "string": [],
        }
        for rec in data:
            cho = (rec.get("edm", {}).get("RDF") or {}).get("ProvidedCHO") or {}
            val = cho.get(field)
            if val is None:
                continue
            items = val if isinstance(val, list) else [val]
            for item in items:
                if isinstance(item, dict):
                    has_label    = bool(item.get("$"))
                    has_resource = bool(item.get("resource"))
                    if has_label and has_resource:
                        examples["both"].append(item)
                    elif has_label:
                        examples["literal_only"].append(item)
                    elif has_resource:
                        examples["resource_only"].append(item)
                elif isinstance(item, str) and item:
                    examples["string"].append(item)

        print(f"=== {field} ===")
        for kind, entries in examples.items():
            print(f"  {kind}: {len(entries)}")
            if entries:
                print(f"    e.g. {entries[0]}")
        print()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <sample.json>", file=sys.stderr)
        sys.exit(1)
    inspect(sys.argv[1])

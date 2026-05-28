"""
Purpose:    Regenerate prov-shared.nq from prov.duckdb metadata columns.
            Reads (uri, entity_type, label, url, identifier, isil, rec_type, provider_uri)
            from prov.duckdb and emits complete PROV-O N-Quads.
            Falls back to type-only triples for older DBs that lack metadata columns.
Usage:      python scripts/py/regen_prov_nq.py \
                --prov-db  gemea/data/parquet/prov.duckdb \
                --prov-out gemea/output/20260520/prov-shared.nq
Inputs:     prov.duckdb — prov_entities table
Outputs:    prov-shared.nq — N-Quads in graph/prov
Deps:       duckdb; goethe-faust/scripts on PYTHONPATH
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "goethe-faust" / "scripts"))

from transform.prescan import regenerate_prov_nq


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1].strip())
    ap.add_argument("--prov-db",  type=Path, required=True)
    ap.add_argument("--prov-out", type=Path, required=True)
    args = ap.parse_args()

    n = regenerate_prov_nq(args.prov_db, args.prov_out)
    print(f"Written {n} triples to {args.prov_out}")


if __name__ == "__main__":
    main()

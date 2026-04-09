#!/usr/bin/env python3
"""
Purpose:  Draw a random sample of titles for specified hierarchy types to
          evaluate whether they are literary/intellectual work titles or
          structural/physical labels. Used to inform the blanket-exclude
          decision in htype-filtering-adr.md.
Usage:    python scripts/analysis/sample_htype_titles.py [--htypes h1 h2 ...] [--n N]
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  stdout
Dependencies: pandas, pyarrow
Assumptions: Run from the gemea/ project root.
"""

import argparse
import pandas as pd
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--htypes", nargs="+",
                    default=["htype_027", "htype_029", "htype_016", "htype_028"])
parser.add_argument("--n", type=int, default=40,
                    help="Number of random titles to sample per htype")
parser.add_argument("--seed", type=int, default=99)
args = parser.parse_args()

HTYPE_LABELS = {
    "htype_027": "Vers", "htype_029": "Widmung",
    "htype_016": "Index", "htype_028": "Vorwort",
}

PARQUET = Path("data/out/s2/s2_meta.parquet")
df = pd.read_parquet(PARQUET, columns=["obj_id", "title", "hierarchy_type"])
df["title_clean"] = df["title"].fillna("").str.strip()
df = df[df["title_clean"] != ""]

for ht in args.htypes:
    sub = df[df["hierarchy_type"] == ht]
    label = HTYPE_LABELS.get(ht, ht)
    n = min(args.n, len(sub))
    sample = sub.sample(n, random_state=args.seed)[["obj_id", "title_clean"]]
    print(f"=== {ht} · {label}  (n={len(sub):,}, sample={n}) ===")
    for _, row in sample.iterrows():
        print(f"  {repr(row.title_clean[:110]):<115}  "
              f"https://www.deutsche-digitale-bibliothek.de/item/{row.obj_id}")
    print()

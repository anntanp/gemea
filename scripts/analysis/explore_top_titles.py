#!/usr/bin/env python3
"""
Purpose:  Print top-N most frequent titles per hierarchy_type to inform the
          pattern blocklists used by filter_content_titles.py.
Usage:    python scripts/analysis/explore_top_titles.py [--top N]
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  stdout
Dependencies: pandas, pyarrow
Assumptions: Run from the gemea/ project root.
"""

import argparse
import pandas as pd
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--top", type=int, default=50)
args = parser.parse_args()

PARQUET = Path("data/out/s2/s2_meta.parquet")

print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["title", "hierarchy_type"])
df = df[df["hierarchy_type"].notna() & ~df["hierarchy_type"].str.contains(" ", na=False)]
df["title_clean"] = df["title"].fillna("").str.strip()
df = df[df["title_clean"] != ""]

for ht, grp in df.groupby("hierarchy_type"):
    top = grp["title_clean"].value_counts().head(args.top)
    total = len(grp)
    print(f"\n=== {ht}  (total={total:,}, showing top {args.top}) ===")
    for title, cnt in top.items():
        print(f"  {cnt:>8,}  {repr(title[:120])}")

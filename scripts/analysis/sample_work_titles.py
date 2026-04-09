#!/usr/bin/env python3
"""
Purpose:  Sample mid-frequency titles classified as work_title for htype_001
          (Abschnitt) and htype_018 (Kapitel) to evaluate whether they are
          genuinely literary/intellectual work titles or structural headings.
          Prints ranks 31-150 by frequency (top-30 are already known structural).
Usage:    python scripts/analysis/sample_work_titles.py
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  stdout
Dependencies: pandas, pyarrow
Assumptions: Run from the gemea/ project root.
"""

import pandas as pd
from pathlib import Path

PARQUET = Path("data/out/s2/s2_meta.parquet")

df = pd.read_parquet(PARQUET, columns=["title", "hierarchy_type"])
df["title_clean"] = df["title"].fillna("").str.strip()

for ht, label in [("htype_001", "Abschnitt"), ("htype_018", "Kapitel")]:
    sub = df[(df["hierarchy_type"] == ht) & (df["title_clean"] != "")]
    vc = sub["title_clean"].value_counts()
    print(f"=== {ht} · {label}  (ranks 31–150 by frequency) ===")
    for title, cnt in vc.iloc[30:150].items():
        print(f"  {cnt:>7,}  {repr(title[:120])}")
    print()

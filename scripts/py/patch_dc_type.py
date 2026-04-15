#!/usr/bin/env python3
# Purpose:      Enrich de_titles_tokenized.parquet with all columns from s2_meta.parquet.
#               Columns already in the tokenized file (title, lang, dc_type, dates) are
#               replaced with the s2_meta versions. all_tokens and content_tokens are
#               preserved from the tokenized file.
# Usage:        python3 scripts/py/patch_dc_type.py
# Inputs:       data/out/s2/s2_meta.parquet
#               data/processed/de_titles_tokenized.parquet
# Outputs:      data/processed/de_titles_tokenized.parquet (columns enriched in-place)
# Dependencies: pandas, pyarrow
# Assumptions:  Run from gemea/ project root.

from pathlib import Path
import pandas as pd

SRC  = Path("data/out/s2/s2_meta.parquet")
DEST = Path("data/processed/de_titles_tokenized.parquet")
TMP  = Path(str(DEST) + ".tmp")

# Columns to keep exclusively from the tokenized file (not in s2_meta)
TOKENIZED_ONLY = ["all_tokens", "content_tokens", "dates"]

print(f"Loading {SRC} …")
src = pd.read_parquet(SRC)
print(f"  {len(src):,} rows, {len(src.columns)} columns: {list(src.columns)}")

print(f"Loading {DEST} …")
dest = pd.read_parquet(DEST)
print(f"  {len(dest):,} rows, {len(dest.columns)} columns: {list(dest.columns)}")

# Keep only obj_id + tokenized-only columns from dest; everything else comes from src
dest_slim = dest[["obj_id"] + TOKENIZED_ONLY]

out = src.merge(dest_slim, on="obj_id", how="right")
assert len(out) == len(dest), f"Row count changed: {len(out)} vs {len(dest)}"

print(f"Result: {len(out):,} rows, {len(out.columns)} columns: {list(out.columns)}")
print(f"dc_type nulls: {out['dc_type'].isna().sum():,}")
print(f"dc_type value_counts (top 10):\n{out['dc_type'].value_counts().head(10).to_string()}")

print(f"Writing {DEST} …")
out.to_parquet(TMP, index=False)
TMP.rename(DEST)
print(f"Done. {DEST.stat().st_size / 1024**2:.1f} MB")

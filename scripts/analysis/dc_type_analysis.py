#!/usr/bin/env python3
"""
Purpose:      Analyse dc_type values across all sector parquet files.
              For each provider: counts total URI entries (is_ext_uri=True),
              total literal entries (is_ext_uri=False), and distinct literal
              values. Produces a parallel per-sector summary.
Usage:        python scripts/analysis/dc_type_analysis.py [--parquet-dir DIR]
Inputs:       output/parquet/s*_meta.parquet  (one file per sector)
Outputs:      data/processed/dc_type_by_provider.csv
              data/processed/dc_type_by_sector.csv
Dependencies: pandas, pyarrow
Assumptions:  Run from the gemea/ project root.
              Files matching output/parquet/s*_meta.parquet are the canonical
              sector snapshots; output/YYYYMMDD/ variants are excluded.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

SECTOR_NAMES: dict[int, str] = {
    1: "Archive",
    2: "Library",
    3: "Monument",
    4: "Research",
    5: "Media",
    6: "Museum",
    7: "Other",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--parquet-dir",
        type=Path,
        default=Path("output/parquet"),
        help="Directory containing s*_meta.parquet files (default: output/parquet)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/processed"),
        help="Output directory for CSVs (default: data/processed)",
    )
    return p.parse_args()


def explode_dc_type(path: Path) -> pd.DataFrame:
    """Read one sector parquet and return a flat DataFrame of dc_type entries.

    Returns columns: provider_id, sector, name, is_ext_uri
    """
    log.info("Reading %s", path)
    table = pq.read_table(path, columns=["provider_id", "sector", "dc_type"])
    df = table.to_pandas()

    # Drop rows where dc_type is null or empty list
    df = df[df["dc_type"].map(lambda x: x is not None and len(x) > 0)]

    # Explode the list<CONCEPT_STRUCT> column into one row per entry
    df = df.explode("dc_type").reset_index(drop=True)
    df = df[df["dc_type"].notna()].copy()

    # Unpack the struct dict into flat columns
    df["name"] = df["dc_type"].map(lambda s: s["name"] if isinstance(s, dict) else s.as_py()["name"] if hasattr(s, "as_py") else None)
    df["is_ext_uri"] = df["dc_type"].map(lambda s: s["is_ext_uri"] if isinstance(s, dict) else s.as_py()["is_ext_uri"] if hasattr(s, "as_py") else None)

    return df[["provider_id", "sector", "name", "is_ext_uri"]]


def aggregate_provider(flat: pd.DataFrame) -> pd.DataFrame:
    """Compute URI count, literal count, distinct literals per provider."""
    uris = (
        flat[flat["is_ext_uri"] == True]
        .groupby("provider_id")
        .size()
        .rename("uri_count")
    )
    literals_df = flat[flat["is_ext_uri"] == False]
    literal_total = (
        literals_df.groupby("provider_id")
        .size()
        .rename("literal_count")
    )
    literal_distinct = (
        literals_df.groupby("provider_id")["name"]
        .nunique()
        .rename("literal_distinct")
    )
    result = (
        pd.concat([uris, literal_total, literal_distinct], axis=1)
        .fillna(0)
        .astype({"uri_count": int, "literal_count": int, "literal_distinct": int})
        .reset_index()
        .sort_values("provider_id")
    )
    return result


def aggregate_sector(flat: pd.DataFrame) -> pd.DataFrame:
    """Compute URI count, literal count, distinct literals per sector."""
    uris = (
        flat[flat["is_ext_uri"] == True]
        .groupby("sector")
        .size()
        .rename("uri_count")
    )
    literals_df = flat[flat["is_ext_uri"] == False]
    literal_total = (
        literals_df.groupby("sector")
        .size()
        .rename("literal_count")
    )
    literal_distinct = (
        literals_df.groupby("sector")["name"]
        .nunique()
        .rename("literal_distinct")
    )
    result = (
        pd.concat([uris, literal_total, literal_distinct], axis=1)
        .fillna(0)
        .astype({"uri_count": int, "literal_count": int, "literal_distinct": int})
        .reset_index()
    )
    result["sector_name"] = result["sector"].map(SECTOR_NAMES)
    result = result[["sector", "sector_name", "uri_count", "literal_count", "literal_distinct"]]
    result = result.sort_values("sector")
    return result


def main() -> None:
    args = parse_args()

    parquet_files = sorted(args.parquet_dir.glob("s*_meta.parquet"))
    if not parquet_files:
        log.error("No s*_meta.parquet files found in %s", args.parquet_dir)
        raise SystemExit(1)
    log.info("Found %d sector files: %s", len(parquet_files), [p.name for p in parquet_files])

    frames: list[pd.DataFrame] = []
    for path in parquet_files:
        frames.append(explode_dc_type(path))

    flat = pd.concat(frames, ignore_index=True)
    log.info("Total dc_type entries: %d", len(flat))

    provider_df = aggregate_provider(flat)
    sector_df = aggregate_sector(flat)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    provider_path = args.out_dir / "dc_type_by_provider.csv"
    sector_path = args.out_dir / "dc_type_by_sector.csv"

    provider_df.to_csv(provider_path, index=False)
    sector_df.to_csv(sector_path, index=False)

    log.info("Wrote %d provider rows → %s", len(provider_df), provider_path)
    log.info("Wrote %d sector rows → %s", len(sector_df), sector_path)

if __name__ == "__main__":
    main()

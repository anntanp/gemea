#!/usr/bin/env python3
"""
Purpose:      Count mediatype and hierarchy_type values per sector across all
              sector parquet files.
Usage:        python scripts/analysis/mediatype_htype_analysis.py [--parquet-dir DIR]
Inputs:       output/parquet/s*_meta.parquet  (one file per sector)
Outputs:      data/processed/mediatype_by_sector.csv
              data/processed/htype_by_sector.csv
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

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
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

MEDIATYPE_NAMES: dict[int, str] = {
    1: "Audio",
    2: "Photo",
    3: "Text",
    5: "Video",
    7: "Not Digitized",
}

# Stored as int16; codes are sequential from 1 (htype_001 → 1, htype_048 → 48)
HTYPE_NAMES: dict[int, str] = {
    1:  "Abschnitt",
    2:  "Anhang",
    3:  "Beigefügtes/enthaltenes Werk",
    4:  "Annotation",
    5:  "Anrede",
    6:  "Aufsatz",
    7:  "Band",
    8:  "Beilage",
    9:  "Einleitung",
    10: "Eintrag",
    11: "Faszikel",
    12: "Fragment",
    13: "Handschrift",
    14: "Heft",
    15: "Illustration",
    16: "Index",
    17: "Inhaltsverzeichnis",
    18: "Kapitel",
    19: "Karte",
    20: "Mehrbändiges Werk",
    21: "Monografie",
    22: "Musik",
    23: "Fortlaufendes Sammelwerk",
    24: "Privilegie",
    25: "Rezension",
    26: "Text",
    27: "Vers",
    28: "Vorwort",
    29: "Widmung",
    30: "Bestand/Findbuch Collection",
    31: "Gliederung/Findbuch Class",
    32: "Serie/Findbuch Serie",
    33: "Unterserie",
    34: "Archivale/Findbuch File",
    35: "Teil/Findbuch Item",
    36: "Bestandsserie",
    37: "Bestandsklassifikation",
    38: "Brief",
    39: "Konvolut",
    40: "Mappe",
    41: "Archiv",
    44: "Zeitung",
    45: "Jahrgang",
    46: "Monat",
    47: "Tag",
    48: "Tektonik",
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


def read_sector(path: Path) -> pd.DataFrame:
    log.info("Reading %s", path)
    table = pq.read_table(path, columns=["sector", "mediatype", "hierarchy_type"])
    return table.to_pandas()


def count_per_sector(
    frames: list[pd.DataFrame],
    col: str,
    label_map: dict[int, str],
    label_col: str,
) -> pd.DataFrame:
    """Cross-tab: (sector, col) → count + pct_of_sector."""
    combined = pd.concat(frames, ignore_index=True)[["sector", col]]
    combined[col] = combined[col].astype("Int64")  # nullable int to preserve NaN

    total_per_sector = combined.groupby("sector").size().rename("sector_total")

    counts = (
        combined.groupby(["sector", col], dropna=False)
        .size()
        .rename("count")
        .reset_index()
    )
    counts = counts.merge(total_per_sector, on="sector")
    counts["pct"] = (counts["count"] / counts["sector_total"] * 100).round(1)
    counts["sector_name"] = counts["sector"].map(SECTOR_NAMES)
    counts[label_col] = counts[col].map(lambda v: label_map.get(int(v), "Unknown") if pd.notna(v) else "Null/Missing")

    counts = counts[["sector", "sector_name", col, label_col, "count", "pct"]].sort_values(
        ["sector", col]
    )
    return counts


def main() -> None:
    args = parse_args()

    parquet_files = sorted(args.parquet_dir.glob("s*_meta.parquet"))
    if not parquet_files:
        log.error("No s*_meta.parquet files found in %s", args.parquet_dir)
        raise SystemExit(1)
    log.info("Found %d sector files: %s", len(parquet_files), [p.name for p in parquet_files])

    frames: list[pd.DataFrame] = [read_sector(p) for p in parquet_files]

    mt_df = count_per_sector(frames, "mediatype", MEDIATYPE_NAMES, "mediatype_label")
    ht_df = count_per_sector(frames, "hierarchy_type", HTYPE_NAMES, "htype_label")

    args.out_dir.mkdir(parents=True, exist_ok=True)

    mt_path = args.out_dir / "mediatype_by_sector.csv"
    ht_path = args.out_dir / "htype_by_sector.csv"

    mt_df.to_csv(mt_path, index=False)
    ht_df.to_csv(ht_path, index=False)

    log.info("Wrote %d rows → %s", len(mt_df), mt_path)
    log.info("Wrote %d rows → %s", len(ht_df), ht_path)

    # Print summary to stdout for the note
    print("\n=== TOTAL OBJECTS PER SECTOR ===")
    combined = pd.concat(frames, ignore_index=True)
    totals = combined.groupby("sector").size().reset_index(name="total")
    totals["sector_name"] = totals["sector"].map(SECTOR_NAMES)
    totals["pct"] = (totals["total"] / totals["total"].sum() * 100).round(1)
    print(totals[["sector", "sector_name", "total", "pct"]].to_string(index=False))
    print(f"Grand total: {totals['total'].sum():,}")

    print("\n=== MEDIATYPE BY SECTOR (pivot: sector × mediatype) ===")
    mt_pivot = mt_df.pivot_table(
        index=["sector", "sector_name"],
        columns="mediatype_label",
        values="count",
        fill_value=0,
    ).reset_index()
    print(mt_pivot.to_string(index=False))

    print("\n=== HTYPE BY SECTOR (top 10 per sector) ===")
    for sector_id in sorted(ht_df["sector"].dropna().unique()):
        sub = ht_df[ht_df["sector"] == sector_id].nlargest(10, "count")
        print(f"\nSector {sector_id} ({SECTOR_NAMES.get(int(sector_id), '?')}):")
        print(sub[["htype_label", "count", "pct"]].to_string(index=False))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Purpose:  Count primary (is_part_of=False) and secondary (is_part_of=True) DDB objects
          by hierarchy_type, producing a summary CSV and a stacked bar PNG.
Usage:    python scripts/analysis/count_hierarchy_types.py
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  data/processed/hierarchy_type_counts.csv
          data/processed/hierarchy_type_counts.png
Dependencies: pandas, pyarrow, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET = Path("data/out/s2/s2_meta.parquet")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_OUT = OUT_DIR / "hierarchy_type_counts.csv"
PNG_OUT = OUT_DIR / "hierarchy_type_counts.png"

# ── htype code → German label ──────────────────────────────────────────────────
HTYPE_LABELS = {
    "htype_001": "Abschnitt",
    "htype_002": "Anhang",
    "htype_003": "Beigefügtes/enthaltenes Werk",
    "htype_004": "Annotation",
    "htype_005": "Anrede",
    "htype_006": "Aufsatz",
    "htype_007": "Band",
    "htype_008": "Beilage",
    "htype_009": "Einleitung",
    "htype_010": "Eintrag",
    "htype_011": "Faszikel",
    "htype_012": "Fragment",
    "htype_013": "Handschrift",
    "htype_014": "Heft",
    "htype_015": "Illustration",
    "htype_016": "Index",
    "htype_017": "Inhaltsverzeichnis",
    "htype_018": "Kapitel",
    "htype_019": "Karte",
    "htype_020": "Mehrbändiges Werk",
    "htype_021": "Monografie",
    "htype_022": "Musik",
    "htype_023": "Fortlaufendes Sammelwerk",
    "htype_024": "Privilegie",
    "htype_025": "Rezension",
    "htype_026": "Text",
    "htype_027": "Vers",
    "htype_028": "Vorwort",
    "htype_029": "Widmung",
    "htype_030": "Bestand/Findbuch Collection",
    "htype_031": "Gliederung/Findbuch Class",
    "htype_032": "Serie/Findbuch Serie",
    "htype_033": "Unterserie",
    "htype_034": "Archivale/Findbuch File",
    "htype_035": "Teil/Findbuch Item",
    "htype_036": "Bestandsserie",
    "htype_037": "Bestandsklassifikation",
    "htype_038": "Brief",
    "htype_039": "Konvolut",
    "htype_040": "Mappe",
    "htype_041": "Archiv",
    "htype_044": "Zeitung",
    "htype_045": "Jahrgang",
    "htype_046": "Monat",
    "htype_047": "Tag",
    "htype_048": "Tektonik",
}

# ── load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "hierarchy_type", "is_part_of"])
print(f"  {len(df):,} rows")

# ── count ──────────────────────────────────────────────────────────────────────
# fill nulls so they appear as "UNK" rather than being silently dropped by groupby
df["hierarchy_type"] = df["hierarchy_type"].fillna("UNK")

counts = (
    df.groupby(["hierarchy_type", "is_part_of"])
    .size()
    .reset_index(name="count")
)
counts["category"] = counts["is_part_of"].map({False: "primary", True: "secondary"})
def resolve_label(code):
    parts = str(code).split()
    return " | ".join(HTYPE_LABELS.get(p, p) for p in parts)

counts["htype_label"] = counts["hierarchy_type"].apply(resolve_label)

# pivot for easier manipulation
pivot = counts.pivot_table(
    index=["hierarchy_type", "htype_label"],
    columns="category",
    values="count",
    fill_value=0,
).reset_index()
pivot.columns.name = None
for col in ("primary", "secondary"):
    if col not in pivot.columns:
        pivot[col] = 0
pivot["total"] = pivot["primary"] + pivot["secondary"]
pivot = pivot.sort_values("total", ascending=False)

# flat CSV with one row per (htype, category)
csv_df = counts[["hierarchy_type", "htype_label", "category", "count"]].sort_values(
    ["hierarchy_type", "category"]
)

# totals row
totals = pd.DataFrame([
    {"hierarchy_type": "TOTAL", "htype_label": "TOTAL", "category": "primary",
     "count": int(pivot["primary"].sum())},
    {"hierarchy_type": "TOTAL", "htype_label": "TOTAL", "category": "secondary",
     "count": int(pivot["secondary"].sum())},
])
csv_df = pd.concat([csv_df, totals], ignore_index=True)
csv_df.to_csv(CSV_OUT, index=False)
print(f"CSV saved → {CSV_OUT}")

total_primary   = int(pivot["primary"].sum())
total_secondary = int(pivot["secondary"].sum())
print(f"Primary objects:   {total_primary:>12,}")
print(f"Secondary objects: {total_secondary:>12,}")
print(f"Total:             {total_primary + total_secondary:>12,}")

# ── plot ───────────────────────────────────────────────────────────────────────
# drop htypes with zero objects (shouldn't happen, but guard)
plot_df = pivot[pivot["total"] > 0].copy()
plot_df = plot_df.set_index("htype_label")

fig, axes = plt.subplots(1, 2, figsize=(16, max(6, len(plot_df) * 0.35)))

for ax, col, color, title in [
    (axes[0], "primary",   "#4C72B0", "Primary objects (is_part_of = False)"),
    (axes[1], "secondary", "#DD8452", "Secondary objects (is_part_of = True)"),
]:
    series = plot_df[col].sort_values(ascending=True)
    bars = ax.barh(series.index, series.values, color=color, edgecolor="none")
    ax.bar_label(bars, labels=[f"{v:,}" for v in series.values], padding=4, fontsize=7)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel("Object count")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.tick_params(axis="y", labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)

unk_count = int(pivot.loc[pivot["hierarchy_type"] == "UNK", "total"].sum()) if "UNK" in pivot["hierarchy_type"].values else 0
fig.suptitle(
    f"DDB Sector 2 — hierarchy_type breakdown\n"
    f"Primary: {total_primary:,}  |  Secondary: {total_secondary:,}  |  Total: {total_primary + total_secondary:,}"
    + (f"  |  UNK (null hierarchy_type): {unk_count:,}" if unk_count else ""),
    fontsize=11,
)
fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
print(f"PNG saved → {PNG_OUT}")

#!/usr/bin/env python3
"""
Purpose:  Visualise DDB Sector 2 objects by language and creation/issuance year.
          Year is extracted from dc_created (first element), falling back to
          dc_issued (first element). Multi-decade gaps are shown as-is.
Usage:    python scripts/analysis/lang_by_year.py [options]
          python scripts/analysis/lang_by_year.py --normalize
          python scripts/analysis/lang_by_year.py --bucket year --top 5 --min-year 1800
Options:  --bucket {decade,year}  time resolution (default: decade)
          --top N                 distinct language series in chart (default: 10)
          --min-year INT          earliest year to include (default: 1400)
          --max-year INT          latest year to include (default: 2025)
          --normalize             plot % share per bucket instead of raw counts
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  data/processed/lang_by_year.csv
          notes/images/lang_by_year.png
Dependencies: pandas, pyarrow, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--bucket", choices=["decade", "year"], default="decade")
parser.add_argument("--top", type=int, default=10)
parser.add_argument("--min-year", type=int, default=1400)
parser.add_argument("--max-year", type=int, default=2025)
parser.add_argument("--normalize", action="store_true",
                    help="Plot %% share per bucket instead of raw counts")
args = parser.parse_args()

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET = Path("data/out/s2/s2_meta.parquet")
CSV_OUT = Path("data/processed/lang_by_year.csv")
PNG_OUT = Path("notes/images/lang_by_year.png")
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

# ── load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "lang", "dc_created", "dc_issued"])
total = len(df)
print(f"  {total:,} rows")


# ── year extraction ────────────────────────────────────────────────────────────
def first_str(val):
    """Return first non-empty string from a list/array or scalar, else None."""
    if val is None:
        return None
    if isinstance(val, (list, np.ndarray)):
        for v in val:
            if v is None:
                continue
            try:
                if pd.isna(v):
                    continue
            except (TypeError, ValueError):
                pass
            s = str(v).strip()
            if s:
                return s
        return None
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass
    s = str(val).strip()
    return s if s else None


def extract_year(created, issued):
    raw = first_str(created) or first_str(issued)
    if raw is None:
        return None
    try:
        y = int(raw[:4])
        return y if args.min_year <= y <= args.max_year else None
    except (ValueError, IndexError):
        return None


print("Extracting years …")
df["year"] = df.apply(lambda r: extract_year(r["dc_created"], r["dc_issued"]), axis=1)

n_with_year = df["year"].notna().sum()
n_created   = df["dc_created"].apply(lambda v: bool(first_str(v))).sum()
n_issued    = df["dc_issued"].apply(lambda v: bool(first_str(v))).sum()

print(f"  dc_created non-empty : {n_created:>10,}  ({n_created / total * 100:.1f}%)")
print(f"  dc_issued  non-empty : {n_issued:>10,}  ({n_issued  / total * 100:.1f}%)")
print(f"  valid year extracted : {n_with_year:>10,}  ({n_with_year / total * 100:.1f}%)")
print(f"  no valid year        : {total - n_with_year:>10,}  ({(total - n_with_year) / total * 100:.1f}%)")

# ── filter to objects with a valid year ────────────────────────────────────────
df = df[df["year"].notna()].copy()
df["year"] = df["year"].astype(int)

if args.bucket == "decade":
    df["bucket"] = (df["year"] // 10) * 10
else:
    df["bucket"] = df["year"]

# ── language normalisation ─────────────────────────────────────────────────────
df["lang"] = df["lang"].fillna("(none)").str.strip()
df.loc[df["lang"] == "", "lang"] = "(none)"

# ── counts ─────────────────────────────────────────────────────────────────────
counts = (
    df.groupby(["bucket", "lang"])
    .size()
    .reset_index(name="count")
)

counts.to_csv(CSV_OUT, index=False)
print(f"\nCSV saved → {CSV_OUT}  ({len(counts):,} rows, {counts['lang'].nunique()} distinct langs)")

# ── identify top-N languages ───────────────────────────────────────────────────
top_langs = (
    counts.groupby("lang")["count"].sum()
    .sort_values(ascending=False)
    .head(args.top)
    .index.tolist()
)
print(f"Top {args.top} languages: {', '.join(top_langs)}")

# ── pivot for plotting ─────────────────────────────────────────────────────────
def make_pivot(df_counts, lang_col):
    piv = df_counts.pivot_table(
        index="bucket", columns=lang_col, values="count", fill_value=0
    )
    return piv

# remap: non-top languages → "other"
counts["lang_plot"] = counts["lang"].where(counts["lang"].isin(top_langs), "other")
plot_counts = counts.groupby(["bucket", "lang_plot"])["count"].sum().reset_index(name="count")
piv = make_pivot(plot_counts, "lang_plot")

# column order: top langs sorted by total, then "other"
col_order = [l for l in top_langs if l in piv.columns]
if "other" in piv.columns:
    col_order.append("other")
piv = piv[col_order]

if args.normalize:
    row_totals = piv.sum(axis=1)
    piv = piv.div(row_totals, axis=0) * 100

# ── plot ───────────────────────────────────────────────────────────────────────
# Color palette: qualitative, colorblind-friendly-ish
PALETTE = [
    "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#c0392b",
    "#16a085", "#d35400", "#2c3e50", "#f39c12", "#1abc9c",
]
colors = {lang: PALETTE[i % len(PALETTE)] for i, lang in enumerate(top_langs)}
colors["other"] = "#bdc3c7"

fig, ax = plt.subplots(figsize=(14, 6))

x = piv.index.values
bottom = pd.Series(0.0, index=piv.index)
for col in piv.columns:
    color = colors.get(col, "#bdc3c7")
    ec = "#c0392b" if col == "(none)" else "none"
    fc = "#fadbd8" if col == "(none)" else color
    ax.fill_between(x, bottom, bottom + piv[col], label=col,
                    color=fc, edgecolor=ec, linewidth=0.3, alpha=0.9)
    bottom = bottom + piv[col]

ax.set_xlabel(f"{'Decade' if args.bucket == 'decade' else 'Year'}")
ax.set_xlim(x[0], x[-1])

if args.normalize:
    ax.set_ylabel("Share (%)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylim(0, 100)
else:
    ax.set_ylabel("Object count")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="upper left", fontsize=8, ncol=2, framealpha=0.7)

mode = "% share" if args.normalize else "object count"
bucket_label = "decade" if args.bucket == "decade" else "year"
ax.set_title(
    f"DDB Sector 2 — language distribution by {bucket_label}  [{mode}]\n"
    f"Total: {total:,} objects  ·  With valid year: {n_with_year:,} ({n_with_year / total * 100:.1f}%)  "
    f"·  Year range: {args.min_year}–{args.max_year}  ·  Top {args.top} languages",
    fontsize=9.5,
)

fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
print(f"PNG saved → {PNG_OUT}")

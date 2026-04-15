#!/usr/bin/env python3
"""
Purpose:  Visualise DDB Sector 2 objects by language and creation/issuance year.
          Year is extracted from dc_created (first element), falling back to
          dc_issued (first element). Multi-decade gaps are shown as-is.
Usage:    python scripts/analysis/lang_by_year.py [options]
          python scripts/analysis/lang_by_year.py --bucket year --top 5 --min-year 1800
Options:  --bucket {decade,year}  time resolution (default: decade)
          --top N                 number of languages shown (default: 10)
          --min-year INT          earliest year to include (default: 1400)
          --max-year INT          latest year to include (default: 2025)
          und, zxx, (none) are always excluded (undefined / no linguistic content)
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
# Language codes that carry no linguistic information — excluded from all output
EXCLUDE_LANGS = {"und", "zxx", "(none)"}

parser = argparse.ArgumentParser()
parser.add_argument("--bucket", choices=["decade", "year"], default="decade")
parser.add_argument("--top", type=int, default=10)
parser.add_argument("--min-year", type=int, default=0)
parser.add_argument("--max-year", type=int, default=2025)
args = parser.parse_args()

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET = Path("data/out/s2/s2_meta.parquet")
CSV_OUT = Path("data/processed/lang_by_year.csv")
PNG_OUT  = Path("notes/images/lang_by_year.png")
PNG_OUT2 = Path("notes/images/lang_by_year_no_top1.png")
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

# ── language normalisation & exclusion ────────────────────────────────────────
df["lang"] = df["lang"].fillna("(none)").str.strip()
df.loc[df["lang"] == "", "lang"] = "(none)"
df = df[~df["lang"].isin(EXCLUDE_LANGS)]

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

# ── helpers ────────────────────────────────────────────────────────────────────
def make_pivot(df_counts, lang_col):
    return df_counts.pivot_table(
        index="bucket", columns=lang_col, values="count", fill_value=0
    )


def gauss_smooth(y, sigma=12):
    r = int(4 * sigma)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k /= k.sum()
    pad = np.pad(y, r, mode="reflect")
    return np.convolve(pad, k, mode="valid")[:len(y)]


PALETTE = [
    "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#c0392b",
    "#16a085", "#d35400", "#2c3e50", "#f39c12", "#1abc9c",
]


def plot_lang_chart(counts, lang_list, title_line2, png_path):
    """Render a variable-width Marimekko stacked-area chart for lang_list."""
    plot_counts = counts[counts["lang"].isin(lang_list)]
    piv = make_pivot(plot_counts, "lang")
    col_order = [l for l in lang_list if l in piv.columns]
    piv = piv[col_order]

    row_totals = piv.sum(axis=1)
    piv_pct = piv.div(row_totals, axis=0) * 100

    buckets    = piv.index.values.astype(float)
    counts_per = row_totals.values.astype(float)
    total_objs = counts_per.sum()
    year_span  = buckets[-1] - buckets[0]

    widths  = counts_per / total_objs * year_span
    lefts   = np.concatenate([[buckets[0]], buckets[0] + np.cumsum(widths[:-1])])
    centres = lefts + widths / 2

    x_fine = np.linspace(centres[0], centres[-1], 800)

    smooth_arr = []
    for col in piv_pct.columns:
        y_interp = np.interp(x_fine, centres, piv_pct[col].values)
        smooth_arr.append(np.clip(gauss_smooth(y_interp), 0, None))
    smooth_arr = np.array(smooth_arr)
    col_sums = smooth_arr.sum(axis=0)
    col_sums[col_sums == 0] = 1
    smooth_arr = smooth_arr / col_sums * 100

    colors     = {lang: PALETTE[i % len(PALETTE)] for i, lang in enumerate(lang_list)}
    color_list = [colors[col] for col in piv_pct.columns]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.stackplot(x_fine, smooth_arr, labels=list(piv_pct.columns),
                 colors=color_list, alpha=0.88)

    # X-ticks at century years; skip those too close together (< 2% of x-range)
    tick_years_all = [b for b in buckets if b % 100 == 0 and b >= buckets[0]]
    tick_pos_all   = [centres[np.argmin(np.abs(buckets - ty))] for ty in tick_years_all]
    x_range = x_fine[-1] - x_fine[0]
    min_gap = 0.02 * x_range
    tick_years, tick_pos, last_pos = [], [], -np.inf
    for ty, tp in zip(tick_years_all, tick_pos_all):
        if tp - last_pos >= min_gap:
            tick_years.append(ty)
            tick_pos.append(tp)
            last_pos = tp
    ax.set_xticks(tick_pos)
    ax.set_xticklabels([str(int(ty)) for ty in tick_years], fontsize=7.5)

    ax.set_xlabel("Year  (x-axis width ∝ object count)")
    ax.set_xlim(x_fine[0], x_fine[-1])
    ax.set_ylabel("Share (%)")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_ylim(0, 100)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(loc="lower right", fontsize=8, ncol=2, framealpha=0.7)
    ax.set_title(
        f"Language Distribution in DDB Bibliographic Titles\n{title_line2}",
        fontsize=9.5,
    )
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG saved → {png_path}")


# ── chart 1: all top-N ─────────────────────────────────────────────────────────
title2_all = (
    f"top {args.top} languages  ·  excluded: und, zxx, (none)  "
    f"·  {n_with_year:,} objects with valid year ({n_with_year / total * 100:.1f}%)"
)
plot_lang_chart(counts, top_langs, title2_all, PNG_OUT)

# ── chart 2: top-N excluding the #1 language ──────────────────────────────────
top1 = top_langs[0]
top_langs_no1 = (
    counts[~counts["lang"].isin([top1])]
    .groupby("lang")["count"].sum()
    .sort_values(ascending=False)
    .head(args.top)
    .index.tolist()
)
title2_no1 = (
    f"top {args.top} languages  ·  excluded: und, zxx, (none), {top1}  "
    f"·  {n_with_year:,} objects with valid year ({n_with_year / total * 100:.1f}%)"
)
plot_lang_chart(counts, top_langs_no1, title2_no1, PNG_OUT2)

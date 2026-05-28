#!/usr/bin/env python3
"""
Purpose:  Analyse DDB objects by language × year and by date-type coverage across all sectors.
          Language: lang_obj (object-level), falling back to lang_title.
          Year: extracted from dates list-of-structs; prefers type 'creation' over
          'publication' over others; within a struct prefers 'begin' then 'value'.
Usage:    python scripts/analysis/lang_by_year_all.py [options]
          python scripts/analysis/lang_by_year_all.py --sectors 1 2 3
          python scripts/analysis/lang_by_year_all.py --bucket year --top 5 --min-year 1800
Options:  --sectors N [N ...]    sectors to include (default: 1 2 3 4 5 6 7)
          --bucket {decade,year} time resolution (default: decade)
          --top N                number of languages shown (default: 10)
          --min-year INT         earliest year to include (default: 1400)
          --max-year INT         latest year to include (default: 2026)
          und, zxx, (none) are always excluded (undefined / no linguistic content)
Inputs:   output/parquet/s<n>_meta.parquet  (for each requested sector)
Outputs:  data/processed/lang_by_year_all.csv    — bucket × lang counts
          data/processed/date_types_all.csv       — date-type coverage per sector
          notes/images/lang_by_year_all.png
          notes/images/lang_by_year_all_no_top1.png
Dependencies: pandas, pyarrow, matplotlib, numpy
Assumptions: Run from the gemea/ project root.
"""

import argparse
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from collections import Counter
from pathlib import Path

EXCLUDE_LANGS    = {"und", "zxx", "(none)"}
DATE_TYPE_PRIO   = {"creation": 0, "publication": 1}

parser = argparse.ArgumentParser()
parser.add_argument("--sectors", type=int, nargs="+", default=list(range(1, 8)), metavar="N")
parser.add_argument("--bucket",   choices=["decade", "year"], default="decade")
parser.add_argument("--top",      type=int, default=10)
parser.add_argument("--min-year", type=int, default=1400)
parser.add_argument("--max-year", type=int, default=2026)
args = parser.parse_args()

PARQUET_DIR = Path("output/parquet")
CSV_LANG    = Path("data/processed/lang_by_year_all.csv")
CSV_DATES   = Path("data/processed/date_types_all.csv")
PNG_OUT     = Path("notes/images/lang_by_year_all.png")
PNG_OUT2    = Path("notes/images/lang_by_year_all_no_top1.png")
for p in (CSV_LANG.parent, PNG_OUT.parent):
    p.mkdir(parents=True, exist_ok=True)


# ── helpers ───────────────────────────────────────────────────────────────────

def best_year(dates_val, min_year: int, max_year: int):
    """Return the best year int from a dates list-of-structs, or None."""
    if not dates_val:  # None or empty list
        return None
    rows = sorted(dates_val, key=lambda d: DATE_TYPE_PRIO.get(d.get("type", ""), 2))
    for d in rows:
        for field in ("begin", "value"):
            raw = d.get(field)
            if not raw:
                continue
            s = str(raw).strip()
            if not s:
                continue
            try:
                y = int(s[:4])
                if min_year <= y <= max_year:
                    return y
            except (ValueError, IndexError):
                continue
    return None


def resolve_lang(lo, lt):
    """lang_obj first, lang_title fallback."""
    for v in (lo, lt):
        if v and isinstance(v, str) and v.strip():
            return v.strip()
    return "(none)"


# ── load + per-sector stats ───────────────────────────────────────────────────

frames       = []
date_records = []

for s in sorted(args.sectors):
    path = PARQUET_DIR / f"s{s}_meta.parquet"
    if not path.exists():
        print(f"  WARNING: {path} not found — skipping sector {s}")
        continue
    print(f"Loading {path} …")
    t    = pq.read_table(path, columns=["obj_id", "lang_obj", "lang_title", "dates"])
    df_s = t.select(["obj_id", "lang_obj", "lang_title"]).to_pandas()
    df_s["dates"] = t["dates"].to_pylist()   # list[list[dict] | None]
    n    = len(df_s)
    print(f"  {n:,} rows")

    # ── date-type analysis ─────────────────────────────────────────────────────
    type_counter   = Counter()   # date-type label → struct count
    objs_with_date = 0
    for dates_val in df_s["dates"]:
        if dates_val is not None and len(dates_val) > 0:
            objs_with_date += 1
            for d in dates_val:
                type_counter[d.get("type") or "(none)"] += 1

    for dtype, cnt in type_counter.items():
        date_records.append({"sector": s, "date_type": dtype, "struct_count": cnt})
    date_records.append({
        "sector": s, "date_type": "_TOTAL_OBJECTS",    "struct_count": n
    })
    date_records.append({
        "sector": s, "date_type": "_OBJECTS_WITH_DATE", "struct_count": objs_with_date
    })

    df_s["_sector"] = s
    frames.append(df_s)

df    = pd.concat(frames, ignore_index=True)
total = len(df)
print(f"\nTotal: {total:,} rows across sectors {sorted(args.sectors)}")

# ── save date-type CSV ────────────────────────────────────────────────────────

df_dates = pd.DataFrame(date_records).sort_values(["sector", "date_type"])
df_dates.to_csv(CSV_DATES, index=False)
print(f"Date-type CSV saved → {CSV_DATES}  ({len(df_dates):,} rows)")

# print a quick pivot
pivot = (
    df_dates[~df_dates["date_type"].str.startswith("_")]
    .pivot_table(index="date_type", columns="sector", values="struct_count", fill_value=0)
)
print("\nDate-type struct counts per sector:")
print(pivot.to_string())


# ── language + year ───────────────────────────────────────────────────────────

print("\nResolving language …")
df["lang"] = df.apply(lambda r: resolve_lang(r["lang_obj"], r["lang_title"]), axis=1)

n_lang_obj   = df["lang_obj"].notna().sum()
n_lang_title = df["lang_title"].notna().sum()
n_lang_none  = (df["lang"] == "(none)").sum()
print(f"  lang_obj   non-null : {n_lang_obj:>10,}  ({n_lang_obj  / total * 100:.1f}%)")
print(f"  lang_title non-null : {n_lang_title:>10,}  ({n_lang_title / total * 100:.1f}%)")
print(f"  resolved (none)     : {n_lang_none:>10,}  ({n_lang_none  / total * 100:.1f}%)")

print("Extracting years …")
df["year"] = df["dates"].apply(lambda v: best_year(v, args.min_year, args.max_year))

n_with_year = df["year"].notna().sum()
print(f"  valid year extracted : {n_with_year:>10,}  ({n_with_year / total * 100:.1f}%)")
print(f"  no valid year        : {total - n_with_year:>10,}  ({(total - n_with_year) / total * 100:.1f}%)")

df = df[df["year"].notna()].copy()
df["year"]   = df["year"].astype(int)
df["bucket"] = (df["year"] // 10) * 10 if args.bucket == "decade" else df["year"]
df = df[~df["lang"].isin(EXCLUDE_LANGS)]

counts = (
    df.groupby(["bucket", "lang"])
    .size()
    .reset_index(name="count")
)
counts.to_csv(CSV_LANG, index=False)
print(f"\nLang CSV saved → {CSV_LANG}  ({len(counts):,} rows, {counts['lang'].nunique()} distinct langs)")

top_langs = (
    counts.groupby("lang")["count"].sum()
    .sort_values(ascending=False)
    .head(args.top)
    .index.tolist()
)
print(f"Top {args.top} languages: {', '.join(top_langs)}")


# ── plot ──────────────────────────────────────────────────────────────────────

PALETTE = [
    "#2980b9", "#27ae60", "#e67e22", "#8e44ad", "#c0392b",
    "#16a085", "#d35400", "#2c3e50", "#f39c12", "#1abc9c",
]


def gauss_smooth(y, sigma=12):
    r   = int(4 * sigma)
    k   = np.exp(-0.5 * (np.arange(-r, r + 1) / sigma) ** 2)
    k  /= k.sum()
    pad = np.pad(y, r, mode="reflect")
    return np.convolve(pad, k, mode="valid")[: len(y)]


def plot_lang_chart(counts_df, lang_list, title_line2, png_path):
    plot_counts = counts_df[counts_df["lang"].isin(lang_list)]
    piv = plot_counts.pivot_table(
        index="bucket", columns="lang", values="count", fill_value=0
    )
    col_order = [l for l in lang_list if l in piv.columns]
    piv = piv[col_order]

    row_totals = piv.sum(axis=1)
    piv_pct    = piv.div(row_totals, axis=0) * 100
    buckets    = piv.index.values.astype(float)
    counts_per = row_totals.values.astype(float)
    total_objs = counts_per.sum()
    year_span  = buckets[-1] - buckets[0]

    widths  = counts_per / total_objs * year_span
    lefts   = np.concatenate([[buckets[0]], buckets[0] + np.cumsum(widths[:-1])])
    centres = lefts + widths / 2
    x_fine  = np.linspace(centres[0], centres[-1], 800)

    smooth_arr = []
    for col in piv_pct.columns:
        y_interp = np.interp(x_fine, centres, piv_pct[col].values)
        smooth_arr.append(np.clip(gauss_smooth(y_interp), 0, None))
    smooth_arr = np.array(smooth_arr)
    col_sums   = smooth_arr.sum(axis=0)
    col_sums[col_sums == 0] = 1
    smooth_arr = smooth_arr / col_sums * 100

    colors     = {lang: PALETTE[i % len(PALETTE)] for i, lang in enumerate(lang_list)}
    color_list = [colors[col] for col in piv_pct.columns]

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.stackplot(x_fine, smooth_arr, labels=list(piv_pct.columns),
                 colors=color_list, alpha=0.88)

    tick_years_all = [b for b in buckets if b % 100 == 0 and b >= buckets[0]]
    tick_pos_all   = [centres[np.argmin(np.abs(buckets - ty))] for ty in tick_years_all]
    x_range        = x_fine[-1] - x_fine[0]
    min_gap        = 0.02 * x_range
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
    sectors_str = ", ".join(f"s{s}" for s in sorted(args.sectors))
    ax.set_title(
        f"Language Distribution in DDB Objects — Sectors {sectors_str}\n{title_line2}",
        fontsize=9.5,
    )
    fig.tight_layout()
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"PNG saved → {png_path}")


title2_all = (
    f"top {args.top} languages  ·  excluded: und, zxx, (none)  "
    f"·  {n_with_year:,} objects with valid year ({n_with_year / total * 100:.1f}%)"
)
plot_lang_chart(counts, top_langs, title2_all, PNG_OUT)

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

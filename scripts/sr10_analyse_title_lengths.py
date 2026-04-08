# Purpose:      Load data/DF_DE_TITLES_20240125b.pkl and plot title-length
#               distribution per year bucket. Length is taken from the
#               pre-computed 'all_tokens' and 'content_tokens' columns;
#               both are shown together on the median panel. Year is taken
#               from the 'dates' column; titles with no 'dates' value fall
#               back to a regex extraction from the title string.
# Usage:        python scripts/sr10_analyse_title_lengths.py
#               python scripts/sr10_analyse_title_lengths.py --data PATH --output-dir PATH
# Inputs:       data/DF_DE_TITLES_20240125b.pkl — DataFrame with obj_id, title,
#                 all_tokens, content_tokens, dates columns
# Outputs:      notes/images/fig_title_lengths.png — stacked bar + dual median chart
#               output/title-length-analysis.json  — bucketed counts and medians
# Dependencies: pandas, matplotlib
# Assumptions:  'dates' column is a string year (e.g. '1931') or NaN.
#               'all_tokens' is the spaCy token count incl. stopwords and punctuation.
#               'content_tokens' is the count with stopwords removed (punct. retained).

import re
import json
import argparse
import pickle
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT       = Path(__file__).resolve().parent.parent
DATA_PATH  = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_DIR = ROOT / "notes" / "images"

SHORT_MAX  = 4   # ≤ 4 tokens  → short   (p25)
MEDIUM_MAX = 14  # 5–14 tokens → medium  (p25–p75)  |  >14 → long

# Fallback: extract year from title string (1400–2029)
YEAR_RE = re.compile(r"\b(?:1[4-9]\d{2}|20[012]\d)\b")

MAX_BINS = 40  # widest bucket before stepping up


# ── helpers ───────────────────────────────────────────────────────────────────

def year_from_title(title: str):
    """Last 4-digit year found in the title string, or None."""
    m = list(YEAR_RE.finditer(str(title)))
    return int(m[-1].group()) if m else None


def bucket_data(year_map, size, year_min, year_max):
    """
    year_map: year (int) → {"all": [int, ...], "content": [int, ...]}
    Returns ordered list of (label, dict) with short/medium/long counts
    and median lists for both token types.
    """
    start = (year_min // size) * size
    end   = ((year_max // size) + 1) * size
    bins  = {}
    for b in range(start, end, size):
        label = f"{b}–{b + size - 1}"
        all_t, con_t = [], []
        for y in range(b, b + size):
            if y in year_map:
                all_t.extend(year_map[y]["all"])
                con_t.extend(year_map[y]["content"])
        bins[label] = {
            "short":   sum(1 for t in all_t if t <= SHORT_MAX),
            "medium":  sum(1 for t in all_t if SHORT_MAX < t <= MEDIUM_MAX),
            "long":    sum(1 for t in all_t if t > MEDIUM_MAX),
            "all_t":   all_t,
            "con_t":   con_t,
        }
    return bins


def choose_bucket(year_min, year_max, year_map):
    for size in (5, 10, 25, 50, 100):
        start = (year_min // size) * size
        end   = ((year_max // size) + 1) * size
        non_empty = sum(
            1 for b in range(start, end, size)
            if any(y in year_map for y in range(b, b + size))
        )
        if non_empty <= MAX_BINS:
            return size
    return 100


def median(lst):
    s = sorted(lst)
    return s[len(s) // 2] if s else 0


# ── main ──────────────────────────────────────────────────────────────────────

def main(data_path: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {data_path} ...")
    with open(data_path, "rb") as f:
        df = pickle.load(f)
    total = len(df)
    print(f"Shape: {df.shape}")

    # ── year resolution ───────────────────────────────────────────────────────
    # Primary: 'dates' column (string year or NaN)
    # Fallback: regex on title string

    dates_null   = df["dates"].isna().sum()
    dates_source = 0   # resolved from 'dates'
    title_source = 0   # resolved from title fallback
    no_year      = 0

    year_map = defaultdict(lambda: {"all": [], "content": []})

    for _, row in df.iterrows():
        all_t = int(row["all_tokens"])
        con_t = int(row["content_tokens"])

        year = None
        if pd.notna(row["dates"]) and str(row["dates"]).strip():
            try:
                y = int(str(row["dates"]).strip()[:4])
                if 1400 <= y <= 2029:
                    year = y
                    dates_source += 1
            except ValueError:
                pass

        if year is None:
            year = year_from_title(row["title"])
            if year:
                title_source += 1
            else:
                no_year += 1

        if year:
            year_map[year]["all"].append(all_t)
            year_map[year]["content"].append(con_t)

    has_year  = dates_source + title_source
    year_min  = min(year_map)
    year_max  = max(year_map)

    # ── overall stats ─────────────────────────────────────────────────────────
    all_all  = df["all_tokens"].tolist()
    all_con  = df["content_tokens"].tolist()

    short_n  = sum(1 for t in all_all if t <= SHORT_MAX)
    medium_n = sum(1 for t in all_all if SHORT_MAX < t <= MEDIUM_MAX)
    long_n   = sum(1 for t in all_all if t > MEDIUM_MAX)

    print(f"\nTotal titles        : {total:,}")
    print(f"Year from 'dates'   : {dates_source:,}  ({100*dates_source/total:.1f}%)")
    print(f"Year from title     : {title_source:,}  ({100*title_source/total:.1f}%)")
    print(f"No year             : {no_year:,}  ({100*no_year/total:.1f}%)")
    print(f"Year range          : {year_min}–{year_max}")
    print(f"\nOverall (all_tokens):")
    print(f"  Short  (≤{SHORT_MAX})   : {short_n:>7,}  ({100*short_n/total:.1f}%)")
    print(f"  Medium ({SHORT_MAX+1}–{MEDIUM_MAX}) : {medium_n:>7,}  ({100*medium_n/total:.1f}%)")
    print(f"  Long   (>{MEDIUM_MAX})  : {long_n:>7,}  ({100*long_n/total:.1f}%)")
    print(f"  Median all_tokens     : {median(all_all)}")
    print(f"  Median content_tokens : {median(all_con)}")

    # ── bucketing ─────────────────────────────────────────────────────────────
    size = choose_bucket(year_min, year_max, year_map)
    bins = bucket_data(year_map, size, year_min, year_max)

    non_empty = [
        (lbl, d) for lbl, d in bins.items()
        if (d["short"] + d["medium"] + d["long"]) > 0
        and int(lbl.split("–")[0]) >= 1500
    ]
    n_pre1500 = sum(
        d["short"] + d["medium"] + d["long"]
        for lbl, d in bins.items()
        if (d["short"] + d["medium"] + d["long"]) > 0
        and int(lbl.split("–")[0]) < 1500
    )
    print(f"\nBucket size: {size} years  ({len(non_empty)} non-empty bins from 1500+)")
    print(f"Pre-1500 records omitted from chart: {n_pre1500:,}")

    print(f"\n{'Year bucket':<14}  {'Total':>7}  {'Short%':>7}  {'Med%':>6}  {'Long%':>6}  "
          f"{'Med all_t':>9}  {'Med con_t':>9}")
    print("-" * 72)
    for lbl, d in non_empty:
        n   = d["short"] + d["medium"] + d["long"]
        s_p = 100 * d["short"]  / n if n else 0
        m_p = 100 * d["medium"] / n if n else 0
        l_p = 100 * d["long"]   / n if n else 0
        print(f"{lbl:<14}  {n:>7,}  {s_p:>6.1f}%  {m_p:>5.1f}%  {l_p:>5.1f}%  "
              f"{median(d['all_t']):>9}  {median(d['con_t']):>9}")

    # ── save JSON ─────────────────────────────────────────────────────────────
    out_json = output_dir / "title-length-analysis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({
            "total_titles": total,
            "year_source": {
                "dates_column": dates_source,
                "title_fallback": title_source,
                "no_year": no_year,
            },
            "year_range": [year_min, year_max],
            "bucket_size": size,
            "length_thresholds": {"short_max": SHORT_MAX, "medium_max": MEDIUM_MAX},
            "overall": {
                "short": short_n, "medium": medium_n, "long": long_n,
                "median_all_tokens": median(all_all),
                "median_content_tokens": median(all_con),
            },
            "bucketed": {
                lbl: {
                    "short": d["short"], "medium": d["medium"], "long": d["long"],
                    "total": d["short"] + d["medium"] + d["long"],
                    "median_all_tokens":     median(d["all_t"]),
                    "median_content_tokens": median(d["con_t"]),
                }
                for lbl, d in non_empty
            },
        }, f, indent=2, ensure_ascii=False)
    print(f"\nSaved JSON  : {out_json}")

    # ── plot ──────────────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    })

    x       = list(range(len(non_empty)))
    xlabels = [lbl.split("–")[0] for lbl, _ in non_empty]
    totals  = [d["short"] + d["medium"] + d["long"] for _, d in non_empty]
    med_all = [median(d["all_t"]) for _, d in non_empty]
    med_con = [median(d["con_t"]) for _, d in non_empty]

    # ── deviation-encoded colour bands ────────────────────────────────────────
    # Base hues kept; brightness shifts ±25% toward black/white based on how
    # much a period's proportion deviates from the corpus-wide average.
    # Positive deviation (above average) → darker; negative → lighter.
    import numpy as np
    import matplotlib.colors as mcolors
    from matplotlib.patches import Patch

    COLOR_SHORT  = "#4C72B0"
    COLOR_MEDIUM = "#DD8452"
    COLOR_LONG   = "#55A868"
    COLOR_ALL    = "#C44E52"
    COLOR_CON    = "#8172B3"

    corpus_total   = sum(totals)
    corpus_short_p = sum(d["short"]  for _, d in non_empty) / corpus_total
    corpus_med_p   = sum(d["medium"] for _, d in non_empty) / corpus_total
    corpus_long_p  = sum(d["long"]   for _, d in non_empty) / corpus_total

    max_short_dev = max(abs(d["short"]  / (d["short"]+d["medium"]+d["long"]) - corpus_short_p) for _, d in non_empty)
    max_med_dev   = max(abs(d["medium"] / (d["short"]+d["medium"]+d["long"]) - corpus_med_p)   for _, d in non_empty)
    max_long_dev  = max(abs(d["long"]   / (d["short"]+d["medium"]+d["long"]) - corpus_long_p)  for _, d in non_empty)

    SHIFT = 0.25  # max brightness shift fraction

    def band_color(hex_color, dev, max_dev):
        """Blend hex_color toward black (dev > 0) or white (dev < 0)."""
        t   = dev / max_dev if max_dev > 0 else 0.0
        rgb = np.array(mcolors.to_rgb(hex_color))
        if t > 0:
            return tuple(rgb * (1 - t * SHIFT))
        else:
            return tuple(rgb + (1 - rgb) * (-t * SHIFT))

    fig_w = max(12, len(x) * 0.65)
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(fig_w, 9),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True,
    )

    # Top: stacked bars with per-bucket deviation shading
    for i, (_, d) in enumerate(non_empty):
        n  = d["short"] + d["medium"] + d["long"]
        sp = d["short"]  / n
        mp = d["medium"] / n
        lp = d["long"]   / n
        sc = band_color(COLOR_SHORT,  sp - corpus_short_p, max_short_dev)
        mc = band_color(COLOR_MEDIUM, mp - corpus_med_p,   max_med_dev)
        lc = band_color(COLOR_LONG,   lp - corpus_long_p,  max_long_dev)
        ax1.bar(i, d["short"],  color=sc, width=0.78, linewidth=0)
        ax1.bar(i, d["medium"], color=mc, width=0.78, linewidth=0, bottom=d["short"])
        ax1.bar(i, d["long"],   color=lc, width=0.78, linewidth=0,
                bottom=d["short"] + d["medium"])

    legend_elements = [
        Patch(facecolor=COLOR_SHORT,  label=f"Short (≤{SHORT_MAX} tokens)"),
        Patch(facecolor=COLOR_MEDIUM, label=f"Medium ({SHORT_MAX+1}–{MEDIUM_MAX} tokens)"),
        Patch(facecolor=COLOR_LONG,   label=f"Long (>{MEDIUM_MAX} tokens)"),
    ]
    ax1.legend(handles=legend_elements, frameon=False, fontsize=9, loc="upper left",
               title="Shade = deviation from corpus avg\n(darker → above avg, lighter → below)",
               title_fontsize=8)

    ax1.set_ylabel("Number of titles", fontsize=10)
    ax1.set_title(
        f"DDB's German Bibliographic Title Length by Year  ·  {size}-year buckets  ·  "
        f"N={sum(totals):,} with year  ·  {100*no_year/total:.1f}% no year",
        fontsize=11, fontweight="bold", pad=10,
    )
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax1.grid(axis="y", alpha=0.3)

    vmax = max(totals) if totals else 1
    ax1.set_ylim(0, vmax * 1.18)
    for i, tot in enumerate(totals):
        ax1.text(i, tot + vmax * 0.012, f"{tot:,}",
                 ha="center", va="bottom", fontsize=8, rotation=90, color="#333333")

    # Bottom: median all_tokens vs median content_tokens
    ax2.plot(x, med_all, color=COLOR_ALL, marker="o", linewidth=1.5, markersize=4,
             label="median all_tokens (incl. stopwords + punct.)")
    ax2.plot(x, med_con, color=COLOR_CON, marker="s", linewidth=1.5, markersize=4,
             linestyle="--", label="median content_tokens (stopwords removed)")
    ax2.fill_between(x, med_con, med_all, alpha=0.15, color="0.5",
                     label="stopword + punct. overhead")
    ax2.set_ylabel("Median\ntokens", fontsize=9)
    ax2.set_xticks(x)
    ax2.set_xticklabels(xlabels, rotation=60, ha="right", fontsize=8)
    ax2.grid(axis="y", alpha=0.3)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v)}"))
    ax2.legend(frameon=False, fontsize=8, loc="upper right")

    fig.tight_layout()
    out_png = output_dir / "fig_title_lengths.png"
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved chart : {out_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyse title-length distribution in DF_DE_TITLES"
    )
    parser.add_argument("--data",       type=Path, default=DATA_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    args = parser.parse_args()
    main(args.data, args.output_dir)

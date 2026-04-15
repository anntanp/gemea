# Purpose:      Plot the raw token-count distribution of all_tokens and
#               content_tokens in DF_DE_TITLES to identify natural breakpoints
#               for short/medium/long length categories.
# Usage:        python scripts/ner/sr10_explore_token_distribution.py
#               python scripts/ner/sr10_explore_token_distribution.py \
#                   --data data/processed/de_titles_tokenized.parquet \
#                   --output-dir notes/images --suffix _v2
# Inputs:       data/DF_DE_TITLES_20240125b.pkl  OR  data/processed/de_titles_tokenized.parquet
# Outputs:      notes/images/fig_token_distribution{suffix}.png — histogram + percentile markers
#               notes/images/token-distribution{suffix}.json    — percentile table and value counts
# Dependencies: pandas, pyarrow, matplotlib, numpy
# Assumptions:  all_tokens and content_tokens are int64 columns.

import json
import argparse
import pickle
from pathlib import Path

import pandas as pd

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

ROOT       = Path(__file__).resolve().parent.parent
DATA_PATH  = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_DIR = ROOT / "notes" / "images"

PERCENTILES = [10, 25, 33, 50, 66, 75, 90, 95, 99]


def load_data(path: Path) -> "pd.DataFrame":
    if path.suffix == ".parquet":
        return pd.read_parquet(path, columns=["all_tokens", "content_tokens"])
    with open(path, "rb") as f:
        return pickle.load(f)


def main(data_path: Path, output_dir: Path, suffix: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading {data_path} ...")
    df = load_data(data_path)

    all_t = df["all_tokens"].values
    con_t = df["content_tokens"].values
    total = len(all_t)

    # ── percentile table ──────────────────────────────────────────────────────
    print(f"\nTotal titles: {total:,}")
    print(f"\n{'Percentile':<12}  {'all_tokens':>12}  {'content_tokens':>14}")
    print("-" * 42)
    pct_all, pct_con = {}, {}
    for p in PERCENTILES:
        v_all = int(np.percentile(all_t, p))
        v_con = int(np.percentile(con_t, p))
        pct_all[p] = v_all
        pct_con[p] = v_con
        print(f"  p{p:<9}  {v_all:>12}  {v_con:>14}")

    # ── value counts (all_tokens, first 40) ───────────────────────────────────
    cap99 = int(np.percentile(all_t, 99))
    unique, counts = np.unique(all_t, return_counts=True)
    print(f"\nall_tokens value counts (1–40, p99={cap99}):")
    print(f"  {'tokens':>6}  {'count':>8}  {'%':>6}  bar")
    print("  " + "-" * 55)
    max_n = counts.max()
    for v, n in zip(unique, counts):
        if v > 40:
            break
        bar = "█" * int(40 * n / max_n)
        print(f"  {v:>6}  {n:>8,}  {100*n/total:>5.1f}%  {bar}")

    # ── save JSON ─────────────────────────────────────────────────────────────
    out_json = output_dir / f"token-distribution{suffix}.json"
    with open(out_json, "w") as f:
        json.dump({
            "total_titles": total,
            "p99_all_tokens": cap99,
            "percentiles": {
                "all_tokens":     {str(p): v for p, v in pct_all.items()},
                "content_tokens": {str(p): v for p, v in pct_con.items()},
            },
            "value_counts_all_tokens": {
                str(int(v)): int(n) for v, n in zip(unique, counts) if v <= 60
            },
        }, f, indent=2)
    print(f"\nSaved JSON  : {out_json}")

    # ── plot ──────────────────────────────────────────────────────────────────
    plt.rcParams.update({
        "font.family": "sans-serif",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "figure.dpi": 150,
    })

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    for ax, data, pct_vals, label, color in [
        (ax1, all_t, pct_all, "all_tokens",     "#4C72B0"),
        (ax2, con_t, pct_con, "content_tokens", "#8172B3"),
    ]:
        cap = int(np.percentile(data, 99))
        vals = data[data <= cap]
        ax.hist(vals, bins=cap, color=color, alpha=0.8, linewidth=0)

        for p, ls, lw in [(25, ":", 1.2), (50, "--", 1.5), (75, ":", 1.2), (90, "-.", 1.2)]:
            v = pct_vals[p]
            ax.axvline(v, color="#C44E52", linewidth=lw, linestyle=ls,
                       label=f"p{p} = {v}")

        ax.set_xlabel("Token count", fontsize=10)
        ax.set_ylabel("Number of titles", fontsize=10)
        ax.set_title(f"{label}  (shown ≤ p99 = {cap})\nN = {total:,}",
                     fontsize=11, fontweight="bold")
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))
        ax.legend(frameon=False, fontsize=8, loc="upper right")
        ax.grid(axis="y", alpha=0.3)

    fig.suptitle("DF_DE_TITLES — Token count distribution", fontsize=12,
                 fontweight="bold", y=1.01)
    fig.tight_layout()
    out_png = output_dir / f"fig_token_distribution{suffix}.png"
    fig.savefig(out_png, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved chart : {out_png}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Explore token-count distribution in DF_DE_TITLES"
    )
    parser.add_argument("--data",       type=Path, default=DATA_PATH)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument("--suffix",     type=str,  default="",
                        help="Suffix appended to output filenames, e.g. '_v2'")
    args = parser.parse_args()
    main(args.data, args.output_dir, args.suffix)

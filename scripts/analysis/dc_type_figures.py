#!/usr/bin/env python3
"""
Purpose:      Generate publication-quality figures for the dc_type sector analysis.
              Produces two figures:
                Fig 1 — horizontal stacked bar: URI vs Literal share by sector
                Fig 2 — bubble chart: URI% × distinct literals, sized by total entries
Usage:        python scripts/analysis/dc_type_figures.py [--data-dir DIR] [--out-dir DIR]
Inputs:       data/processed/dc_type_by_sector.csv
Outputs:      notes/images/fig_dctype_sector_bars.png
              notes/images/fig_dctype_sector_bubble.png
Dependencies: pandas, matplotlib
Assumptions:  Run from the gemea/ project root.
"""

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

# Grayscale palette consistent with print/paper output
COLOR_URI = "#2d2d2d"      # dark gray  → URI entries
COLOR_LITERAL = "#b0b0b0"  # light gray → Literal entries
COLOR_BUBBLE = "#555555"

SINGLE_COL_WIDTH = 3.5  # inches — single-column paper width
FULL_WIDTH = 7.0         # inches — full-column paper width
DPI = 300


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/processed"),
        help="Directory containing dc_type_by_sector.csv (default: data/processed)",
    )
    p.add_argument(
        "--out-dir",
        type=Path,
        default=Path("notes/images"),
        help="Output directory for PNG figures (default: notes/images)",
    )
    return p.parse_args()


def load_data(data_dir: Path) -> pd.DataFrame:
    path = data_dir / "dc_type_by_sector.csv"
    df = pd.read_csv(path)
    df["total"] = df["uri_count"] + df["literal_count"]
    df["uri_pct"] = df["uri_count"] / df["total"] * 100
    df["lit_pct"] = 100 - df["uri_pct"]
    return df


def fig1_stacked_bars(df: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal stacked bar: URI vs Literal share by sector, sorted by URI%."""
    df_sorted = df.sort_values("uri_pct", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.8))

    y = range(len(df_sorted))
    bar_height = 0.55

    ax.barh(
        list(y),
        df_sorted["uri_pct"],
        height=bar_height,
        color=COLOR_URI,
        label="URI-linked",
    )
    ax.barh(
        list(y),
        df_sorted["lit_pct"],
        height=bar_height,
        left=df_sorted["uri_pct"].values,
        color=COLOR_LITERAL,
        label="Literal",
    )

    ax.set_yticks(list(y))
    ax.set_yticklabels(df_sorted["sector_name"], fontsize=9)
    ax.set_xlabel("Share of dc:type entries (%)", fontsize=9)
    ax.set_xlim(0, 115)  # room for annotations on the right
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

    # URI% annotation at the right edge of the URI segment
    for i, row in df_sorted.iterrows():
        idx = df_sorted.index.get_loc(i)
        ax.text(
            row["uri_pct"] + 1.0,
            idx,
            f"{row['uri_pct']:.0f}%",
            va="center",
            ha="left",
            fontsize=8,
            color=COLOR_URI,
            fontweight="bold",
        )
        # N= total on the far right
        n_str = f"N={row['total'] / 1e6:.1f}M"
        ax.text(
            112,
            idx,
            n_str,
            va="center",
            ha="right",
            fontsize=7.5,
            color="#555555",
        )

    ax.legend(
        handles=[
            mpatches.Patch(color=COLOR_URI, label="URI-linked"),
            mpatches.Patch(color=COLOR_LITERAL, label="Literal"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.45, -0.18),
        ncol=2,
        fontsize=8,
        frameon=False,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out_path = out_dir / "fig_dctype_sector_bars.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def fig2_bubble(df: pd.DataFrame, out_dir: Path) -> None:
    """Bubble chart: URI% × distinct literals (log Y), bubble size = total entries."""
    fig, ax = plt.subplots(figsize=(SINGLE_COL_WIDTH, 2.8))

    # Log-normalize bubble area: map [min_total, max_total] → [200, 1800] pt²
    log_totals = df["total"].apply(math.log10)
    log_min, log_max = log_totals.min(), log_totals.max()
    sizes = 200 + (log_totals - log_min) / (log_max - log_min) * 1600

    ax.scatter(
        df["uri_pct"],
        df["literal_distinct"],
        s=sizes,
        color=COLOR_BUBBLE,
        alpha=0.65,
        edgecolors="white",
        linewidths=0.5,
    )

    # (dx offset in %, dy multiplicative offset on log scale)
    label_offsets: dict[str, tuple[float, float]] = {
        "Archive":   (1.5, 1.0),
        "Library":   (1.5, 1.35),   # nudge up — close to Monument
        "Monument":  (1.5, 0.72),   # nudge down — close to Library
        "Research":  (1.5, 1.0),
        "Media":     (1.5, 1.0),
        "Museum":    (1.5, 1.05),
        "Other":     (1.5, 1.0),
    }

    for _, row in df.iterrows():
        dx, dy_mul = label_offsets.get(row["sector_name"], (1.5, 1.0))
        ax.annotate(
            row["sector_name"],
            xy=(row["uri_pct"], row["literal_distinct"]),
            xytext=(row["uri_pct"] + dx, row["literal_distinct"] * dy_mul),
            fontsize=7.5,
            va="center",
            ha="left",
            color="#222222",
        )

    ax.set_yscale("log")
    ax.set_xlabel("URI-linked share (%)", fontsize=9)
    ax.set_ylabel("Distinct literals (log scale)", fontsize=9)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlim(0, 100)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out_path = out_dir / "fig_dctype_sector_bubble.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    try:
        plt.style.use("seaborn-v0_8-whitegrid")
    except OSError:
        plt.style.use("seaborn-whitegrid")

    df = load_data(args.data_dir)

    fig1_stacked_bars(df, args.out_dir)
    fig2_bubble(df, args.out_dir)


if __name__ == "__main__":
    main()

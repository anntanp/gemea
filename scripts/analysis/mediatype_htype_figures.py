#!/usr/bin/env python3
"""
Purpose:      Generate publication-quality figures for the mediatype and
              hierarchy_type sector analysis.
              Produces three figures:
                Fig 1 — stacked bars: mediatype composition per sector
                Fig 2 — stacked bars: htype coverage (covered vs null) per sector
                Fig 3 — small multiples: top htypes for covered sectors
Usage:        python scripts/analysis/mediatype_htype_figures.py [--data-dir DIR] [--out-dir DIR]
Inputs:       data/processed/mediatype_by_sector.csv
              data/processed/htype_by_sector.csv
Outputs:      notes/images/fig_mediatype_sector_bars.png
              notes/images/fig_htype_coverage.png
              notes/images/fig_htype_distribution.png
Dependencies: pandas, matplotlib
Assumptions:  Run from the gemea/ project root.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

FULL_WIDTH = 7.0
SINGLE_COL_WIDTH = 3.5
DPI = 300

# Grayscale palette — dark to light, consistent with dc_type_figures.py
MEDIATYPE_COLORS: dict[str, str] = {
    "Photo":         "#2d2d2d",
    "Text":          "#666666",
    "Audio":         "#999999",
    "Video":         "#bbbbbb",
    "Not Digitized": "#dddddd",
    "Null/Missing":  "#f0f0f0",
}

# Okabe-Ito colorblind-safe palette
MEDIATYPE_COLORS_COLOR: dict[str, str] = {
    "Photo":         "#0072B2",   # blue
    "Text":          "#009E73",   # green
    "Audio":         "#E69F00",   # amber
    "Video":         "#CC79A7",   # mauve
    "Not Digitized": "#D55E00",   # vermillion
    "Null/Missing":  "#bbbbbb",
}

HTYPE_COLORS = {
    "covered": "#2d2d2d",
    "null":    "#cccccc",
}

# Gray gradient for htype bars within a sector (up to ~10 distinct types)
TOP_HTYPE_GRAYS = [
    "#1a1a1a", "#3d3d3d", "#5c5c5c", "#7a7a7a", "#969696",
    "#ababab", "#bebebe", "#d0d0d0", "#e0e0e0", "#eeeeee",
]

SECTOR_ORDER = ["Library", "Archive", "Research", "Museum", "Media", "Other", "Monument"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--out-dir", type=Path, default=Path("notes/images"))
    return p.parse_args()


def load_mediatype(data_dir: Path) -> pd.DataFrame:
    df = pd.read_csv(data_dir / "mediatype_by_sector.csv")
    pivot = df.pivot_table(
        index=["sector", "sector_name"],
        columns="mediatype_label",
        values="count",
        fill_value=0,
    ).reset_index()
    pivot.columns.name = None
    pivot["total"] = pivot.drop(columns=["sector", "sector_name"]).sum(axis=1)
    # convert counts to percentages
    for col in [c for c in pivot.columns if c not in ("sector", "sector_name", "total")]:
        pivot[col + "_pct"] = pivot[col] / pivot["total"] * 100
    return pivot


def load_htype(data_dir: Path) -> pd.DataFrame:
    return pd.read_csv(data_dir / "htype_by_sector.csv")


def fig1_mediatype_bars(mt: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal stacked bar: mediatype % composition per sector (grayscale, publication)."""
    _mediatype_stacked(mt, MEDIATYPE_COLORS, out_dir / "fig_mediatype_sector_bars.png")


def fig1_mediatype_bars_color(mt: pd.DataFrame, out_dir: Path) -> None:
    """Same as fig1_mediatype_bars but using the Okabe-Ito colorblind-safe palette."""
    _mediatype_stacked(mt, MEDIATYPE_COLORS_COLOR, out_dir / "fig_mediatype_sector_bars_color.png")


def _mediatype_stacked(mt: pd.DataFrame, color_map: dict[str, str], out_path: Path) -> None:
    """Shared logic for both the grayscale and colour versions of fig 1."""
    mt = mt.copy()
    mt["_photo_pct"] = mt.get("Photo_pct", 0)
    mt_lib = mt[mt["sector_name"] == "Library"]
    mt_rest = mt[mt["sector_name"] != "Library"].sort_values("_photo_pct", ascending=True)
    mt_sorted = pd.concat([mt_lib, mt_rest], ignore_index=True)

    types = [t for t in ["Not Digitized", "Audio", "Video", "Text", "Photo"] if t + "_pct" in mt.columns]

    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.8))
    y = list(range(len(mt_sorted)))
    bar_h = 0.55
    lefts = [0.0] * len(mt_sorted)

    for mt_type in types:
        col = mt_type + "_pct"
        vals = mt_sorted[col].values if col in mt_sorted.columns else [0] * len(mt_sorted)
        ax.barh(y, vals, height=bar_h, left=lefts, color=color_map[mt_type], label=mt_type)
        lefts = [l + v for l, v in zip(lefts, vals)]

    ax.set_yticks(y)
    ax.set_yticklabels(mt_sorted["sector_name"], fontsize=9)
    ax.set_xlabel("Share of objects (%)", fontsize=9)
    ax.set_xlim(0, 118)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

    for i, row in mt_sorted.iterrows():
        idx = mt_sorted.index.get_loc(i)
        n = row["total"]
        n_str = f"N={n / 1e6:.2f}M" if n >= 1e5 else f"N={n:,.0f}"
        ax.text(117, idx, n_str, va="center", ha="right", fontsize=7.5, color="#555555")

    legend_handles = [mpatches.Patch(color=color_map[t], label=t) for t in reversed(types)]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.44, -0.18),
        ncol=len(types),
        fontsize=8,
        frameon=False,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def fig2_htype_coverage(ht: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal stacked bar: htype covered% vs null% per sector."""
    total = ht.groupby(["sector", "sector_name"])["count"].sum().reset_index(name="total")
    null_df = ht[ht["htype_label"] == "Null/Missing"].groupby("sector")["count"].sum().reset_index(name="null_count")
    cov = total.merge(null_df, on="sector", how="left").fillna({"null_count": 0})
    cov["null_pct"] = cov["null_count"] / cov["total"] * 100
    cov["covered_pct"] = 100 - cov["null_pct"]

    # Sort by covered% ascending (most null at top)
    cov = cov.sort_values("covered_pct", ascending=True).reset_index(drop=True)

    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.6))
    y = list(range(len(cov)))
    bar_h = 0.55

    ax.barh(y, cov["covered_pct"], height=bar_h, color=HTYPE_COLORS["covered"], label="htype assigned")
    ax.barh(y, cov["null_pct"], height=bar_h, left=cov["covered_pct"], color=HTYPE_COLORS["null"], label="Null/Missing")

    ax.set_yticks(y)
    ax.set_yticklabels(cov["sector_name"], fontsize=9)
    ax.set_xlabel("Share of objects (%)", fontsize=9)
    ax.set_xlim(0, 118)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))

    for i, row in cov.iterrows():
        idx = cov.index.get_loc(i)
        if row["covered_pct"] > 2:
            ax.text(
                row["covered_pct"] / 2, idx,
                f"{row['covered_pct']:.0f}%",
                va="center", ha="center", fontsize=8, color="white", fontweight="bold",
            )
        n_str = f"N={row['total'] / 1e6:.2f}M" if row["total"] >= 1e5 else f"N={row['total']:,.0f}"
        ax.text(117, idx, n_str, va="center", ha="right", fontsize=7.5, color="#555555")

    ax.legend(
        handles=[
            mpatches.Patch(color=HTYPE_COLORS["covered"], label="htype assigned"),
            mpatches.Patch(color=HTYPE_COLORS["null"], label="Null/Missing"),
        ],
        loc="upper center",
        bbox_to_anchor=(0.44, -0.18),
        ncol=2,
        fontsize=8,
        frameon=False,
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    out_path = out_dir / "fig_htype_coverage.png"
    fig.savefig(out_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved {out_path}")


def fig3_htype_distribution(ht: pd.DataFrame, out_dir: Path) -> None:
    """Small multiples: top-8 htypes per covered sector (Archive, Library, Research, Other)."""
    covered_sectors = [s for s in ["Archive", "Library", "Research", "Other"]
                       if s in ht["sector_name"].values]

    fig, axes = plt.subplots(2, 2, figsize=(FULL_WIDTH, 5.5))
    axes = axes.flatten()

    for ax_idx, sector_name in enumerate(covered_sectors):
        ax = axes[ax_idx]
        sub = ht[(ht["sector_name"] == sector_name) & (ht["htype_label"] != "Null/Missing")]
        sub = sub.nlargest(8, "count").sort_values("count", ascending=True)

        colors = TOP_HTYPE_GRAYS[: len(sub)]
        bars = ax.barh(list(range(len(sub))), sub["count"].values, color=colors, edgecolor="none")

        ax.set_yticks(list(range(len(sub))))
        ax.set_yticklabels(sub["htype_label"].values, fontsize=8)
        ax.set_xlabel("Objects", fontsize=8)
        ax.set_title(sector_name, fontsize=9, fontweight="bold", pad=4)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{int(v):,}"))
        ax.tick_params(axis="x", labelsize=7.5)

        # pct labels inside or outside bars
        sector_total = ht[ht["sector_name"] == sector_name]["count"].sum()
        for bar, row in zip(bars, sub.itertuples()):
            pct = row.count / sector_total * 100
            x_pos = row.count + sector_total * 0.01
            ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
                    f"{pct:.1f}%", va="center", ha="left", fontsize=7, color="#444444")

        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    plt.suptitle("Top htypes by sector (null excluded)", fontsize=10, y=1.01)
    plt.tight_layout()

    out_path = out_dir / "fig_htype_distribution.png"
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

    mt = load_mediatype(args.data_dir)
    ht = load_htype(args.data_dir)

    fig1_mediatype_bars(mt, args.out_dir)
    fig1_mediatype_bars_color(mt, args.out_dir)
    fig2_htype_coverage(ht, args.out_dir)
    fig3_htype_distribution(ht, args.out_dir)


if __name__ == "__main__":
    main()

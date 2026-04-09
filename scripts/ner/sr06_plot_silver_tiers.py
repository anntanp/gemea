# Purpose:      Plot silver-tier composition by era (tier-1 and tier-2 as stacked bars;
#               tier-0 annotated but not plotted — prevents visual dominance).
# Usage:        python scripts/sr06_plot_silver_tiers.py
#               python scripts/sr06_plot_silver_tiers.py --input PATH --output PATH
# Inputs:       data/processed/sr08_corpus_cell_sizes.csv
# Outputs:      notes/images/fig_silver_tiers.png
# Dependencies: pandas, matplotlib

import argparse
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

ROOT       = Path(__file__).resolve().parent.parent
INPUT_PATH = ROOT / "data" / "processed" / "sr08_corpus_cell_sizes.csv"
OUTPUT_PATH = ROOT / "notes" / "images" / "fig_silver_tiers.png"

ERA_ORDER  = ["pre-1700", "1700-1800", "19th-c", "modern"]
ERA_LABELS = ["Pre-1700", "1700–1800", "19th-c", "Modern"]
TOTAL_LABEL = "Total"

COLOR_T2 = "#2563EB"   # strong blue — tier-2 (structural)
COLOR_T1 = "#93C5FD"   # light blue — tier-1 (heuristic)


def main(input_path: Path, output_path: Path) -> None:
    df = pd.read_csv(input_path)
    df = df[df["era"].isin(ERA_ORDER)].copy()
    df["era"] = pd.Categorical(df["era"], categories=ERA_ORDER, ordered=True)
    df = df.sort_values("era")

    # Compute within-era percentages
    df["t1_pct"] = 100 * df["tier-1"] / df["total"]
    df["t2_pct"] = 100 * df["tier-2"] / df["total"]
    df["t0_pct"] = 100 * df["tier-0"] / df["total"]

    # Add Total row
    totals = {
        "era":    TOTAL_LABEL,
        "tier-0": df["tier-0"].sum(),
        "tier-1": df["tier-1"].sum(),
        "tier-2": df["tier-2"].sum(),
        "total":  df["total"].sum(),
    }
    totals["t1_pct"] = 100 * totals["tier-1"] / totals["total"]
    totals["t2_pct"] = 100 * totals["tier-2"] / totals["total"]
    totals["t0_pct"] = 100 * totals["tier-0"] / totals["total"]
    df = pd.concat([df, pd.DataFrame([totals])], ignore_index=True)

    labels = ERA_LABELS + [TOTAL_LABEL]
    x      = range(len(labels))
    t1     = df["t1_pct"].tolist()
    t2     = df["t2_pct"].tolist()
    t0     = df["t0_pct"].tolist()

    fig, ax = plt.subplots(figsize=(8, 5))

    bars_t2 = ax.bar(x, t2, color=COLOR_T2, label="Tier 2 — structural", zorder=3)
    bars_t1 = ax.bar(x, t1, bottom=t2, color=COLOR_T1, label="Tier 1 — heuristic", zorder=3)

    # Annotate tier-0 % above each bar
    for i, (t2v, t1v, t0v) in enumerate(zip(t2, t1, t0)):
        top = t2v + t1v
        ax.text(
            i, top + 0.15,
            f"tier-0: {t0v:.1f}%",
            ha="center", va="bottom",
            fontsize=8.5, color="#6B7280",
        )

    # Value labels inside bars (only if bar is tall enough)
    for bar, val in zip(bars_t2, t2):
        if val > 0.05:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() / 2,
                f"{val:.2f}%",
                ha="center", va="center",
                fontsize=7.5, color="white", fontweight="bold",
            )
    for bar, base, val in zip(bars_t1, t2, t1):
        if val > 0.3:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                base + val / 2,
                f"{val:.1f}%",
                ha="center", va="center",
                fontsize=7.5, color="#1E3A5F", fontweight="bold",
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=10)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylabel("% of era records", fontsize=10)
    ax.set_title(
        "Silver-tier coverage by era\n"
        "(tier-0 annotated; ~92 % of corpus — not plotted)",
        fontsize=11, pad=12,
    )
    ax.legend(loc="upper right", fontsize=9, framealpha=0.9)
    ax.set_ylim(0, max(t for t in [v1 + v2 for v1, v2 in zip(t1, t2)]) * 2.2)
    ax.grid(axis="y", linestyle="--", alpha=0.4, zorder=0)
    ax.spines[["top", "right"]].set_visible(False)

    # Vertical separator before Total bar
    ax.axvline(len(ERA_LABELS) - 0.5, color="#D1D5DB", linewidth=1, linestyle="--")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input",  type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    main(args.input, args.output)

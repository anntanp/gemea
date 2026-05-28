#!/usr/bin/env python3
"""
Purpose:  Publication-quality figures for language diversity and date coverage
          across all DDB sectors. Three figures:
            Fig 1 — fig_date_coverage_sector.png  : date coverage % per sector
            Fig 2 — fig_date_types_sector.png      : date-type composition per sector
            Fig 3 — fig_lang_diversity_decade.png  : distinct languages × decade
Usage:    python scripts/analysis/lang_date_figures.py [--data-dir DIR] [--out-dir DIR]
Inputs:   data/processed/date_types_all.csv
          data/processed/lang_by_year_all.csv
Outputs:  notes/images/fig_date_coverage_sector.png
          notes/images/fig_date_types_sector.png
          notes/images/fig_lang_diversity_decade.png
Dependencies: pandas, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd

FULL_WIDTH = 7.0
DPI = 300

SECTOR_NAMES = {
    1: "Archive",
    2: "Library",
    3: "Monument",
    4: "Research",
    5: "Media Library",
    6: "Museum",
    7: "Other",
}

# Okabe-Ito colorblind-safe
C_CREATION    = "#0072B2"   # blue
C_PUBLICATION = "#E69F00"   # amber
C_UNKNOWN     = "#009E73"   # green

C_HAS_DATE = "#2d2d2d"
C_NO_DATE  = "#cccccc"

try:
    plt.style.use("seaborn-v0_8-whitegrid")
except OSError:
    plt.style.use("seaborn-whitegrid")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=Path("data/processed"))
    p.add_argument("--out-dir",  type=Path, default=Path("notes/images"))
    return p.parse_args()


# ── Fig 1: date coverage per sector ──────────────────────────────────────────

def fig_date_coverage(df_dates: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal 100% stacked bar: % objects with/without any date, per sector."""
    totals = df_dates[df_dates["date_type"] == "_TOTAL_OBJECTS"].set_index("sector")["struct_count"]
    with_dt = df_dates[df_dates["date_type"] == "_OBJECTS_WITH_DATE"].set_index("sector")["struct_count"]

    cov = pd.DataFrame({
        "sector": totals.index,
        "name": [SECTOR_NAMES[s] for s in totals.index],
        "total": totals.values,
        "has_date": with_dt.values,
    })
    cov["has_pct"]  = cov["has_date"] / cov["total"] * 100
    cov["none_pct"] = 100 - cov["has_pct"]
    cov = cov.sort_values("has_pct")           # ascending → lowest at bottom of barh

    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.8))

    bars_has  = ax.barh(cov["name"], cov["has_pct"],  color=C_HAS_DATE, label="Has date")
    bars_none = ax.barh(cov["name"], cov["none_pct"], left=cov["has_pct"], color=C_NO_DATE, label="No date")

    # annotate has_date% inside the bar if ≥ 8%
    for bar, pct in zip(bars_has, cov["has_pct"]):
        if pct >= 8:
            ax.text(
                bar.get_width() / 2, bar.get_y() + bar.get_height() / 2,
                f"{pct:.0f}%", ha="center", va="center",
                fontsize=7.5, color="white", fontweight="bold",
            )
        else:
            ax.text(
                bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{pct:.1f}%", ha="left", va="center",
                fontsize=7, color="#333333",
            )

    ax.set_xlim(0, 100)
    ax.set_xlabel("Share (%)", fontsize=9)
    ax.set_title("Date Coverage by Sector", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(
        loc="lower right", fontsize=8, framealpha=0.7,
        handles=[
            mpatches.Patch(color=C_HAS_DATE, label="Has date"),
            mpatches.Patch(color=C_NO_DATE,  label="No date"),
        ],
    )

    out = out_dir / "fig_date_coverage_sector.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")


# ── Fig 2: date-type composition per sector ───────────────────────────────────

def fig_date_types(df_dates: pd.DataFrame, out_dir: Path) -> None:
    """Horizontal 100% stacked bar: creation/publication/unknown_event share per sector."""
    types = df_dates[df_dates["date_type"].isin(["creation", "publication", "unknown_event"])]
    pivot = types.pivot_table(
        index="sector", columns="date_type", values="struct_count", fill_value=0
    ).reset_index()

    for col in ("creation", "publication", "unknown_event"):
        if col not in pivot.columns:
            pivot[col] = 0

    pivot["total"] = pivot[["creation", "publication", "unknown_event"]].sum(axis=1)
    pivot = pivot[pivot["total"] > 0]          # drop sectors with zero structs
    pivot["cre_pct"] = pivot["creation"]    / pivot["total"] * 100
    pivot["pub_pct"] = pivot["publication"] / pivot["total"] * 100
    pivot["unk_pct"] = pivot["unknown_event"] / pivot["total"] * 100
    pivot["name"] = pivot["sector"].map(SECTOR_NAMES)
    pivot = pivot.sort_values("pub_pct")       # ascending → lowest pub% at bottom

    fig, ax = plt.subplots(figsize=(FULL_WIDTH, 2.8))

    b_pub = ax.barh(pivot["name"], pivot["pub_pct"], color=C_PUBLICATION, label="publication")
    b_cre = ax.barh(pivot["name"], pivot["cre_pct"], left=pivot["pub_pct"], color=C_CREATION, label="creation")
    b_unk = ax.barh(pivot["name"], pivot["unk_pct"],
                    left=pivot["pub_pct"] + pivot["cre_pct"], color=C_UNKNOWN, label="unknown_event")

    def annotate_bar(bars, pcts, lefts=None):
        for bar, pct, in zip(bars, pcts):
            if pct < 5:
                continue
            x = bar.get_x() + bar.get_width() / 2
            y = bar.get_y() + bar.get_height() / 2
            ax.text(x, y, f"{pct:.0f}%", ha="center", va="center",
                    fontsize=7, color="white", fontweight="bold")

    annotate_bar(b_pub, pivot["pub_pct"])
    annotate_bar(b_cre, pivot["cre_pct"])
    annotate_bar(b_unk, pivot["unk_pct"])

    ax.set_xlim(0, 100)
    ax.set_xlabel("Share of date structs (%)", fontsize=9)
    ax.set_title("Date-Type Composition by Sector\n(objects with at least one date)", fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", labelsize=8.5)
    ax.tick_params(axis="x", labelsize=8)
    ax.legend(
        loc="lower right", fontsize=8, framealpha=0.7,
        handles=[
            mpatches.Patch(color=C_PUBLICATION, label="publication"),
            mpatches.Patch(color=C_CREATION,    label="creation"),
            mpatches.Patch(color=C_UNKNOWN,     label="unknown_event"),
        ],
    )

    out = out_dir / "fig_date_types_sector.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")


# ── Fig 3: language diversity × decade ───────────────────────────────────────

def fig_lang_diversity(df_lang: pd.DataFrame, out_dir: Path) -> None:
    """Distinct language codes and total objects per decade (1500–2020), dual Y-axis."""
    df = df_lang[(df_lang["bucket"] >= 1500) & (df_lang["bucket"] <= 2020)].copy()
    agg = (
        df.groupby("bucket")
        .agg(n_langs=("lang", "nunique"), n_objects=("count", "sum"))
        .reset_index()
    )

    fig, ax1 = plt.subplots(figsize=(FULL_WIDTH, 3.8))
    ax2 = ax1.twinx()

    ax1.plot(agg["bucket"], agg["n_langs"], color=C_CREATION, linewidth=1.8,
             label="Distinct languages (left)")
    ax1.fill_between(agg["bucket"], agg["n_langs"], alpha=0.15, color=C_CREATION)

    ax2.plot(agg["bucket"], agg["n_objects"], color="#b0b0b0", linewidth=1.2,
             linestyle="--", label="Object count (right)")

    ax2.set_yscale("log")
    ax2.set_ylabel("Objects (log scale)", fontsize=8.5, color="#999999")
    ax2.tick_params(axis="y", labelsize=7.5, colors="#999999")
    ax2.spines["right"].set_color("#cccccc")

    # century ticks on x
    centuries = [b for b in agg["bucket"] if b % 100 == 0]
    ax1.set_xticks(centuries)
    ax1.set_xticklabels([str(c) for c in centuries], fontsize=8)

    ax1.set_xlabel("Decade", fontsize=9)
    ax1.set_ylabel("Distinct language codes", fontsize=9, color=C_CREATION)
    ax1.tick_params(axis="y", labelsize=8, colors=C_CREATION)
    ax1.set_title("Language Diversity by Decade (all sectors, 1500–2020)", fontsize=10)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    handles = [
        mpatches.Patch(color=C_CREATION, alpha=0.7, label="Distinct language codes"),
        plt.Line2D([0], [0], color="#b0b0b0", linewidth=1.2, linestyle="--", label="Object count"),
    ]
    ax1.legend(handles=handles, loc="upper left", fontsize=8, framealpha=0.7)

    out = out_dir / "fig_lang_diversity_decade.png"
    fig.tight_layout()
    fig.savefig(out, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved → {out}")


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    df_dates = pd.read_csv(args.data_dir / "date_types_all.csv")
    df_lang  = pd.read_csv(args.data_dir / "lang_by_year_all.csv")

    fig_date_coverage(df_dates, args.out_dir)
    fig_date_types(df_dates, args.out_dir)
    fig_lang_diversity(df_lang, args.out_dir)


if __name__ == "__main__":
    main()

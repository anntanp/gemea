# Purpose:      Show which dc_type values are prevalent within each time-period era.
#               Counts and percentages of each dc_type per era stratum; saves a
#               stacked bar chart (% share within era, top N types).
# Usage:        python scripts/sr11_dctype_by_era.py
#               python scripts/sr11_dctype_by_era.py --data PATH --output PATH --fig PATH --top 8
# Inputs:       data/DF_DE_TITLES_20240125b.pkl
# Outputs:      data/processed/sr11_dctype_by_era.csv      (era × dc_type counts + pcts)
#               data/processed/sr11_dctype_filtered.csv    (per-record; obj_id, era, dc_type, dates)
#               notes/images/fig_dctype_by_era.png          (stacked bar chart)
# Dependencies: pandas, matplotlib
# Assumptions:  'dates' column is a string year (e.g. '1931') or NaN.
#               'dc_type' is a pipe-separated list of tags, not a single value
#               (e.g. "Leichenpredigt|Monografie", "Flugschrift|Monografie").
#               Normalization (normalize_dctype): split on '|', discard structural/
#               component parts (COMPONENT_TYPES), discard generic base-format labels
#               (BASE_TYPES) unless they are the only tag remaining. The result is
#               the most specific genre label, e.g. "Leichenpredigt|Monografie" →
#               "Leichenpredigt". Records whose every tag is a component type are
#               excluded entirely (pure structural entries, no genre signal).
#               Era boundaries: pre-1700 (<1700), 1700-1800 (1700-1799),
#               19th-c (1800-1899), modern (>=1900), unknown (no year).

import re
import argparse
import pickle
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd

ROOT        = Path(__file__).resolve().parent.parent
DATA_PATH   = ROOT / "data" / "DF_DE_TITLES_20240125b.pkl"
OUTPUT_PATH = ROOT / "data" / "processed" / "sr11_dctype_by_era.csv"
FIG_PATH    = ROOT / "notes" / "images" / "fig_dctype_by_era.png"

YEAR_RE   = re.compile(r"\b(?:1[4-9]\d{2}|20[012]\d)\b")
ERA_ORDER = ["pre-1700", "1700-1800", "19th-c", "modern", "unknown"]

# dc_type is a pipe-separated list of tags, e.g. "Leichenpredigt|Monografie".
# COMPONENT_TYPES: structural/positional roles — no genre signal, always stripped.
# BASE_TYPES: generic document-format labels — kept only as fallback when no
#             specific genre is present.
COMPONENT_TYPES: set[str] = {
    "Abschnitt", "Kapitel", "Band", "Heft", "issue",
    "Aufsatz", "Article", "Artikel", "Zeitschriftenartikel",
    "Index", "Inhaltsverzeichnis", "Vorwort", "Beilage",
    "Beigefügtes oder enthaltenes Werk",
    "Text", "Volume", "Section", "Chapter",
    "Sammelwerksbeitrag", "Buchbeitrag", "Vers",
    "Faszikel", "Konferenzbeitrag", "Review",
    "Stellungnahme", "Abschlussbericht", "Gutachten",
    "(none)", "",
}

BASE_TYPES: set[str] = {
    "Monografie", "Monograph", "Monograph|book", "book",
    "mehrbändiges Werk", "Multivolume Work", "Multivolume work",
    "Fortlaufendes Sammelwerk", "Sammelwerk", "Periodical",
    "letter", "Letter",
}


def normalize_dctype(raw: str):
    """Return the most specific genre label for a pipe-separated dc_type value.

    Steps:
      1. Split on '|'; strip whitespace from each part.
      2. Drop all COMPONENT_TYPES parts (no genre signal).
      3. From the remainder, separate BASE_TYPES parts from specific-genre parts.
      4. If specific-genre parts exist, join them with '|' as the label.
      5. If only base-type parts remain, return the first base type (e.g. 'Monografie').
      6. If nothing remains, return None (record is pure component → exclude).
    """
    parts = [p.strip() for p in raw.split("|") if p.strip()]
    parts = [p for p in parts if p not in COMPONENT_TYPES]
    if not parts:
        return None  # pure component record
    specific = [p for p in parts if p not in BASE_TYPES]
    if specific:
        return "|".join(specific)
    return parts[0]  # only base types left; use first


def year_from_title(title: str):
    m = list(YEAR_RE.finditer(str(title)))
    return int(m[-1].group()) if m else None


def resolve_year(row):
    if pd.notna(row["dates"]) and str(row["dates"]).strip():
        try:
            y = int(str(row["dates"]).strip()[:4])
            if 1400 <= y <= 2029:
                return y
        except ValueError:
            pass
    return year_from_title(row["title"])


def assign_era(year):
    if year is None:
        return "unknown"
    if year < 1700:
        return "pre-1700"
    if year < 1800:
        return "1700-1800"
    if year < 1900:
        return "19th-c"
    return "modern"


def plot(pct_df: pd.DataFrame, era_totals: dict, fig_path: Path) -> None:
    """Stacked horizontal bar chart: each era is one bar, segments = dc_type % share."""
    eras   = [e for e in ERA_ORDER if e in pct_df.index]
    types  = list(pct_df.columns)
    n_eras = len(eras)

    fig, ax = plt.subplots(figsize=(11, 0.8 * n_eras + 2.0))

    # Use a qualitative palette; cycle if more types than colours
    cmap   = plt.get_cmap("tab20")
    colors = [cmap(i % 20) for i in range(len(types))]

    lefts = [0.0] * n_eras
    for i, dtype in enumerate(types):
        vals = [pct_df.loc[era, dtype] if era in pct_df.index else 0.0 for era in eras]
        bars = ax.barh(eras, vals, left=lefts, color=colors[i], label=dtype, height=0.6)

        # Label segments that are wide enough to be readable (>= 3 %)
        for bar, val, left in zip(bars, vals, lefts):
            if val >= 3.0:
                ax.text(
                    left + val / 2,
                    bar.get_y() + bar.get_height() / 2,
                    f"{val:.0f}%",
                    ha="center", va="center", fontsize=7, color="white", fontweight="bold",
                )
        lefts = [l + v for l, v in zip(lefts, vals)]

    # Embed record counts in the y-tick labels so they can't be obscured
    ax.set_yticks(range(len(eras)))
    ax.set_yticklabels(
        [f"{era}  (n={era_totals.get(era, 0):,})" for era in eras],
        fontsize=9,
    )

    ax.set_xlabel("Share within era (%)", fontsize=10)
    ax.set_title("dc_type distribution by era — DF_DE_TITLES", fontsize=12, pad=10)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax.set_xlim(0, 100)
    ax.invert_yaxis()

    ax.legend(
        loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0,
        fontsize=8, framealpha=0.85,
        title="dc_type", title_fontsize=8,
        ncol=1,
    )

    fig.tight_layout()
    fig_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"Figure saved: {fig_path}")


def load_data(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(
            path, columns=["obj_id", "title", "dc_type", "dates"]
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def main(data_path: Path, output_path: Path, fig_path: Path, top_n: int) -> None:
    print(f"Loading {data_path} ...")
    df = load_data(data_path)
    print(f"Shape: {df.shape}")

    df["year"] = df.apply(resolve_year, axis=1)
    df["era"]  = df["year"].apply(assign_era)

    df["dc_type"] = df["dc_type"].fillna("(none)").str.strip()
    df["dc_type"] = df["dc_type"].replace("", "(none)")

    # Normalize: split on |, drop component parts, keep most specific genre label
    df["dc_type_norm"] = df["dc_type"].apply(normalize_dctype)
    before = len(df)
    df = df[df["dc_type_norm"].notna()].copy()
    df["dc_type"] = df["dc_type_norm"]
    print(f"Retained {len(df):,} / {before:,} records after normalizing dc_type.")

    # Save filtered/normalized frame for inspection
    filtered_path = output_path.parent / "sr11_dctype_filtered.csv"
    df[["obj_id", "era", "dc_type", "dates"]].to_csv(filtered_path, index=False)
    print(f"Filtered records saved: {filtered_path}")

    ct = pd.crosstab(df["era"], df["dc_type"])
    ct = ct.reindex([e for e in ERA_ORDER if e in ct.index])

    # Long-form CSV
    rows = []
    for era in ct.index:
        era_total = int(ct.loc[era].sum())
        for dtype, n in ct.loc[era].items():
            if n == 0:
                continue
            rows.append({
                "era":       era,
                "dc_type":   dtype,
                "count":     int(n),
                "era_total": era_total,
                "pct":       round(100 * n / era_total, 2) if era_total else 0.0,
            })

    out = pd.DataFrame(rows).sort_values(["era", "count"], ascending=[True, False])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(output_path, index=False)
    print(f"CSV saved: {output_path}\n")

    # Console summary
    for era in ct.index:
        sub       = out[out["era"] == era].head(top_n)
        era_total = int(ct.loc[era].sum())
        print(f"── {era}  (total: {era_total:,})")
        for _, r in sub.iterrows():
            bar = "█" * int(r["pct"] / 2)
            print(f"   {r['dc_type']:<30}  {r['count']:>9,}  {r['pct']:>5.1f}%  {bar}")
        print()

    # Build percentage pivot for top-N types (pooled across all eras)
    top_types = (
        out.groupby("dc_type")["count"].sum()
        .nlargest(top_n)
        .index.tolist()
    )
    era_totals = {era: int(ct.loc[era].sum()) for era in ct.index}

    pct_pivot = pd.DataFrame(index=ct.index, columns=top_types, dtype=float).fillna(0.0)
    for era in ct.index:
        t = era_totals[era]
        for dtype in top_types:
            if dtype in ct.columns:
                pct_pivot.loc[era, dtype] = round(100 * ct.loc[era, dtype] / t, 2) if t else 0.0

    # Collapse remaining types into "other"
    shown_pct   = pct_pivot.sum(axis=1)
    other_pct   = 100.0 - shown_pct
    pct_pivot["(other)"] = other_pct.clip(lower=0.0)

    plot(pct_pivot, era_totals, fig_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data",   type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--fig",    type=Path, default=FIG_PATH)
    parser.add_argument("--top",    type=int,  default=10,
                        help="Top N dc_types to show in chart and console (default: 10)")
    args = parser.parse_args()
    main(args.data, args.output, args.fig, args.top)

#!/usr/bin/env python3
"""
Purpose:  Count DDB Sector 2 objects by language code (the `lang` column).
          Multi-value entries are exploded so each language code is tallied
          independently. Null / empty values are counted as "(none)".
Usage:    python scripts/analysis/count_lang.py [--top N]
          N controls how many language codes are shown in the PNG (default 30).
          All codes are always written to the CSV.
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  data/processed/lang_counts.csv
          notes/images/lang_counts.png
Dependencies: pandas, pyarrow, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import argparse
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--top", type=int, default=30,
                    help="Number of language codes shown in PNG (default: 30)")
args = parser.parse_args()

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET = Path("data/out/s2/s2_meta.parquet")
CSV_OUT = Path("data/processed/lang_counts.csv")
PNG_OUT = Path("notes/images/lang_counts.png")
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)
PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

# ── load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "lang"])
print(f"  {len(df):,} rows")

# ── normalise lang to list-of-strings per row ──────────────────────────────────
# The column may arrive as: Python list, space-separated string, or scalar.
def to_codes(val) -> list[str]:
    if pd.isna(val) or val is None or val == "":
        return ["(none)"]
    if isinstance(val, list):
        codes = [str(v).strip() for v in val if str(v).strip()]
        return codes if codes else ["(none)"]
    # string — split on whitespace
    codes = str(val).split()
    return codes if codes else ["(none)"]

lang_series = df["lang"].apply(to_codes).explode()
total_tokens = len(lang_series)

# ── count ───────────────────────────────────────────────────────────────────────
counts = lang_series.value_counts().reset_index()
counts.columns = ["lang_code", "count"]
counts["pct"] = (counts["count"] / total_tokens * 100).round(2)
counts = counts.sort_values("count", ascending=False).reset_index(drop=True)

counts.to_csv(CSV_OUT, index=False)
print(f"CSV saved → {CSV_OUT}  ({len(counts)} distinct codes)")

# ── console summary ─────────────────────────────────────────────────────────────
print()
print(f"{'lang_code':<20} {'count':>10} {'%':>7}")
print("-" * 40)
for _, r in counts.head(40).iterrows():
    print(f"{r.lang_code:<20} {r.count:>10,} {r.pct:>6.2f}%")
if len(counts) > 40:
    print(f"  … {len(counts) - 40} more codes in CSV")

# ── plot ───────────────────────────────────────────────────────────────────────
TOP_N = args.top
plot_df = counts.head(TOP_N).copy()

# compute "other" bar
other_count = int(counts.iloc[TOP_N:]["count"].sum()) if len(counts) > TOP_N else 0
n_other_codes = max(0, len(counts) - TOP_N)

fig, ax = plt.subplots(figsize=(10, max(5, len(plot_df) * 0.38 + 1.2)))

colors = ["#c0392b" if c == "(none)" else "#2980b9" for c in plot_df["lang_code"]]
bars = ax.barh(plot_df["lang_code"][::-1], plot_df["count"][::-1],
               color=colors[::-1], edgecolor="none")

# count label inside / beside each bar
x_max = plot_df["count"].max()
for bar, (_, r) in zip(bars, plot_df[::-1].iterrows()):
    w = bar.get_width()
    label = f"{int(w):,}  ({r.pct:.1f}%)"
    x_pos = w + x_max * 0.01
    ax.text(x_pos, bar.get_y() + bar.get_height() / 2,
            label, va="center", ha="left", fontsize=7.5, color="#333")

if other_count:
    ax.barh(["other…"], [other_count], color="#95a5a6", edgecolor="none")
    ax.text(other_count + x_max * 0.01, 0,
            f"{other_count:,}  ({other_count / total_tokens * 100:.1f}%)  "
            f"[{n_other_codes} codes]",
            va="center", ha="left", fontsize=7.5, color="#333")

ax.set_xlabel("Object count (lang tokens)")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(
    f"DDB Sector 2 — language distribution (top {TOP_N} of {len(counts)} codes)\n"
    f"Total lang tokens: {total_tokens:,}  ·  Total objects: {len(df):,}  ·  "
    f"Blue = language code  ·  Red = (none)",
    fontsize=9.5,
)

fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
print(f"\nPNG saved → {PNG_OUT}")

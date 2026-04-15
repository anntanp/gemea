#!/usr/bin/env python3
"""
Purpose:  Validate hierarchy-type title quality by computing what fraction of
          titles are generic/structural (boilerplate) vs. content-bearing, for
          both strong and partial candidate htypes identified in
          notes/corpus-analysis/htype-title-quality.md.
Usage:    python scripts/analysis/validate_htype_title_quality.py
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  data/processed/htype_title_quality.csv
          notes/images/htype_title_quality.png
Dependencies: pandas, pyarrow, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET  = Path("data/out/s2/s2_meta.parquet")
CSV_OUT  = Path("data/processed/htype_title_quality.csv")
PNG_OUT  = Path("notes/images/htype_title_quality.png")
PNG_OUT.parent.mkdir(parents=True, exist_ok=True)
CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

# ── generic-title patterns per htype ──────────────────────────────────────────
# A title is "generic" if it is just the section-type label or a boilerplate
# placeholder that carries no descriptive content.
GENERIC_PATTERNS = {
    # strong candidates
    "htype_017": re.compile(
        r"^(inhalts?\s*[-–]?\s*verzeichni[sz][se]?\.?|inhalt\.?|table\s+of\s+contents?\.?|"
        r"contents?\.?|f.rtekning.*|elenco.*)$",
        re.IGNORECASE,
    ),
    "htype_004": re.compile(
        r"^(handschriftliche?\s+eintragungen?\.?|handschriftliches?\s+\w+.*|"
        r"marginalien?\.?|annotations?\.?)$",
        re.IGNORECASE,
    ),
    "htype_010": re.compile(
        r"^(handschriftliche?\s+eintragungen?\.?)$",
        re.IGNORECASE,
    ),
    "htype_016": re.compile(
        r"^(register(\.|\s.*)?|index\.?|indices?\.?|catalogus\s+\w+\.?|"
        r"sachweiser\.?|indices\s+.*|registrum\s+.*)$",
        re.IGNORECASE,
    ),
    "htype_028": re.compile(
        r"^(vorwort\.?|vorrede\.?|praefatio\.?|preface\.?|pr[eé]face\.?|"
        r"einleitung\.?|\u5e8f|epistola\s+\w+\.?|prooemium\.?|prolog\.?|prologue\.?)$",
        re.IGNORECASE,
    ),
    # partial candidates
    "htype_029": re.compile(
        r"^(widmung\.?|widmungsseiten?\.?|d[eé]dicace\.?|dedication\.?|dedicatio\.?)$",
        re.IGNORECASE,
    ),
    "htype_027": re.compile(
        r"^(aliud\.?|idem\.?|hymnus\s+\w+\.?|carmen\s+\w+\.?|versus\s+\w+\.?|ode\s+\w+\.?)$",
        re.IGNORECASE,
    ),
    "htype_001": re.compile(
        r"^(note\.?|deckel\.?|einband\.?|abschnitt\.?|\[leer\]\.?|leer\.?|blank\.?)$",
        re.IGNORECASE,
    ),
    "htype_018": re.compile(
        r"^((seconde?|troisi[eè]me|erste[rns]?|zweite[rns]?|dritte[rns]?|"
        r"vierte[rns]?|premier[e]?|deuxième)\s+(parte?|partie|theil|teil|abschnitt|section\.?)|"
        r"capitulum[\s.]+\w+\.?|einband\.?|kapitel\s*\w*\.?)$",
        re.IGNORECASE,
    ),
}

HTYPE_LABELS = {
    "htype_017": "Inhaltsverzeichnis",
    "htype_004": "Annotation",
    "htype_010": "Eintrag",
    "htype_016": "Index",
    "htype_028": "Vorwort",
    "htype_029": "Widmung",
    "htype_027": "Vers",
    "htype_001": "Abschnitt",
    "htype_018": "Kapitel",
}

STRONG    = {"htype_017", "htype_004", "htype_010", "htype_016", "htype_028"}
PARTIAL   = {"htype_029", "htype_027", "htype_001", "htype_018"}

# ── load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "title", "hierarchy_type"])
df = df[
    df["hierarchy_type"].notna()
    & ~df["hierarchy_type"].str.contains(" ", na=False)
    & df["hierarchy_type"].isin(GENERIC_PATTERNS)
]
df["title_clean"] = df["title"].fillna("").str.strip()
print(f"  {len(df):,} rows in candidate htypes")

# ── classify ───────────────────────────────────────────────────────────────────
records = []
for ht, pat in GENERIC_PATTERNS.items():
    sub = df[df["hierarchy_type"] == ht]
    total = len(sub)
    if total == 0:
        continue

    null_n   = (sub["title_clean"] == "").sum()
    non_null = sub[sub["title_clean"] != ""]
    generic_mask = non_null["title_clean"].apply(lambda t: bool(pat.match(t)))
    generic_n    = int(generic_mask.sum())
    content_n    = int((~generic_mask).sum())

    # generic% counts both null titles and pattern-matched generic titles
    generic_pct = (generic_n + null_n) / total * 100

    top_generic  = non_null[generic_mask]["title_clean"].value_counts().head(5)
    top_content  = non_null[~generic_mask]["title_clean"].value_counts().head(3)

    records.append({
        "hierarchy_type": ht,
        "htype_label":    HTYPE_LABELS[ht],
        "category":       "strong" if ht in STRONG else "partial",
        "total":          total,
        "null_title":     int(null_n),
        "generic":        generic_n,
        "content":        content_n,
        "generic_pct":    round(generic_pct, 1),
        "top_generic":    " | ".join(f'"{k}" ({v:,})' for k, v in top_generic.items()),
        "top_content":    " | ".join(f'"{k}" ({v:,})' for k, v in top_content.items()),
    })

results = pd.DataFrame(records).sort_values("generic_pct", ascending=False)

# ── print summary ──────────────────────────────────────────────────────────────
print()
print(f"{'htype':<12} {'label':<22} {'cat':<8} {'total':>9} {'null':>7} "
      f"{'generic':>8} {'content':>8} {'generic%':>9}")
print("-" * 90)
for _, r in results.iterrows():
    print(f"{r.hierarchy_type:<12} {r.htype_label:<22} {r.category:<8} "
          f"{r.total:>9,} {r.null_title:>7,} {r.generic:>8,} {r.content:>8,} "
          f"{r.generic_pct:>8.1f}%")

print()
for _, r in results.iterrows():
    print(f"\n[{r.hierarchy_type}] {r.htype_label}  ({r.generic_pct:.1f}% generic)")
    print(f"  top generic : {r.top_generic}")
    print(f"  top content : {r.top_content}")

# ── save CSV ───────────────────────────────────────────────────────────────────
results.to_csv(CSV_OUT, index=False)
print(f"\nCSV saved → {CSV_OUT}")

# ── plot ───────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(10, 6))

labels    = results["htype_label"].tolist()
generic   = results["generic_pct"].tolist()
content   = [100 - g for g in generic]
colors_g  = ["#c0392b" if r.category == "strong" else "#e67e22"
             for _, r in results.iterrows()]

y = range(len(labels))
bars_g = ax.barh(y, generic,  color=colors_g, edgecolor="none", label="generic/null")
bars_c = ax.barh(y, content,  left=generic, color="#95a5a6", edgecolor="none",
                 alpha=0.4, label="content-bearing")

# percentage labels inside the generic bar
for i, (bar, pct) in enumerate(zip(bars_g, generic)):
    ax.text(min(pct / 2, pct - 1), i, f"{pct:.1f}%",
            va="center", ha="center", fontsize=8, color="white", fontweight="bold")

ax.set_yticks(list(y))
ax.set_yticklabels(labels, fontsize=9)
ax.set_xlabel("% of titles")
ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
ax.spines[["top", "right"]].set_visible(False)
ax.set_title(
    "Hierarchy-type title quality — fraction of generic/null titles\n"
    "Red = strong candidate · Orange = partial candidate · Grey = content-bearing",
    fontsize=10,
)

# total count annotation on right
for i, (_, r) in enumerate(results.iterrows()):
    ax.text(101, i, f"n={r.total:,}", va="center", fontsize=7, color="#555")

fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
print(f"PNG saved → {PNG_OUT}")

#!/usr/bin/env python3
"""
Purpose:  Classify DDB object titles into three classes:
            - work_title   : potential literary/intellectual work title (GND Werk candidate)
            - section_label: structural section name (Vorwort, Register, Widmung, …)
            - physical_label: digitisation/physical-object label (Titelblatt, Einband, Deckel, …)
          Strategy (Option C hybrid):
            Stage 1 — blanket exclude htypes where no titles are work titles:
                       htype_004 (Annotation), htype_010 (Eintrag), htype_017 (Inhaltsverzeichnis)
            Stage 2 — cross-cutting pattern filter on all remaining objects
Usage:    python scripts/analysis/filter_content_titles.py
Inputs:   data/out/s2/s2_meta.parquet
Outputs:  data/processed/title_class_counts.csv   (counts by htype × class)
          data/processed/title_class_sample.csv   (random sample, 5 per htype × class)
          notes/images/title_class_breakdown.png
Dependencies: pandas, pyarrow, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import re
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────────
PARQUET     = Path("data/out/s2/s2_meta.parquet")
COUNTS_OUT  = Path("data/processed/title_class_counts.csv")
SAMPLE_OUT  = Path("data/processed/title_class_sample.csv")
PNG_OUT     = Path("notes/images/title_class_breakdown.png")
for p in (COUNTS_OUT.parent, PNG_OUT.parent):
    p.mkdir(parents=True, exist_ok=True)

# ── Stage 1: blanket-excluded htypes ──────────────────────────────────────────
# Even outlier titles in these types are descriptive labels, not work titles.
BLANKET_EXCLUDE = {
    "htype_001",  # Abschnitt      — section headings, not works
    "htype_004",  # Annotation     — manuscript annotation labels
    "htype_010",  # Eintrag        — same as Annotation
    "htype_016",  # Index          — back-matter registers/indexes
    "htype_017",  # Inhaltsverzeichnis — table-of-contents labels
    "htype_018",  # Kapitel        — chapter headings, not works
    "htype_028",  # Vorwort        — prefaces/paratexts
    "htype_029",  # Widmung        — dedication texts
}

# ── Stage 2: cross-cutting pattern blocklists ──────────────────────────────────
# Order matters: physical_label is checked first, then section_label.
# Anything not matching either is classified as work_title.

# Physical / digitisation labels — refer to the physical object or scan artefact
PHYSICAL_RE = re.compile(
    r"""^(
        # book binding / cover
        einband\.?|einband\s+(vorne?|hinten?|vorder|rück)\w*\.?|
        vorderdeckel\.?|rückdeckel\.?|deckel\.?|rücken\.?|
        umschlag\.?|vorsatz\.?|vorblatt\.?|schmutztitel\.?|
        spiegel\.?|buchblock\.?|schnitt\.?|

        # title page variants
        titelblatt\.?|titelseite\.?|titelei\.?|

        # colour / calibration targets
        maßstab[/\s]farbkeil\.?|farbkeil\.?|maßstab\.?|

        # plates / illustrations (numbered or generic)
        \[?tafel\s*\w*\.?\]?|tab\.\s*\w+\.?|tafel\s*[ivxlcdm]+\.?|
        tafel\s*\d+\.?|tafeln\.?|
        \[?frontispiz\]?\.?|
        abbildung\.?|\[abbildung\]\.?|
        holzschnitt\.?|\[holzschnitt\]\.?|
        \[?ohne\s+titel\]?\.?|

        # folio / page ranges
        \[\d+[rv][-–]\d+[rv]\]|

        # portraits
        portrait\.?|porträt\.?|

        # single letters / roman numerals (index tabs, ordinal markers)
        [a-z]\.?|[ivxlcdm]+\.|

        # empty / unclassified
        leere?\s*seiten?\.?|leer\.?|
        \(ohne\s+kategorisierung\)\.?|
        \[leer\]\.?|blank\.?|

        # impressum / imprint block
        impressum\.?|kolophon\.?
    )$""",
    re.IGNORECASE | re.VERBOSE,
)

# Section / structural labels — the title IS the section type
SECTION_RE = re.compile(
    r"""^(
        # table of contents
        inhalts?\s*[-–]?\s*verzeichni[sz][se]?\.?|inhaltsübersicht\.?|
        inhalt\.?|inhalt:|innhalt\.?|
        contents?\.?|table\s+of\s+contents?\.?|
        目錄|indice(\s+del\s+.+)?\.?|sommaire\.?|sommario\.?|
        index\s+capitum\.?|elenco.*|
        handschriftliches\s+inhaltsverzeichnis.*|

        # preface / introduction
        vorwort(\s+zur\s+(ersten?|zweiten?|dritten?)\s+auflage)?\.?|
        vorwort\s*des\s+\w+\.?|vorrede\.?|vorbericht\.?|
        vorbemerkung(en)?\.?|vorerinnerung\.?|
        \[vorwort.*\]\.?|\[vorwort\]|
        praefatio\.?|præfatio\.?|prooemium\.?|prolog\.?|prologue?\.?|
        preface\.?|pr[eé]face\.?|prefazione\.?|
        introduction\.?|einleitung\.?|序|epistola\s+nuncupatoria\.?|
        ad\s+lectorem\.?|

        # index / register
        register\.?|register\s+der\s+\w+.*|das\s+\w+\s+register\.?|
        sach\s*register\.?|sachverzeichnis\.?|namen\s*register\.?|
        namenverzeichnis\.?|personen\s*register\.?|
        alphabetisches\s+\w+.*|namen\s*-\s*und\s+sachregister\.?|
        chronologisches\s+register.*|
        index\.?|index\s+rerum.*|indices?\.?|registrum\.?|
        literaturverzeichnis\.?|verzeichnis\s+der\s+abbildungen\.?|
        katalog\.?|

        # dedication
        widmung(en)?\.?|widmungsseiten?\.?|\[widmung\]\.?|
        dedicatio\.?|dedicatoria\.?|d[eé]dicace\.?|dedication\.?|
        epistola\s+dedicatoria\.?|zuschrifft?\.?|zueignung\.?|
        widmungsvorrede\.?|widmungsschreiben\.?|
        handschriftliche\s+widmung\.?|

        # appendix / supplement
        anhang\.?|appendix\.?|beilage(\s+\w+)?\.?|

        # generic structural
        text\.?|\[text\]\.?|text\s+(vorder|rück)seite\.?|
        einleitung\.?|
        brief\.?|\[brief\]\.?|
        \[begleitschreiben\]\.?|
        faszikel\s*\w*\.?|\[faszikel\s*\w*\]\.?|

        # verse / poem placeholders
        aliud\.?|idem\.?|alio\.?|ad\s+eundem\.?|

        # manuscript annotation labels (not blanket-excluded htypes)
        handschriftliche?\s+eintragungen?\.?|
        handschriftliche?\s+notizen?\.?|
        handschriftliche?\s+ergänzungen?\.?|
        handschriftliche?\s+anmerkungen?\.?|
        handschriftliche?\s+korrekturen?\.?|
        anstreichungen?\.?|manicula\.?|randzeichnung\.?|
        errata\.?|nota\s*bene.*|

        # newspaper / journal section headers (in htype_006 context)
        rezensionen?\.?|bücherschau\.?|rundschau\.?|neuerscheinungen?\.?|
        werbung\.?|vermischtes\.?|verschiedenes\.?|nachrichten\.?|
        anzeigen\.?|mitteilungen?\.?|literatur\.?|personalien\.?|
        vereinsnachrichten?\.?|briefkasten\.?|
        frontmatter\.?|titelaufnahme\.?

    )$""",
    re.IGNORECASE | re.VERBOSE,
)

HTYPE_LABELS = {
    "htype_001": "Abschnitt", "htype_003": "Beigefügtes Werk",
    "htype_004": "Annotation", "htype_006": "Aufsatz",
    "htype_007": "Band", "htype_008": "Beilage",
    "htype_010": "Eintrag", "htype_011": "Faszikel",
    "htype_012": "Fragment", "htype_013": "Handschrift",
    "htype_014": "Heft", "htype_015": "Illustration",
    "htype_016": "Index", "htype_017": "Inhaltsverzeichnis",
    "htype_018": "Kapitel", "htype_019": "Karte",
    "htype_020": "Mehrbändiges Werk", "htype_021": "Monografie",
    "htype_022": "Musik", "htype_023": "Fortlaufendes Sammelwerk",
    "htype_024": "Privilegie", "htype_025": "Rezension",
    "htype_026": "Text", "htype_027": "Vers",
    "htype_028": "Vorwort", "htype_029": "Widmung",
    "htype_030": "Bestand", "htype_031": "Gliederung",
    "htype_032": "Serie", "htype_033": "Unterserie",
    "htype_034": "Archivale", "htype_035": "Teil",
    "htype_036": "Bestandsserie", "htype_037": "Bestandsklassifikation",
    "htype_038": "Brief", "htype_039": "Konvolut",
    "htype_040": "Mappe", "htype_041": "Archiv",
    "htype_044": "Zeitung", "htype_045": "Jahrgang",
    "htype_046": "Monat", "htype_047": "Tag",
    "htype_048": "Tektonik", "UNK": "UNK",
}


def classify(title: str, htype: str) -> str:
    if htype in BLANKET_EXCLUDE:
        return "section_label"
    t = title.strip()
    if not t:
        return "physical_label"   # null/empty → no title at all
    if PHYSICAL_RE.match(t):
        return "physical_label"
    if SECTION_RE.match(t):
        return "section_label"
    return "work_title"


# ── load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "title", "hierarchy_type", "is_part_of"])
df["hierarchy_type"] = df["hierarchy_type"].fillna("UNK")
# collapse multi-value htypes to first token
df["hierarchy_type"] = df["hierarchy_type"].str.split().str[0]
df["title_clean"] = df["title"].fillna("").str.strip()
print(f"  {len(df):,} rows")

# ── classify ───────────────────────────────────────────────────────────────────
print("Classifying …")
df["title_class"] = df.apply(
    lambda r: classify(r["title_clean"], r["hierarchy_type"]), axis=1
)

# ── counts ─────────────────────────────────────────────────────────────────────
counts = (
    df.groupby(["hierarchy_type", "title_class"])
    .size()
    .reset_index(name="count")
)
counts["htype_label"] = counts["hierarchy_type"].map(HTYPE_LABELS).fillna(counts["hierarchy_type"])
pivot = counts.pivot_table(
    index=["hierarchy_type", "htype_label"],
    columns="title_class",
    values="count",
    fill_value=0,
).reset_index()
pivot.columns.name = None
for col in ("work_title", "section_label", "physical_label"):
    if col not in pivot.columns:
        pivot[col] = 0
pivot["total"] = pivot["work_title"] + pivot["section_label"] + pivot["physical_label"]
pivot["work_title_pct"] = (pivot["work_title"] / pivot["total"] * 100).round(1)
pivot = pivot.sort_values("total", ascending=False)

pivot.to_csv(COUNTS_OUT, index=False)
print(f"Counts saved → {COUNTS_OUT}")

# ── summary ────────────────────────────────────────────────────────────────────
total_work     = int(pivot["work_title"].sum())
total_section  = int(pivot["section_label"].sum())
total_physical = int(pivot["physical_label"].sum())
grand_total    = int(pivot["total"].sum())

print()
print(f"{'htype':<12} {'label':<24} {'total':>9} {'work_title':>10} {'section':>9} {'physical':>9} {'work%':>7}")
print("-" * 90)
for _, r in pivot.iterrows():
    print(f"{r.hierarchy_type:<12} {r.htype_label:<24} {r.total:>9,} "
          f"{r.work_title:>10,} {r.section_label:>9,} {r.physical_label:>9,} "
          f"{r.work_title_pct:>6.1f}%")
print("-" * 90)
print(f"{'TOTAL':<12} {'':<24} {grand_total:>9,} "
      f"{total_work:>10,} {total_section:>9,} {total_physical:>9,} "
      f"{total_work/grand_total*100:>6.1f}%")

# ── sample ─────────────────────────────────────────────────────────────────────
samples = []
for (ht, cls), grp in df.groupby(["hierarchy_type", "title_class"]):
    s = grp[["obj_id", "hierarchy_type", "title_class", "title_clean", "is_part_of"]].sample(
        min(5, len(grp)), random_state=42
    )
    samples.append(s)
sample_df = pd.concat(samples).sort_values(["hierarchy_type", "title_class"])
sample_df.to_csv(SAMPLE_OUT, index=False)
print(f"Sample saved  → {SAMPLE_OUT}")

# ── plot ───────────────────────────────────────────────────────────────────────
plot_df = pivot[pivot["total"] >= 100].copy()   # skip tiny htypes
plot_df = plot_df.sort_values("work_title_pct", ascending=True)
labels  = plot_df["htype_label"].tolist()
y       = range(len(labels))

fig, ax = plt.subplots(figsize=(12, max(6, len(labels) * 0.38)))

w  = plot_df["work_title"].values
s  = plot_df["section_label"].values
ph = plot_df["physical_label"].values
tot = plot_df["total"].values

bars_w  = ax.barh(list(y), w  / tot * 100, color="#2ecc71", edgecolor="none", label="work_title")
bars_s  = ax.barh(list(y), s  / tot * 100, left=w / tot * 100,
                  color="#e74c3c", edgecolor="none", label="section_label")
bars_ph = ax.barh(list(y), ph / tot * 100, left=(w + s) / tot * 100,
                  color="#95a5a6", edgecolor="none", label="physical_label")

# work_title % label inside green bar
for i, (wv, tv, pct) in enumerate(zip(w, tot, plot_df["work_title_pct"])):
    if wv / tv * 100 > 4:
        ax.text(wv / tv * 100 / 2, i, f"{pct:.0f}%",
                va="center", ha="center", fontsize=7.5,
                color="white", fontweight="bold")

ax.set_yticks(list(y))
ax.set_yticklabels(labels, fontsize=8.5)
ax.set_xlabel("% of titles")
ax.set_xlim(0, 100)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x)}%"))
ax.spines[["top", "right"]].set_visible(False)
ax.legend(loc="lower right", fontsize=8)
ax.set_title(
    f"DDB Sector 2 — title classification by hierarchy_type\n"
    f"Green = work_title ({total_work:,}, {total_work/grand_total*100:.1f}%)  "
    f"Red = section_label ({total_section:,})  "
    f"Grey = physical_label ({total_physical:,})",
    fontsize=9.5,
)

for i, (_, r) in enumerate(plot_df.iterrows()):
    ax.text(101, i, f"n={r.total:,}", va="center", fontsize=6.5, color="#555")

fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
print(f"PNG saved     → {PNG_OUT}")

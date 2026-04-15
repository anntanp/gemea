# GeMeA — Architecture Decision Record: Hierarchy-Type Title Filtering

**Format:** MADR (Markdown Architecture Decision Record)
**Subject:** Which DDB objects to exclude from GND Werk linking based on `hierarchy_type`
**Source:** `notes/corpus-analysis/htype-title-quality.md`, `scripts/analysis/filter_content_titles.py`
**Status:** Accepted

---

## ADR-01 — Blanket-exclude seven hierarchy types from GND Werk linking

**Status:** Accepted
**Date:** 2026-04-09

### Context

The GND Werk linking pipeline (`link_gnd_works.py`) requires titles that could plausibly identify a standalone literary or intellectual work — a title that could have a GND Werk entry. The DDB Sector 2 parquet (`data/out/s2/s2_meta.parquet`, 18,570,245 objects) contains a `hierarchy_type` field that encodes the structural role of each object within its document hierarchy.

Sampling and frequency analysis of titles per hierarchy type (see `notes/corpus-analysis/htype-title-quality.md`, `scripts/analysis/explore_top_titles.py`, `scripts/analysis/sample_work_titles.py`) revealed three categories of non-work titles:

1. **Section labels** — the title is just the section-type name ("Inhalt", "Vorwort", "Register", "Handschriftliche Eintragungen")
2. **Physical/digitisation labels** — the title refers to the physical object or scan artefact ("Titelblatt", "Einband", "Deckel", "Spiegel", "Maßstab/Farbkeil")
3. **Structural ordinals** — the title is an ordinal or generic chapter heading ("Caput I.", "Erstes Kapitel.", "III.", "Erster Aufzug.", single letters A–Z as index tabs)

#### htype_017 · Inhaltsverzeichnis

Titles are overwhelmingly the section-type label or a synonym ("Inhalt", "Inhaltsverzeichnis", "目錄", "Contents"). Even non-boilerplate outliers are structural ("Handschriftliches Inhaltsverzeichnis des Sammelbandes"). No title in this type can be a standalone work title.

#### htype_004 · Annotation

Almost exclusively "Handschriftliche Eintragung/en" — a cataloguer label for the presence of manuscript annotations. The rare outlier ("Aufführungsnotizen (Abbado)") is a descriptive label, not a work title.

#### htype_010 · Eintrag

Same pattern as htype_004. All sampled titles are variations of "Handschriftliche Eintragungen".

#### htype_001 · Abschnitt

The top-150 most frequent titles are dominated by:
- Physical/digitisation labels not fully caught by patterns: single letters as index tabs (A–Z), "Viola", "Basso", "Partitur", "Violoncello", "Sinfonia" (music part labels), "Errata.", "Druckfehler.", "Vorbericht.", "Lebenslauf.", "Schnitte"
- Structural ordinals: "Erster Theil.", "Erster Aufzug.", "Zweyter Aufzug.", "Scene II.", "Scene III."
- Journal section headers: "Bücherschau", "Rundschau", "Werbung", "Schulnachrichten", "Briefkasten", "Vereinsnachrichten", "Buchbesprechungen"
- Errata sections: "Errata.", "Druckfehler.", "Berichtigungen", "Verbesserungen."

More fundamentally, Abschnitt is a structural subdivision of a parent work. Even descriptive section titles ("Die Richtkraft der Aufmerksamkeit") are headings within a larger work, not standalone literary works suitable for GND Werk linking.

#### htype_018 · Kapitel

The top-150 most frequent titles are dominated by:
- Latin chapter ordinals: "Caput I." through "Caput X.", "Cap. I.", "Cap. II.", "Cap. III."
- German chapter ordinals: "Erstes Kapitel.", "Zweites Kapitel.", "Drittes Kapitel.", "Viertes Kapitel.", "Fünftes Kapitel.", "Sechstes Kapitel."
- Roman numerals: "III.", "IV.", "V.", "VI.", "VII.", "VIII.", "IX.", "X.", "XI."
- Single letters as index tabs (A–Z)
- Physical label variants missed by patterns: "Spiegel vorne", "Spiegel hinten", "Leerseiten", "Leerseite", "Vorderseite", "Rückseite", "Maßstab / Farbkeil" (spacing variants), "Titeldaten", "Cover", "〚 Kein Titel 〛"
- Auction/legal conditions: "Versteigerungs-Bedingungen", "Auktions-Bedingungen", "Auktionsbedingungen", "Conditions de la vente"

Same fundamental issue as htype_001: Kapitel is a structural subdivision; chapter titles are not standalone literary works.

#### Summary of title classification results (Option C hybrid, `filter_content_titles.py`)

Before adding htype_001 and htype_018 to the blanket-exclude list:

| htype | Label | total | work_title | section | physical | work% |
|-------|-------|------:|----------:|--------:|---------:|------:|
| htype_017 | Inhaltsverzeichnis | 64,380 | 0 | 64,380 | 0 | 0.0% |
| htype_004 | Annotation | 1,772 | 0 | 1,772 | 0 | 0.0% |
| htype_010 | Eintrag | 1,327 | 0 | 1,327 | 0 | 0.0% |
| htype_028 | Vorwort | 61,256 | 32,113 | 29,089 | 54 | 52.4% |
| htype_016 | Index | 59,158 | 41,627 | 17,465 | 66 | 70.4% |
| htype_029 | Widmung | 13,237 | 10,051 | 3,185 | 1 | 75.9% |
| **htype_018** | **Kapitel** | **2,664,050** | **2,303,455** | **90,951** | **269,644** | **86.5%** |
| **htype_001** | **Abschnitt** | **2,246,940** | **2,048,208** | **46,968** | **151,764** | **91.2%** |

The 86–91% work_title rates for htype_001 and htype_018 are inflated by undetected structural labels (ordinals, music parts, journal section headers, physical variants). Cross-cutting pattern matching cannot reliably recover work titles from these types because even truly descriptive titles are chapter headings, not standalone works.

### Decision

Blanket-exclude the following eight hierarchy types from GND Werk linking:

| htype | Label | Reason |
|-------|-------|--------|
| htype_001 | Abschnitt | Structural subdivisions; titles are section headings, not works |
| htype_004 | Annotation | Cataloguer labels for manuscript annotations |
| htype_010 | Eintrag | Same as htype_004 |
| htype_016 | Index | Back-matter registers and indexes in all languages |
| htype_017 | Inhaltsverzeichnis | Title is always the section-type label |
| htype_018 | Kapitel | Structural subdivisions; titles are chapter headings, not works |
| htype_028 | Vorwort | Prefaces and paratexts; titles are section-type labels |
| htype_029 | Widmung | Dedication texts addressed to named persons, not standalone works |

**htype_027 (Vers) is retained** with cross-cutting pattern filtering: random sampling showed genuine poem titles ("Wintertraum.", "Die Irrlichter", "Vom Wolf und den sieben Geißlein") that are valid GND Werk candidates.

The cross-cutting `PHYSICAL_RE` / `SECTION_RE` pattern filter (Stage 2) remains in place for all remaining htypes to catch residual non-work titles.

### Consequences

**Positive:**
- Eliminates ~4.9M objects (htype_001: 2.25M + htype_018: 2.66M + htype_017: 64K + htype_004: 1.8K + htype_010: 1.3K) that would generate false positive or low-precision GND lookup queries
- Reduces noise in the linking pipeline without requiring complex ordinal/structural pattern maintenance
- Consistent with the GND Werk linking goal: only objects with titles that could identify a standalone intellectual work are sent for lookup

**Negative:**
- A small number of genuinely content-bearing chapter titles in htype_018 (e.g. self-contained essays or named sections) are excluded; judged acceptable given the low signal-to-noise ratio
- htype_028 (Vorwort, 52.4% work_title) and htype_016 (Index, 70.4%) are retained with pattern filtering — their borderline status should be revisited if linking precision is low

### Implementation

`BLANKET_EXCLUDE` set in `scripts/analysis/filter_content_titles.py`:

```python
BLANKET_EXCLUDE = {
    "htype_001",  # Abschnitt
    "htype_004",  # Annotation
    "htype_010",  # Eintrag
    "htype_016",  # Index
    "htype_017",  # Inhaltsverzeichnis
    "htype_018",  # Kapitel
    "htype_028",  # Vorwort
    "htype_029",  # Widmung
}
```

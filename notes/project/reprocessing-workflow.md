# GeMeA — Corpus Reprocessing Workflow

## 1. Overview

This note documents the end-to-end pipeline from the raw DDB data dump to the tokenized parquet used for NER analysis and GND Werk linking. It supersedes the earlier notebook-based approach (`DF_DE_TITLES_20240125b.pkl`). All steps are scripted and reproducible from the project root.

**Why reprocess?** The pkl was built from notebooks with unspecified dependencies, a narrower htype filter, and a `langid` secondary language filter that systematically excluded historically significant titles. See `notes/adr/reprocessing-adr.md` and `notes/adr/corpus-source-adr.md` (ADR-02) for the full decision record.

---

## 2. Pipeline diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  DDB public data dump                                               │
│  (DDB Sector 2 — ~18.5M EDM objects, cortex JSON format)           │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  download / ingest
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data/sqlite/s2.sqlite                                              │
│  table: objs  · column: bufgz (gzip-compressed cortex JSON)        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  scripts/py/export_ddb.py
                               │  (via scripts/sh/process_sqlite.sh)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data/out/s2/s2_meta.parquet                18,570,245 rows         │
│  columns: obj_id · title · lang · dc_type · hierarchy_type ·       │
│           dc_issued · dc_creator · dc_contributor · dc_publisher    │
│           dc_subject · dc_subject_uris · dc_date · agents · ...    │
└──────────┬──────────────────────────────────────────────────────────┘
           │
           │  Step 1 — htype filter  (ADR-01)
           │  scripts/analysis/filter_de_content.py
           │  Remove BLANKET_EXCLUDE htypes:
           │    htype_001 Abschnitt · htype_004 Annotation
           │    htype_010 Eintrag   · htype_016 Index
           │    htype_017 Inhaltsverzeichnis · htype_018 Kapitel
           │    htype_028 Vorwort   · htype_029 Widmung
           │  Removed: 5,112,120 rows (27.5%)
           ▼
           │  Step 2 — language filter  (ADR-02)
           │  Keep dc:language ∈ {ger, gmh, nds, lat}
           │  No automatic langid secondary filter
           │  Removed: 4,244,786 rows (31.5% of remaining)
           ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data/out/s2/s2_meta_de_content.parquet      9,213,339 rows         │
│  Language breakdown:                                                 │
│    ger  8,716,820  (94.6%)                                          │
│    lat    493,712  ( 5.4%)                                          │
│    nds      1,523  (<0.1%)                                          │
│    gmh      1,284  (<0.1%)                                          │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  scripts/analysis/tokenize_de_titles.py
                               │  Model: FacebookAI/xlm-roberta-large
                               │  Preprocessing: normalize_historical()
                               │    NFC · long-s (ſ→s) · ligatures
                               │  Columns added: all_tokens, content_tokens, dates
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│  data/processed/de_titles_tokenized.parquet   9,213,339 rows        │
│  columns: obj_id · title · lang · dc_type · dates ·                │
│           all_tokens · content_tokens                               │
│  779.3 MB                                                           │
└──────┬───────────────────────────────┬───────────────────────────── ┘
       │                               │
       ▼                               ▼
  SR-10 analysis                  SR-11 analysis
  ─────────────                   ──────────────
  sr10_explore_token_             sr11_dctype_by_era.py
    distribution.py               → sr11_dctype_by_era_v2.csv
  → token-distribution_v2.json   → fig_dctype_by_era_v2.png
  → fig_token_distribution_v2.png
       │
       ▼
  sr10_analyse_title_lengths.py
  → title-length-analysis_v2.json
  → fig_title_lengths_v2.png
       │
       ▼
  sr10_render_title_viz.py
  → fig_title_lengths_v2.jsx
  → fig_title_lengths_v2_bw.html
```

---

## 3. Step-by-step

### 3.1 Ingestion: SQLite → Parquet

**Script:** `scripts/py/export_ddb.py` (via `scripts/sh/process_sqlite.sh`)
**Input:** `data/sqlite/s2.sqlite` — DDB Sector 2 dump in cortex JSON format
**Output:** `data/out/s2/s2_meta.parquet`, `data/out/s2/edm_*.nt`

Extracts ProvidedCHO metadata from each compressed JSON record and writes a flat Parquet file. The N-Triples files contain the full EDM graph for QLever ingestion.

```bash
bash scripts/sh/process_sqlite.sh data/sqlite/s2.sqlite
```

### 3.2 Content filtering: htype + language

**Script:** `scripts/analysis/filter_de_content.py`
**Input:** `data/out/s2/s2_meta.parquet`
**Output:** `data/out/s2/s2_meta_de_content.parquet`, `data/processed/filter_de_content_summary.csv`

Two sequential filters applied in order:

**Step 1 — htype filter (ADR-01).** Removes 8 BLANKET_EXCLUDE hierarchy types that do not contain standalone work titles (section headings, annotations, indexes, prefaces, etc.). Removes 5,112,120 rows (27.5%).

**Step 2 — language filter (ADR-02).** Keeps `dc:language ∈ {ger, gmh, nds, lat}`. No secondary automatic language identification filter — `dc:language` is the authoritative signal for GND linking pool assignment (see `notes/corpus-analysis/lang-detection.md` §5). Removes 4,244,786 rows (31.5% of remaining).

```bash
python scripts/analysis/filter_de_content.py
```

### 3.3 Tokenization

**Script:** `scripts/analysis/tokenize_de_titles.py`
**Input:** `data/out/s2/s2_meta_de_content.parquet`
**Output:** `data/processed/de_titles_tokenized.parquet`

Applies `normalize_historical()` preprocessing (NFC normalization, long-s → s, common ligatures), then tokenizes each title with the `xlm-roberta-large` SentencePiece BPE tokenizer. Computes:

- `all_tokens` — subword count excluding `<s>` and `</s>` special tokens
- `content_tokens` — subword count after removing pieces belonging to German stopwords
- `dates` — first 4 characters of `dc_issued[0]`, or `None`

Runtime: ~20 min for 9.2M rows on CPU (batch size 512).

```bash
python scripts/analysis/tokenize_de_titles.py
```

### 3.4 Distribution analysis (SR-10 / SR-11)

All three scripts accept `--data` and `--suffix` arguments to read from the new parquet without overwriting old outputs.

```bash
# Token distribution
python scripts/ner/sr10_explore_token_distribution.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output-dir notes/images --suffix _v2

# Title-length by era
python scripts/ner/sr10_analyse_title_lengths.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output-dir notes/images --suffix _v2

# Render JSX + HTML
python scripts/ner/sr10_render_title_viz.py \
    --json notes/images/title-length-analysis_v2.json \
    --output-dir notes/images --suffix _v2

# dc_type by era
python scripts/ner/sr11_dctype_by_era.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output data/processed/sr11_dctype_by_era_v2.csv \
    --fig notes/images/fig_dctype_by_era_v2.png
```

---

## 4. Key numbers

| Stage | Rows | Notes |
|-------|-----:|-------|
| Raw parquet (`s2_meta.parquet`) | 18,570,245 | All digitized DDB Sector 2 |
| After htype filter | 13,458,125 | −27.5% |
| After language filter (`s2_meta_de_content.parquet`) | 9,213,339 | −31.5% of remaining |
| Tokenized (`de_titles_tokenized.parquet`) | 9,213,339 | 779.3 MB |

Token distribution (xlm-roberta-large BPE):

| | median | p25 | p75 | p90 | p99 |
|---|---|---|---|---|---|
| `all_tokens` | 15 | 8 | 27 | 43 | 126 |
| `content_tokens` | 14 | 8 | 24 | 38 | 113 |

---

## 5. Comparison with old pkl

| | `DF_DE_TITLES_20240125b.pkl` | `de_titles_tokenized.parquet` |
|--|--|--|
| Source | `2024.01 MT-QA.ipynb` | `export_ddb.py` + filter + tokenize |
| N rows | 4,477,780 | 9,213,339 |
| Language filter | `dc:language=ger` AND `langid=ger` | `dc:language ∈ {ger, gmh, nds, lat}` |
| htype filter | `hierarchy_type=content` (notebook-defined) | ADR-01 BLANKET_EXCLUDE |
| Tokenizer | spaCy (model unspecified) | xlm-roberta-large SentencePiece BPE |
| Median `all_tokens` | 8 | 15 |
| p25 / p75 thresholds | 4 / 14 | 8 / 27 |
| Reproducible | No (notebook) | Yes (scripted) |

---

## 6. Related notes

- `notes/adr/htype-filtering-adr.md` — ADR-01
- `notes/adr/corpus-source-adr.md` — ADR-02
- `notes/adr/reprocessing-adr.md` — decision to reprocess from dump
- `notes/corpus-analysis/lang-detection.md` — language filter rationale
- `notes/corpus-analysis/tokenization.md` — tokenizer spec
- `notes/corpus-analysis/de-titles-regeneration-plan.md` — SR-10/SR-11 regeneration plan
- `notes/ner/sr10_de-titles-distribution.md` §7 — v2 distribution results

# GeMeA — Corpus Reprocessing: Impact on GND Linking and NER Pipeline

**Date:** 2026-04-14
**Related ADRs:** ADR-01/02/03 (`notes/adr/`), ADR-01 through ADR-08 (`notes/adr/gnd-linking-adr.md`)
**Related notes:** `notes/project/reprocessing-workflow.md`, `notes/ner/ner-bibliographic.md`

---

## 1. Purpose

This note records how the corpus source migration — retiring `DF_DE_TITLES_20240125b.pkl` in favour of `s2_meta_de_content.parquet` (ADR-03) — propagates through the two downstream subsystems that consume it: the GND Werk linking pipeline (`link_gnd_works.py`) and the NER pipeline. It does not repeat the corpus migration rationale (see `notes/adr/reprocessing-adr.md`); it focuses on the consequent design decisions that are already in effect or that must be revisited.

---

## 2. What changed in the corpus

| Dimension | Old (pkl) | New (parquet) |
|-----------|-----------|---------------|
| N rows | 4,477,780 | 9,213,339 |
| Language filter | `dc:language=ger` AND `langid=ger` | `dc:language ∈ {ger, gmh, nds, lat}` |
| htype filter | `hierarchy_type=content` | ADR-01 BLANKET_EXCLUDE (8 types) |
| Tokenizer | spaCy (model unspecified) | xlm-roberta-large SentencePiece BPE |
| Median `all_tokens` | 8 | 15 |
| p25 / p75 | 4 / 14 | 8 / 27 |
| Latin records | 0 | 493,712 (5.4%) |
| Middle High German | 0 | 1,284 (`gmh`) |
| Low German | ~890 (10.9% of `nds` passed langid) | 1,523 (`nds`) |
| Reproducible | No (notebook) | Yes (scripted pipeline) |

The two major additions are (a) the removal of the `langid` secondary filter, which recovers ~1.1M records that `dc:language` correctly marks as German-family but which fasttext misclassified, and (b) the addition of ~494K Latin-language records representing the pre-1800 bilingual scholarly and theological corpus.

---

## 3. Impact on GND Werk linking

The GND Werk linking pipeline (`link_gnd_works.py`) is not affected by the internal structure of these ADRs — it was designed against the DDB ProvidedCHO records in `s2_meta_de_content.parquet` from the start. The ADRs below were written in March 2026 against the new parquet, not against the pkl. The impact is instead that the **scale and composition** of the input to the linking pipeline has changed.

### 3.1 Scale and deduplication (ADR-06)

ADR-06 deduplicates on `(extracted_title, author_gnd_uri)` pairs before issuing SPARQL queries. The corpus doubles from 4.47M to 9.21M rows, but the deduplication ratio also increases: Latin and pre-modern German titles are more formulaic (especially in the scholarly and theological register), so the unique-pair fraction may be lower than in the modern German subset. The estimated 5–10M unique pairs in ADR-06 should be re-profiled once `link_gnd_works.py` processes the full parquet.

### 3.2 Latin-language records (ADR-03 corpus consequence)

Latin titles were excluded from the pkl. They are now included. The GND linking ADRs are already compatible:

- **ADR-03 (Work class scope):** `gndo:Work`, `gndo:MusicalWork`, `gndo:Manuscript` covers Latin Werk records — GND has dedicated Latin-language entries for theological, legal, and scholarly works.
- **ADR-04 (Author predicates):** `gndo:author`, `gndo:firstAuthor`, `gndo:poet`, `gndo:composer` — predicates apply regardless of title language.
- **ADR-02 (FILTER pattern):** Pattern C uses `LCASE(STR(?prefLabel)) = "{normalized_title}"`. GND `preferredNameForTheWork` for Latin works uses the same plain-string format as German works; the FILTER approach is language-agnostic.
- **ADR-08 (GENERIC_TITLE_WORDS):** `GENERIC_TITLE_WORDS = {"werke"}` is German. Latin equivalents (`opera`, `tractatus`, `epistolae`) were not tested against the DNB endpoint. A supplementary query analogous to `scripts/check_generic_title_words.py` should be run for the 10–15 most common Latin title words in the corpus before running `link_gnd_works.py` against the full parquet.

**Action required:** Profile Latin generic title word collision before the full linking run.

### 3.3 GMH and NDS records

Middle High German (1,284 rows) and Low German (1,523 rows) records are now included. GND covers pre-modern German works in these registers. No ADR changes are required, but recall will be limited: GND `preferredNameForTheWork` is typically recorded in a normalized modern form for older works, while DDB titles may retain historical orthography. The `normalize_historical()` preprocessing step in `tokenize_de_titles.py` (long-s, ligatures, NFC) does not close this gap. Fuzzy matching (`skos:closeMatch`, Levenshtein ≤ 2, ADR-05) is the correct fallback for these records.

### 3.4 ISBD field rating re-run (SR-01 dependency)

`data/processed/sr01_isbd_field_ratings.csv` was computed against the pkl (4.47M rows). The silver label pipeline (`rate_isbd_fields.py`, `build_silver_spans.py`) consumes this file. It must be re-run against `s2_meta_de_content.parquet` (9.21M rows) before the silver pipeline can proceed. This is the next pending step in Phase 0a.

**Action required:** Re-run `scripts/analysis/rate_isbd_fields.py` against `data/out/s2/s2_meta_de_content.parquet`.

---

## 4. Impact on the NER pipeline

### 4.1 Corpus used in SR-01 through SR-12

All study rounds SR-01 through SR-12 were run against the pkl (4.47M rows, ger-only, langid-filtered). The corpus reference in `ner-bibliographic.md` (`DF_DE_TITLES 4.47M`) is the pkl. The new parquet doubles the corpus and adds Latin and pre-modern German. The key implications:

| SR | Impact |
|----|--------|
| SR-01 ISBD signal coverage | Numbers (20.2% subtitle, 0.8% SoR, etc.) are pkl-derived. Must be re-run against parquet. Latin titles carry different ISBD patterns; `. -` and ` :` rates may differ. |
| SR-03 Silver label FP rate | Sample was pkl-derived. Latin and pre-modern German records will have different FP profiles, especially for `f_person` (name-before-title) and `f_year`. |
| SR-06 Historical and Latin title scope | SR-06 resolved that Latin is out of scope for the gold set annotation (Doccano: pre-1700 first, no Latin). This decision stands: Latin NER is deferred. The parquet expansion does not reopen SR-06. |
| SR-08 Gold set | 395 records sampled from pkl. Pre-1750 stratum excludes Latin. The sample is unaffected by the parquet migration; Doccano annotation can proceed as planned. |
| SR-09 NuNER Zero | Evaluated 2026-03-27, F1=0.000 on all labels, all prompt sets. Resolved; confirmed path is LLM annotation + fine-tune xlm-roberta-base. Not affected by parquet migration. |
| SR-10 Token distribution | V2 results (parquet, xlm-roberta BPE) are in §7 of `sr10_de-titles-distribution.md`. New thresholds: ≤8 / 9–27 / >27. SR-10 is resolved against the new parquet. |
| SR-11 LLM labeling strategy | Target ~4–5K tier-0, pre-1750 records. These will be drawn from the new parquet; the era filter is parquet-compatible. Latin records are excluded (SR-06 decision). |
| SR-12 Field-level weighting | Future — blocked on SR-03 extension, SR-04, SR-08. Not yet affected. |

### 4.2 Token threshold recalibration (SR-10 consequence)

The old pkl used spaCy tokens; the new parquet uses xlm-roberta-large BPE. BPE fragments compound German words into more pieces (median 8 → 15). Downstream thresholds that gate NER application (short ≤4 / medium 5–14 / long >14) must be recalibrated:

| Band | Old (pkl, spaCy) | New (parquet, BPE) |
|------|------------------|--------------------|
| Short | ≤ 4 | ≤ 8 (p25) |
| Medium | 5–14 | 9–27 (p25–p75) |
| Long | > 14 | > 27 (p75) |

These new thresholds apply to SR-08 gold set stratification and to the short-title filter in `link_gnd_works.py` (records with very short titles are poor SPARQL query candidates regardless of ISBD markers). See `notes/ner/sr10_title-length-thresholds.md` for the full derivation.

### 4.3 Latin NER scope (SR-06 decision preserved)

SR-06 resolved that the gold set annotation focuses on German-family titles only; Latin is deferred. This decision is compatible with the parquet expansion: Latin records are in the corpus for GND linking purposes, but the NER model (xlm-roberta fine-tune) will be trained on German-family data only. Inference on Latin records will use the ISBD parser as primary extractor and NER as an untuned fallback — acceptable given that Latin titles are more formulaic and better covered by the ISBD structural parser.

---

## 5. Open actions

| Action | Blocks | Priority |
|--------|--------|----------|
| Re-run `rate_isbd_fields.py` against `s2_meta_de_content.parquet` | SR-01 v2, silver pipeline, `build_silver_spans.py` | High — Phase 0a |
| Profile Latin generic title words against DNB endpoint | `link_gnd_works.py` full run | Medium — before linking run |
| Update `sr10_title-length-thresholds.md` with v2 p25/p75 | SR-08 stratification, `link_gnd_works.py` short-title filter | Medium |
| Continue SR-08 Doccano annotation (395 records, pre-1700 first) | SR-09 xlm-roberta fine-tune | High — in progress |
| Proceed with SR-11 LLM labeling (~4–5K pre-1750 records from parquet) | Training data | Active |

---

## 6. Related notes

- `notes/adr/reprocessing-adr.md` — ADR-03 (corpus migration rationale)
- `notes/adr/corpus-source-adr.md` — ADR-02 (pkl → parquet)
- `notes/adr/htype-filtering-adr.md` — ADR-01 (htype filter)
- `notes/adr/gnd-linking-adr.md` — ADR-01 through ADR-08 (GND Werk linking design)
- `notes/ner/ner-bibliographic.md` — SR-01 through SR-12 (NER pipeline)
- `notes/project/reprocessing-workflow.md` — end-to-end pipeline diagram
- `notes/corpus-analysis/lang-detection.md` §5.5 — Latin inclusion rationale

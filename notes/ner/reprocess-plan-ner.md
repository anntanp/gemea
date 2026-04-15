# GeMeA — NER Pipeline Reprocessing: Status and Open Issues

**Date:** 2026-04-14 — 2026-04-15
**Context:** Corpus migrated from `DF_DE_TITLES_20240125b.pkl` (4.47M rows) to `de_titles_tokenized.parquet` (9.21M rows, `dc:type`/`edm:hasType` corrected). Reprocessing complete. pkl-era files archived to `data/before-parquet/`; `_v2` files renamed to canonical names.

---

## 1. Done

| Step | Script / File | Output | Status |
|------|--------------|--------|--------|
| Filter + Latin | `filter_de_content.py` | `s2_meta_de_content.parquet` (9.21M) | ✅ |
| Tokenize | `tokenize_de_titles.py` | `de_titles_tokenized.parquet` (779 MB) | ✅ |
| SR-10 | `sr10_explore_token_distribution.py` + `sr10_analyse_title_lengths.py` + `sr10_render_title_viz.py` | `fig_token_distribution.png`, `fig_title_lengths.png`, `title-length-analysis.json`, etc. | ✅ |
| SR-11 dctype | `sr11_dctype_by_era.py` | `sr11_dctype_by_era.csv` | ✅ |
| SR-01 | `sr01_rate_isbd_fields.py` — added `load_data()`, fixed ROOT | `sr01_isbd_field_ratings.csv` (9.21M rows) | ✅ |
| SR-08 cell sizes | `sr08_corpus_cell_sizes.py` — refactored with argparse + parquet | `sr08_corpus_cell_sizes.csv` | ✅ |
| SR-11 sample | `sr11_sample_validation.py` — fixed bug (args.source), dc_type corrected in parquet | `sr11_prompt_validation_manual.jsonl` (50 records) | ✅ |
| Archive | pkl-era outputs → `data/before-parquet/`; `_v2` files → canonical names | — | ✅ |
| Notes | [notes/project/reprocessing-workflow.md](https://github.com/anntanp/gemea/blob/main/notes/project/reprocessing-workflow.md), [notes/adr/reprocessing-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/reprocessing-adr.md), [notes/adr/corpus-source-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/corpus-source-adr.md), [notes/reprocess-adr.md](https://github.com/anntanp/gemea/blob/main/notes/reprocess-adr.md), [notes/project/reprocess-before-after.md](https://github.com/anntanp/gemea/blob/main/notes/project/reprocess-before-after.md) | — | ✅ |
| [notes/ner/ner-bibliographic.md](https://github.com/anntanp/gemea/blob/main/notes/ner/ner-bibliographic.md) | SR-01 §2.1 + SR-11 §2.11 updated | — | ✅ |

---

## 2. Open issues

### 2.1 `sr11_sample_validation.py` — dc_type field mismatch ✅ RESOLVED

**Problem.** The pkl's `dc_type` carried genre values (`Leichenpredigt`, `Einblattdruck`, `Monografie`). The initial parquet export captured only media format (`TEXT`, `IMAGE`).

**Resolution.** Parquet regenerated (2026-04-15) with correct `dc:type`/`edm:hasType` genre values. Script bug fixed (line 171: `args.source` removed from `load_pool()` call). Run produced 50 records: Monografie 17, Einblattdruck 15, Leichenpredigt 14, other 4. All pre-1750.

### 2.2 `reprocess-before-after.md` §5.1 — incorrect htype attribution ✅

**Problem.** §5.1 (Hypothesis 3) referenced `htype_019 Leichenpredigt`. The correct mapping is `htype_019 = Karte` (map). Leichenpredigt is not a htype code at all.

**Fix:** rewrote Hypothesis 3 to remove the htype_019 reference; now describes ADR-01 BLANKET_EXCLUDE vs. `hierarchy_type=content` in terms of retained full-text types (Einblattdrucke, Leichenpredigten) without using incorrect htype codes.

### 2.3 `sr08_check_agent_coverage.py` — no parquet support

**Problem.** The script reads `dc_creator` / `dc_contributor` from the pkl. These columns are in `s2_meta_de_content.parquet` (they were in `s2_meta.parquet` and passed through the filter) but NOT in `de_titles_tokenized.parquet`. The script needs `--data` pointing to `s2_meta_de_content.parquet`, not the tokenized parquet.

**Priority:** Low — this is descriptive stats for the paper, not blocking anything.

### 2.4 `sr01_rate_isbd_fields.py` ROOT fix

**Status:** Fixed (`parent.parent.parent`). Confirmed working.

### 2.5 Notes not yet updated ✅

[notes/ner/ner-bibliographic.md](https://github.com/anntanp/gemea/blob/main/notes/ner/ner-bibliographic.md) SR-11 §2.11 — updated with v2 run status and dc_type sample distribution.

---

## 3. Remaining open items (low priority)

1. **`sr08_check_agent_coverage.py`** — needs `--data` pointing to `s2_meta_de_content.parquet` (has `dc_creator`/`dc_contributor`). Low priority, descriptive stats only.
2. **`sr11_labeling-strategy.md`** — may reference old pkl paths; not checked.

---

## 4. Files modified so far (this session)

| File | What changed |
|------|-------------|
| [scripts/analysis/filter_de_content.py](https://github.com/anntanp/gemea/blob/main/scripts/analysis/filter_de_content.py) | `DE_LANGS` += `lat` |
| [scripts/analysis/tokenize_de_titles.py](https://github.com/anntanp/gemea/blob/main/scripts/analysis/tokenize_de_titles.py) | New script |
| [scripts/ner/sr10_explore_token_distribution.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr10_explore_token_distribution.py) | `load_data()` + `--suffix` arg |
| [scripts/ner/sr10_analyse_title_lengths.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr10_analyse_title_lengths.py) | `load_data()` + `--suffix` arg |
| [scripts/ner/sr10_render_title_viz.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr10_render_title_viz.py) | `--suffix` arg |
| [scripts/ner/sr11_dctype_by_era.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr11_dctype_by_era.py) | `load_data()` |
| [scripts/ner/sr01_rate_isbd_fields.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr01_rate_isbd_fields.py) | `load_data()`, ROOT fix |
| [scripts/ner/sr08_corpus_cell_sizes.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr08_corpus_cell_sizes.py) | Full rewrite with argparse + `load_data()` |
| [scripts/ner/sr11_sample_validation.py](https://github.com/anntanp/gemea/blob/main/scripts/ner/sr11_sample_validation.py) | `load_corpus()` parquet support, ROOT fix — reverted all workaround code |
| [notes/ner/ner-bibliographic.md](https://github.com/anntanp/gemea/blob/main/notes/ner/ner-bibliographic.md) | SR-01 §2.1 v2 numbers added |
| [notes/corpus-analysis/lang-detection.md](https://github.com/anntanp/gemea/blob/main/notes/corpus-analysis/lang-detection.md) | §5.5 Latin justification added |
| [notes/project/reprocessing-workflow.md](https://github.com/anntanp/gemea/blob/main/notes/project/reprocessing-workflow.md) | New |
| [notes/adr/reprocessing-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/reprocessing-adr.md) | New (ADR-03) |
| [notes/adr/corpus-source-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/corpus-source-adr.md) | New (ADR-02) |
| [notes/reprocess-adr.md](https://github.com/anntanp/gemea/blob/main/notes/reprocess-adr.md) | New (impact on GND linking + NER) |
| [notes/project/reprocess-before-after.md](https://github.com/anntanp/gemea/blob/main/notes/project/reprocess-before-after.md) | New |
| [notes/ner/reprocess-plan-ner.md](https://github.com/anntanp/gemea/blob/main/notes/ner/reprocess-plan-ner.md) | This file |

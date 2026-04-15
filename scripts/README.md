# scripts/

Standalone operational scripts for GeMeA. Each script is self-contained with a header comment.

## Conventions

Every script must begin with:
```
# Purpose:      one-line description
# Usage:        how to invoke
# Inputs:       what it reads
# Outputs:      what it writes
# Dependencies: external tools / packages required
# Assumptions:  preconditions
```

Scripts use `argparse` for CLI arguments. Place all scripts here; document them below when added.

## Index

### `sh/` — shell scripts (orchestration, data movement)

| Script | Purpose |
|--------|---------|
| `sh/download_data.sh` | Fetch mocho-normalized RDF from public data dump |
| `sh/setup_gnd_fuseki.sh` | (deprecated) Start local Fuseki container and load GND authority files |
| `sh/setup_gnd_qlever.sh` | Convert GND JSON-LD to N-Triples, build QLever index, start SPARQL server |

### `py/` — general Python scripts

| Script | Purpose |
|--------|---------|
| `py/sr10_explore_token_distribution.py` | SR-10: plot raw token-count distribution with percentile markers; outputs `notes/images/fig_token_distribution.png` |
| `py/sr10_analyse_title_lengths.py` | SR-10: plot title-length distribution per year bucket; outputs `notes/images/fig_title_lengths.png` |
| `py/sr10_render_title_viz.py` | SR-10: generate per-theme standalone HTML files from fig_title_lengths.jsx |

### `ner/` — NER study-round scripts (SR-01 – SR-11)

| Script | Purpose |
|--------|---------|
| `ner/sr01_check_isbd_titles.py` | SR-01: analyse ISBD punctuation patterns in DF_DE_TITLES; reports per-pattern counts and sample titles |
| `ner/sr01_rate_isbd_fields.py` | SR-01: rate all 4.47M DF_DE_TITLES records for ISBD field presence; assigns silver_tier; optionally writes per-pattern examples with DDB links |
| `ner/sr03_validate_heuristic_fields.py` | SR-03: sample 200 heuristic-tier records from sr01_isbd_field_ratings.csv for manual false-positive review; writes a review sheet CSV |
| `ner/sr03_fp_review.py` | SR-03: apply automated regex rules + per-row manual overrides to classify each heuristic flag as TP or FP |
| `ner/sr03_validate_fp_review.py` | SR-03: validate FP review output — checks row count, field name validity, and referential integrity |
| `ner/sr03_extract_fp_examples.py` | SR-03: extract DDB links and field flags from sr03_heuristic_validation_sample.csv |
| `ner/sr04_validate_translator_disambiguation.py` | SR-04: sample 100 heuristic `f_person` records and classify SoR text as TRANSLATOR / EDITOR / PERSON |
| `ner/sr04_evaluate_translator_heuristic.py` | SR-04: evaluate keyword heuristic against manual `true_class` annotations; prints precision/recall/F1, confusion matrix, FN detail |
| `ner/sr05_validate_trailing_period.py` | SR-05: sample 200 titles ending with `.`; applies heuristic classifier (ISBD_CLOSE / ABBREV / ORDINAL / NATURAL / NOISE) |
| `ner/sr05_trailing_period_review.py` | SR-05: annotate `sr05_trailing_period_sample.csv` with refined `true_class` and `notes`; prints FP rate summary |
| `ner/sr08_sample_gold.py` | SR-08: draw ~500-record stratified NER gold sample by era × silver_tier × dc_type |
| `ner/sr08_prefill_spans.py` | SR-08: pre-fill TITLE / OTHER_TITLE / PERSON spans for tier-1 and tier-2 records using ISBD rules |
| `ner/sr08_verify_spans.py` | SR-08: verify character offset integrity of pre-filled spans; prints spot-check records |
| `ner/sr08_gold_dctype_breakdown.py` | SR-08: dc_type × era breakdown of the gold sample; writes `data/processed/sr08_gold_dctype_breakdown.csv` |
| `ner/sr09_eval_nuner_tier2.py` | SR-09: NuNER tier-2 sanity check — compare to ISBD silver spans, report P/R/F1 per label |
| `ner/sr11_dctype_by_era.py` | SR-11: count and rank dc_type values per era stratum; writes `data/processed/sr11_dctype_by_era.csv` |
| `ner/sr11_sample_validation.py` | SR-11 T11.1a: sample 50 pre-1750 tier-0 records for manual prompt validation |
| `ner/sr11_annotate.py` | SR-11 T11.1b: interactive span annotation helper; resolves character offsets, writes back in place |

### `analysis/` — DDB corpus analysis scripts

| Script | Purpose |
|--------|---------|
| `analysis/count_hierarchy_types.py` | Count primary/secondary objects by hierarchy_type; outputs `data/processed/hierarchy_type_counts.csv` and `notes/images/hierarchy_type_counts.png` |
| `analysis/validate_htype_title_quality.py` | Compute fraction of generic/structural titles per htype; outputs `data/processed/htype_title_quality.csv` and `notes/images/htype_title_quality.png` |
| `analysis/explore_top_titles.py` | Print top-N most frequent titles per hierarchy_type to inform pattern blocklists |
| `analysis/sample_work_titles.py` | Sample mid-frequency titles (ranks 31–150) for htype_001 and htype_018 to evaluate content quality |
| `analysis/sample_htype_titles.py` | Random sample of titles for specified htypes with DDB item links |
| `analysis/filter_content_titles.py` | Classify all titles into work_title / section_label / physical_label (Option C hybrid); outputs `data/processed/title_class_counts.csv`, `title_class_sample.csv`, `notes/images/title_class_breakdown.png` |
| `analysis/count_lang.py` | Count objects by `lang` code (explodes multi-value entries); outputs `data/processed/lang_counts.csv` and `notes/images/lang_counts.png` |
| `analysis/lang_by_year.py` | Count objects by language × year/decade (year from `dc_issued`); outputs `data/processed/lang_by_year.csv` and `notes/images/lang_by_year.png` |
| `analysis/wordcloud_book.py` | Word cloud of "book" in each DDB language, sized by object count; outputs `notes/images/wordcloud_book.png` |
| `analysis/detect_lang_titles.py` | Detect title language with fasttext lid.176, compare against dc:language annotation; outputs `data/processed/lang_detect_titles.csv` and `lang_detect_summary.csv` |
| `analysis/filter_de_content.py` | Filter s2_meta.parquet to German + Latin content titles (removes BLANKET_EXCLUDE htypes + non-ger/gmh/nds/lat lang); outputs `data/out/s2/s2_meta_de_content.parquet` and `data/processed/filter_de_content_summary.csv` |
| `analysis/tokenize_de_titles.py` | Tokenize titles in s2_meta_de_content.parquet with xlm-roberta-large; computes `all_tokens` and `content_tokens` per title; outputs `data/processed/de_titles_tokenized.parquet` |

### `utils/` — shared utilities

| Script | Purpose |
|--------|---------|
| `utils/jsonld_to_nt.py` | Convert a JSON-LD file (.jsonld or .jsonld.gz) to N-Triples using rdflib |
| `utils/check_generic_title_words.py` | Query DNB SPARQL endpoint to count GND Work records per GENERIC_TITLE_WORD; validates high-collision words |
| `utils/check_note_urls.py` | Check URLs referenced in notes/ for broken links |
| `utils/fetch-ids-by-sector.py` | Fetch DDB object IDs by sector from the OAI-PMH endpoint |
| `utils/find_missing_ids.py` | Find IDs present in one data source but missing from another |

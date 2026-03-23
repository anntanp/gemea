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

| Script | Purpose |
|--------|---------|
| `download_data.sh` | Fetch mocho-normalized RDF from public data dump |
| `setup_gnd_fuseki.sh` | (deprecated) Start local Fuseki container and load GND authority files |
| `setup_gnd_qlever.sh` | Convert GND JSON-LD to N-Triples, build QLever index, start SPARQL server |
| `jsonld_to_nt.py` | Convert a JSON-LD file (.jsonld or .jsonld.gz) to N-Triples using rdflib |
| `check_generic_title_words.py` | Query DNB SPARQL endpoint to count GND Work records per GENERIC_TITLE_WORD; validates which words are high-collision and should be excluded from distinctive token selection |
| `check_isbd_titles.py` | Analyse ISBD punctuation patterns in DF_DE_TITLES; reports per-pattern counts and sample titles |
| `rate_isbd_fields.py` | Rate all 4.47M DF_DE_TITLES records for the presence of bibliographic fields (TITLE, PERSON, PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME) using ISBD rules; assigns silver_tier for NER training data selection; optionally writes per-pattern examples with DDB links |
| `validate_heuristic_fields.py` | Sample 200 heuristic-tier records from isbd_field_ratings.csv for manual false-positive review; writes a review sheet CSV with DDB links and blank fp_fields / notes columns |
| `explore_token_distribution.py` | Plot raw token-count distribution of `all_tokens` and `content_tokens` with percentile markers (p25/p50/p75/p90); used to identify data-driven short/medium/long thresholds; outputs `notes/images/fig_token_distribution.png` and `output/token-distribution.json` |
| `analyse_title_lengths.py` | Plot title-length distribution (short/medium/long) per year bucket using `all_tokens` and `content_tokens`; year from `dates` column with title-string fallback; outputs `notes/images/fig_title_lengths.png` and `output/title-length-analysis.json` |
| `validate_translator_disambiguation.py` | SR-04: sample 100 heuristic `f_person` records and apply translator/editor keyword heuristic to classify SoR text as TRANSLATOR / EDITOR / PERSON; writes `data/processed/translator_validation_sample.csv` for manual precision review |
| `evaluate_translator_heuristic.py` | SR-04: evaluate keyword heuristic against manual `true_class` annotations in `translator_validation_sample.csv`; prints precision/recall/F1 for TRANSLATOR and EDITOR, confusion matrix, and false-negative detail |
| `sr03_fp_review.py` | SR-03 false-positive review: reads `data/processed/heuristic_validation_sample.csv`, applies automated regex rules + per-row manual overrides to classify each active heuristic flag (f_year, f_other_title, f_person, f_person_compound, f_parallel, f_edition, f_publisher, f_series, f_volume) as TP or FP, and writes results back to `fp_fields` and `notes` columns |
| `validate_fp_review.py` | Validate the FP review output: checks row count, field name validity, and that fp_fields only references columns actually set to 1 |

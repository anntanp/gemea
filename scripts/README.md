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
| `sr01_check_isbd_titles.py` | SR-01: analyse ISBD punctuation patterns in DF_DE_TITLES; reports per-pattern counts and sample titles |
| `sr01_rate_isbd_fields.py` | SR-01: rate all 4.47M DF_DE_TITLES records for the presence of bibliographic fields using ISBD rules; assigns silver_tier; optionally writes per-pattern examples with DDB links |
| `sr03_validate_heuristic_fields.py` | SR-03: sample 200 heuristic-tier records from sr01_isbd_field_ratings.csv for manual false-positive review; writes a review sheet CSV |
| `sr03_fp_review.py` | SR-03: apply automated regex rules + per-row manual overrides to classify each heuristic flag as TP or FP; writes results to fp_fields and notes columns |
| `sr03_validate_fp_review.py` | SR-03: validate FP review output — checks row count, field name validity, and referential integrity |
| `sr03_extract_fp_examples.py` | SR-03: extract DDB links and field flags from sr03_heuristic_validation_sample.csv |
| `sr04_validate_translator_disambiguation.py` | SR-04: sample 100 heuristic `f_person` records and classify SoR text as TRANSLATOR / EDITOR / PERSON; writes `data/processed/sr04_translator_validation_sample.csv` |
| `sr04_evaluate_translator_heuristic.py` | SR-04: evaluate keyword heuristic against manual `true_class` annotations; prints precision/recall/F1, confusion matrix, and false-negative detail |
| `sr10_explore_token_distribution.py` | SR-10: plot raw token-count distribution with percentile markers; outputs `notes/images/fig_token_distribution.png` |
| `sr10_analyse_title_lengths.py` | SR-10: plot title-length distribution per year bucket; outputs `notes/images/fig_title_lengths.png` |
| `sr11_sample_validation.py` | SR-11 T11.1a: sample 50 pre-1750 tier-0 records for manual prompt validation; stratified by dc_type; excludes SR-08 gold; outputs `data/annotation/sr11_prompt_validation_manual.jsonl` |
| `sr11_annotate.py` | SR-11 T11.1b: interactive span annotation helper; loads `sr11_prompt_validation_manual.jsonl`, prompts for Inline Bracketed input, resolves character offsets, writes back in place |
| `sr05_validate_trailing_period.py` | SR-05: sample 200 titles ending with `.` from DF_DE_TITLES; applies a heuristic classifier (ISBD_CLOSE / ABBREV / ORDINAL / NATURAL / NOISE) and writes `data/processed/sr05_trailing_period_sample.csv` |
| `sr05_trailing_period_review.py` | SR-05: annotate `sr05_trailing_period_sample.csv` with refined `true_class` and `notes`; prints FP rate summary |
| `sr08_sample_gold.py` | SR-08: draw ~500-record stratified NER gold sample by era × silver_tier × dc_type; oversample Leichenpredigt and Einblattdruck; writes `data/annotation/sr08_gold_sample.csv` |
| `sr08_prefill_spans.py` | SR-08: pre-fill TITLE / OTHER_TITLE / PERSON spans for tier-1 and tier-2 records using ISBD rules; marks pre-1700 and tier-0 records as manual; writes `sr08_gold_prefilled.jsonl` and `sr08_manual_queue.csv` |
| `sr08_verify_spans.py` | SR-08: verify character offset integrity of pre-filled spans; prints sample records for manual spot-check |
| `sr11_dctype_by_era.py` | SR-11: count and rank dc_type values per era stratum (pre-1700 / 1700-1800 / 19th-c / modern / unknown); writes `data/processed/sr11_dctype_by_era.csv` |
| `sr09_eval_nuner_tier2.py` | SR-09: NuNER tier-2 sanity check — run NuNER on tier-2 pre-filled records, compare to ISBD-derived silver spans, report exact-span-match P/R/F1 per label; writes `data/processed/sr09_nuner_tier2_results.csv` |
| `sr08_gold_dctype_breakdown.py` | SR-08: dc\_type × era breakdown of the gold sample (`sr08_gold_sample.csv`); counts LP and EB (contains-match) per era; writes `data/processed/sr08_gold_dctype_breakdown.csv` |

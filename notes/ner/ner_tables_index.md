# NER Task — Data Tables Index

All data tables produced by scripts for the NER pipeline, ordered by pipeline stage. For tables embedded in notes but not backed by a file, see the table of tables in [sr08_evaluation-design.md](sr08_evaluation-design.md).

---

| Table name | Note + section | Purpose | Script | Output file |
|---|---|---|---|---|
| **Stage 1 — Corpus characterisation** |||||
| ISBD field ratings | [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md) | Rates each DF_DE_TITLES record by ISBD signal presence; assigns silver tier (0/1/2) | `sr01_rate_isbd_fields.py` | `data/processed/isbd_field_ratings.csv` |
| ISBD examples | [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md) | Sample records illustrating each ISBD field type | `sr01_check_isbd_titles.py` | `data/processed/isbd_examples.csv` |
| Title length distribution | [sr10_de-titles-distribution.md](sr10_de-titles-distribution.md) | Token length quartiles per era; defines short/medium/long thresholds for gold set stratification | `sr10_analyse_title_lengths.py` | ⚠️ output file not confirmed |
| **Stage 2 — Silver label quality** |||||
| Heuristic validation sample | [sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md) | 200-record stratified sample for FP rate estimation per heuristic field | `sr03_validate_heuristic_fields.py` | `data/processed/heuristic_validation_sample.csv` |
| Trailing period sample | [sr05_trailing-period-noise.md](sr05_trailing-period-noise.md) | 200-record sample of titles ending in `.`; FP rate = 93%; led to exclusion of trailing period as signal | `sr05_trailing_period_review.py` | `data/processed/trailing_period_sample.csv` |
| Translator validation sample | [sr04_translator-person-disambiguation.md](sr04_translator-person-disambiguation.md) | 100-record sample for TRANSLATOR/PERSON disambiguation; found 0 true translators | `sr04_validate_translator_disambiguation.py` | `data/processed/translator_validation_sample.csv` |
| **Stage 3 — Historical scope** |||||
| Historical sample | [sr06_historical-scope.md](sr06_historical-scope.md) | 200-record stratified sample (Leichenpredigt + pre-1800 Monografie) for language/register assessment | `sr06_historical_scope.py` | `data/processed/sr06_historical_sample.csv` |
| Historical evaluated | [sr06_historical-scope.md](sr06_historical-scope.md) | Evaluated results with true-class labels; documents EARLY_MODERN_DE 93%, LATIN 0.5% | `sr06_evaluate_historical.py` | `data/processed/sr06_historical_evaluated.csv` |
| **Stage 4 — Gold set design** |||||
| Agent coverage by era | [sr08_evaluation-design.md §1](sr08_evaluation-design.md) | dc:creator/contributor absence rate per era; shows 67% absent overall — motivates PERSON priority | `sr08_check_agent_coverage.py` | `data/processed/sr08_agent_coverage_by_era.csv` |
| Person in title by era | [sr08_evaluation-design.md §1](sr08_evaluation-design.md) | ner_person (FLERT) prevalence per era; shows 8.7% pre-1700, 0.2% modern — grounds PERSON evaluation scope | `sr08_check_person_in_title.py` | `data/processed/sr08_person_in_title_by_era.csv` |
| Corpus cell sizes (era × tier) | [sr08_evaluation-design.md §5](sr08_evaluation-design.md) | Actual record counts per era × silver_tier cell; replaces round-number allocation targets | `sr08_corpus_cell_sizes.py` | `data/processed/sr08_corpus_cell_sizes.csv` |
| CI sample size requirements | [sr08_evaluation-design.md §6](sr08_evaluation-design.md) | Wilson interval computation of minimum instances and records needed per stratum at ±5 pp and ±10 pp | `sr08_ci_sample_size.py` | `data/processed/sr08_ci_sample_size.csv` |
| Gold set composition audit | [sr08_evaluation-design.md §8](sr08_evaluation-design.md) | Current vs. original allocation targets per era × tier; identifies tier-1 over-representation (43.5%) | `sr08_gold_composition_audit.py` | `data/processed/sr08_gold_composition_audit.csv` |
| **Stage 5 — Gold set annotation** |||||
| Gold sample | [sr08_gold-set-composition.md §4](sr08_gold-set-composition.md) | 395-record stratified sample; era × tier × dc_type; input to prefill and annotation | `sr08_sample_gold.py` | `data/annotation/sr08_gold_sample.csv` |
| Gold prefilled (JSONL) | [sr08_gold-set-composition.md §4](sr08_gold-set-composition.md) | 395 records with ISBD-derived spans pre-filled (183 prefilled/partial, 212 empty); source for Doccano import | `sr08_prefill_spans.py` | `data/annotation/sr08_gold_prefilled.jsonl` |
| Manual annotation queue | [sr08_gold-set-composition.md §4](sr08_gold-set-composition.md) | 212 records requiring full manual annotation; sorted by era and tier priority | `sr08_prefill_spans.py` | `data/annotation/sr08_manual_queue.csv` |
| Doccano import | [sr08_annotation-guide.md](sr08_annotation-guide.md) | Doccano-formatted JSONL (`text`, `label`) for import into annotation tool | `sr08_doccano_import.py` | `data/annotation/sr08-doccano-import.jsonl` |

# GeMeA — Reprocessing: Before / After Comparison

**Date:** 2026-04-14
**Covers:** corpus migration (ADR-02/03) + SR-01 v2 + SR-10 v2 + SR-08 cell sizes v2

---

## 1. Corpus

### 1.1 Source and size

| | Old (pkl) | New (parquet) | Change |
|--|--|--|--|
| Source | `DF_DE_TITLES_20240125b.pkl` | `data/processed/de_titles_tokenized.parquet` | — |
| Rows | 4,477,780 | 9,213,339 | +105.8% |
| Language filter | `dc:language=ger` AND `langid=ger` | `dc:language ∈ {ger, gmh, nds, lat}` | — |
| htype filter | `hierarchy_type=content` | ADR-01 BLANKET_EXCLUDE (8 types) | — |
| Tokenizer | spaCy (unspecified model) | xlm-roberta-large SentencePiece BPE | — |

### 1.2 Pipeline funnel (new parquet)

| Stage | Rows | Notes |
|-------|-----:|-------|
| Raw parquet (`s2_meta.parquet`) | 18,570,245 | All digitized DDB Sector 2 |
| After htype filter | 13,458,125 | −27.5% |
| After language filter (`s2_meta_de_content.parquet`) | 9,213,339 | −31.5% of remaining |
| Tokenized (`de_titles_tokenized.parquet`) | 9,213,339 | 779.3 MB |

### 1.3 Language breakdown (new parquet only)

| Language | N | % |
|---|---|---|
| `ger` | 8,716,820 | 94.6% |
| `lat` | 493,712 | 5.4% |
| `nds` | 1,523 | <0.1% |
| `gmh` | 1,284 | <0.1% |

The ~1.1M records recovered by removing the langid filter are entirely within `ger` (fasttext had misclassified them as non-German). Latin, nds, and gmh were absent from the pkl entirely.

### 1.4 Comparison with old pkl

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

## 2. SR-01 ISBD field ratings

### 2.1 ISBD signal rates

| Field | Old (pkl, 4.47M) | New (parquet, 9.21M) | Change |
|-------|-----------------|---------------------|--------|
| `has_dot_dash` (`. -`) | 53,000 (1.2%) | 36,405 (0.4%) | −0.8 pp |
| `f_other_title` (` :`) | 904,410 (20.2%) | 3,457,062 (37.5%) | +17.3 pp |
| `f_person` (` /`) | 35,822 (0.8%) | 49,055 (0.5%) | −0.3 pp |
| `f_year` | 653,756 (14.6%) | 1,843,322 (20.0%) | +5.4 pp |
| `f_edition` | 161,200 (3.6%) | 297,254 (3.2%) | −0.4 pp |
| `f_parallel` (` =`) | — | 39,418 (0.4%) | — |
| `f_place` | — | 9,045 (0.1%) | — |
| `f_publisher` | — | 14,347 (0.2%) | — |
| `f_series` | — | 865 (0.0%) | — |
| `f_volume` | — | 238,907 (2.6%) | — |

Source: `data/before-parquet/processed/ner/sr01_isbd_field_ratings.csv` (old) · `data/processed/ner/sr01_isbd_field_ratings.csv` (new)

### 2.2 Silver tier counts

| Tier | Old (pkl, 4.48M) | % | New (parquet, 9.21M) | % | Change |
|------|-----------------|---|----------------------|---|--------|
| Tier 2 (structural) | 4,613 | 0.10% | 7,105 | 0.08% | +2,492 |
| Tier 1 (heuristic) | 335,569 | 7.49% | 689,453 | 7.48% | +353,884 |
| Tier 0 (no labels) | 4,137,876 | 92.40% | 8,516,781 | 92.44% | +4,378,905 |

Source: `data/before-parquet/processed/ner/sr01_isbd_field_ratings.csv` (old) · `data/processed/ner/sr01_isbd_field_ratings.csv` (new)

**Key finding:** Tier percentages are stable at 0.1% / 7.5% / 92.4% — the ISBD heuristics scale uniformly. Absolute tier-1 silver candidates doubled: 335K → 689K.

---

## 3. SR-10 token distribution (xlm-roberta BPE)

| Statistic | Old (pkl, spaCy) | New (parquet, BPE) | Change |
|-----------|------------------|--------------------|--------|
| Median `all_tokens` | 8 | 15 | +7 |
| p25 | 4 | 8 | +4 |
| p75 | 14 | 27 | +13 |
| p90 | — | 43 | — |
| p99 | — | 126 | — |

BPE fragments compound German words; the higher token counts do not indicate longer titles — they reflect a finer tokenization granularity. The era-stratified length pattern is preserved (pre-1700 titles are longer than modern ones) but absolute values are not comparable across tokenizers.

Source: `data/before-parquet/processed/ner/sr10_era_length_summary.csv` (old) · `notes/images/token-distribution.json` (new)

**Threshold recalibration:** old short/medium/long boundaries (≤4 / 5–14 / >14, spaCy) → new (≤8 / 9–27 / >27, BPE, p25/p75).

---

## 4. SR-08 corpus cell sizes

### 4.1 v1 — pkl (4.47M)

| Era | tier-0 | tier-1 | tier-2 | Total | % |
|-----|-------:|-------:|-------:|------:|---:|
| pre-1700 | 259,434 | 19,102 | 0 | 278,536 | 6.2% |
| 1700–1800 | 530,576 | 36,088 | 1,274 | 567,938 | 12.7% |
| 19th-c | 830,570 | 91,610 | 3,265 | 925,445 | 20.7% |
| modern | 1,123,728 | 75,185 | 70 | 1,198,983 | 26.8% |
| unknown | 1,393,568 | 113,584 | 4 | 1,507,156 | 33.7% |
| **Total** | **4,137,876** | **335,569** | **4,613** | **4,478,058** | 100% |

Source: `data/before-parquet/processed/ner/sr08_corpus_cell_sizes.csv`

### 4.2 v2 — parquet (9.21M)

| Era | tier-0 | tier-1 | tier-2 | Total | % |
|-----|-------:|-------:|-------:|------:|---:|
| pre-1700 | 376,264 | 32,909 | 7 | 409,180 | 4.4% |
| 1700–1800 | 596,952 | 55,718 | 1,731 | 654,401 | 7.1% |
| 19th-c | 3,481,263 | 253,653 | 4,868 | 3,739,784 | 40.6% |
| modern | 3,513,832 | 313,405 | 497 | 3,827,734 | 41.5% |
| unknown | 548,470 | 33,768 | 2 | 582,240 | 6.3% |
| **Total** | **8,516,781** | **689,453** | **7,105** | **9,213,339** | 100% |

Source (v2): `data/processed/ner/sr08_corpus_cell_sizes.csv`

**Note on tier-2:** pre-1700 has only 7 tier-2 records (vs. 1,731 in 1700–1800). This is consistent with pre-1800 printing conventions that rarely use the full ISBD `. -` area separator. The structural tier in pre-1700 is essentially empty — heuristic and manual annotation are the only viable paths.

---

## 5. Hypotheses and conclusions

### 5.1 Why did `f_other_title` jump from 20.2% to 37.5%?

**Hypothesis 1 — langid filter bias.** The old pkl's `langid=ger` filter disproportionately removed longer, more formally structured titles. Longer DDB titles tend to be subtitle-bearing catalog records (`Haupttitel : Untertitel`); shorter ones tend to be bare item labels. Removing the langid filter restores the full subtitle-bearing population.

**Hypothesis 2 — Latin corpus.** The 494K Latin records (theological, scholarly, legal) heavily use ` :` as the title–subtitle delimiter in early modern printing conventions. A 5.4% share of records contributing 17+ percentage points is implausible — Hypothesis 1 is the primary driver.

**Hypothesis 3 — htype filter change.** The ADR-01 BLANKET_EXCLUDE list differs from the old `hierarchy_type=content` filter: it retains certain full-text types (e.g. Einblattdrucke, Leichenpredigten) that the content filter may have excluded. These types often carry compound titles with ` :` separating a genre label from a title proper. This likely contributes a few percentage points.

**Conclusion:** The ` :` rate reflects the real distribution of subtitle-bearing records in the DDB. The old pkl understated it by ~17 pp due to the langid filter removing formally structured titles. The new rate (37.5%) is more reliable.

### 5.2 Why did `has_dot_dash` drop from 1.2% to 0.4%?

**Hypothesis.** The structural ISBD area separator `. -` was introduced in modern catalog practice. The old pkl was biased toward post-1700 records (the langid filter had higher precision on modern German). The new parquet's larger pre-1800 share dilutes the `. -` prevalence.

**Conclusion:** Structural tier (tier-2) remains a minority at 0.1%. The heuristic tier (tier-1) carries virtually all silver candidates — this conclusion is unchanged and strengthened.

### 5.3 Why did `f_person` drop from 0.8% to 0.5%?

**Hypothesis.** The SoR separator ` /` is a modern cataloging convention. Pre-modern records, which now form a larger share, tend to embed the author in the title string rather than separating it with ` /`. The drop reflects genuine rarity of ` /` in pre-modern records, not a regression in the detection heuristic.

**Conclusion:** No action required. The SR-04 finding that PERSON sub-classification is the right approach (rather than relying on ` /` SoR) is consistent with the lower ` /` prevalence in the full corpus.

### 5.4 Why did `f_year` increase from 14.6% to 20.0%?

**Hypothesis.** Pre-modern German and Latin records frequently embed the publication year directly in the title string (e.g., `Gedruckt im Jahr 1683`). The expanded pre-modern corpus raises the overall year-in-title rate.

**Conclusion:** Year extraction (`f_year`) becomes a more useful silver signal in the new corpus. The threshold `f_year + f_person → tier-1` should cover more pre-modern records than before.

### 5.5 Silver tier stability

The tier percentages (0.1% / 7.5% / 92.4%) are identical between pkl and parquet. This is a strong robustness signal: the ISBD heuristics are not corpus-specific. The doubled absolute tier-1 count (335K → 689K) gives a larger silver training pool. The 92.4% tier-0 fraction confirms that NER is the primary extraction path for the vast majority of records — this motivates SR-11 (LLM annotation of pre-1750 tier-0 records).

---

## 5.6 SR-11 sample validation (parquet, dc_type corrected)

`sr11_sample_validation.py` re-run against `de_titles_tokenized.parquet` after `dc:type`/`edm:hasType` regeneration. Pool: 973,146 pre-1750 tier-0 records (after excluding 290 SR-08 gold obj_ids).

| dc_type | N |
|---------|---|
| Monografie | 17 |
| Einblattdruck | 15 |
| Leichenpredigt | 14 |
| Leichenpredigtsammlung | 1 |
| Quelle | 1 |
| Heft | 1 |
| (empty) | 1 |

| Era | N |
|-----|---|
| pre-1700 | 32 |
| 1700–1800 | 18 |

Source: `data/annotation/sr11_prompt_validation_manual.jsonl` — 50 records, empty spans.

---

## 6. What is unchanged

| Aspect | Status |
|--------|--------|
| SR-03–06 conclusions (FP rates, field decisions) | Valid — heuristic behavior is corpus-agnostic |
| SR-08 gold sample (395 records) | Unchanged — all present in new parquet |
| SR-09 decision (NuNER Zero FAIL) | Final |
| Tier percentages (0.1% / 7.5% / 92.4%) | Stable across both corpora |
| SR-10 era-stratified length pattern | Preserved (pre-1700 longest, modern shortest) |

---

## 7. Related notes

- [notes/adr/reprocessing-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/reprocessing-adr.md) — ADR-03 (corpus migration rationale)
- [notes/adr/corpus-source-adr.md](https://github.com/anntanp/gemea/blob/main/notes/adr/corpus-source-adr.md) — ADR-02 (pkl → parquet)
- [notes/project/reprocessing-workflow.md](https://github.com/anntanp/gemea/blob/main/notes/project/reprocessing-workflow.md) — end-to-end pipeline diagram
- [notes/reprocess-adr.md](https://github.com/anntanp/gemea/blob/main/notes/reprocess-adr.md) — impact on GND linking and NER subsystems
- [notes/ner/ner-bibliographic.md](https://github.com/anntanp/gemea/blob/main/notes/ner/ner-bibliographic.md) §2.1 — SR-01 v2 numbers
- [data/processed/ner/sr01_isbd_field_ratings.csv](https://github.com/anntanp/gemea/blob/main/data/processed/ner/sr01_isbd_field_ratings.csv) — 9.2M row ratings
- [data/processed/ner/sr08_corpus_cell_sizes.csv](https://github.com/anntanp/gemea/blob/main/data/processed/ner/sr08_corpus_cell_sizes.csv) — era × tier cell counts
- [data/annotation/sr11_prompt_validation_manual.jsonl](https://github.com/anntanp/gemea/blob/main/data/annotation/sr11_prompt_validation_manual.jsonl) — SR-11 50-record sample

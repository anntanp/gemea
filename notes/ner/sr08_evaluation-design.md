# SR-08 — Evaluation Design Rationale

Companion to [sr08_gold-set-composition.md](sr08_gold-set-composition.md). Documents the reasoning behind evaluation targets, metric choices, and sample size requirements.

---

## 1. Primary goal

The NER model's primary job is **TITLE extraction**. GND work linking depends on having a clean title string.

PERSON extraction is a **secondary goal**, but its value varies sharply by era. Two factors determine usefulness: (1) whether dc:creator/dc:contributor is absent, and (2) whether a person name actually appears in the title string. Both conditions must hold for NER PERSON extraction to add anything.

**Corpus evidence** — scripts: `sr08_check_agent_coverage.py`, `sr08_check_person_in_title.py`; data: `data/processed/sr08_agent_coverage_by_era.csv`, `data/processed/sr08_person_in_title_by_era.csv`:

| Era | Records | dc:creator or contributor absent | Person name in title (ner_person) |
|---|---|---|---|
| Pre-1700 | 278,536 | 67.4% | 8.7% |
| 1700–1800 | 567,938 | 71.3% | 5.0% |
| 19th-c | 925,445 | 61.1% | 0.6% |
| Modern | 1,198,983 | 51.0% | 0.2% |
| **Overall** | **4,477,780** | **67.1%** | **1.4%** |

dc:creator/contributor is absent in the majority of records across all eras — far more than assumed. However, person names in the title string are rare except in pre-1700 (8.7%) and 1700–1800 (5.0%). For modern and 19th-c records, dc:creator is often absent but person names almost never appear in the title, so NER PERSON extraction yields nothing useful regardless.

`ner_person` was derived using **FLERT** (Schweter & Akbik, 2020) — a document-context NER model based on Flair. Citation: Schweter, S., & Akbik, A. (2020). FLERT: Document-Level Features for Named Entity Recognition. arXiv:2011.06993.

**Priority order:**

| Label | Role | Evaluation priority |
|---|---|---|
| `TITLE` | Primary — required for GND linking | Must be reliable across all eras |
| `PERSON` (pre-1700, 1700–1800) | Person names structurally present in title; dc:creator often absent | High |
| `PERSON` (modern, 19th-c) | Person names rarely in title (~0.2–0.6%); NER adds little | Low — don't let it drive sample size |
| `OTHER_TITLE`, `PARALLEL_TITLE` | Supporting metadata | Secondary |

**Why not joint Work accuracy (TITLE ∧ PERSON)?** PERSON is a secondary goal, not a co-requirement. A correct TITLE with a missing PERSON is still useful for GND linking; a missing TITLE is not. Per-label F1 per era is sufficient.

---

## 2. Why 95% CI and not 100%?

100% CI would require infinite samples — you'd need to observe every possible title to be certain. A CI is a statement about **estimate precision**, not population coverage. 95% is a convention (Fisher, 1920s): if you repeated the sampling many times, 95% of those intervals would contain the true F1. It is a practical tradeoff between certainty and annotation cost.

---

## 3. F1 targets

**0.90 is above the ceiling of comparable benchmarks:**

- **OntoNotes WORK_OF_ART** (works mentioned in text): BERT/RoBERTa typically 0.55–0.68 F1; state-of-the-art ~0.72. Consistently the lowest-scoring entity type in OntoNotes. — Weischedel, R., et al. (2013). *OntoNotes Release 5.0.* LDC2013T19. Linguistic Data Consortium. ⚠️ verify LDC catalog number and full author list.
- **HIPE-2022** (historical NER in German newspapers, closest comparable): best systems 0.60–0.78 F1 on named entity types; title-like entities at the lower end. — Ehrmann, M., Romanello, M., Najem-Meyer, S., Doucet, A., & Clematide, S. (2022). HIPE-2022: Naming the Past. *CLEF 2022 Working Notes*, CEUR-WS vol. 3180. ⚠️ verify author list and volume number against sr08_gold-set-composition.md §7.

GeMeA's task is structurally more favourable than these benchmarks — the entire input *is* the title string, so there is no document context to search — but pre-1700 records introduce historical orthography and author-before-title structure that goes beyond anything in those benchmarks.

**Conservative and achievable targets, stratified by era:**

| Stratum | TITLE F1 target | PERSON F1 target |
|---|---|---|
| Modern, tier-2 | ≥ 0.85 | — (person names rarely in title: 0.2%) |
| 19th-c, tier-1 | ≥ 0.80 | — |
| 1700–1800 | ≥ 0.75 | ≥ 0.70 |
| Pre-1700 | ≥ 0.70 | ≥ 0.70 |

These targets are grounded in benchmark ceilings, not in an assumed intervention rate. The intervention rate implied by these targets should be determined empirically once model results are available, and reported in the paper alongside F1.

---

## 4. Metric

The primary metric is **per-label span F1** with exact character-offset and label match, reported separately per era and per tier. A span is correct only if both its boundaries and its label match the gold annotation exactly — partial matches do not count. This is the standard evaluation protocol for sequence labeling tasks and is consistent with HIPE-2022 (Ehrmann et al., 2022) and CoNLL NER benchmarks.


F1 is reported per label (TITLE, PERSON, OTHER_TITLE) rather than as a macro or micro average, because the labels have different prevalences and different practical importance. Averaging across labels would obscure failures on rare but critical types.

**Confidence intervals** are computed using bootstrap resampling (Efron & Tibshirani, 1993): resample the gold set with replacement 1000 times, compute F1 on each resample, and take the 2.5th–97.5th percentile as the 95% CI. Bootstrap is used rather than the Wilson interval because F1 is not a simple proportion — it is a ratio of precision and recall, each of which is itself a ratio — and has no closed-form variance. The 95% level is the field convention in NLP evaluation (Dror et al., 2018; Søgaard et al., 2014) and matches the reporting standard in HIPE-2022, the most directly comparable historical NER benchmark.

Every F1 number reported in the paper must be accompanied by its 95% bootstrap CI. Bare F1 values without CIs should not appear in evaluation tables or claims.

**References:**
- Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap.* Chapman & Hall. ⚠️ verify page/chapter before citing.
- Ehrmann, M., Romanello, M., Najem-Meyer, S., Doucet, A., & Clematide, S. (2022). HIPE-2022: Naming the Past. *CLEF 2022 Working Notes*, CEUR-WS vol. 3180. ⚠️ confirm paper explicitly reports 95% bootstrap CI before citing for this convention.
- Dror, R., et al. (2018). Deep Dominance — How to Properly Compare Deep Neural Models. *ACL 2018*.
- Søgaard, A., et al. (2014). Simple, Robust Methods for Statistical Testing in NLP.

---

## 5. Binding constraint for sample size

Because TITLE prevalence is ~100%, F1 estimates are stable at relatively low n per stratum. The binding constraint is **per-era TITLE F1 reliability** — enough records per stratum to detect a meaningful drop in TITLE F1 between eras.

PERSON on pre-1700 is the secondary constraint: ~70% prevalence in that stratum, but only ~100 pre-1700 records in the current gold sample → ~70 PERSON instances → ±8–10 pp CI. This is marginal for fine-grained comparison but sufficient to detect gross failures (F1 < 0.55).

**Implication for allocation:**

- Modern and 19th-c sample size is driven by TITLE F1 reliability alone — needs fewer records than previously assumed
- Pre-1700 should be oversampled, driven by PERSON fallback reliability
- 1700–1800 is the ambiguous case for PERSON (transitional period for dc:creator availability); treat similarly to pre-1700

**Author-before-title convention (pre-1700):** the placement of the author's name or credential before the title proper on early modern title pages is documented in historical bibliography. Candidate citations — verify before using:
- Gaskell, P. (1972). *A New Introduction to Bibliography.* Oxford: Clarendon Press. ⚠️ Standard reference for hand-press period (c. 1500–1800) title page conventions; verify specific section.
- Reske, C. (2015). *Die Buchdrucker des 16. und 17. Jahrhunderts im deutschen Sprachgebiet.* Wiesbaden: Harrassowitz. ⚠️ German-specific; less certain it addresses title page layout explicitly.
- Willer et al. (2010) — checked in full; does not address pre-ISBD title page conventions. Not a valid citation for this claim.

**Actual corpus cell sizes** — script: `sr08_corpus_cell_sizes.py`; data: `data/processed/sr08_corpus_cell_sizes.csv`:

| Era | Tier-0 | Tier-1 | Tier-2 | Total |
|---|---|---|---|---|
| Pre-1700 | 259,434 | 19,102 | 0 | 278,536 |
| 1700–1800 | 530,576 | 36,088 | 1,274 | 567,938 |
| 19th-c | 830,570 | 91,610 | 3,265 | 925,445 |
| Modern | 1,123,728 | 75,185 | 70 | 1,198,983 |
| Unknown | 1,393,568 | 113,584 | 4 | 1,507,156 |
| **Total** | **4,137,876** | **335,569** | **4,613** | **4,477,058** |

Key observations:
- Tier-2 is 0.1% of the corpus; pre-1700 has zero tier-2 records, modern has only 70
- Tier-1 is 7.5%; tier-0 dominates at 92.4%
- Some allocation targets in sr08_gold-set-composition.md §2.2 were structurally impossible (e.g. tier-2 pre-1700 target = 5, actual corpus = 0)

**The current allocation table in sr08_gold-set-composition.md §2.2 was not derived from corpus proportions or CI targets — the numbers were round-number design judgments, some of which are structurally impossible.** They need to be replaced.

---

## 6. Minimum sample size per stratum

CI width depends on **entity instance counts**, not record counts. The minimum instances needed is derived from the Wilson interval approximation, treating F1 as a proportion (this is a lower bound — bootstrap CI for F1 is empirically wider, so actual required n may be larger):

$$n = \frac{z^2 \cdot p(1-p)}{e^2}$$

where z = 1.96 (95% CI), p = target F1, e = desired half-width. Records needed = instances needed / entity prevalence per stratum (TITLE prevalence ≈ 100%; PERSON prevalence from `sr08_check_person_in_title.py`).

Script: `sr08_ci_sample_size.py`; data: `data/processed/sr08_ci_sample_size.csv`:

| Stratum | Metric | Target F1 | CI target | Instances needed | Prevalence | Records needed |
|---|---|---|---|---|---|---|
| Pre-1700 | TITLE | ≥ 0.70 | ±5 pp | 323 | 100% | 323 |
| Pre-1700 | TITLE | ≥ 0.70 | ±10 pp | 81 | 100% | 81 |
| Pre-1700 | PERSON | ≥ 0.70 | ±5 pp | 323 | 8.7% | 3,713 |
| Pre-1700 | PERSON | ≥ 0.70 | ±10 pp | 81 | 8.7% | 932 |
| 1700–1800 | TITLE | ≥ 0.75 | ±5 pp | 289 | 100% | 289 |
| 1700–1800 | TITLE | ≥ 0.75 | ±10 pp | 73 | 100% | 73 |
| 1700–1800 | PERSON | ≥ 0.70 | ±5 pp | 323 | 5.0% | 6,460 |
| 1700–1800 | PERSON | ≥ 0.70 | ±10 pp | 81 | 5.0% | 1,620 |
| 19th-c | TITLE | ≥ 0.80 | ±5 pp | 246 | 100% | 246 |
| 19th-c | TITLE | ≥ 0.80 | ±10 pp | 62 | 100% | 62 |
| Modern | TITLE | ≥ 0.85 | ±5 pp | 196 | 100% | 196 |
| Modern | TITLE | ≥ 0.85 | ±10 pp | 49 | 100% | 49 |

**The PERSON CI constraint is not achievable at practical annotation cost.** Reaching ±5 pp on PERSON requires 3,713 pre-1700 records and 6,460 1700–1800 records. Even ±10 pp requires 932 and 1,620 respectively — far beyond a feasible gold set.

**Decision: accept wide CI on PERSON (option 2).** The gold set is sized for TITLE reliability. PERSON CI will be wider and must be reported explicitly alongside any PERSON F1 claim. PERSON results are sufficient to detect gross model failures but not fine-grained differences between models. This limitation must be stated in the paper.

**Implication for total gold set size (TITLE-driven):**

| Stratum | Min records (±5 pp) | Min records (±10 pp) |
|---|---|---|
| Pre-1700 | 323 | 81 |
| 1700–1800 | 289 | 73 |
| 19th-c | 246 | 62 |
| Modern | 196 | 49 |
| **Total (minimum)** | **1,054** | **265** |

**Decision: target ±10 pp CI due to time constraints.** The minimum gold set is ~265 records across four era strata. The current gold set (395 records, ~100 per era) already meets this threshold. No expansion is required for the ±10 pp target; the existing 395-record set is sufficient.

---

## 7. What needs to be done to finalise allocation

1. ~~Fix the TITLE F1 usability threshold~~ — resolved: see §3
2. ~~Pull actual corpus cell sizes~~ — resolved: see §5
3. ~~Compute minimum per-stratum record counts~~ — resolved: see §6
4. **Cap at corpus availability and redistribute** — tier-2 is nearly exhausted (0 pre-1700, 70 modern); allocation must shift toward tier-0 and tier-1
5. **Update the allocation table** in sr08_gold-set-composition.md §2.2 with derived numbers and documented rationale
6. ~~Decide whether to expand the gold set~~ — resolved: ±10 pp CI adopted due to time constraints; current 395-record set is sufficient

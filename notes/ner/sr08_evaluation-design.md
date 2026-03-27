# SR-08 — Evaluation Design Rationale

Companion to [sr08_gold-set-composition.md](sr08_gold-set-composition.md). Documents the reasoning behind evaluation targets, metric choices, and sample size requirements.

---

## Tables

| Table | Section | Purpose | Backing data |
|---|---|---|---|
| Agent/person coverage by era | [§1](#1-primary-goal) | Shows dc:creator/contributor absence rate and ner_person prevalence per era; motivates PERSON priority by stratum | `sr08_agent_coverage_by_era.csv`, `sr08_person_in_title_by_era.csv` |
| Label priority order | [§1](#1-primary-goal) | Ranks evaluation labels by role and priority | — |
| F1 targets by stratum | [§3](#3-f1-targets) | Conservative achievable F1 thresholds per era, grounded in benchmark ceilings | — |
| Corpus cell sizes (era × tier) | [§5](#5-binding-constraint-for-sample-size) | Actual record counts per era × silver_tier cell; replaces round-number allocation targets | `sr08_corpus_cell_sizes.csv` |
| CI sample size requirements | [§6](#6-minimum-sample-size-per-stratum) | Wilson interval computation of minimum instances and records needed per stratum and CI target | `sr08_ci_sample_size.csv` |
| Gold set size by CI target | [§6](#6-minimum-sample-size-per-stratum) | Minimum records per era at ±5 pp and ±10 pp; used to select ±10 pp as feasible target | `sr08_ci_sample_size.csv` |
| Gold set composition audit | [§8](#8-revised-allocation-strategy) | Current vs. original allocation targets per era × tier; identifies tier-1 over-representation | `sr08_gold_composition_audit.csv` |
| Proposed revised allocation | [§8](#8-revised-allocation-strategy) | New tier allocation boosting tier-0 in high-risk strata; target vs. actual totals per era | — |

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
- **HIPE-2022** (historical NER in multilingual historical documents, closest comparable): German NERC-Coarse strict F1 — hipe2020-de best system 0.794, neural baseline 0.703; sonar-de (Berlin State Library 19C–20C) best 0.529, baseline 0.307. No TITLE entity type; `work` in classical commentaries (ajmc) is the closest analogue but scores 0.93+ partly due to high train/test mention overlap. — Ehrmann, M., Romanello, M., Najem-Meyer, S., Doucet, A., & Clematide, S. (2022). Extended Overview of HIPE-2022: Named Entity Recognition and Linking in Multilingual Historical Documents. *CLEF 2022 Working Notes*, CEUR-WS Vol. 3180, paper-83. See [ref_hipe2022-overview.md](ref_hipe2022-overview.md).

GeMeA's task is structurally more favourable than these benchmarks — the entire input *is* the title string, so there is no document context to search — but pre-1700 records introduce historical orthography and author-before-title structure that goes beyond anything in those benchmarks.

**Why we target 0.85 for modern records despite OntoNotes WORK_OF_ART SOTA at ~0.72:** the tasks differ structurally in our favour. OntoNotes requires finding work titles embedded anywhere in running prose — the entity boundary is ambiguous and surrounding context is noisy. GeMeA input is the title string itself: no search problem, only segmentation. This justifies a higher target for modern and 19th-c records. Pre-1700 is where we concede (target 0.70) — author-before-title structure and non-standard orthography introduce difficulty that OntoNotes does not have.

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

### 4.1 Span match

**Exact span match** is used: a prediction is correct only if both character boundaries and the label match the gold annotation exactly. Partial boundary overlaps do not count. This is the standard NERC evaluation protocol (HIPE-2022 strict regime, Ehrmann et al., 2022; CoNLL benchmarks) and gives a clean signal — the model either found the right span or it didn't.

Fuzzy (overlapping boundary) match would inflate scores without telling us whether the extracted title is actually usable for GND linking. Exact match is therefore the more appropriate choice for the end goal.

One risk: **boundary disagreement between annotators** on long pre-1700 titles, where the edge between TITLE and a trailing author credential is genuinely ambiguous. If annotators disagree systematically, exact span match will penalise the model for annotation inconsistency rather than extraction failure. This should be flagged in the paper and monitored during annotation. Curation decisions for each structural case are documented in [sr08_title-boundary-curation.md](sr08_title-boundary-curation.md) and must be applied uniformly.

### 4.2 Per-label reporting vs. averages

F1 is reported **per label** (TITLE, OTHER_TITLE, PERSON) per era. No macro or micro averages across labels.

**Why not micro average:** micro F1 pools all TP/FP/FN across all labels before computing the score. Because TITLE is present in ~100% of records, micro F1 would be almost entirely determined by TITLE performance — OTHER_TITLE and PERSON would be invisible.

**Why not macro average:** macro F1 computes F1 per label then averages, weighting all three labels equally regardless of prevalence. PERSON appears in 0.2%–8.7% of records depending on era; averaging it equally with TITLE would let poor PERSON performance (which is already accepted as indicative-only) drag down the headline figure, misrepresenting the pipeline's actual utility for GND linking.

Per-label reporting is transparent about what the pipeline does well (modern TITLE) and where it struggles (pre-1700 PERSON), which is exactly what a resource paper needs to convey.

### 4.3 CI strategy: point estimates now, bootstrap deferred

For the current paper, evaluation follows the HIPE-2022 reporting convention: micro Precision, Recall, and F1 per label per era, as point estimates, with sample sizes reported alongside every figure so readers can judge reliability directly.

Bootstrap CI (Efron & Tibshirani, 1993) would be the more rigorous approach — F1 has no closed-form variance (it is a ratio of precision and recall, each of which is itself a ratio of counts, so there is no algebraic formula to propagate uncertainty through the full expression), meaning resampling is the only general way to quantify uncertainty — but is deferred for two reasons:

1. **Small per-stratum n.** With ~100 records per era stratum, bootstrap CIs will be wide (±10–15 pp). Reporting wide CIs without the sample size to tighten them risks being misleading rather than informative; it is cleaner to state the n and let the reader draw conclusions.
2. **Contribution scope.** The paper's claim is that the pipeline produces usable extractions across eras, not that one model configuration is significantly better than another. Point estimates per era are sufficient to support that claim. Bootstrap CI becomes necessary when comparing two systems where the difference is small — that is a model comparison paper, not this one.

**References:**
- Ehrmann, M., Romanello, M., Najem-Meyer, S., Doucet, A., & Clematide, S. (2022). Extended Overview of HIPE-2022: Named Entity Recognition and Linking in Multilingual Historical Documents. *CLEF 2022 Working Notes*, CEUR-WS Vol. 3180, paper-83. ⚠️ Does not report bootstrap CI — cite for F1 benchmarks and exact span match convention only.
- Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap.* Chapman & Hall. ⚠️ verify page/chapter before citing.
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

## 7. Revised allocation strategy

**Principle: oversample problematic strata, not corpus proportions.**

Tier-0 is the hardest inference path (no ISBD signals) and the most prevalent in the corpus (92.4%). Tier-2 is structurally clean — a small spot-check is enough to verify the prefill logic but contributing many tier-2 records inflates F1 scores without testing the model on difficult cases. The allocation should therefore heavily favour tier-0, with tier-1 included for structural coverage and tier-2 minimised.

Within tier-0, pre-1700 and 1700–1800 are the highest-risk strata: author-before-title structure, historical orthography, and dc:creator absent in 67–71% of records making PERSON extraction the only fallback. These should receive the most records.

**Audit of current gold set** — script: `sr08_gold_composition_audit.py`; data: `data/processed/sr08_gold_composition_audit.csv`:

| Era | Tier-0 (actual) | Tier-1 (actual) | Tier-2 (actual) | Total (actual) | Total (target) | Delta |
|---|---|---|---|---|---|---|
| Pre-1700 | 96 | 34 | 0 | 130 | 100 | +30 |
| 1700–1800 | 37 | 33 | 10 | 80 | 60 | +20 |
| 19th-c | 15 | 30 | 15 | 60 | 60 | 0 |
| Modern | 20 | 40 | 20 | 80 | 80 | 0 |
| Unknown | 10 | 35 | 0 | 45 | 0 | +45 |
| **Total** | **178** | **172** | **45** | **395** | **300** | **+95** |

The original targets summed to only 300; the extra 95 records came from genre oversampling (Leichenpredigt, Einblattdruck) and the unknown era. The current set already oversamples pre-1700 relative to original targets — but the tier composition is off: tier-1 is over-represented (172 records, 43.5%).

Tier-1 records have partial ISBD signals (heuristic ` /` or ` :` but not the full `. -` separator). They test model behaviour on records with weak structural cues — useful, but not where the model is most likely to fail. Tier-0 has no structural signals at all: the model must rely entirely on learned patterns, which is both the hardest case and the most important one (92.4% of the corpus). Each additional tier-0 record in the gold set evaluates the model on a more representative and more challenging example than a tier-1 record would. Tier-1's evaluation contribution is real but lower per record than tier-0.

**Proposed revised allocation** (total kept at 395, tier-0 boosted, tier-2 minimised):

| Era | Tier-0 | Tier-1 | Tier-2 | Total (target) | Total (actual) | Rationale |
|---|---|---|---|---|---|---|
| Pre-1700 | 110 | 20 | 0 | 130 | 130 | Hardest stratum; PERSON fallback; corpus has 0 tier-2 |
| 1700–1800 | 75 | 15 | 5 | 95 | 80 | Transitional; PERSON fallback; minimal tier-2 spot-check |
| 19th-c | 55 | 15 | 5 | 75 | 60 | TITLE primary; tier-0 boosted over current 15 |
| Modern | 55 | 10 | 5 | 70 | 80 | TITLE primary; tier-0 boosted; corpus has only 70 tier-2 total |
| Unknown | 15 | 10 | 0 | 25 | 45 | Reduced; era unknown limits evaluation utility |
| **Total** | **310** | **70** | **15** | **395** | **395** | Tier-0 share: 78.5% vs. current 45.1% |

Key changes from current:
- Tier-0 share increases from 45.1% → 78.5%
- Tier-1 reduced from 172 → 70 (less structural signal = less evaluation value per record)
- Tier-2 reduced from 45 → 15 (spot-check only)
- 1700–1800 total increased from 80 → 95 (PERSON fallback priority)
- Modern reduced from 80 → 70 (lower risk, TITLE only)
- Unknown reduced from 45 → 25

All proposed counts are well within corpus availability (see §5).

---

## 8. Pending items

- [x] Fix the TITLE F1 usability threshold — resolved: see §3
- [x] Pull actual corpus cell sizes — resolved: see §5
- [x] Compute minimum per-stratum record counts — resolved: see §6
- [x] Decide whether to expand the gold set — resolved: ±10 pp CI adopted due to time constraints; current 395-record set is sufficient
- [ ] Cap at corpus availability and redistribute — see §7
- [ ] Update the allocation table in sr08_gold-set-composition.md §2.2 with derived numbers and documented rationale
- [ ] **Resolve unknown-era records** — original target was 0; 45 records entered the gold set as an artifact of Leichenpredigt/Einblattdruck genre oversampling pulling in records whose year could not be resolved. These cannot be evaluated per-era. Decision needed: remove, keep as unstrataified spot-check, or reduce to 25 as proposed in §7.

# Architecture Decision Record — NER for Bibliographic Title Extraction

**Status:** In progress — SR-08 annotation pending; SR-09, SR-11 blocked
**Scope:** NER pipeline for extracting structured bibliographic entities from `DF_DE_TITLES` — a filtered snapshot of the DDB corpus (4.47M records; `ddb:hierarchyType` = `content`, `dc:language` + `langid` = German)
**Full notes:** [ner-bibliographic.md](../ner-bibliographic.md)

---

## 1. Context

DDB title strings are the primary text surface for bibliographic entity extraction in GeMeA. The goal is to extract Work-level entities (`TITLE`, `OTHER_TITLE`, `PERSON`) to support GND work linking. `DF_DE_TITLES` is a filtered snapshot (4.47M records) derived from the DDB corpus by selecting `ddb:hierarchyType` = `content`, then applying `dc:language` + `langid` = German — not the full DDB corpus. It spans pre-1700 Early Modern German to contemporary titles, with no consistent structural markup.

ISBD punctuation (`. -`, ` :`, ` /`) provides structural signals in a minority of records. NER is the fallback for the majority. The two approaches are complementary: ISBD parsing handles structured records reliably; NER handles the unstructured majority.

Each record is assigned a **silver tier** by `sr01_rate_isbd_fields.py` based on how many and which ISBD heuristic fields fire:

| Tier | Criteria | Corpus share | Role |
|---|---|---|---|
| **2** | `has_dot_dash` AND `f_person` AND at least one of `f_edition`, `f_place`, `f_publisher`, `f_year`, `f_series` | 0.1% (4,613 records) | Primary silver training set — structural area separator present; multi-field span labeling with high confidence |
| **1** | `n_fields ≥ 3` OR (`f_person` AND `f_year`) | 7.5% (335,524 records) | Augmentation set — partial ISBD evidence; Work + Expression level annotation |
| **0** | All others — no reliable ISBD signal | 92.4% (4,137,643 records) | Not selected as silver candidates; primary NER inference target |

`has_dot_dash` (`. -` area separator) is the gating condition for tier-2: it is present in only 1.2% of records, which directly caps tier-2 at 0.1%. Tier-0 is where NER does all the work.

---

## 2. Decisions

### D-01 — ISBD as primary extractor, NER as fallback

**Decision:** Rule-based ISBD parser runs first. NER only runs when ISBD fails to produce a confident extraction.

**Why:** ISBD signals (`. -`, ` :`, ` /`) are high-precision when present. Silver label analysis (SR-01) shows tier-2 precision is near-perfect for structural records. NER is slower, less deterministic, and harder to explain — it should not replace a reliable rule when one exists.

**Consequence:** NER applies to ~92.4% of the corpus (tier-0, no ISBD signals) — the majority, not a small edge case.

**Notes:** [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md) · [sr01_isbd-applicability.md](sr01_isbd-applicability.md) · [silver-dataset-pipeline.md](silver-dataset-pipeline.md)

---

### D-02 — Parser must prioritise ` :` over ` /`

**Decision:** `OTHER_TITLE` / `TITLE` boundary uses ` :` as the primary split signal. ` /` (SoR) is secondary.

**Why (SR-02):** ` :` appears in 20.2% of titles; ` /` appears in only 0.8%. Prioritising ` /` would miss 96% of subtitle splits.

**Notes:** [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md) · [sr01_isbd-field-rating-adr.md](sr01_isbd-field-rating-adr.md)

---

### D-03 — Silver tier thresholds and field exclusions

**Decision:** Tier-2 = `has_dot_dash` + ≥2 additional heuristic fields. Excluded from silver labels: `f_parallel` (~80% FP), `f_edition` (~83% FP), trailing `.` (93% FP). Post-filter required on `f_person` (~36% FP) and `f_person_compound` (~29% FP).

**Why (SR-03, SR-05):** FP rates above 15% degrade silver label quality below usefulness. `f_parallel` and `f_edition` were found to fire predominantly on false positives. Trailing `.` adds no detection power beyond `has_dot_dash`.

**Notes:** [sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md) · [sr05_trailing-period-noise.md](sr05_trailing-period-noise.md)

---

### D-04 — TRANSLATOR and EDITOR dropped as silver label targets

**Decision:** `TRANSLATOR` and `EDITOR` are not viable silver label types. `f_person` sub-classified as: `f_resp_person` (true author SoR), `f_resp_org` (corporate body), `f_resp_family` (family), `f_resp_editor` (editor role), `f_resp_other` (non-SoR).

**Why (SR-04):** 0 true translators found in 100-record sample. EDITOR detection: 0 F1. Only 35% of `f_person` records are true author SoRs; 41% are non-SoR false positives, 19% corporate bodies, 5% editors. The ISBD/RDA agent model requires sub-classification, not a flat TRANSLATOR label.

**Notes:** [sr04_translator-person-disambiguation.md](sr04_translator-person-disambiguation.md)

---

### D-05 — No Latin stratum; Early Modern German is the primary historical challenge

**Decision:** Latin records are not stratified or evaluated separately. True Latin prevalence is ~0.5% — too rare to justify a stratum. No Latin NER capability required for Phase 1. EARLY_MODERN_DE (1500–1750) is the primary historical challenge.

**Why (SR-06):** Latin heuristic has 83% FP rate — standard German Protestant/academic vocabulary (`Anno`, `Christi`, `Doctor`) triggers false positives. EARLY_MODERN_DE heuristic achieves F1 = 0.95 after two rule fixes.

**Notes:** [sr06_historical-scope.md](sr06_historical-scope.md)

---

### D-06 — FRBR scope: Work labels in Phase 1, Expression labels in Phase 2

**Decision:** Phase 1 evaluation covers `TITLE`, `OTHER_TITLE`, `PERSON` only. Phase 2 adds `TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM`. Manifestation labels (`PUBLISHER`, `PLACE`, `YEAR`, `EDITION`, `SERIES`, `VOLUME`) deferred.

**Why (SR-07):** DDB objects are Manifestation-level. Work-level labels are the minimum viable set for GND linking quality metrics. Expression labels require additional heuristics and are not needed to establish the paper's primary contribution. Annotating Phase 2 labels in the same pass avoids re-annotation.

**Notes:** [sr08_label-design-rationale.md](sr08_label-design-rationale.md) · [sr08_gold-set-composition.md](sr08_gold-set-composition.md)

---

### D-07 — NER model path: NuNER Zero → LLM labeling → fine-tune xlm-roberta-base

**Decision:** Evaluate NuNER Zero zero-shot first (SR-09). If TITLE F1 meets threshold: deploy zero-shot. If not: generate 4k–5k LLM-labeled records (SR-11) and fine-tune `xlm-roberta-base` on silver + LLM-labeled set.

**Why:** NuNER Zero is the strongest available zero-shot NER model for this task size and language profile (see [ref_gliner-nunerzero-comparison.md](ref_gliner-nunerzero-comparison.md)). Fine-tuning on silver labels alone risks propagating ISBD-induced label noise; LLM annotation of tier-0 records provides coverage where silver labels are absent.

**Notes:** [ref_gliner-nunerzero-comparison.md](ref_gliner-nunerzero-comparison.md) · [sr11_labeling-strategy.md](sr11_labeling-strategy.md)

---

### D-08 — Gold set: 395 records, ±10 pp CI, TITLE-driven allocation

**Decision:** Gold set = 395 records, stratified by era × tier × dc_type. CI target: ±10 pp on TITLE F1 per era (requires ~49–81 records per stratum; current ~100 per era is sufficient). PERSON evaluated as secondary with wide CI (±15–20 pp); reported as indicative only.

**Why (SR-08):** ±5 pp CI on TITLE would require ~1,054 records; ±5 pp CI on PERSON is structurally impractical (requires 3,700–6,500 records due to low prevalence). Time constraints make ±10 pp the right tradeoff. PERSON extraction is secondary because dc:creator/contributor is absent in 67% of records overall but person names appear in titles only for pre-1700 (8.7%) and 1700–1800 (5.0%) — not for modern (0.2%) or 19th-c (0.6%) records.

**F1 targets:**

| Era | TITLE | PERSON |
|---|---|---|
| Modern | ≥ 0.85 | — |
| 19th-c | ≥ 0.80 | — |
| 1700–1800 | ≥ 0.75 | ≥ 0.70 |
| Pre-1700 | ≥ 0.70 | ≥ 0.70 |

Targets are grounded in benchmark ceilings (OntoNotes WORK_OF_ART: 0.55–0.72; HIPE-2022 historical German: 0.60–0.78), not assumed intervention rates.

**Notes:** [sr08_evaluation-design.md](sr08_evaluation-design.md) · [sr08_gold-set-composition.md](sr08_gold-set-composition.md)

---

### D-09 — Tier allocation: oversample tier-0, minimise tier-2

**Decision:** Gold set allocation weights tier-0 at 79% (target), up from 45% (current). Tier-2 reduced to spot-check only (15 records). Pre-1700 and 1700–1800 oversampled within tier-0.

**Why (SR-08):** Tier-0 is the hardest inference path (no ISBD signals), the most prevalent in corpus (92.4%), and the stratum where NER matters most. Tier-2 records inflate F1 without testing difficult cases. Pre-1700 tier-0 is the primary failure risk: author-before-title structure + historical orthography + dc:creator absent in 67%.

**Notes:** [sr08_evaluation-design.md](sr08_evaluation-design.md) §8 · [sr08_gold-set-composition.md](sr08_gold-set-composition.md)

---

### D-10 — Evaluation metric: per-label point-estimate F1, exact span match; bootstrap deferred

**Decision:** Report micro P/R/F1 per label (TITLE, OTHER_TITLE, PERSON) per era as point estimates, following the HIPE-2022 reporting convention. Exact span match throughout (both character boundaries and label must match). No macro or micro averages across labels. Sample sizes reported alongside every F1 figure. Bootstrap CI deferred to future work.

**Why — exact span match:** Gives a clean, unambiguous signal consistent with HIPE-2022 strict regime and CoNLL benchmarks. Fuzzy (overlapping boundary) match would inflate scores without indicating whether the extraction is usable for GND linking. Risk: boundary disagreement between annotators on long pre-1700 titles (TITLE vs. trailing author credential) — should be monitored during annotation and flagged in the paper.

**Why — no macro/micro averages:**
- *Micro average* pools all TP/FP/FN before computing F1 — dominated by TITLE (~100% prevalence), making OTHER_TITLE and PERSON invisible.
- *Macro average* weights all labels equally regardless of prevalence — PERSON (0.2%–8.7% by era) would drag down the headline figure, misrepresenting pipeline utility for the primary goal of GND linking.
- Per-label reporting is transparent: it shows where the pipeline succeeds (modern TITLE) and where it struggles (pre-1700 PERSON).

**Why — point estimates over bootstrap:** The contribution is the pipeline, not a model comparison. Bootstrap CI is necessary when asking whether two systems differ significantly — that is not the question here. Per-stratum n (~100) would also produce wide CIs (±10–15 pp) that are more misleading than informative at this sample size.

**Notes:** [sr08_evaluation-design.md](sr08_evaluation-design.md) §4

---

## 3. Open decisions

| Decision | Blocked on | Notes |
|---|---|---|
| NuNER Zero viability (SR-09) | SR-08 annotation complete | Pass/fail gate for zero-shot vs. fine-tune path |
| LLM annotation prompt design (SR-11) | SR-08 50-record seed | Early Modern German author-before-title prompt spec |
| Silver tier field weighting (SR-12) | SR-03 extension, SR-08 | Replace binary threshold with precision-weighted score |
| Revised allocation re-sample | SR-08 annotation complete | Re-run `sr08_sample_gold.py` with tier-0 boost |

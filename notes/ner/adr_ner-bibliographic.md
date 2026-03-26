# ADR — NER for Bibliographic Title Extraction

**Status:** In progress — SR-08 annotation pending; SR-09, SR-11 blocked
**Scope:** NER pipeline for extracting structured bibliographic entities from `DF_DE_TITLES` (4.47M German DDB title strings)
**Full notes:** [ner-bibliographic.md](../ner-bibliographic.md)

---

## 1. Context

DDB title strings are the primary text surface for bibliographic entity extraction in GeMeA. The goal is to extract Work-level entities (`TITLE`, `OTHER_TITLE`, `PERSON`) to support GND work linking. The pipeline must handle 4.47M records spanning pre-1700 Early Modern German to contemporary titles, with no consistent structural markup.

ISBD punctuation (`. -`, ` :`, ` /`) provides structural signals in a minority of records. NER is the fallback for the majority. The two approaches are complementary: ISBD parsing handles structured records reliably; NER handles the unstructured majority.

---

## 2. Decisions

### D-01 — ISBD as primary extractor, NER as fallback

**Decision:** Rule-based ISBD parser runs first. NER only runs when ISBD fails to produce a confident extraction.

**Why:** ISBD signals (`. -`, ` :`, ` /`) are high-precision when present. Silver label analysis (SR-01) shows tier-2 precision is near-perfect for structural records. NER is slower, less deterministic, and harder to explain — it should not replace a reliable rule when one exists.

**Consequence:** NER applies to ~92.4% of the corpus (tier-0, no ISBD signals) — the majority, not a small edge case.

---

### D-02 — Parser must prioritise ` :` over ` /`

**Decision:** `OTHER_TITLE` / `TITLE` boundary uses ` :` as the primary split signal. ` /` (SoR) is secondary.

**Why (SR-02):** ` :` appears in 20.2% of titles; ` /` appears in only 0.8%. Prioritising ` /` would miss 96% of subtitle splits.

---

### D-03 — Silver tier thresholds and field exclusions

**Decision:** Tier-2 = `has_dot_dash` + ≥2 additional heuristic fields. Excluded from silver labels: `f_parallel` (~80% FP), `f_edition` (~83% FP), trailing `.` (93% FP). Post-filter required on `f_person` (~36% FP) and `f_person_compound` (~29% FP).

**Why (SR-03, SR-05):** FP rates above 15% degrade silver label quality below usefulness. `f_parallel` and `f_edition` were found to fire predominantly on false positives. Trailing `.` adds no detection power beyond `has_dot_dash`.

---

### D-04 — TRANSLATOR and EDITOR dropped as silver label targets

**Decision:** `TRANSLATOR` and `EDITOR` are not viable silver label types. `f_person` sub-classified as: `f_resp_person` (true author SoR), `f_resp_org` (corporate body), `f_resp_family` (family), `f_resp_editor` (editor role), `f_resp_other` (non-SoR).

**Why (SR-04):** 0 true translators found in 100-record sample. EDITOR detection: 0 F1. Only 35% of `f_person` records are true author SoRs; 41% are non-SoR false positives, 19% corporate bodies, 5% editors. The ISBD/RDA agent model requires sub-classification, not a flat TRANSLATOR label.

---

### D-05 — No Latin stratum; Early Modern German is the primary historical challenge

**Decision:** Latin records are not stratified or evaluated separately. True Latin prevalence is ~0.5% — too rare to justify a stratum. No Latin NER capability required for Phase 1. EARLY_MODERN_DE (1500–1750) is the primary historical challenge.

**Why (SR-06):** Latin heuristic has 83% FP rate — standard German Protestant/academic vocabulary (`Anno`, `Christi`, `Doctor`) triggers false positives. EARLY_MODERN_DE heuristic achieves F1 = 0.95 after two rule fixes.

---

### D-06 — FRBR scope: Work labels in Phase 1, Expression labels in Phase 2

**Decision:** Phase 1 evaluation covers `TITLE`, `OTHER_TITLE`, `PERSON` only. Phase 2 adds `TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM`. Manifestation labels (`PUBLISHER`, `PLACE`, `YEAR`, `EDITION`, `SERIES`, `VOLUME`) deferred.

**Why (SR-07):** DDB objects are Manifestation-level. Work-level labels are the minimum viable set for GND linking quality metrics. Expression labels require additional heuristics and are not needed to establish the paper's primary contribution. Annotating Phase 2 labels in the same pass avoids re-annotation.

---

### D-07 — NER model path: NuNER Zero → LLM labeling → fine-tune xlm-roberta-base

**Decision:** Evaluate NuNER Zero zero-shot first (SR-09). If TITLE F1 meets threshold: deploy zero-shot. If not: generate 4k–5k LLM-labeled records (SR-11) and fine-tune `xlm-roberta-base` on silver + LLM-labeled set.

**Why:** NuNER Zero is the strongest available zero-shot NER model for this task size and language profile (see [ref_gliner-nunerzero-comparison.md](ref_gliner-nunerzero-comparison.md)). Fine-tuning on silver labels alone risks propagating ISBD-induced label noise; LLM annotation of tier-0 records provides coverage where silver labels are absent.

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

---

### D-09 — Tier allocation: oversample tier-0, minimise tier-2

**Decision:** Gold set allocation weights tier-0 at 79% (target), up from 45% (current). Tier-2 reduced to spot-check only (15 records). Pre-1700 and 1700–1800 oversampled within tier-0.

**Why (SR-08):** Tier-0 is the hardest inference path (no ISBD signals), the most prevalent in corpus (92.4%), and the stratum where NER matters most. Tier-2 records inflate F1 without testing difficult cases. Pre-1700 tier-0 is the primary failure risk: author-before-title structure + historical orthography + dc:creator absent in 67%.

---

### D-10 — Evaluation metric: per-label bootstrap F1, 95% CI, exact span match

**Decision:** Report per-label span F1 (exact character-offset + label match), per era and per tier. CI: 95% bootstrap (1000 samples). No macro/micro averages. Every F1 number in the paper must carry its CI.

**Why:** F1 has no closed-form variance — bootstrap is required (Efron & Tibshirani, 1993). Per-label reporting avoids averaging across labels with different prevalences and practical importance. Exact span match is the standard NER protocol (consistent with HIPE-2022, Ehrmann et al., 2022). 95% is the field convention (Dror et al., 2018).

---

## 3. Open decisions

| Decision | Blocked on | Notes |
|---|---|---|
| NuNER Zero viability (SR-09) | SR-08 annotation complete | Pass/fail gate for zero-shot vs. fine-tune path |
| LLM annotation prompt design (SR-11) | SR-08 50-record seed | Early Modern German author-before-title prompt spec |
| Silver tier field weighting (SR-12) | SR-03 extension, SR-08 | Replace binary threshold with precision-weighted score |
| Revised allocation re-sample | SR-08 annotation complete | Re-run `sr08_sample_gold.py` with tier-0 boost |

---

## 4. References

- Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap.* Chapman & Hall. ⚠️ verify page/chapter.
- Ehrmann, M., et al. (2022). HIPE-2022: Naming the Past. *CLEF 2022 Working Notes*, CEUR-WS vol. 3180. ⚠️ verify author list and volume.
- Weischedel, R., et al. (2013). *OntoNotes Release 5.0.* LDC2013T19. ⚠️ verify catalog number.
- Dror, R., et al. (2018). Deep Dominance. *ACL 2018*.
- Schweter, S., & Akbik, A. (2020). FLERT: Document-Level Features for Named Entity Recognition. arXiv:2011.06993.
- Zaratiana, U., et al. (2024). GLiNER. *NAACL 2024*.
- Bogdanov, S., et al. (2024). NuNER. *EMNLP 2024*.

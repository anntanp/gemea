# SR-08 — Evaluation Design Rationale

Companion to [sr08_gold-set-composition.md](sr08_gold-set-composition.md). Documents the reasoning behind evaluation targets, metric choices, and sample size requirements.

---

## 1. Primary goal

The NER model's primary job is **TITLE extraction**. GND work linking depends on having a clean title string; dc:creator and dc:contributor cover the person in most cases.

PERSON extraction is a **secondary fallback**: useful when both dc:creator and dc:contributor are blank — which happens predominantly in pre-1700 and 1700–1800 objects. In modern and 19th-century objects, person names rarely appear in the title at all (unless the title is a character's name), so PERSON recall there is structurally low and practically less important.

**Priority order:**

| Label | Role | Evaluation priority |
|---|---|---|
| `TITLE` | Primary — required for GND linking | Must be reliable across all eras |
| `PERSON` (pre-1700, 1700–1800) | Fallback when dc:creator/contributor blank | High — this is the main failure mode |
| `PERSON` (modern, 19th-c) | Rarely present in title; dc:creator usually populated | Low — evaluate but don't let it drive sample size |
| `OTHER_TITLE`, `PARALLEL_TITLE` | Supporting metadata | Secondary |

**Why not joint Work accuracy (TITLE ∧ PERSON)?** Originally considered as the primary metric, but dropped: PERSON is a fallback, not a co-requirement. A correct TITLE with a missing PERSON is still useful; a missing TITLE is not. Per-label F1 per era is sufficient.

---

## 2. Why 95% CI and not 100%?

100% CI would require infinite samples — you'd need to observe every possible title to be certain. A CI is a statement about **estimate precision**, not population coverage. 95% is a convention (Fisher, 1920s): if you repeated the sampling many times, 95% of those intervals would contain the true F1. It is a practical tradeoff between certainty and annotation cost.

---

## 3. F1 targets

**0.90 is above the ceiling of comparable benchmarks:**

- **OntoNotes WORK_OF_ART** (works mentioned in text): BERT/RoBERTa typically 0.55–0.68 F1; state-of-the-art ~0.72. Consistently the lowest-scoring entity type in OntoNotes.
- **HIPE-2022** (historical NER in German newspapers, closest comparable): best systems 0.60–0.78 F1 on named entity types; title-like entities at the lower end.

GeMeA's task is structurally more favourable than these benchmarks — the entire input *is* the title string, so there is no document context to search — but pre-1700 records introduce historical orthography and author-before-title structure that goes beyond anything in those benchmarks.

**Conservative and achievable targets, stratified by era:**

| Stratum | TITLE F1 target | PERSON F1 target |
|---|---|---|
| Modern, tier-2 | ≥ 0.85 | — (dc:creator usually present) |
| 19th-c, tier-1 | ≥ 0.80 | — |
| 1700–1800 | ≥ 0.75 | ≥ 0.70 |
| Pre-1700 | ≥ 0.70 | ≥ 0.70 |

These targets are grounded in benchmark ceilings, not in an assumed intervention rate. The intervention rate implied by these targets should be determined empirically once model results are available, and reported in the paper alongside F1.

---

## 4. Metric

**Per-label span F1** (exact character-offset + label match), reported per era and per tier.

CI method: **bootstrap F1** (1000 samples), not Wilson interval. Wilson applies to proportions; F1 is not a proportion. Report 95% bootstrap CI alongside every F1 number.

- Bootstrap method: Efron & Tibshirani (1993), *An Introduction to the Bootstrap*, Chapman & Hall. ⚠️ verify page/chapter before citing.
- 95% convention in NLP evaluation: Efron & Tibshirani (1993) is the statistical origin; Ehrmann et al. (2022), HIPE-2022 (*CLEF 2022 Working Notes*, CEUR-WS vol. 3180) is the directly comparable precedent for historical NER. ⚠️ confirm HIPE-2022 explicitly reports 95% bootstrap CI before citing.
- Statistical testing and CI norms in NLP: Dror et al. (2018), "Deep Dominance", *ACL 2018*; Søgaard et al. (2014), "Simple, Robust Methods for Statistical Testing in NLP".

---

## 5. Binding constraint for sample size

Because TITLE prevalence is ~100%, F1 estimates are stable at relatively low n per stratum. The binding constraint is **per-era TITLE F1 reliability** — enough records per stratum to detect a meaningful drop in TITLE F1 between eras.

PERSON on pre-1700 is the secondary constraint: ~70% prevalence in that stratum, but only ~100 pre-1700 records in the current gold sample → ~70 PERSON instances → ±8–10 pp CI. This is marginal for fine-grained comparison but sufficient to detect gross failures (F1 < 0.55).

**Implication for allocation:**

- Modern and 19th-c sample size is driven by TITLE F1 reliability alone — needs fewer records than previously assumed
- Pre-1700 should be oversampled, driven by PERSON fallback reliability
- 1700–1800 is the ambiguous case for PERSON (transitional period for dc:creator availability); treat similarly to pre-1700

**The current allocation table in sr08_gold-set-composition.md §2.2 was not derived from corpus proportions or CI targets — the numbers were round-number design judgments.** They need to be replaced.

---

## 6. What needs to be computed to finalise allocation

1. ~~Fix the TITLE F1 usability threshold~~ — resolved: see §3
2. **Pull actual corpus cell sizes** (era × tier) from the corpus — current targets were guesses
3. **Compute minimum per-stratum record counts** from target CI width and expected entity prevalence per stratum
4. **Cap at corpus availability** and redistribute surplus
5. **Update the allocation table** in sr08_gold-set-composition.md §2.2 with derived numbers and documented rationale

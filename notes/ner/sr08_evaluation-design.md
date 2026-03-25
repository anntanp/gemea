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

**Author-before-title convention (pre-1700):** the placement of the author's name or credential before the title proper on early modern title pages is documented in historical bibliography. Candidate citations — verify before using:
- Gaskell, P. (1972). *A New Introduction to Bibliography.* Oxford: Clarendon Press. ⚠️ Standard reference for hand-press period (c. 1500–1800) title page conventions; verify specific section.
- Reske, C. (2015). *Die Buchdrucker des 16. und 17. Jahrhunderts im deutschen Sprachgebiet.* Wiesbaden: Harrassowitz. ⚠️ German-specific; less certain it addresses title page layout explicitly.
- Willer et al. (2010) — checked in full; does not address pre-ISBD title page conventions. Not a valid citation for this claim.

**The current allocation table in sr08_gold-set-composition.md §2.2 was not derived from corpus proportions or CI targets — the numbers were round-number design judgments.** They need to be replaced.

---

## 6. What needs to be computed to finalise allocation

1. ~~Fix the TITLE F1 usability threshold~~ — resolved: see §3
2. **Pull actual corpus cell sizes** (era × tier) from the corpus — current targets were guesses
3. **Compute minimum per-stratum record counts** from target CI width and expected entity prevalence per stratum
4. **Cap at corpus availability** and redistribute surplus
5. **Update the allocation table** in sr08_gold-set-composition.md §2.2 with derived numbers and documented rationale

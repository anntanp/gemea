# Reference Note — HIPE-2022 Extended Overview

**Citation:** Ehrmann, M., Romanello, M., Najem-Meyer, S., Doucet, A., & Clematide, S. (2022). Extended Overview of HIPE-2022: Named Entity Recognition and Linking in Multilingual Historical Documents. *CLEF 2022 Working Notes*, CEUR-WS Vol. 3180, paper-83.

**Note:** A condensed version exists as a separate paper, sometimes cited as "HIPE-2022: Naming the Past" — that is a different document. This note covers the extended overview.

---

## 1. Core claim

HIPE-2022 is the second edition of the HIPE shared task for NER and entity linking (EL) in multilingual historical documents. The central research question is **transferability** of NE processing approaches across languages, time periods, document types, and annotation tag sets.

---

## 2. Datasets

Six NE-annotated datasets covering ca. 200 years (18C–20C):

| Alias | Type | Languages |
|---|---|---|
| hipe2020 | historical newspapers | de, fr, en |
| newseye | historical newspapers | de, fi, fr, sv |
| sonar | historical newspapers (Berlin State Library) | de |
| letemps | historical newspapers | fr |
| topres19th | historical newspapers | en |
| ajmc | classical commentaries (19C) | de, en, fr |

Total corpus: ~2.3M tokens (2,211,449 newspaper + 111,218 commentaries), ~78,000 entity mentions across 5 entity typologies.

Entity types vary by dataset. Universal types (pers, loc, org) appear in all datasets except topres19th. The `ajmc` dataset adds domain-specific types: **work** (work.primlit, work.seclit, work.fragm), scope, object, date — the closest analogue to TITLE in GeMeA.

---

## 3. Evaluation

- **Tasks:** NERC-Coarse, NERC-Fine, Entity Linking (EL)
- **Metric:** micro Precision, Recall, F1-score
- **Regimes:**
  - **Strict:** exact type + boundary match (equivalent to exact span match)
  - **Fuzzy:** exact type + overlapping boundaries
- **No confidence intervals reported.** Results are point estimates only; no bootstrap CI or any other CI method is used.

---

## 4. Results relevant to GeMeA

German NERC-Coarse strict F1 (Table 7, best system per dataset):

| Dataset | Best strict F1 (de) | Notes |
|---|---|---|
| hipe2020 | 0.794 (L3I) | 19C–20C Swiss/Luxembourgish newspapers |
| sonar | 0.529 (Aauzh) | 19C–20C Berlin State Library newspapers |
| newseye | 0.477 (Neur-BSL) | 19C–20C German newspapers |
| ajmc | 0.934 (L3I) | 19C classical commentaries — high mention overlap train/test |

Neural baseline (XLM-R_BASE fine-tuned per dataset) German strict F1: hipe2020 0.703, sonar 0.307, newseye 0.477.

**For GeMeA benchmarking:** hipe2020-de and sonar-de are the most comparable (historical German, OCR noise). Best system range for these two combined: **0.307–0.794** strict; baseline range: **0.307–0.703**. The ajmc `work` type is closest to a TITLE entity but scores high (0.93+) partly due to train/test mention overlap (~30%).

---

## 5. Limitations as a GeMeA benchmark

- HIPE entity types are person, location, organisation — not bibliographic work titles. The `work` type in ajmc is the closest analogue but covers primary/secondary literature references in commentaries, not bare title strings.
- HIPE documents are newspaper articles and commentaries with multi-sentence context; GeMeA input is a single title string.
- No bootstrap CI reported — cannot cite HIPE-2022 as a source for the 95% bootstrap CI convention.
- sonar has no train set (dev + test only), which depresses scores and limits comparability.

---

## 6. Citation use in GeMeA notes

- **Valid:** cite for F1 ceiling on historical German NER (strict regime, hipe2020-de: 0.703–0.794); cite for exact span match as standard NERC evaluation protocol.
- **Not valid:** cite for bootstrap CI convention (not used in HIPE-2022).

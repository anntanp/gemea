# GeMeA — Related Literature

Two tracks for the ISWC 2026 Resource Track paper.

---

## Track A — Library Science & Knowledge Organization

Covers: ISBD/RDF, FRBR/LRM, EDM, cultural heritage KGs, linked library data, bibliographic metadata standards.

| File | Reference | Relevance |
|------|-----------|-----------|
| [artkb-eswc2026.md](artkb-eswc2026.md) | Blanco et al. 2026 — ArtKB (ESWC 2026) | Closest comparable CH KG; differentiation anchor |
| [willer2010-isbd-semantic.md](willer2010-isbd-semantic.md) | Willer, Dunsire & Bosančić 2010 — ISBD and the Semantic Web | ISBD RDF namespace; ISBD-AP; foundational for mocho alignment |

**To add:**
- Europeana Data Model (EDM) spec / Doerr et al.
- FRBRoo / LRM (IFLA 2017)
- CIDOC-CRM
- DDB / linked.swissbib / other national aggregator KGs
- QLever / Bast et al.

---

## Track B — NER: Historical Texts & LLM Methods

Covers: historical NER benchmarks, bibliographic NER, LLM-assisted annotation, NuNER / GLiNER zero-shot NER.

| File | Reference | Relevance |
|------|-----------|-----------|
| — | Ehrmann et al. 2022 — HIPE-2022 | Historical NER benchmark; IAA metric precedent; cited in sr03, sr08 |
| — | Benikova et al. 2014 — GermEval 2014 | German NER benchmark; PER label precedent |
| — | Zhan et al. 2026 — Generative NER | LLM-based NER; zero-shot vs fine-tuned gap (~88 vs ~93 F1 on CoNLL2003) |
| — | Zaratiana et al. 2023 — GLiNER | Zero-shot span extraction; alternative to NuNER |
| — | NuNER Zero (Carbonell et al.) | Compact zero-shot encoder NER; SR-09 baseline |

**To add:**
- Straková et al. (historical multilingual NER fine-tuning)
- Prange et al. (bibliographic NER / title parsing)
- Snow et al. 2008 (crowdsourced annotation quality)
- Artstein & Poesio 2008 (IAA survey)
- Pustejovsky & Stubbs 2012 (annotation best practice)

---

## Cross-cutting (cite in both tracks)

| Topic | Notes |
|-------|-------|
| SPARQL injection / security | owasp-security.md; cite in §5 DevOps |
| Wilson CI | Wilson 1927, Agresti & Coull 1998, Brown et al. 2001 — cited in sr03 §8.4 |

# GeMeA — German Memory Atlas

A knowledge graph browser for the German Digital Library (DDB).

**Track:** ISWC 2026 Resource Track
**Status:** In development

---

## Abstract

> To be written.

---

## What it is

GeMeA exposes 65 million cultural heritage objects from the DDB as a navigable knowledge graph. It provides keyword search, faceted browsing, entity pages, graph visualization, a map view, a timeline, and a public SPARQL endpoint.

**Pipeline:** DDB JSON-LD → [rdf2jsonld](../rdf2jsonld/) → `link_gnd_works.py` (GND Werk linking) → [mocho](../mocho/) (RDA normalization) → QLever + Elasticsearch → GeMeA

---

## Repository Layout

```
gemea/
├── paper/          ISWC 2026 Resource Track paper (LaTeX/LNCS)
├── ingest/         Phase 1 — ETL: mocho RDF → QLever + Elasticsearch
├── frontend/       Phase 3 — Next.js web application
├── docker/         Phase 4 — Docker Compose, Nginx, self-hosting docs
├── api/            Phase 2 — FastAPI backend
├── notes/          Spec, architecture, roadmap, paper outline
├── data/           Raw and processed data
├── scripts/        Standalone ops scripts
├── experiments/    Evaluation runs (for paper quality section)
└── resource/       Published artifact metadata
```

---

## Notes

### Project fundamentals

| File | Content |
|------|---------|
| `notes/spec.md` | Requirements, scope, success criteria |
| `notes/architecture.md` | System architecture and component interactions |
| `notes/roadmap.md` | Phase-by-phase plan (0a → 0 → 1 → 1b → 3 → 4 → 2) |
| `notes/priorities.md` | Current priorities and blockers |

### Phase 0a — NER for title parsing

| File | Content |
|------|---------|
| `notes/ner-bibliographic.md` | NER model spec; FRBR-organized label definitions; fine-tuning path |
| `notes/ner/silver-dataset-pipeline.md` | Silver-label pipeline framework and status |
| `notes/ner/sr01_isbd-field-rating.md` | ISBD field detection spec and silver candidate stratification |
| `notes/ner/sr01_isbd-field-rating-adr.md` | ADR: tier design and flag inclusion/exclusion decisions |
| `notes/ner/sr01_isbd-applicability.md` | ISBD applicability analysis on DDB corpus |
| `notes/ner/sr01_isbd-title-analysis.md` | Title string analysis supporting SR-01 |
| `notes/ner/sr03_silver-label-fp-review.md` | Per-field false-positive rates (200-record sample) |
| `notes/ner/sr04_translator-person-disambiguation.md` | `f_person` sub-classification into `f_resp_*` flags |
| `notes/ner/sr05_trailing-period-noise.md` | Trailing `.` as standalone silver signal — excluded (93% FP) |
| `notes/ner/sr05_abbreviations.md` | Abbreviation handling in ISBD parsing |
| `notes/ner/sr06_historical-scope.md` | Language scope: Early Modern German primary; Latin stratum not needed |
| `notes/ner/sr08_gold-set-composition.md` | Gold set stratification plan (~500 records) |
| `notes/ner/sr08_annotation-guide.md` | NER annotation guide for human and LLM annotators |
| `notes/ner/sr08_label-design-rationale.md` | Rationale for label name choices (PERSON, OTHER_TITLE, PARALLEL_TITLE) with ISBD citations |
| `notes/ner/sr10_de-titles-distribution.md` | `DF_DE_TITLES` provenance and token-length distribution |
| `notes/ner/sr10_title-length-thresholds.md` | Title length thresholds for stratification |
| `notes/ner/sr10_tracing-df-de-titles.md` | Tracing `DF_DE_TITLES` back to DDB source fields |
| `notes/ner/sr11_labeling-strategy.md` | LLM-assisted vs. manual labeling strategy |
| `notes/ner/sr12_field-level-weighting.md` | Field-level weighting in NER evaluation |
| `notes/ner/ref_gliner-nunerzero-comparison.md` | Reference: GLiNER vs. NuNER Zero comparison |
| `notes/ner/ref_zhan2026-generative-ner.md` | Reference: generative NER (Zhan 2026) |

### Phase 0 — Data acquisition and conversion

| File | Content |
|------|---------|
| `notes/gnd-linking-spec.md` | Full spec for `link_gnd_works.py` (title extraction → GND SPARQL → scoring) |
| `notes/gnd-linking-plan.md` | Implementation plan and step-by-step design |
| `notes/gnd-linking-adr.md` | ADRs: match predicate choice, query patterns, open questions |
| `notes/gnd-title-extraction.md` | Title extraction design (ISBD rules + NER fallback) |
| `notes/mocho-alignment.md` | mocho.owl alignment status and integration notes |

### Phase 1 — Ingest

| File | Content |
|------|---------|
| `notes/elasticsearch-index.md` | ES index mapping: German analyzer, GeoPoint, type/sector facets |
| `notes/triplestore-comparison.md` | QLever vs. Virtuoso vs. Jena — decision rationale |
| `notes/gnd-qlever-setup.md` | QLever setup and index configuration notes |

### Phase 3 — Frontend

| File | Content |
|------|---------|
| `notes/graphviz-dynamic-expansion.md` | Cytoscape.js dynamic graph expansion design |

### Phase 4 — DevOps

| File | Content |
|------|---------|
| `notes/owasp-security.md` | OWASP checklist for SPARQL injection, input sanitization, headers |

### Paper (ISWC 2026)

| File | Content |
|------|---------|
| `notes/paper-outline.md` | Section outline and argument structure |
| `notes/literature/` | Related work annotations |

### Reference and background

| File | Content |
|------|---------|
| `notes/ddb-objects.md` | DDB EDM object structure and field inventory |
| `notes/nlp-tasks.md` | NLP task inventory across the pipeline |
| `notes/future-work.md` | Post-v1 ideas and v2 features |
| `notes/review-checklist.md` | Pre-submission review checklist |

---

## ISWC 2026 Deadlines

| Milestone | Date |
|-----------|------|
| Abstract submission | 2 May 2026 |
| Full paper (8–15 pp) | 7 May 2026 |
| Rebuttal | 11–18 June 2026 |
| Notification | 16 July 2026 |
| Camera-ready | 6 August 2026 |
| Conference | 27–29 October 2026 |

---

## Resource

| Field | Value |
|-------|-------|
| Persistent URI | TBD (w3id or Zenodo DOI) |
| License (data) | CC BY 4.0 |
| License (code) | TBD (MIT or Apache 2.0) |
| SPARQL endpoint | TBD |
| Data download | TBD |

---


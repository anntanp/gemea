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

**Pipeline:** DDB JSON-LD → [rdf2jsonld](../rdf2jsonld/) → [mocho](../mocho/) (RDA normalization) → Virtuoso + Elasticsearch → GeMeA

---

## Repository Layout

```
gemea/
├── paper/          ISWC 2026 Resource Track paper (LaTeX/LNCS)
├── ingest/         Phase 1 — ETL: mocho RDF → Virtuoso + Elasticsearch
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

## Compile the Paper

```bash
cd paper
pdflatex 00-main && bibtex 00-main && pdflatex 00-main && pdflatex 00-main
```

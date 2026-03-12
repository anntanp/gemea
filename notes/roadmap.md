# GeMeA — Roadmap

Phase order: **0 → 1 → 1b → 3 → 4 → 2**

---

## Phase 0 — Data Acquisition and Conversion

**Goal:** Obtain the full DDB dataset and produce mocho-normalized N-Triples ready for loading into QLever.

**Output:** N-Triples files (one per provider) in `data/raw/`, suitable as direct input to Phase 1.

### Background

The DDB exposes its metadata as JSON-LD files following the Europeana Data Model (EDM). Two existing external tools handle the conversion pipeline:

- **rdf2jsonld** (`../rdf2jsonld/`) — converts DDB JSON-LD to W3C-compliant RDF/JSON; repairs URI malformations; runs in parallel per provider batch
- **mocho** (`../mocho/`) — ontology alignment tool; maps EDM predicates and classes to RDA/FRBR terms; outputs N-Triples or Turtle

GeMeA does not own these tools. Phase 0 is about **driving** them correctly on the full DDB corpus and validating their output before Phase 1 begins.

### Deliverables

- [ ] `scripts/download_ddb.sh` — fetch full DDB JSON-LD dump from the DDB OAI-PMH feed or bulk export; organize by provider ID under `data/raw/jsonld/`
- [ ] `scripts/run_rdf2jsonld.sh` — invoke rdf2jsonld in parallel over all provider batches; output to `data/raw/rdf-json/`
- [ ] `scripts/run_mocho.sh` — invoke mocho over rdf2jsonld output; output N-Triples per provider to `data/raw/ntriples/`
- [ ] `ingest/validate_rdf.py` — sanity checks on mocho output: triple count per provider, required predicates present (`edm:ProvidedCHO`, `dc:title`, `edm:isShownAt`), URI well-formedness
- [ ] `ingest/tests/test_validate_rdf.py` — unit tests for validation logic on fixture files

### Milestone

All 65M DDB objects converted to N-Triples; `validate_rdf.py` passes with zero critical errors; triple count and provider coverage logged to `data/processed/conversion_report.json`.

---

## Phase 1 — Ingest

**Goal:** Get all 65M DDB objects into QLever and Elasticsearch.

### Deliverables
- [ ] `ingest/load_qlever.py` — build QLever index from N-Triples (`qlever index`); named graphs per provider
- [ ] `ingest/index_es.py` — Elasticsearch document builder
- [ ] `ingest/build_docs.py` — assemble ES docs via SPARQL over QLever
- [ ] `ingest/validate.py` — post-ingest integrity checks
- [ ] `ingest/tests/` — pytest: unit (converters, doc builders) + integration (real ES + QLever)
- [ ] `scripts/ingest_all.sh` — end-to-end ingest driver
- [ ] Elasticsearch index mapping (German analyzer, GeoPoint, keyword facets)
- [ ] QLever index config tuned for dataset scale (`Mmap`, `num-threads`)

### Milestone
Full dataset loaded; SPARQL queries return correct results on sample queries. ES index build is **blocked** until Phase 1b completes.

---

## Phase 1b — GND Enrichment

**Goal:** Link unresolved agents and work titles to GND authority records; write enrichment triples back into QLever before building the Elasticsearch index.

**Depends on:** Phase 1 (QLever loaded). **Blocks:** `build_docs.py` + `index_es.py` in Phase 1.

### Background

The DDB EDM records already contain GND URIs for many agents (`d-nb.info/gnd/...`). Phase 1b handles the remainder:
- **Persons**: agents without GND URIs — link via name string matching against GND authority records
- **Work titles**: `ProvidedCHO` titles → GND *Werktitel* (work title authority records) — enables FRBR Work-level grouping, consistent with mocho's RDA/FRBR normalisation

All new linking triples are written to a dedicated named graph `http://gemea.ddb.de/graph/gnd-enrichment`, keeping them separate from the source data and allowing re-running without touching the original load.

### GND lookup tool: lobid-gnd API

lobid-gnd (`https://lobid.org/gnd`) is the recommended tool — RESTful, JSON-LD responses, free, maintained by hbz. Supports:
- Person lookup: `GET /gnd/search?q=label:"{name}"&filter=type:Person`
- Work lookup: `GET /gnd/search?q=label:"{title}"&filter=type:Work`
- Direct URI resolution: `GET /gnd/{id}.json`

Linking predicate: `owl:sameAs` for high-confidence matches; `skos:closeMatch` for approximate matches.

### Deliverables

- [ ] `ingest/link_gnd_agents.py`
  - Query Virtuoso for all `edm:Agent` URIs without a `d-nb.info/gnd/` URI
  - Batch-lookup names against lobid-gnd API (Person + CorporateBody types)
  - Score candidates (exact label match → `owl:sameAs`; fuzzy → `skos:closeMatch` with confidence score)
  - Write triples to `gnd-enrichment` named graph
- [ ] `ingest/link_gnd_works.py`
  - Query Virtuoso for `edm:ProvidedCHO` titles without a GND Werktitel link
  - Lookup against lobid-gnd (type: `Work`), filtered by language (`de`) and associated agent GND URI where available
  - Write triples to `gnd-enrichment` named graph
- [ ] `ingest/enrichment_report.py`
  - Coverage statistics: agents linked (%), works linked (%), breakdown by provider
  - Match quality breakdown: exact / approximate / unresolved
  - Output: JSON report + summary logged to stdout
- [ ] `ingest/tests/test_gnd_linking.py`
  - Unit: name normalisation, candidate scoring, triple generation
  - Integration: mock lobid API responses; verify correct triples written
- [ ] `scripts/run_gnd_enrichment.sh` — end-to-end driver for both scripts + report
- [ ] Update `build_docs.py` to include GND URIs in ES documents (`agent.gnd_uri`, `cho.gnd_work_uri`)

### Pipeline position

```
load_qlever.py  (Phase 1)
      │
      ▼
link_gnd_agents.py  ──▶  QLever: gnd-enrichment graph
link_gnd_works.py   ──▶  QLever: gnd-enrichment graph
      │
      ▼
build_docs.py + index_es.py  (Phase 1, now runs with enriched data)
```

### Milestone
≥ 80% of agents with name labels linked to GND; enrichment report written; ES documents include GND URIs.

---

## Phase 3 — Frontend

**Goal:** Working web UI, initially against mock API responses.

### Deliverables
- [ ] Next.js app scaffolded (`frontend/`)
- [ ] `SearchBar` + debounced input
- [ ] `/search` page: results list + `FacetSidebar` + pagination
- [ ] `/item/[id]` page: metadata panel + thumbnail + placeholder for graph viz
- [ ] `/agent/[id]`, `/place/[id]`, `/timespan/[id]` entity pages
- [ ] `GraphViz` component (Cytoscape.js) — 1-hop neighborhood
- [ ] `MapView` component (Leaflet + OSM) — geo-referenced objects + clustering
- [ ] `Timeline` component (D3 histogram) — object count by year
- [ ] `/map` and `/explore` pages
- [ ] Responsive layout (Tailwind; mobile + desktop)
- [ ] Content negotiation headers on entity page routes
- [ ] Mock API fixtures for development without live backend
- [ ] `frontend/__tests__/` — Jest + RTL: all components
- [ ] `frontend/e2e/` — Playwright: search → results → entity page; map loads; SPARQL endpoint

### Milestone
Full UI functional against mock data; all pages render correctly on mobile and desktop.

---

## Phase 4 — DevOps

**Goal:** Containerized team deployment with security hardening. Self-hosting for external users is v2.

### Deliverables
- [ ] `docker/docker-compose.yml` — all services (QLever, Elasticsearch, Redis, API, frontend, Nginx)
- [ ] `docker/nginx/nginx.conf` — reverse proxy, TLS, security headers (CSP, HSTS, X-Frame-Options)
- [ ] `.env.example` — all config vars documented; no hardcoded defaults
- [ ] Health check endpoints for all services (`/health`)
- [ ] Rate limiting config (Nginx: `/sparql` 10 req/s, `/search` 50 req/s)
- [ ] Structured logging (JSON) for API + Nginx

### Security checklist (OWASP)
- [ ] A03: SPARQL injection — parameterized templates; UPDATE/INSERT/DELETE blocked at proxy
- [ ] A03: Search input — sanitized before ES query construction
- [ ] A04: Rate limiting — token bucket on `/sparql` and `/search`
- [ ] A05: ES not publicly exposed; QLever admin port firewall-blocked
- [ ] A05: Security headers — CSP, HSTS, X-Frame-Options, Referrer-Policy via Nginx
- [ ] A06: `pip-audit` + `npm audit` in CI; Dependabot enabled
- [ ] A09: Structured logs; no PII; error alerting
- [ ] A10: SPARQL federated query endpoint whitelist

### Milestone
Team instance deployed at public URL; all services healthy; security headers verified.

---

## Phase 2 — API

**Goal:** Wire frontend to live QLever and Elasticsearch; replace mocks.

### Deliverables
- [ ] FastAPI app (`api/`)
- [ ] `GET /search` — Elasticsearch with facets, highlighting, pagination
- [ ] `GET /suggest` — autocomplete
- [ ] `GET /item/{id}`, `/agent/{id}`, `/place/{id}`, `/timespan/{id}` — QLever SPARQL
- [ ] `GET /sparql` — read-only QLever proxy with rate limiting
- [ ] `POST /graphql` — GraphQL schema over RDA/EDM entities (strawberry); resolvers backed by SPARQL
- [ ] `GET /health`
- [ ] Redis caching middleware
- [ ] Content negotiation: HTML / Turtle / JSON-LD on entity endpoints
- [ ] OpenAPI spec auto-generated; matches frontend expectations
- [ ] `api/tests/unit/` — pytest: query builders, pagination, sanitization
- [ ] `api/tests/integration/` — pytest + testcontainers: real ES + mock QLever
- [ ] `api/tests/contract/` — response shapes against OpenAPI spec

### Milestone
Frontend wired to live API; all pages functional with real data; all tests pass.

---

---

## v2 Features (post-v1)

| Feature | Component | Notes |
|---------|-----------|-------|
| **Self-hosting** | DevOps | `docker-compose.lite.yml` (100K objects, <8 GB RAM) + `docker-compose.full.yml` (≥64 GB RAM, ≥1 TB disk); `scripts/download_data.sh`; `docker/docs/self-hosting.md` |
| Text2SPARQL | API `POST /nl-search` | NL → SPARQL via LLM + entity resolution (see ArtKB pattern) |
| Visual search | Qdrant + API `POST /search/image` | Embed thumbnails with CLIP/SwinV2; image-to-image + text-to-image |
| Object storage | MinIO | Cache DDB thumbnails locally |
| ODRL rights | Ingest + triplestore | Per-item licensing as machine-readable ODRL triples |
| Wikidata enrichment | Ingest | Link GND agents/places to Wikidata entities at ingest time |
| Real-time DDB sync | Ingest pipeline | Incremental update from DDB OAI-PMH feed |

---

## Paper Milestones

| Date | Milestone |
|------|-----------|
| 2 May 2026 | Abstract submitted |
| 7 May 2026 | Full paper submitted (8–15 pp, LNCS) |
| 11–18 Jun 2026 | Rebuttal period |
| 16 Jul 2026 | Notification |
| 6 Aug 2026 | Camera-ready |
| 27–29 Oct 2026 | ISWC 2026 conference |

# GeMeA — Roadmap

Phase order: **0a → 0 → 1 → 1b → 3 → 4 → 2**

---

## Phase 0a — NER Training Data for Title Parsing

**Goal:** Prepare silver-labeled training data for the NER fallback in `link_gnd_works.py`. The NER model must be evaluated (and trained if zero-shot is insufficient) before `link_gnd_works.py` can run reliably on the full corpus.

**Blocks:** Phase 0 (`link_gnd_works.py` Step 2 — NER fallback)

**Output:** `data/processed/isbd_field_ratings.csv` with per-record field presence flags and silver tier; NER model evaluation report; decision on whether to use NuNER Zero zero-shot or fine-tune.

### Context

`link_gnd_works.py` uses a two-step title extraction strategy:
1. Rule-based ISBD parser (covers ~28% of records where ISBD punctuation is present)
2. NER fallback for the remaining ~72% (the majority path)

Phase 0a produces the data and model needed for Step 2. It is a distinct NLP subtask separate from GND linking.

### Deliverables

- [ ] `scripts/rate_isbd_fields.py` — rate all 4.47M titles in `DF_DE_TITLES` for the presence of TITLE, OTHER_TITLE, PERSON, PARALLEL_TITLE, EDITION, PUBLISHER, PLACE, YEAR, SERIES, VOLUME using ISBD punctuation rules; output `data/processed/isbd_field_ratings.csv` with `silver_tier` column
  - Tier 2 (structural): `. -` area separator present + PERSON + ≥1 Manifestation field — best multi-field silver candidates
  - Tier 1 (heuristic): `n_fields ≥ 3` or `(PERSON + YEAR)` — usable, lower confidence
  - See `notes/ner/sr01_isbd-field-rating.md` for full spec and `notes/ner/sr01_isbd-field-rating-adr.md` for ADR
- [ ] Silver candidate selection — sample stratified by tier, era (`dc_type`), and field combination; target ~5K records for NER evaluation / training
- [ ] `scripts/build_silver_spans.py` — auxiliary-guided span extraction for silver dataset; inputs: `isbd_field_ratings.csv` + full DF_DE_TITLES (with `dc_publisher`, `dc_creator`, `dc_contributor`, `agents`); output: `data/processed/silver_spans.jsonl`
  - For each silver-tier record, extract span boundaries from the title string using ISBD area parsing (structural) or pattern matching (heuristic)
  - **PLACE / PUBLISHER enrichment**: take `dc_publisher` value and search for it as a substring in `title`; only label the span if found — span boundaries come from the title string (inference-consistent)
  - **PERSON enrichment**: match `dc_creator` / `dc_contributor` names against the post-` /` segment of the title; label if found
  - Output format: one JSON object per record — `{obj_id, title, spans: [{start, end, text, label}]}`
  - See `notes/ner/sr01_isbd-field-rating.md` → *Silver dataset improvement* for design rationale
- [ ] NuNER Zero evaluation — run zero-shot NER on 500 stratified fallback records (no ISBD markers); assess TITLE, PERSON precision on a manually checked gold set; see [ner-bibliographic.md](ner-bibliographic.md)
- [ ] **Decision gate**: if NuNER Zero precision ≥ threshold on gold set → done; else use LLM to label silver candidates and fine-tune `xlm-roberta-base`
- [ ] `notes/ner/sr01_isbd-field-rating.md` — spec for field detection methodology
- [ ] `notes/ner/sr01_isbd-field-rating-adr.md` — ADR for ISBD-based rating approach

### Pipeline position

```
DF_DE_TITLES_20240125b.pkl
      │
      ▼
rate_isbd_fields.py  →  data/processed/isbd_field_ratings.csv
      │
      ▼
build_silver_spans.py  ←  auxiliary columns (dc_publisher, dc_creator, agents)
      │                    (lookup in title string only — span boundaries from title)
      ▼
data/processed/silver_spans.jsonl  →  stratified NER evaluation set (~500 records)
      │
      ▼
NuNER Zero evaluation  →  precision/recall on gold set
      │
      ▼  [if precision sufficient]
NER model ready for link_gnd_works.py Step 2
      │
      ▼  [if fine-tuning needed]
LLM labeling → fine-tune xlm-roberta-base → evaluate → NER model ready
```

### Milestone

`isbd_field_ratings.csv` produced for all 4.47M records; NuNER Zero evaluated on gold set; NER model decision documented; `link_gnd_works.py` NER step has a validated model.

---

## Phase 0 — Data Acquisition and Conversion

**Goal:** Obtain the full DDB dataset, link titles to GND Werk, and produce mocho-normalized N-Triples ready for loading into QLever.

**Output:** N-Triples files (one per provider) in `data/raw/ntriples/`, suitable as direct input to Phase 1.

**⚠ External dependency:** mocho.owl is currently **WIP**. The full pipeline (rdf2jsonld → link_gnd_works → mocho) cannot run end-to-end until mocho.owl stabilizes. This is the single biggest risk to the May 7 deadline. Track mocho progress closely.

### Background

The DDB exposes its metadata as JSON-LD files following the Europeana Data Model (EDM). The conversion pipeline has three steps in order:

1. **rdf2jsonld** (`../rdf2jsonld/`) — converts DDB JSON-LD to W3C-compliant RDF/JSON; repairs URI malformations; runs in parallel per provider batch
2. **link_gnd_works.py** — links `dc:title` strings to GND Werk URIs via lobid-gnd API; the resulting triples are fed to mocho so it can group `edm:ProvidedCHO` instances into `mocho:Work` entities
3. **mocho** (`../mocho/`) — ontology alignment tool; uses GND Werk links to create `mocho:Work` groupings; maps EDM predicates and classes to RDA terms; outputs N-Triples or Turtle

GeMeA does not own rdf2jsonld or mocho. Phase 0 is about **driving** them correctly on the full DDB corpus and validating their output before Phase 1 begins.

### Deliverables

- [ ] `scripts/download_ddb.sh` — fetch full DDB JSON-LD dump from the DDB OAI-PMH feed or bulk export; organize by provider ID under `data/raw/jsonld/`
- [ ] `scripts/run_rdf2jsonld.sh` — invoke rdf2jsonld in parallel over all provider batches; output to `data/raw/rdf-json/`
- [ ] `scripts/link_gnd_works.py` — link `dc:title` strings → GND Werk URIs; feeds mocho
  - Step 1: rule-based ISBD parser (split on ` / ` and `. - `) to extract clean title from messy `dc:title` strings
  - Step 2: NER fallback for records without ISBD punctuation (~72% — majority path); uses model validated in Phase 0a; labels: TITLE, PERSON, PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME — see [ner-bibliographic.md](ner-bibliographic.md)
  - Step 3: deduplicate `(title, author_gnd_uri)` pairs before API calls (~65M records → ~5–10M unique)
  - Step 4: lobid-gnd Werk lookup with author GND URI cross-reference; score candidates (`owl:sameAs` exact / `skos:closeMatch` fuzzy)
  - Output: per-CHO JSON with `raw_title`, `extracted_title`, `extraction_method`, `gnd_werk_uri`, `match_type`, `match_confidence` → `data/raw/gnd-works/`
  - See `notes/gnd-title-extraction.md` for full spec
- [ ] `scripts/run_mocho.sh` — invoke mocho over rdf2jsonld + GND Werk triples; output N-Triples per provider to `data/raw/ntriples/`
- [ ] `ingest/validate_rdf.py` — sanity checks on mocho output: triple count per provider, `mocho:Work` nodes present, required predicates (`edm:ProvidedCHO`, `dc:title`, `edm:isShownAt`), URI well-formedness
- [ ] `ingest/tests/test_validate_rdf.py` — unit tests for validation logic on fixture files

### Pipeline order

```
download_ddb.sh
      │
      ▼
run_rdf2jsonld.sh  →  data/raw/rdf-json/
      │
      ▼
link_gnd_works.py  →  data/raw/gnd-works/  (title → GND Werk URI)
      │
      ▼  (mocho reads both rdf-json/ + gnd-works/)
run_mocho.sh       →  data/raw/ntriples/   ⚠ blocked on mocho.owl stability
      │
      ▼
validate_rdf.py
```

### Milestone

All 65M DDB objects converted to N-Triples; `mocho:Work` nodes present for linked titles; `validate_rdf.py` passes with zero critical errors; triple count and provider coverage logged to `data/processed/conversion_report.json`.

---

## Phase 1 — Ingest

**Goal:** Get all 65M DDB objects into QLever and Elasticsearch.

### Deliverables
- [ ] `ingest/load_qlever.py` — build QLever index from N-Triples (`qlever index`); named graphs per provider
- [ ] `ingest/type_mapping.json` — maps raw `dc:type` strings → controlled vocabulary (literature, music, theater, film, painting, graphic, photography, architecture, sculpture, map, object)
- [ ] `ingest/sector_mapping.json` — maps provider IDs → DDB institutional sector (bibliothek, archiv, museum, mediathek, denkmal)
- [ ] `ingest/build_docs.py` — assemble ES docs via SPARQL over QLever; apply type + sector normalization
- [ ] `ingest/index_es.py` — Elasticsearch document builder
- [ ] `ingest/validate.py` — post-ingest integrity checks
- [ ] `ingest/tests/` — pytest: unit (converters, doc builders, type/sector mapping) + integration (real ES + QLever)
- [ ] `scripts/ingest_all.sh` — end-to-end ingest driver
- [ ] Elasticsearch index mapping (German analyzer, GeoPoint, `type` and `sector` as `keyword` facets)
- [ ] QLever index config tuned for dataset scale (`Mmap`, `num-threads`)

### Milestone
Full dataset loaded; SPARQL queries return correct results on sample queries. ES index build is **blocked** until Phase 1b completes.

---

## Phase 1b — GND Agent Enrichment

**Goal:** Link unresolved agents to GND authority records; write enrichment triples into QLever before building the Elasticsearch index.

**Depends on:** Phase 1 (QLever loaded). **Blocks:** `build_docs.py` + `index_es.py` in Phase 1.

**Note:** GND title/Work linking (`link_gnd_works.py`) was moved to Phase 0 — it must run before mocho. Phase 1b covers only agent linking, which queries QLever and can run post-load.

### Background

The DDB EDM records already contain GND URIs for many agents (`d-nb.info/gnd/...`). Phase 1b handles the remainder:
- **Persons**: agents without GND URIs — link via name string matching against GND authority records
- **CorporateBodies**: institutions and organizations without GND URIs

All new linking triples are written to the named graph `http://gemea.ddb.de/graph/gnd-enrichment`, keeping them separate from source data and allowing re-running without touching the original load.

### GND lookup tool: lobid-gnd API

lobid-gnd (`https://lobid.org/gnd`) — RESTful, JSON-LD responses, free, maintained by hbz:
- Person lookup: `GET /gnd/search?q=label:"{name}"&filter=type:Person`
- CorporateBody lookup: `GET /gnd/search?q=label:"{name}"&filter=type:CorporateBody`
- Direct URI resolution: `GET /gnd/{id}.json`

Linking predicate: `owl:sameAs` for high-confidence matches; `skos:closeMatch` for approximate matches.

### Deliverables

- [ ] `ingest/link_gnd_agents.py`
  - Query QLever for all `edm:Agent` URIs without a `d-nb.info/gnd/` URI
  - Batch-lookup names against lobid-gnd API (Person + CorporateBody types)
  - Score candidates (exact label match → `owl:sameAs`; fuzzy → `skos:closeMatch` with confidence score)
  - Write triples to `gnd-enrichment` named graph in QLever
- [ ] `ingest/enrichment_report.py`
  - Coverage statistics: agents linked (%), works linked (from Phase 0), breakdown by provider
  - Match quality breakdown: exact / approximate / unresolved
  - Output: JSON report + summary logged to stdout
- [ ] `ingest/tests/test_gnd_linking.py`
  - Unit: name normalisation, candidate scoring, triple generation
  - Integration: mock lobid API responses; verify correct triples written
- [ ] `scripts/run_gnd_enrichment.sh` — driver for agent linking + report
- [ ] Update `build_docs.py` to include GND URIs in ES documents (`agent.gnd_uri`, `cho.gnd_work_uri`)

### Pipeline position

```
load_qlever.py  (Phase 1)
      │
      ▼
link_gnd_agents.py  ──▶  QLever: gnd-enrichment graph
      │
      ▼
build_docs.py + index_es.py  (Phase 1, now runs with enriched data)
```

### Milestone
≥ 80% of agents with name labels linked to GND; enrichment report written; ES documents include `agent.gnd_uri`.

---

## Phase 3 — Frontend

**Goal:** Working web UI, initially against mock API responses.

### Deliverables
- [ ] Next.js app scaffolded (`frontend/`)
- [ ] `SearchBar` + debounced input
- [ ] `/search` page: results list + `FacetSidebar` + pagination
- [ ] `/item/[id]` page: metadata panel + thumbnail + placeholder for graph viz
- [ ] `/agent/[id]`, `/place/[id]`, `/timespan/[id]` entity pages
- [ ] `/work/[id]` FRBR Work page with `WEMIHierarchy` component — **conditional**: same as API condition above
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
- [ ] `GET /search` — Elasticsearch with facets (`type`, `sector`, place, institution, year), highlighting, pagination
- [ ] `GET /sectors` — list of DDB institutional sectors with object counts (ES aggregation)
- [ ] `GET /suggest` — autocomplete
- [ ] `GET /item/{id}`, `/agent/{id}`, `/place/{id}`, `/timespan/{id}` — QLever SPARQL
- [ ] `GET /work/{id}`, `/expression/{id}` — QLever SPARQL; FRBR Work/Expression hierarchy; **conditional**: verify mocho outputs `frbr:Work` / `frbr:Expression` nodes and Phase 1b coverage ≥ 70% before implementing
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

# GeMeA — Roadmap

Phase order: **0a → 0 → 1 → 1b → 3 → 4 → 2**

---

## Phase 0a — NER Training Data for Title Parsing

**Goal:** Prepare silver-labeled training data for the NER fallback in `link_gnd_works.py`. The NER model must be evaluated (and trained if zero-shot is insufficient) before `link_gnd_works.py` can run reliably on the full corpus.

**Blocks:** Phase 0 (`link_gnd_works.py` Step 2 — NER fallback)

**Output:** `data/processed/silver_spans.jsonl`; gold set (~500 annotated records); NER model evaluation report; decision on whether to use NuNER Zero zero-shot or fine-tune.

### Context

`link_gnd_works.py` uses a two-step title extraction strategy:
1. Rule-based ISBD parser (covers ~28% of records where ISBD punctuation is present)
2. NER fallback for the remaining ~72% (the majority path)

Phase 0a produces the data and model needed for Step 2. It is a distinct NLP subtask from GND linking, documented in `notes/ner-bibliographic.md` (model and label spec) and `notes/ner/silver-dataset-pipeline.md` (pipeline framework and status).

### Label set

Labels organised by FRBR level; see `notes/ner-bibliographic.md` §3 for full definitions.

**Work:** `TITLE`, `OTHER_TITLE`, `PERSON`
**Expression:** `TRANSLATOR`, `TRANSLATION`, `PARALLEL_TITLE`, `LANGUAGE`, `MEDIUM`
**Manifestation:** `EDITION`, `PUBLISHER`, `PLACE`, `YEAR`, `SERIES`, `VOLUME`

Silver label targets (viable from ISBD-derived signals): `TITLE`, `OTHER_TITLE`, `PERSON` (from `f_resp_person` only — see exclusions below), `YEAR`, `PUBLISHER`, `SERIES`, `VOLUME`. `TRANSLATOR` is not a viable silver target (0 true instances in 100-record sample; SR-04 resolved).

### Deliverables

- [x] `scripts/rate_isbd_fields.py` — rates all 4.47M titles in `DF_DE_TITLES` for ISBD field presence; outputs `data/processed/isbd_field_ratings.csv` with `silver_tier` column
  - Tier 2 (structural): `has_dot_dash AND f_resp_person AND ≥1 Manifestation field` — 4,613 records (0.1%)
  - Tier 1 (heuristic): `n_fields ≥ 3` OR `(f_person AND f_year)` — 335,524 records (7.5%)
  - Tier 0 (unrated): all others — 4,137,643 records (92.4%)
  - Spec: `notes/ner/sr01_isbd-field-rating.md`; ADR: `notes/ner/sr01_isbd-field-rating-adr.md`
- [x] Silver candidate selection spec — stratification by tier, era, `dc_type`, and field combination; see `notes/ner/sr01_isbd-field-rating.md`
- [x] Precision validation — per-field FP rates on 200-record stratified sample (SR-03); decisions:
  - **Excluded** (FP > 15%): `f_parallel` (~80% FP), `f_edition` (~83% FP), trailing `.` standalone signal (93% FP — SR-05)
  - **Sub-classified** (ambiguous signal): `f_person` → `f_resp_*` flags (SR-04): `f_resp_person` 35% (true author SoR), `f_resp_org` 19% (corporate body), `f_resp_editor` 5%, `f_resp_other` 41% (non-SoR FP)
  - **Accepted** (FP ≤ 15%): `f_year`, `f_other_title`, `f_publisher`, `f_series`, `f_volume`
- [x] `notes/ner/sr01_isbd-field-rating.md` — ISBD field detection spec
- [x] `notes/ner/sr01_isbd-field-rating-adr.md` — ADR for tier design and flag decisions
- [x] Historical language scope (SR-06) — 200-record stratified sample; Early Modern German 93%, Latin ~0.5%; **no Latin stratum needed** for gold set; Early Modern German (pre-1750) is the primary historical challenge. See `notes/ner/sr06_historical-scope.md`.
- [x] Corpus characterisation (SR-10) — `DF_DE_TITLES` provenance, token-length distribution (p25=4, p75=14), era-stratified length. See `notes/ner/sr10_de-titles-distribution.md`, `notes/ner/sr10_title-length-thresholds.md`.
- [ ] `scripts/build_silver_spans.py` — span extraction from accepted flags; inputs: `isbd_field_ratings.csv` + DF_DE_TITLES auxiliary columns (`dc_publisher`, `dc_creator`, `dc_contributor`, `agents`); output: `data/processed/silver_spans.jsonl`
  - PLACE / PUBLISHER enrichment: match `dc_publisher` value as substring in title; label only if found
  - PERSON enrichment: match `dc_creator` / `dc_contributor` names against post-` /` segment; use `f_resp_person` flag only (exclude `f_resp_org`, `f_resp_editor`, `f_resp_other`)
  - Output: `{obj_id, title, spans: [{start, end, text, label}]}`
- [ ] SR-07 — FRBR metric scope for paper: confirm which FRBR levels (Work only, or also Expression/Manifestation) the evaluation section covers; determines gold set label scope. Blocks SR-09.
- [ ] SR-09 — Gold set composition: ~500 manually annotated records stratified by era (modern / 19th c. / 1700–1800 / pre-1700), silver tier (2 / 1 / 0), `dc_type`, and title length; annotation guidelines must address pre-1750 author-before-title placement (systematic `f_person` false negative); no dedicated Latin stratum (SR-06). Blocked on SR-07. Blocks SR-08.
- [ ] SR-08 — NuNER Zero evaluation: run `numind/NuNerZero` zero-shot on 500 stratified fallback records; assess F1 per label and per era stratum on gold set. Blocked on SR-09.
- [ ] **Decision gate** (SR-08 output): NuNER Zero F1 ≥ threshold → use zero-shot; else LLM-label silver candidates and fine-tune `xlm-roberta-large` (primary) and `mdeberta-v3-base` (benchmark). See `notes/ner-bibliographic.md` §10 for recommended fine-tuning path.

### Pipeline position

```
DF_DE_TITLES_20240125b.pkl
      │
      ▼  [DONE]
rate_isbd_fields.py  →  data/processed/isbd_field_ratings.csv
      │
      ▼  [NEXT]
build_silver_spans.py  ←  auxiliary columns (dc_publisher, dc_creator, agents)
      │                    f_resp_person only; f_parallel / f_edition excluded
      ▼
data/processed/silver_spans.jsonl
      │
      ▼  [BLOCKED on SR-09]
Gold set construction (~500 manually annotated records, stratified)
      │
      ▼
NuNER Zero evaluation (SR-08)  →  F1 per label + per era stratum
      │
      ▼  [if F1 sufficient]
NER model ready for link_gnd_works.py Step 2
      │
      ▼  [if fine-tuning needed]
LLM labeling → fine-tune xlm-roberta-large → evaluate → NER model ready
```

### Milestone

`silver_spans.jsonl` built from accepted flags; gold set annotated (~500 records, stratified); NuNER Zero evaluated on gold set; NER model decision documented; `link_gnd_works.py` NER step has a validated model.

---

## Phase 0 — Data Acquisition and Conversion

**Goal:** Obtain the full DDB dataset, link titles to GND Werk, and produce mocho-normalized N-Triples ready for loading into QLever.

**Output:** N-Triples files (one per provider) in `data/raw/ntriples/`, suitable as direct input to Phase 1.

**⚠ External dependency:** mocho.owl is currently **WIP**. The full pipeline (rdf2jsonld → link_gnd_works → mocho) cannot run end-to-end until mocho.owl stabilizes. This is the single biggest risk to the May 7 deadline. Track mocho progress closely.

### Background

The DDB exposes its metadata as JSON-LD files following the Europeana Data Model (EDM). The conversion pipeline has three steps in order:

1. **rdf2jsonld** (`../rdf2jsonld/`) — converts DDB JSON-LD to W3C-compliant RDF/JSON; repairs URI malformations; runs in parallel per provider batch
2. **link_gnd_works.py** — links `dc:title` strings to GND Werk URIs via the DNB SPARQL endpoint (`sparql.dnb.de/api/dnbgnd`); the resulting triples are fed to mocho so it can group `edm:ProvidedCHO` instances into `mocho:Work` entities
3. **mocho** (`../mocho/`) — ontology alignment tool; uses GND Werk links to create `mocho:Work` groupings; maps EDM predicates and classes to RDA terms; outputs N-Triples or Turtle

GeMeA does not own rdf2jsonld or mocho. Phase 0 is about **driving** them correctly on the full DDB corpus and validating their output before Phase 1 begins.

### Deliverables

- [ ] `scripts/download_ddb.sh` — fetch full DDB JSON-LD dump from the DDB OAI-PMH feed or bulk export; organize by provider ID under `data/raw/jsonld/`
- [ ] `scripts/run_rdf2jsonld.sh` — invoke rdf2jsonld in parallel over all provider batches; output to `data/raw/rdf-json/`
- [ ] `scripts/link_gnd_works.py` — link `dc:title` strings → GND Werk URIs; feeds mocho
  - Step 1: rule-based ISBD parser (split on ` / ` and `. - `) to extract clean title from messy `dc:title` strings
  - Step 2: NER fallback for records without ISBD punctuation (~72% — majority path); uses model validated in Phase 0a; full label set: `TITLE, OTHER_TITLE, PERSON, TRANSLATOR, TRANSLATION, PARALLEL_TITLE, LANGUAGE, MEDIUM, EDITION, PUBLISHER, PLACE, YEAR, SERIES, VOLUME` — see `notes/ner-bibliographic.md`
  - Step 3: normalize extracted title (Unicode NFC → lowercase → strip diacritics*) → tokenize → remove stopwords → select 2–3 distinctive tokens; *OQ-01: confirm diacritic stripping does not hurt FILTER recall before enabling
  - Step 4: deduplicate `(extracted_title, author_gnd_uri)` pairs (~65M records → ~5–10M unique)
  - Step 5: SPARQL query against DNB endpoint (`https://sparql.dnb.de/api/dnbgnd`, SPARQL 1.1 only — `contains-word` not available); concurrency: `asyncio.Semaphore(10)`
    - **Pattern C with author** (when author GND URI available): `FILTER(LCASE(STR(?prefLabel)) = "{title}")` constrained by `VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }` and `?work ?authorPred <{author_gnd_uri}>`
    - **Pattern C title-only** (no author GND URI): same FILTER without author constraint
    - Target classes: `gndo:Work gndo:MusicalWork gndo:Manuscript` (IFLA LRM-E2 Work; Expression/Manifestation subclasses excluded)
  - Step 6: post-retrieval scoring — `skos:exactMatch` for exact + normalized matches; `skos:closeMatch` for fuzzy (Levenshtein ≤ 2); `owl:sameAs` not used (a DDB ProvidedCHO and GND Werk URI are not the same OWL individual)
  - Output: per-CHO JSON with `raw_title`, `extracted_title`, `extraction_method`, `author_gnd_uri`, `gnd_werk_uri`, `match_type`, `match_confidence` → `data/raw/gnd-works/`
  - Spec: `notes/gnd-linking-spec.md`; implementation plan: `notes/gnd-linking-plan.md`; ADR: `notes/gnd-linking-adr.md`
  - **Open questions**: OQ-01 (does `sparql.dnb.de` normalize Umlauts in FILTER? — test before enabling diacritic stripping); OQ-02 (actual rate limits — profile at concurrency=10); OQ-03 (add `gndo:variantNameForTheWork` UNION branch for higher recall?); OQ-04 (`gndo:composer`/`gndo:firstComposer` analogous to author predicates for MusicalWork?)
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

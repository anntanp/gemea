# GeMeA — Roadmap

Phase order: **1 → 3 → 4 → 2**

---

## Phase 1 — Ingest

**Goal:** Get all 65M DDB objects into Virtuoso and Elasticsearch.

### Deliverables
- [ ] `ingest/load_virtuoso.py` — bulk N-Triples load; named graphs per provider
- [ ] `ingest/index_es.py` — Elasticsearch document builder
- [ ] `ingest/build_docs.py` — assemble ES docs via SPARQL over Virtuoso
- [ ] `ingest/validate.py` — post-ingest integrity checks
- [ ] `ingest/tests/` — pytest: unit (converters, doc builders) + integration (real ES + Virtuoso)
- [ ] `scripts/ingest_all.sh` — end-to-end ingest driver
- [ ] Elasticsearch index mapping (German analyzer, GeoPoint, keyword facets)
- [ ] Virtuoso config tuned for dataset scale (memory, indexing)

### Milestone
Full dataset loaded; SPARQL and ES queries return correct results on sample queries.

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

**Goal:** Containerized, self-hostable stack with security hardening.

### Deliverables
- [ ] `docker/docker-compose.yml` — all services (Virtuoso, Elasticsearch, Redis, API, frontend, Nginx)
- [ ] `docker/docker-compose.lite.yml` — lite mode (100K objects, low RAM)
- [ ] `docker/nginx/nginx.conf` — reverse proxy, TLS, security headers (CSP, HSTS, X-Frame-Options)
- [ ] `.env.example` — all config vars documented; no hardcoded defaults
- [ ] `docker/docs/self-hosting.md` — full setup guide (lite + full mode)
- [ ] `scripts/download_data.sh` — fetch mocho-normalized RDF from public dump
- [ ] Health check endpoints for all services (`/health`)
- [ ] Rate limiting config (Nginx: `/sparql` 10 req/s, `/search` 50 req/s)
- [ ] Structured logging (JSON) for API + Nginx

### Security checklist (OWASP)
- [ ] A03: SPARQL injection — parameterized templates; UPDATE/INSERT/DELETE blocked at proxy
- [ ] A03: Search input — sanitized before ES query construction
- [ ] A04: Rate limiting — token bucket on `/sparql` and `/search`
- [ ] A05: ES not publicly exposed; Virtuoso admin firewall-blocked
- [ ] A05: Security headers — CSP, HSTS, X-Frame-Options, Referrer-Policy via Nginx
- [ ] A06: `pip-audit` + `npm audit` in CI; Dependabot enabled
- [ ] A09: Structured logs; no PII; error alerting
- [ ] A10: SPARQL federated query endpoint whitelist

### Milestone
`docker compose up` brings up the full stack from scratch; `docker compose -f docker-compose.lite.yml up` runs on a laptop.

---

## Phase 2 — API

**Goal:** Wire frontend to live Virtuoso and Elasticsearch; replace mocks.

### Deliverables
- [ ] FastAPI app (`api/`)
- [ ] `GET /search` — Elasticsearch with facets, highlighting, pagination
- [ ] `GET /suggest` — autocomplete
- [ ] `GET /item/{id}`, `/agent/{id}`, `/place/{id}`, `/timespan/{id}` — Virtuoso SPARQL
- [ ] `GET /sparql` — read-only Virtuoso proxy with rate limiting
- [ ] `POST /graphql` — GraphQL schema over RDA/EDM entities (strawberry); resolvers backed by SPARQL
- [ ] `GET /health`
- [ ] Redis caching middleware
- [ ] Content negotiation: HTML / Turtle / JSON-LD on entity endpoints
- [ ] OpenAPI spec auto-generated; matches frontend expectations
- [ ] `api/tests/unit/` — pytest: query builders, pagination, sanitization
- [ ] `api/tests/integration/` — pytest + testcontainers: real ES + mock Virtuoso
- [ ] `api/tests/contract/` — response shapes against OpenAPI spec

### Milestone
Frontend wired to live API; all pages functional with real data; all tests pass.

---

---

## v2 Features (post-v1)

| Feature | Component | Notes |
|---------|-----------|-------|
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

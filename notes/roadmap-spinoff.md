# GeMeA — Spinoff Roadmap: KG Construction Focus

**Scope:** Knowledge graph construction, ontology engineering, and information extraction. No REST API, no web frontend, no Elasticsearch. The resource artifact is the KG itself (QLever SPARQL endpoint + Zenodo dump + pipeline code).

**Paper angle:** Three interlocking contributions — (1) ISBD-guided silver dataset construction + NER pipeline for bibliographic title parsing, (2) GND entity linking over 65M DDB objects via DNB SPARQL, (3) mocho WEMI grouping. Provenance modelling (`provlm`) as a fourth contribution if the extension matures in time; otherwise a "Provenance Model" section adopting it as-is.

Phase order: **0a → 0 → 1 → 1b → 4**

---

## Phase 0a — NER Training Data for Title Parsing

*(Identical to main roadmap — see `roadmap.md` Phase 0a for full spec and current status.)*

**Status summary:**
- [x] `rate_isbd_fields.py` + `isbd_field_ratings.csv`
- [x] Precision validation (SR-03/04/05/06), corpus characterisation (SR-10)
- [ ] `build_silver_spans.py` — next
- [ ] SR-07 FRBR scope, SR-09 gold set, SR-08 NuNER Zero evaluation — SR-09 blocked on SR-07

---

## Phase 0 — Data Acquisition and Conversion

*(Identical to main roadmap — see `roadmap.md` Phase 0 for full spec.)*

**Key point:** `link_gnd_works.py` now uses DNB SPARQL endpoint (`sparql.dnb.de/api/dnbgnd`), not lobid-gnd. Open questions OQ-01 to OQ-04 must be resolved before full run.

---

## Phase 1 — Ingest (QLever only)

**Goal:** Load all 65M DDB objects into QLever.

### Deliverables
- [ ] `ingest/load_qlever.py` — build QLever index from N-Triples (`qlever index`); named graphs per provider
- [ ] `ingest/validate.py` — post-ingest integrity checks: triple count per provider, `mocho:Work` nodes present, required predicates, URI well-formedness
- [ ] `ingest/tests/` — pytest: unit (validators) + integration (real QLever)
- [ ] `scripts/ingest_all.sh` — end-to-end ingest driver
- [ ] QLever index config tuned for dataset scale (`Mmap`, `num-threads`)

### Milestone
Full dataset loaded into QLever; SPARQL queries return correct results on sample queries.

---

## Phase 1b — GND Agent Enrichment

**Goal:** Link unresolved agents to GND authority records; write enrichment triples into QLever before the endpoint goes public.

**Depends on:** Phase 1 (QLever loaded). **Blocks:** Phase 4 (public SPARQL endpoint should expose enriched data).

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

### Pipeline position

```
load_qlever.py  (Phase 1)
      │
      ▼
link_gnd_agents.py  ──▶  QLever: gnd-enrichment graph
      │
      ▼
public SPARQL endpoint (Phase 4, exposes enriched data)
```

### Milestone
≥ 80% of agents with name labels linked to GND; enrichment report written; GND URIs queryable via SPARQL.

---

## Phase 4 — Deployment

**Goal:** Expose the enriched KG as a publicly accessible SPARQL endpoint and publish the KG dump. Minimal footprint — QLever only, no API layer or frontend.

### Deliverables
- [ ] `docker/docker-compose.yml` — single QLever service; read-only SPARQL endpoint exposed on port 7001
- [ ] `docker/nginx/nginx.conf` — reverse proxy; TLS; rate limiting on `/sparql` (10 req/s); block SPARQL UPDATE/INSERT/DELETE at proxy
- [ ] `.env.example` — all config vars documented
- [ ] KG dump published to Zenodo (N-Triples, versioned); DOI recorded in `notes/dataset.md`
- [ ] `scripts/smoke_test.sh` — run 5 representative SPARQL queries against the live endpoint; assert non-empty results

### Security
- [ ] SPARQL injection: UPDATE/INSERT/DELETE blocked at Nginx
- [ ] QLever admin port firewall-blocked (not exposed publicly)
- [ ] Rate limiting on `/sparql`

### Milestone
QLever instance publicly reachable at stable URL; KG dump on Zenodo with DOI; smoke tests pass.

---

## v2 Features (post-v1)

| Feature | Notes |
|---------|-------|
| REST API | FastAPI; `GET /item/{id}`, `/agent/{id}`, `/work/{id}`; read-only QLever proxy; content negotiation (Turtle, JSON-LD) |
| GraphQL | strawberry; RDA/EDM entity schema; SPARQL-backed resolvers |
| Web UI | Next.js + Tailwind; search, facets, entity pages, graph viz (Cytoscape.js), map (Leaflet), timeline (D3) |
| Faceted search | Elasticsearch; German analyzer; `type` and `sector` keyword facets |
| `provlm` provenance layer | Attach `provlm:LMRefinement` triples to NER and entity linking steps; depends on `provlm` extension being published — see `notes/future-work.md` §1 |
| Wikidata enrichment | Link GND agents/places to Wikidata entities at ingest time |
| ODRL rights | Per-item licensing as machine-readable ODRL triples |
| Real-time DDB sync | Incremental update from DDB OAI-PMH feed |
| Text2SPARQL | NL → SPARQL via LLM + entity resolution |
| Visual search | CLIP/SwinV2 embeddings; image-to-image + text-to-image over DDB thumbnails |
| Self-hosting | `docker-compose.lite.yml` (100K objects, <8 GB RAM) + `docker-compose.full.yml` (≥64 GB RAM, ≥1 TB disk) |

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

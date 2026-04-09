# GeMeA — Architecture

## Data Flow

```
DDB JSON-LD files
      │
      ▼  rdf2jsonld (parallel conversion)
RDF/JSON (W3C serialization)
      │
      ▼  scripts/link_gnd_works.py  (Phase 0: title → GND Werk URI, pre-mocho)
RDF/JSON + GND Werk triples
      │
      ▼  mocho (EDM → mocho:Work grouping + RDA normalization)
      │  ⚠ mocho.owl is WIP — pipeline blocked until stable
Normalized RDF triples (N-Triples / Turtle)
      │
      ├──▶  ingest/load_qlever.py ──▶  QLever
      │                                (named graphs per provider)
      │                                        │
      │                                        ▼  Phase 1b
      │                              ingest/link_gnd_agents.py
      │                                  (graph/gnd-enrichment)
      │                                        │
      └──▶  ingest/index_es.py ◀──────────────┘  Elasticsearch
                                         (one doc per ProvidedCHO)
                                                │
                                                ▼
                                         FastAPI (api/)
                                         ├── /search       → Elasticsearch
                                         ├── /item/{id}    → QLever SPARQL
                                         ├── /sparql       → QLever proxy
                                         └── /suggest      → Elasticsearch
                                                │
                                                ▼
                                         Next.js (frontend/)
                                         ├── /             Search home
                                         ├── /search       Results + facets
                                         ├── /item/[id]    Object detail
                                         ├── /agent/[id]   Agent page
                                         ├── /place/[id]   Place page
                                         ├── /timespan/[id] TimeSpan page
                                         ├── /map          Map view
                                         └── /explore      Timeline + graph entry
```

---

## Components

### Ingest (`ingest/`)

| Script | Responsibility |
|--------|---------------|
| `scripts/link_gnd_works.py` | **Pre-mocho (Phase 0)**: link `dc:title` strings → GND Werk URIs via lobid-gnd; output triples feed mocho for `mocho:Work` grouping |
| `load_qlever.py` | Build QLever index from mocho N-Triples via `qlever index`; assign named graphs per provider |
| `index_es.py` | Build Elasticsearch documents from mocho RDF; one doc per ProvidedCHO |
| `build_docs.py` | Assemble ES document fields from SPARQL query over QLever |
| `validate.py` | Post-ingest integrity checks (triple count, missing required fields) |

**mocho:Work:** mocho creates `mocho:Work` entities (mocho-specific class, not standard `frbr:Work`) by grouping `edm:ProvidedCHO` instances that share the same GND Werk URI. The GND Werk link — produced by `link_gnd_works.py` — is the key mocho uses to determine which ProvidedCHOs belong to the same Work. mocho.owl is **currently WIP**; the `/work/{id}` API and WEMI hierarchy are blocked on its stabilization.

**Named graph strategy:** `http://gemea.ddb.de/graph/{provider-id}` — allows per-provider reload without touching the full dataset.

**ES document shape (per ProvidedCHO):**
```json
{
  "id": "http://www.deutsche-digitale-bibliothek.de/item/ABC123",
  "title": ["Faust", "Faust: Der Tragödie erster Teil"],
  "type": "literature",
  "sector": "bibliothek",
  "agent": [{"uri": "http://d-nb.info/gnd/118540238", "label": "Goethe, Johann Wolfgang von"}],
  "place": [{"uri": "http://sws.geonames.org/2925533", "label": "Frankfurt am Main", "lat": 50.11, "lon": 8.68}],
  "timespan": {"earliest": 1808, "latest": 1808},
  "provider": {"id": "...", "label": "Freies Deutsches Hochstift"},
  "thumbnail": "https://...",
  "isShownAt": "https://..."
}
```

`type` is normalized at index time via `ingest/type_mapping.json` (maps raw `dc:type` strings → controlled vocabulary). `sector` is derived from provider metadata.

---

### API (`api/`)

**Framework:** FastAPI (async)

| Endpoint | Backend | Notes |
|----------|---------|-------|
| `GET /search` | Elasticsearch | params: `q`, `type`, `sector`, `place`, `from`, `to`, `institution`, `page`, `size`; `type` is a controlled vocabulary (arts/culture branches, see below) |
| `GET /sectors` | Elasticsearch | list of DDB institutional sectors with object counts |
| `GET /suggest` | Elasticsearch | autocomplete on title + agent + place labels |
| `GET /item/{id}` | QLever SPARQL | full entity description + 1-hop neighbors |
| `GET /agent/{id}` | QLever SPARQL | agent description + linked objects |
| `GET /place/{id}` | QLever SPARQL | place description + linked objects |
| `GET /work/{id}` | QLever SPARQL | FRBR Work: title, agents, expressions, all manifestations; **conditional** on mocho outputting `frbr:Work` nodes |
| `GET /expression/{id}` | QLever SPARQL | FRBR Expression: language, date, parent Work, manifestations; **conditional** on mocho output |
| `GET /sparql` | QLever proxy | read-only pass-through; rate-limited |
| `POST /graphql` | QLever SPARQL | GraphQL schema over RDA/EDM entities; easier frontend consumption than SPARQL |
| `GET /health` | — | service health check |

**`type` — controlled vocabulary (arts and culture branches):**

The `type` filter is restricted to a curated set of top-level domain labels, not raw RDF type URIs. These map to `dc:type` values in the EDM data and are normalized at index time.

| `type` value | Maps to (EDM `dc:type` / GND genre) |
|---|---|
| `literature` | Handschrift, Buch, Manuskript, Textdokument, Werktitel |
| `music` | Musikhandschrift, Notendruck, Tonträger, Musikwerk |
| `theater` | Theaterzettel, Bühnenbildentwurf, Regiebuch |
| `film` | Film, Filmdokument, Kinoplakat |
| `painting` | Gemälde, Aquarell, Zeichnung |
| `graphic` | Druckgrafik, Radierung, Holzschnitt, Lithografie |
| `photography` | Fotografie, Fotodokument, Lichtbild |
| `architecture` | Architekturzeichnung, Bauplan, Modell |
| `sculpture` | Skulptur, Plastik, Objekt |
| `map` | Karte, Kartografisches Dokument |
| `object` | Kunstgewerbe, Objekt, Gebrauchsgegenstand |

Unmapped `dc:type` values are indexed under `object` as fallback. The mapping table is maintained in `ingest/type_mapping.json`.

**`sector` — DDB institutional sectors:**

The DDB organizes providers by institutional type. `sector` is a first-class filter and facet.

| `sector` value | DDB institution type |
|---|---|
| `bibliothek` | Public and research libraries |
| `archiv` | State, municipal, and private archives |
| `museum` | Museums and collections |
| `mediathek` | Media libraries (audio, video, film) |
| `denkmal` | Monument and heritage sites |

**Caching:** Redis; TTL 5 min for search results, 1 hour for entity pages.

**Security (OWASP):**
- SPARQL injection: parameterized query templates; QLever is read-only by default; block UPDATE/INSERT/DELETE at proxy
- Input sanitization: strip HTML/script from all query params
- Rate limiting: token bucket on `/sparql` (10 req/s) and `/search` (50 req/s)
- CORS: configured whitelist; defaults to same-origin
- Security headers: via Nginx (CSP, HSTS, X-Frame-Options, Referrer-Policy)
- Elasticsearch not exposed publicly; behind API only

---

### Frontend (`frontend/`)

**Framework:** Next.js 14+ (App Router), Tailwind CSS

| Page | Route | Key components |
|------|-------|---------------|
| Search home | `/` | `SearchBar`, `FeaturedItems` |
| Search results | `/search` | `SearchBar`, `FacetSidebar`, `ResultList`, `Pagination` |
| Object detail | `/item/[id]` | `MetadataPanel`, `GraphViz` (Cytoscape.js), `ThumbnailGallery` |
| Agent page | `/agent/[id]` | `EntityHeader`, `LinkedObjects` |
| Place page | `/place/[id]` | `EntityHeader`, `MapView` (Leaflet), `LinkedObjects` |
| TimeSpan page | `/timespan/[id]` | `EntityHeader`, `Timeline` (D3), `LinkedObjects` |
| Work page _(conditional)_ | `/work/[id]` | `WEMIHierarchy` (Work → Expressions → Manifestations), `LinkedObjects` |
| Map | `/map` | `MapView` (Leaflet), cluster markers, `SearchBar` |
| Explore | `/explore` | `Timeline` (D3 histogram), `GraphViz` entry |

**Content negotiation** (Linked Data): `/item/{id}` serves HTML to browsers, Turtle/JSON-LD to RDF clients via `Accept` header (handled in API layer).

---

### Docker / Infrastructure (`docker/`)

**Services (Docker Compose):**

| Service | Image | Port | Notes |
|---------|-------|------|-------|
| `qlever` | `adfreiburg/qlever` | 7001 (internal) | persistent volume for QLever index |
| `elasticsearch` | `elasticsearch:8.x` | 9200 (internal) | single-node |
| `redis` | `redis:alpine` | 6379 (internal) | API response cache |
| `api` | custom FastAPI | 8000 (internal) | |
| `frontend` | custom Next.js | 3000 (internal) | |
| `nginx` | `nginx:alpine` | 80, 443 | reverse proxy; TLS termination; security headers |

**Deployment (v1):** Single hosted instance operated by the team. Self-hosting (lite + full mode Docker Compose for external users) is v2 future work.

---

---

## Future Extensions (v2+)

These are not in v1 but the architecture is designed to accommodate them without structural changes.

| Extension | Component | Trigger |
|-----------|-----------|---------|
| **Text2SPARQL** | API: `POST /nl-search` | LLM translates natural language → SPARQL; 2-stage entity resolution (ArtKB pattern: Mistral → label lookup). Removes SPARQL expertise barrier for non-technical users. |
| **Visual search** | Vector DB: Qdrant | Embed DDB thumbnails (via `edm:isShownAt`) with CLIP/SwinV2; `POST /search/image`. Adds image-to-image and text-to-image retrieval. |
| **Object storage** | MinIO | Cache DDB thumbnails locally for reliability and controlled access; replaces dependency on external URLs. |
| **ODRL rights** | Ingest + triplestore | Model per-item licensing (CC0, CC BY, rights reserved) as ODRL expressions. Strengthens FAIR "Reusable" dimension; relevant for institutional reuse. |
| **Wikidata enrichment** | Ingest or API | Link GND agents/places to Wikidata entities; surface additional labels, images, DBpedia abstracts. |

---

## API Contracts

### `GET /search`
```
Query params:
  q           string   keyword query (required)
  type        string   arts/culture branch (controlled vocabulary; see type table above)
  sector      string   DDB institutional sector (bibliothek | archiv | museum | mediathek | denkmal)
  place       string   place URI or label
  from        int      earliest year
  to          int      latest year
  institution string   provider institution URI
  page        int      default 1
  size        int      default 20, max 100

Response 200:
{
  "total": 12345,
  "page": 1,
  "results": [
    {
      "id": "...",
      "title": "...",
      "type": "painting",
      "sector": "museum",
      "thumbnail": "...",
      "highlight": {"title": ["..."]},
      "score": 1.23
    }
  ],
  "facets": {
    "type": [{"value": "painting", "label": "Gemälde / Painting", "count": 42}],
    "sector": [{"value": "museum", "label": "Museum", "count": 18}],
    "place": [...],
    "institution": [...],
    "year": [{"year": 1808, "count": 7}]
  }
}
```

### `GET /sectors`
```
Response 200:
[
  {"value": "bibliothek", "label": "Bibliothek",  "count": 28400000},
  {"value": "archiv",     "label": "Archiv",      "count": 14200000},
  {"value": "museum",     "label": "Museum",      "count": 12100000},
  {"value": "mediathek",  "label": "Mediathek",   "count":  8900000},
  {"value": "denkmal",    "label": "Denkmal",     "count":  1400000}
]
```

### `GET /item/{id}`
```
Response 200:
{
  "id": "...",
  "types": [...],
  "titles": [{"value": "...", "lang": "de"}],
  "agents": [{"uri": "...", "label": "...", "role": "..."}],
  "places": [{"uri": "...", "label": "...", "lat": ..., "lon": ...}],
  "timespan": {"label": "...", "earliest": 1808, "latest": 1808},
  "provider": {"uri": "...", "label": "..."},
  "isShownAt": "...",
  "thumbnails": ["..."],
  "neighbors": [{"uri": "...", "label": "...", "relation": "..."}],
  "work": {"uri": "...", "label": "..."}        // present if GND Werktitel linked
}
```

### `GET /work/{id}` _(conditional on mocho frbr:Work output + Phase 1b coverage)_
```
Response 200:
{
  "id": "...",
  "label": "Faust. Der Tragödie erster Teil",
  "gnd_uri": "http://d-nb.info/gnd/...",
  "agents": [{"uri": "...", "label": "...", "role": "author"}],
  "expressions": [
    {
      "uri": "...",
      "language": "de",
      "date": "1808",
      "manifestations": [
        {"uri": "...", "title": "...", "provider": "...", "thumbnail": "..."}
      ]
    }
  ]
}
```

### `GET /expression/{id}` _(conditional on mocho frbr:Expression output)_
```
Response 200:
{
  "id": "...",
  "work": {"uri": "...", "label": "..."},
  "language": "de",
  "date": "1808",
  "manifestations": [
    {"uri": "...", "title": "...", "provider": "...", "thumbnail": "..."}
  ]
}
```

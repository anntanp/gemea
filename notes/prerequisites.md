# GeMeA — Prerequisites

CS concepts, algorithms, frameworks, design patterns, programming languages, and technical skills needed to build GeMeA independently.

---

## Semantic Web & Knowledge Graphs

- **RDF** (Resource Description Framework): triple model (subject–predicate–object), named graphs
- **SPARQL 1.1**: SELECT, CONSTRUCT, DESCRIBE, ASK; property paths; OPTIONAL; FILTER; aggregation; LIMIT/OFFSET; federated queries
- **OWL** (Web Ontology Language): classes, properties, restrictions, inference/reasoning basics
- **Europeana Data Model (EDM)**: ProvidedCHO, Aggregation, WebResource, Agent, Place, TimeSpan; edm:isShownAt, edm:hasView
- **RDA (Resource Description & Access)**: WEMI hierarchy (Work, Expression, Manifestation, Item); Group 2/3 entities
- **FRBR**: Functional Requirements for Bibliographic Records; entity groups
- **JSON-LD**: @context, @id, @type, @graph; compaction/expansion; Framing
- **RDF/JSON serialization** (W3C): subject-keyed object with predicate arrays
- **Turtle / N-Triples**: for bulk loading and data inspection
- **Named graphs / quads**: NQuads, TriG (for provenance tracking by provider/batch)
- **Namespace prefixes**: dc, dcterms, edm, ore, skos, rdfs, owl, foaf, schema, gnd, wikidata

## Graph Databases

- **QLever**: `qlever index` (build index from N-Triples), `qlever start` (launch server), Qleverfile configuration (`Mmap`, `num-threads`, `text-index`), SPARQL endpoint, built-in text search (`ql:contains-entity`), spatial queries, named graphs
- **Triplestore bulk load patterns**: N-Triples chunk loading, parallel load, checkpoint/restart
- **SPARQL query optimization**: LIMIT early, use named graphs, avoid Cartesian products, query timeout configuration
- **Fallback options** (self-hosting v2): Apache Jena TDB2 + Fuseki (tdbloader2, Fuseki server config); Virtuoso OSE (ISQL, `rdf_loader_run()`)

## Search & Information Retrieval

- **Elasticsearch 8.x**: index mapping, analyzers (standard, German language analyzer `de`), BM25 ranking, faceted search (terms aggregations), highlighting, `multi_match`, `query_string`, pagination (from/size, `search_after`)
- **Index design for cultural heritage**: field types (keyword vs. text), nested objects for multilingual fields, GeoPoint fields for geo-search
- **Faceted search UX**: facet selection, AND/OR logic, cardinality limits
- **Query federation**: combining Elasticsearch text results with SPARQL graph enrichment

## Backend (Python / FastAPI)

- **FastAPI**: path operations, async handlers, Pydantic models, dependency injection, middleware (CORS, caching)
- **SPARQL client**: `SPARQLWrapper` or `httpx` for async HTTP calls to QLever SPARQL endpoint
- **Elasticsearch Python client** (`elasticsearch-py 8.x`): async client, index lifecycle
- **Async Python**: `asyncio`, `httpx`, background tasks
- **Caching**: Redis for SPARQL result caching; HTTP cache headers (`Cache-Control`, ETags)
- **Pagination patterns**: cursor-based vs. offset for large result sets
- **API design**: REST conventions, OpenAPI/Swagger auto-docs, versioning (`/v1/`)

## Ontology Alignment & mocho

- **Ontology alignment**: mapping classes and properties between source ontology (EDM) and target ontology (RDA/FRBR); `owl:equivalentClass`, `owl:equivalentProperty`; SPARQL CONSTRUCT for rule-based transformation
- **mocho** (`../mocho/`): GeMeA's alignment tool; takes rdf2jsonld output + GND Werk triples → produces `mocho:Work` entities + RDA-normalized triples; mocho.owl is WIP
- **mocho:Work**: mocho-specific class grouping `edm:ProvidedCHO` instances that share a GND Werk URI; the grouping key is the GND Werk link produced by `link_gnd_works.py` (must run before mocho)
- **FRBR entity creation**: promoting a flat `edm:ProvidedCHO` record into the WEMI hierarchy (Work → Expression → Manifestation → Item); requires external authority linkage (GND Werktitel) to identify Work-level groupings
- **OWL reasoning**: forward chaining, materialization; difference between declarative alignment (reasoner applies equivalences) vs. procedural transformation (SPARQL CONSTRUCT rules)
- **rdf2jsonld** (`../rdf2jsonld/`): converts DDB JSON-LD → W3C RDF/JSON; repairs URI malformations; parallel processing per provider batch

## ETL / Data Engineering

- **RDF bulk loading**: mocho N-Triples → QLever index via `qlever index`
- **Named graph assignment**: partition by provider for manageability and per-provider reload
- **Python RDF libraries**: `rdflib` (parsing, serialization, graph manipulation)
- **Streaming / chunked processing**: process 65M records without loading all into memory (NDJSON, generators)
- **Elasticsearch bulk indexing**: `helpers.bulk()`, index rollover for large datasets
- **Process orchestration**: sequential shell scripts for v1; Luigi or Airflow for v2
- **Monitoring ingestion**: progress logging, checkpointing, error recovery

## Frontend (Next.js / React)

- **Next.js 14+**: App Router, server components, `fetch` with caching, dynamic routes (`/item/[id]`), ISR (Incremental Static Regeneration) for entity pages
- **React**: hooks (`useState`, `useEffect`, `useCallback`), context, server vs. client components
- **Tailwind CSS**: responsive design (`sm:`, `md:`, `lg:`), dark mode, component utility patterns
- **Search UX patterns**: debounced input, loading states, empty states, result highlighting
- **Facet sidebar**: collapsible sections, URL-synced state (`URLSearchParams`), keyboard accessibility

## Visualization

- **Cytoscape.js**: graph rendering in canvas/SVG, layout algorithms (COSE, Dagre, Breadthfirst), node/edge styling, event handling, performance with large graphs (virtual rendering)
- **Leaflet.js**: tile layers (OSM), marker clusters, GeoJSON overlays, popups, map bounds from data
- **D3.js** (timeline): time scales, brush/zoom, histogram of objects per year
- **Canvas vs. SVG**: SVG for small graphs (<500 nodes), canvas for large; Cytoscape handles both

## Data

- **DDB data model**: item-id, provider-info, view, index_profile, edm fields (see rdf2jsonld spec)
- **GND (Gemeinsame Normdatei)**: German authority file for agents, places, subjects; `d-nb.info/gnd/` URIs
- **Wikidata**: linked entity URIs for enrichment
- **Geographic data**: WGS84 coordinates, GeoNames, TGN (Getty Thesaurus of Geographic Names)
- **Temporal data**: ISO 8601 dates, edm:TimeSpan, `sem:hasBeginTimeStamp` / `sem:hasEndTimeStamp`
- **CC BY 4.0**: license obligations for data display and redistribution

## DevOps & Infrastructure

- **Docker / Docker Compose**: containerize QLever, Elasticsearch, Redis, FastAPI, Next.js, Nginx
- **Nginx**: reverse proxy, TLS termination, security headers, rate limiting (`limit_req_zone`)
- **Environment variables**: secrets management (no hardcoded credentials)
- **Health checks**: `/health` endpoints for all services
- **Volume mounts**: persistent data for QLever index and Elasticsearch indices

## General CS

- **HTTP semantics**: status codes, content negotiation (`Accept: text/turtle`), CORS
- **Content negotiation**: serving HTML, JSON, Turtle, N-Triples from the same URI (Linked Data principles)
- **URI design**: `/item/{id}`, `/agent/{uri}`, `/place/{uri}` — stable, dereferenceable URIs
- **Pagination**: limit/offset tradeoffs at scale; cursor-based for Elasticsearch deep pagination
- **Internationalization (i18n)**: multilingual labels (German primary, English secondary); `lang` tags in RDF

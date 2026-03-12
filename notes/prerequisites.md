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

- **Virtuoso Open Source**: installation, configuration, ISQL, bulk loading via `isql-vt` + `rdf_loader_run()`, SPARQL endpoint (`/sparql`), text index, named graphs, security settings
- **Apache Jena TDB2 + Fuseki**: tdbloader2, dataset assembly, Fuseki server config (for dev/staging)
- **Graph DB performance tuning**: index strategies, query caching, connection pooling, SPARQL query optimization (LIMIT early, use named graphs, avoid Cartesian products)
- **Triplestore bulk load patterns**: N-Triples chunk loading, parallel load, checkpoint/restart

## Search & Information Retrieval

- **Elasticsearch 8.x**: index mapping, analyzers (standard, German language analyzer `de`), BM25 ranking, faceted search (terms aggregations), highlighting, `multi_match`, `query_string`, pagination (from/size, `search_after`)
- **Index design for cultural heritage**: field types (keyword vs. text), nested objects for multilingual fields, GeoPoint fields for geo-search
- **Faceted search UX**: facet selection, AND/OR logic, cardinality limits
- **Query federation**: combining Elasticsearch text results with SPARQL graph enrichment

## Backend (Python / FastAPI)

- **FastAPI**: path operations, async handlers, Pydantic models, dependency injection, middleware (CORS, caching)
- **SPARQL client**: `SPARQLWrapper` or `httpx` for async HTTP calls to Virtuoso `/sparql`
- **Elasticsearch Python client** (`elasticsearch-py 8.x`): async client, index lifecycle
- **Async Python**: `asyncio`, `httpx`, background tasks
- **Caching**: Redis for SPARQL result caching; HTTP cache headers (`Cache-Control`, ETags)
- **Pagination patterns**: cursor-based vs. offset for large result sets
- **API design**: REST conventions, OpenAPI/Swagger auto-docs, versioning (`/v1/`)

## ETL / Data Engineering

- **RDF bulk loading**: converting mocho-normalized RDF/JSON → N-Triples → Virtuoso bulk loader
- **Named graph assignment**: partition by provider, batch, or type for manageability
- **Python RDF libraries**: `rdflib` (parsing, serialization, graph manipulation)
- **Streaming / chunked processing**: process 65M records without loading all into memory (NDJSON, generators)
- **Elasticsearch bulk indexing**: `helpers.bulk()`, index rollover for large datasets
- **Process orchestration**: Luigi or Airflow for multi-stage pipelines (optional for v1)
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

- **Docker / Docker Compose**: containerize Virtuoso, Elasticsearch, FastAPI, Next.js
- **Nginx**: reverse proxy, static asset serving, SPARQL endpoint exposure
- **Environment variables**: secrets management (no hardcoded credentials)
- **Health checks**: `/health` endpoints for all services
- **Volume mounts**: persistent data for Virtuoso TDB and Elasticsearch indices

## General CS

- **HTTP semantics**: status codes, content negotiation (`Accept: text/turtle`), CORS
- **Content negotiation**: serving HTML, JSON, Turtle, N-Triples from the same URI (Linked Data principles)
- **URI design**: `/item/{id}`, `/agent/{uri}`, `/place/{uri}` — stable, dereferenceable URIs
- **Pagination**: limit/offset tradeoffs at scale; cursor-based for Elasticsearch deep pagination
- **Internationalization (i18n)**: multilingual labels (German primary, English secondary); `lang` tags in RDF

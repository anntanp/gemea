# Paper Outline

**Title (draft):** _GeMeA: German Memory Atlas — A Knowledge Graph Browser for the German Digital Library_

**Track:** ISWC 2026 Resource Track
**Page budget:** 8–15 pages (excl. references and Gen AI declaration)
**Format:** Springer LNCS

---

## Core Argument

> _What is the single claim this paper makes? Fill in before writing._

GeMeA fills a critical gap by providing the first open, SPARQL-accessible knowledge graph over the complete German Digital Library corpus (65M objects), normalizing heterogeneous EDM metadata to a unified RDA/FRBR model and exposing it through a full-featured web interface.

---

## Proposed Section Structure

### 1. Introduction (~1 page)
- Problem: 65M DDB objects rich in metadata but inaccessible as a knowledge graph
- Gap: no SPARQL endpoint, no linked-data browser, no cross-entity navigation
- Contribution: GeMeA — open KG browser + public SPARQL endpoint
- Pipeline summary: DDB JSON-LD → rdf2jsonld → mocho → GeMeA
- Paper roadmap

### 2. Related Work (~1–1.5 pages)
- Cultural heritage KGs: Europeana EDM LOD, ArCo (Italian CH, CIDOC-CRM), Smithsonian LOD, BIBFRAME
- **ArtKB** [Blanco et al., ESWC 2026] — closest contemporary: CACAO/CIDOC-CRM, Wikidata source,
  8M triples, 307K artefacts, multimodal (vector DB + object storage); differs from GeMeA in scale
  (200×), scope (art only vs. cross-domain), access (API-only vs. web UI)
- DDB native UI: limitations (no SPARQL, no graph navigation, no open data export)
- Comparison table (rows: GeMeA, ArtKB, Europeana LOD, ArCo, DDB native UI):
  columns: scale, ontology, SPARQL, web UI, multimodal, self-hostable (GeMeA: planned v2)
- ORKG comparison link: TBD

### 3. Resource Description (~3–4 pages)
- Source data: DDB corpus, EDM metadata, 65M ProvidedCHOs
- Pipeline: rdf2jsonld (EDM → RDF/JSON) + mocho (RDA normalization)
- Data model: RDA WEMI + EDM entities; mocho alignment overview
- Schema diagram (figure)
- Named graph strategy (per provider)
- Scale statistics: objects, triples, agents, places, time spans, providers
- VoID dataset descriptor
- Web app: search, facets, entity pages, graph viz, map, timeline
- SPARQL endpoint: URL, supported patterns, rate limits

### 4. Quality and Validation (~1–2 pages)
- URI well-formedness (rdf2jsonld repair rates)
- mocho mapping quality (direct vs. approximate; coverage per source ontology)
- SHACL / SPARQL ASK validation queries
- Completeness: % of DDB corpus loaded; gaps and exclusions
- Known limitations (sparse geo data, temporal ambiguity)
- Metrics table

### 5. Usage and Reusability (~1–2 pages)
- Web UI walkthrough (screenshots)
- Example SPARQL queries (4 listings):
  1. Objects by agent (GND URI)
  2. Objects by place + decade
  3. Object count per provider
  4. 1-hop neighborhood of a ProvidedCHO
- GraphQL endpoint: example query fetching an item with its agents and places
- Extension points: new providers, Wikidata enrichment, v2 features (self-hosting, Text2SPARQL, visual search)

### 6. Impact (~0.5–1 page)
- FAIR compliance analysis
- Target communities: digital humanities, library science, KG/IR research
- Relation to ddbkg (IR benchmarking on GeMeA data)
- Societal interest: German cultural heritage discoverable and machine-readable

### 7. Sustainability (~0.5 page)
- Versioning + update cadence
- Persistent URI plan (w3id)
- Open source (GitHub)
- Self-hosting planned for v2 (Docker Compose lite + full mode)

### 8. Conclusion (~0.5 page)

### Resource Availability Statement _(mandatory)_
- Persistent URI: TBD
- License: CC BY 4.0 (data), TBD (code)
- Canonical citation: TBD

### Declaration of Use of Generative AI _(mandatory; not counted in page limit)_

### References

---

## Open Questions

- [ ] Persistent URI strategy: w3id vs. Zenodo DOI?
- [ ] ORKG comparison: identify comparable resources
- [ ] Include benchmark evaluation results in quality section? (affects page count)
- [ ] Wikidata enrichment: at ingest or query time? (affects resource description)
- [ ] Screenshots for usage section (need UI to exist first)
- [ ] Schema diagram (figure): UML-style or graph diagram?

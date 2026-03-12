# GeMeA — Project Specification

**German Memory Atlas** — A knowledge graph browser for the German Digital Library (DDB).

---

## Problem

65 million DDB cultural heritage objects exist as semantic triples (EDM metadata, RDA/FRBR-normalized via mocho) with no user-facing interface. The data is rich — agents, places, time spans, object types, provider institutions — but inaccessible to non-technical users.

GeMeA makes the collection searchable, browsable, and visually explorable.

---

## Pipeline Context

```
DDB JSON-LD
    ↓  rdf2jsonld
RDF/JSON (W3C)
    ↓  mocho (RDA ontology normalization)
Normalized RDF triples
    ↓  GeMeA ingest
Virtuoso + Elasticsearch
    ↓  GeMeA API
GeMeA Frontend
```

GeMeA is the **terminal stage** of the DDB → mocho pipeline. It consumes mocho's output.

---

## Inputs

| Input | Format | Source |
|-------|--------|--------|
| mocho-normalized RDF | N-Triples / Turtle (TBD: confirm with mocho) | `mocho/output/` |
| DDB item metadata | EDM JSON-LD (fallback/reference) | DDB API / dump |

**Scale**: ~65M objects → estimated 650M–1B triples.

---

## Outputs

A responsive website with:
1. **Search** — keyword search with ranked results
2. **Faceted browse** — filter by object type, place, time period, institution/provider
3. **Entity pages** — detail view for objects (ProvidedCHO), agents, places, time spans
4. **Graph visualization** — interactive network of connections around a selected entity
5. **Map view** — geo-referenced objects on an OSM map
6. **Timeline** — temporal distribution of objects (bar chart / histogram)
7. **SPARQL endpoint** — publicly accessible at `/sparql`

---

## Constraints

- **Scale**: 65M objects; sub-second response for search queries
- **Open access**: no authentication required for browsing or SPARQL
- **License**: CC BY 4.0 (DDB data)
- **Responsive**: mobile + desktop
- **Languages**: German primary; English UI labels
- **URIs**: stable, dereferenceable (content negotiation: HTML / Turtle / JSON-LD)

---

## Success Criteria

- [ ] All 65M objects indexed and searchable by keyword
- [ ] Faceted filtering functional: type, place, time, institution
- [ ] Entity pages for ProvidedCHO, Agent, Place, TimeSpan with linked neighbors
- [ ] Map view renders geo-referenced items with clustering
- [ ] Timeline histogram shows collection temporal distribution
- [ ] Graph viz renders 1-hop neighborhood of any entity
- [ ] SPARQL endpoint handles concurrent queries (target: 10 concurrent)
- [ ] Page load <2s (search results), <3s (entity pages with graph viz)

---

## Open Questions

| # | Question | Impact |
|---|----------|--------|
| 1 | What format does mocho emit? (N-Triples? Turtle? RDF/JSON?) | Ingest pipeline design |
| 2 | Hosting target: local only, VPS, or cloud? | Infrastructure choices |
| 3 | Should the SPARQL endpoint be rate-limited or fully open? | Security/ops |
| 4 | Enrich with Wikidata/GND at ingest or query time? | Data model, latency |
| 5 | Is full-text search needed in German (stemming, umlauts)? | Elasticsearch analyzer config |

---

## Out of Scope (v1)

- User accounts, collections, annotations
- Embedding-based semantic search (planned for ddbkg research)
- Automated reasoning / OWL inference
- Real-time DDB sync (static ingestion only)
- Multi-language UI beyond German/English

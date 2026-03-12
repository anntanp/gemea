# GeMeA — Elasticsearch Index

The ES index is the search-optimized copy of the data that powers `GET /search`. One document per `ProvidedCHO` (cultural heritage object).

---

## Role in the pipeline

```
QLever (full RDF graph)
      │
      ▼  build_docs.py  (SPARQL queries to assemble each document)
      ▼  index_es.py    (bulk-loads documents into Elasticsearch)
Elasticsearch index
      │
      ▼
GET /search  →  keyword queries, facets, ranking, pagination
```

`build_docs.py` queries QLever via SPARQL to assemble each document. It runs **after** Phase 1b (GND enrichment) so that `agent.gnd_uri` and `cho.gnd_work_uri` fields are populated.

---

## Document shape (per ProvidedCHO)

```json
{
  "id": "http://www.deutsche-digitale-bibliothek.de/item/ABC123",
  "title": ["Faust", "Faust: Der Tragödie erster Teil"],
  "type": ["http://www.europeana.eu/schemas/edm/ProvidedCHO"],
  "agent": [{"uri": "gnd:118540238", "label": "Goethe, Johann Wolfgang von", "gnd_uri": "gnd:118540238"}],
  "place": [{"uri": "...", "label": "Frankfurt am Main", "lat": 50.11, "lon": 8.68}],
  "timespan": {"earliest": 1808, "latest": 1808},
  "provider": {"id": "...", "label": "Freies Deutsches Hochstift"},
  "thumbnail": "https://...",
  "isShownAt": "https://...",
  "cho_gnd_work_uri": "gnd:..."
}
```

---

## Why ES alongside QLever

QLever handles structured SPARQL queries (entity lookups, graph traversal). ES handles everything search-specific:

| Capability | QLever | ES |
|------------|--------|----|
| Multi-hop graph queries | ✓ | ✗ |
| BM25 ranked full-text search | ✗ | ✓ |
| German stemming / umlaut normalization | partial (text index) | ✓ (dedicated analyzer) |
| Facet aggregations (counts by type/place/year) | slow | ✓ (sub-100ms) |
| Highlighted snippets | ✗ | ✓ |
| GeoPoint queries + clustering | partial | ✓ |

The two backends are complementary: QLever for "everything about this entity", ES for "find objects matching this keyword with these filters."

---

## Index configuration notes

- **Analyzer**: `german` (Snowball stemmer, umlaut normalization, stopwords)
- **Geo**: `place` field mapped as `geo_point` for map clustering and bounding-box filters
- **Facets**: `type`, `provider.id`, `agent.uri`, `place.uri` mapped as `keyword` (not analyzed) for terms aggregations
- **Timespan**: `timespan.earliest` and `timespan.latest` as `integer` for range filters and histogram aggregation
- **Compound splitting**: consider adding `decompounder` token filter with a domain dictionary from DDB type/genre vocabulary (see `notes/nlp-tasks.md`)

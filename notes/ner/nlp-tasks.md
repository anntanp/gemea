# GeMeA — NLP Tasks and Retrieval Design

---

## v1: What the stack handles

### Lexical search (Elasticsearch / BM25)

German analyzer pipeline: Snowball stemming, umlaut normalization, stopword removal. Handles the common case (keyword query → ranked results).

**Hard cases the analyzer does not solve:**

| Problem | Example | Mitigation |
|---------|---------|------------|
| Compound splitting | `Landschaftsgemälde` ≠ `Gemälde` | ES `decompounder` token filter + domain dictionary from DDB types/genres |
| Historical orthography | `ck` vs `k`, pre-1901 reform | Normalisation rules or phonetic filter |
| Case ambiguity | `Rose` (name) vs `rose` (object description) | Low priority; affects short queries only |

### Structured retrieval (SPARQL / QLever)

Precise multi-hop patterns ES cannot express: "objects whose creator was born in Weimar and died after 1832." Full power for researchers; inaccessible to general users without Text2SPARQL.

### QLever integrated text+SPARQL

QLever supports `FILTER ql:contains-entity()` — text and graph constraints in a single query, no ES round-trip. Example: objects with "Faust" in the title whose creator has a GND URI. Worth a dedicated example in paper §5.

---

## NLP-hard problems

### 1. Entity ambiguity at query time

A query for `Frankfurt` is ambiguous: place filter, creator birthplace, or title token? Currently no disambiguation — ES returns all matches.

**Resolution path:** if the query string resolves to a GND URI, rewrite as a structured filter. GND type (place / person / institution) determines the predicate. A shared entity resolution module, used by both `GET /suggest` and future Text2SPARQL, handles this consistently.

### 2. Entity linking — ingest vs. query time

Two distinct problems, both requiring GND resolution:

- **Ingest time** (Phase 1b): batch, high precision; `"Goethe, Johann Wolfgang von"` → `gnd:118540238` via lobid-gnd; stored as `owl:sameAs` / `skos:closeMatch` triples
- **Query time**: real-time, must be fast; user types `"goethe"` → candidate GND URIs → query rewrite

QLever's text index over `rdfs:label` can serve query-time lookups — same mechanism as ArtKB's Text2SPARQL stage 2. Design this as a single reusable module from the start.

### 3. Text2SPARQL (v2)

Follow the ArtKB pattern (Mistral Small, temperature 0.1):
1. LLM receives ontology structure + NL query → generates SPARQL with entity placeholders
2. SPARQL label lookups resolve placeholders to GND/GeoNames URIs
3. Final query executed against QLever

**German-specific wrinkle**: DDB metadata is in German. The LLM must produce German-language label strings for entity resolution even when the user queries in English. Requirements: multilingual model, correct German label generation, ontology-aware predicate selection (mocho's RDA/FRBR vocabulary).

### 4. Cross-language queries

DDB metadata is almost entirely German. An English query `"landscape painting 18th century"` has poor BM25 recall. Options:

| Approach | Complexity | Quality |
|----------|------------|---------|
| Query translation to German before ES lookup | Low | Good for common terms |
| Multilingual dense retrieval (`multilingual-e5-large` over title embeddings in Qdrant) | Medium | Generalises to any language |
| GND URI as language-agnostic pivot | Low (if entity links) | Precise but only for known entities |

The Qdrant slot planned for v2 visual search also fits multilingual text embeddings.

### 5. Temporal query parsing

`from=` / `to=` API params take raw integers. Natural language expressions ("early 19th century", "Weimarer Klassik") need parsing to year ranges. **HeidelTime** is purpose-built for this, has strong German support, and handles historical texts well. A lightweight pre-processing step before the ES query.

---

## Entity-typed suggest (design question)

The current `GET /suggest` plan is plain ES autocomplete over labels. A richer design returns **entity-typed suggestions**:

```
"goethe" →
  Goethe, Johann Wolfgang von  [Person]  → /agent/gnd:118540238
  Goethe-Institut               [Organization]  → /agent/...
  Faust [Werk von Goethe]       [Work]  → SPARQL filter on cho.gnd_work_uri
```

Each suggestion type routes to a different query strategy. Implementation: NER or type lookup over GND suggestion candidates. Small addition to Phase 2 scope, but it:
- Meaningfully improves UX
- Pre-builds the query-time entity resolution pipeline that Text2SPARQL reuses
- Makes a concrete demo for paper §5

---

## What is interesting for the paper

The retrieval architecture itself (ES + BM25 + SPARQL) is not novel. The interesting angles:

1. **Scale impact on GND linking**: 65M objects → report Phase 1b precision/recall (% agents linked, match quality breakdown) as a quantitative result in §4.
2. **QLever text+SPARQL integration**: demonstrate a query that requires both text matching and graph traversal in a single SPARQL statement — positioned as an advantage over ES-only or SPARQL-only systems.
3. **Entity resolution as a reusable module**: the lobid-gnd pipeline (`owl:sameAs` for exact, `skos:closeMatch` + confidence score for approximate) is a generalizable contribution, not just internal plumbing.

---

## Open questions

- [ ] Compound splitting: build domain dictionary from DDB type/genre vocabulary, or rely on QLever text search for compound-aware matching?
- [ ] HeidelTime integration: pre-processing step in the API layer, or at ingest time as a normalised `timespan.earliest/latest` field?
- [ ] Entity-typed suggest: add to Phase 2 scope?
- [ ] Cross-language: defer entirely to v2, or add query translation as a lightweight Phase 2 option?
- [ ] Text2SPARQL model choice: Mistral Small (ArtKB) vs. smaller open model for lower hosting cost?

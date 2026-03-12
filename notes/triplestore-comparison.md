# Triplestore Comparison for GeMeA

Last reviewed: 2026-03-12

Reference: Bast et al. (2025), "Sparqloscope: A generic benchmark for the comprehensive and concise performance evaluation of SPARQL engines." Sparqloscope evaluated six engines — **QLever, Virtuoso, MillenniumDB, GraphDB, Blazegraph, Jena** — on DBLP (~500 M triples) and Wikidata Truthy (~8 B triples).

---

## Comparison Table

| | **QLever** | **Jena TDB2 + Fuseki** | **Virtuoso OSE** | **Oxigraph** | **GraphDB Free** |
|---|---|---|---|---|---|
| **Scale (1B+ triples)** | Proven (claims 1T on commodity HW) | OK with tuning | Proven (DBpedia) | Untested | OK |
| **Query performance** | Top in Sparqloscope benchmarks | Reliable, moderate | Unpredictable on complex queries | Fast for simple queries | Good |
| **SPARQL 1.1** | Full | Full | Full | Full | Full + OWL reasoning |
| **Named graphs** | Yes | Yes | Yes | Yes | Yes |
| **Built-in text search** | Yes (advanced) | No (external) | Yes (limited) | No | Yes |
| **Spatial queries** | Yes (built-in) | No | Limited | No | Limited |
| **SPARQL autocompletion** | Yes (context-sensitive) | No | No | No | No |
| **Ease of setup** | Easy (`qlever` CLI, Docker) | Easy (single JAR) | Hard (ISQL, INI tuning) | Very easy (binary) | Medium |
| **Self-hosting** | Good | Good | Painful | Excellent | OK (limits on free tier) |
| **License** | Apache 2.0 | Apache 2.0 | GPL v2 | MIT/Apache 2.0 | Proprietary (free tier) |
| **Active development** | Yes (Uni Freiburg, 2025 papers) | Yes (Apache) | Declining | Growing | Yes (commercial) |
| **Community** | Research-oriented | Large, mature | Declining OSS | Small but growing | Commercial |
| **RAM floor (1B triples)** | Moderate | High (JVM) | Very high + tuning | Low | Moderate |

---

## QLever — Detailed Assessment for GeMeA

### Strengths

- **Performance at scale**: Benchmarked top performer against Virtuoso, GraphDB, Blazegraph, and Jena on 500M–8B triple datasets (Sparqloscope). Explicitly claims 1T triples on a single commodity machine.
- **Built-in text search**: Could partially replace or complement Elasticsearch. Relevant for GeMeA's German-language keyword search — needs evaluation against ES's German analyzer.
- **Built-in spatial queries**: Directly supports GeMeA's map view without routing through a separate geo index.
- **SPARQL autocompletion**: Ships a context-sensitive autocomplete API — directly useful for GeMeA's `/suggest` endpoint, potentially replacing a custom ES autocomplete.
- **Apache 2.0**: Cleanest license for an open, self-hostable resource.
- **`qlever` CLI**: Single tool handles index build, server start, and configuration — lowers the barrier for self-hosting users significantly.
- **Research provenance**: Developed at Uni Freiburg (Hannah Bast group), actively published. Credible for an ISWC paper submission.

### Concerns

- **Named graph performance**: Sparqloscope (as of 2025) does not yet evaluate `FROM [NAMED]` and `GRAPH` clauses. GeMeA's named-graph-per-provider strategy needs explicit testing against QLever.
- **Production cultural heritage deployments**: Fewer documented CH deployments than Virtuoso. Newer codebase — less battle-hardened in multi-user production settings.
- **Text search vs. Elasticsearch**: QLever's text search is powerful for SPARQL-integrated text matching, but Elasticsearch offers richer faceted aggregations (terms aggs, nested objects, GeoPoint), German stemming/umlaut normalization, and BM25 ranking. For GeMeA's facet sidebar and result ranking, ES likely remains superior. The two can coexist.
- **Update operations**: Sparqloscope explicitly notes it does not evaluate update performance. If incremental DDB data sync (future feature) is needed, this matters.

### Architecture impact

If QLever's built-in text search and spatial queries are sufficient:

```
Simplified option:
  mocho RDF → QLever (text + spatial + SPARQL)
                   ↓
              FastAPI
                   ↓
             Next.js UI

Full option (recommended for v1):
  mocho RDF → QLever (SPARQL + graph traversal + spatial)
           → Elasticsearch (faceted search + German FTS + autocomplete)
                   ↓
              FastAPI
```

The full option keeps ES for search quality (German language analyzer, facets, BM25). QLever handles all SPARQL queries and entity lookups. Spatial queries can go to either.

---

## Recommendation

**Primary triplestore: QLever**

Reasons over Jena:
1. Performance benchmark evidence (Sparqloscope, 2025) — not just claims
2. Built-in text search and spatial reduce integration surface area
3. Better scale ceiling (1T vs. ~500M–1B for Jena with tuning)
4. `qlever` CLI makes self-hosting substantially easier than both Jena and Virtuoso
5. Apache 2.0, actively published — good fit for ISWC resource paper

Keep **Jena TDB2 + Fuseki** documented as the fallback/alternative in `docker/docs/self-hosting.md` for users who prefer a more established, Java-based option.

Document **Virtuoso** as a high-throughput alternative for institutions with dedicated infrastructure.

---

## Open Tasks

- [ ] Test QLever's named graph (`FROM NAMED` / `GRAPH`) performance on a mocho RDF sample
- [ ] Compare QLever text search vs. Elasticsearch German analyzer on DDB titles (sample query set)
- [ ] Verify QLever Docker image stability for long-running production use
- [ ] Run Sparqloscope on GeMeA data once ingested — use results in paper §4 (Quality)

---

## Citation

```bibtex
@inproceedings{bast2025sparqloscope,
  title     = {Sparqloscope: A generic benchmark for the comprehensive and concise
               performance evaluation of {SPARQL} engines},
  author    = {Bast, Hannah and Kalmbach, Johannes and Textor-Falconi, Robin
               and Ullinger, Christoph},
  year      = {2025},
  url       = {https://purl.org/ad-freiburg/sparqloscope}
}
```

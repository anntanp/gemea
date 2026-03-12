# GeMeA — Priorities

Paper deadline: **7 May 2026** (~8 weeks from 12 Mar 2026)
ISWC Resource Track requirement: resource must be publicly accessible with persistent URI.

---

## Must-haves

Blocking — without these, the resource doesn't exist or the paper fails review.

| Item | Why blocking |
|------|-------------|
| **Phase 0**: DDB data → N-Triples (rdf2jsonld + mocho) | No data, no resource |
| **Phase 1**: `load_qlever.py` — data into QLever | No KG without it |
| **Phase 1**: `index_es.py` + `build_docs.py` — ES index | No search without it |
| **Phase 1b**: `link_gnd_agents.py` + `link_gnd_works.py` | Stated differentiator; feeds quality section numbers |
| **Phase 2**: `GET /search`, `GET /item/{id}`, `GET /agent/{id}`, `GET /place/{id}` | Core API for the UI |
| **Phase 2**: `GET /sparql` (QLever proxy) | ISWC Resource Track requires a public SPARQL endpoint |
| **Phase 3**: `SearchBar` + results list | Minimum viable UI |
| **Phase 3**: `/item/[id]`, `/agent/[id]`, `/place/[id]` entity pages | Demonstrates graph browsing — the core claim |
| **Phase 4**: Docker Compose + Nginx + `.env.example` | Required to deploy a public instance |
| Persistent URI (w3id) + public URL | Mandatory for Resource Availability Statement |

---

## Nice-to-haves

Strengthen the paper or product but not blocking for acceptance.

| Item | Value | Deferral cost |
|------|-------|--------------|
| `FacetSidebar` (type, place, institution, year) | Strong UX; good for §5 screenshots | Can show basic results without facets |
| `GET /suggest` autocomplete | Smooth UX; entity-typed suggest is interesting | Results page works without it |
| `GraphViz` (Cytoscape.js) | Headline feature for a "KG browser" | Could show static neighbor list instead |
| `MapView` (Leaflet) | Visual impact in paper | `/place/[id]` pages work without a map |
| `Timeline` (D3) | Nice for `/explore` | Not needed for core browsing |
| `POST /graphql` | Differentiator vs ArtKB | SPARQL endpoint covers reviewers' bar |
| Content negotiation (Turtle/JSON-LD) | FAIR / Linked Data compliance point | Mention as planned in paper |
| `enrichment_report.py` | Numbers for §4 quality section | Can compute manually from SPARQL |
| Redis caching | Performance | Not needed for paper demo traffic |
| Full test suites | Code quality | Paper doesn't require it |
| Full OWASP checklist | Security | A03/A04/A05 are the critical ones for a public endpoint |

---

## Recommended sequence

```
Phase 0
  → Phase 1 (QLever load only)
  → Phase 1b (GND enrichment)
  → Phase 1 (ES index, now with enriched data)
  → Phase 2 (core endpoints + /sparql)
  → Phase 3 (search + entity pages)
  → Phase 4 (deploy to public URL)
  → paper §3–§5
```

After core entity pages are working, add `FacetSidebar` and `GraphViz` if time allows — high value for paper screenshots. Everything else is post-submission.

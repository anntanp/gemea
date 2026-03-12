# ArtKB: A Multimodal Art Knowledge Base for Cultural Heritage

**Citation**: Blanco, G., Monopoli, T., D'Asaro, F., Peeters, R., Duan, X., Dimou, A., Rizzo, G. ESWC 2026 Resource Track.
**DOI**: 10.5281/zenodo.17812324
**Code**: https://github.com/links-ads/eswc26-artkb (MIT)

---

## Core Claim

An end-to-end modular knowledge base that unifies semantic RDF graphs, visual embeddings (vector DB), and binary digital assets (object storage) under a single API gateway, enabling hybrid symbolic + neural retrieval over cultural heritage data.

## Method

- **Source**: Wikidata — filtered to 7848 CH entity classes (artefacts, artists, museums, movements, genres, materials)
- **Ontology**: CACAO (Cultural Artefact Contextual Ontology) — domain-specific CIDOC-CRM extension with explicit CH subclasses + ODRL for rights
- **Pipeline**: Wikidata dump → type-based filtering → CACAO-aligned parsing → RDF triples; images retrieved from Wikimedia Commons → vectorised with SwinV2 → stored in Qdrant
- **Architecture**: GraphDB + MinIO + Qdrant + FastAPI gateway (SPARQL + GraphQL + REST)
- **Scale**: 8M triples, 1.4M entities, 82 classes, 307K physical artefacts, 76K artists, 2.5K museums, 147K images

## Key Findings / Features

1. **Semantic querying**: SPARQL + GraphQL endpoints; Text2SPARQL via Mistral (2-stage: LLM generates query with placeholders → SPARQL label lookup resolves entity IRIs)
2. **Neural image retrieval**: image-to-image, text-to-image (CLIP), composed image retrieval (MagicLens/LamRA)
3. **AI metadata suggestion**: SwinV2 embeddings → k-NN in Qdrant → similarity-weighted majority vote over neighbour metadata
4. **Text2RDF**: multi-agent LLM pipeline (Google ADK) — NER + coref + relation extraction → CACAO-compliant triples with self-reflective validity check

## Limitations

- Small scale (307K artefacts vs. GeMeA's 65M)
- Single source (Wikidata); no cross-institutional heterogeneity
- No web UI for non-technical users
- No named graphs (single flat graph, no provenance partitioning)
- No self-hosting documentation
- GraphDB is commercial (limits open deployment)
- No geo/temporal exploration views

## Relevance to GeMeA

**Cite in**: §2 Related Work (closest contemporary comparable), §1 Introduction (evidence of active CH KG space)

**Reuse ideas**:
- GraphQL endpoint alongside SPARQL (low effort, high frontend value)
- Text2SPARQL pattern for v2 (Mistral + 2-stage entity resolution)
- Qdrant as vector DB if visual search added later
- ODRL for machine-readable rights (post-v1)

**Differentiate on**:
- Scale: 200× more objects
- Scope: national, cross-domain (not just art)
- Web UI with map, timeline, graph viz
- mocho normalization across heterogeneous institutional metadata
- Named graph provenance per provider
- Explicit self-hosting (Docker + docs)
- Ontology: RDA/EDM (appropriate for library/archive collections) vs. CACAO/CIDOC-CRM (appropriate for art museums)

## BibTeX

```bibtex
@inproceedings{blanco2026artkb,
  title     = {{ArtKB}: A Multimodal Art Knowledge Base for Cultural Heritage},
  author    = {Blanco, Giacomo and Monopoli, Tommaso and D'Asaro, Federico and
               Peeters, Ruben and Duan, Xuemin and Dimou, Anastasia and Rizzo, Giuseppe},
  booktitle = {The Semantic Web -- ESWC 2026},
  year      = {2026},
  doi       = {10.5281/zenodo.17812324},
  url       = {https://github.com/links-ads/eswc26-artkb}
}
```

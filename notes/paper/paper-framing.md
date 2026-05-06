# Paper Framing Notes

**Date**: 2026-04-05
**Context**: Brainstorming session on GeMeA paper framing for ISWC 2026 Resource Track

---

## Proposed framing

**"Domain-specific, data-driven knowledge graph construction and enrichment using LLMs"**

---

## What works well

- **"Data-driven"** is well-supported: corpus profiling, field taxonomy, objecttype matching, and alignment methodology are all grounded in actual data before any modeling. The pipeline starts with `profile_edm_fields.py` and field-frequency analysis — not schema assumptions.
- **"Domain-specific"** is credible with mocho as the middle ontology. This is not generic KG construction — it works within a well-defined bibliographic/cultural heritage domain with established vocabularies (RDA, RiC-O, CIDOC-CRM, Music Ontology). The domain specificity justifies the middle-ontology architecture.
- **"Refinement using LLMs"** fits if LLMs are used for: agent role disambiguation (`affiliate`), language detection (Stage 2 of BCP 47 tagging), objecttype → mocho class resolution, or NER for title/contributor parsing.

---

## Where to be careful

- **"Construction and enrichment"** implies two distinct phases — the paper needs a clear boundary between them, otherwise reviewers will ask where one ends and the other begins. Define construction = alignment + ingest; enrichment = LLM-assisted passes adding new structured triples.
- **"Using LLMs"** needs precision about *where* in the pipeline. LLMs are one component among many (SPARQL, ontology reasoning, rule-based alignment, embedding matching). The framing risks overstating their role if the pipeline is mostly rule-based with LLMs handling edge cases.
- **ISWC Resource Track expectations**: the resource (KG + mocho) must be the primary contribution. LLM framing should support the resource description, not overshadow it. Reviewers will ask: what is the resource, is it available, is it useful?

---

## Suggested framing adjustment

Keep the proposed framing as a *pipeline characterisation*, not the top-level contribution claim. Suggested title direction:

> *"GeMeA: Data-driven construction of a multi-modal cultural heritage knowledge graph using a WEMI-aligned middle ontology"*

With LLM-assisted enrichment named explicitly as a pipeline component in the abstract and §3 (Pipeline). This keeps the resource front and center and positions LLMs as a method, not the contribution.

---

## Relationship to existing paper-outline.md

The current core argument in `paper-outline.md`:
> "GeMeA fills a critical gap by providing the first open, SPARQL-accessible knowledge graph over the complete German Digital Library corpus (65M objects), normalizing heterogeneous EDM metadata to a unified RDA/FRBR model and exposing it through a full-featured web interface."

The new framing adds: *how* the normalization is done (data-driven, domain-specific, LLM-assisted) as a methodological contribution alongside the resource contribution. This strengthens the paper for tracks that value reproducibility and methodology, not just resource availability.

---

## Open questions

- `- []` Where exactly do LLMs enter the pipeline? Enumerate the specific steps: role disambiguation, language detection, objecttype resolution, NER — confirm which are implemented vs. planned
- `- [x]` **"Enrichment"** is the right word — LLM passes add new structured triples (role disambiguation, NER, objecttype resolution), not correct existing ones. Update "refinement" → "enrichment" in framing and title direction above.
- `- []` Reconcile with `paper-outline.md` core argument — update once framing is settled

---

## § Research testbed framing

GeMeA is not a curated benchmark — it is a knowledge graph built from in-use institutional data. This is the source of its research value: the heterogeneity is real, the gaps are real, and the alignment challenges are real. Intended downstream research use cases (not yet demonstrated):

- **Knowledge graph-grounded retrieval** — retrieval over structured cultural heritage metadata
- **Ontological evaluation** — using the MOCHO-aligned subgraph as an evaluation surface
- **Knowledge graph embeddings** — entity and relation embeddings over a large, heterogeneous real-world graph; GeMeA's RDA-decomposed title representation enables empirical comparison of *literal granularity* strategies: does one rich `dc:title` literal outperform several typed RDA relations (`titleProper`, `subtitle`, `variantTitle`) for downstream KGE tasks (link prediction, entity alignment)? This structuring question is unaddressed in the KGE-with-literals literature (LiteralE, DKRL, KEPLER)
- **Explainability** — reasoning over structured provenance and entity links
- **Agentic knowledge graph access** — LLM agents querying via MCP/MCPO
- **Continuous MOCHO refinement** — GeMeA as a living evaluation surface for iterative ontology development

Framing note: describe these as *intended* use cases enabled by the resource, not completed experiments.

---

## § Core methodological motivation

Because sectors interpret the semantics of EDM properties and property values differently — `dc:type` carries controlled-vocabulary terms in library records, free-text strings in museum records, and structural hierarchy identifiers in archive records — no schema-level or structure-based alignment tool can recover these conventions from the schema specification alone. Automatic alignment and transformation can therefore only be achieved through corpus-based analysis at two levels: **coarse-grained** (sector × mediatype stratification to determine which signals are available and reliable per stratum) and **fine-grained** (value distribution analysis within each stratum to discover the actual semantics in use). This is the methodological foundation of the GeMeA alignment approach and the principal justification for the data-driven framing.

---

## § Official justification

**Conference scope.** GeMeA is built on W3C Semantic Web standards throughout — RDF/EDM input, OWL ontology (MOCHO), QLever SPARQL triplestore, Linked Data browser (SHMARQL), and ontology alignment to RDA/FRBR, CIDOC-CRM, and RiC-O. The contribution is squarely within the CfP's stated focus: "knowledge representation based on Semantic Web standards to improve the acquisition, processing, and sharing of data on the web."

**Track fit.** The CfP is explicit: "papers describing concrete resources (knowledge graphs, ontologies, etc.) should be submitted to the resources track." GeMeA proposes no new algorithm (not Research) and is not an application of existing SW technology in a practical setting (not In-Use) — it *is* the resource.

**Impact.** The DDB aggregates 65M objects from Germany's archives, libraries, museums, and media libraries, yet provides no public SPARQL endpoint, no Linked Data interface, and no graph-accessible representation. GeMeA fills this gap as the first open, SPARQL-accessible KG over the DDB corpus, and the MOCHO-based alignment layer advances the state of the art for multi-ontology alignment of heterogeneous EDM metadata at scale.

**Reusability & Reproducibility.** Three access modalities serve distinct user groups — SPARQL (SW researchers), Linked Data browser (DH practitioners), MCP/MCPO interface (LLM/agent developers) — each with CC BY 4.0 licensing, a live endpoint, and public source code. Scope boundaries are documented rather than suppressed, and a usage section with SPARQL examples directly addresses reproducibility.

**Design & Technical Quality.** The resource reuses and extends established high-quality artifacts (EDM, RDA/FRBR, CIDOC-CRM, RiC-O, Music Ontology), which the CfP highlights as best practice for ontology contributions. The data-driven alignment methodology — corpus profiling before modeling, not schema projection — reflects sound design discipline.

**Availability.** The resource is publicly accessible via a live SPARQL endpoint and Linked Data browser at `gemea.ise.fiz-karlsruhe.de`, with source code on GitHub and a CC BY 4.0 data license. The three mandatory requirements (persistent URI, canonical citation, license) must be confirmed before the 7 May deadline — ensure a w3id or DOI is in place.

**Risk.** The MCP/MCPO agentic interface is novel enough that a reviewer might ask whether this belongs in the In-Use track. Frame it in the paper as an *access layer of the resource*, not as a standalone application contribution, to keep the submission clearly in Resource Track territory.

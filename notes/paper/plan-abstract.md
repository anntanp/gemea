# GeMeA — Abstract Draft

**Date**: 2026-04-18
**Title**: GeMeA: Knowledge Graph Testbed for 23M+ German Cultural Heritage Objects
**Track**: ISWC 2026 Resource Track

---

## v1

The German Digital Library (DDB) exposes 65 million cultural heritage objects as richly structured metadata, yet no open knowledge graph or SPARQL endpoint exists over this corpus. GeMeA addresses this gap by providing the first openly accessible knowledge graph over 23M+ DDB objects, built from Europeana Data Model (EDM) records and deployed on QLever — a high-performance SPARQL engine — with SHMARQL as a lightweight Linked Data browser and an MCP/MCPO interface enabling direct integration with agentic AI workflows. To our knowledge, GeMeA is the first cultural heritage knowledge graph to expose an MCP-native access layer alongside a public SPARQL endpoint.

Beyond raw EDM data, GeMeA includes a proof-of-concept ontology alignment layer using mocho, a middle ontology that maps heterogeneous EDM metadata to RDA/FRBR, demonstrating data-driven KG construction and enrichment. Partial entity linking to GND authority records is performed via rule-based ISBD title extraction against a local GND SPARQL index, with coverage statistics reported as an honest baseline for future NER-augmented extensions.

GeMeA is designed as a multi-disciplinary research testbed. It supports ontology evaluation research on a large real-world aligned subgraph, agentic KG framework development via its MCP interface, investigation of RML-based declarative mapping as an alternative to the current procedural pipeline, and provenance modelling of LLM-assisted enrichment steps using PROV-O extensions. All data is published under CC BY 4.0; code, SPARQL endpoint, and Linked Data browser are openly accessible at [URI].

---

## v2

**Prompt**: make it much shorter and brief. emphasize only the details that strengthens the contributions of the paper.

GeMeA is the first openly accessible knowledge graph over 23M+ German Digital Library objects, combining a public SPARQL endpoint (QLever), a Linked Data browser (SHMARQL), and an MCP-native interface — the first of its kind for cultural heritage KGs. It includes a proof-of-concept ontology alignment layer (mocho, EDM → RDA/FRBR) with rule-based GND entity linking, and is designed as a multi-disciplinary research testbed for ontology evaluation, agentic KG frameworks, RML mapping, and LLM enrichment provenance. All data is CC BY 4.0; resources available at [URI].

---

## v3

**Prompt**: write v3 in the same note. avoid the ai-slop characteristics listed in /Users/mta/Documents/claude/babel-ddb/notes/anti-ai-slop.md

GeMeA is a publicly accessible knowledge graph over 23M+ objects from the German Digital Library (DDB), queryable via SPARQL (QLever), browsable via SHMARQL, and accessible to AI agents through an MCP interface — a combination not previously available for cultural heritage data at this scale. The resource includes a mocho-based ontology alignment layer mapping DDB EDM metadata to RDA/FRBR, with partial GND entity linking via rule-based ISBD title extraction. GeMeA is released as a research testbed for work on ontology evaluation, agentic KG applications, RML-based declarative mapping, and provenance modelling of LLM-assisted enrichment. Data is licensed CC BY 4.0; the SPARQL endpoint, Linked Data browser, and source code are available at [URI].

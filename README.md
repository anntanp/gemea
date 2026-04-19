# GeMeA — Knowledge Graph Testbed for 23M+ German Digital Library Objects

**Track**: ISWC 2026 Resource Track &nbsp;|&nbsp; **License**: CC BY-SA 4.0 &nbsp;|&nbsp; **SPARQL**: _endpoint TBD_

---

## Abstract

We present GeMeA, a publicly accessible knowledge graph over 23M+ objects from the German Digital Library (DDB), queryable via SPARQL (QLever), browsable via SHMARQL, and accessible to AI agents through an MCP interface — a combination not previously available for cultural heritage data at this scale. The resource includes a mocho-based ontology alignment layer mapping DDB EDM metadata to RDA/FRBR, with partial GND entity linking via rule-based ISBD title extraction. GeMeA is released as a research testbed for work on ontology evaluation, agentic KG applications, RML-based declarative mapping, and provenance modelling of LLM-assisted enrichment. Data is licensed CC BY-SA 4.0; the SPARQL endpoint, Linked Data browser, and source code are available at [URI].

---

## Access

| Interface | URL | Description |
|-----------|-----|-------------|
| SPARQL endpoint | `http://[host]:42004` | QLever — EDM KG (23M+ objects) |
| Linked Data browser | `http://[host]:42003` | SHMARQL |
| MCP interface | `http://[host]:42005` | MCPO — agentic AI access |
| GND SPARQL | `http://[host]:42006` | QLever — GND Werk / Person / CorporateBody |

---

## Testbed Use Cases

GeMeA is designed as a multi-disciplinary research testbed. Four named research avenues:

1. **Ontology evaluation** — large real-world aligned subgraph via the mocho PoC (EDM → RDA/FRBR); suitable for evaluating alignment quality and completeness on cultural heritage data at scale.

2. **Agentic KG frameworks** — MCP-native access layer, the first of its kind for cultural heritage KGs; supports development of AI agents that query, navigate, and reason over linked cultural heritage data.

3. **RML declarative mapping** — applicability study of RML-based declarative mapping as an alternative to the current procedural pipeline; GeMeA's EDM-to-RDF transformation is a concrete target use case.

4. **LLM enrichment provenance** — PROV-O extensions (Prov-LM) for modelling the provenance of LLM-assisted KG enrichment steps; GeMeA's entity linking and alignment pipeline provides the enrichment trace.

---

## Pipeline

```
DDB JSON-LD → rdf2jsonld → link_gnd_works.py → mocho (EDM→RDA/FRBR) → QLever + SHMARQL + MCPO
```

---

## Repository Layout

```
gemea/
├── scripts/sh/     Setup and deployment shell scripts
├── scripts/py/     Python pipeline scripts
├── ingest/         QLever load modules
├── data/           Raw and processed data (large files tracked via DVC)
├── docker/         Docker Compose configs
├── paper/          ISWC 2026 paper — see paper/iswc-2026 branch for LaTeX source
└── resource/       Published artifact metadata (VoID descriptor, w3id)
```

**v2 (planned)**: Elasticsearch full-text search, Next.js KG browser, FastAPI + GraphQL layer.

---

## Branches

See [`notes/project/git-branching-strategy.md`](notes/project/git-branching-strategy.md) for the full branch map.

| Branch | Purpose |
|--------|---------|
| `main` | Stable public record — tagged at each ISWC deadline |
| `develop` | Active development — code, experiments, research notes |
| `paper/iswc-2026` | LaTeX source for the ISWC 2026 submission |
| `releases` | Zenodo snapshots, versioned KG dumps, VoID releases |
| `hotfix` | Post-submission corrections |
| `meetings` | Research meeting slides (Beamer) — orphan branch, never merges |

---

## Resource

| Field | Value |
|-------|-------|
| Persistent URI | TBD — w3id or Zenodo DOI (registered before May 2, 2026) |
| License | CC BY-SA 4.0 |
| Paper | ISWC 2026 Resource Track |
| SPARQL endpoint | TBD |
| Data download | TBD |

---

## ISWC 2026 Deadlines

| Milestone | Date |
|-----------|------|
| Abstract submission | 2 May 2026 |
| Full paper (8–15 pp) | 7 May 2026 |
| Rebuttal | 11–18 June 2026 |
| Notification | 16 July 2026 |
| Camera-ready | 6 August 2026 |
| Conference | 27–29 October 2026 |

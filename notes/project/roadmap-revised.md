# GeMeA — Revised Roadmap (Bare-Minimum ISWC 2026 Submission)

**Date**: 2026-04-18
**Context**: Time pressure + mocho.owl instability → scaled-down submission targeting ISWC 2026 Resource Track (abstract 2 May, paper 7 May)

---

## 1. Scope

**In scope (v1 — this paper):**
- [26M DDBEDM objects](https://github.com/anntanp/gemea/blob/develop/notes/project/ddb-27m.md) in QLever with public SPARQL endpoint
- Mocho PoC in QLever (ontology alignment on a representative subset)
- **SHMARQL** — lightweight Linked Data publishing layer over QLever; provides browsable web UI + `/sparql` endpoint with zero custom frontend development (Docker, `ghcr.io/epoz/shmarql`)
- MCP/MCPO interfaces on both QLever instances
- GND agent linking described as pipeline component (v1.1); not implemented in v1

**Deferred to v2 (explicitly out of scope for this paper):**
- Elasticsearch + faceted search
- Next.js KG browser frontend (SHMARQL serves as the v1 browsing interface)
- Full 65M object corpus
- FastAPI / GraphQL API (replaced by MCP/MCPO as the novel access story)
- GND Works linking (Phase 0 NER pipeline)

---

## 2. Framing

**Core claim:**
> GeMeA provides the first openly browsable, SPARQL-accessible, and MCP-accessible knowledge graph over the German Digital Library corpus (26M objects), deployed via QLever and SHMARQL, with a mocho-based ontology alignment PoC demonstrating data-driven KG enhancement, and serving as a testbed for LLM + KG research at cultural heritage scale.

**Note:** A "documented observations" / experience report framing was considered and dropped. The three contributions are the resource, the \texttt{mocho} alignment PoC, and the agentic access layer. Scope boundaries from the alignment are documented in §4 Quality as part of the resource description, not as a standalone contribution. NER (GND Works linking) was also dropped from scope: it is a separate problem, and the time pressure of the 7 May deadline makes it the wrong place to spend paper budget.

**Testbed positioning (LLM + KG research):**
- **Retrieval** — benchmark corpus for KG-grounded retrieval: SPARQL-assisted RAG, entity-linked QA over German CH metadata, hybrid text + structured query evaluation
- **Explainability** — provenance-tracked named graphs enable evaluation of KG-grounded explanations for LLM outputs
- **Embeddings** — 26M entities with rich relational structure support entity embedding research and link prediction benchmarks
- **Agentic KG** (`framework.trails`) — MCP/MCPO interface for development and evaluation of multi-step KG reasoning agents
- **Ontology evaluation** (`onto-eval`) — mocho-aligned subgraph with documented scope boundaries as a grounded evaluation target
- **Open question (no existing literature):** Does using verbose, descriptive ontology labels (e.g., `rda:dateOfPublication` vs. MARC codes) meaningfully affect LLM performance on KG tasks? GeMeA's mocho-aligned layer is a natural testbed for this question — worth noting as a research direction, not a prior-work claim.
- **Provenance** — enrichment pipeline traces (GND linking, mocho alignment) as a testbed for provenance modeling of LLM-assisted KG enhancement (PROV-O / Prov-LM extensions)
- **RML** — preliminary idea only, no experiments: the EDM → RDA/mocho mapping is a potential candidate for RML expression; deferred
- Full GeMeA KG browser (v2) — full-featured web UI over the same QLever backend

---

## 3. Current Status

| Component | Status |
|-----------|--------|
| QLever endpoint (115k objects, 8M triples) | **Local only** ⚠ (edm-goethe-faust.nt on local machine; not yet public) |
| Mocho PoC in QLever | **Running on subset** ✓ |
| SHMARQL over QLever | **Pattern proven** (goethe-faust); adapt `docker-compose.shmarql.yml` + `setup.sh` |
| MCP/MCPO on QLever | **Pattern proven** (`setup.sh mcp-add`); needs inventory of exposed tools |
| GND Werk Linking (`link_gnd_works.py`) | **blocked** — depends on Phase 0a NER + mocho.owl stability; rule-based ISBD pass (~28% coverage) possible without NER |
| GND Agent Linking (`link_gnd_agents.py`) | lower priority; deferred to v1.1 |
| Persistent URI (w3id / Zenodo DOI) | **needed before 2 May** |

### 3.1 ID corpus by sector (teach03)

| File | Sector | Ingested | IDs | Size (MB) |
|---|---|---|---|---|
| `ids_sec_01_digitalisat.txt` | Archive | [ 351,405 ] | 3,486,444 | 109.7 |
| `ids_sec_02_digitalisat.txt` | Library | [ x ] | 18,570,245 | 584.5 |
| `ids_sec_03_digitalisat.txt` | Monument Preservation | [ ] | 83,575 | 2.6 |
| `ids_sec_04_digitalisat.txt` | Research | [ ] | 1,223,929 | 38.5 |
| `ids_sec_05_digitalisat.txt` | Media Library | [ 1,309,130 ] | 1,799,840 | 56.7 |
| `ids_sec_06_digitalisat.txt` | Museum | [ x ] | 2,011,737 | 63.3 |
| `ids_sec_07_digitalisat.txt` | Others | [ ] | 89,904 | 2.8 |
| **Total** | | | **27,265,674** | **858.1** |

Source: `fetch-ids-by-sector.py` against DDB Solr API (`digitalisat:true`); files on `ise-d-teach03:/data/ddb/data/ids/`. See `notes/project/ddb-27m.md`.

---

## 4. Gaps to Close Before Abstract (2 May)

### 4.1 Stats from QLever
- Run `SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }` per named graph
- Record: object count, triple count, named graph inventory, provider count

### 4.2 Mocho PoC Description
- Subset size (how many CHOs?)
- Classes produced and triple count
- Mapping quality notes (direct vs. approximate)

### 4.3 Persistent URI
- Register w3id entry or Zenodo DOI
- Required for mandatory Resource Availability Statement

### 4.4 SHMARQL + MCP Adaptation for GeMeA
- Copy `docker-compose.shmarql.yml` and `setup.sh` from `goethe-faust/` (proven pattern)
- Point `DATA_LOAD_PATHS` at GeMeA NT files; adjust `INDEX_NAME`, ports, memory
- Run `./setup.sh mcp-add` to register QLever as Claude Code MCP server
- Capture screenshots of SHMARQL UI for §3.3 and §5 Usage section
- Inventory MCP tools exposed; prepare 2 example agent interactions for §3.4

---

## 5. Paper Structure

**LaTeX draft**: https://overleaf.epoz.org/project/69e62ea641be25a8280374bf



| Section | Content | Status |
|---------|---------|--------|
| §1 Introduction | Problem, gap, contribution, testbed framing | to write |
| §2 Related Work | ArtKB, Europeana LOD, BIBFRAME, DDB native UI; comparison table | mostly drafted |
| §3 Resource Description | EDM schema, QLever index stats, named graphs, VoID | needs stats (§4.1) |
| §3.2 Mocho PoC | Alignment approach, subset size, class coverage, output format | needs §4.2 |
| §3.3 SHMARQL Interface | Lightweight Linked Data browser over QLever; Docker deployment (adapted from goethe-faust); screenshots | needs §4.4 |
| §3.4 MCP/MCPO Layer | Novel access method via `mcp-server-qlever`; tools exposed; example agent interactions | needs §4.4 |
| §4 Quality & Validation | Triple count, URI repair rates, mocho mapping quality, known limitations | needs stats |
| §5 Usage & Reusability | SPARQL examples (×4), SHMARQL screenshots, MCP tool examples (×2), downstream use cases | to write |
| §6 Impact | DH + SW communities, testbed positioning, onto-eval + framework.trails | to write |
| §7 Sustainability | Versioning, w3id URIs, open source, mocho upstream dependency | to write |
| §8 Conclusion | | to write |
| Resource Availability Statement | Persistent URI + CC BY 4.0 + canonical citation | needs URI |

---

## 6. ISWC Resource Track — Non-Negotiable Requirements

| Requirement | Status |
|-------------|--------|
| Resource publicly accessible at review time | ⚠ QLever running locally only (edm-goethe-faust.nt); not yet public + SHMARQL browser (needs deploy) |
| VoID descriptor in paper | to write |
| Persistent URI registered | **before 2 May** |
| License statement (CC BY 4.0 for data) | ready |
| Resource Availability Statement | needs URI |
| Known limitations stated | to write (§4 Quality) |

---

## 7. Risks

**"PoC" framing**: Reviewers penalize papers that read as "we plan to do X." Mitigation: lead with what is deployed (QLever + SHMARQL + MCP — all proven on goethe-faust), frame the full KG browser explicitly as v2, include a limitations section. Honesty beats overselling.

**mocho upstream dependency**: mocho.owl is a dependency we don't control. Describe the PoC as-is; note the upstream status in limitations. Do not promise a full-corpus mocho alignment in this paper.

**Entity linking not started**: Not a blocker. The mocho alignment serves as the KG enhancement PoC. GND agent linking is described as a pipeline component and deferred to v1.1.

---

## 8. What Determines Acceptance

The Resource Track scores differently from a research paper. The following are ordered by weight.

**The one non-negotiable: the resource must be live when reviewers check it.**
Reviewers will click the URI. If the SPARQL endpoint returns an error, the paper is rejected regardless of writing quality. QLever endpoint, SHMARQL browser, and persistent URI must all be reachable before reviews come in.

**Acceptance-critical items, in order:**

1. **Persistent URI registered** — mandatory for the Resource Availability Statement. Must happen before the 2 May abstract, not the 7 May full paper. Single most time-critical item on the checklist.

2. **Concrete stats in §3** — every `\todo{}` placeholder in the scale paragraph is a red flag. Reviewers expect triple counts, object counts, named graph inventory. Claiming "26M objects" without a number in the paper reads as unverified.

3. **The PoC framing must be quantified** — the mocho alignment on a subset is acceptable, but only if §4 Quality clearly states what the subset covers and what it does not. A PoC without numbers fails the quality criterion. Scope boundaries need numbers, not only prose.

4. **SPARQL examples must run** — the four queries in §5 must work against the live endpoint. A reviewer who tries Query 1 and gets a SPARQL error reads everything else with suspicion.

5. **Workflow contribution must be backed by §3/§4 material** — contribution 4 (transformation workflow) differentiates GeMeA from a pure dataset paper. It only carries weight if §3 and §4 contain concrete material to support it. Describing the workflow in the abstract without grounding it in results reduces it to a claim.

**Critical path before 2 May:**
Register persistent URI → get QLever stats → submit abstract with real numbers.

SHMARQL screenshots, MCP tool inventory, and §4 Quality prose can follow before 7 May, but the resource must be accessible and core numbers must be real by abstract time.

---

## 9. Checklist

### Before abstract (2 May)

- [ ] Run QLever triple/object count per named graph; record in notes
- [ ] Document mocho PoC: subset size, classes produced, triple count, mapping quality
- [ ] Register persistent URI (w3id or Zenodo DOI)
- [ ] Adapt `docker-compose.shmarql.yml` + `setup.sh` from goethe-faust for GeMeA
- [ ] Run `./setup.sh mcp-add`; inventory MCP tools exposed
- [ ] Capture SHMARQL UI screenshots
- [ ] Draft abstract (core claim + scale + access methods + testbed framing)

### Before full paper (7 May)

- [ ] §1 Introduction
- [ ] §2 Related Work — finalize comparison table (ArtKB, Europeana LOD, BIBFRAME, DDB native UI)
- [ ] §3 Resource Description — EDM schema, QLever stats, named graphs, VoID descriptor
- [ ] §3.2 Mocho PoC — alignment approach, subset size, class coverage, output format
- [ ] §3.3 SHMARQL Interface — deployment description, screenshots
- [ ] §3.4 MCP/MCPO Layer — tools exposed, 2 example agent interactions
- [ ] §4 Quality & Validation — triple count, URI repair rates, mocho mapping quality, limitations
- [ ] §5 Usage & Reusability — 4 SPARQL examples, 2 MCP examples, downstream use cases
- [ ] §6 Impact — DH + SW communities, onto-eval, framework.trails, ddbkg
- [ ] §7 Sustainability — versioning, w3id URIs, open source, mocho upstream dependency noted
- [ ] §8 Conclusion
- [ ] Resource Availability Statement (persistent URI + CC BY 4.0 + canonical citation)
- [ ] Declaration of Use of Generative AI

---

## 10. Paper Milestones

| Date | Milestone |
|------|-----------|
| 2 May 2026 | Abstract submitted |
| 7 May 2026 | Full paper submitted (≤15 pp + references, LNCS) |
| 11–18 Jun 2026 | Rebuttal period |
| 16 Jul 2026 | Notification |
| 6 Aug 2026 | Camera-ready |
| 27–29 Oct 2026 | ISWC 2026 conference |

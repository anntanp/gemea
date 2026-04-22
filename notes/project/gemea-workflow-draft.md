# GeMeA — Pipeline Workflow

---

## 1. Ingest DDB

### 1.1 Solr ID fetch (per sector)

Cursor-based pagination against the DDB Solr API (`/search/index/search/select`) with `digitalisat:true` + `sector_fct:<sector>` filters, bypassing the 10,000-row `maxResultWindow` limit via `cursorMark`. One ID per line.

**Script:** [`scripts/utils/fetch-ids-by-sector.py`](https://github.com/anntanp/gemea/blob/main/scripts/utils/fetch-ids-by-sector.py)
**Output:** `ids_sec_0N_digitalisat.txt` on `ise-d-teach03:/data/ddb/data/ids/`
**Counts:** see [`notes/project/ddb-27m.md`](https://github.com/anntanp/gemea/blob/main/notes/project/ddb-27m.md) — 27,265,674 IDs across 7 sectors (858 MB total)

### 1.2 JSON download

Batch-fetch full DDB Item API JSON per ID list, one sector at a time. Output stored per sector on `ise-d-teach03`.

### 1.3 NT + Parquet export

Extract EDM metadata from cortex JSON (stored in SQLite as gzip-compressed blobs) → N-Triples for QLever + flat Parquet for analysis.

**Script:** [`scripts/py/export_ddb.py`](https://github.com/anntanp/gemea/blob/main/scripts/py/export_ddb.py) (single sector); [`scripts/sh/export_batch_remote.sh`](https://github.com/anntanp/gemea/blob/main/scripts/sh/export_batch_remote.sh) (all remaining sectors unattended)
**Outputs:** `edm_*.nt` + `sN_meta.parquet` under `/data/ddb/nt/sN/`
**Status:** Sector 2 done; s1, s3–s7 in progress. See [`notes/infra/ddb-all-sectors-export-plan.md`](https://github.com/anntanp/gemea/blob/main/notes/infra/ddb-all-sectors-export-plan.md)

---

## 2. Transform — two alternative paths

These are parallel branches applied to different use cases, not sequential steps.

### 2a. Transform only (no alignment)

**Use case:** NER corpus — flat Parquet for title analysis and NER training data. No ontology alignment needed.

| Step | Script | Output |
|---|---|---|
| htype + language filter | `scripts/analysis/filter_de_content.py` | `sN_meta_de_content.parquet` |
| tokenize | `scripts/analysis/tokenize_de_titles.py` | `de_titles_tokenized.parquet` |

Detailed pipeline for Sector 2: [`notes/project/reprocessing-workflow.md`](https://github.com/anntanp/gemea/blob/main/notes/project/reprocessing-workflow.md)

### 2b. Align + Transform

**Use case:** QLever ingest — full EDM → RDA alignment to produce `mocho:Work` groupings and RDA-mapped predicates.

#### 2b.i Data-driven alignment (GeMeA / mocho)

mocho ([`../mocho/`](https://github.com/anntanp/mocho)) reads rdf2jsonld output + GND Werk triples from Phase 0, groups `edm:ProvidedCHO` instances into `mocho:Work` entities, and maps EDM predicates to RDA terms. Outputs N-Triples per provider.

**Upstream dependency:** [`scripts/py/link_gnd_works.py`](https://github.com/anntanp/gemea/blob/main/scripts/py/link_gnd_works.py) must run first (Phase 0) to produce GND Werk links that mocho uses for Work grouping.

**⚠ Blocked:** mocho.owl is WIP. Pipeline cannot run end-to-end until mocho.owl stabilizes.

#### 2b.ii Open question: procedural (mocho) vs. RML

| Option | Description | Trade-offs |
|---|---|---|
| **mocho (procedural)** | Current approach — Groovy/Java tool; GeMeA does not own it | WIP; external dependency; hard to modify |
| **RML mappings** | Declarative EDM → RDA rules (R2RML/RML); engine: RMLMapper or Morph-KGC | Portable, auditable, no external codebase dependency; requires authoring full mapping ruleset |

**Status:** Unresolved. Decision needed before Phase 1 can run at scale. ADR to be filed under [`notes/adr/`](https://github.com/anntanp/gemea/blob/main/notes/adr/).

---

## 3. Enhancement

Post-ingest enrichment written to QLever named graph `http://gemea.ddb.de/graph/gnd-enrichment`.

| Task | Script | Phase |
|---|---|---|
| GND Werk linking (title → `gndo:Work`) | [`scripts/py/link_gnd_works.py`](https://github.com/anntanp/gemea/blob/main/scripts/py/link_gnd_works.py) | Phase 0 (pre-mocho) |
| GND agent linking (persons + corporate bodies) | `ingest/link_gnd_agents.py` | Phase 1b (post-load) |

See [`notes/project/roadmap.md §Phase 1b`](https://github.com/anntanp/gemea/blob/main/notes/project/roadmap.md) for deliverables and milestone.

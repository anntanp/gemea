# VPS Setup Plan — GeMeA Production Deployment

**Date**: 2026-04-30
**Context**: ISWC 2026 Resource Track — resource must be publicly accessible when reviewers check it (abstract 2 May, full paper 7 May, reviews ~June 2026). Permanent deployment thereafter.

---

## 1. Architecture decision: 1 QLever + named graphs

EDM and mocho data go into **one QLever instance** as separate named graphs, not two
separate instances.

**Why**: The comparison goal requires cross-graph JOINs. With two instances you need
SPARQL federation (`SERVICE`), which adds network overhead and query complexity. With
named graphs, a single query compares both representations:

```sparql
SELECT ?cho ?edmTitle ?mochoTitle WHERE {
  GRAPH <http://gemea.ddb.de/graph/edm>   { ?cho dc:title ?edmTitle }
  GRAPH <http://gemea.ddb.de/graph/mocho> { ?cho rdac:P10088 ?mochoTitle }
}
```

Additional benefits: one SPARQL endpoint, one persistent URI, one MCP server config,
~10–20% index overhead (4th quad column) vs ~2× RAM for two full indexes.

The only case for 2 instances is staged deployment (EDM live while mocho indexes).
Since both NTs land ~8 May and the combined index builds in one shot, this is not
needed here.

### Named graph URIs

| Named graph | Contents | Phase |
|---|---|---|
| `http://gemea.ddb.de/graph/edm` | Source EDM triples (`edm*.nt`) | v1 |
| `http://gemea.ddb.de/graph/mocho` | mocho-transformed triples (`mocho*.nt`) | v1 |
| `http://gemea.ddb.de/graph/work` | GND Werk linking enrichment (`link_gnd_works.py` output) | v1.1 |
| `http://gemea.ddb.de/graph/provenance` | PROV-O traces for pipeline enrichment steps | v1.1 |
| `http://gemea.ddb.de/graph/view-field` | Additional CHO properties from `view.item.fields[].field[]` in the DDB JSON (display-layer fields rendered on the DDB item page: `id`, `name`, `value[].content`, `value[].creditline`, `value[].resource`, `value[].rightsinfo`, `georeference`) | v1.1 |

v1 graphs (EDM + mocho) are the ISWC submission scope. v1.1 graphs load into the same
QLever instance when ready — no re-indexing of v1 data required, only appending.

## 2. Services

| Service | Role | Port |
|---|---|---|
| QLever | Single SPARQL endpoint, two named graphs (EDM + mocho) | 7020 |
| SHMARQL | Linked Data browser + `/sparql` proxy over QLever | 7032 |
| MCP/MCPO | QLever exposed as MCP server (via `mcp-server-qlever`) | 8001 |
| Ollama | LLM inference (gemma4:e4b baseline; GPU-optional) | 11434 |
| OpenWebUI | Chat UI + native SPARQL tool | 3000 |
| **NT dump download** | Static HTTP file server serving `edm*.nt` + `mocho*.nt` | 80/443 |

NT files are served directly from the VPS — the same pattern as the GND service dumps.
NTs are **permanent on-disk** (not archived to object storage); the VPS is the canonical
download location referenced in the Resource Availability Statement.

Pattern proven on `goethe-faust/`; adapt `docker-compose.shmarql.yml` and `setup.sh`.

---

## 3. Scale estimates

**Basis**: goethe-faust corpus (115,432 records). Scale factor: 27M / 115,432 = **233×**.

mocho entity types (Agent, Place, Concept) deduplicate by URI and do not scale 233×
— they scale ~5–20× with corpus breadth. ProvidedCHO + Aggregation scale linearly.

### 3.1 NT file sizes

| File | goethe-faust | At 27M records | Triples at scale |
|---|---|---|---|
| `edm*.nt` | 1.3 GB | ~300 GB | ~2B |
| `mocho*.nt` (CHO+Agg only, current partial) | 8.2 GB (47M triples) | ~1.9 TB | ~11B |
| `mocho*.nt` (all entities, final revised plan) | ~10 GB est. | ~2.2 TB | ~12B |
| JSON source (DDB items) | 2.4 GB | ~560 GB | — |

The revised transform plan (`transform-revised-plan.md`) adds WebResource, Agent, Place,
Concept, PhysicalThing, TimeSpan entities. These add ~15–30 GB at scale (not another TB)
due to URI deduplication.

### 3.2 QLever index size (single instance, two named graphs)

Source: QLever VLDB 2022 benchmarks (Wikidata 6.7B triples → 630 GB index ≈ 94 bytes/triple compressed).
Named graph column (4th quad field) adds ~10–20% vs a triple-only index.

| Input | Triples | Index on disk | RAM to query |
|---|---|---|---|
| EDM named graph | ~2B | ~190 GB | ~50 GB |
| mocho named graph | ~12B | ~1.1 TB | ~170 GB |
| **Combined (EDM + mocho)** | **~14B** | **~1.3–1.4 TB** | **~220–240 GB** |

### 3.3 Storage totals

NTs are permanent (served as downloads from the VPS) — no archiving off-server.

| Phase | Contents | Total |
|---|---|---|
| **Build-time peak** | JSON 560 GB + edm NT 300 GB + mocho NT 2.2 TB + indexes 1.3 TB | **~4.5 TB** |
| **Steady state** | edm NT 300 GB + mocho NT 2.2 TB + indexes 1.3 TB + models/OS 100 GB | **~3.9 TB** |

JSON source can be archived to Hetzner Object Storage after indexing (~€0.01/GB/month)
to reclaim ~560 GB, bringing steady state to ~3.4 TB.

---

## 3. Index build time estimates

Two-stage index build to match the deployment timeline:

**Stage A — pilot corpus (goethe-faust, ~1–2 May)**

| Step | Estimated time |
|---|---|
| Upload goethe-faust NTs to VPS (~9.5 GB) | ~5 min |
| QLever pilot index build (~47M triples) | ~10–30 min |
| **Pilot endpoint live** | **< 1 hr** |

**Stage B — full corpus (~8–10 May)**

| Step | Estimated time |
|---|---|
| Upload full NTs to VPS (1 Gbps, ~2.5 TB) | ~6–8 hrs |
| QLever full-corpus index build (EDM + mocho, ~14B triples) | ~12–20 hrs |
| **Full endpoint live** | **~18–28 hrs after upload starts** |

**Transform pipeline on VPS** (alternative if pre-built NTs are unavailable):
Single-threaded Python: ~3–6 days for 27M records.
Parallelized per sector (7 sectors): ~12–24 hrs with sector-level multiprocessing.

---

## 4. Hardware specifications

### 4.1 Minimum — ISWC review window

Sufficient for ISWC reviewer load (~2–5 concurrent SPARQL queries). CPU Ollama
(gemma4:e4b at ~5–15 tok/s on modern server CPU) is acceptable for demos.

| Component | Spec | Notes |
|---|---|---|
| CPU | 32 cores (AMD EPYC or Xeon) | QLever query parallelism |
| RAM | **256 GB** | QLever mocho ~170 GB + EDM ~50 GB + Ollama ~8 GB + headroom |
| NVMe | **6 TB** | Steady state 3.9 TB (NTs permanent); 6 TB leaves build headroom |
| GPU | None | CPU Ollama; upgrade in Phase 2 |
| Network | 1 Gbps unmetered | |
| OS | Ubuntu 24.04 LTS | |

256 GB RAM is the hard floor. 6 TB NVMe is the hard floor (3.9 TB steady state + build headroom).

### 4.2 Ideal — permanent public deployment

| Component | Spec | Notes |
|---|---|---|
| CPU | 64 cores (AMD EPYC 9554P or equivalent) | |
| RAM | **384–512 GB** | Both QLever instances fully hot-cached + Ollama GPU offload |
| NVMe | **8–10 TB** | NTs permanent (download service) + re-indexing headroom |
| GPU | 24 GB VRAM (NVIDIA A10 or RTX 4090) | Ollama at ~50–100 tok/s |
| Network | 10 Gbps | |

---

## 5. German provider options

Digital sovereignty requirement: server in Germany (GDPR / DSGVO-compliant).

### 5.1 Hetzner Dedicated (Nuremberg / Falkenstein)

Best price/performance. BSI-certified datacenters. **No GPU on dedicated servers** —
use a separate Hetzner Cloud GPU instance for Ollama if needed.

| Config | RAM | NVMe | Est. price |
|---|---|---|---|
| AX162-R | 256 GB | 2× 1.92 TB | ~€240/month |
| AX162-R + 2 addon drives | 256 GB | ~6 TB total | ~€320/month |
| Custom root server | 256–512 GB | up to 10 TB | ~€350–500/month |

Hetzner Object Storage: S3-compatible, ~€0.01/GB/month — use for NT archiving.

Hetzner Cloud GPU (Frankfurt): GX2-120 with A40 48 GB VRAM at ~€2.30/hr reserved
— viable as a separate Ollama-only VM if GPU inference is required before a full
dedicated GPU server is justified.

### 5.2 OVHcloud (Strasbourg / Frankfurt)

GPU dedicated servers available. More expensive than Hetzner for CPU-only.

| Config | RAM | Storage | GPU | Est. price |
|---|---|---|---|---|
| Advance-3 | 192 GB | 4× 3.84 TB NVMe | none | ~€350/month |
| Advance-4 | 384 GB | 4× 3.84 TB NVMe | none | ~€500/month |
| GPU-3 | 192 GB | 2× 1.92 TB NVMe | 1× A100 40 GB | ~€1,400/month |

Advance-3 RAM (192 GB) is below the 256 GB floor — avoid for this workload.

### 5.3 IONOS (Frankfurt — German company, DSGVO-native)

- Dedicated Pro: up to 512 GB RAM, 4–8 TB NVMe, ~€400–600/month
- GPU cloud instances available separately
- Good option if DSGVO-native company ownership matters

### 5.4 Netcup (Karlsruhe)

Storage-optimized, cheapest bulk NVMe. RAM tops out at 256 GB on standard configs.
Suitable if cost is the primary constraint and 256 GB RAM is acceptable.

---

## 6. Recommended path

### Phase 1 — Provision now (2026-04-30)

**Hetzner AX162-R + 2 additional NVMe addon drives** (~6 TB total, ~€320/month).

Order today: provisioning takes hours, NTs must be on the VPS by **2–3 May**.

| Date | Milestone |
|---|---|
| 30 Apr | Order server; begin goethe-faust NT upload as pilot |
| 1–2 May | VPS live; pilot NTs (goethe-faust `edm*.nt` + `mocho*.nt`) served via HTTP; QLever index on pilot corpus running; SHMARQL accessible |
| 2 May | **Abstract submitted** — resource URL points to live VPS |
| 8 May | Full 27M NTs ready; upload to VPS |
| 9–10 May | QLever full-corpus index build (~18–28 hrs); endpoint updated |
| Before 7 May paper | SHMARQL screenshots captured, MCP tool inventory done |

CPU Ollama (gemma4:e4b) is adequate for the review window.

### Phase 2 — After ISWC notification (July 2026)

If accepted: add Hetzner Cloud GPU instance for Ollama, or migrate to OVHcloud
Advance-4 (384 GB RAM, 15 TB NVMe) for single-machine ideal spec.

---

## 7. Open questions

- [x] Persistent URI: w3id (redirects to VPS) — register before 2 May
- [x] NT versioning: date-stamped filenames + `latest/` symlink
- [x] NT download format: `.nt.gz`
- [ ] Ollama model beyond gemma4:e4b for the public phase?
- [ ] `graph/view-field`: predicate mapping for `view.item.fields[].field[]` — defer to post-submission

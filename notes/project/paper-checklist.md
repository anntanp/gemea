# GeMeA — ISWC 2026 Paper Checklist

**Deadlines**: Abstract 2 May · Full paper 7 May · Camera-ready 6 Aug 2026

Ordered by priority and difficulty within each bucket. Blocking tasks first, then hardest-first.

---

## §0 Prerequisites

Files and infrastructure that must exist before tasks can proceed. Ordered by urgency.

**Sector 2 (available)**
- [x] [P01](p01-s2-edm-nt.md) `data/out/s2/edm_00_0000.nt` … `edm_07_0023.nt` (192 files, ~326 GB) → T02, T03, T08
- [x] [P02](p02-s2-meta-parquet.md) `data/out/s2/s2_meta.parquet` (3.2 GB) → T05, T08

**Remaining sectors (v2 — note in §4 limitations)**
- [ ] [P03](p03-s1-edm-nt.md) `data/out/s1/edm_*.nt`
- [ ] [P04](p04-s3-edm-nt.md) `data/out/s3/edm_*.nt`
- [ ] [P05](p05-s4-edm-nt.md) `data/out/s4/edm_*.nt`
- [ ] [P06](p06-s5-edm-nt.md) `data/out/s5/edm_*.nt`
- [ ] [P07](p07-s6-edm-nt.md) `data/out/s6/edm_*.nt`
- [ ] [P08](p08-s7-edm-nt.md) `data/out/s7/edm_*.nt`
- [ ] [P09](p09-s1-meta-parquet.md) `data/out/s1/s1_meta.parquet`
- [ ] [P10](p10-s3-meta-parquet.md) `data/out/s3/s3_meta.parquet`
- [ ] [P11](p11-s4-meta-parquet.md) `data/out/s4/s4_meta.parquet`
- [ ] [P12](p12-s5-meta-parquet.md) `data/out/s5/s5_meta.parquet`
- [ ] [P13](p13-s6-meta-parquet.md) `data/out/s6/s6_meta.parquet`
- [ ] [P14](p14-s7-meta-parquet.md) `data/out/s7/s7_meta.parquet`

**GND (available)**
- [x] [P15](p15-gnd-werk-nt.md) `data/gnd/nt/werk.nt` (1.6 GB) → T03
- [x] [P16](p16-gnd-werk-jsonld.md) `data/gnd/authorities-gnd-werk_lds.jsonld.gz` (89 MB) → T03
- [x] [P17](p17-gnd-person-jsonld.md) `data/gnd/authorities-gnd-person_lds_20260217.jsonld.gz` (1.4 GB) → T03
- [x] [P18](p18-gnd-koerperschaft-jsonld.md) `data/gnd/authorities-gnd-koerperschaft_lds.jsonld.gz` (215 MB) → T03
- [x] [P19](p19-gnd-geografikum-jsonld.md) `data/gnd/authorities-gnd-geografikum_lds.jsonld.gz` (44 MB) → T03
- [x] [P20](p20-gnd-entityfacts-jsonld.md) `data/gnd/authorities-gnd_entityfacts.jsonld.gz` (1.3 GB) → T03

**Goethe-Faust PoC (available)**
- [x] [P21](p21-goethe-faust-edm-nt.md) `../goethe-faust/output/ddbedm-goethe-faust.nt` (1.3 GB, 8.6M triples) → T02, T03
- [x] [P22](p22-goethe-faust-mocho-nt.md) `../goethe-faust/output/mocho-goethe-faust.nt` (21 MB, 115K triples) → T05, T12

**Infrastructure (missing — blocks abstract)**
- [ ] [P23](p23-setup-sh.md) `setup.sh` — adapt from `../goethe-faust/setup.sh` → blocks T02, T04
- [ ] [P24](p24-docker-compose-qlever.md) `docker-compose.qlever.yml` — adapt from `../goethe-faust/` → blocks T02, T04, T06
- [ ] [P25](p25-docker-compose-shmarql.md) `docker-compose.shmarql.yml` — adapt from `../goethe-faust/` → blocks T02, T06
- [ ] [P26](p26-qlever-endpoint.md) QLever endpoint — running with goethe-faust EDM; full s2 ingest (26M objects) still needed → blocks T03, T04, T08, T11

---

## §8.1 Before abstract (2 May)

- [ ] T01 `[medium]` Register persistent URI (w3id or Zenodo DOI) — blocks Resource Availability Statement
- [ ] T02 `[hard]` Adapt `docker-compose.shmarql.yml` + `setup.sh` from goethe-faust for GeMeA — blocks §3.3, §3.4, screenshots
- [ ] T03 `[easy]` Run QLever triple/object count per named graph; record in notes (→ §3, §4)
- [ ] T04 `[easy]` Run `./setup.sh mcp-add`; inventory MCP tools exposed (→ §3.4) — after T02
- [ ] T05 `[medium]` Document mocho PoC: subset size, classes produced, triple count, mapping quality (→ §3.2)
- [ ] T06 `[easy]` Capture SHMARQL UI screenshots (→ §3.3, §5) — after T02
- [ ] T07 `[easy]` Finalise and submit abstract — v3 ready; insert URI from T01

## §8.2 Before full paper (7 May)

- [ ] T08 `[hard]` §4 Quality & Validation — triple count, URI repair rates, mocho mapping quality, known limitations
- [ ] T09 `[medium-hard]` §1 Introduction — problem, gap, contribution, testbed framing
- [ ] T10 `[medium]` §3 Resource Description — EDM schema, QLever stats, named graphs, VoID descriptor
- [ ] T11 `[medium]` §3.4 MCP/MCPO Layer — tools exposed, 2 example agent interactions
- [ ] T12 `[medium]` §3.2 Mocho PoC — alignment approach, subset size, class coverage, output format
- [ ] T13 `[medium]` §5 Usage & Reusability — 4 SPARQL examples, 2 MCP examples, downstream use cases
- [ ] T14 `[medium]` §2 Related Work — finalise comparison table (ArtKB, Europeana LOD, BIBFRAME, DDB native UI)
- [ ] T15 `[easy-medium]` §6 Impact — DH + SW communities, onto-eval, framework.trails, ddbkg
- [ ] T16 `[easy]` §3.3 SHMARQL Interface — deployment description + screenshots
- [ ] T17 `[easy]` §7 Sustainability — versioning, w3id URIs, open source, mocho upstream dependency
- [ ] T18 `[easy]` §8 Conclusion
- [ ] T19 `[easy]` Resource Availability Statement — persistent URI + CC BY 4.0 + canonical citation
- [ ] T20 `[easy]` Declaration of Use of Generative AI

## §8.3 Between submission and camera-ready (7 May – 6 Aug)

- [ ] T21 `[medium-hard]` Enhance SHMARQL with markdown-defined documentation pages or MkDocs integration — enables pretty `.png` screenshots and `.jsx` component exports for paper figures
- [ ] T22 `[medium]` Add new data or additional stats if newly available
- [ ] T23 `[hard]` Address reviewer comments
- [ ] T24 `[easy]` Final LNCS formatting pass
- [ ] T25 `[easy]` Smoke-test all URIs, links, and QLever endpoint

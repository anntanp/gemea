# Data-Driven Alignment of the DDB Corpus

Related write-ups: [parquet-source.md](parquet-source.md), [dc-type-write-up.md](dc-type-write-up.md), [mediatype-htype-write-up.md](mediatype-htype-write-up.md)

---

## 1. Source

The DDB distributes its metadata holdings as a Cortex export: seven SQLite files (`s1.sqlite`–`s7.sqlite`), one per sector, each obtained via a pull from the DDB API. Each file contains a single `objs` table; each row holds one gzip-compressed Cortex JSON-LD blob in the `bufgz` column. The seven files together cover 65.3 million objects, of which 27.3 million carry digitized surrogates (as of March 2026).

| Sector | SQLite | Objects | Digitized |
|--------|--------|--------:|----------:|
| Archive | `s1.sqlite` | 36,170,381 | 3,486,444 |
| Library | `s2.sqlite` | 23,734,627 | 18,570,245 |
| Monument | `s3.sqlite` | 115,727 | 83,575 |
| Research | `s4.sqlite` | 1,276,653 | 1,223,929 |
| Media Library | `s5.sqlite` | 1,801,719 | 1,799,840 |
| Museum | `s6.sqlite` | 2,114,461 | 2,011,737 |
| Other | `s7.sqlite` | 99,161 | 89,904 |
| **Total** | | **65,312,729** | **27,265,674** |

`prescan.py` (Pass 1 of the two-pass transform) decompresses and parses each blob and writes a flat metadata Parquet file per sector (`s<N>_meta.parquet`). These Parquet files are the working surface for all corpus analysis. See [parquet-source.md](parquet-source.md) for the pipeline, 15-column schema, and field extraction notes.

---

## 2. Why corpus analysis was necessary for the alignment

The alignment target — mocho, which maps DDB EDM to RDA/FRBR — requires deciding which EDM fields are reliable enough to serve as alignment anchors. The Cortex schema describes what fields *exist*; it says nothing about what they contain, how consistently they are populated, or whether their semantics are stable across sectors. Three findings from the corpus analysis showed that those questions could not be answered without empirical inspection.

### 2.1 Coverage is uneven across sectors

`hierarchy_type` (*htype*) — the DDB's structural and bibliographic type classification — has zero coverage in Monument, Media Library, and Museum, and is 84% null in Other. Any alignment rule that treats *htype* as a reliable type signal silently excludes 5.9 million objects (21.4% of the digitized corpus). See [mediatype-htype-write-up.md](mediatype-htype-write-up.md) §3.

### 2.2 Field semantics are sector-local, not corpus-wide

Where *htype* is populated, Archive and Library use non-overlapping vocabularies: Archive is dominated by EAD-derived codes (Archivale/Findbuch File), while Library distributes across 25 MARC-derived bibliographic types (Heft, Aufsatz, Kapitel, Monografie, Abschnitt). A single alignment rule across both sectors would conflate archival arrangement with bibliographic granularity. The split was only visible after cross-tabulating type distributions per sector. See [mediatype-htype-write-up.md](mediatype-htype-write-up.md) §4.

### 2.3 Authority linking is heterogeneous

`dc:type`, the primary object-type field, carries either a controlled-vocabulary URI or a free-text literal depending on the contributing institution. Authority-linking rates range from 9% (Archive) to 85% (Media Library) — a nine-fold spread that reflects cataloguing practice, not data quality variation. Museum presents 48,484 distinct literal values, 21 times more than any other sector. The alignment cannot treat `dc:type` uniformly; it must handle URI-linked and literal entries separately, and must know per-sector which share of entries is URI-linked before deciding whether literal normalization is worth the cost. See [dc-type-write-up.md](dc-type-write-up.md) §2–§4.

### 2.4 Consequence for anchor field selection

Only `mediatype` — five coarse values, populated for > 99.99% of all objects — provides a reliable cross-sector type anchor without gap-filling. `dc:type` adds richer semantics but requires separate URI and literal handling. `hierarchy_type` is suitable only within Library and Archive. The corpus analysis converted these latent risks into quantified trade-offs that inform each alignment decision in mocho.

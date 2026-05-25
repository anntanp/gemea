# Parquet File Provenance

Script: [export_ddb.py](https://github.com/anntanp/gemea/blob/main/scripts/py/export_ddb.py), [export_batch_remote.sh](https://github.com/anntanp/gemea/blob/main/scripts/sh/export_batch_remote.sh)
Schema: [parquet_schema.json](https://github.com/anntanp/gemea/blob/main/data/schema/parquet_schema.json)
Export plan: [ddb-all-sectors-export-plan.md](https://github.com/anntanp/gemea/blob/main/notes/infra/ddb-all-sectors-export-plan.md)

---

## 1. Source

The DDB distributes its cultural heritage objects through a Cortex export: one SQLite file per sector (`s1.sqlite`–`s7.sqlite`). Each file contains a single table, `objs`, with a `bufgz` column storing one gzip-compressed cortex JSON blob per object. The cortex JSON follows a DDB-specific EDM serialisation — non-standard in its use of `$` for text values, `resource` for URI references, and camelCase field names — that differs from standard JSON-LD.

Sector s2 (Library) was exported first, producing `s2_meta.parquet` (18,570,245 rows). Sectors s1 and s3–s7 were exported in a subsequent batch run on the remote server `ise-d-teach03` using the same script.

| Sector | SQLite | Parquet |
|--------|--------|---------|
| s1 (Archive) | `s1.sqlite` | `s1_meta.parquet` |
| s2 (Library) | `s2.sqlite` | `s2_meta.parquet` |
| s3 (Monument) | `s3.sqlite` | `s3_meta.parquet` |
| s4 (Research) | `s4.sqlite` | `s4_meta.parquet` |
| s5 (Media Library) | `s5.sqlite` | `s5_meta.parquet` |
| s6 (Museum) | `s6.sqlite` | `s6_meta.parquet` |
| s7 (Other) | `s7.sqlite` | `s7_meta.parquet` |

## 2. Export pipeline

`export_ddb.py` reads rows from `objs` in `rowid` order and distributes them across `MAX_WORKERS` worker processes via a shared queue. Each worker decompresses the `bufgz` blob, parses the cortex JSON, and produces two outputs in parallel: batched N-Triple files (`ddbedm-<stem>_<worker>_<batch>.nt`) and a stream of metadata rows forwarded to a dedicated `meta_writer` process. The meta writer accumulates rows in memory and flushes them to Parquet in chunks of 500,000. The final file is written atomically via a `.tmp` rename.

Default configuration used for the batch run:

| Parameter | Default | Notes |
|-----------|---------|-------|
| `BATCH_SIZE` | 100,000 | NT records per file |
| `PARQUET_CHUNK` | 500,000 | Rows per Parquet write |
| `MAX_WORKERS` | `nproc − 2` | Passed as env override |

The script supports resumable export via a `.export_progress.json` checkpoint: if a run is interrupted, the next invocation queries `objs WHERE rowid > last_rowid` and writes a separate Parquet file for the resumed segment. The batch driver (`export_batch_remote.sh`) skips a sector if `<stem>_meta.parquet` already exists and no checkpoint file is present.

## 3. Schema

Each Parquet file contains one row per `edm:ProvidedCHO`. Fifteen columns cover identity, text, agents, dates, type/subject annotations, and three classification codes.

| Column | Type | Source |
|--------|------|--------|
| `obj_id` | string | `properties.item-id` |
| `title` | string | `ProvidedCHO.title.$` |
| `lang_title` | string | `ProvidedCHO.title.lang` |
| `lang_obj` | string | `ProvidedCHO.language` / `dcTermsLanguage` |
| `description` | list\<string\> | `ProvidedCHO.description` |
| `provider_id` | string | `provider-info.provider-ddb-id` |
| `dataset_id` | string | `properties.dataset-id` |
| `dc_type` | list\<CONCEPT_STRUCT\> | `ProvidedCHO.dcType` |
| `agents` | list\<AGENT_STRUCT\> | `ProvidedCHO.creator` / `contributor` / `publisher`; LIDO events |
| `dates` | list\<DATE_STRUCT\> | `ProvidedCHO.date` / `created` / `issued`; LIDO events |
| `dc_subject` | list\<CONCEPT_STRUCT\> | `ProvidedCHO.dcSubject` / `dcTermsSubject` |
| `hierarchy_type` | int16 | `ProvidedCHO.hierarchyType` (stripped `htype_` prefix) |
| `mediatype` | int16 | Concept URI matching `/medientyp/mt<N>` |
| `sector` | int16 | Concept URI matching `/sparte/sparte<N>` |
| `is_part_of` | bool | `ProvidedCHO.isPartOf` presence |

**Nested structs**:

- `CONCEPT_STRUCT`: `name` (string), `is_ext_uri` (bool). When `is_ext_uri=True`, `name` holds the `skos:prefLabel` resolved from a sibling `Concept` entity, not the URI itself.
- `AGENT_STRUCT`: `name` (string), `type` (string: `creation` / `publication` / `contribution` / `unknown_event`), `is_ext_uri` (bool).
- `DATE_STRUCT`: `value` (string), `begin` (string), `end` (string), `type` (string: `creation` / `publication` / `unknown_event`).

`mediatype` and `sector` are derived by scanning the `Concept` list for URIs that contain `/medientyp/mt` or `/sparte/sparte` and parsing the trailing integer. DDB vocabulary concept URIs matching `ddb.vocnet.org` are excluded from `dc_type` and `dc_subject` entries.

## 4. Field extraction notes

**Title.** Only the first element of a multi-valued `title` array is retained. Language tag comes from the same dict entry; if absent, `lang_title` is empty.

**Agents.** Three DC agent roles (`creator`, `publisher`, `contributor`) are extracted directly from the `ProvidedCHO`. LIDO-structured agents — encoded as `edm:Event` participants linked via `edm:hasMet` — are resolved through the event map and appended with type `unknown_event`. If an agent dict carries both a literal `$` and a `resource` URI, both are preserved: `name` gets the literal and `is_ext_uri` reflects the URI.

**Dates.** `dc:date` values are normalised: `yyyymmdd` strings are reformatted to `yyyy-mm-dd`; parenthetical qualifiers (e.g., `(ca.)`) are stripped before parsing. LIDO creation and publication events are detected by matching `edm:Event.hasType` against a fixed set of LIDO event type URIs and resolving the linked `TimeSpan`.

**Concept label resolution.** For `dc_type` and `dc_subject` entries that carry a URI reference rather than a literal, the script builds a lookup map from the `Concept` entities in the same record (`about` → `prefLabel`) before extraction. Entries with an external URI but no resolvable label in the record are omitted.

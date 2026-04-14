# export_s2.py — Design Note

## 1. Context

`s2.sqlite` (18.5M rows, table `objs`, column `bufgz`) stores gzip-compressed JSON blobs containing DDB cortex records. Each blob contains an `edm.RDF` section plus metadata fields (`properties`, `provider-info`, `indexing-profile`, `preview`, `view`, `source`).

Two outputs are needed:

- **§4**: Batched N-Triples (`.nt` files) of the EDM section for QLever ingestion via mocho
- **§5**: Parquet with extractable metadata columns to recreate DDB.pkl downstream

The script is a rewrite of `extract_src_from_full.py`, fixing its known bugs (§2) and replacing XML/string logic with JSON parsing and proper pyoxigraph serialisation (§3.2).

---

## 2. Bugs fixed from source scripts

### 2.1 Single poison pill for N workers
`extract_src_from_full.py` sends one `(None, None)` to a queue shared by 90 workers. Only one worker stops; the rest block on `Q.get()` forever. `main()` then deadlocks on `w.join()`.

**Fix**: send one `(None, None)` per worker after exhausting the cursor.

### 2.2 Importer process never flushes on shutdown
The `importer` process in `extract_src_from_full.py` only writes files to SQLite on a timed interval. Files written after the last interval are lost when the process exits.

**Fix**: not applicable in the new script — the importer pattern is dropped entirely.

### 2.3 Unclosed file handles
Both scripts use `open(...).read()` and `open(..., "wb").write(...)` without `with` blocks.

**Fix**: use `with open(...)` throughout.

### 2.4 Hardcoded input file
`extract_src_from_full.py` hardcodes `INPUT_FILE = "s2_.sqlite"` inside `main()`.

**Fix**: take from `sys.argv[1]`.

### 2.5 Worker count hardcoded at 90
Designed for a 96-CPU server (`teach02`). Will over-subscribe or under-use other machines.

**Fix**: `min(multiprocessing.cpu_count() - 2, MAX_WORKERS)`, overridable via env var.

### 2.6 Progress modulo mismatch
`count % 999999 == 0` but `tps = 99999 / elapsed` — off by 10×.

**Fix**: single `REPORT_INTERVAL` constant used in both places.

---

## 3. Design decisions

### 3.1 Architecture

```
main process
  │  SELECT * FROM objs WHERE bufgz IS NOT NULL
  │  feeds (uid, bufgz_blob) → WorkQ
  │
  ├── N workers
  │     decompress → parse JSON
  │     build EDM triples (pyoxigraph)
  │     extract metadata row
  │     accumulate locally to BATCH_SIZE records
  │     on full: write .nt file → disk
  │              flush metadata rows → MetaQ
  │
  └── 1 meta-writer process
        reads MetaQ
        writes Parquet in streaming chunks (pyarrow.parquet.ParquetWriter)
```

### 3.2 N-Triples serialisation: pyoxigraph vs string concatenation

`xml_from_lido.py` builds N-Triples by string concatenation:

```python
lido_rdf = "\n".join([f"{subj} {p} {o} ." for p, o in triples])
```

This silently produces invalid N-Triples when values contain quotes, newlines, or malformed IRIs — QLever may reject or silently misparse those triples at 18.5M-record scale.

**Fix**: use `px.Store()` + `store.dump(buf, "application/n-triples")`. pyoxigraph raises on bad IRIs at construction time and escapes all literals correctly at serialisation time.

### 3.3 Batched .nt output

Workers write their own numbered batch files to avoid a single large file that QLever may not load:

```
{OUTPUT_DIR}/edm_{worker_id:02d}_{batch_num:04d}.nt
```

Each worker resets its local triple buffer every `BATCH_SIZE` records.

### 3.4 Parquet output

Accumulated metadata rows are written in streaming chunks of `PARQUET_CHUNK` rows using `pyarrow.parquet.ParquetWriter` to avoid loading 18.5M rows into RAM at once.

---

## 4. EDM JSON → RDF mapping

**Scope**: the N-Triples output contains ALL triples from `edm.RDF` — every entity type, every property. §4.2 is the complete reference, not a subset.

**Parser**: the DDB cortex JSON serialization is non-standard (not W3C JSON-LD). A standard JSON-LD parser cannot be used. The implementation requires a custom recursive traversal that:
1. Iterates all entity types present in `edm.RDF`
2. For each entity, maps JSON field names → predicate URIs via a hardcoded lookup table (built from §4.2)
3. Converts values using the patterns in §4.1
4. Mints URIs for bare IDs per §4.3

### 4.1 Value patterns

Each EDM entity has an `about` field as subject URI. Property values follow three patterns:

| Pattern | Example | RDF object |
|---|---|---|
| `{"resource": "http://..."}` | `aggregatedCHO` | `px.NamedNode(resource)` |
| `{"$": "Faust", "lang": "de"}` | `title` | `px.Literal($, language=lang)` |
| `{"$": "text"}` or scalar string | `identifier` | `px.Literal(value)` |
| Array of above | `creator[]` | multiple triples |
| `null` | any field | skip — no triple emitted |

### 4.2 Entity and predicate table

Source: `data/ddbedm-properties-per-sector.csv` (columns: Archive, Lib, HP, Research, Media, Museum, Others).

**ProvidedCHO** (`edm:ProvidedCHO`)

| Predicate | Sectors |
|---|---|
| `dc:contributor` | Archive, Lib, Research, Museum, Others |
| `dc:creator` | all |
| `dc:date` | all |
| `dc:description` | Archive, Lib, Research, Media, Museum, Others |
| `dc:format` | all |
| `dc:identifier` | all |
| `dc:language` | Archive, Lib, HP, Research, Media, Museum |
| `dc:publisher` | Lib, Research, Media, Museum |
| `dc:relation` | Archive, Lib, Research, Media, Museum, Others |
| `dc:rights` | all |
| `dc:source` | Lib, Research |
| `dc:subject` | all |
| `dc:title` | all |
| `dc:type` | all |
| `dcterms:alternative` | Lib, Research, Media, Museum |
| `dcterms:bibliographicCitation` | all |
| `dcterms:extent` | Archive, Lib, Research, Media, Museum, Others |
| `dcterms:isPartOf` | Archive, Lib, HP, Research, Museum |
| `dcterms:issued` | Lib, HP, Research, Museum, Others |
| `dcterms:language` | Archive, Lib, HP, Research, Media, Museum |
| `dcterms:medium` | Archive, Lib, Museum |
| `dcterms:provenance` | Research, Media, Museum |
| `dcterms:spatial` | all |
| `dcterms:subject` | all |
| `dcterms:temporal` | Lib, Research, Museum |
| `ddb:aggregationEntity` | Archive, Lib, HP, Research |
| `ddb:hierarchyPosition` | Archive, Lib, HP, Research |
| `ddb:hierarchyType` | Archive, Lib, Research, Museum |
| `edm:currentLocation` | all |
| `edm:hasMet` | all |
| `edm:hasType` | all |
| `edm:isNextInSequence` | Lib, Research |
| `edm:type` | all |

**Aggregation** (`ore:Aggregation`)

| Predicate | Sectors |
|---|---|
| `dcterms:rights` | all |
| `ddb:aggregator` | all |
| `edm:aggregatedCHO` | all |
| `edm:dataProvider` | all |
| `edm:hasView` | Archive, Lib, HP, Research, Media, Others |
| `edm:isShownAt` | all |
| `edm:isShownBy` | all |
| `edm:object` | all |
| `edm:provider` | all |
| `edm:rights` | all |

**Agent** (`edm:Agent`)

| Predicate | Sectors |
|---|---|
| `dcterms:isPartOf` | all |
| `edm:wasPresentAt` | all |
| `rdf:type` | all |
| `skos:prefLabel` | all |

**Concept** (`skos:Concept`)

| Predicate | Sectors |
|---|---|
| `skos:notation` | all |
| `skos:prefLabel` | all |

**Event** (`edm:Event`)

| Predicate | Sectors |
|---|---|
| `crm:P11_had_participant` | all |
| `edm:happenedAt` | Archive, Lib, Research, Media, Museum, Others |
| `edm:hasType` | all |
| `edm:occuredAt` | all |

**PhysicalThing**

| Predicate | Sectors |
|---|---|
| `dc:title` | Archive, Lib, Research |
| `dcterms:isPartOf` | Archive, Lib, Research |
| `ddb:aggregationEntity` | Archive, Lib, Research |
| `ddb:hierarchyPosition` | Archive, Lib, Research |
| `ddb:hierarchyType` | Archive, Lib, Research |

**Place** (`edm:Place`)

| Predicate | Sectors |
|---|---|
| `skos:prefLabel` | all |
| `wgs84_pos:lat` | Archive, Lib, HP, Research |
| `wgs84_pos:long` | Archive, Lib, HP, Research |

**TimeSpan** (`edm:TimeSpan`)

| Predicate | Sectors |
|---|---|
| `edm:begin` | all |
| `edm:end` | all |
| `skos:notation` | Archive, Lib, HP, Research, Media, Museum |

**WebResource** (`edm:WebResource`)

| Predicate | Sectors |
|---|---|
| `dc:creator` | Archive, Research, Media, Museum, Others |
| `dc:description` | HP |
| `dc:format` | Archive, Lib, Research, Media, Others |
| `dc:publisher` | Lib, Museum |
| `dc:rights` | all |
| `dc:type` | all |
| `dcterms:created` | Lib, Museum | date of digitization, not of the CHO |
| `dcterms:rights` | all |
| `edm:rights` | all |

**LinguisticSystem**

| Predicate | Sectors |
|---|---|
| `rdf:value` | Archive, Lib, HP, Research, Media, Museum |

### 4.3 Malformed / bare entity IDs

Some entities have bare 32-character DDB IDs instead of HTTP URIs in their `about` field and in resource references. Confirmed examples from sampling:

| Field | Value |
|---|---|
| `Aggregation.about` | `YHCMWESBNVG6HTXITH2LAJTZNQDEXBPG` |
| `Agent.about` | `O5XUSBA7IPKSXYUTN6EQNWK62BQRF7GN` |
| `Event.about` | `UXK2PKGWLTUIECMOPIMOC5LFYVSG5X2Z` |
| `ProvidedCHO.hasMet[].resource` | `UXK2PKGWLTUIECMOPIMOC5LFYVSG5X2Z` |

These cross-reference each other within the same record (e.g. `ProvidedCHO.hasMet` → `Event.about`). `px.NamedNode()` rejects bare strings with no scheme — it will raise at construction time.

**Minting rule**: if a value used as a subject or resource reference does not start with `http` or `urn`, mint a URN using the EDM class name as a path segment:

```
urn:edm:<ClassName>:<bare-id>
```

Examples:
- `YHCMWESBNVG6HTXITH2LAJTZNQDEXBPG` (Aggregation) → `urn:edm:Aggregation:YHCMWESBNVG6HTXITH2LAJTZNQDEXBPG`
- `O5XUSBA7IPKSXYUTN6EQNWK62BQRF7GN` (Agent) → `urn:edm:Agent:O5XUSBA7IPKSXYUTN6EQNWK62BQRF7GN`
- `UXK2PKGWLTUIECMOPIMOC5LFYVSG5X2Z` (Event) → `urn:edm:Event:UXK2PKGWLTUIECMOPIMOC5LFYVSG5X2Z`

```python
DDBEDM = "urn:edm:"

def to_named_node(val: str, entity_type: str) -> px.NamedNode:
    if val.startswith("http") or val.startswith("urn"):
        return px.NamedNode(val)
    return px.NamedNode(DDBEDM + entity_type + ":" + val)
```

For `.resource` cross-references (e.g. `ProvidedCHO.hasMet[].resource` → `Event.about`), the target entity type must be resolved by building a lookup of all `about` values to entity types within the same record before minting.

### 4.4 Type triples

Each entity gets an `rdf:type` triple, e.g.:
```
<http://...ProvidedCHO/xyz> <rdf:type> <edm:ProvidedCHO> .
```

---

## 5. Parquet schema

**Scope**: ProvidedCHO fields only. WebResource, Aggregation (except `dataProvider`), Agent, Place, Event, TimeSpan details are serialised to N-Triples (§4) but not extracted to the Parquet.

### 5.1 Predicate mapping (verified against sample `22222G7MCFV667CKZLOK6DHL3SUWYQ4G`)

| Column | Predicate URI | Cortex JSON path | Status |
|---|---|---|---|
| `obj_id` | — | `properties.item-id` | ✓ |
| `lang` | `dc:language` | `edm.RDF.ProvidedCHO.language` (scalar string, e.g. `"eng"`) | ✓ |
| `title` | `dc:title` | `edm.RDF.ProvidedCHO.title.$` | ✓ |
| `dc_type` | `dc:type` | `edm.RDF.ProvidedCHO.dcType` (e.g. `"TEXT"`) | ✓ |
| `dc_creator` | `dc:creator` | `edm.RDF.ProvidedCHO.creator[*]` — list of `{label, uri}` structs; label and URI paired when both present in same dict entry (~21% of creator entries have a GND URI) | ✓ |
| `dc_publisher` | `dc:publisher` + `edm:dataProvider` | `edm.RDF.ProvidedCHO.publisher[*]` + `edm.RDF.Aggregation.dataProvider[*]` — list of `{label, uri}` structs; dataProvider label and URI are separate list entries (unpaired) | ✓ |
| `agents` | `edm:hasMet` → `P11_had_participant` | `ProvidedCHO.hasMet[*].resource` → `Event.P11_had_participant[*].resource` → Agent URIs | ✓ |
| `dc_contributor` | `dc:contributor` | `edm.RDF.ProvidedCHO.contributor[*]` — list of `{label, uri}` structs; absent in MARC records, present in Kultur/LIDO records (~23% of contributor entries have a GND URI) | ✓ |
| `dc_subject` | `dc:subject` (literals) | `edm.RDF.ProvidedCHO.dcSubject[*].$` — present in Kultur/LIDO records | ✓ |
| `dc_subject` (URIs) | `dcterms:subject` | `edm.RDF.ProvidedCHO.dcTermsSubject[*].resource` — bare IDs need URI minting per §4.3 | ✓ |
| `dc_date` | `dc:date` | `edm.RDF.ProvidedCHO.date` — normalised to `yyyy` or `yyyy-mm-dd/yyyy-mm-dd`; stripped of parenthetical qualifier — 446/1000 (44.6%) in excerpt | ✓ needs normalisation |
| `dc_date_qualifier` | — | parenthetical event-type label extracted from `dc:date` raw string (e.g. `"Fotografische Aufnahme"`, `"Hergestellt"`); null when absent | ✓ |
| `dc_created` | `dcterms:created` | Event chain only — `dcterms:created` on WebResource is digitization date (out of scope for Parquet). CHO creation source: `lido00012`, `eventType/creation`, `lido00007` via hasMet chain |
| `dc_issued` | `dcterms:issued` | `edm.RDF.ProvidedCHO.issued` (⚠ path unconfirmed); also via Event chain: `lido00228`, `eventType/publication` |
| `hierarchy_type` | `ddb:hierarchyType` | `edm.RDF.ProvidedCHO.hierarchyType` (scalar string, e.g. `"htype_001"`) — present in Archive, Lib, Research, Museum sectors | ✓ |
| `is_part_of` | `dcterms:isPartOf` | `bool(edm.RDF.ProvidedCHO.isPartOf)` — true if the CHO is a child node in a hierarchy; present in Archive, Lib, HP, Research, Museum sectors | ✓ |

**Event-based date extraction chain** (primary source for Kultur/LIDO records):

```
ProvidedCHO.hasMet[*].resource
  → Event (matched by bare ID or URI)
    → Event.hasType.resource  ← LIDO event type URI
    → Event.occuredAt         ← bare ID or URI of TimeSpan
      → TimeSpan.begin / TimeSpan.end
```

LIDO event type → date column mapping (confirmed from `items-excerpt-1000.json`):

| LIDO URI | Label | → column |
|---|---|---|
| `lido00012` | Creation | `dc_created` |
| `eventType/creation` | Creation (legacy URI) | `dc_created` |
| `lido00007` | Production | `dc_created` |
| `lido00228` | Publishing | `dc_issued` |
| `eventType/publication` | Publication (legacy URI) | `dc_issued` |
| `lido00003` | Unknown event | skip |
| `lido01127` | Photography | skip |
| others | — | skip |

### 5.2 Unresolved fields

**`dc_issued` direct path on ProvidedCHO** — cortex JSON field name not yet confirmed (`ProvidedCHO.issued`?); present in Lib, HP, Research, Museum, Others sectors per CSV. Event chain (`lido00228`, `eventType/publication`) is the fallback.

**`Event.occuredAt` → `TimeSpan`** — `occuredAt` is null in all 1000 records of the Kultur/LIDO excerpt. The TimeSpan chain does not appear to be populated in practice. Primary date source is `ProvidedCHO.date` (44.6% of records).

### 5.3 Omitted columns

NER/model columns from DDB.pkl (`ner_person`, `ner_date`, `model2_*`, `agent_match`, etc.) are not extracted — they are populated by downstream scripts.

---

## 6. Environment variables and constants

| Name | Default | Purpose |
|---|---|---|
| `OUTPUT_DIR` | `./out/` | Output directory for .nt files and Parquet |
| `BATCH_SIZE` | `100_000` | Records per .nt file per worker |
| `MAX_WORKERS` | `cpu_count() - 2` | Cap on worker processes |
| `PARQUET_CHUNK` | `500_000` | Rows per Parquet write flush |
| `REPORT_INTERVAL` | `100_000` | Progress log frequency (main process) |

---

## 7. Output layout

```
out/
  edm_00_0000.nt
  edm_00_0001.nt
  ...
  edm_89_0012.nt
  s2_meta.parquet
```

---

## 8. Verification steps

### 8.1 Smoke test
Run against a small slice:
```bash
BATCH_SIZE=1000 python export_s2.py s2.sqlite
```

### 8.2 N-Triples validation
```bash
rapper -i ntriples -c out/edm_00_0000.nt
```

### 8.3 Parquet sanity check
```python
import pandas as pd
df = pd.read_parquet('out/s2_meta.parquet')
print(df.shape, df.dtypes)
print(df.sample(5))
```

### 8.4 Spot-check one record
Pick one `obj_id` from the Parquet, look it up in `s2.sqlite`, decompress the blob,
and verify `title`/`dc_creator` match.

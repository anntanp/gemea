# GeMeA — GND Werk Linking: Requirements Specification

**Document type:** Software Requirements Specification
**Framework:** IREB CPRE (Certified Professional for Requirements Engineering)
**Subject:** `scripts/link_gnd_works.py` — offline GND Werk entity linking
**Source:** `notes/gnd/gnd-linking-plan.md`
**Status:** Draft

---

## 1. System Context

### 1.1 Purpose

`link_gnd_works.py` enriches Deutsche Digitale Bibliothek (DDB) ProvidedCHO records with GND Werk URIs by matching extracted `dc:title` strings against GND authority records via the DNB SPARQL endpoint. The resulting triples feed the mocho grouping pipeline, which uses the GND Werk URI as the key to cluster ProvidedCHOs into `mocho:Work` entities.

### 1.2 Pipeline position

```
DDB JSON-LD
    ↓ rdf2jsonld
RDF/JSON
    ↓ link_gnd_works.py        ← this system
RDF/JSON + GND Werk triples
    ↓ mocho
Normalized RDF
    ↓ QLever + Elasticsearch
GeMeA API → /work/{id}
```

`link_gnd_works.py` is an **offline ingest step**. It runs once per re-ingest during Phase 0 and never serves live requests. Throughput and batch efficiency are the governing design constraints; per-query latency is not.

### 1.3 System boundary

| Inside scope | Outside scope |
|---|---|
| Title extraction from `dc:title` strings | mocho Work grouping logic |
| SPARQL queries against `sparql.dnb.de` | GND Werk URI dereferencing |
| Post-retrieval scoring and match type assignment | ES index build |
| Triple generation (`skos:exactMatch`, `skos:closeMatch`) | API serving |
| Deduplication of title/author pairs | GND agent linking (Phase 1b) |

### 1.4 Knowledge base

**Endpoint:** `https://sparql.dnb.de/api/dnbgnd`
**Description:** DNB Bibliography and GND (`authorities-gnd_lds`, `dnb-all_lds` v23.02.2026) — updated monthly
**Scale:** 1,242,168,767 triples; 186,556,644 subjects; 591 predicates
**Protocol:** SPARQL 1.1 over HTTP POST (`application/x-www-form-urlencoded`); QLever-specific extensions (`contains-word`, `score()`) **not available** on this endpoint (confirmed by recon query 0.2)

---

## 2. Stakeholders

| Stakeholder | Role | Goal |
|---|---|---|
| GeMeA development team | Builder + operator | Pipeline produces ≥70% Werk linking rate; triples are correct and loadable into QLever |
| ISWC 2026 paper reviewers | Evaluators | Quality metrics (precision, coverage) are reproducible and reported transparently |
| DDB / DNB | Data provider | Public endpoint is not abused; queries stay within acceptable load |
| End users (GeMeA web UI) | Consumers | `/work/{id}` pages exist for major works; WEMI grouping is meaningful |

---

## 3. Functional Requirements

### FR-01 — Title extraction

**ID:** FR-01
**Priority:** Must
**Statement:** The system shall extract a clean title string from each ProvidedCHO `dc:title` value prior to GND lookup.
**Method:** Two-stage extraction:
1. Rule-based ISBD parser (primary): split on ` / `, `. - `, ` : ` per ISBD punctuation conventions
2. NER fallback (secondary): NuNER Zero zero-shot NER on records without ISBD markers (~71.6% of corpus)

**Rationale:** Raw `dc:title` strings contain ISBD-encoded publication metadata (edition, publisher, place, year) concatenated with the title. Sending raw strings to GND produces low-precision matches.

---

### FR-02 — GND Werk lookup

**ID:** FR-02
**Priority:** Must
**Statement:** The system shall query the DNB SPARQL endpoint to retrieve GND Werk candidates for each extracted title.
**Query target classes:** `gndo:Work`, `gndo:MusicalWork`, `gndo:Manuscript` — the three GND subclasses that correspond to IFLA LRM-E2 Work (confirmed by recon query 0.1; combined population: 580,284 entities).
**Excluded classes:** `gndo:Expression`, `gndo:VersionOfAMusicalWork` (IFLA LRM-E3), `gndo:ProvenanceCharacteristic` (no WEMI equivalent), `gndo:CollectiveManuscript` (zero entities in dataset).

---

### FR-03 — Author-constrained query (Pattern C with author)

**ID:** FR-03
**Priority:** Must
**Statement:** When a ProvidedCHO is linked to a person with a GND URI, the system shall constrain the SPARQL query to Works associated with that person.
**Author predicates:** `gndo:author`, `gndo:firstAuthor`, `gndo:poet`, `gndo:composer` — enumerated explicitly via `VALUES ?authorPred` because SPARQL 1.1 does not infer `rdfs:subPropertyOf` without a reasoner, and `gndo:firstAuthor` is a subproperty of `gndo:author`.
**Query:**
```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <{author_gnd_uri}> .
  FILTER(LCASE(STR(?prefLabel)) = "{normalized_title}")
}
LIMIT 10
```

---

### FR-04 — Title-only query (Pattern C without author)

**ID:** FR-04
**Priority:** Must
**Statement:** When no author GND URI is available, the system shall query by normalized title string alone.
**Query:**
```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  FILTER(LCASE(STR(?prefLabel)) = "{normalized_title}")
}
LIMIT 10
```
**Note:** QLever `contains-word` text search is not available on this endpoint (confirmed recon 0.2). Pattern C (FILTER on normalized string) is the sole active query path.

---

### FR-05 — Title normalization pipeline

**ID:** FR-05
**Priority:** Must
**Statement:** The system shall normalize extracted titles before query construction through three ordered phases:

| Phase | Step | Description |
|---|---|---|
| Normalization | Unicode NFC | Canonical Decomposition + Composition (Unicode Annex #15); ensures consistent code-point representation |
| Normalization | Lowercase | Case-fold after NFC |
| Normalization | Strip diacritics | NFD decompose → remove combining characters (`unicodedata.category == 'Mn'`); maps `ä→a`, `ü→u`, `ö→o` |
| Tokenization | Split | Split on whitespace and punctuation into word tokens |
| Filtering | Remove stopwords | `der, die, das, ein, eine, von, und, zu, im, in, an, auf, für, mit, bei, dem, den` |
| Filtering | Remove generic title words | Only `werke` is confirmed high-collision as a standalone GND title (3,212 exact matches); all other originally proposed words have ≤90 exact matches and need not be filtered (confirmed by `scripts/check_generic_title_words.py`, recon 0.4) |
| Filtering | Select distinctive tokens | 2–3 tokens by semantic centrality (see `gnd-linking-plan.md` §Step 2) |

---

### FR-06 — Post-retrieval match scoring

**ID:** FR-06
**Priority:** Must
**Statement:** The system shall assign a match type and confidence score to each candidate returned by the SPARQL query.

| Condition | `match_type` | RDF predicate |
|---|---|---|
| `prefLabel == extracted_title` (case-insensitive) | `exact` | `skos:exactMatch` |
| Normalized match (diacritics + punctuation stripped) | `normalized` | `skos:exactMatch` |
| Levenshtein distance ≤ 2 to `prefLabel` or any `gndo:variantNameForTheWork` | `fuzzy` | `skos:closeMatch` |
| No candidate above threshold | `unresolved` | — (no triple written) |

`match_confidence` = normalized edit similarity to `prefLabel` (float 0–1).
**Predicate rationale:** `skos:exactMatch` (not `owl:sameAs`) is used because a DDB ProvidedCHO and a GND Werk URI are not the same OWL individual; `skos:exactMatch` asserts retrieval-level equivalence without triggering OWL identity entailments (Halpin et al., ISWC 2010).

---

### FR-07 — Triple output

**ID:** FR-07
**Priority:** Must
**Statement:** The system shall write one JSON record per ProvidedCHO to `data/raw/gnd-works/`, containing:

```json
{
  "cho_uri": "https://www.deutsche-digitale-bibliothek.de/item/ABC123",
  "raw_title": "...",
  "extracted_title": "Faust",
  "extraction_method": "isbd" | "ner",
  "author_gnd_uri": "https://d-nb.info/gnd/118540238",
  "gnd_werk_uri": "https://d-nb.info/gnd/118607359",
  "match_type": "exact" | "normalized" | "fuzzy",
  "match_confidence": 1.0
}
```

Unresolved records omit `gnd_werk_uri`, `match_type`, `match_confidence`.

---

### FR-08 — Deduplication

**ID:** FR-08
**Priority:** Must
**Statement:** The system shall deduplicate `(extracted_title, author_gnd_uri)` pairs before issuing SPARQL queries and join results back to all ProvidedCHOs sharing the same pair.
**Rationale:** ~65M ProvidedCHOs share ~5–10M unique title/author pairs. Without deduplication, the same query is issued tens of times for the same pair (e.g., all copies of *Faust* across institutions), wasting endpoint capacity.

---

## 4. Non-Functional Requirements

### NFR-01 — Throughput

**ID:** NFR-01
**Priority:** Must
**Statement:** The system shall complete a full run over ~5–10M unique title/author pairs within a time frame compatible with a monthly re-ingest cycle.
**Initial concurrency:** 10 parallel HTTP requests (`asyncio.Semaphore(10)`); tunable upward after rate-limit profiling of the DNB endpoint.

---

### NFR-02 — Linking coverage

**ID:** NFR-02
**Priority:** Must
**Statement:** The system shall achieve ≥70% GND Werk linking rate across all ProvidedCHOs. This is the minimum threshold for enabling the `/work/{id}` API endpoint and WEMI hierarchy pages in GeMeA.

---

### NFR-03 — Linking precision

**ID:** NFR-03
**Priority:** Must
**Statement:** Manual spot-check of 100 randomly sampled linked pairs shall show ≥90% correct Werk assignments for `exact` and `normalized` matches.

---

### NFR-04 — Endpoint availability dependency

**ID:** NFR-04
**Priority:** Should
**Statement:** The system shall handle transient `sparql.dnb.de` failures gracefully — retry with exponential backoff (max 3 retries), log failures, and continue processing remaining pairs. Failed pairs shall be written to a retry queue for re-processing.
**Rationale:** The DNB endpoint has no published SLA. A single timeout must not abort a multi-hour batch run.

---

### NFR-05 — Reproducibility

**ID:** NFR-05
**Priority:** Must
**Statement:** Given the same input data and the same GND dataset version, the system shall produce identical output. The GND dataset version (`dnb-all_lds` v23.02.2026) shall be recorded in output metadata.

---

## 5. Constraints

### CON-01 — SPARQL 1.1 only

**ID:** CON-01
**Statement:** The DNB endpoint (`sparql.dnb.de`) enforces SPARQL 1.1 grammar. QLever-specific keywords (`contains-word`, `score()`, `TEXTLIMIT`) are not available and must not be used in production queries.
**Source:** Confirmed by recon query 0.2 — `contains-word` returns a parse error.

---

### CON-02 — Public endpoint, no SLA

**ID:** CON-02
**Statement:** `sparql.dnb.de` is a publicly operated endpoint with no published rate limits or uptime SLA. The system must not exceed concurrency levels that could constitute abusive load. Initial limit: 10 concurrent requests.

---

### CON-03 — GND ontology version

**ID:** CON-03
**Statement:** Query design is based on `gnd_20251218.ttl`. If the GND ontology is updated, author predicates (`gndo:author`, `gndo:firstAuthor`, `gndo:poet`, `gndo:composer`) and Work-class membership must be re-verified.

---

### CON-04 — Offline execution only

**ID:** CON-04
**Statement:** `link_gnd_works.py` must not be invoked at API request time. It is a batch ingest script. Results are pre-computed and loaded into QLever; the GeMeA API reads from QLever at runtime.

---

### CON-05 — RDF predicate semantics

**ID:** CON-05
**Statement:** The system shall use `skos:exactMatch` for exact and normalized matches, and `skos:closeMatch` for fuzzy matches. `owl:sameAs` must not be used, as a DDB ProvidedCHO and a GND Werk URI are not the same OWL individual.
**Reference:** Miles & Bechhofer, SKOS Reference, W3C 2009, §10; Halpin et al., ISWC 2010.

---

## 6. Acceptance Criteria

| ID | Criterion | Verification method |
|---|---|---|
| AC-01 | All SPARQL queries conform to SPARQL 1.1 grammar | Run each query template against the endpoint with a known title; no parse errors |
| AC-02 | `VALUES ?wtype` contains exactly `gndo:Work gndo:MusicalWork gndo:Manuscript` | Code review; verified against recon 0.1 results |
| AC-03 | `VALUES ?authorPred` contains `gndo:author gndo:firstAuthor gndo:poet gndo:composer` | Code review; verified against recon 0.3 results |
| AC-04 | Levenshtein threshold of ≤ 2 validated against gold set | Spot-check 500 stratified records; adjust if precision < 90% |
| AC-05 | Deduplication reduces query count from ~65M to ~5–10M | Log unique pair count before and after dedup |
| AC-06 | ≥70% Werk linking rate on full DDB corpus | Pipeline run report |
| AC-07 | Output JSON conforms to FR-07 schema | Schema validation on sample output |
| AC-08 | `owl:sameAs` does not appear in any output triple | `grep owl:sameAs` on output files |

---

## 7. Open Questions

| ID | Question | Blocking |
|---|---|---|
| OQ-01 | Does the DNB endpoint normalize Umlauts in FILTER comparisons? (`ä` vs `a`) — affects diacritic stripping in FR-05 | No — test empirically |
| OQ-02 | What are the actual rate limits on `sparql.dnb.de`? | No — profile during first batch run |
| OQ-03 | Should `gndo:variantNameForTheWork` be queried in a separate UNION pattern to increase recall for fuzzy matching? Currently only `gndo:preferredNameForTheWork` is queried | No |
| OQ-04 | Does `gndo:composer`/`gndo:firstComposer` behave analogously to `gndo:author`/`gndo:firstAuthor` for MusicalWork records? | No — verify with a musician query analogous to recon 0.3 |

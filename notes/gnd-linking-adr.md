# GeMeA — Architecture Decision Record: GND Werk Entity Linking

**Format:** MADR (Markdown Architecture Decision Record)
**Subject:** Design decisions for `scripts/link_gnd_works.py`
**Source:** `notes/gnd-linking-plan.md`
**Status:** Accepted

---

## ADR-01 — Use the DNB public SPARQL endpoint instead of a local GND instance

**Status:** Accepted
**Date:** 2026-03-21

### Context

The original plan assumed a locally operated GND instance (lobid-gnd REST API) for Werk lookups. The endpoint was listed as TBD, requiring infrastructure setup, data ingestion, and maintenance. The DNB operates a public QLever-backed SPARQL endpoint at `https://sparql.dnb.de/api/dnbgnd` containing the full GND dataset (1.24B triples, updated monthly).

### Decision

Use `https://sparql.dnb.de/api/dnbgnd` as the GND lookup endpoint. No local GND infrastructure is required.

### Consequences

**Positive:**
- No infrastructure setup, ingestion pipeline, or maintenance for a local GND instance
- Dataset is DNB-authoritative and updated monthly
- Covers the full GND (580,284 Work-class entities confirmed by recon)

**Negative:**
- No published SLA; endpoint availability is outside our control
- No published rate limits; concurrency must be profiled conservatively
- Cannot add custom indexes or text search configuration

**Mitigations:**
- Retry with exponential backoff on transient failures (NFR-04)
- Initial concurrency cap of 10 parallel requests, tunable after profiling

---

## ADR-02 — Use SPARQL 1.1 FILTER instead of QLever `contains-word` for title matching

**Status:** Accepted (forced by recon result)
**Date:** 2026-03-21

### Context

The linking plan originally designed three query patterns:
- **Pattern A** — title + author, using QLever `contains-word` for full-text search with relevance ranking (`score()`)
- **Pattern B** — title only, using `contains-word` with UNION over `gndo:variantNameForTheWork`
- **Pattern C** — FILTER fallback for when `contains-word` is unavailable

Recon query 0.2 returned a SPARQL parse error when `contains-word` was used:
```
Invalid SPARQL query: Token "contains-word": mismatched input 'contains-word'
expecting {'(', 'a', '^', '!', IRI_REF, PNAME_NS, PNAME_LN, VAR1, VAR2, PREFIX_LANGTAG}
```

The DNB endpoint enforces SPARQL 1.1 grammar. QLever-specific syntax is not available.

### Decision

Pattern C (`FILTER(LCASE(STR(?prefLabel)) = "{normalized_title}")`) is the sole active query path. Patterns A and B are retained in the plan as reference but are not used.

Pattern C is parameterised by author availability:
- **With author GND URI:** add `VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }` and `?work ?authorPred <{author_gnd_uri}>`
- **Without author GND URI:** title FILTER only

### Consequences

**Positive:**
- Fully SPARQL 1.1 compliant; no dependency on QLever extensions
- Exact and normalized matches are deterministic and reproducible

**Negative:**
- No relevance ranking — all matches are binary (match / no match); scoring is done entirely in Python post-retrieval
- No variant name search in a single query — `gndo:variantNameForTheWork` requires a separate query or UNION
- Fuzzy matching (Levenshtein ≤ 2) must be handled entirely in Python; the SPARQL query retrieves only exact/normalized candidates

**Mitigations:**
- Post-retrieval scoring in Python covers normalized and fuzzy match types (Step 3)
- A second UNION pattern over `gndo:variantNameForTheWork` can be added to Pattern C without requiring `contains-word`

---

## ADR-03 — Restrict Work class scope to IFLA LRM-E2 equivalents only

**Status:** Accepted
**Date:** 2026-03-21

### Context

The GND ontology defines seven subclasses of `gndo:Work`. Not all correspond to the IFLA LRM Work concept (LRM-E2: "a distinct intellectual or artistic creation"). Querying all subclasses would return Expression-level and non-WEMI entities as Werk candidates, producing semantically incorrect links.

### Decision

Restrict `VALUES ?wtype` to the three GND classes that map to IFLA LRM-E2:

```sparql
VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
```

| Class | IFLA LRM | Population | Decision |
|---|---|---|---|
| `gndo:Work` | LRM-E2 — direct match | 242,333 | Include |
| `gndo:MusicalWork` | LRM-E2 — musical composition as distinct creative entity | 330,818 | Include |
| `gndo:Manuscript` | LRM-E2 — unique historical manuscript is the intellectual creation | 7,133 | Include |
| `gndo:Expression` | LRM-E3 — realization of a Work | 5,766 | Exclude |
| `gndo:VersionOfAMusicalWork` | LRM-E3 — specific arrangement/version | 2,905 | Exclude |
| `gndo:ProvenanceCharacteristic` | No WEMI equivalent | 10,080 | Exclude |
| `gndo:CollectiveManuscript` | LRM-E4 — container Manifestation | 0 | Exclude |

### Consequences

**Positive:**
- Links are semantically correct at the WEMI Work level
- Avoids false positives from Expression-level or non-creative entities
- Covers 580,284 entities — the full Work-level GND population

**Negative:**
- `gndo:Expression` entities (5,766) are excluded; DDB records that are specifically linked to an Expression (e.g., a translation) will not receive a Werk link via this pipeline
- Decision is tied to `gnd_20251218.ttl`; must be re-verified if the ontology changes

---

## ADR-04 — Enumerate author predicates explicitly rather than relying on property inference

**Status:** Accepted
**Date:** 2026-03-21

### Context

The GND ontology defines a property hierarchy for creator roles. `gndo:firstAuthor` is declared `rdfs:subPropertyOf gndo:author`. Naively querying only `gndo:author` would miss triples stored as `gndo:firstAuthor`. SPARQL 1.1 does not infer `rdfs:subPropertyOf` without an OWL reasoner.

Recon query 0.3 (Works linked to Goethe, `https://d-nb.info/gnd/118540238`) confirmed:
- `gndo:author` — 8/10 results (dominant predicate)
- `gndo:poet` — 1/10 (lyrical works)
- `gndo:relatedPerson` — 1/10 (too broad; excluded)

The relevant property hierarchy from `gnd_20251218.ttl`:

| Property | Subproperty of | Scope |
|---|---|---|
| `gndo:author` | RDA P60434 | Textual works |
| `gndo:firstAuthor` | `gndo:author` | Single/lead author |
| `gndo:poet` | RDA P60477 | Words of non-dramatic musical works |
| `gndo:composer` | RDA P60426 | Musical works |
| `gndo:firstComposer` | `gndo:composer` | Single/lead composer |

### Decision

Use `VALUES ?authorPred` to enumerate all relevant author predicates explicitly:

```sparql
VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
```

`gndo:relatedPerson` is excluded as it is not specific to the creator role. `gndo:firstComposer` is included implicitly via `gndo:composer` only if confirmed by a musician-specific recon query (OQ-04).

### Consequences

**Positive:**
- Correct recall across all creator role predicates without requiring OWL reasoning
- Explicit enumeration is transparent and easy to audit

**Negative:**
- New GND role predicates introduced in future ontology versions will not be covered automatically; requires manual update

---

## ADR-05 — Use `skos:exactMatch` and `skos:closeMatch` instead of `owl:sameAs`

**Status:** Accepted
**Date:** 2026-03-21

### Context

Entity linking pipelines commonly use `owl:sameAs` to assert that two URIs identify the same entity. However, a DDB ProvidedCHO URI and a GND Werk URI are not the same OWL individual: the ProvidedCHO is a catalog record for a physical manifestation; the Werk URI is an authority record for an abstract work. Asserting `owl:sameAs` between them would be ontologically incorrect and would cause unintended OWL entailments in any downstream reasoner.

Halpin et al. (ISWC 2010, *When owl:sameAs Isn't the Same*) document widespread misuse of `owl:sameAs` for approximate and cross-type identity in linked data, and recommend SKOS mapping properties as the correct alternative for concept-level matching.

### Decision

| Match type | Condition | Predicate |
|---|---|---|
| `exact` | Case-insensitive string equality | `skos:exactMatch` |
| `normalized` | Match after diacritic + punctuation stripping | `skos:exactMatch` |
| `fuzzy` | Levenshtein distance ≤ 2 | `skos:closeMatch` |
| `unresolved` | No candidate above threshold | — |

`skos:exactMatch` asserts that two concepts "can be used interchangeably for all retrieval purposes" (SKOS Reference, W3C 2009, §10) — appropriate for confirmed title-to-Werk matches without OWL identity entailments. `skos:closeMatch` is used for fuzzy matches where interchangeability holds only in some retrieval contexts.

### Consequences

**Positive:**
- Semantically correct — no false OWL identity assertions
- `skos:exactMatch` and `skos:closeMatch` are standard SKOS mapping properties, consumable by any SKOS-aware client
- Match confidence is preserved in the `match_type` field; downstream consumers can filter by confidence level

**Negative:**
- SPARQL queries that assume `owl:sameAs` for entity resolution will not find these links; consumers must query for SKOS predicates explicitly

---

## ADR-06 — Deduplicate title/author pairs before querying

**Status:** Accepted
**Date:** 2026-03-21

### Context

The DDB corpus contains ~65M ProvidedCHOs, but many share identical `dc:title` strings across institutions (multiple copies of the same work). Issuing one SPARQL query per ProvidedCHO would result in the same query being issued dozens or hundreds of times for popular works (e.g., all copies of *Faust* across German libraries).

### Decision

Deduplicate on `(extracted_title, author_gnd_uri)` pairs before querying:
1. First pass: collect all pairs from rdf2jsonld output
2. Issue SPARQL queries for unique pairs only (~5–10M estimated)
3. Second pass: join results back to all ProvidedCHOs sharing the same pair

### Consequences

**Positive:**
- Reduces SPARQL queries from ~65M to ~5–10M (10–13× reduction)
- Reduces load on the public DNB endpoint
- Proportionally reduces total run time

**Negative:**
- Requires an intermediate data structure (hash map of pair → result) that may be large in memory for the full corpus; may need disk-backed storage (e.g., SQLite) for the full 65M run

---

## ADR-07 — Run as offline batch ingest, not as a runtime API component

**Status:** Accepted
**Date:** 2026-03-21

### Context

An alternative design would have the GeMeA API resolve GND Werk links on demand — querying `sparql.dnb.de` at request time when a user views an item page. This would keep linking results always up-to-date with the latest GND data.

### Decision

`link_gnd_works.py` runs offline during Phase 0 ingest. Results are pre-computed, stored as triples, and loaded into QLever. The API reads from QLever at runtime and never calls `sparql.dnb.de` directly.

### Consequences

**Positive:**
- API latency is unaffected by `sparql.dnb.de` availability or response time
- Linking results are stable within an ingest cycle; no per-request variability
- Throughput and batch efficiency are the governing constraints — latency per query is irrelevant

**Negative:**
- Linking results are only as fresh as the last ingest; GND updates between ingests are not reflected
- A full re-ingest is required to pick up GND changes (acceptable given the monthly update cadence)

---

## ADR-08 — Filter only `werke` from distinctive token selection; all other generic words are low-collision

**Status:** Accepted
**Date:** 2026-03-21

### Context

The linking plan's title normalization pipeline (Step 2, Criterion 2) originally proposed filtering a list of ~15 generic German words (`werke`, `briefe`, `gedichte`, `schriften`, …) from distinctive token selection, on the assumption that these words would produce many false-positive GND Werk matches when used as FILTER values.

`scripts/check_generic_title_words.py` was written to empirically validate this assumption by querying the DNB endpoint for exact `preferredNameForTheWork` matches on singular, plural, and article+noun forms for each candidate word. Results (confirmed 2026-03-21, `dnb-all_lds` v23.02.2026):

| Word | Exact GND Work matches | Keep as filter? |
|---|---|---|
| `werke` | 3,212 | Yes — filter |
| `gedichte` | 74 | No — low collision |
| `sammlung` | 54 | No |
| `schriften` | 46 | No |
| `briefe` | 45 | No |
| `band` | 37 | No |
| `katalog` | 29 | No |
| `texte` | 28 | No |
| `teil` | 27 | No |
| `bericht` | 23 | No |
| `geschichte` | 20 | No |
| `aufsätze` | 17 | No |
| `heft` | 15 | No |
| `nummer` | 6 | No |
| `jahrgang` | 0 | No |

The threshold of 100 was used: only words with ≥100 exact matches as a standalone GND Work title are genuinely high-collision.

A secondary finding from recon query 0.4: GND `preferredNameForTheWork` literals are stored as plain strings with no `@de` language tag, and the values are typically full ISBD-qualified strings (e.g., `"Faust. - [Neue Ausg.]"`) rather than clean title tokens. This means Pattern C FILTER matching on individual tokens will rarely match GND values directly; the normalization and token-selection pipeline targets multi-word title strings, not individual tokens as standalone GND names.

### Decision

The `GENERIC_TITLE_WORDS` filter set in `link_gnd_works.py` shall contain only `{"werke"}`. The remaining 14 candidate words are not filtered.

### Consequences

**Positive:**
- Filter list is empirically validated, not speculative — avoids over-filtering distinctive tokens
- Words like `briefe` (45 matches), `gedichte` (74) are genuinely distinctive in most contexts and correctly retained
- Decision is reproducible via `scripts/check_generic_title_words.py`; can be re-run against future GND versions

**Negative:**
- `werke` (3,212 matches) remains a false-positive risk if it appears as the sole distinctive token in a title; mitigated by requiring 2–3 distinctive tokens and treating single-token results as lower confidence
- The validation measures collision on standalone GND Work names only; words that are distinctive when combined (e.g., `"Werke und Briefe"`) are not captured by this analysis — acceptable given Pattern C's exact-match semantics

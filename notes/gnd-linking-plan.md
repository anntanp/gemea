# GeMeA — GND Werk Linking via QLever DNB Endpoint

Script: `scripts/link_gnd_works.py`
Replaces: lobid-gnd REST API approach (previously planned but endpoint was TBD)

`link_gnd_works.py` is an **offline ingest step**, not a runtime component. It runs once (or on re-ingest) during Phase 0 to enrich ProvidedCHO records with GND Werk URIs. Its output feeds mocho → QLever → the GeMeA API. The GND linking results are ultimately exposed through the API's `/work/{id}` endpoint and SPARQL proxy — `link_gnd_works.py` itself never serves live requests. Design constraints follow from this: throughput and batch efficiency matter; latency per query does not.

---

## 1. Summary

| Section | What it covers |
|---|---|
| [3. Knowledge base index](#3-knowledge-base-index) | DNB endpoint dataset stats (triples, subjects, predicates) |
| [4. Endpoint and HTTP API](#4-endpoint-and-http-api) | `https://sparql.dnb.de/api/dnbgnd` — POST format, QLever settings |
| [5. Step 0 — Recon queries](#5-step-0--recon-queries-run-once-before-implementation) | Four one-off queries to validate Work classes, text index, author predicates, literal format before implementation |
| [6. Step 1 — Title extraction](#6-step-1--title-extraction) | Extract clean title from raw `dc:title`: ISBD rule-based parser (primary) + NuNER Zero NER fallback |
| [7. Step 2 — Query patterns](#7-step-2--query-patterns) | Patterns A/B/C with justification; conclusion: Pattern C (FILTER) is the sole active path |
| [8. Step 3 — Title token preparation](#8-step-3--title-token-preparation) | Normalization → tokenization → stopword removal → distinctive token selection; `GENERIC_TITLE_WORDS` validation |
| [9. Step 4 — Post-retrieval scoring](#9-step-4--post-retrieval-scoring) | Match type assignment (exact / normalized / fuzzy); `skos:exactMatch` vs `skos:closeMatch` vs `owl:sameAs` |
| [10. Step 5 — Changes to `link_gnd_works.py`](#10-step-5--changes-to-link_gnd_workspy) | Replace lobid REST with async `httpx` POST; concurrency semaphore |
| [11. Step 6 — What this replaces](#11-step-6--what-this-replaces) | Old lobid plan vs new QLever plan |

---

## 2. Open questions

| ID | Question | Blocking | Status |
|---|---|---|---|
| ~~OQ-00a~~ | ~~Is `preferredNameForTheWork` in the text index?~~ | — | **Resolved** — Recon 0.2: `contains-word` causes SPARQL parse error. Endpoint enforces SPARQL 1.1 only. Pattern C is the sole active query path. |
| ~~OQ-00b~~ | ~~Exact predicate for author link (`gndo:firstAuthor` or `gndo:creator`)?~~ | — | **Resolved** — Recon 0.3: `gndo:author` dominant (8/10); `gndo:firstAuthor` added via `VALUES` (subproperty, SPARQL won't infer); `gndo:poet` for lyrical works; `gndo:composer` for musical works. |
| OQ-01 | Does `sparql.dnb.de` normalize Umlauts in FILTER comparisons? (`ä` vs `a`) | No | Open — see [§2.1](#21-recon-05--umlaut-handling-in-filter-comparisons-oq-01) |
| OQ-02 | What are the actual rate limits on `sparql.dnb.de`? | No | Open — no published SLA; profile at `CONCURRENCY = 10` during first batch run |
| OQ-03 | Should `gndo:variantNameForTheWork` be added as a UNION branch in Pattern C to increase recall? | No | Open — preferred names are often ISBD-qualified strings (recon 0.4); variant names may carry the clean title form |
| OQ-04 | Does `gndo:composer`/`gndo:firstComposer` behave analogously to `gndo:author`/`gndo:firstAuthor` for MusicalWork records? | No | Open — verify with a musician query analogous to recon 0.3 |

### 2.1 Recon 0.5 — Umlaut handling in FILTER comparisons (OQ-01)

The question is whether `LCASE(STR(?prefLabel)) = "gotz von berlichingen"` (diacritics stripped) matches a record stored as `"Götz von Berlichingen"`. LCASE performs case folding only; it does not decompose or strip combining characters. The hypothesis is that the endpoint does **not** normalize Umlauts, meaning a stripped form will not match an umlaut-bearing literal — and therefore diacritic stripping in FR-05 would *hurt* recall against `preferredNameForTheWork`.

Test case: Goethe's *Götz von Berlichingen* (`https://d-nb.info/gnd/118540238` as author) — a well-known work with `ö` in the title.

**Query A — with umlaut (expect: results)**

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <https://d-nb.info/gnd/118540238> .
  FILTER(LCASE(STR(?prefLabel)) = "götz von berlichingen")
}
LIMIT 10
```

```bash
curl -s -X POST "https://sparql.dnb.de/api/dnbgnd" \
  -H "Accept: application/sparql-results+json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'query=PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <https://d-nb.info/gnd/118540238> .
  FILTER(LCASE(STR(?prefLabel)) = "götz von berlichingen")
}
LIMIT 10'
```

**Query B — diacritics stripped (expect: no results if endpoint does not normalize)**

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <https://d-nb.info/gnd/118540238> .
  FILTER(LCASE(STR(?prefLabel)) = "gotz von berlichingen")
}
LIMIT 10
```

```bash
curl -s -X POST "https://sparql.dnb.de/api/dnbgnd" \
  -H "Accept: application/sparql-results+json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'query=PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <https://d-nb.info/gnd/118540238> .
  FILTER(LCASE(STR(?prefLabel)) = "gotz von berlichingen")
}
LIMIT 10'
```

**Interpretation:**

| Query A result | Query B result | Conclusion | Impact on FR-05 |
|---|---|---|---|
| Results returned | No results | Endpoint does **not** normalize Umlauts — FILTER is byte-exact | Strip diacritics from **query string only if GND stores stripped forms**; otherwise keep Umlauts; send both forms via UNION |
| Results returned | Results returned | Endpoint normalizes Umlauts (accent-insensitive collation) | Stripping is safe; normalized form sufficient for FILTER |
| No results | No results | Title not stored as `preferredNameForTheWork` in this form | Re-check with `gndo:variantNameForTheWork` (OQ-03) |

---

## 3. Knowledge base index

**Description:** DNB Bibliography and GND (Gemeinsame Normdatei) (`authorities-gnd_lds`, `dnb-all_lds` version 23.02.2026) — updated monthly

| Metric | Value |
|---|---|
| Triples | 1,242,168,767 |
| Subjects | 186,556,644 |
| Predicates | 591 |
| Objects | 457,761,162 |

---

## 4. Endpoint and HTTP API

**Endpoint:** `https://sparql.dnb.de/api/dnbgnd`
**Method:** `POST`
**Body:** `query=<URL-encoded SPARQL>` (`application/x-www-form-urlencoded`)
**Accept:** `application/sparql-results+json`

QLever instance settings:
- Languages: `en`
- Default max rows: 100
- Default mode: 3 — SPARQL & context-sensitive entities

QLever-specific keywords used: `contains-word`, `textlimit`, `score()`

---

## 5. Step 0 — Recon queries (run once before implementation)

Three things to verify before writing production queries.

### 5.1 Work type coverage

IFLA LRM defines a Work (LRM-E2) as "a distinct intellectual or artistic creation" — the abstract entity at the top of the WEMI hierarchy, independent of any particular realization or carrier. The GND ontology (`gnd_20251218.ttl`) models six subclasses of `gndo:Work`. Only three correspond to the IFLA LRM Work concept:

| GND class | Label (en / de) | MARC21 | IFLA LRM | Include in queries |
|---|---|---|---|---|
| `gndo:Work` | Work / Werk | `079 $v=wit` | LRM-E2 Work — direct match | **Yes** |
| `gndo:MusicalWork` | Musical work / Werk der Musik | `079 $v=wim` | LRM-E2 Work — a musical composition as distinct creative entity | **Yes** |
| `gndo:Manuscript` | Manuscript / Schriftdenkmal | `079 $v=wis` | LRM-E2 Work — a unique historical manuscript (e.g. Nibelungenlied) is the distinct intellectual creation itself | **Yes** |
| `gndo:Expression` | Expression / Expression | `079 $v=wie` | LRM-E3 Expression — the realization of a Work in a specific linguistic or notational form; one level below Work in WEMI | No |
| `gndo:VersionOfAMusicalWork` | Version of a musical work / Fassung eines Werks der Musik | `079 $v=wif` | LRM-E3 Expression — a specific arrangement or version is a realization of the Work, not a new Work (unless substantially transformed) | No |
| `gndo:CollectiveManuscript` | Collective manuscript / Sammelhandschrift | `079 $v=wil` | LRM-E4 Manifestation — a bound collection of multiple works; the container, not the intellectual creation | No |
| `gndo:ProvenanceCharacteristic` | Provenance characteristic / Provenienzmerkmal | `079 $v=wip` | No WEMI equivalent — ownership marks and traces left in/on physical items; not a creative entity | No |

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?type (COUNT(?w) AS ?n) WHERE {
  VALUES ?type {
    gndo:Work gndo:MusicalWork gndo:Manuscript
    gndo:Expression gndo:VersionOfAMusicalWork
    gndo:CollectiveManuscript gndo:ProvenanceCharacteristic
  }
  ?w a ?type .
}
GROUP BY ?type ORDER BY DESC(?n)
```

Constraining with `VALUES` avoids a full dataset type scan and lets the endpoint use per-type indexes. The original open-ended query caused a 504 Gateway Timeout.

**Results:**

| ?type | ?n |
|---|---|
| MusicalWork | 330,818 |
| Work | 242,333 |
| ProvenanceCharacteristic | 10,080 |
| Manuscript | 7,133 |
| Expression | 5,766 |
| VersionOfAMusicalWork | 2,905 |
| CollectiveManuscript | — (no results; zero entities in dataset) |

**Conclusion:** `VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }` is confirmed. The three IFLA LRM Work-equivalent classes cover 580,284 entities (242,333 + 330,818 + 7,133). The four excluded classes are either IFLA Expression-level (`Expression`, `VersionOfAMusicalWork`), have no WEMI equivalent (`ProvenanceCharacteristic`), or are absent from this dataset (`CollectiveManuscript`).

### 5.2 Confirm text index covers `preferredNameForTheWork`

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?w ?label ?score WHERE {
  ?w a gndo:Work .
  ?w gndo:preferredNameForTheWork ?label .
  ?label contains-word "faust"
  BIND(score(?label) AS ?score)
}
ORDER BY DESC(?score) LIMIT 5
```

**Test (curl):**

```bash
curl -s -X POST "https://sparql.dnb.de/api/dnbgnd" \
  -H "Accept: application/sparql-results+json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'query=PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?w ?label WHERE {
  ?w a gndo:Work .
  ?w gndo:preferredNameForTheWork ?label .
  ?label contains-word "faust"
}
LIMIT 5'
```

**Result:**

```json
{
  "exception": "Invalid SPARQL query: Token \"contains-word\": mismatched input 'contains-word' expecting {'(', 'a', '^', '!', IRI_REF, PNAME_NS, PNAME_LN, VAR1, VAR2, PREFIX_LANGTAG}",
  "metadata": { "line": 5, "positionInLine": 9, "startIndex": 155, "stopIndex": 167 },
  "status": "ERROR"
}
```

The parser fails at line 5, position 9 — exactly where `contains-word` appears as predicate. The endpoint enforces SPARQL 1.1 grammar; `contains-word` is QLever-specific syntax and is not available here. **Patterns A and B do not apply. Pattern C is the active query path.**

### 5.3 Confirm author predicate name

Query Works that link to Goethe (`https://d-nb.info/gnd/118540238`) to find the predicate used:

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?work ?pred WHERE {
  ?work ?pred <https://d-nb.info/gnd/118540238> .
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  ?work a ?wtype .
}
LIMIT 10
```

**Results:**

| ?work | ?pred |
|---|---|
| 4427937-1 | author |
| 134483180X | relatedPerson |
| 1367943906 | author |
| 1345022085 | author |
| 1367911087 | author |
| 134558573X | author |
| 1345758731 | poet |
| 1346874786 | author |
| 1347120017 | author |
| 1347121307 | author |

**Conclusion:** The dominant predicate is `gndo:author` (8/10 results). `gndo:poet` appears as a role-specific variant (Goethe wrote lyrics for musical works); `gndo:relatedPerson` is too broad for author linking.

From `gnd_20251218.ttl`, the relevant author-role property hierarchy is:

| Property | Label (en/de) | `rdfs:subPropertyOf` | MARC21 | Scope |
|---|---|---|---|---|
| `gndo:author` | Author / Verfasser | RDA `P60434` | `$4=auta` | Textual works; primary creator |
| `gndo:firstAuthor` | First author / Erste Verfasserschaft | **`gndo:author`**, RDA `P60434` | `$4=aut1` | Subproperty of `author`; single/lead author |
| `gndo:creator` | Creator / Urheber | — | `$4=urhe` | General; no subproperty relation to `author` |
| `gndo:poet` | Poet / Dichter | RDA `P60477` | `$4=dich` | Words of non-dramatic musical works |
| `gndo:composer` | Composer / Komponist | RDA `P60426` | `$4=koma` | Musical works |

**SPARQL does not infer `rdfs:subPropertyOf` without a reasoner.** A query constraining `gndo:author` will miss triples that use `gndo:firstAuthor`, even though `firstAuthor` is a subproperty of `author`. Pattern A must explicitly cover both using `VALUES ?authorPred { gndo:author gndo:firstAuthor }`. `gndo:poet` and `gndo:composer` should be added for coverage of MusicalWork records.

### 5.4 Confirm literal format of `preferredNameForTheWork`

Determines whether VALUES-based queries must include `@de` language-tagged variants.

```bash
curl -s -X POST "https://sparql.dnb.de/api/dnbgnd" \
  -H "Accept: application/sparql-results+json" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode 'query=PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?l (lang(?l) AS ?tag) WHERE {
  <https://d-nb.info/gnd/4427937-1> gndo:preferredNameForTheWork ?l .
}
LIMIT 5'
```

**Result:**

```json
{
  "l": { "type": "literal", "value": "Faust I / Walpurgisnacht / Berlin / Staatsbibliothek Berlin / Ms. germ. qu. 527" },
  "tag": { "type": "literal", "value": "" }
}
```

**Conclusions:**
1. `preferredNameForTheWork` literals have **no language tag** — `@de` variants are not needed in VALUES clauses.
2. GND preferred names are **not clean titles** — this Manuscript entry carries a full ISBD-style string including location and shelfmark, not just the work title. Pattern C's exact FILTER match will not resolve titles like "Faust" against such records; those can only be matched via `gndo:variantNameForTheWork` or through a separate normalized-title query.

---

## 6. Step 1 — Title extraction

Raw `dc:title` strings in DDB ProvidedCHOs are ISBD-encoded: they concatenate title, statement of responsibility, edition, publisher, place, and year into a single field using ISBD punctuation. Sending raw strings to GND produces low-precision matches. Extraction runs before token preparation (Step 3) and GND querying (Step 2).

### 6.1 Method: two-stage pipeline

| Stage | Trigger | Method |
|---|---|---|
| **Primary — ISBD rule-based parser** | Record contains ISBD punctuation markers | Split on ` / `, `. - `, ` : ` per ISBD conventions; take the leading segment as the title |
| **Secondary — NER fallback** | No ISBD markers detected (~71.6% of corpus) | Zero-shot NER with NuNER Zero; extract spans tagged as work titles |

The ISBD parser handles the minority of records that use structured punctuation. NuNER Zero (zero-shot) handles the majority without ISBD markers, where rule-based splitting would either produce nothing or split on the wrong boundary.

### 6.2 ISBD split rules

| Separator | Meaning in ISBD | Action |
|---|---|---|
| ` / ` | Statement of responsibility | Take everything before as title |
| `. - ` | New ISBD area (edition, publication, etc.) | Take everything before as title |
| ` : ` | Subtitle or other title information | Optional split; retain subtitle if short |

Example: `"Faust : eine Tragödie / von Goethe. - Neue Ausg."` → extracted title: `"Faust : eine Tragödie"` (or `"Faust"` if subtitle is stripped).

### 6.3 Output

`extracted_title` — a clean title string passed to Step 3 (token preparation) and used as the FILTER value in Pattern C queries.
`extraction_method` — `"isbd"` or `"ner"`, recorded in the output JSON (FR-07).

Full extraction design is documented in `notes/gnd-title-extraction.md`. NER model selection, evaluation, and bibliographic NER considerations are documented in `notes/ner-bibliographic.md`.

---

## 7. Step 2 — Query patterns

| Query pattern | Fields | Justification |
|---|---|---|
| **A** — Title + author | `gndo:preferredNameForTheWork` (text search); `gndo:author`, `gndo:firstAuthor`, `gndo:poet`, `gndo:composer` (constraint via VALUES) | Author URI narrows the candidate set before text matching; highest precision. Use when author GND URI is available and text index is confirmed (recon 0.2–0.3). |
| **B** — Title only | `gndo:preferredNameForTheWork` (preferred); `gndo:variantNameForTheWork` (UNION fallback) | No author URI available. UNION over variant names increases recall for cases where the DDB title matches a GND alternative form rather than the preferred label. Use when text index is confirmed but no author URI. |
| **C** — FILTER fallback | `gndo:preferredNameForTheWork` (exact string match) | `contains-word` unavailable or not indexed for the predicate (determined by recon 0.2). Exact/normalized string comparison only; no relevance ranking. Lower recall than A/B. |

### 7.1 Pattern A — Title + author, text-indexed (primary)

Used when: author GND URI is available AND `contains-word` is confirmed (recon 0.2).

`gndo:firstAuthor` is a subproperty of `gndo:author` but SPARQL does not infer this without a reasoner — both must be listed explicitly. `gndo:poet` and `gndo:composer` cover musical and lyrical works.

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?work ?prefLabel ?score WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work ?authorPred <{author_gnd_uri}> .
  ?prefLabel contains-word "{title_tokens}"
  BIND(score(?prefLabel) AS ?score)
}
ORDER BY DESC(?score)
TEXTLIMIT 5
LIMIT 10
```

`TEXTLIMIT 5` caps QLever's internal text candidates for performance; `LIMIT 10` caps output rows.

### 7.2 Pattern B — Title only, text-indexed

Used when: no author GND URI is available.
UNION catches cases where the DDB title matches a GND variant name rather than the preferred form.

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?work ?prefLabel ?varLabel ?score WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  {
    ?prefLabel contains-word "{title_tokens}"
    BIND(?prefLabel AS ?varLabel)
    BIND(score(?prefLabel) AS ?score)
  } UNION {
    ?work gndo:variantNameForTheWork ?alt .
    ?alt contains-word "{title_tokens}"
    BIND(?alt AS ?varLabel)
    BIND(score(?alt) AS ?score)
  }
}
ORDER BY DESC(?score)
TEXTLIMIT 5
LIMIT 10
```

### 7.3 Pattern C — FILTER (active query path)

Exact-match only; normalized title (diacritics stripped, lowercased) maximizes recall.

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

### 7.4 Conclusion from Step 0

| Finding | Source | Impact on Step 1 |
|---|---|---|
| `contains-word` raises a SPARQL parse error | Step 0.2 | Patterns A and B are not available. **Pattern C is the sole active query path.** |
| `VALUES ?wtype { gndo:Work gndo:MusicalWork gndo:Manuscript }` covers 580,284 entities (242k + 331k + 7k) | Step 0.1 | Confirmed — use in all patterns |
| Dominant author predicate is `gndo:author`; `gndo:firstAuthor` is a subproperty but SPARQL does not infer it | Step 0.3 | Pattern A must use `VALUES ?authorPred { gndo:author gndo:firstAuthor gndo:poet gndo:composer }` |
| `gndo:poet` appears for lyrical/musical works (Goethe as lyricist) | Step 0.3 | Include `gndo:poet` in `VALUES ?authorPred` |
| `CollectiveManuscript` has zero entities in this dataset | Step 0.1 | Confirmed exclusion; no impact on queries |

Pattern C with author constraint (when author GND URI is available) becomes the effective Pattern A: same `VALUES ?authorPred` constraint, FILTER instead of `contains-word`.

---

## 8. Step 3 — Title token preparation

QLever `contains-word` is word-based, not phrase-based by default. Title preparation has three distinct phases: normalization, tokenization, and filtering.

### 8.1 Normalization (pre-tokenization)

1. **Unicode NFC normalize** — Unicode Standard Annex #15, Normalization Form C: Canonical Decomposition followed by Canonical Composition. Ensures consistent code-point representation before any string operation. Example: `a` + combining diaeresis (two code points, NFD) → `ä` (one code point, NFC). Required so that lowercasing, diacritic stripping, and string comparison behave predictably regardless of source encoding.
2. **Lowercase** — case-fold the NFC-normalized string.
3. **Strip diacritics** — decompose (NFD) then remove combining characters (`unicodedata.category(c) == 'Mn'`). Maps `ä→a`, `ü→u`, `ö→o`, `ß→ss`. Note: test whether the GND endpoint requires this — if the text index is accent-insensitive, stripping may reduce rather than increase recall.

### 8.2 Tokenization

4. **Split on whitespace and punctuation** — split the normalized string into individual word tokens.

### 8.3 Filtering

5. **Remove stopwords:** `der, die, das, ein, eine, von, und, zu, im, in, an, auf, für, mit, bei, dem, den`
6. **Select 2–3 distinctive tokens** (see below)

### 8.4 Distinctive token selection

**Underlying principle:** `contains-word` with multiple tokens is AND semantics — each additional token makes the query more restrictive. Candidate retrieval should maximize recall (get the right GND Work somewhere in the top-10); precision is handled by post-retrieval string scoring in Step 3. The goal is the minimum set of tokens that identifies the work without over-constraining.

**Criterion 1 — Semantic centrality.** Use tokens that are the essential content of the title, not modifiers or structural words:

- **Keep:** nouns, proper nouns (place/person names embedded in titles), semantically unique adjectives
- **Drop even if not in the stopword list:** articles, prepositions, ordinals (*erster, zweiter*), format/edition terms (*Band, Teil, Heft, Auflage, Bd., Nr.*)

Example: *"Die Leiden des jungen Werthers"* → tokens `leiden werthers`; the proper noun alone (`werthers`) is sufficient with Pattern A.

**Criterion 2 — Low collision frequency.** Prefer tokens that appear in few GND Works. Some words are not stopwords but are so common in bibliographic titles that they add almost no discriminating power:

```python
GENERIC_TITLE_WORDS = {
    "briefe", "gedichte", "werke", "schriften", "geschichte",
    "bericht", "katalog", "sammlung", "aufsätze", "texte",
    "band", "teil", "heft", "nummer", "jahrgang",
}
```

Example: *"Gedichte"* alone returns thousands of GND Works. *"faust"* alone is sufficient with an author URI.

This list should be derived empirically from a frequency query against the endpoint, not hardcoded blindly — run after recon 0.1.

**Script:** `scripts/check_generic_title_words.py` — queries the DNB endpoint per word using exact VALUE matching on capitalized German forms (plain literals, no `@de` tag — confirmed by recon 0.4). Run with `python scripts/check_generic_title_words.py`.

**Results** (counts = GND Works whose full `preferredNameForTheWork` is exactly this word or common article+word variants; threshold ≥100 = drop):

| Word | Count | Keep in list? |
|---|---|---|
| briefe | 74 | Yes (low collision) |
| gedichte | 90 | Yes (low collision) |
| werke | 3,212 | **No — drop from list** |
| schriften | 1 | Yes (low collision) |
| geschichte | 5 | Yes (low collision) |
| bericht | 2 | Yes (low collision) |
| katalog | 0 | Yes (low collision) |
| sammlung | 0 | Yes (low collision) |
| aufsätze | 0 | Yes (low collision) |
| texte | 2 | Yes (low collision) |
| band | 0 | Yes (low collision) |
| teil | 1 | Yes (low collision) |
| heft | 0 | Yes (low collision) |
| nummer | 0 | Yes (low collision) |
| jahrgang | 0 | Yes (low collision) |

**Conclusion:** Only `werke` (3,212) exceeds the threshold and is genuinely high-collision as a standalone title. All other words are low-frequency as full titles — GND preferred names are typically qualified strings (ISBD-style, see recon 0.4), not bare single-word titles. `GENERIC_TITLE_WORDS` should be revised to contain only `werke`; the others do not need filtering for Pattern C exact-match queries.

**Decision rule:**

```python
def select_tokens(tokens: list[str]) -> list[str]:
    # tokens: already stopword-filtered, lowercased, diacritics-stripped
    distinctive = [t for t in tokens if t not in GENERIC_TITLE_WORDS and len(t) > 3]
    return distinctive[:3] if len(distinctive) >= 2 else tokens[:3]
```

`len(t) > 3` also drops short high-frequency fragments not caught by the stopword list.

**Why 2–3 tokens specifically:**

- 1 token: usually sufficient with Pattern A (author constraint already narrows heavily); sometimes sufficient for highly distinctive titles in Pattern B
- 2–3 tokens: the sweet spot for Pattern B — enough to discriminate, low risk of AND-excluding the right Work due to GND/DDB title variation
- >3 tokens: increasing risk of false negatives when GND's preferred form differs from DDB's (e.g., GND has *"Faust. Der Tragödie erster Teil"* but DDB has *"Faust: Erster Teil"* — four tokens from the DDB form likely miss the GND entry)

**Multi-word handling:**
- Short (1–3 tokens after filtering): pass all remaining tokens
- Long titles: apply `select_tokens()` above
- High-ambiguity titles (single generic word like *Briefe*, *Gedichte* with no distinctive co-tokens): require author constraint (Pattern A); skip title-only search (Pattern B) if no author URI is available

---

## 9. Step 4 — Post-retrieval scoring

QLever's `score()` is used only to rank candidates before string comparison. Match type is assigned in Python:

| Condition | `match_type` | Triple predicate |
|---|---|---|
| `prefLabel == extracted_title` (case-insensitive) | `exact` | `skos:exactMatch` |
| Normalized match (strip diacritics + punctuation) | `normalized` | `skos:exactMatch` |
| Levenshtein distance ≤ 2 to `prefLabel` or any `variantNameForTheWork` | `fuzzy` | `skos:closeMatch` |
| No candidate above threshold | `unresolved` | — |

`match_confidence` = normalized edit similarity to `prefLabel` (not QLever score).

This logic is unchanged from the original plan in `notes/gnd-title-extraction.md`.

### 9.1 Predicate justification

**`skos:exactMatch`** (exact and normalized matches) — asserts two concepts are "an exact match" and can be used interchangeably for all retrieval purposes, without the OWL identity entailments of `owl:sameAs` (Miles & Bechhofer, *SKOS Simple Knowledge Organization System Reference*, W3C Recommendation, 2009, §10). Semantically appropriate here: a DDB ProvidedCHO and a GND Werk URI are not the same individual (CHO = catalog record for a manifestation; Werk URI = authority record for an abstract work), so asserting OWL individual identity would be incorrect.

**`skos:closeMatch`** (fuzzy matches) — links two concepts "sufficiently similar that they can be used interchangeably in some information retrieval applications" but stops short of asserting full equivalence (Miles & Bechhofer, 2009, §10).

**Why not `owl:sameAs`:** Halpin et al. show that `owl:sameAs` is routinely misused in linked data to express approximate or cross-type identity, producing unwanted OWL entailments downstream. Their recommendation: reserve `owl:sameAs` for verified same-individual identity; use SKOS mapping properties for concept-level matching (Halpin, Hayes, McCusker, McGuinness & Thompson, *When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data*, ISWC 2010, DOI: 10.1007/978-3-642-17746-0_16).

**Match type taxonomy** (exact / normalized / fuzzy) follows the standard candidate generation ladder in entity linking (Shen, Wang & Han, *Entity Linking with a Knowledge Base: Issues, Techniques, and Solutions*, IEEE TKDE 27(2), 2015, §3.1, DOI: 10.1109/TKDE.2014.2327028).

**Levenshtein distance** (Levenshtein, *Binary Codes Capable of Correcting Deletions, Insertions, and Reversals*, Soviet Physics Doklady 10(8), 1966). The threshold of ≤ 2 is a common empirical choice; validate against the gold set planned in `gnd-title-extraction.md` §Paper §4 quality metrics.

---

## 10. Step 5 — Changes to `link_gnd_works.py`

Replace the lobid-gnd REST call (Steps 3–4 in `gnd-title-extraction.md`) with:

```python
import httpx
import asyncio

QLEVER_ENDPOINT = "https://sparql.dnb.de/api/dnbgnd"
CONCURRENCY = 10  # tune up after rate-limit testing

_semaphore = asyncio.Semaphore(CONCURRENCY)

async def query_gnd_werk(
    extracted_title: str,
    author_gnd_uri: str | None
) -> list[dict]:
    tokens = tokenize_for_qlever(extracted_title)
    sparql = (
        QUERY_A.format(title_tokens=tokens, author_gnd_uri=author_gnd_uri)
        if author_gnd_uri
        else QUERY_B.format(title_tokens=tokens)
    )
    async with _semaphore:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(
                QLEVER_ENDPOINT,
                data={"query": sparql},
                headers={"Accept": "application/sparql-results+json"}
            )
    r.raise_for_status()
    return r.json()["results"]["bindings"]
```

Pattern selection:
- Pattern A if `author_gnd_uri` is set
- Pattern B otherwise
- Pattern C as fallback if recon 0.2 shows `contains-word` is unavailable (confirmed — Pattern C is the sole active path)

---

## 11. Step 6 — What this replaces

| Old plan | New plan |
|---|---|
| `GET /gnd/search?q=label:"{title}"&filter=type:Work` (lobid REST) | SPARQL POST to QLever endpoint |
| Endpoint TBD / local infrastructure required | Public DNB endpoint, no setup |
| No text relevance ranking | QLever `score()` ranks candidates |
| `link_gnd_works.py` depended on lobid API availability | Depends on `sparql.dnb.de` uptime (DNB-operated) |
| Title-only or title + author_uri via query param | Same semantics; `gndo:firstAuthor` predicate (verify in recon 0.3) |

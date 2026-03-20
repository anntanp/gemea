# GeMeA — GND Werk Linking via QLever DNB Endpoint

Script: `scripts/link_gnd_works.py`
Replaces: lobid-gnd REST API approach (previously planned but endpoint was TBD)

---

## Endpoint and HTTP API

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

## Step 0 — Recon queries (run once before implementation)

Three things to verify before writing production queries.

### 0.1 Work type coverage

Determine which GND classes to include in `VALUES ?wtype`:

```sparql
SELECT ?type (COUNT(?w) AS ?n) WHERE {
  ?w a ?type .
  FILTER(STRSTARTS(STR(?type), "https://d-nb.info/standards/elementset/gnd#"))
}
GROUP BY ?type ORDER BY DESC(?n) LIMIT 20
```

Expected results include `gndo:Work`, `gndo:MusicalWork`, `gndo:SeriesOfConferencePublications`. Record which to include.

### 0.2 Confirm text index covers `preferredNameForTheWork`

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

If this returns results → use Pattern A/B (text-indexed).
If QLever errors or returns empty → fall back to Pattern C (FILTER REGEX).

### 0.3 Confirm author predicate name

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?pred WHERE {
  <https://d-nb.info/gnd/118607359> ?pred ?obj .
  FILTER(STRSTARTS(STR(?obj), "https://d-nb.info/gnd/"))
}
LIMIT 10
```

Determines whether to use `gndo:firstAuthor` or `gndo:creator` in Pattern A.

---

## Step 1 — Query patterns

| Query pattern | Fields | Justification |
|---|---|---|
| **A** — Title + author | `gndo:preferredNameForTheWork` (text search); `gndo:firstAuthor` (constraint) | Author URI narrows the candidate set before text matching; highest precision. Use when author GND URI is available and text index is confirmed (recon 0.2–0.3). |
| **B** — Title only | `gndo:preferredNameForTheWork` (preferred); `gndo:variantNameForTheWork` (UNION fallback) | No author URI available. UNION over variant names increases recall for cases where the DDB title matches a GND alternative form rather than the preferred label. Use when text index is confirmed but no author URI. |
| **C** — FILTER fallback | `gndo:preferredNameForTheWork` (exact string match) | `contains-word` unavailable or not indexed for the predicate (determined by recon 0.2). Exact/normalized string comparison only; no relevance ranking. Lower recall than A/B. |

### Pattern A — Title + author, text-indexed (primary)

Used when: author GND URI is available AND `contains-word` is confirmed (recon 0.2).

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?work ?prefLabel ?score WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  ?work gndo:firstAuthor <{author_gnd_uri}> .
  ?prefLabel contains-word "{title_tokens}"
  BIND(score(?prefLabel) AS ?score)
}
ORDER BY DESC(?score)
TEXTLIMIT 5
LIMIT 10
```

Replace `gndo:firstAuthor` with the predicate confirmed in recon 0.3.
`TEXTLIMIT 5` caps QLever's internal text candidates for performance; `LIMIT 10` caps output rows.

### Pattern B — Title only, text-indexed

Used when: no author GND URI is available.
UNION catches cases where the DDB title matches a GND variant name rather than the preferred form.

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?work ?prefLabel ?varLabel ?score WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork }
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

### Pattern C — FILTER fallback (if `contains-word` not available on the predicate)

Exact-match only; normalized title (diacritics stripped, lowercased) maximizes recall.

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?work ?prefLabel WHERE {
  VALUES ?wtype { gndo:Work gndo:MusicalWork }
  ?work a ?wtype .
  ?work gndo:preferredNameForTheWork ?prefLabel .
  FILTER(LCASE(STR(?prefLabel)) = "{normalized_title}")
}
LIMIT 10
```

---

## Step 2 — Title token preparation

QLever `contains-word` is word-based, not phrase-based by default.

**Tokenization rules:**
1. Unicode NFC normalize
2. Lowercase
3. Strip diacritics (test both forms — QLever may or may not handle Umlauts natively; see open questions)
4. Remove stopwords: `der, die, das, ein, eine, von, und, zu, im, in, an, auf, für, mit, bei, dem, den`
5. For multi-word titles: select 2–3 distinctive tokens (see below)

### Distinctive token selection

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

## Step 3 — Post-retrieval scoring

QLever's `score()` is used only to rank candidates before string comparison. Match type is assigned in Python:

| Condition | `match_type` | Triple predicate |
|---|---|---|
| `prefLabel == extracted_title` (case-insensitive) | `exact` | `skos:exactMatch` |
| Normalized match (strip diacritics + punctuation) | `normalized` | `skos:exactMatch` |
| Levenshtein distance ≤ 2 to `prefLabel` or any `variantNameForTheWork` | `fuzzy` | `skos:closeMatch` |
| No candidate above threshold | `unresolved` | — |

`match_confidence` = normalized edit similarity to `prefLabel` (not QLever score).

This logic is unchanged from the original plan in `gnd-title-extraction.md`.

### Predicate justification

**`skos:exactMatch`** (exact and normalized matches) — asserts two concepts are "an exact match" and can be used interchangeably for all retrieval purposes, without the OWL identity entailments of `owl:sameAs` (Miles & Bechhofer, *SKOS Simple Knowledge Organization System Reference*, W3C Recommendation, 2009, §10). Semantically appropriate here: a DDB ProvidedCHO and a GND Werk URI are not the same individual (CHO = catalog record for a manifestation; Werk URI = authority record for an abstract work), so asserting OWL individual identity would be incorrect.

**`skos:closeMatch`** (fuzzy matches) — links two concepts "sufficiently similar that they can be used interchangeably in some information retrieval applications" but stops short of asserting full equivalence (Miles & Bechhofer, 2009, §10).

**Why not `owl:sameAs`:** Halpin et al. show that `owl:sameAs` is routinely misused in linked data to express approximate or cross-type identity, producing unwanted OWL entailments downstream. Their recommendation: reserve `owl:sameAs` for verified same-individual identity; use SKOS mapping properties for concept-level matching (Halpin, Hayes, McCusker, McGuinness & Thompson, *When owl:sameAs Isn't the Same: An Analysis of Identity in Linked Data*, ISWC 2010, DOI: 10.1007/978-3-642-17746-0_16).

**Match type taxonomy** (exact / normalized / fuzzy) follows the standard candidate generation ladder in entity linking (Shen, Wang & Han, *Entity Linking with a Knowledge Base: Issues, Techniques, and Solutions*, IEEE TKDE 27(2), 2015, §3.1, DOI: 10.1109/TKDE.2014.2327028).

**Levenshtein distance** (Levenshtein, *Binary Codes Capable of Correcting Deletions, Insertions, and Reversals*, Soviet Physics Doklady 10(8), 1966). The threshold of ≤ 2 is a common empirical choice; validate against the gold set planned in `gnd-title-extraction.md` §Paper §4 quality metrics.

---

## Step 4 — Changes to `link_gnd_works.py`

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
- Pattern C as fallback if recon 0.2 shows `contains-word` is unavailable

---

## Step 5 — What this replaces

| Old plan | New plan |
|---|---|
| `GET /gnd/search?q=label:"{title}"&filter=type:Work` (lobid REST) | SPARQL POST to QLever endpoint |
| Endpoint TBD / local infrastructure required | Public DNB endpoint, no setup |
| No text relevance ranking | QLever `score()` ranks candidates |
| `link_gnd_works.py` depended on lobid API availability | Depends on `sparql.dnb.de` uptime (DNB-operated) |
| Title-only or title + author_uri via query param | Same semantics; `gndo:firstAuthor` predicate (verify in recon 0.3) |

---

## Open questions

- [ ] **Is `gndo:preferredNameForTheWork` in the text index?** Run recon 0.2. Determines Pattern A/B vs Pattern C.
- [ ] **Exact predicate for author link** — `gndo:firstAuthor` or `gndo:creator`? Run recon 0.3.
- [ ] **Umlaut handling in `contains-word`** — does the QLever text index at DNB normalize Umlauts, or must queries use diacritic-stripped tokens? Test `"goethe"` vs `"göthe"` against a known record.
- [ ] **Rate limits on the public endpoint** — no published SLA; start at `CONCURRENCY = 10`, measure latency, tune up cautiously.

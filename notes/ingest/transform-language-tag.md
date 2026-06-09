# GeMeA — Language Tag Normalization in `scripts/transform/`

## 1. Plan

### 1.1 Problem

DDB cortex JSON records carry language codes from the source catalog, including ISO 639-2 collective codes such as `wen` (Sorbian languages). These codes are not valid BCP 47 language subtags. QLever's RDF parser validates language tags against BCP 47 and terminates indexing on encountering an invalid tag.

### 1.2 Intervention point

Language tags enter the N-Quads output at one primary site and several secondary inline sites:

**Primary — `scripts/transform/utils.py:125-127`**, inside `value_to_nt_obj()`:

```python
lang = val.get("lang")
if lang:
    return [f'"{escaped}"@{lang}']   # ← invalid tag emitted here
```

This function handles all `{"$": text, "lang": code}` dict values: titles, descriptions, subjects, locations, etc.

**Secondary — `scripts/transform/emitters.py`**, inline lang extractions that build `f'"{escaped}"@{lang}'` directly without going through `value_to_nt_obj()`:

| Lines | Emitter function |
|-------|-----------------|
| 297, 316 | `emit_subject_triples()` |
| 380, 396–397 | `emit_location_triples()` |
| 424, 434, 452–453 | `emit_creator_triples()` |
| 479, 501–502, 518–519, 522–523 | `emit_title_triples()` |

### 1.3 Implementation

Use `langcodes` (Elia Robyn Speer, v3.5.1) for validation rather than a hand-curated dict.

Two classes of invalid code must be rejected:

1. **Malformed codes** (e.g. `gerger`) — `langcodes.tag_is_valid()` returns `False`.
2. **IANA collection subtags** (e.g. `wen`, `gem`) — `langcodes.tag_is_valid()` returns `True` (they ARE in the IANA registry), but QLever rejects them. Detected by membership in `_IANA_COLLECTION_CODES`, a `frozenset` parsed at import time from the IANA registry bundled with `langcodes` (`data/language-subtag-registry.txt`, `Scope: collection` blocks). Currently 116 codes.

In `utils.py`:

```python
_IANA_COLLECTION_CODES: frozenset[str] = _build_iana_collection_codes()

@lru_cache(maxsize=512)
def _invalid_bcp47(lang: str) -> bool:
    return not langcodes.tag_is_valid(lang) or lang in _IANA_COLLECTION_CODES

# In value_to_nt_obj():
if lang and _invalid_bcp47(str(lang)):
    if lang_coll is not None:
        lang_coll.add(str(lang))
    lang = "und"
```

All invalid codes (collective or malformed) → `"und"`. Original code retained via `dcterms:language` provenance triple (§1.4). The `lru_cache` amortizes the `tag_is_valid` call; only ~256 distinct codes exist in the corpus.

### 1.4 Provenance retention

**Information loss.** Mapping any collective code to `und` is semantically correct but lossy: `@gem` and `@und` are not equivalent — the former asserts Germanic-family membership, the latter asserts nothing. This loss is inherent to the normalization; the catalog data itself did not identify the specific language.

To partially mitigate this in the RDF graph: at each emission site, when `orig_lang != norm_lang`, emit unconditionally to `https://gemea.ise.fiz-karlsruhe.de/graph/lang-title`:

```turtle
GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/lang-title> {
    <subject> dcterms:language <http://id.loc.gov/vocabulary/iso639-2/gem> .
}
```

### 1.5 Mapping curation

Normalization uses `langcodes` (v3.5.1) rather than a hand-curated dict. All 28 corpus collective codes (identified by cross-referencing the LOC ISO 639-2 table against `data/processed/lang_counts.csv`) normalize to `und`. So does any other invalid or malformed code (e.g. `gerger`). Original codes are preserved in the `graph/lang-title` named graph (§1.4).

---

## 2. ADR

**Status:** Accepted
**Date:** 2026-05-10

### 2.1 Context

DDB source data contains ISO 639-2 collective codes (e.g. `wen`) and malformed codes (e.g. `gerger`) in the `lang` field of cortex JSON. These are not valid BCP 47 language subtags for individual-language assertions. QLever validates RDF language tags against BCP 47 and terminates indexing on the first invalid tag.

### 2.2 Decision

In `value_to_nt_obj()` (`utils.py`), replace any invalid lang tag with `"und"` using `langcodes` (v3.5.1) for validation. Two failure modes are handled:

1. Codes rejected by `langcodes.tag_is_valid()` (e.g. `gerger`) → `"und"`
2. Codes in `_IANA_COLLECTION_CODES` — the set of `Scope: collection` subtags from the IANA registry bundled with `langcodes` (116 codes, including `wen`, `gem`, etc.) — → `"und"`

When a code is normalized, emit `dcterms:language <http://id.loc.gov/vocabulary/iso639-2/{orig_code}>` unconditionally to `https://gemea.ise.fiz-karlsruhe.de/graph/lang-title`. The provenance subject is `ddb_uri`.

### 2.3 Consequences

- QLever indexing succeeds on records carrying previously invalid language tags.
- N-Quads output contains only valid BCP 47 language tags; original codes preserved via `dcterms:language` URI triples.
- **Information loss**: `wen` → `und` (was `hsb` in the earlier dict-based approach). The `dcterms:language` triple partially recovers the original assertion.
- No manual maintenance: `_IANA_COLLECTION_CODES` updates automatically with `langcodes` upgrades. Any newly introduced invalid code is caught without a code change.
- A new named graph `https://gemea.ise.fiz-karlsruhe.de/graph/lang-title` is added. `graph/prov` is not touched.

### 2.4 Rejected alternatives

**Hand-curated `LANG_NORMALIZE` dict.**
Requires manual maintenance. Missed `gerger` on the first pass. `langcodes` covers all cases without manual curation.

**Strip the language tag on normalization failure.**
Falls back to a plain `xsd:string` literal, losing all language signal. Rejected: `und` asserts "undetermined language" and is a valid BCP 47 tag, which is preferable.

---

## 3. Code Change Plan

### 3.1 Overview

| # | File | Location | Change |
|---|------|----------|--------|
| C1 | `utils.py` | module level | add `_IANA_COLLECTION_CODES`, `_invalid_bcp47()`; import `langcodes` |
| C2 | `utils.py` | `value_to_nt_obj()` | validate `lang` via `_invalid_bcp47()`; populate optional `lang_coll` set |
| C3 | `emitters.py` | inline lang sites (×9) | normalize `lang`; populate `lang_coll` inline; update imports |
| C4 | `emitters.py` | `emit_ddbedm_triples()` | pass `lang_coll` to every `value_to_nt_obj()` call; return it |
| C5 | `transform.py` | `transform_record()` | receive `lang_coll`; emit provenance triples to `lang-title` stream |
| C6 | `constants.py` | graph URIs | add `GRAPH_LANG_TITLE` constant |

### 3.2 C1 — `langcodes` validation helpers

Add to `utils.py` at module level (imports: `langcodes`, `lru_cache`, `Path`). See §1.3 for code. `langcodes==3.5.1` added to `requirements.txt`.

### 3.3 C2 — validate in `value_to_nt_obj()`

Add `lang_coll: set[str] | None = None` parameter (mirrors existing `sani_ctr` pattern):

```python
lang = val.get("lang")
if lang and _invalid_bcp47(str(lang)):
    if lang_coll is not None:
        lang_coll.add(str(lang))
    lang = "und"
if lang:
    return [f'"{escaped}"@{lang}']
```

No return type change. `und`-normalized codes produce `@und` literals — there is no `und` filter in this pipeline.

### 3.4 C3 — scope: CHO fields only

Empirical analysis (`analyse_lang_tags_by_entity.py`) confirmed no collective codes on non-CHO entities (Agent prefLabels, Place prefLabels, Concept labels, etc.) in the corpus. Secondary emitters (`emit_subject_triples`, `emit_creator_triples`, `emit_contributor_triples`, `emit_current_location_triples`) are **not changed** — their inline `f'"{escaped}"@{lang}'` constructions are untouched.

`value_to_nt_obj()` normalization (C2) silently fixes any edge cases that slip through those paths, but `lang_coll` tracking is restricted to CHO fields only.

### 3.5 C4 — pass `lang_coll` through `emit_ddbedm_triples()` and `emit_mocho_triples()`

Add `lang_coll: set[str] | None = None` parameter to both functions. Pass to every `value_to_nt_obj()` call that processes CHO fields (title, generic property loop). Return signature of `emit_ddbedm_triples()` is unchanged — `lang_coll` is mutated in place.

```python
# emit_ddbedm_triples()
for obj_nt in value_to_nt_obj(val, sani_ctr, lang_coll): ...

# emit_mocho_triples() — title and generic loop
for obj_nt in value_to_nt_obj(cho.get("title"), sani_ctr, lang_coll): ...
for obj_nt in value_to_nt_obj(val, sani_ctr, lang_coll): ...
```

### 3.6 C5 — provenance triples in `transform_record()`

Create `lang_coll: set[str] = set()`, pass to both emitters (mutated in place), emit one provenance triple per unique `orig_lang` after emitters complete:

```python
_DCTERMS_LANGUAGE = "http://purl.org/dc/terms/language"
_ISO639_2_BASE    = "http://id.loc.gov/vocabulary/iso639-2/"

lang_coll: set[str] = set()
emit_ddbedm_triples(rdf, GRAPH_DDBEDM, lang_coll)
emit_mocho_triples(..., lang_coll=lang_coll)

if lang_coll:
    ddb_nt = f"<{ddb_uri}>"
    for orig_lang in sorted(lang_coll):
        streams[GRAPH_LANG_TITLE].append(make_nq(
            ddb_nt,
            f"<{_DCTERMS_LANGUAGE}>",
            f"<{_ISO639_2_BASE}{orig_lang}>",
            GRAPH_LANG_TITLE,
        ))
```

Deduplication is free — `lang_coll` is a `set`.

### 3.7 C6 — `GRAPH_LANG_TITLE` constant

Add to `constants.py`. `GRAPH_PROV` is not touched.

```python
GRAPH_LANG_TITLE = "https://gemea.ise.fiz-karlsruhe.de/graph/lang-title"
```

---

## 4. Test Cases

Test file: `scripts/transform/tests/test_transform.py`

### 4.1 `LANG_NORMALIZE` dict

```python
def test_lang_normalize_wen():
    assert LANG_NORMALIZE["wen"] == "hsb"

def test_lang_normalize_collective_to_und():
    for code in ("gem", "sem", "dra", "alg", "btk", "sit", "sla"):
        assert LANG_NORMALIZE[code] == "und", code

def test_lang_normalize_passthrough():
    # valid BCP 47 codes must not appear in the dict
    for code in ("ger", "eng", "lat", "hsb", "dsb", "und", "zxx"):
        assert code not in LANG_NORMALIZE, code

def test_lang_normalize_complete():
    expected = {
        "wen", "alg", "bat", "bnt", "btk", "cau", "crp", "dra",
        "gem", "inc", "ira", "map", "mkh", "myn", "nic", "nub",
        "oto", "pra", "roa", "sai", "sal", "sem", "sit", "sla",
        "smi", "tai", "tup", "tut",
    }
    assert set(LANG_NORMALIZE.keys()) == expected
```

### 4.2 `value_to_nt_obj()` — normalization (C2)

```python
def test_value_to_nt_obj_wen_normalized():
    val = {"$": "Janske jěchanje", "lang": "wen"}
    assert value_to_nt_obj(val) == ['"Janske jěchanje"@hsb']

def test_value_to_nt_obj_valid_lang_unchanged():
    val = {"$": "Faust", "lang": "ger"}
    assert value_to_nt_obj(val) == ['"Faust"@ger']

def test_value_to_nt_obj_collective_to_und():
    val = {"$": "some text", "lang": "gem"}
    assert value_to_nt_obj(val) == ['"some text"@und']

def test_value_to_nt_obj_no_lang():
    val = {"$": "untitled"}
    assert value_to_nt_obj(val) == ['"untitled"']

def test_value_to_nt_obj_lang_coll_populated():
    coll: set[str] = set()
    val = {"$": "Janske jěchanje", "lang": "wen"}
    value_to_nt_obj(val, lang_coll=coll)
    assert coll == {"wen"}

def test_value_to_nt_obj_lang_coll_not_populated_for_valid():
    coll: set[str] = set()
    val = {"$": "Faust", "lang": "ger"}
    value_to_nt_obj(val, lang_coll=coll)
    assert coll == set()
```

### 4.3 Provenance triple (C5)

```python
DCTERMS_LANGUAGE_IRI = "http://purl.org/dc/terms/language"
GRAPH_LANG_TITLE     = "https://gemea.ise.fiz-karlsruhe.de/graph/lang-title"
ISO639_2_BASE        = "http://id.loc.gov/vocabulary/iso639-2/"

def test_provenance_triple_emitted_to_lang_title(record_with_wen):
    streams, *_ = transform_record(record_with_wen, ...)
    lang_lines = streams.get(GRAPH_LANG_TITLE, [])
    prov = [l for l in lang_lines
            if f"<{DCTERMS_LANGUAGE_IRI}>" in l and f"<{ISO639_2_BASE}wen>" in l]
    assert len(prov) == 1
    assert ddb_uri in prov[0]   # subject is ddb_uri, not cho_uri

def test_no_provenance_triple_for_valid_lang(record_with_ger):
    streams, *_ = transform_record(record_with_ger, ...)
    assert GRAPH_LANG_TITLE not in streams

def test_provenance_triple_multiple_collective_langs(record_with_gem_and_sem):
    streams, *_ = transform_record(record_with_gem_and_sem, ...)
    lang_lines = streams.get(GRAPH_LANG_TITLE, [])
    uris = {l.split(f"<{ISO639_2_BASE}")[1].split(">")[0]
            for l in lang_lines if f"<{ISO639_2_BASE}" in l}
    assert uris == {"gem", "sem"}
```

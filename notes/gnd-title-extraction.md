# GeMeA — GND Werk Linking: Title Extraction

Script: `scripts/link_gnd_works.py`
Pipeline position: after rdf2jsonld, before mocho

---

## The problem

DDB `dc:title` strings are not clean bibliographic titles — they follow **ISBD punctuation conventions** and pack multiple data elements into a single string:

```
Faust / von Johann Wolfgang von Goethe. - 3. Aufl. - Weimar : Böhlau, 1887
```

This single `dc:title` value contains: title, statement of responsibility, edition, place of publication, publisher, and year. Sending the raw string to the lobid-gnd Werk lookup fails or produces low-precision results.

---

## Step 1 — Rule-based ISBD parser (primary)

ISBD uses standardized punctuation as area separators. Split on these markers in order:

| Marker | Splits off |
|--------|-----------|
| ` / ` | Statement of responsibility (everything after) |
| ` : ` | Subtitle (keep) or publisher (drop if preceded by place) |
| `. - ` | New ISBD area (edition, publication info, etc.) |

**Algorithm:**

```python
def extract_title_isbd(raw: str) -> str | None:
    # Split on statement of responsibility
    if " / " in raw:
        title_part = raw.split(" / ")[0].strip()
    else:
        title_part = raw
    # Drop anything after ". -" (edition/publication area)
    if ". - " in title_part:
        title_part = title_part.split(". - ")[0].strip()
    # Keep subtitles joined by " : " (strip trailing punctuation)
    return title_part.rstrip(".,;:/").strip() or None
```

`extraction_method = "isbd"` when this produces a non-empty result shorter than the raw string.

---

## Step 2 — NER fallback (secondary)

For records without ISBD markers (~15–30% of DDB records based on provider conventions), use a German NER model to label spans:

**Model**: `deepset/gbert-large` fine-tuned on bibliographic NER, or a custom-trained model with label set:

| Label | Example |
|-------|---------|
| `TITLE` | "Faust" |
| `PERSON` | "Johann Wolfgang von Goethe" |
| `PUBLISHER` | "Böhlau" |
| `YEAR` | "1887" |
| `EDITION` | "3. Aufl." |

Extract the `TITLE` span(s). If multiple `TITLE` spans: join with ` : ` (main title + subtitle).

`extraction_method = "ner"` for these records. NER is slower — only invoke when ISBD parsing fails.

---

## Step 3 — Author GND URI cross-reference

The extracted title alone is often ambiguous (many works share the same title). Cross-referencing with the author's GND URI narrows the lobid-gnd Werk result set.

If the `edm:ProvidedCHO` links to an `edm:Agent` that already has a `d-nb.info/gnd/` URI (from Phase 1b pre-population or the source data), pass it to the lobid-gnd query:

```
GET /gnd/search?q=label:"{title}" AND creator:{gnd_person_uri}&filter=type:Work
```

Without an author GND URI, fall back to title-only search:

```
GET /gnd/search?q=label:"{title}"&filter=type:Work
```

---

## Step 4 — lobid-gnd Werk lookup and scoring

lobid-gnd API: `https://lobid.org/gnd`

```
GET /gnd/search?q=label:"{extracted_title}"&filter=type:Work&size=5
```

Score the top candidates:

| Condition | Match type | Predicate |
|-----------|-----------|-----------|
| Exact label match (case-insensitive) | `exact` | `owl:sameAs` |
| Normalized match (diacritics, punctuation stripped) | `normalized` | `owl:sameAs` |
| Fuzzy match (Levenshtein ≤ 2) | `fuzzy` | `skos:closeMatch` |
| No candidate above threshold | `unresolved` | — (no triple written) |

---

## Scale: deduplication

65M ProvidedCHOs, but many share identical `dc:title` strings (multiple copies of the same work across institutions). Deduplicate before calling lobid-gnd:

```
unique titles ≈ 5–10M (estimated; actual number computed during run)
```

**Strategy:**
1. First pass: collect all `(raw_title, author_gnd_uri_if_available)` pairs from rdf2jsonld output
2. Deduplicate by pair; run lobid-gnd lookups on unique pairs only
3. Second pass: join results back to all ProvidedCHOs sharing the same pair

This reduces API calls from ~65M to ~5–10M and respects lobid-gnd rate limits.

---

## Output format

Per-ProvidedCHO JSON record (written to `data/raw/gnd-works/`):

```json
{
  "cho_uri": "https://www.deutsche-digitale-bibliothek.de/item/ABC123",
  "raw_title": "Faust / von Johann Wolfgang von Goethe. - 3. Aufl. - Weimar : Böhlau, 1887",
  "extracted_title": "Faust",
  "extraction_method": "isbd",
  "author_gnd_uri": "https://d-nb.info/gnd/118540238",
  "gnd_werk_uri": "https://d-nb.info/gnd/118607359",
  "match_type": "exact",
  "match_confidence": 1.0
}
```

Unresolved records omit `gnd_werk_uri`, `match_type`, `match_confidence`.

The `extraction_method` field enables paper §4 quality reporting: how many records were resolved by rule vs. NER, and what the overall Werk linking coverage is.

---

## Integration with mocho

mocho reads both the rdf2jsonld output and the GND Werk triples produced by `link_gnd_works.py`. The GND Werk URI is the key mocho uses to group `edm:ProvidedCHO` instances into `mocho:Work` entities. ProvidedCHOs with `gnd_werk_uri = null` (unresolved) remain as standalone Manifestations without a parent Work.

See `notes/mocho-alignment.md` for mocho internals.

---

## Paper §4 quality metrics

- **Title extraction coverage**: % of ProvidedCHOs where ISBD parsing succeeded vs. NER fallback vs. unresolved
- **GND Werk linking rate**: % of ProvidedCHOs with a confirmed GND Werk URI
- **Work grouping size distribution**: how many ProvidedCHOs per `mocho:Work` (distribution; median; max)
- **Precision sample**: manual spot-check of 100 linked pairs

Target: ≥ 70% Werk linking rate (condition for enabling `/work/{id}` API and WEMI pages).

# Cortex JSON — ProvidedCHO Schema

Inspected from `goethe-faust/data/items-excerpt-1000.json` (1,000 items, Deutsche Fotothek / LIDO source).
Script: `scripts/analysis/inspect_cho_keys.py`
CSV: `data/processed/cho_keys.csv`

---

## 1. ProvidedCHO keys (by frequency)

| Key | Count | Notes |
|-----|-------|-------|
| `about` | 1000 | URI of the ProvidedCHO |
| `title` | 1000 | `{resource, lang, $}` dict or list |
| `hasMet` | 952 | List of event refs; see §3 |
| `identifier` | 864 | List of strings |
| `hasType` | 840 | List of type refs |
| `hierarchyType` | 799 | `htype_NNN` code string |
| `dcType` | 792 | `{lang, $}` dict |
| `description` | 766 | List of `{lang, $}` dicts |
| `extent` | 662 | List of `{lang, $}` dicts |
| `aggregationEntity` | 645 | bool string |
| `edmType` | 644 | `"IMAGE"` etc. |
| `language` | 605 | ISO 639-2 code string |
| `dcTermsLanguage` | 605 | List of `{resource, …}` dicts |
| `dcSubject` | 590 | List of `{lang, $}` dicts |
| `dcTermsSubject` | 590 | List of `{resource, …}` dicts |
| `isPartOf` | 589 | List of `{resource, …}` dicts |
| **`date`** | **446** | List of strings — free-text dc:date |
| `hierarchyPosition` | 445 | String |
| `currentLocation` | 430 | `{resource, …}` dict |
| **`issued`** | **421** | List of `{resource, lang, $}` dicts — dcterms:issued |
| `creator` | 355 | List of `{resource, lang, $}` dicts |
| `contributor` | 270 | List of `{resource, lang, $}` dicts |
| `format` | 196 | `{lang, $}` dict |
| `spatial` | 75 | List of `{resource, lang, $}` dicts |
| `alternative` | 55 | List of `{lang, $}` dicts |

---

## 2. Date fields

### `date` (dc:date)
- Free-text string, often with parenthetical qualifier: `"2018 (Fotografische Aufnahme)"`, `"18300213"`
- Parsed by `parse_dc_date()` in `export_ddb.py`

### `issued` (dcterms:issued)
- List of `{resource: null, lang: null, $: "year"}` dicts
- `$` holds the year string: `"1895"`, `"[1849]"`, `"2014"`
- Extracted by `_scalar_values(cho.get("issued"))` → reads `$` field
- Present in 421/1000 items (42%)

### `created` (dcterms:created)
- **Not present** in ProvidedCHO for this dataset
- `cho.get("created")` always returns `None`
- Fix in `export_ddb_parquet.py` is correct but has no effect for LIDO/Fotothek items

---

## 3. hasMet — event chain

Events referenced via `hasMet` (list of `{resource: "<event-id>"}` dicts).
Events live under `rdf.Event` keyed by `about`. Each event has:
- `hasType.resource` — LIDO event type URI
- `occuredAt.resource` — TimeSpan URI (often null for library objects)
- TimeSpans live under `rdf.TimeSpan` keyed by `about`, with `begin`/`end` fields

**Key finding:** For Sector 2 library objects, `occuredAt` is null across all tested records — the LIDO event chain does not yield dates. Only the direct `issued` field on ProvidedCHO is populated.

---

## 4. Implications for export_ddb_parquet.py

| Column | Source | Status |
|--------|--------|--------|
| `dc_date` | `cho.get("date")` → `parse_dc_date()` | Works |
| `dc_issued` | `cho.get("issued")` first, then LIDO chain | Works — direct field is the only populated source |
| `dc_created` | `cho.get("created")` first, then LIDO chain | Fix is correct; field absent in this dataset so column stays empty |

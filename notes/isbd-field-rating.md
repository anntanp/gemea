# GeMeA — ISBD Field Rating: Spec and Methodology

**Script:** `scripts/rate_isbd_fields.py`
**Output:** `data/processed/isbd_field_ratings.csv`, `data/processed/isbd_examples.csv`
**Phase:** 0a — NER Training Data (see [roadmap.md](roadmap.md))
**ADR:** [isbd-field-rating-adr.md](isbd-field-rating-adr.md)

---

## Objective

Map the presence of bibliographic fields in each title string across all 4.47M records in `DF_DE_TITLES`. The field presence flags are used to:

1. **Select silver candidates** for NER training — records where ISBD structure clearly identifies multiple labelable spans
2. **Stratify** the NER evaluation gold set by field combination type
3. **Understand corpus coverage** — which fields are detectable from the title string alone vs. requiring other columns (`dc_publisher`, `dc_creator`, etc.)

---

## ISBD Area Structure

ISBD organises a catalog record into areas separated by ` . - ` (space · period · space · hyphen · space). Within DF_DE_TITLES, the `title` column contains the full ISBD string as catalogued, not just the proper title. A fully structured record looks like:

```
Title proper : other title information / statement of responsibility
  . - Edition statement
  . - Place of publication : Publisher, Year
  . - (Series title ; volume number)
```

**Examples from the corpus:**

```
Die höchstnöthige Sterbe-Schule : Bey Christlicher Beerdigung / Christian Gerber
```
→ Title area only; no `. -`; has ` :` (other title) and ` /` (SoR)

```
Faust : der Tragödie erster Teil / Johann Wolfgang von Goethe. - 12. Aufl. - Leipzig : Insel-Verlag, 1920
```
→ Full structural record; area separator present; PLACE, PUBLISHER, YEAR all detectable

```
Critik der reinen Vernunft / Immanuel Kant. - Riga : Hartknoch, 1781. - (Philosophische Bibliothek ; Bd. 37)
```
→ Title, SoR, publication area, series area

The `. - ` separator is the primary structural signal. Records **without** it are catalogued with incomplete ISBD punctuation — the title string may still contain useful signals (` :`, ` /`, year) but field boundary precision is lower.

---

## Detection Rules

### Structural tier (has `. - `)

Split on `. - `. Parse `area[0]` as the title area; `area[1:]` as subsequent areas.

| Field | Source area | Pattern | Notes |
|---|---|---|---|
| `TITLE` | area[0] | Always present | The string before the first ` :` or ` /` |
| `OTHER_TITLE` | area[0] | ` :` | Subtitle / other title info after the colon |
| `PERSON` | area[0] | ` /` | Statement of responsibility |
| `PARALLEL_TITLE` | area[0] | ` =` | Title in another language; Expression-level |
| `EDITION` | area[1+] | Edition keyword regex | "Aufl.", "Ausg.", "rev.", "überarb.", etc. |
| `PLACE` | area[1+] | `\w.+ : \w` in rest | Left side of imprint " : " block |
| `PUBLISHER` | area[1+] | `\w.+ : \w` in rest | Right side of imprint " : " block |
| `YEAR` | area[1+] | `\b(1[4-9]\d{2}\|20[012]\d)\b` | 4-digit year in publication area |
| `SERIES` | area[1+] | `\([^)]+;\s*[^)]*\d[^)]*\)` | Parenthetical with semicolon + digit |
| `VOLUME` | anywhere | `\b(Bd\|Teil\|Vol\|Heft\|Nr\|Lfg)\.\s*\d+` | Part / volume number |

### Heuristic tier (no `. - `)

Apply whole-string patterns. Reduced precision for PLACE/PUBLISHER (only `Verlag` keyword → PUBLISHER; PLACE not flagged without area structure).

| Field | Pattern | Precision note |
|---|---|---|
| `OTHER_TITLE` | ` :` anywhere | May fire on non-ISBD colons |
| `PERSON` | ` /` anywhere | Generally reliable |
| `PARALLEL_TITLE` | ` =` anywhere | Generally reliable |
| `EDITION` | Edition keyword regex | Generally reliable |
| `YEAR` | 4-digit year regex | May fire on non-publication years in text |
| `PUBLISHER` | `\bVerlag\b` or `\bPress\b` | Low recall; misses most publishers |
| `PLACE` | Not detected | Requires `. -` area structure |
| `SERIES` | `\([^)]+;\s*[^)]*\d[^)]*\)` | Generally reliable |
| `VOLUME` | Volume keyword regex | Generally reliable |

---

## Output Schema

`data/processed/isbd_field_ratings.csv` — one row per record.

| Column | Type | Description |
|---|---|---|
| `obj_id` | str | DDB object ID — link: `https://ddb.de/item/<obj_id>` |
| `title` | str | Original title string |
| `has_dot_dash` | bool | `. -` area separator present |
| `f_title` | int | Always 1 |
| `f_other_title` | int | Subtitle / other title info detected |
| `f_person` | int | Statement of responsibility detected |
| `f_parallel` | int | Parallel title detected |
| `f_edition` | int | Edition statement detected |
| `f_place` | int | Place of publication detected |
| `f_publisher` | int | Publisher detected |
| `f_year` | int | Publication year detected |
| `f_series` | int | Series block detected |
| `f_volume` | int | Volume / part number detected |
| `n_fields` | int | Sum of all f_* flags |
| `silver_tier` | int | 0 / 1 / 2 — see below |

`data/processed/isbd_examples.csv` (generated with `--examples N`) — N records per ISBD pattern with `ddb_url`.

---

## Silver Tier Assignment

| Tier | Criteria | Intended use in NER training |
|---|---|---|
| **2** | `has_dot_dash AND f_person AND any(f_edition, f_place, f_publisher, f_year, f_series)` | Primary training set — structural annotation enables multi-field span labeling with high confidence |
| **1** | `n_fields ≥ 3` OR `(f_person AND f_year)` | Augmentation set — partial annotation; Work + Expression level |
| **0** | All others | Not selected as silver candidates |

Tier 2 is the primary source for silver labels. Tier 1 is used for augmentation after tier-2 evaluation.

---

## Expected Coverage

Based on `isbd-title-analysis.md` (DF_DE_TITLES, 4.47M rows):

| Field | Expected coverage | Source |
|---|---|---|
| `OTHER_TITLE` (` :`) | ~20% | 909k / 4.47M from analysis |
| `YEAR` | ~20–30% | Includes both structural and heuristic |
| `PERSON` (` /`) | ~0.8% | 34k / 4.47M from analysis |
| `PARALLEL_TITLE` (` =`) | ~0.6% | 26k / 4.47M from analysis |
| `SERIES` (structural) | < 5% | Subset of has_dot_dash records |
| `EDITION` | ~5–10% | Estimated from keyword frequency |
| `PLACE` / `PUBLISHER` | ~5–10% | Subset of has_dot_dash records with imprint |

`has_dot_dash` (structural completeness) is expected at ~28% (consistent with ISBD coverage analysis). Tier-2 silver candidates will be a subset of those.

---

## Limitations

- **PLACE** is only detected in the structural tier. Most non-ISBD records will have `f_place = 0` even if place information exists elsewhere (e.g., `dc_publisher` contains "Dresden : Riedel").
- **PUBLISHER** heuristic recall is low — "Verlag" keyword misses many publishers. The `dc_publisher` column could supplement detection but is kept out of scope (title-string-only rating).
- **` ;` ambiguity** — ` ;` in the title area signals a subsequent statement of responsibility; in a series area it separates title from volume number. The script does not distinguish these; SERIES detection requires the parenthetical + digit pattern.
- **Multi-volume records** — some records have multiple `. -` separators for volume entries; the script takes only the first split, potentially missing volume-level fields in entries 3+.
- **False positives in heuristic tier** — ` :` fires on non-ISBD colons (URLs, ratios); ` /` fires on fractions or paths. Silver tier 1 should be validated on a ~200-record sample before use.

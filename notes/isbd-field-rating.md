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
→ Title area only; no `. -`; has ` :` (other title) and ` /` (SoR[^sor])

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

[^sor]: **SoR — Statement of Responsibility** (Verantwortlichkeitsangabe). The ISBD term for the portion of a catalog record that names those responsible for the intellectual content: authors, editors, translators, illustrators, etc. In MARC 21 it is encoded in 245 $c, introduced by ` / ` (trailing mark on 245 $b). Multiple contributors are separated by ` ; `. Example: `Titel / Autor ; Herausgeber ; Übersetzer`. In the rating script, ` /` is the primary cue for detecting `PERSON` (and `TRANSLATOR`) spans. Sources: ISBD consolidated edition (2011), Area 1, §1.4 <https://www.ifla.org/files/assets/cataloguing/isbd/isbd-cons_20110321.pdf>; ThULB Jena, ISBD-Interpunktion <https://koha-wiki.thulb.uni-jena.de/erschliessung/katalogisierung/handbuecher/isbd-interpunktion/>

---

## Detection Rules

Source: ThULB Jena, *ISBD-Interpunktion* (Koha-Wiki, CC BY-SA 4.0). <https://koha-wiki.thulb.uni-jena.de/erschliessung/katalogisierung/handbuecher/isbd-interpunktion/>

ISBD punctuation marks are **trailing** — each mark appears at the end of the preceding MARC subfield, immediately before the next subfield's content. In a flat ISBD string (as stored in `title`), the mark therefore precedes the field it introduces. The table below maps each NER label to its ISBD punctuation signal, MARC source field, and detection pattern.

### Structural tier (has `. - `)

Split on `. - ` (the area separator formed by the trailing `.` of one MARC field group and the ` - ` leader of the next). Parse `area[0]` as the title area; `area[1:]` as subsequent areas.

**Group 1 — Title and Statement of Responsibility (MARC 245)**

| Field | MARC subfield | Trailing mark | Signal in flat string | Detection pattern |
|---|---|---|---|---|
| `TITLE` | 245 $a | ` :` (if $b follows) or ` /` (if $c follows) | Always present as leading content | String before first ` :` or ` /` |
| `OTHER_TITLE` | 245 $b | ` /` (if $c follows) | ` :` precedes the subtitle | ` :` in area[0] |
| `PERSON` (SoR[^sor]) | 245 $c | `.` (area close) | ` /` precedes the SoR | ` /` in area[0] |
| `PARALLEL_TITLE` | 246 / 245 | ` =` | ` =` precedes parallel title | ` =` in area[0] |
| `VOLUME` (part number in title) | 245 $n | `,` | `Bd. N,` or `Teil N,` | `\b(Bd\|Teil\|Vol\|Nr)\.\s*\d+` |

Note: ` :` appears in **both** Group 1 (before subtitle) and Group 4 (before publisher). The area separator `. - ` is used to distinguish them — ` :` before the first `. - ` belongs to the title area; ` :` after it belongs to the publication area.

**Group 2 — Edition (MARC 250)**

| Field | MARC subfield | Trailing mark | Detection pattern |
|---|---|---|---|
| `EDITION` | 250 $a | `.` (area close) | Edition keyword regex: `Aufl`, `Ausg`, `ed.`, `überarb`, `erw`, `verb`, `Neuausg` |

**Group 4 — Publication Area (MARC 264)**

| Field | MARC subfield | Trailing mark | Detection pattern |
|---|---|---|---|
| `PLACE` | 264 $a | ` :` | Left of ` : ` in area[1+] |
| `PUBLISHER` | 264 $b | `,` | Right of ` : ` up to `,` in area[1+] |
| `YEAR` | 264 $c | `.` (area close) | `\b(1[4-9]\d{2}\|20[012]\d)\b` in area[1+] |

**Group 6 — Series (MARC 490)**

| Field | MARC subfield | Trailing mark | Detection pattern |
|---|---|---|---|
| `SERIES` | 490 $a | ` ;` | `\([^)]+;\s*[^)]*\d[^)]*\)` in area[1+] |
| `VOLUME` (series numbering) | 490 $v | `.` | Digit after ` ;` inside parenthetical |

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

## Actual Coverage

Results from `rate_isbd_fields.py` on `DF_DE_TITLES_20240125b.pkl` (4,477,780 records), 2026-03-21.

| Field | Count | % | Notes |
|---|---|---|---|
| `has_dot_dash` | 53,785 | **1.2%** | ⚠ Much lower than expected — see below |
| `f_title` | 4,477,780 | 100.0% | Always present |
| `f_other_title` | 905,344 | **20.2%** | Consistent with prior analysis (909k) |
| `f_person` | 33,739 | **0.8%** | Consistent with prior analysis (34k) |
| `f_person_compound` | 1,040 | 0.0% | Compound SoR (`/ ... ;`) — very sparse |
| `f_parallel` | 26,084 | **0.6%** | Consistent with prior analysis (26k) |
| `f_edition` | 158,991 | **3.6%** | Lower end of expected range |
| `f_place` | 6,241 | **0.1%** | Structural-only; subset of has_dot_dash |
| `f_publisher` | 8,229 | **0.2%** | Includes `Verlag` keyword hits |
| `f_year` | 652,082 | **14.6%** | Below expected 20–30%; see below |
| `f_series` | 620 | 0.0% | Structural-only; very sparse |
| `f_volume` | 83,772 | **1.9%** | |

**Silver tiers:**

| Tier | Count | % |
|---|---|---|
| Tier 2 (structural, multi-field) | 4,613 | 0.1% |
| Tier 1 (heuristic, partial) | 335,524 | 7.5% |
| Tier 0 (not selected) | 4,137,643 | 92.4% |

### Key findings

**`has_dot_dash` at 1.2% vs. expected ~28%.** The area separator `. - ` (with spaces on both sides) matches only 53k records. The prior `check_isbd_titles.py` analysis counted 28% as having *any* ISBD marker, not specifically the `. - ` area separator. Most DDB records are catalogued with title-area punctuation (` :`, ` /`) but without full area separation — the `. - ` separator is rare in this dataset. This means structural-tier detection is far more limited than assumed; the heuristic tier carries nearly all the load.

**`f_year` at 14.6% vs. expected 20–30%.** The year regex `\b(?:1[4-9]\d{2}|20[012]\d)\b` covers 1400–2029. Lower coverage than expected likely reflects that many DDB records store the date in `dc:date` / `dates` column rather than the title string.

**Tier 2 at 0.1% (4,613 records).** Directly consequent on `has_dot_dash` being 1.2% — tier 2 requires the area separator. Still a usable silver set for fine-tuning; 4,600 structurally annotated records is within normal range for bibliographic NER.

| # | obj_id | Title (truncated) | Detected fields |
|---|---|---|---|
| 1 | [KPVZSSDOTJWL7PGKA5YX6OOW57MQ4PYR](https://ddb.de/item/KPVZSSDOTJWL7PGKA5YX6OOW57MQ4PYR) | Naturgeschichte und Abbildungen der Säugethiere : Nach den neuesten Systemen … / vo… | PERSON, OTHER_TITLE, YEAR, PLACE, PUBLISHER, EDITION |
| 2 | [I57Y5U5NVXENFX57QU66VNLMZCL3VDXD](https://ddb.de/item/I57Y5U5NVXENFX57QU66VNLMZCL3VDXD) | Pieske, Christa, Bilder für jedermann : Wandbilddrucke 1840–1940 ; [Museum für Dt. Volkskunde…] | PERSON, OTHER_TITLE, PLACE, PUBLISHER, VOLUME |
| 3 | [VQOVBGV47PA25EXTCPCNQ25V736DXDUM](https://ddb.de/item/VQOVBGV47PA25EXTCPCNQ25V736DXDUM) | Erwin : vier Gespräche über das Schöne und die Kunst / von K. W. F. Solger. - Berlin : Realschulbuchhandlung, 1815 | PERSON, OTHER_TITLE, YEAR, PLACE, PUBLISHER |

**Tier 1 at 7.5% (335k records).** The practical silver candidate pool. Heuristic false positive rate unknown — see `scripts/validate_heuristic_fields.py`.

| # | obj_id | Title (truncated) | Detected fields |
|---|---|---|---|
| 1 | [UBMFYC2EUGMB3Q5FK65JZMRFMVJXA3E4](https://ddb.de/item/UBMFYC2EUGMB3Q5FK65JZMRFMVJXA3E4) | Die höchstnöthige Sterbe-Schule : Bey Christlicher Beerdigung Der … Fr. Marien Elisabeth von Schönberg… | OTHER_TITLE, YEAR |
| 2 | [PBKMFCEQ2CM622H4SXHBIA5KYYJUQO6U](https://ddb.de/item/PBKMFCEQ2CM622H4SXHBIA5KYYJUQO6U) | Assaphs Und einer jglichen gleubigen Seele Fewrige Liebe gegen Gott … : Bey … Leichbegängnüß … 16. May Anno 1647 | OTHER_TITLE, YEAR |
| 3 | [K74VAL7PLJW2K7J5HPJURCYGPUBK6BUV](https://ddb.de/item/K74VAL7PLJW2K7J5HPJURCYGPUBK6BUV) | Warhafftiger Abtruck gleichlautender Copey Kaysers Rudolffi des Anderen Käys. Mandati … | OTHER_TITLE, YEAR |

**Tier 0 at 92.4% (4.1M records).** No or insufficient ISBD signals — not selected as silver candidates.

| # | obj_id | Title | Detected fields |
|---|---|---|---|
| 1 | [5CPBHIPP5PFCDYGZWNJA2OLCZBXDZDXZ](https://ddb.de/item/5CPBHIPP5PFCDYGZWNJA2OLCZBXDZDXZ) | Sitzung 24, 2. Juli 1931 | YEAR only |
| 2 | [A5XNH66CR2PGPDT6D4MBWZV2LKARBZX5](https://ddb.de/item/A5XNH66CR2PGPDT6D4MBWZV2LKARBZX5) | Abbildung und Beschreibung allerhand Menschen | none |
| 3 | [SPWM52CIKUEGY2OVBAUNBXIBWGGGV7OX](https://ddb.de/item/SPWM52CIKUEGY2OVBAUNBXIBWGGGV7OX) | Elegia De Obsidione Magdeburgensi, Klag-Reimen/ Von Beläg- und Eroberung der weitberühmbten Uhralten Stadt Magdeburg | none |

---

## Limitations

- **PLACE** is only detected in the structural tier. Most non-ISBD records will have `f_place = 0` even if place information exists elsewhere (e.g., `dc_publisher` contains "Dresden : Riedel").
- **PUBLISHER** heuristic recall is low — "Verlag" keyword misses many publishers. The `dc_publisher` column could supplement detection but is kept out of scope for field ratings (title-string-only).

### Silver dataset improvement: auxiliary-guided span lookup

`rate_isbd_fields.py` intentionally rates only the `title` column (ADR-03). However, for **silver span extraction only**, PLACE and PUBLISHER coverage can be improved by a post-step that uses auxiliary columns as a lookup to find matching text *inside* the title string:

- Take `dc_publisher` (e.g., `"Leipzig : Insel-Verlag"`) and search for it as a substring in `title`
- If found, the span boundaries come from the title string — inference-consistent
- Same for person names from `dc_creator` / `dc_contributor` vs. `PERSON` spans, and series strings from `agents`

This approach differs from blind auxiliary-column labeling (ruled out in ADR-03) because the label is only applied when the value actually appears in the title. It is a downstream enrichment step for the silver dataset, not a change to field ratings.

**Script:** `scripts/build_silver_spans.py` — described in Phase 0a of the roadmap. Inputs: `isbd_field_ratings.csv` + `DF_DE_TITLES` (with auxiliary columns). Output: `data/processed/silver_spans.jsonl` with span-level NER labels per silver-tier record.
- **` ;` ambiguity** — ` ;` in the title area signals a subsequent statement of responsibility (compound SoR); in a series area it separates title from volume number. Mitigated by two complementary patterns: (1) SERIES requires `\([^)]+;\s*[^)]*\d[^)]*\)` — the ` ;` must be inside parentheses with a digit, so a bare ` ;` in the title area will never fire it; (2) `f_person_compound` detects compound SoR via ` /[^(]+;` — ` /` followed by content then ` ;` outside parentheses, distinguishing `Titel / Autor A ; Autor B` (SoR) from `(Series ; Bd. 3)` (series).
- **Multi-volume records** — some records have multiple `. -` separators for volume entries; the script takes only the first split, potentially missing volume-level fields in entries 3+.
- **False positives in heuristic tier** — ` :` fires on non-ISBD colons (URLs, ratios); ` /` fires on fractions or paths. Silver tier 1 should be validated on a ~200-record sample before use.

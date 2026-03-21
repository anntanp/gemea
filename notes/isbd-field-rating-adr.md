# GeMeA — Architecture Decision Record: ISBD Field Rating and Silver Dataset

**Format:** MADR (Markdown Architecture Decision Record)
**Subject:** Design decisions for `scripts/rate_isbd_fields.py` and NER silver dataset strategy
**Source:** `notes/isbd-field-rating.md`, `notes/ner-bibliographic.md`
**Status:** Accepted

---

## ADR-01 — Rate field presence as binary flags rather than implementing a full ISBD parser

**Status:** Accepted
**Date:** 2026-03-21

### Context

`link_gnd_works.py` requires an NER fallback for ~72% of DDB title strings that lack clean ISBD punctuation. Training or evaluating an NER model requires knowing which bibliographic fields (TITLE, PERSON, PUBLISHER, etc.) are present and labelable in each record. Two approaches were considered:

1. **Full ISBD parser** — extract actual span boundaries for every field in every record; produce labeled span output directly
2. **Field presence rating** — detect which fields are likely present as binary flags; defer span extraction to `link_gnd_works.py`

A full ISBD parser would need to handle all 8 ISBD areas, AACR2 vs. RDA punctuation variants, abbreviation noise (trailing period), multi-volume records, and edge cases across five centuries of German and Latin bibliographic records (pre-1900 cataloging conventions differ significantly from modern ISBD).

### Decision

Implement field presence rating (binary flags) rather than a full parser. The rating script detects structural signals to answer "is this field present?" without extracting spans. Span extraction remains the responsibility of `link_gnd_works.py`.

### Consequences

**Positive:**
- Fast and simple — fully vectorised pandas operations; runs on 4.47M records in seconds
- Clean separation of concerns: detection (this script) vs. extraction (`link_gnd_works.py`)
- Output is directly usable for silver tier assignment, gold set stratification, and corpus statistics
- Easier to validate: binary flags on a 200-record sample are quicker to audit than span boundaries

**Negative:**
- Does not produce training labels directly; still requires a separate span extraction step
- Binary flags do not distinguish multiple instances (e.g., two ` /` segments in a compound SoR)

**Mitigations:**
- Silver tier 2 criterion (`has_dot_dash AND f_person AND ≥1 manifestation field`) ensures only structurally clean records reach the primary training set, where span extraction is reliable
- Multi-instance cases are rare enough that they do not significantly affect training data quality at the selected tier

---

## ADR-02 — Two-tier detection: structural (`. -`) and heuristic (whole-string)

**Status:** Accepted
**Date:** 2026-03-21

### Context

ISBD area structure is only present in ~28% of DF_DE_TITLES records. For the remaining ~72%, no area separator exists and field boundaries are ambiguous. Two options for handling these records:

1. **Structural-only** — only detect fields in records with `. -`; leave 72% unrated
2. **Two-tier** — apply structural parsing where `. -` is present; fall back to whole-string heuristics for the rest

### Decision

Use two-tier detection. For records without `. -`, apply whole-string regex patterns with reduced confidence. PLACE and PUBLISHER are only detected in the structural tier. The `silver_tier` column encodes tier quality: tier 2 requires structural evidence; tier 1 accepts heuristic evidence.

### Consequences

**Positive:**
- Heuristic tier covers 72% of the corpus; even low-precision field flags are useful for gold set stratification and corpus statistics
- `silver_tier` field makes confidence explicit — downstream users know which records have structural vs. heuristic support

**Negative:**
- Heuristic ` :` fires on non-ISBD colons; ` /` fires on fractions or file paths; false positive rate unknown

**Mitigations:**
- Tier 1 silver candidates require manual validation on ~200-record sample before use in NER training
- PLACE intentionally excluded from heuristic tier to avoid noisy positives

---

## ADR-03 — Title-string-only rating; exclude auxiliary columns (dc_publisher, dc_creator)

**Status:** Accepted
**Date:** 2026-03-21

### Context

DF_DE_TITLES contains `dc_publisher`, `dc_creator`, and `dc_contributor` columns that could supplement field detection. For example, `dc_publisher` often contains "Dresden : Riedel" — a clean imprint string that would enable reliable PLACE and PUBLISHER detection even without `. -` in the title. Three options:

1. **Title-only** — rate only the `title` column
2. **Title + auxiliaries** — use `dc_publisher`, `dc_creator` to fill gaps
3. **Auxiliary-first** — prefer auxiliary columns; fall back to title parsing

### Decision

Rate only the `title` column. The goal of this script is to assess what is detectable from the string that `link_gnd_works.py` actually receives at inference time — which is the title string, not the full record. Training the NER model on auxiliary-column labels would create a mismatch between training signal and inference context.

### Consequences

**Positive:**
- Ratings faithfully reflect what the NER model will see at inference time
- Avoids mixing detection sources that have different reliability profiles

**Negative:**
- PUBLISHER and PLACE recall is low for heuristic-tier records; `dc_publisher` could provide high-quality imprint labels for ~3M records without `. -`

**Mitigations:**
- A future script can join `isbd_field_ratings.csv` with `dc_publisher` for richer corpus statistics (outside the scope of NER training data)
- The paper's evaluation section should note that publisher/place coverage reflects title-string detection only

---

## ADR-04 — Silver tier 2 requires has_dot_dash + PERSON + ≥1 manifestation field

**Status:** Accepted
**Date:** 2026-03-21

### Context

Silver labels are auto-generated from ISBD structure; their quality directly determines NER model quality. The tier 2 criterion was chosen to balance three concerns:

1. **Annotation completeness** — at least two distinct field types must be labelable (TITLE always present + something else)
2. **Structural reliability** — span boundaries must be unambiguous (requires `. -`)
3. **Training signal diversity** — silver set must include both Work-level (TITLE, PERSON) and Manifestation-level (PUBLISHER, PLACE, YEAR) labels

Alternative tier 2 criteria considered:
- `has_dot_dash AND n_fields ≥ 3` — too broad; includes records where only ` :` + YEAR are detected (no PERSON)
- `has_dot_dash AND f_person AND f_year` — misses records with PUBLISHER/PLACE but no explicit year in title string

### Decision

Require `has_dot_dash AND f_person AND any(f_edition, f_place, f_publisher, f_year, f_series)`. This guarantees:
- Work-level signal (PERSON from ` /`)
- At least one Manifestation-level signal
- Structural area separation (unambiguous span boundaries)

### Consequences

**Positive:**
- Tier 2 records are the richest for multi-field NER training — TITLE, PERSON, and ≥1 Manifestation label per record
- `has_dot_dash` requirement filters out most heuristic false positives

**Negative:**
- Tier 2 will cover only a small fraction of the corpus (~1–5% estimated); most ISBD-structured records lack ` /`
- PERSON (` /`) appears in only 0.8% of DF_DE_TITLES; tier 2 will be a small but high-quality set

**Mitigations:**
- Tier 1 (`n_fields ≥ 3` or `f_person AND f_year`) supplements tier 2 for augmentation
- The small size of tier 2 is expected and acceptable — 5–50K structurally clean records is sufficient for fine-tuning if needed

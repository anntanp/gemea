# GeMeA — ISBD Rule Applicability in DF_DE_TITLES

Summary of which ISBD punctuation rules work reliably in the DDB corpus, which fail, and which require era- or type-specific heuristics. Synthesises findings from SR-01–SR-04 and the field rating run on 4,477,780 records.

**Sources:** [isbd-field-rating.md](isbd-field-rating.md), [isbd-title-analysis.md](isbd-title-analysis.md), [silver-label-fp-review.md](silver-label-fp-review.md), [translator-person-disambiguation.md](translator-person-disambiguation.md), [ner-bibliographic.md](ner-bibliographic.md)

---

## 1. ISBD area structure in DDB

A fully conformant ISBD record uses `. -` (trailing period + space-dash-space) to separate areas:

```
Title proper : other title information / statement of responsibility
  . - Edition statement
  . - Place : Publisher, Year
  . - (Series ; volume)
```

**In practice, DDB records rarely follow this fully.** Only **1.2%** (53,785 records) contain the `. -` area separator. Most records are catalogued with title-area punctuation only (` :`, ` /`) — the structural tier is almost absent.

---

## 2. Rule-by-rule applicability

### ✅ Reliable rules

| Rule | Signal | Coverage | FP rate | Notes |
|---|---|---|---|---|
| `. -` area separator | Structural tier boundary | 1.2% | Very low | When present, field parsing is high-precision; rare in corpus |
| ` :` OTHER_TITLE | Subtitle boundary | 20.2% | ~8% | Main false positives: `:YYYY–YYYY` life-date colon, ` :: ` DDB catalog separator |
| `f_year` publication year | 4-digit year regex | 14.6% | ~6% | False positives: founding years (`gegr.`), life dates, manuscript date ranges, composition dates |
| `f_publisher` | `Verlag`/`Press` keyword | 0.2% | ~0% | Low recall — misses most publishers; high precision when it fires |
| `f_series` | Parenthetical + ` ;` + digit | 0.0% | ~0% | Very sparse; reliable when present |
| `f_volume` | `Bd.`, `Teil`, `Heft`, `Nr.` + digit | 1.9% | ~0% | Reliable |

### ❌ Unreliable rules — excluded from silver labels

| Rule | Signal | Coverage | FP rate | Why it fails in DDB |
|---|---|---|---|---|
| ` =` PARALLEL_TITLE | Parallel title | 0.6% | ~80% | DDB serials use `=` for enumeration equivalences (`= Jg. X`, `= Bd.`, `= N.F.`, `= Quartal`) — not parallel titles in another language |
| `Ausgabe` EDITION | Edition keyword | 3.6% | ~83% | Newspaper issues use "Ausgabe vom [date]" for daily issue labels, not edition statements |

### ⚠️ Rules requiring post-filtering

| Rule | Signal | Coverage | FP rate | Required post-filter |
|---|---|---|---|---|
| ` /` PERSON (SoR) | Statement of responsibility | 0.8% | ~36% | Exclude: single-letter series suffixes (`/ K`, `/ M`), corporate body SoRs, date separators (`/ 1701.`), double-slash manuscript transcriptions (`//`) |
| ` /…;` PERSON_COMPOUND | Compound SoR | 0.0% | ~29% | Exclude: corporate bodies followed by topic subtitles; volume numbers after `;` |

### ➖ Not detectable from title string alone

| Field | Reason |
|---|---|
| `PLACE` | Only detectable in structural tier (after `. -`); 0.1% coverage |
| `TRANSLATOR` | Zero hits in 100-record sample of ` /`-flagged records; translators absent from title string or in separate metadata fields |
| `EDITOR` | `(Hg.)` suffix and body-text `bearb.` not captured by SoR-text keyword match |

---

## 3. Era-dependent heuristics

### Pre-1750: early modern titles

| Feature | Observation | Heuristic implication |
|---|---|---|
| **Long-form title pages** | 42–50% of tokens >14; median 12–15 tokens. Full bibliographic description (subtitle, author, place, printer) folded into title string. | All ISBD fields may be present but without ISBD punctuation — rule-based extraction unreliable; NER is the primary path |
| **Author before title** | Author name + credentials appear at the start of the string, before the work title. No ` /` present. | `f_person = 0` even when an author is named. Detection requires a name-before-title NER pattern, not SoR heuristic. See [silver-label-fp-review.md §5](silver-label-fp-review.md#5-pre-1750-false-negatives--author-before-title) |
| **Latin titles** | Unknown proportion; Leichenpredigten and pre-Reformation works frequently Latin or Early Modern German. | Tokenisation and stopword removal behave differently; `de_core_news_sm` is not optimised for Latin |
| **YEAR false positives** | Manuscript dates, death dates, composition dates common in long ISBD strings from this era | Filter years appearing after `gegr.`, `biß`, `bereit … geschrieben`, or in `Anno YYYY biß YYYY` patterns |

### 19th–early 20th century: serials and newspapers (dc_type = issue|Heft|Zeitung)

| Feature | Observation | Heuristic implication |
|---|---|---|
| **`Ausgabe vom [date]`** | Ordinal + "Ausgabe" + weekday/date is a newspaper issue label | Exclude `f_edition` for `dc_type` containing `issue`, `Heft`, or `Zeitung` |
| **`= Jg.`, `= Bd.`, `= N.F.`** | `=` introduces enumeration equivalences in serial records, not parallel titles | Exclude `f_parallel` for serial dc_types; re-apply only when `=` is followed by a non-German string |
| **Corporate SoRs** | Statistical offices, government agencies named after ` /` (~19% of `f_person` pool in sample) | Post-filter: if the SoR text matches a known institutional keyword (`Landesamt`, `Bundesamt`, `Ministerium`, `Gesellschaft`, `Institut`) → label as CORPORATE, not PERSON |

### Post-2000: digital-born metadata

| Feature | Observation | Heuristic implication |
|---|---|---|
| **Short titles, separate subtitle fields** | Only 9% short (≤4 tokens), 62% medium; digital metadata stores subtitle in separate fields — the `title` column may contain only the main title | ` :` recall drops; OTHER_TITLE may not appear in title string even when a subtitle exists |
| **Richer structured descriptions** | Median token count reverses upward (11 tokens) — structured descriptions reappear but in modern format | ISBD `. -` still rare; heuristic rules apply as before |

---

## 4. Field-level summary by dc_type

| dc_type | Reliable fields | Unreliable / excluded | Special note |
|---|---|---|---|
| Monografie (pre-1750) | `f_other_title`, `f_year` (with date filter) | `f_person` (false negative), `f_parallel`, `f_edition` | Author-before-title pattern; long-form ISBD strings |
| Monografie (post-1800) | All accepted fields | `f_parallel`, `f_edition` | Standard rules apply |
| issue / Heft / Zeitung | `f_other_title`, `f_year`, `f_volume` | `f_parallel`, `f_edition`, `f_person` (corporate) | Exclude edition + parallel entirely |
| Leichenpredigt | `f_other_title`, `f_year` (with filter) | `f_person` (false negative) | Name of deceased and husband's credentials embedded mid-title; no SoR marker |
| Statistische Berichte | `f_other_title`, `f_year`, `f_volume` | `f_person` (corporate SoR) | Post-filter `f_person` for institutional keywords |

---

## 5. Implications for silver label selection

When building the NER silver training set from tier-1 records:

1. **Always apply** post-filter on `f_person`: exclude corporate-body SoRs and series-letter suffixes
2. **Always exclude** `f_parallel` and `f_edition` from silver labels without `dc_type`-conditional logic
3. **Filter `f_year` false positives** using date-context patterns (founding years, life dates, manuscript dates)
4. **Apply dc_type guards** before including `f_person` (newspapers) and `f_edition` (non-newspapers)
5. **Pre-1750 stratum**: annotate author spans from name-before-title pattern separately; do not rely on `f_person`
6. **Tier 2 (4,613 records)** remains the highest-confidence silver set — all rules apply with structural precision

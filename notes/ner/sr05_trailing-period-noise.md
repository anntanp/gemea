# GeMeA — Trailing Period Noise (SR-05)

**SR-05** in [ner-bibliographic.md](../ner-bibliographic.md).

---

## 1. Question

Trailing `.` fires in 19.5% of the corpus (875,349 records). Can it be used as a heuristic signal for ISBD area structure (area-close marker), or is the false-positive rate too high?

---

## 2. Method

`scripts/sr05_validate_trailing_period.py` drew a 200-record stratified sample from all titles ending with `.`. `scripts/sr05_trailing_period_review.py` classified each record into:

| Class | Meaning |
|---|---|
| `ISBD_CLOSE` | Period is a genuine ISBD area-close marker (end of a complete bibliographic area) |
| `NATURAL` | Period ends a natural-language sentence, chapter title, or date expression |
| `NOISE` | Single-word entry, fragment, index term, page reference |
| `ORDINAL` | Period follows an ordinal number (digit or Roman numeral) |
| `ABBREV` | Period is part of a German/Latin abbreviation (`Hrsg.`, `Bd.`, etc.) |

Detection heuristics:
- `ISBD_CLOSE`: contains `. -` area separator, or ends with 4-digit year AND contains ` :` / ` /`
- `ABBREV`: last token matches a curated abbreviation list
- `ORDINAL`: last token is a non-year digit or Roman numeral
- `NOISE`: single-word regex, page range, paragraph marker
- `NATURAL`: all remaining (long prose strings and short headings)

---

## 3. Results — 200-record sample

| true_class | Count | % |
|---|---|---|
| NATURAL | 149 | 74% |
| NOISE | 20 | 10% |
| ORDINAL | 15 | 8% |
| **ISBD_CLOSE** | **14** | **7%** |
| ABBREV | 2 | 1% |

**FP rate: 93%** (186/200) — far above the 15% acceptance threshold.

### ISBD_CLOSE breakdown

| Signal | Count | Example |
|---|---|---|
| `. -` area separator | 11 | `Feste Erdharze. - Gemeine Metalle.` |
| Year + ` :` or ` /` | 3 | `Oesterreichisches Deo Gratias, Das ist: … 1739.` |

All 14 ISBD_CLOSE records are **already detected by existing signals**: the 11 structural ones are covered by `has_dot_dash`; the 3 year+marker ones are covered by `f_year` + `f_other_title`/`f_person` co-occurrence.

### FP examples

| Class | Example |
|---|---|
| NATURAL | `Eine selbstschreibende Atwoodsche Fallmaschine.` |
| NATURAL | `Nothwendige Anmerckungen über die vierzehende Handlung.` |
| NATURAL (date) | `Erste Ausgabe vom Donnerstag, den 28. Januar 1915.` |
| NATURAL (date) | `Reise von Astrachan nach Kisljar, im Januar 1770.` |
| NOISE | `Inhalt.` |
| NOISE | `Vorerinnerung.` |
| ORDINAL | `Taxe für die Teichgräber. No. 27.` |
| ABBREV | `Weise, fromm und gesund zu leben … 3.verb.Aufl.` |

---

## 4. Key findings

1. **93% FP rate** — the trailing period is dominated by natural-language sentence endings (74%) and structural noise (ordinals, abbreviations, fragments). Genuine ISBD area-closes are 7% of the pool.

2. **Zero marginal detection power** — all 14 true positives are already captured by `has_dot_dash` or by the combination of `f_year` with another ISBD marker. Trailing `.` alone carries no information beyond what existing flags already provide.

3. **Date expression contamination** — the most common false pattern is a date string ending with a year (newspaper issue dates: `Ausgabe vom [weekday], den [date] [year].`; event dates; historical correspondence). These are also flagged as FP in SR-03 (`f_edition`) and SR-03 (`f_year`). Consistent failure mode across signals.

4. **Single-word entries** — 10% are table-of-contents fragments (`Inhalt.`, `Vorerinnerung.`, `Vorrede.`) that entered `DF_DE_TITLES` as standalone items. These carry no useful bibliographic structure.

---

## 5. Decision

- **Exclude** trailing `.` from heuristic silver-tier signals entirely — 93% FP, zero marginal value
- The corpus coverage figure (19.5%) is an upper bound reflecting natural prose punctuation, not ISBD structure
- `has_dot_dash` (1.2% coverage, very low FP) remains the only reliable period-based structural signal
- No abbreviation stripping or co-occurrence guard is worth implementing; the signal is irredeemable in the heuristic tier

# GeMeA — ISBD Rule Applicability in DF_DE_TITLES

Summary of which ISBD punctuation rules work reliably in the DDB corpus, which fail, and which require era- or type-specific heuristics. Synthesises findings from SR-01–SR-04 and the field rating run on 4,477,780 records.

**Sources:** [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md), [sr01_isbd-title-analysis.md](sr01_isbd-title-analysis.md), [sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md), [sr04_translator-person-disambiguation.md](sr04_translator-person-disambiguation.md), [ner-bibliographic.md](../ner-bibliographic.md)

---

## 0. Note lineage

Three notes share the `sr01_` prefix. They are not redundant — each covers a distinct stage:

| Note | Stage | What it contains |
|---|---|---|
| [sr01_isbd-title-analysis.md](sr01_isbd-title-analysis.md) | Initial scan | Raw output of [sr01_check_isbd_titles.py](../../scripts/sr01_check_isbd_titles.py) (2026-03-17). DataFrame schema, raw per-pattern counts (` :` 20.3%, trailing `.` 17.5%, ` /` 0.8%, etc.), and a first-pass note on trailing period noise. Motivated building the full field-rating pipeline. |
| [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md) | Full rating run | Documents [sr01_rate_isbd_fields.py](../../scripts/sr01_rate_isbd_fields.py) — the detection logic, output schema (`isbd_field_ratings.csv`), silver tier definitions, and validation sample methodology. Source of the corpus-wide tier counts (tier 2: 4,613 records; tier 1: 335,524 records). |
| [sr01_isbd-applicability.md](sr01_isbd-applicability.md) *(this file)* | Synthesis | Rule-by-rule applicability decisions derived from the rating run and subsequent SR-03/SR-04 validation. Answers: which signals to use, which to exclude, and which require sub-classification or era guards. |

The "28%" figure that appears in early notes (including the original ADR-02) came from [sr01_isbd-title-analysis.md](sr01_isbd-title-analysis.md) — the proportion of records with any ISBD signal excluding trailing `.`. The corrected structural-tier figure (`. -` present in **1.2%** of records) comes from the full rating run in [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md).

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

Coverage %: share of 4,477,780 DF_DE_TITLES records where the flag fires, from `sr01_rate_isbd_fields.py` → `data/processed/isbd_field_ratings.csv`. FP rates from SR-03 200-record stratified sample ([sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md)).

| Signal | Pattern | Coverage | FP rate | Decision |
|---|---|---|---|---|
| [Area separator](#211-area-separator) | `. -` | 1.2% | very low | Accept |
| [Subtitle](#212-subtitle) | ` :` | 20.2% | ~8% | Accept |
| [Year](#213-year) | 4-digit regex | 14.6% | ~6% | Accept |
| [Publisher](#214-publisher) | `Verlag`/`Press` keyword | 0.2% | ~0% | Accept |
| [Series](#215-series) | parenthetical + ` ;` + digit | 0.0% | ~0% | Accept |
| [Volume](#216-volume) | `Bd.`/`Teil`/`Heft`/`Nr.` + digit | 1.9% | ~0% | Accept |
| [Parallel title](#221-parallel-title) | ` =` | 0.6% | ~80% | Exclude |
| [Edition](#222-edition) | `Ausgabe`/`Aufl.` keyword | 3.6% | ~83% | Exclude |
| [Statement of Responsibility](#231-statement-of-responsibility) | ` /` | 0.8% | ~36% for PERSON | Sub-classify |
| [Compound SoR](#232-compound-sor) | ` /…;` | 0.0% | ~29% | Sub-classify |
| [Not detectable](#24-not-detectable) | — | — | — | — |

---

### 2.1 Accepted rules

#### 2.1.1 Area separator

Signal: `. -` | Coverage: 1.2% | FP rate: very low

When present, field parsing is high-precision; the separator unambiguously marks area boundaries. Rare in corpus — the structural tier covers only 53k records.

| Title | URL |
|---|---|
| `Kriegstagebuch der Seekriegsleitung 1939 - 1945. - Teil A ; Band 65. Januar 1945` | [↗](https://ddb.de/item/UR75EQHR72BNWYVZG3XKMUHOAKSLJ2XO) |
| `Ohne Grenzen :XXXII. Deutscher Kunsthistorikertag … - 24. März 2013; Tagungsband` | [↗](https://ddb.de/item/JD76UJ72HGLPBD57MJL4X5TDNTT6VQIL) |

---

#### 2.1.2 Subtitle

Signal: ` :` (OTHER_TITLE) | Coverage: 20.2% | FP rate: ~8%

Main false positives: `:YYYY–YYYY` life-date colon; ` :: ` DDB catalog-field separator.

**True positives:**

| Title | URL |
|---|---|
| `Der Weltverkehr und seine Mittel :Rundschau über Schiffahrt und Welthandel …` | [↗](https://ddb.de/item/5LOLZLJ77E2OZ3FXXWICQGVZJEXFQ542) |
| `Modulhandbuch Bachelor Angewandte Medien- und Kommunikationswissenschaft :Studienordnungsversion: 2012` | [↗](https://ddb.de/item/MBL5TP4QQTJE42U3LVAACUXAIUSMKTFI) |

**False positives:**

| Title | URL | Reason |
|---|---|---|
| `Johann Ludwig Böhner :7. Januar 1787 - 28. März 1860 ; [Katalog]` | [↗](https://ddb.de/item/THF6HTNRUTSYTYBY377JLKXHCWVHNYQP) | `:` precedes life dates, not subtitle |
| `Feldmarschall … Khevenhüller-Frankenburg … :1683-1744 ; eine Lebensskizze` | [↗](https://ddb.de/item/SKUC2ZDHLCDGXDWQ2NMGSDXZ5U6GLRPC) | `:` precedes life-date range |

---

#### 2.1.3 Year

Signal: `f_year` (4-digit regex 1400–2029) | Coverage: 14.6% | FP rate: ~6%

**True positives:**

| Title | URL |
|---|---|
| `Allgemeine Deutsche Krankenkasse … : IV. Quartal 1922` | [↗](https://ddb.de/item/JBIOMGMUG5PXUG7RIS44KJYCY553B34U) |
| `Programm des Evangelischen Gymnasiums … 1876/77` | [↗](https://ddb.de/item/PRFIMYOD64K5YG73YHJWSV6N7CRAOYCC) |

**False positives:**

| Title | URL | Reason |
|---|---|---|
| `Jeversches Wochenblatt : Friesisches Tageblatt ; gegr. 1791` | [↗](https://ddb.de/item/AGZJAK7XYRNH3IWXEWFVELM4OFBJARLL) | Founding year (`gegr.`) |
| `Porträt Georg Philipp Wucherer (1734 - 1805) :Kupferstich ; Radierung` | [↗](https://ddb.de/item/7EG6MNM55XRFKT63ZIUZN35OZAZMMY2B) | Life dates in parentheses |

---

#### 2.1.4 Publisher

Signal: `f_publisher` (`Verlag`/`Press` keyword) | Coverage: 0.2% | FP rate: ~0%

Low recall — misses most publishers; high precision when fires.

| Title | URL |
|---|---|
| `Jugendschriften : aus dem Verlag von Q. Spamer in Leipzig` | [↗](https://ddb.de/item/2RIK6UPHKWTOU65R3S5GOUR5GYQULL4I) |
| `Information des Bereiches FDJ-Presse im Verlag Junge Welt: 19/66 vom 20. Mai 1966 ; [Mitteilungen]` | [↗](https://ddb.de/item/QFX2RP37W4IUCIGM3VE3FAUSYERTN5OY) |

---

#### 2.1.5 Series

Signal: `f_series` (parenthetical + ` ;` + digit) | Coverage: 0.0% | FP rate: ~0%

Very sparse; reliable when present.

---

#### 2.1.6 Volume

Signal: `f_volume` (`Bd.`, `Teil`, `Heft`, `Nr.` + digit) | Coverage: 1.9% | FP rate: ~0%

| Title | URL |
|---|---|
| `Ärztliches Vereinsblatt für Deutschland. Jg. 22, Nr. 269` | [↗](https://ddb.de/item/EFXCKGZWS446BTD22OVYS4FNACIZR2RR) |
| `Das Echo. Jg. 17, Nr. 819` | [↗](https://ddb.de/item/O6J6EQJNBQ7DW2RGCJQNBGLFYZ5DNNRZ) |

---

### 2.2 Excluded rules

#### 2.2.1 Parallel title

Signal: ` =` (PARALLEL_TITLE) | Coverage: 0.6% | FP rate: ~80%

A **parallel title** (ISBD Area 1, `f_parallel`) is the title of the work restated in a second language or script on the same title page — e.g., a bilingual German/English monograph. It is introduced by ` =` and is distinct from `OTHER_TITLE` (` :`, a subtitle or alternative title in the *same* language). In a fully conformant ISBD record: `Titel : Untertitel = Title : Subtitle`.

In the DDB corpus, ` =` is almost never used for genuine parallel titles. Serial records systematically repurpose `=` for enumeration equivalences (`= Jg. X`, `= Bd.`, `= N.F.`, `= Quartal`), making the signal unreliable.

| Title | URL | Reason |
|---|---|---|
| `Allgemeine Zeitung. 1898, 1898 = Jg. 101, 4 - 5` | [↗](https://ddb.de/item/ZUE6UGELN66IR7NQR3QEZSGEHRPKDHD6) | `=` introduces volume enumeration |
| `Verzeichnis der Vorlesungen … 1833/34 (1833) = Winter-Halbjahr` | [↗](https://ddb.de/item/HBGATPAF5KAQZFMSNA5FUZ3OQC2ZS3KH) | `=` introduces semester designation |

---

#### 2.2.2 Edition

Signal: `f_edition` (`Ausgabe`/`Aufl.` keyword) | Coverage: 3.6% | FP rate: ~83%

Newspaper and periodical records use "Ausgabe vom [weekday, date]" as an issue-date label, not an edition statement.

| Title | URL | Reason |
|---|---|---|
| `Erste Ausgabe vom Dienstag, den 18. Mai 1937.` | [↗](https://ddb.de/item/YASRD5RWR6SXOLRMJ24A66FL4EWJ5ZNP) | Newspaper print-run label |
| `Dritte Ausgabe vom Samstag, den 21. Dezember 1895.` | [↗](https://ddb.de/item/G474LKFU2M4HUG6SNJJFK2CPUNEBQIOC) | Same pattern — ordinal + issue date |

---

### 2.3 Rules requiring sub-classification

#### 2.3.1 Statement of Responsibility

Signal: ` /` | Coverage: 0.8% | FP rate: ~36% for PERSON label

` /` detects the presence of a responsible entity but does not distinguish entity type. From SR-04 (100-record sample), the ` /` pool maps onto the ISBD/RDA/MARC agent model — **person** | **collective agents** (corporate body, family) | **role qualifier** | **non-SoR**:

| Category | Entity type | `f_resp_*` flag | % of ` /` pool | Example |
|---|---|---|---|---|
| Person | Individual person | `f_resp_person` | 35% | `… / von M. Rosenstock` [↗](https://ddb.de/item/ZGN4C7ZJ7NBZV65ZSIZHC5N2SM3VGIOB) |
| Collective agent | Corporate body | `f_resp_org` | 19% | `… / Privates Katholisches Lyzeum Magdeburg` [↗](https://ddb.de/item/OROZ7FMM4X4XDYVYBJSJP33NZKIFPUD5) |
| Collective agent | Family name | `f_resp_family` | — | Not yet validated |
| Role qualifier | Editor / adaptor | `f_resp_editor` | 5% | `… / hrsg. von Abraham Geiger` [↗](https://ddb.de/item/HGCH7UKPABAHS46CGTA6D4V5CQOELPOY) |
| Non-SoR | False positive | `f_resp_other` | 41% | `Ah fuggi il traditor / O flieh den Bösewicht` [↗](https://ddb.de/item/6GPNJKG4RDEVFEDHMGU5F7OKLWG2N2GT) |
| — | Translator | `f_resp_translator` | 0% | Not detectable from title strings in this corpus |

Corporate body SoRs are a **recognised entity class** (19% of the ` /` pool), not noise — they map to the MARC 21 corporate name entry (1xx/7xx ind1=2) and may warrant a `CORPORATE` NER label in future. They should be sub-classified with `f_resp_org`, not silently discarded.

Additional corporate body example:
`Jahresbericht … / Hochschule für Angewandte Wissenschaften Würzburg-Schweinfurt` [↗](https://ddb.de/item/NC2UQJ4O4RF76SG3G2DPJ4DNEC6KTOSM)

---

#### 2.3.2 Compound SoR

Signal: ` /…;` (PERSON_COMPOUND) | Coverage: 0.0% | FP rate: ~29%

| Title | URL | Reason |
|---|---|---|
| `Jahrbuch / Deutsche Shakespeare-Gesellschaft; 3` | [↗](https://ddb.de/item/BDMEHSHZCBPUG6NL3OKG4FMKKGL4VHMH) | `; 3` is a volume number |
| `Statistische Berichte / Hessisches Statistisches Landesamt … ; Ergebnisse nach Verwaltungsbezirken …` | [↗](https://ddb.de/item/GKSDCS5H4ERC4ZTPNRBOBMH5ZDU6WQN2) | Corporate SoR; `;` separates topic subtitles |

---

### 2.4 Not detectable

Fields not recoverable from the title string alone:

| Field | Reason |
|---|---|
| `PLACE` | Only detectable in structural tier (after `. -`); 0.1% coverage |
| `TRANSLATOR` | Zero hits in 100-record sample; translators absent from title string or in separate metadata fields |
| `EDITOR` | `(Hg.)` suffix and body-text `bearb.` not reliably captured by SoR-text keyword match; partial detection only |

---

## 3. Era-dependent heuristics

### 3.1 Pre-1750: early modern titles

| Feature | Observation | Heuristic implication |
|---|---|---|
| **Long-form title pages** | 42–50% long (>14 tokens); median 12–15 tokens. Full bibliographic description folded into title string — the title page functioned as a table of contents | All ISBD fields may be present but without ISBD punctuation; NER is the primary path |
| **Author before title** | Author name + credentials appear at the start of the string, before the work title. No ` /` present → `f_person = 0` even when an author is named | Requires name-before-title NER pattern; do not rely on `f_resp_person`. See [sr03_silver-label-fp-review.md §5](sr03_silver-label-fp-review.md#5-pre-1750-false-negatives--author-before-title) |
| **Latin titles** | Unknown proportion; Leichenpredigten and pre-Reformation works frequently Latin or Early Modern German | `de_core_news_sm` not optimised for Latin; tokenisation and stopword removal unreliable |
| **YEAR false positives** | Manuscript dates, death dates, composition dates common | Filter years appearing after `gegr.`, `biß`, `bereit … geschrieben`, `Anno YYYY biß YYYY` |

### 3.2 19th–early 20th century: serials and newspapers (dc_type = issue|Heft|Zeitung)

| Feature | Observation | Heuristic implication |
|---|---|---|
| **`Ausgabe vom [date]`** | Ordinal + "Ausgabe" + weekday/date is a newspaper issue label, not edition statement | Exclude `f_edition` entirely for serial dc_types |
| **`= Jg.`, `= Bd.`, `= N.F.`** | `=` introduces enumeration equivalences, not parallel titles | Exclude `f_parallel` for serial dc_types |
| **Corporate body SoRs** | Government agencies, statistical offices, universities named after ` /` (~19% of ` /` pool) | Sub-classify as `f_resp_org`; treat as CORPORATE entity, not PERSON |

### 3.3 Post-2000: digital-born metadata

| Feature | Observation | Heuristic implication |
|---|---|---|
| **Short titles, separate subtitle fields** | Only 9% short; digital metadata stores subtitle separately — `title` may contain only the main title | ` :` recall drops; OTHER_TITLE may not appear in title string even when a subtitle exists |
| **Richer structured descriptions** | Median 11 tokens — structured descriptions reappear but in modern format | ISBD `. -` still rare; heuristic rules apply as before |

---

## 4. Field-level summary by dc_type

| dc_type | Reliable fields | Excluded | Special note |
|---|---|---|---|
| Monografie (pre-1750) | `f_other_title`, `f_year` (date filter) | `f_parallel`, `f_edition` | `f_person` is false negative (author before title); long-form strings |
| Monografie (post-1800) | All accepted fields | `f_parallel`, `f_edition` | Standard rules apply |
| issue / Heft / Zeitung | `f_other_title`, `f_year`, `f_volume` | `f_parallel`, `f_edition` | `f_person` present but sub-classify: mostly `f_resp_org` |
| Leichenpredigt | `f_other_title`, `f_year` (date filter) | `f_parallel`, `f_edition` | `f_person` is false negative; deceased + husband credentials embedded mid-title |
| Statistische Berichte | `f_other_title`, `f_year`, `f_volume` | `f_parallel`, `f_edition` | `f_person` present → sub-classify as `f_resp_org` |

---

## 5. Implications for silver label selection

1. **Sub-classify `f_person`** into `f_resp_person`, `f_resp_org`, `f_resp_editor`, `f_resp_other` before assigning NER labels — do not treat ` /` as synonymous with individual authorship
2. **Treat `f_resp_org` as a distinct entity class** (CORPORATE), not a false positive — 19% of ` /` records; maps to MARC corporate name entry
3. **Always exclude** `f_parallel` and `f_edition` from heuristic silver labels
4. **Filter `f_year` false positives** using date-context patterns (founding years, life dates, manuscript dates)
5. **Apply dc_type guards**: exclude `f_edition` and `f_parallel` for serial types; sub-classify `f_person` for institutional dc_types
6. **Pre-1750 stratum**: annotate author spans from name-before-title pattern separately; do not rely on `f_resp_person`
7. **Tier 2 (4,613 records)** remains the highest-confidence silver set — structural tier with unambiguous span boundaries

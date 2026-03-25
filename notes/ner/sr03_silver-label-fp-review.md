# GeMeA — Silver Label False-Positive Review (SR-03)

**SR-03** in [ner-bibliographic.md](../ner-bibliographic.md). See also [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md).

---

## 1. Background

`sr01_rate_isbd_fields.py` assigns silver labels to titles by detecting ISBD punctuation patterns at two tiers:

- **Tier 2 (structural):** `. -` area separator present — strong structural signal, expected high precision
- **Tier 1 (heuristic):** no `. -`, but other markers fire (` :`, ` /`, 4-digit year, edition keyword, etc.) — weaker signal, false positive rate unknown

Heuristic patterns over-fire on non-ISBD content:
- ` :` fires on any colon, not just ISBD subtitle separators
- ` /` fires on fractions, series letter suffixes, and region names as well as Statement of Responsibility (SoR)
- A 4-digit number fires on founding years, life dates, and manuscript dates — not only publication years

---

## 2. Review method

`scripts/sr03_validate_heuristic_fields.py` produced a 200-record stratified sample at `data/processed/heuristic_validation_sample.csv`, with one stratum per heuristic field flag. `scripts/sr03_fp_review.py` applied automated regex rules + per-row overrides to classify each active flag as TP or FP, writing results to the `fp_fields` and `notes` columns.

---

## 3. Results

**81 of 200 records (40.5%) have at least one false positive.**

| Field | FP count | FP rate | Decision | Primary false-positive pattern |
|---|---|---|---|---|
| `f_parallel` | 20 | ~80% | ❌ Exclude | ` =` fires on serial enumeration (`= Jg. X`, `= Bd.`, `= N.F.`, `= Quartal`) and volume-part labels — not parallel titles |
| `f_edition` | 30 | ~83% | ❌ Exclude | "Ausgabe vom [date]" in newspaper titles is a daily-issue label, not an edition statement |
| `f_person` | 17 | ~36% | ⚠️ Post-filter | ` /` fires on single-letter series suffixes (`/ K`, `/ M`), region names, supplement labels (`/ Beiblatt`), date separators |
| `f_person_compound` | 7 | ~29% | ⚠️ Post-filter | Corporate body SoRs where `;` separates topic subtitles not persons; volume numbers after `;` |
| `f_year` | 9 | ~6% | ✅ Accept | Founding years (gegr.), life dates, manuscript date ranges, composition dates — low FP rate |
| `f_other_title` | 8 | ~8% | ✅ Accept | ` :: ` catalog-field separators (DDB Abschnitt records); `:YYYY–YYYY` life-date colons — low FP rate |
| `f_publisher` | — | — | ✅ Accept | No FPs detected in sample |
| `f_series` | — | — | ✅ Accept | No FPs detected in sample |
| `f_volume` | — | — | ✅ Accept | No FPs detected in sample |

---

## 4. Examples

### f_parallel — serial enumeration, not parallel title

| Title | URL | Notes |
|---|---|---|
| `Verzeichnis der Vorlesungen ... 1833/34 (1833) = Winter-Halbjahr` | [↗](https://ddb.de/item/HBGATPAF5KAQZFMSNA5FUZ3OQC2ZS3KH) | `=` introduces a season designator, not a parallel title |
| `Allgemeine Zeitung. 1898, 1898 = Jg. 101, 4 - 5` | [↗](https://ddb.de/item/ZUE6UGELN66IR7NQR3QEZSGEHRPKDHD6) | `=` introduces volume enumeration (`Jg.`), not a parallel title |
| `Königlich Bayerisches Intelligenzblatt für den Rezat-Kreis. 1824,2, 1824,[2] = Juli - Dez.` | [↗](https://ddb.de/item/JUOJ3V3BX24ZIQYYLTONL2IBLCASGHFA) | `=` introduces a date-range designator, not a parallel title |

### f_edition — newspaper issue date labels

| Title | URL | Notes |
|---|---|---|
| `Erste Ausgabe vom Dienstag, den 18. Mai 1937.` | [↗](https://ddb.de/item/YASRD5RWR6SXOLRMJ24A66FL4EWJ5ZNP) | "Ausgabe vom …" is a newspaper issue label, not an edition statement |
| `Erste Ausgabe vom Freitag, den 01. Februar 1929.` | [↗](https://ddb.de/item/QWHLSHE3RY3BLLA6M44R6ZIB34OA3SWL) | Same pattern — daily issue date |
| `Dritte Ausgabe vom Samstag, den 21. Dezember 1895.` | [↗](https://ddb.de/item/G474LKFU2M4HUG6SNJJFK2CPUNEBQIOC) | Same pattern — ordinal + date |

### f_person — ` /` firing on non-SoR contexts

| Title | URL | Notes |
|---|---|---|
| `1988: Statistische Berichte der Freien und Hansestadt Hamburg / K` | [↗](https://ddb.de/item/5VJBG7E7EIOY5VARC2MWNZTKHRKYPPYR) | `/ K` is a series letter suffix |
| `12. Wochen / 1701.` | [↗](https://ddb.de/item/VMYTGXKFHVZZ2JN4U4FDFKUWLOHKXQHE) | `/ 1701.` is a date/enumeration separator |
| `Matthatia - BSB Mus.ms. 2761 :[…] Matth. Fischer // Matthatia // 1.2.` | [↗](https://ddb.de/item/TESMJCHDS7J3G74XAGVKMC7JBBD6F4PV) | `//` separates lines of a title-page transcription |

### f_person_compound — corporate body or volume number after `;`

| Title | URL | Notes |
|---|---|---|
| `Jahrbuch / Deutsche Shakespeare-Gesellschaft; 3` | [↗](https://ddb.de/item/BDMEHSHZCBPUG6NL3OKG4FMKKGL4VHMH) | `; 3` is a volume number, not a second person |
| `Statistische Berichte / Hessisches Statistisches Landesamt. B … ; Ergebnisse nach Verwaltungsbezirken …` | [↗](https://ddb.de/item/GKSDCS5H4ERC4ZTPNRBOBMH5ZDU6WQN2) | Corporate body SoR; `;` separates topic subtitles, not persons |
| `Statistische Berichte / Bayerisches Landesamt für Statistik … ; endgültige Ergebnisse` | [↗](https://ddb.de/item/54SBATDZQJGK5KQSFK3Q2RZU7U2RAQBM) | Same pattern — government agency SoR |

### f_year — founding years, life dates, composition dates

| Title | URL | Notes |
|---|---|---|
| `Jeversches Wochenblatt : Friesisches Tageblatt ; gegr. 1791` | [↗](https://ddb.de/item/AGZJAK7XYRNH3IWXEWFVELM4OFBJARLL) | 1791 is founding year (`gegr.`) |
| `Porträt Georg Philipp Wucherer (1734 - 1805) :Kupferstich ; Radierung` | [↗](https://ddb.de/item/7EG6MNM55XRFKT63ZIUZN35OZAZMMY2B) | 1734–1805 are life dates in parentheses |
| `Omnia possideat … bereit 1649. 1. Herbstmonat geschrieben` | [↗](https://ddb.de/item/KUYEGVHZ7535QJG7V5XM2NU5HW2CTAAG) | 1649 is composition date; 1656 is death date — neither is the publication year |

### f_other_title — life-date colon or `::` catalog separator

| Title | URL | Notes |
|---|---|---|
| `Feldmarschall Ludwig Andreas Graf von Khevenhüller-Frankenburg … :1683-1744 ; eine Lebensskizze` | [↗](https://ddb.de/item/SKUC2ZDHLCDGXDWQ2NMGSDXZ5U6GLRPC) | `:` precedes life dates, not a subtitle |
| `Johann Ludwig Böhner :7. Januar 1787 - 28. März 1860 ; [Katalog]` | [↗](https://ddb.de/item/THF6HTNRUTSYTYBY377JLKXHCWVHNYQP) | Same pattern — name + `:` + life dates |
| `Transnationales Strafrecht / Transnational Criminal Law :: gesammelte Beiträge; collected publications` | [↗](https://ddb.de/item/XDNVRXBWWZMMHHFOPZBUEVOOJYL6TGDH) | `::` is a DDB catalog-field separator, not ISBD |

---

## 5. Pre-1750 false negatives — author before title

Early modern German title pages frequently front-load the author's name and credentials before the work title, rather than placing them after ` /` (the ISBD SoR position). The ` /` heuristic misses these entirely — `f_person = 0` despite a named author being present.

| Title | URL | Pattern |
|---|---|---|
| `David Beuthers, Gewesenen Churfürstl. Sächsischen Probation-Meisters zu Dreßden, und Philosophi Adepti, Zwey rare Chymische Tractate :…` | [↗](https://ddb.de/item/KQCJ7APICPYVGBUZ544FKAICNU73FVKH) | Name + role credentials precede work title; no ` /` present |
| `Leich-Sermon … Bey … Sepultur Der … Magdalenen Heidewig Stissers/ Deß … Johan Julii Herings … HaußFrawen …` | [↗](https://ddb.de/item/7GZQOGDUS4AXD2LYGSHUWJPY6BDC3KMS) | Named deceased and husband's credentials embedded mid-title; SoR absent |
| `Königsberg, b. Fr. Nicolovius: Handbuch des römischen Privatrechts … Von Theodor Schmalz, D. Königl. Preuss. Consistorialrathe und Professor …` | [↗](https://ddb.de/item/T6YL7Z2YEIEFTKDTG4GFDBIIZIFYHIBB) | Author name follows `Von` mid-title, not ` /` |

This is a structural blind spot: the pattern cannot be fixed by post-filtering `f_person`. Early modern records in the SR-08 gold set will need a separate author-detection strategy (e.g. name-before-title NER, or annotation without relying on the SoR heuristic).

---

## 6. Decision gate outcome

Threshold: FP < 15% per field.

- **Excluded from silver labels:** `f_parallel`, `f_edition` — FP rates far exceed 15%; patterns fire predominantly on non-ISBD content in this corpus
- **Accepted with post-filtering:** `f_person`, `f_person_compound` — above threshold; require keyword guard (exclude single letters, region names, supplement labels) before use
- **Accepted:** `f_year`, `f_other_title`, `f_publisher`, `f_series`, `f_volume` — within threshold

---

## 7. Additional finding — pre-1750 author placement

Pre-1750 titles systematically place the author's name and credentials *before* the main title (not after ` /`), making `f_person` a **false negative** for this entire stratum. The SoR heuristic misses the majority of early modern authors. This is a structural blind spot, not a noise issue — the pattern cannot be fixed by post-filtering. Implications for SR-08 gold set composition: early modern records must be annotated with a different author-detection strategy.

---

## 8. Statistical sampling notes

### 8.1 Why stratified, not simple random

The nine heuristic flags fire at very different rates in the DDB corpus. Flags like `f_year` and `f_other_title` fire on a large share of records; flags like `f_parallel` and `f_edition` are comparatively rare. A simple random sample of 200 records would allocate observations roughly in proportion to flag prevalence — meaning rare flags might appear in only a handful of records, too few to estimate their FP rates reliably.

Stratified sampling solves this by treating each flag as a separate stratum and drawing records independently within each one. This guarantees that every flag type is represented regardless of its corpus frequency, making per-flag FP rate estimation feasible even for uncommon patterns.

Each record check is a **Bernoulli trial** — it either is or isn't a false positive. With n independent checks, the number of FPs follows a binomial distribution B(n, p). The reliability of the estimate increases with n: the variance of the proportion estimate is p(1−p)/n, so doubling n halves the variance and narrows the confidence interval by a factor of 1/√2.

### 8.2 Stratum definition

Each stratum consists of records where a given flag is active (`flag = 1`). Because a single record can trigger multiple flags simultaneously (e.g. a title with both ` /` and `;`), records are not mutually exclusive across strata — the same record may appear in the `f_person` stratum and the `f_person_compound` stratum. The reported FP rates are per-flag, not per-record.

### 8.3 What a confidence interval is, what it is not

The headline figure — 81 of 200 records have at least one FP — reflects the stratified design, not the population rate. Because strata were sampled independently (not in proportion to their corpus size), the 40.5% cannot be interpreted as the expected FP rate across all heuristic-labeled records in production. It is a summary of review coverage, not a population estimate. The per-flag rates in §3 are the operationally meaningful numbers.

A note on what the per-flag confidence intervals express: a 95% CI means that if we repeated this sampling procedure many times, 95% of the resulting intervals would contain the true FP rate. It does **not** mean "there is a 95% probability that the true rate lies in this interval" — the true rate is a fixed (unknown) number; the interval either contains it or it doesn't. The 95% is a property of the procedure, not of this specific interval.

### 8.4 Precision of per-flag estimates

With modest per-stratum sample sizes, the individual FP rate estimates carry uncertainty. As a rough guide, a 95% confidence interval (Wilson method) for a proportion has a half-width of roughly:

| Sample size | Half-width at p ≈ 0.50 | Half-width at p ≈ 0.10 |
|---|---|---|
| n = 20 | ±22 pp | ±13 pp |
| n = 30 | ±18 pp | ±11 pp |
| n = 50 | ±14 pp | ±8 pp |

**pp = percentage points** — an absolute unit. A half-width of ±22 pp at p = 0.50 means the interval runs from 28% to 72%. Writing "±22%" would be ambiguous (relative to the estimate, that would be ±11 pp); "pp" removes the ambiguity.

The CI width is proportional to √(p(1−p)/n). The product p(1−p) is maximised at p = 0.5 (giving 0.25) and shrinks at extreme values: p = 0.1 or 0.9 gives 0.09; p = 0.8 gives 0.16. Flags with FP rates far from 50% are therefore more precisely estimated at a given n. Concretely: the `f_parallel` (~80%) and `f_edition` (~83%) exclusion decisions are robust — their rates are far enough above the 15% threshold that sampling noise does not change the outcome. The `f_year` (~6%) and `f_other_title` (~8%) accept decisions are similarly robust. The `f_person` (~36%) and `f_person_compound` (~29%) post-filter decisions are above threshold with margin, but sit closer to 0.5 and should be revisited if stratum sizes are small.

**Computing the Wilson interval in Python** (preferred over Wald when p is near 0 or 1, because Wald can produce negative lower bounds for rare events):

```python
from statsmodels.stats.proportion import proportion_confint

# k = FP count, n = stratum size — from §3 results table
fields = [
    ("f_parallel",        20,  25),   # ~80% FP → Exclude
    ("f_edition",         30,  36),   # ~83% FP → Exclude
    ("f_person",          17,  47),   # ~36% FP → Post-filter
    ("f_person_compound",  7,  24),   # ~29% FP → Post-filter
    ("f_year",             9, 150),   # ~6%  FP → Accept
    ("f_other_title",      8, 100),   # ~8%  FP → Accept
]

for field, k, n in fields:
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    print(f"{field:<22}  {k/n:.0%}  95% CI [{lo:.0%}, {hi:.0%}]")
```

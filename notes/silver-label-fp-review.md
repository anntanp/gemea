# GeMeA — Silver Label False-Positive Review (SR-03)

**SR-03** in [ner-bibliographic.md](ner-bibliographic.md). See also [isbd-field-rating.md](isbd-field-rating.md).

---

## 1. Background

`rate_isbd_fields.py` assigns silver labels to titles by detecting ISBD punctuation patterns at two tiers:

- **Tier 2 (structural):** `. -` area separator present — strong structural signal, expected high precision
- **Tier 1 (heuristic):** no `. -`, but other markers fire (` :`, ` /`, 4-digit year, edition keyword, etc.) — weaker signal, false positive rate unknown

Heuristic patterns over-fire on non-ISBD content:
- ` :` fires on any colon, not just ISBD subtitle separators
- ` /` fires on fractions, series letter suffixes, and region names as well as Statement of Responsibility (SoR)
- A 4-digit number fires on founding years, life dates, and manuscript dates — not only publication years

---

## 2. Review method

`scripts/validate_heuristic_fields.py` produced a 200-record stratified sample at `data/processed/heuristic_validation_sample.csv`, with one stratum per heuristic field flag. `scripts/sr03_fp_review.py` applied automated regex rules + per-row overrides to classify each active flag as TP or FP, writing results to the `fp_fields` and `notes` columns.

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

This is a structural blind spot: the pattern cannot be fixed by post-filtering `f_person`. Early modern records in the SR-07 gold set will need a separate author-detection strategy (e.g. name-before-title NER, or annotation without relying on the SoR heuristic).

---

## 6. Decision gate outcome

Threshold: FP < 15% per field.

- **Excluded from silver labels:** `f_parallel`, `f_edition` — FP rates far exceed 15%; patterns fire predominantly on non-ISBD content in this corpus
- **Accepted with post-filtering:** `f_person`, `f_person_compound` — above threshold; require keyword guard (exclude single letters, region names, supplement labels) before use
- **Accepted:** `f_year`, `f_other_title`, `f_publisher`, `f_series`, `f_volume` — within threshold

---

## 7. Additional finding — pre-1750 author placement

Pre-1750 titles systematically place the author's name and credentials *before* the main title (not after ` /`), making `f_person` a **false negative** for this entire stratum. The SoR heuristic misses the majority of early modern authors. This is a structural blind spot, not a noise issue — the pattern cannot be fixed by post-filtering. Implications for SR-07 gold set composition: early modern records must be annotated with a different author-detection strategy.

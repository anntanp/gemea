# Hierarchy Type Title Quality

Analysis of which `hierarchy_type` values produce titles that carry no meaningful content — i.e., titles that are merely structural labels, repeated boilerplate, or section-type names rather than descriptive text. Based on sampling from `data/out/s2/s2_meta.parquet` (18,570,245 objects, Sector 2).

## 1. Strong candidates — titles almost never carry content

### 1.1 htype_017 · Inhaltsverzeichnis (n=64,380)

Titles are overwhelmingly the section label itself or near-synonyms. Essentially zero information content.

| Title | Link |
|-------|------|
| "Inhaltsverzeichnis" | [NPPIMZ3WQRLD4CBVA2VPQMW3KYEKFOEB](https://www.deutsche-digitale-bibliothek.de/item/NPPIMZ3WQRLD4CBVA2VPQMW3KYEKFOEB) |
| "Inhalts-Verzeichniß." | [ORKMRZYAOHCHE7VRE33UQT3LNUF7G6P6](https://www.deutsche-digitale-bibliothek.de/item/ORKMRZYAOHCHE7VRE33UQT3LNUF7G6P6) |
| "Inhalt" | [JMUDQAV2FEKZVMMW7RCH7PK4NS4O6A77](https://www.deutsche-digitale-bibliothek.de/item/JMUDQAV2FEKZVMMW7RCH7PK4NS4O6A77) |
| "Inhalt" | [WEONH6MXZLBDXMAX5PUUKNBN42NSXTZE](https://www.deutsche-digitale-bibliothek.de/item/WEONH6MXZLBDXMAX5PUUKNBN42NSXTZE) |
| "Allgemeine Ab- und Eintheilung dieses Gesang-Buches." | [JEZGMYDQIB2ZE2RL6K4N4KQXLEFYQMXA](https://www.deutsche-digitale-bibliothek.de/item/JEZGMYDQIB2ZE2RL6K4N4KQXLEFYQMXA) |
| "Förtekning på de Rön, som åro införde i detta Qvartals Handlingar." | [BIRCGXODAGFCOMWZWUQAGZQK44UIVHEB](https://www.deutsche-digitale-bibliothek.de/item/BIRCGXODAGFCOMWZWUQAGZQK44UIVHEB) |

The last two show that occasional outliers exist (non-German sources), but they remain structural.

### 1.2 htype_004 · Annotation (n=1,772)

Almost exclusively "Handschriftliche Eintragung/en" — a cataloguer label for the presence of manuscript annotations, not a title.

| Title | Link |
|-------|------|
| "Handschriftliche Eintragungen" | [Q6B5T5BXINSQFH4EQ6A7CK65V25ODUXT](https://www.deutsche-digitale-bibliothek.de/item/Q6B5T5BXINSQFH4EQ6A7CK65V25ODUXT) |
| "Handschriftliche Eintragungen" | [IETUCDS3QI2Y5J3YAZZYXYKARGQUQFBH](https://www.deutsche-digitale-bibliothek.de/item/IETUCDS3QI2Y5J3YAZZYXYKARGQUQFBH) |
| "Handschriftliche Eintragung" | [PNLPPBVUIGPFU4TTQA6V3WJJZXDHJU3O](https://www.deutsche-digitale-bibliothek.de/item/PNLPPBVUIGPFU4TTQA6V3WJJZXDHJU3O) |
| "Handschriftliches Inhaltsverzeichnis des Sammelbandes" | [Q223GXSWLRT4KYXOH2F3JUA6D3OIOY52](https://www.deutsche-digitale-bibliothek.de/item/Q223GXSWLRT4KYXOH2F3JUA6D3OIOY52) |
| "(12v) Notizen zur Berechnung des Erddurchmessers & zu komputistischen Merkversen." | [XZQCFWBQFUQKBW7754TAVQQWWO2YOY22](https://www.deutsche-digitale-bibliothek.de/item/XZQCFWBQFUQKBW7754TAVQQWWO2YOY22) |

The last example is an outlier with actual content; the majority pattern is boilerplate.

### 1.3 htype_010 · Eintrag (n=1,327)

Same pattern as htype_004 — all sampled titles are "Handschriftliche Eintragungen/Eintragung".

| Title | Link |
|-------|------|
| "Handschriftliche Eintragungen" | [PMR4PHL4LJ5FHGX6T4FPW4YQVCG67QOA](https://www.deutsche-digitale-bibliothek.de/item/PMR4PHL4LJ5FHGX6T4FPW4YQVCG67QOA) |
| "Handschriftliche Eintragungen" | [527QVBVOLHTTXJWMMVMU2D2J5YVOLIWM](https://www.deutsche-digitale-bibliothek.de/item/527QVBVOLHTTXJWMMVMU2D2J5YVOLIWM) |
| "Handschriftliche Eintragungen" | [HBJ6SQSFPZ3FKWISDHIOI54RESE7I2RO](https://www.deutsche-digitale-bibliothek.de/item/HBJ6SQSFPZ3FKWISDHIOI54RESE7I2RO) |
| "Handschriftliche Eintragung" | [6I5A6V53XSLXMFPSZ5ENDYNZNTXLJCHT](https://www.deutsche-digitale-bibliothek.de/item/6I5A6V53XSLXMFPSZ5ENDYNZNTXLJCHT) |
| "Handschriftliche Eintragungen." | [3RPJCUUVMYDNO6KTCYIGOFJL6NSQ5NJE](https://www.deutsche-digitale-bibliothek.de/item/3RPJCUUVMYDNO6KTCYIGOFJL6NSQ5NJE) |

### 1.4 htype_016 · Index (n=59,158)

Titles are mostly "Register" or ordinal variants. A few are more specific but still structural.

| Title | Link |
|-------|------|
| "Register" | [NZH5TFFSFUE34MMM54QG5LB3WA2MWED7](https://www.deutsche-digitale-bibliothek.de/item/NZH5TFFSFUE34MMM54QG5LB3WA2MWED7) |
| "Das dritte Register" | [HU2JKO7XYOMRHBOMOS62V5JHX7XGTWVV](https://www.deutsche-digitale-bibliothek.de/item/HU2JKO7XYOMRHBOMOS62V5JHX7XGTWVV) |
| "Catalogus auctorum" | [PGGBXJKFFSZKGAH6H43ML2FQEACISEI4](https://www.deutsche-digitale-bibliothek.de/item/PGGBXJKFFSZKGAH6H43ML2FQEACISEI4) |
| "Register uber diß vorgehende Büchlein von der Beicht und Absolution." | [6PFNYPGEBCTP2IS6ZHO6LQ2WTUBZXELN](https://www.deutsche-digitale-bibliothek.de/item/6PFNYPGEBCTP2IS6ZHO6LQ2WTUBZXELN) |
| "[Falsch eingebunden] Register der neuen Teutschen Weltlichen Lieder" | [EN6ICRHQ5NI24CFST5YZYW4PJAISAJJ6](https://www.deutsche-digitale-bibliothek.de/item/EN6ICRHQ5NI24CFST5YZYW4PJAISAJJ6) |

### 1.5 htype_028 · Vorwort (n=61,256)

Titles are the section-type label ("Vorwort.", "Vorrede.", "Praefatio.", "序") or minimally extend it. Rarely descriptive.

| Title | Link |
|-------|------|
| "Vorwort." | [ULLLWJU6525OQRDRLB3TPAY7XBEBUK3O](https://www.deutsche-digitale-bibliothek.de/item/ULLLWJU6525OQRDRLB3TPAY7XBEBUK3O) |
| "序" | [3FQGNL6YFJT3FX5AC2CX3ZQ4IJEW7ANR](https://www.deutsche-digitale-bibliothek.de/item/3FQGNL6YFJT3FX5AC2CX3ZQ4IJEW7ANR) |
| "Epistola Nuncupatoria" | [BU42ZB557HHTXQBHMGCAWZXOFIJ4BPD2](https://www.deutsche-digitale-bibliothek.de/item/BU42ZB557HHTXQBHMGCAWZXOFIJ4BPD2) |
| "Vorwort des Herausgebers" | [MC3XFH3I4PML3M7HIHWQ4R2DK2H6LX6X](https://www.deutsche-digitale-bibliothek.de/item/MC3XFH3I4PML3M7HIHWQ4R2DK2H6LX6X) |
| "Einleitung. Begränzung und Epochen des Mittelalters." | [XXHLVMFDBKRCN577FSZK4WPGAGIVVQPC](https://www.deutsche-digitale-bibliothek.de/item/XXHLVMFDBKRCN577FSZK4WPGAGIVVQPC) |

The last example carries partial content but is borderline.

---

## 2. Partial candidates — mixed content quality

### 2.1 htype_029 · Widmung (n=13,237)

Bimodal: some are just "Widmung" / "Widmungsseiten.", others are long dedications that name people and institutions — potential NER material.

| Title | Link |
|-------|------|
| "Widmung" | [DH3MKSYIWBLSQFTWKQ7ZJV27IYBBUWWF](https://www.deutsche-digitale-bibliothek.de/item/DH3MKSYIWBLSQFTWKQ7ZJV27IYBBUWWF) |
| "Illustrissimo Heroi Dn. Eberhardo Libero Baroni de Danckelman [...]" | [XRVC3HI77GCVNIL4GTOTE4GKFYOUCNBB](https://www.deutsche-digitale-bibliothek.de/item/XRVC3HI77GCVNIL4GTOTE4GKFYOUCNBB) |
| "Viro Illustri ... Domino Joanni Georgio Steigertahl [...]" | [FMJMCCFWOB6MC5YNDDXUR3SECV2ABV2L](https://www.deutsche-digitale-bibliothek.de/item/FMJMCCFWOB6MC5YNDDXUR3SECV2ABV2L) |
| "Der Edlen und Vieltugendreichen Frawen/ Catharinen Düsterhopen/ [...]" | [PS5STJ3ILXDCMXTJUS3CZ3L3FPMXVNIV](https://www.deutsche-digitale-bibliothek.de/item/PS5STJ3ILXDCMXTJUS3CZ3L3FPMXVNIV) |

### 2.2 htype_001 · Abschnitt (n=2,246,940)

Largest group after htype_014/006/018. Highly variable — some generic, many meaningful.

| Title | Link | Quality |
|-------|------|---------|
| "Note" | [YEOESNFAABYXI72KDUK7WP7JXVQODWIT](https://www.deutsche-digitale-bibliothek.de/item/YEOESNFAABYXI72KDUK7WP7JXVQODWIT) | empty |
| "Deckel." | — | empty |
| "Siebenzehntes Hundert." | [4UW6RJDPKZECP75OZZVBROEJBL6BOJSL](https://www.deutsche-digitale-bibliothek.de/item/4UW6RJDPKZECP75OZZVBROEJBL6BOJSL) | structural |
| "Bey den Verlegern dieser Nachrichten ist auch zu haben:" | [4AFYGTOPFXFKLCTHYH5UTLM6NM7HW6EL](https://www.deutsche-digitale-bibliothek.de/item/4AFYGTOPFXFKLCTHYH5UTLM6NM7HW6EL) | borderline |
| "Abb. 86 Stenosicrendes Adenokarzinom des Rektums" | [FWSQKPB565YGSO2SCITL4SF4RTJFIX7W](https://www.deutsche-digitale-bibliothek.de/item/FWSQKPB565YGSO2SCITL4SF4RTJFIX7W) | content |
| "Wilhelm II. vierter Statthalter, General-Capitain und Admiral. 1647." | [DT7LSBQFPZ5L43YVOHQUQJH7VDIQ5MZS](https://www.deutsche-digitale-bibliothek.de/item/DT7LSBQFPZ5L43YVOHQUQJH7VDIQ5MZS) | content |

Cannot exclude as a class; needs finer-grained filtering.

### 2.3 htype_018 · Kapitel (n=2,664,050)

Similarly mixed. Ordinal labels ("Seconde partie", "Capitulum III") alongside real chapter titles.

| Title | Link | Quality |
|-------|------|---------|
| "Seconde partie" | [V3RS446VU6OQ6UKP4GACNNBWQ7GFKC7J](https://www.deutsche-digitale-bibliothek.de/item/V3RS446VU6OQ6UKP4GACNNBWQ7GFKC7J) | structural |
| "Einband" | — | empty |
| "Dialogo Forestiere, e Gentilhuomo Romano" | [WQM4MU3WXMS54KO77BJNHQAEJIIPRKOB](https://www.deutsche-digitale-bibliothek.de/item/WQM4MU3WXMS54KO77BJNHQAEJIIPRKOB) | content |
| "Sechstes Sinnbild von Geheimnuß der Natur [...]" | [RRFIYJBN5V3IJY2BTLDRTKVMVGC4I2JC](https://www.deutsche-digitale-bibliothek.de/item/RRFIYJBN5V3IJY2BTLDRTKVMVGC4I2JC) | content |

### 2.4 htype_027 · Vers (n=2,484)

"Aliud." (Latin for "another one") is a recurring empty placeholder; named verses are content-bearing.

| Title | Link | Quality |
|-------|------|---------|
| "Aliud." | [U7WOMKN5TWHHQ4PYV2WGL7CAVYSXJEDY](https://www.deutsche-digitale-bibliothek.de/item/U7WOMKN5TWHHQ4PYV2WGL7CAVYSXJEDY) | empty placeholder |
| "Hymnus VII." | [LTTEUBQECFAZI6XZUPXX3CFPG3X5OZJL](https://www.deutsche-digitale-bibliothek.de/item/LTTEUBQECFAZI6XZUPXX3CFPG3X5OZJL) | structural |
| "Phalaecium, ad Praestantißimum Virum, dn. Ioannem Mollinum ..." | [7UFMTNFUHEBJGRQYG2S5QKU6PFWAAC64](https://www.deutsche-digitale-bibliothek.de/item/7UFMTNFUHEBJGRQYG2S5QKU6PFWAAC64) | content |
| "In Effigiem Exercitatissimi Et Ingeniosissimi Viri D. Leonhardi Thurnesii [...]" | [WDGUZNUQKOOKBPZEZL5SICY5736C4TT3](https://www.deutsche-digitale-bibliothek.de/item/WDGUZNUQKOOKBPZEZL5SICY5736C4TT3) | content |

---

## 3. Not candidates — titles carry real content

| htype | Label | Reason |
|-------|-------|--------|
| htype_006 | Aufsatz | Article titles, specific and descriptive |
| htype_021 | Monografie | Monograph titles, highly specific |
| htype_013 | Handschrift | Manuscript descriptions with shelfmarks and dates |
| htype_007 | Band | Volume titles with series context |
| htype_014 | Heft | Newspaper issue titles with dates |
| htype_015 | Illustration | Caption-like titles, often specific |
| htype_019 | Karte | Map titles with geographic scope |
| htype_038 | Brief | Letter descriptions with sender/recipient/date |
| htype_003 | Beigefügtes/enthaltenes Werk | Contained works with their own titles |
| htype_020 | Mehrbändiges Werk | Multi-volume work titles |

---

## 4. What "content" means

A title has **content** if it could identify a specific literary or intellectual work — i.e., it is a candidate for GND Werk linking. This excludes:

- **Section labels** — titles that are just the htype name or a boilerplate synonym ("Inhalt", "Vorwort", "Register", "Handschriftliche Eintragungen")
- **Physical/digitisation labels** — titles referring to the physical object or scanning artefact ("Titelblatt", "Einband", "Deckel", "Spiegel", "Maßstab/Farbkeil", "Umschlag")

The validation script (`scripts/analysis/validate_htype_title_quality.py`) initially treated these two non-content classes together. Revisiting the top titles for htype_018 (Kapitel) and htype_001 (Abschnitt) revealed that many "non-generic" titles are actually physical/digitisation labels — not work titles either.

---

## 5. Filtering strategy

Three approaches were considered:

**Option A — Blanket htype filter.** Exclude entire htypes where most titles are non-content.
- Pro: simple, no false positives within excluded types
- Con: drops the minority of real work titles inside each htype; brittle across institutions

**Option B — Cross-cutting title pattern filter.** Ignore htype; apply universal blocklists for section labels and physical labels across all htypes.
- Pro: catches bad titles in htypes not flagged; keeps good titles in "bad" htypes; one filter to maintain
- Con: patterns must be thorough; edge cases (a work genuinely titled "Register") get dropped

**Option C — Hybrid (chosen).** Two-stage:
1. **Blanket exclude** htypes where *even the outlier titles* are not work titles: htype_017 (Inhaltsverzeichnis), htype_004 (Annotation), htype_010 (Eintrag). Their non-boilerplate titles ("目錄", "Aufführungsnotizen", "Handschriftliches Inhaltsverzeichnis") are descriptive labels, not work titles.
2. **Cross-cutting pattern filter** on all remaining htypes, with two blocklists:
   - *Section labels*: "Vorwort", "Register", "Widmung", "Aliud.", ordinal part labels, etc.
   - *Physical/digitisation labels*: "Titelblatt", "Einband", "Deckel", "Spiegel", "Umschlag", "Maßstab/Farbkeil", etc.

Implementation: `scripts/analysis/filter_content_titles.py`

### 5.1 Results

Full counts in `data/processed/title_class_counts.csv`; figure in `notes/images/title_class_breakdown.png`.

| htype | Label | total | work_title | section_label | physical_label | work% |
|-------|-------|------:|----------:|-------------:|---------------:|------:|
| htype_014 | Heft | 5,620,537 | 5,583,356 | 5,259 | 31,922 | 99.3% |
| htype_006 | Aufsatz | 3,098,229 | 3,043,589 | 50,793 | 3,847 | 98.2% |
| htype_018 | Kapitel | 2,664,050 | 2,303,455 | 90,951 | 269,644 | 86.5% |
| htype_021 | Monografie | 2,416,560 | 2,414,796 | 1,704 | 60 | 99.9% |
| htype_001 | Abschnitt | 2,246,940 | 2,048,208 | 46,968 | 151,764 | 91.2% |
| UNK | UNK | 863,401 | 861,319 | 563 | 1,519 | 99.8% |
| htype_007 | Band | 704,948 | 704,862 | 83 | 3 | 100.0% |
| htype_015 | Illustration | 241,546 | 211,546 | 51 | 29,949 | 87.6% |
| htype_013 | Handschrift | 139,618 | 137,778 | 1,776 | 64 | 98.7% |
| htype_008 | Beilage | 134,291 | 133,657 | 529 | 105 | 99.5% |
| htype_017 | Inhaltsverzeichnis | 64,380 | 0 | 64,380 | 0 | 0.0% |
| htype_028 | Vorwort | 61,256 | 32,113 | 29,089 | 54 | 52.4% |
| htype_016 | Index | 59,158 | 41,627 | 17,465 | 66 | 70.4% |
| htype_026 | Text | 53,318 | 49,592 | 2,040 | 1,686 | 93.0% |
| htype_038 | Brief | 45,131 | 44,916 | 189 | 26 | 99.5% |
| htype_003 | Beigefügtes Werk | 44,593 | 44,570 | 16 | 7 | 99.9% |
| htype_020 | Mehrbändiges Werk | 31,121 | 31,080 | 29 | 12 | 99.9% |
| htype_023 | Fortlaufendes Sammelwerk | 30,936 | 30,874 | 62 | 0 | 99.8% |
| htype_019 | Karte | 26,644 | 26,518 | 3 | 123 | 99.5% |
| htype_029 | Widmung | 13,237 | 10,051 | 3,185 | 1 | 75.9% |
| htype_011 | Faszikel | 3,992 | 3,731 | 259 | 2 | 93.5% |
| htype_027 | Vers | 2,484 | 2,302 | 152 | 30 | 92.7% |
| htype_004 | Annotation | 1,772 | 0 | 1,772 | 0 | 0.0% |
| htype_010 | Eintrag | 1,327 | 0 | 1,327 | 0 | 0.0% |
| htype_012 | Fragment | 686 | 682 | 4 | 0 | 99.4% |
| **TOTAL** | | **18,570,245** | **17,760,712** | **318,649** | **490,884** | **95.6%** |

Notable findings:
- **htype_028 (Vorwort)**: only 52.4% work titles — "Vorwort zur zweiten Auflage", "Preface", etc. are correctly caught as section labels; may be worth reviewing the boundary (e.g. "Vorbericht" is borderline)
- **htype_018 (Kapitel)** and **htype_001 (Abschnitt)**: physical labels (Einband, Spiegel, Titelblatt…) pull the work% down to 86–91%
- **htype_015 (Illustration)**: 12% physical labels ([Tafel N], Frontispiz, etc.) — expected for a digitisation-heavy type
- **95.6%** of all 18.6M titles survive as potential work_title candidates

---

## 6. Summary

| Category | htypes | Action |
|----------|--------|--------|
| Blanket exclude | htype_017, htype_004, htype_010 | Drop entirely — no work titles even in outliers |
| Pattern filter (stage 2) | all remaining htypes | Drop section labels + physical/digitisation labels |
| Keep as-is | htype_006, htype_021, htype_013, htype_007, htype_014, htype_015, htype_019, htype_038, htype_003, htype_020 | Titles are content-bearing by construction |

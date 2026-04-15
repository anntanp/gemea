# GeMeA — DF_DE_TITLES: Source and Title-Length Distribution

**SR-10** in [ner-bibliographic.md](../ner-bibliographic.md). See also [sr10_title-length-thresholds.md](sr10_title-length-thresholds.md).

---

## 1. Corpus provenance

`DF_DE_TITLES` originates in `2023.11 NER.ipynb` — the earliest notebook in the series. `2024.01 MT-QA.ipynb` produced the timestamped pickle (`DF_DE_TITLES_20240125b.pkl`) but is not the source of the variable definition.

Definition (from `2023.11 NER.ipynb`, consistent with `2023.12 Relation Extraction.ipynb`):

> "4,477,641 objects are titles of all TEXT objects, tagged to be in German (`dc:language`) and identified by `langid` to be in German."

Selection funnel:

| | No. Records |
|---|---|
| Total Titles (DDB) | 16,805,998 |
| TEXT | 8,402,999 |
| Valid HTYPEs (% of TEXT) | 1,812,559 (21.57%) |
| No Language Tags (% of valid) | 384,405 (21.21%) |
| **Titles tagged + identified as German** | **4,477,641 (53.29%)** |

`DF_DE_TITLES` is a filtered snapshot of the DDB corpus: `ddb:hierarchyType` = `content` (the "Valid HTYPEs" step in the funnel above), then `dc:language` = German AND `langid` = German. Not filtered by `dc:type`, provider, or era beyond these two steps. Tokenization in the source notebook uses `spacy.load` (model unspecified in the trace).

**Implication.** The corpus spans all eras and `dc:type` values — both long ISBD strings and short bare titles. ISBD coverage figures (20.2% ` :`, 0.8% ` /`) reflect this broad population.

---

## 2. Token-count distribution

Script: `scripts/explore_token_distribution.py` — raw distribution of `all_tokens` and `content_tokens` across all 4,477,780 titles.

![Token distribution](../images/fig_token_distribution.png)

Percentile table:

| Percentile | all_tokens | content_tokens |
|---|---|---|
| p10 | 2 | 1 |
| p25 | 4 | 2 |
| p33 | 5 | 3 |
| p50 | 8 | 5 |
| p66 | 12 | 6 |
| p75 | 14 | 8 |
| p90 | 24 | 13 |
| p95 | 36 | 19 |
| p99 | 74 | 40 |

Shape: roughly flat from 1–9 tokens (5–8% each), peak at 4 tokens (8.0%), then steadily declining. Notable bump at 20 tokens (1.9% vs. 1.3% at 19 and 1.0% at 21) — likely a truncation artifact in the source data.

**Threshold decision: quartiles (≤4 / 5–14 / >14)** — p25 = 4, p75 = 14, equal outer groups (~25% each). Full rationale and alternatives in [sr10_title-length-thresholds.md](ner/sr10_title-length-thresholds.md).

---

## 3. Title-length distribution by year

Script: `scripts/analyse_title_lengths.py` — token counts from pre-computed `all_tokens` (includes stopwords and punctuation) and `content_tokens` (stopwords removed; punctuation retained); year from `dates` column (1400–2029), falling back to title regex for nulls.

Year coverage: 89.4% from `dates` column, 1.0% from title regex fallback, **9.6% no year** (429,097 titles).

![Title-length distribution by year](../images/fig_title_lengths.png)

Overall distribution (4,477,780 titles; `all_tokens` including stopwords and punctuation):

| Category | Threshold | Count | % |
|---|---|---|---|
| Short | ≤ 4 tokens (p25) | 1,269,034 | 28.3% |
| Medium | 5–14 tokens (p25–p75) | 2,110,610 | 47.1% |
| Long | > 14 tokens (p75) | 1,098,136 | 24.5% |
| **Median all_tokens** | | **8** | |
| **Median content_tokens** | | **5** | |

Per 25-year bucket (N = 4,048,683 titles with year; 1500+):

| Year bucket | Total | Short% | Medium% | Long% | Median all_t | Median con_t |
|---|---|---|---|---|---|---|
| 1500–1524 | 12,209 | 14.9% | 39.8% | 45.3% | 13 | 7 |
| 1525–1549 | 23,901 | 13.5% | 42.0% | 44.5% | 13 | 7 |
| 1550–1574 | 33,802 | 15.3% | 42.2% | 42.6% | 12 | 6 |
| 1575–1599 | 37,307 | 14.6% | 42.7% | 42.7% | 12 | 6 |
| 1600–1624 | 57,887 | 14.7% | 36.7% | 48.6% | 14 | 7 |
| 1625–1649 | 36,795 | 17.6% | 32.1% | 50.3% | 15 | 8 |
| 1650–1674 | 56,317 | 16.4% | 34.6% | 49.0% | 14 | 7 |
| 1675–1699 | 65,723 | 15.7% | 34.3% | 50.0% | 15 | 7 |
| 1700–1724 | 112,587 | 17.0% | 37.7% | 45.3% | 13 | 6 |
| 1725–1749 | 125,802 | 18.5% | 39.3% | 42.2% | 12 | 6 |
| 1750–1774 | 183,051 | 22.1% | 44.3% | 33.6% | 10 | 5 |
| 1775–1799 | 406,016 | 35.5% | 40.1% | 24.4% | 7 | 4 |
| 1800–1824 | 195,586 | 25.5% | 41.9% | 32.5% | 9 | 5 |
| 1825–1849 | 318,929 | 22.8% | 50.9% | 26.3% | 7 | 5 |
| 1850–1874 | 364,664 | 24.4% | 49.0% | 26.7% | 9 | 5 |
| 1875–1899 | 503,814 | 35.7% | 46.1% | 18.2% | 6 | 4 |
| 1900–1924 | 624,305 | 38.4% | 49.4% | 12.2% | 6 | 4 |
| 1925–1949 | 267,685 | 36.0% | 45.4% | 18.7% | 7 | 4 |
| 1950–1974 | 107,850 | 36.5% | 43.1% | 20.4% | 7 | 4 |
| 1975–1999 | 106,457 | 31.4% | 51.0% | 17.7% | 8 | 5 |
| 2000–2024 | 400,569 | 8.9% | 62.2% | 28.9% | 11 | 6 |

---

## 4. Key findings

- **Pre-1750:** 42–50% long (>14 tokens), median `all_tokens` 12–15. Consistent with early modern title-page conventions: descriptive long-form titles that fold in subtitle, author, place, and printer information into a single string — the title page functioned as a table of contents.
- **Post-1775 shift:** median drops from 10 (1750–1774) to 7 (1775–1799); long falls from 34% to 24%. The shift predates any cataloging standardization and aligns with the Enlightenment and Sturm-und-Drang turn toward concise, standalone titles — a publishing convention change, not a cataloging artifact. Short (≤4) rises further to 35–38% in the 1875–1949 period as modern commercial publishing norms consolidate.
- **2000–2024 reverses:** only 9% short, 62% medium, 29% long — digital-born metadata with richer structured descriptions and subtitle fields recorded separately.
- **Non-content token overhead:** `content_tokens` (stopwords removed, punctuation retained) runs ~3 tokens below `all_tokens` (stopwords + punctuation included) median consistently across all eras.
- **Implication for SR-08 (gold set):** stratify by length as well as era. Pre-1750 long-form records stress the NER model differently from the short modern majority — the TITLE boundary is structurally different. The 9.6% no-year group needs separate treatment — sample by `dc_type` or `silver_tier` instead.

---

## 5. Longest title in the dataset

The record with the highest `all_tokens` count (921 tokens; 506 `content_tokens`) is a collective review of 33 pamphlets from the *Allgemeine Literatur-Zeitung*, 1831:

> [Sammelrezension von 33 Schriften, veranlasst durch die aufrührerischen Bewegungen im Königreiche Hannover.] (Fortsetzung vom vorigen Stück.) Rezensiert werden: 1) Gans, S. P.: Ueber die Verarmung der Städte und des Landmanns …

`obj_id`: [`52Q5EDQ44JLQS4WFJL2UNTHBQ4TZPAPB`](https://www.deutsche-digitale-bibliothek.de/item/52Q5EDQ44JLQS4WFJL2UNTHBQ4TZPAPB) — link validated 2026-03-27.

This is a pathological case: the full `title` field contains the enumerated bibliographic descriptions of all 33 reviewed works concatenated into one string, not a single descriptive title. It represents a cataloging artifact where a multi-item review was ingested as a single title record, inflating the token count far beyond any genuine title.

---

## 7. v2 — regenerated from `s2_meta_de_content.parquet` (2026-04-14)

The analysis was re-run against the new canonical source (`data/out/s2/s2_meta_de_content.parquet`) following the corpus source migration (ADR-02). The old `DF_DE_TITLES` figures in §§2–5 are preserved for comparison; this section documents the differences.

**Source:** `data/processed/de_titles_tokenized.parquet` — produced by `scripts/analysis/tokenize_de_titles.py` (xlm-roberta-large tokenizer; 9,213,339 rows).
**Scripts:** `scripts/ner/sr10_explore_token_distribution.py`, `scripts/ner/sr10_analyse_title_lengths.py` (both adapted to accept parquet via `--suffix _v2`).
**Outputs:** `notes/images/fig_token_distribution_v2.png`, `notes/images/token-distribution_v2.json`, `notes/images/fig_title_lengths_v2.png`, `notes/images/title-length-analysis_v2.json`, `notes/images/fig_title_lengths_v2.jsx`, `notes/images/fig_title_lengths_v2_bw.html`.

### 7.1 Corpus differences

| | DF_DE_TITLES (pkl) | s2_meta_de_content (parquet) |
|--|--|--|
| N rows | 4,477,780 | 9,213,339 |
| Language filter | `dc:language=ger` AND `langid=ger` | `dc:language ∈ {ger, gmh, nds, lat}` |
| htype filter | `hierarchy_type = content` (narrower) | ADR-01 BLANKET_EXCLUDE (8 types) |
| Tokenizer | spaCy (model unspecified) | xlm-roberta-large (SentencePiece BPE) |
| `all_tokens` definition | spaCy tokens incl. punctuation | xlm-roberta subword pieces excl. `<s>`/`</s>` |

The doubled row count reflects: (a) broader htype retention, (b) removal of the `langid` secondary filter, and (c) addition of Latin (493,712 records, 5.4%).

### 7.2 Token-count distribution (v2)

![Token distribution v2](../images/fig_token_distribution_v2.png)

| Percentile | all_tokens | content_tokens |
|---|---|---|
| p10 | 5 | 5 |
| p25 | 8 | 8 |
| p33 | 10 | 9 |
| p50 | 15 | 14 |
| p66 | 22 | 20 |
| p75 | 27 | 24 |
| p90 | 43 | 38 |
| p95 | 63 | 59 |
| p99 | 126 | 113 |

Median shifts from 8 → 15 tokens. The xlm-roberta BPE tokenizer produces more pieces per word than spaCy (subword splitting of compound German words and historical orthography), which accounts for most of the increase. The threshold values (p25 ≤ 4 / p75 ≤ 14) from the old corpus do not transfer — new thresholds should be recalibrated against v2 percentiles (p25 = 8, p75 = 27).

### 7.3 Title-length by era (v2)

![Title lengths v2](../images/fig_title_lengths_v2.png)

Year coverage: 93.5% from `dates` column, 0.8% from title regex fallback, 5.7% undated (521,091 titles). Bucket size: 25 years (22 non-empty bins from 1500+).

Overall (9,213,339 titles, `all_tokens`):

| Category | Threshold | Count | % |
|---|---|---|---|
| Short | ≤ 4 tokens | 853,046 | 9.3% |
| Medium | 5–14 tokens | 3,519,499 | 38.2% |
| Long | > 14 tokens | 4,840,794 | 52.5% |
| **Median all_tokens** | | **15** | |
| **Median content_tokens** | | **14** | |

Per 25-year bucket (titles with year ≥ 1500):

| Year bucket | Total | Short% | Med% | Long% | Median all_t | Median con_t |
|---|---|---|---|---|---|---|
| 1500–1524 | 18,788 | 3.4% | 17.5% | 79.0% | 32 | 30 |
| 1525–1549 | 23,182 | 2.3% | 15.6% | 82.1% | 36 | 34 |
| 1550–1574 | 32,226 | 3.6% | 15.2% | 81.2% | 40 | 38 |
| 1575–1599 | 41,895 | 2.8% | 12.8% | 84.4% | 52 | 50 |
| 1600–1624 | 70,934 | 3.0% | 16.3% | 80.7% | 44 | 43 |
| 1625–1649 | 46,624 | 3.2% | 16.3% | 80.5% | 45 | 43 |
| 1650–1674 | 74,698 | 2.2% | 18.3% | 79.5% | 43 | 42 |
| 1675–1699 | 80,204 | 2.4% | 14.5% | 83.2% | 46 | 44 |
| 1700–1724 | 100,910 | 3.5% | 14.1% | 82.3% | 48 | 45 |
| 1725–1749 | 118,444 | 4.4% | 14.4% | 81.2% | 40 | 37 |
| 1750–1774 | 167,584 | 6.3% | 29.9% | 63.7% | 22 | 20 |
| 1775–1799 | 283,642 | 6.4% | 36.0% | 57.6% | 18 | 16 |
| 1800–1824 | 366,440 | 12.5% | 43.4% | 44.1% | 13 | 12 |
| 1825–1849 | 748,880 | 14.9% | 43.6% | 41.6% | 12 | 11 |
| 1850–1874 | 1,190,737 | 13.3% | 42.1% | 44.6% | 12 | 12 |
| 1875–1899 | 1,451,602 | 10.2% | 39.5% | 50.3% | 15 | 13 |
| 1900–1924 | 1,891,190 | 9.3% | 42.1% | 48.7% | 14 | 13 |
| 1925–1949 | 1,127,662 | 7.1% | 44.9% | 48.0% | 14 | 12 |
| 1950–1974 | 105,051 | 10.3% | 41.5% | 48.2% | 14 | 12 |
| 1975–1999 | 107,852 | 9.8% | 38.6% | 51.6% | 15 | 13 |
| 2000–2024 | 623,625 | 4.2% | 24.2% | 71.6% | 20 | 18 |

### 7.4 Key differences vs. v1

- **Era pattern preserved.** The pre-1750 long-title dominance (median 32–52, >79% long) and the post-1775 shortening are reproduced — confirming the effect is a real corpus-historical signal, not an artifact of the old corpus construction.
- **Absolute medians higher.** xlm-roberta BPE splits compound German words into 2–4 subwords each; spaCy splits on whitespace/punctuation only. The ratio between eras is more meaningful than the absolute values.
- **Long-title share inflated.** 52.5% long vs. 24.5% in v1, driven by BPE fragmentation. The p25/p75 threshold pair (4/14) must be recalibrated: v2 p25 = 8, p75 = 27.
- **Short% collapses to ~9%.** In v1, "short" (≤4 spaCy tokens) caught many 1–3 word titles; xlm-roberta produces ≥5 pieces for most such titles, so the short category shrinks substantially.

### 7.5 Implications

- **Threshold recalibration needed** before using length categories in SR-08 gold set stratification: replace (≤4 / 5–14 / >14) with (≤8 / 9–27 / >27) or recompute from v2 percentiles.
- **Latin sub-corpus** (493,712 records, 5.4%) should be faceted separately in era analysis — Latin titles have higher BPE fragmentation and different length characteristics than German-family titles.

---

## 6. References

The post-1775 title-length shift is attributed to a publishing convention change (early modern → modern title-page norms), not to cataloging standardization. The following are high-confidence anchors for that claim:

- **Reinhard Wittmann, *Geschichte des deutschen Buchhandels* (2nd ed., C.H. Beck, 1999), p. 122.** The standard history of the German book trade. Chapter IV ("Die Entstehung des modernen Buchhandels: Nettohandel, Nachdruck, Reformversuche") documents the decline of Latin in German book production using *Meßnovitäten* (Leipzig fair new titles): 27.7% Latin in 1740 → 14.25% in 1770 → 3.97% in 1800. *Relevant because:* Latin scholarly titles (*dissertatio*, *tractatus de*, ablative constructions) are structurally long. Their displacement from 27.7% to 3.97% of production between 1740 and 1800 directly depresses median token counts in the 1775–1799 bucket. This is an indirect but quantitatively grounded mechanism for the length drop — the inference is transparent (structural property of Latin title types + documented production share) even though Wittmann does not state the title-length consequence. Provides periodization (1760s–1800) and mechanism. See full note: [wittmann1999-geschichte-buchhandels.md](../literature/wittmann1999-geschichte-buchhandels.md).

- **Georg Jäger (ed.), *Geschichte des deutschen Buchhandels im 19. und 20. Jahrhundert*, vol. 1 (MVB, 2001).** Multi-volume institutional history of the German book trade in the modern period. Documents the consolidation of standardized title and imprint conventions through the 19th century, including the separation of title, subtitle, and publication data into distinct bibliographic fields. *Relevant because:* explains the further shortening visible in the 1825–1924 period and the structural reason `all_tokens` stabilizes at median 6–9 — subtitle and publisher information migrate out of the title string. ⚠️ *Not yet verified against specific pages — cited for context only.*

> **Note on citation strategy:** The post-1775 token-length drop is reported as an empirical observation from `DF_DE_TITLES`; the quantitative evidence is from the corpus itself. Wittmann (1999, p. 122) provides an indirect but quantitatively grounded mechanism (Latin production share decline). No source making the title-length claim explicitly has been identified; none is required for the paper's argument. For a dedicated citation on early modern German title-page conventions, the *Archiv für Geschichte des Buchwesens* remains the primary journal to search.

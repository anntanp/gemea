# GeMeA — NER for Bibliographic Title Extraction

Context: NER is the **fallback** in `link_gnd_works.py` for records without ISBD markers. The primary extractor is the rule-based ISBD parser. NER only runs when that fails.

**Scale of the fallback**: analysis of 115K Goethe-Faust DDB items ([isbd-title-analysis.md](../../goethe-faust/notes/isbd-title-analysis.md)) shows only **~29% of titles carry any ISBD pattern**, meaning NER applies to ~71% of records — the majority, not a small edge case. The dominant ISBD signal is ` :` (18%); the ` / ` split used by the parser appears in only 2.1% of titles. These figures are from one DDB provider subset and may vary across the full corpus.

Target label set: `TITLE`, `OTHER_TITLE`, `PERSON`, `TRANSLATOR`, `PARALLEL_TITLE`, `LANGUAGE`, `MEDIUM`, `EDITION`, `PUBLISHER`, `PLACE`, `YEAR`, `SERIES`, `VOLUME`.

---

## 1. Summary

| Section | What it covers |
|---|---|
| [3. FRBR label scope](#3-frbr-label-scope) | Label definitions organised by FRBR level (Work, Expression, Manifestation) |
| [4. Historical language scope](#4-historical-language-scope) | Risk assessment for pre-modern German and Latin titles; impact on model choice |
| [5. Model options](#5-model-options) | Comparison table: spaCy, Flair, gbert, xlm-roberta, LLM, NuNER Zero, GLiNER, GROBID |
| [6. NuNER Zero — zero-shot NER](#6-nunner-zero--zero-shot-ner-current-recommendation) | Current recommendation: usage code, merge logic, evaluation requirement |
| [7. LLM options at inference time](#7-llm-options-at-inference-time) | Cost/effort comparison for all-NER-record inference paths |
| [8. If no labeled training data is available](#8-if-no-labeled-training-data-is-available) | Silver labeling from ISBD pipeline; LLM one-time labeler; distant supervision |
| [9. Available datasets for fine-tuning](#9-available-datasets-for-fine-tuning) | empathyai/books-ner, HIPE-2022, CLEF-HIPE-2020, GermEval 2014 |
| [10. Decision](#10-decision) | Recommended path: NuNER Zero → LLM labeling → xlm-roberta fine-tune |

---

## 2. Open questions

**SR** = Study/Research question. Numbered in discovery order; not all will appear in the paper.

| ID | Title | Status | Blocks |
|---|---|---|---|
| [SR-01](#21-sr-01--isbd-signal-coverage-corpus-wide) | ISBD signal coverage (corpus-wide) | ✅ Resolved | — |
| [SR-02](#22-sr-02--isbd-parser-split-priority) | ISBD parser split priority | ✅ Resolved | — |
| [SR-03](#23-sr-03--silver-label-quality-and-false-positive-rate) | Silver label quality and false positive rate | 🔲 Open | [SR-08](#28-sr-08--nunner-zero-evaluation) |
| [SR-04](#24-sr-04--translator--person-disambiguation) | TRANSLATOR / PERSON disambiguation | 🔲 Open | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-05](#25-sr-05--trailing-period-noise) | Trailing period noise | 🔲 Open | — |
| [SR-06](#26-sr-06--historical-and-latin-title-scope) | Historical and Latin title scope | 🔲 Open | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-07](#27-sr-07--gold-set-composition) | Gold set composition | 🔲 Open | [SR-08](#28-sr-08--nunner-zero-evaluation) |
| [SR-08](#28-sr-08--nunner-zero-evaluation) | NuNER Zero evaluation | 🔲 Open — blocked on SR-07 | — |
| [SR-09](#29-sr-09--frbr-metric-scope-for-paper) | FRBR metric scope for paper | 🔲 Open | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-10](#210-sr-10--df_de_titles-source-and-title-length-scope) | DF_DE_TITLES source and title-length scope | ✅ Resolved | — |

### 2.1 SR-01 — ISBD signal coverage (corpus-wide)
**Status:** Resolved — [isbd-field-rating.md](isbd-field-rating.md)
- DF_DE_TITLES (4.47M): 20.2% have ` :`, 0.8% have ` /`, 14.6% have a year, 3.6% have an edition keyword
- Area separator `. -` present in only **1.2%** of records (53k) — structural tier is limited; heuristic tier carries 99% of silver candidates
- Tier 2 silver (structural, multi-field): **4,613 records** (0.1%)
- Tier 1 silver (heuristic, partial): **335,524 records** (7.5%)

### 2.2 SR-02 — ISBD parser split priority
**Status:** Resolved
- ` /` (SoR) appears in only 0.8% of titles; ` :` (subtitle) at 20.2% is the dominant title-area signal
- Parser must prioritise ` :` splitting for `OTHER_TITLE` / `TITLE` boundary, not ` /`

### 2.3 SR-03 — Silver label quality and false positive rate
**Status:** Open — blocked on validation
- Tier-2 labels are structurally derived (`. -` area separator present) — expected high precision
- Tier-1 labels use heuristic whole-string patterns — false positive rate unknown for ` :`, ` /`, YEAR
- **Action:** run `scripts/validate_heuristic_fields.py` (200-record stratified sample); accept tier-1 for augmentation only if false positive rate < 15% per field

### 2.4 SR-04 — TRANSLATOR / PERSON disambiguation
**Status:** Open
- ` /` fires for both PERSON (author) and TRANSLATOR; keyword matching ("übersetzt von", "Übers.:", "transl.") provides first-pass split
- **Action:** validate keyword heuristic precision on 100-record sample of ` /`-flagged titles before using TRANSLATOR as a distinct silver label

### 2.5 SR-05 — Trailing period noise
**Status:** Open
- Trailing `.` fires in 17.5% of corpus but also hits abbreviations (`Hrsg.`, `Bd.`) and ordinals — upper bound, not a clean signal
- **Action:** before using as silver label signal, require co-occurrence with another ISBD marker, or strip a curated German abbreviation list

### 2.6 SR-06 — Historical and Latin title scope
**Status:** Open
- 92.4% of records (tier 0) have no ISBD signals and fall to NER fallback — unknown share are Latin or pre-modern German
- **Action:** sample 200 records from `dc_type` = Leichenpredigt / pre-1800 Monografie; estimate Latin / Early Modern German proportion to determine how much historical signal is needed in training

### 2.7 SR-07 — Gold set composition
**Status:** Open — blocks SR-08
- **Requirement:** ~500 manually annotated records stratified by: era (modern / 19th c. / pre-1800 / Latin), silver tier (2 / 1 / 0), and `dc_type`
- Must cover tier-0 fallback records (the NER majority path) not just ISBD-structured ones

### 2.8 SR-08 — NuNER Zero evaluation
**Status:** Open — blocked on SR-07
- **Requirement:** run NuNER Zero zero-shot on 500 stratified fallback records; assess TITLE and PERSON F1 on gold set
- **Decision gate:** precision ≥ threshold → use zero-shot; else → LLM labeling + fine-tune `xlm-roberta-base` on silver + LLM-labeled set

### 2.9 SR-09 — FRBR metric scope for paper
**Status:** Open
- **Requirement:** confirm which FRBR levels the paper's quality metrics cover — Work (TITLE, PERSON) only, or also Expression (TRANSLATOR, PARALLEL_TITLE, MEDIUM) and Manifestation (PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME)
- Determines which label types must appear in the gold set and which NER labels are in scope for the evaluation section

### 2.10 SR-10 — DF_DE_TITLES source and title-length scope
**Status:** Partially resolved — provenance traced; length distribution open

**Provenance (resolved).** `DF_DE_TITLES` was traced via `grep -rHn "pkl_vars.*DF_DE_TITLES" *.ipynb` across the notebook archive. The variable originates in `2023.11 NER.ipynb` — the earliest notebook in the series and the one that defines the construction. `2024.01 MT-QA.ipynb` produced a separately timestamped pickle (`DF_DE_TITLES_20240125b.pkl`) but is not the source. The definition from `2023.11 NER.ipynb`, consistent with `2023.12 Relation Extraction.ipynb`, is:

> "4,477,641 objects are titles of all TEXT objects, tagged to be in German (`dc:language`) and identified by `langid` to be in German."

Selection criteria from the `2023.11 NER.ipynb` / `2024.01 MT-QA.ipynb` shared header:

| | DDB | No. Records |
|---|---|---|
| Total Titles | | 16,805,998 |
| TEXT | | 8,402,999 |
| Languages | | 236 |
| No Language Tags | | 1,521,242 (18.10%) |
| Valid HTYPES (% of TEXT) | | 1,812,559 (21.57%) |
| Languages of Valid HTYPES | | 224 |
| No Language Tags (% of VALID) | | 384,405 (21.21%) |
| **Titles tagged+ident as 'DE'** | | **4,477,641 (53.29%)** |

`DF_DE_TITLES` is therefore a **language filter** applied to the full DDB TEXT object dump: records where `dc:language` is tagged German AND `langid` confirms German. It is not filtered by `dc:type`, provider, or era. Tokenization in the source notebook uses `spacy.load` (model unspecified in the trace).

**Implication for generalizability.** The corpus includes both long ISBD strings and short bare-title strings across all eras and `dc:type` values. No length or era filter was applied. ISBD coverage figures (20.2% ` :`, 0.8% ` /`) reflect this broad population.

**Token-count distribution (resolved).** `scripts/explore_token_distribution.py` — raw distribution of `all_tokens` and `content_tokens` across all 4,477,780 titles. Output: `output/fig_token_distribution.png`, `output/token-distribution.json`.

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

Value-count histogram (all_tokens 1–20): the distribution is roughly flat from 1–9 tokens (5–8% each), with a peak at 4 tokens (8.0%), then declines steadily. Notable bump at 20 tokens (1.9% vs. 1.3% at 19 and 1.0% at 21) — likely a truncation artifact in the source data.

Threshold decision: **quartiles (≤4 / 5–14 / >14)** — p25 = 4, p75 = 14, equal outer groups. See [title-length-thresholds.md](title-length-thresholds.md) for the full empirical basis, alternatives considered, and rejection rationale.

**Title-length distribution (resolved).** `scripts/analyse_title_lengths.py` — token counts from pre-computed `all_tokens` (includes stopwords) and `content_tokens` (stopwords removed) columns; year from `dates` column (1400–2029), falling back to title regex for nulls. Outputs: `output/fig_title_lengths.png`, `output/title-length-analysis.json`.

Year coverage: 89.4% from `dates` column, 1.0% from title fallback, **9.6% no year** (429,097 titles).

Overall distribution (all 4,477,780 titles, by `all_tokens` including stopwords; thresholds from [title-length-thresholds.md](title-length-thresholds.md)):

| Category | Threshold | Count | % |
|---|---|---|---|
| Short | ≤ 4 tokens (p25) | 1,269,034 | 28.3% |
| Medium | 5–14 tokens (p25–p75) | 2,110,610 | 47.1% |
| Long | > 14 tokens (p75) | 1,098,136 | 24.5% |
| **Median all_tokens** | | **8** | |
| **Median content_tokens** | | **5** | |

Distribution per 25-year bucket (N = 4,048,683 titles with year; 1500+):

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

**Key findings:**
- Pre-1750 titles are dominated by long strings: 42–50% long (>14 tokens), median `all_tokens` 12–15 — full ISBD-qualified bibliographic descriptions, not bare titles.
- Post-1775: sharp shift — median drops to 6–9 tokens; long falls to 12–24%. Short (≤4) rises to 35–38% in the 1875–1949 period.
- 2000–2024 reverses: only 9% short, 62% medium, 29% long — digital-born metadata with richer structured descriptions.
- `content_tokens` (stopwords removed) runs consistently ~3 tokens below `all_tokens` (stopwords included) median — stable stopword overhead across all eras.
- **Implication for SR-07 (gold set):** stratify by length as well as era; pre-1750 long-form records stress the NER model differently from the short modern majority. The 9.6% no-year group needs separate treatment — sample by `dc_type` or `silver_tier` instead.

---

## 3. FRBR label scope

Labels are organised by FRBR level. The goal is to extract enough structure to distinguish Works, Expressions, and Manifestations in the KG.

**Work** — the abstract intellectual creation

| Label | What it marks | Typical ISBD / catalog cue |
|---|---|---|
| `TITLE` | Proper title | Before ` :` or ` /`; primary string |
| `OTHER_TITLE` | Subtitle / other title information | After ` :` |
| `PERSON` | Author / creator | After ` /`; "von", "hrsg. von", "ed. by" |

**Expression** — a particular realization of the Work (language, translator, medium)

| Label | What it marks | Typical ISBD / catalog cue |
|---|---|---|
| `TRANSLATOR` | Translator name | After ` /`; "übersetzt von", "Übers.:", "transl. by" |
| `TRANSLATION` | Translation source phrase | "Aus dem Englischen", "in deutscher Übersetzung", "traduit de" |
| `PARALLEL_TITLE` | Title in another language | After ` =` |
| `LANGUAGE` | Language of this expression | Explicit language name when stated in the title field |
| `MEDIUM` | Notational / physical medium | "Klavierauszug", "Partitur", "Textbuch", "Hörbuch" |

**Manifestation** — a specific published edition

| Label | What it marks | Typical ISBD / catalog cue |
|---|---|---|
| `EDITION` | Edition statement | "2. Aufl.", "Neuausg.", "rev. ed.", "erw. Fassung" |
| `PLACE` | Place of publication | Before `:` in `. - Place : Publisher` imprint block |
| `PUBLISHER` | Publisher name | After `:` in imprint block; "Verlag", known publisher names |
| `YEAR` | Year of publication | Trailing 4-digit year; after `,` in imprint |
| `SERIES` | Series title | Inside `( )` after imprint |
| `VOLUME` | Volume / part number | "Bd.", "Teil", "Vol.", "Heft", "Nr." |

**Notes on Expression vs. Manifestation boundary.** A title string rarely contains explicit language codes (those live in MARC 041); `LANGUAGE` and `TRANSLATION` are therefore sparse but high-value when present. `PARALLEL_TITLE` (` =` cue) and `TRANSLATOR` are more common and are the primary Expression-distinguishing signals available in the title field. `MEDIUM` is relevant for music scores and audio items in the DDB.

---

## 4. Historical language scope

DDB objects span several centuries. Title content may be in modern German, Early Modern German, Middle High German, Latin, or other languages. This affects model choice.

**Key distinction**: the NER task is structural, not semantic. The model identifies *which span is the title* within a catalog string — it does not need to understand the title. Catalog records follow modern ISBD conventions regardless of object era, so:

- **ISBD parsing (primary)** — unaffected; punctuation-based, language-agnostic
- **Silver labeling** — unaffected; labels derive from ISBD structure, not title content
- **NER fallback** — affected for the ~71% of records without ISBD markers

For the fallback, historical language introduces real risk:

| Scenario | Risk | Notes |
|---|---|---|
| Modern German catalog record, historical title | Low | Surrounding catalog text is modern; only the title span is archaic |
| Early Modern / Middle High German title | Medium | Tokenization degrades; subword vocab misses historical orthography |
| Latin titles | Medium | Common for pre-18th century scholarly works; monolingual German models fail |
| Mixed-language catalog strings | Medium | Some DDB providers mix German and Latin in descriptions |

---

## 5. Model options

| Model | Type | Fine-tune needed? | TITLE OOB | PERSON OOB | Historical/Latin | Notes |
|---|---|---|---|---|---|---|
| `xlm-roberta-large` | Transformer | Yes | No | No | Good | **Recommended base for fine-tuning** — multilingual training covers Latin and historical text better than monolingual alternatives |
| spaCy `de_core_news_lg` | Transformer | No | No | Yes | Poor | Trained on modern German news; degrades on historical orthography and Latin |
| `flair/ner-german-large` | Stacked embeddings | No | No | Yes (PER) | Poor | CoNLL-2003 labels; same limitation as spaCy |
| `deepset/gbert-large` | BERT-large | Yes | No | No | Poor | Monolingual modern German; no off-the-shelf bibliographic NER |
| LLM (GPT-4o, Claude, Llama 3) | Generative | No | Yes | Yes | Good | Handles Latin and historical German well; too slow at 5–10M records but strong as a one-time labeler |
| **NuNER Zero** (`numind/NuNER_Zero`) | Zero-shot NER | No | Yes | Yes | Moderate | +3.1% F1 over GLiNER-large-v2.1; token classifier (handles arbitrarily long entities); same size, local CPU; **current SOTA in this category** |
| GLiNER (`gliner_multi-v2.1`) | Zero-shot NER | No | Yes | Yes | Moderate | NAACL 2024; span-based with configurable width; multilingual; slightly behind NuNER Zero on benchmarks |
| GROBID | Rule-based + CRF | No | Partial | Partial | Poor | Trained on scientific citations, not ISBD/library catalog — different domain; not recommended |

**Note on gbert-large**: was listed as the original plan but was never properly justified. Monolingual modern German is the wrong choice for a historically diverse corpus.

---

## 6. NuNER Zero — zero-shot NER (current recommendation)

[NuNER Zero](https://huggingface.co/numind/NuNER_Zero) (NuMind, 2024) is the current SOTA compact zero-shot NER model, outperforming GLiNER-large-v2.1 by +3.1% F1. Unlike GLiNER, it is a token classifier rather than span-based, so it handles arbitrarily long entities — relevant for verbose DDB title strings.

```python
from gliner import GLiNER

model = GLiNER.from_pretrained("numind/NuNerZero")

# Labels must be lower-cased
labels = [
    # Work
    "title", "other title", "person",
    # Expression
    "translator", "translation", "parallel title", "language", "medium",
    # Manifestation
    "edition", "publisher", "place", "year", "series", "volume",
]

text = "Faust drittes Buch von Goethe erschienen Weimar"
entities = model.predict_entities(text, labels)

# Merge adjacent tokens with the same label (token classifier output)
def merge_entities(entities, text):
    if not entities:
        return []
    merged = []
    current = entities[0]
    for nxt in entities[1:]:
        if nxt["label"] == current["label"] and nxt["start"] <= current["end"] + 1:
            current["text"] = text[current["start"]:nxt["end"]].strip()
            current["end"] = nxt["end"]
        else:
            merged.append(current)
            current = nxt
    merged.append(current)
    return merged

entities = merge_entities(entities, text)
# → [{"text": "Faust drittes Buch", "label": "title", "score": 0.91}, ...]
```

BERT-sized — runs on CPU, same deployment footprint as GLiNER. Zero-shot precision on DDB strings is unknown; **evaluate on ~500 stratified fallback records before committing** (see [SR-08](#28-sr-08--nunner-zero-evaluation)).

---

## 7. LLM options at inference time

NER applies to ~71% of records (~3.5–7M unique pairs after deduplication). LLM API at inference is expensive at this scale; local options are strongly preferred.

| Approach | Scale | Cost | Historical/Latin | Effort |
|---|---|---|---|---|
| **NuNER Zero** (local) | All NER records | Free | Moderate | Low — deploy and evaluate |
| **Local LLM** (Llama 3.1 8B) | All NER records | GPU infra only | Moderate | Medium |
| **LLM one-time labeler → fine-tune xlm-roberta** | Generate labels once | Low one-time API cost | Good | Medium |
| **Fine-tuned xlm-roberta-base** | All NER records | Cheap at inference | Good (if trained on historical) | High upfront |
| **LLM API at inference** (GPT-4o, Claude) | All NER records | ~$1,500–3,500 at full scale | Good | Low — but costly |

**Recommended path**: start with NuNER Zero on 500 stratified NER records. If precision is acceptable, done. If not, use an LLM to label a few thousand records and fine-tune `xlm-roberta-base` on that output.

---

## 8. If no labeled training data is available

**8.1 Silver labeling from the ISBD pipeline**

The ~28% of records where ISBD area structure is present (`has_dot_dash`) become auto-labeled training examples. Silver candidate selection is handled by `scripts/rate_isbd_fields.py` → `data/processed/isbd_field_ratings.csv`:

- **Silver tier 2** (primary): `has_dot_dash AND f_person AND ≥1 manifestation field` — structural annotation, multi-field spans; use as primary training set
- **Silver tier 1** (augmentation): `n_fields ≥ 3` or `(f_person AND f_year)` — partial annotation; validate ~200 records before use

See [isbd-field-rating.md](isbd-field-rating.md) for the full detection spec and [isbd-field-rating-adr.md](isbd-field-rating-adr.md) for design decisions.

ISBD pattern → NER label mapping across FRBR levels:

| ISBD pattern | Label(s) | Notes |
|---|---|---|
| Before ` :` or ` /` | `TITLE` | Primary title string |
| After ` :` | `OTHER_TITLE` | Subtitle / other title info |
| After ` =` | `PARALLEL_TITLE` | Expression-level; often a translation |
| After ` /`; no "übersetzt" keyword | `PERSON` | Statement of responsibility |
| After ` /`; "übersetzt von", "Übers.:", "transl. by" | `TRANSLATOR` | Expression-level |
| Span matching "Aus dem …", "in … Übersetzung", "traduit de" | `TRANSLATION` | Expression-level; sparse |
| Medium keyword ("Klavierauszug", "Partitur", "Textbuch", "Hörbuch") | `MEDIUM` | Expression-level; relevant for music/audio |
| Edition keyword before `. -` block | `EDITION` | "Aufl.", "Neuausg.", "rev. ed." |
| `. - Place :` block, first token(s) before `:` | `PLACE` | Manifestation-level |
| `. - Place :` block, after `:` up to `,` | `PUBLISHER` | Manifestation-level |
| Trailing 4-digit year or year after `,` | `YEAR` | Manifestation-level |
| `( Series ; N )` block, title part | `SERIES` | Manifestation-level |
| "Bd.", "Teil", "Vol.", "Heft", "Nr." + number | `VOLUME` | Manifestation-level |

TRANSLATOR disambiguation is the main ambiguity: the ` /` cue fires for both `PERSON` and `TRANSLATOR`; keyword matching ("übersetzt", "Übers.", "transl.") is sufficient for a first-pass split. Language-agnostic structurally — works for Latin and historical German titles. Fine-tune `xlm-roberta-base` on these labels. Evaluate on a manually checked gold set of ~500 records including historical and Latin examples.

**8.2 LLM as a one-time labeler**

Use GPT-4o or Claude to label a few thousand records. Handles Latin and historical German well. Fine-tune a smaller model on those outputs. Expensive per call but a one-time cost.

**8.3 Distant supervision (supplementary)**

For records where a GND Werk URI was confirmed via the local GND instance, the extracted title string is a positive `TITLE` example. Linked person GND URIs supply `PERSON` labels. Useful to augment silver labels, not sufficient alone.

---

## 9. Available datasets for fine-tuning

| Dataset | Labels | Language | Size | Relevance |
|---|---|---|---|---|
| [empathyai/books-ner-dataset](https://huggingface.co/datasets/empathyai/books-ner-dataset) | TITLE, AUTHOR | English | Project Gutenberg catalogues | Closest label match; English only — use for domain-transfer pretraining |
| [HIPE-2022 (ajmc)](https://github.com/hipe-eval/HIPE-2022-data) | Fine-grained bibliographic refs | German, French, English | ~10K tokens | Historical document NER with bibliographic references; German included — more relevant given historical scope |
| [CLEF-HIPE-2020](https://zenodo.org/record/3836029) | PER, ORG, LOC, PROD (work titles) | German, French, English | Historical newspapers | PROD label covers work titles; 19th-century orthography — relevant for historical German |
| [GermEval 2014](https://sites.google.com/site/germeval2014ner/) | PER, ORG, LOC, OTH | German | ~31K sentences | Modern German only; useful only for PERSON transfer |

**Recommended fine-tuning path**:
1. Pretrain on `empathyai/books-ner-dataset` for TITLE/AUTHOR signal (domain transfer)
2. Fine-tune on silver-labeled DDB records
3. Supplement with HIPE-2022 ajmc and CLEF-HIPE-2020 for historical German and Latin signal
4. Evaluate on a gold set stratified by era (modern, 19th c., pre-1800, Latin)

---

## 10. Decision

1. **Try NuNER Zero first** — current SOTA compact zero-shot NER, no training data, runs locally, handles arbitrarily long spans. Evaluate on 500 stratified fallback records (see [SR-08](#28-sr-08--nunner-zero-evaluation)).
2. **If NuNER Zero precision is insufficient**, use an LLM to label those same records and fine-tune `xlm-roberta-base` on that output.
3. **Silver labeling** (ISBD-derived) augments any fine-tuning — language-agnostic, large volume, no annotation cost.
4. Use `xlm-roberta` over any monolingual German model — the historical and Latin scope makes multilingual pretraining essential.
5. **GROBID**: trained on scientific citations, not library catalog records — not recommended.

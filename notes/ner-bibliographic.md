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
| [SR-03](#23-sr-03--silver-label-quality-and-false-positive-rate) | Silver label quality and false positive rate | ✅ Resolved | [SR-08](#28-sr-08--nunner-zero-evaluation) |
| [SR-04](#24-sr-04--translator--person-disambiguation) | TRANSLATOR / PERSON disambiguation | ✅ Resolved | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-05](#25-sr-05--trailing-period-noise) | Trailing period noise | ✅ Resolved | — |
| [SR-06](#26-sr-06--historical-and-latin-title-scope) | Historical and Latin title scope | ✅ Resolved | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-07](#27-sr-07--gold-set-composition) | Gold set composition | 🔲 Open | [SR-08](#28-sr-08--nunner-zero-evaluation) |
| [SR-08](#28-sr-08--nunner-zero-evaluation) | NuNER Zero evaluation | 🔲 Open — blocked on SR-07 | — |
| [SR-09](#29-sr-09--frbr-metric-scope-for-paper) | FRBR metric scope for paper | 🔲 Open | [SR-07](#27-sr-07--gold-set-composition) |
| [SR-10](#210-sr-10--df_de_titles-source-and-title-length-scope) | DF_DE_TITLES source and title-length scope | ✅ Resolved — [de-titles-distribution.md](ner/sr10_de-titles-distribution.md) | — |

### 2.1 SR-01 — ISBD signal coverage (corpus-wide)
**Status:** Resolved — [isbd-field-rating.md](ner/sr01_isbd-field-rating.md)
- DF_DE_TITLES (4.47M): 20.2% have ` :`, 0.8% have ` /`, 14.6% have a year, 3.6% have an edition keyword
- Area separator `. -` present in only **1.2%** of records (53k) — structural tier is limited; heuristic tier carries 99% of silver candidates
- Tier 2 silver (structural, multi-field): **4,613 records** (0.1%)
- Tier 1 silver (heuristic, partial): **335,524 records** (7.5%)

### 2.2 SR-02 — ISBD parser split priority
**Status:** Resolved
- ` /` (SoR — Statement of Responsibility: the ISBD punctuation that separates the title from the creator/contributor field, e.g. *Faust / von Goethe*) appears in only 0.8% of titles; ` :` (subtitle) at 20.2% is the dominant title-area signal
- Parser must prioritise ` :` splitting for `OTHER_TITLE` / `TITLE` boundary, not ` /`

### 2.3 SR-03 — Silver label quality and false positive rate
**Status:** Resolved — see [silver-label-fp-review.md](ner/sr03_silver-label-fp-review.md)

- 81 of 200 sampled heuristic-tier records (40.5%) have at least one false positive
- **Excluded:** `f_parallel` (~80% FP), `f_edition` (~83% FP)
- **Post-filter required:** `f_person` (~36% FP), `f_person_compound` (~29% FP)
- **Accepted:** `f_year`, `f_other_title`, `f_publisher`, `f_series`, `f_volume` (all < 15% FP)
- Pre-1750 author placement (name before title, not after ` /`) is a structural false-negative blind spot for `f_person` — flagged for SR-07

### 2.4 SR-04 — TRANSLATOR / PERSON disambiguation
**Status:** Resolved — see [translator-person-disambiguation.md](ner/sr04_translator-person-disambiguation.md)

- Only 35% of `f_person` records are true author SoRs; 41% are non-SoR false positives, 19% corporate bodies, 5% editors
- **0 true translators** in 100-record sample — TRANSLATOR label not viable from title strings
- EDITOR detection: 0 F1; `(Hg.)` suffix and body-text `bearb.` missed by heuristic
- **Decision:** `f_person` sub-classified following the ISBD/RDA agent model — person (`f_resp_person`) | collective agents (`f_resp_org` corporate body, `f_resp_family` family) | role qualifier (`f_resp_editor`) | non-SoR (`f_resp_other`); TRANSLATOR and EDITOR dropped as silver label targets
- **`f_resp_org` introduced** for the 19% of ` /` records where the responsible entity is a corporate body (government agency, statistical office, university, etc.) — collective agent, treated as a distinct CORPORATE entity class, not a false positive; `f_resp_family` added for family name entries (not yet validated)

### 2.5 SR-05 — Trailing period noise
**Status:** Resolved — see [trailing-period-noise.md](ner/sr05_trailing-period-noise.md)

- 200-record stratified sample of titles ending with `.` (pool: 875,349 = 19.5% of corpus)
- True class distribution: NATURAL 74%, NOISE 10%, ORDINAL 8%, ISBD_CLOSE 7%, ABBREV 1%
- **FP rate: 93%** — far above the 15% acceptance threshold
- All 14 true ISBD_CLOSE records already captured by `has_dot_dash` (11) or year + ` :` / ` /` co-occurrence (3) — trailing `.` adds no new detection power
- **Decision:** exclude trailing `.` as a standalone heuristic-tier signal; the `has_dot_dash` flag already covers the structural tier completely

### 2.6 SR-06 — Historical and Latin title scope
**Status:** Resolved — see [sr06_historical-scope.md](ner/sr06_historical-scope.md)

- 200-record stratified sample: 100 Leichenpredigt + 100 pre-1800 Monografie
- **True-class distribution: EARLY_MODERN_DE 93%, GERMAN 6%, LATIN 0.5%, OTHER 0.5%**
- **LATIN heuristic: 83% FP rate** — `Anno`, `Christi`, `Jesu`, `Doctor` are standard German Protestant/academic vocabulary; embedding does not make the title Latin
- EARLY_MODERN_DE heuristic: F1 = 0.95; main FP source is `[ck]h\w+` cluster firing on ordinary German words ("Heilige", "höffliche")
- **Decision D1:** drop LATIN as a heuristic class for this stratum — true prevalence ~0.5%, no reliable heuristic signal; manual identification sufficient
- **Decision D2/D3:** restrict `[ck]h\w+` to word-initial position (≥5 chars); remove `Herrn` from early modern markers
- **Impact on model selection:** no Latin NER capability needed; Early Modern German (1500–1750) is the primary historical challenge — long title-page transcriptions, pre-title author placement, non-standard orthography
- **Gold set implication:** no dedicated Latin stratum; add pre-1700 stratum (Leichenpredigt + legal/administrative Monografie) as the historical register proxy

### 2.7 SR-07 — Gold set composition
**Status:** Open — blocks SR-08
- **Requirement:** ~500 manually annotated records stratified by: era (modern / 19th c. / 1700–1800 / pre-1700), silver tier (2 / 1 / 0), and `dc_type`
- Must cover tier-0 fallback records (the NER majority path) not just ISBD-structured ones
- **No Latin stratum (from SR-06):** true Latin prevalence is ~0.5% — too rare to stratify; identify manually if encountered. Pre-1700 stratum (Leichenpredigt + legal/administrative Monografie) is the historical register proxy.
- **Pre-1750 PERSON annotation (from SR-03):** the ` /` SoR heuristic is a systematic false negative for pre-1750 titles — authors appear before the work title, not after ` /`. Gold set annotators must not rely on the SoR position as a cue for the `PERSON` label in this stratum; author spans need to be identified from the opening name + credentials pattern (e.g. *Firstname Lastname, [role/title], [work title]*). This affects annotation guidelines and model evaluation: PERSON F1 on the pre-1750 stratum should be tracked separately from the modern stratum. See [silver-label-fp-review.md §5](ner/sr03_silver-label-fp-review.md#5-pre-1750-false-negatives--author-before-title) for examples.

### 2.8 SR-08 — NuNER Zero evaluation
**Status:** Open — blocked on SR-07
- **Requirement:** run NuNER Zero zero-shot on 500 stratified fallback records; assess TITLE and PERSON F1 on gold set
- **Decision gate:** precision ≥ threshold → use zero-shot; else → LLM labeling + fine-tune `xlm-roberta-base` on silver + LLM-labeled set

### 2.9 SR-09 — FRBR metric scope for paper
**Status:** Open
- **Requirement:** confirm which FRBR levels the paper's quality metrics cover — Work (TITLE, PERSON) only, or also Expression (TRANSLATOR, PARALLEL_TITLE, MEDIUM) and Manifestation (PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME)
- Determines which label types must appear in the gold set and which NER labels are in scope for the evaluation section

### 2.10 SR-10 — DF_DE_TITLES source and title-length scope
**Status:** Resolved — see [de-titles-distribution.md](ner/sr10_de-titles-distribution.md)

- **Provenance:** `DF_DE_TITLES` originates in `2023.11 NER.ipynb`; `2024.01 MT-QA.ipynb` produced the dated pkl only. Corpus = 4,477,780 German-tagged DDB TEXT objects (`dc:language` + `langid` = German); no filter by `dc:type`, provider, or era. `all_tokens` = spaCy `de_core_news_sm` token count including stopwords and punctuation; `content_tokens` = stopwords removed, punctuation retained.
- **Token thresholds:** quartiles — short ≤4 (p25), medium 5–14, long >14 (p75). See [title-length-thresholds.md](ner/sr10_title-length-thresholds.md).
- **Length by year:** pre-1750 dominated by long strings (42–50%, median 12–15 tokens); post-1775 shift to median 6–9; 2000–2024 reversal (62% medium). 9.6% of titles have no year.
- **Implication for SR-07:** stratify gold set by length and era; pre-1750 long-form records stress the NER model differently from the short modern majority.

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

| Model | Params | Type | Fine-tune needed? | TITLE OOB | PERSON OOB | Historical/Latin | Notes |
|---|---|---|---|---|---|---|---|
| `xlm-roberta-large` | 560M | Transformer | Yes | No | No | Good | **Recommended base for fine-tuning** — multilingual (100 langs); dominant backbone in HIPE-2022 and CLEF-HIPE-2020 top systems (see §9) |
| `xlm-roberta-base` | 270M | Transformer | Yes | No | No | Good | Lighter alternative to XLM-R large; same multilingual coverage, lower capacity |
| `mdeberta-v3-base` | 86M | Transformer | Yes | No | No | Good | Multilingual DeBERTa (100 langs); disentangled attention + ELECTRA pretraining; competitive with XLM-R base; **no large multilingual variant available** — ceiling lower than XLM-R large |
| `deberta-v3-large` | 304M | Transformer | Yes | No | No | ❌ N/A | **English-only** — not applicable for German/multilingual use |
| spaCy `de_core_news_lg` | — | Transformer | No | No | Yes | Poor | Trained on modern German news; degrades on historical orthography |
| `flair/ner-german-large` | — | Stacked embeddings | No | No | Yes (PER) | Poor | CoNLL-2003 labels; same limitation as spaCy |
| `deepset/gbert-large` | 336M | BERT-large | Yes | No | No | Poor | Monolingual modern German — wrong choice for historically diverse corpus |
| LLM (GPT-4o, Claude, Llama 3) | — | Generative | No | Yes | Yes | Good | Handles historical German well; too slow at 5–10M records but strong as a one-time labeler |
| **NuNER Zero** (`numind/NuNER_Zero`) | ~180M | Zero-shot NER | No | Yes | Yes | Moderate | +3.1% F1 over GLiNER-large-v2.1; token classifier (handles arbitrarily long entities); local CPU; **current SOTA zero-shot** |
| GLiNER (`gliner_multi-v2.1`) | ~200M | Zero-shot NER | No | Yes | Yes | Moderate | NAACL 2024; span-based; multilingual; slightly behind NuNER Zero |
| GROBID | — | Rule-based + CRF | No | Partial | Partial | Poor | Trained on scientific citations, not ISBD/library catalog — different domain; not recommended |

**On DeBERTa vs XLM-R:** `deberta-v3-large` outperforms `xlm-roberta-large` on English NER benchmarks, but is English-only. The multilingual DeBERTa (`mdeberta-v3-base`) is only available at base size — so the choice for this task is effectively `xlm-roberta-large` (560M, multilingual large) vs `mdeberta-v3-base` (86M, multilingual base). XLM-R large is the stronger model and the documented choice for historical multilingual NER. Both should be benchmarked in SR-08 if fine-tuning is pursued.

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

See [isbd-field-rating.md](ner/sr01_isbd-field-rating.md) for the full detection spec and [isbd-field-rating-adr.md](ner/sr01_isbd-field-rating-adr.md) for design decisions.

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
| [HIPE-2022 (ajmc)](https://github.com/hipe-eval/HIPE-2022-data) | Fine-grained bibliographic refs | German, French, English | ~10K tokens | Historical document NER with bibliographic references; German included. Top systems used `xlm-roberta-large` as backbone. Ehrmann et al. (2022) ⚠️ *verify citation* |
| [CLEF-HIPE-2020](https://zenodo.org/record/3836029) | PER, ORG, LOC, PROD (work titles) | German, French, English | Historical newspapers | PROD label covers work titles; 19th-century orthography. XLM-R large dominant in top submissions. Ehrmann et al. (2020) ⚠️ *verify citation* |
| [GermEval 2014](https://sites.google.com/site/germeval2014ner/) | PER, ORG, LOC, OTH | German | ~31K sentences | Modern German only; useful only for PERSON transfer |

**Recommended fine-tuning path**:
1. Pretrain on `empathyai/books-ner-dataset` for TITLE/AUTHOR signal (domain transfer)
2. Fine-tune on silver-labeled DDB records
3. Supplement with HIPE-2022 ajmc and CLEF-HIPE-2020 for historical German and Latin signal
4. Evaluate on a gold set stratified by era (modern, 19th c., 1700–1800, pre-1700) — no dedicated Latin stratum needed (SR-06: ~0.5% prevalence)

---

## 10. Decision

1. **Try NuNER Zero first** — current SOTA compact zero-shot NER, no training data, runs locally, handles arbitrarily long spans. Evaluate on 500 stratified fallback records (see [SR-08](#28-sr-08--nunner-zero-evaluation)).
2. **If NuNER Zero precision is insufficient**, use an LLM to label those same records and fine-tune `xlm-roberta-large` on that output. Benchmark `mdeberta-v3-base` alongside as a lighter-weight alternative.
3. **Silver labeling** (ISBD-derived) augments any fine-tuning — language-agnostic, large volume, no annotation cost. Note: silver set covers modern records; pre-1750 stratum requires gold or LLM labels (SR-06).
4. Use `xlm-roberta-large` over any monolingual German model — multilingual pretraining is essential for Early Modern German. `deberta-v3-large` is English-only and not applicable; `mdeberta-v3-base` is the multilingual DeBERTa but only available at base size.
5. **GROBID**: trained on scientific citations, not library catalog records — not recommended.

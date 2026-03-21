# GeMeA — NER for Bibliographic Title Extraction

Context: NER is the **fallback** in `link_gnd_works.py` for records without ISBD markers. The primary extractor is the rule-based ISBD parser. NER only runs when that fails.

**Scale of the fallback**: analysis of 115K Goethe-Faust DDB items ([isbd-title-analysis.md](../../goethe-faust/notes/isbd-title-analysis.md)) shows only **~29% of titles carry any ISBD pattern**, meaning NER applies to ~71% of records — the majority, not a small edge case. The dominant ISBD signal is ` :` (18%); the ` / ` split used by the parser appears in only 2.1% of titles. These figures are from one DDB provider subset and may vary across the full corpus.

Target label set: `TITLE`, `OTHER_TITLE`, `PERSON`, `TRANSLATOR`, `PARALLEL_TITLE`, `LANGUAGE`, `MEDIUM`, `EDITION`, `PUBLISHER`, `PLACE`, `YEAR`, `SERIES`, `VOLUME`.

---

## FRBR label scope

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

## Historical language scope

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

## Model options

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

## NuNER Zero — zero-shot NER (current recommendation)

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

BERT-sized — runs on CPU, same deployment footprint as GLiNER. Zero-shot precision on DDB strings is unknown; **evaluate on ~500 stratified fallback records before committing**.

---

## LLM options at inference time

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

## If no labeled training data is available

**1. Silver labeling from the ISBD pipeline**
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

**2. LLM as a one-time labeler**
Use GPT-4o or Claude to label a few thousand records. Handles Latin and historical German well. Fine-tune a smaller model on those outputs. Expensive per call but a one-time cost.

**Distant supervision (supplementary)**
For records where a GND Werk URI was confirmed via the local GND instance, the extracted title string is a positive `TITLE` example. Linked person GND URIs supply `PERSON` labels. Useful to augment silver labels, not sufficient alone.

---

## Available datasets for fine-tuning

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

## Decision

1. **Try NuNER Zero first** — current SOTA compact zero-shot NER, no training data, runs locally, handles arbitrarily long spans. Evaluate on 500 stratified fallback records.
2. **If NuNER Zero precision is insufficient**, use an LLM to label those same records and fine-tune `xlm-roberta-base` on that output.
3. **Silver labeling** (ISBD-derived) augments any fine-tuning — language-agnostic, large volume, no annotation cost.
4. Use `xlm-roberta` over any monolingual German model — the historical and Latin scope makes multilingual pretraining essential.
5. **GROBID**: trained on scientific citations, not library catalog records — not recommended.

---

## Open questions

| ID | Title | Status | Blocks |
|---|---|---|---|
| SR-01 | ISBD signal coverage (corpus-wide) | ✅ Resolved | — |
| SR-02 | ISBD parser split priority | ✅ Resolved | — |
| SR-03 | Silver label quality and false positive rate | 🔲 Open | SR-08 |
| SR-04 | TRANSLATOR / PERSON disambiguation | 🔲 Open | SR-07 |
| SR-05 | Trailing period noise | 🔲 Open | — |
| SR-06 | Historical and Latin title scope | 🔲 Open | SR-07 |
| SR-07 | Gold set composition | 🔲 Open | SR-08 |
| SR-08 | NuNER Zero evaluation | 🔲 Open — blocked on SR-07 | — |
| SR-09 | FRBR metric scope for paper | 🔲 Open | SR-07 |
| SR-10 | DF_DE_TITLES source and title-length scope | 🔲 Open | — |

---

### SR-01 — ISBD signal coverage (corpus-wide)
**Status:** Resolved — [isbd-field-rating.md](isbd-field-rating.md)
- DF_DE_TITLES (4.47M): 20.2% have ` :`, 0.8% have ` /`, 14.6% have a year, 3.6% have an edition keyword
- Area separator `. -` present in only **1.2%** of records (53k) — structural tier is limited; heuristic tier carries 99% of silver candidates
- Tier 2 silver (structural, multi-field): **4,613 records** (0.1%)
- Tier 1 silver (heuristic, partial): **335,524 records** (7.5%)

### SR-02 — ISBD parser split priority
**Status:** Resolved
- ` /` (SoR) appears in only 0.8% of titles; ` :` (subtitle) at 20.2% is the dominant title-area signal
- Parser must prioritise ` :` splitting for `OTHER_TITLE` / `TITLE` boundary, not ` /`

### SR-03 — Silver label quality and false positive rate
**Status:** Open — blocked on validation
- Tier-2 labels are structurally derived (`. -` area separator present) — expected high precision
- Tier-1 labels use heuristic whole-string patterns — false positive rate unknown for ` :`, ` /`, YEAR
- **Action:** run `scripts/validate_heuristic_fields.py` (200-record stratified sample); accept tier-1 for augmentation only if false positive rate < 15% per field

### SR-04 — TRANSLATOR / PERSON disambiguation
**Status:** Open
- ` /` fires for both PERSON (author) and TRANSLATOR; keyword matching ("übersetzt von", "Übers.:", "transl.") provides first-pass split
- **Action:** validate keyword heuristic precision on 100-record sample of ` /`-flagged titles before using TRANSLATOR as a distinct silver label

### SR-05 — Trailing period noise
**Status:** Open
- Trailing `.` fires in 17.5% of corpus but also hits abbreviations (`Hrsg.`, `Bd.`) and ordinals — upper bound, not a clean signal
- **Action:** before using as silver label signal, require co-occurrence with another ISBD marker, or strip a curated German abbreviation list

### SR-06 — Historical and Latin title scope
**Status:** Open
- 92.4% of records (tier 0) have no ISBD signals and fall to NER fallback — unknown share are Latin or pre-modern German
- **Action:** sample 200 records from `dc_type` = Leichenpredigt / pre-1800 Monografie; estimate Latin / Early Modern German proportion to determine how much historical signal is needed in training

### SR-07 — Gold set composition
**Status:** Open — blocks SR-08
- **Requirement:** ~500 manually annotated records stratified by: era (modern / 19th c. / pre-1800 / Latin), silver tier (2 / 1 / 0), and `dc_type`
- Must cover tier-0 fallback records (the NER majority path) not just ISBD-structured ones

### SR-08 — NuNER Zero evaluation
**Status:** Open — blocked on SR-07
- **Requirement:** run NuNER Zero zero-shot on 500 stratified fallback records; assess TITLE and PERSON F1 on gold set
- **Decision gate:** precision ≥ threshold → use zero-shot; else → LLM labeling + fine-tune `xlm-roberta-base` on silver + LLM-labeled set

### SR-09 — FRBR metric scope for paper
**Status:** Open
- **Requirement:** confirm which FRBR levels the paper's quality metrics cover — Work (TITLE, PERSON) only, or also Expression (TRANSLATOR, PARALLEL_TITLE, MEDIUM) and Manifestation (PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME)
- Determines which label types must appear in the gold set and which NER labels are in scope for the evaluation section

### SR-10 — DF_DE_TITLES source and title-length scope
**Status:** Open
- **Question 1:** Confirm the exact source of `DF_DE_TITLES` — is it derived from a specific DDB facet, dc_type filter, or the full object dump? Understanding the selection criteria affects generalizability claims in the paper.
- **Question 2:** The current corpus skews toward long ISBD strings. Short titles (single-token or bare proper-title strings with no punctuation signals) represent the NER-fallback majority and may need explicit representation in the silver and gold sets to avoid training on a length-biased sample.
- **Action:** Check DF_DE_TITLES provenance in pipeline notes / download script; plot title-length distribution (token count); decide whether to stratify sampling by length (e.g. short ≤ 5 tokens, medium 6–20, long > 20)

# GeMeA — NER for Bibliographic Title Extraction

Context: NER is the **fallback** in `link_gnd_works.py` for records without ISBD markers (~15–30% of DDB records). The primary extractor is the rule-based ISBD parser. NER only runs when that fails.

Target label set: `TITLE`, `PERSON`, `PUBLISHER`, `YEAR`, `EDITION`.

---

## Historical language scope

DDB objects span several centuries. Title content may be in modern German, Early Modern German, Middle High German, Latin, or other languages. This affects model choice.

**Key distinction**: the NER task is structural, not semantic. The model identifies *which span is the title* within a catalog string — it does not need to understand the title. Catalog records follow modern ISBD conventions regardless of object era, so:

- **ISBD parsing (primary)** — unaffected; punctuation-based, language-agnostic
- **Silver labeling** — unaffected; labels derive from ISBD structure, not title content
- **NER fallback** — affected only for the ~15–30% of records without ISBD markers

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
| **GLiNER** (`gliner_multi-v2.1`) | Zero-shot NER | No | Yes | Yes | Moderate | Zero-shot, any label set, BERT-sized, runs on CPU; multilingual variant covers German, Latin, historical text; best first thing to try |
| GROBID | Rule-based + CRF | No | Partial | Partial | Poor | Trained on scientific citations, not ISBD/library catalog — different domain; not recommended |

**Note on gbert-large**: was listed as the original plan but was never properly justified. Monolingual modern German is the wrong choice for a historically diverse corpus.

---

## GLiNER — zero-shot NER

[GLiNER](https://github.com/urchade/GLiNER) accepts arbitrary labels at inference time with no fine-tuning. The multilingual variant covers German, Latin, and historical text reasonably well.

```python
from gliner import GLiNER

model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")

entities = model.predict_entities(
    "Faust drittes Buch von Goethe erschienen Weimar",
    labels=["title", "person", "publisher", "year", "edition"],
)
# → [{"text": "Faust drittes Buch", "label": "title", "score": 0.91}, ...]
```

BERT-sized — runs on CPU, deployable alongside the existing stack. Zero-shot precision on domain-specific ISBD strings is unknown; **evaluate on ~500 fallback records before committing**.

---

## LLM options at inference time

NER only runs on the fallback subset (~15–30% of records that failed ISBD parsing): 750K–3M unique pairs, not 5–10M. At that scale, API LLMs become feasible.

| Approach | Scale | Cost | Historical/Latin | Effort |
|---|---|---|---|---|
| **GLiNER zero-shot** (local) | All fallback records | Free | Moderate | Low — deploy and evaluate |
| **LLM API at inference** (GPT-4o, Claude) | Fallback subset only | ~$300–900 at fallback scale | Good | Low |
| **Local LLM** (Llama 3.1 8B) | All records | GPU infra only | Moderate | Medium |
| **LLM one-time labeler → fine-tune xlm-roberta** | Generate labels once | Low one-time API cost | Good | Medium |
| **Fine-tuned xlm-roberta-base** | All records | Cheap at inference | Good (if trained on historical) | High upfront |

**Recommended path**: start with GLiNER zero-shot on 500 fallback records. If precision is acceptable, done. If not, use a LLM API to label those records and fine-tune `xlm-roberta-base` on that output.

---

## If no labeled training data is available

**1. Silver labeling from the ISBD pipeline**
The ~70–85% of records where ISBD parsing succeeds become auto-labeled training examples:
- Pre-`/` segment → `TITLE`
- Post-`/` segment → `PERSON` (statement of responsibility)
- Post-`. -` segments → `EDITION`, `PUBLISHER`, `YEAR` by position

Language-agnostic — works for Latin and historical German titles. Fine-tune `xlm-roberta-base` on these labels. Evaluate on a manually checked gold set of ~500 records including historical and Latin examples.

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

1. **Try GLiNER zero-shot first** — no training data, runs locally, handles multilingual. Evaluate on 500 stratified fallback records.
2. **If GLiNER precision is insufficient**, use an LLM API to label those same records and fine-tune `xlm-roberta-base` on that output.
3. **Silver labeling** (ISBD-derived) augments any fine-tuning — language-agnostic, large volume, no annotation cost.
4. Use `xlm-roberta` over any monolingual German model — the historical and Latin scope makes multilingual pretraining essential.
5. **GROBID**: trained on scientific citations, not library catalog records — not recommended.

---

## Open questions

- [ ] Is TITLE extraction sufficient, or are PUBLISHER/YEAR/EDITION labels needed for the paper's quality metrics?
- [ ] Silver label quality: how clean are the ISBD-derived annotations for training, especially for historical records?
- [ ] What share of non-ISBD records have Latin or historical German titles? (determines how much historical signal is needed)
- [ ] Gold set composition: sample should be stratified by era to catch historical degradation early

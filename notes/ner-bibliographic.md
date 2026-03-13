# GeMeA — NER for Bibliographic Title Extraction

Context: NER is the **fallback** in `link_gnd_works.py` for records without ISBD markers (~15–30% of DDB records). The primary extractor is the rule-based ISBD parser. NER only runs when that fails.

Target label set: `TITLE`, `PERSON`, `PUBLISHER`, `YEAR`, `EDITION`.

---

## Model options

| Model | Type | Fine-tune needed? | TITLE OOB | PERSON OOB | German | Notes |
|---|---|---|---|---|---|---|
| **GROBID** | Rule-based + CRF | No | Yes | Yes | Yes | Purpose-built for bibliographic reference parsing; best default choice |
| spaCy `de_core_news_lg` | Transformer | No | No | Yes | Native | Fast; PERSON only — no TITLE without fine-tuning |
| `flair/ner-german-large` | Stacked embeddings | No | No | Yes (PER) | Native | CoNLL-2003 labels; production-ready PERSON, nothing for TITLE |
| `deepset/gbert-large` | BERT-large | Yes | No | No | Native | No off-the-shelf bibliographic NER; requires custom training data |
| `xlm-roberta-large` | Transformer | Yes | No | No | Multilingual | Best base if fine-tuning; multilingual generalizes better than gbert |
| LLM (GPT-4o, Claude, Llama 3) | Generative | No | Yes | Yes | Yes | Zero-shot/few-shot prompt NER; too slow and expensive at 5–10M records |

**Note on gbert-large**: was listed as the original plan but was never properly justified. There is no public fine-tuned checkpoint for bibliographic NER with the required label set. GROBID should be evaluated first.

---

## If no labeled training data is available

Three practical options, in order of effort:

**1. GROBID (no training needed)**
Pre-trained CRF models for bibliographic reference parsing. Handles title, author, publisher, date, edition out of the box. Run as a local service. Evaluate precision on a sample of DDB strings before committing.

**2. Silver labeling from the ISBD pipeline**
The ~70% of records where ISBD parsing succeeds become auto-labeled training examples:
- Pre-`/` segment → `TITLE`
- Post-`/` segment → `PERSON` (statement of responsibility)
- Post-`. -` segments → `EDITION`, `PUBLISHER`, `YEAR` by position

Fine-tune a smaller model (xlm-roberta-base or spaCy) on these silver labels. Evaluate on a manually checked gold set of ~500 records. One-time cost; no external dataset needed.

**3. LLM as a one-time labeler**
Use GPT-4o or Claude to label a few thousand records (not all 5–10M). Fine-tune a smaller model on those outputs. Expensive per call but a one-time cost to produce a labeled set.

**Distant supervision (supplementary)**
For records where a GND Werk URI was confirmed via the local GND instance, the extracted title string is a positive `TITLE` example. Linked person GND URIs supply `PERSON` labels. Useful to augment silver labels, not sufficient alone.

---

## Available datasets for fine-tuning

| Dataset | Labels | Language | Size | Relevance |
|---|---|---|---|---|
| [empathyai/books-ner-dataset](https://huggingface.co/datasets/empathyai/books-ner-dataset) | TITLE, AUTHOR | English | Project Gutenberg catalogues | Closest label match; English only — use for domain-transfer pretraining |
| [HIPE-2022 (ajmc)](https://github.com/hipe-eval/HIPE-2022-data) | Fine-grained bibliographic refs | German, French, English | ~10K tokens | German bibliographic NER; domain is classical commentary, not library catalog |
| [CLEF-HIPE-2020](https://zenodo.org/record/3836029) | PER, ORG, LOC, PROD (work titles) | German, French, English | Historical newspapers | PROD label covers work/title mentions; historical text domain |
| [GermEval 2014](https://sites.google.com/site/germeval2014ner/) | PER, ORG, LOC, OTH | German | ~31K sentences | General NER; useful only for PERSON transfer |

**Recommended fine-tuning path (if needed)**:
1. Pretrain on `empathyai/books-ner-dataset` for TITLE/AUTHOR signal (domain transfer)
2. Fine-tune on silver-labeled DDB records (see above)
3. Evaluate on manually checked gold set; supplement with HIPE-2022 ajmc for German signal if needed

---

## Decision

1. **Evaluate GROBID first** on a sample of DDB strings that failed ISBD parsing. If precision is acceptable, use it as the fallback — no training data needed.
2. **If GROBID is insufficient**, generate silver labels from the ISBD-parsed majority and fine-tune `xlm-roberta-base` (or spaCy `de_core_news_lg` with a custom NER component).
3. Do not default to gbert-large without a concrete reason — it requires training data and is slower than the alternatives.

---

## Open questions

- [ ] What is GROBID's precision on non-ISBD DDB strings? (requires a sample evaluation)
- [ ] Is TITLE extraction sufficient, or are PUBLISHER/YEAR/EDITION labels needed for the paper's quality metrics?
- [ ] Silver label quality: how clean are the ISBD-derived annotations for training?

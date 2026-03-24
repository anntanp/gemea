# Zhan et al. (2026) — Assessment of Generative NER in the Era of LLMs

**Citation:** Qi Zhan, Yile Wang, Hui Huang. *Assessment of Generative Named Entity Recognition in the Era of Large Language Models.* arXiv:2601.17898v1, 25 Jan 2026. Shenzhen University.

**File:** `references/2026-zhan-assessment-nerllm.pdf`

---

## 1. Core claim

Fine-tuned open-source LLMs with parameter-efficient methods (LoRA) and structured output formats can match the performance of traditional encoder-based NER models on standard flat NER benchmarks, while maintaining general-purpose capabilities. Generative NER is a viable alternative to sequence-labeling approaches.

---

## 2. Method

- **Models:** LLaMA3.1/3.2/3.3 (1B–8B) and Qwen2.5/3 (1.5B–7B), fine-tuned with LoRA (rank 256, α 512, all linear modules); 2 epochs, batch size 8, lr 2e-5
- **Output formats tested:** Inline Bracketed, Inline XML, Category-grouped JSON, Occurrence-based JSON, Offset-based JSON (5 formats)
- **Datasets:** CoNLL2003, OntoNotes5.0 (flat, general domain); ACE2005, GENIA (nested; general and biomedical)
- **Baselines:** BERT-Tagger, BERT-MRC, W2NER, Biaffine+CNN (traditional encoder-based); GPT-3 zero-shot and few-shot (generative closed-source)

---

## 3. Key findings

### 3.1 Output format is decisive

| Format | Avg F1 (flat) | Avg F1 (nested) |
|---|---|---|
| Inline Bracketed | 90.69 | 77.22 |
| Inline XML | 90.07 | 76.91 |
| Category-grouped JSON | 85.60 | 74.92 |
| Occurrence-based JSON | 87.52 | 72.81 |
| Offset-based JSON | 29.66 | 14.51 |

Inline Bracketed and Inline XML are significantly better than all JSON formats. Offset-based JSON collapses completely — character-level position calculation is incompatible with autoregressive generation.

### 3.2 Fine-tuned LLMs match encoder-based models on general-domain NER

LLaMA3.1-8B with Inline Bracketed format: F1 93.83 on CoNLL2003, 91.28 on OntoNotes5.0 — comparable to BERT-MRC (93.04 / 91.11) and above GPT-3 fine-tuned (~90.62 / 69.01 on flat/nested).

### 3.3 Zero-shot LLM NER is materially weaker

GPT-3 zero-shot: F1 ~88.54 on flat, ~68.51 on nested — a real step down from fine-tuned performance. Zero-shot cannot substitute for fine-tuning on precision-sensitive tasks.

### 3.4 Low-resource domain gap persists

On GENIA (biomedical), LLMs fall behind specialized fine-tuned models (LLaMA3.1-8B Inline Bracketed: 83.75 avg F1 vs BERT-MRC 85.32). Domain-specific knowledge gaps are not fully compensated by model scale or instruction following.

### 3.5 LLMs genuinely learn entities, not memorize labels

Replacing label names with arbitrary symbols causes only a marginal F1 drop (−0.62 on CoNLL2003-SE, −0.42 on CoNLL2003-SO). Performance is driven by instruction following and entity recognition, not by memorizing entity-label correlations.

### 3.6 Fine-tuning preserves general capabilities

LoRA fine-tuning for NER causes minor fluctuations (±3–4%) on general benchmarks (MMLU, HellaSwag, GSM8K, TruthfulQA). DROP improves significantly (+25 F1) because NER fine-tuning strengthens entity span extraction, which DROP requires.

---

## 4. Error analysis (§5)

LLMs and encoder models make qualitatively different errors:

| Error type | BERT-MRC | LLaMA3.1-8B |
|---|---|---|
| Wrong Types | 29.0% | 38.2% |
| Omitted Mentions | 45.5% | 13.7% |
| Completely-O | 0% | 25.2% |

- **Encoder models** predominantly miss entities (Omitted Mentions 45.5%) — conservative extraction
- **LLMs** predominantly misclassify types (38.2%) and over-extract (Completely-O 25.2%) — aggressive extraction driven by pre-training world knowledge conflicting with annotation guidelines

---

## 5. Implications for GeMeA

### 5.1 NuNER Zero (SR-08) remains relevant

NuNER Zero is not evaluated in this paper (it uses a GLiNER/encoder span-extraction architecture, not generative). The zero-shot gap documented here (GPT-3 ZS ~88 vs fine-tuned ~93 on general NER) supports the SR-08 decision logic: evaluate zero-shot first; only fine-tune if zero-shot falls below threshold. The risk is that historical Early Modern German bibliographic NER is further out-of-distribution than standard CoNLL2003, so NuNER Zero's zero-shot precision may be lower than the general-domain gap suggests.

### 5.2 Fine-tuned generative LLMs should be added as SR-08 benchmark

If NuNER Zero is insufficient and fine-tuning is pursued, a small fine-tuned LLM (Qwen3-1.7B or LLaMA3.2-1B with LoRA) should be benchmarked alongside `xlm-roberta-large`. The paper shows 1B–4B models lag 7B–8B by ~10 F1 points, but the 7B–8B range matches encoder-based models — and LoRA fine-tuning footprint is manageable for the DDB use case.

### 5.3 LLM labeling output format

If Claude or another LLM is used to generate silver labels or annotate the SR-09 gold set, use **Inline Bracketed** or **Inline XML** output format. JSON formats (especially offset-based) perform significantly worse. Category-grouped JSON also loses positional information.

### 5.4 Low-resource domain caveat applies directly

The GENIA biomedical gap is structurally similar to GeMeA's situation: historical German bibliographic text is a low-resource domain where LLM pre-training provides minimal coverage. This supports prioritising the SR-09 gold set and fine-tuning over zero-shot-only deployment.

### 5.5 Error mode expectation

When evaluating LLM-based NER on DDB strings, expect: (1) type misclassification as the dominant error (TITLE vs OTHER_TITLE boundary, PERSON vs corporate body); (2) over-extraction on short, fragment-like records. Encoder-based models (NuNER Zero, xlm-roberta-large) will likely under-extract instead — missing entities in long Early Modern German strings.

---

## 6. Limitations of the paper (relevance to GeMeA)

- Evaluates only LLaMA and Qwen families — does not cover encoder-only zero-shot models (GLiNER, NuNER Zero)
- All datasets are modern general-domain or biomedical English/multilingual — no historical NER, no bibliographic structure
- Does not evaluate multilingual performance on non-English text
- LoRA fine-tuning assumes a labelled training set; does not address the zero/low-resource regime directly

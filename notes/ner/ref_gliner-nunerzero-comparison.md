# GLiNER and NuNER Zero — Pros, Cons, and Caveats

Sources:
- Zaratiana, U., Tomeh, N., Holat, P., & Charnois, T. (2024). GLiNER: Generalist Model for Named Entity Recognition using Bidirectional Transformer. *Proceedings of NAACL 2024*, pp. 5364–5376. (`references/2024-zaratiana-gliner.pdf`)
- Bogdanov, S., Constantin, A., Bernard, T., Crabbé, B., & Bernard, E. (2024). NuNER: Entity Recognition Encoder Pre-Training via LLM-Annotated Data. *Proceedings of EMNLP 2024*, pp. 11829–11841. (`references/2024-bogdanov-nuner.pdf`)

⚠️ **Metric incompatibility:** GLiNER reports entity-level exact-match F1; NuNER reports macro-averaged token-classification F1. Numerical scores across the two papers are not directly comparable.

---

## 1. Relationship between GLiNER and NuNER Zero

GLiNER (NAACL 2024) is the base architecture: a single bidirectional encoder that jointly encodes entity type descriptions and the input text, then scores span–type pairs via dot product. NuNER (EMNLP 2024) is a separate pre-training strategy that uses a different architecture (two independent encoders, concept encoder discarded at inference) trained on 1M LLM-annotated sentences. **NuNER Zero** is a released HuggingFace model (`numind/NuNer_Zero`) that adapts NuNER for zero-shot NER — but its zero-shot benchmarks are **not reported in the EMNLP 2024 paper**; the authors explicitly state "we only studied the Few-shot learning capabilities of the model, without experimenting with the potential Zero-shot modifications of NuNER" (Bogdanov et al., 2024, p. 11836, Limitations). Any cited zero-shot performance figures for NuNER Zero come from sources outside these two papers.

---

## 2. Pros and cons — GLiNER (citable)

| # | Claim | Evidence | Source |
|---|---|---|---|
| ✅ | **Zero-shot OOD performance competitive with LLMs 40× larger.** GLiNER-L (300M) outperforms GoLLIE-7B (avg F1 60.9 vs. 58.0) and UniNER-13B (55.6) on the 7-dataset CrossNER/MIT zero-shot benchmark. GLiNER-M (90M) matches UniNER-13B at 1/140th the parameter count. | Table 1 | Zaratiana et al. (2024) §4.1 |
| ✅ | **CPU-capable inference, O(n log n) decode.** Greedy span selection with a priority queue; stated to run on CPU. | §2.3, abstract | Zaratiana et al. (2024) |
| ✅ | **Multilingual (GLiNER-Multi variant) surpasses ChatGPT on most languages.** On MultiCONER zero-shot, GLiNER-Multi (mdeberta-v3-base) scores 39.5 F1 on German vs. ChatGPT 37.1; outperforms ChatGPT in 8 of 10 non-training languages. | Table 3 | Zaratiana et al. (2024) §4.2 |
| ✅ | **Nested entity support.** Decoding scheme explicitly handles fully nested spans. | §2.3 | Zaratiana et al. (2024) |
| ✅ | **Free-text label definitions — arbitrary entity types without retraining.** Entity types are natural language strings passed at inference time. | §2.1 | Zaratiana et al. (2024) |
| ❌ | **Cannot extract discontinuous entities.** Authors state this directly: "One notable limitation is the model's inability to extract discontinuous entities." | Limitations | Zaratiana et al. (2024) |
| ❌ | **Hard span-length cap at 12 tokens.** Maximum span width is fixed at K=12 tokens to preserve linear complexity; longer spans are not extracted. | §2.3 / App. A.1 | Zaratiana et al. (2024) |
| ❌ | **Training data is English-only (Pile-NER).** The 44,889-passage training corpus is English. The multilingual variant (GLiNER-Multi) uses mdeberta-v3-base but is not pre-trained on multilingual data — multilingual capability depends entirely on the backbone. | §3.1 | Zaratiana et al. (2024) |
| ❌ | **Gap vs. supervised fine-tuned models remains large.** Zero-shot avg F1 on MultiCONER is 32.9 (GLiNER-Multi) vs. supervised XLM-R baseline 54.9 — a 22-point gap. | Table 3 | Zaratiana et al. (2024) §4.2 |
| ❌ | **Underperforms on non-Latin scripts.** Bengali F1: GLiNER-En 0.89, GLiNER-Multi 25.9 vs. ChatGPT 23.3. German/Latin-script performance is substantially better. | Table 3 | Zaratiana et al. (2024) §4.2 |
| ⚠️ | **Exact-match metric may undercount partial span matches.** Authors acknowledge this may not fully capture partial or context-sensitive entity extractions. | Limitations | Zaratiana et al. (2024) |

---

## 3. Pros and cons — NuNER / NuNER Zero (citable)

| # | Claim | Evidence | Source |
|---|---|---|---|
| ✅ | **Few-shot performance substantially better than RoBERTa baseline.** At k=1 annotation per entity type: NuNER 39.4 avg F1 vs. RoBERTa 24.5 (avg across 4 datasets: OntoNotes 5.0, BioNLP, MIT Restaurant, MIT Movie). | Table 4 / Fig. 7 | Bogdanov et al. (2024) §4.1 |
| ✅ | **Matches UniversalNER-7B at 1/56th the parameters.** At k=8–128 shots: NuNER (125M) ≈ UniversalNER-7B (7B) on entity-level micro F1 (58.75 vs. 57.89 at k=8–16). | Table 2 | Bogdanov et al. (2024) §4.3 |
| ✅ | **Drop-in replacement for BERT/RoBERTa.** Concept encoder is discarded after training; only the text encoder is kept, usable in standard token-classification pipelines. | §3.3 | Bogdanov et al. (2024) |
| ✅ | **Inference cost orders of magnitude below GPT-4.** Authors estimate <$0.0001 per example vs. ~$0.10 for GPT-4. | §6 | Bogdanov et al. (2024) |
| ✅ | **Multilingual variant outperforms mBERT on MultiNERD** at all few-shot sizes (k=1: 27.71 vs. 10.84; k=64: 67.68 vs. 62.20). | App. A.2, Table 3 | Bogdanov et al. (2024) |
| ❌ | **Zero-shot capability of NuNER Zero is not evaluated in the paper.** Authors explicitly: "we only studied the Few-shot learning capabilities of the model, without experimenting with the potential Zero-shot modifications of NuNER." Any zero-shot benchmarks for the HuggingFace NuNer_Zero release are not documented in this publication. | Limitations | Bogdanov et al. (2024) p. 11836 |
| ❌ | **Training data is English-only** (C4 web corpus, GPT-3.5 annotation). Multilingual variant is appendix-level with no German-specific results. | §3.1, App. A.2 | Bogdanov et al. (2024) |
| ❌ | **Concept diversity gap.** Training concept distribution is heavy-tailed — >100k concepts appear only once; frequent concepts dominate. Performance on rare entity types (e.g. bibliographic roles: TRANSLATOR, SERIES) is likely lower than on common types (person, location). | §3.1 / Fig. 4 | Bogdanov et al. (2024) |
| ❌ | **BioNLP performance degrades beyond 100k training examples** — reason unexplained. Suggests instability in domain-specific low-resource settings. | §5.2 / Table 7 | Bogdanov et al. (2024) |
| ⚠️ | **arXiv ID 2402.15343 unconfirmed.** The EMNLP 2024 venue and authorship are confirmed from the PDF; the arXiv preprint ID requires independent verification before citation. | — | — |

---

## 4. Relevance to GeMeA (SR-09)

Neither GLiNER nor NuNER Zero has been evaluated on:
- Historical German text (Early Modern orthography, pre-1750)
- Bibliographic NER (TITLE, PERSON, OTHER_TITLE, TRANSLATOR)
- ISBD-structured records or DDB catalog strings

The supervised baseline gap (GLiNER-Multi: 32.9 vs. XLM-R supervised: 54.9 on MultiCONER) is consistent with the zero-shot LLM performance gap documented in Zhan et al. (2026). For GeMeA's low-resource historical domain, a similar or larger gap should be expected. SR-09 evaluation on 500 stratified records is necessary before drawing any conclusions about viability.

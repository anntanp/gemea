# Tokenization for GND Werk Linking

## 1. Two tokenization contexts

Title tokenization for GND Werk linking occurs in two distinct pipeline stages with different requirements:

| Context | Stage | Approach |
|---------|-------|----------|
| **A — GND match lookup** | After title extraction | Rule-based normalization; no model |
| **B — NER title extraction** | Before title extraction | Transformer tokenizer + NER model |

> **Note:** ISBD coverage figures (previously cited as ~29% ISBD / ~71% no-ISBD) are stale. They were computed on an earlier dataset that used different htype filtering and langid-based language selection — both superseded by `s2_meta_de_content.parquet` (ADR-01 htypes + `dc:language ∈ {ger, gmh, nds}`). Recompute ISBD coverage against the current parquet before using any split percentages downstream.

---

## 2. Context A — Rule-based normalization (GND match lookup)

Already specced in `notes/gnd/gnd-linking-plan.md`. No ML model needed.

```
NFC normalize → lowercase → strip diacritics
→ split on whitespace + punctuation
→ remove stopwords (der, die, das, ein, eine, von, und, zu, im, in, an, auf, für, mit, bei, dem, den)
→ drop tokens len ≤ 3
→ select up to 3 distinctive tokens (exclude GENERIC_TITLE_WORDS)
```

---

## 3. Context B — Transformer tokenizer (NER fallback)

### 3.1 Recommended model

**`xlm-roberta-large`** (`FacebookAI/xlm-roberta-large`)

Already the documented NER backbone in `notes/ner/ner-bibliographic.md`, supported by HIPE-2022 and CLEF-HIPE-2020 evidence where it was the dominant top-system backbone for historical bibliographic NER in German.

| Property | Detail |
|----------|--------|
| Tokenizer | SentencePiece BPE, 250K vocabulary |
| Historical orthography | Handled via subword fallback — unknown words decompose into known subword pieces |
| `gmh` / `nds` | No dedicated pretraining, but BPE degrades gracefully; gmh + nds = 2,800 records (0.03% of corpus) — not a critical path |
| Max sequence length | 512 tokens; longest DDB titles reach ~50 tokens (pre-1750 extreme); no truncation needed in practice |
| Batch size | 32–64 on GPU; titles are short so throughput is high |

### 3.2 Why not German-specific models

| Model | Reason rejected |
|-------|----------------|
| `dbmdz/bert-base-historic-german-cased` | Trained on newspapers 1890–1939 only; does not cover Early Modern German (1500–1750); base size only |
| `deepset/gbert-large` | Modern German only; degrades on pre-1800 orthography (confirmed SR-06) |
| spaCy `de_core_news_lg` | Same limitation as gbert-large; rejected SR-06 |
| `mdeberta-v3-base` | Competitive but no large multilingual variant; weaker cross-lingual transfer than xlm-roberta-large |

### 3.3 Historical orthography preprocessing

Early Modern German (1500–1750) is the dominant historical stratum (~93% of pre-modern records). Apply lightweight Unicode normalization *before* the tokenizer:

```python
import unicodedata

def normalize_historical(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    # long s (ſ) → s
    text = text.replace("\u017f", "s").replace("\u017e", "s")
    # common ligatures
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("\ufb00", "ff").replace("\ufb03", "ffi").replace("\ufb04", "ffl")
    return text
```

BPE handles remaining orthographic variation (e.g. `Theil` → `Th`, `##eil`; `heyligen` → subwords). No further preprocessing needed.

### 3.4 Tokenizer call

```python
from transformers import AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-large")

def tokenize_title(title: str) -> dict:
    title = normalize_historical(title)
    return tokenizer(
        title,
        truncation=True,
        max_length=128,            # safety cap; well above any real title length
        return_offsets_mapping=True,  # required: maps token predictions → char offsets
    )
```

`return_offsets_mapping=True` is required downstream for converting NER token-level span predictions back to character offsets, which the GND linking output format needs (`extracted_title` as a substring of `raw_title`).

---

## 4. Scope

This note covers tokenization only. The following are handled separately:

- Fine-tuning `xlm-roberta-large` on the German bibliographic NER gold set → `notes/ner/`
- ISBD rule-based title extraction → `notes/gnd/gnd-linking-plan.md`
- GND SPARQL query construction and scoring → `notes/gnd/gnd-linking-spec.md`

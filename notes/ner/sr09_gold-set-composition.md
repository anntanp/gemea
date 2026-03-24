# GeMeA — Gold Set Composition (SR-08)

**SR-08** in [ner-bibliographic.md](../ner-bibliographic.md).
Blocks: SR-09 (NuNER Zero / GLiNER evaluation), SR-11 (LLM annotation batch), SR-12 (field-level weighting calibration).

---

## 1. Purpose

The gold set is the single authoritative evaluation corpus for the GeMeA NER pipeline. It has three roles:

1. **Model evaluation** — compute span-level F1 per label type on a held-out human-annotated sample; drives SR-09 (NuNER Zero / GLiNER zero-shot benchmark vs. fine-tuned baselines)
2. **LLM annotation quality gate** — the 50-record manually annotated seed is used as few-shot examples and as the reference for the ≥85% agreement threshold check before running the full 4k–5k batch (SR-11 §2.3)
3. **Silver label calibration** — NER F1 at different tier cutoffs lets SR-12 set the weighted-score boundary between tier-1 and tier-0 treatment

---

## 2. Composition requirements

### 2.1 Target size

| Phase | Size | Rationale |
|---|---|---|
| **Seed** (manual, immediate) | 50–100 records | Minimum for SR-11 few-shot bootstrap; annotation takes ~2–4 hours manually |
| **Full gold set** | ~500 records | Sufficient for stable F1 estimates; 500 × p(1−p)/n ≈ ±4.4% margin at 95% CI (worst-case p=0.5) |

The 50-record seed is a subset of the full gold set — do not annotate separately. Annotate the full 500 in one pass; use the first 50–100 as the SR-11 prompt seed.

### 2.2 Stratification

Gold set records must be stratified across four dimensions simultaneously:

| Dimension | Strata | Reason |
|---|---|---|
| **Era** | modern (≥1900), 19th c. (1800–1899), 1700–1800, pre-1700 | NER difficulty and register vary sharply by era; PERSON recall drops for pre-1750 author-before-title structure |
| **Silver tier** | tier-2 (structural), tier-1 (heuristic), tier-0 (no labels) | Evaluation must cover all inference paths; tier-0 is the main fallback (92.4% of corpus) |
| **`dc_type`** | Leichenpredigt, Monografie, Einblattdruck (and modern residual) | Genre-specific structure differences affect label distribution; Leichenpredigt has the highest pre-1750 density |
| **Title length** | short (≤4 tokens), medium (5–14), long (>14) | Pre-1750 long strings (42–50% of era) stress boundary detection differently than short modern titles |

**Allocation target (500 records):**

| Era | Tier-2 | Tier-1 | Tier-0 | Total |
|---|---|---|---|---|
| Modern (≥1900) | 20 | 40 | 20 | 80 |
| 19th c. (1800–1899) | 15 | 30 | 15 | 60 |
| 1700–1800 | 10 | 20 | 30 | 60 |
| Pre-1700 | 5 | 15 | 80 | 100 |
| Modern/19th residual | — | — | 100 | 100 |
| dc_type oversampling | 40 (Leichenpredigt + Einblattdruck) | | | 100 |
| **Total** | **~50** | **~105** | **~245** | **~500** |

> Note: tier-0 is over-represented in the pre-1700 strata because that is where the LLM annotation (SR-11) applies — the gold set must evaluate model behaviour on the primary inference path.

Leichenpredigt and Einblattdruck records are oversampled to 40–50 each (drawn from pre-1700/1700–1800 strata) because these genres have the most structurally distinctive title-page conventions and are the highest-risk failure modes for the NER model.

### 2.3 No Latin stratum

True Latin prevalence in DF_DE_TITLES is ~0.5% (SR-06). Latin records are not a separate stratum — identify them manually during annotation if encountered and mark `lang=la` in the annotation metadata. Do not attempt Latin NER evaluation in Phase 1.

---

## 3. Annotation schema

### 3.1 Phase 1 labels (required for evaluation)

| Label | What it marks | Notes |
|---|---|---|
| `TITLE` | Main work title; primary intellectual content identifier | May include subtitle if no `OTHER_TITLE` separator is present |
| `OTHER_TITLE` | Subtitle or alternative title | Introduced by `Das ist:`, `oder`, `:`, `nämlich`, `welches handelt von` |
| `PERSON` | Author, editor, responsible person; includes credentials and role descriptions forming a single naming unit | Pre-1750: includes opening credential sequence and post-name role phrases; see §4 |

### 3.2 Phase 2 labels (include in schema, skip for Phase 1 evaluation)

Annotate these in the same pass to avoid re-annotation when SR-07 Phase 2 is reached:

| Label | What it marks |
|---|---|
| `TRANSLATOR` | Translator; only when a translation keyword is present (`übersetzt`, `Übers.`, `transl.`, `traduit`) |
| `PARALLEL_TITLE` | Title in a second language, typically after `=` |
| `MEDIUM` | Statement of medium or format for music (e.g. `für Klavier und Violine`) |

Phase 2 labels need not be evaluated in Phase 1. Annotate them anyway so the gold set does not need to be extended when Phase 2 evaluation is due.

### 3.3 Span boundary convention

- Spans are **character-level** offsets into the raw `dc:title` string (no pre-tokenization)
- Spans are **non-overlapping** and **non-nested** — if a PERSON span contains a title fragment, the PERSON boundary stops before that fragment
- Spans **must** be contiguous substrings of the input — no gap spans
- For pre-1750 records: the PERSON span includes degree abbreviations, full name, and role phrases up to (but not including) the first content noun of the title; see §4 for examples

---

## 4. Annotation guidelines for pre-1750 records

These records are the highest-risk stratum for annotation error and model failure. Annotators must not apply modern bibliographic conventions.

### 4.1 Author-before-title structure

In pre-1750 titles, the author's name and credentials appear **before** the main title. There is no ` /` separator. The typical structure is:

```
[credential + name + role phrase | PERSON] [main title | TITLE] [subtitle | OTHER_TITLE]
```

Example:
```
Input:  "D. Johann Gerhard, Professoris zu Jena, Erklärung der Historien des Leidens"
Output: [D. Johann Gerhard, Professoris zu Jena | PERSON] [Erklärung der Historien des Leidens | TITLE]
```

### 4.2 PERSON span boundaries

**Include in the PERSON span:**
- Academic degree abbreviations immediately before the name: `D.` (Doktor), `M.` (Magister), `Lic.`, `Mag.`
- Full personal name (first name + surname)
- Role or position phrases following the name: `Pfarrers zu X`, `der H. Schrifft Lehrers`, `Professoris`, `Pastoris`, `Superintendenten`
- Genitive or prepositional phrases identifying the post: `zu Jena`, `in Leipzig`, `bey der Gemeine zu X`

**Stop the PERSON span** at the first token that is clearly part of the work title (a content noun, verb phrase, or `Das ist:`).

### 4.3 Common errors to avoid

| Error | Example | Correct annotation |
|---|---|---|
| Annotating the credential sequence as TITLE | `D. Johann Gerhard` marked as TITLE | Mark as PERSON; title begins after role phrase |
| Splitting credentials from name | `D. Johann Gerhard` → only `Johann Gerhard` as PERSON | Include degree abbreviation in the PERSON span |
| Marking dedicatees as PERSON | `Herrn N.N. gewidmet` | Only label named dedicatees if also the author; generic dedications are not labeled |
| Marking embedded Latin as a separate entity | `Anno MDXLVI` | Part of the TITLE span; do not extract separately |
| Labeling `durch` / `von` phrases as TRANSLATOR | `durch Johann Schmidt` | Label PERSON unless a translation keyword is present |

---

## 5. Sampling procedure

### 5.1 Draw the sample

```python
import pandas as pd
import numpy as np

rng = np.random.default_rng(seed=42)

# Load corpus
df = pd.read_parquet("data/processed/df_de_titles.parquet")

# Derive era strata
df["era"] = pd.cut(
    pd.to_numeric(df["dates"], errors="coerce"),
    bins=[-np.inf, 1700, 1800, 1900, np.inf],
    labels=["pre-1700", "1700-1800", "19th-c", "modern"],
    right=False,
)
df["era"] = df["era"].cat.add_categories("unknown").fillna("unknown")

# Draw per stratum
strata = [
    ("modern",    "2",  20), ("modern",    "1",  40), ("modern",    "0",  20),
    ("19th-c",    "2",  15), ("19th-c",    "1",  30), ("19th-c",    "0",  15),
    ("1700-1800", "2",  10), ("1700-1800", "1",  20), ("1700-1800", "0",  30),
    ("pre-1700",  "2",   5), ("pre-1700",  "1",  15), ("pre-1700",  "0",  80),
]

frames = []
for era, tier, n in strata:
    pool = df[(df["era"] == era) & (df["silver_tier"] == tier)]
    k = min(n, len(pool))
    frames.append(pool.sample(n=k, random_state=rng.integers(1e6)))

# Oversample Leichenpredigt + Einblattdruck
for dc_type in ["Leichenpredigt", "Einblattdruck"]:
    pool = df[
        df["dc_type"].str.contains(dc_type, na=False) &
        df["silver_tier"].isin(["0", "1"])
    ]
    frames.append(pool.sample(n=min(50, len(pool)), random_state=rng.integers(1e6)))

gold_sample = (
    pd.concat(frames)
    .drop_duplicates(subset=["identifier"])
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)
gold_sample.to_csv("data/annotation/sr09_gold_sample.csv", index=False)
print(f"Gold sample size: {len(gold_sample)}")
```

### 5.2 Output format

Each annotated record should produce a JSON Lines file (`data/annotation/sr09_gold.jsonl`) with entries of the form:

```json
{
  "identifier": "de/...",
  "dc_title": "D. Johann Gerhard, Professoris zu Jena, ...",
  "era": "pre-1700",
  "dc_type": "Leichenpredigt",
  "silver_tier": "0",
  "spans": [
    {"start": 0, "end": 35, "label": "PERSON", "text": "D. Johann Gerhard, Professoris zu Jena"},
    {"start": 37, "end": 82, "label": "TITLE",  "text": "Erklärung der Historien des Leidens..."}
  ],
  "annotator": "manual",
  "annotation_date": "2026-XX-XX",
  "notes": ""
}
```

Phase 2 labels (`TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM`) use the same span format — add them to the `spans` array if present.

---

## 6. Evaluation metrics

Run after annotation is complete; use the held-out portion (full 500) against model predictions.

### 6.1 Span-level exact match F1

Standard NER evaluation: a span is correct if **both** the character offsets and the label match exactly.

```python
from seqeval.metrics import classification_report  # or spacy scorer

# Convert spans to BIO tags per token, then compute
```

Report separately:
- Per-label F1: `TITLE`, `OTHER_TITLE`, `PERSON` (Phase 1); `TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM` (Phase 2 when ready)
- Per-era F1: `modern`, `19th-c`, `1700-1800`, `pre-1700` — PERSON F1 on pre-1700 must be tracked separately (author-before-title failure mode)
- Per-tier F1: tier-2, tier-1, tier-0 — primary interest is tier-0 (NER fallback path)

### 6.2 Thresholds and decision gates

| Metric | Threshold | Action if below |
|---|---|---|
| Overall span F1 (all labels) | ≥ 0.80 | Do not advance to production; extend fine-tuning data |
| TITLE F1 (all eras) | ≥ 0.85 | Minimum for reliable title extraction feeding GND linking |
| PERSON F1 (pre-1700 stratum) | ≥ 0.75 | Below this: author-before-title prompt rule is not learned; revise SR-11 prompt and re-run LLM labeling |
| LLM annotation agreement (SR-11 spot-check) | ≥ 0.85 span F1 vs. gold | Below this: revise system prompt before full 4k–5k batch |

These thresholds are consistent with the "practical minimum for reliable boundary learning" framing in SR-11 §1 and with the SR-09 decision gate in ner-bibliographic.md §2.8.

---

## 7. Relationship to other SRs

| SR | Dependency on SR-08 |
|---|---|
| SR-09 (NuNER Zero / GLiNER evaluation) | Needs full 500-record gold set to run zero-shot benchmarks |
| SR-11 (LLM annotation) | Needs 50-record seed for few-shot prompt; needs spot-check agreement against gold sample |
| SR-12 (field-level weighting) | Needs NER F1 vs. score-cutoff to calibrate tier-1/0 boundary |

The 50-record manual seed annotated first also serves as the SR-11 prompt seed — annotate these from the pre-1700 tier-0 stratum (the highest-risk and least-covered stratum) to maximize value of the seed.

---

## 8. Blockers and open questions

| Item | Status |
|---|---|
| Annotation tool selection | Unresolved — `doccano`, `Label Studio`, or JSON Lines in a spreadsheet are all viable for 500 records; Label Studio preferred for span annotations |
| Inter-annotator agreement (IAA) | Desirable but not required for Phase 1 — a single trained annotator is sufficient for the 500-record set; flag ambiguous cases in `notes` field |
| Pre-1750 annotation examples | 5 examples in SR-11 §4.3 serve as annotator training; review against real DDB records before starting |
| `silver_tier` column name in corpus | Check actual column name in `df_de_titles.parquet` — may be `tier`, `label_tier`, or `silver_tier` |

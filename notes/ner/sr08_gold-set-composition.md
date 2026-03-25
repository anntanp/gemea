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

### 2.4 Sample size adequacy

The allocation table targets ~500 records, but `sr08_sample_gold.py` produced **395** due to structural constraints: the pre-1700 stratum has no tier-2 records (ISBD conventions postdate these titles), and some strata are smaller in the corpus than the target allocation.

F1 reliability in NER depends on **entity instance counts**, not record counts. A record contributes one TITLE span, zero or one OTHER_TITLE, and zero or one PERSON — so entity counts are strictly less than record counts. Rough estimates at 395 records:

| Label | Approx. prevalence | Est. instances | F1 CI half-width (±pp) |
|---|---|---|---|
| TITLE | ~100% | ~395 | ±2–3 |
| OTHER_TITLE | ~40% | ~158 | ±5–6 |
| PERSON (all eras) | ~30% | ~120 | ±6–7 |
| PERSON (pre-1700 only) | ~70% of ~100 | ~70 | ±8–10 |
| TRANSLATOR | rare | ~10–20 | ±15–20 |
| PARALLEL_TITLE | rare | ~10–15 | ±18–22 |

CI half-widths are approximate 95% Wilson intervals on a proportion; actual F1 CIs require bootstrap resampling but scale similarly.

**Conclusions:**

- **Phase 1 labels (TITLE, OTHER_TITLE, PERSON overall):** workable. TITLE and OTHER_TITLE F1 estimates are stable. Overall PERSON is marginal but sufficient to detect gross failures.
- **PERSON (pre-1700 stratum):** ~±10 pp uncertainty. Can detect coarse failure (F1 < 0.65) but not fine-grained model differences. Report with an explicit CI; do not report as a hard number.
- **Phase 2 labels (TRANSLATOR, PARALLEL_TITLE):** not interpretable at 395 records. CIs of ±15–20 pp make any F1 number uninformative. These labels should be annotated in the same pass (§3.2) to avoid re-annotation, but excluded from Phase 1 evaluation claims.

**Implication for the paper:** limit evaluation claims to Phase 1 labels. Report CIs alongside F1 (bootstrap, 1000 samples). Mention Phase 2 annotation as future evaluation work. If PERSON F1 on the pre-1700 stratum is a primary contribution claim, consider expanding that stratum by 50–100 records (annotating more pre-1700 tier-0 from `sr08_manual_queue.csv`) to bring CI half-width below ±7 pp.

---

## 3. Annotation schema and guidelines

See **[sr08_annotation-guide.md](sr08_annotation-guide.md)** for the complete annotation reference: label definitions, decision flowchart, examples with DDB links, span boundary rules, LLM task format, and workflow.

Label scope summary:

| Phase | Labels | Status |
|---|---|---|
| Phase 1 | `TITLE`, `OTHER_TITLE`, `PERSON` | Required; evaluated in SR-09 |
| Phase 2 | `TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM` | Annotate in same pass; not evaluated in Phase 1 |

Annotate Phase 2 labels in the same pass to avoid re-annotation when SR-07 Phase 2 is reached. Spans are character-level offsets into the raw `title` string; run `sr08_verify_spans.py` after each batch.

---

## 4. Sampling procedure

### 4.1 Draw the sample

```python
import pandas as pd
import numpy as np

rng = np.random.default_rng(seed=42)

# Load corpus and ratings (silver_tier is in the ratings CSV, not in the pkl)
df = pd.read_pickle("data/DF_DE_TITLES_20240125b.pkl")
ratings = pd.read_csv("data/processed/isbd_field_ratings.csv", usecols=["obj_id", "silver_tier"])
df = df.merge(ratings, on="obj_id", how="left")
df["silver_tier"] = df["silver_tier"].fillna(0).astype(int).astype(str)

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
    .drop_duplicates(subset=["obj_id"])
    .sample(frac=1, random_state=42)
    .reset_index(drop=True)
)
gold_sample.to_csv("data/annotation/sr08_gold_sample.csv", index=False)
print(f"Gold sample size: {len(gold_sample)}")
```

### 4.2 Output format

See [sr08_annotation-guide.md §8](sr08_annotation-guide.md#8-output-format-jsonl) for the full JSONL record schema (`obj_id`, `title`, `era`, `dc_type`, `silver_tier`, `ddb_link`, `spans`, `annotation_status`, `annotator`, `annotation_date`, `notes`).

---

## 5. Evaluation metrics

Run after annotation is complete; use the held-out portion (full 500) against model predictions.

### 5.1 Span-level exact match F1

Standard NER evaluation: a span is correct if **both** the character offsets and the label match exactly.

```python
from seqeval.metrics import classification_report  # or spacy scorer

# Convert spans to BIO tags per token, then compute
```

Report separately:
- Per-label F1: `TITLE`, `OTHER_TITLE`, `PERSON` (Phase 1); `TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM` (Phase 2 when ready)
- Per-era F1: `modern`, `19th-c`, `1700-1800`, `pre-1700` — PERSON F1 on pre-1700 must be tracked separately (author-before-title failure mode)
- Per-tier F1: tier-2, tier-1, tier-0 — primary interest is tier-0 (NER fallback path)

### 5.2 Thresholds and decision gates

| Metric | Threshold | Action if below |
|---|---|---|
| Overall span F1 (all labels) | ≥ 0.80 | Do not advance to production; extend fine-tuning data |
| TITLE F1 (all eras) | ≥ 0.85 | Minimum for reliable title extraction feeding GND linking |
| PERSON F1 (pre-1700 stratum) | ≥ 0.75 | Below this: author-before-title prompt rule is not learned; revise SR-11 prompt and re-run LLM labeling |
| LLM annotation agreement (SR-11 spot-check) | ≥ 0.85 span F1 vs. gold | Below this: revise system prompt before full 4k–5k batch |

These thresholds are consistent with the "practical minimum for reliable boundary learning" framing in SR-11 §1 and with the SR-09 decision gate in ner-bibliographic.md §2.8.

---

## 6. Relationship to other SRs

| SR | Dependency on SR-08 |
|---|---|
| SR-09 (NuNER Zero / GLiNER evaluation) | Needs full 500-record gold set to run zero-shot benchmarks |
| SR-11 (LLM annotation) | Needs 50-record seed for few-shot prompt; needs spot-check agreement against gold sample |
| SR-12 (field-level weighting) | Needs NER F1 vs. score-cutoff to calibrate tier-1/0 boundary |

The 50-record manual seed annotated first also serves as the SR-11 prompt seed — annotate these from the pre-1700 tier-0 stratum (the highest-risk and least-covered stratum) to maximize value of the seed.

---

## 7. Annotator requirements

### 7.1 Number of annotators and IAA

**2 annotators** are required, with a third adjudicating disagreements. The benefit of annotation scales steeply from 1→2 and diminishes sharply after 3 — Snow et al. (2008) showed empirically that for most NLP labeling tasks, 2–3 annotators reach near-ceiling quality. The primary value of a second annotator is to surface systematic disagreement (ambiguous boundary cases, guideline gaps), not to average out noise.

**Stratum-level requirements:**

| Stratum | Annotators | Rationale |
|---|---|---|
| Pre-1700 tier-0 (~130 records) | 2 + adjudication | Highest structural ambiguity; author-before-title boundary is genuinely hard |
| 1700–1800 and other tier-0 (~82 records) | 2 | Transitional register; guidelines not fully sufficient |
| Tier-1 partial (136 records) | 1 + self-review | Auto-extracted spans constrain boundaries; verify script catches offset errors |
| Tier-2 pre-filled (47 records) | 1 spot-check | ISBD structural rules leave little room for disagreement |

Both annotators on the pre-1700 stratum must have **Early Modern German reading competence** — the credential/title boundary requires understanding the semantic structure of a 16th–17th century title page, which cannot be inferred from modern bibliographic conventions alone. See §7.2 for what this means in practice.

**IAA metric:** use **pairwise span F1**, not Cohen's κ. κ is inflated for NER because unlabeled tokens dominate the denominator and inflate chance agreement (Hripcsak & Rothschild, 2005; Artstein & Poesio, 2008). Treat one annotator as reference and the other as system; compute F1 over exact character-offset + label pairs. Targets: ≥ 0.80 overall; ≥ 0.75 for the pre-1700 PERSON label. These are consistent with the LLM agreement threshold in §5.2.

### 7.2 Annotator qualifications by stratum

German C1 proficiency is sufficient for the modern and 19th-century strata but not for pre-1700. The task splits into two distinct regimes.

**Modern and 19th-century strata — C1 is sufficient**

Post-1800 titles use standard German orthography and modern bibliographic conventions. The annotation decisions are structural (locating ` : ` and ` / `), not lexical. A well-briefed C1 speaker working from the annotation guide can do this reliably.

**Pre-1700 stratum — C1 is not sufficient**

Three things fail with a general C1 annotator on Early Modern German titles:

1. **Orthographic variation.** Pre-standard German has no fixed spelling — common words appear in unfamiliar forms. A C1 speaker trained on modern German may not recognize them, making it harder to locate the credential/title boundary.
2. **Latin mixing.** A substantial share of pre-1700 credential phrases are partly or fully Latin: `Professoris Theologiae ordinarii`, `Philosophi Adepti`, `Sacrosanctae Theologiae Licentiati`. Without basic Latin recognition, the annotator cannot determine whether a phrase is part of PERSON or the opening of the title.
3. **Administrative and ecclesiastical title structures.** Recognizing that `Churfürstl. Sächsischen Probation-Meisters zu Dreßden` is a court-administrative credential — part of PERSON, not part of the work description — requires prior knowledge of the Holy Roman Empire's institutional vocabulary. This is intuitive to someone trained in German history or Germanistik; it is opaque to a general C1 speaker.

**What is needed is disciplinary background, not nativeness.** A non-native speaker with an MA in German studies, German history, or historical theology is more capable than a native speaker with no humanities training. The minimum requirements for the pre-1700 stratum:

- Reading ability in Early Modern German (frühneuhochdeutsch) — not paleography (titles are already transcribed), but recognition of pre-standard orthography and archaic morphology
- Basic Latin recognition — enough to identify that a phrase is Latin and parse its rough structure
- Familiarity with Early Modern academic, ecclesiastical, or administrative titles as naming units

A humanities PhD student (Germanistik, German history, early modern history) typically has all three. This is consistent with HIPE-2022 practice, which used specialized annotators with historical language training rather than general native speakers (Ehrmann et al., 2022).

**Qualification summary by stratum:**

| Stratum | Minimum qualification |
|---|---|
| Modern, 19th-c | C1 + annotation guide training session |
| 1700–1800 | C1 with Early Modern exposure, or humanities student; run 20-record IAA pilot first |
| Pre-1700 | Humanities background with Early Modern German + basic Latin; nativeness not required |

The 1700–1800 stratum is the ambiguous case — German is moving toward standardization but credential conventions are still variable. Run a 20-record IAA pilot with both C1 and humanities-background annotators before committing the full stratum to one profile.

**Domain-comparable precedent:** CLEF-HIPE-2020 and HIPE-2022, the closest comparable benchmarks (historical NER in German and other European languages), used 2 annotators per document with adjudication, reporting IAA F1 of 0.77–0.89 by entity type (Ehrmann et al., 2020; 2022). Named person entities were among the harder ones — consistent with the PERSON challenges in this corpus.

**Minimum viable path (single annotator):** acceptable only for the 183 pre-filled/partial records where ISBD rules tightly constrain the span boundaries. Not acceptable for the 212 manual records. For those, a second annotator on at least the 50-record SR-11 seed is the minimum before running the full batch.

**References**

- Artstein, R., & Poesio, M. (2008). Inter-coder agreement for computational linguistics. *Computational Linguistics*, 34(4), 555–596.
- Ehrmann, M., Romanello, M., Flückiger, A., & Clematide, S. (2020). Extended overview of CLEF-HIPE-2020. *CLEF 2020 Working Notes*, CEUR-WS vol. 2696.
- Ehrmann, M., et al. (2022). HIPE-2022: Naming the past. *CLEF 2022 Working Notes*, CEUR-WS vol. 3180.
- Hripcsak, G., & Rothschild, A. S. (2005). Agreement, the F-measure, and reliability in information retrieval. *Journal of the American Medical Informatics Association*, 12(3), 296–298.
- Pustejovsky, J., & Stubbs, A. (2012). *Natural Language Annotation for Machine Learning*. O'Reilly.
- Snow, R., O'Connor, B., Jurafsky, D., & Ng, A. Y. (2008). Cheap and fast — but is it good? Evaluating non-expert annotations for natural language tasks. *EMNLP 2008*, 254–263.

---

## 8. Blockers and open questions

| Item | Status |
|---|---|
| Annotation tool selection | Unresolved — `doccano`, `Label Studio`, or JSON Lines in a spreadsheet are all viable for 500 records; Label Studio preferred for span annotations |
| Inter-annotator agreement (IAA) | See §7.1 — 2 annotators required for manual queue; span F1 ≥ 0.80 target |
| Pre-1750 annotation examples | See [sr08_annotation-guide.md §4](sr08_annotation-guide.md#4-examples-by-title-structure) — 10 examples with real DDB links; review before starting |
| `silver_tier` column name in corpus | Check actual column name in `df_de_titles.parquet` — may be `tier`, `label_tier`, or `silver_tier` |

# GeMeA — Silver Dataset Pipeline: Summary and General Framework

A synthesis of what has been done to automatically construct a silver NER training dataset from ISBD punctuation rules in 4,477,780 German DDB title strings, including all resolved study/research questions (SRs). The final section extracts a domain-agnostic framework.

**Related notes:** [ner-bibliographic.md](../ner-bibliographic.md), [sr01_isbd-field-rating.md](sr01_isbd-field-rating.md), [sr01_isbd-field-rating-adr.md](sr01_isbd-field-rating-adr.md), [sr01_isbd-applicability.md](sr01_isbd-applicability.md), [sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md), [sr04_translator-person-disambiguation.md](sr04_translator-person-disambiguation.md), [sr10_de-titles-distribution.md](sr10_de-titles-distribution.md), [sr10_title-length-thresholds.md](sr10_title-length-thresholds.md)

---

## 1. What was done

### Phase 0 — Corpus characterisation

**SR-10** ([sr10_de-titles-distribution.md](sr10_de-titles-distribution.md), [sr10_title-length-thresholds.md](sr10_title-length-thresholds.md))

Before doing anything with labels, the corpus was characterised along two dimensions:

- **Provenance.** `DF_DE_TITLES` traced to `2023.11 NER.ipynb` — a language-filtered (dc:language + langid = German) subset of 4,477,780 DDB TEXT objects spanning all eras and dc_types with no length or topic filter.
- **Token length distribution.** Raw distribution of `all_tokens` (spaCy `de_core_news_sm`, includes stopwords + punctuation) and `content_tokens` (stopwords removed). Percentiles: p25=4, p50=8, p75=14. Data-driven length thresholds set at p25/p75 — short ≤4, medium 5–14, long >14.
- **Era-stratified length.** Pre-1750 titles are 42–50% long (median 12–15 tokens) — full bibliographic title pages folded into a single string. Post-1775: shift to median 6–9 tokens (Enlightenment/Romantic publishing convention change). 2000–2024: reversal to 62% medium — digital-born metadata with structured fields.

*Purpose for silver dataset:* stratification variables for sampling and gold set design; establishes that pre-1750 records require different handling.

---

### Phase 1 — Signal detection

**SR-01** (ISBD signal coverage corpus-wide)

`scripts/check_isbd_titles.py` measured the raw occurrence of ISBD punctuation patterns across all 4.47M records:

| Signal | Count | % |
|---|---|---|
| ` :` (subtitle) | 909,869 | 20.3% |
| Trailing `.` (area close) | 783,752 | 17.5% |
| ` ;` (subsequent SoR / series) | 174,813 | 3.9% |
| ` /` (SoR) | 33,907 | 0.8% |
| ` =` (parallel title) | 26,264 | 0.6% |

**Finding:** only 1.2% of records carry the `. -` full area separator. The structural tier is far smaller than expected; heuristic detection must carry the load for 98.8% of records.

**SR-02** (ISBD parser split priority)

` /` (SoR) appears in only 0.8% of titles; ` :` (subtitle) at 20.2% is the dominant signal. The parser must prioritise ` :` splitting for OTHER_TITLE / TITLE boundary, not ` /`.

---

### Phase 2 — Field presence rating and tier assignment

`scripts/rate_isbd_fields.py` ran over all 4.47M records and produced `data/processed/isbd_field_ratings.csv` with binary flags for each ISBD field and a confidence tier.

**Two-tier detection (ADR-02):**
- **Structural tier** (`has_dot_dash = True`): apply area-aware parsing; field boundaries unambiguous
- **Heuristic tier** (`has_dot_dash = False`): apply whole-string regex; reduced precision; PLACE not detected

**Tier assignment (ADR-04 / ADR-06):**

| Tier | Criterion | Count | % |
|---|---|---|---|
| 2 — structural | `has_dot_dash AND f_resp_person AND ≥1 manifestation field` | 4,613 | 0.1% |
| 1 — heuristic | `n_fields ≥ 3` OR `(f_person AND f_year)` | 335,524 | 7.5% |
| 0 — unrated | All others | 4,137,643 | 92.4% |

---

### Phase 3 — Precision validation

**SR-03** ([sr03_silver-label-fp-review.md](sr03_silver-label-fp-review.md))

`scripts/validate_heuristic_fields.py` drew a 200-record stratified sample from tier-1 records (one stratum per flag). `scripts/sr03_fp_review.py` applied automated rules + per-row overrides to label each active flag as TP or FP.

Results (FP rate per field, 15% acceptance threshold):

| Field | FP rate | Decision |
|---|---|---|
| `f_parallel` | ~80% | ❌ Exclude |
| `f_edition` | ~83% | ❌ Exclude |
| `f_person` | ~36% | ⚠️ Sub-classify |
| `f_person_compound` | ~29% | ⚠️ Sub-classify |
| `f_year` | ~6% | ✅ Accept |
| `f_other_title` | ~8% | ✅ Accept |
| `f_publisher`, `f_series`, `f_volume` | ~0% | ✅ Accept |

**Additional finding:** pre-1750 titles place the author name before the main title (not after ` /`), making `f_person` a systematic false negative for that stratum.

---

### Phase 4 — Signal disambiguation

**SR-04** ([sr04_translator-person-disambiguation.md](sr04_translator-person-disambiguation.md))

` /` is not a homogeneous signal. `scripts/validate_translator_disambiguation.py` applied a keyword heuristic to the SoR text and `scripts/evaluate_translator_heuristic.py` evaluated it against 100 manually annotated records.

True class distribution of `f_person = 1` (heuristic tier), mapped to the ISBD/RDA agent model (person | collective agents | role qualifier | non-SoR):

| Category | Entity type | `f_resp_*` flag | % |
|---|---|---|---|
| Person | Individual person (author) | `f_resp_person` | 35% |
| Collective agent | Corporate body | `f_resp_org` | 19% |
| Collective agent | Family name | `f_resp_family` | — (not yet validated) |
| Role qualifier | Editor / adaptor | `f_resp_editor` | 5% |
| Non-SoR | False positive | `f_resp_other` | 41% |
| — | Translator | `f_resp_translator` | 0% |

**Decisions:** TRANSLATOR not viable as a silver label (undetectable from title strings). Corporate bodies (`f_resp_org`) and family names (`f_resp_family`) are **collective agents** — a distinct entity class from individual persons, not noise. `f_person` must be sub-classified before silver label assignment.

---

### Where things stand

| Step | Status | Output |
|---|---|---|
| Corpus characterisation | ✅ Done | Length thresholds, era distribution |
| Signal detection | ✅ Done | Pattern counts, SR-01/02 findings |
| Field rating | ✅ Done | `isbd_field_ratings.csv` (4.47M rows) |
| Precision validation | ✅ Done | Per-field FP rates, accept/exclude decisions |
| Trailing period (SR-05) | ✅ Done | Excluded — 93% FP, zero marginal value |
| SoR disambiguation | ✅ Done | `f_resp_*` sub-classification schema |
| Applicability rules | ✅ Done | Era + dc_type guards |
| Silver span extraction | 🔲 Next | `scripts/build_silver_spans.py` (Phase 0a) |
| Historical language scope (SR-06) | ✅ Done | EARLY_MODERN_DE 93%, LATIN 0.5% — no Latin stratum needed |
| Gold set construction | 🔲 Blocked on SR-07 | Manual annotation |
| NER evaluation | 🔲 Blocked on SR-07 | SR-08 |

---

## 2. General framework

The pipeline above is an instance of a general approach for constructing silver NER datasets from structured text corpora using domain conventions. It has five stages.

---

### Stage 1 — Corpus characterisation

Before writing any detection rules, understand the corpus:

- **Provenance and scope.** Who produced the data, under what standards, in what time period? Standards change; a single corpus may contain multiple cataloguing regimes.
- **Token length distribution.** Compute percentiles; identify natural breakpoints for stratification. Short texts need different models and evaluation methods than long ones.
- **Era / type distribution.** Plot signal coverage and text length by metadata dimension (year, type, source). Signals that work for modern records may fail for historical ones.

*Output:* stratification variables; known failure modes before any rule is written.

---

### Stage 2 — Signal inventory

Enumerate all structural signals that could indicate field boundaries in the domain:

- In bibliographic data: ISBD punctuation (`. -`, ` :`, ` /`, ` =`)
- In legal documents: section numbering, header patterns, defined-term conventions
- In medical records: ICD code markers, section headers, measurement unit patterns
- In scientific papers: citation brackets, figure/table captions, equation labels

For each signal: measure raw coverage, note known ambiguities. Do not assume a signal is reliable — assume the opposite until validated.

*Output:* signal inventory with coverage counts.

---

### Stage 3 — Field presence rating

Convert the signal inventory into binary presence flags per record:

- One flag per candidate field
- Apply signals in priority order (structural > heuristic)
- Assign a **confidence tier** based on how many and which signals are present
- Tier 2 (highest): multiple independent structural signals
- Tier 1 (medium): at least one heuristic signal above a count threshold
- Tier 0 (unrated): insufficient signal

*Key design decisions:*
- Rate only the primary text field (not auxiliary columns) — training/inference consistency (ADR-03)
- Binary flags, not spans — defer span extraction; simpler to validate
- Make tier criteria explicit and falsifiable

*Output:* flag matrix + tier column over full corpus; fast to run (vectorised regex).

---

### Stage 4 — Precision validation

For each flag, measure empirical false-positive rate on a stratified sample:

1. Draw a sample stratified by flag (ensure each flag has representation)
2. For each record, inspect the raw text and annotate each active flag as TP or FP
3. Compute FP rate per flag
4. Apply a threshold (e.g. < 15% FP) to decide: accept / post-filter / exclude

**Sub-classification step.** For any flag with high FP rate due to signal ambiguity (one punctuation mark → multiple entity types), sub-classify using a keyword heuristic and validate the sub-classifier separately:
- Map keyword matches to sub-classes
- Annotate true entity types on a sample
- Measure precision/recall per sub-class
- Assign each sub-class a separate flag

*Output:* per-flag accept/exclude/post-filter decisions; sub-classification schema with validated precision.

---

### Stage 5 — Guard application and span extraction

Apply the validation findings as guards before building the silver dataset:

- **Field exclusion guards:** remove flags that failed the FP threshold entirely
- **Domain guards:** apply field exclusion conditionally on metadata (e.g. exclude `f_edition` for newspaper dc_types)
- **Era guards:** apply different detection strategies for different time periods
- **Sub-classification guards:** use `f_resp_*`-style flags to restrict silver labels to validated entity sub-types

Then extract spans from tier-2 (structural) and filtered tier-1 (heuristic) records using the accepted flags as label sources.

*Output:* `silver_spans.jsonl` — one record per title, with NER span labels derived from structural signals.

---

### Stage 6 (downstream) — Gold evaluation and model training

Silver labels are noisy by construction. The pipeline must close with a gold evaluation set:

- **Stratified sample** across tier, era, length, and dc_type
- **Manual annotation** using guidelines that account for known failure modes (e.g. pre-1750 author placement)
- **Separate evaluation by stratum** — do not aggregate F1 across structurally different sub-populations
- **Decision gate** before committing to a model: if zero-shot NER (e.g. NuNER Zero) meets the threshold, skip fine-tuning; else use silver + LLM-labeled data to fine-tune

---

### Framework summary

```
Corpus characterisation
        ↓
  Signal inventory          ← domain conventions (ISBD, legal codes, etc.)
        ↓
  Field presence rating     ← binary flags + confidence tiers
        ↓
  Precision validation      ← stratified sample, FP rates, accept/exclude
        ↓
  Sub-classification        ← keyword heuristic for ambiguous signals
        ↓
  Guard application         ← field, domain, era guards
        ↓
  Silver span extraction    ← tier-2 structural + filtered tier-1 heuristic
        ↓
  Gold evaluation           ← stratified manual annotation + F1 by stratum
        ↓
  Model training / zero-shot evaluation
```

**What makes this replicable:**
- The approach requires only: a large corpus, a domain convention with structural signals, and metadata for stratification
- Each stage produces a falsifiable artifact (flag matrix, FP rate table, sub-classification precision table) — not just a dataset
- Validation is built into the pipeline, not bolted on at the end
- The confidence tier system makes data quality explicit at every downstream step
- Failure modes discovered during validation feed back into corpus characterisation (e.g. era-specific guards), making the pipeline self-documenting

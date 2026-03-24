# GeMeA — Field-Level Weighting for Silver Tier Assignment (SR-11)

**SR-11** in [ner-bibliographic.md](../ner-bibliographic.md).

---

## 1. Background

The current three-tier silver assignment uses binary threshold logic: `n_fields ≥ 3` OR `(f_person AND f_year)` for tier 1. All fields above the FP exclusion threshold (≤83% FP) contribute equally regardless of their measured reliability. SR-03 established per-field FP rates for five fields; the remaining fields with non-negligible coverage have not been sampled. Field-level weighting would replace the binary threshold with a precision-weighted score, enabling a principled four-tier split and more accurate tier-boundary calibration.

---

## 2. Requirements

### 2.1 FP rates for all candidate fields

SR-03 sampled five fields. Status:

| Field | Coverage | SR-03 FP rate | Status |
|---|---|---|---|
| `f_year` | 14.6% | 6% | ✅ Done |
| `f_other_title` | 20.2% | 8% | ✅ Done |
| `f_person` | 0.8% | 36% (pre-sub-classification) | ✅ Done (SR-04 sub-classification pending) |
| `f_edition` | 3.6% | 83% | ✅ Done — excluded |
| `f_parallel` | 0.6% | 80% | ✅ Done — excluded |
| `f_volume` | 1.9% | — | ❌ Not sampled |
| `f_publisher` | 0.2% | — | ❌ Not sampled |
| `f_place` | 0.1% | — | ❌ Not sampled (structural-only; likely low FP) |
| `f_series` | 0.0% | — | ❌ Not sampled (too sparse to matter) |

Minimum additional sampling needed: `f_volume` and `f_publisher` (~100 records each, uniform random sample from records where each field fires).

### 2.2 Precision-based weight per field

Each included field gets a weight:

```
weight_i = 1 − FP_rate_i  (= estimated precision)
```

The composite score for a record is the sum of weights across its active fields:

```
score(r) = Σ weight_i  for all i where field_i(r) = 1
```

This is a simple additive model. A multiplicative model (product of precisions = probability of all fields being true simultaneously, assuming independence) is an alternative but more conservative — the additive model is appropriate when co-occurring fields provide independent evidence.

### 2.3 Calibration dataset for tier boundary

The score threshold separating "usable augmentation" from "discard" cannot be derived from FP rates alone. Calibration options:

- **Internal**: use tier-2 records (known-good, structural) as positive anchors; sample tier-0 records as negatives; find the score that maximises separation.
- **External**: once SR-07 gold set exists, measure NER F1 for models trained at different score cutoffs and select the elbow.

The external method is preferred — it directly measures annotation quality impact rather than proxy precision metrics. It requires SR-07 to be completed first.

### 2.4 Conditional FP rates (optional, higher priority if adding a fourth tier)

Current FP estimates treat fields as independent. They are likely not: `f_year` firing alone (date in title string) is less reliable than `f_year AND f_other_title` co-occurring (subtitle + date structure). A joint sample (~100 records per high-frequency field pair) is needed to quantify interaction effects.

This is optional for a three-tier refinement but required to justify a four-tier split based on score ranges.

---

## 3. Proposed scoring scheme (draft)

Using current FP rate estimates for included fields:

| Field | Estimated precision | Weight |
|---|---|---|
| `f_other_title` | 0.92 | 0.92 |
| `f_year` | 0.94 | 0.94 |
| `f_person` (sub-classified) | ~0.64 (post-SR-04 filter) | 0.64 |
| `f_volume` | TBD | — |
| `f_publisher` | TBD | — |
| `f_place` | TBD (structural; likely ~0.9) | — |
| `has_dot_dash` | ~1.00 (structural) | 1.00 |

A record with `f_year + f_other_title + f_person` would score ~2.50 — clearly above any reasonable tier-1 threshold. A record with only `f_year` would score ~0.94 — at risk of falling below threshold depending on calibration.

---

## 4. Relationship to current tier logic

The current binary tier-1 threshold (`n_fields ≥ 3` OR `f_person AND f_year`) is approximately equivalent to a score cutoff of ~1.9 (three average-weight fields) or the specific pair f_person + f_year (~1.58). Field-level weighting would make this cutoff explicit and adjustable, and would naturally down-weight any future field with a higher measured FP rate.

A four-tier split (e.g., tier 1a: score ≥ 2.5, tier 1b: 1.5 ≤ score < 2.5) is the primary motivation for this SR — it allows curriculum learning in fine-tuning (train first on high-confidence records, then add lower-confidence augmentation).

---

## 5. Blocked on

- SR-03 extension: `f_volume` and `f_publisher` FP sampling (~200 additional records)
- SR-04 completion: `f_person` sub-classification precision finalised
- SR-07 completion (for external calibration of tier boundary)

# GeMeA — Historical and Latin Title Scope (SR-06)

**SR-06** in [ner-bibliographic.md](../ner-bibliographic.md).

---

## 1. Background

NER fallback applies to ~71% of DF_DE_TITLES records (the share with no ISBD markers; see SR-01). An unknown proportion of these are Latin or Early Modern German — both require different tokenisation, different model capabilities, and potentially different annotation strategies than modern German. This study estimates that proportion for two high-prevalence historical strata, and evaluates the accuracy of a heuristic language classifier.

---

## 2. Method

### 2.1 Stratum selection

Two strata were selected as high-density proxies for historical records in DF_DE_TITLES. Script: [sr06_historical_scope.py](../../scripts/sr06_historical_scope.py).

| Stratum | Filter | Total records | Tier-0 records | Rationale |
|---|---|---|---|---|
| A — Leichenpredigt | `dc_type` contains "Leichenpredigt" | 11,255 | 4,809 (43%) | Funerary sermons; nearly all pre-1750; known to contain Latin scripture and Early Modern German prose; the most historically homogeneous dc_type in DF_DE_TITLES |
| B — Monografie pre-1800 | `dc_type == "Monografie"` AND `year_num < 1800` | 175,094 | 145,268 (83%) | Broad historical monograph category; spans 1500–1799; includes legal texts, academic dissertations, religious tracts, administrative documents — the widest coverage of pre-modern production types |

Strata were chosen to span the two dominant historical production contexts: devotional/funerary (Leichenpredigt, mostly 1600–1750) and scholarly/administrative (Monografie, 1500–1799). Other potentially relevant dc_types (e.g. pre-1800 Periodika, Handschrift, Einblattdruck) were excluded from this study; their language distributions may differ.

**Year filter for Stratum B:** `year_num` is derived from `pd.to_numeric(df["dates"], errors="coerce")` — a best-effort parse of the free-text `dates` field. Records with non-numeric or missing dates are excluded from Stratum B; they would not be in the tier-0 historical fallback in any case.

**No tier filter applied:** both strata include tier-0, tier-1, and tier-2 records. The study targets language scope, not silver label quality; all records are valid regardless of tier.

### 2.2 Sampling

100 records drawn from each stratum by uniform random sampling (seed 42), giving n=200 total. The split is **equal** despite the size imbalance (Leichenpredigt 11k vs Monografie pre-1800 175k) — a deliberate choice to ensure Leichenpredigt, the smaller but historically denser stratum, contributes meaningfully to the analysis. Proportional sampling would have given Leichenpredigt only ~12 records.

### 2.3 Classification

A heuristic classifier ([sr06_historical_scope.py](../../scripts/sr06_historical_scope.py)) assigned each title one of four classes: **LATIN**, **EARLY_MODERN_DE**, **GERMAN**, **OTHER**. A stricter true-class annotator ([sr06_evaluate_historical.py](../../scripts/sr06_evaluate_historical.py)) was then applied to measure heuristic accuracy. True-class annotation rules are documented in the script header.

### 2.4 Is n=200 sufficient?

Each observed proportion p̂ = k/n is treated as a Bernoulli trial estimate. The Wilson interval is used rather than the Wald interval (p̂ ± 1.96√(p̂(1−p̂)/n)) because Wald is unreliable when p̂ is near 0 or 1 — it can produce negative lower bounds and undercovers the true proportion. Wilson conditions on the hypothetical true proportion p rather than p̂, giving valid coverage across the full [0,1] range. For the LATIN finding (k=1, n=200), this distinction is material: Wald gives [0%, 1.5%] with a clipped lower bound, while Wilson gives [0.01%, 2.8%].

For the key findings, 95% confidence intervals (Wilson interval — Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *Journal of the American Statistical Association*, 22(158), 209–212):

| Finding | Observed | 95% CI | Decision sensitivity |
|---|---|---|---|
| EARLY_MODERN_DE prevalence | 93% (186/200) | [88.5%, 96.1%] | Even at lower bound (88.5%), conclusion — Early Modern German is dominant — holds |
| LATIN prevalence | 0.5% (1/200) | [0.01%, 2.8%] | Upper bound confirms Latin is < 3% — sufficient to rule out a dedicated Latin stratum |
| Heuristic overall accuracy | 91% (182/200) | [86.3%, 94.2%] | Precision/recall estimates reliable to ±4% |
| LATIN heuristic FP rate | 83% (11/13 FPs among heuristic-LATIN) | [52%, 98%] | Wide CI due to small n (12 heuristic-LATIN); directionally correct but exact rate uncertain |

**Why n=200 is enough.** Sufficiency depends on the decision being made, not on CI width alone. The two decisions here are binary thresholds:

1. *Is Early Modern German dominant enough to be the primary training target?* — requires knowing prevalence is well above some meaningful threshold, say 70%. The lower CI bound is 88.5%, clearing 70% by 18 percentage points. No additional samples would change this conclusion.

2. *Is Latin rare enough to exclude from the gold set?* — requires knowing prevalence is well below a useful stratification threshold, say 5%. The upper CI bound is 2.8%, comfortably below 5%. Again, additional samples would only narrow the interval further in the same direction.

Both decisions are robust because the observed proportions are extreme (93% and 0.5%), not near the decision boundary. Extreme proportions require fewer observations to establish — the variance of a proportion estimator is p(1−p)/n, which is maximised at p=0.5 and small near 0 or 1. Had the results been, say, EARLY_MODERN_DE 55% and LATIN 8%, n=200 would not have been sufficient to distinguish signal from noise.

**Conclusion:** n=200 is sufficient for the decision this study supports — determining whether a Latin stratum is needed in the gold set (SR-08) and confirming Early Modern German as the primary historical challenge. It is **not** sufficient for precise per-class prevalence estimates publishable as corpus statistics; a larger stratified sample (n≥500 per stratum) would be needed for that.

**Unsampled strata:** Leichenpredigt and pre-1800 Monografie represent ~186k records. Pre-1800 Periodika, Handschrift, and Einblattdruck are not covered. Their language distribution may skew differently (e.g. Handschrift may have higher Latin prevalence). Flag for SR-08 gold set design if these dc_types are included.

---

## 3. Results

### 3.1 Heuristic output (sr06_historical_scope.py)

| Class | Count | % |
|---|---|---|
| EARLY_MODERN_DE | 182 | 91% |
| LATIN | 12 | 6% |
| GERMAN | 5 | 2% |
| OTHER | 1 | 0% |

### 3.2 True-class distribution (sr06_evaluate_historical.py)

| Class | Count | % |
|---|---|---|
| EARLY_MODERN_DE | 186 | 93% |
| GERMAN | 12 | 6% |
| LATIN | 1 | 0.5% |
| OTHER | 1 | 0.5% |

### 3.3 Per-class heuristic accuracy

| Class | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| EARLY_MODERN_DE | 0.962 | 0.941 | 0.951 | 175 | 7 | 11 |
| GERMAN | 1.000 | 0.417 | 0.588 | 5 | 0 | 7 |
| LATIN | 0.083 | 1.000 | 0.154 | 1 | 11 | 0 |
| OTHER | 1.000 | 1.000 | 1.000 | 1 | 0 | 0 |

Overall agreement: **182/200 (91%)**.

### 3.4 Per-stratum true-class distribution

| Stratum | EARLY_MODERN_DE | GERMAN | LATIN | OTHER |
|---|---|---|---|---|
| Leichenpredigt (n=100) | 99 | 0 | 0 | 1 |
| Monografie_pre1800 (n=100) | 87 | 12 | 1 | 0 |

---

## 4. Error analysis

### 4.1 LATIN false positives (11/12 — 83% FP rate)

The heuristic classifies 12 records as LATIN; only 1 is a true Latin text. Three triggering patterns account for all 11 false positives:

| Pattern | Count | Example |
|---|---|---|
| `Anno` + pre-1600 year (single-hit rule) | 5 | `Romischer kayserlicher Maiestat Regiment … Anno MVCX…` — Early Modern German legal text with `Anno` as a date label |
| `Jesu` / `Christi` / `Doctor` in Leichenpredigt title | 5 | `Christliche Leichpredigt. Uber die Wort Petri … Von diesem (Jesu) …` — these are standard German Protestant devotional vocabulary, not Latin text |
| `Doctor` + `Christi` together | 1 | `Ein nützliche Sermon Doctor Martini Luthers … von dem reych Christi` |

All 11 misclassified records are **Early Modern German** texts. Latin terms embedded in otherwise German titles do not make the title Latin.

### 4.2 EARLY_MODERN_DE false positives (7 — 4% FP rate)

Seven records classified as EARLY_MODERN_DE are true GERMAN:

| Trigger | Count | Notes |
|---|---|---|
| `[ck]h\w+` cluster (e.g. "Heilige", "höffliche") | 4 | Historical cluster pattern fires on common German words — too broad |
| `Herrn` (dative "Herr") | 1 | Used in modern German as well as early modern |
| Year < 1700 (year-only rule) | 1 | `Antwort Sir Eduard Turners … anno 1664` — English-language pamphlet translated to German; no spelling markers |
| `D.` abbreviation | 1 | Academic title abbreviation, not a spelling marker |

### 4.3 True LATIN record

One genuinely Latin record in the sample: a 1769 alchemical treatise (*Delarvatio Tincturae Philosophorum*) with multiple Latin morphological endings (`-atio`, `-orum`). Mixed Latin-German title with "Das ist:" introducing a German subtitle.

---

## 5. Key findings

1. **Latin is not a meaningful training challenge for this stratum.** True prevalence is ~0.5% (1/200). The heuristic's 83% FP rate arises because `Anno`, `Christi`, `Jesu`, and `Doctor` are standard German Protestant/academic vocabulary — not reliable Latin indicators in isolation.

2. **The corpus is overwhelmingly Early Modern German.** 93% of historical records use early-modern German spelling and vocabulary. Leichenpredigt is 99% Early Modern German; pre-1800 Monografie is 87%.

3. **EARLY_MODERN_DE heuristic is broadly reliable (F1 = 0.95)** but the `[ck]h\w+` cluster pattern fires on ordinary German words ("Heilige", "höffliche", "nach") — this contributes false positives in the 1700–1800 range where early modern markers are absent.

4. **"Year < 1700" fallback causes 1 FP** (translated English pamphlet); year-only detection without spelling markers is unreliable for non-German texts.

5. **GERMAN is underdetected (recall 0.42)** — 7 records with years 1664–1793 and no early-modern markers were correctly classified as GERMAN by the true annotator but caught as EARLY_MODERN_DE by the heuristic's `[ck]h\w+` pattern.

---

## 6. Decisions

### D1 — Drop LATIN as a heuristic class for this stratum

LATIN prevalence is ~0.5% with 83% FP rate. The heuristic cannot distinguish Latin terms embedded in German titles from true Latin texts without syntactic analysis. For gold set purposes, LATIN records are rare enough to be identified manually if needed.

**Action:** Remove LATIN class from the historical language heuristic. Records with embedded Latin vocabulary are Early Modern German and should be labelled as such.

### D2 — Restrict `[ck]h\w+` to word-initial position and minimum 5 characters

The cluster pattern fires on internal occurrences like "Heilige" (`ch`), "höffliche" (`ch`). Restricting to word-initial `[ck]h` (e.g. "khuon", "Churfürst") would be more historically specific.

**Action:** Update `EARLY_MODERN_DE` regex in `sr06_historical_scope.py`; rerun and verify FP rate drops.

### D3 — Remove `Herrn` from EARLY_MODERN_DE markers

`Herrn` (dative of `Herr`) is standard modern German, not an early modern marker.

**Action:** Remove from regex pattern.

### D4 — Gold set implication: no Latin stratum needed

SR-08 gold set design does not need a dedicated Latin stratum. Early Modern German is the primary historical challenge. The gold set should include a **pre-1700** stratum (long-form Leichenpredigt and legal/administrative Monografie) as a proxy for the full historical register.

---

## 7. Impact on model selection

The NER model does not need Latin capability for the historical stratum. Early Modern German (1500–1750) is the key challenge:

- Long, complex title-page transcriptions (median 15–20 tokens, some >50)
- Author name + credentials placed *before* the title (not after ` /`) — a structural false negative for `f_person`; see SR-03 §5
- Non-standard orthography (`vnd`, `seyn`, `deß`) tokenised differently by modern German tokenisers

Fine-tuning on a pre-1750 stratum is the appropriate path, but the **current silver dataset is not sufficient**:

- Pre-1750 records are almost entirely tier-0 — no `. -` markers, no `f_person` (author-before-title pattern), so `rate_isbd_fields.py` produces no silver labels for this stratum
- Fine-tuning on modern silver data alone will not expose the model to early modern orthography or the name-before-title structure

**What is needed:** the SR-08 gold set (pre-1700 stratum, human-annotated) or LLM-labeled pre-1750 records as an interim (see [ner-bibliographic.md §8.2](../ner-bibliographic.md)).

**Model choice:** `xlm-roberta-base` (or `-large`) is preferred over monolingual German models (`gbert-large`) — multilingual pretraining covers early modern orthography variation better, and aligns with the decision in [ner-bibliographic.md §5](../ner-bibliographic.md). Dedicated Latin NER models (e.g. LatinBERT) are not required — true Latin prevalence is ~0.5%.

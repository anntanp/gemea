# GeMeA — Historical and Latin Title Scope (SR-06)

**SR-06** in [ner-bibliographic.md](../ner-bibliographic.md).

---

## 1. Background

NER fallback applies to ~71% of DF_DE_TITLES records (the share with no ISBD markers; see SR-01). An unknown proportion of these are Latin or Early Modern German — both require different tokenisation, different model capabilities, and potentially different annotation strategies than modern German. This study estimates that proportion for two high-prevalence historical strata, and evaluates the accuracy of a heuristic language classifier.

---

## 2. Method

`scripts/sr06_historical_scope.py` sampled 200 records from two strata:

| Stratum | Filter | Total records | Tier-0 records |
|---|---|---|---|
| A — Leichenpredigt | `dc_type` contains "Leichenpredigt" | 11,255 | 4,809 |
| B — Monografie pre-1800 | `dc_type == "Monografie"` AND `year < 1800` | 175,094 | 145,268 |

100 records sampled from each stratum (seed 42). A heuristic classifier assigned one of four classes: **LATIN**, **EARLY_MODERN_DE**, **GERMAN**, **OTHER**.

`scripts/sr06_evaluate_historical.py` applied a stricter true-class annotator and computed agreement with the heuristic. True-class annotation rules are documented in the script header.

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

SR-07 gold set design does not need a dedicated Latin stratum. Early Modern German is the primary historical challenge. The gold set should include a **pre-1700** stratum (long-form Leichenpredigt and legal/administrative Monografie) as a proxy for the full historical register.

---

## 7. Impact on model selection

The NER model does not need Latin capability for the historical stratum. Early Modern German (1500–1750) is the key challenge:

- Long, complex title-page transcriptions (median 15–20 tokens, some >50)
- Author name + credentials placed *before* the title (not after ` /`) — a structural false negative for `f_person`; see SR-03 §5
- Non-standard orthography (`vnd`, `seyn`, `deß`) tokenised differently by modern German tokenisers

A `gbert-large` or `xlm-roberta-base` fine-tuned on a pre-1750 stratum is appropriate. Dedicated Latin NER models (e.g. LatinBERT) are not required at this scale.

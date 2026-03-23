# GeMeA — TRANSLATOR / PERSON Disambiguation (SR-04)

**SR-04** in [ner-bibliographic.md](ner-bibliographic.md).

---

## 1. Question

` /` (Statement of Responsibility) fires for PERSON (author), TRANSLATOR, EDITOR, and non-SoR contexts. Can a keyword heuristic reliably split TRANSLATOR from PERSON before using either as a distinct silver label?

---

## 2. Method

`scripts/validate_translator_disambiguation.py` classifies the SoR text (string after ` /`) into:

- `TRANSLATOR` — *übersetzt*, *Übers.*, *Übertragung*, *übertragen*, *aus dem [language]*, *transl.*, *translated*
- `EDITOR` — *Hrsg.*, *herausgegeben*, *hg.*, *bearb.*, *edited by*, *zusammengestellt*
- `PERSON` — no keyword matched; assumed author
- `OTHER` — ` /` is not a SoR (false positive)

Pool: **28,570** heuristic-tier records with `f_person = 1` (no area separator).

`scripts/evaluate_translator_heuristic.py` evaluates the heuristic against manual `true_class` annotations in `data/processed/translator_validation_sample.csv`.

---

## 3. Results — 100-record sample

**True class distribution:**

| true_class | Count | % |
|---|---|---|
| OTHER | 41 | 41% |
| PERSON | 35 | 35% |
| CORPORATE | 19 | 19% |
| EDITOR | 5 | 5% |
| TRANSLATOR | 0 | 0% |

**Heuristic precision / recall / F1:**

| Class | Precision | Recall | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| TRANSLATOR | 0.00 | 0.00 | 0.00 | 0 | 3 | 0 |
| EDITOR | 0.00 | 0.00 | 0.00 | 0 | 0 | 5 |

**Confusion matrix (rows = true_class, cols = heuristic_class):**

| | PERSON | TRANSLATOR |
|---|---|---|
| CORPORATE | 19 | 0 |
| EDITOR | 2 | 3 |
| OTHER | 41 | 0 |
| PERSON | 35 | 0 |
| TRANSLATOR | 0 | 0 |

---

## 4. Key findings

1. **TRANSLATOR label is not viable** from `f_person` heuristic — zero true translators in 100 records. The corpus has very few translated works with explicit SoR markers in the title string; translators are absent from the title or recorded in separate metadata fields.

2. **PERSON is heavily contaminated** — only 35% of `f_person` records are true author SoRs. The remaining 65%: non-SoR false positives (41%), corporate bodies (19%), editors (5%). Consistent with the SR-03 `f_person` FP rate (~36% on the structural+heuristic pool).

3. **3 heuristic TRANSLATOR hits are all true EDITOR** — Hrsg. and bearb. keywords fired; the heuristic has no translator-specific signal at all in the sample.

4. **EDITOR detection is low-recall** — `(Hg.)` suffix and `bearb.` appearing in the title body (not SoR text) were missed by the regex.

5. **Corporate body SoRs are a large unhandled class** (19%) — government agencies, statistical offices, research centres named after ` /`. No current label covers this.

---

## 5. Decision

- **TRANSLATOR:** do not use as a silver label from `f_person` records — undetectable from title strings in this corpus.
- **EDITOR:** do not use as a silver label without extending the keyword list to handle suffix patterns (`(Hg.)`) and body-text `bearb.`.
- **PERSON:** restrict to records where the SoR text matches a personal name pattern and does not match known corporate-body signals — consistent with the SR-03 post-filtering requirement.
- **CORPORATE:** surface as a new candidate label for ` /`-flagged records where the SoR names an institution; not in scope for the current label set but worth noting for SR-07 gold set design.

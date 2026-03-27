# SR-09 — NuNER Zero Tier-2 Sanity Check

**Purpose:** Pilot evaluation of NuNER Zero on tier-2 pre-filled records, using ISBD-derived silver spans as pseudo-gold. Confirms whether NuNER Zero produces plausible output on DDB title strings before committing to full gold annotation.

**Script:** `scripts/sr09_eval_nuner_tier2.py`
**Output:** `data/processed/sr09_nuner_tier2_results.csv`

---

## 1. What this is (and is not)

**Is:** A fast sanity check. Tier-2 records have deterministic ISBD-derived spans (high-confidence silver labels). Using them as pseudo-gold requires no annotation and takes minutes to run.

**Is not:** The paper evaluation. Tier-2 records (0.1% of corpus) are the *easiest* stratum — fully structured ISBD with `. -` area separator. Performance here will be optimistic relative to tier-0 (92.4% of corpus), and pre-1700 has zero tier-2 records, so the hardest era is unrepresented.

**Decision gate:** If NuNER Zero fails badly on tier-2 (e.g. TITLE F1 < 0.60), it is broken on this domain and the fallback to LLM annotation + fine-tuned XLM-R is triggered immediately. If it performs well, full gold annotation proceeds.

---

## 2. Input

- `data/annotation/sr08_gold_prefilled.jsonl` filtered to `annotation_status == "pre-filled"` (tier-2 records only)
- Gold spans: ISBD-derived silver labels (`spans` field) — TITLE, OTHER_TITLE, PERSON

Tier-2 criterion: `has_dot_dash AND f_person AND ≥1 of {place, publisher, year, series}`. These are fully structured ISBD records; the TITLE boundary is unambiguous.

---

## 3. Label prompts

NuNER Zero takes entity types as natural language strings at inference. Prompts used:

| Our label | Prompt passed to NuNER Zero |
|---|---|
| `TITLE` | `"title of a book, work, or publication"` |
| `OTHER_TITLE` | `"subtitle or other title information"` |
| `PERSON` | `"person name or author name"` |

These are deliberately generic — NuNER Zero was trained on English C4 + GPT-3.5 data and has never seen ISBD strings. More specific prompts (e.g. `"main title in an ISBD bibliographic record"`) can be tested but are not the baseline.

---

## 4. Metric

**Exact span match F1** per label — a prediction is correct only if `start`, `end`, and `label` all match the gold span exactly. Partial overlaps do not count. Same protocol as the paper evaluation (spiel_ner.md §5.1).

Reported: precision, recall, F1 per label. No macro or micro average.

---

## 5. Expected range

| Label | Expected F1 range | Reasoning |
|---|---|---|
| TITLE | 0.70–0.90 | Tier-2 titles are short and well-structured; `. -` cuts off everything after the title area cleanly |
| OTHER_TITLE | 0.50–0.80 | Depends on whether NuNER Zero picks up the subtitle after ` : ` |
| PERSON | 0.40–0.75 | SoR strings after ` / ` are often verbose ("von Goethe, Johann Wolfgang"); exact boundary match is strict |

These are rough priors based on the HIPE-2022 sonar benchmark (best system F1 0.529 on German 19C newspaper NER without a train set). Tier-2 is structurally easier but the domain gap is large.

---

## 6. Pass / fail criteria

| Outcome | TITLE F1 | Interpretation |
|---|---|---|
| Pass | ≥ 0.70 | NuNER Zero is viable; proceed to full gold annotation (SR-09 proper) |
| Marginal | 0.55–0.70 | Inspect failures; consider revised label prompts before deciding |
| Fail | < 0.55 | NuNER Zero broken on this domain; trigger LLM annotation + XLM-R fine-tuning fallback |

---

## 7. How to run

```bash
# Install gliner if not already installed
pip install gliner

# Run the sanity check (default threshold 0.5)
python3 scripts/sr09_eval_nunerzero_tier2.py

# With custom threshold
python3 scripts/sr09_eval_nunerzero_tier2.py --threshold 0.4

# With explicit model ID (correct casing)
python3 scripts/sr09_eval_nunerzero_tier2.py --model numind/NuNer_Zero

# Save detailed per-record output
python3 scripts/sr09_eval_nunerzero_tier2.py --detail data/processed/sr09_detail.jsonl
```

---

## 8. Results (2026-03-27)

### 8.1 Prompt set: `default`

| Label | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| TITLE | 0.000 | 0.000 | 0.000 | 0 | 145 | 47 |
| OTHER_TITLE | 0.000 | 0.000 | 0.000 | 0 | 14 | 15 |
| PERSON | 0.000 | 0.000 | 0.000 | 0 | 253 | 45 |

**Failure mode:** wrong granularity. The model fires at token level — `"Rastegar"`, `"Nosratollah"`, `"Uto"`, `"von"`, `"Melzer"` as separate PERSON spans — rather than extracting the full bibliographic field. TITLE predictions are individual content words (`"österreichischen"`, `"Iranisten"`), not the full title span. Zero exact matches across all labels.

### 8.2 Prompt set: `structural`

Prompts explicitly referenced ISBD separators (` / `, ` : `).

| Label | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| TITLE | 0.000 | 0.000 | 0.000 | 0 | 0 | 47 |
| OTHER_TITLE | 0.000 | 0.000 | 0.000 | 0 | 0 | 15 |
| PERSON | 0.000 | 0.000 | 0.000 | 0 | 1 | 45 |

**Failure mode:** no predictions. ISBD-specific language in the prompts is unfamiliar to the model (trained on English C4); all confidence scores fall below the 0.5 threshold. The single PERSON FP is a spurious low-confidence hit.

### 8.3 Prompt set: `catalog`

Prompts described field roles in library catalog context.

| Label | P | R | F1 | TP | FP | FN |
|---|---|---|---|---|---|---|
| TITLE | 0.000 | 0.000 | 0.000 | 0 | 0 | 47 |
| OTHER_TITLE | 0.000 | 0.000 | 0.000 | 0 | 0 | 15 |
| PERSON | 0.000 | 0.000 | 0.000 | 0 | 6 | 45 |

**Failure mode:** same as `structural` — domain-specific language suppresses scores below threshold; nearly no predictions.

### 8.4 Interpretation

The two runs jointly rule out prompt engineering as a fix:

- Generic prompts → fires at token level, wrong granularity, 0 TP
- Domain-specific prompts → scores too low to cross threshold, 0 predictions

The root cause is architectural: NuNER Zero is a token classifier trained on English newswire-style NER. It has no concept of bibliographic field segmentation — it cannot learn from the prompt alone that `Rastegar, Nosratollah, Uto von Melzer` at the start of an ISBD string is the TITLE field, not a list of person names.

**Verdict: FAIL.** TITLE F1 = 0.000, well below the 0.55 threshold. NuNER Zero zero-shot is not viable for ISBD bibliographic segmentation.

**Next step:** LLM annotation of the gold set → fine-tune `xlm-roberta-base`.

---

## 9. Limitations of this evaluation

- **Tier-2 bias:** results are optimistic. The model sees the easiest records in the corpus.
- **No pre-1700:** zero tier-2 records — the hardest era is entirely absent from this check.
- **Silver pseudo-gold:** the "gold" spans are ISBD-derived, not human-annotated. If the silver label is wrong (e.g. a false-positive ` : ` that is not a real subtitle), the model is penalised for a correct prediction.
- **English-only training:** NuNER Zero has never seen German, historical text, or ISBD strings. Prompt wording can affect results significantly.

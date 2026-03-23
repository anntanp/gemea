# GeMeA — Title Length Category Thresholds

**Applies to:** `scripts/analyse_title_lengths.py`, gold set stratification (SR-07), NER evaluation (SR-08)
**Source data:** `data/DF_DE_TITLES_20240125b.pkl` — 4,477,780 German DDB titles
**Token count column:** `all_tokens` (pre-computed spaCy `de_core_news_sm` token count, includes stopwords and punctuation)

---

## Decision

| Category | Threshold | Basis |
|---|---|---|
| **Short** | ≤ 4 tokens | p25 |
| **Medium** | 5–14 tokens | p25–p75 |
| **Long** | > 14 tokens | above p75 |

Thresholds are the **quartile boundaries** (p25 = 4, p75 = 14) of the `all_tokens` distribution across the full corpus. This produces equal-sized outer groups (≈25% each) and a 50% middle band, grounded in the data rather than arbitrary round numbers.

---

## Empirical basis

Script: `scripts/explore_token_distribution.py` — output: `output/fig_token_distribution.png`, `output/token-distribution.json`.

**Tokenization.** `all_tokens` and `content_tokens` were pre-computed in `2023.11 NER.ipynb` using the spaCy `de_core_news_sm` pipeline. `all_tokens` is the total token count after spaCy tokenization — includes stopwords and punctuation, which spaCy attaches as separate tokens (e.g. `,`, `.`, `:`, `/` each count as one token). `content_tokens` is the count after removing spaCy's stopword list (`token.is_stop`); punctuation tokens are retained in `content_tokens` unless explicitly filtered. The `de_core_news_sm` tokenizer handles German-specific splitting (e.g. separating clitics, punctuation) — token counts are therefore not equivalent to simple whitespace splits, and will differ slightly from `str.split()` counts, particularly for titles with ISBD punctuation (` :`, ` /`, `. -`).

Percentile table (`all_tokens`):

| Percentile | all_tokens | content_tokens |
|---|---|---|
| p10 | 2 | 1 |
| p25 | 4 | 2 |
| p33 | 5 | 3 |
| p50 | 8 | 5 |
| p66 | 12 | 6 |
| p75 | 14 | 8 |
| p90 | 24 | 13 |
| p95 | 36 | 19 |
| p99 | 74 | 40 |

Resulting corpus split:

| Category | Count | % |
|---|---|---|
| Short (≤ 4) | 1,269,034 | 28.3% |
| Medium (5–14) | 2,110,610 | 47.1% |
| Long (> 14) | 1,098,136 | 24.5% |
| **Total** | **4,477,780** | **100%** |

Distribution shape: roughly flat from 1–9 tokens (5–8% each, peaking at 4 tokens with 8.0%), then steadily declining. Notable bump at 20 tokens (1.9% vs. 1.3% at 19 and 1.0% at 21) — likely a truncation artifact in source data.

---

## Alternatives considered and rejected

| Option | Short | Medium | Long | Reason rejected |
|---|---|---|---|---|
| Arbitrary (original) | ≤ 5 | 6–20 | > 20 | No empirical basis; "long" = only top 13% |
| Terciles | ≤ 5 (p33) | 6–12 | > 12 | "Long" = top 34%, too broad |
| Tail-focused | ≤ 5 (p33) | 6–24 | > 24 | Reserves "long" for top 10%; useful for outlier analysis but obscures the gradient |
| **Quartiles** | ≤ 4 (p25) | 5–14 | > 14 | **Selected** — equal outer groups, natural shoulder at p75 |

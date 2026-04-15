# GeMeA — Architecture Decision Record: Corpus Source for NER Analysis

**Format:** MADR (Markdown Architecture Decision Record)
**Subject:** Primary corpus source for SR-10/SR-11 distribution analysis and downstream NER pipeline
**Status:** Accepted

---

## ADR-02 — Replace `DF_DE_TITLES_20240125b.pkl` with `s2_meta_de_content.parquet`

**Status:** Accepted
**Date:** 2026-04-14

### Context

All SR-10 and SR-11 analysis scripts were built against `data/DF_DE_TITLES_20240125b.pkl`, a pickle snapshot produced by `2024.01 MT-QA.ipynb`. This pkl applied two filters on top of the raw DDB corpus:

1. `dc:language = ger` **AND** `langid = ger` (dual German filter)
2. `hierarchy_type = content` (a narrower htype filter than ADR-01)

Resulting population: **4,477,780 titles**, tokenized with spaCy (model unspecified).

This source has two known problems:

**Problem 1 — Stale htype filter.** The pkl's `hierarchy_type = content` filter differs from ADR-01 (BLANKET_EXCLUDE of 8 specific htypes). The pkl excluded types that ADR-01 retains, and may have retained types ADR-01 excludes. The GND linking pipeline (`link_gnd_works.py`) runs against `s2_meta_de_content.parquet`; analysis artifacts produced from the pkl do not reflect its actual input population.

**Problem 2 — `langid` secondary filter.** The pkl was built using automatic language identification (`langid.py`) as a secondary filter on top of `dc:language=ger`. `notes/corpus-analysis/lang-detection.md` §5 establishes that `dc:language` is the more reliable signal for GND linking: fasttext disagrees with `dc:language=ger` on 9.4% of titles, including German works with Latin/French titles and nearly all `gmh`/`nds` titles (0% and 10.9% fasttext match). Applying a secondary langid filter systematically removes the historically significant pre-modern subset most in need of GND linking.

### Decision

Replace the pkl with `data/out/s2/s2_meta_de_content.parquet` as the canonical source for all corpus analysis and NER pipeline work. This parquet is produced by `scripts/analysis/filter_de_content.py` from `data/out/s2/s2_meta.parquet` using:

1. ADR-01 BLANKET_EXCLUDE htype filter (8 types removed)
2. `dc:language ∈ {ger, gmh, nds, lat}` — no secondary langid filter

Tokenization is pre-computed by `scripts/analysis/tokenize_de_titles.py` (xlm-roberta-large, SentencePiece BPE) into `data/processed/de_titles_tokenized.parquet`.

### Latin inclusion

`lat` is included alongside the German-family codes. Rationale: pre-1800 German cultural heritage is heavily bilingual; GND has Latin Werk records; xlm-roberta handles Latin. See `notes/corpus-analysis/lang-detection.md` §5.5. Latin should be faceted separately in analysis outputs (5.4% of final corpus).

### Consequences

| | Old (pkl) | New (parquet) |
|--|--|--|
| N rows | 4,477,780 | 9,213,339 |
| Language filter | `dc:language=ger` AND `langid=ger` | `dc:language ∈ {ger, gmh, nds, lat}` |
| Tokenizer | spaCy (model unspecified) | xlm-roberta-large SentencePiece BPE |
| Median `all_tokens` | 8 | 15 |
| p25 / p75 | 4 / 14 | 8 / 27 |

**SR-10 threshold recalibration required.** The (≤4 / 5–14 / >14) short/medium/long thresholds from the pkl do not transfer to xlm-roberta token counts. New thresholds: ≤8 / 9–27 / >27 (v2 p25/p75). See `notes/ner/sr10_title-length-thresholds.md`.

**SR-08 gold set stratification.** If title length is used as a stratification variable, use v2 thresholds. Pre-1750 records show median 32–52 BPE tokens (vs. 12–15 in the old pkl); the relative era pattern is preserved.

**Old pkl artifacts preserved.** `notes/images/fig_token_distribution.png`, `fig_title_lengths.png`, `title-length-analysis.json`, and `token-distribution.json` reflect the pkl. The v2 equivalents (`*_v2.*`) reflect the parquet. Both are retained for comparison.

### Rejected alternatives

**Keep the pkl and update htype filter only.** Rejected: the `langid` secondary filter problem is independent and would require re-running the notebook, which is not reproducible from current sources. The parquet pipeline is fully scripted and reproducible.

**Use `langid` as a validation signal only.** Accepted as a partial measure: see `lang-detection.md` §5.3 — fasttext may be used post-hoc as a quality flag, never as a gate on what enters the pipeline.

### Related

- `notes/adr/htype-filtering-adr.md` — ADR-01 (htype filter)
- `notes/corpus-analysis/lang-detection.md` — fasttext vs. dc:language analysis
- `notes/corpus-analysis/filter-de-content.md` → `scripts/analysis/filter_de_content.py`
- `notes/corpus-analysis/de-titles-regeneration-plan.md` — regeneration workflow
- `notes/ner/sr10_de-titles-distribution.md` §7 — v2 distribution results

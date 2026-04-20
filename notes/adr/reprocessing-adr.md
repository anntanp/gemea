# GeMeA — Architecture Decision Record: Corpus Reprocessing from DDB Dump

**Format:** MADR (Markdown Architecture Decision Record)
**Subject:** Whether to patch `DF_DE_TITLES_20240125b.pkl` or rebuild from the raw DDB dump
**Status:** Accepted

---

## ADR-03 — Rebuild corpus pipeline from DDB dump; retire notebook-derived pkl

**Status:** Accepted
**Date:** 2026-04-14

### Context

The NER analysis pipeline (SR-10, SR-11) and the GND Werk linking input were both built against `data/DF_DE_TITLES_20240125b.pkl`, a pickle snapshot produced by `2024.01 MT-QA.ipynb`. Tracing the pkl's provenance (SR-10, `notes/ner/sr10_tracing-df-de-titles.md`) revealed three compounding problems:

**Problem 1 — Non-reproducibility.** The pkl was produced in an undated Jupyter notebook with an unspecified spaCy model version. No script reproduces it; the notebook is not committed to the repository. Patching it would require re-running the notebook in an environment that may not be recoverable.

**Problem 2 — Stale htype filter.** The pkl used `hierarchy_type = content` as a filter condition. This differs from ADR-01's BLANKET_EXCLUDE list in both directions: some types the pkl excluded are valid work-title candidates; some it included are structural labels. The pkl's population does not match the GND linking pipeline's actual input.

**Problem 3 — Langid secondary filter.** The pkl applied `langid=ger` as a secondary filter on top of `dc:language=ger`. Analysis in `notes/corpus-analysis/lang-detection.md` §5 shows:
- fasttext (langid proxy) disagrees with `dc:language=ger` on 9.4% of titles — 1.1M records
- `gmh` (Middle High German): 0% fasttext match → eliminated entirely by the filter
- `nds` (Low German): 10.9% fasttext match → 89% eliminated
- German works with Latin/French titles → systematically misdetected and excluded

These exclusions are not annotation errors; they are linguistically correct `dc:language` assignments. The langid filter introduces systematic bias against the historically significant pre-modern subset.

**Problem 4 — Missing Latin.** Pre-1800 German scholarly, theological, and legal publishing was heavily bilingual. GND has Latin Werk records. Restricting to `dc:language=ger` omits ~494K Latin-language objects in Sector 2 that belong in the German cultural heritage linking pool.

### Decision

Retire the pkl. Build the corpus pipeline from scratch using the DDB Sector 2 SQLite dump as the authoritative source, applying fully scripted, reproducible filters.

**New pipeline** (see `notes/project/reprocessing-workflow.md`):

```
data/sqlite/s2.sqlite
    │  export_ddb.py
    ▼
data/out/s2/s2_meta.parquet            18,570,245 rows
    │  filter_de_content.py
    │  Step 1: ADR-01 htype filter     −5,112,120 (27.5%)
    │  Step 2: dc:language ∈ {ger,gmh,nds,lat}  −4,244,786 (31.5% of remaining)
    ▼
data/out/s2/s2_meta_de_content.parquet  9,213,339 rows
    │  tokenize_de_titles.py
    │  xlm-roberta-large SentencePiece BPE
    ▼
data/processed/de_titles_tokenized.parquet
```

### Consequences

**Corpus size doubles.** 4,477,780 → 9,213,339 rows. The increase reflects: (a) broader htype retention under ADR-01, (b) removal of the langid secondary filter, (c) addition of Latin (493,712 records).

**Tokenizer changes.** spaCy → xlm-roberta-large BPE. BPE produces more pieces per word (median `all_tokens` 8 → 15); the era-stratified length pattern is preserved but absolute values are not comparable. Downstream thresholds (short ≤4 / medium 5–14 / long >14) must be recalibrated to v2 percentiles (p25=8, p75=27).

**SR-01 ISBD ratings not yet migrated.** `data/processed/sr01_isbd_field_ratings.csv` was computed against the pkl. It must be re-run against `s2_meta_de_content.parquet` before `build_silver_spans.py` can proceed. This is the next pending step in Phase 0a.

**Old artifacts preserved.** SR-10/SR-11 outputs from the pkl are retained as `notes/images/fig_*.png` and `notes/images/*.json`. New outputs carry a `_v2` suffix. Both sets coexist for comparison.

**Reproducibility restored.** Every step in the new pipeline is a standalone Python script with a standard header (purpose, usage, inputs, outputs, dependencies, assumptions). The pipeline can be re-run end-to-end from `data/sqlite/s2.sqlite`.

### Rejected alternatives

**Patch the pkl in-place.** Requires re-running the source notebook. The notebook environment (spaCy model version, Python version, input data state) is not recoverable. Patching individual columns (htype mask, lang mask) would produce a hybrid artifact with inconsistent provenance — harder to reason about than a clean rebuild.

**Keep the pkl for SR-01/silver pipeline; only rebuild for SR-10/SR-11.** The silver pipeline (`rate_isbd_fields.py`, `build_silver_spans.py`) produces outputs that feed the gold set and NER model. Maintaining two parallel corpus definitions (pkl for silver, parquet for GND linking) would guarantee that model training data does not match the production input — a fundamental train/serve mismatch. Rejected.

**Apply `langid` as a post-hoc quality flag only.** Accepted as a partial measure and documented in `lang-detection.md` §5.3: fasttext at high confidence on long titles is a useful annotation-error flag. It is not used as a gate on pipeline input.

### Related ADRs

- **ADR-01** (`notes/adr/htype-filtering-adr.md`) — BLANKET_EXCLUDE htype filter
- **ADR-02** (`notes/adr/corpus-source-adr.md`) — pkl → parquet migration, language filter rationale, Latin inclusion

# Plan: Retire pkl-era outputs, promote parquet-era files, run SR-11

## Context

The pkl → parquet migration (ADR-02/03) is now complete. `de_titles_tokenized.parquet` (9.21M rows) has been regenerated with the correct `dc:type`/`edm:hasType` genre values (Leichenpredigt, Einblattdruck, Monografie). The following parquet-era outputs exist under `_v2` suffixed names and need to become canonical:

- `sr01_isbd_field_ratings_v2.csv` — 9.2M rows ✅
- `sr08_corpus_cell_sizes_v2.csv` ✅
- `sr11_dctype_by_era_v2.csv` ✅
- SR-10 v2 PNG/JSON/JSX in `notes/images/`

Goal: archive pkl-era files, rename `_v2` → canonical, fix sr11 bug, run sr11.

---

## Step A — Archive pkl-era files to `data/before-parquet/`

Move pkl-derived outputs only. Preserve relative paths under `data/before-parquet/`. Do NOT move annotation gold data or corpus-agnostic SR-03–06/09 outputs.

**Files to move:**

| Source | Destination |
|--------|-------------|
| `data/processed/ner/sr01_isbd_field_ratings.csv` | `data/before-parquet/processed/ner/sr01_isbd_field_ratings.csv` |
| `data/processed/ner/sr08_corpus_cell_sizes.csv` | `data/before-parquet/processed/ner/sr08_corpus_cell_sizes.csv` |
| `data/processed/ner/sr08_agent_coverage_by_era.csv` | `data/before-parquet/processed/ner/sr08_agent_coverage_by_era.csv` |
| `data/processed/ner/sr10_era_length_summary.csv` | `data/before-parquet/processed/ner/sr10_era_length_summary.csv` |
| `data/processed/ner/sr11_dctype_by_era.csv` | `data/before-parquet/processed/ner/sr11_dctype_by_era.csv` |
| `data/processed/ner/sr11_dctype_filtered.csv` | `data/before-parquet/processed/ner/sr11_dctype_filtered.csv` |
| `data/processed/sr11_dctype_filtered.csv` | `data/before-parquet/processed/sr11_dctype_filtered.csv` |
| `data/annotation/sr11_prompt_validation_manual.jsonl` | `data/before-parquet/annotation/sr11_prompt_validation_manual.jsonl` |
| `data/annotation/sr11_prompt_validation_manual_v2.jsonl` | `data/before-parquet/annotation/sr11_prompt_validation_manual_v2.jsonl` |

Note on the two jsonl files:
- `..._manual.jsonl` — original pkl-based run
- `..._manual_v2.jsonl` — generated from bad parquet (dc_type=TEXT/IMAGE), 5 records only; also archived

**notes/images/ — pkl-era files with v2 counterparts (move to `data/before-parquet/images/`):**

| Source | Destination |
|--------|-------------|
| `notes/images/fig_dctype_by_era.png` | `data/before-parquet/images/fig_dctype_by_era.png` |
| `notes/images/fig_title_lengths.png` | `data/before-parquet/images/fig_title_lengths.png` |
| `notes/images/fig_title_lengths.jsx` | `data/before-parquet/images/fig_title_lengths.jsx` |
| `notes/images/fig_title_lengths.html` | `data/before-parquet/images/fig_title_lengths.html` |
| `notes/images/fig_token_distribution.png` | `data/before-parquet/images/fig_token_distribution.png` |
| `notes/images/title-length-analysis.json` | `data/before-parquet/images/title-length-analysis.json` |

Note: `fig_title_lengths_v2_bw.html` has no old counterpart — keep in notes/images/ and rename to `fig_title_lengths_bw.html`. HTML theme variants (`_leather`, `_lighter`, `_retro`, `_vscode_dark`) have no v2 counterparts; leave in place.

`token-distribution_v2.json` has no old counterpart (old token stats were not saved as JSON) — rename in place.

**Files NOT to move (keep in place):**
- `data/annotation/sr08_gold_sample.csv` — used as exclusion list in sr11, still valid
- `data/annotation/sr08-doccano-import.jsonl`, `sr08_gold_prefilled.*`, `sr08_manual_queue.csv`, `export_245867_pretty.json`, `doccano/` — annotation data
- `data/processed/ner/sr03_*`, `sr04_*`, `sr05_*`, `sr06_*` — corpus-agnostic conclusions
- `data/processed/ner/sr08_ci_sample_size.csv`, `sr08_gold_composition_audit.csv`, `sr08_gold_dctype_breakdown.csv` — gold-set stats
- `data/processed/ner/sr09_*` — NuNER results, decision final
- `data/processed/ner/lang_*.csv` — language detection stats
- `data/processed/corpus/` — corpus analysis files
- `data/processed/filter_de_content_summary.csv` — pipeline audit

---

## Step B — Rename `_v2` files to canonical names

| `_v2` source | Canonical destination | Notes |
|---|---|---|
| `data/processed/sr11_dctype_by_era_v2.csv` | `data/processed/ner/sr11_dctype_by_era.csv` | Also moves from processed/ root to ner/ |
| `data/processed/ner/sr08_corpus_cell_sizes_v2.csv` | `data/processed/ner/sr08_corpus_cell_sizes.csv` | — |
| `data/processed/ner/sr01_isbd_field_ratings_v2.csv` | `data/processed/ner/sr01_isbd_field_ratings.csv` | — |
| `notes/images/fig_dctype_by_era_v2.png` | `notes/images/fig_dctype_by_era.png` | — |
| `notes/images/fig_title_lengths_v2.png` | `notes/images/fig_title_lengths.png` | — |
| `notes/images/fig_title_lengths_v2.jsx` | `notes/images/fig_title_lengths.jsx` | — |
| `notes/images/fig_title_lengths_v2_bw.html` | `notes/images/fig_title_lengths_bw.html` | New name (no old equivalent) |
| `notes/images/fig_token_distribution_v2.png` | `notes/images/fig_token_distribution.png` | — |
| `notes/images/title-length-analysis_v2.json` | `notes/images/title-length-analysis.json` | — |
| `notes/images/token-distribution_v2.json` | `notes/images/token-distribution.json` | New name (no old equivalent) |

---

## Step C — Fix `sr11_sample_validation.py` bug

**File:** `scripts/ner/sr11_sample_validation.py`

**Bug (line 171):** `load_pool()` accepts 3 args but the call passes 4. `args.source` was removed during the revert but the call was not updated.

```python
# current (broken)
pool = load_pool(args.data, args.ratings, args.gold, args.source)

# fix
pool = load_pool(args.data, args.ratings, args.gold)
```

No other changes. `load_corpus()` parquet support and ROOT fix are already in place. After Step B, the `RATINGS` default (`sr01_isbd_field_ratings.csv`) resolves correctly.

---

## Step D — Run `sr11_sample_validation.py`

```bash
python scripts/ner/sr11_sample_validation.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output data/annotation/sr11_prompt_validation_manual.jsonl
```

(Default `--ratings` resolves to `data/processed/ner/sr01_isbd_field_ratings.csv` after Step B.)

**Expected:** 50 pre-1750 tier-0 records; dc_type distribution shows Leichenpredigt / Einblattdruck / Monografie (not TEXT/IMAGE or htype codes); era ∈ {pre-1700, 1700–1800}.

**Update `reprocess-before-after.md`:** add SR-11 section with dc_type and era distribution table.

---

## Step E — Update notes

After Steps B–D:

| File | What to update |
|------|----------------|
| `notes/project/reprocessing-workflow.md` | Remove `_v2` from all output filenames in pipeline diagram |
| `notes/project/reprocess-before-after.md` | §7 file references → canonical names; add SR-11 output stats |
| `notes/ner/reprocess-plan-ner.md` | Mark Steps A–D done; update file name references |
| `notes/ner/ner-bibliographic.md` | SR-11 section: add run status + dc_type distribution |
| `notes/ner/sr10_de-titles-distribution.md` | Update file references after SR-10 rename |
| `notes/images/README.md` | Update filenames to canonical (remove `_v2` from entries) |

---

## Verification

1. `data/annotation/sr11_prompt_validation_manual.jsonl` — ~50 records, dc_type = genre values
2. `data/before-parquet/` — all pkl-era outputs present, structure mirrors `data/`
3. No `_v2` files remain in `data/processed/` or `data/annotation/`
4. `scripts/ner/sr11_sample_validation.py` runs without error from project root

---

## Critical files

| File | Action |
|------|--------|
| `scripts/ner/sr11_sample_validation.py` | Fix line 171: remove `args.source` from `load_pool()` |
| `data/before-parquet/` | Create; move pkl-era outputs |
| `data/processed/ner/sr01_isbd_field_ratings.csv` | Renamed from `_v2` (Step B) |
| `data/processed/ner/sr08_corpus_cell_sizes.csv` | Renamed from `_v2` (Step B) |
| `data/processed/ner/sr11_dctype_by_era.csv` | Renamed from `_v2` + moved from processed/ root (Step B) |
| `data/annotation/sr11_prompt_validation_manual.jsonl` | Fresh output from Step D (50 records, correct dc_type) |
| `notes/project/reprocessing-workflow.md` | Remove `_v2` from all output filenames |
| `notes/ner/ner-bibliographic.md` | Add SR-11 run status |

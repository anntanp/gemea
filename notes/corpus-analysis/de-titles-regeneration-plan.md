# Regenerate SR-10/SR-11 analysis artifacts from s2_meta_de_content.parquet

## 1. Context

The SR-10 / SR-11 analysis scripts all read from `data/DF_DE_TITLES_20240125b.pkl`, a stale pickle built from an old dataset with different htype filtering and langid-based language selection. The new canonical source is `data/out/s2/s2_meta_de_content.parquet` (ADR-01 htypes + `dc:language ∈ {ger, gmh, nds, lat}`).

**Latin inclusion:** `lat` is added alongside the German-family codes. Pre-1800 German cultural heritage is heavily bilingual (scholarly, theological, and legal works in Latin); GND has Latin Werk records; xlm-roberta handles Latin via its multilingual pretraining. Analysis scripts should facet `lang` separately so German-family and Latin distributions can be read independently.

The pkl has pre-computed columns the scripts depend on — `all_tokens`, `content_tokens`, `dates` — that the parquet does not. A new tokenization step must produce these before the downstream scripts can run.

---

## 2. Dependency chain

```
s2_meta_de_content.parquet
        │
        ▼
[1] tokenize_de_titles.py          → data/processed/de_titles_tokenized.parquet
        │                               (obj_id, title, lang, all_tokens, content_tokens, dates, dc_type)
        ├──────────────────────────────────────────────────────────────────┐
        ▼                                                                  ▼
[2] sr10_explore_token_distribution.py                    [5] sr11_dctype_by_era.py
    → notes/images/fig_token_distribution.png                 → notes/images/fig_dctype_by_era.png
    → notes/images/token-distribution.json                    → data/processed/sr11_dctype_by_era.csv
        │
        ▼
[3] sr10_analyse_title_lengths.py
    → notes/images/fig_title_lengths.png
    → notes/images/title-length-analysis.json
        │
        ▼
[4] sr10_render_title_viz.py  (reads JSON only — no changes needed)
    → notes/images/fig_title_lengths.jsx
    → notes/images/fig_title_lengths_bw.html  (and other themes)
```

---

## 3. Output file naming

Do **not** overwrite the existing SR-10/SR-11 artifacts produced from the stale pkl. Instead, write new files with a `_v2` suffix so old and new outputs coexist for comparison:

| Old file | New file |
|----------|----------|
| `notes/images/fig_token_distribution.png` | `notes/images/fig_token_distribution_v2.png` |
| `notes/images/token-distribution.json` | `notes/images/token-distribution_v2.json` |
| `notes/images/fig_title_lengths.png` | `notes/images/fig_title_lengths_v2.png` |
| `notes/images/title-length-analysis.json` | `notes/images/title-length-analysis_v2.json` |
| `notes/images/fig_title_lengths.jsx` | `notes/images/fig_title_lengths_v2.jsx` |
| `notes/images/fig_title_lengths_bw.html` (and other themes) | `notes/images/fig_title_lengths_v2_bw.html` etc. |
| `notes/images/fig_dctype_by_era.png` | `notes/images/fig_dctype_by_era_v2.png` |
| `data/processed/sr11_dctype_by_era.csv` | `data/processed/sr11_dctype_by_era_v2.csv` |

Pass the new paths via `--output-dir` / `--output` / `--fig` CLI arguments; no hardcoded path changes needed in the scripts.

---

## 4. Step 1 — `scripts/analysis/tokenize_de_titles.py` ✓ done

**Input:** `data/out/s2/s2_meta_de_content.parquet`
**Output:** `data/processed/de_titles_tokenized.parquet`

Columns in output:

| Column | Source | Notes |
|--------|--------|-------|
| `obj_id` | parquet passthrough | |
| `title` | parquet passthrough | raw, before normalization |
| `lang` | parquet passthrough | ISO 639-2/B code |
| `dc_type` | parquet passthrough | DDB genre/type field |
| `dates` | `dc_issued[0][:4]` | first 4 chars of first issued value; NaN if absent |
| `all_tokens` | xlm-roberta tokenizer | subword count, excl. `<s>` and `</s>` special tokens |
| `content_tokens` | xlm-roberta tokenizer | subword count after removing pieces that belong to stopword words |

**Tokenization:**
1. Apply `normalize_historical(text)` (long-s, ligatures, NFC) — from `notes/corpus-analysis/tokenization.md`
2. `tokenizer(text, return_offsets_mapping=True)` with `AutoTokenizer.from_pretrained("FacebookAI/xlm-roberta-large")`
3. `all_tokens = len(input_ids) - 2`
4. For `content_tokens`: identify which token positions correspond to stopword words using offset mapping → subtract their count

**Stopword list** (German only; Latin titles are not filtered):
```python
STOPWORDS = {"der","die","das","ein","eine","von","und","zu","im","in",
             "an","auf","für","mit","bei","dem","den","des","einer","eines"}
```

**Processing:** batch size 512, tokenizer only (no forward pass needed). ~15–20 min for 9.2M rows on CPU.

---

## 5. Steps 2–5 — Adapt existing scripts to accept parquet

Each of the three scripts (`sr10_explore_token_distribution.py`, `sr10_analyse_title_lengths.py`, `sr11_dctype_by_era.py`) currently loads data with:
```python
with open(data_path, "rb") as f:
    df = pickle.load(f)
```

**Change:** Replace loading block with a helper that detects file extension:
```python
def load_data(path: Path) -> pd.DataFrame:
    if path.suffix == ".parquet":
        return pd.read_parquet(path)
    with open(path, "rb") as f:
        return pickle.load(f)
```

**JSON output paths:** Scripts currently write JSON to `output/`. Change default output dir to `notes/images/` to match the expected file locations (`title-length-analysis.json`, `token-distribution.json`).

**`sr11_dctype_by_era.py` note:** Verify that `dc_type` in the parquet uses the same pipe-separated genre format (e.g. `"Leichenpredigt|Monografie"`) as the pkl. If the parquet stores a single value, the `normalize_dctype()` split-on-`|` logic still works (single value = no split).

---

## 6. Invocation order

```bash
# Step 1 — tokenize ✓ done → data/processed/de_titles_tokenized.parquet

# Step 2 — token distribution
python scripts/ner/sr10_explore_token_distribution.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output-dir notes/images \
    --suffix _v2

# Step 3 — title length analysis
python scripts/ner/sr10_analyse_title_lengths.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output-dir notes/images \
    --suffix _v2

# Step 4 — render JSX + HTML (reads JSON; no changes needed except JSON path)
python scripts/ner/sr10_render_title_viz.py \
    --json notes/images/title-length-analysis_v2.json \
    --output-dir notes/images \
    --suffix _v2

# Step 5 — dc_type by era
python scripts/ner/sr11_dctype_by_era.py \
    --data data/processed/de_titles_tokenized.parquet \
    --output data/processed/sr11_dctype_by_era_v2.csv \
    --fig notes/images/fig_dctype_by_era_v2.png
```

---

## 7. Critical files

| File | Action |
|------|--------|
| `data/out/s2/s2_meta_de_content.parquet` | Input — ✓ regenerated (9.2M rows, ger+gmh+nds+lat) |
| `scripts/analysis/tokenize_de_titles.py` | ✓ done |
| `scripts/ner/sr10_explore_token_distribution.py` | Add parquet loader + `--suffix` arg |
| `scripts/ner/sr10_analyse_title_lengths.py` | Add parquet loader + `--suffix` arg |
| `scripts/ner/sr10_render_title_viz.py` | Add `--suffix` arg (JSON path + output filenames) |
| `scripts/ner/sr11_dctype_by_era.py` | Add parquet loader |
| `data/processed/de_titles_tokenized.parquet` | ✓ done (9.2M rows, 779.3 MB) |
| `scripts/README.md` | ✓ updated |

---

## 8. Prerequisites — all done

1. **`scripts/analysis/filter_de_content.py`**: ✓ `DE_LANGS = {"ger", "gmh", "nds", "lat"}` — done.
2. **`notes/corpus-analysis/lang-detection.md`**: ✓ §5.5 added — done.
3. **Parquet regenerated**: 9,213,339 rows (49.6% of corpus, 1,239.6 MB). Breakdown: ger 8,716,820 (94.6%), lat 493,712 (5.4%), nds 1,523, gmh 1,284.

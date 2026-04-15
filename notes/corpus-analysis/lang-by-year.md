# Language × Year Analysis — Plan and Findings

## 1. Goal

Visualise how the language distribution of DDB Sector 2 objects changes over time, to understand the temporal scope of each language in the corpus.

---

## 2. Data

- **Source:** `data/out/s2/s2_meta.parquet` (18,570,245 objects)
- **Language column:** `lang` — scalar ISO 639-2 code; 94.7% non-null, 0% multi-value
- **Year columns:** `dc_created` (list[str]), `dc_issued` (list[str])

### 2.1 Year extraction strategy

1. Take the first non-empty element of `dc_created`
2. If empty/null, fall back to the first non-empty element of `dc_issued`
3. Parse the first 4 characters as an integer; accept range 1400–2025
4. Objects with no valid year are excluded from the chart; their count is printed at runtime

> **Note:** exploration notes suggested event chains may be sparsely populated. Actual coverage is printed at runtime (see §3).

---

## 3. Coverage (to be filled after first run)

| Metric | Count | % |
|--------|-------|---|
| dc_created non-empty | 0 | 0.0% — column entirely empty |
| dc_issued non-empty | 15,867,918 | 85.4% — sole year source in practice |
| Valid year extracted | 15,335,152 | 82.6% |
| No valid year | 3,235,093 | 17.4% — excluded from chart |

---

## 4. Script

**`scripts/analysis/lang_by_year.py`**

| Flag | Default | Description |
|------|---------|-------------|
| `--bucket` | `decade` | Time resolution: `decade` or `year` |
| `--top` | `10` | Number of distinct language series in chart |
| `--min-year` | `1400` | Earliest year to include |
| `--max-year` | `2025` | Latest year to include |
| `--normalize` | off | Plot % share per bucket instead of raw counts |

```bash
# default: decade buckets, top-10 languages, raw counts
python scripts/analysis/lang_by_year.py

# normalised (% share)
python scripts/analysis/lang_by_year.py --normalize

# yearly resolution, top-5, post-1800 only
python scripts/analysis/lang_by_year.py --bucket year --top 5 --min-year 1800
```

---

## 5. Outputs

| File | Description |
|------|-------------|
| `data/processed/lang_by_year.csv` | Long-form: `bucket`, `lang`, `count` |
| `notes/images/lang_by_year.png` | Stacked area chart (raw counts) |

---

## 6. Chart design

- **Type:** stacked area (raw) or 100% stacked area (`--normalize`)
- **X-axis:** decade (or year) bucket
- **Y-axis:** object count or % share
- **Series:** top-N languages in distinct colors + `other` in grey; `(none)` in light red

# Language × Year Analysis — All Sectors

> Supersedes the s2-only analysis in [lang-by-year-s2.md](lang-by-year-s2.md).

## 1. Goal

Visualise how the language distribution of DDB objects changes over time across all seven sectors (s1–s7), and characterise the date-type coverage of the new parquet schema.

---

## 2. Data

- **Source:** `output/parquet/s<n>_meta.parquet` for n ∈ {1, …, 7}
- **Schema:** new prescan schema — see [parquet-source.md](write-ups/parquet-source.md)
- **Language column:** `lang_obj` (object-level ISO 639-2 from `ProvidedCHO.language` / `dcTermsLanguage`), falling back to `lang_title` (title's language tag)
- **Year column:** `dates` — list of `DATE_STRUCT` (`value`, `begin`, `end`, `type`)

### 2.1 Year extraction strategy

1. Prefer structs with `type = "creation"`, then `"publication"`, then others
2. Within a chosen struct, try `begin` first (normalised range start), then `value`
3. Parse the first 4 characters as an integer; accept range 1400–2026
4. Objects with no valid year are excluded from the language chart

### 2.2 Language resolution

- Use `lang_obj` if non-null and non-empty
- Fall back to `lang_title`
- Mark as `(none)` if both absent; always excluded from charts together with `und` and `zxx`

---

## 3. Coverage (fill after first run)

### 3.1 Language

| Metric | Count | % |
|--------|-------|---|
| Total rows (all sectors) | 27,526,560 | 100.0% |
| `lang_obj` non-null | 27,526,560 | 100.0% |
| `lang_title` non-null | 27,526,560 | 100.0% |
| Resolved `(none)` | 2,254,502 | 8.2% |
| Distinct language codes (excl. none/und/zxx) | 251 | — |

> Both `lang_obj` and `lang_title` are 100% non-null because `prescan.py` writes an empty string rather than NULL when no language is found; `(none)` reflects objects where both fields are empty strings.

### 3.2 Year

| Metric | Count | % |
|--------|-------|---|
| Valid year extracted | 19,669,829 | 71.5% |
| No valid year (excluded) | 7,856,731 | 28.5% |

### 3.3 Date types

Raw counts in `data/processed/date_types_all.csv` (columns: `sector`, `date_type`, `struct_count`).

**Struct counts per sector** (number of `DATE_STRUCT` entries, not objects):

| date_type | s1 Archive | s2 Library | s3 Monument | s4 Research | s5 Media | s6 Museum | s7 Other |
|-----------|----------:|----------:|------------:|------------:|---------:|----------:|---------:|
| `creation` | 31,854 | 0 | 24,444 | 437,904 | 141,475 | 0 | 63,170 |
| `publication` | 213,132 | 16,014,337 | 0 | 521,720 | 192 | 6,256 | 14,414 |
| `unknown_event` | 2,213,722 | 37,948 | 22,068 | 189,515 | 1,109,988 | 43,257 | 6,325 |
| **Objects with any date** | 2,458,048 | 15,905,240 | 43,887 | 1,103,979 | 1,198,257 | 45,871 | 67,769 |
| **Total objects** | 3,638,021 | 18,570,245 | 83,572 | 1,227,252 | 1,799,838 | 2,117,728 | 89,904 |
| **% with date** | 67.6% | 85.6% | 52.5% | 89.9% | 66.6% | 2.2% | 75.4% |

**Notable patterns:**
- s2 (Library): `publication` dominates — matches the `dc_issued` reliance in the old s2-only analysis
- s1 (Archive): `unknown_event` dominates — LIDO event chains with unrecognised type
- s6 (Museum): only 2.2% have any date — very sparse; contributes little to the year analysis
- s3 (Monument): no `publication` dates; mix of `creation` and `unknown_event`

---

## 4. Script

**[`scripts/analysis/lang_by_year_all.py`](https://github.com/anntanp/gemea/blob/main/scripts/analysis/lang_by_year_all.py)**

| Flag | Default | Description |
|------|---------|-------------|
| `--sectors N [N ...]` | `1 2 3 4 5 6 7` | Sectors to include |
| `--bucket` | `decade` | Time resolution: `decade` or `year` |
| `--top` | `10` | Number of distinct language series in chart |
| `--min-year` | `1400` | Earliest year to include |
| `--max-year` | `2026` | Latest year to include |

```bash
# default: all sectors, decade buckets, top-10 languages
python scripts/analysis/lang_by_year_all.py

# library sector only
python scripts/analysis/lang_by_year_all.py --sectors 2

# yearly resolution, top-5, post-1800 only
python scripts/analysis/lang_by_year_all.py --bucket year --top 5 --min-year 1800

# archive + museum only
python scripts/analysis/lang_by_year_all.py --sectors 1 6
```

---

## 5. Outputs

| File | Description |
|------|-------------|
| `data/processed/lang_by_year_all.csv` | Long-form: `bucket`, `lang`, `count` |
| `data/processed/date_types_all.csv` | Date-type struct counts per sector |
| `notes/images/lang_by_year_all.png` | Marimekko stacked-area chart, top-N languages |
| `notes/images/lang_by_year_all_no_top1.png` | Same chart with dominant language excluded |

---

## 6. Chart design

- **Type:** Marimekko 100% stacked area — x-axis width proportional to object count per bucket
- **X-axis:** decade (or year) bucket; ticks at century years
- **Y-axis:** share (%) with Gaussian smoothing for visual clarity
- **Series:** top-N languages in distinct colors; `und`, `zxx`, `(none)` always excluded

---

## 7. Findings

- **Top 10 languages (by object count):** `ger`, `lat`, `eng`, `spa`, `fre`, `ita`, `dut`, `grc`, `chi`, `mul`
- German (`ger`) dominates strongly; the `_no_top1` chart shows the distribution without it
- 251 distinct language codes in the corpus after excluding `und`, `zxx`, `(none)`

**Language distribution — all sectors (top 10 languages)**

![Language distribution by decade, all sectors](https://raw.githubusercontent.com/anntanp/gemea/develop/notes/images/lang_by_year_all.png)

**Language distribution — German excluded**

![Language distribution by decade, German excluded](https://raw.githubusercontent.com/anntanp/gemea/develop/notes/images/lang_by_year_all_no_top1.png)

**Language diversity by decade**

![Distinct language codes per decade vs object count](https://raw.githubusercontent.com/anntanp/gemea/develop/notes/images/fig_lang_diversity_decade.png)

**Date coverage by sector**

![Date coverage per sector](https://raw.githubusercontent.com/anntanp/gemea/develop/notes/images/fig_date_coverage_sector.png)

**Date-type composition by sector**

![Date-type composition per sector](https://raw.githubusercontent.com/anntanp/gemea/develop/notes/images/fig_date_types_sector.png)

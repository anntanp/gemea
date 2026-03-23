# ISBD Punctuation Analysis — DF_DE_TITLES

**Dataset:** `data/DF_DE_TITLES_20240125b.pkl` — 4,477,780 rows × 27 columns
- Source: German titles from "content" objects.

**Script:** `scripts/check_isbd_titles.py`
**Date:** 2026-03-17

## DataFrame Schema

| Column | Description |
|---|---|
| `obj_id` | DDB object identifier (use: `https://ddb.de/item/<obj_id>`) |
| `lang` | Language code (e.g. `de`) |
| `title` | Title string — primary field for ISBD analysis |
| `title_en` | English title (if available) |
| `valid_htype` | Boolean — record has a valid hierarchical type |
| `agent_uris` | Boolean — at least one agent URI present |
| `agent_literals` | Boolean — at least one agent literal present |
| `agent_both` | Boolean — both URI and literal agent present |
| `date` | Boolean — date field present |
| `both` | Boolean — both agent and date present |
| `blank` | Boolean — blank record |
| `all_tokens` | Token count (all) |
| `content_tokens` | Token count (content tokens only) |
| `dc_type` | DC type string(s), pipe-separated (e.g. `Leichenpredigt\|Monografie`) |
| `agents` | Agent string(s), pipe-separated (names + publisher block) |
| `ner_person` | NER-extracted person name |
| `agent_match` | Agent match score |
| `dates` | Extracted date string(s) |
| `ner_date` | NER-extracted date |
| `agent_approx_match` | Approximate agent match score |
| `date_match` | Date match score |
| `dc_subject` | DC subject field |
| `dc_creator` | DC creator field |
| `dc_contributor` | DC contributor field(s), pipe-separated |
| `dc_publisher` | DC publisher field |
| `model2_q1_answer` | Model 2 Q1 answer |
| `model2_q1_match` | Model 2 Q1 match flag |

## Summary

| Metric | Count | % |
|---|---|---|
| Rows total | 4,477,780 | — |
| Empty / null titles | 0 | 0% |
| Titles with ≥1 ISBD pattern (incl. trailing `.`) | 1,993,553 | **44.5%** |
| Titles with ≥1 ISBD pattern (excl. trailing `.`) | 1,272,718 | **28.4%** |

## Pattern Breakdown

| Pattern | Signal | Count | % |
|---|---|---|---|
| ` :` | Other title information | 909,869 | 20.3% |
| trailing `.` | Area-end period | 783,752 | 17.5% |
| `[ ]` | Supplied / inferred data | 315,263 | 7.0% |
| `…` / `...` | Ellipsis / truncation | 246,370 | 5.5% |
| ` ;` | Subsequent SoR / series | 174,813 | 3.9% |
| ` /` | Statement of responsibility | 33,907 | 0.8% |
| ` =` | Parallel title | 26,264 | 0.6% |

## Notes on the Trailing Period

The trailing period (`.` at end of string) is an **ISBD area-closing mark** — it closes the title area when the field doesn't already end with `?`, `!`, or `)`. Examples:

- `Harzreise im Winter.` — closes title area
- `Goethes Briefe, Bd. 2.` — closes title + numbering
- `Der neue Amadis.` — simple title close

**Why it's noisy.** The regex `[^.]\.$` (last char is `.`, preceded by a non-dot) also fires on:

- **Abbreviations as last token**: `Hrsg.`, `Bd.`, `Nr.`, `u.a.` — very common in German bibliographic data
- **Ordinals**: `4.`, `Bd. 3.`
- **Incomplete titles ending in an abbreviation**: `... et al.`

The 17.5% / 783k figure is therefore an **upper bound**. True ISBD area-closing periods are a subset. To get a cleaner signal, one would need to either:
1. Strip known German abbreviations before applying the pattern, or
2. Use a more conservative heuristic (e.g., require the title to also contain another ISBD marker, suggesting it was catalogued with full ISBD punctuation).

For the purposes of GeMeA title extraction, ` :` (20.3%) is the most reliable single ISBD indicator — it almost always signals an `other title information` segment that should be split off from the main title.

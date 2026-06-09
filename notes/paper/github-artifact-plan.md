# GitHub Artifact Plan — ISWC 2026 Supplemental Package

Repo: `ISE-FIZKarlsruhe/gemea` (at `~/Documents/claude/ise/gemea`)

---

## 1. Repository structure

```
ise/gemea/
├── README.md                        create
├── LICENSE                          exists
├── CITATION.cff                     create
├── docs/
│   └── adr/
│       ├── transform-adr.md                from goethe-faust/notes/
│       ├── transform-props-mapping-adr.md  from goethe-faust/notes/
│       └── transform-script-adr.md         from goethe-faust/notes/
├── paper/
│   └── iswc-2026.pdf                manual (add after submission)
├── scripts/
│   ├── README.md                    create (transform → NQ → QLever workflow)
│   ├── transform/                   from goethe-faust/scripts/transform/
│   │   ├── __init__.py, __main__.py
│   │   ├── transform.py, loaders.py, emitters.py
│   │   ├── constants.py, merge.py, sqlite_export.py, utils.py
│   │   └── tests/
│   └── config/                      from goethe-faust/output/config/
│       ├── lookup_dctype_to_class.csv
│       ├── lookup_htype_doco_rico.csv/json
│       ├── lookup_class_prop_alignment.csv
│       ├── image_type2class.json
│       ├── video_type2class.json
│       ├── audio_type2class.json
│       ├── lido_event_types.csv
│       └── loc-iso-639-2-utf-8.txt
├── goethe-faust/
│   ├── README.md                    adapted from ddbkg/goethe-faust (update citation)
│   ├── LICENSE                      create (MIT)
│   ├── requirements.txt             from ddbkg/goethe-faust/
│   ├── config.env.example           from ddbkg/goethe-faust/
│   ├── docker-compose.qlever.yml    from ddbkg/goethe-faust/
│   ├── docker-compose.shmarql.yml   from ddbkg/goethe-faust/
│   ├── scripts/                     see §3
│   ├── output/                      see §4
│   └── data/
│       ├── ids-all-goethe-faust.txt      from goethe-faust/data/  (3.6 MB, in git)
│       └── items-excerpt-1000.json       from goethe-faust/data/  (39 MB, in git)
│       # items-all-goethe-faust.json hosted on download page (2.4 GB, gitignored)
```

---

## 2. Deferred (post-acceptance)

- `resource/void.ttl` — VoID descriptor (FAIR requirement for camera-ready)
- `resource/dcat.ttl` — DCAT record
- `resource/queries/` — example SPARQL queries
- Persistent URI (w3id or Zenodo DOI)

---

## 3. goethe-faust/scripts/ — corpus analysis only

Sources: `ddbkg/goethe-faust/scripts/` for fetch/build/analyse;
`goethe-faust/scripts/` for dc:type, dispatch, and config-generation scripts.

A new `goethe-faust/scripts/README.md` replaces the existing one (which is babel-ddb focused).

### Phase 1 — Data acquisition

| Script | Source | Output |
|---|---|---|
| `fetch-search-all.py` | ddbkg/goethe-faust/scripts/ | `data/ddb-search-goethe-all.json` |
| `fetch-items.sh` | ddbkg/goethe-faust/scripts/ | `data/items-all-goethe-faust.json` |
| `fetch-progress.sh` | ddbkg/goethe-faust/scripts/ | stdout only |
| `find_missing_items.py` | ddbkg/goethe-faust/scripts/ | `data/ids-missing.txt` |

### Phase 2 — DataFrame build

| Script | Source | Output |
|---|---|---|
| `build_dataframe.py` | ddbkg/goethe-faust/scripts/ | `output/items-dataframe.parquet`, `output/items-dataframe-sample.csv` |

### Phase 3 — Core corpus analysis

| Script | Source | Output |
|---|---|---|
| `analyse_items.py` | ddbkg/goethe-faust/scripts/ | `output/items-analysis.json` |
| `analyse_years.py` | ddbkg/goethe-faust/scripts/ | `output/fig_years.png`, `output/years-analysis.json` |
| `analyse_bucket.py` | ddbkg/goethe-faust/scripts/ | stdout only |
| `audit_timespan_coverage.py` | ddbkg/goethe-faust/scripts/ | stdout only |
| `extract_view_fields.py` | ddbkg/goethe-faust/scripts/ | `output/view-<item-id>.json` |
| `extract_view_id_name.py` | ddbkg/goethe-faust/scripts/ | `output/view_id_name.json` |
| `profile_edm_fields.py` | goethe-faust/scripts/ | `output/edm_field_profile.json`, `output/edm_field_profile.csv` |
| `profile_json_keys.py` | goethe-faust/scripts/ | `output/edm_json_key_profile.csv` |

### Phase 4 — dc:type / htype analysis

| Script | Source | Output |
|---|---|---|
| `count_dctype_by_mediatype.py` | goethe-faust/scripts/ | `output/dctype_sparte*.csv` (one per sector) |
| `count_dctype_gnd_coverage.py` | goethe-faust/scripts/ | `output/dctype_gnd_coverage.csv` |
| `count_htype_by_sector.py` | goethe-faust/scripts/ | `output/htype_by_sector.csv` |
| `top10_dctype_by_sector.py` | goethe-faust/scripts/ | `output/top10_dctype_by_sector.csv` |
| `top10_dctype_per_htype.py` | goethe-faust/scripts/ | `output/top10_dctype_per_htype.csv`, `...-annotated.csv` |
| `dispatch_signal_ratio.py` | goethe-faust/scripts/ | `output/dispatch_signal_ratio.csv`, `output/dispatch_fallback.csv` |
| `summarise_vocab_coverage.py` | goethe-faust/scripts/ | `output/vocab_coverage_summary.csv` |

### Phase 5 — Dispatch validation

| Script | Source | Output |
|---|---|---|
| `validate_dispatch.py` | goethe-faust/scripts/ | `output/dispatch_validation.csv`, `output/validation_sample.csv` |
| `validate_sample.py` | goethe-faust/scripts/ | stdout only |
| `inspect_fallback.py` | goethe-faust/scripts/ | stdout only |
| `sample_type_dispatch.py` | goethe-faust/scripts/ | stdout only |
| `analyse_ispartof.py` | goethe-faust/scripts/ | evidence for isPartOf alignment (transform-props-mapping-adr.md D12) |

### Config generation (outputs → gemea/scripts/config/)

These scripts generate the lookup tables consumed by `gemea/scripts/transform/`.
Outputs are checked in under `gemea/scripts/config/` (source: `goethe-faust/output/config/`).

| Script | Source | Output |
|---|---|---|
| `gen_dctype_class_mapping.py` | goethe-faust/scripts/ | `config/lookup_dctype_to_class.csv` |
| `gen_htype_doco_mapping.py` | goethe-faust/scripts/ | `config/lookup_htype_doco_rico.csv/json` |
| `gen_image_type2class.py` | goethe-faust/scripts/ | `config/image_type2class.json` |
| `gen_video_type2class.py` | goethe-faust/scripts/ | `config/video_type2class.json` |
| `gen_agent_alignment_rows.py` | goethe-faust/scripts/ | `config/lookup_class_prop_alignment.csv` |

### Excluded from goethe-faust/scripts/

| Script | Reason |
|---|---|
| `align_ddbedm_to_mocho.py` | Transform entry point, not corpus analysis |
| `visualise_items.py`, `plot_latex_figs.py`, `translate_and_plot.py`, `summarise_results.py`, `match_objecttypes.py` | babel-ddb era |
| `monitor_transform.sh`, `run-transform-sector.sh`, `run_gemea_dryrun.sh`, `run_gemea_transform.sh`, `verify_transform_output.py` | Transform pipeline, not corpus analysis |
| `fix_nq_iris.py`, `split_nq.py` | Transform post-processing |
| `open_diagram.py`, `openwebui-sparql-tool.py`, `setup_venv.sh`, `merge_stats.py`, `extract_sqlite_sample.py` | Internal utilities |
| `analyse_description.py`, `analyse_language.py`, `analyse_locations.py`, `analyse_extent.py`, `analyse_spatial_event_overlap.py`, `analyse_lang_tags_by_entity.py` | Not cited in alignment docs |
| `contributor_agent_coverage.py`, `creator_agent_coverage.py`, `event_hastype_coverage.py`, `timespan_date_coverage.py` | Not cited in alignment docs |
| `count_dctype_sparte004.py`, `inspect_json_schema.py`, `link_gnd_works.py` | Sector-specific POC / Phase 0 pipeline |

---

## 4. goethe-faust/output/ — corpus analysis outputs only

All files are in git except those listed as gitignored.

### Include

| File | Notes |
|---|---|
| `fig1_metadata_format.png` – `fig6_view_fields_top20.png` | Corpus characterization figures |
| `fig2_sparte.png`, `fig_years.png`, `dataset-summary.png` | |
| `items-analysis.json`, `years-analysis.json` | |
| `view_id_name.json`, `edm_field_profile.json` | |
| `edm_json_key_profile.csv`, `edm_field_profile.csv` | |
| `alignment_ddbedm_mocho.json`, `alignment_ddbedm_mocho.csv` | |
| `dctype_sparte001.csv` – `dctype_sparte007.csv` | |
| `dctype_frequency_all.csv`, `dctype_gnd_coverage.csv` | |
| `dctype_dispatch_sample.csv`, `dctype_dispatch_summary.csv` | |
| `dctype_to_gnd_uri.csv` | |
| `htype_by_sector.csv` | |
| `top10_dctype_by_sector.csv` | |
| `top10_dctype_per_htype.csv`, `top10_dctype_per_htype-annotated.csv` | |
| `dispatch_signal_ratio.csv`, `dispatch_fallback.csv` | |
| `dispatch_validation.csv` | 9.2 MB — largest included file |
| `validation_report.csv`, `validation_sample.csv` | |
| `vocab_coverage_summary.csv` | |
| `items-dataframe-sample.csv` | |
| `ddb-type2fabio.json` | |

### Gitignored

| File | Reason |
|---|---|
| `ddbedm-goethe-faust.nt` | 1.3 GB |
| `ddbedm-goethe-faust.nt.gz` | 120 MB |
| `items-all-goethe-faust_meta.parquet` | 25 MB, binary |
| `items-dataframe.parquet` / `.parquet.zip` | 8 MB / 6.5 MB, binary |
| `transform/` | Timestamped transform run artefacts |
| `mocho-transform/` | Internal |
| `transcripts/` | Internal |
| `config/` | Moved to `gemea/scripts/config/` |

---

## 5. Notes from goethe-faust/notes/ relevant to gemea/

Excludes `corpus-analysis.md` and `transform-*.md` (already in scope).

### Directly relevant — keep/move to gemea/notes/

| Note | Why |
|---|---|
| `entity-property-mapping.md` | Approved EDM → mocho/RDA alignment table; backs paper §resource |
| `audio-type-class-mapping.md` | Justification for `config/audio_type2class.json` |
| `image-type-class-mapping.md` | Justification for `config/image_type2class.json` |
| `video-type-class-mapping.md` | Justification for `config/video_type2class.json` |
| `tabularasa.md` | 6-layer conceptual model for EDM→mocho; theoretical framing |
| `ddbedm-prov-o-plan.md` | PROV-O mapping, in-progress; pipeline provenance layer |
| `s4-dispatch-plan.md` | sparte004 dispatch design; part of alignment decision trail |
| `inputs.md` | Input inventory (per project convention) |
| `outputs.md` | Output inventory |

### Relevant but lower priority

| Note | Why |
|---|---|
| `goethe-faust-gnd-linking-plan.md` | GND Werk linking plan (Phase 0); referenced by transform-adr.md |
| `prov-lm-future-plan.md` | Future provenance work; useful for paper §sustainability |
| `graph-views-plan.md` | Future SPARQL views design; useful for paper §impact |
| `isbd-title-analysis.md` | ISBD analysis; mostly NER (next phase) but overlaps with title extraction |

### Infrastructure — relevant to gemea deployment

| Note | Why |
|---|---|
| `infra-local-setup.md` | Local service setup (Ollama, Docker, QLever) |
| `plan-configurable-setup.md` | Configurable setup.sh plan; ties to `setup_gnd_qlever.sh` in repo |
| `ollama-qlever-mcp-plan.md` | MCP+QLever integration; referenced in ddbkg README |

### Exclude — internal/session artefacts

| Note | Reason |
|---|---|
| `how-claude-transcript.md`, `memory-handover-20260414.md`, `session-summary-final-dataset.md` | Session notes |
| `troubleshooting-mcpo.md`, `troubleshooting-openwebui-password.md` | Operational one-offs |
| `openwebui-native-tool.md`, `openwebui-ollama-setup.md` | OpenWebUI specific |
| `adhoc-manifestation-types.md` | Documents a script excluded from the repo |
| `tabularasa-mocho-plan.md` | Internal fix plan, superseded by transform-revised-plan.md |
| `plan-check-script.md` | check.sh plan, not implemented |

---

## 6. Root README.md outline

```
## 0. What is GeMeA
   One-paragraph blurb: KG for 65M DDB cultural heritage objects, EDM → mocho
   alignment, QLever + SHMARQL self-hosting. SPARQL endpoint URL (fill after deployment).

## 1. Resource statistics
   Use tab:scale from paper/iswc-2026/30-resource.tex.
   Columns: Sector | Objects | Total triples | DDB-EDM triples | MOCHO triples | PROV triples
   | Sector            | Objects    | Total triples     | DDB-EDM       | MOCHO       | PROV        |
   | Library           | 18,338,116 | 1,930,178,220     | 1,040,390,087 | 356,952,292 | 532,835,841 |
   | Archive           |  3,456,119 |   467,439,123     |   259,483,277 |  61,795,115 | 146,160,731 |
   | Museum            |  2,011,841 |   230,484,127     |   123,795,378 |  48,164,578 |  58,524,171 |
   | Media Library     |  1,709,846 |   258,176,923     |   145,905,243 |  58,871,240 |  53,400,440 |
   | Research          |  1,165,891 |   138,118,201     |    75,842,237 |  24,633,128 |  37,642,836 |
   | Monument Preserv. |     79,393 |     9,020,751     |     4,852,432 |   1,555,297 |   2,613,022 |
   | Others            |     85,408 |     9,996,438     |     5,487,618 |   1,958,508 |   2,550,312 |
   | **Total**         | **26,846,614** | **3,043,413,783** | **1,655,756,272** | **553,930,158** | **833,727,353** |

## 2. Downloads & endpoints
   | Resource | URL |
   |---|---|
   | GeMeA N-Quads dump | https://gemea.ise.fiz-karlsruhe.de/downloads/gemea |
   | Goethe-Faust corpus (JSONL + N-Quads) | https://gemea.ise.fiz-karlsruhe.de/downloads/goethe-faust/ |
   | SHMARQL Linked Data browser | https://gemea.ise.fiz-karlsruhe.de/shmarql |

## 3. Pipeline
   Narrative + diagram covering:
   - Phase 0: DDB API → SQLite → N-Triples (export_ddb.py)
   - POC: goethe-faust/ — 115K records, corpus analysis, class dispatch design
   - Phase 1: EDM → mocho transform (scripts/transform/)
   - Phase 1b: GND agent enrichment
   - Phase 3: QLever ingest + SHMARQL frontend

## 3. Directory structure
   Annotated repo tree (scripts/, goethe-faust/, paper/).

## 4. Self-hosting
   QLever + SHMARQL quick-start (adapt from goethe-faust/README.md).
   Prerequisites checklist, docker compose commands, port defaults.

## 5. License
   | Component | License |
   |-----------|---------|
   | Code      | MIT     |
   | Data      | CC BY 4.0 |

## 6. Troubleshooting
   T1–T5: QLever permission denied, port conflict, NQ file not found,
   container dependency failure, MCP config. Adapt from infra-local-setup.md.

## 7. Caveats
   - Goethe-Faust POC covers 115K records, not full 27M corpus
   - NER enrichment (Phase 2) deferred
   - GND Werk linking partial (Phase 0 in progress)
   - Resource metadata (VoID, DCAT, persistent URI) deferred post-acceptance

## 8. Citation
   BibTeX block for ISWC 2026 paper.
```

---

## 7. Curated requirements.txt (merged gemea + goethe-faust)

| Package | Needed by |
|---|---|
| `requests` | `fetch-search-all.py` |
| `tqdm` | fetch + analysis scripts |
| `pandas` | `build_dataframe.py`, analysis scripts |
| `pyarrow` | `build_dataframe.py` |
| `matplotlib` | `analyse_years.py` |
| `ijson` | large JSONL streaming |
| `isodate` | temporal analysis |
| `duckdb` | dispatch validation scripts |
| `rapidfuzz` | `gen_htype_doco_mapping.py` |
| `langcodes` | `transform/utils.py` |
| `rdflib` | transform package |

Drop from source requirements.txt: `fasttext-wheel`, `gliner`, `onnxruntime`, `torch`,
`transformers`, `sentence-transformers`, `wordcloud`, `pyoxigraph`, `networkx`,
`deep-translator`, `scikit-learn`, `beautifulsoup4`.

---

## 8. To create from scratch

| File | Notes |
|---|---|
| `README.md` (repo root) | Landing page: what GeMeA is, repo layout, quick-start |
| `CITATION.cff` | GeMeA ISWC 2026 citation |
| `goethe-faust/LICENSE` | MIT (same as gemea root LICENSE) |
| `goethe-faust/scripts/README.md` | New, corpus-analysis focused; replaces ddbkg version |
| `gemea/scripts/README.md` | Documents transform → NQ → QLever indexing workflow |
| `gemea/scripts/transform/README.md` | Documents the transform package; links to `docs/adr/transform-adr.md`, `transform-props-mapping-adr.md`, `transform-script-adr.md` |
| `goethe-faust/data/.gitignore` | Excludes `items-all-goethe-faust.json` |
| `goethe-faust/output/.gitignore` | Excludes large/binary/internal files (see §4) |

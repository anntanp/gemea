## Full corpus transform — `run_gemea_transform.sh`

Single command that runs the complete two-pass pipeline across all 7 sectors.
Run from the `goethe-faust/` project root inside a `tmux` or `screen` session on teach03.

### Steps

1. **Activate the virtual environment**

   ```bash
   source .venv/bin/activate
   ```

2. **Start a fresh run** (wipes previous outputs for this version):

   ```bash
   bash scripts/run_gemea_transform.sh --new
   ```

   Or **resume** after interruption (skips sectors with non-empty `.nq` output):

   ```bash
   bash scripts/run_gemea_transform.sh --resume
   ```

   The script runs four phases automatically:

   | Phase | What happens |
   |---|---|
   | 0 — Prescan | 7 sectors in parallel → `prov.duckdb` (with full metadata), `concept_labels.duckdb`, `agent_labels.duckdb`, per-sector `*_meta.parquet` |
   | 0.5 — Regen prov NQ | Single call: reads `prov.duckdb` metadata columns → writes `prov-shared.nq` |
   | 1+2 — Export + Transform | Each sector: SQLite → JSONL → N-Quads (128 workers total, all sectors in parallel); workers read `prov.duckdb` to suppress already-emitted shared nodes |
   | 3 — DuckDB merge | All `*-werk-staging.duckdb` shards → `werk-staging-merged.duckdb` |
   | 4 — NQ split + merge | `.nq` files split by graph into per-graph `.nt`; `prov-shared.nq` included |

3. **Check outputs** under the dated output directory:

   ```
   /data/gemea/www/downloads/gemea/<yyyymmdd>/
     nq/                           per-graph .nt files (ddbedm.nt, mocho.nt, prov.nt)
     s{1..7}/                      per-sector .nq, .duckdb, -stats.json, -errors.jsonl, .log
     werk-staging-merged.duckdb
     prov.duckdb                   PROV-O shared node URIs + metadata (uri, entity_type, label, url, identifier, isil, rec_type, provider_uri)
     concept_labels.duckdb
     agent_labels.duckdb
     prov-shared.nq                generated from prov.duckdb via Phase 0.5 regen; can be regenerated at any time
     parquet/s{1..7}_meta.parquet  per-sector metadata Parquet
   ```

### Arguments to change

**Hardcoded paths** — edit directly in the script:

| Variable | Default | Change when |
|---|---|---|
| `SQLITE_DIR` | `/data/ddb/data` | SQLite files are elsewhere |
| `EXPORT_DIR` | `/data/ddb/gemea/json-export` | JSONL export should go elsewhere |
| `OUT_BASE` | `/data/gemea/www/downloads/gemea/<yyyymmdd>` | Edit `OUT_BASE=` line to change output root |
| `WORKERS` | `s1:20 s2:50 s3:1 s4:10 s5:15 s6:15 s7:1` (112 total) | Tune to available cores; values are proportional to sector record counts |

**Override env vars** — prepend to the command, no script edit needed:

| Variable | Overrides | Notes |
|---|---|---|
| `PROV_DB_ARG` | `prov.duckdb` path | Share across runs to skip re-emitting known PROV-O nodes |
| `CONCEPT_LABELS_DB_ARG` | `concept_labels.duckdb` path | |
| `AGENT_LABELS_DB_ARG` | `agent_labels.duckdb` path | |
| `PARQUET_DIR_ARG` | per-sector Parquet output dir | |
| `PARQUET_MERGE_ARG` | if set, merges all per-sector Parquet into one file at this path | Leave unset to skip the merge step |

Example with overrides:

```bash
PROV_DB_ARG=/data/shared/prov.duckdb \
PARQUET_MERGE_ARG=/data/gemea/all_meta.parquet \
bash scripts/run_gemea_transform.sh --new
```

---
## Pre-Parquet Workflow?
#### First Run Prerequisite:
- `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`

#### Step 0. Pre-Scan

`--prov-out` is no longer a prescan argument. `prov-shared.nq` is generated in Step 0.5.

- teach03
```
$ python3 -m transform.prescan \
  --db                /data/ddb/data/s7.sqlite \
  --prov-db           ${OUTPUT_DIR}/prov.duckdb \
  --concept-labels-db ${OUTPUT_DIR}/concept_labels.duckdb \
  --agent-labels-db   ${OUTPUT_DIR}/agent_labels.duckdb \
  --lido              ../output/config/lido_event_types.csv \
  --parquet-out       ${OUTPUT_DIR}/s7_meta.parquet

```

Run 2026-05-21/22:

| Sector | Records (DB) | Errors | Duration | Prov nodes | Concept URIs | Agent URIs |
|--------|-------------:|-------:|----------|----------:|-------------:|-----------:|
| s1 | 3,638,025 | 3 | 22m 56s | 425 | 50,182 | 6,109 |
| s2 | 18,570,245 | 0 | 2h 5m 44s | 412 | 107,362 | 821,384 |
| s3 | 83,575 | 0 | 26s | 20 | 128 | 923 |
| s4 | 1,227,316 | 1† | 6m 43s | 131 | 4,225 | 25,586 |
| s5 | 1,799,840 | 2 | 10m 43s | 58 | 26,014 | 9,173 |
| s6 | 2,117,728 | 0 | 12m 28s | 656 | 39,616 | 6,148 |
| s7 | 89,904 | 0 | 41s | 61 | 970 | 6,323 |

† s4 logs 1,227,252 processed vs. 1,227,316 in DB — 64 records unaccounted despite 1 logged error. s3 logs 83,572 processed vs. 83,575 in DB with 0 errors — 3 records unaccounted. All errors are `decompress/parse error: Expecting value` on empty compressed blobs.

```
2026-05-22 07:24:52 INFO     Regenerated /home/ann/gemea/output/parquet/prov-shared.nq: 9388 lines
```

```

#### Step 0.5. Generate prov-shared.nq

Run once after all sectors' prescan is complete. Reads `prov.duckdb` metadata columns
and writes complete PROV-O triples (provider names, dataset labels, etc.).
Safe to re-run at any time — overwrites the output file.

```bash
PYTHONPATH=~/goethe-faust python3 -m transform.prescan regen \
  --prov-db  ~/gemea/output/parquet/prov.duckdb \
  --prov-out ~/gemea/output/parquet/prov-shared.nq
```

Or via the standalone script (no PYTHONPATH needed):
```bash
python3 gemea/scripts/py/regen_prov_nq.py \
  --prov-db  ~/gemea/output/parquet/prov.duckdb \
  --prov-out ~/gemea/output/parquet/prov-shared.nq
```

#### Step 1. Transform

Pass `--prov-db` so workers suppress re-emitting shared PROV-O nodes already in prov.duckdb.

```bash

bash scripts/run-transform-sector.sh --merge --sector s5 --workers 15 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s2 --workers 50 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s6 --workers 15 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s1 --workers 20 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s3 --workers 1 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s4 --workers 10 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb

bash scripts/run-transform-sector.sh --merge --sector s7 --workers 1 --prov-db /data/gemea/www/downloads/gemea/20260523/duckdb/prov.duckdb
```

defaults:
--output-dir /data/gemea/www/downloads/gemea/<yyyymmdd>
--sqlite-dir /data/gemea/sqlite

```

```

#### Step 2a. Test
cd /data/gemea
uv run linker.py <source-dir> /data/gemea/qlever_test_nq/
uv run linker.py /data/gemea/www/downloads/gemea/20260511/nq/ /data/gemea/qlever_test_nq/. 
cd /data/gemea/qlever_test_nq
uv run qlever index --name gemea --overwrite-existing

#### Step 2b. Actual
cd /data/gemea
uv run linker.py /data/gemea/www/downloads/gemea/20260511/nq/ /data/gemea/qlever
cd /data/gemea/qlever
vi Qleverfile
- edit `INPUT_FILES`
- edit `FORMAT`
- edit `CAT_INPUT_FILES`, change to zcat if using `.nq.gz`
uv run qlever index --name gemea --overwrite-existing


#### Ollama + OpenWebUI
https://kast.epoz.org/


#### Caddyfile `/home/etienne/ise.fiz-karlsruhe.de/`

```
2026-05-12 13:56:22.673 - INFO: QLever index builder b7623fc, compiled on Sun Apr 12 04:30:08 UTC 2026 using git hash b7623f
2026-05-12 13:56:22.673 - INFO: Locale was not specified in settings file, default is en_US
2026-05-12 13:56:22.673 - INFO: You specified "locale = en_US" and "ignore-punctuation = 0"
2026-05-12 13:56:22.673 - INFO: You specified "num-triples-per-batch = 20,000,000", choose a lower value if the index builder runs out of memory
2026-05-12 13:56:22.673 - INFO: By default, integers that cannot be represented by QLever will throw an exception
2026-05-12 13:56:22.673 - WARN: Implicitly using the parallel parser for a single input file for reasons of backward compatibility; this is deprecated, please use the command-line option --parallel-parsing or -p
2026-05-12 13:56:22.673 - INFO: Processing triples from single input stream /dev/stdin (parallel = true) ...
2026-05-12 13:56:22.674 - INFO: Parsing input triples and creating partial vocabularies, one per batch ...
2026-05-12 14:08:06.625 - INFO: Triples parsed: 946,175,401 [average speed 1.3 M/s, last batch 1.4 M/s, fastest 1.5 M/s, slowest 1.0 M/s]
2026-05-12 14:08:11.389 - INFO: Number of triples created (including QLever-internal ones): 1,016,416,815 [may contain duplicates]
2026-05-12 14:08:11.389 - INFO: Number of partial vocabularies created: 48
2026-05-12 14:08:11.389 - INFO: Merging partial vocabularies ...
2026-05-12 14:10:03.522 - INFO: Words merged: 175,136,907 [average speed 1.6 M/s, last batch 1.7 M/s, fastest 2.1 M/s, slowest 1.1 M/s]
2026-05-12 14:10:03.897 - INFO: Finished writing compressed internal vocabulary, size = 4.4 GB [uncompressed = 12.8 GB, ratio = 33%]
2026-05-12 14:10:03.898 - INFO: Number of words in external vocabulary: 175,136,907
2026-05-12 14:10:15.656 - INFO: Converting triples from local IDs to global IDs ...
2026-05-12 14:11:02.261 - INFO: Triples converted: 1,016,416,815 [average speed 21.8 M/s, last batch 10.2 M/s, fastest 32.7 M/s, slowest 5.6 M/s]
2026-05-12 14:11:13.027 - INFO: Creating permutations SPO and SOP ...
2026-05-12 14:14:11.356 - INFO: Number of inputs to `uniqueView`: 946,175,4014 M/s, last batch 8.7 M/s, fastest 13.7 M/s, slowest 0.5 M/s]
2026-05-12 14:14:11.356 - INFO: Number of unique elements: 600,544,765
2026-05-12 14:14:11.356 - INFO: Triples sorted: 600,544,765 [average speed 3.4 M/s, last batch 8.7 M/s, fastest 13.7 M/s, slowest 0.5 M/s]
2026-05-12 14:14:12.729 - INFO: Statistics for SPO: #relations = 90,355,162, #blocks = 12,841, #triples = 600,544,765
2026-05-12 14:14:12.730 - INFO: Statistics for SOP: #relations = 90,355,162, #blocks = 12,841, #triples = 600,544,765
2026-05-12 14:14:12.757 - INFO: Number of distinct patterns: 2,374
2026-05-12 14:14:12.757 - INFO: Number of subjects with pattern: 90,355,162 [all]
2026-05-12 14:14:12.757 - INFO: Total number of distinct subject-predicate pairs: 509,866,231
2026-05-12 14:14:12.757 - INFO: Average number of predicates per subject: 5.6
2026-05-12 14:14:12.757 - INFO: Average number of subjects per predicate: 11,330,361
2026-05-12 14:14:16.023 - INFO: Creating permutations OSP and OPS ...
2026-05-12 14:16:19.782 - INFO: Triples sorted: 600,544,765 [average speed 4.9 M/s, last batch 4.6 M/s, fastest 19.9 M/s, slowest 1.2 M/s]
2026-05-12 14:16:19.816 - INFO: Statistics for OSP: #relations = 126,933,434, #blocks = 17,287, #triples = 600,544,765
2026-05-12 14:16:19.816 - INFO: Statistics for OPS: #relations = 126,933,434, #blocks = 17,287, #triples = 600,544,765
2026-05-12 14:16:20.186 - INFO: Adding 90,355,162 triples to the POS and PSO permutation for the internal `ql:has-pattern` ...
2026-05-12 14:16:27.501 - INFO: Creating permutations PSO and POS ...
2026-05-12 14:16:47.461 - INFO: Number of inputs to `uniqueView`: 160,596,5762 M/s, last batch 0.8 M/s, fastest 20.8 M/s, slowest 0.8 M/s]
2026-05-12 14:16:47.461 - INFO: Number of unique elements: 103,047,129
2026-05-12 14:16:47.461 - INFO: Triples sorted: 103,047,129 [average speed 5.2 M/s, last batch 0.8 M/s, fastest 20.8 M/s, slowest 0.8 M/s]
2026-05-12 14:16:48.418 - INFO: Statistics for PSO: #relations = 119, #blocks = 3,310, #triples = 103,047,129
2026-05-12 14:16:48.419 - INFO: Statistics for POS: #relations = 119, #blocks = 3,310, #triples = 103,047,129
2026-05-12 14:16:58.730 - INFO: Creating permutations PSO and POS ...
2026-05-12 14:18:37.630 - INFO: Triples sorted: 600,544,765 [average speed 6.1 M/s, last batch 11.0 M/s, fastest 22.0 M/s, slowest 0.9 M/s]
2026-05-12 14:18:38.950 - INFO: Statistics for PSO: #relations = 45, #blocks = 19,237, #triples = 600,544,765
2026-05-12 14:18:38.950 - INFO: Statistics for POS: #relations = 45, #blocks = 19,237, #triples = 600,544,765
2026-05-12 14:18:39.396 - INFO: Index build completed
2026-05-12 14:18:39.397 - INFO:
2026-05-12 14:18:39.397 - INFO: Adding text index ...
2026-05-12 14:18:39.397 - INFO: Considering each literal as a text record
2026-05-12 14:18:39.397 - INFO: The git hash used to build this index was "b7623f"
2026-05-12 14:18:39.397 - INFO: Reading vocabulary from file gemea.vocabulary.words ...
2026-05-12 14:18:39.405 - INFO: Done, number of words: 175,136,907
2026-05-12 14:18:39.406 - INFO: Number of words in internal vocabulary (these are also part of the external vocabulary): 175,327
2026-05-12 14:22:50.837 - INFO: Reading vocabulary from file gemea.text.vocabulary ...
2026-05-12 14:22:51.158 - INFO: Done, number of words: 17,872,400
2026-05-12 14:22:51.664 - INFO: Building the half-inverted index lists ...
2026-05-12 14:49:50.311 - INFO: Statistics for text index: #words = 410,168,105, #blocks = 354,167
2026-05-12 14:49:50.337 - INFO: Text index build completed
```
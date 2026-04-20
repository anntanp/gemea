# DDB All-Sectors Export Plan

Export N-Triples + Parquet for sectors s1, s3–s7 (P03–P14). Sector s2 already done (P01/P02).

---

## Context

`export_s2.py` was developed for sector 2 but works on any `s*.sqlite` cortex file.
Renamed to `export_ddb.py` to reflect general use. A new remote-server batch driver
`export_batch_remote.sh` processes the remaining sectors unattended.

## Checklist tasks produced

| Sector sqlite | NT output (P##) | Parquet output (P##) |
|---|---|---|
| `s1.sqlite` | P03 `data/out/s1/edm_*.nt` | P09 `data/out/s1/s1_meta.parquet` |
| `s3.sqlite` | P04 `data/out/s3/edm_*.nt` | P10 `data/out/s3/s3_meta.parquet` |
| `s4.sqlite` | P05 `data/out/s4/edm_*.nt` | P11 `data/out/s4/s4_meta.parquet` |
| `s5.sqlite` | P06 `data/out/s5/edm_*.nt` | P12 `data/out/s5/s5_meta.parquet` |
| `s6.sqlite` | P07 `data/out/s6/edm_*.nt` | P13 `data/out/s6/s6_meta.parquet` |
| `s7.sqlite` | P08 `data/out/s7/edm_*.nt` | P14 `data/out/s7/s7_meta.parquet` |

## Scripts

| Script | Purpose |
|---|---|
| `scripts/py/export_ddb.py` | Export one `s*.sqlite` → batched NT + Parquet (renamed from `export_s2.py`) |
| `scripts/sh/export_batch_remote.sh` | Remote-server batch driver: processes s1, s3–s7 sequentially; skip-if-done; timestamped log |

## export_batch_remote.sh design

### Env-var overrides

| Variable | Default | Purpose |
|---|---|---|
| `VENV_DIR` | `./venv` | Python venv path |
| `SQLITE_DIR` | `/data/ddb` | Input sqlite directory |
| `OUT_BASE` | `/data/ddb/out` | Root output directory |
| `EXPORT_SCRIPT` | `./scripts/py/export_ddb.py` | Path to export_ddb.py |
| `MAX_WORKERS` | `nproc - 2`, min 1 | Workers passed to export_ddb.py |
| `BATCH_SIZE` | `100000` | Batch size passed to export_ddb.py |
| `LOG_FILE` | `/data/ddb/logs/export_batch.log` | Timestamped run log |

### Skip-if-done (per sector)

Done when: `$OUT_BASE/<stem>/<stem>_meta.parquet` exists **and** no `.export_progress.json`
checkpoint. Resumes automatically if checkpoint is present (export_ddb.py supports it).

### Error handling

Each sector is wrapped; failure logs the error and continues to the next sector.
Exit code non-zero if any sector failed.

### Exit summary

```
=== Summary ===
Processed : N
Skipped   : N
Failed    : N
Elapsed   : Xm Ys
Log       : /data/ddb/logs/export_batch.log
```

## Files changed during rename

| File | Change |
|---|---|
| `scripts/py/export_ddb.py` | New — renamed from `export_s2.py` |
| `scripts/py/export_s2.py` | Deleted |
| `scripts/py/export_ddb_parquet.py` | Renamed from `export_s2_parquet.py`; import updated: `from export_ddb import` |
| `scripts/py/export_s2_parquet.py` | Deleted |
| `scripts/sh/process_sqlite.sh` | Call updated: `export_ddb.py` |
| `scripts/sh/smoke_test_export_s2.sh` | Import updated: `from export_ddb import` |
| `scripts/ner/sr11_sample_validation.py` | Comment updated |
| 6× `notes/**/*.md` | Name references updated |
| `scripts/README.md` | New entries added |

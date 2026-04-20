#!/usr/bin/env bash
# Purpose:      Run export_ddb.py against one or more s*.sqlite files
# Usage:        bash scripts/sh/process_sqlite.sh [s1.sqlite s2.sqlite ...]
#               If no arguments given, processes all data/sqlite/s*.sqlite files
# Inputs:       data/sqlite/s*.sqlite  — one per sector
# Outputs:      data/out/<stem>/edm_WW_NNNN.nt     — batched N-Triples per worker/batch
#               data/out/<stem>/<stem>_meta.parquet — ProvidedCHO metadata
#               data/out/<stem>/.export_progress.json — checkpoint (deleted on success)
# Dependencies: Python venv with pyoxigraph, pyarrow
# Assumptions:  Run from project root; .venv exists

set -euo pipefail
cd "$(dirname "$0")/../.."

source .venv/bin/activate

# --- configuration (override via env) ---
MAX_WORKERS="${MAX_WORKERS:-$(python3 -c 'import multiprocessing; print(max(1, multiprocessing.cpu_count() - 2))')}"
BATCH_SIZE="${BATCH_SIZE:-100000}"
BASE_OUT="data/out"

# --- resolve input files ---
if [[ $# -gt 0 ]]; then
    FILES=("$@")
else
    FILES=(data/sqlite/s*.sqlite)
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "ERROR: no sqlite files found" >&2
    exit 1
fi

echo "Processing ${#FILES[@]} file(s) with MAX_WORKERS=${MAX_WORKERS}, BATCH_SIZE=${BATCH_SIZE}"
echo

for DB in "${FILES[@]}"; do
    STEM="$(basename "${DB}" .sqlite)"
    OUT="${BASE_OUT}/${STEM}"
    echo "=== ${DB} → ${OUT} ==="
    mkdir -p "${OUT}"
    OUTPUT_DIR="${OUT}" \
    MAX_WORKERS="${MAX_WORKERS}" \
    BATCH_SIZE="${BATCH_SIZE}" \
        python3 scripts/py/export_ddb.py "${DB}"
    echo
done

echo "All done."

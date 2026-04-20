#!/usr/bin/env bash
# Purpose:      Batch-export DDB sector sqlite files (P03–P14) to N-Triples + Parquet
#               on a remote server; idempotent — skips sectors already complete.
# Usage:        bash scripts/sh/export_batch_remote.sh [s1.sqlite s3.sqlite ...]
#               With no arguments, processes s1 s3 s4 s5 s6 s7 under SQLITE_DIR.
#               Override settings via env vars (see configuration section below).
# Inputs:       SQLITE_DIR/s{1,3,4,5,6,7}.sqlite  — one per remaining DDB sector
# Outputs:      OUT_BASE/<stem>/ddbedm-<stem>_WW_NNNN.nt  — batched N-Triples (P03–P08)
#               OUT_BASE/<stem>/<stem>_meta.parquet        — metadata Parquet (P09–P14)
#               LOG_FILE                                   — timestamped run log
# Dependencies: Python venv with pyoxigraph, pyarrow; export_ddb.py
# Assumptions:  VENV_DIR/bin/activate exists; sqlite files are named s<N>.sqlite;
#               sector s2 is already complete and is not reprocessed here.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# --- configuration (override via env) ---
VENV_DIR="${VENV_DIR:-${PROJECT_ROOT}/venv}"
SQLITE_DIR="${SQLITE_DIR:-/data/ddb}"
OUT_BASE="${OUT_BASE:-/data/ddb/out}"
EXPORT_SCRIPT="${EXPORT_SCRIPT:-${PROJECT_ROOT}/scripts/py/export_ddb.py}"
MAX_WORKERS="${MAX_WORKERS:-$(python3 -c 'import multiprocessing; print(max(1, multiprocessing.cpu_count() - 2))')}"
BATCH_SIZE="${BATCH_SIZE:-100000}"
LOG_FILE="${LOG_FILE:-/data/ddb/logs/export_batch.log}"

# --- counters ---
processed=0
skipped=0
failed=0
start_ts=$(date +%s)

# --- logging ---
log() {
    local msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "${msg}"
    echo "${msg}" >> "${LOG_FILE}"
}

# --- exit summary ---
summary() {
    local end_ts elapsed mins secs
    end_ts=$(date +%s)
    elapsed=$(( end_ts - start_ts ))
    mins=$(( elapsed / 60 ))
    secs=$(( elapsed % 60 ))
    log "=== Summary ==="
    log "Processed : ${processed}"
    log "Skipped   : ${skipped}"
    log "Failed    : ${failed}"
    log "Elapsed   : ${mins}m ${secs}s"
    log "Log       : ${LOG_FILE}"
    if [[ ${failed} -gt 0 ]]; then
        exit 1
    fi
}
trap summary EXIT

# --- resolve input files ---
if [[ $# -gt 0 ]]; then
    files=("$@")
else
    default_stems=(s1 s3 s4 s5 s6 s7)
    files=()
    for stem in "${default_stems[@]}"; do
        files+=("${SQLITE_DIR}/${stem}.sqlite")
    done
fi

# --- preflight ---
mkdir -p "$(dirname "${LOG_FILE}")"

log "Host      : $(hostname)"
log "Date      : $(date)"
log "Project   : ${PROJECT_ROOT}"
log "VENV_DIR  : ${VENV_DIR}"
log "SQLITE_DIR: ${SQLITE_DIR}"
log "OUT_BASE  : ${OUT_BASE}"
log "Script    : ${EXPORT_SCRIPT}"
log "Workers   : ${MAX_WORKERS}"
log "Batch size: ${BATCH_SIZE}"
log "Files     : ${#files[@]}"

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
    log "ERROR: venv not found at ${VENV_DIR}/bin/activate"
    exit 1
fi

if [[ ! -f "${EXPORT_SCRIPT}" ]]; then
    log "ERROR: export script not found: ${EXPORT_SCRIPT}"
    exit 1
fi

# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"

# --- process each file ---
for db in "${files[@]}"; do
    stem="$(basename "${db}" .sqlite)"
    out="${OUT_BASE}/${stem}"
    parquet="${out}/${stem}_meta.parquet"
    checkpoint="${out}/.export_progress.json"

    if [[ ! -f "${db}" ]]; then
        log "SKIP ${db} — file not found"
        (( skipped++ ))
        continue
    fi

    # skip-if-done: parquet exists and no in-progress checkpoint
    if [[ -f "${parquet}" && ! -f "${checkpoint}" ]]; then
        log "SKIP ${stem} — already complete (${parquet})"
        (( skipped++ ))
        continue
    fi

    if [[ -f "${checkpoint}" ]]; then
        log "RESUME ${stem} — checkpoint found, resuming"
    else
        log "START ${stem}"
    fi

    mkdir -p "${out}"

    if OUTPUT_DIR="${out}" \
       MAX_WORKERS="${MAX_WORKERS}" \
       BATCH_SIZE="${BATCH_SIZE}" \
       python3 "${EXPORT_SCRIPT}" "${db}" 2>&1 | tee -a "${LOG_FILE}"
    then
        log "DONE ${stem}"
        (( processed++ ))
    else
        log "ERROR ${stem} — export_ddb.py exited non-zero"
        (( failed++ ))
    fi
done

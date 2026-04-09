#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Purpose:   Set up a local QLever SPARQL endpoint for GND Werk authority data
#            and register the mcp-server-qlever MCP server with Claude Code.
#
# Usage:     ./setup-gnd-werk-qlever-mcp.sh [--skip-convert] [--skip-mcp]
#
# Inputs:    data/gnd/authorities-gnd-werk_lds.jsonld.gz  (DNB open data, CC0)
#            ../mcp-server-qlever/scripts/jsonld-to-nt.py
#
# Outputs:   data/gnd/nt/werk.nt             (N-Triples, ~1.5 GB)
#            data/gnd/qlever-index/           (QLever index, ~300 MB)
#            QLever running on localhost:7020
#            Claude Code MCP server "gnd-werk" registered (project-scoped)
#
# Dependencies:
#   - Docker (>= 20)
#   - Python 3.10+ with ijson reachable via PYTHONPATH or installed
#   - claude CLI (~/.local/bin/claude) for MCP registration
#
# Assumptions:
#   - Script is run from any directory; all paths derived from BASH_SOURCE.
#   - The gemea project root is two levels above this script (scripts/sh/).
#   - mcp-server-qlever repo is a sibling of the gemea project root.
#   - Re-running is safe: conversion and index build are skipped if already done.
# -----------------------------------------------------------------------------

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GEMEA_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
MCP_SERVER_DIR="$(cd "${GEMEA_DIR}/../mcp-server-qlever" && pwd)"

JSONLD_GZ="${GEMEA_DIR}/data/gnd/authorities-gnd-werk_lds.jsonld.gz"
NT_FILE="${GEMEA_DIR}/data/gnd/nt/werk.nt"
INDEX_DIR="${GEMEA_DIR}/data/gnd/qlever-index"
COMPOSE_FILE="${GEMEA_DIR}/docker-compose.qlever-gnd.yml"
CONVERT_SCRIPT="${MCP_SERVER_DIR}/scripts/jsonld-to-nt.py"

QLEVER_PORT="${QLEVER_PORT:-7020}"
CLAUDE_BIN="${CLAUDE_BIN:-${HOME}/.local/bin/claude}"

SKIP_CONVERT=false
SKIP_MCP=false

# --- Parse arguments ---

for arg in "$@"; do
  case "$arg" in
    --skip-convert) SKIP_CONVERT=true ;;
    --skip-mcp)     SKIP_MCP=true ;;
    --help|-h)
      sed -n '2,/^# -{10}/p' "${BASH_SOURCE[0]}" | sed 's/^# \?//'
      exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# --- Logging ---

log()  { echo "[$(date '+%H:%M:%S')] $*"; }
warn() { echo "[$(date '+%H:%M:%S')] WARN: $*" >&2; }
die()  { echo "[$(date '+%H:%M:%S')] ERROR: $*" >&2; exit 1; }

log "=== GND Werk QLever + MCP setup ==="
log "gemea:      ${GEMEA_DIR}"
log "mcp-server: ${MCP_SERVER_DIR}"
log "nt file:    ${NT_FILE}"
log "index dir:  ${INDEX_DIR}"
log "endpoint:   http://localhost:${QLEVER_PORT}"

# --- Prerequisite checks ---

check_prereqs() {
  log "Checking prerequisites..."

  command -v docker >/dev/null 2>&1 || die "docker not found"
  docker info >/dev/null 2>&1       || die "Docker daemon is not running"

  [[ -f "${COMPOSE_FILE}" ]] || die "docker-compose file not found: ${COMPOSE_FILE}"
  [[ -f "${CONVERT_SCRIPT}" ]] || die "jsonld-to-nt.py not found: ${CONVERT_SCRIPT}"
  [[ -f "${JSONLD_GZ}" ]] || die "source data not found: ${JSONLD_GZ}"

  find_python310
}

find_python310() {
  # Prefer an explicit Python 3.10+ binary; fall back to system python3 if >= 3.10.
  local candidates=(
    python3.12 python3.11 python3.10
    /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /opt/homebrew/bin/python3.10
    /usr/local/bin/python3.12 /usr/local/bin/python3.11 /usr/local/bin/python3.10
  )

  for candidate in "${candidates[@]}"; do
    if command -v "$candidate" >/dev/null 2>&1; then
      local version
      version="$("$candidate" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)"
      local major
      major="$("$candidate" -c 'import sys; print(sys.version_info.major)' 2>/dev/null)"
      if [[ "$major" -eq 3 && "$version" -ge 10 ]]; then
        PYTHON="${candidate}"
        log "Python: ${PYTHON} (3.${version})"
        return
      fi
    fi
  done

  die "Python 3.10+ not found. Install via: brew install python@3.10"
}

# --- Phase 1: JSONLD → N-Triples conversion ---

convert_jsonld() {
  if [[ "${SKIP_CONVERT}" == true ]]; then
    log "Skipping conversion (--skip-convert)."
    return
  fi

  if [[ -s "${NT_FILE}" ]]; then
    local lines
    lines="$(wc -l < "${NT_FILE}")"
    log "werk.nt already exists (${lines} lines). Skipping conversion."
    return
  fi

  log "Converting ${JSONLD_GZ} → ${NT_FILE} ..."
  mkdir -p "$(dirname "${NT_FILE}")"

  # ijson may be installed only for Python 3.9 (gemea venv); expose it via PYTHONPATH.
  local venv_site="${GEMEA_DIR}/.venv/lib/python3.9/site-packages"
  local pythonpath=""
  if [[ -d "${venv_site}/ijson" ]]; then
    pythonpath="${venv_site}"
    log "ijson: using gemea venv at ${venv_site}"
  fi

  PYTHONPATH="${pythonpath}" "${PYTHON}" "${CONVERT_SCRIPT}" \
    --input "${JSONLD_GZ}" \
    --stats \
    > "${NT_FILE}"

  local lines
  lines="$(wc -l < "${NT_FILE}")"
  log "Conversion done: ${lines} triples written to ${NT_FILE}"
  [[ "${lines}" -gt 0 ]] || die "Conversion produced an empty file."
}

# --- Phase 2: Start QLever ---

start_qlever() {
  mkdir -p "${INDEX_DIR}"

  # If container is already healthy, nothing to do.
  local status
  status="$(docker inspect gemea-qlever-gnd-werk-1 --format '{{.State.Health.Status}}' 2>/dev/null || true)"
  if [[ "${status}" == "healthy" ]]; then
    log "QLever already running and healthy on port ${QLEVER_PORT}."
    return
  fi

  log "Starting QLever (docker compose up)..."
  QLEVER_PORT="${QLEVER_PORT}" docker compose -f "${COMPOSE_FILE}" up -d

  log "Waiting for QLever to become healthy (index build may take several minutes)..."
  wait_healthy
}

wait_healthy() {
  local retries=120
  local interval=5
  local elapsed=0

  for ((i = 1; i <= retries; i++)); do
    local s
    s="$(docker inspect gemea-qlever-gnd-werk-1 --format '{{.State.Health.Status}}' 2>/dev/null || true)"
    case "$s" in
      healthy)
        log "QLever is healthy after ${elapsed}s."
        return ;;
      "")
        # Container may have exited before health check registered.
        local state
        state="$(docker inspect gemea-qlever-gnd-werk-1 --format '{{.State.Status}}' 2>/dev/null || true)"
        [[ "${state}" == "exited" ]] && {
          docker logs gemea-qlever-gnd-werk-1 --tail 30 >&2
          die "QLever container exited unexpectedly."
        }
        ;;
    esac
    sleep "${interval}"
    elapsed=$(( i * interval ))
  done

  docker logs gemea-qlever-gnd-werk-1 --tail 30 >&2
  die "QLever did not become healthy within $(( retries * interval ))s."
}

# --- Phase 3: Smoke test ---

smoke_test() {
  log "Smoke test: querying triple count..."
  local count
  count="$(curl -sf "http://localhost:${QLEVER_PORT}" \
    --data-urlencode 'query=SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }' \
    -H "Accept: application/sparql-results+json" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['results']['bindings'][0]['n']['value'])")"
  log "Triple count: ${count}"
  [[ "${count}" -gt 0 ]] || die "Smoke test failed: zero triples returned."
}

# --- Phase 4: Register MCP server ---

register_mcp() {
  if [[ "${SKIP_MCP}" == true ]]; then
    log "Skipping MCP registration (--skip-mcp)."
    return
  fi

  if [[ ! -x "${CLAUDE_BIN}" ]]; then
    warn "claude CLI not found at ${CLAUDE_BIN}. Skipping MCP registration."
    warn "Register manually:"
    warn "  claude mcp add gnd-werk -- docker run --rm -i --network=host \\"
    warn "    ghcr.io/xorwell/mcp-server-qlever:latest -e http://localhost:${QLEVER_PORT}"
    return
  fi

  # Check if already registered to stay idempotent.
  if "${CLAUDE_BIN}" mcp list 2>/dev/null | grep -q "^gnd-werk"; then
    log "MCP server 'gnd-werk' already registered."
    return
  fi

  log "Registering MCP server 'gnd-werk' with Claude Code (project-scoped to gemea)..."
  (cd "${GEMEA_DIR}" && "${CLAUDE_BIN}" mcp add gnd-werk -- \
    docker run --rm -i --network=host \
    ghcr.io/xorwell/mcp-server-qlever:latest \
    -e "http://localhost:${QLEVER_PORT}")
  log "MCP server registered. Open a Claude Code session in ${GEMEA_DIR} to use it."
}

# --- Main ---

check_prereqs
convert_jsonld
start_qlever
smoke_test
register_mcp

log "=== Setup complete ==="
log "  SPARQL endpoint: http://localhost:${QLEVER_PORT}"
log "  MCP server:      gnd-werk (project-scoped to gemea)"
log "  Stop QLever:     docker compose -f ${COMPOSE_FILE} down"

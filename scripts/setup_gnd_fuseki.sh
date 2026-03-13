#!/usr/bin/env bash
# Purpose:      Start a local Fuseki SPARQL instance and load GND authority files
# Usage:        ./setup_gnd_fuseki.sh [--load <types>] [--start-only]
# Inputs:       data/gnd/authorities-gnd-*.jsonld.gz
# Outputs:      Running Fuseki container at http://localhost:3030/gnd/sparql
# Dependencies: docker, curl, gunzip, python3
# Assumptions:  GND .jsonld.gz files are in data/gnd/ relative to project root;
#               port 3030 is available; Docker daemon is running;
#               FUSEKI_ADMIN_PASSWORD env var set or default 'gnd' is acceptable

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data/gnd"
CONTAINER_NAME="gemea-fuseki-gnd"
FUSEKI_IMAGE="stain/jena-fuseki:latest"
FUSEKI_DATA_VOL="gemea-fuseki-gnd-data"   # named Docker volume for persistence
FUSEKI_HOST="http://localhost:3030"
DATASET="gnd"
ADMIN_PASSWORD="${FUSEKI_ADMIN_PASSWORD:-gnd}"  # override via env var

# Named graph base URI — consistent with gemea graph naming convention
GRAPH_BASE="http://gemea.ddb.de/graph/gnd"

# Valid entity type names (space-separated; used for --load all and validation)
ALL_ENTITY_TYPES="werk person geografikum koerperschaft kongress sachbegriff entityfacts"

# ── Entity type → file path ────────────────────────────────────────────────────
# Person file includes a date suffix; update if DNB releases a newer dump.
gnd_file_for() {
    local entity="$1"
    case "$entity" in
        werk)          echo "$DATA_DIR/authorities-gnd-werk_lds.jsonld.gz" ;;
        person)        echo "$DATA_DIR/authorities-gnd-person_lds_20260217.jsonld.gz" ;;
        geografikum)   echo "$DATA_DIR/authorities-gnd-geografikum_lds.jsonld.gz" ;;
        koerperschaft) echo "$DATA_DIR/authorities-gnd-koerperschaft_lds.jsonld.gz" ;;
        kongress)      echo "$DATA_DIR/authorities-gnd-kongress_lds.jsonld.gz" ;;
        sachbegriff)   echo "$DATA_DIR/authorities-gnd-sachbegriff_lds.jsonld.gz" ;;
        entityfacts)   echo "$DATA_DIR/authorities-gnd_entityfacts.jsonld.gz" ;;
        *) die "Unknown entity type: '$entity'. Valid: $ALL_ENTITY_TYPES" ;;
    esac
}

# ── Helpers ───────────────────────────────────────────────────────────────────
log()  { echo "[$(date +%H:%M:%S)] $*"; }
die()  { echo "ERROR: $*" >&2; exit 1; }

check_deps() {
    for cmd in docker curl gunzip; do
        command -v "$cmd" &>/dev/null || die "'$cmd' is required but not found"
    done
}


# ── Container management ───────────────────────────────────────────────────────
# The container mounts:
#   - FUSEKI_DATA_VOL → /fuseki   (persistent TDB + config)
#   - DATA_DIR        → /staging  (source .jsonld files for tdbloader)
create_container() {
    log "Starting new Fuseki container ($CONTAINER_NAME)"
    docker run -d \
        --name  "$CONTAINER_NAME" \
        -p 3030:3030 \
        -e "ADMIN_PASSWORD=$ADMIN_PASSWORD" \
        -e "FUSEKI_DATASET_1=$DATASET" \
        -e "JVM_ARGS=-Xmx8g" \
        -v "${FUSEKI_DATA_VOL}:/fuseki" \
        -v "${DATA_DIR}:/staging:ro" \
        "$FUSEKI_IMAGE"
}

wait_for_fuseki() {
    log "Waiting for Fuseki to be ready..."
    local attempts=0
    until curl -sf "${FUSEKI_HOST}/\$/ping" &>/dev/null; do
        sleep 2
        attempts=$((attempts + 1))
        [ $attempts -ge 30 ] && die "Fuseki did not respond after 60s — check: docker logs $CONTAINER_NAME"
    done
    log "Fuseki is ready"
}

start_fuseki() {
    local recreate="${1:-false}"

    local running stopped
    running=$(docker ps    --format '{{.Names}}' | grep -c "^${CONTAINER_NAME}$" || true)
    stopped=$(docker ps -a --format '{{.Names}}' | grep -c "^${CONTAINER_NAME}$" || true)

    if [ "$recreate" = "true" ] && [ "$stopped" -gt 0 ]; then
        log "Removing existing container for recreate..."
        docker rm -f "$CONTAINER_NAME"
        stopped=0; running=0
    fi

    if [ "$running" -gt 0 ]; then
        log "Fuseki already running ($CONTAINER_NAME)"
    elif [ "$stopped" -gt 0 ]; then
        log "Restarting stopped container $CONTAINER_NAME"
        docker start "$CONTAINER_NAME"
    else
        create_container
    fi

    wait_for_fuseki
}

# ── Data loading ───────────────────────────────────────────────────────────────
# Uses tdbloader inside the container to write directly to TDB, bypassing HTTP.
# This avoids the JSON-LD parser OOM that occurs with the GSP HTTP endpoint.
#
# Workflow:
#   1. Decompress .gz → .jsonld alongside source (then delete after load)
#   2. Stop Fuseki to release exclusive TDB lock
#   3. Run tdb2.tdbloader via docker exec (file visible at /staging/)
#   4. Restart Fuseki
load_file() {
    local gz_path="$1"
    local entity_type="$2"
    local graph_uri="${GRAPH_BASE}/${entity_type}"

    if [ ! -f "$gz_path" ]; then
        log "  WARNING: $gz_path not found — skipping $entity_type"
        return
    fi

    local gz_size
    gz_size=$(du -sh "$gz_path" | cut -f1)

    # Decompress alongside the source; tdbloader reads it from /staging/ inside container
    local tmp_path="${gz_path%.gz}"
    local staging_path="/staging/$(basename "$tmp_path")"
    log "Decompressing $entity_type ($gz_size) → $tmp_path"
    gunzip -kf "$gz_path"   # -k keeps .gz, -f overwrites if exists

    log "Stopping Fuseki to acquire TDB lock..."
    docker stop "$CONTAINER_NAME" >/dev/null

    log "Loading $entity_type → $graph_uri"
    docker run --rm \
        -v "${FUSEKI_DATA_VOL}:/fuseki" \
        -v "${DATA_DIR}:/staging:ro" \
        -e "JVM_ARGS=-Xmx8g" \
        "$FUSEKI_IMAGE" \
        /jena/bin/tdb2.tdbloader \
            --loc "/fuseki/databases/${DATASET}" \
            --graph "$graph_uri" \
            "$staging_path" \
        || { rm -f "$tmp_path"; die "tdbloader failed for $entity_type"; }

    rm -f "$tmp_path"

    log "Restarting Fuseki..."
    docker start "$CONTAINER_NAME"
    wait_for_fuseki

    log "  Done: $entity_type"
}

load_entity() {
    local entity="$1"
    local filepath
    filepath="$(gnd_file_for "$entity")"
    load_file "$filepath" "$entity"
}

# ── Usage ──────────────────────────────────────────────────────────────────────
usage() {
    cat <<EOF
Usage: $(basename "$0") [OPTIONS]

Start a local Fuseki container and load GND authority files into named graphs.
Each entity type is loaded into: ${GRAPH_BASE}/<type>

Options:
  --load <types>    Comma-separated entity types to load, or 'all'
                    Valid: $ALL_ENTITY_TYPES
                    Default: werk  (needed for link_gnd_works.py)
  --start-only      Start Fuseki without loading any data
  --recreate        Remove and recreate the container (needed after config changes)
  --help            Show this help

Environment:
  FUSEKI_ADMIN_PASSWORD   Container admin password (default: gnd)

Examples:
  $(basename "$0")                        # start + load werk only
  $(basename "$0") --load all             # load all entity types (~large)
  $(basename "$0") --load werk,person     # load specific types
  $(basename "$0") --start-only           # just start the container

Endpoints (after startup):
  SPARQL query:  ${FUSEKI_HOST}/${DATASET}/sparql
  Admin UI:      ${FUSEKI_HOST}/
  GSP (data):    ${FUSEKI_HOST}/${DATASET}/data

Notes:
  - Data is persisted in Docker volume '${FUSEKI_DATA_VOL}'.
  - Re-running --load replaces the named graph (tdbloader is idempotent per graph).
  - Decompressed .jsonld files are written alongside the .gz source and
    deleted after loading. Ensure ~2–10 GB free in data/gnd/.
  - Loading stops Fuseki briefly for exclusive TDB access, then restarts it.
EOF
}

# ── Main ───────────────────────────────────────────────────────────────────────
main() {
    local load_types="werk"
    local start_only=false
    local recreate=false

    while [ $# -gt 0 ]; do
        case "$1" in
            --load)       load_types="$2"; shift 2 ;;
            --start-only) start_only=true; shift ;;
            --recreate)   recreate=true; shift ;;
            --help|-h)    usage; exit 0 ;;
            *) die "Unknown argument: '$1'. Use --help for usage." ;;
        esac
    done

    check_deps
    start_fuseki "$recreate"
    $start_only && exit 0

    if [ "$load_types" = "all" ]; then
        for entity in $ALL_ENTITY_TYPES; do
            load_entity "$entity"
        done
    else
        # Split comma-separated list
        old_ifs="$IFS"
        IFS=','
        for entity in $load_types; do
            IFS="$old_ifs"
            # strip whitespace
            entity="$(echo "$entity" | tr -d ' ')"
            load_entity "$entity"
        done
        IFS="$old_ifs"
    fi

    log "All done."
    log "  SPARQL endpoint: ${FUSEKI_HOST}/${DATASET}/sparql"
    log "  Admin UI:        ${FUSEKI_HOST}/"
}

main "$@"

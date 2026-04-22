#!/usr/bin/env bash
# Purpose: Run download.py for a given sector with isolated DB and output paths.
# Usage:   ./run_download.sh [sector]   e.g. ./run_download.sh s2
# Inputs:  <sector>.sqlite (must exist in current dir)
# Outputs: Downloads staged in ./out_<sector>/, committed to <sector>.sqlite
# Deps:    download.py (same directory), httpx
sector="${1:-s1}"
DB_PATH="${sector}.sqlite" \
OUTPUT_PATH="./out_${sector}/" \
python "$(dirname "$0")/../py/download.py"

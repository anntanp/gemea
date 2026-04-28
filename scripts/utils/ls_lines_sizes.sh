#!/usr/bin/env bash
# Purpose: List files in a directory with size (KB) and line count
# Usage:   ./ls_sizes.sh [DIR]
#          DIR defaults to current directory if omitted
# Inputs:  directory path
# Outputs: tab-aligned table to stdout: FILE | SIZE_KB | LINES
# Dependencies: du, wc, column

DIR="${1:-.}"

(
  printf "FILE\tSIZE_KB\tLINES\n"
  for f in "$DIR"/*; do
    [ -f "$f" ] && printf "%s\t%s\t%s\n" \
      "$(basename "$f")" \
      "$(du -k "$f" | cut -f1)" \
      "$(wc -l < "$f")"
  done
) | column -t -s $'\t'

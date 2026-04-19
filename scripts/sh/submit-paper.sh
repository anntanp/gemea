#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# Purpose:     Compile the ISWC 2026 paper and publish the PDF to main.
#
# Usage:       ./scripts/sh/submit-paper.sh --tag <tag>
#
# Tags:
#   abstract-v1    Abstract submission (2 May 2026)
#   paper-v1       Full paper submission (7 May 2026)
#   camera-ready   Camera-ready (6 Aug 2026)
#
# Inputs:      paper/iswc-2026/00-main.tex   LaTeX root (current branch)
# Outputs:     paper/iswc2026.pdf committed to main and tagged
#
# Dependencies: latexmk, pdflatex, git >= 2.5
# Assumptions:  Run from the paper/iswc-2026 branch with a clean working tree.
# -----------------------------------------------------------------------------
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TEX_ROOT="${REPO_ROOT}/paper/iswc-2026/00-main.tex"
TEX_PDF="${REPO_ROOT}/paper/iswc-2026/00-main.pdf"
WORKTREE_PATH="/tmp/gemea-main-worktree"
ALLOWED_TAGS=("abstract-v1" "paper-v1" "camera-ready")

# --- Phase 1: parse and validate arguments ---

TAG=""
while [[ $# -gt 0 ]]; do
    case "$1" in
        --tag) TAG="$2"; shift 2 ;;
        *) echo "ERROR: unknown argument: $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$TAG" ]]; then
    echo "ERROR: --tag is required." >&2
    echo "       Allowed tags: ${ALLOWED_TAGS[*]}" >&2
    exit 1
fi

valid_tag=0
for t in "${ALLOWED_TAGS[@]}"; do
    [[ "$TAG" == "$t" ]] && valid_tag=1 && break
done

if [[ $valid_tag -eq 0 ]]; then
    echo "ERROR: unknown tag '${TAG}'." >&2
    echo "       Allowed tags: ${ALLOWED_TAGS[*]}" >&2
    exit 1
fi

# --- Phase 2: branch and working tree checks ---

current_branch="$(git -C "${REPO_ROOT}" rev-parse --abbrev-ref HEAD)"
if [[ "$current_branch" != "paper/iswc-2026" ]]; then
    echo "ERROR: must be run from the paper/iswc-2026 branch." >&2
    echo "       Current branch: ${current_branch}" >&2
    exit 1
fi

if [[ -n "$(git -C "${REPO_ROOT}" status --porcelain)" ]]; then
    echo "ERROR: working tree is dirty. Commit or stash changes before submitting." >&2
    git -C "${REPO_ROOT}" status --short >&2
    exit 1
fi

if [[ ! -f "$TEX_ROOT" ]]; then
    echo "ERROR: LaTeX root not found: ${TEX_ROOT}" >&2
    exit 1
fi

# --- Phase 3: check for existing tag ---

if git -C "${REPO_ROOT}" tag | grep -qx "$TAG"; then
    echo "ERROR: tag '${TAG}' already exists." >&2
    echo "       Delete it first if you intend to re-tag: git tag -d ${TAG}" >&2
    exit 1
fi

# --- Phase 4: compile ---

echo "==> Compiling ${TEX_ROOT} ..."
latexmk -pdf -interaction=nonstopmode -cd "$TEX_ROOT"

if [[ ! -f "$TEX_PDF" ]]; then
    echo "ERROR: PDF not produced. Check the LaTeX log for errors:" >&2
    echo "       ${TEX_ROOT%.tex}.log" >&2
    exit 1
fi

echo "==> PDF produced: ${TEX_PDF}"

# --- Phase 5: publish to main via worktree ---

cleanup_worktree() {
    git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_PATH}" 2>/dev/null || true
}
trap cleanup_worktree EXIT

if [[ -d "${WORKTREE_PATH}" ]]; then
    echo "==> Removing stale worktree at ${WORKTREE_PATH} ..."
    git -C "${REPO_ROOT}" worktree remove --force "${WORKTREE_PATH}"
fi

echo "==> Checking out main into ${WORKTREE_PATH} ..."
git -C "${REPO_ROOT}" worktree add "${WORKTREE_PATH}" main

echo "==> Copying PDF ..."
cp "${TEX_PDF}" "${WORKTREE_PATH}/paper/iswc2026.pdf"

echo "==> Committing to main ..."
(
    cd "${WORKTREE_PATH}"
    git add paper/iswc2026.pdf
    # Remove the stub README if present (tracked file — use git rm, not rm)
    if git ls-files --error-unmatch paper/README.md &>/dev/null 2>&1; then
        git rm paper/README.md
    fi
    git commit -m "chore(paper): publish ${TAG} — iswc2026.pdf"
    git tag "${TAG}"
)

echo "==> Removing worktree ..."
trap - EXIT
git -C "${REPO_ROOT}" worktree remove "${WORKTREE_PATH}"

# --- Phase 6: instructions ---

echo ""
echo "Done. PDF committed to main and tagged '${TAG}'."
echo ""
echo "Push to remote:"
echo "  git push origin main --tags"

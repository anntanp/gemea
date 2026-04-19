#!/usr/bin/env bash
# =============================================================================
# Purpose:  One-time Gitflow branch setup for the gemea repository.
#           Creates the full branch structure, cleans up main, updates
#           .gitignore, and initialises private satellite repos (.claude/,
#           transcripts/).
#
# Usage:    ./scripts/sh/git-setup.sh
#
# Inputs:   - Existing gemea git repo on `main` (git@github.com:anntanp/gemea)
#           - .venv/ present (used to generate requirements.txt)
#           - notes/rms/rm057.{tex,bib} present (migrated to meetings branch)
#
# Outputs:  Branches: develop, releases, hotfix, paper/iswc-2026, meetings
#           Files committed to main: LICENSE (CC-BY-SA-4.0), requirements.txt,
#             docker-compose.qlever-gnd.yml,
#             data/ddbedm-properties-per-sector.csv, data/before-parquet/ (partial),
#             updated .gitignore
#           Private repos initialised (with LICENSE): .claude/ (gemea-claude),
#             transcripts/ (gemea-transcripts)
#
# Dependencies: git, python3 (via .venv), pip
#
# Assumptions:
#   - Run from the gemea repo root
#   - main is the current branch and is up to date with origin
#   - None of the target branches exist yet
#   - .venv/ exists and has packages installed
#   - paper/iswc2026/ files are tracked on main but deleted locally (moved by user)
#   - notes/rms/rm057.{tex,bib} are tracked on main and still on disk;
#     script copies them to meetings/ but does NOT delete them — see manual git rm in summary
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

GITEA_BASE="https://git.xorwell.de/at"
REMOTE_CLAUDE="gemea-claude"
REMOTE_TRANSCRIPTS="gemea-transcripts"

TARGET_BRANCHES=(develop releases hotfix paper/iswc-2026 meetings)

log() { echo "[git-setup] $*"; }
die() { echo "[git-setup] ERROR: $*" >&2; exit 1; }

# --- §1: verify ----------------------------------------------------------

verify_repo() {
    [[ -d "$REPO_ROOT/.git" ]] || die "Not a git repo: $REPO_ROOT"

    local remote_url
    remote_url=$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null) \
        || die "No 'origin' remote found"

    [[ "$remote_url" == *"anntanp/gemea"* ]] \
        || die "Unexpected remote: $remote_url (expected anntanp/gemea)"

    local current_branch
    current_branch=$(git -C "$REPO_ROOT" rev-parse --abbrev-ref HEAD)
    [[ "$current_branch" == "main" ]] \
        || die "Must be on 'main' branch (currently on '$current_branch')"

    log "Repo verified: $REPO_ROOT"
}

guard_branches() {
    local existing=()
    for branch in "${TARGET_BRANCHES[@]}"; do
        if git -C "$REPO_ROOT" show-ref --quiet "refs/heads/$branch"; then
            existing+=("$branch")
        fi
    done
    if [[ ${#existing[@]} -gt 0 ]]; then
        die "Branches already exist: ${existing[*]} — aborting to avoid overwrite"
    fi
    log "Branch guard passed — none of the target branches exist"
}

# --- §2: pre-branch commits on main --------------------------------------

commit_tracked_deletions() {
    log "Committing tracked deletions (paper/iswc2026/, notes/rms/)..."

    cd "$REPO_ROOT"

    local to_stage=()
    git ls-files --deleted | grep -q "^paper/iswc2026/" && to_stage+=(paper/iswc2026/)
    git ls-files --deleted | grep -q "^notes/rms/"      && to_stage+=(notes/rms/)

    if [[ ${#to_stage[@]} -eq 0 ]]; then
        log "  No tracked deletions found — skipping"
        return
    fi

    # Stage the already-deleted files using git add -u (no rm involved)
    git add -u "${to_stage[@]}"
    local msg
    msg="chore: remove ${to_stage[*]} (migrated to branches)"
    git commit -m "$msg"
    log "  Committed deletions: ${to_stage[*]}"
}

generate_requirements() {
    log "Generating requirements.txt from .venv..."

    [[ -f "$REPO_ROOT/.venv/bin/activate" ]] \
        || die ".venv not found at $REPO_ROOT/.venv"

    cd "$REPO_ROOT"
    # shellcheck source=/dev/null
    source .venv/bin/activate
    pip freeze > requirements.txt
    deactivate

    git add requirements.txt
    git commit -m "chore: add requirements.txt from .venv"
    log "  requirements.txt committed ($(wc -l < requirements.txt | tr -d ' ') packages)"
}

write_license() {
    local target_dir="$1"
    cat > "$target_dir/LICENSE" <<'EOF'
Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)

Copyright (c) 2026 anntanp

You are free to:
  Share — copy and redistribute the material in any medium or format
  Adapt — remix, transform, and build upon the material for any purpose,
           even commercially

Under the following terms:
  Attribution  — You must give appropriate credit, provide a link to the
                 license, and indicate if changes were made.
  ShareAlike   — If you remix, transform, or build upon the material, you
                 must distribute your contributions under the same license
                 as the original.

No additional restrictions — You may not apply legal terms or technological
measures that legally restrict others from doing anything the license permits.

Full license text: https://creativecommons.org/licenses/by-sa/4.0/legalcode
EOF
}

commit_new_tracked_files() {
    log "Committing LICENSE, docker-compose.qlever-gnd.yml, ddb properties CSV..."

    cd "$REPO_ROOT"

    write_license "$REPO_ROOT"

    local to_add=(LICENSE)
    [[ -f docker-compose.qlever-gnd.yml ]] && to_add+=(docker-compose.qlever-gnd.yml)
    [[ -f data/ddbedm-properties-per-sector.csv ]] \
        && to_add+=(data/ddbedm-properties-per-sector.csv)

    git add "${to_add[@]}"
    git commit -m "chore: add LICENSE (CC-BY-SA-4.0), docker-compose.qlever-gnd, ddb properties CSV"
    log "  Committed: ${to_add[*]}"
}

commit_before_parquet() {
    log "Committing data/before-parquet/ (excluding large files)..."

    [[ -d "$REPO_ROOT/data/before-parquet" ]] \
        || { log "  data/before-parquet/ not found — skipping"; return; }

    cd "$REPO_ROOT"

    cat > data/before-parquet/.gitignore <<'EOF'
processed/sr11_dctype_filtered.csv
processed/ner/sr11_dctype_filtered.csv
processed/ner/sr01_isbd_field_ratings.csv
EOF

    git add data/before-parquet/
    git commit -m "chore: add data/before-parquet (images, annotation, small NER CSVs; large files gitignored)"
    log "  data/before-parquet/ committed"
}

# --- §3: update .gitignore -----------------------------------------------

update_gitignore() {
    log "Updating .gitignore..."

    cd "$REPO_ROOT"

    # Fix data/gnd entry so .dvc pointer files are not blocked by the directory rule
    if grep -qx "data/gnd" .gitignore; then
        # BSD sed (macOS) requires '' after -i
        sed -i '' 's|^data/gnd$|data/gnd/**\
!data/gnd/*.dvc|' .gitignore
        log "  Fixed data/gnd → data/gnd/** + !data/gnd/*.dvc"
    fi

    # Entries to append (idempotent — each skipped if already present)
    local -a new_entries=(
        ""
        "# Python env"
        ".venv/"
        ""
        "# Generated outputs"
        "out/"
        "output/"
        ""
        "# Private satellite repos"
        "transcripts/"
        ""
        "# Large data and indexes"
        "qlever-gnd-index/"
        "data/processed/"
        "data/raw/"
        "data/annotation/"
        "data/sqlite/"
        "data/out/"
        "data/*.pkl"
        ""
        "# Meeting slides template (local only)"
        "notes/rms/beamer-bodilla-template/"
    )

    for entry in "${new_entries[@]}"; do
        if [[ -z "$entry" || "$entry" == \#* ]]; then
            echo "$entry" >> .gitignore
        elif ! grep -qxF "$entry" .gitignore; then
            echo "$entry" >> .gitignore
        fi
    done

    git add .gitignore
    git commit -m "chore: update .gitignore for venv, large data, private dirs, DVC fix"
    log "  .gitignore updated and committed"
}

# --- §4–5: create Gitflow branches ---------------------------------------

create_gitflow_branches() {
    log "Creating Gitflow branches from main..."

    cd "$REPO_ROOT"

    git checkout -b develop  main  && log "  develop  ← main"
    git checkout -b releases main  && log "  releases ← main"
    git checkout -b hotfix   main  && log "  hotfix   ← main"

    git checkout main
}

create_paper_branch() {
    log "Creating paper/iswc-2026 from develop..."

    cd "$REPO_ROOT"
    git checkout -b paper/iswc-2026 develop
    git checkout develop
    log "  paper/iswc-2026 ← develop"
}

# --- §6: meetings orphan branch ------------------------------------------

create_meetings_branch() {
    log "Creating meetings orphan branch..."

    cd "$REPO_ROOT"

    git checkout --orphan meetings
    # Empty the index without touching the working tree
    git read-tree --empty

    mkdir -p meetings/rm057

    local src_tex="$REPO_ROOT/notes/rms/rm057.tex"
    local src_bib="$REPO_ROOT/notes/rms/rm057.bib"

    [[ -f "$src_tex" ]] && cp "$src_tex" meetings/rm057/slides.tex \
        && log "  Copied rm057.tex → meetings/rm057/slides.tex"
    [[ -f "$src_bib" ]] && cp "$src_bib" meetings/rm057/slides.bib \
        && log "  Copied rm057.bib → meetings/rm057/slides.bib"

    cat > meetings/README.md <<'EOF'
# GeMeA — Research Meetings

Beamer slides, supporting data, and figures from research meetings.
This branch is a permanent archive; it never merges into main.

## 1. Structure

One subfolder per meeting, numbered sequentially:

```
rm057/
├── slides.tex
├── slides.bib
├── slides.pdf      (add after compile)
├── data/           (supporting CSVs)
└── images/         (figures)
```

## 2. Naming

`rmNNN/` where NNN is the sequential meeting number (zero-padded to 3 digits).
EOF

    git add meetings/
    git commit -m "init: meetings branch with rm057 slides"
    log "  meetings branch initialised"

    # Force checkout needed: git read-tree --empty leaves working tree files
    # untracked from meetings' perspective; -f overwrites them safely since
    # they are identical to what develop has
    git checkout -f develop
}

# --- §7: private satellite repos -----------------------------------------

init_satellite_repo() {
    local dir="$1"
    local name="$2"
    local remote_url="$3"

    log "Initialising private repo: $dir → $remote_url"

    [[ -d "$REPO_ROOT/$dir" ]] || { log "  $dir not found — skipping"; return; }

    cd "$REPO_ROOT/$dir"

    if [[ -d .git ]]; then
        log "  $dir already a git repo — skipping init"
        cd "$REPO_ROOT"
        return
    fi

    write_license "$REPO_ROOT/$dir"

    git init -b main
    git add .
    git commit -m "init: $name private repo (CC-BY-SA-4.0)"
    git remote add origin "$remote_url"
    log "  Initialised, committed, remote set"

    cd "$REPO_ROOT"
}

init_satellite_repos() {
    init_satellite_repo ".claude"     "$REMOTE_CLAUDE"       "$GITEA_BASE/$REMOTE_CLAUDE"
    init_satellite_repo "transcripts" "$REMOTE_TRANSCRIPTS"  "$GITEA_BASE/$REMOTE_TRANSCRIPTS"
}

# --- §8: summary ---------------------------------------------------------

print_summary() {
    cd "$REPO_ROOT"

    echo ""
    echo "============================================================"
    echo "  git-setup complete — $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================================"
    echo ""
    echo "Branches:"
    git branch
    echo ""
    echo "------------------------------------------------------------"
    echo "  MANUAL git rm REQUIRED"
    echo "------------------------------------------------------------"
    echo "  These files are still on disk and tracked on develop."
    echo "  Verify the meetings branch first, then run:"
    echo ""
    echo "  # Verify:"
    echo "  git show meetings:meetings/rm057/slides.tex | head -5"
    echo "  git show meetings:meetings/rm057/slides.bib | head -5"
    echo ""
    echo "  # Remove originals from develop:"
    echo "  git rm notes/rms/rm057.tex notes/rms/rm057.bib"
    echo "  git commit -m \"chore: remove notes/rms/rm057 (migrated to meetings branch)\""
    echo ""
    echo "  # If beamer template is tracked (check: git ls-files notes/rms/):"
    echo "  git rm -r notes/rms/beamer-bodilla-template/"
    echo "  git commit -m \"chore: remove beamer template (gitignored)\""
    echo ""
    echo "------------------------------------------------------------"
    echo "  PRIVATE REPOS — push manually after creating on Gitea"
    echo "------------------------------------------------------------"
    echo "  1. Create empty repos (no README, no .gitignore):"
    echo "       $GITEA_BASE/$REMOTE_CLAUDE"
    echo "       $GITEA_BASE/$REMOTE_TRANSCRIPTS"
    echo "  2. Push:"
    echo "       cd .claude     && git push -u origin main && cd .."
    echo "       cd transcripts && git push -u origin main && cd .."
    echo ""
    echo "------------------------------------------------------------"
    echo "  PUSH GEMEA BRANCHES TO GITHUB"
    echo "------------------------------------------------------------"
    echo "  git push -u origin develop releases hotfix paper/iswc-2026"
    echo "  git checkout meetings && git push -u origin meetings && git checkout develop"
    echo ""
    echo "Current branch: $(git rev-parse --abbrev-ref HEAD)"
    echo "============================================================"
}

# --- main ----------------------------------------------------------------

main() {
    log "Starting — $(date '+%Y-%m-%d %H:%M:%S') on $(hostname)"
    log "Repo root: $REPO_ROOT"

    cd "$REPO_ROOT"

    verify_repo
    guard_branches

    commit_tracked_deletions
    generate_requirements
    commit_new_tracked_files
    commit_before_parquet

    update_gitignore

    create_gitflow_branches
    create_paper_branch
    create_meetings_branch

    init_satellite_repos

    git checkout develop

    print_summary
}

main "$@"

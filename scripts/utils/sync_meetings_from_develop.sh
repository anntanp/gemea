#!/usr/bin/env bash
# Purpose: Sync scripts/, paper/, and notes/ from develop into the meetings branch,
#          with pre-flight snapshot, rollback script, and a GitHub release tag.
# Usage:   ./sync_meetings_from_develop.sh
# Inputs:  interactive prompts (tag name, stash/commit choice)
# Outputs: snapshot commit on meetings, rollback script in /tmp, merged changes staged
# Dependencies: git
# Assumptions: run from anywhere inside the gemea repo working tree

set -euo pipefail

# ── helpers ────────────────────────────────────────────────────────────────────

die()  { echo "ERROR: $*" >&2; exit 1; }
info() { echo "==> $*"; }
ask()  { read -rp "$1 " REPLY; echo "$REPLY"; }

# ── 0. resolve repo root ───────────────────────────────────────────────────────

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) \
  || die "Not inside a git repository."
cd "$REPO_ROOT"

# ── 1. prompt for release tag ──────────────────────────────────────────────────

while true; do
  TAG=$(ask "Enter the release tag (e.g. RM042):")
  [[ "$TAG" =~ ^RM[0-9]+$ ]] && break
  echo "  Tag must match RM<digits> (e.g. RM042). Try again."
done

# ── 2. enforce meetings branch ────────────────────────────────────────────────

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "meetings" ]]; then
  die "Must be on the 'meetings' branch (currently on '$CURRENT_BRANCH')."
fi

# ── 3. handle uncommitted changes ─────────────────────────────────────────────

DIRTY=$(git status --porcelain)
if [[ -n "$DIRTY" ]]; then
  echo
  echo "Uncommitted changes detected:"
  git status --short
  echo
  echo "What would you like to do?"
  echo "  s) Stash changes and continue"
  echo "  p) Commit and push changes now, then continue"
  echo "  q) Quit — handle manually"

  CHOICE=$(ask "Choose [s/p/q]:")
  case "$CHOICE" in
    s|S)
      STASH_MSG="sync_meetings_from_develop: pre-sync stash ($TAG)"
      git stash push -u -m "$STASH_MSG"
      info "Changes stashed: '$STASH_MSG'"
      STASHED=true
      ;;
    p|P)
      COMMIT_MSG=$(ask "Commit message:")
      git add -A
      git commit -m "$COMMIT_MSG"
      git push origin meetings
      info "Changes committed and pushed."
      STASHED=false
      ;;
    q|Q)
      info "Aborted. No changes made."
      exit 0
      ;;
    *)
      die "Invalid choice '$CHOICE'."
      ;;
  esac
else
  STASHED=false
fi

# ── 4. snapshot: tag current HEAD before any changes ─────────────────────────

SNAPSHOT_TAG="${TAG}-meetings-pre-sync"
PRE_SYNC_SHA=$(git rev-parse HEAD)

git tag "$SNAPSHOT_TAG" HEAD
info "Snapshot tag created: $SNAPSHOT_TAG (${PRE_SYNC_SHA:0:8})"

# ── 4a. write rollback script ─────────────────────────────────────────────────

ROLLBACK_SCRIPT="$TMPDIR/rollback_${TAG}.sh"
cat > "$ROLLBACK_SCRIPT" <<ROLLBACK
#!/usr/bin/env bash
# Rollback: undo sync_meetings_from_develop.sh ($TAG)
# Run from anywhere inside the gemea repo.
set -euo pipefail
REPO_ROOT=\$(git rev-parse --show-toplevel)
cd "\$REPO_ROOT"
git checkout meetings
git reset --hard $PRE_SYNC_SHA
echo "Rolled back meetings to $PRE_SYNC_SHA ($SNAPSHOT_TAG)"
ROLLBACK
chmod +x "$ROLLBACK_SCRIPT"
info "Rollback script written to: $ROLLBACK_SCRIPT"

# ── 5. merge scripts/, paper/, notes/ from develop ───────────────────────────

MERGE_PATHS=(scripts/ paper/ notes/)

info "Checking out paths from develop: ${MERGE_PATHS[*]}"
git checkout develop -- "${MERGE_PATHS[@]}"

# show what changed
CHANGED=$(git diff --cached --name-only)
if [[ -z "$CHANGED" ]]; then
  info "No differences found between develop and meetings for the target paths."
else
  echo
  echo "Files staged from develop:"
  git diff --cached --name-only | sed 's/^/  /'
  echo
  COMMIT_MSG="sync: merge scripts/, paper/, notes/ from develop [$TAG]"
  git commit -m "$COMMIT_MSG"
  info "Committed: $COMMIT_MSG"

  PUSH_NOW=$(ask "Push meetings to origin now? [y/n]:")
  if [[ "$PUSH_NOW" =~ ^[Yy]$ ]]; then
    git push origin meetings
    info "Pushed."
  else
    info "Not pushed. Run: git push origin meetings"
  fi
fi

# ── 6. remind about stash ─────────────────────────────────────────────────────

if [[ "$STASHED" == true ]]; then
  echo
  echo "Your pre-sync stash is still saved."
  echo "To restore it: git stash pop"
fi

echo
info "Done. Tag '$SNAPSHOT_TAG' marks the pre-sync state."
info "Rollback if needed: bash $ROLLBACK_SCRIPT"

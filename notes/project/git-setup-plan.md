# GeMeA — Git Workspace Setup Plan

**Date**: 2026-04-19
**Script**: `scripts/sh/git-setup.sh`
**Goal**: Reorganize the gemea repo into the Gitflow-based branch structure defined in `notes/project/git-branching-strategy.md`.

---

## 0. Checklist

- [ ] §1 Verify repo state
- [ ] §2 Pre-branch commits on `main`
  - [ ] §2.1 Commit tracked deletions (`paper/iswc2026/`, `notes/rms/`)
  - [ ] §2.2 Generate and commit `requirements.txt`
  - [ ] §2.3 Commit new tracked files (`docker-compose.qlever-gnd.yml`, `data/ddbedm-properties-per-sector.csv`)
  - [ ] §2.4 Commit `data/before-parquet/` (with internal `.gitignore` for large files)
- [ ] §3 Update and commit `.gitignore`
- [ ] §4 Create Gitflow branches from `main`
- [ ] §5 Create `paper/iswc-2026` from `develop`
- [ ] §6 Create `meetings` orphan branch
- [ ] §7 Init private satellite repos (`.claude/`, `transcripts/`)
- [ ] §8 Switch to `develop`; print summary + manual git rm list

---

## 1. Verify

- Abort if not in gemea repo root (check for `.git/` + `git remote get-url origin` matching `anntanp/gemea`)
- Abort if any target branch already exists: `develop`, `releases`, `hotfix`, `paper/iswc-2026`, `meetings`

---

## 2. Pre-branch commits on `main`

All commits here land on `main` so every downstream branch inherits a clean state.

### 2.1 Tracked deletions

```bash
git rm -r paper/iswc2026/     # 18 files — moved to paper/iswc-2026 branch by user
git rm -r notes/rms/          # rm057.tex, rm057.bib — moved to meetings branch
git commit -m "chore: remove paper/iswc2026 and notes/rms (migrated to branches)"
```

### 2.2 requirements.txt

```bash
source .venv/bin/activate
pip freeze > requirements.txt
deactivate
git add requirements.txt
git commit -m "chore: add requirements.txt from .venv"
```

### 2.3 New tracked files

Create `LICENSE` (CC-BY-SA-4.0) and commit alongside project config files:

```bash
git add LICENSE docker-compose.qlever-gnd.yml data/ddbedm-properties-per-sector.csv
git commit -m "chore: add LICENSE (CC-BY-SA-4.0), docker-compose.qlever-gnd, ddb properties CSV"
```

### 2.4 data/before-parquet/

Create `data/before-parquet/.gitignore` to exclude the three large files (>100 MB each):

```
processed/sr11_dctype_filtered.csv
processed/ner/sr11_dctype_filtered.csv
processed/ner/sr01_isbd_field_ratings.csv
```

Then:

```bash
git add data/before-parquet/
git commit -m "chore: add data/before-parquet (images, annotation, small NER CSVs; large files gitignored)"
```

---

## 3. Update .gitignore

Append to existing `.gitignore` (keep `.claude` entry as-is):

```
# Python env
.venv/

# Generated outputs
out/
output/

# Private satellite repos
transcripts/

# Large data and indexes
qlever-gnd-index/
data/processed/
data/raw/
data/annotation/
data/sqlite/
data/out/
data/*.pkl

# Meeting slides template (stays local, not migrated)
notes/rms/beamer-bodilla-template/
```

Special case — `data/gnd/` entry must change to allow `.dvc` pointer files:

```
# old: data/gnd/
# new:
data/gnd/**
!data/gnd/*.dvc
```

Commit:

```bash
git add .gitignore
git commit -m "chore: update .gitignore for venv, large data, private dirs"
```

---

## 4. Create Gitflow branches from `main`

```bash
git checkout -b develop main
git checkout -b releases main
git checkout -b hotfix main
git checkout main
```

Branch map:

```
main
├── develop      ← active development
├── releases     ← Zenodo snapshots, versioned KG dumps
└── hotfix       ← post-submission corrections
```

---

## 5. Create paper/iswc-2026 from develop

```bash
git checkout -b paper/iswc-2026 develop
git checkout develop
```

Note: `paper/latex/` LaTeX source was already moved to this branch by the user. No file operations needed here.

---

## 6. Create meetings orphan branch

```bash
git checkout --orphan meetings
git read-tree --empty   # empty the index; working tree untouched
mkdir -p meetings/rm057
cp notes/rms/rm057.tex meetings/rm057/slides.tex
cp notes/rms/rm057.bib meetings/rm057/slides.bib
```

Create `meetings/README.md`:

```markdown
# GeMeA — Research Meetings

Beamer slides, supporting data, and figures from research meetings.
This branch is a permanent archive; it never merges into main.

## 1. Structure

One subfolder per meeting, numbered sequentially:

```
rm057/
├── slides.tex
├── slides.pdf      (add after compile)
├── data/           (supporting CSVs)
└── images/         (figures)
```

## 2. Naming

`rmNNN/` where NNN is the sequential meeting number (zero-padded to 3 digits).
```

Commit:

```bash
git add meetings/
git commit -m "init: meetings branch with rm057 slides"
```

Return to develop:

```bash
git checkout develop
```

---

## 7. Init private satellite repos

### 7.1 .claude/

```bash
cd .claude/
git init
git add .
git commit -m "init: gemea-claude private repo"
git remote add origin https://git.xorwell.de/at/gemea-claude
cd ..
```

### 7.2 transcripts/

```bash
cd transcripts/
git init
git add .
git commit -m "init: gemea-transcripts private repo"
git remote add origin https://git.xorwell.de/at/gemea-transcripts
cd ..
```

Both repos are already ignored by gemea's `.gitignore` (`.claude` listed; `transcripts/` added in §3).

`git remote add origin` sets the URL locally — it does **not** contact Gitea. The remote repos do not need to exist yet at this point.

Script prints the required manual steps (see §8).

---

## 8. Final state and summary

Script leaves user on `develop` and prints the following.

### 8.1 Manual git rm required

These files are still on disk and tracked on `develop`. Script cannot delete them — do this manually after verifying the meetings branch is correct:

```bash
# Verify first:
git show meetings:meetings/rm057/slides.tex | head -5
git show meetings:meetings/rm057/slides.bib | head -5

# Then remove from develop:
git rm notes/rms/rm057.tex notes/rms/rm057.bib
git commit -m "chore: remove notes/rms/rm057 (migrated to meetings branch)"

# If notes/rms/beamer-bodilla-template/ is tracked (check with git ls-files notes/rms/):
git rm -r notes/rms/beamer-bodilla-template/
git commit -m "chore: remove beamer template (gitignored)"
```

### 8.2 Push instructions

```
Private repos initialized locally (remotes set, NOT pushed):
  .claude/     → https://git.xorwell.de/at/gemea-claude
  transcripts/ → https://git.xorwell.de/at/gemea-transcripts

ACTION REQUIRED before pushing private repos:
  1. Create empty repos on Gitea (no README, no .gitignore):
       https://git.xorwell.de/at/gemea-claude
       https://git.xorwell.de/at/gemea-transcripts
  2. Push:
       cd .claude     && git push -u origin main && cd ..
       cd transcripts && git push -u origin main && cd ..

Push gemea branches to GitHub:
  git push -u origin develop releases hotfix paper/iswc-2026
  git checkout meetings && git push -u origin meetings && git checkout develop
```

---

## 9. Verification

```bash
git branch -a
# expect: develop, hotfix, meetings, paper/iswc-2026, releases (+ main + remotes after push)

git log --oneline meetings
# expect: one commit — "init: meetings branch with rm057 slides"

git log --oneline main | head -5
# expect: gitignore + data/before-parquet + docker-compose + requirements.txt + deletion commits

cat requirements.txt | head -5
# expect: pinned package list from .venv

ls meetings/rm057/
# expect: slides.tex  slides.bib
```

---

## 10. Full run sequence

Run in order. Steps marked **[manual]** are not in the script.

```bash
# 1. Run the setup script
cd ~/Documents/claude/gemea
./scripts/sh/git-setup.sh

# 2. [manual] Verify meetings branch before deleting originals
git show meetings:meetings/rm057/slides.tex | head -5
git show meetings:meetings/rm057/slides.bib | head -5

# 3. [manual] Remove notes/rms originals from develop
git rm notes/rms/rm057.tex notes/rms/rm057.bib
git commit -m "chore: remove notes/rms/rm057 (migrated to meetings branch)"

# 4. [manual] Remove beamer template if tracked
git ls-files notes/rms/                          # check what's still tracked
# if beamer-bodilla-template/ appears:
git rm -r notes/rms/beamer-bodilla-template/
git commit -m "chore: remove beamer template (gitignored)"

# 5. [manual] Create repos on Gitea (browser):
#   https://git.xorwell.de/at/gemea-claude
#   https://git.xorwell.de/at/gemea-transcripts
#   Note: if Gitea auto-generates a README, use --force on first push (step 6)

# 6. [manual] Push private satellite repos
#   If Gitea repo was created empty:
cd .claude     && git push -u origin main && cd ..
cd transcripts && git push -u origin main && cd ..
#   If Gitea repo has auto-generated content (use --force):
cd .claude     && git push -u origin main --force && cd ..
cd transcripts && git push -u origin main --force && cd ..

# 7. [manual] Push gemea branches to GitHub
git push -u origin develop releases hotfix paper/iswc-2026
git checkout meetings && git push -u origin meetings && git checkout develop

# 8. [manual] Verify remote state
git branch -a
git log --oneline main | head -8
```

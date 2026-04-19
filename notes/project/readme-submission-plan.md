# README and Submission Script Plan

**Date**: 2026-04-19
**Status**: In progress

---

## 1. Context

`README.md` on `main` has been rewritten to present GeMeA as a Knowledge Graph Testbed (not "browser"). This plan covers the remaining work: fixing the committed README, creating `docs/` stubs, and writing the paper submission script.

Prior tasks closed:
- Resource paper framing → `notes/project/roadmap-revised.md`
- Gitflow branch setup → `notes/project/git-setup-plan.md` + `scripts/sh/git-setup.sh`

---

## 2. README fixes needed on main

The README committed to `main` needs two fixes:

### 2.1 Repository layout (§5)

Change `scripts/sh/` → flat `scripts/` (both .sh and sample .py). Add `docs/` entry.

```
gemea/
├── scripts/        Setup, deployment .sh + sample usage .py scripts
├── ingest/         QLever load modules (for reproducibility)
├── data/           Raw inputs tracked via DVC (.dvc pointer files)
├── docker/         Docker Compose configs (EDM + GND stacks)
├── docs/           Guides: SPARQL examples, self-hosting setup, MCP access
├── paper/          Submitted PDF (iswc2026.pdf) — stub README until submission
└── resource/       VoID descriptor, w3id metadata
```

Note: `notes/`, `experiments/`, internal `scripts/py/` ETL pipeline, `api/`, `frontend/` live on `develop` only.

### 2.2 Branches section

The Branches section links to `notes/project/git-branching-strategy.md`. This link will break when `notes/` is removed from `main`. Replace with inline branch table.

---

## 3. docs/ stubs on main

Create three stub files under `docs/`:

| File | Content |
|------|---------|
| `docs/sparql-queries.md` | Example SPARQL queries over the EDM KG |
| `docs/setup.md` | Self-hosting with Docker Compose |
| `docs/mcp-access.md` | Using the MCP interface from AI agents |

---

## 4. paper/ on main

### 4.1 Before submission — stub (already committed)

`paper/README.md` is on `main`:
```markdown
# GeMeA — ISWC 2026 Paper
**Track**: ISWC 2026 Resource Track
**Title**: GeMeA: Knowledge Graph Testbed for 23M+ German Digital Library Objects
**LaTeX source**: `paper/iswc-2026` branch
The submitted PDF will appear here as `iswc2026.pdf` at the `paper-v1` tag (7 May 2026).
```

### 4.2 At submission — scripts/sh/submit-paper.sh (on paper/iswc-2026)

```
Inputs:  paper/iswc-2026/00-main.tex  (LaTeX root)
Outputs: paper/iswc2026.pdf committed to main; tag applied; user stays on paper/iswc-2026
```

**Allowed tags**: `abstract-v1` | `paper-v1` | `camera-ready`

**Steps**:
1. Parse `--tag <tag>`; validate; abort if missing or invalid
2. Verify current branch is `paper/iswc-2026`; abort if not
3. Verify working tree is clean; abort if dirty
4. `latexmk -pdf -interaction=nonstopmode -cd paper/iswc-2026/00-main.tex`
5. Verify PDF was produced; abort with clear message if not
6. `git worktree add /tmp/gemea-main-worktree main`
7. Copy PDF → `/tmp/gemea-main-worktree/paper/iswc2026.pdf`
8. In worktree: stage PDF, `git rm paper/README.md` (stub), commit, apply tag
9. `git worktree remove /tmp/gemea-main-worktree`
10. Print push instructions

**Usage**:
```bash
./scripts/sh/submit-paper.sh --tag abstract-v1   # 2 May 2026
./scripts/sh/submit-paper.sh --tag paper-v1      # 7 May 2026
./scripts/sh/submit-paper.sh --tag camera-ready  # 6 Aug 2026
```

---

## 5. Main branch cleanup — manual git rm

Record rollback SHA before each step:
```bash
git rev-parse HEAD   # save this
```

```bash
# Verify notes/ is intact on develop first:
git show develop:notes/project/roadmap-revised.md | head -3

# Then on main:
git rm -r notes/
git commit -m "chore: move notes/ to develop only (not public-facing)"

git rm -r experiments/
git rm -r scripts/py/
git rm -r api/ frontend/
git commit -m "chore: strip internal dirs from main (develop-only)"

# Rollback if needed:
git reset --hard <SHA>
```

---

## 6. Checklist

- [ ] Fix README §5 layout (scripts/, docs/)
- [ ] Fix README Branches section (remove notes/ link, inline table)
- [ ] Create docs/sparql-queries.md stub
- [ ] Create docs/setup.md stub
- [ ] Create docs/mcp-access.md stub
- [ ] Write scripts/sh/submit-paper.sh on paper/iswc-2026
- [ ] Manual: git rm notes/ from main (after verifying develop)
- [ ] Manual: git rm experiments/ scripts/py/ api/ frontend/ from main

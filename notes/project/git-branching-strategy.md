# GeMeA — Git Branching Strategy

**Date**: 2026-04-19
**Based on**: Gitflow (Vincent Driessen, 2010) + research-specific additions

---

## Branch map

| Branch | Gitflow equivalent | Purpose |
|--------|-------------------|---------|
| `main` | `main` | Paper submissions. Tagged at each ISWC deadline: `abstract-v1`, `paper-v1`, `camera-ready`. |
| `develop` | `develop` | Active development — code, drafts, experiments. Merges into `main` at submission freeze. |
| `paper/iswc-2026` | `feature/*` | LaTeX source only. Long-lived feature branch; merged to `main` + tagged on submission. |
| `releases` | `release/*` | Data and software releases — Zenodo snapshots, VoID descriptors, versioned KG dumps. Tagged `v1.0`, `v1.1`, etc. |
| `hotfix` | `hotfix/*` | Post-submission corrections to submitted code or data only. |
| `meetings` | *(no equivalent)* | Meeting notes, slides, agendas, decisions. Orphan branch. Never merges. |

---

## Key distinctions

- `main` is the **academic record** — what was submitted when.
- `releases` is the **resource record** — what version of the KG/code is publicly available. Overlaps with `main` at camera-ready, then diverges as the KG is updated post-publication.
- `meetings` is an orphan branch (no shared history with `main`) — keeps documentary content out of the commit graph.
- `paper/iswc-2026` isolates LaTeX commits from pipeline/infrastructure commits on `develop`.

---

## ISWC 2026 tag schedule

| Tag | Branch | Date |
|-----|--------|------|
| `abstract-v1` | `main` | 2 May 2026 |
| `paper-v1` | `main` | 7 May 2026 |
| `camera-ready` | `main` | 6 Aug 2026 |

---

## References

- Driessen, V. (2010). *A successful Git branching model*. https://nvie.com/posts/a-successful-git-branching-model/
- Tooling: `git flow` CLI (`brew install git-flow`)

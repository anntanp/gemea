# QLever Index Build — GeMeA

**Context**: Two-stage build matching the deployment timeline in `setup-vps-plan.md` §2.

---

## 1. Index build time estimates

**Stage A — pilot corpus (goethe-faust, ~1–2 May)**

| Step | Estimated time |
|---|---|
| Upload goethe-faust NTs to VPS (~9.5 GB) | ~5 min |
| QLever pilot index build (~47M triples) | ~10–30 min |
| **Pilot endpoint live** | **< 1 hr** |

**Stage B — full corpus (~8–10 May)**

| Step | Estimated time |
|---|---|
| Upload full NTs to VPS (1 Gbps, ~2.5 TB) | ~6–8 hrs |
| QLever full-corpus index build (EDM + mocho, ~14B triples) | ~12–20 hrs |
| **Full endpoint live** | **~18–28 hrs after upload starts** |

**Transform pipeline on VPS** (alternative if pre-built NTs are unavailable):
Single-threaded Python: ~3–6 days for 27M records.
Parallelized per sector (7 sectors): ~12–24 hrs with sector-level multiprocessing.

> From Etienne:
> ```2026-04-21 08:36:56.065 - INFO: QLever index builder b7623fc, compiled on Sun Apr 12 04:30:08 UTC 2026 using git hash b7623f
2026-04-21 09:02:07.211 - INFO: Text index build completed```

## Decisions

    - D1. may 5, 2026; feature merge; The number of occurrences of the word in the literal is stored in the graph. ; https://github.com/ad-freiburg/qlever/pull/2579

    - D2. date; decision; short-description; url
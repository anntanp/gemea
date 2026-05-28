"""
Purpose:    Revise the paper's per-sector triple table to account for the
            edm:currentLocation and edm:Agent label-stub fixes added 2026-05-07/08,
            and estimate .nq disc-space requirements.
Usage:      python scripts/estimate_table_revised.py
Inputs:     Hard-coded before-fix table from 30-resource.tex; goethe-faust
            before/after stats from output/transform/.
Outputs:    data/processed/table_scale_revised.csv
Deps:       stdlib only
Assumes:    Run from gemea/ directory.
"""

from __future__ import annotations

import csv
from pathlib import Path

# ── Goethe-faust proxy: change ratios from emitter audit + agent label fixes ──
# Before: POC run 2026-05-06 (transform_stats from 20260506_154602)
# After:  post-all-fixes run 2026-05-08 (20260507_232804)
GF_BEFORE = dict(total=14_713_376, ddbedm=8_957_262, mocho=1_898_754, prov=3_857_360)
GF_AFTER  = dict(total=14_782_653, ddbedm=8_957_734, mocho=1_968_805, prov=3_856_114)

DELTA_RATIO = {
    "ddbedm": (GF_AFTER["ddbedm"] - GF_BEFORE["ddbedm"]) / GF_BEFORE["ddbedm"],
    "mocho":  (GF_AFTER["mocho"]  - GF_BEFORE["mocho"])  / GF_BEFORE["mocho"],
    "prov":   (GF_AFTER["prov"]   - GF_BEFORE["prov"])   / GF_BEFORE["prov"],
}

# ── Bytes-per-triple from actual .nq file (goethe-faust post-fix run) ──────────
NQ_BYTES   = 3_146_053_776   # bytes, goethe-faust.nq
NQ_TRIPLES = 14_782_653
BYTES_PER_TRIPLE = NQ_BYTES / NQ_TRIPLES   # 212.8 B/triple

# ── Before-fix table (from 30-resource.tex, generated pre-2026-05-07) ─────────
SECTORS = [
    ("Library",           18_338_116, 1_040_390_087, 356_952_292, 532_835_841),
    ("Archive",            3_456_119,   259_483_277,  61_795_115, 146_160_731),
    ("Museum",             2_011_841,   123_795_378,  48_164_578,  58_524_171),
    ("Media Library",      1_709_846,   145_905_243,  58_871_240,  53_400_440),
    ("Research",           1_165_891,    75_842_237,  24_633_128,  37_642_836),
    ("Monument Preserv.",     79_393,     4_852_432,   1_555_297,   2_613_022),
    ("Others",                85_408,     5_487_618,   1_958_508,   2_550_312),
]

rows = []
for sector, objects, old_ddbedm, old_mocho, old_prov in SECTORS:
    new_ddbedm = round(old_ddbedm * (1 + DELTA_RATIO["ddbedm"]))
    new_mocho  = round(old_mocho  * (1 + DELTA_RATIO["mocho"]))
    new_prov   = round(old_prov   * (1 + DELTA_RATIO["prov"]))
    new_total  = new_ddbedm + new_mocho + new_prov
    delta      = new_total - (old_ddbedm + old_mocho + old_prov)
    nq_gb      = new_total * BYTES_PER_TRIPLE / 1e9
    rows.append((sector, objects, new_ddbedm, new_mocho, new_prov, new_total, delta, nq_gb))

# Totals row
tot_obj     = sum(r[1] for r in rows)
tot_ddbedm  = sum(r[2] for r in rows)
tot_mocho   = sum(r[3] for r in rows)
tot_prov    = sum(r[4] for r in rows)
tot_total   = sum(r[5] for r in rows)
tot_delta   = sum(r[6] for r in rows)
tot_nq_gb   = sum(r[7] for r in rows)

rows.append(("TOTAL", tot_obj, tot_ddbedm, tot_mocho, tot_prov, tot_total, tot_delta, tot_nq_gb))

# ── Write CSV ────────────────────────────────────────────────────────────────
out = Path("data/processed/table_scale_revised.csv")
out.parent.mkdir(parents=True, exist_ok=True)
with open(out, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["sector", "objects", "ddbedm_triples", "mocho_triples",
                "prov_triples", "total_triples", "delta_vs_before", "nq_size_gb"])
    for r in rows:
        w.writerow([r[0], r[1], r[2], r[3], r[4], r[5], r[6], f"{r[7]:.1f}"])

# ── Print summary ─────────────────────────────────────────────────────────────
print(f"Proxy ratios from goethe-faust (before→after):")
for g, v in DELTA_RATIO.items():
    print(f"  {g:8s}: {v:+.4%}")
print(f"Bytes/triple (post-fix .nq): {BYTES_PER_TRIPLE:.1f} B")
print()
print(f"{'Sector':<22} {'Objects':>12} {'DDB-EDM':>16} {'MOCHO':>16} {'PROV':>16} {'Total':>18} {'Δ':>12} {'NQ GB':>8}")
print("-" * 122)
for r in rows:
    print(f"{r[0]:<22} {r[1]:>12,} {r[2]:>16,} {r[3]:>16,} {r[4]:>16,} {r[5]:>18,} {r[6]:>+12,} {r[7]:>8.1f}")
print()
print(f"Saved → {out}")
print(f"\nDisc-space summary (N-Quads only):")
print(f"  Total triples:  {tot_total:,}")
print(f"  .nq file:       {tot_nq_gb/1024:.2f} TB")
print(f"  QLever index:   {tot_nq_gb/1024*0.4:.2f} TB  (rough: ~40% of .nq)")
print(f"  Pipeline total: {tot_nq_gb/1024*1.4:.2f} TB  (.json input + .nq + QLever)")

#!/usr/bin/env python3
# Purpose:      Audit the current gold set composition (era × tier), compare against
#               the original allocation targets from sr08_gold-set-composition.md §2.2,
#               and summarise gaps relative to the revised evaluation goals.
# Usage:        python3 scripts/sr08_gold_composition_audit.py
# Input:        data/annotation/sr08_gold_sample.csv
# Output:       stdout summary + data/processed/sr08_gold_composition_audit.csv
# Dependencies: pandas
# Assumptions:  silver_tier is a string column (0, 1, 2)

import pandas as pd

INPUT = "data/annotation/sr08_gold_sample.csv"
OUT   = "data/processed/sr08_gold_composition_audit.csv"

df = pd.read_csv(INPUT, dtype={"silver_tier": str})

# Actual composition
actual = df.groupby(["era", "silver_tier"]).size().unstack(fill_value=0)
actual.columns = [f"tier-{c}" for c in actual.columns]
actual["total"] = actual.sum(axis=1)

# Original allocation targets from sr08_gold-set-composition.md §2.2
# (era, tier-0, tier-1, tier-2, note)
targets = {
    "modern":    {"tier-0": 20, "tier-1": 40, "tier-2": 20},
    "19th-c":    {"tier-0": 15, "tier-1": 30, "tier-2": 15},
    "1700-1800": {"tier-0": 30, "tier-1": 20, "tier-2": 10},
    "pre-1700":  {"tier-0": 80, "tier-1": 15, "tier-2":  5},
    "unknown":   {"tier-0":  0, "tier-1":  0, "tier-2":  0},
}
target_df = pd.DataFrame(targets).T
target_df.index.name = "era"
target_df["total"] = target_df.sum(axis=1)

# Delta
delta = actual.subtract(target_df, fill_value=0)

print("=== ACTUAL gold set composition ===")
print(actual.to_string())
print(f"\nTotal: {actual['total'].sum():.0f}")

print("\n=== ORIGINAL allocation targets (sr08_gold-set-composition.md §2.2) ===")
print(target_df.to_string())
print(f"\nTotal: {target_df['total'].sum():.0f}")

print("\n=== DELTA (actual − target) ===")
print(delta.to_string())

# Save
audit = pd.concat(
    [actual.add_suffix("_actual"), target_df.add_suffix("_target"), delta.add_suffix("_delta")],
    axis=1,
)
audit.to_csv(OUT)
print(f"\nSaved to {OUT}")

#!/usr/bin/env python3
# Purpose:      Compute minimum entity instance counts needed to achieve a target CI
#               half-width for F1, using the Wilson interval approximation (treating F1
#               as a proportion). This is a lower bound — bootstrap CI for F1 is
#               empirically wider than Wilson, so actual required n may be larger.
# Usage:        python3 scripts/sr08_ci_sample_size.py
# Output:       stdout table + data/processed/sr08_ci_sample_size.csv
# Dependencies: numpy, pandas
# Assumptions:  Wilson interval: n = z^2 * p(1-p) / e^2
#               z = 1.96 (95% CI), e = target half-width, p = target F1 (worst-case p=0.5)

import numpy as np
import pandas as pd

OUT = "data/processed/sr08_ci_sample_size.csv"

Z = 1.96  # 95% CI

cases = [
    # (stratum,        metric,  target_f1, ci_halfwidth)
    ("Pre-1700",    "TITLE",   0.70, 0.05),
    ("Pre-1700",    "TITLE",   0.70, 0.10),
    ("Pre-1700",    "PERSON",  0.70, 0.05),
    ("Pre-1700",    "PERSON",  0.70, 0.10),
    ("1700-1800",   "TITLE",   0.75, 0.05),
    ("1700-1800",   "TITLE",   0.75, 0.10),
    ("1700-1800",   "PERSON",  0.70, 0.05),
    ("1700-1800",   "PERSON",  0.70, 0.10),
    ("19th-c",      "TITLE",   0.80, 0.05),
    ("19th-c",      "TITLE",   0.80, 0.10),
    ("Modern",      "TITLE",   0.85, 0.05),
    ("Modern",      "TITLE",   0.85, 0.10),
]

# Person prevalence by era (from sr08_check_person_in_title.py)
person_prevalence = {
    "Pre-1700":  0.087,
    "1700-1800": 0.050,
    "19th-c":    0.006,
    "Modern":    0.002,
}

rows = []
for stratum, metric, p, e in cases:
    # Wilson: n = z^2 * p(1-p) / e^2
    n_instances = int(np.ceil(Z**2 * p * (1 - p) / e**2))

    if metric == "TITLE":
        prevalence = 1.0  # TITLE always present
    else:
        prevalence = person_prevalence[stratum]

    n_records = int(np.ceil(n_instances / prevalence))

    rows.append({
        "stratum":      stratum,
        "metric":       metric,
        "target_F1":    p,
        "ci_halfwidth": f"±{int(e*100)} pp",
        "instances_needed": n_instances,
        "prevalence":   prevalence,
        "records_needed": n_records,
    })

df = pd.DataFrame(rows)
print(df.to_string(index=False))
print()
print("Note: Wilson interval treats F1 as a proportion — this is a lower bound.")
print("Bootstrap CI for F1 is empirically wider; actual required n may be larger.")

df.to_csv(OUT, index=False)
print(f"\nSaved to {OUT}")

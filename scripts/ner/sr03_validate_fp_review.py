"""
Validate FP review output in sr03_heuristic_validation_sample.csv.
Purpose: Check row count, field name validity, and that fp_fields only flags columns set to 1.
Usage: python scripts/validate_fp_review.py
Inputs: data/processed/sr03_heuristic_validation_sample.csv
Outputs: Printed summary to stdout.
Dependencies: pandas
Assumptions: CSV has been processed by sr03_fp_review.py.
"""

import pandas as pd

df = pd.read_csv("/Users/mta/Documents/claude/gemea/data/processed/sr03_heuristic_validation_sample.csv", dtype=str, keep_default_na=False)

total = len(df)
fp_set = (df["fp_fields"] != "").sum()
notes_set = (df["notes"] != "").sum()
mismatch_fn = ((df["fp_fields"] != "") & (df["notes"] == "")).sum()

print("Total rows:", total)
print("Rows with fp_fields set:", fp_set)
print("Rows with notes set:", notes_set)
print("fp non-empty but notes empty:", mismatch_fn)

valid_fields = {"f_other_title","f_person","f_person_compound","f_parallel","f_edition",
                "f_year","f_publisher","f_series","f_volume"}
bad_rows = []
flag_mismatch = []
for _, r in df.iterrows():
    fp = r["fp_fields"]
    if fp:
        for f in fp.split(","):
            f = f.strip()
            if f not in valid_fields:
                bad_rows.append((r["obj_id"], f))
            if r.get(f, "0") != "1":
                flag_mismatch.append((r["obj_id"], f, r.get(f, "?")))

print("Bad field names:", bad_rows if bad_rows else "none")
print("Flags on non-1 fields:", flag_mismatch if flag_mismatch else "none")
print("Columns:", list(df.columns))

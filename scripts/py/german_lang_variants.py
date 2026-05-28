"""
Purpose: Identify ISO 639 language tags for German variants in lang_counts.csv and report their share of the dataset.
Usage: python scripts/py/german_lang_variants.py
Inputs: data/processed/lang_counts.csv
Outputs: data/processed/german_variant_lang_counts.csv
Dependencies: pandas
Assumptions: lang_counts.csv has columns lang_code, count, pct; total is sum of all counts.
"""

import pandas as pd
from pathlib import Path

GERMAN_VARIANTS = {
    "ger": "German (modern standard)",
    "nds": "Low German / Low Saxon",
    "gmh": "Middle High German",
    "goh": "Old High German",
    "gsw": "Alemannic / Swiss German",
}

df = pd.read_csv("data/processed/lang_counts.csv")
total = df["count"].sum()

rows = []
for code, label in GERMAN_VARIANTS.items():
    row = df[df["lang_code"] == code]
    count = int(row["count"].iloc[0]) if not row.empty else 0
    rows.append({"lang_code": code, "label": label, "count": count, "pct_of_total": round(count / total * 100, 4)})

out = pd.DataFrame(rows)
out.loc[len(out)] = {"lang_code": "TOTAL", "label": "All German variants", "count": out["count"].sum(), "pct_of_total": round(out["count"].sum() / total * 100, 4)}

out_path = Path("data/processed/german_variant_lang_counts.csv")
out.to_csv(out_path, index=False)
print(out.to_string(index=False))
print(f"\nDataset total records: {total:,}")

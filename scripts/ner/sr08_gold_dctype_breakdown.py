# Purpose:      Show dc_type composition of the gold sample (sr08_gold_sample.csv)
#               broken down by era stratum. Highlights Leichenpredigt and Einblattdruck
#               share to assess how much the oversampling skews each era stratum.
# Usage:        python scripts/sr08_gold_dctype_breakdown.py
# Inputs:       data/annotation/sr08_gold_sample.csv
# Outputs:      data/processed/sr08_gold_dctype_breakdown.csv
#               Prints a per-era × dc_type summary table to stdout.
# Dependencies: pandas
# Assumptions:  dc_type is a pipe-separated list (e.g. "Leichenpredigt|Monografie").
#               era column is already present (pre-1700, 1700-1800, 19th-c, modern, unknown).

import pandas as pd
from pathlib import Path

ROOT   = Path(__file__).resolve().parent.parent
INPUT  = ROOT / "data" / "annotation" / "sr08_gold_sample.csv"
OUTPUT = ROOT / "data" / "processed" / "sr08_gold_dctype_breakdown.csv"

ERA_ORDER = ["pre-1700", "1700-1800", "19th-c", "modern", "unknown"]

COMPONENT_TYPES = {
    "Abschnitt", "Kapitel", "Band", "Heft", "issue",
    "Aufsatz", "Article", "Artikel", "Zeitschriftenartikel",
    "Index", "Inhaltsverzeichnis", "Vorwort", "Beilage",
    "Beigefügtes oder enthaltenes Werk",
    "Text", "Volume", "Section", "Chapter",
    "Sammelwerksbeitrag", "Buchbeitrag", "Vers",
    "Faszikel", "Konferenzbeitrag", "Review",
    "Stellungnahme", "Abschlussbericht", "Gutachten",
    "(none)", "",
}

BASE_TYPES = {
    "Monografie", "Monograph", "Monograph|book", "book",
    "mehrbändiges Werk", "Multivolume Work", "Multivolume work",
    "Fortlaufendes Sammelwerk", "Sammelwerk", "Periodical",
    "letter", "Letter",
}


def normalize_dctype(raw: str) -> str:
    parts = [p.strip() for p in str(raw).split("|") if p.strip()]
    parts = [p for p in parts if p not in COMPONENT_TYPES]
    if not parts:
        return "(component-only)"
    specific = [p for p in parts if p not in BASE_TYPES]
    if specific:
        return "|".join(specific)
    return parts[0]


def main():
    df = pd.read_csv(INPUT)
    print(f"Gold sample: {len(df)} records")

    df["dc_type_norm"] = df["dc_type"].fillna("(none)").apply(normalize_dctype)
    df["era"] = df["era"].fillna("unknown")

    # Per-era × dc_type counts
    ct = (
        df.groupby(["era", "dc_type_norm"], observed=True)
        .size()
        .reset_index(name="n")
        .sort_values(["era", "n"], ascending=[True, False])
    )
    era_totals = df.groupby("era", observed=True).size().rename("era_total")
    ct = ct.merge(era_totals, on="era")
    ct["pct"] = (100 * ct["n"] / ct["era_total"]).round(1)

    # Reorder eras
    era_cat = pd.CategoricalDtype(ERA_ORDER, ordered=True)
    ct["era"] = ct["era"].astype(era_cat)
    ct = ct.sort_values(["era", "n"], ascending=[True, False])

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    ct.to_csv(OUTPUT, index=False)
    print(f"Saved: {OUTPUT}\n")

    # Console summary
    for era in ERA_ORDER:
        sub = ct[ct["era"] == era]
        if sub.empty:
            continue
        total = sub["era_total"].iloc[0]
        print(f"── {era}  (n={total})")
        for _, row in sub.iterrows():
            bar = "█" * int(row["pct"] / 5)
            flag = ""
            if row["dc_type_norm"] in ("Leichenpredigt", "Einblattdruck"):
                flag = " ◄"
            print(f"   {row['dc_type_norm']:<35}  {row['n']:>4}  {row['pct']:>5.1f}%  {bar}{flag}")
        print()

    # Summary: LP + EB share per era (raw contains-match — catches compound types)
    print("── Leichenpredigt + Einblattdruck share per era (contains-match on raw dc_type):")
    df["has_lp"] = df["dc_type"].str.contains("Leichenpredigt", na=False)
    df["has_eb"] = df["dc_type"].str.contains("Einblattdruck", na=False)
    df["has_lp_or_eb"] = df["has_lp"] | df["has_eb"]

    share_raw = (
        df.groupby("era", observed=True)["has_lp_or_eb"].sum()
        / era_totals
        * 100
    ).round(1).rename("lp_eb_pct")
    lp_raw = (
        df.groupby("era", observed=True)["has_lp"].sum()
    ).rename("lp_n")
    eb_raw = (
        df.groupby("era", observed=True)["has_eb"].sum()
    ).rename("eb_n")

    combined = era_totals.to_frame().join(lp_raw).join(eb_raw).join(share_raw).fillna(0)
    combined["lp_n"]  = combined["lp_n"].astype(int)
    combined["eb_n"]  = combined["eb_n"].astype(int)
    print(combined.to_string())


if __name__ == "__main__":
    main()

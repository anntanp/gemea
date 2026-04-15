#!/usr/bin/env python3
"""
Purpose:  Detect the language of each DDB title and compare against the dc:language
          annotation. Measures annotation agreement and surfaces systematic mismatches.
Usage:    python scripts/analysis/detect_lang_titles.py [options]
          python scripts/analysis/detect_lang_titles.py --sample 10000
Options:  --model-path PATH   path to lid.176.bin (default: data/models/lid.176.bin)
          --sample N          run on a random sample of N rows (for testing)
          --min-title-len INT skip titles shorter than N characters (default: 3)
Inputs:   data/out/s2/s2_meta.parquet
          data/models/lid.176.bin  (download from https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin)
Outputs:  data/processed/lang_detect_titles.csv   (per-row: obj_id, title, lang_annotated, lang_detected, confidence, match)
          data/processed/lang_detect_summary.csv   (per-language: n, match_n, match_pct, top_wrong_1..3)
Dependencies: pandas, pyarrow, fasttext
Assumptions: Run from the gemea/ project root.
"""

import argparse
import textwrap
from collections import Counter
from pathlib import Path

import fasttext
import numpy as np
import pandas as pd

# ── CLI ────────────────────────────────────────────────────────────────────────
parser = argparse.ArgumentParser()
parser.add_argument("--model-path", default="data/models/lid.176.bin")
parser.add_argument("--sample", type=int, default=None)
parser.add_argument("--min-title-len", type=int, default=3)
args = parser.parse_args()

# ── Paths ──────────────────────────────────────────────────────────────────────
PARQUET   = Path("data/out/s2/s2_meta.parquet")
MODEL     = Path(args.model_path)
CSV_ROWS  = Path("data/processed/lang_detect_titles.csv")
CSV_SUMM  = Path("data/processed/lang_detect_summary.csv")
CSV_ROWS.parent.mkdir(parents=True, exist_ok=True)

# ── Model check ────────────────────────────────────────────────────────────────
if not MODEL.exists():
    print(textwrap.dedent(f"""
        ERROR: fasttext model not found at {MODEL}

        Download it with:
            mkdir -p data/models
            curl -L -o data/models/lid.176.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin
        or (quantized, 917 KB, slightly lower accuracy):
            curl -L -o data/models/lid.176.ftz https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz
        Then rerun with --model-path data/models/lid.176.ftz if using the quantized version.
    """).strip())
    raise SystemExit(1)

# ── ISO 639-1 → ISO 639-2/B mapping ───────────────────────────────────────────
# Bibliographic codes (ISO 639-2/B) as used by DDB
ISO1_TO_ISO2B = {
    "de": "ger", "la": "lat", "en": "eng", "fr": "fre",
    "it": "ita", "nl": "dut", "es": "spa",
    "el": "gre",   # modern Greek (fasttext uses 'el'; DDB 'grc' = ancient Greek, unmappable)
    "zh": "chi", "ru": "rus", "pl": "pol", "ja": "jpn",
    "he": "heb", "ar": "ara", "da": "dan", "sv": "swe",
    "nb": "nor", "no": "nor", "pt": "por", "hu": "hun",
    "cs": "cze",  "fi": "fin", "tr": "tur", "fa": "per",
    "hy": "arm",  "yi": "yid", "az": "aze", "sr": "srp",
    "sk": "slo",  "sa": "san", "ml": "mal", "kn": "kan",
    # gaps identified from error analysis
    "ca": "cat",  # Catalan
    "hr": "hrv",  # Croatian
    "ro": "rum",  # Romanian
    "uk": "ukr",  # Ukrainian
    "bo": "tib",  # Tibetan
    "rm": "roh",  # Romansh
    "sq": "alb",  # Albanian
    "cy": "wel",  # Welsh
    "bg": "bul",  # Bulgarian
    "mk": "mac",  # Macedonian
    "sl": "slv",  # Slovenian
    "lt": "lit",  # Lithuanian
    "lv": "lav",  # Latvian
    "et": "est",  # Estonian
    "is": "ice",  # Icelandic
    "ga": "gle",  # Irish
    "af": "afr",  # Afrikaans
    "sw": "swa",  # Swahili
    "id": "ind",  # Indonesian
    "vi": "vie",  # Vietnamese
    "eo": "epo",  # Esperanto
    "eu": "baq",  # Basque
    "gl": "glg",  # Galician
    "tl": "tgl",  # Tagalog
    "ko": "kor",  # Korean
    "ms": "may",  # Malay
}

# Codes with no ISO 639-1 equivalent — fasttext cannot produce these
HISTORICAL_CODES = {"grc", "gmh", "chu", "nds", "mnc", "ota", "wen"}

# Annotation codes that carry no single-language meaning → excluded
EXCLUDE_LANG = {None, "(none)", "und", "zxx", "mul"}

# ── Load ───────────────────────────────────────────────────────────────────────
print(f"Loading {PARQUET} …")
df = pd.read_parquet(PARQUET, columns=["obj_id", "title", "lang"])
print(f"  {len(df):,} rows total")

if args.sample:
    df = df.sample(n=args.sample, random_state=42)
    print(f"  Sampled {args.sample:,} rows")

# ── Filter ─────────────────────────────────────────────────────────────────────
before = len(df)
df["title"] = df["title"].fillna("").str.strip()
df["lang"]  = df["lang"].fillna("(none)").str.strip()

mask = (
    (df["title"].str.len() >= args.min_title_len) &
    (df["lang"] != "") &
    (~df["lang"].isin(EXCLUDE_LANG))
)
df = df[mask].copy()
print(f"  After filter (title≥{args.min_title_len} chars, lang annotated): {len(df):,} rows "
      f"({len(df) / before * 100:.1f}% of total)")

# ── Load fasttext model ────────────────────────────────────────────────────────
print(f"\nLoading model {MODEL} …")
model = fasttext.load_model(str(MODEL))

# ── Detect in chunks ───────────────────────────────────────────────────────────
CHUNK = 50_000
detected_codes, confidences = [], []

print(f"Detecting language in chunks of {CHUNK:,} …")
titles = df["title"].tolist()
for start in range(0, len(titles), CHUNK):
    batch = [t.replace("\n", " ") for t in titles[start:start + CHUNK]]
    labels, probs = model.predict(batch)
    detected_codes.extend(lbl[0].replace("__label__", "") for lbl in labels)
    confidences.extend(float(p[0]) for p in probs)
    if (start // CHUNK + 1) % 10 == 0:
        pct = min((start + CHUNK) / len(titles) * 100, 100)
        print(f"  {start + CHUNK:>10,} / {len(titles):,}  ({pct:.0f}%)")

print(f"  Done.")

# ── Map and compute match ──────────────────────────────────────────────────────
df["lang_detected"] = [ISO1_TO_ISO2B.get(c, c) for c in detected_codes]
df["confidence"]    = confidences
df["lang_annotated"] = df["lang"]
df["match"]         = df["lang_detected"] == df["lang_annotated"]

# ── Save per-row CSV ───────────────────────────────────────────────────────────
out_cols = ["obj_id", "title", "lang_annotated", "lang_detected", "confidence", "match"]
df[out_cols].to_csv(CSV_ROWS, index=False)
print(f"\nPer-row CSV saved → {CSV_ROWS}  ({len(df):,} rows)")

# ── Summary A: overall ─────────────────────────────────────────────────────────
n_total  = len(df)
n_match  = df["match"].sum()
n_miss   = n_total - n_match

print("\n" + "━" * 60)
print(f" Overall results")
print("━" * 60)
print(f"  Titles evaluated : {n_total:>12,}")
print(f"  Match (exact)    : {n_match:>12,}  ({n_match / n_total * 100:.1f}%)")
print(f"  Mismatch         : {n_miss:>12,}  ({n_miss  / n_total * 100:.1f}%)")

# ── Summary B: per-language match table ───────────────────────────────────────
def top_wrong(grp, n=3):
    """Top-n wrong detections for a group of mismatch rows."""
    counts = Counter(grp["lang_detected"])
    return ", ".join(f"{lang}({cnt/len(grp)*100:.1f}%)"
                     for lang, cnt in counts.most_common(n))

rows = []
for lang, grp in df.groupby("lang_annotated"):
    n       = len(grp)
    match_n = grp["match"].sum()
    wrong   = grp[~grp["match"]]
    top3    = top_wrong(wrong) if len(wrong) else ""
    rows.append({
        "lang_annotated": lang,
        "n": n,
        "match_n": match_n,
        "match_pct": round(match_n / n * 100, 1),
        "historical": lang in HISTORICAL_CODES,
        "top_wrong_1": (Counter(wrong["lang_detected"]).most_common(1) or [("", 0)])[0][0],
        "top_wrong_2": (Counter(wrong["lang_detected"]).most_common(2)[1:2] or [("", 0)])[0][0],
        "top_wrong_3": (Counter(wrong["lang_detected"]).most_common(3)[2:3] or [("", 0)])[0][0],
        "top_wrong_str": top3,
    })

summary = pd.DataFrame(rows).sort_values("n", ascending=False)
summary.to_csv(CSV_SUMM, index=False)
print(f"\nPer-language summary saved → {CSV_SUMM}")

# Print table (top 20 by n)
print("\n" + "━" * 80)
print(f" Per-language match rate (top 20 by count)")
print("━" * 80)
print(f"{'lang':<8} {'n':>10} {'match%':>8}  top wrong detections")
print("─" * 80)
for _, r in summary.head(20).iterrows():
    hist_flag = " *" if r["historical"] else ""
    print(f"{r['lang_annotated']:<8}{hist_flag:<2} {r['n']:>10,} {r['match_pct']:>7.1f}%  {r['top_wrong_str']}")
print("  * = historical code with no fasttext equivalent; mismatch structurally expected")

# ── Summary C: error analysis ──────────────────────────────────────────────────
print("\n" + "━" * 60)
print(" Error analysis")
print("━" * 60)

# Confusion matrix (top 10 × top 10)
top_ann = summary.head(10)["lang_annotated"].tolist()
mismatches = df[~df["match"]]
conf_pairs = Counter(zip(mismatches["lang_annotated"], mismatches["lang_detected"]))
print("\n  Top mismatch pairs (annotated → detected):")
for (ann, det), cnt in conf_pairs.most_common(15):
    pct_of_ann = cnt / df[df["lang_annotated"] == ann].shape[0] * 100
    print(f"    {ann} → {det}: {cnt:>8,}  ({pct_of_ann:.1f}% of {ann} titles)")

# Title length: matches vs mismatches
match_len = df[df["match"]]["title"].str.len().median()
miss_len  = df[~df["match"]]["title"].str.len().median()
print(f"\n  Median title length:  matches={match_len:.0f} chars   mismatches={miss_len:.0f} chars")

# Confidence distribution
print(f"\n  Confidence (mean):  matches={df[df['match']]['confidence'].mean():.3f}   "
      f"mismatches={df[~df['match']]['confidence'].mean():.3f}")

# ── Summary D: low-confidence correct ─────────────────────────────────────────
low_conf_correct = df[df["match"] & (df["confidence"] < 0.5)]
print(f"\n  Low-confidence correct (conf<0.5): {len(low_conf_correct):,} "
      f"({len(low_conf_correct) / n_match * 100:.1f}% of matches)")

# Historical code breakdown
hist_df = df[df["lang_annotated"].isin(HISTORICAL_CODES)]
if len(hist_df):
    print(f"\n  Historical codes (no fasttext equivalent):")
    for lang, grp in hist_df.groupby("lang_annotated"):
        top_det = Counter(grp["lang_detected"]).most_common(3)
        top_str = ", ".join(f"{l}({c})" for l, c in top_det)
        print(f"    {lang}: {len(grp):,} titles → fasttext detects: {top_str}")

print("\n" + "━" * 60)

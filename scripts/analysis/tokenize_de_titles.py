#!/usr/bin/env python3
"""
Purpose:      Tokenize titles in s2_meta_de_content.parquet using xlm-roberta-large
              and compute all_tokens / content_tokens counts for each title.
              Output is consumed by sr10_explore_token_distribution.py,
              sr10_analyse_title_lengths.py, and sr11_dctype_by_era.py.
Usage:        python scripts/analysis/tokenize_de_titles.py
              python scripts/analysis/tokenize_de_titles.py --batch-size 1024
Inputs:       data/out/s2/s2_meta_de_content.parquet
Outputs:      data/processed/de_titles_tokenized.parquet
                columns: obj_id, title, lang, dc_type, dates,
                         all_tokens, content_tokens
Dependencies: pandas, pyarrow, transformers, torch
Assumptions:  Run from the gemea/ project root.
              FacebookAI/xlm-roberta-large tokenizer cached in HF cache or available online.
"""

import argparse
import unicodedata
from pathlib import Path

import pandas as pd
from transformers import AutoTokenizer

# ── Paths ──────────────────────────────────────────────────────────────────────
PARQUET_IN  = Path("data/out/s2/s2_meta_de_content.parquet")
PARQUET_OUT = Path("data/processed/de_titles_tokenized.parquet")
PARQUET_OUT.parent.mkdir(parents=True, exist_ok=True)

MODEL_NAME = "FacebookAI/xlm-roberta-large"

# German stopwords only — Latin titles are not filtered
STOPWORDS = {
    "der", "die", "das", "ein", "eine", "von", "und", "zu", "im", "in",
    "an", "auf", "für", "mit", "bei", "dem", "den", "des", "einer", "eines",
}


# ── Preprocessing ──────────────────────────────────────────────────────────────
def normalize_historical(text: str) -> str:
    """NFC + long-s + common ligatures (see notes/corpus-analysis/tokenization.md)."""
    text = unicodedata.normalize("NFC", text)
    text = text.replace("\u017f", "s").replace("\u017e", "s")   # ſ, ǅ → s
    text = text.replace("\ufb01", "fi").replace("\ufb02", "fl")
    text = text.replace("\ufb00", "ff").replace("\ufb03", "ffi").replace("\ufb04", "ffl")
    return text


# ── Batch tokenizer ────────────────────────────────────────────────────────────
def compute_token_counts(titles: list[str], tokenizer) -> tuple[list[int], list[int]]:
    """
    Return (all_tokens, content_tokens) for a batch of title strings.

    all_tokens     = subword count excluding <s> and </s> special tokens
    content_tokens = subword count after ignoring subwords that belong to
                     stopword words (identified via offset mapping)
    """
    normalized = [normalize_historical(t) for t in titles]

    enc = tokenizer(
        normalized,
        truncation=True,
        max_length=128,
        return_offsets_mapping=True,
        padding=False,
    )

    all_counts     = []
    content_counts = []

    for i, title in enumerate(normalized):
        ids     = enc["input_ids"][i]
        offsets = enc["offset_mapping"][i]

        # all_tokens: exclude the two special tokens (<s> at 0, </s> at end)
        n_all = len(ids) - 2
        all_counts.append(max(n_all, 0))

        # content_tokens: exclude subwords whose source word is a stopword
        # A "word" is the contiguous title span covered by consecutive subwords
        # with the same character run. We use the offset map: a subword at
        # position j belongs to a stopword if the title substring it covers
        # (after stripping punctuation from boundaries) lowercases to a stopword.
        # Simpler approach: collect word-level spans first.
        title_lower = title.lower()
        stopword_positions: set[int] = set()  # token index positions to skip

        # Build word spans from offsets (skip special tokens at pos 0 and -1)
        j = 1
        while j < len(ids) - 1:
            start, end = offsets[j]
            if start == end:  # special/padding token with zero span
                j += 1
                continue
            # Extend to the full word: keep advancing while next token continues
            # without a gap (continuation pieces in XLM-R have no leading space)
            word_start = start
            word_end   = end
            word_token_indices = [j]
            k = j + 1
            while k < len(ids) - 1:
                ns, ne = offsets[k]
                if ns == word_end:
                    word_end = ne
                    word_token_indices.append(k)
                    k += 1
                else:
                    break
            word = title_lower[word_start:word_end].strip(".,;:!?\"'()[]{}–—-")
            if word in STOPWORDS:
                stopword_positions.update(word_token_indices)
            j = k

        n_content = sum(
            1 for idx in range(1, len(ids) - 1)
            if idx not in stopword_positions
        )
        content_counts.append(n_content)

    return all_counts, content_counts


# ── Main ───────────────────────────────────────────────────────────────────────
def main(batch_size: int) -> None:
    print(f"Loading {PARQUET_IN} …")
    df = pd.read_parquet(
        PARQUET_IN,
        columns=["obj_id", "title", "lang", "dc_type", "dc_issued"],
    )
    n_total = len(df)
    print(f"  {n_total:,} rows\n")

    # ── dates column: first 4 chars of dc_issued[0] ───────────────────────────
    def extract_year(val):
        if val is None:
            return None
        # dc_issued may be a list, numpy array, or scalar
        try:
            if hasattr(val, "__len__") and not isinstance(val, str):
                val = val[0] if len(val) > 0 else None
        except (TypeError, KeyError):
            pass
        if val is None:
            return None
        s = str(val).strip()
        return s[:4] if len(s) >= 4 else None

    df["dates"] = df["dc_issued"].apply(extract_year)
    df = df.drop(columns=["dc_issued"])

    # ── fill missing titles ────────────────────────────────────────────────────
    df["title"] = df["title"].fillna("").astype(str)

    # ── load tokenizer ─────────────────────────────────────────────────────────
    print(f"Loading tokenizer: {MODEL_NAME} …")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    print("  Tokenizer loaded.\n")

    # ── batch tokenize ─────────────────────────────────────────────────────────
    titles = df["title"].tolist()
    n_batches = (n_total + batch_size - 1) // batch_size

    all_tokens_col     = []
    content_tokens_col = []

    for b in range(n_batches):
        lo = b * batch_size
        hi = min(lo + batch_size, n_total)
        batch = titles[lo:hi]

        a, c = compute_token_counts(batch, tokenizer)
        all_tokens_col.extend(a)
        content_tokens_col.extend(c)

        if (b + 1) % 50 == 0 or b == n_batches - 1:
            pct = (hi / n_total) * 100
            print(f"  batch {b+1:>5}/{n_batches}  ({hi:>9,}/{n_total:,}  {pct:5.1f}%)")

    df["all_tokens"]     = all_tokens_col
    df["content_tokens"] = content_tokens_col

    # ── save ───────────────────────────────────────────────────────────────────
    out_cols = ["obj_id", "title", "lang", "dc_type", "dates",
                "all_tokens", "content_tokens"]
    df[out_cols].to_parquet(PARQUET_OUT, index=False)
    size_mb = PARQUET_OUT.stat().st_size / 1024**2
    print(f"\nSaved {n_total:,} rows → {PARQUET_OUT}  ({size_mb:.1f} MB)")

    # ── quick summary ──────────────────────────────────────────────────────────
    import numpy as np
    at = df["all_tokens"].values
    ct = df["content_tokens"].values
    print(f"\nall_tokens     — median {int(np.median(at))}, p90 {int(np.percentile(at,90))}, max {at.max()}")
    print(f"content_tokens — median {int(np.median(ct))}, p90 {int(np.percentile(ct,90))}, max {ct.max()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch-size", type=int, default=512,
                        help="Number of titles per tokenizer call (default: 512)")
    args = parser.parse_args()
    main(args.batch_size)

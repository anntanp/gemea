#!/usr/bin/env python3
"""
Purpose:  Word cloud of the word "book" in each DDB language, sized by object count.
Usage:    python scripts/analysis/wordcloud_book.py
Inputs:   data/processed/lang_by_year.csv
Outputs:  notes/images/wordcloud_book.png
Dependencies: pandas, wordcloud, matplotlib
Assumptions: Run from the gemea/ project root.
"""

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from wordcloud import WordCloud

# ── Paths ──────────────────────────────────────────────────────────────────────
CSV_IN  = Path("data/processed/lang_by_year.csv")
PNG_OUT = Path("notes/images/wordcloud_book.png")
PNG_OUT.parent.mkdir(parents=True, exist_ok=True)

# ── "Book" in each ISO 639-2 language code present in the corpus ───────────────
# Codes follow ISO 639-2/B (bibliographic) as used by DDB.
BOOK = {
    "ger": "Buch",           # German
    "lat": "liber",          # Latin
    "eng": "book",           # English
    "fre": "livre",          # French
    "ita": "libro",          # Italian
    "dut": "boek",           # Dutch
    "spa": "libro",          # Spanish  (same word as Italian — counts merge)
    "grc": "βιβλίον",        # Ancient Greek
    "gre": "βιβλίο",         # Modern Greek
    "chi": "书",              # Chinese
    "rus": "книга",          # Russian
    "pol": "książka",        # Polish
    "jpn": "本",              # Japanese
    "heb": "ספר",            # Hebrew
    "ara": "كتاب",           # Arabic
    "dan": "bog",            # Danish
    "swe": "bok",            # Swedish
    "nor": "bok",            # Norwegian (same as Swedish — counts merge)
    "por": "livro",          # Portuguese
    "hun": "könyv",          # Hungarian
    "cze": "kniha",          # Czech
    "slo": "kniha",          # Slovak   (same as Czech — counts merge)
    "fin": "kirja",          # Finnish
    "tur": "kitap",          # Turkish
    "per": "کتاب",           # Persian
    "san": "पुस्तक",          # Sanskrit
    "hin": "पुस्तक",          # Hindi    (same as Sanskrit — counts merge)
    "mal": "പുസ്തകം",         # Malayalam
    "kan": "ಪುಸ್ತಕ",          # Kannada
    "arm": "գիրք",           # Armenian
    "yid": "בוך",            # Yiddish
    "srp": "књига",          # Serbian
    "aze": "kitab",          # Azerbaijani
    "ota": "كتاب",           # Ottoman Turkish (Arabic script, same word as Arabic)
    "wen": "kniha",          # Sorbian
    "nds": "Book",           # Low German
    "gmh": "buoch",          # Middle High German
    "chu": "книга",          # Church Slavonic (same script/word as Russian)
    "mnc": "bithe",          # Manchu
}

# ── Load and aggregate ─────────────────────────────────────────────────────────
print(f"Loading {CSV_IN} …")
df = pd.read_csv(CSV_IN)
totals = df.groupby("lang")["count"].sum()

# Build frequency dict: word → total object count across all langs using that word
freq: dict[str, int] = {}
matched_langs = []
for code, word in BOOK.items():
    if code in totals.index:
        freq[word] = freq.get(word, 0) + int(totals[code])
        matched_langs.append((code, word, int(totals[code])))

matched_langs.sort(key=lambda x: -x[2])
print(f"\n{'Code':<6} {'Word':<16} {'Objects':>12}")
print("-" * 36)
for code, word, n in matched_langs:
    print(f"{code:<6} {word:<16} {n:>12,}")

total_covered = sum(n for _, _, n in matched_langs)
total_all = int(totals.sum())
print(f"\nCovered: {total_covered:,} / {total_all:,} objects "
      f"({total_covered / total_all * 100:.1f}%)")

# ── Font — needs Unicode coverage for CJK, Arabic, Hebrew, Devanagari, etc. ───
FONT_CANDIDATES = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "/usr/share/fonts/noto/NotoSans-Regular.ttf",
]
font_path = next((f for f in FONT_CANDIDATES if Path(f).exists()), None)
if font_path is None:
    raise FileNotFoundError(
        "No Unicode font found. Install a Noto or Arial Unicode font and add its "
        "path to FONT_CANDIDATES."
    )
print(f"\nFont: {font_path}")

# ── Word cloud ─────────────────────────────────────────────────────────────────
wc = WordCloud(
    font_path=font_path,
    width=1400,
    height=700,
    background_color="white",
    colormap="tab20",
    max_words=200,
    prefer_horizontal=0.7,
    margin=20,
    random_state=42,
).generate_from_frequencies(freq)

fig, ax = plt.subplots(figsize=(14, 7))
ax.imshow(wc, interpolation="bilinear")
ax.axis("off")
ax.set_title(
    "\"Book\" in Each Language — DDB Sector 2\n"
    f"Word size ∝ object count  ·  {total_covered:,} objects covered "
    f"({total_covered / total_all * 100:.1f}%)",
    fontsize=11,
    pad=12,
)
fig.tight_layout()
fig.savefig(PNG_OUT, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"PNG saved → {PNG_OUT}")

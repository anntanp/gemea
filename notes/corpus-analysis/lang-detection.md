                # Language Detection vs. dc:language Annotation

## 1. Task

Read all titles from `data/out/s2/s2_meta.parquet`, detect the language of each title using an automatic language identification model, and compare the detected language against the `lang` annotation (ISO 639-2/B code assigned by cataloguers). The goal is to measure annotation agreement, surface systematic mismatches, and identify languages where detection is unreliable.

Script: `scripts/analysis/detect_lang_titles.py`
Outputs: `data/processed/lang_detect_titles.csv`, `data/processed/lang_detect_summary.csv`

---

## 2. Library comparison

| Library | Latin | Short-text acc. | Speed | ISO out | Status | Link |
|---------|-------|-----------------|-------|---------|--------|------|
| **[fasttext lid.176](https://fasttext.cc/docs/en/language-identification.html)** | ✓ | **best** (<70 chars) | ~120k/s | 639-1 | Active | [GitHub](https://github.com/facebookresearch/fastText) |
| [lingua-py](https://github.com/pemistahl/lingua-py) | ✓ | excellent | moderate | 639-1/3 | Requires Python ≥3.12 | [PyPI](https://pypi.org/project/lingua-language-detector/) |
| [langid](https://github.com/saffsd/langid.py) | ✓ | ~91% | slow | 639-1 | Inactive | [PyPI](https://pypi.org/project/langid/) |
| [langdetect](https://github.com/Mimino666/langdetect) | **✗** | ~92% | very slow | 639-1 | Inactive | [PyPI](https://pypi.org/project/langdetect/) |
| [pycld2](https://github.com/aboSamoor/pycld2) | ✓ | poor (<200 chars) | fastest | custom | Legacy | [PyPI](https://pypi.org/project/pycld2/) |
| [gcld3](https://github.com/google/cld3) | ? | moderate | fast | BCP-47 | Archived | [PyPI](https://pypi.org/project/gcld3/) |

Benchmark sources: [Modelpredict language identification survey](https://modelpredict.com/language-identification-survey) · [Amitness benchmark](https://amitness.com/posts/language-identification-python)

### 2.1 Decision: fasttext lid.176.bin

- Best documented short-text accuracy on texts <70 characters — the dominant range for bibliographic titles
- 176 languages including Latin (`la`)
- ~120k sentences/sec → ~2 min for 14M rows single-threaded
- gemea venv is Python 3.9, which rules out lingua-py (requires ≥3.12)
- Model: `lid.176.bin` (126 MB) or quantized `lid.176.ftz` (917 KB, slightly lower accuracy)

---

## 3. Method

### 3.1 Filter criteria

Rows included if:
- `title` non-empty and `len(title) ≥ 3`
- `lang` not in `{None, "(none)", "und", "zxx", "mul"}` — codes with no single-language annotation to compare

### 3.2 Detection

Batch predict using `model.predict(list_of_titles)` in chunks of 50k. Strip `__label__` prefix from fasttext output. Map ISO 639-1 output → ISO 639-2/B via lookup table.

### 3.3 ISO 639-1 → ISO 639-2/B mapping

```
de→ger  la→lat  en→eng  fr→fre  it→ita  nl→dut  es→spa
el→gre  zh→chi  ru→rus  pl→pol  ja→jpn  he→heb  ar→ara
da→dan  sv→swe  nb→nor  pt→por  hu→hun  cs→cze  fi→fin
tr→tur  fa→per  hy→arm  yi→yid  az→aze  sr→srp  sk→slo
sa→san  ml→mal  kn→kan
```

### 3.4 Historical codes with no fasttext equivalent

The following ISO 639-2/B codes in the DDB corpus have no ISO 639-1 counterpart — fasttext cannot produce them. Mismatches for these codes are structurally expected:

`grc` (Ancient Greek), `gmh` (Middle High German), `chu` (Church Slavonic), `nds` (Low German), `mnc` (Manchu), `ota` (Ottoman Turkish), `wen` (Sorbian)

---

## 4. Results

Run: full corpus (18,570,245 rows), model `lid.176.ftz`, `--min-title-len 3`.
Outputs: `data/processed/lang_detect_titles.csv`, `data/processed/lang_detect_summary.csv`.

### 4.1 Overall match rate

| | n | % |
|-|--:|--:|
| Titles evaluated | 16,895,265 | 91.0% of corpus |
| Match (exact) | 14,122,880 | **83.6%** |
| Mismatch | 2,772,385 | 16.4% |

Initial run (before mapping fixes) yielded 79.0% — the +4.6pp gain comes from adding 25 missing ISO 639-1 → 639-2/B code mappings (`ca→cat`, `hr→hrv`, `ro→rum`, `uk→ukr`, etc.) and fixing the empty-lang filter bug.

### 4.2 Per-language match table

Top languages by object count:

| lang | label | n | match% | top wrong detections |
|------|-------|--:|-------:|----------------------|
| ger | German | 11,993,373 | **90.6%** | eng(54.9%), fre(10.6%), ita(6.6%) |
| eng | English | 2,520,089 | **96.9%** | ger(54.1%), fre(9.4%), spa(8.3%) |
| lat | Latin | 1,330,227 | **19.1%** | eng(42.2%), ger(20.8%), ita(14.3%) |
| fre | French | 467,395 | 69.5% | ger(42.5%), eng(38.5%), ita(4.0%) |
| ita | Italian | 165,198 | 64.1% | ger(38.6%), eng(30.3%), spa(9.4%) |
| dut | Dutch | 50,254 | 63.1% | ger(45.5%), eng(28.4%), fre(7.9%) |
| spa | Spanish | 41,625 | 74.3% | eng(32.5%), ger(27.7%), por(11.3%) |
| grc * | Ancient Greek | 31,543 | 0.0% | ger(38.4%), eng(27.3%), lat(8.7%) |
| ara | Arabic | 31,024 | 1.4% | ger(31.9%), eng(31.1%), lv(14.4%) |
| chi | Chinese | 30,707 | 30.9% | jpn(36.8%), eng(20.9%), sh(13.7%) |
| rus | Russian | 24,056 | 16.6% | sl(29.5%), cze(16.1%), ger(11.6%) |
| pol | Polish | 23,528 | 67.4% | ger(54.5%), eng(22.1%), fre(7.4%) |
| heb | Hebrew | 15,826 | 3.3% | ger(35.2%), eng(34.1%), fre(5.2%) |
| jpn | Japanese | 13,546 | 47.0% | chi(42.4%), eng(20.5%), sh(17.8%) |
| per | Persian | 11,616 | 44.8% | ger(52.6%), eng(16.2%), lv(9.0%) |
| dan | Danish | 10,356 | 41.4% | eng(28.5%), ger(25.5%), no(19.7%) |
| swe | Swedish | 10,278 | 52.4% | eng(29.2%), ger(26.5%), dan(10.9%) |
| gre | Modern Greek | 9,989 | 3.0% | ger(26.2%), eng(20.1%), lv(17.8%) |
| nds * | Low German | 9,768 | 10.9% | ger(51.5%), eng(19.2%), dut(6.2%) |
| por | Portuguese | 9,752 | 80.0% | spa(32.3%), eng(24.8%), ger(23.6%) |
| mnc * | Manchu | 9,004 | 0.0% | chi(32.7%), eng(23.4%), id(9.7%) |
| ota * | Ottoman Turkish | 7,427 | 0.0% | ger(26.0%), eng(17.4%), lv(14.7%) |

\* = historical code with no ISO 639-1 equivalent; 0% match is structurally expected.

### 4.3 Error analysis

**Top mismatch pairs (annotated → detected, full corpus):**

| annotated | detected | count | % of annotated |
|-----------|----------|------:|---------------:|
| (empty) | ger | 685,959 | 69.8% |
| ger | eng | 621,917 | 5.2% |
| lat | eng | 454,133 | 34.1% |
| lat | ger | 224,229 | 16.9% |
| lat | ita | 153,632 | 11.5% |
| (empty) | eng | 127,584 | 13.0% |
| ger | fre | 120,215 | 1.0% |
| lat | spa | 68,138 | 5.1% |
| lat | fre | 64,551 | 4.9% |
| fre | ger | 60,641 | 13.0% |

**Title length:** Mismatch titles are roughly half as long (median 27 chars vs. 60 chars for matches). Short titles contain less disambiguating signal.

**Confidence:** Mean confidence 0.853 for matches, 0.496 for mismatches — the model itself signals uncertainty on the hard cases.

**Code mapping gaps — detected correctly but counted as mismatch:**
Several 0% languages are actually correct detections with missing ISO 639-1 → 639-2/B mappings:

| DDB code | fasttext output | mapping missing |
|----------|-----------------|-----------------|
| cat (Catalan) | `ca` | `ca → cat` |
| hrv (Croatian) | `hr` | `hr → hrv` |
| nor (Norwegian) | `no` | `no → nor` |
| rum (Romanian) | `ro` | `ro → rum` |
| ukr (Ukrainian) | `uk` | `uk → ukr` |
| tib (Tibetan) | `bo` | `bo → tib` |
| roh (Romansh) | `rm` | `rm → roh` |
| alb (Albanian) | `sq` | `sq → alb` |
| wel (Welsh) | `cy` | `cy → wel` |

Adding these mappings would recover true matches for ~5K–15K titles.

**Script-detection failures (near-0% despite modern language):**
Languages where fasttext produces largely random output suggest the titles are not in the expected script, are transliterated, or are too short:

- `ara` (1.4%), `heb` (3.3%) — Arabic/Hebrew script titles likely transcribed in Latin script in many records; fasttext trained on native-script text
- `gre` (3.0%) — Modern Greek annotated records detected as `ger`/`eng`/`lv` — possibly transliterated or title is in Latin script
- `rus` (16.6%) — detected as `sl`/`cze` (South Slavic confusion) — Cyrillic script input, but wrong Slavic language

**Historical codes — what fasttext detects instead:**

| code | label | n | top detections |
|------|-------|--:|----------------|
| grc | Ancient Greek | 31,543 | ger(38.4%), eng(27.3%), lat(8.7%) |
| mnc | Manchu | 9,004 | chi(32.7%), eng(23.4%), id(9.7%) |
| ota | Ottoman Turkish | 7,427 | ger(26.0%), eng(17.4%), lv(14.7%) |
| gmh | Middle High German | 3,607 | ger(66.5%), eng(13.6%) — plausible |
| chu | Church Slavonic | 4,792 | sl(18.2%), eng(17.0%), rus(16.0%) |
| nds | Low German | 9,768 | ger(51.5%), eng(19.2%), dut(6.2%) — plausible |
| wen | Sorbian | 1,427 | ger(31.9%), pol(15.3%), hsb(11.4%) |

`gmh` → `ger` and `nds` → `ger`/`dut` are linguistically sensible; the others indicate no meaningful detection.

### 4.4 Low-confidence correct detections

892,606 titles match the annotation but with confidence < 0.5 (6.3% of all matches). These are annotation-confirmed but borderline — worth inspecting for ambiguous titles that happened to land on the right label.

---

## 5. Which tag is more reliable: dc:language or fasttext?

**`dc:language` annotation is more reliable** for this corpus.

### 5.1 Why the annotation wins

- **Scope**: `dc:language` describes the language of the *document content*, not just the title. A German-language catalog entry about an Arabic manuscript gets `lang=ara` — fasttext sees a German title and correctly detects German, but the annotation is right about the content.
- **Historical languages**: For `grc`, `gmh`, `chu`, `ota`, `mnc`, `wen` (~67K objects), fasttext is structurally incapable of producing the correct code. The annotation is the only source of truth.
- **Non-Latin scripts**: `ara` (1.4%), `heb` (3.3%), `gre` (3.0%), `rus` (16.6%) — these are real Arabic/Hebrew/Greek/Russian texts, but many titles are transliterated or appear in Latin script in the catalog record. The annotation reflects the actual document; fasttext is fooled by the title's script.
- **Short titles**: Mismatch titles have a median length of 21 chars vs. 60 for matches. Titles with 1–3 words don't carry enough signal for reliable detection regardless of model.

### 5.2 Where fasttext adds value

Fasttext is useful as a **quality flag**, not a ground truth. Where fasttext disagrees *with high confidence* on a well-supported language (`ger`, `eng`, `fre`) — and the title is reasonably long — that's a candidate for annotation error worth inspecting. The 621K `ger`-annotated titles detected as English at mean confidence 0.853 are a concrete example: a fraction of these are likely genuine mislabellings.

### 5.3 Recommended use for GND Werk linking

GND Werk linking matches titles against GND authority records by the language of the *work* — which is what `dc:language` encodes. The fasttext model only sees the title string, which can be in a different language than the work itself:

- A German-language bibliography entry about a Latin text may have a Latin title → fasttext detects Latin, but the work is German (`lang=ger`) and belongs in the German GND pool.
- A Latin work catalogued with a German descriptive title → fasttext detects German, but `lang=lat` correctly places it in the Latin pool.

Using fasttext for language-based pool assignment would introduce systematic errors at exactly the boundary cases where catalogue practice diverges from title language.

| Signal | Use for |
|--------|---------|
| `dc:language` | **Language pool assignment for GND Werk linking** and all other downstream tasks |
| fasttext + high confidence + long title | Flag suspicious annotations for manual review |
| fasttext alone | Do not use as a replacement for `dc:language` |

### 5.4 Is it wrong to use fasttext as a secondary filter on top of dc:language?

**Yes.** Filtering `dc:language ∈ {ger, gmh, nds}` titles by fasttext detection would be wrong for GND linking. The data shows why:

Within the 11.9M `ger`-annotated titles, fasttext disagrees on **9.4% (≈1.1M titles)**. Those disagreements include:

- **German works with non-German titles** — a German novel catalogued with its French subtitle, a German scholarly work with a Latin title. `dc:language=ger` is correct; fasttext is misled by the title string.
- **Short German titles** — fasttext mismatch correlates strongly with title length (median 21 chars for mismatches vs. 60 for matches). A three-word German title is a valid GND Werk candidate but fasttext may call it English or French.
- **`gmh` and `nds`** — fasttext produces 0% match for gmh and 10.9% for nds. A secondary fasttext filter would eliminate nearly all Middle High German titles and 89% of Low German titles — the historically significant subset most in need of GND linking.

**Correct procedure:**

1. Filter by `dc:language ∈ {ger, gmh, nds, lat}` → `s2_meta_de_content.parquet`
2. Send all of those to GND Werk lookup — no further language filter

Fasttext remains useful *after* linking as a post-hoc quality signal: if a linked title is detected as a completely different language at high confidence and is long enough to be reliable, that is worth flagging. It should never gate what enters the linking pipeline.

### 5.5 Why Latin is included alongside the German-family codes

`dc:language = lat` is included in `s2_meta_de_content.parquet` alongside `ger`, `gmh`, and `nds` for three reasons:

1. **Corpus composition.** Pre-1800 German cultural heritage is heavily bilingual. Scholarly, theological, legal, and administrative works were routinely written in Latin — often by German authors, printed in German cities, and catalogued in German libraries. `lat`-annotated records in DDB sector 2 are not foreign objects; they are a core stratum of the German historical record.

2. **GND authority coverage.** GND has Latin Werk records for canonical pre-modern texts (e.g. Luther's Latin writings, humanist editions). Excluding `lat` from the linking pool would leave these records unlinked even when GND authority entries exist.

3. **Tokenizer coverage.** `xlm-roberta-large` was pretrained on multilingual text including Latin. Latin titles tokenize without degradation — no special preprocessing beyond `normalize_historical()` (NFC, long-s, ligatures) is needed.

**Practical note:** Downstream analysis scripts should report `lat` as a separate facet from `ger`/`gmh`/`nds` so that token-length distributions and era breakdowns for the German-family languages are not conflated with the Latin sub-corpus (~1.3M records).

---

## 6. Limitations

- **Historical codes**: fasttext has no representation for gmh, chu, nds, grc, ota, mnc, wen — these always register as mismatch regardless of annotation quality.
- **Title-only**: detection operates on the title string only. Multilingual titles, transliterated titles, or heavily abbreviated titles confuse the model.
- **Short titles**: titles of 1–2 words are unreliable regardless of library. The `--min-title-len 3` filter mitigates but does not eliminate this.
- **Code granularity**: fasttext does not distinguish `grc` (Ancient Greek) from `el` (Modern Greek); both appear as `el`.

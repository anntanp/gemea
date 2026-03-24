# GeMeA — Gold Set Annotation Guide (SR-08)

Companion to [sr08_gold-set-composition.md](sr08_gold-set-composition.md).

---

## 1. Labels

### 1.1 Phase 1 — annotate for every record

| Label | What to mark | Typical cue |
|---|---|---|
| `TITLE` | Main work title | Opening content string; before ` :` or ` /` in modern records |
| `OTHER_TITLE` | Subtitle or alternative title | After `Das ist:`, `oder`, ` :`, `nämlich`, `welches handelt von` |
| `PERSON` | Author / editor — full name **plus** any credentials and role phrases that form a single naming unit | After ` /` in modern records; **opening span** in pre-1700 records |

### 1.2 Phase 2 — annotate in the same pass (not evaluated yet)

| Label | What to mark | Trigger |
|---|---|---|
| `TRANSLATOR` | Translator | Only when a keyword is present: `übersetzt`, `Übers.`, `transl.`, `traduit` |
| `PARALLEL_TITLE` | Title in a second language | After ` =` |
| `MEDIUM` | Instrumentation / medium for music | `für Klavier und Violine`, `für gemischten Chor` |

---

## 2. Workflow

The sampling and pre-fill scripts produce three files:

| File | Contents | Your action |
|---|---|---|
| `data/annotation/sr08_gold_prefilled.jsonl` | All 395 records; pre-filled spans where possible | Import into annotation tool (or edit directly) |
| `data/annotation/sr08_manual_queue.csv` | 212 records flagged `manual`, sorted pre-1700 first | Work through this list first |
| `data/annotation/sr08_gold_sample.csv` | Original sample with metadata | Reference only |

### 2.1 Annotation status

Each record in the JSONL has an `annotation_status` field:

| Status | Count | Meaning |
|---|---|---|
| `pre-filled` | 47 | Tier-2 (structural `. -`), non-pre-1700 — high confidence; review and accept or correct |
| `partial` | 136 | Tier-1 (heuristic), non-pre-1700 — verify each span before accepting |
| `manual` | 212 | Pre-1700 or tier-0 — annotate from scratch |

### 2.2 Suggested order

1. **Pre-1700 tier-0** (~130 records) — the records the evaluation rests on; follow §3 carefully
2. **1700-1800 tier-0** (37 records) — transitional register; may be either author-before-title or modern structure
3. **Modern/19th-c tier-0** (45 records) — no ISBD markers but modern structure; usually short
4. **Partial tier-1** (136 records) — review auto-extracted spans, correct boundaries
5. **Pre-filled tier-2** (47 records) — spot-check; most are correct

---

## 3. Pre-1700 annotation rules

### 3.1 Author-before-title structure

In pre-1700 titles the author's credentials appear **before** the main title — there is no ` /` separator. The pattern is:

```
[credential + name + role | PERSON] [main title | TITLE] [subtitle | OTHER_TITLE]
```

Example:
```
Input:  "D. Johann Gerhard, Professoris zu Jena, Erklärung der Historien des Leidens"
Output: [D. Johann Gerhard, Professoris zu Jena | PERSON]
        [Erklärung der Historien des Leidens | TITLE]
```

### 3.2 PERSON span boundaries

**Include in the PERSON span:**
- Degree abbreviations immediately before the name: `D.` (Doktor), `M.` (Magister), `Lic.`, `Mag.`
- Full personal name (first name + surname)
- Role or position phrases: `Pfarrers zu X`, `der H. Schrifft Lehrers`, `Professoris`, `Pastoris`
- Genitive / prepositional post identifiers: `zu Jena`, `in Leipzig`, `bey der Gemeine zu X`

**Stop the PERSON span** at the first token that is clearly part of the work title (a content noun, verb phrase, or `Das ist:`).

### 3.3 Common errors

| Error | Wrong | Correct |
|---|---|---|
| Credential sequence labelled as TITLE | `D. Johann Gerhard, Professoris zu Jena` → TITLE | PERSON |
| Degree abbreviation excluded from span | `Johann Gerhard` → PERSON | `D. Johann Gerhard, ...` → PERSON |
| Dedicatee labelled as PERSON when not the author | `Herrn N.N. gewidmet` → PERSON | Not labelled |
| Embedded Latin treated as separate entity | `Anno MDXLVI` → TITLE | Part of the enclosing TITLE span |
| `durch` / `von` phrase labelled TRANSLATOR | `durch Johann Schmidt` → TRANSLATOR | PERSON (no translation keyword present) |

---

## 4. Modern records — watch for surname-first

Modern DDB catalog records frequently open with the author's surname in citation form before the actual title:

```
"Mayer, Anton L., Die Liturgie in der europäischen Geistesgeschichte / ..."
```

The pre-fill script extracts everything before ` /` as `TITLE`. You must split this:

```
[Mayer, Anton L. | PERSON] [Die Liturgie in der europäischen Geistesgeschichte | TITLE]
```

The boundary is at the first comma-separated full name — once the title string clearly shifts to a noun phrase, that is where TITLE begins. There is no fixed separator in this pattern; use semantic judgement.

---

## 5. Span format (output JSONL)

Each record in `sr08_gold_prefilled.jsonl` has this structure:

```json
{
  "obj_id":       "ABCDE12345FGHIJ",
  "title":        "D. Johann Gerhard, Professoris zu Jena, ...",
  "dates":        "1662",
  "dc_type":      "Leichenpredigt|Monografie",
  "silver_tier":  "0",
  "era":          "pre-1700",
  "ddb_link":     "https://www.deutsche-digitale-bibliothek.de/item/ABCDE12345FGHIJ",
  "spans": [
    {"start": 0,  "end": 38, "label": "PERSON", "text": "D. Johann Gerhard, Professoris zu Jena"},
    {"start": 40, "end": 82, "label": "TITLE",  "text": "Erklärung der Historien des Leidens"}
  ],
  "annotation_status": "manual",
  "annotator":    "your-name",
  "annotation_date": "2026-XX-XX",
  "notes":        ""
}
```

- `start` / `end` are **character offsets** into the `title` string (0-indexed, end exclusive)
- Spans must be non-overlapping and contiguous substrings of `title`
- Fill in `annotator` and `annotation_date` when you complete a record
- Use `notes` for ambiguous cases

---

## 6. Verification script

After annotating a batch, run:

```bash
python3 scripts/sr08_verify_spans.py
```

This checks that all character offsets are consistent and prints sample records for review.

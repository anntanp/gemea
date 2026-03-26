# SR-08 — TITLE Boundary Curation for Exact Span Match

Companion to [sr08_annotation-guide.md](sr08_annotation-guide.md) and [sr08_evaluation-design.md](sr08_evaluation-design.md).

**Purpose:** Exact span match is unforgiving — a prediction is wrong if it is off by even one character. Consistent TITLE boundaries across annotators are therefore a prerequisite for meaningful evaluation. This note documents the curation decisions that define where the TITLE span begins and ends in each structural case. Every case here represents a real ambiguity encountered in the corpus.

---

## 1. Why boundary consistency matters for exact span match

Evaluation uses exact character-offset + label match (HIPE-2022 strict regime). A model prediction that extracts the correct words but includes one extra leading article, one trailing comma, or one whitespace character scores as a false positive and false negative simultaneously — the same penalty as getting the wrong span entirely.

If two annotators make different but individually reasonable boundary decisions (e.g., one includes a leading article, one does not), the gold set contains noise that the model cannot resolve: whatever it predicts, it will be penalised on some gold records. This inflates false positives and depresses F1 independently of model quality.

The rules below must be applied uniformly. When a new ambiguous case is encountered during annotation, it should be added here before annotating more records of that type.

---

## 2. General rules

| Rule | Decision |
|---|---|
| Leading and trailing whitespace | Never include in any span. `start` points to the first non-space character; `end` is one past the last non-space character. |
| Separating punctuation between spans | Not included in any span. The ` / `, ` : `, `, ` between TITLE and PERSON or OTHER_TITLE belongs to neither. |
| Truncation markers | ` …` and `...` at the end of a span are excluded. Stop the span before the space preceding the ellipsis. |
| Verification | `title[start:end] == text` must hold exactly. Run `sr08_verify_spans.py` after every batch. |

---

## 3. TITLE start boundary

### 3.1 Leading articles

**Decision: include.**

German definite and indefinite articles (`Der`, `Die`, `Das`, `Ein`, `Eine`) that open the title are part of the TITLE span. The article is lexically fused with the title phrase — stripping it would require title-normalisation logic that is not part of the annotation task and would produce boundaries inconsistent with how GND work records store titles.

> `Die Leiden des jungen Werthers` → TITLE start = `D` of `Die`

### 3.2 Cataloger-added date prefix

**Decision: exclude; TITLE starts after the prefix.**

Some catalog entries prepend a year or date designator before the actual title, separated by `: ` or a space:

> `1988: Statistische Berichte der Freien und Hansestadt Hamburg`

The `1988:` prefix is a cataloger's issue designator, not part of the work title. TITLE starts at the first substantive word after the prefix and its separator.

> TITLE: `Statistische Berichte der Freien und Hansestadt Hamburg` (start after `1988: `)

### 3.3 Pre-1700 — TITLE starts after PERSON span

In author-before-title records, the TITLE span begins at the first substantive noun phrase that names the work. The boundary is the first character after the separating punctuation (typically `, `) that follows the PERSON span.

> `David Beuthers, … Philosophi Adepti, Zwey rare Chymische Tractate`
>
> PERSON ends at `i` of `Adepti`; TITLE starts at `Z` of `Zwey`.
> The `, ` between them is in neither span.

When no separator is present (name runs directly into title), use the last role-noun or location phrase as the PERSON endpoint and the first title noun as the TITLE start. If the boundary is genuinely unresolvable, annotate the full string as TITLE and record a note.

### 3.4 `Von` attribution mid-string

**Decision: TITLE ends before `Von`; PERSON starts after `Von `.**

> `Handbuch des römischen Privatrechts … Von Theodor Schmalz, D. …`
>
> TITLE: `Handbuch des römischen Privatrechts` (end before ` …`)
> PERSON: `Theodor Schmalz, D. …` (start after `Von `)

`Von` itself is the attribution keyword and is excluded from both spans.

---

## 4. TITLE end boundary

### 4.1 Subtitle separator ` :`

**Decision: TITLE ends before ` :`; the space before the colon is not included.**

> `Jeversches Wochenblatt : Friesisches Tageblatt`
>
> TITLE: `Jeversches Wochenblatt` (end = position of the space before `:`)

The ` :` separator and the space following it belong to neither TITLE nor OTHER_TITLE.

**Exception — life-date colon:** when ` :` follows a person's name and is immediately followed by a date or date range (`7. Januar 1787`, `1734–1805`), it is a life-date delimiter, not a subtitle separator. The full name is TITLE; what follows is not OTHER_TITLE. See §5.6 of the annotation guide.

### 4.2 SoR separator ` /`

**Decision: TITLE ends before ` /`.**

> `Jahrbuch / Deutsche Shakespeare-Gesellschaft`
>
> TITLE: `Jahrbuch` (end before ` /`)

The ` /` and trailing space belong to neither span.

**Exception — series letter suffix:** when ` /` is followed by a single letter or short code (`/ K`, `/ M`, `/ A1`), it is a series designator, not a SoR separator. Do not label either part; TITLE covers the substantive title phrase before ` /`.

### 4.3 Trailing ISBD area separator `. -`

**Decision: TITLE does not include `. -` or any trailing punctuation that is part of the ISBD record structure.**

Stop the TITLE span at the last character of the title phrase, before any `. -`, trailing `,`, or `;` that introduces additional fields.

> `Geschichte der deutschen Literatur. - 2. Aufl.`
>
> TITLE: `Geschichte der deutschen Literatur`

### 4.4 Parenthetical additions

Two cases:

| Case | Decision |
|---|---|
| Life dates identifying the depicted subject: `(1734 - 1805)` | **Include in TITLE.** They are part of the identifying phrase. |
| Cataloger's genre notes: `(Roman)`, `(Erzählung)`, `[Katalog]`, `[Entwurf]` | **Exclude.** Stop TITLE before the parenthesis. |

Distinguishing criterion: if removing the parenthetical would change *which work* is identified, include it. If it only adds a genre or format note that the cataloger appended, exclude it.

> `Porträt Georg Philipp Wucherer (1734 - 1805)` → include `(1734 - 1805)` — it identifies which portrait
>
> `Faust (Drama)` → TITLE = `Faust`, exclude `(Drama)` — it is a genre note

### 4.5 Ordinal or volume number at the start of the title

**Decision: include if it is part of the title phrase; exclude if it is a cataloger-prepended volume designator.**

> `3. Rechenschaftsbericht der Deutschen Volkspartei` → TITLE includes `3.` — it is integral to the work title
>
> `Bd. 3: Systematischer Teil` → `Bd. 3` is a volume designator; TITLE = `Systematischer Teil` starting after `: `

Criterion: if the number is followed by a substantive noun that would also stand as a title without the number, treat the number as a volume designator and exclude it. If the number is part of the work's identity (e.g., a numbered report or installment), include it.

### 4.6 Truncated strings

**Decision: exclude the truncation marker; TITLE ends at the last substantive word before ` …`.**

> `Handbuch des römischen Privatrechts …` → TITLE = `Handbuch des römischen Privatrechts`

---

## 5. Cases requiring inter-annotator discussion before proceeding

The following structural patterns have not yet been fully resolved. Do not annotate records of these types without first agreeing on a rule and recording it here.

| Pattern | Open question |
|---|---|
| Pre-1700 title with no separator between long credential and title proper | Where exactly does credential end? Use last role-noun heuristic or flag for discussion. |
| DDB `::` separator mid-string | Whether what follows is OTHER_TITLE or a second catalog field — current decision is to not label it (see §5.5 annotation guide); confirm this holds for all cases. |
| Title string is entirely a Leichenpredigt opening formula with no named work | Whether to annotate the formulaic phrase as TITLE or leave the full string as TITLE — current decision: full string as TITLE. |
| Multi-language title with no `=` or ` / ` separator | Whether the second-language portion is PARALLEL_TITLE or part of TITLE — requires case-by-case judgement; record in `notes` field. |

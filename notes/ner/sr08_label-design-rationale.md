# GeMeA — NER Label Design Rationale (SR-08)

Companion to [sr08_annotation-guide.md](sr08_annotation-guide.md).
Records the reasoning behind label name choices, for paper justification and future annotator training.

---

## 1. Governing principle

All Phase 1 and Phase 2 label names map to **ISBD field designations**, not to interpretations of content or role. This has two advantages: (1) annotators can apply the label based on structural position in the string rather than semantic judgment; (2) the labels align with the bibliographic metadata standard that produced the corpus, making downstream linking to MARC and RDA records unambiguous.

---

## 2. PERSON — not AUTHOR or CREATOR

### 2.1 The SoR position covers multiple agent types

The ISBD Statement of Responsibility (SoR) position — introduced by ` / ` — contains not just authors but also editors (`hrsg. von`), compilers, corporate bodies, and contributors. `AUTHOR` is semantically wrong for:

- `Jahrbuch / Deutsche Shakespeare-Gesellschaft` — the responsible agent is a corporate body, not an author
- `Statistische Berichte / Hessisches Statistisches Landesamt` — a government agency issuing statistical reports

`CREATOR` is closer but still excludes editors and corporate agents. `PERSON` is the neutral term that marks *where the responsible agent appears in the string* without asserting a role.

### 2.2 SR-04 confirmed role heterogeneity

SR-04 validated 100 `f_person` records and found:

| Class | Share |
|---|---|
| True author SoR | 35% |
| Non-SoR false positives | 41% |
| Corporate body | 19% |
| Editor | 5% |

Training a model on `AUTHOR` spans that are 65% non-authors would produce a noisily labeled training set. `PERSON` defers role assignment to a downstream classification step using the SR-04 `f_resp_*` flags (`f_resp_person`, `f_resp_org`, `f_resp_editor`, `f_resp_other`), without requiring re-annotation of spans.

### 2.3 Precedent in historical NER benchmarks

HIPE-2022 and GermEval 2014 use `PER` (person) rather than role-bearing labels for the same reason: string evidence rarely disambiguates author from editor from corporate body reliably enough to justify a role label at annotation time (Ehrmann et al., 2022; Benikova et al., 2014).

### 2.4 PERSON_DESIGNATION deferred to Phase 2

A `PERSON_DESIGNATION` label splitting the bare name from the credential phrase was considered and deferred. See [sr08_annotation-guide.md §5.8](sr08_annotation-guide.md#58-pre-1700----author-before-title-alchemical-treatise) for the full design note.

---

## 3. OTHER_TITLE — not ALTERNATIVE_TITLE

### 3.1 ISBD source

`OTHER_TITLE` maps directly to the ISBD field designation **"other title information"** (ISBD §1.3), which covers all titles subordinate to the title proper that appear after the ` : ` separator — subtitles, explanatory phrases, catchphrases, and format descriptions. The MARC 21 encoding is Field 245 `$b` (Remainder of title).

### 3.2 "Alternative title" has a different, specific ISBD meaning

ISBD §1.1.3 defines *alternative title* narrowly as the second part of a compound title joined by the word "or" (or its equivalent in another language):

> *The Tempest, or, The Enchanted Island*

This is a title that names the same work in two ways within the title proper — not a subtitle subordinate to it. `ALTERNATIVE_TITLE` as a label would therefore be semantically incorrect for the subtitle use case and would conflict with the ISBD definition.

### 3.3 Schema conflict with PARALLEL_TITLE

`ALTERNATIVE_TITLE` would also create overlap with `PARALLEL_TITLE` (Phase 2), which covers titles in a second language — the closest thing to an "alternative" in everyday use. Having both in the schema would require annotators to make a distinction not supported by the string evidence alone. `OTHER_TITLE` avoids this by staying faithful to the ISBD field boundary: it means "whatever ISBD places after ` : `."

---

## 4. PARALLEL_TITLE — not FOREIGN_TITLE

### 4.1 ISBD source

`PARALLEL_TITLE` maps directly to the ISBD field designation **"parallel title"** (ISBD §1.4): the title proper restated in another language *or script* on the same title page, introduced by ` = `.

### 4.2 "Parallel" is a structural property, not a language property

A parallel title is a restatement of the same work's title at the same hierarchical level — not merely any non-German string. `FOREIGN_TITLE` would mischaracterize the label in two directions:

- **False positives:** A Latin subtitle, an English series description, or a French dedication phrase are not parallel titles. They are other things that happen to be in a foreign language. `FOREIGN_TITLE` would require labeling them; `PARALLEL_TITLE` does not.
- **False negatives:** A German work with an Austrian-German parallel title (`Handbuch der Chemie = Leitfaden der Chemie`) has two German titles — neither is "foreign" — yet the second is a `PARALLEL_TITLE` by ISBD definition.

### 4.3 Annotation consequence

The trigger for labeling `PARALLEL_TITLE` is structural: appearance after ` = ` or after ` / ` when the following string is a title-form restatement of the title proper. A `FOREIGN_TITLE` label would require a language judgment first — a harder, separate decision. `PARALLEL_TITLE` keeps the annotation criterion purely structural, consistent with the decision flowchart in [sr08_annotation-guide.md §4](sr08_annotation-guide.md#4-decision-flowchart).

---

## 5. References

- Benikova, D., Biemann, C., Kisselew, M., & Padó, S. (2014). GermEval 2014 Named Entity Recognition Shared Task: Companion Paper. *Proceedings of the KONVENS GermEval Shared Task on Named Entity Recognition*, 104–112.
- Ehrmann, M., et al. (2022). HIPE-2022: Naming the past. *CLEF 2022 Working Notes*, CEUR-WS vol. 3180.
- IFLA. (2011). *ISBD: International Standard Bibliographic Description* (Consolidated ed.). De Gruyter Saur. — §1.1.3 (alternative title), §1.3 (other title information), §1.4 (parallel title).
- IFLA Study Group on FRBR. (2009). *Functional Requirements for Bibliographic Records: Final Report* (rev. ed.). IFLA. https://repository.ifla.org/handle/123456789/811
- Library of Congress. (2019). *MARC 21 Format for Bibliographic Data*, Field 245. https://www.loc.gov/marc/bibliographic/bd245.html

# Paper Idea — TPDL: Linking DDB Titles to GND Works

**Venue:** International Conference on Theory and Practice of Digital Libraries (TPDL)
**Typical deadline:** ~April–May; conference ~September
**Format:** Full paper 12–15 pp. LNCS or short paper 6–8 pp.
**Status:** Idea — not started

---

## Pitch

65 million objects in the Deutsche Digitale Bibliothek carry raw `dc:title` strings in ISBD punctuation format. We describe a pipeline to extract clean titles from these strings — using a rule-based ISBD parser and a zero-shot NER model — and link them to GND Werktitel authority records via a public SPARQL endpoint. A key contribution is the silver-labeled NER training corpus, automatically derived from the ISBD-parsed subset, which we release as the first large-scale German bibliographic NER dataset. We report linking coverage and precision across title types and extraction methods, and quantify how much GND authority enrichment changes downstream retrieval quality in the GeMeA knowledge graph.

---

## Core contributions

1. **Silver NER dataset** — automatically labeled from 4.5M DDB titles (DF_DE_TITLES) using the ISBD parser as a distant supervisor. First large-scale German bibliographic NER dataset with `TITLE`, `PERSON`, `PUBLISHER`, `YEAR`, `EDITION` labels. Released publicly.

2. **Entity linking pipeline** — ISBD rule-based extraction + NuNER Zero zero-shot NER fallback → QLever SPARQL lookup against the DNB GND endpoint (`https://sparql.dnb.de/api/dnbgnd`) with three-tier match scoring (exact / normalized / fuzzy). Deduplication reduces 65M lookups to ~5–10M unique pairs.

3. **Evaluation at scale** — linking coverage and precision reported by extraction method (ISBD vs. NER), title language (modern German / historical German / Latin), and match type. Manual gold set of ~500 records stratified by era.

4. **Downstream impact** — before/after comparison in GeMeA: how many ProvidedCHOs gain a `mocho:Work` parent; change in WEMI grouping depth; effect on `/work/{id}` page coverage.

---

## Research questions

1. What fraction of DDB `dc:title` strings can be resolved to a GND Werktitel, and how does that vary by extraction method?
2. How clean are silver labels derived from ISBD parsing? Can they train a NER model that generalizes to the non-ISBD majority (71%)?
3. How does NuNER Zero zero-shot NER compare to an ISBD-fine-tuned model on bibliographic title extraction?
4. What proportion of historical German and Latin titles remain unresolved, and why?

---

## Paper structure (sketch)

1. **Introduction** — scale of the DDB, motivation for GND Werk linking, gap: no existing pipeline or labeled data
2. **Background** — GND authority data, ISBD punctuation conventions, GeMeA architecture (brief)
3. **Dataset: DF_DE_TITLES** — 4.47M titles, ISBD coverage analysis (28.4% excl. trailing period), pattern breakdown (`:` 20.3%, `/` 0.8%, etc.); source: `ner/sr01_isbd-title-analysis.md`
4. **Title extraction**
   - Rule-based ISBD parser (primary; 28.4% coverage)
   - Silver labeling procedure (ISBD → auto-annotation → dataset release)
   - NuNER Zero zero-shot NER (fallback; 71.6% of records)
   - Evaluation: gold set of 500 stratified records
5. **Entity linking via QLever GND**
   - Endpoint and query design (Pattern A/B/C; `contains-word`; `gndo:firstAuthor` cross-reference)
   - Distinctive token selection for `contains-word`
   - Post-retrieval scoring: exact / normalized / fuzzy; predicate assignment (`owl:sameAs` / `skos:closeMatch`)
   - Deduplication strategy (65M → 5–10M unique pairs)
6. **Results**
   - Linking coverage by extraction method and title language
   - Precision sample (100 manually checked linked pairs)
   - Work grouping size distribution
   - Downstream GeMeA impact
7. **Discussion** — failure modes, historical/Latin titles, ambiguous titles without author URI
8. **Conclusion and dataset release**

---

## Design decisions

### `skos:exactMatch` over `owl:sameAs` for confirmed links

The linking pipeline uses `skos:exactMatch` (exact and normalized matches) and `skos:closeMatch` (fuzzy matches) rather than `owl:sameAs`. The choice is worth one sentence in the paper because reviewers from a Semantic Web background will ask.

**The argument:** `owl:sameAs` asserts that two URIs denote the same individual — any triple true of one is entailed true of the other under OWL semantics. A DDB ProvidedCHO and a GND Werk URI are not the same individual: the CHO is a catalog record for a physical manifestation; the Werk URI is an authority record for an abstract work. Asserting `owl:sameAs` between them would be ontologically incorrect and would propagate unintended inferences through any reasoner that consumes the data.

`skos:exactMatch` asserts that two concepts "can be used interchangeably for all retrieval purposes" (Miles & Bechhofer, *SKOS Reference*, W3C 2009, §10) — appropriate for confirmed title-to-Werk links without the OWL identity burden. `skos:closeMatch` handles fuzzy matches where interchangeability holds only in some retrieval contexts.

Supporting citation: Halpin et al. (*When owl:sameAs Isn't the Same*, ISWC 2010) document systematic misuse of `owl:sameAs` in linked data for approximate and cross-type identity, and recommend SKOS mapping properties as the correct alternative.

---

## Key numbers to report (from existing analysis)

| Metric | Value | Source |
|---|---|---|
| Total DDB objects | ~65M | GeMeA project |
| DF_DE_TITLES rows | 4,477,780 | `ner/sr01_isbd-title-analysis.md` |
| ISBD coverage (excl. trailing `.`) | 28.4% | `ner/sr01_isbd-title-analysis.md` |
| NER fallback scope | ~71.6% | `ner/sr01_isbd-title-analysis.md` |
| ` :` pattern (most reliable ISBD signal) | 20.3% | `ner/sr01_isbd-title-analysis.md` |
| ` /` pattern (SoR split) | 0.8% | `ner/sr01_isbd-title-analysis.md` |
| Unique title pairs (estimated) | 5–10M | `gnd-title-extraction.md` |
| Target Werk linking rate | ≥70% | `gnd-title-extraction.md` |

---

## Differentiators from the ISWC GeMeA paper

| | ISWC GeMeA paper | This TPDL paper |
|---|---|---|
| Focus | Full KG architecture (GeMeA system) | Title extraction + GND linking methodology |
| Audience | Semantic Web / KG | Digital libraries / information science |
| Contribution | System + resource | Dataset + pipeline + evaluation |
| NER detail | Brief (one paragraph) | Central (§4) |
| Linking evaluation | Quality metrics for paper §4 | Core results (§6) |
| Dataset release | Not planned | Yes — silver NER corpus |

The two papers cite each other but are self-contained. This paper feeds the GeMeA pipeline; ISWC describes the broader system.

---

## Related work hooks

- Bibliographic entity linking: VIAF, OCLC WorldCat reconciliation
- German NER: GermEval 2014, CLEF-HIPE-2020, HIPE-2022 (ajmc)
- Zero-shot NER: NuNER Zero (NuMind 2024), GLiNER (NAACL 2024)
- ISBD parsing: no prior automated approach at this scale (gap to claim)
- Silver labeling via distant supervision: Mintz et al. 2009 (standard citation)
- QLever for large-scale SPARQL: Bast et al. (university of Freiburg)

---

## Open questions before committing

- [ ] Does TPDL accept dataset/resource papers, or must the focus be a methodology paper? Check recent proceedings.
- [ ] Is the silver corpus large enough to be a standalone contribution, or does it need NuNER Zero evaluation results first?
- [ ] Overlap with ISWC GeMeA paper: are §4 quality metrics in the ISWC paper sufficient to preclude a standalone TPDL paper, or is the NER + linking detail clearly outside ISWC scope?
- [ ] Do we have the DF_DE_TITLES for the full DDB corpus, or only the 4.47M German content subset? Coverage numbers change significantly.

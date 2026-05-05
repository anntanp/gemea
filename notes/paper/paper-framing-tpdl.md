---
title: TPDL 2026 Paper Framing
date: 2026-05-04
context: Two repackaging candidates from babel-ddb / mocho / goethe-faust / gemea for TPDL 2026
---

# TPDL 2026 — Paper Framing

## 0. Deadlines and contribution types

| Milestone | Date |
|---|---|
| Abstract | **7 May 2026** (3 days) |
| Full paper | 13 May 2026 (9 days) |
| Notification | 29 June 2026 |
| Camera-ready | 19 July 2026 |

**Contribution types**:
- Full paper: 15 pp + refs → LNCS
- Short / Late Breaking: 8 pp + refs → CCIS
- Demo: 8 pp + refs → CCIS (presented in demo session)

**Venue fit**: TPDL is a digital libraries / LAM conference. Unlike ISWC, reviewers value practical metadata standards work, LAM community relevance, and reproducible pipelines — not novel algorithms. This plays strongly in favor of both framings below.

---

## 1. Framing A — Data-driven harmonization of heterogeneous cultural heritage metadata

**Working title**: *Corpus-driven Alignment of Heterogeneous EDM Metadata to Domain Ontologies: A Case Study on 115K DDB Records*

**One-sentence hook**: When seven institutional sectors use the same EDM property (`dc:type`) with incompatible semantics, schema-level alignment fails; a corpus-profiling methodology recovers sector-specific conventions and maps them to RDA, RiC-O, and VRA Core at scale.

### 1.1 Core argument

The DDB-EDM profile is a structural wrapper, not a semantic contract: `dc:type` carries controlled-vocabulary terms in libraries, free-text strings in museums, and structural hierarchy identifiers in archives. No ontology-to-ontology alignment tool can recover these conventions from the schema alone. The methodology contribution is: **profile corpus before modelling, not after**.

Three-layer dispatch architecture (Layer 1: property alignment; Layer 2: htype → RiC-O/DoCO class; Layer 3: dc:type × sector × mediatype → WEMI-slot class) operationalises this and produces 44.4M triples from 115,432 records with quantified coverage at each dispatch level.

### 1.2 Source material to repackage

| Source | What to take |
|---|---|
| babel-ddb paper | §Alignment rationale, motivation for hub ontology, `owl:unionOf` multi-typing pattern, sector heterogeneity framing |
| mocho notes | Architecture overview, WEMI-to-domain-ontology mapping design, import chain (RDA + RiC-O + Music Ontology + VRA Core + CIDOC-CRM) |
| goethe-faust `transform-writeup.md` | §1–§4 are already paper-ready (layers diagram, htype table, dc:type dispatch table, run stats) |
| goethe-faust `alignment_ddbedm_mocho.csv` | Quantitative coverage table (field × match\_method × WEMI level) |
| mocho `alignment-ddbedm-mocho-spec.md` | Known gaps table, success criteria |

### 1.3 TPDL topic fit

- **Data Integration and Harmonization, Metadata Standards** (primary)
- **Knowledge Organization: Knowledge Graphs, Ontologies, Thesauri** (secondary)
- **Digital Cultural Heritage** (domain framing)
- **Linked Data and Open Data Platforms** (output format)

### 1.4 Contribution type recommendation

**Short paper (8 pp)** — the methodology is clear and the numbers are already computed; a full 15-page paper would require a user study or broader evaluation not currently available.

Alternatively: **Full paper (15 pp)** if a second corpus (e.g. the full 65M DDB records via gemea ingest stats) is included to show the methodology scales beyond the goethe-faust pilot.

### 1.5 Pros

- Nearly all content exists: `transform-writeup.md` §1–4 is essentially §2–3 of the paper.
- Run stats (44.4M triples, dc:type W/M-slot hit rates, fallback rates) are already computed and saved.
- babel-ddb provides the motivation and related work; no new literature review needed.
- Strong TPDL LAM fit: RDA, RiC-O, EDM are all core metadata standards the community knows.
- No evaluation results to generate — the methodology paper argument is: "here is what exists in the data, here is how we handled it, here is what came out."

### 1.6 Cons

- The goethe-faust corpus is a *search-result* sample (Goethe/Faust queries), not a representative DDB sample — a careful scope statement is needed to avoid overgeneralization claims.
- mocho is not yet publicly released (v1.0 pending) — availability claims must be scoped to the ontology source and pipeline scripts, not a published artefact.
- The three-layer dispatch is complex; reviewers unfamiliar with EDM may need significant background that competes with page budget.
- Overlap with babel-ddb (SemDH 2026) must be managed — TPDL version must foreground the *methodology* (data-driven profiling), not the ontology alignment decisions already described in babel-ddb.

### 1.7 Task list

- [ ] Write abstract (≤250 words) — basis: `transform-writeup.md` §Problem + §Run results; **due 7 May**
- [ ] Draft §1 Introduction — motivate corpus-driven alignment vs. schema alignment; 1 p
- [ ] Draft §2 Background — DDB-EDM, WEMI, hub ontology pattern; 1.5 p; reuse babel-ddb §§1–2
- [ ] Draft §3 Methodology — three-layer dispatch with Mermaid diagram (already in `transform-writeup.md`); 2 p
- [ ] Draft §4 Results — run stats table + per-layer coverage table from `transform_stats.json` + `alignment_ddbedm_mocho.csv`; 1.5 p
- [ ] Draft §5 Discussion — known gaps, scope limits, reproducibility; 1 p; reuse `alignment-ddbedm-mocho-spec.md` §Known gaps
- [ ] Draft §6 Related Work — EDM alignment papers (DDB2FaBiO, Europeana data model literature); 0.5 p
- [ ] Draft §7 Conclusion; 0.5 p
- [ ] Confirm mocho availability statement (GitHub URL + license)
- [ ] Confirm goethe-faust corpus availability or note it is a private pilot dataset
- [ ] Convert to LNCS LaTeX (reuse `latex-springer-lncs/` setup from gemea paper)
- [ ] Submit via EasyChair

**Estimated writing effort**: 3–4 days for a short paper if reuse from existing notes is maximal.

---

## 2. Framing B — NER for historical bibliographic catalog strings

**Working title**: *Segmenting Historical Bibliographic Title Strings with ISBD-Guided Silver Labeling and Zero-Shot NER*

**One-sentence hook**: 71.6% of 4.48M German-language DDB catalog records lack ISBD punctuation signals, requiring an NER fallback; we show why standard NER models fail on this register and propose a silver-label pipeline that covers the remaining 28.4% as training data.

### 2.1 Core argument

Bibliographic catalog strings are a distinct register: structured by ISBD punctuation, not prose syntax, and historically variable in orthography (Early Modern German). General-purpose NER fails on three dimensions (wrong labels, wrong domain, historical register). The contribution is: (a) an ISBD-guided automatic silver labeling strategy for the 28.4% of records with structural signals, and (b) a zero-shot NER baseline (NuNER Zero) evaluated against a 395-record stratified gold set.

This is a **methodology + dataset** paper, not an end-to-end NER results paper. The claim is: *here is how to approach this task and why it is hard*, with preliminary results.

### 2.2 Source material to repackage

| Source | What to take |
|---|---|
| `gemea/notes/ner/spiel_ner.md` | §0–§8 map directly to paper sections; chain-of-thought outline is complete |
| `gemea/notes/ner/sr01_isbd-*` | ISBD field rating, applicability, title analysis — §2 Background |
| `gemea/notes/ner/sr05_*`, `sr06_*` | Noise sources, historical scope — §3.2 Challenges |
| `gemea/notes/ner/silver-dataset-pipeline.md` | Silver labeling methodology — §3.3 |
| `gemea/notes/ner/sr08_gold-set-composition.md`, `sr08_evaluation-design.md` | Gold set — §4 Evaluation Design |
| `gemea/notes/ner/sr09_nuner-tier2-sanity.md` | NuNER Zero baseline — §5 Baseline |
| `gemea/notes/ner/sr10_de-titles-distribution.md`, `fig_title_lengths.png` | Corpus statistics — §2 |

### 2.3 TPDL topic fit

- **NLP for Document Analysis** (primary)
- **Historical Document Analysis** (primary)
- **Entity Extraction and Semantic Linking** (secondary)
- **Multimodal and Multilingual Information Access** (multilingual/historical angle)
- **Digital Cultural Heritage** (domain)

### 2.4 Contribution type recommendation

**Short paper (8 pp)** — positions as a *Late Breaking Results* or *methodology* paper. Avoids the need for completed F1 evaluation to submit; presents silver pipeline + gold design + preliminary NuNER Zero results as the contribution.

If the gold annotation is completed before 13 May: full paper (15 pp) with per-stratum F1 results becomes viable.

### 2.5 Pros

- `spiel_ner.md` §0–§8 is a near-complete paper structure — sections map 1:1.
- All corpus statistics are already computed and saved as CSVs.
- The "why off-the-shelf NER fails" argument (§3 in spiel_ner) is original, documented, and the TPDL historical document analysis community will find it directly relevant.
- Historical German bibliographic records are a well-known pain point for the LAM community — this hits the TPDL audience precisely.
- No running system is required: the paper can be framed as methodology + dataset contribution with preliminary results.
- The scale (4.48M German-language records, 65M total DDB objects) is impressive for a TPDL venue.

### 2.6 Cons

- Gold annotation (395 records) may not be completed by 13 May — the paper weakens significantly without at least preliminary F1 results.
- NuNER Zero baseline results (sr09) need to be expanded from a sanity check to a formal evaluation section — this requires writing/running evaluation code.
- The ISBD silver pipeline is already described in gemea notes, but the actual Python code (`silver_labeler.py` or equivalent) must exist and be reproducible for submission.
- TPDL is not primarily an NLP venue — reviewers may lack background to evaluate NuNER Zero model selection; more motivation needed than for an ACL/EMNLP submission.
- GeMeA is the downstream use case, but GeMeA is not built — cannot claim end-to-end integration.

### 2.7 Task list

- [ ] Write abstract (≤250 words) — basis: `spiel_ner.md` chain-of-thought + §1 Scale; **due 7 May**
- [ ] Draft §1 Introduction — the 71.6% fallback framing; 1 p
- [ ] Draft §2 Corpus and task definition — DDB, German-language filter, ISBD structure, label set; 1.5 p; reuse `sr01_isbd-title-analysis.md` + `sr10_de-titles-distribution.md`
- [ ] Draft §3 Challenges — wrong labels / wrong domain / historical register; 1.5 p; reuse `spiel_ner.md` §3
- [ ] Draft §4 Silver labeling methodology — ISBD signal extraction, tier confidence; 1.5 p; reuse `silver-dataset-pipeline.md`
- [ ] Draft §5 Evaluation design — gold set (395 records, stratified by era + tier), exact span match, CI constraints; 1 p; reuse `sr08_*`
- [ ] Draft §6 Preliminary results — NuNER Zero zero-shot baseline; 1 p — **requires running formal eval**
- [ ] Draft §7 Related Work — HIPE-2022, historical NER, bibliographic NLP; 0.5 p
- [ ] Draft §8 Conclusion and future work; 0.5 p
- [ ] **Critical path**: run formal NuNER Zero evaluation on gold set (or a subset) to have numbers for §6
- [ ] Confirm silver dataset and gold set availability / license statement (CC BY 4.0 via DDB)
- [ ] Convert to LNCS LaTeX

**Estimated writing effort**: 4–5 days for a short paper; the critical-path blocker is the formal evaluation run (§6).

---

## 3. Comparison

| Criterion | Framing A (Harmonization) | Framing B (NER) |
|---|---|---|
| Content readiness | ~85% exists in notes | ~70% exists; §6 evaluation is the blocker |
| Writing effort | 3–4 days | 4–5 days + eval run |
| TPDL reviewer fit | Strong (metadata standards, LAM) | Good (historical doc analysis, NLP) |
| Novel contribution | Methodology + stats | Methodology + dataset + preliminary results |
| Risk | Scope/overlap with babel-ddb | Weak §6 without completed gold eval |
| Requires new code | No | Yes (formal eval script) |
| Requires new data | No | Possibly (gold annotation completion) |
| Competition | Low (few EDM harmonization papers at this scale) | Medium (historical NER is active) |

**Recommendation**: Submit **Framing A** as the primary target. It has the lowest execution risk given the 9-day window: the methodology and numbers exist, and the writing is primarily reorganization + pruning of existing notes. Prepare the abstract for both tracks by 7 May and decide based on how §6 of Framing B looks after a quick NuNER eval run.

---

## 4. What NOT to submit for TPDL

- **GeMeA as a system/demo paper** — the frontend is not built; a demo submission without a live system is not viable.
- **mocho as an ontology resource paper** — this fits ISWC (ontology track) better; mocho is also not publicly released yet.
- **Full GeMeA pipeline paper** — this is the ISWC 2026 Resource Track paper already in progress; submitting a version to TPDL risks dual-submission issues.

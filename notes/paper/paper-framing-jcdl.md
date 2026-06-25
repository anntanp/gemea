---
title: JCDL 2026 Paper Framing
date: 2026-05-20
context: Primary submission: Framing 2 (NER). TPDL cancelled — dual-submission constraints removed.
---

# JCDL 2026 — Paper Framing

## 0. Deadlines and contribution types

| Milestone | Date |
|---|---|
| Full and short paper submission | **30 June 2026** |
| Notification | 20 August 2026 |
| Camera-ready | 10 September 2026 |

**Contribution types**:
- Full paper: 10 pp + refs → ACM sigconf, double-blind
- Short paper: 4 pp + refs → ACM sigconf, double-blind

**Venue fit**: JCDL is ACM/IEEE, with a broader CS audience than TPDL. Reviewers expect empirical evaluation — run statistics alone do not constitute an evaluation at this venue. Strong fits from this work: "Metadata standards, linked data, semantic annotation, and interoperability in digital collections"; "NLP, information extraction, and semantic search"; "Knowledge graphs, semantic web, ontologies"; "Multilingual and multicultural digital libraries."

**Dual-submission check (mandatory before submitting)**:
- babel-ddb/SemDH 2026: submitted; no overlap in contribution if JCDL framings are evaluated, not design-focused
- GeMeA/ISWC 2026 Resource Track: if submitted, JCDL must not describe the same resource contribution; both framings below are distinct (methodology evaluation and NLP, respectively)
- TPDL 2026: submission cancelled — all TPDL-conditioned dual-submission constraints no longer apply

---

## 1. Framing 1 — Sector-aware corpus profiling for cultural heritage KG construction

**Working title**: *Profiles Before Predicates: A Corpus-Driven Pipeline for Aligning Heterogeneous Cultural Heritage Metadata to Domain Ontologies*

**One-sentence hook**: Because seven institutional sectors use the same EDM property (`dc:type`) with incompatible semantics, schema-level alignment systematically fails; a sector-stratified corpus profiling approach recovers per-sector conventions and maps them to WEMI-typed domain ontology classes, producing 44.4M triples from 115K records with quantified coverage — and scales to 65M objects in the full DDB pipeline.

### 1.1 Core argument

The DDB-EDM profile is a structural wrapper, not a semantic contract. `dc:type` carries controlled-vocabulary terms in libraries, free-text in museums, and structural hierarchy identifiers in archives. No ontology-to-ontology alignment tool can recover these conventions from the schema alone. The methodology contribution is: **profile corpus before modelling, not after**.

The three-layer dispatch architecture (Layer 1: property alignment; Layer 2: htype → RiC-O/DoCO class; Layer 3: dc:type × sector × mediatype → WEMI-slot class) operationalises this and produces 44.4M triples from 115,432 goethe-faust records with quantified coverage at each dispatch level. GeMeA full-corpus ingest statistics (65M objects) provide scale-up validation.

**Differentiation from submitted/planned papers**:
- babel-ddb/SemDH: argues *what* MOCHO is and why the hub ontology design is correct; this paper argues *how* to apply it at scale and whether it works (evaluation, not design)
- GeMeA/ISWC: resource description with FAIR criteria; this paper describes the pipeline methodology and evaluates alignment quality — different contribution type

### 1.2 Source material to repackage

| Source | What to take |
|---|---|
| `goethe-faust/notes/transform-writeup.md` §1–4 | Paper §§2–4 (layers diagram, htype table, dc:type dispatch, run stats) — nearly verbatim |
| `output/alignment_ddbedm_mocho.csv` | Coverage table (field × match\_method × WEMI level) |
| `output/transform_stats.json` | Per-layer hit rates, fallback rates, triple counts |
| babel-ddb §2–3 | Background motivation, hub ontology pattern, WEMI rationale |
| `mocho/notes/alignment-ddbedm-mocho-spec.md` | Known gaps table, success criteria |
| GeMeA full-corpus ingest stats (if available) | §5 scale-up: object counts, triple counts, provider distribution |

### 1.3 JCDL topic fit

- **Metadata standards, linked data, semantic annotation, and interoperability in digital collections** (primary)
- **Knowledge graphs, semantic web, ontologies, and graph-based knowledge representation** (secondary)
- **Data mining, data analytics, and visualization of library collections** (data profiling angle)
- **Domain-specific applications of digital libraries** (DDB/German CH domain)

### 1.4 Contribution type recommendation

**Full paper (10 pp)** if GeMeA full-corpus stats are available and a retrieval evaluation is included (even a lightweight 20–30 known-answer query comparison). JCDL reviewers expect evaluation; pipeline statistics without a retrieval or quality experiment will not pass review.

**Short paper (4 pp)** as a fallback if GeMeA stats are unavailable and the retrieval experiment cannot be run — present as a methodology paper with goethe-faust pilot results only; accept a lower acceptance ceiling.

### 1.5 Evaluation needed for JCDL (absent from TPDL version)

- **WEMI-type precision by stratum**: extend the heuristic eval figures from T12 (babel-ddb camera-ready: `dc:type="Buch"` 81.6%, `"Monografie"` 99.4%) to all `dc:type` values across all sector × mediatype strata; report weighted precision over the full goethe-faust corpus
- **Retrieval evaluation (recommended)**: 20–30 known-answer queries comparing entity-centric SPARQL retrieval (agent URIs, place URIs, work URIs from MOCHO-typed triples) to DDB native full-text search; metric = precision@k; use the Goethe-Faust corpus where ground truth is known

### 1.6 Pros

- Content ~85% exists in notes; `transform-writeup.md` §1–4 maps 1:1 to paper §§2–4
- Run stats are saved and reproducible
- babel-ddb provides ready-made related work; no new literature review needed
- Scale story (115K pilot → 65M full corpus) is compelling for JCDL
- No new annotation required — evaluation is automated (SPARQL queries + precision computation)
- Strong JCDL "Content, Collections" track fit; RDA, RiC-O, EDM are increasingly in scope at DL venues

### 1.7 Cons

- JCDL reviewers expect an IR evaluation, not just pipeline statistics; retrieval experiment must be designed and run before submission
- GeMeA full-corpus ingest statistics depend on the GeMeA pipeline completing in time
- The three-layer dispatch is complex; reviewers unfamiliar with EDM need background that competes with the 10-page budget

### 1.8 Task list

- [ ] Write abstract (≤250 words) — basis: `transform-writeup.md` §Problem + §Run results
- [ ] Draft §1 Introduction — profile-first vs. schema-first framing; 1 p
- [ ] Draft §2 Background — DDB-EDM sectors, WEMI, MOCHO hub ontology; 1.5 p; reuse babel-ddb §§1–2
- [ ] Draft §3 Methodology — three-layer dispatch with Mermaid diagram; 2 p; reuse `transform-writeup.md`
- [ ] Draft §4 Results — run stats table + per-layer coverage table; 1.5 p; reuse saved CSVs
- [ ] Draft §5 Scale-up — GeMeA full-corpus stats (if available); 1 p
- [ ] Draft §6 Retrieval Evaluation — SPARQL vs. DDB keyword search; 1.5 p (new work)
- [ ] Draft §7 Discussion — known gaps, scope limits, reproducibility; 1 p
- [ ] Draft §8 Related Work — EDM alignment papers, BIBFRAME–EDM, DDB2FaBiO; 0.5 p
- [ ] Draft §9 Conclusion; 0.5 p
- [ ] Convert to ACM sigconf LaTeX
- [ ] Submit via EasyChair

**Estimated writing effort**: 9–12 days (6–7 writing + reuse; 2–3 days retrieval eval; 1 day formatting).

---

## 2. Framing 2 — NER for historical German bibliographic title strings

**Title**: *WEM Model: Bibliographic NER for Historical German Catalogs*

**Acronym rationale**: WEM = Work–Expression–Manifestation (FRBR/LRM levels); sounds like WEMI; *wem* (German dative "to whom") signals attribution and authorship; Werkmodell echoes the German compound for a model of a Work. Phase 1 evaluates Work-level entities (TITLE, OTHER_TITLE, PERSON); E and M levels are future phases.

**One-sentence hook**: Standard NER models fail on ISBD-formatted bibliographic catalog strings across three independent dimensions — wrong label set, wrong domain, wrong register — and 92.4% of 9.2M German-language DDB records lack ISBD structural signals; WEM Model delivers an ISBD-guided silver labeling pipeline, a 395-record stratified gold evaluation, and a four-system comparison establishing the zero-shot and fine-tuned performance ceiling for Work-level entity extraction from historical German library catalogs.

### 2.1 Core argument

Bibliographic catalog strings are a distinct NLP register: structured by ISBD punctuation, not prose syntax, and historically variable in orthography (Early Modern German). General-purpose NER fails on three dimensions: wrong label set (CoNLL PER/ORG/LOC vs. TITLE/OTHER\_TITLE/PERSON), wrong domain (newswire vs. GLAM), wrong register (prose vs. ISBD formulaic). The contribution is: (a) an ISBD-guided silver labeling strategy covering the 28.4% of records with structural signals, tiered by confidence; (b) a zero-shot NuNER Zero evaluation on a 395-record stratified gold set; (c) a characterization of where zero-shot fails (historical strata) as motivation for fine-tuning.

This is a **methodology + dataset + evaluation** paper. The claim is: *here is how to approach this task, why it is hard, and what the zero-shot ceiling is* — with F1 per stratum as the evidence.

**Differentiation from submitted/planned papers**:
- babel-ddb/SemDH: ontology design, no NLP; fully distinct
- GeMeA/ISWC: resource description, NER is one pipeline component not evaluated; fully distinct

### 2.2 Source material to repackage

| Source | What to take |
|---|---|
| `https://github.com/anntanp/bibner-werk/blob/main/notes/ner/spiel_ner.md` §0–§8 | Paper §§1–6; chain-of-thought maps directly to section structure |
| `sr10_de-titles-distribution.md` + `fig_title_lengths.png` | §2 corpus statistics |
| `sr01_isbd-field-rating.md`, `sr01_isbd-applicability.md`, `sr01_isbd-title-analysis.md` | §3 ISBD background + silver labeling applicability |
| `silver-dataset-pipeline.md` | §3 silver labeling methodology |
| `sr08_gold-set-composition.md`, `sr08_evaluation-design.md`, `sr08_annotation-guide.md` | §4 gold set design and evaluation protocol |
| `sr09_nuner-tier2-sanity.md` | §5 baseline (needs formal eval run, not just sanity check) |
| `sr05_trailing-period-noise.md`, `sr06_historical-scope.md` | §3 register challenges and noise sources |
| `ref_gliner-nunerzero-comparison.md`, `ref_hipe2022-overview.md` | §6 related work |

### 2.3 JCDL topic fit

- **Natural language processing, information extraction, and semantic search** (primary)
- **Multilingual and multicultural digital libraries** (German, historical orthography)
- **Digitization, transcription, and analysis of cultural heritage and multimedia collections** (primary)
- **Digital humanities methods, computational social science** (DH angle)
- **Knowledge discovery, entity-centric retrieval** (downstream use)

### 2.4 Contribution type recommendation

**Full paper (10 pp)** if gold annotation is completed and formal F1 evaluation (NuNER Zero + at least one fine-tuned baseline) is run before submission. The silver dataset release and reproducibility statement strengthen the contribution further.

**Short paper (4 pp)** as a fallback if gold annotation is incomplete — present silver pipeline + NuNER Zero sanity baseline as a methodology paper; accept a significantly lower acceptance ceiling and risk reviewers requesting a full evaluation.

### 2.5 Critical path

1. **Gold annotation** — human annotators: frankp 393/395 (primary), maria 131/395, gundi 82/395; user annotation pass due 17 June; `ann.jsonl` = Claude pre-annotation (183/395, seeding only); reconcile all → `gold_reconciled.jsonl`
2. **IAA computation** — human-human pairs only: frankp∩maria (131 records), frankp∩gundi (81 records); report range in §4; computable now
3. **Early eval on frankp's 393 records** — NuNER Zero + gliner_multi zero-shot + few-shot; results confirmed on reconciled set after 17 June
4. **Build silver spans** (`build_silver_spans.py`, Stage 5) — prerequisite for fine-tuning
5. **Set up fine-tuning script** (`train_gliner_silver.py`) — ready to fire on 17 June
6. **`gliner_multi-v2.1` fine-tuned on silver labels** (1–2 days; tier-2 + 50K stratified tier-1; exclude 395 gold IDs; use label descriptions)
7. **Qwen2.5-14B zero-shot + few-shot** *(optional, time-permitting)* — not on critical path; run only after fine-tuned gliner_multi results are in
8. **Silver dataset release** (CC BY 4.0; confirm DDB data license)

**Hardware**: A100 80GB PCIe (CUDA 12.4, primary) + 2× Tesla V100S-PCIe 32GB (CUDA 11.6, fallback). Use A100 for all LLM inference and gliner_multi fine-tuning: bf16, flash attention 2, and vLLM are all available. Qwen2.5-14B (bf16, ~28GB) and Qwen2.5-32B (bf16, ~64GB) both fit on the A100 with headroom; use vLLM for batch inference. Qwen2.5-72B in 4-bit (~36GB) is feasible if a larger scaling point is wanted.

### 2.6 Pros

- `spiel_ner.md` §0–§8 is a near-complete paper skeleton; chain-of-thought outline directly produces §§1–6
- All corpus statistics are already computed and saved as CSVs; `fig_title_lengths.png` is publication-ready
- The "why off-the-shelf NER fails" argument (§3 of spiel\_ner) is original and the JCDL historical/multilingual DL audience will find it directly relevant
- Historical German bibliographic records are a known pain point in the LAM community; scale (4.48M records, 71.6% NER fallback) is compelling
- No architectural novelty required: methodology + dataset + evaluation is the contribution type
- The convergence of pilot (29% ISBD coverage) and full corpus (28.4%) validates generalizability within the paper

### 2.7 Cons

- Formal eval code does not yet exist (`sr09` is a sanity check, not a paper-ready evaluation script)
- GLiNER2 (Zaratiana et al., 2025) is English-only; use `urchade/gliner_multi-v2.1` (multilingual GLiNER v1 fine-tune) for both zero-shot and fine-tuned baselines — these are distinct from the GLiNER2 system paper
- LLM structured output parsing is fragile; need a robust parser for JSON span extraction from Qwen2.5-14B output; budget half a day for prompt iteration
- Historical German orthography variation is a known challenge; discussion of tokenization choices may consume page budget
- GeMeA is the downstream consumer of NER output, but GeMeA is not built — cannot claim end-to-end integration; describe as intended downstream use

### 2.8 Task list

- [ ] Complete gold annotation (395 records) — started 20 May, due 28 May
- [ ] Run formal NuNER Zero evaluation on gold set; save per-stratum F1 + CI to `data/processed/`
- [ ] Run `urchade/gliner_multi-v2.1` zero-shot evaluation on gold set; save per-stratum F1 + CI to `data/processed/`
- [ ] Run Qwen2.5-14B zero-shot on gold set (fp16, single V100S; HF Transformers; structured JSON prompt); save per-stratum F1 + CI to `data/processed/`
- [ ] Run Qwen2.5-14B few-shot (k=5, Tier 1 silver examples) on gold set; save per-stratum F1 + CI to `data/processed/`
- [ ] Fine-tune `urchade/gliner_multi-v2.1` on silver labels; evaluate on gold set; save per-stratum F1 + CI
- [ ] Write abstract (≤250 words) — basis: `spiel_ner.md` chain-of-thought + §1 Scale
- [ ] Draft §1 Introduction — 71.6% fallback framing; 1 p
- [ ] Draft §2 Corpus and Task — DDB, German-language filter, ISBD structure, label set; 1.5 p
- [ ] Draft §3 Challenges and Silver Labeling — register failures + ISBD signal extraction + tiered confidence; 2 p
- [ ] Draft §4 Evaluation Design — gold set (395 records, stratified by era + silver tier), exact span match, CI constraints; 1 p
- [ ] Draft §5 Results — NuNER Zero + fine-tuned baseline F1 per stratum; analysis of failures; 2 p
- [ ] Draft §6 Related Work — HIPE-2022, historical NER, bibliographic NLP; 0.5 p
- [ ] Draft §7 Conclusion and Future Work; 0.5 p
- [ ] Confirm silver dataset and gold set availability/license (CC BY 4.0 via DDB)
- [ ] Add reproducibility statement (anonymized dataset + eval scripts via anonymous.4open.science)
- [ ] Convert to ACM sigconf LaTeX
- [ ] Submit via EasyChair

**Estimated writing effort**: 10–13 days from 28 May (eval code + NuNER Zero + gliner_multi zero-shot: 2 days; Qwen2.5-14B zero-shot + few-shot + prompt engineering: 1–2 days; gliner_multi fine-tuning: 1–2 days; writing: 5–6 days; formatting: 1 day) → submission-ready by ~10 June; ~20 days of buffer before 30 June deadline.

---

## 3. Comparison

| Criterion | Framing 1 (Harmonization + Eval) | Framing 2 (NER) |
|---|---|---|
| Content readiness | ~85% exists; eval experiment is new | ~80%; gold annotation completing 28 May |
| New code needed | Retrieval eval script (required) | Eval script + gliner_multi fine-tuning |
| Dual-submission risk | None (TPDL cancelled) | None (TPDL cancelled) |
| JCDL reviewer fit | "Metadata standards + KG construction" — strong | "NLP + DL" — strong |
| Evaluation type | WEMI-type precision + retrieval@k | F1 per stratum (NuNER Zero + gliner_multi zero-shot + Qwen2.5-14B zero-shot + Qwen2.5-14B few-shot + gliner_multi fine-tuned) |
| Man-days remaining | 9–12 | ~18–21 total (8 d annotation + 10–13 d post-annotation) |
| Acceptance w/ evaluation | 35–45% | 40–50% |
| Acceptance w/o evaluation | 15–20% (pipeline stats only) | 20–30% (zero-shot only) |
| Key risk | Retrieval eval required; pipeline stats alone insufficient | LLM output parsing fragility; annotation must complete on schedule |

**Recommendation**: **Framing 2 is the primary submission.** Gold annotation due 28 May; five-system comparison (NuNER Zero, gliner_multi zero-shot, Qwen2.5-14B zero-shot, Qwen2.5-14B few-shot, gliner_multi fine-tuned) gives per-stratum F1 results with a 40–50% acceptance ceiling. Submission-ready by ~10 June with ~20 days of buffer. Framing 1 is a viable backup but requires a retrieval experiment to clear the JCDL bar; pipeline statistics alone will not pass review.

---

## 4. What NOT to submit for JCDL

- **GeMeA resource paper** — this is the ISWC 2026 Resource Track submission; submitting the same resource to JCDL is a dual-publication violation
- **babel-ddb/MOCHO design paper** — this is the SemDH 2026 submission; a JCDL version must foreground MOCHO *evaluation* (competency questions, alignment coverage), not the design rationale already in the SemDH paper; only viable if T13 (full MOCHO validation) is completed
- **Full GeMeA pipeline paper** — covers the same ground as both ISWC (resource) and Framing 1 (methodology); submitting all three creates dual-submission and self-plagiarism risk

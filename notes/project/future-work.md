# GeMeA — Future Work

---

## 1. Provenance Ontology Extension for KG Refinement

**Source:** rm055.pdf (slides 17–24); discussion 2026-03-24

### 1.1 Background

Standard Prov-O models KG refinement steps as `prov:Activity` / `prov:Agent` / `prov:Entity` triples. This is sufficient for simple, single-model pipelines but cannot express:

- Hyperparameter configurations
- LLM-specific reasoning steps (CoT, ICL, etc.)
- Prompt or workflow identity
- Confidence scores on newly generated triples
- Which refinement type (NER, entity linking, link prediction, etc.) was applied

The `provlm` extension (rm055.pdf) proposes three new classes on top of Prov-O:

| Class | Parent | Purpose |
|---|---|---|
| `provlm:LMRefinement` | `prov:Activity` | A model-driven KG refinement step |
| `provlm:LanguageModel` | `prov:SoftwareAgent` | The model as provenance agent |
| `provlm:RefinementPlan` | `prov:Plan` | Prompt or config used |

Plus a structured `provlm:ConfidenceAssessment` blank node (score + dimension + metric) and a `provlm:RefinementTypeScheme` SKOS vocabulary (NER, EntityLinking, link prediction, ontology alignment, etc.).

### 1.2 How GeMeA's pipeline maps onto `provlm`

**Phase 0a — NER (title extraction)**

```turtle
gemea:NERRun42 a provlm:LMRefinement ;
    provlm:refinementType provlm:NER ;
    prov:wasAssociatedWith gemea:NuNERZero ;
    prov:hadPlan gemea:NERLabelConfig ;
    prov:used gemea:DF_DE_TITLES ;
    provlm:hasConfidenceAssessment [
        provlm:confidenceScore "0.87"^^xsd:float ;
        provlm:confidenceDimension "token-level probability" ;
        provlm:confidenceMetric "F1"
    ] .

gemea:NuNERZero a provlm:LanguageModel ;
    rdfs:label "numind/NuNerZero" .

gemea:NERLabelConfig a provlm:RefinementPlan ;
    rdfs:comment "Label set: TITLE, OTHER_TITLE, PERSON, ... (13 FRBR-organized labels)" .
```

**Phase 0 — GND Werk entity linking (`link_gnd_works.py`)**

The NuNER Zero extraction step is `provlm:LMRefinement` with `provlm:refinementType provlm:EntityLinking`. The downstream SPARQL lookup against `sparql.dnb.de` is a plain `prov:Activity` (no LM involved), linked to a versioned dataset entity:

```turtle
gemea:SPARQLLinkingRun a prov:Activity ;
    prov:used gemea:DNBDataset-v23.02.2026 ;
    provlm:hasConfidenceAssessment [
        provlm:confidenceScore "1.0"^^xsd:float ;
        provlm:confidenceDimension "retrieval consistency score" ;
        provlm:confidenceMetric "exact"
    ] .

gemea:DNBDataset-v23.02.2026 a prov:Entity ;
    rdfs:label "dnb-all_lds v23.02.2026" ;
    prov:generatedAtTime "2026-02-23"^^xsd:date .
```

**Phase 1b — GND agent linking (`link_gnd_agents.py`)**

No LM involved (lobid-gnd REST API + string matching). Standard Prov-O suffices.

### 1.3 Gaps — what `provlm` does not cover for GeMeA

**Gap 1 — Hybrid pipelines.** GeMeA's title extraction is two-stage: ISBD rule-based parsing (`prov:Activity`) followed by NuNER Zero fallback (`provlm:LMRefinement`). The extension has no representation for a composite activity where only the fallback branch is LM-driven. A `prov:wasInformedBy` chain between two separate activities is the minimal workaround, but does not make the branching logic explicit. A `provlm:HybridRefinement` class (or a `provlm:hasFallback` property) would address this.

**Gap 2 — Non-LM retrieval confidence.** `match_confidence` in `link_gnd_works.py` is Levenshtein edit-distance over SPARQL-retrieved candidates — not an LM score. The `provlm:confidenceDimension` vocabulary has no slot for string-similarity-based retrieval confidence. The SKOS scheme needs extending (e.g. `provlm:EditDistanceSimilarity`, `provlm:SPARQLExactMatch`).

**Gap 3 — Traditional ML vs. generative LLM boundary.** NuNER Zero is a compact token classifier producing token-level probabilities — it fits the "generative LLM" column of slide 22 (token-level prob) but is not a generative model. The extension does not draw this distinction formally. GeMeA sits in the grey zone and would benefit from a `provlm:NeuralSequenceLabeler` subclass of `provlm:LanguageModel` (distinct from `provlm:GenerativeLM`).

**Gap 4 — Dataset version provenance on SPARQL steps.** NFR-05 requires recording the GND dataset version used for Werk linking. Standard `prov:used` handles this, but the extension is silent on how to attach dataset version provenance to a hybrid activity where some steps query an external endpoint and others run locally.

### 1.4 Potential GeMeA contributions

1. **Worked instantiation** — apply `provlm` to a real cultural heritage KG pipeline (DDB, 65M objects); validate the extension on a non-biomedical, non-English domain.

2. **Hybrid pipeline representation** — propose a convention (or new property) for activities that mix rule-based, neural, and SPARQL steps in a directed sequence; `prov:wasInformedBy` chain vs. composite activity design.

3. **SKOS vocabulary extension** — add `provlm:ISBDParsing` and `provlm:SPARQLEntityLinking` to `provlm:RefinementTypeScheme`; add `provlm:EditDistanceSimilarity` and `provlm:RetrievalExactMatch` to the confidence dimension vocabulary.

4. **Model type taxonomy** — distinguish `provlm:NeuralSequenceLabeler` (NuNER Zero, xlm-roberta) from `provlm:GenerativeLM` (GPT-4o, Claude) as subclasses of `provlm:LanguageModel`; different confidence encoding applies to each.

### 1.5 Paper scope note

The ISWC Resource Track target is 8–15 pp. `provlm` is not ready to publish as part of the GeMeA paper — it is still being designed. Two paths forward:

**Option A — Finish `provlm` first, then cite it from GeMeA.** Complete the extension (address gaps in §1.3), publish it at Semantics/ESWC/an ISWC workshop, then reference it from the GeMeA Resource Track paper as a provenance layer. Cleanest separation; each paper stands on its own.

**Option B — Include a "Provenance Model" section in GeMeA as a contribution-in-progress.** Present the instantiation (Turtle snippets for the three pipeline phases), note the open gaps, and position the full extension as future work. Lower bar — does not require `provlm` to be complete before the May 7 deadline.

### 1.6 Origin

The `provlm` extension is unpublished, unfinished work (rm055.pdf, internal meeting). GeMeA is a concrete use case for grounding and completing it. The gaps in §1.3 are open design questions in the extension itself, not just GeMeA-specific issues.

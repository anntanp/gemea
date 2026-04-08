# Paper Framing Notes

**Date**: 2026-04-05
**Context**: Brainstorming session on GeMeA paper framing for ISWC 2026 Resource Track

---

## Proposed framing

**"Domain-specific, data-driven knowledge graph construction and enrichment using LLMs"**

---

## What works well

- **"Data-driven"** is well-supported: corpus profiling, field taxonomy, objecttype matching, and alignment methodology are all grounded in actual data before any modeling. The pipeline starts with `profile_edm_fields.py` and field-frequency analysis — not schema assumptions.
- **"Domain-specific"** is credible with mocho as the middle ontology. This is not generic KG construction — it works within a well-defined bibliographic/cultural heritage domain with established vocabularies (RDA, RiC-O, CIDOC-CRM, Music Ontology). The domain specificity justifies the middle-ontology architecture.
- **"Refinement using LLMs"** fits if LLMs are used for: agent role disambiguation (`affiliate`), language detection (Stage 2 of BCP 47 tagging), objecttype → mocho class resolution, or NER for title/contributor parsing.

---

## Where to be careful

- **"Construction and enrichment"** implies two distinct phases — the paper needs a clear boundary between them, otherwise reviewers will ask where one ends and the other begins. Define construction = alignment + ingest; enrichment = LLM-assisted passes adding new structured triples.
- **"Using LLMs"** needs precision about *where* in the pipeline. LLMs are one component among many (SPARQL, ontology reasoning, rule-based alignment, embedding matching). The framing risks overstating their role if the pipeline is mostly rule-based with LLMs handling edge cases.
- **ISWC Resource Track expectations**: the resource (KG + mocho) must be the primary contribution. LLM framing should support the resource description, not overshadow it. Reviewers will ask: what is the resource, is it available, is it useful?

---

## Suggested framing adjustment

Keep the proposed framing as a *pipeline characterisation*, not the top-level contribution claim. Suggested title direction:

> *"GeMeA: Data-driven construction of a multi-modal cultural heritage knowledge graph using a WEMI-aligned middle ontology"*

With LLM-assisted enrichment named explicitly as a pipeline component in the abstract and §3 (Pipeline). This keeps the resource front and center and positions LLMs as a method, not the contribution.

---

## Relationship to existing paper-outline.md

The current core argument in `paper-outline.md`:
> "GeMeA fills a critical gap by providing the first open, SPARQL-accessible knowledge graph over the complete German Digital Library corpus (65M objects), normalizing heterogeneous EDM metadata to a unified RDA/FRBR model and exposing it through a full-featured web interface."

The new framing adds: *how* the normalization is done (data-driven, domain-specific, LLM-assisted) as a methodological contribution alongside the resource contribution. This strengthens the paper for tracks that value reproducibility and methodology, not just resource availability.

---

## Open questions

- `- []` Where exactly do LLMs enter the pipeline? Enumerate the specific steps: role disambiguation, language detection, objecttype resolution, NER — confirm which are implemented vs. planned
- `- [x]` **"Enrichment"** is the right word — LLM passes add new structured triples (role disambiguation, NER, objecttype resolution), not correct existing ones. Update "refinement" → "enrichment" in framing and title direction above.
- `- []` Reconcile with `paper-outline.md` core argument — update once framing is settled

# GeMeA — Paper Outline Options

**Date**: 2026-04-19
**Title**: GeMeA: Knowledge Graph Testbed for 23M+ German Cultural Heritage Objects
**Track**: ISWC 2026 Resource Track
**Format**: Springer LNCS, ≤15 pages + references

---

## Option A — ISWC Resource Track standard

Follows the expected section pattern; reviewers can find what they need quickly.

1. Introduction
2. Related Work
3. Resource Description
   - 3.1 EDM Knowledge Graph (26M objects, QLever, SHMARQL)
   - 3.2 Ontology Alignment PoC (mocho, EDM → RDA/FRBR)
   - 3.3 Access Layer (SPARQL, MCP/MCPO)
   - 3.4 Entity Linking (GND, rule-based baseline)
4. Quality & Validation
5. Usage & Reusability
6. Impact & Sustainability
7. Conclusion

---

## Option B — Testbed-forward

Restructures around the paper's distinguishing claim; good if reviewers need convincing that a PoC-scale resource warrants publication.

1. Introduction
2. Related Work
3. Resource Description
4. KG Enhancement Pipeline (mocho PoC + entity linking)
5. Testbed Applications (onto-eval, MCP/agentic, RML, Prov-LM)
6. Quality & Sustainability
7. Conclusion

---

## Option C — With Discussion

Adds explicit space for limitations and positioning; useful given the PoC framing.

1. Introduction
2. Related Work
3. Resource Description
4. Quality & Validation
5. Usage & Reusability
6. Discussion (scope, known gaps, comparison with ArtKB/Europeana LOD)
7. Conclusion

---

## Recommendation

**Option A** for first submission — matches reviewer expectations for the Resource Track and maps cleanly onto mandatory sections (availability, quality, usage, sustainability). Testbed applications fit into §5 Usage & Reusability without a dedicated section.

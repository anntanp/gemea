# ISBD and the Semantic Web

**Citation**: Willer, M., Dunsire, G., & Bosančić, B. (2010). ISBD and the Semantic Web. *JLIS.it*, 1(2), 213–236.
**DOI**: 10.4403/jlis.it-4536
**Track**: A — Library Science

---

## Core Claim

ISBD can be represented in RDF and integrated into the Semantic Web without abandoning its record-level integrity. The Dublin Core Application Profile (DCAP) framework — specifically the Description Set Profile (DSP) — is the appropriate vehicle for encoding ISBD's mandatory/optional, order, and repeatability constraints alongside the element namespace.

## Method

Institutional/process paper documenting the IFLA ISBD/XML Study Group's 2008–2010 activity. Reports design decisions taken during two formal and two ad hoc meetings, including the pivot from an XML schema to an RDF/XML approach. Not empirical; no evaluation.

## Key Findings / Design Decisions

**RDF representation:**
- ISBD has a single class: `Resource` (a bibliographic resource). No classes for persons, places, etc. — ISBD does not model relationships between resources.
- All ISBD attributes become RDF **properties** with domain `Resource`; no ranges declared (deferred to ISBD-AP).
- Convention: property label = verb + attribute name, e.g., "has title proper" (`P1004`), "has edition statement" (`P1008`). Verb added for readability and to indicate triple direction.
- URIs are opaque numeric identifiers (`iflastandards.info/ns/ISBD/elements/P1004`) — language-neutral; human-readable labels attached separately, enabling multilingual MulDiCat equivalents.

**Aggregated statements (ISBD areas):**
- ISBD's nine areas (0–8) are modelled as Syntax Encoding Schemes (SES) — sub-classes of a generic ISBD SES.
- Area 0 (content/media/carrier) gets Vocabulary Encoding Schemes (VES) via SKOS controlled vocabularies already in the Open Metadata Registry.
- This preserves mandatory/optional status, element order, repeatability, and punctuation rules at the area level.

**ISBD Application Profile (ISBD-AP) and DSP-ISBD:**
- ISBD-AP = a Dublin Core Application Profile specifying which ISBD RDF properties to use in a metadata application, with usage constraints.
- DSP-ISBD = XML document (pre-defined markup + qualifiers) defining the Description Set Profile for ISBD records.
- "has title proper" is non-repeatable (`maxOccurs=1`) and not mandatory at record level (a collection without a common title may lack it) — `minOccurs=0`.
- Mandatory elements: only those with a specified default (e.g., place of publication defaults to "[S.l.]") qualify as strictly mandatory in DSP terms; most ISBD mandatory elements are "mandatory if applicable."

**Namespace policy:**
- No deliberate alignment with FRBR/RDA namespaces at this stage — relationships between ISBD and FRBR/RDA are not formally defined; premature alignment risks incorrect semantics.
- Super-properties (e.g., `dcterms:title` for title-type properties) may be added later without touching ISBD definitions.
- All ISBD properties carry the IFLA brand (`iflastandards.info`) — signal of provenance and authority.

**Early adopters (2010):**
- British Library: using `has edition statement` (P1008), `has note on language` (P1074), `has place of publication` (P1016) in experimental BNB RDF/XML triples.
- Universitätsbibliothek Mannheim: `has edition statement` in catalogue RDF representation.

## Limitations

- Status report as of mid-2010; ISBD Consolidated Edition not yet published (appeared 2011). All decisions were provisional.
- OWL constraints for conditional aggregated elements (not all components mandatory) remain unresolved within DCAP architecture.
- No empirical evaluation of the RDF representation's utility or coverage.
- Project funded for two years; third year proposed to finalize alignment with 2011 consolidated edition.

## Relevance to GeMeA

**Cite in:** §2 Related Work (linked library data / ISBD as Semantic Web vocabulary); potentially §3 Data Pipeline when discussing mocho alignment with ISBD/RDA.

**Direct technical connections:**
- The ISBD namespace (`iflastandards.info/ns/ISBD/elements/`) described here is what `mocho.owl` aligns to. The property naming convention (verb + attribute, numeric URI) explains why mocho properties look as they do.
- The distinction between ISBD's flat property model (no relationship classes) and FRBR's entity-relationship model is foundational for understanding why `link_gnd_works.py` needs GND as a separate entity graph rather than inferring works from ISBD records directly.
- The "no range declarations" decision means ISBD RDF properties alone cannot enforce value types — validation must happen at the ISBD-AP / application layer, i.e., in mocho.

**Differentiation angle (what GeMeA adds beyond this):**
- This paper shows ISBD can be *represented* as RDF; GeMeA demonstrates it can be *queried at scale* (65M objects) with a faceted UI, SPARQL endpoint, and NER-enriched entity links.

## BibTeX

```bibtex
@article{willer2010isbd,
  title   = {{ISBD} and the {Semantic Web}},
  author  = {Willer, Mirna and Dunsire, Gordon and Bosan{\v{c}}i{\'{c}}, Boris},
  journal = {JLIS.it},
  volume  = {1},
  number  = {2},
  pages   = {213--236},
  year    = {2010},
  doi     = {10.4403/jlis.it-4536}
}
```

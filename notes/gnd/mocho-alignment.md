# GeMeA — mocho Alignment

mocho (`../mocho/`) is the ontology alignment tool that normalizes DDB EDM metadata to RDA/FRBR. **mocho.owl is currently WIP** — the full pipeline is blocked until it stabilizes.

---

## Pipeline position

```
rdf2jsonld output (RDF/JSON)
      │
      ▼  scripts/link_gnd_works.py  (must run BEFORE mocho)
RDF/JSON + GND Werk triples
      │
      ▼  mocho  (reads both; uses GND Werk URIs to create mocho:Work groupings)
N-Triples  →  load_qlever.py
```

`link_gnd_works.py` is a hard prerequisite for mocho. The GND Werk URI is the key mocho uses to determine which `edm:ProvidedCHO` instances belong to the same Work.

---

## What the alignment involves

### Class mappings (EDM → RDA/FRBR)

| EDM | RDA/FRBR | Notes |
|-----|----------|-------|
| `edm:ProvidedCHO` | `frbr:Manifestation` | Primary mapping |
| `ore:Aggregation` | `frbr:Item` | Digital surrogate |
| `edm:Agent` | `frbr:Person` / `frbr:CorporateBody` | Split by GND type |
| `edm:Place` | `frbr:Place` | |
| `edm:TimeSpan` | `frbr:TimeSpan` | |

### Property mappings (EDM → RDA)

| EDM | RDA |
|-----|-----|
| `dc:title` | `rda:title` |
| `dc:creator`, `dc:contributor` | `rda:creator`, `rda:contributor` |
| `dc:date`, `dcterms:issued` | `rda:dateOfPublication` |
| `dc:language` | `rda:languageOfExpression` |
| `dc:type` | `rda:carrierType` / `rda:mediaType` |
| `edm:isShownAt` | `rda:electronicLocatorForOnlineResource` |

### mocho:Work entity creation

The key challenge in EDM→FRBR alignment is that EDM is flat (one `ProvidedCHO` per record) while FRBR requires a Work → Expression → Manifestation hierarchy.

mocho creates `mocho:Work` entities by grouping `edm:ProvidedCHO` instances that share the same GND Werk URI:

```
GND Werk: d-nb.info/gnd/118607359 ("Faust")
  └── mocho:Work (new entity)
        ├── edm:ProvidedCHO/ABC123  (Staatsbibliothek copy)
        ├── edm:ProvidedCHO/ABC124  (Weimar copy)
        └── edm:ProvidedCHO/ABC125  (Frankfurt copy)
```

ProvidedCHOs without a GND Werk link remain as standalone Manifestations with no parent Work.

---

## Key open questions (pending mocho.owl stabilization)

- Does mocho create distinct `mocho:Work` URI resources, or annotate ProvidedCHOs with Work-level properties?
- Does mocho create `mocho:Expression` nodes, or is the hierarchy two-level (Work → Manifestation)?
- What namespace does mocho use for its classes and properties?
- Does mocho use a declarative OWL reasoner or SPARQL CONSTRUCT rules internally?

---

## Verification queries (run after mocho output loaded into QLever)

```sparql
# Are mocho:Work nodes present?
SELECT (COUNT(?w) AS ?count) WHERE {
  ?w a mocho:Work .
}

# How many ProvidedCHOs have a parent Work?
SELECT (COUNT(?cho) AS ?count) WHERE {
  ?w a mocho:Work ;
     mocho:hasManifestation ?cho .
}

# Sample Work with its manifestations
SELECT ?w ?cho ?title WHERE {
  ?w a mocho:Work .
  ?w mocho:hasManifestation ?cho .
  ?cho dc:title ?title .
} LIMIT 20
```

---

## Impact on /work/{id} API

- If mocho creates distinct `mocho:Work` URI resources → `/work/{id}` queries QLever directly for the Work entity and its linked ProvidedCHOs
- If mocho only annotates → Work pages must be reconstructed at query time by grouping ProvidedCHOs sharing a GND Werk URI

Verify before building the API endpoint. See `notes/project/priorities.md` for the gate condition.

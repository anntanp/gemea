# GND SPARQL Queries

Endpoint: `https://gnd.ise.fiz-karlsruhe.de/sparql`  
Ontology: `mocho/ontology/gnd_20251218.ttl`

---

## 1. Werk counts by class

**Date**: 2026-05-05

### Query

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>

SELECT ?class (COUNT(?s) AS ?count) WHERE {
  VALUES ?class {
    gndo:Work gndo:Collection gndo:CollectiveManuscript
    gndo:Expression gndo:Manuscript gndo:MusicalWork
    gndo:ProvenanceCharacteristic gndo:VersionOfAMusicalWork
  }
  ?s a ?class .
}
GROUP BY ?class
ORDER BY DESC(?count)
```

Counts direct `rdf:type` assertions per class (no inference). Subclasses enumerated
from the ontology (`rdfs:subClassOf gndo:Work`). `CollectiveManuscript` returned 0.

### Results

| Class (gndo:) | Label (de) | Count |
|---|---|---|
| `MusicalWork` | Werk der Musik | 330,818 |
| `Work` | Werk (direct) | 242,332 |
| `ProvenanceCharacteristic` | Provenienzmerkmal | 10,080 |
| `Manuscript` | Schriftdenkmal | 7,133 |
| `Expression` | Expression | 5,766 |
| `VersionOfAMusicalWork` | Fassung eines Werks der Musik | 2,905 |
| `Collection` | Sammlung | 1,751 |
| `CollectiveManuscript` | Sammelhandschrift | 0 |
| **Total** | | **600,785** |

Query time: 57 ms.

---

## Prompts

- *this is the ontology of the gnd sparql instance /Users/mta/Documents/claude/mocho/ontology/gnd_20251218.ttl. Find out how many Werke there are. and the number per subclass (Werke, Musikwerke, etc.). Document the sparql query to notes/gnd-sparql.md*

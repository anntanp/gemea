# GND Werk — SPARQL Query Reference

Endpoint: `http://localhost:7020`

---

## 1. Dataset overview

```sparql
# Triple count and predicates
SELECT ?p (COUNT(*) AS ?n) WHERE {
  ?s ?p ?o .
} GROUP BY ?p ORDER BY DESC(?n) LIMIT 20
```

```sparql
# Count GND Werk entities
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {
  ?s a gndo:Work .
}
```

---

## 2. Entity lookup

```sparql
# Describe a specific Werk by GND ID
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
DESCRIBE <https://d-nb.info/gnd/4020506-7>
```

```sparql
# All triples for a Werk
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?p ?o WHERE {
  <https://d-nb.info/gnd/4020506-7> ?p ?o .
}
```

---

## 3. Title search

```sparql
# Works with a preferred name containing "Faust"
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?title WHERE {
  ?s gndo:preferredNameForTheWork ?title .
  FILTER(CONTAINS(LCASE(?title), "faust"))
} LIMIT 20
```

```sparql
# Variant titles
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?pref ?var WHERE {
  ?s gndo:preferredNameForTheWork ?pref ;
     gndo:variantNameForTheWork ?var .
  FILTER(CONTAINS(LCASE(?pref), "faust"))
} LIMIT 20
```

---

## 4. Authority links

```sparql
# Works with Wikidata links
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?werk ?title ?wd WHERE {
  ?werk a gndo:Work ;
        gndo:preferredNameForTheWork ?title ;
        owl:sameAs ?wd .
  FILTER(STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/"))
} LIMIT 20
```

```sparql
# Works with VIAF links
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?werk ?title ?viaf WHERE {
  ?werk a gndo:Work ;
        gndo:preferredNameForTheWork ?title ;
        owl:sameAs ?viaf .
  FILTER(STRSTARTS(STR(?viaf), "http://viaf.org/viaf/"))
} LIMIT 20
```

---

## 5. Work types / subtypes

```sparql
# GND Work subtype distribution
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?type (COUNT(*) AS ?n) WHERE {
  ?s a ?type .
  FILTER(STRSTARTS(STR(?type), "https://d-nb.info/standards/elementset/gnd#"))
} GROUP BY ?type ORDER BY DESC(?n)
```

---

## 6. Related works

```sparql
# Works that reference another work (broaderTermInstantial, partOf, etc.)
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?rel ?o WHERE {
  ?s gndo:broaderTermInstantial ?o .
} LIMIT 20
```

---

## 7. MCP tool equivalents

| Task | MCP tool | Key param |
|------|----------|-----------|
| Run any query | `sparql_query` | `query` |
| Look up entity | `describe_entity` | `iri` |
| Search by label | `search_entities` | `search_term`, `label_predicate=gndo:preferredNameForTheWork` |
| List predicates | `get_predicates` | — |
| Dataset stats | `get_index_stats` | — |
| Autocomplete | `sparql_autocomplete` | `partial_query` |

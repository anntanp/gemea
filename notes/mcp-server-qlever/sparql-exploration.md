# GND Werk — SPARQL Exploration Queries

Run these via `sparql_query` (MCP tool) or `curl http://localhost:7020`.

---

## Named graphs

```sparql
SELECT DISTINCT ?g (COUNT(*) AS ?n)
WHERE { GRAPH ?g { ?s ?p ?o } }
GROUP BY ?g
ORDER BY DESC(?n)
```

## Triple count

```sparql
SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }
```

## Predicates by frequency

```sparql
SELECT ?p (COUNT(*) AS ?n)
WHERE { ?s ?p ?o }
GROUP BY ?p
ORDER BY DESC(?n)
```

## RDF types

```sparql
SELECT ?type (COUNT(*) AS ?n)
WHERE { ?s a ?type }
GROUP BY ?type
ORDER BY DESC(?n)
```

## Sample Werk entity

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?p ?o WHERE {
  ?s a gndo:Work ; ?p ?o .
} LIMIT 50
```

## Preferred titles (sample)

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?title WHERE {
  ?s gndo:preferredNameForTheWork ?title .
} LIMIT 20
```

## Title search: "Goethe Faust"

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?title WHERE {
  ?s gndo:preferredNameForTheWork ?title .
  FILTER(CONTAINS(LCASE(STR(?title)), "goethe") && CONTAINS(LCASE(STR(?title)), "faust"))
} LIMIT 50
```

## Describe entity: Goethes Faust (1244830623)

```sparql
SELECT ?p ?o WHERE {
  <https://d-nb.info/gnd/1244830623> ?p ?o .
}
```

## Preferred name of literary source 4099197-0

```sparql
SELECT ?p ?o WHERE {
  <https://d-nb.info/gnd/4099197-0> ?p ?o .
}
```

## Works with Wikidata sameAs

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?s ?title ?wd WHERE {
  ?s gndo:preferredNameForTheWork ?title ;
     owl:sameAs ?wd .
  FILTER(STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/"))
} LIMIT 20
```

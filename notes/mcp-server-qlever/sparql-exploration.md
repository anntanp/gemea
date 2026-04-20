# GND Werk — SPARQL Exploration Queries

Run these via `sparql_query` (MCP tool) or `curl http://localhost:7020`.

---

## Goethe-authored books — goethe-faust QLever

Query ProvidedCHO records with `dc:creator` matching Goethe by GND URI or literal.
UNION needed because `export_ddb.py` emits only the URI when a `resource` field is present,
or only the literal when not — never both.

```sparql
PREFIX dc:  <http://purl.org/dc/elements/1.1/>
PREFIX edm: <http://www.europeana.eu/schemas/edm/>

SELECT ?item ?title ?creator WHERE {
  ?item a edm:ProvidedCHO ;
        dc:title ?title .
  {
    ?item dc:creator <http://d-nb.info/gnd/118540238> .
    BIND(<http://d-nb.info/gnd/118540238> AS ?creator)
  } UNION {
    ?item dc:creator ?creator .
    FILTER(ISLITERAL(?creator) && CONTAINS(LCASE(STR(?creator)), "goethe"))
  }
}
ORDER BY ?title
```

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

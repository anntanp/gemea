# GND Werk — SPARQL Exploration Queries

Run these via `sparql_query` (MCP tool) or `curl http://localhost:7020`.

## Contents

1. [Goethe-authored books — goethe-faust QLever](#1-goethe-authored-books--goethe-faust-qlever)
2. [Named graphs](#2-named-graphs)
3. [Triple count](#3-triple-count)
4. [Predicates by frequency](#4-predicates-by-frequency)
5. [RDF types](#5-rdf-types)
6. [Sample Werk entity](#6-sample-werk-entity)
7. [Preferred titles (sample)](#7-preferred-titles-sample)
8. [Title search: "Goethe Faust"](#8-title-search-goethe-faust)
9. [Describe entity: Goethes Faust (1244830623)](#9-describe-entity-goethes-faust-1244830623)
10. [Preferred name of literary source 4099197-0](#10-preferred-name-of-literary-source-4099197-0)
11. [Works with Wikidata sameAs](#11-works-with-wikidata-sameas)
12. [dc:title encoding variation (ISBD punctuation coverage)](#12-dctitle-encoding-variation-isbd-punctuation-coverage)
    - 12.1 [Sample ISBD-punctuated titles](#121-sample-isbd-punctuated-titles)
    - 12.2 [Sample bare titles (no ISBD punctuation)](#122-sample-bare-titles-no-isbd-punctuation)
13. [Corpus analysis — goethe-faust local QLever (port 7030)](#13-corpus-analysis--goethe-faust-local-qlever-port-7030)
14. [Sector distribution](#14-sector-distribution)
15. [dc:type IRI vs literal — library sector (sparte002)](#15-dctype-iri-vs-literal--library-sector-sparte002)
16. [dc:type top values — archive sector (sparte001)](#16-dctype-top-values--archive-sector-sparte001)
17. [Goethe attribution anomaly — objects attributed to Goethe that may be collection items](#17-goethe-attribution-anomaly--objects-attributed-to-goethe-that-may-be-collection-items)

---

## 1. Goethe-authored books — goethe-faust QLever

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

## 2. Named graphs

```sparql
SELECT DISTINCT ?g (COUNT(*) AS ?n)
WHERE { GRAPH ?g { ?s ?p ?o } }
GROUP BY ?g
ORDER BY DESC(?n)
```

## 3. Triple count

```sparql
SELECT (COUNT(*) AS ?n) WHERE { ?s ?p ?o }
```

## 4. Predicates by frequency

```sparql
SELECT ?p (COUNT(*) AS ?n)
WHERE { ?s ?p ?o }
GROUP BY ?p
ORDER BY DESC(?n)
```

## 5. RDF types

```sparql
SELECT ?type (COUNT(*) AS ?n)
WHERE { ?s a ?type }
GROUP BY ?type
ORDER BY DESC(?n)
```

## 6. Sample Werk entity

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?p ?o WHERE {
  ?s a gndo:Work ; ?p ?o .
} LIMIT 50
```

## 7. Preferred titles (sample)

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?title WHERE {
  ?s gndo:preferredNameForTheWork ?title .
} LIMIT 20
```

## 8. Title search: "Goethe Faust"

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
SELECT ?s ?title WHERE {
  ?s gndo:preferredNameForTheWork ?title .
  FILTER(CONTAINS(LCASE(STR(?title)), "goethe") && CONTAINS(LCASE(STR(?title)), "faust"))
} LIMIT 50
```

## 9. Describe entity: Goethes Faust (1244830623)

```sparql
SELECT ?p ?o WHERE {
  <https://d-nb.info/gnd/1244830623> ?p ?o .
}
```

## 10. Preferred name of literary source 4099197-0

```sparql
SELECT ?p ?o WHERE {
  <https://d-nb.info/gnd/4099197-0> ?p ?o .
}
```

## 11. Works with Wikidata sameAs

```sparql
PREFIX gndo: <https://d-nb.info/standards/elementset/gnd#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
SELECT ?s ?title ?wd WHERE {
  ?s gndo:preferredNameForTheWork ?title ;
     owl:sameAs ?wd .
  FILTER(STRSTARTS(STR(?wd), "http://www.wikidata.org/entity/"))
} LIMIT 20
```

## 12. dc:title encoding variation (ISBD punctuation coverage)

Show the split between ISBD-punctuated titles (containing " / " as proper-title/statement-of-responsibility separator) and bare titles, to illustrate inconsistent encoding across contributing institutions.

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX edm: <http://www.europeana.eu/schemas/edm/>

SELECT
  (SUM(IF(CONTAINS(?title, " / "), 1, 0)) AS ?isbd_slash)
  (SUM(IF(CONTAINS(?title, " : "), 1, 0)) AS ?isbd_colon)
  (SUM(IF(!CONTAINS(?title, " / ") && !CONTAINS(?title, " : "), 1, 0)) AS ?bare)
  (COUNT(?title) AS ?total)
WHERE {
  GRAPH <http://gemea.ddb.de/graph/ddbedm> {
    ?cho a edm:ProvidedCHO ;
         dc:title ?title .
  }
}
```

### 12.1 Sample ISBD-punctuated titles

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX edm: <http://www.europeana.eu/schemas/edm/>

SELECT ?title WHERE {
  GRAPH <http://gemea.ddb.de/graph/ddbedm> {
    ?cho a edm:ProvidedCHO ;
         dc:title ?title .
    FILTER(CONTAINS(?title, " / "))
  }
} LIMIT 20
```

### 12.2 Sample bare titles (no ISBD punctuation)

```sparql
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX edm: <http://www.europeana.eu/schemas/edm/>

SELECT ?title WHERE {
  GRAPH <http://gemea.ddb.de/graph/ddbedm> {
    ?cho a edm:ProvidedCHO ;
         dc:title ?title .
    FILTER(!CONTAINS(?title, " / ") && !CONTAINS(?title, " : ") && !CONTAINS(?title, " = "))
  }
} LIMIT 20
```

---

## 13. Corpus analysis — goethe-faust local QLever (port 7030)

Run via `curl http://localhost:7030`. Named graph: `https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm`.
Sector path: `edm:dataProvider → rdf:type → <http://ddb.vocnet.org/sparte/sparteXXX>`.

---

## 14. Sector distribution

How records are distributed across DDB sectors via `edm:dataProvider → rdf:type → sparte`.

```sparql
SELECT ?p ?sparte (COUNT(*) AS ?n)
WHERE {
  GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> {
    ?cho ?p ?inst .
    ?inst <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?sparte .
    FILTER(CONTAINS(STR(?sparte), "sparte"))
  }
}
GROUP BY ?p ?sparte
ORDER BY DESC(?n)
```

**Result (goethe-faust corpus):**

| Predicate | Sector | Records |
|---|---|---|
| edm:dataProvider | sparte001 (Archive) | 50,230 |
| edm:dataProvider | sparte002 (Library) | 50,214 |
| edm:dataProvider | sparte006 (Museum) | 9,216 |
| edm:dataProvider | sparte005 (Media Library) | 4,290 |
| edm:dataProvider | sparte004 (Research) | 1,283 |
| edm:aggregator | sparte007 (Others) | 198 |
| edm:dataProvider | sparte003 (Monument) | 112 |

---

## 15. dc:type IRI vs literal — library sector (sparte002)

> how many dc:type values in the ddbedm graph from sparte002 or libraries link to controlled vocabulary?

```sparql
SELECT ?kind (COUNT(?o) AS ?n)
WHERE {
  GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> {
    ?cho <http://purl.org/dc/elements/1.1/type> ?o .
    ?agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?cho .
    ?agg <http://www.europeana.eu/schemas/edm/dataProvider> ?inst .
    ?inst <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://ddb.vocnet.org/sparte/sparte002> .
    BIND(IF(isIRI(?o), "iri", "literal") AS ?kind)
  }
}
GROUP BY ?kind
```

**Result:** IRI (controlled vocab): 11,603 (35.8%) — literal (free text): 20,775 (64.2%) — total: 32,378

---

## 16. dc:type top values — archive sector (sparte001)

> what type of terms are in the dc:type of archive sectors sparte001?

```sparql
SELECT ?o (COUNT(*) AS ?n)
WHERE {
  GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> {
    ?cho <http://purl.org/dc/elements/1.1/type> ?o .
    ?agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?cho .
    ?agg <http://www.europeana.eu/schemas/edm/dataProvider> ?inst .
    ?inst <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://ddb.vocnet.org/sparte/sparte001> .
  }
}
GROUP BY ?o
ORDER BY DESC(?n)
LIMIT 20
```

**Result (top values):** Predominantly free-text German document-type labels ("Dokument", "Archivale",
"Urkunden", "Akten", "Schriftgut"). Small minority are Getty AAT IRIs (`vocab.getty.edu/aat/…`).
Note: these are document-type labels, not structural hierarchy codes — hierarchy signal in archive
records comes from `ddb:hierarchyType` (htype), not dc:type.

---

## 17. Goethe attribution anomaly — objects attributed to Goethe that may be collection items

> which objects are attributed to Goethe as a creator or contributor but could be only something he owned as part of his collection?

Cross-tab by sector and dc:type:

```sparql
SELECT ?sparte ?dctype (COUNT(DISTINCT ?cho) AS ?n)
WHERE {
  GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> {
    { ?cho <http://purl.org/dc/elements/1.1/creator> <http://d-nb.info/gnd/118540238> }
    UNION
    { ?cho <http://purl.org/dc/elements/1.1/contributor> <http://d-nb.info/gnd/118540238> }
    OPTIONAL { ?cho <http://purl.org/dc/elements/1.1/type> ?dctype }
    ?agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?cho .
    ?agg <http://www.europeana.eu/schemas/edm/dataProvider> ?inst .
    ?inst <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?sparte .
    FILTER(CONTAINS(STR(?sparte), "sparte"))
  }
}
GROUP BY ?sparte ?dctype
ORDER BY ?sparte DESC(?n)
```

Confirmed misattributions — museum records only:

```sparql
SELECT ?cho ?title ?type
WHERE {
  GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> {
    ?cho <http://purl.org/dc/elements/1.1/creator> <http://d-nb.info/gnd/118540238> .
    ?cho <http://purl.org/dc/elements/1.1/type> ?type .
    OPTIONAL { ?cho <http://purl.org/dc/elements/1.1/title> ?title }
    ?agg <http://www.europeana.eu/schemas/edm/aggregatedCHO> ?cho .
    ?agg <http://www.europeana.eu/schemas/edm/dataProvider> ?inst .
    ?inst <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> <http://ddb.vocnet.org/sparte/sparte006> .
  }
}
LIMIT 10
```

**Findings:** 120 museum records link Goethe's GND URI as creator. Titles follow the pattern
*Maker: Johann Wolfgang von Goethe* (e.g., "Kowalski, Klaus: Johann Wolfgang von Goethe",
"Bovy, Jean Francois Antoine: Johann Wolfgang von Goethe") — the depicted person was recorded
as creator, not the maker. Suspect types:

| Type | Count | Note |
|---|---|---|
| Prints (aat/300033973) | 51 | Portraits of Goethe |
| Inszenierung | 30 | Stage productions |
| Medaille | 5 | Commemorative medals |
| Plakette | 2 | Plaques |
| Prägewerkzeug | 2 | Minting dies |
| Papiergeld | 1 | Coins/banknotes |

Pattern is undetectable without cross-institution graph queries; used as worked example in
ISWC 2026 paper §5 (Metadata quality analysis).

## 18. Total triple count — gemea-qlever (2026-05-14)

```sparql
SELECT (COUNT(*) AS ?triples) WHERE { ?s ?p ?o }
```

**Endpoint:** `https://gemea.ise.fiz-karlsruhe.de/shmarql/` (note: `/sparql` redirects to ShmarQL UI; use `/shmarql/` for programmatic queries)

**Result:** 600,544,765 triples

## 19. Triple count per named graph — graph/ddbedm (2026-05-14)

```sparql
SELECT (COUNT(*) AS ?triples) WHERE { GRAPH <https://gemea.ise.fiz-karlsruhe.de/graph/ddbedm> { ?s ?p ?o } }
```

**Endpoint:** `https://gemea.ise.fiz-karlsruhe.de/shmarql/`

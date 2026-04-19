# SPARQL Query Examples

Example queries against the GeMeA SPARQL endpoint (`http://[host]:42004`).

> Substitute `[host]` with the actual hostname or IP of your deployment.

---

## Count all objects

```sparql
SELECT (COUNT(?s) AS ?count)
WHERE {
  ?s a <http://www.europeana.eu/schemas/edm/ProvidedCHO> .
}
```

---

## List objects by sector (Sparte)

```sparql
PREFIX edm: <http://www.europeana.eu/schemas/edm/>
PREFIX ddb: <https://www.deutsche-digitale-bibliothek.de/ns/emo/>

SELECT ?item ?title ?sector
WHERE {
  ?item a edm:ProvidedCHO ;
        <http://purl.org/dc/elements/1.1/title> ?title ;
        ddb:sector ?sector .
}
LIMIT 20
```

Sector codes: `sparte001` Archive · `sparte002` Library · `sparte003` Monument · `sparte004` Research · `sparte005` Media Library · `sparte006` Museum · `sparte007` Others

---

## Find objects linked to a GND entity

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?item ?title
WHERE {
  ?item <http://purl.org/dc/elements/1.1/title> ?title ;
        owl:sameAs <https://d-nb.info/gnd/118540238> .
}
LIMIT 10
```

---

## Objects with geo coordinates

```sparql
PREFIX geo: <http://www.w3.org/2003/01/geo/wgs84_pos#>

SELECT ?item ?lat ?lon
WHERE {
  ?item geo:lat ?lat ;
        geo:long ?lon .
}
LIMIT 20
```

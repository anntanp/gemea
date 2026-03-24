# Big-Picture Dumb Questions

## 1. How do we load 18M objects (1–3B triples) and run database-like queries?

### 1.1 Scale clarification

18 million EDM objects × 50–200 triples each = **~1–3 billion triples** total. This is large-scale RDF territory (Wikidata is ~15B triples).

Example query type: "how many objects are dated 1775–1800 where the title is shorter than usual (few tokens)?" — fundamentally an analytical/OLAP workload.

### 1.2 Options considered

**DuckDB from Parquet (fast for flat analytics, but doesn't scale here)**

- Works well at 18M rows if data is pre-flattened
- At 1–3B triples: denormalizing EDM's variable-length, multi-valued properties into a flat schema is high-complexity and loses the graph
- Best role: analytics side-table, not primary store

**QLever (right call for primary store)**

- Built for billions of triples; handles Wikidata (~15B) comfortably
- Load pipeline:
  ```bash
  # 1. Convert to N-Triples
  # 2. qlever index --input edm.nt  (sort + build binary index)
  # 3. qlever start
  ```
- Index build: 4–12 hours one-time (I/O bound), then millisecond–second SPARQL queries
- Weakness: string operations like token-counting are awkward in SPARQL

**HDT + Jena/SPARQL**

- Compresses RDF 10–15×, supports random-access; weaker on aggregation queries
- Better for archival + lightweight access than analytical workloads

**Virtuoso Open Source**

- Battle-tested at this scale (DBpedia, Bio2RDF)
- Slower bulk load than QLever; open-source version has known performance caps

### 1.3 Recommended architecture

QLever as primary store (full 1–3B triples) + a thin **DuckDB analytics layer** (1 row per object, pre-materialized):

```
QLever (full graph)
    ↓ SPARQL SELECT (run once / nightly)
DuckDB / Parquet (~18M rows)
    columns: id, title, token_count, year_start, year_end, type, provider, ...
```

Materialization query (SPARQL → DuckDB):

```sparql
SELECT ?id ?title ?year WHERE {
  ?id edm:year ?year ; dc:title ?title .
}
```

Analytical query (DuckDB):

```sql
SELECT count(*) FROM objects
WHERE year_start >= 1775 AND year_end <= 1800
  AND token_count < 4;
```

Pre-compute `token_count` at materialization time — don't compute it at query time in SPARQL.

This maps onto the existing pipeline: QLever + ES + DuckDB (DuckDB handles numerical/aggregate queries where full-text search isn't needed).

### 1.4 Bottom line

- **Primary store**: QLever — index build is a one-time cost, query performance is excellent
- **Analytics**: materialize key fields (year, token count, type, provider) into DuckDB
- **Avoid**: trying to flatten 1–3B triples into a single relational schema

# GND Werk — Data Observations

---

## 1. Author not embedded in work title

**Observation (2026-04-06):** In GND Werk, authorship is modelled as a separate linked entity via
`gndo:firstAuthor` (or `gndo:author`), not as a string embedded in `gndo:preferredNameForTheWork`.

**Example:** Goethe's *Faust, 1* (`gnd/4099197-0`) has:
- `preferredNameForTheWork` → `"Faust, 1"` — no mention of "Goethe"
- `firstAuthor` → `gnd/118540238` (= Goethe's person record)

A title search for "Goethe Faust" (FILTER on both terms in the same literal) therefore **misses the
canonical work** and returns only derivative works whose titles happen to contain both words
(e.g. *Kompositionen zu Goethes Faust*, *Szenen aus Goethes Faust*).

**Implication for GeMeA / `link_gnd_works.py`:** Title-only matching against `preferredNameForTheWork`
is insufficient for author-scoped retrieval. Queries must either:
1. Follow `firstAuthor` → person IRI and filter there, or
2. Use a two-hop pattern: `?work gndo:firstAuthor <gnd/author> ; gndo:preferredNameForTheWork ?title`.

**Variant names** (`gndo:variantNameForTheWork`) also do not contain author names — same limitation applies.

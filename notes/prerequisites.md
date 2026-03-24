# GeMeA — Prerequisites

CS concepts, algorithms, frameworks, design patterns, programming languages, and technical skills needed to build GeMeA independently.

---

## Semantic Web & Knowledge Graphs

- **RDF** (Resource Description Framework): triple model (subject–predicate–object), named graphs
- **SPARQL 1.1**: SELECT, CONSTRUCT, DESCRIBE, ASK; property paths; OPTIONAL; FILTER; aggregation; LIMIT/OFFSET; federated queries
- **OWL** (Web Ontology Language): classes, properties, restrictions, inference/reasoning basics
- **Europeana Data Model (EDM)**: ProvidedCHO, Aggregation, WebResource, Agent, Place, TimeSpan; edm:isShownAt, edm:hasView
- **RDA (Resource Description & Access)**: WEMI hierarchy (Work, Expression, Manifestation, Item); Group 2/3 entities
- **FRBR**: Functional Requirements for Bibliographic Records; entity groups
- **JSON-LD**: @context, @id, @type, @graph; compaction/expansion; Framing
- **RDF/JSON serialization** (W3C): subject-keyed object with predicate arrays
- **Turtle / N-Triples**: for bulk loading and data inspection
- **Named graphs / quads**: NQuads, TriG (for provenance tracking by provider/batch)
- **Namespace prefixes**: dc, dcterms, edm, ore, skos, rdfs, owl, foaf, schema, gnd, wikidata
- **SKOS mapping properties**: `skos:exactMatch` vs `skos:closeMatch` vs `owl:sameAs` — semantics, entailment differences, and when to use each; Halpin et al. (ISWC 2010) on `owl:sameAs` misuse in linked data
- **GND ontology** (`gndo:` namespace): Work/MusicalWork/Manuscript class hierarchy; `preferredNameForTheWork`, `variantNameForTheWork`; author predicate hierarchy (`gndo:author`, `gndo:firstAuthor` as subproperty, `gndo:poet`, `gndo:composer`); SPARQL does not infer `rdfs:subPropertyOf` without a reasoner — explicit `VALUES` required

## Graph Databases

- **QLever**: `qlever index` (build index from N-Triples), `qlever start` (launch server), Qleverfile configuration (`Mmap`, `num-threads`, `text-index`), SPARQL endpoint, built-in text search (`ql:contains-entity`), spatial queries, named graphs
- **Triplestore bulk load patterns**: N-Triples chunk loading, parallel load, checkpoint/restart
- **SPARQL query optimization**: LIMIT early, use named graphs, avoid Cartesian products, query timeout configuration
- **Fallback options** (self-hosting v2): Apache Jena TDB2 + Fuseki (tdbloader2, Fuseki server config); Virtuoso OSE (ISQL, `rdf_loader_run()`)

## Search & Information Retrieval

- **Elasticsearch 8.x**: index mapping, analyzers (standard, German language analyzer `de`), BM25 ranking, faceted search (terms aggregations), highlighting, `multi_match`, `query_string`, pagination (from/size, `search_after`)
- **Index design for cultural heritage**: field types (keyword vs. text), nested objects for multilingual fields, GeoPoint fields for geo-search
- **Faceted search UX**: facet selection, AND/OR logic, cardinality limits
- **Query federation**: combining Elasticsearch text results with SPARQL graph enrichment

## Backend (Python / FastAPI)

- **FastAPI**: path operations, async handlers, Pydantic models, dependency injection, middleware (CORS, caching)
- **SPARQL client**: `SPARQLWrapper` or `httpx` for async HTTP calls to QLever SPARQL endpoint
- **Elasticsearch Python client** (`elasticsearch-py 8.x`): async client, index lifecycle
- **Async Python**: `asyncio`, `httpx`, background tasks
- **Caching**: Redis for SPARQL result caching; HTTP cache headers (`Cache-Control`, ETags)
- **Pagination patterns**: cursor-based vs. offset for large result sets
- **API design**: REST conventions, OpenAPI/Swagger auto-docs, versioning (`/v1/`)

## Ontology Alignment & mocho

- **Ontology alignment**: mapping classes and properties between source ontology (EDM) and target ontology (RDA/FRBR); `owl:equivalentClass`, `owl:equivalentProperty`; SPARQL CONSTRUCT for rule-based transformation
- **mocho** (`../mocho/`): GeMeA's alignment tool; takes rdf2jsonld output + GND Werk triples → produces `mocho:Work` entities + RDA-normalized triples; mocho.owl is WIP
- **mocho:Work**: mocho-specific class grouping `edm:ProvidedCHO` instances that share a GND Werk URI; the grouping key is the GND Werk link produced by `link_gnd_works.py` (must run before mocho)
- **FRBR entity creation**: promoting a flat `edm:ProvidedCHO` record into the WEMI hierarchy (Work → Expression → Manifestation → Item); requires external authority linkage (GND Werktitel) to identify Work-level groupings
- **OWL reasoning**: forward chaining, materialization; difference between declarative alignment (reasoner applies equivalences) vs. procedural transformation (SPARQL CONSTRUCT rules)
- **rdf2jsonld** (`../rdf2jsonld/`): converts DDB JSON-LD → W3C RDF/JSON; repairs URI malformations; parallel processing per provider batch

## ETL / Data Engineering

- **RDF bulk loading**: mocho N-Triples → QLever index via `qlever index`
- **Named graph assignment**: partition by provider for manageability and per-provider reload
- **Python RDF libraries**: `rdflib` (parsing, serialization, graph manipulation)
- **Streaming / chunked processing**: process 65M records without loading all into memory (NDJSON, generators)
- **Elasticsearch bulk indexing**: `helpers.bulk()`, index rollover for large datasets
- **Process orchestration**: sequential shell scripts for v1; Luigi or Airflow for v2
- **Monitoring ingestion**: progress logging, checkpointing, error recovery

## Frontend (Next.js / React)

- **Next.js 14+**: App Router, server components, `fetch` with caching, dynamic routes (`/item/[id]`), ISR (Incremental Static Regeneration) for entity pages
- **React**: hooks (`useState`, `useEffect`, `useCallback`), context, server vs. client components
- **Tailwind CSS**: responsive design (`sm:`, `md:`, `lg:`), dark mode, component utility patterns
- **Search UX patterns**: debounced input, loading states, empty states, result highlighting
- **Facet sidebar**: collapsible sections, URL-synced state (`URLSearchParams`), keyboard accessibility

## Visualization

- **Cytoscape.js**: graph rendering in canvas/SVG, layout algorithms (COSE, Dagre, Breadthfirst), node/edge styling, event handling, performance with large graphs (virtual rendering)
- **Leaflet.js**: tile layers (OSM), marker clusters, GeoJSON overlays, popups, map bounds from data
- **D3.js** (timeline): time scales, brush/zoom, histogram of objects per year
- **Canvas vs. SVG**: SVG for small graphs (<500 nodes), canvas for large; Cytoscape handles both

## Data

- **DDB data model**: item-id, provider-info, view, index_profile, edm fields (see rdf2jsonld spec)
- **GND (Gemeinsame Normdatei)**: German authority file for agents, places, subjects; `d-nb.info/gnd/` URIs; QLever DNB SPARQL endpoint (`https://sparql.dnb.de/api/dnbgnd`); literal format (no `@de` tags on `preferredNameForTheWork`); Work class coverage (~580k entities across Work/MusicalWork/Manuscript)
- **ISBD punctuation encoding**: how DDB `dc:title` strings embed title, statement of responsibility, edition, and publication area in a single field using ` / `, `. - `, ` : ` as area separators; why raw strings produce low-precision GND matches
- **Wikidata**: linked entity URIs for enrichment
- **Geographic data**: WGS84 coordinates, GeoNames, TGN (Getty Thesaurus of Geographic Names)
- **Temporal data**: ISO 8601 dates, edm:TimeSpan, `sem:hasBeginTimeStamp` / `sem:hasEndTimeStamp`
- **CC BY 4.0**: license obligations for data display and redistribution

## DevOps & Infrastructure

- **Docker / Docker Compose**: containerize QLever, Elasticsearch, Redis, FastAPI, Next.js, Nginx
- **Nginx**: reverse proxy, TLS termination, security headers, rate limiting (`limit_req_zone`)
- **Environment variables**: secrets management (no hardcoded credentials)
- **Health checks**: `/health` endpoints for all services
- **Volume mounts**: persistent data for QLever index and Elasticsearch indices

## General CS

- **HTTP semantics**: status codes, content negotiation (`Accept: text/turtle`), CORS
- **Content negotiation**: serving HTML, JSON, Turtle, N-Triples from the same URI (Linked Data principles)
- **URI design**: `/item/{id}`, `/agent/{uri}`, `/place/{uri}` — stable, dereferenceable URIs
- **Pagination**: limit/offset tradeoffs at scale; cursor-based for Elasticsearch deep pagination
- **Internationalization (i18n)**: multilingual labels (German primary, English secondary); `lang` tags in RDF

## NLP & Named Entity Recognition

### Bibliographic NER fundamentals

- **NER task formulation**: sequence labeling (BIO/BIOES tags) vs. span extraction (start/end indices); why span extraction suits bibliographic NER (non-contiguous labels, variable-length spans, nested possible)
- **FRBR-based label hierarchy**: Work-level (`TITLE`, `OTHER_TITLE`, `PERSON`), Expression-level (`TRANSLATOR`, `PARALLEL_TITLE`, `MEDIUM`), Manifestation-level (`PUBLISHER`, `PLACE`, `YEAR`, `EDITION`, `SERIES`, `VOLUME`); why evaluation scope must be declared before gold set design
- **ISBD rule-based NER**: using ` / `, `. - `, ` : ` as split heuristics for title extraction; FP rate analysis per signal; why structural coverage is ~1.2% of corpus while heuristic coverage reaches ~8%
- **Silver labeling**: auto-labeling training data from heuristic rules; silver tier hierarchy (tier 2 = high-confidence structural, tier 1 = heuristic partial, tier 0 = no label); FP rate as the primary quality gate; why silver labels are not ground truth
- **Statement of Responsibility (SoR) disambiguation**: ` /` cue fires for PERSON, TRANSLATOR, corporate body, editor — requires sub-classification; FP rate ~36% for raw `f_person` heuristic; keyword-based disambiguation for TRANSLATOR (~"übersetzt", "Übers.", "transl.")
- **Author-before-title structure**: pre-1750 German bibliographic records place author name and credentials before the work title (not after ` /`); systematic false negative for ISBD-based PERSON detection; must be handled explicitly in annotation guidelines and prompts

### Models and architectures

- **Encoder-only NER (sequence labeling)**: BERT-style models (`xlm-roberta-large`, `mdeberta-v3-base`) with token classification head; why multilingual pretraining is preferred over monolingual German for historical text; `deberta-v3-large` is English-only — not applicable
- **Span extraction NER (GLiNER)**: joint encoding of entity type descriptions and input text; span scoring via dot product; handles arbitrary label definitions without retraining; max span width cap (K=12 tokens); O(n log n) decode; discontinuous entities not supported; Zaratiana et al. (NAACL 2024)
- **NuNER Zero**: GLiNER variant pretrained on 1M LLM-annotated C4 sentences for zero-shot transfer; concept and text encoders are separate (text encoder is a drop-in for BERT/RoBERTa); zero-shot performance not benchmarked in the EMNLP 2024 paper (Bogdanov et al.) — production zero-shot claims unverified; inference cost <$0.0001/example
- **Generative NER**: LLM (LLaMA, Qwen) + LoRA fine-tuning with structured output format; output format critically affects performance — Inline Bracketed/XML achieves F1 ~90–94 on CoNLL2003; JSON formats drop to 85–87; Offset-based JSON collapses (~30 F1); Zhan et al. (arXiv 2601.17898, 2026)
- **Zero-shot NER gap**: zero-shot LLMs score ~88 F1 on general-domain flat NER vs. ~93 for fine-tuned; gap widens in low-resource/specialized domains (GENIA biomedical: 79 vs. 84); expect similar or larger gap for historical German bibliographic NER
- **LoRA (Low-Rank Adaptation)**: parameter-efficient fine-tuning by injecting low-rank weight updates; rank r and scaling factor α are key hyperparameters; preserves general capabilities (MMLU, HellaSwag) with minor fluctuation (±3–4%) after NER fine-tuning (Zhan et al. 2026)

### Evaluation and datasets

- **HIPE-2022 (ajmc)**: historical document NER benchmark; German, French, English; fine-grained bibliographic reference labels; top systems used `xlm-roberta-large`; Ehrmann et al. (2022) — ⚠️ verify citation
- **CLEF-HIPE-2020**: historical newspaper NER; German, French, English; PROD label covers work titles; 19th-century orthography; XLM-R large dominant in top submissions; Ehrmann et al. (2020) — ⚠️ verify citation
- **CoNLL2003**: standard flat NER benchmark (PER, ORG, LOC, MISC); 4 labels, general English/German; used for model comparison in Zhan et al. (2026)
- **GLiNER zero-shot benchmark**: 7 CrossNER/MIT datasets; GLiNER-L (300M) avg F1 60.9 vs. GoLLIE-7B 58.0 and ChatGPT 47.5; entity-level exact match (not token-level)
- **MultiCONER multilingual**: GLiNER-Multi scores 39.5 F1 on German vs. ChatGPT 37.1; supervised XLM-R baseline 64.6 — ~25-point gap for zero-shot approaches
- **Evaluation metrics**: entity-level exact-match F1 (GLiNER) vs. token-level macro F1 (NuNER) — not directly comparable; always report which metric is used; track PERSON F1 on pre-1750 stratum separately from modern stratum
- **Fine-tuning dataset sizing**: rule of thumb ~200–500 annotated spans per entity type from a strong pretrained checkpoint; Work-only (3 types) needs ~1k–2k records; Work + Expression (6 types) needs ~3k–5k records

### LLM annotation (prompt engineering for NER)

- **Inline Bracketed format**: `[span text | LABEL]` — natural language-like, best-performing output format for generative NER (Zhan et al. 2026); use for LLM annotation of training data
- **Few-shot NER prompting**: include 5 annotated examples per structural pattern; examples must cover domain-specific edge cases (not generic CoNLL2003-style examples); draw from manually verified seed set
- **Systematic vs. random LLM errors**: LLMs make type errors (38.2% of errors) and over-extract (Completely-O: 25.2%); encoder models under-extract (Omitted Mentions: 45.5%); design evaluation to detect both failure modes
- **Spot-check protocol**: verify ~5% of LLM-annotated records manually; compute per-label F1; threshold 85% agreement before using batch as training data; if below threshold, revise prompt and re-run

---

## Corpus Analysis & Statistics

### Foundational probability and distributions (prerequisites for CI formulas)

These topics underpin everything in this section. Study them first if the CI formulas below are unclear.

- **Binomial distribution**: models the number of successes k in n independent Bernoulli trials, each with success probability p; `B(n, p)`; mean = np, variance = np(1−p); the FP rate study (k FPs in n sampled records) is a binomial experiment. *Reference: OpenIntro Statistics §3.3 (free at openintro.org/book/os/)*
- **Variance of a Bernoulli random variable**: for a single trial with success probability p, variance = p(1−p); this expression is maximised at p=0.5 (take derivative d/dp[p(1−p)] = 1−2p = 0, solve: p=0.5); at p=0.5 variance = 0.25; at p=0 or p=1 variance = 0; this is why p=0.5 is used as the worst-case assumption when p is unknown. *Reference: OpenIntro Statistics §3.4*
- **Central Limit Theorem (CLT)**: for large n, the sampling distribution of p̂ = k/n is approximately normal with mean p and standard deviation √(p(1−p)/n), regardless of the underlying distribution; this is what justifies using z-scores in the CI formula. Typically considered adequate for n·p ≥ 10 and n·(1−p) ≥ 10. *Reference: OpenIntro Statistics §4.1*
- **Normal distribution N(μ, σ²)**: a symmetric bell-shaped probability distribution fully described by its mean μ (centre) and variance σ² (spread); 68% of values fall within ±1σ, 95% within ±2σ, 99.7% within ±3σ. *Reference: OpenIntro Statistics §3.1*
- **Standardisation and z-scores**: any normal random variable X ~ N(μ, σ²) can be converted to a standard score z = (X − μ) / σ; z measures how many standard deviations X is above or below the mean; z=0 is the mean, z=1 is one standard deviation above, z=−1.96 is 1.96 standard deviations below. *Reference: OpenIntro Statistics §3.1*
- **Standard normal distribution N(0,1)**: a normal distribution with mean=0 and standard deviation=1; all z-scores live on this scale; the cumulative distribution function Φ(z) = P(Z ≤ z) gives the probability that a standard normal variable falls at or below z; look up in a z-table or compute `scipy.stats.norm.cdf(z)`. The inverse Φ⁻¹(p) gives the z-score at the p-th percentile: `scipy.stats.norm.ppf(p)`. *Reference: OpenIntro Statistics §3.1*
- **Two-sided 95% CI — what it means step by step**:
  1. You want an interval that captures 95% of the probability mass of the sampling distribution of p̂
  2. The remaining 5% (called α = 0.05) falls *outside* the interval
  3. "Two-sided" means you split that 5% equally between the left tail and the right tail: 2.5% each
  4. You need the z-value that marks the boundary of the upper 2.5% tail: Φ⁻¹(1 − 0.025) = Φ⁻¹(0.975) = **1.96**
  5. By symmetry, −1.96 marks the lower tail boundary
  6. So P(−1.96 ≤ Z ≤ 1.96) = 0.95 — exactly 95% of the standard normal distribution lies between −1.96 and +1.96
  7. The CI formula p̂ ± 1.96·SE then says: "the true p lies within 1.96 standard errors of our estimate, with 95% confidence"
  - *"Two-sided"* means you allow the true value to be either above or below your estimate — appropriate when you don't know in advance which direction the error goes
  - *"95% confidence"* means: if you repeated the sampling and CI construction many times, 95% of those intervals would contain the true p — it is a statement about the procedure, not about this specific interval
  - For a **one-sided** upper bound (e.g., "is FP rate below 15%?"), all 5% goes into one tail: z = Φ⁻¹(0.95) = 1.645
  - *Reference: OpenIntro Statistics §4.2*
- **Confidence level and α**: α = 1 − confidence level; α=0.05 for 95%, α=0.01 for 99%; for two-sided intervals use z = Φ⁻¹(1 − α/2); for 99% CI: z = Φ⁻¹(0.995) = 2.576. *Reference: OpenIntro Statistics §4.2*

### Proportion estimation and confidence intervals

- **Bernoulli trial model**: observed proportion p̂ = k/n is a point estimate of the true population proportion p; variance of the estimator is p(1−p)/n, maximised at p=0.5 and approaching zero near 0 or 1; this is why extreme proportions can be established with small samples
- **Wald interval**: p̂ ± z·√(p̂(1−p̂)/n); simple but unreliable when p̂ is near 0 or 1 — produces negative lower bounds, systematically undercovers the true proportion at the 95% level; do not use for FP rates or rare-class prevalence estimates
- **Wilson interval**: preferred for all proportion estimates in this project; conditions on a hypothetical true p rather than p̂; formula: (p̂ + z²/2n ± z·√(p̂(1−p̂)/n + z²/4n²)) / (1 + z²/n); always produces bounds in [0,1]; Wilson (1927), JASA 22(158), 209–212; use `statsmodels.stats.proportion.proportion_confint(k, n, method='wilson')` in Python
- **One-sided vs. two-sided intervals**: use two-sided (default) when estimating a proportion with unknown direction; use one-sided upper bound when the decision is "is this proportion below a threshold?" (e.g., "is FP rate below 15%?")

### Sample size determination

Sample size is not a universal constant — it depends on the decision being made, the expected proportion, and the acceptable error margin.

**For proportion estimation (given target margin of error e and confidence level 1−α):**

```
n = z² · p(1−p) / e²
```

where z = 1.96 for 95% CI. Because p is unknown, use p = 0.5 for the most conservative estimate (maximum variance). Examples:

| Target margin e | p = 0.5 (worst case) | p = 0.1 (rare class) | p = 0.9 (dominant class) |
|---|---|---|---|
| ±10% | n = 97 | n = 35 | n = 35 |
| ±5% | n = 385 | n = 139 | n = 139 |
| ±3% | n = 1,068 | n = 384 | n = 384 |
| ±1% | n = 9,604 | n = 3,458 | n = 3,458 |

Rule of thumb for FP rate studies: **n = 100–200 per heuristic signal** gives ±7–10% margin, sufficient for deciding whether to include or exclude a signal (the decision threshold is usually far from the observed rate). Derived from the Wald formula with two substitutions: (1) p=0.5, the worst-case value that maximises variance p(1−p) = 0.25 — any true FP rate will give a narrower interval; (2) z=1.96, the 97.5th percentile of the standard normal distribution corresponding to a two-sided 95% confidence level (i.e., α=0.05, z = Φ⁻¹(1−0.025) = 1.96). Substituting: n=100 → margin = 1.96×√(0.25/100) = ±9.8%; n=200 → margin = 1.96×√(0.25/200) = ±6.9%. No separate citation — this is an application of the standard proportion CI formula, not an empirically established NLP convention.

**For rare-class detection (is prevalence below threshold T?):**

The decision is one-sided: does the upper CI bound fall below T? With k=1 positive in n=200 (p̂=0.5%), the Wilson upper bound is 2.8% — sufficient to rule out a "5% Latin stratum" threshold. With k=0, the upper bound is 3·1/n (rule of three); for n=100 this gives an upper bound of 3%.

**Decision-relative sufficiency:** n is sufficient when the CI bound clears the decision threshold by a safe margin, regardless of CI width. The key question is not "is the CI narrow?" but "does the CI exclude the decision-relevant range?" Had SR-06 observed LATIN = 8% (near the 5% threshold), n=200 would not have been sufficient — wider CI would have straddled the threshold.

**For FP rate comparison between two signals:**

Use Fisher's exact test (small n) or chi-square test (n > 30 per cell) to test whether two signals have significantly different FP rates. In practice, if one signal is 6% FP and another is 83% FP, no formal test is needed — the difference is decision-relevant regardless of statistical significance.

**For inter-annotator agreement:**

- **Raw agreement rate**: proportion of records where two annotators agree; simple but ignores chance agreement
- **Cohen's κ**: κ = (P_o − P_e) / (1 − P_e), where P_o = observed agreement, P_e = expected agreement by chance; κ > 0.8 = strong agreement; κ 0.6–0.8 = moderate; κ < 0.6 = weak; preferred over raw agreement for annotation quality assessment
- **Practical threshold for LLM annotation spot-check**: raw span-level F1 ≥ 85% (per SR-11 protocol) is a reasonable proxy; Cohen's κ is more principled but requires a two-annotator setup

### Threshold definition

Thresholds in this project are decision thresholds, not statistical significance thresholds. They must be set before observing the data and justified by the decision consequences.

**FP rate acceptance threshold (heuristic signals, SR-03):**

The acceptance threshold of ~15% FP was chosen based on training data economics: a silver label with ≤15% FP contributes more correct signal than noise; above 15%, the false labels begin to dominate learning. This is a practical engineering heuristic, not a theoretically derived value. It implies that for every 100 labels with 15% FP, the model sees 85 correct and 15 incorrect training examples — analogous to label smoothing in the range 0.1–0.2, which is empirically acceptable.

**Exclusion threshold (SR-05 trailing period):** set at 15% FP — same reasoning as above. Trailing period showed 93% FP, far beyond the threshold.

**Agreement threshold for LLM annotation (SR-11):** 85% span-level F1 against a manually annotated reference set before running the full batch. Rationale: below 85%, LLM errors are likely systematic (not random noise) — a prompt revision will improve the whole batch, not just a few records.

**NuNER Zero decision gate (SR-08):** threshold TBD — to be set after reviewing SR-09 gold set F1 distribution; candidate values are precision ≥ 0.80 on TITLE and PERSON (Work-level), or F1 ≥ 0.75 on the pre-1750 stratum.

**Stratification cutoffs (SR-10, title length):** p25 = 4 tokens (short), p75 = 14 tokens (long); quartile-based, not domain-specific — chosen to ensure each stratum contains ~25% of the corpus, balancing stratum sizes for gold set sampling.

### Stratified sampling design

- **Proportional allocation**: sample from each stratum in proportion to its size in the population; appropriate when estimating corpus-wide prevalence; gives large strata more influence
- **Equal allocation**: sample the same n from each stratum regardless of stratum size; appropriate when each stratum needs independent analysis and a small stratum must contribute meaningfully (SR-06: Leichenpredigt n=100 despite being 6% of the combined sample vs. proportional ~12 records)
- **Optimal (Neyman) allocation**: sample proportional to stratum size × stratum standard deviation; minimises overall variance for fixed total n; requires prior estimate of within-stratum variance — impractical for first-pass corpus studies
- **Effective sample size with stratification**: stratified samples are more precise than simple random samples when within-stratum variance < total variance; the design effect (DEFF) = variance(stratified) / variance(SRS) is typically < 1 for well-chosen strata
- **Seed for reproducibility**: always set `random_state=42` (or equivalent) in `df.sample()`; log the seed alongside the results

### Script patterns for corpus analysis

- **Sampling**: `df.sample(n=100, random_state=42)` for uniform random; `df.groupby('stratum').apply(lambda x: x.sample(min(n, len(x)), random_state=42))` for stratified equal
- **Wilson CI in Python**: `from statsmodels.stats.proportion import proportion_confint; low, high = proportion_confint(k, n, alpha=0.05, method='wilson')`
- **Confusion matrix**: `sklearn.metrics.confusion_matrix(y_true, y_pred, labels=[...])` + `classification_report` for per-class precision/recall/F1
- **Cohen's κ**: `sklearn.metrics.cohen_kappa_score(annotator_a, annotator_b)`
- **FP rate per signal**: group by signal flag, compute `(true_class != signal_intended_class).mean()` per group

---

## Early Modern German

- **Orthographic features**: u/v interchange (`vnd` = und, `vnser` = unser), i/j interchange, final -en/-enn variation, ck clusters (`drucken`, `Stück`), double vowels (`seelig`, `heer`), genitive `deß` = des; standard pre-1750 forms, not errors
- **Title page conventions**: author credentials + name + role description appear before the work title (not after ` /`); credential sequence includes degree abbreviation (D., M., Lic., Mag.), full name, and post ("Pfarrers zu X", "Professoris zu Jena"); stop PERSON span at first content noun of the title
- **Genre conventions**: Leichenpredigt (funerary sermon, 1600–1750) — funeral occasion, deceased's name, preacher's name, scriptural text; academic dissertations — respondent + praeses names, thesis title in Latin; legal/administrative monographs — dedicatee, petition occasion
- **Embedded Latin vocabulary**: `Anno`, `Christi`, `Jesu`, `Doctor`, `Oratio`, `Disputatio`, `Theses` in otherwise German titles — standard Protestant/academic vocabulary, not Latin-language records; true Latin prevalence in pre-1800 Monografie/Leichenpredigt: ~0.5% (SR-06)
- **"Das ist:" construction**: introduces a German-language subtitle after a Latin or abbreviated main title; signals an OTHER_TITLE span
- **Language classifier heuristics and failure modes**: `Anno` + pre-1600 year → false LATIN (date label); `Christi`/`Jesu`/`Doctor` in Leichenpredigt → false LATIN (Protestant devotional vocabulary); `[ck]h\w+` cluster → false EARLY_MODERN_DE on modern German words (`Heilige`, `nach`); `Herrn` → false EARLY_MODERN_DE (also modern German)
- **Tokenisation challenges**: non-standard orthography tokenised differently by modern German tokenisers (`de_core_news_sm`); `vnd` not in vocabulary; compound splitting may fail on early modern compounds; median title length pre-1750 is 12–15 tokens (long-form), some >50 tokens

---

## Entity Linking

- **Entity linking pipeline**: candidate generation → candidate ranking → threshold filtering → output (URI or unresolved); match type taxonomy: exact / normalized / fuzzy / unresolved (Shen, Wang & Han, IEEE TKDE 27(2), 2015)
- **Levenshtein distance**: edit distance (insertions, deletions, substitutions); threshold ≤2 for fuzzy match in bibliographic entity linking; Levenshtein (Soviet Physics Doklady, 1966)
- **String normalization for matching**: Unicode NFC normalization → lowercase → NFD decomposition → strip combining characters (category `Mn`) → diacritic stripping (ä→a, ü→u, ö→o, ß→ss); LCASE in SPARQL is case-fold only — does not strip diacritics; endpoint-side diacritic normalization must be tested empirically (OQ-01)
- **Stopword removal for candidate generation**: remove grammatical function words to maximize discriminating power; `contains-word` with multiple tokens is AND semantics — more tokens = higher precision, lower recall; target 2–3 distinctive tokens; prefer nouns and proper nouns over generic title words
- **Generic title word filtering**: empirically validate which words are high-collision in the target KG (e.g., `werke` = 3,212 GND Work entries as full preferred name); derive `GENERIC_TITLE_WORDS` from a frequency query, not by assumption
- **`rdfs:subPropertyOf` and SPARQL**: SPARQL 1.1 does not perform property hierarchy inference without an OWL reasoner; must enumerate subproperties explicitly via `VALUES` (e.g., `gndo:firstAuthor` is a subproperty of `gndo:author` — a SPARQL query on `gndo:author` will not return triples using `gndo:firstAuthor`)
- **Async batch querying**: `asyncio.Semaphore` for concurrency control against a public SPARQL endpoint; `httpx.AsyncClient` for async HTTP; rate limit profiling before full batch run; timeout handling and retry logic
- **SPARQL FILTER string operations**: `LCASE(STR(?var))` for case-insensitive comparison; `lang(?var)` to check language tags; `STR()` to convert typed literals to plain strings for comparison

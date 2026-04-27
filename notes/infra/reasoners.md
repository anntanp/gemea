## 1. OWL Reasoners for mocho + GeMeA

### 1.1 Key surveys

- **Dentler et al. (2011)** — comparison for OWL 2 EL on large ontologies; benchmark suite still referenced widely.
- **ORE workshops (2012–2014)** — annual OWL Reasoner Evaluation with standardized benchmarks across all OWL 2 profiles. Best empirical source.
- **Steigmiller et al. (2014)** — introduces Konclude with comparisons against HermiT, FaCT++, Pellet.
- **Kazakov et al. (2014)** — ELK paper; motivates consequence-based reasoning for EL at scale.

### 1.2 Reasoners and trade-offs

| Reasoner | Profile | Algorithm | Speed | Scale | Notes |
|---|---|---|---|---|---|
| **HermiT** | OWL 2 DL | Hypertableau | Slow | Poor | Most complete; best correctness guarantees |
| **FaCT++** | OWL 2 DL | Optimised tableau | Fast for TBox | Medium | Strong TBox classification; C++ |
| **Pellet / Openllet** | OWL 2 DL | Tableau | Medium | Medium | Explanation support; DL-safe rules; actively maintained fork |
| **ELK** | OWL 2 EL | Consequence-based | Very fast | Excellent | Parallel; handles SNOMED CT (300k+ classes); no DL expressivity |
| **Konclude** | OWL 2 DL | Parallel tableau | Fast | Good | Best DL reasoner for large TBoxes; less maintained |
| **Whelk** | OWL 2 EL | Consequence-based | Fast | Good | JVM; integrates with ROBOT/ODK pipeline |

### 1.3 Recommendation for mocho + GeMeA

**mocho requires OWL 2 DL.** Inspection of `mocho-full.owl` confirms DL-only constructs:

| Construct | Count | EL? |
|---|---|---|
| `owl:allValuesFrom` | 23 | No |
| `owl:cardinality` | 10 | No |
| `owl:maxQualifiedCardinality` | 2 | No |
| `owl:complementOf` | 1 | No |
| `owl:disjointWith` | 11 | No |
| `owl:propertyChainAxiom` | 14 | Partial |

ELK will reject this ontology. Use **Openllet** as the primary reasoner (best-maintained DL reasoner, active fork of Pellet, integrates with ROBOT). Fall back to **Konclude** if TBox classification becomes a bottleneck.

**GeMeA** uses QLever, which has no built-in OWL reasoner. Materialise inferences offline and load the result into QLever — do not rely on runtime reasoning from the triplestore.

**Why Openllet over Konclude:**

- **Maintenance**: Openllet (Clark & Parsia fork) is actively maintained; Konclude's last release is 2020.
- **ROBOT integration**: `robot reason --reasoner Openllet` works out of the box; Konclude requires a separate server or CLI invocation outside the ODK pipeline.
- **Debugging**: Openllet has explanation support — when reasoning fails or produces unexpected inferences, you can ask why. Konclude has no such tooling.
- **Scale**: Konclude's parallel tableau pays off on very large TBoxes. mocho has 334 classes and 456 object properties — not the scale where that advantage materialises.

Use Konclude only if Openllet proves too slow in practice.

**Pipeline**: `robot reason --reasoner Openllet` as part of the mocho build → load materialised triples into QLever.

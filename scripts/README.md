# scripts/

Standalone operational scripts for GeMeA. Each script is self-contained with a header comment.

## Conventions

Every script must begin with:
```
# Purpose:      one-line description
# Usage:        how to invoke
# Inputs:       what it reads
# Outputs:      what it writes
# Dependencies: external tools / packages required
# Assumptions:  preconditions
```

Scripts use `argparse` for CLI arguments. Place all scripts here; document them below when added.

## Index

| Script | Purpose |
|--------|---------|
| `download_data.sh` | Fetch mocho-normalized RDF from public data dump |
| `setup_gnd_fuseki.sh` | (deprecated) Start local Fuseki container and load GND authority files |
| `setup_gnd_qlever.sh` | Convert GND JSON-LD to N-Triples, build QLever index, start SPARQL server |
| `jsonld_to_nt.py` | Convert a JSON-LD file (.jsonld or .jsonld.gz) to N-Triples using rdflib |
| `check_generic_title_words.py` | Query DNB SPARQL endpoint to count GND Work records per GENERIC_TITLE_WORD; validates which words are high-collision and should be excluded from distinctive token selection |
| `check_isbd_titles.py` | Analyse ISBD punctuation patterns in DF_DE_TITLES; reports per-pattern counts and sample titles |
| `rate_isbd_fields.py` | Rate all 4.47M DF_DE_TITLES records for the presence of bibliographic fields (TITLE, PERSON, PUBLISHER, PLACE, YEAR, EDITION, SERIES, VOLUME) using ISBD rules; assigns silver_tier for NER training data selection; optionally writes per-pattern examples with DDB links |

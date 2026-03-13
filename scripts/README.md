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
| `setup_gnd_fuseki.sh` | Start local Fuseki container and load GND authority files into named graphs |

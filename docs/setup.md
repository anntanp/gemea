# Self-Hosting GeMeA

## Prerequisites

- Docker ≥ 24 and Docker Compose v2
- ~50 GB free disk space for the EDM KG index
- Ports 42003–42006 available

## Quick start

```bash
git clone https://git.xorwell.de/at/gemea-claude.git
cd gemea-claude
docker compose -f docker/edm-stack.yml up -d
```

Services started:

| Service | Port | Description |
|---------|------|-------------|
| QLever EDM | 42004 | SPARQL endpoint over EDM KG |
| SHMARQL | 42003 | Linked Data browser |
| MCPO | 42005 | MCP interface for AI agents |
| QLever GND | 42006 | SPARQL endpoint over GND index |

## Loading the data

> Detailed instructions in `ingest/README.md`.

```bash
# Download DVC-tracked data pointers
dvc pull data/

# Run the QLever load pipeline
bash ingest/load-edm.sh
bash ingest/load-gnd.sh
```

## Stopping

```bash
docker compose -f docker/edm-stack.yml down
```

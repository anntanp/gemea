# mcp-server-qlever — GND Werk Setup

## 1. Overview

[mcp-server-qlever](https://github.com/XORwell/mcp-server-qlever) is a TypeScript MCP server
(MIT, Christian Nennemann) that connects Claude Code to any QLever SPARQL endpoint. It exposes
12 tools + 2 prompts over MCP stdio transport.

- **Source**: `~/Documents/claude/mcp-server-qlever/`
- **QLever endpoint** (once running): `http://localhost:7020`
- **Data**: GND Werk authority dump (DNB, CC0) — ~3.5M triples

---

## 2. Tools exposed

| Tool | Purpose |
|------|---------|
| `sparql_query` | Execute SPARQL → formatted text |
| `sparql_query_json` | Execute SPARQL → raw JSON |
| `get_index_stats` | Triple count, predicates, etc. |
| `describe_entity` | All triples for an IRI |
| `search_entities` | Full-text label search |
| `get_predicates` | Predicates by frequency |
| `sparql_autocomplete` | Context-sensitive autocomplete via `/ac` |
| `analyze_query` | Query plan without execution |
| `list_named_graphs` | Named graphs with triple counts |
| `search_fulltext` | Entity–keyword co-occurrence (text index) |
| `spatial_query` | Geographic radius / bounding-box search |
| `sparql_update` | SPARQL 1.1 Update (needs access token) |

---

## 3. One-time data preparation

### 3.1 Convert JSON-LD → N-Triples

Source file: `data/gnd/authorities-gnd-werk_lds.jsonld.gz` (85 MB gz, 1.4 GB uncompressed)
Output: `data/gnd/nt/werk.nt`

```bash
cd ~/Documents/claude/gemea
python3 ../mcp-server-qlever/scripts/jsonld-to-nt.py \
  --input data/gnd/authorities-gnd-werk_lds.jsonld.gz \
  --stats \
  > data/gnd/nt/werk.nt
```

Uses `ijson` for streaming (install: `pip install ijson`). Expects ~3.5M triples.

---

## 4. Running QLever

```bash
cd ~/Documents/claude/gemea

# First run: builds index (~5–10 min), then serves
docker compose -f docker-compose.qlever-gnd.yml up -d --wait

# Check it's up:
curl http://localhost:7020/?cmd=stats
```

Index is persisted in Docker volume `gemea-gnd-index`. Subsequent starts are instant.

To stop:
```bash
docker compose -f docker-compose.qlever-gnd.yml down
```

To wipe the index and rebuild:
```bash
docker compose -f docker-compose.qlever-gnd.yml down -v
docker compose -f docker-compose.qlever-gnd.yml up -d --wait
```

---

## 5. Registering the MCP server

Node.js is not installed locally — use the Docker image instead.

### Project-scoped (gemea project)

```bash
claude mcp add gnd-werk -- docker run --rm -i --network=host \
  ghcr.io/xorwell/mcp-server-qlever:latest -e http://localhost:7020
```

### Or add to `.claude/settings.json` manually

```json
{
  "mcpServers": {
    "gnd-werk": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i", "--network=host",
        "ghcr.io/xorwell/mcp-server-qlever:latest",
        "-e", "http://localhost:7020"
      ]
    }
  }
}
```

Verify: `claude mcp list`

---

## 6. Runtime requirements

| Component | How it runs |
|-----------|------------|
| QLever SPARQL engine | Docker (`adfreiburg/qlever`) on port 7020 |
| mcp-server-qlever | Docker (`ghcr.io/xorwell/mcp-server-qlever`) via stdio |
| ijson (conversion only) | System Python 3 (`pip install ijson`) |

No local Node.js required.

---

## 7. Current state (2026-04-06)

- `werk.nt`: `data/gnd/nt/werk.nt` — 12,055,580 triples, 1.5 GB
- QLever index: `data/gnd/qlever-index/` (bind-mount, persisted on host)
- MCP registration: project-scoped to `~/Documents/claude/gemea` in `~/.claude.json`

The MCP server is **project-scoped**: the `gnd-werk` tools only appear in Claude Code
sessions opened inside `~/Documents/claude/gemea/`. In any other directory they are not visible.

---

## 8. Day-to-day workflow

```bash
cd ~/Documents/claude/gemea

# Start QLever (must be running before opening a Claude session that uses MCP):
docker compose -f docker-compose.qlever-gnd.yml up -d

# Stop QLever:
docker compose -f docker-compose.qlever-gnd.yml down

# Wipe index and rebuild from werk.nt:
docker compose -f docker-compose.qlever-gnd.yml down -v   # removes data/gnd/qlever-index contents
docker compose -f docker-compose.qlever-gnd.yml up -d

# Check endpoint is live:
curl -sf http://localhost:7020/?cmd=stats | python3 -c "import sys,json; s=json.load(sys.stdin); print('triples:', s['num-triples-normal'])"
```

> **Note on `-v` / wipe**: `down -v` here removes a named Docker volume if any exist.
> Since we use a bind mount (`./data/gnd/qlever-index`), you need to delete the directory manually:
> `rm -rf data/gnd/qlever-index && mkdir data/gnd/qlever-index`
> then `docker compose -f docker-compose.qlever-gnd.yml up -d`.

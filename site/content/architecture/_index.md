---
title: "Architecture"
description: "How GeMeA is built: ingest pipeline, runtime access, and self-hosting"
showTableOfContents: true
---

GeMeA is built as a two-stage system: a build-time **ingest pipeline** that transforms DDB JSON records into named-graph N-Quads and loads them into QLever, and a set of **runtime access layers** served from `gemea.ise.fiz-karlsruhe.de`.

---

## Ingest pipeline

```
DDB Search API ──► fetch IDs ──► fetch JSON records
                                       │
                                       ▼
                              SQLite (per sector)
                                       │
                         scripts/transform/ (Phase 1)
                         EDM → mocho alignment
                                       │
                                       ▼
                              N-Quads (named graphs)
                                       │
                              qlever index build
```

Records are fetched via the DDB Search API filtered to `digitalisat:true` (digitised objects only). Each sector is processed independently and stored in a per-sector SQLite cache before being transformed into N-Quads.

---

## Runtime access

{{< mermaid >}}
flowchart LR
    User([User])

    subgraph SPARQL["SPARQL Backend\n(gemea.ise.fiz-karlsruhe.de)"]
        direction TB
        QL[QLever\nSPARQL endpoint]
        SHMARQL[SHMARQL\nLinked Data browser]
        SHMARQL -->|SPARQL proxy| QL
    end

    subgraph COM["Commercial client"]
        CL[Claude]
        TC[mcp-server-qlever]
        CL -->|MCP| TC
    end

    subgraph OSS["Open-source client\n(self-hosted)"]
        OW[OpenWebUI]
        OL[Ollama]
        MCPO[MCPO]
        T[mcp-server-qlever]
        OW -->|inference| OL
        OL -->|open-source LLM| OW
        OW -->|tool call| MCPO
        MCPO -->|MCP stdio| T
    end

    User -->|chat| CL
    User -->|chat| OW
    User -->|browse| SHMARQL
    TC -->|SPARQL GET| QL
    QL -->|JSON results| TC
    T -->|SPARQL GET| QL
    QL -->|JSON results| T
{{< /mermaid >}}

---

## Tech stack

| Component | Technology |
|---|---|
| Graph database | [QLever](https://github.com/ad-freiburg/qlever) — high-performance SPARQL engine |
| Linked Data browser | [SHMARQL](https://github.com/epoz/shmarql) — dereferenceable LD + SPARQL endpoint |
| Ontology alignment | [mocho](https://github.com/ISE-FIZKarlsruhe/mocho) — mid-level cultural heritage ontology |
| MCP interface | [mcp-server-qlever](https://github.com/xorwell/mcp-server-qlever) |
| Deployment | Docker Compose |

---

## Self-hosting

The SPARQL endpoint is available at `https://gemea.ise.fiz-karlsruhe.de/shmarql/` — no setup required to query it. To run the full stack locally, download the N-Quads dump and use `docker-compose.qlever.yml` from the [GitHub repository](https://github.com/ise-fizkarlsruhe/gemea).

### Query via Claude (commercial)

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "gemea-qlever": {
      "command": "docker",
      "args": ["run", "--rm", "-i",
               "ghcr.io/xorwell/mcp-server-qlever:latest",
               "-e", "https://gemea.ise.fiz-karlsruhe.de/shmarql/"]
    }
  }
}
```

### Query via Ollama + OpenWebUI (open-source)

1. Install [Ollama](https://ollama.com/download) and pull a model: `ollama pull gemma4:e4b`
2. Start OpenWebUI: `docker compose -f docker-compose.openwebui.yml up -d`
3. Open `http://localhost:3000`, go to **Admin → Settings → Tools**, and add the MCPO tool server URL: `https://gemea.ise.fiz-karlsruhe.de/shmarql/`

---

## Goethe–Faust proof of concept

The alignment and dispatch logic were developed and validated on the Goethe–Faust sub-corpus — 115,432 DDB records retrieved via the keywords *Goethe* and *Faust* — before scaling to the full 26.8M-object collection. Corpus analysis scripts, outputs, and design decisions are in [`goethe-faust/`](https://github.com/ise-fizkarlsruhe/gemea/tree/main/goethe-faust) in the repository.

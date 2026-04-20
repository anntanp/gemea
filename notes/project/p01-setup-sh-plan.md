# P01: gemea/setup.sh + config.env.example

## Context

P01 unblocks T02 (adapt docker-compose stack) and T04 (`mcp-add` inventory). GeMeA replicates the goethe-faust service pattern — QLever + SHMARQL + MCPO — at 26M-object scale, with a separate GND QLever stack. Neither `setup.sh` nor `config.env.example` exist yet in `gemea/`.

## Files to create

| File | Purpose |
|------|---------|
| `gemea/setup.sh` | Two-stack start/stop script |
| `gemea/config.env.example` | Template with GeMeA defaults for both stacks |

## Source to adapt

- `/Users/mta/Documents/claude/goethe-faust/setup.sh` — exact patterns for env loading, runtime env file, compose wrapper, check_prereqs, cmd_up, cmd_logs, cmd_mcp_add
- `/Users/mta/Documents/claude/goethe-faust/config.env.example` — comment style
- `/Users/mta/Documents/claude/gemea/docker-compose.qlever-gnd.yml` — GND service name (`qlever-gnd-werk`), port var (`${QLEVER_PORT:-7020}`)

## Design

### Two-arg dispatch

```
./setup.sh edm <up|down|status|logs|mcp-add>
./setup.sh gnd <up|down|status|logs|mcp-add>
```

### Stack defaults

| Variable | EDM | GND |
|----------|-----|-----|
| Port (QLever) | 42004 | 42006 |
| Port (SHMARQL) | 42003 | — |
| Port (MCPO) | 42005 | — |
| NT_INPUT | `data/out/s2/` | `data/gnd/nt/` |
| INDEX_DIR | `data/qlever-index` | `data/gnd/qlever-index` |
| LOG_DIR | `data/logs/edm` | `data/logs/gnd` |
| QLEVER_MEMORY | 16GB | 16GB |
| INDEX_NAME | `gemea` | `gnd` |
| MCP name | `gemea-edm` | `gemea-gnd` |
| Compose file | `docker-compose.qlever.yml` (P02) | `docker-compose.qlever-gnd.yml` (exists) |

### Runtime env files

`setup_edm()` writes `.env.runtime.edm`; `setup_gnd()` writes `.env.runtime.gnd`. Both use **unprefixed** var names (`QLEVER_PORT`, not `EDM_QLEVER_PORT`) to match docker compose variable references.

Critical for GND: the existing compose uses `${QLEVER_PORT:-7020}`. Passing `QLEVER_PORT=42006` via `--env-file .env.runtime.gnd` overrides the default without modifying the compose file.

### Service names (for `logs` dispatch)

- EDM: `qlever-gemea`, `shmarql`, `mcpo`
- GND: `qlever-gnd-werk` (taken from existing compose)

### check_prereqs

- EDM: docker, docker compose, `.nt` files in `data/out/s2/`, and `docker-compose.qlever.yml` exists (guard for P02 not yet done)
- GND: docker, docker compose, `data/gnd/nt/werk.nt` non-empty (uses `-s` flag, consistent with GND compose entrypoint check)

### config.env.example structure

Two sections: `# EDM stack` and `# GND stack`, each with Port, Input data, Directories, QLever tuning subsections. Note on `GND_INDEX_NAME`: compose hardcodes `gnd-werk` in entrypoint; this var has no effect until P03.

## Implementation steps

1. Write `gemea/config.env.example` — no dependencies, verify visually
2. Write `gemea/setup.sh` — adapt goethe-faust patterns; use `EDM_`/`GND_` prefixed defaults in script, unprefixed names in runtime env files
3. `chmod +x gemea/setup.sh`
4. Check `gemea/.gitignore` — add `config.env`, `.env.runtime.edm`, `.env.runtime.gnd` if missing

## Verification

```bash
# Should print usage and exit 1
./setup.sh

# Should print compose ps for GND (containers may not be running, that's fine)
./setup.sh gnd status

# Should print EDM compose ps — will error if docker-compose.qlever.yml missing (expected until P02)
./setup.sh edm status
```

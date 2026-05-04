# GND QLever MCP Setup Plan

**Date**: 2026-05-05  
**Context**: Configure `mcp-server-qlever` for the GND QLever instance at
`https://gnd.ise.fiz-karlsruhe.de/sparql` in Claude Code, for use across
goethe-faust, mocho, and gemea projects. Plan feeds into `setup.sh` for
self-hosting deployment (see `setup-vps-plan.md §1`).

---

## 1. Server

**Image**: `ghcr.io/xorwell/mcp-server-qlever:latest` (stdio transport; Docker required)  
**Transport**: stdio — runs as a local subprocess; QLever endpoint is plain HTTPS.

**Endpoints**:

| MCP server name | URL | Status |
|---|---|---|
| `gnd-qlever` | `https://gnd.ise.fiz-karlsruhe.de/sparql` | live |
| `gemea-qlever` | `https://gemea.ise.fiz-karlsruhe.de/sparql` | Phase 2 (setup-vps-plan.md §2) |

---

## 2. Option A — Global (`~/.claude/settings.json`)

Available in every Claude Code session on the machine.

```json
{
  "mcpServers": {
    "gnd-qlever": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "ghcr.io/xorwell/mcp-server-qlever:latest",
        "-e", "https://gnd.ise.fiz-karlsruhe.de/sparql"
      ]
    }
  }
}
```

**Trade-off**: single edit; Docker container starts for every Claude Code session regardless of project.

---

## 3. Option B — Scoped (per-project `.claude/settings.json`)

Same `mcpServers` block written into each of three project settings files:

| Project | Settings file |
|---|---|
| `goethe-faust` | `~/Documents/claude/goethe-faust/.claude/settings.json` |
| `mocho` | `~/Documents/claude/mocho/.claude/settings.json` |
| `gemea` | `~/Documents/claude/gemea/.claude/settings.json` |

**Trade-off**: MCP only active in the three relevant projects; requires merging into three files.

---

## 4. Recommendation

**Option B (scoped)**. GND SPARQL queries are only relevant in these three projects.
Global activation starts Docker for unrelated sessions.

When the GeMeA endpoint goes live (Phase 2), add `gemea-qlever` to the same three files.

---

## 5. `setup.sh` actions (self-hosting users)

Steps for the downloadable self-hosting script:

1. Check `docker info` — exit with install hint if Docker unavailable
2. `docker pull ghcr.io/xorwell/mcp-server-qlever:latest`
3. Prompt: **global** or **scoped**?
   - Global → merge `mcpServers` block into `~/.claude/settings.json`
   - Scoped → prompt for project root(s); merge into `<project>/.claude/settings.json` for each
4. Merge via `jq` (idempotent, preserves existing keys):

```bash
TARGET="$HOME/.claude/settings.json"   # or per-project path

# Create file if missing
[ -f "$TARGET" ] || echo '{}' > "$TARGET"

jq '.mcpServers["gnd-qlever"] = {
  "command": "docker",
  "args": ["run","--rm","-i",
           "ghcr.io/xorwell/mcp-server-qlever:latest",
           "-e","https://gnd.ise.fiz-karlsruhe.de/sparql"]
}' "$TARGET" > "$TARGET.tmp" && mv "$TARGET.tmp" "$TARGET"
```

5. Verify: `claude mcp list` — confirm `gnd-qlever` appears

---

## 6. Hooks

Claude Code supports `PreToolUse` and `PostToolUse` hooks that fire around any tool
call, including MCP tools. MCP tool names follow the pattern
`mcp__<server-name>__<tool-name>`, so `gnd-qlever` tools match on `mcp__gnd-qlever__`.

| Hook | When it fires | Common use |
|---|---|---|
| `PreToolUse` | Before the MCP tool runs | Log query, validate, block |
| `PostToolUse` | After the MCP tool returns | Log result, audit trail |

`PreToolUse` can **block** the call by exiting non-zero.

### 6.1 Example — auto-log SPARQL queries (gemea)

Automates the gemea CLAUDE.md rule: "write the query to
`notes/mcp-server-qlever/sparql-exploration.md` before executing."

```json
"hooks": {
  "PreToolUse": [
    {
      "matcher": "mcp__gnd-qlever__",
      "hooks": [
        {
          "type": "command",
          "command": "echo \"$(date -u +%Y-%m-%dT%H:%M:%SZ) $TOOL_INPUT\" >> ~/Documents/claude/gemea/notes/mcp-server-qlever/sparql-exploration.md"
        }
      ]
    }
  ]
}
```

Add to `gemea/.claude/settings.json` alongside the `mcpServers` block.

---

## 7. Future: GeMeA endpoint (Phase 2)

When `gemea.ise.fiz-karlsruhe.de/sparql` is live, run the same `jq` merge with
`gemea-qlever` as the key and the GeMeA SPARQL URL as the `-e` argument.
The `setup.sh` should add both entries in one pass.

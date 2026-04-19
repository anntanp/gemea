# MCP Access

GeMeA exposes an MCP (Model Context Protocol) interface via MCPO at `http://[host]:42005`. This allows AI agents and tools that support MCP to query the knowledge graph directly.

## Connecting from Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "gemea": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://[host]:42005/mcp"]
    }
  }
}
```

Substitute `[host]` with the actual hostname or IP of your deployment.

## What is available

The MCP interface proxies the QLever SPARQL endpoint. Agents can:

- Execute SPARQL SELECT queries over 23M+ DDB objects
- Browse entity descriptions (Linked Data pages via SHMARQL at port 42003)
- Query the GND index for authority records (port 42006)

## Example agent prompt

```
Use the GeMeA SPARQL endpoint to find all objects from the DDB Archive sector
(sparte001) with geo coordinates, and return the first 10 with their titles and locations.
```

## Related

- SPARQL query examples: [sparql-queries.md](sparql-queries.md)
- Self-hosting setup: [setup.md](setup.md)

# GeMeA — MCP-First Roadmap Revision

Based on agent-first and MCP-first architectural principles (see `references/xorwell-ai-first-app-design.md`).

---

## 1. Central thesis

The current roadmap treats the REST API as the primary integration surface. Agent-first design inverts this: **MCP is the primary interface; REST is secondary**. The key implication is not a technology swap but a design reorientation — every tool exposed through MCP must be designed for an LLM consumer, not a developer.

---

## 2. Revised phase order

```
0a → 0 → 1 → 1b → 2a (MCP server + NL search) → 2b (REST thin wrapper) → 3 (Frontend + chat) → 4 (DevOps + MCP gateway)
```

---

## 3. What changes

### 3.1 Add Phase 2a — MCP Server (primary integration layer)

Insert between Phase 1b and Phase 3. This is the most consequential change.

The MCP server is a **semantic facade** over QLever + Elasticsearch — not a 1:1 endpoint wrapper. The design unit is the *outcome*, not the endpoint. Fewer, higher-impact tools consistently outperform large fine-grained toolsets.

**Target tool set (~10–15 tools):**

| Tool | Orchestrates internally |
|------|------------------------|
| `gemea_search(query, facets, era)` | ES query + facet aggregation |
| `gemea_work_explore(uri, depth)` | SPARQL work lookup + graph traversal |
| `gemea_agent_works(agent_uri)` | agent page + linked works SPARQL |
| `gemea_sparql(nl_query)` | NL → SPARQL generation + read-only proxy |
| `gemea_map_objects(bbox, type)` | geo-filtered QLever query |
| `gemea_provenance(cho_uri)` | full lineage: DDB → GND → mocho triples |
| `gemea_related_works(work_uri)` | FRBR Work neighborhood via SPARQL |
| `gemea_suggest(partial_query)` | ES autocomplete |

MCP **Resources** (read-only URI-addressed data): item, work, agent, place, timespan pages. These map to MCP Resources, not Tools — agents read them without side effects.

MCP **Prompts**: reusable templates for common interaction patterns (e.g., "explore the FRBR hierarchy of a work given a title string").

**Tool description discipline:** each description must specify *when* to use the tool, *how* to format arguments, and *what* to expect back — not just the function signature. This is what the LLM uses for selection.

**Transport:** Streamable HTTP (mandatory for multi-user deployment — stdio is single-client only). Single HTTP endpoint supporting POST (request-response) and GET (SSE for long-running SPARQL queries). Session management via `Mcp-Session-Id` header.

**Authorization:** OAuth 2.1 + mandatory PKCE. GeMeA MCP server acts as OAuth Resource Server. Redis-backed session state enables stateless horizontal scaling.

**Naming convention:** snake_case, domain-noun-verb pattern (`gemea_work_explore`, `gemea_agent_works`). Prefix clustering keeps related tools grouped for the LLM.

#### 3.1.1 Deliverables

- [ ] MCP server scaffold (`mcp/`)
- [ ] Tool implementations: `gemea_search`, `gemea_work_explore`, `gemea_agent_works`, `gemea_sparql`, `gemea_map_objects`, `gemea_provenance`
- [ ] Resource handlers: item, work, agent, place URIs
- [ ] Streamable HTTP transport with `Mcp-Session-Id` session management
- [ ] OAuth 2.1 + PKCE authorization middleware
- [ ] Redis session state store
- [ ] Tool description corpus (separate from code — review for LLM clarity)
- [ ] `mcp/tests/` — unit tests per tool; integration tests with live QLever + ES

#### 3.1.2 Milestone

MCP server callable from Claude Desktop or `mcp` CLI; all tools return correctly curated responses; OAuth flow functional; session state survives server restart.

---

### 3.2 Elevate Text2SPARQL from v2 → Phase 2a

In REST-first design, NL search is a convenience feature. In agent-first design, `gemea_sparql(nl_query)` is **the primary query mechanism for agent consumers** — they state intent, not SPARQL. An LLM orchestrating GeMeA tools will use this constantly.

Move into Phase 2a scope. Implementation: LLM-generated SPARQL backed by the read-only QLever proxy, with a curated schema description injected into the system prompt. The raw `/sparql` proxy remains available for power users.

---

### 3.3 Demote Phase 2 REST API to Phase 2b

Phase 2 (FastAPI) stays but is no longer the primary target. Scope narrows to:

- **Frontend glue**: `/search`, `/item/{id}`, entity pages — called by the Next.js frontend
- **Backward-compatibility surface**: deterministic programmatic consumers

**Drop or defer:** `POST /graphql` (GraphQL). It duplicates what the MCP semantic facade provides. Agent consumers use MCP tools; human-facing queries go through REST. GraphQL adds complexity without a distinct consumer.

---

### 3.4 Phase 3 Frontend — add agent chat interface

The web UI is unchanged. Add one component: a **chat panel** that routes NL queries through the MCP server via a thin HTTP bridge (`gemea_sparql` + `gemea_search`). This means the frontend exercises the same tools an external agent uses — MCP layer gets human-driven testing in parallel with development.

Low implementation cost. Adds paper value (demonstrates agent-accessible interface for human and machine consumers).

---

### 3.5 Phase 4 DevOps — extend for MCP

Add to existing Phase 4 deliverables:

**MCP gateway layer** — sits between agents and the MCP server; handles:
- Identity validation (OAuth token verification)
- Policy enforcement (is this agent permitted to call this tool with these arguments?)
- Append-only audit log (every tool call: server, tool name, arguments, response, timestamps)
- OpenTelemetry span emission

This is a compliance and observability layer, not just logging. Even a minimal implementation is sufficient for the paper.

**Token-aware rate limiting** — not request-counting. A single `gemea_work_explore` call triggers multiple SPARQL + ES operations. Use token bucket per session:
- Per-minute burst protection
- Per-day budget cap
- Return `Retry-After` + remaining quota headers so agents self-throttle

Replace the current Nginx request-rate config (`/sparql 10 req/s`, `/search 50 req/s`) with session-level token bucket middleware in the MCP gateway.

**OpenTelemetry tracing:**
- Trace = full agent session
- Span = individual tool call or SPARQL/ES query
- W3C Trace Context headers propagated across all hops
- Inject OTel context into MCP `_meta` field for tool calls
- Structured logs carry trace/span IDs for correlation

#### 3.5.1 Additional DevOps deliverables

- [ ] `mcp-gateway/` — identity validation, policy enforcement, audit log, OTel spans
- [ ] Append-only audit log (tool call metadata: server, tool, args, response, actor, timestamps)
- [ ] Token bucket rate limiter per MCP session (replace Nginx request-count limits for MCP traffic)
- [ ] OpenTelemetry instrumentation: traces for agent sessions, spans for tool calls + SPARQL queries
- [ ] `docker/docker-compose.yml` updated: add MCP server + gateway services

---

## 4. What does not change

Phases 0a, 0, 1, 1b are data infrastructure. Agent-first design principles apply to the access layer, not the ingest pipeline. Leave those phases structurally unchanged.

The GND linking pipeline *could* be refactored as an orchestrator-workers agent pattern, but that is scope creep given the May 7 deadline. The monolithic scripts are appropriate — the non-determinism is bounded and the control flow is fixed.

---

## 5. Paper angle

This reframing strengthens the ISWC Resource Track contribution. GeMeA becomes "KG browser *and* MCP server for cultural heritage" — an agent-consumable semantic facade over 65M objects with provenance tracing, not only a web UI.

The `gemea_provenance` tool (DDB → GND → mocho lineage) is directly relevant to the Semantic Web community's interests in data lineage within agent-driven workflows. The MCP server with QLever + ES as backend is a concrete instantiation of agent-first GLAM infrastructure — a novel contribution.

Suggested additions to the paper:
- Section on MCP tool design for KG access (semantic facade pattern, outcome-oriented tools)
- Evaluation: compare `gemea_sparql(nl_query)` accuracy vs. raw SPARQL on a benchmark query set
- Discussion: agent-accessible cultural heritage infrastructure as a research direction

---

## 6. Design tensions and tradeoffs

| Tension | Resolution |
|---------|-----------|
| MCP tools vs. REST endpoints | MCP is primary (agents); REST is secondary (frontend, deterministic consumers) |
| Tool granularity | Outcome-oriented (~10 tools), not endpoint-oriented (~20+ routes) |
| GraphQL | Drop for v1; MCP tools cover agent use cases |
| Text2SPARQL timing | Phase 2a, not v2 — core to agent-first access |
| NL search accuracy | Accept lower recall for v1; document as known limitation in paper |
| Auth complexity | OAuth 2.1 + PKCE is mandatory for multi-user MCP; no shortcut |

---

## 7. References

- `references/xorwell-ai-first-app-design.md` — 17 architectural principles (source of this analysis)
- `notes/architecture.md` — current GeMeA architecture
- `notes/roadmap.md` — original phase-order roadmap

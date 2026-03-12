# GeMeA — GraphViz: Dynamic Neighbor Expansion

Component: `GraphViz` (Cytoscape.js) on `/item/[id]`, `/agent/[id]`, `/place/[id]`

---

## Static fallback (no Cytoscape.js)

Render the `neighbors` array from `GET /item/{id}` as a plain HTML list of links. Same data, no interactivity. Sufficient for must-have entity pages.

## Dynamic expansion (Cytoscape.js)

No separate graph API endpoint needed. All data comes from repeated calls to the existing `GET /item/{id}` endpoint.

### Flow

1. **Initial render**: `GET /item/{id}` returns central node + `neighbors` array (1-hop). Cytoscape.js renders as a graph.
2. **User clicks a neighbor node**: frontend calls `GET /item/{neighbor-id}` → response includes that node's neighbors → merge new nodes/edges into the existing Cytoscape.js instance.
3. **Repeat**: each click expands one more hop. Graph grows as the user explores.

```
User clicks node B
  → GET /item/B
  → response: { neighbors: [C, D, E] }
  → add C, D, E to Cytoscape graph
  → mark B as "expanded" (skip re-fetch on re-click)
```

### Implementation pieces

- **Cytoscape.js** — graph rendering + layout (`cose-bilkent` or `cola` for force-directed)
- **React state** — track which node IDs have been fetched/expanded
- **Stop conditions** — max node count (e.g., 100 nodes) or max depth (e.g., 3 hops) to prevent runaway expansion

### Key point

Dynamic graph expansion is a pure frontend concern. The API contract is already sufficient — it is all `GET /item/{id}` calls under the hood.

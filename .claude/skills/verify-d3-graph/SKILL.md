---
name: verify-d3-graph
description: >
  [Verify·UI·Browser] Navigate to a page containing a D3 SVG graph component, verify
  SVG renders with expected node and edge counts via JavaScript DOM queries. Tests
  TaxonomyGraph and BlueprintDependencyGraph. Requires dev server. SRP: D3 SVG
  graph structure validation only.
model: sonnet
user-invocable: true
disable-model-invocation: true
---

# Verify D3 Graph Render

Validates D3 SVG graph components render correctly with expected node structure.

## Input
- `base_url`: e.g. `http://localhost:3000`
- `route`: e.g. `/taxonomy`, `/blueprints/1`
- `expected_min_nodes`: minimum node count (e.g. 3)
- `svg_container_selector`: CSS selector for SVG parent (e.g. `.graph-container`)

## Execution Model

- **TRIVIAL**: Lead-direct. Single graph node/edge count check.
- **STANDARD**: Spawn 1 browser-verifier (maxTurns: 15) for multi-graph pages.
- **COMPLEX**: Not typically required for graph verification tasks.

## Phase-Aware Execution

P7 verify phase only. Operates after execution-code PASS.

## Methodology

### DPS for browser-verifier
- **OBJECTIVE**: Verify D3 SVG graph at `{base_url}{route}` renders with ≥ `{expected_min_nodes}` nodes and ≥ `{expected_min_edges}` edges.
- **CONTEXT**: `base_url`, `route`, `expected_min_nodes`, `expected_min_edges`, `svg_selector` (default: `svg`)
- **CONSTRAINTS**: maxTurns: 15; use JS DOM queries only; do not rely on visual element positions
- **CRITERIA**: node_count ≥ expected_min_nodes, edge_count ≥ expected_min_edges, no JS errors
- **OUTPUT**: L1 YAML (status/node_count/edge_count/console_errors) + L2 narrative

### Execution Steps

1. **Navigate**: `navigate(url = base_url + route)`
2. **Wait**: `computer(action: wait, duration: 3)` (D3 simulation needs time)
3. **Screenshot**: `computer(action: screenshot)` for visual evidence
4. **Node count**: `javascript_tool("document.querySelectorAll('svg .node').length")`
5. **Edge count**: `javascript_tool("document.querySelectorAll('svg .edges line').length")`
6. **SVG exists**: `javascript_tool("!!document.querySelector('svg')")`
7. **Simulation settled**: `javascript_tool("document.querySelectorAll('svg circle').length")`
- **Console check**: `read_console_messages(onlyErrors: true)` — catch D3 simulation errors

## Output
```yaml
status: PASS | FAIL | WARN
route: "{route}"
svg_found: true | false
node_count: N
edge_count: N
expected_min_nodes: N
screenshot_id: "{imageId}"
```
L2: Node count, edge count, console error count. PASS routes to verify-quality. FAIL routes to execution-code with expected vs actual counts.

## Decision Points
- svg_found = false → FAIL (component did not mount)
- node_count < expected_min_nodes → FAIL
- node_count ≥ expected_min_nodes, edge_count = 0 → WARN (edges may not have loaded)

## Quality Gate
- PASS: svg_found AND node_count ≥ expected_min_nodes
- WARN: nodes present but fewer edges than expected
- FAIL: no SVG, no nodes, or page crashed

## Anti-Patterns
- Do NOT wait more than 5s for D3 simulation (use explicit wait, then query)
- Do NOT describe node positions — report counts only
- Do NOT assume specific node counts — pass expected_min_nodes/edges as parameters

## Transitions

### Receives From
| Source | Data Expected | Format |
|--------|---------------|--------|
| execution-code (PASS) | base_url + route + expected counts | DPS CONTEXT |
| (User invocation) | Same parameters | Direct |

### Sends To
| Target | Data Produced | Trigger |
|--------|---------------|---------|
| verify-quality | PASS signal + node_count + edge_count | On PASS |
| execution-code | FAIL + expected_vs_actual counts | On FAIL |

> D17 Note: Ch2: `tasks/{work_dir}/p7-verify-d3-graph.md` · Ch3: micro-signal to Lead

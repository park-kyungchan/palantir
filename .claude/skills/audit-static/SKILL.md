---
name: audit-static
description: |
  [P2·Research·Static] Maps structural dependency graph and coupling hotspots.

  WHEN: After research-codebase AND research-external complete. Wave 2 parallel audit.
  DOMAIN: research (skill 3 of 7). Parallel: static ∥ behavioral ∥ relational ∥ impact.
  INPUT_FROM: research-codebase (local patterns, file inventory), research-external (community constraints), design-architecture (component structure).
  OUTPUT_TO: research-coordinator (dependency graph for cross-dimensional consolidation).

  METHODOLOGY: (1) Ingest Wave 1 research findings, (2) Map file-to-file import/reference chains via Glob/Grep, (3) Identify hotspots (files with >3 dependents), (4) Build dependency DAG with edge weights, (5) Report graph + hotspots with file:line evidence.
  OUTPUT_FORMAT: L1 YAML dependency summary, L2 markdown DAG with hotspot analysis.
user-invocable: false
disable-model-invocation: false
---

# Audit — Static (Structural Dependencies)

## Execution Model
- **STANDARD**: Spawn analyst (maxTurns:25). Systematic import chain mapping across all files identified by Wave 1.
- **COMPLEX**: Spawn 2 analysts with non-overlapping directory scopes. Merge dependency graphs at Lead level.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p2-audit-static.md`, sends micro-signal: `PASS|deps:{N}|hotspots:{N}|ref:/tmp/pipeline/p2-audit-static.md`.

## Methodology

### 1. Ingest Wave 1 Findings
Read research-codebase L1/L2 output to extract:
- File inventory (all files discovered with their roles)
- Existing patterns and conventions (naming, import style)
- Module boundaries identified by codebase exploration

Read research-external L2 for community constraints that affect dependency interpretation (e.g., circular import restrictions, module resolution rules).

Read design-architecture L1 for component structure to scope the analysis to architecturally relevant files.

### 2. Map Import/Reference Chains
For each file in the scoped inventory:
- **Grep** for import/require/from statements to find outgoing edges
- **Grep** reverse: find all files that import/reference the current file (incoming edges)
- Record each edge as `source -> target` with reference type (import, dynamic require, config reference, skill INPUT_FROM/OUTPUT_TO)
- For non-code files (YAML, JSON, MD): detect cross-file references by name, path, or identifier

Scope to architecturally relevant directories. Exclude `node_modules/`, `.git/`, build artifacts.

### 3. Identify Dependency Hotspots
A hotspot is any file with disproportionate coupling:
- **Fan-out hotspot**: File imports >3 other files (high outgoing dependency)
- **Fan-in hotspot**: File is imported by >3 other files (high incoming dependency)
- **Both**: File has high fan-in AND fan-out (coupling hub)

For each hotspot, record:
- File path and role
- Fan-in count and fan-out count
- List of connected files with edge types
- Risk assessment: HIGH (hub with >5 connections), MEDIUM (>3), LOW (<=3)

### 4. Build Dependency DAG
Construct a directed acyclic graph representation:
- Nodes = files (with role labels from Wave 1)
- Edges = dependency relationships (with type labels)
- Edge weights = strength of coupling (1=single reference, 2=multiple references, 3=bidirectional)
- Detect cycles (if any) and flag as structural risk

DAG format in L2 output:
```
[file-A] --(import)--> [file-B] weight:1
[file-B] --(import)--> [file-C] weight:2
[file-C] --(config)--> [file-A] weight:1 CYCLE
```

### 5. Report Graph and Hotspots
Produce final output with:
- Complete edge list with types and weights
- Hotspot table sorted by total connections (fan-in + fan-out)
- Cycle report (if any detected)
- Summary statistics: total nodes, total edges, average fan-out, max fan-in
- All findings with file:line evidence for every edge

## Failure Handling

### No Dependencies Found
- **Cause**: Codebase has no inter-file references (single-file project or fully decoupled)
- **Action**: Report empty graph with `deps: 0`. This is valid for TRIVIAL pipelines.
- **Route**: research-coordinator with empty graph and note

### Wave 1 Input Missing
- **Cause**: research-codebase or research-external did not produce output
- **Action**: FAIL with identification of missing upstream. Cannot build dependency graph without file inventory.
- **Route**: Lead for re-routing to missing upstream skill

### Analyst Exhausted Before Complete Scan
- **Cause**: Large codebase exceeds analyst turn budget
- **Action**: Report partial graph with coverage percentage (files scanned / total files)
- **Route**: research-coordinator with partial flag and uncovered file list

## Anti-Patterns

### DO NOT: Infer Dependencies Without Evidence
Every edge in the dependency graph must have a concrete file:line reference showing the import/reference. Do not assume dependencies based on naming conventions or directory proximity alone.

### DO NOT: Include Transitive Dependencies as Direct
If A imports B and B imports C, record A->B and B->C as separate edges. Do not add A->C unless A directly references C. Transitive analysis is audit-impact's responsibility.

### DO NOT: Modify Files During Analysis
This is a read-only audit. Even if you discover broken imports or missing files, document them as findings and do not fix them.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-codebase | File inventory, local patterns | L1 YAML: pattern inventory, L2: file:line findings |
| research-external | Community constraints on dependencies | L2: known dependency rules, module resolution patterns |
| design-architecture | Component structure for scoping | L1 YAML: components list with module boundaries |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| research-coordinator | Dependency graph + hotspot analysis | Always (Wave 2 -> Wave 2.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing Wave 1 input | Lead | Which upstream missing, what data needed |
| Analyst exhausted | research-coordinator | Partial graph + coverage percentage + uncovered list |
| No dependencies found | research-coordinator | Empty graph with explanatory note |

## Quality Gate
- Every dependency edge has file:line evidence for source and target
- Hotspot classification applied to all nodes with >3 connections
- No inferred edges (all edges have concrete references)
- DAG representation includes node roles and edge types
- Cycle detection performed and results reported (even if zero cycles)
- Coverage metric reported: files scanned / total inventory files

## Output

### L1
```yaml
domain: research
skill: audit-static
total_nodes: 0
total_edges: 0
hotspot_count: 0
cycle_count: 0
coverage_percent: 100
hotspots:
  - file: ""
    fan_in: 0
    fan_out: 0
    risk: HIGH|MEDIUM|LOW
```

### L2
- Dependency DAG with all edges, types, and weights
- Hotspot table sorted by total connections
- Cycle report with involved files and edge chain
- Summary statistics: nodes, edges, avg fan-out, max fan-in
- Coverage notes: files scanned vs total inventory
- All findings with file:line evidence

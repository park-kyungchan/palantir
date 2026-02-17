---
name: audit-static
description: >-
  Maps structural dependency graph and coupling hotspots via
  Glob/Grep import analysis. Builds weighted DAG with file:line
  evidence. Parallel with audit-behavioral, audit-relational,
  and audit-impact. Use after research-codebase and
  research-external complete. Reads from research-codebase local
  patterns and file inventory, research-external community
  constraints, and design-architecture component structure.
  Produces dependency summary and DAG with hotspot analysis for
  research-coordinator.
user-invocable: false
disable-model-invocation: false
allowed-tools: "Read Glob Grep Write"
metadata:
  category: audit
  tags: [dependency-graph, coupling-analysis, structural-audit]
  version: 2.0.0
---

# Audit — Static (Structural Dependencies)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check of 1-2 file imports via Grep. No agent spawn. maxTurns: 0.
- **STANDARD**: Spawn analyst (maxTurns:25). Systematic import chain mapping across all files identified by Wave 1.
- **COMPLEX**: Spawn 2 analysts with non-overlapping directory scopes (maxTurns:25 each). Merge dependency graphs at Lead level.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p2-audit-static.md`, sends micro-signal: `PASS|deps:{N}|hotspots:{N}|ref:/tmp/pipeline/p2-audit-static.md`.

## Decision Points

### Analyst Scope Strategy
Based on file inventory size from research-codebase L1.
- **≤15 files**: Single analyst, full codebase scope. maxTurns: 20.
- **16-50 files**: Single analyst, directory-scoped passes. maxTurns: 25.
- **>50 files**: Spawn 2 analysts with non-overlapping directory partitions. maxTurns: 25 each.
- **Default**: Single analyst (STANDARD tier).

### Hotspot Sensitivity
- **Standard threshold (>3 connections)**: Default for most codebases.
- **Lowered threshold (>2 connections)**: When design changes touch core infrastructure where moderate coupling is risky.

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

### Delegation Prompt Specification

#### COMPLEX Tier (2 parallel analysts)
- **Context**: Paste research-codebase L1 `pattern_inventory` + file list. Paste research-external L2 dependency constraints. Paste design-architecture L1 `components[]` for scoping. Assign directory scope: `{scope_dirs}`.
- **Task**: "Map all file-to-file import/reference chains within assigned directory scope. Build dependency DAG with edge weights. Identify hotspot files (>3 connections). Report complete edge list with file:line evidence for every edge."
- **Constraints**: Read-only analysis (analyst agent, no Bash). Scope to assigned directories only. Exclude node_modules/, .git/, build artifacts. maxTurns: 25.
- **Expected Output**: L1 YAML: total_nodes, total_edges, hotspot_count, cycle_count, coverage_percent. L2: full DAG edges, hotspot table sorted by connections, cycle report.
- **Delivery**: SendMessage to Lead: `PASS|deps:{N}|hotspots:{N}|ref:/tmp/pipeline/p2-audit-static.md`

#### STANDARD Tier (single analyst)
Same as COMPLEX but single analyst with full codebase scope. No directory partitioning.

#### TRIVIAL Tier
Lead-direct inline. Grep 1-2 files for imports, note edges. No formal DPS.

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

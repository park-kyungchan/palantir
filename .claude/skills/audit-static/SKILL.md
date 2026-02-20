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
  research-coordinator. On FAIL, Lead applies D12 escalation
  ladder. DPS needs research-codebase file inventory and local
  patterns, research-external dependency constraints, and
  design-architecture component list. Exclude other audit
  dimension results (behavioral/relational/impact) and
  pre-design conversation history.
user-invocable: true
disable-model-invocation: true
---

# Audit — Static (Structural Dependencies)

## Execution Model
- **TRIVIAL**: Lead-direct. Inline Grep of 1-2 file imports. No spawn.
- **STANDARD**: 1 analyst (maxTurns:25). Systematic import chain mapping across Wave 1 files.
- **COMPLEX**: 2 analysts with non-overlapping directory scopes (maxTurns:25 each). Merge DAGs at Lead level.

## Decision Points

### Analyst Scope Strategy
Based on file inventory size from research-codebase L1:
- **≤15 files**: Single analyst, full codebase. maxTurns: 20.
- **16-50 files**: Single analyst, directory-scoped passes. maxTurns: 25.
- **>50 files**: 2 analysts with non-overlapping directory partitions. maxTurns: 25 each.

### Hotspot Sensitivity
- **Standard (>3 connections)**: Default for most codebases.
- **Lowered (>2 connections)**: When design changes touch core infrastructure.

## Methodology

### 1. Ingest Wave 1 Findings
Read research-codebase L1/L2 for file inventory, patterns, module boundaries.
Read research-external L2 for dependency constraints (e.g., circular import restrictions).
Read design-architecture L1 for component structure scoping.

### 2. Map Import/Reference Chains
For each file in scope:
- Grep for import/require/from → outgoing edges
- Grep reverse: find all importers → incoming edges
- Record each edge as `source -> target` with type (import, config ref, skill INPUT_FROM/OUTPUT_TO)
- Non-code files: detect cross-file references by name/path/identifier
- Exclude: `node_modules/`, `.git/`, build artifacts

### 3. Identify Hotspots
- **Fan-out hotspot**: imports >3 files
- **Fan-in hotspot**: imported by >3 files
- **Hub**: high fan-in AND fan-out
- Risk: HIGH (>5 connections), MEDIUM (>3), LOW (≤3)

### 4. Build Dependency DAG
Nodes = files with role labels. Edges = dependencies with type labels.
Edge weights: 1=single ref, 2=multiple refs, 3=bidirectional.
Detect and flag cycles as structural risk.

### 5. Report
Complete edge list + hotspot table (sorted by total connections) + cycle report + summary stats (nodes, edges, avg fan-out, max fan-in) + coverage metric.

### DPS for COMPLEX Tier (2 analysts)
For DPS construction guide: Read `~/.claude/resources/dps-construction-guide.md`

- **Context INCLUDE**: research-codebase L1 pattern_inventory + file list; research-external L2 constraints; design-architecture L1 components[]; assigned `scope_dirs`.
- **Context EXCLUDE**: Other audit dimensions; pre-design history; full pipeline state.
- **Task**: "Map all import/reference chains within assigned directories. Build DAG with edge weights. Identify hotspots (>3 connections). Report with file:line evidence."
- **Constraints**: Read-only (analyst). Scope to assigned dirs only. maxTurns: 25.
- **Delivery**: `PASS|deps:{N}|hotspots:{N}|ref:tasks/{work_dir}/p2-audit-static.md`

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

| Failure | Action |
|---------|--------|
| Grep/scan tool error | L0: Retry same analyst |
| Incomplete scan, missing files | L1: Nudge with refined scope |
| Analyst exhausted turns | L2: Respawn with narrowed scope |
| Scope overlap between analysts | L3: Restructure partition |
| 3+ L2 failures | L4: AskUserQuestion |

- **No dependencies found**: Valid for single-file projects. Report empty graph, route to coordinator.
- **Wave 1 input missing**: FAIL — cannot build graph without file inventory. Route to Lead.
- **Analyst exhausted**: Report partial graph with `coverage_percent`. Route to coordinator with uncovered file list.

## Anti-Patterns

### DO NOT: Infer dependencies without file:line evidence
Every DAG edge must reference a concrete import/reference line. No assumption by naming or proximity.

### DO NOT: Include transitive dependencies as direct
A→B and B→C ≠ A→C unless A directly references C. Transitive analysis is audit-impact's domain.

### DO NOT: Modify files during analysis
Read-only audit. Document broken imports as findings, do not fix.

## Phase-Aware Execution
For shared protocol: Read `~/.claude/resources/phase-aware-execution.md`
Runs in P2 Team mode. Writes to `tasks/{work_dir}/p2-audit-static.md`. Micro-signal: `PASS|deps:{N}|hotspots:{N}|ref:...`

## Transitions

### Receives From
| Source | Data |
|--------|------|
| research-codebase | File inventory, local patterns (L1+L2) |
| research-external | Dependency constraints (L2) |
| design-architecture | Component structure (L1 components[]) |

### Sends To
| Target | Condition |
|--------|-----------|
| research-coordinator | Always (Wave 2 → 2.5 consolidation) |

### Failure Routes
| Failure | Route | Data |
|---------|-------|------|
| Missing Wave 1 input | Lead | Which upstream missing |
| Analyst exhausted | research-coordinator | Partial graph + coverage% + uncovered list |
| Empty graph | research-coordinator | Empty graph with note |

## Quality Gate
- Every edge has file:line evidence (source AND target)
- Hotspot classification applied to all nodes >3 connections
- No inferred edges
- DAG includes node roles and edge types
- Cycle detection performed (even if zero)
- Coverage metric reported

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
pt_signal: "metadata.phase_signals.p2_research"
signal_format: "PASS|deps:{N}|hotspots:{N}|ref:tasks/{work_dir}/p2-audit-static.md"
```

### L2
- Dependency DAG with edges, types, weights
- Hotspot table sorted by connections
- Cycle report
- Summary: nodes, edges, avg fan-out, max fan-in
- Coverage notes
- All findings with file:line evidence

---
name: plan-static
description: >-
  Decomposes tasks by structural dependency clusters into
  SRP-bounded units. Builds acyclic task DAG with critical path.
  Parallel with plan-behavioral, plan-relational, and
  plan-impact. Use after research-coordinator complete. Reads
  from research-coordinator audit-static L3 dependency graph via
  $ARGUMENTS. Produces task list with dependency edges and
  complexity, and cluster rationale for validate-syntactic.
  On FAIL (coverage <85% or HIGH orphans), routes back to
  plan-static with refined research context. DPS needs
  research-coordinator audit-static L3 dependency graph. Exclude
  behavioral, relational, and impact dimension data.
user-invocable: true
disable-model-invocation: true
---

# Plan — Static Decomposition

## Execution Model
- **TRIVIAL**: Lead-direct. Flat file list, no clusters. 1-2 tasks with linear dependencies.
- **STANDARD**: Spawn analyst (maxTurns:15). Cluster identification across 3-8 files. Dependency-aware grouping.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep dependency graph analysis, 9+ files, multi-cluster, cross-module.

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`

## Methodology

### 1. Read Audit-Static L3 (Dependency Graph)
Load the audit-static L3 file path provided via `$ARGUMENTS`. Validate the file exists and contains a parseable dependency graph (file-level imports, calls, inheritance, coupling metrics, module boundary annotations). If absent, route to Failure Handling (Missing Audit Input).

### 2. Identify Dependency Clusters
Classify all nodes in the graph:
- **Tight clusters**: files with bidirectional or high-frequency dependencies — MUST stay in the same task
- **Loose couplings**: files connected by a single edge — CAN be in separate tasks (edge becomes a task dependency)
- **Isolated nodes**: files with no incoming or outgoing edges — each forms its own single-file task

### 3. Define Task Boundaries (SRP, 1-4 Files)
For each identified cluster, create one task:
- Max 4 files per task. If cluster exceeds 4, split along the weakest internal coupling edge.
- Every file belongs to exactly one task (exclusive ownership).
- Each task represents one coherent SRP unit. Naming: imperative verb + target module.
- Related files (module + tests) stay together. Config files grouped into infra tasks.

### 4. Assign File Ownership and Estimate Complexity
List exact file paths per task (create or modify). Estimate complexity (TRIVIAL/STANDARD/COMPLEX) using structural signals.

> Complexity indicator table and ownership rubric: read `resources/methodology.md`

### 5. Build Task DAG with Critical Path
For each task pair, determine relationship from the original dependency graph:
- **blocks**: producer task must complete before consumer task starts
- **independent**: no dependency edge between clusters

Identify the critical path (longest blocking chain) and calculate per-wave parallelism (count of independent tasks per level).

> DPS analyst spawn templates (TRIVIAL/STANDARD/COMPLEX): read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Decision Points
- **Cluster split**: cluster > 4 files AND weak internal edge (≤ 2 coupling edges) → split along weakest edge
- **Cluster merge**: two adjacent clusters share > 3 bidirectional edges → merge into single task
- **Task granularity**: single-file for isolated nodes; 2-4 files for tight clusters; default 2-3 for balance
- **Iteration**: Lead tracks `metadata.iterations.plan-static: N` in PT. Iteration 1 = strict; iteration 2 = relaxed with documented gaps. Max 2 iterations.

> Cluster strategy examples and iteration tracking (D15): read `resources/methodology.md`

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Tool error or timeout during cluster analysis | L0 Retry | Re-invoke same agent with same DPS |
| Cluster output incomplete or off-direction | L1 Nudge | Respawn with refined DPS targeting refined scope constraints |
| Agent stuck on cycle detection or context exhausted | L2 Respawn | Kill agent → fresh analyst with refined DPS |
| Task graph structure broken or scope shift | L3 Restructure | Modify task graph, redefine clusters |
| Strategic ambiguity or 3+ L2 failures | L4 Escalate | AskUserQuestion with options |

| Failure Type | Severity | Route To |
|---|---|---|
| Missing audit-static L3 input | CRITICAL | research-coordinator — cannot decompose without dependency graph |
| Dependency graph has cycles | HIGH | Self (re-analyze) — break at weakest coupling edge, document forced splits |
| Cluster exceeds 4-file limit, no clear split | MEDIUM | Self (re-analyze) — split at least-coupled edge, accept cross-task deps |
| All files isolated (no clusters) | LOW | Complete normally — each file becomes its own task |

> Escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns
- **DO NOT ignore dependency edges when grouping** — directory or naming convention grouping produces tasks that cross natural boundaries; always use audit-static L3 as primary input
- **DO NOT create tasks larger than 4 files** — causes agent context overflow and reduces parallelism; split even if it adds cross-task dependencies
- **DO NOT assign same file to multiple tasks** — file ownership must be exclusive; if two tasks need a file, assign to the primary modifier and add a dependency edge to the consumer
- **DO NOT speculate beyond audit data** — this skill converts IS (audit findings) to SHOULD (task plan); do not invent dependencies absent from the audit-static L3
- **DO NOT decompose below testable granularity** — each task must be independently verifiable; if a task's changes cannot be validated without another task completing first, merge them

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|---|---|---|
| research-coordinator | audit-static L3 file path | `$ARGUMENTS`: path to L3 with dependency graph |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| validate-syntactic | Task breakdown with dependency edges | Always (PASS or partial) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|---|---|---|
| Missing audit input | research-coordinator | Which L3 file is missing |
| Unresolvable cycles | Lead (escalation) | Cycle details with file:line evidence |

> D17 Note: Two-Channel protocol — Ch2 (file output to tasks/{work_dir}/) + Ch3 (micro-signal to Lead).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
- Every file in the dependency graph assigned to exactly one task (≥95% file coverage required for PASS)
- No task exceeds 4 files
- Dependency graph between tasks is acyclic (DAG)
- Critical path identified with complexity estimates
- Each task has SRP-compliant scope description

## Output

### L1
```yaml
domain: plan
skill: static
status: complete|partial
task_count: 0
total_files: 0
critical_path_length: 0
pt_signal: "metadata.phase_signals.p3_plan_static"
signal_format: "{STATUS}|tasks:{N}|critical_path:{N}|ref:tasks/{work_dir}/p3-plan-static.md"
tasks:
  - id: ""
    files: []
    complexity: trivial|standard|complex
    depends_on: []
    cluster: ""
```

### L2
- Dependency cluster identification with rationale
- Task list with file ownership and complexity estimates
- Inter-task dependency DAG visualization
- Critical path analysis

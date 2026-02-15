---
name: plan-static
description: |
  [P3·Plan·StaticDecompose] Decomposes tasks by structural dependency clusters into SRP-bounded units.

  WHEN: After research-coordinator complete. Wave 3 parallel with plan-behavioral/relational/impact.
  DOMAIN: plan (skill 1 of 4). Wave 3 parallel execution.
  INPUT_FROM: research-coordinator (audit-static L3 dependency graph via $ARGUMENTS).
  OUTPUT_TO: plan-verify-static (task breakdown with file assignments and dependency edges).

  METHODOLOGY: (1) Read audit-static L3 dependency graph, (2) Identify tight/loose/isolated dependency clusters, (3) Define task boundaries (1-4 files per task, SRP-compliant), (4) Assign exclusive file ownership and estimate complexity (T/S/C), (5) Output acyclic task DAG with critical path and parallelism potential.
  OUTPUT_FORMAT: L1 YAML task list with dependency edges and complexity, L2 cluster rationale with critical path visualization.
user-invocable: false
disable-model-invocation: false
---

# Plan — Static Decomposition

## Execution Model
- **TRIVIAL**: Lead-direct. Flat file list with no clusters. 1-2 tasks with linear dependencies.
- **STANDARD**: Spawn analyst. Systematic cluster identification across 3-8 files. Dependency-aware task grouping.
- **COMPLEX**: Spawn analyst (maxTurns:25). Deep dependency graph analysis across 9+ files, multiple clusters, cross-module boundaries.

## Phase-Aware Execution
- **Standalone / P0-P1**: Spawn agent with `run_in_background`. Lead reads TaskOutput directly.
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.
- **Delivery**: Agent writes to `/tmp/pipeline/p3-plan-static.md`, sends micro-signal: `{STATUS}|tasks:{N}|deps:{N}|ref:/tmp/pipeline/p3-plan-static.md`

## Decision Points

### Cluster Split vs Merge
When dependency cluster boundaries are ambiguous.
- **Split**: If cluster > 4 files AND a weak internal edge exists (≤ 2 coupling edges). Split along weakest edge.
- **Merge**: If two adjacent clusters share > 3 bidirectional edges. Merge into single task (accept larger scope).
- **Default**: Keep cluster intact when 1-4 files with clear internal cohesion.

### Task Granularity Selection
When assigning files to tasks after clustering.
- **Single-file**: If file has 0 dependencies (isolated node). Create minimal 1-file task.
- **Multi-file**: If files form tight cluster (mutual deps). Group 2-4 files per SRP-bounded task.
- **Default**: Prefer 2-3 files per task for balanced parallelism and manageability.

## Methodology

### 1. Read Audit-Static L3 (Dependency Graph)
Load the audit-static L3 file path provided via `$ARGUMENTS`. This file contains:
- File-level dependency graph (imports, calls, inheritance)
- Module boundary annotations
- Coupling metrics between files

Validate the input exists and contains a parseable dependency graph. If absent, route to Failure Handling (Missing Audit Input).

### 2. Identify Dependency Clusters
Analyze the dependency graph to find natural grouping boundaries:
- **Tight clusters**: Files with bidirectional or high-frequency dependencies (import each other, call each other)
- **Loose couplings**: Files connected by a single edge (one import, one call)
- **Isolated nodes**: Files with no incoming or outgoing edges

Grouping rules:
- Files in a tight cluster MUST be in the same task (splitting them causes cross-task coordination overhead)
- Loosely coupled files CAN be in separate tasks (edge becomes a dependency between tasks)
- Isolated files form their own single-file tasks

### 3. Define Task Boundaries (1-4 Files, SRP)
For each identified cluster, create a task:
- **Max 4 files per task**: If a cluster has >4 files, split along the weakest internal coupling edge
- **Min 1 file per task**: Every file must belong to exactly one task
- **SRP compliance**: Each task should represent one coherent unit of structural change
- **Task naming**: Imperative verb + target module (e.g., "Implement auth handler cluster")

Boundary validation:
- No file assigned to multiple tasks
- Related files (module + its tests) stay in same task
- Config files (.claude/) grouped into infra tasks, source files into code tasks

### 4. Assign File Ownership and Estimate Complexity
For each task:
- List exact file paths (create or modify)
- Estimate complexity using structural signals:

| Indicator | TRIVIAL | STANDARD | COMPLEX |
|-----------|---------|----------|---------|
| Files per task | 1 | 2-3 | 4 |
| Internal edges | 0-1 | 2-3 | 4+ |
| Cross-task deps | 0 | 1 | 2+ |
| Module boundaries | Same | 1-2 | Cross-module |

### 5. Output Task List with Dependency Edges
Build the final task graph:
- For each pair of tasks, determine relationship from the original dependency graph:
  - **blocks**: Producer task must complete before consumer task starts
  - **independent**: No dependency edge between task clusters
- Identify critical path (longest chain of blocking dependencies)
- Calculate parallelism potential (tasks per wave)

**DPS -- Analyst Spawn Template (COMPLEX):**
- **Context**: Paste audit-static L3 content (dependency graph, module boundaries, coupling metrics). Include pipeline tier and total file count.
- **Task**: "Identify dependency clusters in the file graph. Group files into tasks (1-4 files each, SRP). Assign file ownership (non-overlapping). Map inter-task dependency edges. Identify critical path. Estimate per-task complexity (T/S/C)."
- **Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No modifications. maxTurns: 20.
- **Expected Output**: L1 YAML with task_count, tasks[] (id, files, complexity, depends_on, cluster). L2 task descriptions with cluster rationale and critical path visualization.
- **Delivery**: Write full result to `/tmp/pipeline/p3-plan-static.md`. Send micro-signal to Lead: `PASS|tasks:{N}|deps:{N}|ref:/tmp/pipeline/p3-plan-static.md`.

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Flat file list (1-2 files), assign each to single task. No cluster analysis needed. Output inline.
**STANDARD**: Spawn analyst (maxTurns: 15). Simplified cluster identification across 3-8 files. Single-pass grouping. Skip critical path if ≤ 3 tasks.
**COMPLEX**: Full DPS above. Deep multi-cluster analysis, cross-module boundaries, full critical path.

## Failure Handling
| Failure Type | Severity | Route To | Blocking? | Resolution |
|---|---|---|---|---|
| Missing audit-static L3 input | CRITICAL | research-coordinator | Yes | Cannot decompose without dependency graph. Request re-run. |
| Dependency graph has cycles | HIGH | Self (re-analyze) | No | Break cycles at weakest coupling edge. Document forced splits. |
| Cluster exceeds 4-file limit, no clear split | MEDIUM | Self (re-analyze) | No | Split along least-coupled internal edge. Accept increased cross-task deps. |
| All files isolated (no clusters) | LOW | Complete normally | No | Each file becomes its own task. Note: trivial decomposition. |

## Anti-Patterns

### DO NOT: Ignore Dependency Edges When Grouping
Grouping files by directory or naming convention instead of actual dependency edges produces tasks that cross natural boundaries. Always use the audit-static dependency graph as primary input.

### DO NOT: Create Tasks Larger Than 4 Files
Tasks exceeding 4 files cause agent context overflow and reduce parallelism. Split large clusters even if it means adding cross-task dependencies.

### DO NOT: Assign Same File to Multiple Tasks
File ownership must be exclusive. If two tasks need the same file, assign it to the primary modifier and create a dependency edge to the secondary consumer.

### DO NOT: Speculate Beyond Audit Data
This skill converts IS (audit findings) to SHOULD (task plan). Do not invent dependencies not present in the audit-static L3. If the audit missed something, that is an upstream gap.

### DO NOT: Decompose Below Testable Granularity
Each task should be independently verifiable. If a task's changes cannot be validated without another task completing first, merge them.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-coordinator | audit-static L3 file path | `$ARGUMENTS`: file path to L3 with dependency graph |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-static | Task breakdown with dependency edges | Always (PASS or partial) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit input | research-coordinator | Which L3 file is missing |
| Unresolvable cycles | Lead (escalation) | Cycle details with file:line evidence |

## Quality Gate
- Every file in the dependency graph assigned to exactly one task
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

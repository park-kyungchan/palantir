---
name: plan-decomposition
description: |
  [P4·Plan·Decomposition] Decomposes architecture into implementable tasks with file ownership, dependency chains, and complexity estimates.

  WHEN: research domain complete. Architecture validated against codebase. Ready for implementation planning.
  DOMAIN: plan (skill 1 of 3). Sequential: decomposition -> interface -> strategy.
  INPUT_FROM: research-audit (consolidated findings), design-architecture (component structure).
  OUTPUT_TO: plan-interface (interface specs), plan-strategy (sequencing), orchestration-decompose (approved plan).

  METHODOLOGY: (1) Read architecture and research, (2) Break components into tasks (max 4 files each), (3) Assign file ownership (non-overlapping), (4) Identify inter-task dependencies, (5) Estimate complexity (T/S/C).
  TIER_BEHAVIOR: TRIVIAL=Lead-only, STANDARD=analyst, COMPLEX=2-4 analysts.
  OUTPUT_FORMAT: L1 YAML task list with assignments+deps, L2 task descriptions.
user-invocable: true
disable-model-invocation: false
---

# Plan — Decomposition

## Execution Model
- **TRIVIAL**: Lead-direct. Simple 1-2 task breakdown with file assignments.
- **STANDARD**: Spawn analyst. Systematic decomposition with dependency analysis.
- **COMPLEX**: Spawn 2-4 analysts. Each decomposes non-overlapping architecture modules.

## Methodology

### 1. Read Architecture and Research
Load design-architecture ADRs and research-audit findings.
List all components needing implementation.

### 2. Break Components into Tasks
For each component:
- Define 1 task per coherent unit of work
- Max 4 files per task (non-overlapping ownership)
- Task subject: imperative action verb + target ("Implement X handler")

### 3. Assign File Ownership
Rules:
- Each file belongs to exactly 1 task
- Related files (e.g., module + its tests) stay in same task
- Config files (.claude/) go to infra tasks, source files to code tasks

### 4. Map Dependencies
For each task pair, determine:
- **blocks**: Task A must complete before Task B can start
- **independent**: Tasks can run in parallel
- Identify critical path (longest dependency chain)

### 5. Estimate Complexity
Per task:
- TRIVIAL: <=2 files, single function/section change
- STANDARD: 3-4 files, connected changes
- COMPLEX: Cross-module, requires integration testing

## Quality Gate
- Every architecture component has >=1 implementation task
- No file assigned to multiple tasks
- Dependency graph is acyclic (DAG)
- Critical path identified

## Output

### L1
```yaml
domain: plan
skill: decomposition
task_count: 0
total_files: 0
tasks:
  - id: ""
    files: []
    complexity: trivial|standard|complex
    depends_on: []
```

### L2
- Task descriptions with file ownership
- Dependency chain visualization
- Complexity estimates per task

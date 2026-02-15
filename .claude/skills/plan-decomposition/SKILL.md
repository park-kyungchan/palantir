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

## Decision Points

### Tier Assessment for Decomposition
- **TRIVIAL**: Architecture has 1-2 components, each mapping to 1 task. Lead decomposes directly — no analyst needed. Total files ≤4.
- **STANDARD**: Architecture has 3-5 components, mapping to 3-8 tasks. Spawn 1 analyst for systematic decomposition with dependency analysis.
- **COMPLEX**: Architecture has 6+ components spanning 3+ modules, mapping to 9+ tasks. Spawn 2-4 analysts, each responsible for non-overlapping architecture modules.

### Spawn vs Lead-Direct Heuristic
- **Lead-direct when**: Total expected tasks ≤3, AND all components are in a single module, AND no cross-component dependencies exist
- **Spawn analyst when**: Expected tasks >3, OR cross-module dependencies exist, OR component structure is non-trivial
- **Multiple analysts when**: Architecture has clearly separable module boundaries AND total components >5

### Task Granularity Decision
How fine-grained should tasks be?
- **Too coarse** (1 task for entire module): Agent context overflow, hard to parallelize, all-or-nothing failure
- **Too fine** (1 task per function): Excessive coordination overhead, interface explosion, over-decomposition
- **Right granularity**: 1 task per coherent unit of work, typically 2-4 files, representing one testable behavior change
- **Heuristic**: If a task description needs >3 sentences to explain, it's too coarse. If it can be described in <5 words, it's too fine.

### File Assignment Strategy
- **By module** (default): All files in a module go to the same task. Minimizes cross-task dependencies.
- **By layer** (when architecture is layered): Group files by layer (API, service, data). Each layer task has minimal dependencies.
- **By feature** (when feature cuts across layers): Group all files for one feature together. Creates self-contained tasks.

Selection: Use module grouping by default. Switch to feature grouping when >50% of cross-module dependencies are within the same feature.

### Complexity Estimation Calibration
Complexity directly affects orchestration-assign's agent selection and maxTurns allocation:
- **Under-estimating** (calling COMPLEX task TRIVIAL): Agent runs out of turns, incomplete work
- **Over-estimating** (calling TRIVIAL task COMPLEX): Wasteful resource allocation
- **Calibration signals**: File count, dependency count, test requirement, integration points

| Indicator | TRIVIAL | STANDARD | COMPLEX |
|-----------|---------|----------|---------|
| Files per task | 1-2 | 3-4 | 5+ |
| Dependencies | 0 | 1-2 | 3+ |
| Test required | No/unit | Unit | Integration |
| Module boundary | Same | 1-2 | Cross-module |

## Methodology

### 1. Read Architecture and Research
Load design-architecture ADRs and research-audit findings.
List all components needing implementation.

### 2. Break Components into Tasks
For each component:
- Define 1 task per coherent unit of work
- Max 4 files per task (non-overlapping ownership)
- Task subject: imperative action verb + target ("Implement X handler")

**DPS — Analyst Spawn Template:**
- **Context**: Paste design-architecture L1 (components[] with names, responsibilities, dependencies) and research-audit L1 (coverage matrix, validated patterns). Include file system structure hints from research-codebase L2 (existing file paths and patterns).
- **Task**: "Decompose each component into implementation tasks. Per task: imperative subject, max 4 files (non-overlapping), complexity estimate (T/S/C). Map dependencies: blocks/independent per task pair. Identify critical path."
- **Scope**: For COMPLEX, split by architecture module — non-overlapping analyst assignments.
- **Constraints**: Read-only. Use Glob for file system validation. No modifications.
- **Expected Output**: L1 YAML with task_count, tasks[] (id, files, complexity, depends_on). L2 task descriptions and dependency visualization.

### 3. Assign File Ownership
Rules:
- Each file belongs to exactly 1 task
- Related files (e.g., module + its tests) stay in same task
- Config files (.claude/) go to infra tasks, source files to code tasks

#### File Ownership Conflict Resolution
When a file logically belongs to multiple tasks:
1. **Identify primary modifier**: Which task makes the most significant change to the file?
2. **Assign to primary**: Give ownership to the primary modifier
3. **Create interface**: The secondary task gets an interface contract describing what it needs from the file
4. **Ordering**: Primary task executes first, secondary task executes after and uses the modified file

Common conflict patterns:
- **Shared config file**: Assign to the task that creates/restructures it. Other tasks get read access.
- **Module index file (e.g., `__init__.py`, `index.ts`)**: Assign to the last task that adds exports to it. Earlier tasks define their exports in interface contracts.
- **Test file**: Assign to the same task as the code it tests. If testing multiple tasks' code, create a dedicated integration test task.

### 4. Map Dependencies
For each task pair, determine:
- **blocks**: Task A must complete before Task B can start
- **independent**: Tasks can run in parallel
- Identify critical path (longest dependency chain)

#### Dependency Pattern Recognition
Common dependency patterns and how to handle them:

| Pattern | Example | Handling |
|---------|---------|----------|
| Producer-Consumer | Task A creates module, Task B imports it | Hard dependency: A → B |
| Shared Schema | Task A and B both use type T | Interface contract: define T first |
| Test Dependency | Task A writes code, Task B writes tests | Sequential: A → B |
| Config Dependency | Task A creates config, Task B reads it | Hard dependency: A → B |
| Parallel Safe | Task A and B modify different modules | Independent: A ∥ B |

#### Critical Path Identification
1. Build dependency DAG from all task dependencies
2. Calculate longest path through DAG (sum of complexity estimates)
3. Tasks ON the critical path must be prioritized in execution
4. Tasks OFF the critical path can be delayed without affecting total completion time
5. Report critical path in L2 with estimated duration

### 5. Estimate Complexity
Per task:
- TRIVIAL: <=2 files, single function/section change
- STANDARD: 3-4 files, connected changes
- COMPLEX: Cross-module, requires integration testing

## Failure Handling

### Architecture Data Insufficient
- **Cause**: design-architecture didn't produce enough detail for task decomposition
- **Action**: Route back to design-architecture with specific questions (e.g., "How should module X interact with module Y?")
- **Never decompose speculatively**: without clear architecture, task definitions will be wrong

### Research Findings Contradict Architecture
- **Cause**: research-audit found patterns that conflict with architecture decisions
- **Action**: Route to design-architecture for reconciliation. Include specific contradiction details.
- **Example**: Architecture specifies REST API but codebase uses GraphQL everywhere

### Complexity Underestimation Detected (Post-Hoc)
- **Cause**: During execution, a TRIVIAL-estimated task turns out to be COMPLEX
- **Action**: Not directly handled here (execution handles it). But decomposition can prevent this by:
  - Cross-checking file count against complexity estimate
  - Flagging tasks where files span multiple modules as minimum STANDARD

### Circular Dependencies in Task Graph
- **Cause**: Task A depends on Task B which depends on Task A
- **Action**: Merge the circular tasks into a single larger task, or break the cycle by extracting a shared interface contract
- **Report**: Include cycle details in L2 for plan-interface to address

## Anti-Patterns

### DO NOT: Create Tasks Without File Assignments
Every task must specify exact file paths to create or modify. Tasks like "Set up the database" without file assignments are un-implementable — orchestration cannot assign them to an agent.

### DO NOT: Assign Same File to Multiple Tasks
This creates merge conflicts during execution. If two tasks need the same file, either merge the tasks or use interface contracts to sequence access.

### DO NOT: Ignore Existing Codebase Patterns
Research-codebase findings reveal existing patterns. New tasks should follow these patterns. A task that creates a new pattern where an existing one applies will fail review.

### DO NOT: Decompose Below Test Granularity
Each task should be independently testable. If a task's changes can't be verified without another task's changes, the tasks should be merged.

### DO NOT: Create Tasks for Orchestration Concerns
Tasks should describe WHAT to implement, not HOW to orchestrate. "Spawn 2 implementers" is an orchestration concern, not a plan task. Plan tasks describe implementation goals.

### DO NOT: Over-Decompose TRIVIAL Tiers
For TRIVIAL tiers (1-2 components), creating more than 2-3 tasks adds unnecessary overhead. The benefit of parallelism disappears with only 1-2 agent instances.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| research-audit | Consolidated research findings | L1 YAML: `coverage_matrix`, `findings[]`, L2: pattern details |
| design-architecture | Component structure with ADRs | L1 YAML: `components[]`, L2: module boundaries, data flow |
| research-codebase | Existing codebase patterns | L2: file paths, conventions, existing structure |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-interface | Task list with file assignments | Always (decomposition → interface) |
| plan-strategy | Task list with dependencies | Always (decomposition → strategy via interface) |
| orchestration-decompose | Approved task list | After plan-verify PASS (indirect) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Architecture insufficient | design-architecture | Specific missing detail questions |
| Research contradicts architecture | design-architecture | Contradiction details |
| Circular dependencies | Self (re-decompose) or plan-interface | Cycle details |

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

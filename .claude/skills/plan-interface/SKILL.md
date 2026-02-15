---
name: plan-interface
description: |
  [P3·Plan·Interface] Interface specification and dependency ordering specialist. Defines precise interface contracts between tasks and determines completion order based on interface dependencies.

  WHEN: After plan-decomposition produces task breakdown. Tasks exist but inter-task interfaces undefined.
  DOMAIN: plan (skill 2 of 3). Sequential: decomposition -> interface -> strategy.
  INPUT_FROM: plan-decomposition (task list with file assignments), design-interface (API contracts from design).
  OUTPUT_TO: plan-strategy (interface constraints for sequencing), orchestration-assign (interface dependencies for assignment).

  METHODOLOGY: (1) Read task breakdown and design interfaces, (2) For each task boundary: define input/output contract, (3) Map design interfaces to task-level interfaces, (4) Determine dependency ordering (which tasks first), (5) Identify integration points needing cross-task coordination.
  OUTPUT_FORMAT: L1 YAML interface registry per task, L2 dependency ordering with rationale.
user-invocable: true
disable-model-invocation: false
---

# Plan — Interface

## Execution Model
- **TRIVIAL**: Lead-direct. Simple interface list between 2-3 tasks.
- **STANDARD**: Spawn analyst. Formal inter-task contract specification.
- **COMPLEX**: Spawn 2-4 analysts. Each covers non-overlapping task boundaries.

## Decision Points

### Tier Assessment for Interface Specification
- **TRIVIAL**: 1-3 tasks with 0-1 cross-task boundaries. Lead defines interfaces directly. No analyst spawn.
- **STANDARD**: 4-6 tasks with 2-4 boundaries. Spawn 1 analyst for formal contract specification.
- **COMPLEX**: 7+ tasks with 5+ boundaries, cross-module interfaces, shared data structures. Spawn 2-4 analysts, each covering non-overlapping boundary clusters.

### Contract Formality Level
How detailed should interface contracts be?
- **Minimal** (TRIVIAL): "Task A produces file X.ts, Task B reads it." Just file paths and names.
- **Standard** (STANDARD): Function signatures, data types, return values, error cases. Enough for implementers to work independently.
- **Full** (COMPLEX): Complete contract with validation rules, example payloads, edge cases, versioning. Required when tasks are assigned to different agents who cannot coordinate at runtime.

Rule: Formality level should match tier. Over-specifying TRIVIAL interfaces wastes planning time. Under-specifying COMPLEX interfaces causes integration failures.

### Design Interface Reuse Decision
- **Direct reuse**: When design-interface contract maps 1:1 to a task boundary → copy contract directly
- **Adaptation needed**: When design-interface covers a broader scope than a single task boundary → extract relevant subset
- **New contract needed**: When task decomposition created boundaries not present in design → define new contract
- **Gap detection**: If design-interface has no contract for a task boundary → flag as design gap, route to design-interface for completion

### Ordering Strategy Selection
Two approaches to determining implementation order:

**Bottom-up** (default): Start with tasks that have no dependencies (leaf tasks), work up to tasks that consume their outputs.
- Best for: Independent modules, clear producer-consumer relationships
- Parallel opportunity: All leaf tasks can start simultaneously

**Top-down** (when integration is priority): Start with the integration task, stub its dependencies, then implement stubs.
- Best for: Complex integration points where interface validation is critical early
- Risk: Stubs may not reflect real implementation behavior

Selection heuristic: Use bottom-up unless design-risk identified integration as high-RPN risk.

## Methodology

### 1. Read Task Breakdown
Load plan-decomposition output and design-interface contracts.
List all task boundaries where output of one feeds input of another.

### 2. Define Task-Level Contracts
For each task boundary:
- **Producer task**: What it outputs (file format, data structure, location)
- **Consumer task**: What it expects (required fields, types, paths)
- **Validation**: How consumer verifies producer's output

**DPS — Analyst Spawn Template:**
- **Context**: Paste plan-decomposition L1 (tasks[] with files, dependencies) and design-interface L1 (interface registry, contracts). For each task boundary, include the producer task's files and the consumer task's expected inputs.
- **Task**: "For each task boundary: define producer output format (file/data structure/location), consumer expectation (required fields/types/paths), validation method. Map to design interfaces. Determine implementation ordering (no-dep tasks first)."
- **Constraints**: Read-only. No modifications. Cross-reference plan and design artifacts.
- **Expected Output**: L1 YAML with contract_count, contracts[] (producer, consumer, data_type, validated). L2 contracts and ordering.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Contract Template
Each interface contract should specify:
```
Contract: {producer_task_id} -> {consumer_task_id}
Type: file_output | function_call | data_structure | event
Producer output:
  - Path/format: {where/what the producer creates}
  - Schema: {data structure, required fields, types}
  - Validation: {how consumer can verify correctness}
Consumer expectation:
  - Required fields: {what must be present}
  - Optional fields: {what may be present}
  - Error handling: {what to do if validation fails}
```

#### Contract Quality Checklist
For each contract, verify:
- [ ] Producer and consumer tasks both exist in plan-decomposition
- [ ] Data types are concrete (not "some data" but "JSON object with fields X, Y, Z")
- [ ] Validation method is implementable (not "check it looks right" but "verify field X is non-null string")
- [ ] Error handling is specified (what happens when contract is violated at runtime)
- [ ] Both sides use the same terminology (no naming mismatches between producer and consumer)

### 3. Map to Design Interfaces
Connect task-level contracts to design-interface specifications:
- Each design interface should map to >=1 task boundary
- Flag gaps: design interfaces without corresponding task boundaries

#### Interface Mapping Matrix
| Design Interface | Task Boundary | Mapping Type | Status |
|-----------------|---------------|-------------|--------|
| API /users endpoint | T1 -> T3 | Direct reuse | Mapped |
| Database schema | T2 -> T4 | Adaptation (subset) | Mapped |
| Auth token flow | T3 -> T5 | New (design gap) | FLAG |

Flags indicate design gaps that should be reported to design-interface for resolution.

### 4. Determine Implementation Order
Based on producer-consumer relationships:
1. Tasks with no dependencies -> Tier 1 (parallel start)
2. Tasks depending on Tier 1 -> Tier 2
3. Continue until all tasks ordered
- Document rationale for ordering decisions

#### Implementation Tier Visualization
```
Tier 1 (no dependencies, parallel start):
  |-- Task-A (create user model)
  +-- Task-B (create auth module)

Tier 2 (depends on Tier 1):
  |-- Task-C (implement API endpoints) -> depends on A
  +-- Task-D (implement auth middleware) -> depends on B

Tier 3 (depends on Tier 2):
  +-- Task-E (integration tests) -> depends on C, D
```

#### Parallelism Opportunity Report
For each tier, report:
- Tasks that can run simultaneously
- Estimated time savings from parallelism vs sequential
- Dependencies that constrain parallelism (potential optimization targets)

### 5. Identify Integration Points
Tasks requiring cross-task coordination:
- Shared data structures
- File system conventions (naming, paths)
- Task API metadata schemas

## Failure Handling

### Design Interface Gaps
- **Cause**: Task boundary exists but no corresponding design-interface contract
- **Action**: Flag in L2 output. Route to design-interface for gap completion. Do NOT proceed with undefined contracts -- this causes integration failures downstream.
- **Workaround**: For non-critical boundaries, define a minimal contract (file path + basic schema) as a placeholder. Mark as `validated: false`.

### Incompatible Contracts
- **Cause**: Producer output format doesn't match consumer expectation (design error)
- **Action**: Report specific mismatch. Route to design-interface for resolution. Include both sides' expectations.
- **Never resolve by**: changing task decomposition to match broken contracts -- fix the contract, not the plan.

### Circular Interface Dependencies
- **Cause**: Task A's contract requires Task B's output, and vice versa
- **Action**: Break cycle by extracting shared data structure into a pre-task (Task 0 that both depend on). Route to plan-decomposition for task restructuring if cycle involves file assignments.

### Analyst Failed to Complete Contract Specification
- **Cause**: Too many boundaries for analyst turns, or ambiguous architecture
- **Action**: Set `status: partial`. Include completed contracts. Route incomplete boundaries back for second analyst pass.
- **Pipeline impact**: plan-strategy can proceed with completed contracts. Missing contracts become known risks.

## Anti-Patterns

### DO NOT: Define Contracts Without Concrete Types
"Task A sends data to Task B" is not a contract. "Task A writes `UserModel` JSON to `/tmp/users.json` with fields `{id: string, name: string, email: string}`" IS a contract. Concrete types prevent integration failures.

### DO NOT: Ignore Design-Interface Contracts
Task-level contracts should refine design-interface contracts, not replace them. If plan creates a new contract that contradicts design, it's a design gap -- not a planning override.

### DO NOT: Over-Specify Internal Contracts
For tasks assigned to the SAME agent instance, formal contracts are unnecessary overhead. The agent has both files in context. Only specify formal contracts for CROSS-AGENT boundaries.

### DO NOT: Create Contracts for Read-Only Access
If Task B only READS a file that Task A creates (doesn't modify it), the contract is simply: "Task B reads file X after Task A completes." No schema specification needed for read-only access to existing files.

### DO NOT: Define Ordering Without Dependencies
Implementation order must be justified by dependency edges or interface contracts. Arbitrary ordering ("do A first because it's simpler") wastes parallelism opportunities.

### DO NOT: Skip Integration Point Documentation
Tasks that share data structures, file conventions, or API schemas need explicit integration point documentation. Undocumented integration points become the most common source of execution failures.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-decomposition | Task list with file assignments and dependencies | L1 YAML: `tasks[].{id, files[], depends_on[]}` |
| design-interface | API contracts and integration point designs | L1 YAML: `interfaces[]`, L2: contract specifications |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-strategy | Interface constraints and implementation ordering | Always (interface -> strategy) |
| orchestration-assign | Interface dependencies for assignment | After plan-verify PASS (indirect) |
| design-interface | Design gap report | If unmapped task boundaries found |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Design interface gaps | design-interface | Unmapped boundary list |
| Incompatible contracts | design-interface | Mismatch details (both sides) |
| Circular dependencies | plan-decomposition | Cycle details and split recommendation |
| Analyst incomplete | Self (second pass) | Remaining boundaries to specify |

## Quality Gate
- Every task boundary has defined contract
- Producer output matches consumer expectation
- Implementation order is deterministic and acyclic
- All design interfaces mapped to task contracts

## Output

### L1
```yaml
domain: plan
skill: interface
contract_count: 0
integration_points: 0
implementation_tiers: 0
contracts:
  - producer: ""
    consumer: ""
    data_type: ""
    validated: true|false
```

### L2
- Interface contracts per task boundary
- Implementation ordering with tier groups
- Integration point documentation

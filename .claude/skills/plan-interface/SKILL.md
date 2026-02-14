---
name: plan-interface
description: |
  [P4·Plan·Interface] Interface specification and dependency ordering specialist. Defines precise interface contracts between tasks and determines completion order based on interface dependencies.

  WHEN: After plan-decomposition produces task breakdown. Tasks exist but inter-task interfaces undefined.
  DOMAIN: plan (skill 2 of 3). Sequential: decomposition -> interface -> strategy.
  INPUT_FROM: plan-decomposition (task list with file assignments), design-interface (API contracts from design).
  OUTPUT_TO: plan-strategy (interface constraints for sequencing), orchestration-assign (interface dependencies for assignment).

  METHODOLOGY: (1) Read task breakdown and design interfaces, (2) For each task boundary: define input/output contract, (3) Map design interfaces to task-level interfaces, (4) Determine dependency ordering (which tasks first), (5) Identify integration points needing cross-task coordination.
  OUTPUT_FORMAT: L1 YAML interface registry per task, L2 dependency ordering with rationale, L3 contracts.
user-invocable: true
disable-model-invocation: false
---

# Plan — Interface

## Execution Model
- **TRIVIAL**: Lead-direct. Simple interface list between 2-3 tasks.
- **STANDARD**: Spawn analyst. Formal inter-task contract specification.
- **COMPLEX**: Spawn 2-4 analysts. Each covers non-overlapping task boundaries.

## Methodology

### 1. Read Task Breakdown
Load plan-decomposition output and design-interface contracts.
List all task boundaries where output of one feeds input of another.

### 2. Define Task-Level Contracts
For each task boundary:
- **Producer task**: What it outputs (file format, data structure, location)
- **Consumer task**: What it expects (required fields, types, paths)
- **Validation**: How consumer verifies producer's output

### 3. Map to Design Interfaces
Connect task-level contracts to design-interface specifications:
- Each design interface should map to >=1 task boundary
- Flag gaps: design interfaces without corresponding task boundaries

### 4. Determine Implementation Order
Based on producer-consumer relationships:
1. Tasks with no dependencies -> Tier 1 (parallel start)
2. Tasks depending on Tier 1 -> Tier 2
3. Continue until all tasks ordered
- Document rationale for ordering decisions

### 5. Identify Integration Points
Tasks requiring cross-task coordination:
- Shared data structures
- File system conventions (naming, paths)
- Task API metadata schemas

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

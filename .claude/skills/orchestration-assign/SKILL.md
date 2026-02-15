---
name: orchestration-assign
description: |
  [P6·Orchestration·Assign] Teammate selection and task mapping specialist. Maps task groups to agent types via frontmatter WHEN conditions, tool requirements, and capabilities. Produces task-teammate matrix.

  WHEN: After orchestration-decompose produces task groups. Tasks decomposed but not yet assigned.
  DOMAIN: orchestration (skill 2 of 3). Sequential: decompose -> assign -> verify.
  INPUT_FROM: orchestration-decompose (task groups with dependency edges), plan-interface (interface dependencies for assignment).
  OUTPUT_TO: orchestration-verify (assignments for validation), execution domain (after verify PASS).

  METHODOLOGY: (1) Read task groups from decomposition, (2) Match each group to best agent type using frontmatter WHEN/TOOLS, (3) Assign tasks respecting 4-teammate limit, (4) Balance workload across teammates, (5) Generate task-teammate matrix with rationale.
  OUTPUT_FORMAT: L1 YAML task-teammate matrix, L2 ASCII assignment visualization with workload balance.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Assign

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 assignments.
- **STANDARD**: Lead-direct. Uses Agent L1 WHEN conditions for matching.
- **COMPLEX**: Lead-direct with sequential-thinking for complex assignment optimization.

## Methodology

### 1. Read Decomposed Groups
Load orchestration-decompose output (task groups with agent capability).

### 2. Match Groups to Agent Types
For each group, select specific agent type:

| Agent | Profile | Best For |
|-------|---------|----------|
| analyst | B (ReadAnalyzeWrite) | Analysis, design, verification, planning |
| researcher | C (ReadAnalyzeWriteWeb) | External docs, library research, API validation |
| implementer | D (CodeImpl) | Source code changes, test execution |
| infra-implementer | E (InfraImpl) | .claude/ file changes, configuration |

### 3. Balance Workload
Within each execution phase:
- No agent type spawned more than 4 times
- Distribute tasks evenly across instances
- Consider task complexity for balanced assignment

### 4. Generate Assignment Matrix

| Group | Agent Type | Instance | Tasks | Files |
|-------|-----------|----------|-------|-------|
| G1 | analyst | analyst-1 | [T1, T2] | [a.md, b.md] |
| G2 | implementer | impl-1 | [T3] | [c.ts, d.ts] |

### 5. Document Rationale
For each assignment:
- Why this agent type? (WHEN condition match)
- Why this task grouping? (dependency + capability)
- Any alternatives considered?

## Quality Gate
- Every group assigned to exactly 1 agent type
- No agent type exceeds 4 instances
- No file assigned to multiple agent instances
- Rationale documented per assignment

## Output

### L1
```yaml
domain: orchestration
skill: assign
assignment_count: 0
agent_types_used: 0
assignments:
  - group: ""
    agent_type: ""
    instance: ""
    tasks: []
    files: []
```

### L2
- Task-teammate assignment matrix
- Workload balance indicators
- Assignment rationale per group

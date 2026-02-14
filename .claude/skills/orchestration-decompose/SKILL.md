---
name: orchestration-decompose
description: |
  [P6a·Orchestration·Decompose] Task-to-teammate decomposition specialist. Analyzes validated plan to break tasks into teammate-assignable work units with dependency awareness. Uses Agent/Skill frontmatter already in Lead's context for routing.

  WHEN: plan-verify domain complete (all 3 PASS). Validated plan ready for teammate assignment. Domain entry point for orchestration.
  DOMAIN: orchestration (skill 1 of 3). Sequential: decompose → assign → verify.
  INPUT_FROM: plan-verify domain (PASS verdict), plan-decomposition (task list with dependencies).
  OUTPUT_TO: orchestration-assign (decomposed tasks ready for teammate mapping).

  CONSTRAINT: Use ONLY Agent/Skill frontmatter already in Lead's Main Context. NO external file reads (no agent-catalog.md, no references/).
  METHODOLOGY: (1) Read validated plan, (2) Group tasks by agent capability match (using frontmatter descriptions), (3) Identify dependency chains between task groups, (4) Ensure each group respects 4-teammate limit, (5) Output decomposition with dependency edges.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML task groups with dependency edges, L2 ASCII dependency graph visualization.
user-invocable: true
disable-model-invocation: true
---

# Orchestration — Decompose

## Execution Model
- **TRIVIAL**: Lead-direct. Simple 1-2 task grouping.
- **STANDARD**: Lead-direct (uses auto-loaded Agent/Skill L1 for routing).
- **COMPLEX**: Lead-direct with sequential-thinking for complex grouping decisions.

Note: This skill is always Lead-direct because it requires access to Agent/Skill frontmatter already in Lead's context.

## Methodology

### 1. Read Validated Plan
Load plan-strategy output (execution phases, task list, dependencies).

### 2. Group Tasks by Agent Capability
Match tasks to agent profiles using L1 PROFILE tags:
- **analyst** (Profile-B): Read + analyze + write. For analysis, design, planning tasks.
- **researcher** (Profile-C): Read + analyze + web. For external doc research.
- **implementer** (Profile-D): Read + edit + bash. For source code changes.
- **infra-implementer** (Profile-E): Read + edit + write. For .claude/ config changes.

### 3. Build Task Groups
Group tasks that:
- Need the same agent profile
- Can execute in parallel (no dependencies)
- Stay within 4-teammate limit

### 4. Define Dependency Edges
Between groups:
- Group A -> Group B: at least 1 task in B depends on task in A
- Minimize cross-group dependencies
- No cycles allowed

### 5. Output Decomposition
Produce task-group list with:
- Group ID, tasks, agent capability match
- Dependency edges between groups
- Execution order (topological sort)

## Quality Gate
- Every task assigned to exactly 1 group
- Agent capability matches task requirements
- Dependency graph is acyclic
- Each group <=4 tasks (teammate limit)

## Output

### L1
```yaml
domain: orchestration
skill: decompose
group_count: 0
dependency_edges: 0
groups:
  - id: ""
    tasks: []
    agent_capability: ""
```

### L2
- Task grouping rationale
- Dependency edge justification
- ASCII dependency graph

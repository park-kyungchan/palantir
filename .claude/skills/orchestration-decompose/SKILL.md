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

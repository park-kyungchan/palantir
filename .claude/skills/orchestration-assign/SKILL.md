---
name: orchestration-assign
description: |
  [P6a·Orchestration·Assign] Teammate selection and task mapping specialist. Maps decomposed task groups to specific agent types based on frontmatter WHEN conditions, tool requirements, and model capabilities. Produces task-teammate matrix.

  WHEN: After orchestration-decompose produces task groups. Tasks decomposed but not assigned to teammates.
  DOMAIN: orchestration (skill 2 of 3). Sequential: decompose → assign → verify.
  INPUT_FROM: orchestration-decompose (task groups with dependency edges).
  OUTPUT_TO: orchestration-verify (assignments for validation), execution domain (validated assignments after verify PASS).

  CONSTRAINT: Max 4 teammates per domain execution. Consider agent WHEN conditions from frontmatter descriptions.
  METHODOLOGY: (1) Read task groups from decomposition, (2) Match each group to best agent type using frontmatter WHEN/TOOLS/MODEL, (3) Assign tasks respecting 4-teammate limit, (4) Balance workload across teammates, (5) Generate task-teammate matrix with rationale.
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML task-teammate matrix, L2 ASCII assignment visualization with workload balance indicators.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Assign

## Output

### L1
```yaml
domain: orchestration
skill: assign
total_teammates: 0
assignments:
  - group: ""
    agent_type: ""
    teammate_count: 0
    rationale: ""
```

### L2
- Agent type matching rationale
- Workload balance analysis
- ASCII assignment matrix

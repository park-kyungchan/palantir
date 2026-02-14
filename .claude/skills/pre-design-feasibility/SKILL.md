---
name: pre-design-feasibility
description: |
  [P0-1·PreDesign·Feasibility] Claude Code native capabilities verification. Spawns claude-code-guide agent to check whether proposed requirements can be implemented using only CC native features (tools, skills, agents, hooks, MCP).

  WHEN: After pre-design-validate PASS. Requirements complete but CC feasibility unconfirmed.
  DOMAIN: pre-design (skill 3 of 3). Sequential: brainstorm → validate → feasibility. Terminal skill in pre-design domain.
  INPUT_FROM: pre-design-validate (validated, complete requirements).
  OUTPUT_TO: design-architecture (feasibility-confirmed requirements ready for architecture).

  METHODOLOGY: (1) Extract technical requirements from validated document, (2) Spawn claude-code-guide: "Can these requirements be implemented with Claude Code native capabilities?", (3) Analyze response for blockers, (4) If infeasible: identify alternatives or scope reduction, report to Lead, (5) If feasible: approve and pass to design.
  CLOSED_LOOP: Check → FAIL → Revise requirements → Re-check (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML feasibility verdict per requirement, L2 markdown feasibility report with alternatives for infeasible items.
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Feasibility

## Output

### L1
```yaml
domain: pre-design
skill: feasibility
status: PASS|FAIL
feasible: 0
infeasible: 0
items:
  - requirement: ""
    verdict: feasible|infeasible|partial
    alternative: ""
```

### L2
- Per-requirement feasibility verdict with CC capability mapping
- Alternatives for infeasible items
- claude-code-guide consultation summary

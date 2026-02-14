---
name: manage-skills
description: |
  [Homeostasis·Manager·Skills] Session-aware skill lifecycle manager. Detects codebase changes via git diff, maps changed files to domains (pre-design through verify), determines CREATE/UPDATE/DELETE actions for skills across ALL 9 domains.

  WHEN: After implementing features that introduce new patterns, after modifying skills, before PR, or periodically for drift detection. AI can auto-invoke after session changes.
  DOMAIN: Homeostasis (cross-cutting, operates on .claude/skills/ directory).

  DETECTION_RULES: .claude/agents/ changes → design domain, .claude/skills/ changes → self-management, .claude/references/ changes → research domain, docs/plans/ changes → plan domain, 3+ uncovered files in same domain → CREATE new skill.
  METHODOLOGY: (1) Run git diff to detect changes, (2) Map changed files to domains via detection rules, (3) Check existing skill coverage per domain, (4) Propose CREATE/UPDATE/DELETE actions, (5) User approval, (6) Execute, (7) Run verify-cc-feasibility on results.
  CLOSED_LOOP: Detect → Analyze → Propose → Approve → Execute → Verify → Done.
  OUTPUT_FORMAT: L1 YAML action list (CREATE/UPDATE/DELETE per skill), L2 markdown change analysis with rationale.
user-invocable: true
disable-model-invocation: false
input_schema:
  type: object
  properties:
    target_domain:
      type: string
      enum: ["pre-design", "design", "research", "plan", "plan-verify", "orchestration", "execution", "verify", "all"]
      description: "Domain to analyze (default: all)"
    action:
      type: string
      enum: ["scan", "create", "update", "delete"]
      description: "Action to perform (default: scan)"
  required: []
---

# Manage — Skills

## Output

### L1
```yaml
domain: homeostasis
skill: manage-skills
status: complete
actions:
  - skill: ""
    action: CREATE|UPDATE|DELETE
    domain: ""
    reason: ""
```

### L2
- Git diff analysis summary
- Domain coverage report
- Proposed action rationale per skill

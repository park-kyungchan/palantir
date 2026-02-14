---
name: delivery-pipeline
description: |
  [P9·Delivery·Terminal] Pipeline-end delivery executor. Consolidates all domain outputs, creates git commit with structured message, archives session artifacts to MEMORY.md and ARCHIVE.md, updates PERMANENT Task to DELIVERED status.

  WHEN: verify domain complete (all 5 stages PASS). Pipeline finished. Ready for commit and archive.
  DOMAIN: Cross-cutting terminal phase (not part of 9-domain feedback loop).
  INPUT_FROM: verify domain (all-PASS verification report).
  OUTPUT_TO: Git repository (commit), MEMORY.md (knowledge archive), ARCHIVE.md (session archive).

  PREREQUISITE: All verify-* skills must return PASS. No outstanding FAIL findings.
  METHODOLOGY: (1) Read verify domain all-PASS report, (2) Consolidate pipeline results from all domains, (3) Generate commit message from PT impact map and architecture decisions, (4) Archive session learnings to MEMORY.md, (5) Mark PT as DELIVERED via TaskUpdate, (6) Create git commit, (7) Cleanup session artifacts.
  CONSTRAINT: Executed by delivery-agent fork. Requires user confirmation before git commit.
  OUTPUT_FORMAT: L1 YAML delivery manifest, L2 markdown delivery summary with commit hash.
user-invocable: true
disable-model-invocation: true
confirm: true
input_schema:
  type: object
  properties:
    commit_message:
      type: string
      description: "Optional custom commit message override"
  required: []
---

# Delivery Pipeline

## Fork Execution

Executed by `delivery-agent` (`subagent_type: delivery-agent`).
Agent has TaskUpdate only (no TaskCreate). Requires user confirmation before git commit.

## Output

### L1
```yaml
domain: cross-cutting
skill: delivery-pipeline
status: delivered
commit_hash: ""
files_changed: 0
pt_status: DELIVERED
```

### L2
- Delivery manifest (all domain outputs)
- Commit message with impact summary
- Archive entries (MEMORY.md + ARCHIVE.md)

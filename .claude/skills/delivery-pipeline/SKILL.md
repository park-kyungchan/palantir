---
name: delivery-pipeline
description: |
  [P9·Delivery·Terminal] Pipeline-end delivery executor. Consolidates all domain outputs, creates git commit with structured message, archives session learnings to MEMORY.md, updates PERMANENT Task to DELIVERED status.

  WHEN: verify domain complete (all 5 stages PASS). Pipeline finished. Ready for commit and archive.
  DOMAIN: Cross-cutting terminal phase (not part of 9-domain feedback loop).
  INPUT_FROM: verify domain (all-PASS verification report).
  OUTPUT_TO: Git repository (commit), MEMORY.md (knowledge archive).

  PREREQUISITE: All verify-* skills must return PASS. No outstanding FAIL findings.
  METHODOLOGY: (1) Read verify domain all-PASS report, (2) Consolidate pipeline results from all domains, (3) Generate commit message from PT impact map and architecture decisions, (4) Archive session learnings to MEMORY.md, (5) Mark PT as DELIVERED via TaskUpdate, (6) Create git commit, (7) Cleanup session artifacts.
  CONSTRAINT: Executed by delivery-agent fork. Requires user confirmation before git commit.
  OUTPUT_FORMAT: L1 YAML delivery manifest, L2 markdown delivery summary with commit hash.
user-invocable: true
disable-model-invocation: true
argument-hint: "[commit-message]"
---

# Delivery Pipeline

## Execution Model
- **TRIVIAL**: Lead-direct via delivery-agent fork. Simple commit with 1-2 files.
- **STANDARD**: delivery-agent fork. Full consolidation + commit + archive.
- **COMPLEX**: delivery-agent fork with extended consolidation from multiple domains.

## Methodology

### 1. Verify All-PASS Status
Before any delivery action:
- Read verify domain output: all 5 stages must show PASS
- If any FAIL: abort delivery, report to Lead for fix loop
- Confirm no outstanding critical findings

### 2. Consolidate Pipeline Results
Gather outputs from all pipeline domains:
- Pre-design: requirements and feasibility results
- Design: architecture decisions, interface contracts, risk assessment
- Research: codebase patterns, external dependency validation
- Plan: task breakdown, interface specs, implementation strategy
- Execution: file change manifests, review findings

### 3. Generate Commit Message
Build structured commit message from consolidation:
- Title: concise summary of pipeline purpose
- Body: key decisions, files changed, architecture rationale
- Include Co-Authored-By attribution

### 4. Archive Session Learnings
Update MEMORY.md with:
- New patterns discovered during pipeline
- Architecture decisions worth remembering
- Bug fixes or workarounds found
- Update topic file index if new topics created

### 5. Execute Delivery
With user confirmation:
- Mark PT as DELIVERED via TaskUpdate
- Stage relevant files with git add
- Create git commit with structured message
- Cleanup session artifacts (team files, temporary outputs)

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
- Archive entries (MEMORY.md)

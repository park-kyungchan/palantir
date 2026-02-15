---
name: delivery-pipeline
description: |
  [P9·Delivery·Terminal] Pipeline-end delivery executor. Consolidates all domain outputs, creates git commit with structured message, archives session learnings to MEMORY.md, updates PT to DELIVERED status.

  WHEN: Verify domain complete (all 5 stages PASS, no outstanding FAIL). Pipeline finished, ready for commit and archive.
  DOMAIN: Cross-cutting terminal phase (not part of 9-domain feedback loop).
  INPUT_FROM: verify domain (all-PASS verification report).
  OUTPUT_TO: Git repository (commit), MEMORY.md (knowledge archive).

  METHODOLOGY: (1) Read verify all-PASS report, (2) Consolidate pipeline results, (3) Generate commit message from PT impact map and architecture decisions, (4) Archive learnings to MEMORY.md, (5) Mark PT DELIVERED via TaskUpdate, (6) Git commit, (7) Cleanup artifacts.
  CONSTRAINT: Executed by delivery-agent. Requires user confirmation before git commit.
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

## Quality Gate
- Verify domain all-PASS confirmed (no outstanding FAIL verdicts)
- All pipeline domain outputs consolidated
- Commit message includes: summary, key decisions, files changed
- MEMORY.md updated with session learnings (Read-Merge-Write)
- PT status marked DELIVERED via TaskUpdate
- Git commit successful with specific file staging (no git add -A)

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

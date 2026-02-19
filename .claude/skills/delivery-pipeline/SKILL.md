---
name: delivery-pipeline
description: >-
  [P8·Cross-Cutting·Terminal] Delivers pipeline results via
  structured git commit, MEMORY.md archive, and PT completion.
  User confirmation required before git commit. Pipeline terminal
  skill. Use after verify domain complete with all 4 stages PASS
  and no outstanding FAIL. Reads from verify-cc-feasibility (main
  pipeline) or self-implement (homeostasis path) with all-PASS
  confirmed. Produces git commit, MEMORY.md archive, and PT status
  DELIVERED. On FAIL (pre-commit hook failure or user rejection),
  Lead retries L0 or applies D12 escalation. DPS needs
  verify-cc-feasibility all-PASS confirmation + PT metadata for
  commit message. Exclude detailed verify findings beyond PASS
  status. delivery-agent memory:none — full context required in
  DPS (D11 exception: include all).
user-invocable: true
disable-model-invocation: false
argument-hint: "[commit-message]"
---

# Delivery Pipeline

## Current Git State
- Branch: !`git branch --show-current`
- Recent commits:
!`git log --oneline -3 2>/dev/null || echo "(no commits)"`

## Execution Model
- **TRIVIAL**: Lead-direct via delivery-agent fork. Simple commit with 1-2 files.
- **STANDARD**: delivery-agent fork. Full consolidation + commit + archive.
- **COMPLEX**: delivery-agent fork with extended consolidation from multiple domains.

## Methodology

### 1. Verify All-PASS Status
Before any delivery action:
- Read verify domain output: all 4 stages must show PASS
- If any FAIL: abort delivery, report to Lead for fix loop
- Confirm no outstanding critical findings

> delivery-agent has `memory: none` — Lead MUST include verify verdict summary in the spawn prompt.

### 2. Consolidate Pipeline Results
Gather outputs from all completed pipeline domains (pre-design through execution). Read Ch2 output files from `tasks/{team}/` directly.

### 3. Generate Commit Message
Build structured commit message using conventional commit format (`type(scope): summary`). Use `$ARGUMENTS` as commit title if provided; otherwise synthesize from PT description and key decisions.
> For commit format details, type/scope selection, and examples: read `resources/methodology.md`

### 4. Archive Session Learnings
Update MEMORY.md via Read-Merge-Write: read current content → merge new session entry + INFRA state updates + new topic file links → write merged result. Never overwrite without reading first.
> For archive procedure detail and session entry format: read `resources/methodology.md`

### 5. Execute Delivery
With user confirmation:
- Mark PT as DELIVERED via TaskUpdate
- Stage relevant files with git add (specific files only — never `git add -A`)
- Create git commit with structured message
- Cleanup session artifacts (team files, temporary outputs)

## Decision Points

### Commit Scope
- **Full pipeline**: All domains complete, verify all-PASS → single commit covering all changes.
- **Partial**: User requests commit of completed work before full pipeline finishes → stage only relevant subset.
- **Multi-commit**: COMPLEX tier with logically separable change sets → split into 2 commits with clear boundaries.

### MEMORY.md Archive Depth
- **Minimal**: TRIVIAL tier — 2-3 line session summary.
- **Standard**: STANDARD tier — session summary with key decisions, files changed, patterns discovered.
- **Extended**: COMPLEX tier or pipelines that discovered new bugs/workarounds — full session entry plus topic file updates.

### Delivery-Agent Spawn DPS
delivery-agent has `memory: none` — Lead must provide ALL context in spawn prompt (D11 exception: include all, not filter).
> For full INCLUDE/EXCLUDE list, DPS task spec, and tier-specific maxTurns: read `resources/methodology.md`

### Pre-Delivery Checklist
Before spawning delivery-agent, Lead must verify all required checks. If any fail, route to fix domain first.

| Check | Required |
|-------|----------|
| Verify all-PASS (all 4 stages) | Yes |
| PT exists with active status | Yes |
| No untracked sensitive files (.env, credentials) | Yes |
| Changed files manifest from execution domain | Yes |
| No outstanding FAIL routes pending | Yes |
| Branch is clean (no external uncommitted changes) | Recommended |

### Artifact Cleanup Scope
- **Conservative**: Remove only `/tmp/` session artifacts and team communication files.
- **Full**: Remove `/tmp/` artifacts, team files, and intermediate plan/design files fully captured in the commit.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Pre-commit hook failure (lint, format) | L0 Retry | Auto-fix via hook feedback, re-attempt commit |
| MEMORY.md archive format error | L1 Nudge | SendMessage with corrected archive format |
| delivery-agent exhausted turns or commit tool failure | L2 Respawn | Kill → fresh delivery-agent with refined DPS |
| PT metadata stale or verify status contradicted | L3 Restructure | Re-run verify stage before delivery |
| User rejects commit or strategic scope concern | L4 Escalate | AskUserQuestion with situation + options |

> For verbose failure sub-case detail (PT missing, git conflict, maxTurns exceeded, user rejection): read `resources/methodology.md`
> For escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

**DO NOT: Use `git add -A` or `git add .`** — always stage specific pipeline-changed files to avoid committing unrelated changes or sensitive data.

**DO NOT: Skip MEMORY.md Update for "Small" Changes** — every delivery archives learnings; small entries compound into institutional knowledge.

**DO NOT: Complete PT Before Git Commit Succeeds** — PT DELIVERED status must only be set after the commit is confirmed; premature completion creates false history.

**DO NOT: Deliver Without User Confirmation** — delivery-agent requires explicit AskUserQuestion confirmation before `git commit`, for all tiers without exception.

**DO NOT: Include Raw Agent Output in Commit Messages** — synthesize key decisions into clean conventional commit format; never copy-paste L1/L2 agent output.

**DO NOT: Deliver Partial Results Without User Awareness** — include non-blocking MEDIUM verify warnings in commit message body; hiding warnings erodes trust.

**DO NOT: Archive Implementation Details in MEMORY.md** — session entries are 3-5 lines max; code snippets, diffs, and agent logs belong in topic files, not MEMORY.md.

**DO NOT: Call TeamDelete Before PT Completion** — correct order: `TaskUpdate(PT, completed)` → agent shutdown → `TeamDelete`. Reversed order makes PT unreachable. (Incident: 2026-02-17)

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| verify-cc-feasibility | All-PASS verification report (4 stages) | L1 YAML: `all_pass: true`, per-stage verdicts |
| (User invocation) | Direct delivery request with optional commit message | `$ARGUMENTS` text: commit message or empty |
| self-implement | RSI cycle results ready for commit | L1 YAML: `status: complete`, `files_changed`, `commit_hash: ""` |

### Sends To
| Target | Data Produced | Trigger Condition |
|--------|---------------|-------------------|
| (Terminal) | Git commit + MEMORY.md archive | Always (pipeline terminal) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Verify FAIL outstanding | execution-code or execution-infra | Failed verify stage details |
| PT not found | task-management | Request to create/reconstruct PT |
| Git conflict | (User) | Conflicting file list for manual resolution |
| Agent exceeds maxTurns | Lead-direct or re-spawn delivery-agent | Partial completion status, remaining steps |
| User rejects commit | execution-code or execution-infra | User feedback on what to change |

> D17 Note: P2+ team mode — use 4-channel protocol (Ch1 PT, Ch2 `tasks/{team}/`, Ch3 micro-signal, Ch4 P2P).
> Micro-signal format: read `.claude/resources/output-micro-signal-format.md`

## Quality Gate
All conditions must be true for delivery to be considered successful:
- Verify domain all-PASS confirmed (no outstanding FAIL verdicts)
- All pipeline domain outputs consolidated into delivery manifest
- Commit message follows conventional commit format (type, scope, summary, body)
- Commit message body includes: key decisions, files changed count, architecture rationale
- Non-blocking warnings from verify domain included in commit message if present
- MEMORY.md updated with session learnings using Read-Merge-Write (not overwrite)
- Session entry in MEMORY.md is 3-5 lines maximum (no implementation details)
- PT status marked DELIVERED via TaskUpdate (only after commit succeeds)
- Git commit successful with specific file staging (no `git add -A`)
- User confirmation received before git commit via AskUserQuestion
- No sensitive files (.env, credentials, secrets) included in commit

## Fork Execution

Executed by `delivery-agent` (`subagent_type: delivery-agent`).

**Agent Properties**:
- `memory: none` — no conversation history access; all context must be in spawn prompt
- `model: haiku` — lightweight model sufficient for structured delivery tasks
- `maxTurns: 20` — budget for commit + MEMORY.md + PT update sequence
- `tools`: Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion
- `color: cyan` — visual identification in tmux

**Key Limitations**:
- No TaskCreate — can only update existing PT, not create new ones
- No sub-agent spawning — delivery-agent works alone
- Requires user confirmation for all external actions (git commit, MEMORY.md write)
- Cannot modify .claude/ infrastructure files (agents, skills, hooks, settings)

## Output
### L1
```yaml
domain: cross-cutting
skill: delivery-pipeline
status: delivered
commit_hash: ""
files_changed: 0
pt_status: DELIVERED
pt_signal: "metadata.phase_signals.p8_delivery"
signal_format: "{STATUS}|commit:{hash}|files:{N}|ref:tasks/{team}/p8-delivery.md"
```
### L2
- Delivery manifest (all domain outputs consolidated)
- Commit message with impact summary and conventional commit format
- MEMORY.md archive entries (session history, INFRA state updates if applicable)
- List of staged files with paths
- Any residual warnings from verify domain (non-blocking MEDIUM findings)
- PT task ID and final status confirmation

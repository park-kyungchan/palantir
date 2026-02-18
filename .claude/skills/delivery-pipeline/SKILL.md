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

**Note**: delivery-agent has `memory: none` — no access to conversation history. Lead MUST include verify verdict summary (all 4 stage PASS/FAIL status) in the delivery-agent spawn prompt. The all-PASS gate is effectively verified by Lead before spawning.

### 2. Consolidate Pipeline Results
Gather outputs from all pipeline domains:
- Pre-design: requirements and feasibility results
- Design: architecture decisions, interface contracts, risk assessment
- Research: codebase patterns, external dependency validation
- Plan: task breakdown, interface specs, implementation strategy
- Execution: file change manifests, review findings

### 3. Generate Commit Message
Build structured commit message from consolidation.

**Conventional Commit Format**:
```
type(scope): concise summary

Body: key decisions, architecture rationale
Files changed: N files across M domains

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Type Selection**:
- `feat` — new features, capabilities, or pipeline additions
- `fix` — bug fixes, defect corrections, broken behavior repair
- `refactor` — restructuring without behavior change (rename, reorganize, simplify)
- `docs` — documentation-only changes (MEMORY.md, README, design docs)
- `chore` — maintenance tasks (dependency updates, cleanup, config tweaks)
- `perf` — performance improvements (optimization, caching, reduced overhead)

**Scope Selection**: Use the primary domain name (e.g., `infra`, `execution`, `verify`) or project feature name (e.g., `ontology`, `src`, `hooks`). For cross-domain changes, use the most impactful domain.

**When `$ARGUMENTS` provides a commit message**: Use it as the commit title line. Expand the body from pipeline results (key decisions, file count, architecture rationale). Do not override the user-provided title.

**When no `$ARGUMENTS`**: Synthesize the title from the PT description and key architecture decisions made during the pipeline. The title should capture the "what" in under 72 characters.

### 4. Archive Session Learnings
Update MEMORY.md using the Read-Merge-Write pattern:

**Read**: delivery-agent reads current MEMORY.md content in full. This captures existing session history entries, topic file index, INFRA state table, and all other sections.

**Merge**: Construct the updated content by merging new information into existing structure:
- Add new session entry to Session History section (append, never overwrite prior entries)
- Update topic file index if new topic files were created during the pipeline
- Update INFRA State table if infrastructure components changed (version bumps, new agents/skills, settings modifications)
- Update Known Bugs table if new bugs discovered or existing bugs resolved

**Write**: Write the merged content back. Never overwrite without reading first — parallel sessions or manual edits may have modified MEMORY.md between pipeline start and delivery.

**Session Entry Format**:
```markdown
### {Feature Name} ({Date}, branch: {branch})
{1-3 line summary of what was accomplished and why}
- Key decisions: {architectural or design choices made}
- Files changed: N files
- Commit: {hash}
```

### 5. Execute Delivery
With user confirmation:
- Mark PT as DELIVERED via TaskUpdate
- Stage relevant files with git add
- Create git commit with structured message
- Cleanup session artifacts (team files, temporary outputs)

## Decision Points

### Commit Scope Decision
- **Full pipeline delivery**: All pipeline domains completed, verify all-PASS. Standard delivery: consolidate everything, single commit covering all changes.
- **Partial delivery**: User requests commit of completed work before full pipeline finishes (e.g., INFRA-only changes while code work continues). Stage only the relevant subset of files.
- **Multi-commit delivery**: COMPLEX tier with logically separable change sets (e.g., INFRA changes + source code changes). Split into 2 commits with clear boundaries for cleaner git history.

### MEMORY.md Archive Depth
- **Minimal archive**: TRIVIAL tier or routine changes. Add 2-3 line session summary to Session History.
- **Standard archive**: STANDARD tier. Session summary with key decisions, files changed, and any new patterns discovered.
- **Extended archive**: COMPLEX tier or pipelines that discovered new bugs, workarounds, or architectural insights. Full session entry plus updates to relevant topic files (e.g., agent-teams-bugs.md).

### Delivery-Agent Spawn DPS
Since delivery-agent has `memory: none`, Lead must provide ALL context in the spawn prompt. The agent has zero access to prior conversation history.

- **Context**:

  > **D11 Exception**: delivery-agent operates with `memory: none`. Unlike other skills where D11 context distribution filters noise, delivery-pipeline DPS must include ALL context. Rationale: terminal skill with user-confirmation gate — complete context prevents back-and-forth that delays delivery.

  INCLUDE: verify all-PASS summary (all 4 stage verdicts), pipeline tier classification, complete changed file list with paths, PT task ID, current branch name, key architecture decisions from the pipeline, commit message from `$ARGUMENTS` if provided, MEMORY.md current state summary for Read-Merge-Write.

  EXCLUDE: per-stage verify findings detail beyond PASS/FAIL verdict, rejected design alternatives, historical rationale for prior-phase decisions.
- **Task**: "Consolidate pipeline results. Generate commit message using conventional commit format. Update MEMORY.md using Read-Merge-Write pattern. Stage files with `git add [specific files]`. Create commit after user confirmation. Mark PT DELIVERED via TaskUpdate."
- **Constraints**: NO `git add -A` or `git add .`. Must use AskUserQuestion for confirmation before git commit. Must TaskUpdate PT only after commit succeeds (not before). Must use individual file staging. Never include sensitive files (.env, credentials, secrets).
- **Expected Output**: L1 YAML with `commit_hash`, `files_changed`, `pt_status`. L2 delivery summary with commit message, archive entries, and any warnings.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

#### Delivery-Agent Tier-Specific DPS Variations
**TRIVIAL**: Same agent. Context: minimal (1-2 files, simple commit). maxTurns: 10.
**STANDARD**: Same agent. Context: full consolidation (3-5 files, commit body with decisions). maxTurns: 15.
**COMPLEX**: Full DPS above. Context: extended multi-domain consolidation (6+ files). maxTurns: 20.

### Pre-Delivery Checklist
Before spawning delivery-agent, Lead must verify:

| Check | Method | Required |
|-------|--------|----------|
| Verify all-PASS | Read verify domain L1 output (all 4 stages) | Yes |
| PT exists | TaskGet [PERMANENT] — must have active PT | Yes |
| Branch is clean | `git status` via pipeline context | Recommended |
| No untracked sensitive files | Check for .env, credentials, secrets in changed files | Yes |
| Changed files are known | Pipeline file manifest from execution domain | Yes |
| No outstanding FAIL routes | Check no unresolved failure loops pending | Yes |

If any required check fails, do not spawn delivery-agent. Route to the appropriate fix domain first.

### Artifact Cleanup Scope
- **Conservative cleanup**: Remove only /tmp/ session artifacts and team communication files. Keep all design docs and plan files for reference.
- **Full cleanup**: Remove /tmp/ artifacts, team files, and intermediate plan/design files that are fully captured in the commit and MEMORY.md. Use when intermediate files would create noise in the working directory.

## Failure Handling

| Failure Type | Level | Action |
|---|---|---|
| Pre-commit hook failure (lint, format) | L0 Retry | Auto-fix via hook feedback, re-attempt commit |
| MEMORY.md archive format error | L1 Nudge | SendMessage with corrected archive format |
| delivery-agent exhausted turns or commit tool failure | L2 Respawn | Kill → fresh delivery-agent with refined DPS |
| PT metadata stale or verify status contradicted | L3 Restructure | Re-run verify stage before delivery |
| User rejects commit or strategic scope concern | L4 Escalate | AskUserQuestion with situation + options |

### Verify Domain Has Outstanding FAIL
- **Cause**: One or more of the 5 verify stages did not pass. Delivery was invoked prematurely.
- **Action**: Abort delivery immediately. Report which verify stages failed. Route back to Lead for fix loop (execution-code/execution-infra depending on failure type).

### PT Not Found or Missing Metadata
- **Cause**: PERMANENT Task was never created, was accidentally completed, or lacks critical metadata (tier, current_phase).
- **Action**: If PT exists but metadata is incomplete: reconstruct from pipeline outputs before proceeding. If PT does not exist: abort delivery and report to Lead -- cannot mark DELIVERED without a PT.

### Git Staging Conflict
- **Cause**: Files modified by pipeline have uncommitted changes from outside the pipeline, or merge conflicts exist on the branch.
- **Action**: Report conflicting files to Lead. Do not force-stage or auto-resolve. User must manually resolve conflicts before delivery can proceed.

### MEMORY.md Merge Conflict
- **Cause**: MEMORY.md was modified by another process or previous session between Read and Write.
- **Action**: Re-read MEMORY.md, merge changes manually (Read-Merge-Write pattern), then retry the update. Never overwrite without reading current state.

### Delivery-Agent Exceeds maxTurns
- **Cause**: Agent ran out of turns (maxTurns: 20) before completing all delivery steps (commit, MEMORY.md update, PT update). This can happen with large file manifests or complex MEMORY.md merges.
- **Action**: Check what completed by examining the agent's partial output. If git commit succeeded but MEMORY.md was not updated, Lead can update MEMORY.md directly (Lead-direct edit is acceptable for MEMORY.md since it is a project memory file, not a code artifact). If git commit did not happen, re-spawn delivery-agent with a focused prompt containing only the remaining steps and the same file list.

### User Rejects Commit
- **Cause**: User responds "no" when delivery-agent asks for commit confirmation via AskUserQuestion. This could indicate disagreement with commit scope, message, or desire to make additional changes.
- **Action**: Delivery-agent must exit gracefully without committing. No git operations, no PT status change. Lead should ask user what needs to change. If the issue is commit content, re-route to the appropriate execution domain skill (execution-code or execution-infra) for fixes, then re-invoke delivery-pipeline after the fix loop completes. If the issue is only the commit message, re-spawn delivery-agent with a corrected message.

## Anti-Patterns

### DO NOT: Use `git add -A` or `git add .`
Always stage specific files that were changed by the pipeline. Blanket staging risks committing unrelated changes, temporary files, or sensitive data that happened to be in the working directory.

### DO NOT: Skip MEMORY.md Update for "Small" Changes
Every pipeline delivery archives learnings, regardless of size. Even TRIVIAL pipelines may reveal patterns (e.g., a file that's frequently modified, a recurring issue). The archive is cumulative -- small entries compound into valuable institutional knowledge.

### DO NOT: Complete PT Before Git Commit Succeeds
PT status must only be marked DELIVERED after the git commit is confirmed successful. If you mark PT DELIVERED and then the commit fails, the task system shows completion but the work is not persisted.

### DO NOT: Deliver Without User Confirmation
The delivery-agent requires explicit user confirmation before executing `git commit`. Never auto-commit, even for TRIVIAL tiers. The user is the final gatekeeper for what enters the repository.

### DO NOT: Include Raw Agent Output in Commit Messages
Commit messages should be human-readable summaries, not copy-pasted L1/L2 output from agents. Synthesize the key decisions and changes into a clean, conventional commit format.

### DO NOT: Deliver Partial Pipeline Results Without User Awareness
If the verify domain had warnings (non-blocking MEDIUM findings that did not prevent PASS), include them in the commit message body as a "Known Issues" or "Residual Warnings" section. The user should know about residual issues even if they are non-blocking. Hiding warnings behind a PASS verdict erodes trust in the delivery process.

### DO NOT: Archive Implementation Details in MEMORY.md
MEMORY.md captures session-level summaries, not implementation details. Do not include code snippets, full file diffs, agent conversation logs, or step-by-step execution traces. Keep session entries to 3-5 lines maximum. Detailed implementation notes belong in topic files (e.g., `memory/infrastructure-history.md`) linked from the topic file index, not in the session entry itself.

### DO NOT: Call TeamDelete Before PT Completion
TeamDelete removes the entire `~/.claude/tasks/{team-name}/` directory, including PT task files. If PT has not been marked completed before TeamDelete, the PT becomes unreachable ("Task not found"). **Correct order**: `TaskUpdate(PT, status: completed)` → agent shutdown → `TeamDelete`. **Incident**: 2026-02-17 Meta-Cognition pipeline — PT #1 lost due to reversed ordering.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| verify-cc-feasibility | All-PASS verification report (4 stages) | L1 YAML: `all_pass: true`, per-stage verdicts |
| (User invocation) | Direct delivery request with optional commit message | `$ARGUMENTS` text: commit message or empty |
| self-implement | RSI cycle results ready for commit | L1 YAML: `status: complete`, `files_changed`, `commit_hash: ""` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (Terminal) | Git commit + MEMORY.md archive | Always (delivery is pipeline terminal) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Verify FAIL outstanding | execution-code or execution-infra | Failed verify stage details |
| PT not found | task-management | Request to create/reconstruct PT |
| Git conflict | (User) | Conflicting file list for manual resolution |
| Agent exceeds maxTurns | Lead-direct or re-spawn delivery-agent | Partial completion status, remaining steps |
| User rejects commit | execution-code or execution-infra | User feedback on what to change |

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
- Git commit successful with specific file staging (no git add -A)
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

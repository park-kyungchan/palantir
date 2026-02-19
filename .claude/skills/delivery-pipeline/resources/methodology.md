# Delivery Pipeline — Detailed Methodology

> On-demand reference. Contains commit message templates, MEMORY.md archive procedure,
> DPS INCLUDE/EXCLUDE blocks, tier-specific DPS variations, and failure sub-case detail.

## Commit Message Format Details

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

## MEMORY.md Archive Procedure (Read-Merge-Write)

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

## Delivery-Agent Spawn DPS — INCLUDE/EXCLUDE

**D11 Exception**: delivery-agent operates with `memory: none`. Unlike other skills where D11 context distribution filters noise, delivery-pipeline DPS must include ALL context. Rationale: terminal skill with user-confirmation gate — complete context prevents back-and-forth that delays delivery.

**INCLUDE**: verify all-PASS summary (all 4 stage verdicts), pipeline tier classification, complete changed file list with paths, PT task ID, current branch name, key architecture decisions from the pipeline, commit message from `$ARGUMENTS` if provided, MEMORY.md current state summary for Read-Merge-Write.

**EXCLUDE**: per-stage verify findings detail beyond PASS/FAIL verdict, rejected design alternatives, historical rationale for prior-phase decisions.

**Task**: "Consolidate pipeline results. Generate commit message using conventional commit format. Update MEMORY.md using Read-Merge-Write pattern. Stage files with `git add [specific files]`. Create commit after user confirmation. Mark PT DELIVERED via TaskUpdate."

**Constraints**: NO `git add -A` or `git add .`. Must use AskUserQuestion for confirmation before git commit. Must TaskUpdate PT only after commit succeeds (not before). Must use individual file staging. Never include sensitive files (.env, credentials, secrets).

**Expected Output**: L1 YAML with `commit_hash`, `files_changed`, `pt_status`. L2 delivery summary with commit message, archive entries, and any warnings.

## Tier-Specific DPS Variations

| Tier | Context | maxTurns |
|------|---------|----------|
| TRIVIAL | Minimal (1-2 files, simple commit) | 10 |
| STANDARD | Full consolidation (3-5 files, commit body with decisions) | 15 |
| COMPLEX | Extended multi-domain consolidation (6+ files) | 20 |

## Failure Sub-Cases (Verbose Detail)

### Verify Domain Has Outstanding FAIL
- **Cause**: One or more of the 5 verify stages did not pass. Delivery was invoked prematurely.
- **Action**: Abort delivery immediately. Report which verify stages failed. Route back to Lead for fix loop (execution-code/execution-infra depending on failure type).

### PT Not Found or Missing Metadata
- **Cause**: PERMANENT Task was never created, was accidentally completed, or lacks critical metadata (tier, current_phase).
- **Action**: If PT exists but metadata is incomplete: reconstruct from pipeline outputs before proceeding. If PT does not exist: abort delivery and report to Lead — cannot mark DELIVERED without a PT.

### Git Staging Conflict
- **Cause**: Files modified by pipeline have uncommitted changes from outside the pipeline, or merge conflicts exist on the branch.
- **Action**: Report conflicting files to Lead. Do not force-stage or auto-resolve. User must manually resolve conflicts before delivery can proceed.

### MEMORY.md Merge Conflict
- **Cause**: MEMORY.md was modified by another process or previous session between Read and Write.
- **Action**: Re-read MEMORY.md, merge changes manually (Read-Merge-Write pattern), then retry the update. Never overwrite without reading current state.

### Delivery-Agent Exceeds maxTurns
- **Cause**: Agent ran out of turns before completing all delivery steps (commit, MEMORY.md update, PT update). Can happen with large file manifests or complex MEMORY.md merges.
- **Action**: Check what completed by examining the agent's partial output. If git commit succeeded but MEMORY.md was not updated, Lead can update MEMORY.md directly (Lead-direct edit is acceptable for MEMORY.md since it is a project memory file, not a code artifact). If git commit did not happen, re-spawn delivery-agent with a focused prompt containing only the remaining steps and the same file list.

### User Rejects Commit
- **Cause**: User responds "no" when delivery-agent asks for commit confirmation via AskUserQuestion. This could indicate disagreement with commit scope, message, or desire to make additional changes.
- **Action**: Delivery-agent must exit gracefully without committing. No git operations, no PT status change. Lead should ask user what needs to change. If the issue is commit content, re-route to execution-code or execution-infra for fixes, then re-invoke delivery-pipeline after the fix loop completes. If the issue is only the commit message, re-spawn delivery-agent with a corrected message.

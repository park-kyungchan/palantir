---
name: delivery-pipeline
description: "Phase 9 delivery — consolidates pipeline results, creates git commits, archives session artifacts, and updates MEMORY.md. Lead-only terminal phase. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[feature name or session-id]"
---

# Delivery Pipeline

Phase 9 (Delivery) orchestrator. Lead-only terminal phase — no teammates spawned.
Consolidates pipeline output, commits to git, archives session artifacts, and migrates
durable lessons to MEMORY.md.

**Announce at start:** "I'm using delivery-pipeline to orchestrate Phase 9 (Delivery) for this feature."

**Core flow:** PT Check (Lead) → 9.1 Input Discovery → 9.2 Consolidation → 9.3 Delivery → 9.4 Cleanup → Terminal Summary

## When to Use

```
Have Phase 7 or 8 output (verification complete)?
├── Working in Agent Teams mode? ─── no ──→ Commit manually
├── yes
├── PT or GC shows Phase 7/8 COMPLETE? ── no ──→ Run /verification-pipeline first
├── yes
├── Gate 7 (or 8) APPROVED? ── no ──→ Resolve gate issues first
├── yes
└── Use /delivery-pipeline
```

**Why terminal?** Phase 9 is the final pipeline step. There is no Phase 10. After delivery,
the pipeline is complete and the feature is shipped.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Gate Records (Phase 7/8):**
!`ls -t /home/palantir/.agent/teams/*/phase-{7,8}/gate-record.yaml 2>/dev/null | head -10`

**Existing Archives:**
!`ls /home/palantir/.agent/teams/*/ARCHIVE.md 2>/dev/null || echo "No archives yet"`

**Implementation Plans:**
!`ls /home/palantir/docs/plans/*-pipeline.md /home/palantir/docs/plans/*-plan.md 2>/dev/null || true`

**Git Status:**
!`cd /home/palantir && git status --short 2>/dev/null | head -20`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Pipeline Session Directories:**
!`ls -d /home/palantir/.agent/teams/*/ 2>/dev/null | while read d; do echo "$(basename "$d"): $(ls "$d"/phase-*/gate-record.yaml 2>/dev/null | wc -l) gates"; done`

**Feature Input:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

```
TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to 9.1    │     │
          ▼     ▼
        /permanent-tasks    Continue to 9.1
        creates PT-v1       without PT
        → then 9.1
```

If a PERMANENT Task exists, its content (user intent, codebase impact map, prior decisions)
provides essential context for consolidation and archival. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 9.1.

---

## Phase 9.1: Input Discovery + Validation

No teammates spawned. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find completed pipeline output. Multi-session is the
standard case — each pipeline skill creates a separate session directory.

**Discovery algorithm:**

1. Scan ALL `.agent/teams/*/phase-{7,8}/gate-record.yaml` for `result: APPROVED`
2. If `$ARGUMENTS` provides a feature name, filter directories matching `{feature}*`
3. If `$ARGUMENTS` provides a specific session-id or path, use that directly
4. If PT exists, cross-reference PT content for session references not captured by prefix
   matching (handles renamed features where session directories have different prefixes)
5. If multiple unrelated candidates found, present options via `AskUserQuestion`
6. If no candidates, check PT for Phase 7/8 status (PT is cross-session)
7. If still not found, inform user: "No completed pipeline found. Run /verification-pipeline first."

**Present findings to user:** After discovery, show all identified session directories and
ask user to confirm the set before proceeding. Do not silently auto-discover — the user
must see and approve which sessions are included.

**Cross-session artifact collection:** Once confirmed, collect ALL related session directories.
Read gate records from each to build a complete phase history for ARCHIVE.md.

### Validation

| # | Check | On Failure |
|---|-------|------------|
| V-1 | PT exists with Phase 7 (or 8) COMPLETE — OR — GC exists with equivalent status | Abort: "No completed pipeline found" |
| V-2 | Gate 7 (or 8) record exists with APPROVED in some session directory | Abort: "Final gate not approved" |
| V-3 | Implementation plan exists in `docs/plans/` | Warn: "Plan not found — commit will lack plan reference" |
| V-4 | Git working tree has changes to commit | Warn: "No changes detected — skip to Phase 9.4?" |

V-3 and V-4 are warnings, not aborts — Phase 9 may still create ARCHIVE.md and update
MEMORY.md even without code changes.

Use `sequential-thinking` to evaluate validation results. On all checks PASS → proceed to Consolidation.

---

## Phase 9.2: Consolidation

Three sequential operations. All Lead-only.

Use `sequential-thinking` for all decisions in this phase.

### Op-1: Final PT Update

If a PERMANENT Task exists:

1. Read current PT via TaskGet
2. Add final metrics to the PT description:
   - Files created/modified count
   - Test pass rate (from Phase 7 gate record)
   - Phase completion dates (from gate records across sessions)
3. Mark all phases COMPLETE in Phase Status section
4. Bump version to PT-v{final}
5. Update subject to: `[PERMANENT] {feature} — DELIVERED`

If no PT exists, skip to Op-2 (GC-only pipeline — legacy support).

### Op-2: PT → MEMORY.md Migration

Migrate durable lessons from the pipeline to persistent memory.

1. Read current MEMORY.md (`~/.claude/projects/-home-palantir/memory/MEMORY.md`)
2. Read PT content (or GC + TEAM-MEMORY.md if no PT)
3. Use `sequential-thinking` to extract durable content:

   **Keep:** Architecture decisions, key constraints, bug discoveries, user preferences,
   patterns learned, infrastructure state changes, deferred work items

   **Discard:** Transient phase status, session-specific paths, teammate assignments,
   intermediate gate records, approach iteration details

4. Draft merged MEMORY.md using Read-Merge-Write:
   - Deduplicate entries with existing MEMORY.md content
   - Resolve contradictions (newer information wins)
   - Elevate abstraction (specific session details → general patterns)
5. Present diff summary to user for review
6. **USER CONFIRMATION REQUIRED** — wait for approval before writing
7. On approval: write merged MEMORY.md
8. On rejection: skip (MEMORY.md unchanged)

### Op-3: ARCHIVE.md Creation

Generate a complete pipeline record from all available sources.

1. Read PT (or GC) for feature summary and decisions
2. Read gate records from ALL related session directories
3. Read TEAM-MEMORY.md files (if they exist) for lessons learned
4. Read orchestration-plan.md files for team composition
5. Generate ARCHIVE.md using the template (see ARCHIVE.md Template section below)
6. Write to `.agent/teams/{primary-session-id}/ARCHIVE.md`
   - Use the most recent session directory (verification/execution) as primary
   - If single session, use that directory

---

## Phase 9.3: Delivery

Two user-confirmed operations. Lead-only.

Use `sequential-thinking` for commit message generation and PR body drafting.

### Op-4: Git Commit

1. Run `git status` and `git diff --name-only` to inventory changes
2. Identify files to stage — exclude `.env*`, `*credentials*`, `*secrets*` per CLAUDE.md §8
3. Generate commit message using Conventional Commits:

   ```
   {type}({scope}): {description}

   {body — key changes, metrics, architecture reference}

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```

4. Present to user: staged files list + proposed commit message
5. **USER CONFIRMATION REQUIRED** — wait for approval

**On approval:** Stage specific files and commit. Never use `git add -A`.

**On modification request:** User can:
- Add or remove files from the staging list
- Edit the commit message
- Re-present updated staging + message for fresh confirmation
- Loop until user approves or skips

**On rejection (skip commit):** Check if MEMORY.md was modified in Op-2.
If yes, present two choices:
1. **Keep changes** — MEMORY.md stays modified on disk (available for a future commit)
2. **Revert MEMORY.md** — restore original from git (`git checkout -- {path}`)

### Op-5: PR Creation (Optional)

1. Ask user: "Create a pull request for this commit?"
2. **USER CONFIRMATION REQUIRED**
3. If yes:
   - Generate PR title from commit message
   - Generate PR body from ARCHIVE.md summary section
   - Use `gh pr create --title "..." --body "..."`
   - Report PR URL to user
4. If no: skip

---

## Phase 9.4: Cleanup

Two operations. Lead-only.

### Op-6: Session Artifact Cleanup

1. Inventory ALL related `.agent/teams/{session-id}/` directories
2. Classify files in each:

   **Preserve:** L1/L2/L3 directories, ARCHIVE.md, gate-record.yaml files,
   orchestration-plan.md, TEAM-MEMORY.md, global-context.md

   **Delete candidates:** `pre-compact-tasks-*.json`, `tool-failures.log`,
   `compact-events.log`, `teammate-lifecycle.log`, temporary debug files

3. Present cleanup plan to user showing preserve vs delete lists
4. **USER CONFIRMATION REQUIRED**
5. On approval: delete transient files
6. On rejection: keep all files

### Op-7: Task List Cleanup

1. Read task list via TaskList
2. Mark any remaining open tasks as completed (if work is done)
3. PT subject already updated to "DELIVERED" in Op-1
4. No user confirmation needed — task state is internal

---

## Terminal Summary

Present to user after all operations complete:

```markdown
## Pipeline Delivery Complete

**Feature:** {name}
**Duration:** Phase 1 → Phase 9
**Phases:** {completed count}/9 COMPLETE

**Deliverables:**
- Commit: {hash} on {branch} (or "skipped")
- PR: {URL or "not created"}
- Archive: .agent/teams/{session-id}/ARCHIVE.md
- Memory: Updated with {N} new entries (or "unchanged")

**Metrics:**
- Files created: {N}
- Files modified: {N}
- Tests: {pass}/{total}
- Implementers used: {N}
- Gate iterations: {N}

**Pipeline Complete.** No next phase — this is the terminal step.
```

No "Next:" section. No auto-chaining. The pipeline is finished.

---

## ARCHIVE.md Template

Use this template when generating ARCHIVE.md in Op-3:

```markdown
# Pipeline Archive — {Feature Name}

**Date:** {start} → {end}
**Complexity:** {SIMPLE|MEDIUM|COMPLEX}
**Pipeline:** Phases {list} completed

## Gate Record Summary

| Phase | Gate | Result | Date | Iterations |
|-------|------|--------|------|------------|
| 1 | G1 | {result} | {date} | {N} |
| 2 | G2 | {result} | {date} | {N} |
| ... | ... | ... | ... | ... |

## Key Decisions

| # | Decision | Phase | Rationale |
|---|----------|-------|-----------|
| D-1 | {decision} | P{N} | {rationale} |

## Implementation Metrics

- Tasks: {completed}/{total}
- Files created: {N} — {list}
- Files modified: {N} — {list}
- Implementers: {N}
- Test results: {pass}/{total} ({rate}%)
- Review iterations: spec {N}, code {N}

## Deviations from Plan

{Any noted deviations from Phase 4 plan, or "None"}

## Lessons Learned

{Extracted from TEAM-MEMORY.md and Lead observations}

## Team Composition

| Role | Agent | Tasks | Key Contribution |
|------|-------|-------|------------------|
| researcher-1 | ... | ... | ... |
| architect-1 | ... | ... | ... |
| ... | ... | ... | ... |
```

---

## Cross-Cutting Requirements

### Sequential Thinking

Lead uses `mcp__sequential-thinking__sequentialthinking` for all analysis, judgment, and
decision-making throughout the pipeline.

| Phase | When |
|-------|------|
| 9.1 Discovery | Validation evaluation, session identification, candidate filtering |
| 9.2 Consolidation | PT→MEMORY extraction criteria, ARCHIVE.md content synthesis |
| 9.3 Delivery | Commit message generation, staged file selection, PR body drafting |
| 9.4 Cleanup | Preserve/delete classification, artifact importance assessment |

### Error Handling

| Situation | Response |
|-----------|----------|
| No Phase 7/8 output found | Inform user, suggest /verification-pipeline |
| PT and GC both missing | Warn user, attempt discovery from gate records alone |
| Git working tree clean | Warn, offer to skip to Phase 9.4 (ARCHIVE + cleanup only) |
| Commit rejected by user | Offer modification or skip, handle MEMORY.md state |
| PR creation fails | Report error, provide manual `gh pr create` command |
| MEMORY.md merge conflict | Present both versions, let user choose |
| Session directory not found | Fall back to PT for cross-session references |
| User cancellation | Preserve all artifacts created so far, report partial completion |

### Compact Recovery

If Lead's session compacts during Phase 9:

1. Read the most recent ARCHIVE.md (if Op-3 already ran)
2. Read task list for PT status
3. Check git log for recent commits (if Op-4 already ran)
4. Resume from the last incomplete operation

Phase 9 is Lead-only with no teammates, so recovery is simpler than multi-agent phases.

---

## Key Principles

- **User confirms everything external** — git, PR, MEMORY.md, cleanup all need explicit approval
- **Consolidation before delivery** — knowledge persistence (9.1) precedes git operations (9.2)
- **Multi-session by default** — scan across all related session directories, not just one
- **Present, don't assume** — show discovered sessions and let user confirm the set
- **Sequential thinking always** — structured reasoning at every decision point
- **Terminal phase** — no auto-chaining, no "Next:" section, pipeline ends here
- **Preserve artifacts** — L1/L2/L3 and ARCHIVE.md survive cleanup
- **Read-Merge-Write for MEMORY** — reuse /permanent-tasks pattern for PT→MEMORY migration
- **Conventional Commits** — follow established git message format
- **PT cross-reference** — use PERMANENT Task to discover sessions that prefix matching misses

## Never

- Auto-commit without user confirmation
- Force push or skip git hooks
- Include secrets or credentials in commits (CLAUDE.md §8)
- Use `git add -A` or `git add .` (stage specific files only)
- Add a "Next:" section to the terminal summary
- Spawn teammates (Phase 9 is Lead-only)
- Auto-chain to another skill after termination
- Delete L1/L2/L3 directories or ARCHIVE.md during cleanup
- Write MEMORY.md without user preview and approval
- Silently auto-discover sessions without user confirmation

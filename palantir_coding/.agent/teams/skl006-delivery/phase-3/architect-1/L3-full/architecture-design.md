# Architecture Design — SKL-006 Delivery Pipeline + RSIL Catalog

**Architect:** architect-1
**Date:** 2026-02-08
**Phase:** 3 (Architecture)
**Consumers:** Phase 4 architect (detailed design), Phase 5 devils-advocate (validation), Lead (scope decisions)

---

## 1. Architecture Decisions

### AD-1: SKL-006 Phase Structure — 3 Sub-Phases

**Decision:** Structure Phase 9 as three sub-phases: 9.1 (Consolidation), 9.2 (Delivery), 9.3 (Cleanup).

**Rationale:** Phase 9 has three distinct operation clusters with natural ordering:
- 9.1 = knowledge consolidation (PT final update, PT→MEMORY migration, ARCHIVE.md) — must happen before git
- 9.2 = external delivery (git stage, commit, optional PR) — must happen with user confirmation
- 9.3 = session cleanup (artifact archival, task list, team files) — must happen last

**Alternatives Considered:**
- Option A: 6 flat operations (Op-1 through Op-6 from research). Rejected — too granular, creates unnecessary Lead decision points. All 6 operations have a natural 3-cluster grouping.
- Option B: 2 sub-phases (delivery + cleanup). Rejected — conflates knowledge persistence with git operations. MEMORY.md update must precede commit (the commit message may reference decisions from the archive).

### AD-2: Git Operation Safety — User-Confirmed, Never Auto-Commit

**Decision:** All git operations require explicit user confirmation. Present a preview (staged files + proposed commit message) and wait for approval.

**Rationale:** CLAUDE.md §8 states "Never force push main. Never skip hooks. No secrets in commits." Phase 9 interacts with git — the most externally-visible part of the pipeline. Auto-commit would violate the spirit of careful external-facing actions. The existing codebase uses Conventional Commits (`type(scope): description`), which the skill should generate but let the user approve.

**Alternatives Considered:**
- Auto-commit with opt-out. Rejected — violates CLAUDE.md §8 safety philosophy. A bad commit is harder to fix than a confirmation dialog.
- Multi-commit strategy (one per phase). Rejected — over-engineers the common case. Single commit with comprehensive message is the established pattern (see `git log` in research).

### AD-3: ARCHIVE.md Location — Session Directory

**Decision:** `ARCHIVE.md` lives at `.agent/teams/{session-id}/ARCHIVE.md`, not in `docs/`.

**Rationale:** The archive is a pipeline execution record — session-scoped, not project-permanent. MEMORY.md captures the durable lessons; ARCHIVE.md captures the full process. Session directory is the right scope because:
1. Multiple pipelines may run for the same project — each produces its own archive
2. The archive references session-specific paths (L1/L2/L3 directories)
3. CLAUDE.md §10 says "Archive to MEMORY.md + ARCHIVE.md" — MEMORY.md is cross-session, ARCHIVE.md is per-session

**Template:** Defined in §3 below.

### AD-4: PT→MEMORY Migration — Selective Read-Merge-Write

**Decision:** Extract durable content from PT into MEMORY.md using the same Read-Merge-Write pattern as `/permanent-tasks`, with explicit keep/discard criteria.

**Rationale:** The `/permanent-tasks` skill already defines Read-Merge-Write consolidation rules (deduplicate, resolve contradictions, elevate abstraction). Reusing this pattern for MEMORY.md migration maintains consistency. The key difference: PT→MEMORY is a one-way extraction (PT is not modified), not bidirectional sync.

**Keep criteria:** Architecture decisions, key constraints, bug discoveries, user preferences, patterns learned
**Discard criteria:** Transient phase status, session-specific paths, teammate assignments, intermediate gate records

### AD-5: Session Cleanup Scope — Preserve Artifacts, Clean Transients

**Decision:** Preserve L1/L2/L3 directories, ARCHIVE.md, gate-record.yaml files, orchestration-plan.md. Delete pre-compact snapshots, tool-failure logs, compact-events, teammate-lifecycle logs.

**Rationale:** Artifacts have downstream value (future pipeline can reference past designs). Transient files (snapshots, logs) are debugging aids with no cross-session value. The 29+ pre-compact snapshot files identified by R-2 are a concrete waste to clean up.

**User confirmation:** Yes — present the cleanup plan before executing. Users may want to keep specific transient files for debugging.

### AD-6: RSIL Sprint Scope — 5 In-Sprint, 8 Deferred

**Decision:** Include items that directly enable SKL-006, are quick wins (<30 min), or fix correctness issues. Defer large-scope items.

**In-sprint items (5):**
| ID | Item | Rationale |
|----|------|-----------|
| IMP-002 | Hook NLP: on-session-compact.sh | Quick win, ~10 lines, correctness (legacy markers) |
| IMP-003 | Hook NLP: on-subagent-start.sh | Quick win, ~5 lines, correctness (legacy marker) |
| IMP-004 | ARCHIVE.md dead reference fix | Directly required by SKL-006 (ARCHIVE.md now defined) |
| H-1 | Agent MEMORY.md templates | Already deferred from previous sprint, low effort (~6 files × 10 lines) |
| IMP-010 | Pre-compact snapshot cleanup in SKL-006 | Directly required by Phase 9.3 cleanup operation |

**Deferred items (8):**
| ID | Item | Reason for Deferral |
|----|------|---------------------|
| IMP-001 | task-api-guideline.md NLP | Large scope (530→200L), already flagged as separate terminal work |
| IMP-005 | Skill DRY extraction (Phase 0, etc.) | Large scope (~191 lines across 5 files), high coordination |
| IMP-006 | GC→PT full migration | Architectural change affecting all 5 pipeline skills |
| H-2 | Skills preload in agent frontmatter | Requires content creation for preloaded skills |
| H-3 | Hooks in agent/skill frontmatter | Large migration (8 hooks → distributed), coordination-heavy |
| H-4 | Prompt/agent hooks | Requires testing new hook types, risk of breaking existing flow |
| H-6 | Effort parameter strategy | Not configurable in Claude Code CLI (API-level only per R-1 gap) |
| H-7 | Task(agent_type) restrictions | Touches all 6 agent files, needs careful testing |

**Also deferred (low priority / not actionable):**
| ID | Item | Reason |
|----|------|--------|
| H-5 | delegate mode | Documentation only, no functional change |
| M-2 | Async hooks | Minor optimization |
| M-3 | statusLine | Nice-to-have visibility enhancement |
| M-5 | maxTurns tuning | Requires empirical data to optimize |
| M-8 | PermissionRequest hooks | Broad permission concern |
| IMP-007 | researcher Write tool mismatch | System overrides .md frontmatter, cosmetic |
| IMP-008 | Skill common patterns extraction | Subset of IMP-005 |
| IMP-009 | §11 DIA trim | Part of IMP-001 |
| IMP-011 | API keys in settings | Security, but env var migration is a separate concern |
| IMP-012 | maxTurns documentation | Low priority |
| IMP-013 | Hook jq preamble | Low priority |

### AD-7: Skill DRY Extraction Approach — Defer, Reference Pattern Ready

**Decision:** Do NOT extract shared patterns to a reference file in this sprint. Instead, design SKL-006 with the same repeated patterns (Phase 0, Clean Termination, etc.) for consistency. When extraction eventually happens, SKL-006 will be part of it.

**Rationale:** DRY extraction across 6 skills is a high-coordination task affecting 6 files simultaneously. Doing it alongside a new skill creation risks destabilizing working skills. The real benefit (maintenance, not token savings — 7.5% reduction is modest) argues for a dedicated sprint. For now, SKL-006 matches the established skill pattern exactly.

### AD-8: GC→PT Migration — Future Sprint, Not Blocking

**Decision:** SKL-006 handles both GC-based and PT-based input discovery. Full GC→PT migration is a separate, larger initiative.

**Rationale:** The brainstorming-pipeline still creates GC as primary artifact. All downstream skills reference GC versions. Changing this fundamental flow while shipping SKL-006 creates too much blast radius. SKL-006 should work with what exists: check for PT (preferred) and GC (fallback). This maintains backward compatibility while being ready for the eventual PT-only world.

---

## 2. SKL-006 Architecture — Delivery Pipeline

### 2.1 Skill Identity

```yaml
name: delivery-pipeline
description: "Phase 9 delivery — consolidates pipeline results, creates git commits,
  archives session artifacts, and updates MEMORY.md. Lead-only terminal phase.
  Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to Phase 7/8 output]"
```

### 2.2 Core Flow

```
PT Check (Lead) → Input Discovery → Phase 9.1 Consolidation → Phase 9.2 Delivery → Phase 9.3 Cleanup → Terminal Summary
```

No teammates spawned. No TeamCreate/TeamDelete. No understanding verification. Lead executes all operations directly.

### 2.3 Phase 0: PERMANENT Task Check

Identical to other skills. Follows established Phase 0 pattern.

### 2.4 Phase 9.1: Input Discovery + Validation

**Multi-session is the standard case.** Each pipeline skill creates a separate session directory:
- brainstorming: `.agent/teams/{feature}/` → P1-3
- write-plan: `.agent/teams/{feature}-write-plan/` → P4
- validation: `.agent/teams/{feature}-validation/` → P5
- execution: `.agent/teams/{feature}-execution/` → P6
- verification: `.agent/teams/{feature}-verification/` → P7-8

Phase 9 must aggregate across ALL related directories.

**Discovery algorithm:**
1. Scan ALL `.agent/teams/*/phase-{7,8}/gate-record.yaml` for `result: APPROVED`
2. If `$ARGUMENTS` provides a feature name, filter directories matching `{feature}*`
3. If `$ARGUMENTS` provides a specific session-id or path, use that directly
4. If multiple unrelated candidates found, present options via `AskUserQuestion`
5. If no candidates, check the PERMANENT Task for Phase 7/8 status (PT is cross-session)
6. If still not found, inform user

**Cross-session artifact collection:** Once the feature is identified, collect ALL related session directories by matching the feature name prefix. Read gate records from each to build a complete phase history for ARCHIVE.md.

**Validation Table:**

| # | Check | On Failure |
|---|-------|------------|
| V-1 | PT exists with Phase 7 (or 8) COMPLETE — OR — GC exists with equivalent status across any session dir | Abort: "No completed pipeline found" |
| V-2 | Gate 7 (or 8) record exists with APPROVED in some session directory | Abort: "Final gate not approved" |
| V-3 | Implementation plan exists in docs/plans/ | Warn: "Plan not found — commit will lack plan reference" |
| V-4 | Git working tree has changes to commit | Warn: "No changes detected — skip to Phase 9.3?" |

V-3 and V-4 are warnings, not aborts — Phase 9 may still create ARCHIVE.md and update MEMORY.md even without code changes.

**Post-commit rejection recovery (AD-2 supplement):** If the user rejects the commit in Op-4 after MEMORY.md was already written in Op-2, ask: "MEMORY.md was updated with pipeline lessons. Keep these updates, or revert?" This gives the user clean control over the inconsistency.

### 2.5 Phase 9.1: Consolidation

Three sequential operations:

#### Op-1: Final PT Update
- Read current PT via TaskGet
- Add final metrics (files created/modified, test pass rate, phase completion dates)
- Mark all phases COMPLETE in Phase Status
- Bump version to PT-v{final}
- This is the last PT version — mark as "[PERMANENT] {feature} — DELIVERED"

#### Op-2: PT → MEMORY.md Migration
- Read current MEMORY.md (`~/.claude/projects/-home-palantir/memory/MEMORY.md`)
- Read current PT content
- Use sequential-thinking to extract durable content:
  - Keep: Feature summary, architecture decisions, key constraints, bug discoveries, patterns learned
  - Discard: Phase status, session paths, teammate assignments, intermediate states
- Write merged MEMORY.md using Read-Merge-Write (deduplicate, resolve, elevate)
- Present diff summary to user for review before writing

#### Op-3: ARCHIVE.md Creation
- Generate from PT + gate records (across ALL related session directories) + TEAM-MEMORY.md files + orchestration-plan.md files
- Write to `.agent/teams/{primary-session-id}/ARCHIVE.md` (use the verification/execution session as primary, or the first session if single)
- Template (see §3 below)

### 2.6 Phase 9.2: Delivery

Two user-confirmed operations:

#### Op-4: Git Commit
1. Run `git status` and `git diff --name-only` to inventory changes
2. Identify files to stage (exclude .env, secrets per CLAUDE.md §8)
3. Generate commit message using Conventional Commits pattern:
   ```
   {type}({scope}): {description}

   {body with key changes, metrics}

   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
4. Present to user: staged files list + proposed commit message
5. Wait for user confirmation
6. On approval: `git add {specific files} && git commit`
7. On rejection: user edits or skips

#### Op-5: PR Creation (Optional)
1. Ask user: "Create a pull request?"
2. If yes: generate PR title and body from ARCHIVE.md summary
3. Use `gh pr create` with structured body
4. If no: skip

### 2.7 Phase 9.3: Cleanup

Two user-confirmed operations:

#### Op-6: Session Artifact Cleanup
1. Inventory `.agent/teams/{session-id}/` contents
2. Classify files:
   - **Preserve:** L1/L2/L3 directories, ARCHIVE.md, gate-record.yaml, orchestration-plan.md, TEAM-MEMORY.md
   - **Delete candidates:** pre-compact-tasks-*.json, tool-failures.log, compact-events.log, teammate-lifecycle.log
3. Present cleanup plan to user
4. On approval: delete transient files
5. On rejection: keep all

#### Op-7: Task List Cleanup
1. List all tasks via TaskList
2. Mark completed tasks as completed (if not already)
3. Update PT subject to indicate delivery: "[PERMANENT] {feature} — DELIVERED"

### 2.8 Terminal Summary

```markdown
## Pipeline Delivery Complete

**Feature:** {name}
**Duration:** Phase 1 → Phase 9
**Phases:** {completed count}/9 COMPLETE

**Deliverables:**
- Commit: {hash} on {branch}
- PR: {URL or "not created"}
- Archive: .agent/teams/{session-id}/ARCHIVE.md
- Memory: Updated with {N} new entries

**Metrics:**
- Files created: {N}
- Files modified: {N}
- Tests: {pass}/{total}
- Implementers used: {N}
- Gate iterations: {N}

**Pipeline Complete.** No next phase — this is the terminal step.
```

No "Next:" section — Phase 9 is terminal.

---

## 3. ARCHIVE.md Template

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

## 4. RSIL In-Sprint Implementation Architecture

### 4.1 IMP-002: on-session-compact.sh NLP Conversion

**Current:** Uses `[DIA-RECOVERY]`, `[DIRECTIVE]+[INJECTION]`, `[STATUS] CONTEXT_RECEIVED`
**Target:** Natural language equivalents
**Change:** Replace protocol markers in the `additionalContext` output strings with plain instructions:
- `[DIA-RECOVERY]` → "Your session was compacted."
- `[DIRECTIVE]+[INJECTION]` → "Read your files to restore context:"
- `[STATUS] CONTEXT_RECEIVED` → remove (not needed in compact recovery)

**Impact:** 1 file, ~10 lines changed. No functional change — only string content in hook output.
**Backward compatibility:** Full — hook behavior unchanged.
**Layer 2 forward compatibility:** N/A — hook is Layer 1 infrastructure.

### 4.2 IMP-003: on-subagent-start.sh NLP Conversion

**Current:** Uses `[DIA-HOOK]` prefix in log messages
**Target:** Remove prefix, use natural log message
**Change:** Replace `[DIA-HOOK]` in echo/logging strings with descriptive natural text.

**Impact:** 1 file, ~5 lines changed. No functional change.
**Backward compatibility:** Full.
**Layer 2 forward compatibility:** N/A.

### 4.3 IMP-004: ARCHIVE.md Dead Reference Fix

**Current:** CLAUDE.md §10 line 155 says "Archive to MEMORY.md + ARCHIVE.md at work end" — ARCHIVE.md is undefined.
**Target:** Now that SKL-006 defines ARCHIVE.md template and creation process, the reference is no longer dead. No change needed to CLAUDE.md — the reference becomes valid when SKL-006 is implemented.

**Impact:** 0 files changed. Resolution is the existence of SKL-006 itself.
**Note:** If we want to add a brief clarification to CLAUDE.md, we could add "(created by /delivery-pipeline)" after the ARCHIVE.md reference, but this is optional.

### 4.4 H-1: Agent MEMORY.md Templates

**Scope:** Create initial MEMORY.md files at `~/.claude/agent-memory/{role}/MEMORY.md` for roles that don't have one yet.

**Status check needed:** architect already has MEMORY.md (111 lines). Need to check which others exist.

**Template per agent:**
```markdown
# {Role} Agent Memory

## Patterns Learned
{empty — populated through work}

## Common Mistakes to Avoid
{empty — populated through work}

## Effective Strategies
{empty — populated through work}
```

**Impact:** Up to 5 new files (6 roles minus architect which exists). ~10 lines each.
**Backward compatibility:** Full — memory files are additive.
**Layer 2 forward compatibility:** HIGH — agents build domain knowledge across sessions.

### 4.5 IMP-010: Pre-compact Snapshot Cleanup in SKL-006

**Architecture:** This is built into SKL-006 Phase 9.3 (Op-6). No separate implementation needed — it's part of the skill design itself. The cleanup logic identifies `pre-compact-tasks-*.json` files as delete candidates.

**Impact:** Integrated into SKL-006. No separate file changes.

---

## 5. Component Interaction Diagram

```
User
  │
  ▼
/delivery-pipeline ($ARGUMENTS)
  │
  ├─ Phase 0: PT Check (TaskList → TaskGet)
  │
  ├─ Phase 9.1: Input Discovery
  │   ├─ Find gate records (.agent/teams/*/phase-{7,8}/)
  │   ├─ Validate entry conditions
  │   └─ Load PT + GC + orchestration-plan
  │
  ├─ Phase 9.1: Consolidation
  │   ├─ Op-1: Final PT Update (TaskUpdate)
  │   ├─ Op-2: PT→MEMORY.md (Read → merge → Write)
  │   └─ Op-3: ARCHIVE.md (Read PT + gates → Write)
  │
  ├─ Phase 9.2: Delivery
  │   ├─ Op-4: Git Commit (git status → stage → commit)
  │   │   └─ USER CONFIRMATION REQUIRED
  │   └─ Op-5: PR (optional, gh pr create)
  │       └─ USER CONFIRMATION REQUIRED
  │
  ├─ Phase 9.3: Cleanup
  │   ├─ Op-6: Artifact cleanup (.agent/teams/ transients)
  │   │   └─ USER CONFIRMATION REQUIRED
  │   └─ Op-7: Task list cleanup (mark delivered)
  │
  └─ Terminal Summary (no "Next" phase)
```

**Key property:** No teammates spawned anywhere. Lead executes all operations directly.
**User interaction points:** 4 — MEMORY.md review, git commit, PR decision, cleanup scope.

---

## 6. Risk Matrix

| # | Risk | Probability | Impact | Score | Mitigation |
|---|------|-------------|--------|-------|------------|
| R-1 | MEMORY.md corruption during merge | LOW | HIGH | 6 | Read-Merge-Write with user preview. Git provides recovery. |
| R-2 | Accidental secret in commit | LOW | CRITICAL | 8 | Explicit exclude list in staging. CLAUDE.md §8 rules apply. |
| R-3 | Session cleanup deletes needed files | LOW | MEDIUM | 4 | User confirmation before any deletion. Classify preserve/delete explicitly. |
| R-4 | PT not found (pipeline ran without PT) | MEDIUM | LOW | 3 | Fallback to GC-based discovery. Warn user but don't abort. |
| R-5 | Multiple pipeline sessions — wrong one selected | LOW | MEDIUM | 4 | Present candidates via AskUserQuestion. User selects explicitly. |
| R-6 | ARCHIVE.md too large (many phases, many decisions) | LOW | LOW | 2 | Template is structured. Truncate team composition for large teams. |

No CRITICAL unmitigated risks. All risks have structural mitigations.

---

## 7. Layer 2 Forward-Compatibility Assessment

### SKL-006 Readiness
- **Phase pipeline structure:** Phase 9 is domain-agnostic. Works for any feature type.
- **ARCHIVE.md template:** Generic — "Feature Name", "Key Decisions", "Metrics". No domain-specific fields.
- **MEMORY.md migration:** Extracts patterns, decisions, constraints — works for Ontology Framework sessions.
- **Git operations:** Domain-agnostic. Conventional Commits pattern works for any project.
- **Cleanup:** Session-scoped file cleanup is domain-agnostic.

### RSIL Items Readiness
- **H-1 Agent memory:** HIGH forward-compatibility. Ontology sessions will benefit from persistent agent knowledge.
- **IMP-002/003 Hook NLP:** N/A — infrastructure-only, no domain impact.

### Potential Layer 2 Extensions (future)
- ARCHIVE.md could include Ontology-specific sections (ObjectTypes defined, LinkTypes, etc.)
- PT→MEMORY migration could include domain-specific extraction rules
- These would be additive, not requiring changes to the base SKL-006 design.

---

## 8. Interface Specifications

### 8.1 SKL-006 Input Interface

**From previous phase (Phase 7 or 8):**
- `.agent/teams/{session-id}/phase-{7,8}/gate-record.yaml` with `result: APPROVED`
- PT-v{final} (via TaskGet) OR GC-v{final} (via file read)
- `docs/plans/{implementation-plan}.md` (optional but expected)
- `.agent/teams/{session-id}/orchestration-plan.md`
- `.agent/teams/{session-id}/TEAM-MEMORY.md` (if exists)

**Dynamic Context (auto-injected):**
- Git status and recent changes
- Existing plans in docs/plans/
- Infrastructure version
- Pipeline session directories

### 8.2 SKL-006 Output Interface

**Artifacts created:**
- `.agent/teams/{session-id}/ARCHIVE.md` — full pipeline record
- Updated `~/.claude/projects/-home-palantir/memory/MEMORY.md` — durable lessons
- Git commit (on user approval)
- PR (on user request)

**PT modification:**
- PT-v{final} with all phases COMPLETE and "[PERMANENT] {feature} — DELIVERED" subject

**Cleanup effects:**
- Transient files in `.agent/teams/{session-id}/` deleted (on user approval)

### 8.3 Existing Skills — No Interface Changes

SKL-006 is purely additive. It consumes output from existing skills but doesn't modify their contracts:
- verification-pipeline Clean Termination already outputs "Next: Phase 9 (Delivery)"
- SKL-006 discovers this output via file system (gate records, GC)
- No changes to any existing skill's output format

---

## 9. Implementation Task Breakdown (Phase 4 Input)

### Task Group A: SKL-006 SKILL.md Creation (Primary)
- T-A1: Create `.claude/skills/delivery-pipeline/SKILL.md` — full skill file
  - Frontmatter, When to Use, Dynamic Context, Phase 0, Phases 9.1-9.3, Terminal Summary
  - Cross-Cutting (seq-thinking, error handling, compact recovery)
  - Key Principles, Never list
  - Estimated: ~350-400 lines (matching verification-pipeline scale)
- **Files:** 1 new file
- **Dependencies:** None (can start immediately)

### Task Group B: RSIL Quick Wins (Parallel with A)
- T-B1: on-session-compact.sh NLP conversion (~10 lines changed)
- T-B2: on-subagent-start.sh NLP conversion (~5 lines changed)
- T-B3: Agent MEMORY.md templates (up to 5 new files)
- **Files:** 2 modified, up to 5 new
- **Dependencies:** None (independent of SKL-006)

### Task Group C: Integration (After A+B)
- T-C1: Verify ARCHIVE.md reference in CLAUDE.md §10 is resolved by SKL-006 existence
- T-C2: End-to-end consistency check — SKL-006 reads from verification-pipeline output format
- **Files:** 0-1 modified (optional CLAUDE.md clarification)
- **Dependencies:** T-A1, T-B1, T-B2

### Estimated Total
- 1 new skill file (~350-400 lines)
- 2 modified hooks (~15 lines changed)
- Up to 5 new MEMORY.md template files (~50 lines total)
- 0-1 modified CLAUDE.md (optional)

---

## 10. Phase 4 Entry Requirements

For Phase 4 (Detailed Design) to proceed, the architect needs:
1. This architecture document approved (Gate 3)
2. User decision on RSIL scope (AD-6 confirmed or modified)
3. Confirmation of ARCHIVE.md template (AD-3)
4. Confirmation of cleanup scope (AD-5)

### Items Requiring User Input
1. **ARCHIVE.md location:** Session directory confirmed? (AD-3 recommends `.agent/teams/{session-id}/`)
2. **RSIL sprint scope:** 5 in-sprint items confirmed? (AD-6)
3. **PR default:** Always offer PR creation, or only when on a non-main branch?
4. **Multi-session awareness:** Should Phase 9 search for artifacts across multiple `.agent/teams/` directories? (Current design: single session discovery. Multi-session would add complexity.)

# SKL-006 Delivery Pipeline + RSIL — Implementation Plan

> **For Lead:** Phase 4 detailed design. Translates Phase 3 architecture into actionable tasks.
> Orchestrate using CLAUDE.md v6.0 Phase Pipeline protocol.

**Goal:** Create SKL-006 (Phase 9 Delivery Pipeline) + RSIL items (hook reduction 8→3, hook NLP, agent MEMORY.md templates).

**Architecture Source:** `.agent/teams/skl006-delivery/phase-3/architect-1/L3-full/architecture-design.md` (approved)

**Pipeline:** Full Agent Teams Phase 6 → Phase 7-8 → Phase 9.

---

## 1. Orchestration Overview

### Pipeline Structure

```
Phase 6: Implementation   — 2 parallel implementers
Phase 7: Verification     — Structural validation by Lead
Phase 9: Delivery         — Lead commits
```

### Teammate Allocation

| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
| Implementer A | 1 | `implementer` | SKL-006 SKILL.md (new file) | Phase 6 |
| Implementer B | 1 | `implementer` | Hook files + settings.json + agent .md frontmatter + agent MEMORY.md | Phase 6 |

**WHY two implementers:** The two workstreams are fully independent:
- Workstream A creates a new file from scratch (SKL-006 SKILL.md) — no cross-references to Workstream B
- Workstream B modifies existing infrastructure files (hooks, settings, agent .md, MEMORY templates) — no dependency on SKL-006 content
- Zero file overlap between workstreams = safe parallelism
- Combined scope (~550 lines new + ~250 lines changed) exceeds single-implementer comfort zone

### Task Summary

| # | Task | Owner | Dependencies |
|---|------|-------|-------------|
| T-1 | Create SKL-006 SKILL.md | Impl-A | None |
| T-2 | Hook reduction (8→3): delete 5 hooks + update settings.json | Impl-B | None |
| T-3 | Hook NLP: on-session-compact.sh + on-subagent-start.sh | Impl-B | None |
| T-4 | NL-MIGRATE: move L1/L2 check + idle logic to agent .md frontmatter | Impl-B | T-2 |
| T-5 | Agent MEMORY.md templates (tester, integrator) | Impl-B | None |
| T-6 | Cross-workstream validation | Lead | T-1, T-2, T-3, T-4, T-5 |

---

## 2. Architecture Summary

### SKL-006: 3 Sub-Phases

From Phase 3 AD-1: Phase 9 structured as 9.1 (Consolidation), 9.2 (Delivery), 9.3 (Cleanup).

- **9.1 Consolidation:** Final PT update, PT→MEMORY.md migration (Read-Merge-Write), ARCHIVE.md creation
- **9.2 Delivery:** Git commit (user-confirmed), optional PR (user-confirmed)
- **9.3 Cleanup:** Session artifact cleanup (user-confirmed), task list cleanup

Key properties:
- Lead-only, no teammates spawned, terminal phase (no "Next:")
- 4 user confirmation points
- Multi-session discovery (cross-session default)
- ARCHIVE.md in session directory
- Post-rejection recovery for MEMORY.md

### RSIL Items (NL-First Framework)

Per AD-15 (NL-First Boundary): reduce hooks 8→3, maximize NL instructions.

**In-Sprint (7 items):**
| ID | Item | Category |
|----|------|----------|
| HOOK-REDUCE | Remove 5 hooks from settings.json | A (Hook) |
| HOOK-DELETE | Delete 5 .sh files | A (Hook) |
| IMP-002 | on-session-compact.sh NLP | A (Hook) |
| IMP-003 | on-subagent-start.sh NLP | A (Hook) |
| NL-MIGRATE | L1/L2 check + idle → agent .md NL | B (NL) |
| H-1 | Agent MEMORY.md templates (tester, integrator) | B (NL) |
| IMP-004 | ARCHIVE.md reference resolved by SKL-006 existence | N/A (no change) |

**Deferred (all re-evaluate items):**
| ID | Item | Reason |
|----|------|--------|
| IMP-001 | task-api-guideline.md NLP (530→~200L) | Massive scope, user-confirmed separate work |
| H-2 | Skills preload in agent frontmatter | Requires content creation + testing per agent |
| H-6 | Effort parameter strategy | Not configurable in CC CLI (API-level only) |
| H-7 | Task(agent_type) restrictions | Touches all 6 agent files, needs careful testing |
| IMP-011 | API key security | Separate security concern |

### Feasibility Re-evaluation Details

**IMP-001 (task-api-guideline.md NLP):** Technically feasible but ~530 lines → ~200 lines is a full rewrite. The MEMORY.md already flags this as "separate terminal work." DEFER — risk of destabilizing DIA protocol mid-sprint.

**H-2 (Skills preload in frontmatter):** Technically feasible (CC supports `allowedMcpServers` and similar frontmatter). But requires creating meaningful preloaded content for each of 6 agents. Low ROI for this sprint. DEFER.

**H-6 (Effort parameter):** R-1 confirmed this is API-level only (`max_tokens`, thinking budget). CC CLI does not expose per-agent effort parameter configuration. DEFER — not actionable.

**H-7 (Task agent_type restrictions):** Feasible via `disallowedTools` pattern. But touches all 6 agent files and requires careful testing of each restriction set. Not urgent — current disallowedTools already prevents mutations. DEFER.

**IMP-011 (API key security):** Feasible (move from settings.json to env vars). But this is a security migration separate from the delivery pipeline concern. DEFER.

---

## 3. File Ownership Assignment

### Implementer A (SKL-006)

| File | Operation | Est. Lines |
|------|-----------|-----------|
| `.claude/skills/delivery-pipeline/SKILL.md` | CREATE | ~380 |

### Implementer B (RSIL Infrastructure)

| File | Operation | Est. Lines Changed |
|------|-----------|-------------------|
| `.claude/settings.json` | MODIFY (remove 5 hook entries) | ~50 lines removed |
| `.claude/hooks/on-subagent-stop.sh` | DELETE | -53 lines |
| `.claude/hooks/on-teammate-idle.sh` | DELETE | -52 lines |
| `.claude/hooks/on-task-completed.sh` | DELETE | -57 lines |
| `.claude/hooks/on-task-update.sh` | DELETE | -36 lines |
| `.claude/hooks/on-tool-failure.sh` | DELETE | -35 lines |
| `.claude/hooks/on-session-compact.sh` | MODIFY (NLP strings) | ~5 lines changed |
| `.claude/hooks/on-subagent-start.sh` | MODIFY (NLP strings) | ~5 lines changed |
| `.claude/agents/implementer.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agents/integrator.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agents/architect.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agents/tester.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agents/researcher.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agents/devils-advocate.md` | MODIFY (add NL L1/L2 reminder) | ~3 lines added |
| `.claude/agent-memory/tester/MEMORY.md` | CREATE | ~15 lines |
| `.claude/agent-memory/integrator/MEMORY.md` | CREATE | ~15 lines |

### Shared (Read-Only Reference)

| File | Reader |
|------|--------|
| `.claude/CLAUDE.md` | Both (reference for style/protocol) |
| `.claude/skills/verification-pipeline/SKILL.md` | Impl-A (pattern reference) |
| `.claude/skills/brainstorming-pipeline/SKILL.md` | Impl-A (Phase 0 pattern) |
| Architecture design (Phase 3 L3) | Both (design source) |

---

## 4. TaskCreate Definitions

### Task T-1: Create SKL-006 SKILL.md

```
subject: "Create delivery-pipeline SKILL.md (Phase 9)"

description: |
  ## Objective
  Create `.claude/skills/delivery-pipeline/SKILL.md` — the complete Phase 9 delivery
  pipeline skill. This is a NEW file creation.

  ## Acceptance Criteria
  AC-0: Read the Phase 3 architecture design and verification-pipeline SKILL.md for
        patterns before writing any code.
  AC-1: YAML frontmatter matches established skill pattern (name, description, argument-hint)
  AC-2: "When to Use" decision tree present
  AC-3: Dynamic Context section with shell injection commands present
  AC-4: Phase 0 (PT Check) follows established pattern from verification-pipeline
  AC-5: Phase 9.1 (Consolidation) implements Op-1 (PT update), Op-2 (PT→MEMORY),
        Op-3 (ARCHIVE.md) as specified in architecture §2.5
  AC-6: Phase 9.2 (Delivery) implements Op-4 (git commit) and Op-5 (PR) with
        user confirmations as specified in architecture §2.6
  AC-7: Phase 9.3 (Cleanup) implements Op-6 (artifact cleanup) and Op-7 (task cleanup)
        as specified in architecture §2.7
  AC-8: Terminal Summary with no "Next:" section
  AC-9: Cross-Cutting Requirements section (sequential-thinking, error handling, compact recovery)
  AC-10: Key Principles and Never list present
  AC-11: ARCHIVE.md template embedded in skill (from architecture §3)
  AC-12: Multi-session discovery algorithm (from architecture §2.4)
  AC-13: Post-rejection recovery for MEMORY.md (from architecture §2.4)
  AC-14: NLP v6.0 native — zero protocol markers
  AC-15: Estimated ~350-400 lines

  ## Dependencies
  blockedBy: []
  blocks: [T-6]

  ## Reference Files
  - Architecture: .agent/teams/skl006-delivery/phase-3/architect-1/L3-full/architecture-design.md
  - Pattern: .claude/skills/verification-pipeline/SKILL.md
  - Phase 0 pattern: .claude/skills/brainstorming-pipeline/SKILL.md

activeForm: "Creating delivery-pipeline SKILL.md"
```

### Task T-2: Hook Reduction (8→3)

```
subject: "Remove 5 hooks from settings.json and delete 5 hook .sh files"

description: |
  ## Objective
  Reduce hooks from 8 to 3 per NL-First Framework (AD-15). Remove 5 hooks that are
  being migrated to NL instructions or deferred to Layer 2.

  ## Acceptance Criteria
  AC-0: Read current settings.json and all 5 target .sh files before making changes.
  AC-1: settings.json retains ONLY these 3 hook sections:
        - SubagentStart (on-subagent-start.sh)
        - PreCompact (on-pre-compact.sh)
        - SessionStart[compact] (on-session-compact.sh)
  AC-2: These 5 hook sections removed from settings.json:
        - SubagentStop (on-subagent-stop.sh)
        - PostToolUse[TaskUpdate] (on-task-update.sh)
        - TeammateIdle (on-teammate-idle.sh)
        - TaskCompleted (on-task-completed.sh)
        - PostToolUseFailure (on-tool-failure.sh)
  AC-3: These 5 .sh files deleted:
        - .claude/hooks/on-subagent-stop.sh
        - .claude/hooks/on-teammate-idle.sh
        - .claude/hooks/on-task-completed.sh
        - .claude/hooks/on-task-update.sh
        - .claude/hooks/on-tool-failure.sh
  AC-4: settings.json remains valid JSON after edits
  AC-5: The 3 remaining .sh files are untouched by this task (T-3 handles their NLP)

  ## Dependencies
  blockedBy: []
  blocks: [T-4, T-6]

  ## Key Context
  The 5 hooks being removed served these purposes:
  - on-subagent-stop: L1/L2 check on teammate stop → migrating to NL in agent .md (T-4)
  - on-teammate-idle: L1/L2 check on idle → migrating to NL in agent .md (T-4)
  - on-task-completed: L1/L2 check on task complete → migrating to NL in agent .md (T-4)
  - on-task-update: Task lifecycle logging → defer to Layer 2 audit
  - on-tool-failure: Tool failure logging → defer to Layer 2 audit

activeForm: "Removing 5 hooks from settings.json and deleting .sh files"
```

### Task T-3: Hook NLP Conversion

```
subject: "Convert protocol markers in on-session-compact.sh and on-subagent-start.sh to NL"

description: |
  ## Objective
  Replace legacy protocol markers in the 2 remaining modifiable hooks with natural
  language equivalents (IMP-002, IMP-003).

  ## Acceptance Criteria
  AC-0: Read both .sh files before modifying.
  AC-1: on-session-compact.sh: Replace protocol markers in additionalContext strings:
        - "[DIA-RECOVERY]" → "Your session was compacted."
        - "[DIRECTIVE]+[INJECTION]" → "Read your files to restore context:"
        - "[STATUS] CONTEXT_RECEIVED" → removed (not needed in compact recovery)
        - Full replacement described in §5 below.
  AC-2: on-subagent-start.sh: Replace "[DIA-HOOK]" prefix with natural text:
        - "[DIA-HOOK] Active team:" → "Active team:"
        - Full replacement described in §5 below.
  AC-3: No functional/behavioral changes — only string content in output.
  AC-4: Both hooks still exit 0 and produce valid JSON output.
  AC-5: jq fallback path in on-session-compact.sh also updated.

  ## Dependencies
  blockedBy: []
  blocks: [T-6]

activeForm: "Converting hook protocol markers to natural language"
```

### Task T-4: NL-MIGRATE — L1/L2 + Idle Logic to Agent Frontmatter

```
subject: "Add NL L1/L2 save reminders to all 6 agent .md files"

description: |
  ## Objective
  The 3 deleted hooks (on-subagent-stop, on-teammate-idle, on-task-completed) enforced
  L1/L2 file creation via exit-code blocking. With NL-First, this enforcement moves to
  natural language instructions in each agent's .md file.

  ## Acceptance Criteria
  AC-0: Read all 6 agent .md files before modifying.
  AC-1: Each of the 6 agent .md files has the NL L1/L2 reminder added to its
        Constraints section (exact text in §5 below).
  AC-2: The reminder is role-appropriate — same core message, adapted wording per role.
  AC-3: No other changes to agent .md files beyond adding this reminder.
  AC-4: devils-advocate.md gets a read-only variant (reminder to write L1/L2 despite
        being read-only for source code).

  ## Dependencies
  blockedBy: [T-2] (hooks must be removed first to avoid duplicate enforcement)
  blocks: [T-6]

  ## Key Context
  The 3 hooks that enforced L1/L2 creation:
  - on-subagent-stop: checked L1/L2 on stop, logged WARNING if missing
  - on-teammate-idle: blocked idle with exit 2 if L1/L2 missing (<50B L1, <100B L2)
  - on-task-completed: blocked task completion with exit 2 if L1/L2 missing
  NL replacement: natural instruction in each agent's Constraints section.

activeForm: "Adding NL L1/L2 reminders to agent definitions"
```

### Task T-5: Agent MEMORY.md Templates

```
subject: "Create MEMORY.md templates for tester and integrator agents"

description: |
  ## Objective
  Create initial MEMORY.md files for the 2 agent roles that don't have one yet:
  tester and integrator. Existing files (architect, researcher, devils-advocate,
  implementer) are NOT touched.

  ## Acceptance Criteria
  AC-0: Verify which agent-memory directories exist before creating files.
  AC-1: ~/.claude/agent-memory/tester/MEMORY.md created with template (see §5)
  AC-2: ~/.claude/agent-memory/integrator/MEMORY.md created with template (see §5)
  AC-3: Template follows established pattern from existing agent MEMORY.md files
  AC-4: Each file ~15 lines with role-appropriate section headers
  AC-5: Existing MEMORY.md files NOT modified

  ## Dependencies
  blockedBy: []
  blocks: [T-6]

activeForm: "Creating agent MEMORY.md templates"
```

### Task T-6: Cross-Workstream Validation

```
subject: "Validate consistency across all modified/created files"

description: |
  ## Objective
  Lead-only validation task. Verify cross-workstream consistency after both
  implementers complete their work.

  ## Acceptance Criteria
  AC-1: settings.json is valid JSON with exactly 3 hook entries
  AC-2: Only 3 .sh files remain in .claude/hooks/
  AC-3: SKL-006 SKILL.md follows NLP v6.0 (zero protocol markers)
  AC-4: SKL-006 references correct input/output paths from architecture
  AC-5: All 6 agent .md files have NL L1/L2 reminder in Constraints
  AC-6: ARCHIVE.md reference in CLAUDE.md §10 line 155 is now resolvable
        (SKL-006 defines ARCHIVE.md creation)
  AC-7: 2 new MEMORY.md templates exist at correct paths
  AC-8: on-session-compact.sh and on-subagent-start.sh have zero protocol markers
  AC-9: All modified files have consistent style with existing codebase

  ## Dependencies
  blockedBy: [T-1, T-2, T-3, T-4, T-5]
  blocks: []

activeForm: "Validating cross-workstream consistency"
```

---

## 5. Change Specifications

### CS-1: `.claude/skills/delivery-pipeline/SKILL.md` (CREATE) — VL-3

**New file.** Complete content specification follows. Implementer A should use
`verification-pipeline/SKILL.md` (522 lines) as the structural template and
`brainstorming-pipeline/SKILL.md` for the Phase 0 pattern.

**Frontmatter:**
```yaml
---
name: delivery-pipeline
description: "Phase 9 delivery — consolidates pipeline results, creates git commits,
  archives session artifacts, and updates MEMORY.md. Lead-only terminal phase.
  Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[feature name or session-id]"
---
```

**Structure (sections in order):**

1. **Title + Intro** (~5 lines): "Phase 9 (Delivery) orchestrator. Lead-only terminal phase."
2. **When to Use** (~15 lines): Decision tree checking Phase 7/8 completion, Agent Teams mode.
3. **Dynamic Context** (~25 lines): Auto-injected shell commands:
   - `!`ls -d .agent/teams/*/phase-{7,8}/gate-record.yaml 2>/dev/null``
   - `!`ls .agent/teams/*/ARCHIVE.md 2>/dev/null || echo "No archives yet"``
   - `!`ls docs/plans/*-pipeline.md docs/plans/*-plan.md 2>/dev/null || true``
   - `!`cd /home/palantir && git status --short 2>/dev/null | head -20``
   - `!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null``
   - `$ARGUMENTS`
4. **Phase 0: PT Check** (~25 lines): Identical pattern to verification-pipeline Phase 0.
5. **Phase 9.1: Input Discovery + Validation** (~40 lines):
   - Multi-session discovery algorithm from architecture §2.4
   - Validation table (V-1 through V-4)
   - Feature identification via `$ARGUMENTS` or gate record scan
6. **Phase 9.1: Consolidation** (~60 lines):
   - Op-1: Final PT Update (mark all phases COMPLETE, bump version, mark DELIVERED)
   - Op-2: PT→MEMORY.md (Read-Merge-Write with keep/discard criteria, user preview)
   - Op-3: ARCHIVE.md (template embedded, cross-session gate record aggregation)
7. **Phase 9.2: Delivery** (~40 lines):
   - Op-4: Git Commit (git status, staged file list, Conventional Commits message, user confirmation)
   - Op-5: PR Creation (optional, gh pr create, user confirmation)
   - Post-rejection recovery (if user rejects commit after MEMORY.md was written)
8. **Phase 9.3: Cleanup** (~30 lines):
   - Op-6: Artifact cleanup (preserve/delete classification, user confirmation)
   - Op-7: Task list cleanup (mark delivered)
9. **Terminal Summary** (~20 lines): Template with metrics, no "Next:" section.
10. **ARCHIVE.md Template** (~40 lines): From architecture §3.
11. **Cross-Cutting Requirements** (~30 lines): Sequential thinking table, error handling table, compact recovery.
12. **Key Principles** (~15 lines): From architecture design.
13. **Never** (~10 lines): Terminal phase prohibitions.

**Estimated total: ~355-400 lines.**

### CS-2: `.claude/settings.json` (MODIFY) — VL-2

**Current state:** 133 lines, 8 hook sections in the `hooks` object.

**Change:** Remove 5 hook entries from the `hooks` object, keeping only:
- `SubagentStart` (lines 21-33)
- `PreCompact` (lines 60-72)
- `SessionStart` (lines 73-86)

**Remove these 5 entries:**
- `SubagentStop` (lines 34-46) — L1/L2 check → NL
- `PostToolUse[TaskUpdate]` (lines 47-59) — logging → Layer 2
- `TeammateIdle` (lines 87-99) — L1/L2 check → NL
- `TaskCompleted` (lines 100-112) — L1/L2 check → NL
- `PostToolUseFailure` (lines 113-125) — logging → Layer 2

**Result:** `hooks` object contains exactly 3 entries. All other settings.json content unchanged.

**Verification:** Parse with `jq .` to confirm valid JSON.

### CS-3: Delete 5 Hook .sh Files — VL-1

**Files to delete (Bash `rm`):**
```
.claude/hooks/on-subagent-stop.sh    (53 lines)
.claude/hooks/on-teammate-idle.sh    (52 lines)
.claude/hooks/on-task-completed.sh   (57 lines)
.claude/hooks/on-task-update.sh      (36 lines)
.claude/hooks/on-tool-failure.sh     (35 lines)
```

**Remaining files (3):**
```
.claude/hooks/on-subagent-start.sh   (67 lines, modified by CS-5)
.claude/hooks/on-pre-compact.sh      (43 lines, unchanged)
.claude/hooks/on-session-compact.sh  (25 lines, modified by CS-4)
```

### CS-4: `.claude/hooks/on-session-compact.sh` (MODIFY) — VL-1

**Current line 10:**
```bash
echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — DIA re-injection required" >> "$LOG_DIR/compact-events.log"
```
**New line 10:**
```bash
echo "[$TIMESTAMP] SESSION_COMPACT | Context compacted — re-injection required" >> "$LOG_DIR/compact-events.log"
```

**Current line 17 (jq path additionalContext):**
```
"additionalContext": "[DIA-RECOVERY] Context was compacted. As Lead: 1) Read orchestration-plan.md 2) Read Shared Task List 3) Send [DIRECTIVE]+[INJECTION] with latest GC to each active teammate 4) Wait for [STATUS] CONTEXT_RECEIVED before proceeding."
```
**New line 17:**
```
"additionalContext": "Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."
```

**Current line 22 (fallback path additionalContext):**
```
echo '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"[DIA-RECOVERY] Context was compacted. As Lead: 1) Read orchestration-plan.md 2) Read Shared Task List 3) Send [DIRECTIVE]+[INJECTION] with latest GC to each active teammate 4) Wait for [STATUS] CONTEXT_RECEIVED before proceeding."}}'
```
**New line 22:**
```
echo '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"Your session was compacted. As Lead: 1) Read orchestration-plan.md 2) Read task list (including PERMANENT Task) 3) Send fresh context to each active teammate with the latest PT version 4) Teammates should read their L1/L2/L3 files to restore progress."}}'
```

**Also update comment on line 3:**
```bash
# DIA Enforcement: Lead must re-inject context to all active teammates
```
→
```bash
# Recovery: Lead must re-inject context to all active teammates
```

### CS-5: `.claude/hooks/on-subagent-start.sh` (MODIFY) — VL-1

**Current line 35 (GC legacy path additionalContext):**
```
"additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
```
**New line 35:**
```
"additionalContext": ("Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
```

**Current line 46 (PT path additionalContext):**
```
"additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Context is managed via PERMANENT Task. Use TaskGet on task with subject containing [PERMANENT] for full project context.")
```
**New line 46:**
```
"additionalContext": ("Active team: " + $team + ". Context is managed via PERMANENT Task. Use TaskGet on task with subject containing [PERMANENT] for full project context.")
```

**Current line 58 (no-team fallback additionalContext):**
```
"additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
```
**New line 58:**
```
"additionalContext": ("Active team: " + $team + ". Current GC: " + $ver + ". Verify your injected context version matches.")
```

**Also update comment on line 2:**
```bash
# Hook: SubagentStart — Logging + context injection (PT-first, GC legacy fallback)
```
→ (no change needed — comment is already natural language)

### CS-6: Agent .md NL L1/L2 Reminder — All 6 Files (MODIFY) — VL-2

Add the following line to each agent's **Constraints** section (at the end):

**For implementer.md (line 80, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**For integrator.md (line 81, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**For architect.md (line 74, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**For tester.md (line 77, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**For researcher.md (line 63, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**For devils-advocate.md (line 73, end of Constraints):**
```markdown
- Write L1/L2/L3 files proactively throughout your work — they are your only recovery mechanism if your session compacts. Do not wait until the end.
```

**Note:** agent-common-protocol.md already has this guidance in "Saving Your Work" (lines 57-64). The agent .md addition reinforces it at the Constraints level where agents check before acting.

### CS-7: `.claude/agent-memory/tester/MEMORY.md` (CREATE) — VL-1

```markdown
# Tester Agent Memory

## Patterns Learned
(Populated through work — record effective test strategies, failure analysis techniques)

## Common Mistakes to Avoid
(Populated through work — record pitfalls encountered during testing)

## Effective Strategies
(Populated through work — record what worked well for test design and execution)
```

### CS-8: `.claude/agent-memory/integrator/MEMORY.md` (CREATE) — VL-1

```markdown
# Integrator Agent Memory

## Patterns Learned
(Populated through work — record effective merge strategies, conflict resolution patterns)

## Common Mistakes to Avoid
(Populated through work — record pitfalls encountered during integration)

## Effective Strategies
(Populated through work — record what worked well for cross-boundary merges)
```

---

## 6. Interface Contracts

### IC-1: SKL-006 Input Interface

**From verification-pipeline (Phase 7/8):**
- `.agent/teams/{session-id}/phase-{7,8}/gate-record.yaml` with `result: APPROVED`
- PERMANENT Task (via TaskGet) OR Global Context (via file read)
- `docs/plans/{implementation-plan}.md` (optional but expected)
- `.agent/teams/{session-id}/orchestration-plan.md`
- `.agent/teams/{session-id}/TEAM-MEMORY.md` (if exists)

**Contract:** SKL-006 does NOT modify verification-pipeline output format. It discovers and consumes existing artifacts. No changes to upstream skills.

### IC-2: SKL-006 Output Interface

**Artifacts created:**
- `.agent/teams/{session-id}/ARCHIVE.md`
- Updated `~/.claude/projects/-home-palantir/memory/MEMORY.md`
- Git commit (on user approval)
- PR (on user request)

**Contract:** Terminal phase — no downstream consumer. Output is for the user and future sessions.

### IC-3: Hook Reduction — NL Migration Contract

**Before (mechanical enforcement):**
- on-subagent-stop: logs L1/L2 existence check, WARNING on missing
- on-teammate-idle: exit 2 blocks idle if L1/L2 missing (L1 <50B, L2 <100B)
- on-task-completed: exit 2 blocks completion if L1/L2 missing

**After (NL enforcement):**
- Agent .md Constraints section: "Write L1/L2/L3 files proactively..."
- agent-common-protocol.md "Saving Your Work" section: already exists (lines 57-64)
- CLAUDE.md §10 Integrity Principles: already says "Save work to L1/L2/L3 files proactively"

**Contract change:** Enforcement moves from blocking (hook exit 2) to guidance (NL instruction). The trade-off is accepted per AD-15 (NL-First): Opus 4.6's instruction following is strong enough for non-critical enforcement. The 3 remaining hooks handle truly critical paths (spawn context, pre-compact state, post-compact recovery).

### IC-4: Settings.json Hook Structure

**Before:** 8 hook entries (SubagentStart, SubagentStop, PostToolUse, PreCompact, SessionStart, TeammateIdle, TaskCompleted, PostToolUseFailure)

**After:** 3 hook entries (SubagentStart, PreCompact, SessionStart)

**Contract:** All 3 remaining hooks maintain the same JSON output format (`hookSpecificOutput` with `additionalContext`). No consumers need to change.

---

## 7. Validation Checklist

### V1: SKL-006 Structural Completeness
- [ ] Frontmatter (name, description, argument-hint) present
- [ ] When to Use decision tree present
- [ ] Dynamic Context with shell injection present
- [ ] Phase 0 (PT Check) present
- [ ] Phase 9.1 (Input Discovery + Consolidation) present with Op-1/2/3
- [ ] Phase 9.2 (Delivery) present with Op-4/5
- [ ] Phase 9.3 (Cleanup) present with Op-6/7
- [ ] Terminal Summary present (no "Next:" section)
- [ ] ARCHIVE.md template embedded
- [ ] Cross-Cutting Requirements present
- [ ] Key Principles + Never list present
- [ ] Zero protocol markers (NLP v6.0)

### V2: Settings.json Integrity
- [ ] Valid JSON (`jq .` succeeds)
- [ ] Exactly 3 hook entries in `hooks` object
- [ ] SubagentStart, PreCompact, SessionStart present
- [ ] All other settings (env, permissions, plugins, language, teammateMode) unchanged

### V3: Hook File Inventory
- [ ] Exactly 3 .sh files in `.claude/hooks/`:
  on-subagent-start.sh, on-pre-compact.sh, on-session-compact.sh
- [ ] 5 deleted files confirmed absent
- [ ] Remaining hooks exit 0 and produce valid JSON

### V4: Hook NLP Conversion
- [ ] on-session-compact.sh: zero instances of `[DIA-RECOVERY]`, `[DIRECTIVE]`, `[INJECTION]`, `[STATUS]`
- [ ] on-subagent-start.sh: zero instances of `[DIA-HOOK]`
- [ ] Both hooks still produce valid JSON output

### V5: Agent .md NL Reminder
- [ ] All 6 agent .md files have L1/L2 proactive save reminder in Constraints section
- [ ] Reminder text is consistent across all files
- [ ] No other changes to agent .md files

### V6: Code Plausibility
- [ ] SKL-006 shell injection commands are syntactically valid
- [ ] ARCHIVE.md template markdown renders correctly
- [ ] Git commit message template follows Conventional Commits
- [ ] `gh pr create` command syntax is correct
- [ ] File paths referenced in SKL-006 match actual codebase structure

### V7: Agent MEMORY.md Templates
- [ ] `~/.claude/agent-memory/tester/MEMORY.md` exists with template content
- [ ] `~/.claude/agent-memory/integrator/MEMORY.md` exists with template content
- [ ] Existing 4 MEMORY.md files untouched

---

## 8. Risk Mitigation

| # | Risk | Prob | Impact | Score | Mitigation |
|---|------|------|--------|-------|------------|
| R-1 | settings.json invalid JSON after hook removal | LOW | HIGH | 6 | Verify with `jq .` immediately after edit. Implementer has Bash tool. |
| R-2 | Deleted hooks were needed for an edge case | LOW | MEDIUM | 4 | All 5 deleted hooks' logic is either migrated to NL (L1/L2 check) or deferred to Layer 2 (logging). on-subagent-stop L1/L2 logging was redundant with on-teammate-idle blocking. |
| R-3 | SKL-006 SKILL.md too large for single implementer context | LOW | HIGH | 6 | ~380 lines is within comfort zone (verification-pipeline is 522 lines, written by single implementer). Architecture design provides exact structure. |
| R-4 | NL L1/L2 reminder insufficient vs hook enforcement | MEDIUM | MEDIUM | 6 | Accepted trade-off per AD-15. Opus 4.6 instruction following is reliable. agent-common-protocol.md + agent .md + CLAUDE.md §10 = triple reinforcement. |
| R-5 | Two implementers create merge conflict | VERY LOW | LOW | 1 | Zero file overlap — Impl-A creates new file, Impl-B modifies existing files. No merge possible. |

---

## 9. Commit Strategy

**Single commit (recommended):**

```bash
git add .claude/skills/delivery-pipeline/SKILL.md \
  .claude/settings.json \
  .claude/hooks/on-session-compact.sh \
  .claude/hooks/on-subagent-start.sh \
  .claude/agents/implementer.md \
  .claude/agents/integrator.md \
  .claude/agents/architect.md \
  .claude/agents/tester.md \
  .claude/agents/researcher.md \
  .claude/agents/devils-advocate.md \
  .claude/agent-memory/tester/MEMORY.md \
  .claude/agent-memory/integrator/MEMORY.md

# Stage deletions explicitly
git rm .claude/hooks/on-subagent-stop.sh \
  .claude/hooks/on-teammate-idle.sh \
  .claude/hooks/on-task-completed.sh \
  .claude/hooks/on-task-update.sh \
  .claude/hooks/on-tool-failure.sh

git commit -m "feat(skill): SKL-006 delivery-pipeline + NL-First hook reduction (8→3)

Create Phase 9 delivery pipeline skill with 3 sub-phases:
- 9.1 Consolidation (PT update, PT→MEMORY migration, ARCHIVE.md)
- 9.2 Delivery (git commit, optional PR, user-confirmed)
- 9.3 Cleanup (artifact cleanup, task list cleanup)

Push INFRA to NL-First boundary (AD-15):
- Reduce hooks 8→3: keep SubagentStart, PreCompact, SessionStart
- Delete 5 hooks (stop, idle, task-completed, task-update, tool-failure)
- Migrate L1/L2 enforcement to NL in agent .md Constraints
- Convert remaining hook protocol markers to natural language
- Create agent MEMORY.md templates for tester and integrator

Architecture: docs/plans/2026-02-08-skl006-delivery-pipeline.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Staging plan:**
1. Implementer B stages all modifications and deletions
2. Implementer A stages new SKILL.md
3. Lead verifies staged files match the plan before committing

---

## 10. Phase 6 Entry Conditions

For implementation to begin, the following must be true:

| # | Condition | Status |
|---|-----------|--------|
| EC-1 | Phase 3 architecture approved (Gate 3) | Required |
| EC-2 | Phase 4 plan approved (Gate 4, this document) | Required |
| EC-3 | Phase 5 validation passed (Gate 5) | Required |
| EC-4 | RSIL feasibility re-evaluation complete | DONE (§2) |
| EC-5 | NL-First boundary framework confirmed by user | Required (confirmed in PT-v3) |
| EC-6 | File ownership boundaries clear and non-overlapping | DONE (§3) |
| EC-7 | All reference files accessible | DONE (architecture L3, exemplars, current files) |

**Implementation readiness:** Once Gates 3-5 approve, Phase 6 can begin immediately. Both implementers can start in parallel from task creation.

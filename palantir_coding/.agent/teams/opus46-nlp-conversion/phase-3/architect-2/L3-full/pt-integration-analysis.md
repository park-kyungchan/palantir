# PERMANENT Task Integration — Full Architecture Analysis (L3)

**Architect:** architect-2 | **Phase:** 3 (revision) | **GC:** v3 | **Date:** 2026-02-08

---

## 1. AD-7: GC to PERMANENT Task as Context Delivery Mechanism

### Conceptual Shift

From push-based (Lead physically embeds full context in every directive) to pull-based
(Lead includes Task ID reference, teammates self-serve via TaskGet).

### CLAUDE.md Section-by-Section Changes

#### Section 0 (Language Policy), line 8
```
CURRENT: "directives, GC, tasks, L1/L2/L3"
NEW:     "directives, PT, tasks, L1/L2/L3"
```

#### Section 3 (Role Protocol) — Lead, line 40
```
CURRENT: Maintains `orchestration-plan.md` and `global-context.md` (versioned: GC-v{N}).
         Sole writer of Task API (TaskCreate/TaskUpdate). Runs DIA engine continuously (see §6).

NEW:     Maintains `orchestration-plan.md` and PERMANENT Task (Task #1, versioned: PT-v{N}).
         Sole writer of Task API (TaskCreate/TaskUpdate). Runs DIA engine continuously (see §6).
```

#### Section 3 (Role Protocol) — Teammates, lines 44-49
**NO CHANGE.** TaskGet already listed. Details of PT usage handled by common-protocol.md.

#### Section 4 (Communication Protocol) table, lines 53-67

| Row | Current | New |
|-----|---------|-----|
| Row 1 | `Directive + Injection \| Lead → Teammate` | `Directive + PT Reference \| Lead → Teammate` |
| Row 5 | `Context Update \| ... \| When global-context.md changes` | `Context Update \| ... \| When PERMANENT Task changes (PT-v{N} bump)` |

All other rows: **NO CHANGE**.

#### Section 6 (DIA Engine) — Context Injection, lines 102-103
```
CURRENT:
- **Context Injection:** Embed GC-v{N} + task-context.md in every [DIRECTIVE].
  Delta mode when version_gap==1; full mode for FC-1~FC-5 (see task-api-guideline.md §14).

NEW:
- **Context Injection:** Include PT Task ID + PT-v{N} in every [DIRECTIVE].
  Teammate reads PT via TaskGet. task-context.md still embedded directly.
  Notifications: delta when gap==1, full re-read instruction on FC-1~FC-5.
```

**Design note:** Delta/full distinction shifts from delivery format to notification format.
TaskGet always returns full current state. The delta is only for the notification message
telling teammates WHAT changed. FC fallback conditions become "tell teammate to re-read PT"
rather than "re-embed full GC."

#### Section 6 (DIA Engine) — Propagation, lines 107-108
```
CURRENT:
- **Propagation:** On deviation → bump GC-v{N} → [CONTEXT-UPDATE] to affected teammates.
  Deviation levels: COSMETIC (log) / INTERFACE_CHANGE (re-inject) / ARCHITECTURE_CHANGE (re-plan).

NEW:
- **Propagation:** On deviation → bump PT-v{N} (TaskUpdate) → [CONTEXT-UPDATE] to affected teammates.
  Deviation levels: COSMETIC (log) / INTERFACE_CHANGE (notify + re-read) / ARCHITECTURE_CHANGE (re-plan).
```

#### Section 6 — GC Version Tracking, lines 111-112
```
CURRENT:
### GC Version Tracking
YAML front matter: `version: GC-v{N}` (monotonic). Lead tracks per-teammate version in orchestration-plan.md.

NEW:
### PT Version Tracking
Version: PT-v{N} (monotonic, in PERMANENT Task description). Lead tracks per-teammate confirmed
version in orchestration-plan.md.
```

#### Section 6 — NEW subsection: PERMANENT Task
```
### PERMANENT Task (PT)
Single Source of Truth for the pipeline. Task #1 in the Shared Task List.
Structure: User Intent | Codebase Impact Map | Architecture Decisions | Phase Status | Constraints.
Versioned: PT-v{N} (monotonic). Lead updates via Read-Merge-Write (TaskGet → consolidate → TaskUpdate).
Teammates read via TaskGet (self-serve). /permanent-tasks skill for user requirement reflection.
```

#### Section 6 — Output Directory, lines 122-127
```
CURRENT:
.agent/teams/{session-id}/
├── orchestration-plan.md, global-context.md, TEAM-MEMORY.md
└── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md

NEW:
.agent/teams/{session-id}/
├── orchestration-plan.md, TEAM-MEMORY.md
└── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
```

#### Section 9 (Compact Recovery) — Lead, lines 156-158
```
CURRENT:
1. Read orchestration-plan.md → Shared Task List → current gate-record.yaml → teammate L1 indexes.
2. Re-inject [DIRECTIVE]+[INJECTION] with latest GC-v{N} to each active teammate.

NEW:
1. Read orchestration-plan.md → TaskGet(PT ID) → Shared Task List → gate-record.yaml → teammate L1 indexes.
2. Send [DIRECTIVE] with PT Task ID + task-context.md to each active teammate (lightweight).
```

#### Section 9 — Teammate, lines 160-163
```
CURRENT:
Core rule: report [CONTEXT_LOST] → await [INJECTION] → re-submit [IMPACT-ANALYSIS].
Never proceed with summarized or remembered information alone.

NEW:
Core rule: TaskList → find [PERMANENT] → TaskGet(PT ID) → read L1/L2/L3 → [CONTEXT_RECOVERED] → re-submit [IMPACT-ANALYSIS].
Self-recovery via TaskGet eliminates blocking wait for Lead re-injection.
```

#### Section 9 — CONTEXT_PRESSURE, lines 165-166
```
CURRENT:
On teammate [STATUS] CONTEXT_PRESSURE: read L1/L2/L3 → shutdown teammate → re-spawn with L1/L2 injection.

NEW:
On teammate [STATUS] CONTEXT_PRESSURE: read L1/L2/L3 → shutdown → re-spawn with PT Task ID + L1/L2 summary in task-context.
```

#### [PERMANENT] Lead Duties

| Item | Line | Current | New |
|------|------|---------|-----|
| 2 (CIP) | 172-173 | Embed GC-v{N} + task-context.md. Physical embedding guarantees delivery. | Include PT Task ID + PT-v{N}. task-context.md still embedded. Teammate reads PT via TaskGet. |
| 5 (Propagation) | 180 | bump GC-v{N} → [CONTEXT-UPDATE] | bump PT-v{N} (TaskUpdate) → [CONTEXT-UPDATE] with delta summary |
| 9 (Hooks) | 189 | SubagentStart injects GC version via additionalContext | SubagentStart injects PT Task ID + PT-v{N} via additionalContext |

Items 1, 3, 4, 6, 7, 8: **NO CHANGE.**

#### [PERMANENT] Teammate Duties

| Item | Line | Current | New |
|------|------|---------|-----|
| 1 (Receipt) | 192 | Parse [INJECTION], send [STATUS] CONTEXT_RECEIVED with version. | Read PT via TaskGet(PT ID from [DIRECTIVE]), send [STATUS] CONTEXT_RECEIVED with PT-v{N}. |
| 4 (Updates) | 196 | On [CONTEXT-UPDATE] → send [ACK-UPDATE] | Same flow; [CONTEXT-UPDATE] now includes "TaskGet for PT-v{new}" |
| 6 (Recovery) | 199 | On compact → [CONTEXT_LOST] → await [INJECTION] → re-submit. | On compact → TaskList → find [PERMANENT] → TaskGet → L1/L2/L3 → [CONTEXT_RECOVERED] → re-submit. |

Items 2, 2a, 3, 4a, 5, 7: **NO CHANGE.**

---

### task-api-guideline.md Changes

#### Section 1 (Pre-Call), line 18
```
CURRENT: Read injected context from [DIRECTIVE] (global-context.md + task-context.md)
NEW:     TaskGet(PT ID from [DIRECTIVE]) for PERMANENT Task + read task-context.md
```

#### Section 6 (Semantic Integrity — Lead), line 165
```
CURRENT: Embed full global-context.md (GC-v{N}) + task-context.md in every [DIRECTIVE].
NEW:     Include PT Task ID + PT-v{N} in every [DIRECTIVE], task-context.md embedded directly.
```

#### Section 6 (Semantic Integrity — Teammate), line 171
```
CURRENT: Parse [INJECTION] — extract global-context.md and task-context.md.
NEW:     TaskGet(PT ID) for PERMANENT Task content + parse task-context.md.
```

#### Section 11 (CIP), line 269
```
CURRENT: 1. Global-context.md full text (with version: GC-v{N})
NEW:     1. PERMANENT Task ID (for TaskGet self-serve) + PT-v{N} version assertion
```

#### Section 11 — Injection Points table (lines 277-288)
All IP-001 through IP-009: replace "GC + TC" with "PT Task ID + TC" or "PT Task ID only".
IP-005 (Auto-compact Recovery): "GC + TC + L1/L2" → "PT Task ID + TC + L1/L2 summary"

#### Section 14 (Context Delta), lines 296-300, 499-502, 522
```
All "GC-v{old} → GC-v{new}" → "PT-v{old} → PT-v{new}"
All "[ACK-UPDATE] GC-v{new}" → "[ACK-UPDATE] PT-v{new}"
```

#### Section 14 — Fallback Decision Tree (lines 511-517)
```
CURRENT: Is teammate in CONTEXT_LOST state? → YES → FULL (FC-2)
NEW:     Is teammate in compact recovery? → YES → Instruct TaskGet + full task-context re-send (FC-2)
```

#### NEW subsection needed in Section 6 or new Section 15: "PERMANENT Task Type"
```
### PERMANENT Task
- Subject: "[PERMANENT] {feature/project name}"
- Status: in_progress (throughout pipeline)
- Description: Fixed 5-section structure (User Intent, Codebase Impact Map,
  Architecture Decisions, Phase Status, Constraints)
- Update pattern: Read-Merge-Write (TaskGet → intelligent consolidation → TaskUpdate)
- Consolidation rules: Deduplicate, resolve contradictions, elevate abstraction
- Version: PT-v{N} tracked in description text
- Lifecycle: Phase 0 creation → mid-work updates → L2 archive + MEMORY.md + ARCHIVE.md at end
```

---

### agent-common-protocol.md Changes

#### Phase 0: Context Receipt (lines 8-13)
```
CURRENT:
1. Receive [DIRECTIVE] + [INJECTION] from Lead.
2. Parse embedded global-context.md (note GC-v{N}).
3. Parse embedded task-context.md.
4. Send to Lead: `[STATUS] Phase {N} | CONTEXT_RECEIVED | GC-v{ver}, TC-v{ver}`

NEW:
1. Receive [DIRECTIVE] from Lead with PT Task ID and PT-v{N}.
2. Call TaskGet(PT Task ID) — read full PERMANENT Task content.
3. Review Codebase Impact Map section for your Impact Analysis.
4. Parse task-context.md from [DIRECTIVE].
5. Send to Lead: `[STATUS] Phase {N} | CONTEXT_RECEIVED | PT-v{ver}, TC-v{ver}`
```

#### Mid-Execution Updates (lines 18-22)
```
CURRENT:
On [CONTEXT-UPDATE] from Lead:
1. Parse updated global-context.md.
2. Send: `[ACK-UPDATE] GC-v{ver} received. Items: ...`

NEW:
On [CONTEXT-UPDATE] from Lead:
1. Call TaskGet(PT ID) for latest PERMANENT Task content.
2. Send: `[ACK-UPDATE] PT-v{ver} confirmed. Items: ...`
```

#### Auto-Compact Detection (lines 66-72)
```
CURRENT:
If you see "This session is being continued from a previous conversation":
1. Send `[STATUS] CONTEXT_LOST` to Lead immediately.
2. Do not proceed with any work using only summarized context.
3. Await [INJECTION] from Lead with full GC + task-context.
4. Read your own L1/L2/L3 files to restore progress.
5. Re-submit [IMPACT-ANALYSIS] to Lead (TIER 0 exempt — await Lead instructions instead).
6. Wait for [IMPACT_VERIFIED] before resuming work.

NEW:
If you see "This session is being continued from a previous conversation":
1. Call TaskList — find task with '[PERMANENT]' in subject.
2. Call TaskGet(PT ID) — immediate self-recovery, no wait needed.
3. Read your own L1/L2/L3 files to restore task-specific progress.
4. Send `[STATUS] CONTEXT_RECOVERED | PT-v{N}` to Lead.
5. Re-submit [IMPACT-ANALYSIS] to Lead (TIER 0 exempt — await Lead instructions instead).
6. Wait for [IMPACT_VERIFIED] before resuming work.
```

---

## 2. AD-8: Impact Map Integration into DIA v6.0

### CLAUDE.md §6 DIA Engine — Impact Verification
```
CURRENT:
- **Impact Verification:** Review every [IMPACT-ANALYSIS] against RC checklist. [VERIFICATION-QA] for gaps.

NEW:
- **Impact Verification:** Review every [IMPACT-ANALYSIS] against RC checklist.
  Cross-reference RC-04/RC-06/RC-07 against PT Codebase Impact Map. [VERIFICATION-QA] for gaps.
```

### RC Checklist Evaluation Method Changes (task-api-guideline.md §11)

RC criteria text: **NO CHANGE.** Evaluation method changes for 3 items:

| RC Item | Current Evaluation | New Evaluation |
|---------|-------------------|----------------|
| RC-04 (Affected file list complete) | Lead judgment | Validate against PT Impact Map Module Dependencies |
| RC-06 (Cross-teammate impact) | Lead judgment | Validate against PT Impact Map Ripple Paths |
| RC-07 (Downstream causal chain) | Lead judgment | Validate against PT Impact Map Interface Boundaries |

### LDAP Challenge Grounding

**CLAUDE.md [PERMANENT] item 7:**
```
CURRENT:
After RC checklist, generate [CHALLENGE] targeting GAP-003.

NEW:
After RC checklist, generate [CHALLENGE] targeting GAP-003.
Challenges grounded in PT Codebase Impact Map — reference documented module dependencies,
ripple paths, and interface boundaries.
```

**Examples of grounded challenges:**
- INTERCONNECTION_MAP: "The Impact Map shows Module A → B → C. Your analysis mentions A and C but not B."
- RIPPLE_TRACE: "The Impact Map identifies {path} as a ripple path. Trace the propagation."
- SCOPE_BOUNDARY: "The Impact Map shows {interface} at the boundary. Is your scope correctly bounded?"

### Continuous Monitoring

**CLAUDE.md §6 DIA Engine:**
```
CURRENT:
- **Continuous Monitoring:** Read L1/L2/L3 → compare against Phase 4 design → detect deviations.

NEW:
- **Continuous Monitoring:** Read L1/L2/L3 → compare against Phase 4 design AND PT Codebase Impact Map → detect deviations.
  Impact Map provides authoritative ripple paths for deviation level classification.
```

### agent-common-protocol.md Phase 0 Addition

New step 3 (between TaskGet and task-context parsing):
```
3. Review Codebase Impact Map section for your Impact Analysis.
```

### Agent .md Files

**NO CHANGE.** Impact Map access flows through common-protocol Phase 0 and TaskGet (already in tools).
Optional enhancement (not required): agent Phase 1.5 sections could reference Impact Map for defense evidence.

---

## 3. AD-9: Recovery via TaskGet Self-Service

### Recovery Flow Comparison

```
OLD: Teammate compact → [CONTEXT_LOST] → WAIT → Lead re-injects → parse → [IMPACT-ANALYSIS] → verify
NEW: Teammate compact → TaskList → TaskGet(PT) → L1/L2/L3 → [CONTEXT_RECOVERED] → [IMPACT-ANALYSIS] → verify
```

### PT Task ID Discovery After Compact

After compact, all in-memory state is destroyed. Discovery method:
1. Call TaskList (reads from disk, survives compact)
2. Iterate results, find task where subject contains "[PERMANENT]"
3. Call TaskGet(found ID) for full PERMANENT Task content

Robust because: Task API is disk-based, "[PERMANENT]" prefix is reliable marker, task count small.

### DIA Integrity Preservation

Self-recovery does NOT bypass DIA:
- Impact Analysis re-submission: REQUIRED (step 5 in new protocol)
- Lead verification: REQUIRED (step 6)
- The only change: Lead is informed (CONTEXT_RECOVERED) rather than blocking (CONTEXT_LOST)

---

## 4. Task Split: 4-Task to 10-Task

### Dependency Graph
```
T1 (SKILL.md CREATE)           T2 (CLAUDE.md MODIFY)         T9 (MEMORY)   T10 (ARCHIVE)
     |                              |          |               (indep)       (indep)
     |                    +---------+----------+
     |                    |         |          |
     |                    v         v          v
     |               T3 (guide)  T4 (proto)  T8 (hook)
     |                            |
     +----------------------------+
     |                            |
     v                            v
     T5 (brainstorm)    T6 (write-plan)    T7 (exec-plan)
     (needs T1 + T4)    (needs T1 + T4)    (needs T1 + T4)
```

### Execution Schedule (Max 2 Concurrent)

| Round | Slot A | Slot B | Dependencies Satisfied |
|-------|--------|--------|----------------------|
| 1 | T1: CREATE permanent-tasks/SKILL.md | T2: MODIFY CLAUDE.md | Both independent |
| 2 | T3: MODIFY task-api-guideline.md | T4: MODIFY agent-common-protocol.md | Both need T2 |
| 3 | T5: MODIFY brainstorming SKILL | T6: MODIFY write-plan SKILL | Both need T1+T4 |
| 4 | T7: MODIFY exec-plan SKILL | T8: MODIFY on-subagent-start.sh | T7: T1+T4; T8: T2 |
| 5 | T9: MODIFY MEMORY.md | T10: CREATE ARCHIVE.md | T9 needs T2; T10 indep |

### Critical Path

T2 → T4 → T5/T6/T7 (3 rounds on longest chain). T2 is the bottleneck.

---

## 5. Deduplication: Complete Reference Inventory

### CLAUDE.md (15 replacements)

| Line | Old Pattern | New Pattern |
|------|------------|-------------|
| 8 | `GC` | `PT` |
| 40 | `global-context.md (versioned: GC-v{N})` | `PERMANENT Task (Task #1, versioned: PT-v{N})` |
| 55 | `Directive + Injection` | `Directive + PT Reference` |
| 59 | `global-context.md changes` | `PERMANENT Task changes (PT-v{N} bump)` |
| 102 | `Embed GC-v{N}` | `Include PT Task ID + PT-v{N}` |
| 103 | `Delta mode...FC-1~FC-5` | `Delta notification...TaskGet` |
| 107 | `bump GC-v{N}` | `bump PT-v{N} (TaskUpdate)` |
| 111 | `GC Version Tracking` | `PT Version Tracking` |
| 112 | `version: GC-v{N}` | `PT-v{N} (in Task description)` |
| 125 | `global-context.md` in dir listing | (removed) |
| 158 | `latest GC-v{N}` | `PT Task ID + PT-v{N}` |
| 172 | `Embed GC-v{N}` | `Include PT Task ID + PT-v{N}` |
| 173 | `Physical embedding guarantees` | `TaskGet self-serve` |
| 180 | `bump GC-v{N}` | `bump PT-v{N}` |
| 189 | `GC version via additionalContext` | `PT Task ID + PT-v{N} via additionalContext` |

### task-api-guideline.md (10 replacements)

| Section:Line | Old Pattern | New Pattern |
|-------------|------------|-------------|
| §1:18 | `global-context.md + task-context.md` | `TaskGet(PT ID) + task-context.md` |
| §6:165 | `Embed full global-context.md (GC-v{N})` | `Include PT Task ID + PT-v{N}` |
| §6:171 | `Parse [INJECTION] — extract global-context.md` | `TaskGet(PT ID) for PERMANENT Task` |
| §11:269 | `Global-context.md full text` | `PT Task ID + PT-v{N} reference` |
| §11:277-288 | All IP rows: `GC + TC` | `PT Task ID + TC` |
| §14:296 | `GC-v{old} → GC-v{new}` | `PT-v{old} → PT-v{new}` |
| §14:499 | `GC-v{old} → GC-v{new}` | `PT-v{old} → PT-v{new}` |
| §14:511 | `CONTEXT_LOST state` | `compact recovery` |
| §14:522 | `GC-v{new} received` | `PT-v{new} confirmed` |

### agent-common-protocol.md (5 replacements)

| Section:Line | Old Pattern | New Pattern |
|-------------|------------|-------------|
| Phase 0:11 | `Parse embedded global-context.md (note GC-v{N})` | `Call TaskGet(PT ID) — note PT-v{N}` |
| Phase 0:13 | `GC-v{ver}, TC-v{ver}` | `PT-v{ver}, TC-v{ver}` |
| Mid-Exec:20 | `Parse updated global-context.md` | `TaskGet(PT ID) for latest PT` |
| Mid-Exec:21 | `GC-v{ver} received` | `PT-v{ver} confirmed` |
| Auto-Compact:69 | `Await [INJECTION]...full GC + task-context` | `TaskList → [PERMANENT] → TaskGet` |

### brainstorming-pipeline/SKILL.md (8+ replacements)

| Section | Old Pattern | New Pattern |
|---------|------------|-------------|
| Gate 1 (157) | Create `global-context.md (GC-v1)` file | TaskCreate "[PERMANENT] ..." with PT-v1 |
| 2.1 (234) | `GC-v1 "Phase 2 Research Needs"` | `PT-v1` |
| 2.3 directive (263) | `[INJECTION] GC-v1: {full embedded}` | `PT Task ID: {id} \| PT-v1` |
| Gate 2 (301) | `Update global-context.md → GC-v2` | `TaskUpdate PT → PT-v2` |
| 3.1 directive (330) | `[INJECTION] GC-v2: {full embedded}` | `PT Task ID + PT-v2` |
| Gate 3 (384) | `Update global-context.md → GC-v3` | `TaskUpdate PT → PT-v3` |
| Clean Term (408) | `global-context.md (GC-v3)` | `PERMANENT Task (PT-v3)` |
| Dynamic Context (34) | `ls .../global-context.md` | TaskList search for [PERMANENT] |

### agent-teams-write-plan/SKILL.md (6+ replacements)

| Section | Old Pattern | New Pattern |
|---------|------------|-------------|
| Dynamic Context (33) | `ls .../global-context.md` | TaskList for [PERMANENT] |
| 4.1 Discovery (55) | `global-context.md with Phase 3: COMPLETE` | PT with Phase 3: COMPLETE |
| 4.3 Directive (108) | `GC-v3 full embedding` | PT Task ID reference |
| Gate 4 (194) | `GC-v3 → GC-v4` | `PT-v3 → PT-v4` |
| Clean Term (222) | `GC-v4 + plan document` | `PT-v4 + plan` |

### agent-teams-execution-plan/SKILL.md (6+ replacements)

| Section | Old Pattern | New Pattern |
|---------|------------|-------------|
| Dynamic Context (38) | `ls .../global-context.md` | TaskList for [PERMANENT] |
| 6.1 Discovery (61) | `global-context.md with Phase 4: COMPLETE` | PT with Phase 4: COMPLETE |
| 6.3 Directive (162) | `GC-v4 full embedding` | PT Task ID reference |
| 6.7 (412) | `GC-v4 → GC-v5` | `PT-v4 → PT-v5` |
| Clean Term (460) | `GC-v5` | `PT-v5` |

### on-subagent-start.sh (logic rewrite)

Replace lines 24-48 (GC file search) with orchestration-plan.md PT metadata search:
```bash
# PT version injection via additionalContext
ORCH_FILE=""
if [ "$TEAM_NAME" != "no-team" ] && [ -n "$TEAM_NAME" ]; then
  ORCH_FILE="$LOG_DIR/$TEAM_NAME/orchestration-plan.md"
fi

# Fallback: most recently modified team directory
if [ -z "$ORCH_FILE" ] || [ ! -f "$ORCH_FILE" ]; then
  LATEST_ORCH=$(ls -t "$LOG_DIR"/*/orchestration-plan.md 2>/dev/null | head -1)
  if [ -n "$LATEST_ORCH" ]; then
    ORCH_FILE="$LATEST_ORCH"
  fi
fi

if [ -f "$ORCH_FILE" ]; then
  PT_VERSION=$(grep -m1 '^pt_version:' "$ORCH_FILE" 2>/dev/null | awk '{print $2}')
  PT_TASK_ID=$(grep -m1 '^pt_task_id:' "$ORCH_FILE" 2>/dev/null | awk '{print $2}')
  if [ -n "$PT_VERSION" ]; then
    jq -n --arg ver "$PT_VERSION" --arg id "$PT_TASK_ID" --arg team "$TEAM_NAME" '{
      "hookSpecificOutput": {
        "hookEventName": "SubagentStart",
        "additionalContext": ("[DIA-HOOK] Active team: " + $team + ". Current PT: " + $ver + ". PT Task ID: " + $id + ". Call TaskGet to read PERMANENT Task.")
      }
    }'
    exit 0
  fi
fi
```

Requires orchestration-plan.md YAML front matter to include:
```yaml
---
feature: {feature-name}
current_phase: {N}
pt_version: PT-v{N}
pt_task_id: {id}
---
```

---

## 6. Invariants (No Change)

1. Phase Pipeline structure (§2) — 9 phases, zones, teammates, effort levels
2. 6 agent types and their tool lists
3. File Ownership Rules (§5)
4. Spawn Matrix (§6)
5. Gate Checklist criteria (§6)
6. L1/L2/L3 Handoff format (§6)
7. Team Memory protocol (§6)
8. MCP Tools matrix (§7)
9. Safety Rules (§8)
10. DIA tier system (TIER 0/1/2/3)
11. LDAP 7 categories
12. LDAP per-phase intensity
13. RC-01~RC-10 criteria text (evaluation method changes for RC-04/06/07)
14. Two-Gate system (Gate A → Gate B)
15. Pre-Spawn Checklist (S-1, S-2, S-3)
16. Agent disallowedTools (TaskCreate/TaskUpdate blocked)
17. 6 agent .md files (no direct GC references exist)
18. Sub-Orchestrator patterns (guideline §9)
19. Metadata operations (guideline §10)
20. Known Issues ISS-001~004 (ISS-005 recovery changes per AD-9)

---

## 7. Edge Cases and Risks

### AD-7 Edge Cases

1. **TaskGet after compact:** Task API is disk-based (`~/.claude/tasks/{team-name}/{id}.json`).
   TaskGet works as long as team scope is maintained. No known failure mode.

2. **PT description size:** If Codebase Impact Map grows large, split to external file with
   PT holding path reference (design Section 9 risk mitigation).

3. **Race condition (concurrent TaskGet during TaskUpdate):** `.lock` file mechanism in Task API
   handles this (task-api-guideline.md §2).

4. **PT accidentally deleted:** Only Lead has TaskUpdate. Status "deleted" permanently removes.
   Mitigation: operational discipline. Could add hook-based safety check.

### AD-8 Edge Cases

1. **Impact Map accuracy:** Built incrementally. May be incomplete in early phases.
   Mitigated by Read-Merge-Write consolidation at every gate.

2. **Impact Map staleness:** Between PT updates, implementations may diverge.
   Mitigated by Lead's Continuous Monitoring updating PT on deviation detection.

### AD-9 Edge Cases

1. **PT Task ID unknown after compact:** TaskList traversal with "[PERMANENT]" subject search.
   Robust: disk-based, reliable marker, small task count.

2. **False CONTEXT_RECOVERED:** Teammate reads PT bytes but doesn't understand.
   Mitigated: Impact Analysis re-submission catches this (Lead still verifies).

3. **Concurrent recovery:** Multiple teammates compact simultaneously. TaskGet is read-only.
   No conflict.

### NLI + PT Interaction

Both transformations must be applied simultaneously within each implementation task.
NLI changes expression style (markers → natural language).
PT changes content (GC mechanics → PT mechanics).
Implementers need both the original L3 and the PT design spec.

---

## 8. New Content Summary

### Entirely new files
- `permanent-tasks/SKILL.md` — ~100 lines per design Section 4
- `memory/ARCHIVE.md` — consolidated from existing topic files

### New sections in existing files
- CLAUDE.md: "PERMANENT Task (PT)" subsection in §6 (~5 lines)
- task-api-guideline.md: "PERMANENT Task Type" subsection (~15 lines)
- agent-common-protocol.md: Step 3 in Phase 0 (Impact Map review, ~1 line)
- All 3 skill files: "Phase 0: PERMANENT Task Check" block (~15 lines each)

### Orchestration-plan.md front matter change
```yaml
# Old
gc_version: GC-v{N}

# New
pt_version: PT-v{N}
pt_task_id: {task_id}
```

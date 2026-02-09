# COA-3: Continuous Documentation Enforcement — Complete Specification

## Problem Statement

**Gap:** §9 says "proactively throughout execution" but no enforcement mechanism exists.

**Current State:**
- CLAUDE.md §9 (line 273): "Teammates must write L1/L2/L3 intermediate artifacts proactively throughout execution."
- CLAUDE.md §9 (line 275): "On detecting ~75% context pressure → immediately save L1/L2/L3"
- CLAUDE.md §3 Teammates (line 87): "Write L1/L2/L3 files at ~75% context pressure, then report CONTEXT_PRESSURE."
- CLAUDE.md §3 Teammates (line 88): "Pre-Compact Obligation: L1/L2/L3 files are the sole recovery mechanism."
- All 6 agent .md "Pre-Compact Obligation" sections: Echo "proactively throughout execution — not only at ~75%"
- on-teammate-idle.sh hook: Checks L1/L2 existence at IDLE time — after work, not during.
- on-task-completed.sh hook: Checks L1/L2 existence at task completion — at the END, not during.

**The enforcement gap is clear:** The ONLY concrete trigger is "~75% context pressure" which is a last-resort emergency save. The "proactively throughout execution" mandate has zero enforcement mechanisms between task start and ~75% pressure. The hooks catch it at IDLE/complete, but by then the work is done. The goal of COA-3 is to create enforcement DURING execution.

**Impact of Gap:** BUG-002 demonstrated this: teammates received large directives, consumed context reading files, never wrote any artifacts, then auto-compacted with zero recoverable output. The Pre-Spawn Checklist (Gate S-2) prevents the largest cases, but medium-sized tasks can still lose 30-60 minutes of work if no intermediate artifacts exist.

## Proposed Protocol

### Checkpoint-Based Documentation Triggers

Documentation obligations are tied to COA-2 self-location events — every self-locate checkpoint includes a documentation status check.

| # | Trigger | Documentation Obligation | Enforcement |
|---|---------|------------------------|-------------|
| DC-T1 | Task Boundary | MUST update L1 (task entry) + L2 (task results) before self-locating for new task | [SELF-LOCATE] Docs field = current required |
| DC-T2 | Major Milestone | SHOULD update L2 with intermediate findings at significant completion points | [SELF-LOCATE] Docs field visibility |
| DC-T3 | ~75% Context Pressure | MUST write full L1/L2/L3 immediately | [STATUS] CONTEXT_PRESSURE (existing) |
| DC-T4 | >15 Minutes Since L2 Update | SHOULD update L2 if meaningful work completed since last update | Time-based awareness via COA-2 |
| DC-T5 | Before IDLE Transition | MUST have L1/L2 files (≥50/≥100 bytes) | on-teammate-idle.sh hook (existing) |
| DC-T6 | Before Task Completion | MUST have L1/L2 files | on-task-completed.sh hook (existing) |

### Docs Status Field (in COA-2 [SELF-LOCATE])

The `Docs: {status}` field in [SELF-LOCATE] serves as the enforcement carrier:

| Docs Status | Definition | Lead Response |
|-------------|-----------|---------------|
| `current` | L1/L2 updated within the last completed step | None — on track |
| `stale` | L1/L2 exist but not updated in >1 completed step | Sub-workflow → ATTENTION; Lead sends documentation reminder |
| `missing` | L1/L2 not yet written in this session | Sub-workflow → ATTENTION if >first self-locate; Lead sends documentation obligation notice |

### Documentation Content Requirements (by checkpoint)

| Checkpoint | L1 Update | L2 Update | L3 Update |
|------------|-----------|-----------|-----------|
| After first major step | Initial L1 with status tracking | Initial L2 with context receipt and scope | Not required |
| Task boundary | Add task entry with status | Add task results narrative | Add task artifacts |
| Major milestone | Update progress flags | Add findings/decisions section | Add relevant details |
| ~75% pressure | Full L1 rewrite with current state | Full L2 rewrite with all findings | Full L3 dump |

### Incremental L1/L2 Writing Pattern

**L1-index.yaml incremental pattern:**
```yaml
# Version 1 (after impact verification):
findings: []
status: verified
progress:
  task_1_complete: false

# Version 2 (after task 1 milestone):
findings:
  - id: F-001
    topic: "Auth handler interface"
    priority: high
    status: in_progress
    summary: "Interface requires 3 additional parameters"
status: in_progress
progress:
  task_1_complete: false

# Version 3 (after task 1 complete):
findings:
  - id: F-001
    topic: "Auth handler interface"
    priority: high
    status: complete
    summary: "Implemented with 3 additional parameters, tests passing"
status: in_progress
progress:
  task_1_complete: true
  task_2_complete: false
```

**L2-summary.md incremental pattern:**
```markdown
# Version 1: Status + context
# Version 2: + first findings section
# Version 3: + task 1 results
# Version 4: + task 2 progress
# ... grows with each checkpoint
```

### Token Cost Analysis

- Incremental L1/L2 writes: ~200-500 tokens per checkpoint (Read + Write)
- Expected 3-5 documentation checkpoints per task
- Total: ~1000-2500 additional tokens per task
- ROI: Prevents loss of 30-60 min work (re-spawn cost: ~50K+ tokens)

## Integration Points

### 1. CLAUDE.md §9 — Enhanced Compact Recovery Section

**Current text (lines 272-276):**
```markdown
### Teammate Pre-Compact Obligation
- Teammates must write L1/L2/L3 intermediate artifacts proactively throughout execution.
- L1/L2/L3 are the only recovery mechanism — in-memory work is permanently lost on compact.
- On detecting ~75% context pressure → immediately save L1/L2/L3 → report [STATUS] CONTEXT_PRESSURE.
- `/resume` cannot restore teammates (ISS-004) — Lead must shutdown and re-spawn.
```

**Proposed replacement:**
```markdown
### Teammate Pre-Compact Obligation
- Teammates must write L1/L2/L3 intermediate artifacts at every documentation checkpoint (COA-3).
- Documentation checkpoints: task boundaries, major milestones, and every >15 minutes of active work.
- L1/L2 documentation status is carried in [SELF-LOCATE] messages (Docs field: current/stale/missing).
- Lead monitors Docs status via sub-workflow table — stale/missing triggers documentation reminder.
- On ~75% context pressure → full L1/L2/L3 save → report [STATUS] CONTEXT_PRESSURE.
- L1/L2/L3 are the sole recovery mechanism — unsaved work is permanently lost on compact.
- `/resume` cannot restore teammates (ISS-004) — Lead must shutdown and re-spawn.
```

### 2. CLAUDE.md §3 Teammates (line ~87-89)

**Current text:**
```markdown
- Write L1/L2/L3 files at ~75% context pressure, then report CONTEXT_PRESSURE.
- **Pre-Compact Obligation:** L1/L2/L3 files are the sole recovery mechanism. Unsaved work is
  permanently lost on auto-compact. Write intermediate artifacts proactively throughout execution,
  not only at ~75%. On CONTEXT_PRESSURE, Lead will shutdown and re-spawn with L1/L2 injection.
```

**Proposed replacement:**
```markdown
- **Documentation Checkpoints (COA-3):** Write L1/L2 at task boundaries and major milestones.
  Report documentation status in [SELF-LOCATE] Docs field. At ~75% context pressure, write
  full L1/L2/L3 and report CONTEXT_PRESSURE. L1/L2/L3 are the sole recovery mechanism —
  unsaved work is permanently lost on auto-compact. Lead monitors Docs status and sends
  reminders when stale/missing.
```

### 3. All 6 agent .md — Pre-Compact Obligation Section

**Current text (example from researcher.md, lines 131-133):**
```markdown
### Pre-Compact Obligation
Write intermediate L1/L2/L3 proactively throughout execution — not only at ~75%.
L1/L2/L3 are your only recovery mechanism. Unsaved work is permanently lost on compact.
```

**Proposed replacement (for all 6 agent .md):**
```markdown
### Documentation Checkpoints (COA-3)
Write L1/L2 at these checkpoints:
- **Task boundary:** Update L1 + L2 before starting each new task
- **Major milestone:** Update L2 with intermediate findings at significant completion points
- **Time-based:** If >15 minutes since last L2 update and meaningful work completed
- **~75% context pressure:** Full L1/L2/L3 save + [STATUS] CONTEXT_PRESSURE
Report Docs status (current/stale/missing) in every [SELF-LOCATE] message.
L1/L2/L3 are your only recovery mechanism. Unsaved work is permanently lost on compact.
```

### 4. task-api-guideline.md §8 ISS-005 (lines 228-236)

**Current text:**
```markdown
### ISS-005: Teammate Auto-Compact Recovery [HIGH]
...
- **Mitigation (Teammate):** Write L1/L2/L3 intermediate artifacts proactively throughout execution.
  On ~75% context pressure → save immediately → report [STATUS] CONTEXT_PRESSURE.
```

**Proposed replacement:**
```markdown
- **Mitigation (Teammate):** Write L1/L2 at documentation checkpoints (COA-3): task boundaries,
  milestones, >15min intervals. Report Docs status in [SELF-LOCATE]. On ~75% context pressure →
  full L1/L2/L3 save → report [STATUS] CONTEXT_PRESSURE.
```

## Conflict Analysis

| Existing Protocol | Conflict? | Analysis |
|-------------------|-----------|----------|
| Pre-Compact Obligation | REPLACES (vague → concrete) | "Proactively throughout execution" becomes specific checkpoints. No behavior conflict — same intent, concrete mechanism. |
| on-teammate-idle.sh | COMPATIBLE | Hook checks at IDLE; COA-3 enforces during execution. Complementary timing. |
| on-task-completed.sh | COMPATIBLE | Hook checks at completion; COA-3 enforces during execution. |
| COA-2 Self-Location | DEPENDS ON | Documentation status carried in [SELF-LOCATE] Docs field. COA-3 requires COA-2 as carrier. |
| COA-1 Sub-Workflow | FEEDS INTO | Docs status visible in sub-workflow table. ATTENTION triggered on stale/missing. |
| DIA Layers 1-4 | NO CONFLICT | Documentation is orthogonal to verification. Different concerns. |

## Scenario: Documentation Saves Work During Unexpected Compact

```
T+0:   implementer-1 starts Task 1/3 (auth module)
T+5:   [SELF-LOCATE] Task 1/3 | Step: reading source files | Docs: missing
       → Lead notes Docs: missing at first self-locate — acceptable
T+12:  [SELF-LOCATE] Task 1/3 | Step: implementing auth handler | Docs: missing
       → Lead notes Docs: missing at second self-locate — ATTENTION
       → Lead: "Update L1/L2 with current findings before continuing"
T+14:  implementer-1 writes L1/L2 with auth handler progress (3 functions implemented)
       [SELF-LOCATE] Task 1/3 | Step: implementing auth handler | Docs: current
T+20:  implementer-1 continues working, writes 2 more functions
T+22:  AUTO-COMPACT hits (context exhaustion from large file reads)
       → Without COA-3: ALL work lost (0 recoverable artifacts)
       → With COA-3: L1/L2 from T+14 preserved (3/5 functions documented)
       → Re-spawn recovers from checkpoint, only 6 minutes of work lost vs 22 minutes
```

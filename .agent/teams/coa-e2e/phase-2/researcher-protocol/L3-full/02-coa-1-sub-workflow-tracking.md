# COA-1: Sub-Workflow Orchestration Plan — Complete Specification

## Problem Statement

**Gap:** orchestration-plan.md tracks phase-level only. Within P6 with 3 implementers, no formal sub-workflow tracking protocol exists.

**Current State:**
- CLAUDE.md §6 Output Directory (lines 212-225): Structure is `phase-{N}/{role}-{id}/` — phase-level granularity only.
- orchestration-plan.md template in brainstorming-pipeline SKILL.md (lines 186-207): Tracks "Active Teammates" as a flat list with no task-level progress.
- execution-plan SKILL.md Monitoring Cadence (lines 300-305): Table shows tmux visual / TaskList / Read L1 / SendMessage query — all ad-hoc methods, no formalized tracking structure.
- CLAUDE.md §6 DIA Engine (lines 178-188): "Continuous: Read teammate L1/L2/L3 → compare against Phase 4 design → detect deviations" — the intent exists but no formal tracking format is specified.
- CLAUDE.md §6 Gate Checklist (lines 165-170): 5 criteria, none about within-phase progress tracking.
- CLAUDE.md §6 User Visibility — ASCII Status Visualization (lines 172-176): Requires visual progress reporting but provides no data structure to source it from.

**Impact of Gap:** Lead has no structured way to track parallel teammate progress. Without formal sub-workflow tracking: (a) ASCII visualization has no data source, (b) anomaly detection is impossible until teammate reports BLOCKED or COMPLETE, (c) Gate evaluation cannot verify "all teammates progressing normally" because there's no definition of "normally", (d) context recovery after Lead compact has no sub-workflow state to restore.

## Proposed Protocol

### Sub-Workflow Table Format (in orchestration-plan.md)

```markdown
## Sub-Workflow Status
<!-- Updated by Lead on [SELF-LOCATE] receipt. COA-1 protocol. -->

| Teammate | Current Task | Step | Progress | Last SL | Docs | MCP | Status | Notes |
|----------|-------------|------|----------|---------|------|-----|--------|-------|
| implementer-1 | Task 1/3 | implementing auth | 40% | 2min | current | 4 | ON_TRACK | — |
| implementer-2 | Task 1/2 | debugging edge case | 35% | 18min | stale | 1 | ATTENTION | silent >15min |
| implementer-3 | Task 1/1 | running self-tests | 85% | 1min | current | 5 | ON_TRACK | — |
```

### Status Derivation Rules

| Status | Conditions | Lead Action |
|--------|-----------|-------------|
| ON_TRACK | Last SL < 15min AND Docs ∈ {current} AND no anomalies | None — normal operation |
| ATTENTION | Last SL > 15min OR Docs = stale OR MCP below expected | Trigger COA-4 RV-1 (status ping) |
| BLOCKED | Teammate reported [STATUS] BLOCKED | Evaluate blocker, initiate resolution |
| REVERIFY | Anomaly detected, RV-2/RV-3 in progress | Await [REVERIFY-RESPONSE] |
| COMPLETING | Teammate reported final [SELF-LOCATE] at ~90%+ | Monitor for [STATUS] COMPLETE |
| COMPACT_RISK | Teammate reported [STATUS] CONTEXT_PRESSURE | Initiate shutdown + re-spawn |

### Lead Obligations

1. **Update Table:** On each [SELF-LOCATE] received, update the sub-workflow table row for that teammate.
2. **Anomaly Scan:** After each update, scan all rows for ATTENTION conditions.
3. **Trigger Re-Verification:** On ATTENTION status, trigger COA-4 re-verification (Level 1 first, escalate as needed).
4. **Gate Pre-Check:** Before any Gate evaluation, verify all sub-workflow rows are ON_TRACK or BLOCKED-resolved.
5. **ASCII Visualization:** Include sub-workflow table summary in user-facing ASCII status reports.
6. **Recovery Checkpoint:** Sub-workflow table in orchestration-plan.md survives Lead compact (file-based persistence).

### ASCII Visualization Integration

The sub-workflow table provides structured data for the ASCII visualization required by CLAUDE.md §6:

```
═══════════════════════════════════════════════════════════
 COA E2E Integration — Phase 6 (Implementation)
═══════════════════════════════════════════════════════════
 Phase Pipeline:
 [P1✓] → [P2✓] → [P3✓] → [P4✓] → [P5✓] → [P6▶] → [P7○] → [P8○] → [P9○]

 Sub-Workflow:
 implementer-1: ████████░░░░░░ Task 2/3 (40%) ON_TRACK    MCP:4 Docs:✓
 implementer-2: █████░░░░░░░░░ Task 1/2 (35%) ⚠ATTENTION  MCP:1 Docs:△
 implementer-3: ████████████░░ Task 1/1 (85%) ON_TRACK    MCP:5 Docs:✓

 Key Metrics:
 Tasks: 2/6 complete | Blockers: 0 | Re-verifications: 0
═══════════════════════════════════════════════════════════
```

## Integration Points

### 1. CLAUDE.md §6 — New "Sub-Workflow Tracking" Subsection

**Location:** After "Gate Checklist" (line ~170), before "DIA Engine (Lead)" (line ~178).

**Proposed new subsection:**
```markdown
### Sub-Workflow Tracking (COA-1)
- Lead maintains a Sub-Workflow Status table in orchestration-plan.md
- Table populated from teammate [SELF-LOCATE] messages (COA-2)
- Status derivation: ON_TRACK / ATTENTION / BLOCKED / REVERIFY / COMPLETING / COMPACT_RISK
- ATTENTION status triggers COA-4 re-verification
- All rows must be ON_TRACK or BLOCKED-resolved before any Gate evaluation
- Sub-workflow summary included in ASCII status visualization
```

### 2. CLAUDE.md §6 Gate Checklist (line ~165)

**Current text:**
```markdown
### Gate Checklist
1. All phase output artifacts exist in teammate's output directory?
2. Output quality meets next-phase entry conditions?
3. No unresolved critical issues?
4. No inter-teammate conflicts?
5. L1/L2/L3 handoff files generated?
```

**Proposed addition (item 6):**
```markdown
6. Sub-workflow status for all teammates is ON_TRACK or BLOCKED-resolved?
```

### 3. CLAUDE.md §6 DIA Engine (line ~184)

**Current text:**
```markdown
- **Continuous:** Read teammate L1/L2/L3 → compare against Phase 4 design → detect deviations.
```

**Proposed replacement:**
```markdown
- **Continuous:** Maintain sub-workflow table from [SELF-LOCATE] signals. Read teammate L1/L2/L3 →
  compare against Phase 4 design → detect deviations. Trigger COA-4 re-verification on anomaly.
```

### 4. CLAUDE.md §6 Output Directory (line ~212)

**Current template shows orchestration-plan.md at top level. No change needed to directory structure** — the sub-workflow table lives INSIDE orchestration-plan.md, not as a separate file.

### 5. All 4 SKILL.md files — orchestration-plan.md Template

**brainstorming-pipeline SKILL.md (line ~186):** Add Sub-Workflow Status section to orchestration-plan.md template.

**agent-teams-write-plan SKILL.md:** Add Sub-Workflow Status section (single architect row).

**agent-teams-execution-plan SKILL.md (line ~87):** Add Sub-Workflow Status section (N implementer rows). This skill benefits most from COA-1 since it manages parallel implementers.

**plan-validation-pipeline SKILL.md:** Add Sub-Workflow Status section (single devils-advocate row).

### 6. execution-plan SKILL.md — Monitoring Cadence (line ~300)

**Current text:**
```markdown
### Monitoring Cadence
| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| tmux visual | 0 tokens | Continuous | Always (primary) |
| TaskList | ~500 tokens | Every 15 min | Periodic check |
| Read L1 | ~2K tokens | On demand | When blocker reported |
| SendMessage query | ~200 tokens | On silence | >30 min no update |
```

**Proposed replacement:**
```markdown
### Monitoring Cadence
| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| Sub-workflow table | ~100 tokens | On each [SELF-LOCATE] | Primary (COA-1) |
| tmux visual | 0 tokens | Continuous | Visual complement |
| TaskList | ~500 tokens | Every 15 min | Backup check |
| Read L1 | ~2K tokens | On demand | When ATTENTION/BLOCKED |
| [REVERIFY] | ~200 tokens | On anomaly | COA-4 trigger |
```

## Conflict Analysis

| Existing Protocol | Conflict? | Analysis |
|-------------------|-----------|----------|
| orchestration-plan.md | EXTENDS | Adds a new section. Existing sections (Gate History, Active Teammates, Phase Plan) unchanged. |
| Gate Checklist | EXTENDS | Adds 1 criterion. Existing 5 criteria unchanged. |
| DIA Engine | EXTENDS | Formalizes "Continuous" monitoring. No conflict. |
| ASCII Visualization | ENABLES | Provides the data structure the visualization requirement needs. |
| Monitoring Cadence | IMPROVES | Replaces ad-hoc monitoring with structured signal-based approach. |
| Context Recovery (§9) | IMPROVES | Sub-workflow table in orchestration-plan.md persists across Lead compact. |

## Scenario: Sub-Workflow in Phase 6 Recovery

```
T+0:   Lead has 3-row sub-workflow table, all ON_TRACK
T+30:  Lead context compacts
T+31:  Lead recovers: reads orchestration-plan.md → sub-workflow table is there
       (Last known state of each implementer preserved in file)
T+32:  Lead sends [REVERIFY] Level 1 to all 3 implementers (post-recovery check)
T+33:  All 3 respond with [SELF-LOCATE] → Lead rebuilds live sub-workflow state
       Gap: any progress between T+30 and T+33 is missed (max ~3 min gap)
       Mitigation: L1/L2 intermediate artifacts (COA-3) fill the detail gap
```

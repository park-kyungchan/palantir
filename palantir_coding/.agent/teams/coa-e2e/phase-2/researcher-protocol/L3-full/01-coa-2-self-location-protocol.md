# COA-2: Self-Location Protocol — Complete Specification

## Problem Statement

**Gap:** No obligation for agents to periodically confirm their position in the pipeline.

**Current State:**
- CLAUDE.md §4 (lines 93-122): Defines 12 communication format strings. None is a self-location format.
- CLAUDE.md §3 Teammates (lines 73-89): Obligations listed are Context Receipt, Impact Analysis, Plan-Before-Execute, Task API read-only, Report completion, Team Memory, Context Delta, Pre-Compact. No periodic position-confirmation obligation.
- All 6 agent .md Protocol sections: Define Phase 0 (Context Receipt), Phase 1 (Impact Analysis), Phase 1.5 (Challenge), Phase 2+ (Execution), Mid-Execution Updates (only for [CONTEXT-UPDATE]), Completion. No self-location checkpoint during execution.
- execution-plan SKILL.md (lines 296-329): Monitoring cadence is Lead-initiated only (tmux visual, TaskList, Read L1, SendMessage query). No teammate-initiated heartbeat.

**Impact of Gap:** Lead has no real-time visibility into teammate progress within a phase. The only signals are: (a) [STATUS] COMPLETE at the end, (b) [STATUS] BLOCKED on error, (c) TEAM-MEMORY.md updates (Edit-capable agents only), (d) Lead-initiated queries. Between these signals, teammates are opaque — "working" with no progress visibility. This prevents early anomaly detection and delays re-verification triggers.

## Proposed Protocol

### Format String

```
[SELF-LOCATE] Phase {N} | Task {T}/{total} | Step: {description} | Progress: {est%} | MCP: {count} | Docs: {current|stale|missing}
```

**Field definitions:**
| Field | Type | Description |
|-------|------|-------------|
| Phase {N} | int | Current phase number (from GC pipeline status) |
| Task {T}/{total} | fraction | Current task number / total assigned tasks |
| Step: {description} | string | Brief description of current activity (≤10 words) |
| Progress: {est%} | percentage | Estimated progress through current task |
| MCP: {count} | int | Cumulative MCP tool calls in this session (feeds COA-5) |
| Docs: {status} | enum | L1/L2 artifact freshness: current (updated within last step), stale (>1 step behind), missing (not yet written) |

**Example messages:**
```
[SELF-LOCATE] Phase 6 | Task 2/3 | Step: implementing auth middleware | Progress: 40% | MCP: 4 | Docs: current
[SELF-LOCATE] Phase 2 | Task 1/1 | Step: reading source files | Progress: 20% | MCP: 2 | Docs: missing
[SELF-LOCATE] Phase 6 | Task 3/3 | Step: running self-tests | Progress: 85% | MCP: 7 | Docs: current
```

### Trigger Points

| # | Trigger | Condition | Obligation |
|---|---------|-----------|------------|
| SL-T1 | Task Boundary | Starting a new task within the phase | MANDATORY — self-locate before beginning new task |
| SL-T2 | Milestone | Completing a significant sub-step (e.g., finished reading, first draft done, self-review complete) | MANDATORY — self-locate at major transition points |
| SL-T3 | Time-Based | >15 minutes since last [SELF-LOCATE] | SHOULD — prevents silent drift; exact timing is agent's judgment |
| SL-T4 | On-Demand | Lead sends status query via SendMessage | MUST — respond with [SELF-LOCATE] within next turn |
| SL-T5 | Context Update | After processing [CONTEXT-UPDATE] and sending [ACK-UPDATE] | SHOULD — helps Lead track post-update state |

### Per-Role Expectations

| Role | Phase | Expected Frequency | Notes |
|------|-------|--------------------|-------|
| researcher | P2 | Per-research-domain + milestones | Typically 3-5 per session |
| architect | P3/P4 | Per-design-component + milestones | Typically 4-8 per session |
| devils-advocate | P5 | Start + completion only | Short execution, 2 self-locates |
| implementer | P6 | Per-task-boundary + per-milestone | Typically 5-15 per session (most active) |
| tester | P7 | Per-test-suite + milestones | Typically 3-6 per session |
| integrator | P8 | Per-conflict-resolution + milestones | Typically 4-8 per session |

### Token Cost Analysis

- Each [SELF-LOCATE] message: ~50-80 tokens (sending) + ~20 tokens (Lead processing)
- Expected 5-10 self-locates per teammate per session
- Total cost: ~500-800 tokens per teammate — negligible vs total session cost (~100K+ tokens)
- ROI: Early anomaly detection prevents wasted work (cost of re-spawn: ~50K tokens)

## Integration Points

### 1. CLAUDE.md §4 Communication Protocol (line ~111)

**Current text (lines 95-109):**
```markdown
| Type | Direction | When |
|------|-----------|------|
| Directive + Injection | Lead → Teammate | Spawn, assignment, correction, recovery |
| Impact Analysis | Teammate → Lead | Before any work (required) |
| Verification Q&A | Lead ↔ Teammate | During impact review |
| Re-education | Lead → Teammate | After failed verification (max 3) |
| Context Update | Lead → Teammate | When global-context.md changes (delta or full) |
| Update ACK | Teammate → Lead | After receiving context update |
| Team Memory Update | Teammate → File | During work (Edit own section with discoveries) |
| Status Report | Teammate → Lead | Completion or blocking |
| Plan Submission | Teammate → Lead | Before mutation (implementer/integrator) |
| Approval/Rejection | Lead → Teammate | Response to impact or plan |
| Phase Broadcast | Lead → All | Phase transitions only |
| Adversarial Challenge | Lead → Teammate | After RC checklist, within Gate A (Layer 3) |
| Challenge Response | Teammate → Lead | Defense against [CHALLENGE] question |
```

**Proposed addition (insert after "Challenge Response" row):**
```markdown
| Self-Location | Teammate → Lead | Periodic during execution (task boundary, milestone, time-based) |
| Re-Verification Request | Lead → Teammate | Mid-execution when anomaly detected (see COA-4) |
| Re-Verification Response | Teammate → Lead | Response to re-verification request |
```

**Format strings section (line ~111-122), add:**
```markdown
- `[SELF-LOCATE] Phase {N} | Task {T}/{total} | Step: {desc} | Progress: {%} | MCP: {count} | Docs: {status}`
- `[REVERIFY] Phase {N} | Level {L} | Target: {role-id} | Reason: {trigger} | Question: {optional}`
- `[REVERIFY-RESPONSE] Phase {N} | Level {L} | {response content}`
```

### 2. CLAUDE.md §3 Teammates (line ~73)

**Current text (line 73-89):** Lists 8 teammate obligations.

**Proposed addition (insert after "Pre-Compact Obligation" bullet):**
```markdown
- **Self-Location (COA-2):** Send [SELF-LOCATE] at task boundaries, major milestones,
  and when >15 minutes since last self-locate. Include MCP usage count and L1/L2 status.
  Respond to Lead status queries with [SELF-LOCATE] within next turn.
```

### 3. All 6 agent .md files — Execution Phase

**For researcher.md (line ~87, Phase 2: Execution section):**
Add after step 9:
```markdown
10. Send [SELF-LOCATE] at research milestones (after completing each research domain, after L1/L2 write)
```

**For architect.md (line ~93, Phase 2: Execution section):**
Add after step 8:
```markdown
9. Send [SELF-LOCATE] at design milestones (after each component design, after L1/L2 write)
```

**For implementer.md (line ~106, Phase 3: Execution section):**
Add after step 8:
```markdown
9. Send [SELF-LOCATE] at task boundaries and implementation milestones (after each file modified, after self-test, after review)
```

**For tester.md (line ~87, Phase 2: Execution section):**
Add after step 11:
```markdown
12. Send [SELF-LOCATE] at testing milestones (after each test suite written, after execution, after failure analysis)
```

**For integrator.md (line ~109, Phase 3: Execution section):**
Add after step 10:
```markdown
11. Send [SELF-LOCATE] at integration milestones (after each conflict resolved, after integration test)
```

**For devils-advocate.md (line ~52, Phase 1: Execution section):**
Add after step 9:
```markdown
10. Send [SELF-LOCATE] at start and completion (minimal frequency — short execution phase)
```

## Conflict Analysis

| Existing Protocol | Conflict? | Analysis |
|-------------------|-----------|----------|
| [STATUS] format | NO | [STATUS] is for phase-level events (COMPLETE, BLOCKED, CONTEXT_RECEIVED). [SELF-LOCATE] is for within-phase position tracking. Complementary, not overlapping. |
| DIA CIP (Layer 1) | NO | Self-location is a new signal; CIP handles context delivery. No interaction. |
| DIA DIAVP (Layer 2) | NO | DIAVP is entry-gate. Self-location is mid-execution. Different lifecycle points. |
| DIA LDAP (Layer 3) | NO | LDAP is within Gate A. Self-location is post-Gate A during execution. |
| Hooks (Layer 4) | COMPATIBLE | on-teammate-idle.sh checks L1/L2. Self-locate carries Docs status, providing earlier visibility than IDLE check. |
| Context Delta (§14) | COMPATIBLE | SL-T5 trigger adds self-locate after [ACK-UPDATE], improving post-update visibility. |
| Team Memory (§13) | NO | Team Memory is Edit-based discovery sharing. Self-location is SendMessage-based status signal. |

## Scenario: Self-Location in Multi-Implementer Phase 6

```
Timeline (3 parallel implementers in Phase 6):

T+0:   All 3 receive [DIRECTIVE] + [INJECTION]
T+2:   All 3 submit [IMPACT-ANALYSIS]
T+5:   All 3 receive [IMPACT_VERIFIED]
T+6:   All 3 submit [PLAN], receive [APPROVED]

T+7:   implementer-1: [SELF-LOCATE] Phase 6 | Task 1/3 | Step: reading source | Progress: 10% | MCP: 0 | Docs: missing
       implementer-2: [SELF-LOCATE] Phase 6 | Task 1/2 | Step: reading source | Progress: 15% | MCP: 1 | Docs: missing
       implementer-3: [SELF-LOCATE] Phase 6 | Task 1/1 | Step: reading plan §5 | Progress: 5% | MCP: 0 | Docs: missing

T+15:  implementer-1: [SELF-LOCATE] Phase 6 | Task 1/3 | Step: implementing auth handler | Progress: 40% | MCP: 2 | Docs: current
       implementer-2: (no self-locate — 8 minutes silence)
       implementer-3: [SELF-LOCATE] Phase 6 | Task 1/1 | Step: writing tests | Progress: 70% | MCP: 3 | Docs: current

       Lead sub-workflow table:
       | Teammate | Task | Progress | Last SL | Docs | MCP | Status |
       |----------|------|----------|---------|------|-----|--------|
       | impl-1 | 1/3 | 40% | 0min | current | 2 | ON_TRACK |
       | impl-2 | 1/2 | 15% | 8min | missing | 1 | ON_TRACK |
       | impl-3 | 1/1 | 70% | 0min | current | 3 | ON_TRACK |

T+25:  implementer-2 still silent (18 minutes since last self-locate)
       Lead sub-workflow: impl-2 status → ATTENTION
       Lead triggers COA-4 RV-1: [REVERIFY] Phase 6 | Level 1 | Target: implementer-2 | Reason: >15min silence
       implementer-2 responds: [SELF-LOCATE] Phase 6 | Task 1/2 | Step: debugging complex edge case | Progress: 35% | MCP: 1 | Docs: stale
       → Lead notes Docs: stale → sends documentation reminder
       → Lead notes MCP: 1 at 35% → within acceptable range

T+35:  implementer-1: [SELF-LOCATE] Phase 6 | Task 2/3 | Step: starting task 2 | Progress: 0% | MCP: 4 | Docs: current
       (Task boundary trigger — just completed Task 1)
```

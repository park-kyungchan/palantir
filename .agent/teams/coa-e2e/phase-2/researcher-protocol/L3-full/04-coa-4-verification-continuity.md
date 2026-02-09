# COA-4: Verification Continuity — Complete Specification

## Problem Statement

**Gap:** DIA verification is entry-gate only. No mid-execution re-verification mechanism exists.

**Current State:**
- CLAUDE.md [PERMANENT] (lines 304-370): DIA Enforcement defines 4 layers — CIP (delivery), DIAVP (comprehension), LDAP (systemic reasoning), Hooks (artifacts). ALL operate at entry-gate (before work begins).
- task-api-guideline.md §11 Verification Flow (lines 348-355): "1. Teammate submits [IMPACT-ANALYSIS] → 2. Lead reviews against RC → 3. [IMPACT_VERIFIED] / [IMPACT_REJECTED]" — one-time at task start.
- task-api-guideline.md §11 Two-Gate Flow (lines 427-430): "Gate A: [IMPACT-ANALYSIS] → [IMPACT_VERIFIED]. Gate B: [PLAN] → [APPROVED]." Both are pre-execution gates.
- Context Delta (§14): [CONTEXT-UPDATE] triggers [ACK-UPDATE], but ACK is a simple acknowledgment (applied/total, impact, action). No comprehension re-verification.
- CLAUDE.md §6 DIA Engine (line 184): "Continuous: Read teammate L1/L2/L3 → compare against Phase 4 design → detect deviations." The intent for continuous monitoring exists, but the action on deviation is limited to "COSMETIC (log) / INTERFACE_CHANGE (re-inject) / ARCHITECTURE_CHANGE (re-plan)" — no comprehension re-check.

**Scenarios where understanding drifts AFTER verification:**
1. Teammate reads unexpected code complexity that silently changes their approach
2. [CONTEXT-UPDATE] arrives, teammate ACKs with CONTINUE but didn't deeply process the change
3. Teammate encounters an edge case not anticipated in Impact Analysis and pivots without reporting
4. Teammate's context gradually fills with file reads, pushing original understanding out of active window
5. External dependency changes (discovered via MCP tools) invalidate original assumptions

**Impact of Gap:** Once [IMPACT_VERIFIED], the teammate operates autonomously until COMPLETE or BLOCKED. If understanding drifts mid-execution, the error is only discovered at Gate evaluation (too late — rework required) or never discovered (shipped with incorrect understanding).

## Proposed Protocol

### Re-Verification Framework (3 Levels)

| Level | Name | Token Cost | Trigger | Format | Expected Response |
|-------|------|-----------|---------|--------|-------------------|
| RV-1 | Status Ping | ~100 tokens | Silence anomaly, stale docs | `[REVERIFY] Level 1` | [SELF-LOCATE] with current status |
| RV-2 | Comprehension Check | ~300 tokens | Scope change, milestone, low MCP | `[REVERIFY] Level 2: {question}` | [REVERIFY-RESPONSE] with specific answer |
| RV-3 | Abbreviated Re-IA | ~800 tokens | Deviation detected, significant scope change | `[REVERIFY] Level 3: Re-submit abbreviated IA` | [REVERIFY-RESPONSE] with 3-RC mini-IA |

### Format Strings

**Lead → Teammate:**
```
[REVERIFY] Phase {N} | Level {L} | Target: {role-id} | Reason: {trigger_description}
```
For Level 2, append: `| Question: {specific comprehension question}`
For Level 3, append: `| Scope: Abbreviated IA (RC-01, RC-04, RC-07)`

**Teammate → Lead:**
```
[REVERIFY-RESPONSE] Phase {N} | Level {L} | {response_content}
```

### Trigger Conditions

| # | Trigger | Source | Level | Condition |
|---|---------|--------|-------|-----------|
| RV-T1 | Silence Anomaly | COA-1 sub-workflow | RV-1 | >15 min since last [SELF-LOCATE] |
| RV-T2 | Stale Documentation | COA-1 sub-workflow | RV-1 | Docs = stale at 2+ consecutive self-locates |
| RV-T3 | Scope Change | Context Delta (§14) | RV-2 | [CONTEXT-UPDATE] with Impact: affected for this teammate |
| RV-T4 | Milestone Transition | COA-2 self-locate | RV-2 | Teammate transitions from one task to next (optional, Lead discretion) |
| RV-T5 | Low MCP Usage | COA-5 check | RV-2 | MCP count = 0 at >50% task progress in Required phase |
| RV-T6 | L1/L2 Deviation | DIA Engine continuous | RV-3 | Lead reads L1/L2 and detects approach diverging from Phase 4 design |
| RV-T7 | Post-Recovery | Lead compact recovery | RV-1→RV-3 | After Lead recovers from compact, re-establish teammate state |

### RV-3 Abbreviated Impact Analysis

When Lead triggers RV-3, the teammate submits a mini-IA with 3 RC items (subset of full DIAVP):

```
[REVERIFY-RESPONSE] Phase {N} | Level 3

## Abbreviated Re-IA
- RC-01 (Task Understanding): {current task restated — has it changed from original IA?}
- RC-04 (File List): {current affected file list — any new files discovered?}
- RC-07 (Downstream Chain): {downstream impact — still valid after execution discoveries?}

## Change Summary
- Original IA claimed: {key point from original}
- Current reality: {what changed and why}
- Impact: {NONE | MINOR_ADJUSTMENT | SIGNIFICANT_DEVIATION}
```

**Lead evaluation of RV-3:**
- If all 3 RC items match original IA → understanding intact, continue
- If RC-01 or RC-07 changed but changes are justified → acknowledge, update task-context
- If SIGNIFICANT_DEVIATION → escalate to Lead decision: update GC, re-plan, or continue with adjustments

### Escalation Path

```
RV-1 (ping) → teammate responds with [SELF-LOCATE]
  └── response OK → resume normal tracking
  └── response shows anomaly → escalate to RV-2

RV-2 (question) → teammate responds with [REVERIFY-RESPONSE]
  └── answer demonstrates understanding → resume
  └── answer shows comprehension gap → escalate to RV-3

RV-3 (mini-IA) → teammate responds with abbreviated IA
  └── IA shows understanding intact → resume
  └── IA shows justified deviation → Lead updates context, continue
  └── IA shows unjustified deviation → [REJECTED], teammate corrects approach
  └── 3x RV-3 failure → ABORT teammate → re-spawn (same as DIA 3x rejection)
```

### Frequency Limits (prevent over-verification)

| Constraint | Rationale |
|-----------|-----------|
| Max 1 RV-2 per 30 minutes per teammate | Prevent verification overhead from exceeding work time |
| Max 1 RV-3 per task per teammate | RV-3 is heavyweight; more frequent = re-spawn instead |
| RV-1 has no frequency limit | It's just a ping — minimal cost |
| No re-verification during DIA entry gate | Already being verified through standard DIAVP |
| No re-verification for devils-advocate | TIER 0 exempt, short execution, read-only |

## Integration Points

### 1. CLAUDE.md [PERMANENT] — Extend DIA Description

**Current text (line ~310-313):**
```markdown
DIA Enforcement converts trust-based protocol into verify-before-proceed enforcement.
Layer 1 (CIP) guarantees delivery. Layer 2 (DIAVP) proves comprehension. Layer 3 (LDAP) proves
systemic impact reasoning. Layer 4 (Hooks) enforces artifact production automatically.
Prevention cost (5-22K tokens/teammate) is far less than rework cost (full pipeline re-execution).
```

**Proposed replacement:**
```markdown
DIA Enforcement converts trust-based protocol into verify-before-proceed enforcement.
Layer 1 (CIP) guarantees delivery. Layer 2 (DIAVP) proves comprehension. Layer 3 (LDAP) proves
systemic impact reasoning. Layer 4 (Hooks) enforces artifact production automatically.
**Verification Continuity (COA-4):** Extends DIA from entry-gate to mid-execution with 3-level
re-verification (RV-1 ping, RV-2 comprehension check, RV-3 abbreviated re-IA). Triggered by
sub-workflow anomalies (COA-1) and scope changes (Context Delta §14). Prevents understanding
drift after initial verification passes.
Prevention cost (5-22K tokens/teammate + ~1K per re-verification) is far less than rework cost.
```

### 2. CLAUDE.md §4 Communication Protocol — Format Strings

Add to the format strings list (after [CHALLENGE-RESPONSE]):
```markdown
- `[REVERIFY] Phase {N} | Level {L} | Target: {role-id} | Reason: {trigger}`
- `[REVERIFY-RESPONSE] Phase {N} | Level {L} | {response content}`
```

Add to the communication types table:
```markdown
| Re-Verification Request | Lead → Teammate | Mid-execution anomaly detected (COA-4) |
| Re-Verification Response | Teammate → Lead | Response to re-verification |
```

### 3. CLAUDE.md §6 DIA Engine — Enhance Continuous Monitoring

**Current text (line ~184):**
```markdown
- **Continuous:** Read teammate L1/L2/L3 → compare against Phase 4 design → detect deviations.
```

**Proposed replacement:**
```markdown
- **Continuous:** Monitor sub-workflow table (COA-1) for anomalies. Read teammate L1/L2/L3 →
  compare against Phase 4 design → detect deviations. On anomaly or deviation → trigger
  re-verification (COA-4): RV-1 for silence, RV-2 for scope change, RV-3 for detected deviation.
```

### 4. task-api-guideline.md §11 — New Re-Verification Subsection

**Location:** After "Two-Gate Flow" (line ~430), before §12.

**Proposed new subsection:**
```markdown
### Verification Continuity (COA-4)

Extends DIA from entry-gate to mid-execution. Three re-verification levels:

| Level | Trigger | Cost | Action |
|-------|---------|------|--------|
| RV-1 | Silence/stale docs | ~100 tok | [REVERIFY] Level 1 → [SELF-LOCATE] response |
| RV-2 | Scope change/low MCP | ~300 tok | [REVERIFY] Level 2: {question} → [REVERIFY-RESPONSE] |
| RV-3 | Detected deviation | ~800 tok | [REVERIFY] Level 3 → abbreviated IA (RC-01,04,07) |

Escalation: RV-1 → RV-2 → RV-3 → ABORT (3x failure at any level).
Frequency: Max 1 RV-2/30min, max 1 RV-3/task. No limit on RV-1.
Exempt: devils-advocate (TIER 0), Lead-only phases (P1/P9).
```

### 5. All 6 agent .md — Add Mid-Execution Re-Verification

**For all agent .md files, add to Protocol section (after "Mid-Execution Updates"):**

```markdown
### Mid-Execution Re-Verification (COA-4)
On receiving [REVERIFY] from Lead:
- Level 1: Respond with [SELF-LOCATE] reporting current position and status
- Level 2: Respond with [REVERIFY-RESPONSE] answering the specific question
- Level 3: Respond with [REVERIFY-RESPONSE] containing abbreviated IA (RC-01, RC-04, RC-07)
Re-verification is Lead-initiated. Continue normal work between re-verification events.
```

**Exception for devils-advocate.md:** Add note: "TIER 0 exempt — re-verification not expected for short read-only execution."

## Conflict Analysis

| Existing Protocol | Conflict? | Analysis |
|-------------------|-----------|----------|
| DIA Entry Gate (DIAVP) | EXTENDS | Entry-gate remains unchanged. COA-4 adds mid-execution checks. Both coexist. |
| DIA LDAP | NO CONFLICT | LDAP is within Gate A. COA-4 is post-Gate A during execution. Different timing. |
| Context Delta (§14) | EXTENDS | [CONTEXT-UPDATE] → [ACK-UPDATE] remains. COA-4 adds deeper check after significant updates. |
| Two-Gate Flow | NO CONFLICT | Gate A → Gate B → execution. COA-4 operates during execution, after both gates pass. |
| DIA Engine Continuous | FORMALIZES | "Read L1/L2/L3 → detect deviations" becomes a formal protocol with levels and escalation. |
| Re-education (3x fail) | COMPATIBLE | RV-3 3x failure → same ABORT as DIAVP 3x rejection. Consistent escalation path. |

## Scenario: Scope Change During Phase 6

```
T+0:   implementer-1 verified (Gate A + B passed), working on Task 2/3
T+10:  User adds new requirement → Lead bumps GC-v4 → GC-v5
T+11:  Lead sends [CONTEXT-UPDATE] GC-v4 → GC-v5 to implementer-1
       Delta: ADDED §Scope: new_requirement: "Rate limiting on auth endpoints"
T+12:  implementer-1: [ACK-UPDATE] GC-v5 received. Items: 1/1. Impact: affects auth module I'm implementing. Action: PAUSE.
T+13:  Lead evaluates: rate limiting directly affects implementer-1's auth handler.
       Triggers COA-4: [REVERIFY] Phase 6 | Level 2 | Target: implementer-1 | Reason: scope change affects auth module | Question: How does the rate limiting requirement change your implementation plan for the auth handler?
T+14:  implementer-1: [REVERIFY-RESPONSE] Phase 6 | Level 2 | Rate limiting requires adding middleware layer before auth handler. Original plan had auth handler as direct endpoint handler. New approach: auth handler delegates to rate limiter first. Affected files: src/auth/handler.py (original), src/auth/rate_limiter.py (NEW). Interface change: handler signature adds rate_config parameter.
T+15:  Lead evaluates: interface change detected (new parameter, new file).
       → Lead updates task-context with rate limiting scope
       → Lead sends: "Acknowledged. Update your [PLAN] to include rate_limiter.py. File ownership expanded."
       → implementer-1 submits revised [PLAN] → Lead approves → work continues with updated scope
```

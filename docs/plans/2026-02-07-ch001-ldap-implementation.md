# CH-001: LDAP Implementation — Agent Teams Execution Plan

> **For Lead:** This plan is designed for Agent Teams native execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
> Do NOT use superpowers:executing-plans. Follow DIA v2.0 protocol for the implementer.

**Goal:** Add Layer 3 (LDAP adversarial challenge) to DIA Enforcement, upgrading v2.0 → v3.0.

**Architecture:** LDAP operates within Gate A of existing DIAVP. After RC checklist evaluation,
Lead generates context-specific [CHALLENGE] questions. Teammate defends via SendMessage
turn-based IDLE-WAKE cycle. No new files or hooks — 7 existing files modified.

**Design Source:** `docs/plans/2026-02-07-ch001-ldap-design.yaml` (approved)

**Pipeline:** Simplified Phase 6 (Infrastructure) — single implementer, no Phase 2-5 preceding.

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

This is a **simplified infrastructure pipeline** (not full 9-phase product pipeline):

```
Phase 1: Discovery        — Lead reads this plan (YOU ARE HERE)
Phase 6: Implementation   — Single implementer executes all file edits
Phase 6.V: Verification   — Lead validates cross-references
Phase 9: Delivery          — Lead commits and cleans up
```

### Teammate Allocation

| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
| Implementer | 1 | `implementer` | All 7 target files (see §3) | Phase 6 |

**WHY single implementer:** All 7 files have tight cross-references (message formats,
challenge categories, intensity matrix). Splitting across implementers would create
coordination overhead exceeding parallelization benefit. File ownership consistency
is critical.

### Execution Sequence

```
Lead:   TeamCreate("ch001-ldap")
Lead:   TaskCreate × 3 (Task A, B, C — see §4)
Lead:   Spawn implementer teammate
Lead:   Send [DIRECTIVE] + [INJECTION] (global-context + task-context)
        ┌──────────────────────────────────────────────────────┐
        │ DIA Protocol (current v2.0 — LDAP does not exist yet) │
        │                                                        │
        │ Implementer: [STATUS] CONTEXT_RECEIVED                 │
        │ Implementer: [IMPACT-ANALYSIS] (TIER 1, 6 sections)   │
        │ Lead: RC-01~10 review                                  │
        │ Lead: [IMPACT_VERIFIED] or [VERIFICATION-QA]           │
        │ Implementer: [PLAN] (Gate B)                           │
        │ Lead: [APPROVED] or [REJECTED]                         │
        └──────────────────────────────────────────────────────┘
        Implementer: Execute Task A → Task B → Task C
        Implementer: Self-verify → Write L1/L2/L3
        Implementer: [STATUS] Phase 6 | COMPLETE
Lead:   Gate Review (cross-reference validation)
Lead:   Commit (or instruct implementer to commit)
Lead:   Shutdown teammate → TeamDelete
```

---

## 2. global-context.md Template

> Lead: Create this as `.agent/teams/{session-id}/global-context.md` at TeamCreate time.

```yaml
---
version: GC-v1
project: CH-001 LDAP Implementation
pipeline: Simplified Infrastructure (Phase 1 → 6 → 6.V → 9)
current_phase: 6
---
```

```markdown
# Global Context — CH-001 LDAP

## Project Summary
Upgrade DIA Enforcement from v2.0 (2-layer: CIP + DIAVP) to v3.0 (3-layer: CIP + DIAVP + LDAP).
LDAP = Lead Devil's Advocate Protocol. Adds adversarial challenge step (Layer 3) within Gate A
to verify systemic impact awareness (GAP-003).

## Design Reference
- Approved design: `docs/plans/2026-02-07-ch001-ldap-design.yaml`
- Implementation plan: `docs/plans/2026-02-07-ch001-ldap-implementation.md` (this file)

## Key Design Decisions
- GAP-003a (Interconnection Blindness) + GAP-003b (Ripple Blindness)
- 7 challenge categories: INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE,
  FAILURE_MODE, DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
- Shift-Left intensity: MAXIMUM(P3/P4), HIGH(P6/P8), MEDIUM(P2/P7), EXEMPT(P5), NONE(P1/P9)
- Implementation: Option A (Within Gate A) + Option D (task-context.md persistence)
- Enforcement: IDLE-WAKE turn-based cycle via SendMessage

## Scope
- 7 files modified, 0 files created, 0 hooks added
- CLAUDE.md: v2.0 → v3.0
- task-api-guideline.md: v2.0 → v3.0
- 5 agent .md files: add Phase 1.5 section
- devils-advocate.md: NO change (TIER 0 exempt)

## Cross-Reference Integrity Requirement [CRITICAL]
All 7 files share these exact strings — they MUST match across all files:
- Message format: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
- Message format: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`
- 7 category IDs: INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE,
  DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
- Intensity levels: NONE, MEDIUM, HIGH, MAXIMUM, EXEMPT

## Active Teammates
- implementer-1: Sole implementer. Owns all 7 target files.

## Phase Status
- Phase 1 (Discovery): COMPLETE
- Phase 6 (Implementation): IN_PROGRESS
- Phase 6.V (Verification): PENDING
- Phase 9 (Delivery): PENDING
```

---

## 3. File Ownership Assignment

> Lead: Include this in task-context.md for the implementer.

| File | Ownership | Operation |
|------|-----------|-----------|
| `.claude/CLAUDE.md` | implementer-1 | MODIFY (3 sections: §3, §4, [PERMANENT]) |
| `.claude/references/task-api-guideline.md` | implementer-1 | MODIFY (§11 + version header) |
| `.claude/agents/implementer.md` | implementer-1 | MODIFY (add Phase 1.5) |
| `.claude/agents/integrator.md` | implementer-1 | MODIFY (add Phase 1.5) |
| `.claude/agents/architect.md` | implementer-1 | MODIFY (add Phase 1.5) |
| `.claude/agents/tester.md` | implementer-1 | MODIFY (add Phase 1.5) |
| `.claude/agents/researcher.md` | implementer-1 | MODIFY (add Phase 1.5) |
| `.claude/agents/devils-advocate.md` | — | READ-ONLY (verify no change needed) |

---

## 4. TaskCreate Definitions

> Lead: Create these 3 tasks via TaskCreate after TeamCreate.
> Task A and B are the implementation work. Task C is verification.
> Task C is blockedBy Task A and Task B.

### Task A: Modify Core Infrastructure Files

```
subject: "Implement LDAP Layer 3 in CLAUDE.md and task-api-guideline.md"

description: |
  ## Objective
  Add LDAP (Layer 3) to the two core infrastructure files: CLAUDE.md (Team Constitution)
  and task-api-guideline.md (DIA Enforcement Protocol). This establishes the protocol
  definition that all agent files will reference.

  ## Context in Global Pipeline
  - Phase: 6 (Implementation)
  - Upstream: Approved design at docs/plans/2026-02-07-ch001-ldap-design.yaml
  - Downstream: Task B (agent .md files reference formats defined here)

  ## Detailed Requirements
  See §5 "Edit Specifications — Task A" in this plan for exact content.

  ## File Ownership
  - .claude/CLAUDE.md (3 edits: §3 Lead, §4 Communication, [PERMANENT])
  - .claude/references/task-api-guideline.md (2 edits: version header, §11 Layer 3)

  ## Dependency Chain
  - blockedBy: []
  - blocks: [Task C]

  ## Acceptance Criteria
  1. CLAUDE.md version header reads "3.0"
  2. CLAUDE.md §3 Lead has LDAP duty bullet
  3. CLAUDE.md §4 has [CHALLENGE] and [CHALLENGE-RESPONSE] in table and formats
  4. CLAUDE.md [PERMANENT] has item 7 (LDAP) and item 2a (Challenge Response)
  5. CLAUDE.md [PERMANENT] WHY mentions all 3 layers
  6. task-api-guideline.md version header reads "3.0 (DIA Enforcement + LDAP)"
  7. task-api-guideline.md §11 has Layer 3 section between Verification Flow and Two-Gate Flow
  8. Layer 3 section contains: GAP-003 definition, 7 categories table, intensity table,
     8-step challenge flow, enforcement mechanism, defense quality criteria, compaction recovery

activeForm: "Implementing LDAP in core infrastructure files"
```

### Task B: Add Phase 1.5 to Agent Definition Files

```
subject: "Add LDAP Phase 1.5 Challenge Response to 5 agent definitions"

description: |
  ## Objective
  Insert Phase 1.5 (Challenge Response) section into 5 agent .md files between
  Phase 1 (Impact Analysis) and the next section (Two-Gate System or Phase 2).
  Verify devils-advocate.md requires no change.

  ## Context in Global Pipeline
  - Phase: 6 (Implementation)
  - Upstream: Task A establishes protocol formats in CLAUDE.md and guideline
  - Downstream: Task C (cross-reference validation)

  ## Detailed Requirements
  See §6 "Edit Specifications — Task B" in this plan for exact content per agent.

  ## File Ownership
  - .claude/agents/implementer.md (TIER 1, HIGH: 2Q)
  - .claude/agents/integrator.md (TIER 1, HIGH: 2Q, all 7 categories)
  - .claude/agents/architect.md (TIER 2, MAXIMUM: 3Q + alternative)
  - .claude/agents/tester.md (TIER 2, MEDIUM: 1Q)
  - .claude/agents/researcher.md (TIER 3, MEDIUM: 1Q)
  - .claude/agents/devils-advocate.md (READ-ONLY — verify no change)

  ## Dependency Chain
  - blockedBy: []
  - blocks: [Task C]

  ## Acceptance Criteria
  1. Each of 5 agents has Phase 1.5 section in correct location
  2. Intensity levels match: implementer(HIGH:2Q), integrator(HIGH:2Q),
     architect(MAXIMUM:3Q+alt), tester(MEDIUM:1Q), researcher(MEDIUM:1Q)
  3. Message format strings match CLAUDE.md §4 exactly
  4. Expected categories are role-appropriate (see §6)
  5. devils-advocate.md confirmed unchanged (TIER 0 exempt)

activeForm: "Adding Phase 1.5 to agent definitions"
```

### Task C: Cross-Reference Validation and Commit

```
subject: "Validate cross-references across all 7 modified files and commit"

description: |
  ## Objective
  Verify that all cross-references (message formats, category IDs, intensity levels,
  GAP-003 definitions, version numbers) are consistent across all 7 modified files.
  Then commit all changes.

  ## Context in Global Pipeline
  - Phase: 6.V (Verification)
  - Upstream: Task A (core files) + Task B (agent files)
  - Downstream: Phase 9 (Delivery)

  ## Detailed Requirements
  See §7 "Validation Checklist" in this plan for exact checks.

  ## File Ownership
  - All 7 modified files + devils-advocate.md (READ for verification)

  ## Dependency Chain
  - blockedBy: [Task A, Task B]
  - blocks: []

  ## Acceptance Criteria
  1. [CHALLENGE] format string identical in: CLAUDE.md §4, guideline §11, all 5 agents
  2. [CHALLENGE-RESPONSE] format string identical across all files
  3. All 7 category IDs consistent (no typos, no missing)
  4. Intensity matrix matches: CLAUDE.md [PERMANENT] = guideline §11 table = agent headers
  5. Version numbers: CLAUDE.md=3.0, guideline=3.0
  6. GAP-003a/b definitions consistent between guideline §11 and design YAML
  7. All changes committed to git

activeForm: "Validating cross-references and committing"
```

---

## 5. Edit Specifications — Task A (Core Infrastructure)

### A1: CLAUDE.md §3 Lead Role

**Location:** After line `- Runs DIA engine continuously (see §6)` (line 49),
BEFORE `- Sole writer of Task API` (line 50).

**Insert:**

```markdown
- **Adversarial Challenge (LDAP):** After RC checklist evaluation, generate context-specific
  [CHALLENGE] questions targeting GAP-003 (systemic impact awareness). Evaluate defense quality.
  Intensity by phase: MAXIMUM (P3/P4: 3Q+alt), HIGH (P6/P8: 2Q), MEDIUM (P2/P7: 1Q),
  EXEMPT (P5), NONE (P1/P9). See [PERMANENT] §7 for enforcement details.
```

### A2: CLAUDE.md §4 Communication Protocol — Table Rows

**Location:** After last table row `| Phase Broadcast | Lead → All | Phase transitions ONLY |` (line 78).

**Insert:**

```markdown
| Adversarial Challenge | Lead → Teammate | After RC checklist, within Gate A (Layer 3) |
| Challenge Response | Teammate → Lead | Defense against [CHALLENGE] question |
```

### A3: CLAUDE.md §4 Communication Protocol — Formats

**Location:** After last format entry `- [APPROVED] Proceed. / [REJECTED] Reason: ...` (line 89).

**Insert:**

```markdown
- `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
- `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`
```

### A4: CLAUDE.md Version Header

**Location:** Line 3.

**Change from:**
```
> **Version:** 2.0 | **Architecture:** Agent Teams (Opus 4.6 Native) | **DIA Enforcement:** Enabled
```

**Change to:**
```
> **Version:** 3.0 | **Architecture:** Agent Teams (Opus 4.6 Native) | **DIA Enforcement:** Enabled (LDAP)
```

### A5: CLAUDE.md [PERMANENT] — Lead Enforcement Duty §7

**Location:** After item 6 `6. **Failure Escalation:** ...` (line 205).

**Insert:**

```markdown
7. **Adversarial Challenge (LDAP):** After RC checklist (Layer 2), generate [CHALLENGE] questions
   targeting systemic impact awareness (GAP-003a: interconnection, GAP-003b: ripple).
   - WHY: Eliminates "understood but didn't think through systemic impact" failure.
     RC checklist proves comprehension; LDAP proves critical systemic reasoning.
   - Challenge Categories (7): INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE,
     DEPENDENCY_RISK, ASSUMPTION_PROBE, ALTERNATIVE_DEMAND
   - Intensity: MAXIMUM (P3/P4: 3Q + alternative), HIGH (P6/P8: 2Q), MEDIUM (P2/P7: 1Q),
     EXEMPT (P5: devils-advocate owns critique), NONE (P1/P9: Lead only)
   - Enforcement: Gate A [IMPACT_VERIFIED] withheld until challenge defense passes.
     Structural enforcement via turn-based IDLE-WAKE cycle (SendMessage).
   - Failure: Failed defense = [IMPACT_REJECTED] with challenge evidence. Max 3 attempts → ABORT.
```

### A6: CLAUDE.md [PERMANENT] — Teammate Compliance Duty 2a

**Location:** After item 2 (Impact Analysis), BEFORE item 3 (Task API).

**Insert:**

```markdown
2a. **Challenge Response:** On [CHALLENGE] from Lead, respond with [CHALLENGE-RESPONSE] defending
    systemic impact analysis. Provide specific evidence (module names, propagation paths, blast radius).
    - No work until all challenges answered AND [IMPACT_VERIFIED] received.
    - Expected categories vary by tier (see agent .md Protocol section).
```

### A7: CLAUDE.md [PERMANENT] — WHY Section Update

**Location:** WHY This Exists paragraph (lines 186-189).

**Replace from:**
```
Protocol alone is not enforcement. Without physical verification, teammates may skip context reading,
work with stale understanding, or produce code that conflicts with other teammates' outputs.
DIA Enforcement converts "trust-based" protocol into "verify-before-proceed" enforcement.
Prevention cost (5-14K tokens/teammate) << Rework cost (full pipeline re-execution).
```

**Replace to:**
```
Protocol alone is not enforcement. Without physical verification, teammates may skip context reading,
work with stale understanding, produce code that conflicts with other teammates' outputs, or fail
to consider systemic interconnection and ripple effects across the entire task scope and codebase.
DIA Enforcement converts "trust-based" protocol into "verify-before-proceed" enforcement.
Layer 1 (CIP) guarantees delivery. Layer 2 (DIAVP) proves comprehension. Layer 3 (LDAP) proves
systemic impact reasoning. Prevention cost (5-22K tokens/teammate) << Rework cost (full pipeline re-execution).
```

### A8: CLAUDE.md [PERMANENT] — Cross-References

**Location:** Cross-References section (after line 220).

**Add line:**
```markdown
- LDAP design: `docs/plans/2026-02-07-ch001-ldap-design.yaml` (7 challenge categories, intensity matrix)
```

### A9: task-api-guideline.md Version Header

**Location:** Line 5.

**Change from:**
```
> **Version:** 2.0 (DIA Enforcement) | Updated: 2026-02-07
```

**Change to:**
```
> **Version:** 3.0 (DIA Enforcement + LDAP) | Updated: 2026-02-07
```

### A10: task-api-guideline.md §11 — Layer 3 LDAP

**Location:** After line `3. Max 3 failures → [IMPACT_ABORT] → Teammate terminated → re-spawn with enhanced context` (line 313), BEFORE the Two-Gate Flow section.

**Insert the following block (complete Layer 3 specification):**

```markdown

**Layer 3: Adversarial Challenge Protocol (LDAP)**

**WHY:** Eliminates GAP-003 (understood but no systemic impact awareness).
RC checklist verifies "do you understand WHAT to do?" but not "do you understand
HOW your work affects the interconnected system?" LDAP forces critical reasoning
about interconnection (GAP-003a) and ripple propagation (GAP-003b).

**GAP-003 Definition:**
- GAP-003a (Interconnection Blindness): Teammate does not see how their module participates
  in the organic/integrated operation of the whole system.
- GAP-003b (Ripple Blindness): Teammate cannot trace where and how far their changes
  propagate through the entire task scope and codebase.

**Challenge Categories:**

| ID | GAP | Purpose |
|----|-----|---------|
| INTERCONNECTION_MAP | 003a | Verify module participation in organic whole |
| SCOPE_BOUNDARY | 003a | Verify scope is neither too narrow nor too wide |
| RIPPLE_TRACE | 003b | Verify change propagation tracing to terminal effects |
| FAILURE_MODE | 003b | Verify system-wide failure consequence awareness |
| DEPENDENCY_RISK | 003b | Verify upstream volatility propagation awareness |
| ASSUMPTION_PROBE | 003a+b | Challenge unstated assumptions hiding impact gaps |
| ALTERNATIVE_DEMAND | 003a+b | Force consideration of systemic alternatives |

**Challenge Intensity by Phase:**

| Phase | Level | Min Questions | Alternative Required | Reason |
|-------|-------|--------------|---------------------|--------|
| P1 | NONE | 0 | — | Lead only phase |
| P2 | MEDIUM | 1 | No | Research scope verification |
| P3 | MAXIMUM | 3 | Yes | Architecture — cheapest to fix |
| P4 | MAXIMUM | 3 | Yes | Detailed design — cheapest to fix |
| P5 | EXEMPT | 0 | — | Devils-advocate owns critique |
| P6 | HIGH | 2 | No | Implementation — code-level propagation |
| P7 | MEDIUM | 1 | No | Testing — scope and failure awareness |
| P8 | HIGH | 2 | No | Integration — cross-boundary awareness |
| P9 | NONE | 0 | — | Lead only phase |

**Challenge Flow (within Gate A, after RC evaluation):**
1. Lead reads teammate's [IMPACT-ANALYSIS] content
2. Lead identifies weak spots in systemic impact reasoning
3. Lead generates N questions (N = phase intensity min_questions)
4. Lead sends: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
5. Teammate responds: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`
6. Repeat for all questions (turn-based via IDLE-WAKE cycle)
7. Lead evaluates combined RC + challenge defense quality:
   - Strong defense → [IMPACT_VERIFIED] Proceed.
   - Partial defense → [VERIFICATION-QA] follow-up for specific gaps
   - Failed defense → [IMPACT_REJECTED] with challenge evidence cited
8. For MAXIMUM intensity: teammate MUST propose at least one alternative approach
   with its own interconnection map and ripple profile

**Enforcement Mechanism:**
- Structural: Lead withholds [IMPACT_VERIFIED] until challenge defense passes
- Turn-based: Teammate IDLE after [IMPACT-ANALYSIS] → Lead sends [CHALLENGE] →
  Teammate WAKES → responds → IDLE → Lead evaluates (natural pause via IDLE state)
- Hard: Gate A prerequisite for Gate B (implementer/integrator)
- Soft: Agent .md Phase 1.5 instructions (guidance)

**Defense Quality Criteria:**
- Strong: Specific module names, concrete propagation paths, quantified blast radius
- Weak: Vague claims, generic statements, missing propagation paths
- Failed: No systemic reasoning, copy-paste from [IMPACT-ANALYSIS], factual errors

**Compaction Recovery:**
- Challenge round/state persisted in task-context.md by Lead
- PreCompact hook includes challenge state in pre-compact snapshot
- On recovery: Lead re-injects task-context.md with challenge state → resumes from last round
```

---

## 6. Edit Specifications — Task B (Agent Definitions)

### B1: implementer.md — Phase 1.5 (TIER 1, HIGH: 2Q)

**Location:** After `- 3 failures → [IMPACT_ABORT] → await termination and re-spawn` (line 78),
BEFORE `### Two-Gate System` (line 80).

**Insert:**

```markdown

### Phase 1.5: Challenge Response [MANDATORY — HIGH: 2Q minimum]
After submitting [IMPACT-ANALYSIS] and before receiving [IMPACT_VERIFIED], Lead may issue
adversarial challenges to verify systemic impact awareness (GAP-003).

On receiving [CHALLENGE]:
1. Parse: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
2. Think through the challenge — how does your implementation connect to and affect the system?
3. Respond with specific, concrete evidence (module names, file paths, propagation chains)
4. Send: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense with specific evidence}`
5. Await next [CHALLENGE] or [IMPACT_VERIFIED] / [IMPACT_REJECTED]

**Expected categories:** RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, INTERCONNECTION_MAP
**Defense quality:** Specific module names, concrete propagation paths, quantified blast radius.
Vague or generic claims = weak defense = potential [IMPACT_REJECTED].
```

### B2: integrator.md — Phase 1.5 (TIER 1, HIGH: 2Q, all categories)

**Location:** After `- 3 failures → [IMPACT_ABORT] → await termination and re-spawn` (line 78),
BEFORE `### Two-Gate System` (line 80).

**Insert:**

```markdown

### Phase 1.5: Challenge Response [MANDATORY — HIGH: 2Q minimum]
After submitting [IMPACT-ANALYSIS] and before receiving [IMPACT_VERIFIED], Lead may issue
adversarial challenges to verify systemic impact awareness (GAP-003).

On receiving [CHALLENGE]:
1. Parse: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
2. Think through the challenge — how does your integration work connect to and affect the system?
3. Respond with specific, concrete evidence (module names, file paths, merge conflict chains)
4. Send: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense with specific evidence}`
5. Await next [CHALLENGE] or [IMPACT_VERIFIED] / [IMPACT_REJECTED]

**Expected categories:** All 7 categories. Integration = cross-boundary by nature,
so interconnection and ripple awareness are critical.
**Defense quality:** Specific module names, concrete propagation paths, quantified blast radius.
Vague or generic claims = weak defense = potential [IMPACT_REJECTED].
```

### B3: architect.md — Phase 1.5 (TIER 2, MAXIMUM: 3Q + alternative)

**Location:** After `- [IMPACT_REJECTED] → re-study injected context → re-submit (max 3 attempts)` (line 67),
BEFORE `### Phase 2: Execution` (line 69).

**Insert:**

```markdown

### Phase 1.5: Challenge Response [MANDATORY — MAXIMUM: 3Q + alternative required]
After submitting [IMPACT-ANALYSIS] and before receiving [IMPACT_VERIFIED], Lead WILL issue
adversarial challenges to verify systemic impact awareness (GAP-003).
Architecture phases (P3/P4) receive MAXIMUM intensity — design flaws caught here
prevent exponential downstream cost.

On receiving [CHALLENGE]:
1. Parse: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
2. Think through the challenge — how does your design connect to and affect the entire system?
3. Respond with specific evidence (component names, interface contracts, propagation chains)
4. Send: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense with specific evidence}`
5. If Category is ALTERNATIVE_DEMAND: MUST propose at least one concrete alternative approach
   with its own interconnection map and ripple profile
6. Await next [CHALLENGE] or [IMPACT_VERIFIED] / [IMPACT_REJECTED]

**Expected categories:** All 7 categories. Highest scrutiny phase.
**Defense quality:** Specific component names, interface contract references, concrete
propagation chains, quantified blast radius. Vague claims = weak defense.
```

### B4: tester.md — Phase 1.5 (TIER 2, MEDIUM: 1Q)

**Location:** After `- [IMPACT_REJECTED] → re-study injected context → re-submit (max 3 attempts)` (line 66),
BEFORE `### Phase 2: Execution` (line 68).

**Insert:**

```markdown

### Phase 1.5: Challenge Response [MANDATORY — MEDIUM: 1Q minimum]
After submitting [IMPACT-ANALYSIS] and before receiving [IMPACT_VERIFIED], Lead may issue
adversarial challenges to verify systemic impact awareness (GAP-003).

On receiving [CHALLENGE]:
1. Parse: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
2. Think through the challenge — how does your test scope connect to the system?
3. Respond with specific evidence (test targets, failure paths, coverage implications)
4. Send: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense with specific evidence}`
5. Await next [CHALLENGE] or [IMPACT_VERIFIED] / [IMPACT_REJECTED]

**Expected categories:** SCOPE_BOUNDARY, FAILURE_MODE, DEPENDENCY_RISK
**Defense quality:** Specific test targets, concrete failure scenarios, coverage gap analysis.
```

### B5: researcher.md — Phase 1.5 (TIER 3, MEDIUM: 1Q)

**Location:** After `- [IMPACT_REJECTED] → re-study injected context → re-submit (max 2 attempts)` (line 67),
BEFORE `### Phase 2: Execution` (line 69).

**Insert:**

```markdown

### Phase 1.5: Challenge Response [MANDATORY — MEDIUM: 1Q minimum]
After submitting [IMPACT-ANALYSIS] and before receiving [IMPACT_VERIFIED], Lead may issue
adversarial challenges to verify systemic impact awareness (GAP-003).

On receiving [CHALLENGE]:
1. Parse: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`
2. Think through the challenge — how does your research scope connect to downstream work?
3. Respond with specific evidence (downstream consumers, research boundary justification)
4. Send: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense with specific evidence}`
5. Await next [CHALLENGE] or [IMPACT_VERIFIED] / [IMPACT_REJECTED]

**Expected categories:** INTERCONNECTION_MAP, SCOPE_BOUNDARY, ASSUMPTION_PROBE
**Defense quality:** Specific downstream consumer identification, concrete scope boundaries,
assumption justification with evidence.
```

### B6: devils-advocate.md — Verify No Change

**Action:** Read `.claude/agents/devils-advocate.md` and confirm:
- `### TIER 0: Impact Analysis Exempt` exists
- No Phase 1 section (goes Phase 0 → Phase 1: Execution)
- No Phase 1.5 insertion needed
- Document in L1-index.yaml: `devils-advocate.md: VERIFIED_NO_CHANGE`

---

## 7. Validation Checklist (Task C)

### V1: Message Format Consistency

Check `[CHALLENGE]` format string is IDENTICAL in:
- [ ] `.claude/CLAUDE.md` §4 Formats
- [ ] `.claude/references/task-api-guideline.md` §11 Challenge Flow step 4
- [ ] `.claude/agents/implementer.md` Phase 1.5 step 1
- [ ] `.claude/agents/integrator.md` Phase 1.5 step 1
- [ ] `.claude/agents/architect.md` Phase 1.5 step 1
- [ ] `.claude/agents/tester.md` Phase 1.5 step 1
- [ ] `.claude/agents/researcher.md` Phase 1.5 step 1

Expected: `[CHALLENGE] Phase {N} | Q{X}/{total}: {question} | Category: {category_id}`

Check `[CHALLENGE-RESPONSE]` format string is IDENTICAL in:
- [ ] `.claude/CLAUDE.md` §4 Formats
- [ ] `.claude/references/task-api-guideline.md` §11 Challenge Flow step 5
- [ ] All 5 agent .md files Phase 1.5 step 4

Expected: `[CHALLENGE-RESPONSE] Phase {N} | Q{X}: {defense}`

### V2: Intensity Matrix Consistency

| Phase | CLAUDE.md [PERMANENT] | guideline §11 table | Agent header |
|-------|-----------------------|--------------------|----|
| P2 | MEDIUM 1Q | MEDIUM 1Q | researcher: `[MANDATORY — MEDIUM: 1Q minimum]` |
| P3 | MAXIMUM 3Q+alt | MAXIMUM 3Q Yes | architect: `[MANDATORY — MAXIMUM: 3Q + alternative required]` |
| P4 | MAXIMUM 3Q+alt | MAXIMUM 3Q Yes | architect: `[MANDATORY — MAXIMUM: 3Q + alternative required]` |
| P5 | EXEMPT | EXEMPT | devils-advocate: (no Phase 1.5) |
| P6 | HIGH 2Q | HIGH 2Q | implementer: `[MANDATORY — HIGH: 2Q minimum]` |
| P7 | MEDIUM 1Q | MEDIUM 1Q | tester: `[MANDATORY — MEDIUM: 1Q minimum]` |
| P8 | HIGH 2Q | HIGH 2Q | integrator: `[MANDATORY — HIGH: 2Q minimum]` |

### V3: Category Assignments

- [ ] researcher: INTERCONNECTION_MAP, SCOPE_BOUNDARY, ASSUMPTION_PROBE (3)
- [ ] architect: All 7 categories
- [ ] implementer: RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, INTERCONNECTION_MAP (4)
- [ ] tester: SCOPE_BOUNDARY, FAILURE_MODE, DEPENDENCY_RISK (3)
- [ ] integrator: All 7 categories

### V4: Version Numbers

- [ ] `.claude/CLAUDE.md` line 3: `Version: 3.0`
- [ ] `.claude/references/task-api-guideline.md` line 5: `Version: 3.0 (DIA Enforcement + LDAP)`

### V5: GAP-003 Definition Consistency

Compare GAP-003a/b definitions between:
- [ ] `docs/plans/2026-02-07-ch001-ldap-design.yaml` §1 (source of truth)
- [ ] `.claude/references/task-api-guideline.md` §11 Layer 3 "GAP-003 Definition"
- [ ] `.claude/CLAUDE.md` [PERMANENT] §7 (referenced indirectly)

---

## 8. Commit Strategy

> The implementer has Bash access and can commit.

**Option 1 (Recommended): Single commit after all edits**

After Task A + B + C all pass, commit everything at once:

```bash
git add .claude/CLAUDE.md .claude/references/task-api-guideline.md \
  .claude/agents/implementer.md .claude/agents/integrator.md \
  .claude/agents/architect.md .claude/agents/tester.md .claude/agents/researcher.md
git commit -m "feat(dia): DIA v3.0 — LDAP Layer 3 adversarial challenge protocol

Add Layer 3 (Lead Devil's Advocate Protocol) to DIA Enforcement:
- 7 challenge categories targeting GAP-003 (systemic impact awareness)
- Shift-Left intensity scaling (MAXIMUM for P3/P4, HIGH for P6/P8)
- Phase 1.5 Challenge Response added to 5 agent definitions
- Turn-based IDLE-WAKE enforcement via SendMessage
- Compaction recovery via task-context.md persistence

Files modified: CLAUDE.md (v3.0), task-api-guideline.md (v3.0),
implementer.md, integrator.md, architect.md, tester.md, researcher.md

Design: docs/plans/2026-02-07-ch001-ldap-design.yaml

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

**Option 2: Per-task commits (if Lead prefers granularity)**

Lead instructs implementer to commit after each task:
- Task A commit: `feat(dia): add LDAP Layer 3 to CLAUDE.md and task-api-guideline.md`
- Task B commit: `feat(dia): add Phase 1.5 to 5 agent definitions`
- Task C commit: (no changes — validation only)

---

## 9. Gate Criteria (Lead Evaluation)

### Phase 6 Gate (after implementer reports COMPLETE)

| # | Criterion | Check Method |
|---|-----------|-------------|
| 1 | All 7 files modified correctly | Read each file, verify sections exist |
| 2 | Cross-references pass V1-V5 | Run validation checklist (§7) |
| 3 | No broken markdown formatting | Visual inspection of each file |
| 4 | Version numbers updated | Check CLAUDE.md=3.0, guideline=3.0 |
| 5 | devils-advocate.md unchanged | Diff against original |
| 6 | L1/L2/L3 handoff files written | Check implementer output directory |
| 7 | Git commit clean | `git status` shows no uncommitted changes |

**Gate result:**
- ALL PASS → APPROVE → Phase 9 (Delivery)
- 1-2 FAIL (non-critical) → ITERATE → implementer fixes
- 3+ FAIL → REJECT → re-evaluate approach

---

## 10. Summary

| Item | Value |
|------|-------|
| Pipeline | Simplified Infrastructure (Phase 1 → 6 → 6.V → 9) |
| Teammates | 1 implementer (single, all files) |
| TaskCreate entries | 3 (Task A: core, Task B: agents, Task C: validation) |
| Files modified | 7 |
| Files created | 0 |
| Hooks added | 0 |
| Estimated lines added | ~172 |
| DIA Protocol | v2.0 (LDAP does not exist during implementation) |
| Commit strategy | Single commit (recommended) or per-task |
| Gate criteria | 7 items (§9) |

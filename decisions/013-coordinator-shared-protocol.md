# Decision 013: Coordinator Shared Protocol Design

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 5 existing + 3 new coordinators (D-005) · D-006 F-011  
**Depends on:** Decision 005, Decision 006, Decision 008, Decision 009, Decision 011

---

## 1. Problem Statement

D-006 F-011 identified coordinator boilerplate duplication: all 5 existing coordinators
share ~60-80 lines of identical content (understanding verification, failure handling,
coordinator recovery, Mode 3 fallback, L1 incremental writes).

With D-005 adding 3 new coordinators (architecture, planning, validation), total = 8.
Each `coordinator.md` file is 100-150 lines, of which ~80 lines are boilerplate.

**Duplication cost:**
- 8 coordinators × 80 shared lines = 640 lines of duplicated content
- Any protocol change requires updating ALL 8 files
- Inconsistencies creep in (D-006 found minor wording differences)

**Additionally, D-008, D-009, D-011 introduce new coordinator responsibilities:**
- D-008: Sub-gate evaluation protocol
- D-009: Category-level memory mediation
- D-011: Downstream Handoff section in L2

**Core question:** How to DRY coordinator protocol while preserving per-coordinator
specialization?

---

## 2. Current State: Coordinator File Audit

### 2.1 Shared Sections Across All 5 Coordinators

From code-level audit of all coordinator `.md` files:

| Section | research- | verification- | execution- | testing- | infra-quality- |
|---------|:-:|:-:|:-:|:-:|:-:|
| "Read agent-common-protocol.md" | ✅ | ✅ | ✅ | ✅ | ✅ |
| Workers list | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) |
| "All workers pre-spawned by Lead" | ✅ | ✅ | ✅ | ✅ | ✅ |
| Before Starting Work (TaskGet + message) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Understanding Verification (AD-11) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Communication with Lead | ✅ | ✅ | ✅ | ✅ | ✅ |
| Communication with Workers | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) |
| Failure Handling | ✅ | ✅ | ✅ | ✅ | ✅ |
| Mode 3 Fallback | ✅ | ✅ | ✅ | ✅ | ✅ |
| Coordinator Recovery | ✅ (identical) | ✅ (identical) | ✅ (identical) | ✅ (identical) | ✅ (identical) |
| Output Format (L1/L2/L3) | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) | ✅ (custom) |
| Constraints (no code mod, no Task write) | ✅ (identical) | ✅ (identical) | ✅ (identical) | ✅ (identical) | ✅ (identical) |
| "Write L1 incrementally" | ✅ | ✅ | ✅ | ✅ | ✅ |

### 2.2 Unique Per-Coordinator Content

| Coordinator | Unique Content |
|-------------|---------------|
| **research-coordinator** | Research question distribution by source type, gap identification rounds |
| **verification-coordinator** | Dimension 1:1 mapping, cross-dimension synthesis protocol, verdict categories |
| **execution-coordinator** | Two-stage review dispatch, fix loop rules (max 3 iterations), consolidated report format, spec review→code review ordering |
| **testing-coordinator** | Sequential lifecycle (tester→integrator), Phase 7/8 conditional logic |
| **infra-quality-coordinator** | 4-dimension score aggregation, weighted average formula, cross-dimension re-analysis |

### 2.3 Minor Inconsistencies Found (Code-Level Audit)

| Finding | Files | Issue |
|---------|-------|-------|
| Timeout values differ | research: 20/30min, verification: 15/25min, execution: 30/40min, testing: 20/30min, infra: 15/25min | Intentional (phase-specific) but undocumented |
| Mode 3 block phrasing | 4/5 identical, execution-coordinator adds "Workers respond to whoever messages them" note | Minor wording difference |
| Recovery steps | All 4 steps identical | Perfect duplication — candidate for extraction |

---

## 3. Proposed: Coordinator Shared Protocol Reference

### 3.1 File: `.claude/references/coordinator-shared-protocol.md`

```markdown
# Coordinator Shared Protocol

This protocol covers procedures common to ALL coordinators. Role-specific behavior
(worker types, dimension mapping, review protocols) lives in each coordinator's .md file.

All coordinators MUST:
1. Read agent-common-protocol.md (shared with all agents)
2. Read THIS document (shared with all coordinators)
3. Read their own coordinator .md file (role-specific behavior)

---

## Pre-Spawned Workers
Workers are pre-spawned by Lead. You manage them via SendMessage.
You never spawn workers yourself — Lead handles all teammate creation.

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message Lead with:
- Your understanding of the scope for your category
- How you plan to distribute work across workers
- What output format you'll consolidate into
- Any concerns about scope or worker assignments

## Understanding Verification (AD-11)
Verify each worker's understanding using the Impact Map excerpt from Lead:
- Ask 1-2 probing questions focused on intra-category concerns
- Questions should verify the worker understands their scope AND adjacent impacts
- Escalate to Lead if verification fails after 3 attempts
- Report verification status to Lead (pass/fail per worker)

## Sub-Gate Evaluation (D-008)
Before reporting to Lead for main gate evaluation:
1. Confirm all workers have submitted L1 + L2
2. Complete cross-dimension synthesis (if applicable, per role-specific protocol)
3. Write consolidated L2 with Downstream Handoff section (D-011)
4. Report readiness to Lead

## Category Memory Mediation (D-009)
Workers report memory findings to you via SendMessage (not direct to file).
After consolidation, write to category MEMORY.md:
- Shared Patterns: cross-worker applicable findings
- {Role}-Specific sections: per-worker findings
- Coordinator Notes: cross-dimension observations
Path: ~/.claude/agent-memory/{category}/MEMORY.md

## Downstream Handoff (D-011)
Your L2-summary.md MUST include a "Downstream Handoff" section at the end:
### Downstream Handoff
- Decisions Made (forward-binding): AD-N items
- Risks Identified (must-track): R-N items
- Interface Contracts (must-satisfy): IC-N items
- Constraints (must-enforce): C-N items
- Open Questions (requires resolution): OQ-N items
- Artifacts Produced: L1/L2/L3 paths

## Communication with Lead
- **Receive:** Scope, worker names, Impact Map excerpt, output paths
- **Send:** Consolidated findings, escalations, completion report
- Leader-specific cadence is defined in your coordinator .md file

## Failure Handling
- Worker unresponsive: Send status query at threshold-1. Alert Lead at threshold-2.
  (Thresholds defined per coordinator — see your .md file)
- Cross-dimension conflict: Consolidate conflicting findings, present to Lead for resolution
- Own context pressure: Write L1/L2 immediately, alert Lead (Mode 3 fallback)

## Mode 3 Fallback
If you become unresponsive or report context pressure, Lead takes over worker management
directly. Workers respond to whoever messages them — the transition is seamless from
the worker perspective.

## Coordinator Recovery
If your session is continued from a previous conversation:
1. Read your own L1/L2 files to restore progress context
2. Read team config (`~/.claude/teams/{team-name}/config.json`) for worker names
3. Message Lead for current assignment status and any changes since last checkpoint
4. Reconfirm understanding with Lead before resuming worker management

## Constraints
- No code modification — you coordinate, not implement
- No task creation or updates (Task API is read-only)
- No Edit tool — use Write for L1/L2/L3 only
- Write L1/L2/L3 proactively
- Write L1 incrementally — update L1-index.yaml after each completed worker stage
- Never resolve cross-boundary issues yourself — escalate to Lead
```

### 3.2 Updated Coordinator .md Files (Template)

Each coordinator's `.md` file becomes significantly shorter:

```markdown
---
name: {category}-coordinator
description: |
  {Category} coordinator. Manages {workers}.
  {Category-specific detail}.
  Spawned in Phase {N}. Max 1 instance.
model: opus
permissionMode: default
memory: user
color: {color}
maxTurns: {N}
tools: [Read, Glob, Grep, Write, TaskList, TaskGet, sequential-thinking]
disallowedTools: [TaskCreate, TaskUpdate, Edit, Bash]
---
# {Category} Coordinator

Read and follow:
1. `.claude/references/agent-common-protocol.md` (shared agent procedures)
2. `.claude/references/coordinator-shared-protocol.md` (shared coordinator procedures)

## Workers
- **{worker-1}:** {description}
- **{worker-2}:** {description}

## {Category-Specific Protocol}
{What makes this coordinator unique — dimension mapping, review dispatch, etc.}

## Worker-Specific Communication
{Custom communication patterns for this category}

## Timeouts
- Worker unresponsive: query at {T1}min, alert Lead at {T2}min

## Output Format
- **L1-index.yaml:** {custom}
- **L2-summary.md:** {custom}
- **L3-full/:** {custom}
```

**Estimated reduction per coordinator:** 150 lines → 60-80 lines (50% smaller)

---

## 4. Line Count Impact

| Metric | Before | After |
|--------|:---:|:---:|
| coordinator-shared-protocol.md | 0 | ~100 lines |
| Average coordinator .md | ~110 lines | ~65 lines |
| Total across 8 coordinators | ~880 lines | ~520 + 100 = 620 lines |
| Duplicated boilerplate | ~640 lines | 0 lines |
| Net savings | — | ~260 lines fewer, zero duplication |

---

## 5. Agent Read Cost Analysis (Tmux/Opus-4.6)

**Before DRY:** Each coordinator reads:
- agent-common-protocol.md (162 lines)
- own coordinator .md (110 lines)
- Total: 272 lines

**After DRY:** Each coordinator reads:
- agent-common-protocol.md (162 lines)
- coordinator-shared-protocol.md (100 lines) ← NEW
- own coordinator .md (65 lines)
- Total: 327 lines (+55 lines, +20%)

**Trade-off:** Coordinators read slightly more total text, but:
1. The shared protocol is read ONCE and cached in context
2. The coordinator .md is now focused on role-specific behavior only
3. Protocol updates propagate instantly to all 8 coordinators
4. Within Opus-4.6's 200K context, +55 lines is negligible (~0.01% of budget)

---

## 6. Options

### Option A: Full DRY (Extract shared protocol)
- Create `coordinator-shared-protocol.md`
- Refactor all 8 coordinator .md files to reference it
- Include D-008/D-009/D-011 new responsibilities in shared protocol

### Option B: Partial DRY (Extract only identical blocks)
- Extract only Coordinator Recovery, Mode 3 Fallback, and Constraints
- Keep Understanding Verification in each coordinator (different examples)
- Smaller shared file (~50 lines)

### Option C: No DRY (Keep current structure)
- Duplicate new D-008/D-009/D-011 responsibilities into all 8 files
- Highest maintenance burden but simplest structure

### Option D: Full DRY + Coordinator Base Template (Recommended)
- Create `coordinator-shared-protocol.md` (full shared protocol)
- Define a coordinator template that new coordinators follow
- All 8 coordinators reference the shared protocol
- Template ensures consistency for D-005 new coordinators

---

## 7. User Decision Items

- [ ] Which option? (A / B / C / **D recommended**)
- [ ] Accept 3-file read hierarchy (agent-common → coordinator-shared → own .md)?
- [ ] Accept the shared protocol content per §3.1?
- [ ] Accept the coordinator template per §3.2?
- [ ] Accept timeout values remaining per-coordinator (not standardized)?
- [ ] Accept the line count trade-off (+55 lines per coordinator read)?

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: Coordinator shared protocol — Option [X]
SCOPE:
  - Create .claude/references/coordinator-shared-protocol.md
  - Refactor: research-coordinator.md, verification-coordinator.md,
    execution-coordinator.md, testing-coordinator.md, infra-quality-coordinator.md
  - New D-005 coordinators follow template: architecture-coordinator.md,
    planning-coordinator.md, validation-coordinator.md
CONSTRAINTS:
  - agent-common-protocol.md unchanged (agents, not just coordinators)
  - Per-coordinator unique content preserved in individual .md files
  - Timeout values remain per-coordinator (phase-appropriate)
  - D-008/D-009/D-011 responsibilities in shared protocol, not individual files
PRIORITY: Shared protocol > Existing refactor > New coordinator template
DEPENDS_ON: D-005 (new coordinators), D-008 (sub-gate), D-009 (memory), D-011 (handoff)
```

# Domain 1: executing-plans + subagent-driven-development 원본 분석

> **Date:** 2026-02-07
> **Researcher:** researcher-1
> **Sources:** executing-plans/SKILL.md, subagent-driven-development/SKILL.md, implementer-prompt.md, spec-reviewer-prompt.md, code-quality-reviewer-prompt.md

---

## 1. Execution Model Comparison

### executing-plans (Batch + Human Checkpoint)

| Aspect | Detail |
|--------|--------|
| Model | Linear batch execution |
| Batch size | Default 3 tasks |
| Agent count | 1 (same agent throughout) |
| Context | Accumulated (same context window) |
| Checkpoint | Human reviews between batches |
| Tracking | TodoWrite (mark in_progress → completed) |
| Error handling | Stop immediately on blocker, ask for clarification |
| Entry | Reads plan file, creates TodoWrite, proceeds |
| Exit | Invokes `finishing-a-development-branch` sub-skill |

**Flow:** Load Plan → Create TodoWrite → [Batch of 3: execute → verify → mark complete] → Report → Human Feedback → Next Batch → ... → finishing-a-development-branch

**Strengths:**
- Simple, predictable execution model
- Human stays in loop between batches
- "Review plan critically first" — catches plan issues before execution
- Clear stop conditions (blocker, unclear instruction, verification failure)

**Weaknesses for Agent Teams:**
- Single agent = context pollution across tasks (no fresh context)
- Linear only — no parallel execution
- Human checkpoint every 3 tasks = high latency for large plans
- TodoWrite API = incompatible with Lead-only TaskCreate

### subagent-driven-development (Ephemeral Subagent + Two-Stage Review)

| Aspect | Detail |
|--------|--------|
| Model | Per-task ephemeral subagent dispatch |
| Agent count | 1 implementer + 2 reviewers per task (sequential) |
| Context | Fresh per task (controller provides full text) |
| Checkpoint | Automatic (two-stage review replaces human checkpoint) |
| Tracking | TodoWrite (controller marks on behalf of subagent) |
| Error handling | Q&A before work + fix subagent on failure |
| Entry | Read plan once, extract ALL tasks upfront |
| Exit | Final code-reviewer for entire implementation → finishing-a-development-branch |

**Flow:** Extract All Tasks → [Per Task: Implementer → Spec Review → (fix loop) → Code Quality Review → (fix loop) → Mark Complete] → Final Review → finishing-a-development-branch

**Strengths:**
- Fresh context per task (no pollution)
- Two-stage review catches both spec drift and quality issues
- Controller curates context (no file reading overhead for subagent)
- Subagent can ask questions before and during work
- Fix loop ensures issues are actually resolved

**Weaknesses for Agent Teams:**
- Sequential task execution only ("Never dispatch multiple implementation subagents in parallel")
- Ephemeral subagent = no DIA verification
- TodoWrite API = incompatible
- No file ownership enforcement
- No global-context awareness

---

## 2. Two-Stage Review System (Key Pattern to Preserve)

### Stage 1: Spec Compliance Review (spec-reviewer-prompt.md)

**Purpose:** Verify implementer built EXACTLY what was requested — nothing more, nothing less.

**Core principle:** "Do Not Trust the Report" — reviewer independently reads code, compares to spec.

**3-Axis verification:**
1. **Missing requirements:** Did they implement everything requested?
2. **Extra/unneeded work:** Did they build things not requested? Over-engineer?
3. **Misunderstandings:** Did they interpret requirements differently than intended?

**Output:** ✅ Spec compliant / ❌ Issues found (specific file:line references)

**Critical rule:** "Verify by reading code, not by trusting report."

### Stage 2: Code Quality Review (code-quality-reviewer-prompt.md)

**Purpose:** Verify implementation is well-built (clean, tested, maintainable).

**Prerequisite:** Stage 1 must PASS before Stage 2 begins. "Only dispatch after spec compliance review passes."

**Uses:** superpowers:code-reviewer agent template (code-reviewer.md)

**Input:** WHAT_WAS_IMPLEMENTED, PLAN_OR_REQUIREMENTS, BASE_SHA, HEAD_SHA, DESCRIPTION

**Checks (from code-reviewer.md):**
- Code Quality: separation of concerns, error handling, type safety, DRY, edge cases
- Architecture: design decisions, scalability, performance, security
- Testing: real logic tests (not mocks), edge cases, integration tests, all passing
- Requirements: all met, matches spec, no scope creep, breaking changes documented
- Production Readiness: migration, backward compat, documentation, no obvious bugs

**Output:** Strengths → Issues (Critical/Important/Minor with file:line) → Recommendations → Assessment (Ready to merge? Yes/No/With fixes)

### Order is CRITICAL
```
Implementer completes task
    ↓
Stage 1: Spec Compliance (did they build the RIGHT thing?)
    ↓ (must pass)
Stage 2: Code Quality (did they build it WELL?)
    ↓ (must pass)
Task complete
```

Rationale: No point reviewing code quality if the code doesn't match the spec.

---

## 3. Implementer Prompt Construction (Context Curation)

From `implementer-prompt.md`, the controller provides:

1. **Task Description:** FULL TEXT pasted from plan (subagent does NOT read plan file)
2. **Context:** Scene-setting — where task fits, dependencies, architectural context
3. **Pre-work Q&A:** Explicit invitation to ask questions before starting
4. **Job specification:** Implement → Test (TDD if specified) → Verify → Commit → Self-review → Report
5. **Self-review checklist:** Completeness, Quality, Discipline (YAGNI), Testing

**Key insight:** Controller does the expensive work of curating context. Subagent receives a complete, focused package. This eliminates file reading overhead and ensures consistent context.

**Report format:** What implemented, test results, files changed, self-review findings, issues/concerns.

---

## 4. Task Tracking Mechanism

Both skills use TodoWrite:
- executing-plans: Agent creates TodoWrite at start, marks tasks in_progress/completed
- subagent-driven-development: Controller creates TodoWrite, marks on behalf of subagents

**Agent Teams replacement:** Lead creates tasks via TaskCreate. Implementer teammates read via TaskList/TaskGet but cannot update. Lead updates task status based on teammate [STATUS] reports.

---

## 5. Error Recovery Patterns

### executing-plans
- Blocker mid-batch → STOP immediately, ask for clarification
- Plan has critical gaps → STOP before starting
- Unclear instruction → Ask, don't guess
- Verification fails repeatedly → STOP, report
- Partner updates plan → Return to Review (Step 1)

### subagent-driven-development
- Subagent asks questions → Answer clearly and completely, don't rush
- Reviewer finds issues → Implementer (same subagent) fixes → reviewer re-reviews → repeat until approved
- Subagent fails task → Dispatch FIX subagent with specific instructions (don't fix manually = context pollution)
- Never proceed with unfixed issues
- Never move to next task while review has open issues

### Agent Teams mapping
- Blocker → implementer sends [STATUS] BLOCKED to Lead
- Plan gaps → implementer reports via [STATUS], Lead decides
- Reviewer issues → implementer fixes within ownership boundary, re-dispatches reviewer subagent
- Failed subagent → Lead re-spawns or reassigns
- Context pollution → mitigated by persistent teammate + L1/L2/L3 handoff

---

## 6. Principles to PRESERVE in Agent Teams Version

| # | Principle | Source | Rationale |
|---|-----------|--------|-----------|
| P-1 | Two-stage review (spec → quality) | subagent-driven-dev | Catches both spec drift AND quality issues |
| P-2 | Controller curates context for subagent | subagent-driven-dev | Eliminates file reading overhead |
| P-3 | "Do Not Trust the Report" | spec-reviewer | Independent code verification |
| P-4 | Ordered review (spec BEFORE quality) | code-quality-reviewer | No point checking quality if spec wrong |
| P-5 | Fix loop (reviewer → fix → re-review) | subagent-driven-dev | Issues are actually resolved |
| P-6 | Self-review before handoff | implementer-prompt | First line of defense |
| P-7 | Pre-work Q&A | implementer-prompt | Surface issues before implementation |
| P-8 | Stop on blocker, don't guess | both skills | Prevents cascading errors |
| P-9 | Critical plan review before execution | executing-plans | Catches plan issues early |
| P-10 | Fresh context per task | subagent-driven-dev | No context pollution |
| P-11 | Final whole-project review | subagent-driven-dev | Catches cross-task issues |

## 7. Elements to REPLACE in Agent Teams Version

| # | Element | Replacement | Rationale |
|---|---------|-------------|-----------|
| R-1 | TodoWrite tracking | Lead TaskCreate + teammate TaskList/TaskGet | DIA enforcement requires Lead-only write |
| R-2 | Human checkpoint between batches | Lead Gate 6 evaluation | Automated but more rigorous |
| R-3 | Ephemeral subagent per task | Persistent implementer teammate | DIA requires impact verification |
| R-4 | Single implementer (sequential) | Adaptive 1-4 implementers (parallel capable) | Throughput + file ownership isolation |
| R-5 | Controller = same session agent | Lead = pipeline controller (delegate mode) | Lead never modifies code directly |
| R-6 | `finishing-a-development-branch` chain | Clean Termination (no auto-chain) | Phase 7/8/9 are separate |
| R-7 | Git worktree setup | Shared workspace + file ownership | Agent Teams workspace model |
| R-8 | No DIA pre-work verification | TIER 1 Impact Analysis + LDAP HIGH | Systemic impact awareness |
| R-9 | No global-context awareness | GC-v4 injection via CIP | Pipeline continuity |
| R-10 | Flat task list | Dependency-aware TaskCreate with blockedBy/blocks | Prevents execution ordering issues |
| R-11 | No file ownership enforcement | CLAUDE.md §5 non-overlapping assignment | Concurrent edit prevention |

---

## 8. Integration Points with Agent Teams Pipeline

### Input (from Phase 4 — agent-teams-write-plan)
- GC-v4 with Phase 4 COMPLETE
- 10-section implementation plan (§1 Orchestration Overview, §4 TaskCreate Definitions, §5 Change Specifications)
- File Ownership Map (§3)

### Output (to Phase 7 or verification-pipeline)
- GC-v5 with Phase 6 COMPLETE
- Implementer L1/L2/L3 per task
- Gate 6 record (spec compliance + code quality results)
- Code changes in workspace

### Skill Chain Position
```
brainstorming-pipeline (P1-3) → agent-teams-write-plan (P4) → [plan-validation P5] → execution-pipeline (P6) → [verification-pipeline P7-8] → [delivery P9]
```

# Domain 3: code-reviewer Agent 통합 방안

> **Date:** 2026-02-07
> **Researcher:** researcher-1
> **Sources:** code-reviewer.md (agent), requesting-code-review/SKILL.md, requesting-code-review/code-reviewer.md (template), superpowers-agent-teams-compatibility-analysis.md (G-09)

---

## 1. code-reviewer Agent Capabilities

### Agent Definition (superpowers)
```yaml
name: code-reviewer
description: Senior Code Reviewer — plan alignment + code quality
model: inherit  # uses parent's model (Opus 4.6)
```

### 6 Review Dimensions
| # | Dimension | What It Checks |
|---|-----------|----------------|
| 1 | Plan Alignment | Implementation vs plan: deviations, completeness, justified improvements |
| 2 | Code Quality | Error handling, type safety, naming, maintainability, patterns |
| 3 | Architecture & Design | SOLID, separation of concerns, coupling, scalability, extensibility |
| 4 | Documentation & Standards | Comments, function docs, headers, project conventions |
| 5 | Issue Identification | Critical/Important/Minor categorization, actionable recommendations |
| 6 | Communication Protocol | Deviation handling, plan update suggestions, constructive feedback |

### Output Structure
```
Strengths → Issues (Critical/Important/Minor with file:line) → Recommendations → Assessment (Ready to merge? Yes/No/With fixes)
```

---

## 2. code-reviewer.md Template (Reusable)

### Input Placeholders
| Placeholder | Description |
|-------------|-------------|
| {WHAT_WAS_IMPLEMENTED} | From implementer's report |
| {PLAN_OR_REQUIREMENTS} | Task spec from plan §5 |
| {BASE_SHA} | Git commit before task |
| {HEAD_SHA} | Git commit after task |
| {DESCRIPTION} | Brief task summary |

### Review Checklist (5 areas, 21 items)
1. **Code Quality (5):** Separation of concerns, error handling, type safety, DRY, edge cases
2. **Architecture (4):** Sound design, scalability, performance, security
3. **Testing (4):** Real tests (not mocks), edge cases, integration, all passing
4. **Requirements (4):** All met, matches spec, no scope creep, breaking changes documented
5. **Production Readiness (4):** Migration, backward compat, documentation, no obvious bugs

### Issue Severity
| Severity | Action Required | Examples |
|----------|----------------|---------|
| Critical | Must fix immediately | Bugs, security, data loss, broken functionality |
| Important | Should fix before proceeding | Architecture problems, missing features, test gaps |
| Minor | Nice to have | Style, optimization, documentation |

---

## 3. Compatibility Analysis Status (from G-09)

Compatibility category: **ADAPTABLE** (minor adaptation needed)

Key findings:
- code-reviewer agent is already registered in superpowers
- Lead can dispatch as sub-orchestration during Gate 6
- OR implementer can dispatch as subagent (Sub-Orchestrator capability)
- Template (code-reviewer.md) is reusable without modification
- Only needed change: context injection (add global-context reference)

---

## 4. Integration Architecture: Two-Stage Review in Gate 6

### Option A: Lead Dispatches Both Reviewers (Centralized)

```
Implementer reports [STATUS] COMPLETE
    ↓
Lead dispatches spec-reviewer subagent (Task tool, general-purpose)
    ↓
Spec reviewer reads code, compares to plan §5
    ↓ (PASS)
Lead dispatches code-reviewer subagent (Task tool, superpowers:code-reviewer)
    ↓
Code reviewer checks quality, architecture, testing
    ↓ (PASS)
Lead evaluates combined results → Gate 6 decision
```

**Pros:** Lead has full control, reviewer results go directly to Lead, consistent with Lead's pipeline controller role.
**Cons:** Lead must wait for each reviewer sequentially, higher token usage for Lead's context.

### Option B: Implementer Dispatches Both Reviewers (Delegated — RECOMMENDED)

```
Implementer completes task
    ↓
Implementer dispatches spec-reviewer subagent (Task tool)
    ↓ (issues found → implementer fixes → re-dispatch)
    ↓ (PASS)
Implementer dispatches code-reviewer subagent (Task tool, superpowers:code-reviewer)
    ↓ (issues found → implementer fixes → re-dispatch)
    ↓ (PASS)
Implementer reports [STATUS] COMPLETE with review results to Lead
    ↓
Lead evaluates results + optional cross-verification → Gate 6 decision
```

**Pros:**
- Aligns with Sub-Orchestrator capability (implementer.md explicitly supports this)
- Fix loop stays within implementer (no Lead round-trips for each fix)
- Preserves superpowers' original pattern (controller dispatches reviewers)
- Lead focuses on cross-task and cross-implementer concerns at Gate 6
- Lower token usage for Lead (reviewer results come as summary)

**Cons:**
- Less direct Lead visibility into review process
- Mitigated by: implementer must include review results in [STATUS] COMPLETE report

### Option C: Hybrid (Spec by Implementer, Quality by Lead)

Implementer handles spec compliance (fast iteration), Lead handles quality review (strategic oversight).

**Not recommended:** Splits the review responsibility unnecessarily. If implementer can be trusted for spec review dispatch, they can handle quality review dispatch too. Lead's cross-verification at Gate 6 provides sufficient oversight.

### RECOMMENDATION: Option B (Delegated)

Rationale:
1. Sub-Orchestrator is an existing implementer capability — using it is natural
2. Fix loops are faster within implementer (no Lead round-trips)
3. Lead's role at Gate 6 is cross-verification, not per-task review execution
4. Preserves the superpowers pattern of "controller dispatches then acts on results"
5. Scales better with multiple implementers (Lead doesn't bottleneck on review dispatch)

---

## 5. Spec Compliance Review Adaptation for Agent Teams

### Original: spec-reviewer-prompt.md
- Input: task requirements text + implementer report
- Method: Read actual code, compare to requirements line-by-line
- Output: ✅ compliant / ❌ issues (missing/extra/misunderstanding)

### Agent Teams Adaptation

**New input context:**
```
Task tool (general-purpose):
  description: "Spec compliance review for Task N"
  prompt: |
    You are reviewing whether an implementation matches its specification.

    ## Specification (from Implementation Plan §5)
    {FULL TEXT of plan §5 Change Specification for this task}

    ## Implementer Report
    {From implementer's [STATUS] COMPLETE report}

    ## Files to Inspect
    {List of files from implementer's file ownership}

    ## CRITICAL: Do Not Trust the Report
    [Original spec-reviewer-prompt.md distrust instructions — PRESERVED]

    ## Verification Axes
    1. Missing requirements: spec items not implemented
    2. Extra/unneeded work: features not in spec
    3. Misunderstandings: wrong interpretation of spec

    Verify by reading code, not by trusting report.

    Report: ✅ Spec compliant / ❌ Issues found with file:line references
```

**Changes from original:**
- Input source: plan §5 Change Specification (instead of general plan text)
- File scope: Limited to implementer's file ownership set
- No other structural changes needed — the spec-reviewer pattern is robust

### code-quality-reviewer Adaptation

**Minimal change needed.** The code-reviewer.md template already has all required placeholders:

```
Task tool (superpowers:code-reviewer):
  description: "Code quality review for Task N"
  prompt: |
    (Use code-reviewer.md template)

    WHAT_WAS_IMPLEMENTED: {implementer report}
    PLAN_OR_REQUIREMENTS: {plan §5 spec for this task}
    BASE_SHA: {commit before task}
    HEAD_SHA: {commit after task}
    DESCRIPTION: {task summary}
```

**Only addition:** Include global-context reference so reviewer understands project-level constraints.

---

## 6. Gate 6 Evaluation Flow (Lead Perspective)

### Per-Implementer Gate 6 Evaluation

```
FOR EACH implementer:
  1. Receive [STATUS] COMPLETE from implementer
     - Includes: files changed, test results, spec review result, quality review result, self-review findings
  2. Lead reads implementer's L1-index.yaml + L2-summary.md
  3. Lead cross-verifies:
     a. Spec review result vs plan §5 (spot-check)
     b. Quality review result vs project standards
     c. Test results vs plan §7 (validation checklist)
     d. File ownership compliance (no out-of-boundary modifications)
  4. If issues found:
     - [REJECTED] with specific fix instructions → implementer revises
  5. If approved:
     - Mark task as completed (TaskUpdate)
```

### Cross-Implementer Gate 6 Evaluation (Final)

```
AFTER ALL implementers complete:
  1. Lead reads all implementer L1/L2 summaries
  2. Lead checks for:
     a. Cross-task interface consistency
     b. Integration points between implementer outputs
     c. No conflicting changes (should be prevented by file ownership, but verify)
  3. Optional: Dispatch final code-reviewer for entire implementation
     (preserves subagent-driven-development's "final whole-project review" pattern)
  4. Gate 6 decision: APPROVE / ITERATE / ABORT
  5. On APPROVE: Update GC-v4 → GC-v5 (Phase 6 COMPLETE)
```

### Two-Stage Review → Single Gate Integration

| superpowers (separate stages) | Agent Teams (unified gate) |
|-------------------------------|---------------------------|
| Spec review → quality review → controller marks complete | Spec review → quality review → implementer reports → Lead evaluates at Gate 6 |
| Controller is judge | Lead is judge (with reviewer subagent assistance) |
| Per-task only | Per-task + cross-task (final review) |
| No DIA | Full DIA before implementation begins |
| No file ownership check | File ownership compliance verified at gate |

---

## 7. Output Format: Review Results for Lead

### Implementer's [STATUS] COMPLETE Report (Proposed)

```
[STATUS] Phase 6 | COMPLETE | Task {N}: {summary}

## Implementation Summary
- Files created: {list}
- Files modified: {list}
- Tests added: {count}, all passing

## Spec Compliance Review
- Result: ✅ / ❌
- Reviewer: (subagent, ephemeral)
- Issues found and resolved: {count}
- Final review: PASS

## Code Quality Review
- Result: ✅ / ❌
- Assessment: Ready to merge / With fixes / Not ready
- Critical issues: {count} (all resolved)
- Important issues: {count} (all resolved)
- Minor issues: {count} (noted, deferred if applicable)

## Self-Review Findings
- {any issues found and fixed during self-review}

## Artifacts
- L1: {path}
- L2: {path}
- L3: {path}
```

### Lead's Gate 6 Record (Proposed)

```yaml
phase: 6
result: APPROVED / ITERATE / ABORT
date: YYYY-MM-DD
per_task:
  - task_id: N
    implementer: implementer-{X}
    spec_review: PASS
    quality_review: PASS
    self_test: PASS
    file_ownership: COMPLIANT
cross_task:
  interface_consistency: PASS
  integration_points: VERIFIED
  final_review: PASS / SKIPPED
gate_criteria:
  G6-1: PASS  # All tasks completed
  G6-2: PASS  # All spec reviews passed
  G6-3: PASS  # All quality reviews passed
  G6-4: PASS  # All self-tests passed
  G6-5: PASS  # File ownership compliant
  G6-6: PASS  # Cross-task interfaces consistent
  G6-7: PASS  # No unresolved critical issues
```

---

## 8. Risk Analysis

| Risk | Severity | Mitigation |
|------|----------|------------|
| Reviewer subagent misses critical issue | MEDIUM | Lead cross-verification at Gate 6 + final whole-project review |
| Implementer suppresses negative review results | LOW | Lead can independently dispatch reviewer to spot-check |
| Review loop costs too many tokens | MEDIUM | Cap review iterations (e.g., max 3 per stage) |
| Spec reviewer can't access all necessary files | LOW | Implementer provides file list; reviewer has full Read access |
| Multiple implementers create integration issues | MEDIUM | Cross-task Gate 6 evaluation + optional final review |

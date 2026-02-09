# Architecture Design — execution-pipeline

> **Phase:** 3 (Architecture) | **Architect:** architect-1 | **Date:** 2026-02-07
> **GC:** v2 | **Gate A:** PASS (RC 7/7, LDAP 4/4 STRONG) | **Gate B:** APPROVED

---

## 1. Overview

execution-pipeline은 Agent Teams 파이프라인의 Phase 6(Implementation)을 orchestrate하는 스킬이다. agent-teams-write-plan이 출력한 GC-v4 + 10-section implementation plan을 입력으로 받아, adaptive implementer를 spawn하고, two-stage review를 통합하여 코드 변경을 실행한 후, Gate 6 검증을 거쳐 GC-v5를 출력한다.

### Skill Chain Position

```
brainstorming-pipeline (P1-3) → agent-teams-write-plan (P4) → [plan-validation P5]
    → execution-pipeline (P6) → [verification-pipeline P7-8] → [delivery P9]
```

### Design Scope

- Phase 6 전용 (Implementation only)
- 입력: GC-v4 (Phase 4/5 COMPLETE) + 10-section implementation plan
- 출력: GC-v5 (Phase 6 COMPLETE) + implemented code + Gate 6 record
- Clean Termination (no auto-chain to Phase 7)

---

## 2. Unresolved Questions — Resolution (AD-1)

### UQ-1: Fix Loop Max — Fixed 3 per Stage

**Resolution:** 고정 3회.

**Rationale:**
- 가변 방식은 "complexity를 누가 어떤 기준으로 판단하는가"라는 meta-problem을 도입
- 3회는 spec compliance와 code quality 각각에 충분한 iteration 허용
- 3회 초과가 필요하다면, 이는 plan spec 자체에 근본적 문제가 있다는 신호
- 3회 소진 시: implementer가 Lead에게 [STATUS] BLOCKED 보고 → Lead가 plan revision 또는 ABORT 결정
- Plan revision은 execution-pipeline 범위 밖 (Phase 4 재실행 필요)

### UQ-2: Final Whole-Project Review — Conditional

**Resolution:** Lead 재량에 의한 conditional (mandatory도 optional도 아님).

**Rationale:**
- 단일 implementer → cross-task 검증 불필요 (implementer 내부 순차 실행이 일관성 보장)
- 2+ implementers → Lead가 cross-task evaluation 중 필요 여부 판단
- 판단 기준: inter-implementer interface 수, 변경 범위의 복잡도, cross-task evaluation에서 발견된 concern 유무
- Token overhead: final review ≈ 5-15K tokens — 복잡한 feature에서는 rework 방지 대비 저렴

### UQ-3: Review 조작 방지 — 3-Layer Defense

**Resolution:** 전수 spot-check가 아닌 구조적 3-Layer Defense.

| Layer | Actor | Coverage | Cost |
|-------|-------|----------|------|
| L1: Automated | spec/code-reviewer subagent | 100% (모든 코드) | 0 tokens for Lead |
| L2: Self-report | Implementer [STATUS] COMPLETE | 100% (모든 task) | ~500 tokens/task |
| L3: Spot-check | Lead at Gate 6 | Sampling (risk-proportional) | ~3K tokens/sample |

**추가 메커니즘:**
- L2-summary.md에 reviewer subagent raw output 포함 의무화 → Lead가 원문 확인 가능
- Self-interest alignment: persistent implementer이므로 Phase 7 rework 비용이 자신에게 귀속
- Phase 7 tester safety net: 실제 코드 실행으로 최종 검증

**Spot-check sampling 기준:**
- HIGH risk task (interface 생성, core module 변경) → spot-check 필수
- LOW risk task (config, test 파일) → L1+L2 report 신뢰

### UQ-4: Context Pressure — Pre-Compact Obligation + Per-Task Checkpoint

**Resolution:** CLAUDE.md Pre-Compact Obligation 적용 + 매 task 완료 시 L1/L2/L3 checkpoint.

**Strategy:**
1. Implementer는 매 task 완료 시 L1/L2/L3를 갱신 (not only at ~75%)
2. 복수 task 순차 처리 시, 각 task 완료가 자연스러운 checkpoint
3. CONTEXT_PRESSURE 감지 시: L1/L2/L3 즉시 작성 → [STATUS] CONTEXT_PRESSURE → Lead가 shutdown → re-spawn with L1/L2 injection
4. Re-spawned implementer는 L1/L2에서 완료된 task 확인 → 다음 task부터 재개

---

## 3. Adaptive Spawn Algorithm (AD-2)

LDAP Q1 challenge에서 정밀화된 알고리즘.

### "Independent Cluster" 정의

두 조건을 **모두** 만족하는 task 그룹:
1. **파일 비공유** — group 간 File Ownership이 비중첩 (CLAUDE.md §5)
2. **blockedBy 없음** — group 간 순서 의존성이 없음

blockedBy는 semantic dependency를 의미한다. Task B가 Task A를 blockedBy하면, B는 A의 output을 consume하므로 interface contract이 존재한다. 이런 task들은 같은 implementer가 순차 실행하여 context continuity를 유지해야 한다.

### Algorithm

```
Input: plan §3 (File Ownership Assignment) + plan §4 (TaskCreate Definitions)

Step 1: Extract all tasks with their blockedBy/blocks relationships from §4
Step 2: Build directed dependency graph
Step 3: Compute connected components (undirected) → dependent groups
Step 4: For each component, merge file ownership sets from §3
Step 5: Verify inter-component file sets are non-overlapping
         If overlap found → merge components → re-compute
Step 6: implementer_count = min(connected_component_count, 4)
Step 7: Assign each implementer one connected component
Step 8: Within each component, determine topological execution order

Output: implementer assignments with task lists + file ownership sets
```

### Spawn Count Heuristics

| Connected Components | Implementers | Strategy |
|---------------------|-------------|----------|
| 1 (all tasks dependent) | 1 | Sequential execution, topological order |
| 2-3 | 2-3 | Parallel independent components |
| 4+ | 4 (max) | Merge smallest components until ≤4 |

### DIA Overhead Consideration

- Per implementer: 5-22K tokens (Impact Analysis + LDAP HIGH 2Q)
- 4 implementers worst case: ~88K tokens DIA overhead
- Trade-off: DIA overhead < parallel execution time savings for 6+ independent tasks
- Heuristic: ≤5 tasks with 1-2 components → 1-2 implementers (DIA overhead dominates)

---

## 4. Two-Stage Review Protocol (AD-3)

Option B: Implementer Delegation. LDAP ALTERNATIVE challenge에서 Option A 대비 우월성을 정량적으로 검증 완료.

### Architecture

```
Implementer completes task implementation
    ↓
Self-review (implementer-internal, per implementer.md checklist)
    ↓
Implementer dispatches spec-reviewer subagent (Task tool, general-purpose)
    ↓
    ├── PASS → proceed to Stage 2
    └── FAIL → implementer fixes → re-dispatch (max 3 iterations)
                └── 3x FAIL → [STATUS] BLOCKED, Lead escalation
    ↓
Implementer dispatches code-reviewer subagent (Task tool, superpowers:code-reviewer)
    ↓
    ├── PASS → proceed to completion
    └── FAIL → implementer fixes → re-dispatch (max 3 iterations)
                └── 3x FAIL → [STATUS] BLOCKED, Lead escalation
    ↓
Implementer writes L1/L2/L3 (includes reviewer raw output in L2)
    ↓
[STATUS] Phase 6 | COMPLETE | Task {N}: {summary}
```

### Stage 1: Spec Compliance Review

**Subagent type:** general-purpose (Task tool)
**DIA:** Exempt (read-only, ephemeral, no mutation)

**Prompt template:**
```
You are reviewing whether an implementation matches its specification.

## Specification (from Implementation Plan §5)
{FULL TEXT of plan §5 Change Specification for this task}

## Implementer Report
{From implementer's self-review}

## Files to Inspect
{List of files within implementer's file ownership}

## Verification Principle: Do Not Trust the Report
Verify by reading actual code, not by trusting the implementer's report.

## Verification Axes
1. Missing requirements: spec items not implemented
2. Extra/unneeded work: features not in spec (YAGNI violation)
3. Misunderstandings: wrong interpretation of spec

Report: PASS (spec compliant) / FAIL with file:line references and specific issues
```

### Stage 2: Code Quality Review

**Subagent type:** superpowers:code-reviewer (Task tool)
**Prerequisite:** Stage 1 MUST pass before Stage 2 begins
**DIA:** Exempt (read-only, ephemeral)

**Prompt inputs:**
- WHAT_WAS_IMPLEMENTED: implementer's self-review report
- PLAN_OR_REQUIREMENTS: plan §5 spec for this task
- BASE_SHA: git commit before task (from `git rev-parse HEAD` before implementation)
- HEAD_SHA: git commit after task
- DESCRIPTION: task summary + global-context reference

**Review checklist:** Code Quality (5) + Architecture (4) + Testing (4) + Requirements (4) + Production Readiness (4) = 21 items

### Fix Loop Rules

- Max 3 iterations per stage (spec and quality independently)
- Each iteration: reviewer identifies issues → implementer fixes → reviewer re-reviews
- Implementer fixes only within own file ownership boundary
- If fix requires cross-boundary change → [STATUS] BLOCKED (see AD-4)
- If 3 iterations exhausted without PASS → implementer reports [STATUS] BLOCKED to Lead
- Lead decides: revise plan spec / reassign task / ABORT

### Review Order Enforcement

Spec compliance MUST pass before code quality review begins. Rationale: no point reviewing code quality if the code doesn't match the spec. This order is enforced by the SKILL.md instructions to implementer.

---

## 5. Cross-Boundary Issue Escalation Protocol (AD-4)

LDAP Q2 challenge에서 도출된 4-stage protocol.

### Trigger

Implementer (or its reviewer subagent) discovers an issue in a file outside implementer's ownership boundary.

### Protocol

```
Stage 1: Detection
  Reviewer or implementer identifies issue in file owned by another implementer
  Implementer cannot fix (CLAUDE.md §5: cross-boundary write FORBIDDEN)

Stage 2: Escalation
  Implementer sends to Lead:
  [STATUS] Phase 6 | BLOCKED | Task {N}: {issue description}
  - File: {path} (owned by implementer-{X})
  - Expected: {from spec §5.Y}
  - Actual: {current state}
  - Impact: {how this blocks my task}

Stage 3: Lead Judgment + Propagation
  Lead reads issue, determines root cause:

  Case A — Other implementer deviation:
    Lead → [CONTEXT-UPDATE] to implementer-{X}:
    "Interface in {file} deviates from spec. Fix required."
    Implementer-{X} → [ACK-UPDATE] → fixes → re-runs review → [STATUS] UPDATE
    Lead → unblocks original implementer

  Case B — Plan spec error:
    Lead → bumps GC version (GC-v4.{N})
    Lead → [CONTEXT-UPDATE] to ALL affected implementers with corrected spec
    All affected → [ACK-UPDATE] → resume with corrected spec

Stage 4: Ripple Termination
  Lead verifies:
  - Fix is spec-compliant (spot-check if HIGH risk)
  - Original implementer's re-review passes
  - No further implementers affected
  - If further affected → repeat Stage 3
```

### Ripple Severity by Implementer State

| Other Implementer State | Severity | Lead Action |
|------------------------|----------|-------------|
| Task not yet started | LOW | Deliver correction before work begins |
| Task in progress | MEDIUM | Send [CONTEXT-UPDATE], implementer pauses + fixes |
| Task completed | HIGH | Re-open task, fix, re-review, re-evaluate at Gate 6 |
| Working on next task (previous complete) | HIGH | Cascading fix risk — check if new task depends on old output |

---

## 6. Gate 6 Structure (AD-5)

LDAP Q3 challenge에서 보강된 3-layer defense 기반 gate.

### Per-Task Evaluation

Lead evaluates each implementer's [STATUS] COMPLETE report:

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| G6-1 | Spec review PASS | Read implementer L2 → reviewer raw output |
| G6-2 | Quality review PASS | Read implementer L2 → reviewer raw output |
| G6-3 | Self-test PASS | Read implementer L2 → test execution results |
| G6-4 | File ownership COMPLIANT | Verify changed files ⊆ assigned ownership set |
| G6-5 | L1/L2/L3 artifacts exist | Check file existence |

### Cross-Task Evaluation

After ALL implementers complete:

| # | Criterion | Verification Method |
|---|-----------|-------------------|
| G6-6 | Inter-implementer interface consistency | Lead reads interface files from each implementer, cross-references |
| G6-7 | No unresolved critical issues | Check all [STATUS] BLOCKED resolved |

### Optional: Final Whole-Project Review

Conditional on Lead judgment (UQ-2 resolution):
- Trigger: 2+ implementers AND (complex interfaces OR cross-task concerns found)
- Method: Lead dispatches code-reviewer subagent with full project scope
- Scope: entire implementation (all implementer outputs combined)

### Spot-Check Protocol (L3 Layer)

Lead performs risk-proportional sampling:
- Per implementer: 1 highest-risk task → Read code → compare to spec §5
- Cross-task: Read all inter-implementer interface files directly
- Total: ~6-8 verification points for 4 implementers

### Gate 6 Result

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
  unresolved_issues: NONE
  final_review: PASS / SKIPPED / N/A
gate_criteria:
  G6-1: PASS
  G6-2: PASS
  G6-3: PASS
  G6-4: PASS
  G6-5: PASS
  G6-6: PASS
  G6-7: PASS
iteration: {1-3}
```

### Gate 6 Results

- **APPROVE:** All G6-1~G6-7 PASS → proceed to GC-v5 + Clean Termination
- **ITERATE (max 3):** Specific fix instructions to affected implementer(s) → re-evaluate
- **ABORT:** 3x iteration exceeded OR fundamental plan flaw → report to user

---

## 7. GC-v4 → GC-v5 Delta (AD-6)

### Sections Added

```markdown
## Phase Pipeline Status
- Phase 6: COMPLETE (Gate 6 APPROVED)
- Phase 7: PENDING

## Implementation Results
- Tasks completed: {N}/{total}
- Files created: {list}
- Files modified: {list}
- Implementers used: {count}

## Interface Changes from Phase 4 Spec
- {deviation description, if any — or "None"}

## Gate 6 Record
- Per-task: {summary per implementer}
- Cross-task: {interface consistency result}
- Final review: {PASS / SKIPPED}

## Phase 7 Entry Conditions
- Test targets: {list of files/modules to test}
- Integration points: {list of cross-module interfaces}
- Known risks: {from Gate 6 observations}
```

### Sections Updated

- Phase Pipeline Status: Phase 6 line → COMPLETE
- Decisions Log: append Phase 6 decisions (D-10+)

---

## 8. Clean Termination + Handoff Interface (AD-7)

### Termination Sequence

```
1. Gate 6 APPROVED
2. Update GC-v4 → GC-v5 (add Phase 6 results)
3. Write phase-6/gate-record.yaml
4. Present output summary to user
5. Shutdown all implementers (SendMessage type: "shutdown_request")
6. TeamDelete — clean team coordination files
7. Artifacts preserved in .agent/teams/{session-id}/
```

### Output Summary (presented to user)

```markdown
## execution-pipeline Complete (Phase 6)

**Feature:** {name}
**Complexity:** {level}
**Implementers:** {count} ({names})
**Tasks:** {completed}/{total}

**Code Changes:**
- Files created: {count}
- Files modified: {count}

**Gate 6:** APPROVED (iteration {N})
- Spec compliance: ALL PASS
- Code quality: ALL PASS
- File ownership: COMPLIANT
- Cross-task interfaces: CONSISTENT

**Artifacts:** .agent/teams/{session-id}/
**Global Context:** GC-v5

**Next:** Phase 7 (Testing) — use the verification-pipeline skill.
Input: GC-v5 + implementer artifacts.
```

### Handoff Interface to verification-pipeline

verification-pipeline expects:
- GC-v5 with Phase 6 COMPLETE + Phase 7 Entry Conditions
- Implementer L1/L2/L3 per task (test targets, integration points)
- Gate 6 record (known risks, interface changes)
- Code changes in workspace

---

## 9. SKILL.md Design (AD-8)

### Structure (following precedent skills)

```
Frontmatter: name, description, argument-hint
Introduction paragraph + announce + core flow
When to Use (decision tree)
Dynamic Context (!`shell``)
Phase 6.1: Input Discovery + Validation
Phase 6.2: Team Setup
Phase 6.3: Adaptive Spawn + DIA
Phase 6.4: Task Execution + Review
Phase 6.5: Monitoring + Issue Resolution
Phase 6.6: Gate 6
Phase 6.7: Clean Termination
Cross-Cutting: sequential thinking, error handling, compact recovery
Key Principles
Never list
```

### Frontmatter

```yaml
name: execution-pipeline
description: Use after agent-teams-write-plan (or plan-validation) to execute an implementation plan (Phase 6). Spawns adaptive implementers with DIA v3.0 enforcement, two-stage review, and Gate 6 evaluation. Requires Agent Teams mode and CLAUDE.md v3.0+.
argument-hint: "[session-id or path to implementation plan]"
```

### Dynamic Context Injection

```
**Implementation Plans:**
!`ls docs/plans/*-implementation.md 2>/dev/null; ls docs/plans/*-plan.md 2>/dev/null`

**Previous Pipeline Output:**
!`ls -d .agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Git Status:**
!`cd /home/palantir && git diff --name-only 2>/dev/null | head -20`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS
```

### When to Use Decision Tree

```
Have an implementation plan from agent-teams-write-plan?
├── Working in Agent Teams mode? ─── no ──→ Use /executing-plans (solo)
├── yes
├── GC-v4 with Phase 4 COMPLETE? ── no ──→ Run /agent-teams-write-plan first
├── yes
├── Plan validated (Phase 5)?
│   ├── yes ──→ Use /execution-pipeline
│   └── no ──→ Recommended: run plan-validation first, or proceed at own risk
└── Use /execution-pipeline
```

### Key Design Decisions in SKILL.md

1. **Input validation:** GC-v4 existence + Phase 4/5 COMPLETE + plan file existence + §3/§4 sections
2. **Adaptive spawn:** Connected components algorithm (AD-2)
3. **DIA:** TIER 1 + LDAP HIGH (2Q) — delegated to CLAUDE.md [PERMANENT]
4. **Review:** Two-stage within implementer (AD-3) — spec then quality
5. **Fix loop:** Max 3 per stage, BLOCKED on exhaustion (AD-1 UQ-1)
6. **Cross-boundary:** 4-stage escalation (AD-4)
7. **Gate 6:** Per-task (G6-1~5) + cross-task (G6-6~7) + conditional final review (AD-5)
8. **GC update:** v4 → v5 with Phase 6 results (AD-6)
9. **Termination:** Clean, no auto-chain (AD-7)
10. **Monitoring:** tmux visual (primary, 0 tokens) + TaskList every 15 min (~500 tokens) + L1 on blocker (~2K tokens)

---

## 10. Pattern Preservation Verification

### 11 Patterns PRESERVED from superpowers

| # | Pattern | How Preserved |
|---|---------|--------------|
| P-1 | Two-stage review | Implementer Sub-Orchestrator: spec → quality (AD-3) |
| P-2 | Context curation | Lead injects GC-v4 + task-context via CIP; implementer curates for reviewer subagent |
| P-3 | "Do Not Trust the Report" | Spec-reviewer prompt explicitly includes distrust instruction (AD-3 Stage 1) |
| P-4 | Ordered review | Spec MUST pass before quality begins — enforced in SKILL.md instructions |
| P-5 | Fix loop | Max 3 per stage within implementer (AD-3) |
| P-6 | Self-review | Implementer self-reviews before dispatching reviewers (implementer.md checklist) |
| P-7 | Pre-work Q&A | Implementer's DIA [IMPACT-ANALYSIS] serves as structured pre-work Q&A |
| P-8 | Stop on blocker | [STATUS] BLOCKED protocol (AD-4) |
| P-9 | Critical plan review | DIA Gate A: implementer reviews plan for feasibility before execution |
| P-10 | Fresh context | Each reviewer subagent is ephemeral with task-specific context |
| P-11 | Final whole-project review | Conditional at Gate 6 cross-task (AD-5 UQ-2) |

### 11 Elements REPLACED

| # | Original | Replacement |
|---|---------|-------------|
| R-1 | TodoWrite | Lead TaskCreate (DIA enforcement) |
| R-2 | Human checkpoint | Gate 6 (Lead evaluation) |
| R-3 | Ephemeral implementer | Persistent implementer teammate (DIA verified) |
| R-4 | Sequential only | Adaptive parallel (1-4 implementers) |
| R-5 | Same-session controller | Delegate Lead (never modifies code) |
| R-6 | finishing-a-development-branch chain | Clean Termination |
| R-7 | Git worktree | Shared workspace + file ownership |
| R-8 | No DIA | TIER 1 + LDAP HIGH (2Q) |
| R-9 | No global context | GC-v4 injection via CIP |
| R-10 | Flat task list | Dependency-aware (blockedBy/blocks) |
| R-11 | No file ownership | CLAUDE.md §5 non-overlapping |

---

## 11. Risk Register

| # | Risk | Severity | Mitigation | Residual |
|---|------|----------|------------|----------|
| R-1 | Implementer review result manipulation | MEDIUM | 3-Layer Defense + L2 raw output + Phase 7 safety net | LOW |
| R-2 | Lead context pressure (multi-implementer) | MEDIUM | Option B delegation (58% token savings vs Option A) | LOW |
| R-3 | Cross-boundary interface inconsistency | MEDIUM | 4-stage escalation + Gate 6 cross-task check | LOW |
| R-4 | Fix loop exhaustion (3x) | LOW | Lead escalation → plan revision or ABORT | MINIMAL |
| R-5 | Implementer context pressure (multi-task) | MEDIUM | Per-task L1/L2/L3 checkpoint + CONTEXT_PRESSURE protocol | LOW |
| R-6 | Connected component merge reducing parallelism | LOW | Inherent in dependency structure — accept | MINIMAL |
| R-7 | Final review token overhead | LOW | Conditional (Lead judgment) — skip for simple features | MINIMAL |
| R-8 | Plan spec error discovered during execution | MEDIUM | Case B escalation (AD-4) + GC bump + all-affected update | LOW |

---

## 12. Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Lead (Pipeline Controller)            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ TaskCreate│  │ DIA      │  │ Gate 6   │  │ GC-v5    │   │
│  │ per task  │  │ Verify   │  │ Evaluate │  │ Update   │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
└───────┼──────────────┼──────────────┼──────────────┼─────────┘
        │              │              │              │
   [DIRECTIVE]    [CHALLENGE]    Read L1/L2     Write GC
   +[INJECTION]   [VERIFIED]    Spot-check       v5
        │              │              │              │
┌───────▼──────────────▼──────────────▼──────────────┘
│                  Implementer-{N}
│
│  ┌────────────┐    ┌──────────────────────────────┐
│  │ DIA        │    │ Task Execution                │
│  │ Gate A + B │    │                                │
│  └─────┬──────┘    │  Code → Self-review           │
│        │           │    ↓                           │
│        ▼           │  ┌─────────────┐               │
│   [IMPACT_         │  │spec-reviewer│ (ephemeral)   │
│    VERIFIED]       │  │ subagent    │               │
│        │           │  └──────┬──────┘               │
│        ▼           │         ↓ fix loop (max 3)     │
│   [APPROVED]       │  ┌─────────────┐               │
│        │           │  │code-reviewer│ (ephemeral)   │
│        ▼           │  │ subagent    │               │
│   Execute          │  └──────┬──────┘               │
│                    │         ↓ fix loop (max 3)     │
│                    │  L1/L2/L3 + [STATUS] COMPLETE  │
│                    └────────────────────────────────┘
└──────────────────────────────────────────────────────
```

---

## 13. Implementation Notes for SKILL.md Author

1. **Implementer directive template** must include: GC-v4 full text + task-context (assignment, file ownership, plan §5 spec, acceptance criteria, review instructions)
2. **Review instructions** in task-context should specify: two-stage order, fix loop max 3, reviewer prompt templates, L2 raw output requirement
3. **Monitoring cadence**: tmux visual is zero-cost; TaskList every 15 min is ~500 tokens; only Read L1 on blocker reports
4. **Timeout**: >30 min implementer silence → Lead sends status query; >40 min → escalate
5. **GC-v4 injection** uses IP-001 (Initial Spawn) from task-api-guideline.md §11
6. **Pre-Compact Obligation**: SKILL.md should instruct implementers to write intermediate artifacts proactively, not only at ~75%

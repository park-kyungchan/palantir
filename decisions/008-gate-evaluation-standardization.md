# Decision 008: Gate Evaluation Standardization

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 9 Gates across 6 Skills · D-007 BN-004 identified inconsistency  
**Depends on:** Decision 005, Decision 007

---

## 1. Problem Statement

Each Skill defines gate criteria differently. Lead applies varying rigor across gates,
creating inconsistent quality thresholds. With D-005 expanding to 8 coordinators and
5 new Skills, the gate count will grow from 9 to ~14. Without standardization, gate
evaluation quality will further diverge.

**Core question:** What is the CANONICAL gate evaluation model, and how do we ensure
consistent rigor WITHOUT over-constraining Opus-4.6's judgment?

---

## 2. Current State: Gate Inventory

### 2.1 Existing Gates (9 across 6 Skills)

| Gate | Skill | Evaluator | Current Criteria Format | Evidence Required |
|------|-------|-----------|------------------------|-------------------|
| Gate 0 | brainstorming-pipeline | Lead | "Does PT exist and is it valid?" | PT existence check |
| Gate 1 | brainstorming-pipeline | Lead | "Discovery sufficient for Architecture?" | NL judgment |
| Gate 2 | brainstorming-pipeline | Lead | "Research sufficient?" | NL judgment |
| Gate 3 | brainstorming-pipeline | Lead | "Architecture complete? ADRs documented?" | ADR existence |
| Gate 4 | agent-teams-write-plan | Lead | "Plan has all 10 sections? File ownership non-overlapping?" | Section count + ownership validation |
| Gate 5 | plan-validation-pipeline | Lead + devils-advocate | "Challenge categories scored? Verdict issued?" | Score table + verdict |
| Gate 6 | agent-teams-execution-plan | Lead | "All tasks PASS both review stages?" | Review verdicts |
| Gate 7 | verification-pipeline | Lead | "All acceptance criteria covered?" | Test pass/fail |
| Gate 8 | verification-pipeline | Lead | "Integration conflicts resolved? Cross-boundary tests pass?" | Integration test results |

### 2.2 Inconsistencies Identified

**Problem A: Evidence Granularity Varies**
- Gate 0: Binary check (PT exists or not) — appropriate for trivial gate
- Gate 2: "Research sufficient?" — no minimum evidence count, no coverage threshold
- Gate 5: Score table with explicit categories — most rigorous
- Gate 7: "All acceptance criteria covered?" — rigorous but format undefined

**Problem B: Verdict Taxonomy Varies**
- Gate 5 uses: APPROVE / CONDITIONAL_APPROVE / REJECT
- Gate 6 uses: PASS / FAIL (per task)
- Others use: implicit PASS/FAIL (Lead continues or doesn't)

**Problem C: Failure Recovery Path Varies**
- Gate 5 REJECT: Re-execute Phase 4 (explicitly defined)
- Gate 7 FAIL: Re-assign to testers (implicit)
- Gate 2 FAIL: Add more research tasks (undefined)

**Problem D: No Minimum Evidence Count**
- Lead can pass Gate 2 by reading one researcher's L2 and deciding "sufficient"
- Lead can pass Gate 3 by seeing one ADR exists without reading its content
- No mechanism prevents shallow evaluation

### 2.3 D-005 Impact: New Gates

D-005 introduces 3 new orchestration Skills, each needing gates:

| New Gate | New Skill | Phase | Needs |
|----------|-----------|-------|-------|
| Gate 3a | architecture-orchestration | P3 | Architecture quality across 3 dimensions |
| Gate 4a | planning-orchestration | P4 | Plan quality across 3 dimensions |
| Gate 5a | validation-orchestration | P5 | Challenge verdict across 3 dimensions |

Plus potential sub-gates within coordinators (worker completion checks).

**Total projected gates: ~14 Lead-evaluated + ~8 coordinator-evaluated = ~22 gate events per pipeline run.**

---

## 3. Analysis

### 3.1 Why Standardization is Needed

| Without Standard | Risk |
|-----------------|------|
| Lead passes Gate 2 with minimal evidence | Architecture built on insufficient research → costly rework in P6 |
| Lead passes Gate 3 without reading ADRs | Plan based on vague architecture → implementation conflicts |
| Gate 5 applies one standard, Gate 7 applies another | Similar quality issues caught at different levels of rigor |
| New coordinators invent their own gate criteria | 8 different evaluation philosophies across 8 coordinators |

### 3.2 Why OVER-Standardization is Dangerous

| Over-Constraint | Risk |
|-----------------|------|
| Mandatory checklist with 20+ items per gate | Lead spends more tokens evaluating gates than agents spend working |
| Rigid evidence count requirements | Trivial features penalized with same rigor as complex features |
| Formalized scoring formulas ("Score ≥ 7.5 to pass") | Opus-4.6's nuanced judgment reduced to arithmetic |
| Mandatory re-evaluation on any CONDITIONAL | Prevents pragmatic "proceed with known risk" decisions |

### 3.3 The Balance Point

**Key insight:** Gate evaluation should be TIERED like pipeline complexity (D-001):
- TRIVIAL pipeline: lightweight gates (evidence existence check)
- STANDARD pipeline: moderate gates (evidence sufficiency judgment)
- COMPLEX pipeline: rigorous gates (evidence quality + cross-validation)

This aligns with both D-001 (pipeline tiers) and the Shift-Left philosophy
(invest more in early gates where changes are cheapest).

---

## 4. Proposed: Universal Gate Evaluation Framework

### 4.1 Gate Structure (ALL gates must have)

```
Every gate evaluation by Lead or Coordinator must include:

1. EVIDENCE COLLECTION
   - List all artifacts read for this evaluation
   - Minimum: 1 L1 + 1 L2 per contributing agent

2. CHECKLIST (gate-specific, defined in Skill)
   - Minimum 3, maximum 10 items per gate
   - Each item is a YES/NO question
   - Threshold: ALL must be YES for PASS, ANY NO triggers CONDITIONAL or FAIL

3. VERDICT
   - PASS: All checklist items satisfied. Proceed to next phase.
   - CONDITIONAL_PASS: Minor gaps identified. Proceed with noted risks.
   - FAIL: Critical gaps. Re-execute phase with specific remediation instructions.
   
4. VERDICT JUSTIFICATION
   - 2-3 sentences explaining the verdict
   - If CONDITIONAL: list exactly what is accepted despite gaps
   - If FAIL: list exactly what must change before re-evaluation

5. DOWNSTREAM IMPACT NOTE
   - What the next phase should know about this gate's findings
   - Unresolved items carried forward as explicit risks
```

### 4.2 Gate Severity Tiers (Aligned with D-001)

| Pipeline Tier | Gate Depth | Minimum Evidence | Checklist Length | Typical Token Cost |
|--------------|-----------|-----------------|-----------------|-------------------|
| TRIVIAL | Shallow | 1 L2 per contributor | 3 items | ~500 tokens |
| STANDARD | Moderate | 1 L1 + 1 L2 per contributor | 5 items | ~1500 tokens |
| COMPLEX | Deep | All L1 + L2 + sample L3 per contributor | 7-10 items | ~3000 tokens |

### 4.3 Shift-Left Gate Investment Profile

```
PRE-Phase Gates (G0–G5a):   70-80% of total gate evaluation effort
  → Catching issues here saves 10x vs catching in P6-P8

EXEC-Phase Gates (G6):      15-20% of evaluation effort
  → Review quality directly prevents rework

POST-Phase Gates (G7–G8):   5-10% of evaluation effort
  → By this point, most issues should be resolved
```

### 4.4 Per-Gate Checklist Definitions

#### Gate 0: PT Validation
```
□ PERMANENT Task exists with [PERMANENT] in subject
□ User Intent section is non-empty and unambiguous
□ Codebase Impact Map has at least 1 entry (or is explicitly "new codebase")
```

#### Gate 1: Discovery Sufficiency (P1→P2)
```
□ At least 1 discovery agent (codebase-researcher or external-researcher) completed L2
□ L2 contains file structure analysis OR external source citations
□ Key terms from user intent appear in discovery findings
□ No "INSUFFICIENT_DATA" or equivalent warnings in L1
□ (COMPLEX only) Cross-reference between codebase and external findings
```

#### Gate 2: Research Sufficiency (P2→P3)
```
□ All spawned researchers have submitted L2 reports
□ Research covers all aspects of user intent (not partial)
□ Verification agents (if spawned) have completed with verdicts
□ No WRONG verdicts remain unresolved in verification report
□ (COMPLEX only) External sources cited with URLs for key claims
```

#### Gate 3 / Gate 3a: Architecture Quality (P3→P4)
```
□ At least 1 ADR documented in L2 or L3
□ Component boundaries clearly defined
□ Interface contracts between components specified
□ Risk assessment present (explicit risks, not "no risks found")
□ (D-005) structure/interface/risk dimensions each have L2 output
□ (COMPLEX only) Trade-off analysis for alternative approaches
□ (COMPLEX only) Non-functional requirements addressed (scale, performance)
```

#### Gate 4 / Gate 4a: Plan Quality (P4→P5)
```
□ Plan has all 10 sections (non-negotiable)
□ File ownership is non-overlapping across implementers
□ Interface contracts between implementers defined
□ Task dependencies are acyclic
□ Acceptance criteria are testable (not vague)
□ (D-005) decomposition/interface/strategy dimensions each have L2 output
□ (COMPLEX only) Each task has estimated effort indicator
```

#### Gate 5 / Gate 5a: Validation Verdict (P5→P6)
```
□ All challenge categories evaluated with score
□ Overall verdict issued (APPROVE/CONDITIONAL/REJECT)
□ If CONDITIONAL: specific conditions listed
□ If REJECT: specific remediation instructions provided
□ No CRITICAL severity findings left unaddressed
□ (D-005) correctness/completeness/robustness each scored independently
□ (COMPLEX only) Risk acceptance documented for CONDITIONAL items
```

#### Gate 6: Implementation Quality (P6→P7)
```
□ All implementation tasks have status=completed
□ Both review stages (spec + code) PASSED for each task
□ No review FAIL verdicts remain unresolved
□ File ownership boundaries were respected (no cross-boundary edits)
□ (D-005) contract-reviewer and regression-reviewer verdicts included
□ (COMPLEX only) Integration-relevant interfaces verified working
```

#### Gate 7: Testing Verdict (P7→P8)
```
□ All acceptance criteria from Gate 4 plan have corresponding tests
□ Test pass rate meets threshold (100% for TRIVIAL/STANDARD, 95%+ for COMPLEX)
□ No test with status=FAIL remains unaddressed
□ Coverage assessment: which acceptance criteria are fully/partially/not tested
□ (D-005) unit/contract/regression test dimensions each reported
```

#### Gate 8: Integration Verdict (P8→P9)
```
□ Cross-boundary interfaces tested and working
□ No merge conflicts remain unresolved
□ Integration tests pass (separate from unit tests)
□ (If applicable) Performance within acceptable bounds
□ Downstream delivery readiness confirmed
```

### 4.5 Coordinator Sub-Gates

Coordinators evaluate worker completion BEFORE reporting to Lead for main gate:

```
Coordinator Sub-Gate Protocol:
1. All workers have submitted L1 + L2
2. Cross-dimension synthesis completed (if applicable)
3. Consolidated report written to coordinator's own L2
4. No worker reported BLOCKED or FAILED status
5. Understanding verification passed for all workers
```

This is NOT a formal gate — it's a coordinator readiness check. Lead then performs
the formal gate evaluation using the coordinator's consolidated L2.

---

## 5. Options

### Option A: Full Framework (All gates, all tiers)
- Apply §4 framework to ALL 14+ gates
- Create `gate-evaluation-standard.md` reference document
- Update ALL existing Skills to reference the standard
- Coordinators follow sub-gate protocol

**Pros:** Maximum consistency, predictable quality  
**Cons:** Requires updating all 6 existing Skills + 5 new Skills

### Option B: PRE-Phase Only (Gates 0-5a)
- Apply framework only to PRE-phase gates (G0–G5a)
- EXEC and POST gates keep current format
- Shift-Left investment prioritized

**Pros:** Maximum impact per effort (70-80% of value)  
**Cons:** EXEC/POST gates remain inconsistent

### Option C: Severity Tiers Only (No checklists)
- Implement only the 3-tier depth model (TRIVIAL/STANDARD/COMPLEX)
- Let Lead/Coordinators create ad-hoc checklists within the tier's depth constraint
- Don't pre-define per-gate checklists

**Pros:** Maximum flexibility for Opus-4.6  
**Cons:** Inconsistency remains within tiers

### Option D: Framework + Progressive Adoption (Recommended)
- Create `gate-evaluation-standard.md` with full framework
- Mandate for new Skills (D-005 architecture/planning/validation)
- Existing Skills adopt progressively (next time they're updated)
- Coordinator sub-gate protocol applied immediately to all coordinators

**Pros:** Immediate consistency for new work, gradual migration  
**Cons:** Temporary inconsistency between old and new Skills

---

## 6. Interaction with Other Decisions

| Decision | Interaction with D-008 |
|----------|----------------------|
| D-001 (Pipeline Routing) | Gate depth tiers map 1:1 to pipeline tiers (TRIVIAL/STANDARD/COMPLEX) |
| D-005 (Agent Decomposition) | 3 new Skills need gates → framework provides them pre-defined |
| D-007 (Bottleneck BN-001) | Standardized gates REDUCE Lead's decision burden (checklist vs invention) |
| D-007 (Bottleneck BN-004) | This decision directly resolves BN-004 |
| D-011 (Handoff Protocol) | Gate evaluation includes "Downstream Impact Note" → feeds handoff |
| D-013 (Coordinator Protocol) | Coordinator sub-gate is part of shared protocol |
| Future L2 | `ActionType: PassGate` with `SubmissionCriteria` maps directly to checklist items |

---

## 7. User Decision Items

- [ ] Which option? (A / B / C / **D recommended**)
- [ ] Accept gate severity tiers (Shallow/Moderate/Deep)?
- [ ] Accept Shift-Left investment profile (70-80% PRE, 15-20% EXEC, 5-10% POST)?
- [ ] Accept per-gate checklists as defined in §4.4?
- [ ] Accept coordinator sub-gate protocol per §4.5?
- [ ] Are there missing gates or unnecessary gates?
- [ ] Should CONDITIONAL_PASS require user confirmation (not just Lead judgment)?

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: Gate evaluation standardization — Option [X]
SCOPE:
  - Create .claude/references/gate-evaluation-standard.md
  - Contains: gate structure (5-element), severity tiers, per-gate checklists
  - Mandate for: new D-005 Skills
  - Progressive adoption for: existing Skills
  - Coordinator sub-gate: apply to all coordinator .md files
CONSTRAINTS:
  - AD-15 (no new hooks for gate enforcement)
  - Gate evaluation is NL (Layer-1) — formal enforcement deferred to Layer-2
  - Checklists are minimum floors, not maximum ceilings
  - Opus-4.6 judgment preserved — checklists assist, not replace
PRIORITY: PRE-phase gates > EXEC gates > POST gates
DEPENDS_ON: D-001 (tiers), D-005 (new Skills), D-007 (BN-004 resolution)
```

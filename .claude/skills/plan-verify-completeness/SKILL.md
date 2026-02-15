---
name: plan-verify-completeness
description: |
  [P5·PlanVerify·Completeness] Gap detection and missing element identifier. Checks plan covers all requirements, architecture components have tasks, and no scenarios left unaddressed.

  WHEN: plan domain complete. Plan ready for completeness challenge. Can run parallel with correctness and robustness.
  DOMAIN: plan-verify (skill 2 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), pre-design-validate (original requirements for coverage).
  OUTPUT_TO: orchestration-decompose (if PASS) or plan domain (if FAIL, revision).

  METHODOLOGY: (1) Read plan and original requirements, (2) Build requirement-to-task traceability matrix, (3) Identify requirements without corresponding tasks, (4) Check all architecture components have tasks, (5) Identify untested scenarios and missing error handling.
  OUTPUT_FORMAT: L1 YAML traceability matrix with coverage percentage, L2 markdown gap report.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Completeness

## Execution Model
- **TRIVIAL**: Lead-direct. Quick requirement coverage check.
- **STANDARD**: Spawn analyst. Systematic traceability matrix construction.
- **COMPLEX**: Spawn 2-4 analysts. Divide: requirement coverage vs architecture coverage.

## Methodology

### 1. Load Requirements and Plan
Read pre-design-validate (original requirements) and plan-strategy (implementation plan).

**Context Persistence Note (C-02)**: In COMPLEX pipelines, P0 output may be compacted by the time P5 runs. Lead MUST extract the original requirements from P0 into the analyst's spawn prompt. If PT (Permanent Task) exists, Lead reads requirements from PT metadata. Otherwise, Lead re-reads pre-design-validate L1 from its context.

**DPS — Analyst Spawn Template:**
- **Context**: Paste the ORIGINAL requirements from pre-design-validate L1 (completeness matrix) and L2 (requirements document). If available, paste from PT metadata. Also paste plan-strategy L1 (complete plan with all tasks). Paste design-architecture L1 (components).
- **Task**: "Build requirement-to-task traceability matrix. For each requirement: identify which task(s) implement it. For each architecture component: verify at least 1 task implements it. Identify untested scenarios and missing error handling. Calculate coverage percentages."
- **Constraints**: Read-only. No modifications.
- **Expected Output**: L1 YAML with requirement_coverage, architecture_coverage, uncovered counts. L2 traceability matrix and gap report.

### 2. Build Traceability Matrix

| Requirement | Task(s) | Covered? | Evidence |
|-------------|---------|----------|----------|
| REQ-1: scope item | task-A, task-B | yes | Files: x.md, y.md |
| REQ-2: constraint | -- | no | No task addresses this |

### 3. Check Architecture Coverage
For each design-architecture component:
- Does at least 1 task implement this component?
- Are all interface contracts addressed by tasks?
- Are all risk mitigations included in the plan?

### 4. Identify Missing Scenarios
Check for uncovered situations:
- Error handling: Does each task have error recovery?
- Edge cases: Are boundary conditions addressed?
- Integration: Are cross-task integration steps planned?

### 5. Report Coverage Metrics
- Requirement coverage: tasks/requirements x 100%
- Architecture coverage: implemented components/total components x 100%
- Target: both >=90% for PASS

## Quality Gate
- Traceability matrix complete (every requirement checked)
- Requirement coverage >=90%
- Architecture coverage >=90%
- No critical requirement uncovered

## Output

### L1
```yaml
domain: plan-verify
skill: completeness
status: PASS|FAIL
requirement_coverage: 0
architecture_coverage: 0
uncovered_requirements: 0
uncovered_components: 0
```

### L2
- Traceability matrix with coverage percentages
- Gap report for uncovered requirements
- Missing scenario analysis

---
name: plan-verify-robustness
description: |
  [P5·PlanVerify·Robustness] Edge case and failure mode challenger. Tests implementation plan against edge cases, failure scenarios, security implications, and resource constraints to ensure robustness under adverse conditions.

  WHEN: plan domain complete. Implementation plan ready for robustness challenge. Can run parallel with correctness and completeness.
  DOMAIN: plan-verify (skill 3 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), design-risk (risk assessment for focused challenge).
  OUTPUT_TO: orchestration-decompose (if PASS) or plan domain (if FAIL, for revision).

  METHODOLOGY: (1) Read plan and risk assessment, (2) Generate edge case scenarios per task, (3) Simulate failure modes (what if task X fails?), (4) Check security implications of implementation approach, (5) Verify resource constraints (4-teammate limit, file count limits).
  CLOSED_LOOP: Challenge → Find weaknesses → Report → Plan revision → Re-challenge (max 3 iterations).
  MAX_TEAMMATES: 4.
  OUTPUT_FORMAT: L1 YAML robustness verdict with edge case list, L2 markdown challenge report, L3 detailed failure scenario analysis.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Robustness

## Execution Model
- **TRIVIAL**: Lead-direct. Quick edge case scan.
- **STANDARD**: Spawn analyst. Systematic failure mode and edge case analysis.
- **COMPLEX**: Spawn 2-4 analysts. Divide: failure modes, security, resource constraints.

## Methodology

### 1. Load Plan and Risk Assessment
Read plan-strategy and design-risk outputs.

### 2. Generate Edge Case Scenarios
For each task, brainstorm:
- What if the input is empty/malformed?
- What if a dependency task failed silently?
- What if the file system is in unexpected state?
- What if context window runs out mid-task?

### 3. Simulate Failure Modes
For each task:
- **Task fails completely**: What breaks downstream? Is rollback possible?
- **Task produces partial output**: Can consumers handle incomplete data?
- **Task exceeds resource limits**: Time, context window, API rate limits?

### 4. Security Challenge
Check implementation approach for:
- Sensitive data exposure (files in commits, metadata leaks)
- Permission escalation (agent uses tool not in its profile)
- Input injection (untrusted data in file paths, Bash commands)

### 5. Resource Constraint Verification
Confirm plan operates within system limits:
- Max 4 teammates per execution phase
- Context window budget per agent (~200K tokens)
- File size limits for Read/Write operations
- Git operations won't corrupt repository state

## Quality Gate
- Every task has >=1 edge case scenario analyzed
- Top failure modes have documented recovery
- No unmitigated security concerns
- Resource constraints validated

## Output

### L1
```yaml
domain: plan-verify
skill: robustness
status: PASS|FAIL
edge_cases: 0
failure_modes: 0
security_concerns: 0
resource_issues: 0
findings:
  - task: ""
    type: edge-case|failure|security|resource
    severity: critical|high|medium|low
    mitigation: ""
```

### L2
- Edge case scenarios per task
- Failure mode analysis with recovery plans
- Security assessment and resource validation

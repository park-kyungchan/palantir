---
name: plan-verify-robustness
description: |
  [P5·PlanVerify·Robustness] Edge case and failure mode challenger. Challenges plan against edge cases, failures, security, and resource constraints to ensure robustness under adverse conditions.

  WHEN: plan domain complete. Plan ready for robustness challenge. Can run parallel with correctness and completeness.
  DOMAIN: plan-verify (skill 3 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), design-risk (risk assessment for focused challenge).
  OUTPUT_TO: orchestration-decompose (if PASS) or plan domain (if FAIL, revision).

  METHODOLOGY: (1) Read plan and risk assessment, (2) Generate edge case scenarios per task, (3) Simulate failure modes (what if task X fails?), (4) Check security implications of approach, (5) Verify resource constraints (4-teammate limit, file count limits).
  OUTPUT_FORMAT: L1 YAML robustness verdict with edge case list, L2 markdown challenge report.
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

**DPS — Analyst Spawn Template:**
- **Context**: Paste plan-strategy L1 (execution plan) and design-risk L1 (risk matrix with top RPN items). Include relevant environment constraints: "Opus 4.6 ~200K context, max 4 teammates, tmux Agent Teams."
- **Task**: "Per task: generate edge case scenarios (empty/malformed input, silent dependency failure, unexpected filesystem state, context window exhaustion). Simulate failure modes (complete failure, partial output, resource exceeded). Security check (data exposure, permission escalation, injection). Verify resource constraints (4 teammates, ~200K tokens, file limits)."
- **Constraints**: Read-only. Use sequential-thinking for systematic edge case generation. No modifications.
- **Expected Output**: L1 YAML robustness verdict with edge_cases, failure_modes, findings[]. L2 per-task scenarios, failure analysis, security assessment.

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

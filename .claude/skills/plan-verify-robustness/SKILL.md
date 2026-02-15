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

## Decision Points

### Tier Assessment for Robustness Checking
- **TRIVIAL**: 1-3 tasks, low risk profile (no external dependencies, no data mutations). Lead performs quick edge case scan: "What if this fails? Can we recover?"
- **STANDARD**: 4-8 tasks, moderate risk (some external dependencies, data modifications). Spawn 1 analyst for systematic failure mode analysis.
- **COMPLEX**: 9+ tasks, high risk (external APIs, data migrations, multi-phase execution). Spawn 2-4 analysts divided by concern: failure modes, security, resource constraints.

### Parallel Execution with Other Plan-Verify Skills
Robustness runs in parallel with correctness and completeness:
- **Correctness**: Plan implements the RIGHT things
- **Completeness**: Plan implements ALL things
- **Robustness**: Plan handles BAD things (this skill)

Lead spawns all 3 simultaneously for STANDARD/COMPLEX.

### Risk Focus Selection
Where to focus robustness analysis based on design-risk output:
- **If design-risk identified high-RPN risks**: Focus analysis on tasks that implement risky components. These get deeper edge case coverage.
- **If design-risk was not executed** (TRIVIAL/STANDARD tier): Use generic failure mode checklist. Cover all tasks equally.
- **If design-risk found no significant risks**: Abbreviated robustness check is acceptable. Focus on resource constraints and basic failure recovery.

### Severity Threshold for FAIL
- **FAIL**: Any unmitigated critical or high severity finding
- **Conditional PASS**: Only medium/low severity findings, all with documented mitigations or acceptance rationale
- **PASS**: No findings, or all findings are low severity with trivial mitigation

What makes a finding "unmitigated":
- No rollback strategy exists for the failure scenario
- No error handling is planned for the error type
- No alternative path exists if the primary approach fails
- Resource constraint violation has no workaround

### Edge Case Generation Strategy
Two approaches to generating edge cases:

**Risk-driven** (default when design-risk available):
- Start from identified risks
- Generate scenarios that trigger each risk
- Verify plan has mitigation for each scenario

**Systematic** (when no risk assessment available):
- For each task input: test empty, null, malformed, oversized, missing
- For each dependency: test timeout, error, partial result, stale data
- For each resource: test exhaustion, contention, unavailability

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

#### Edge Case Template Per Task
For task {task_id}:
```
Inputs:
  - Normal: {expected input}
  - Empty: What happens with no input? → {behavior}
  - Malformed: What if input schema is wrong? → {behavior}
  - Oversized: What if input exceeds expected size? → {behavior}

Dependencies:
  - Available: {normal flow}
  - Unavailable: What if dependency task failed? → {recovery}
  - Partial: What if dependency produced incomplete output? → {recovery}
  - Stale: What if dependency output is from a previous run? → {detection}

Resources:
  - Normal: {expected resource usage}
  - Exhausted: What if context window is full? → {behavior}
  - Contention: What if another agent is using same file? → {behavior}
```

#### Common Edge Cases for Pipeline Skills
| Pipeline Stage | Common Edge Case | Typical Mitigation |
|---------------|------------------|-------------------|
| Pre-design | User requirements are ambiguous | Validation forces clarification |
| Design | Architecture conflicts with existing code | Codebase research catches conflicts |
| Plan | Circular dependencies in task graph | Plan-verify-correctness catches cycles |
| Execution | Implementer modifies wrong file | File ownership enforcement |
| Verify | Verify finds issues but no iterations remain | Report partial, continue pipeline |
| Delivery | Git conflict during commit | Delivery-agent resolves or aborts |

### 3. Simulate Failure Modes
For each task:
- **Task fails completely**: What breaks downstream? Is rollback possible?
- **Task produces partial output**: Can consumers handle incomplete data?
- **Task exceeds resource limits**: Time, context window, API rate limits?

#### Failure Mode Simulation Protocol
For each task, simulate these failure categories:

**Complete Failure** (task produces nothing):
- Impact: Which downstream tasks are blocked?
- Recovery: Can the task be retried? (max 3 iterations)
- Fallback: Is there an alternative approach?
- Blast radius: How many other tasks are affected?

**Partial Failure** (task produces incomplete output):
- Impact: Can consumers handle partial data? (graceful degradation)
- Detection: How does the consumer know the data is incomplete?
- Recovery: Retry with narrower scope? Skip incomplete parts?

**Silent Failure** (task appears to succeed but output is wrong):
- Detection: How is incorrect output detected? (tests, review, verification)
- Impact: If undetected, how far does the wrong output propagate?
- Prevention: What checks can catch this before downstream consumption?

**Resource Exhaustion** (task runs out of turns, context, time):
- Detection: maxTurns reached, timeout, context overflow signal
- Recovery: Partial output salvage, task splitting, resource increase
- Prevention: Task complexity estimation in plan-decomposition

#### Failure Propagation Analysis
Map how a single task failure cascades through the dependency graph:
1. Identify the failed task
2. List all tasks that directly depend on it (first-order impact)
3. List tasks that depend on those tasks (second-order impact)
4. Calculate total blast radius (% of plan affected)
5. If blast radius >50%: flag as critical risk, recommend adding redundancy

### 4. Security Challenge
Check implementation approach for:
- Sensitive data exposure (files in commits, metadata leaks)
- Permission escalation (agent uses tool not in its profile)
- Input injection (untrusted data in file paths, Bash commands)

#### Security Review Checklist for Plans
| Security Concern | What to Check | Plan Element |
|-----------------|---------------|-------------|
| Credential exposure | Are API keys, tokens in file content or commits? | Task outputs, git operations |
| Permission escalation | Does any agent use tools beyond its profile? | Agent assignments in plan |
| Input injection | Are untrusted inputs used in Bash commands? | Implementer tasks with user input |
| Data leakage | Does plan expose sensitive data in logs/output? | Logging tasks, output artifacts |
| Race condition | Do parallel tasks modify shared state? | File ownership, shared resources |
| Supply chain | Does plan install unverified dependencies? | External research, package tasks |

#### Security Findings Escalation
- **Critical security finding**: Automatic FAIL regardless of other checks
- **High security finding**: FAIL unless explicit mitigation is in the plan
- **Medium security finding**: Warning, include in L2 but does not block PASS
- **All security findings**: Must be visible to execution-review downstream

### 5. Resource Constraint Verification
Confirm plan operates within system limits:
- Max 4 teammates per execution phase
- Context window budget per agent (~200K tokens)
- File size limits for Read/Write operations
- Git operations won't corrupt repository state

## Failure Handling

### Design-Risk Not Available
- **Cause**: design-risk was not executed (skipped in TRIVIAL/STANDARD tiers)
- **Action**: Use systematic edge case generation instead of risk-driven. Set `risk_source: generic`.
- **Impact**: Robustness check is less focused but still functional.

### Too Many Edge Cases for Analyst Turns
- **Cause**: COMPLEX tier with 15+ tasks x 5+ edge cases each
- **Action**: Prioritize by blast radius (high-impact tasks first). Report completed analysis and flag remaining tasks as unchecked.
- **Routing**: Set `status: PARTIAL`. Pipeline treats as FAIL.

### Unmitigable Risk Found
- **Cause**: A failure scenario has no possible mitigation within current plan
- **Action**: FAIL with specific risk details. Route to plan-strategy for rollback strategy addition, or to design-architecture for architectural change.
- **Example**: "If external API is down, there is no fallback and the feature cannot work" -- design must provide offline fallback.

### Security Finding Requires Plan Restructuring
- **Cause**: Security concern is architectural (e.g., sensitive data flows through public channel)
- **Action**: FAIL with security finding. Route to design-architecture for secure redesign.
- **Never accept**: Security findings as "known risks" without explicit mitigation plan.

### All Scenarios Pass But Plan Has Single Point of Failure
- **Cause**: One critical task with no redundancy affects entire plan
- **Action**: Flag as high severity finding. Recommend adding redundancy (backup task, alternative approach).
- **Impact**: Does not automatically FAIL but strongly recommends plan revision.

## Anti-Patterns

### DO NOT: Test Only Happy Paths
Robustness explicitly means testing UNHAPPY paths. If every edge case analysis concludes "this will work fine," the analysis is insufficiently adversarial.

### DO NOT: Accept "We'll Handle It at Runtime"
Every failure scenario in the plan must have a documented mitigation IN the plan. Deferring failure handling to execution is not mitigation -- it is hoping the problem does not occur.

### DO NOT: Ignore Resource Constraints
The 4-teammate limit, ~200K context window, and maxTurns caps are HARD constraints. Plans that assume unlimited resources will fail at execution.

### DO NOT: Skip Security for Internal Tools
Even internal pipeline tools (.claude/ changes, hook scripts) can have security implications. A malicious hook script or an agent with over-provisioned tools can cause damage.

### DO NOT: Generate Redundant Edge Cases
"Input is null" and "input is undefined" and "input is missing" are the same edge case. Group similar scenarios to avoid wasting analyst turns on variations of the same failure.

### DO NOT: Rate All Findings as Critical
Severity inflation makes triage impossible. Reserve "critical" for genuine plan-breaking issues. "The error message could be better" is low severity, not critical.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-strategy | Complete execution plan | L1 YAML: `phases[].{tasks[], checkpoint}` |
| design-risk | Risk assessment with RPN scores | L1 YAML: `risks[].{description, rpn, mitigation}` |
| plan-decomposition | Task complexity estimates | L1 YAML: `tasks[].{complexity}` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-decompose | Robustness PASS verdict | All 3 plan-verify PASS |
| plan domain | FAIL with edge case/failure findings | Unmitigated critical/high findings |
| design-architecture | Security/architectural FAIL | Security finding requires redesign |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Unmitigated risk | plan-strategy | Risk details + mitigation recommendation |
| Security concern | design-architecture | Security finding + redesign recommendation |
| Analyst incomplete | Self (re-invoke) or Lead | Partial analysis + remaining scope |
| Resource constraint violation | plan-strategy | Constraint details + adjustment needed |

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

---
name: plan-verify
description: |
  [P4·PlanVerify] Unified plan validation: correctness, completeness, robustness. Single analyst reads plan once, checks all 3 dimensions sequentially. Per-dimension tracking for dashboard.

  WHEN: plan domain complete (all 3 skills done). Plan ready for validation challenge.
  DOMAIN: plan-verify (unified). Replaces 3 parallel skills with 1 sequential-dimension check.
  INPUT_FROM: plan-strategy (plan), design-architecture (spec), plan-interface (contracts), pre-design-validate (requirements), design-risk (risks).
  OUTPUT_TO: orchestration-decompose (all PASS) or plan domain (any FAIL, dimension-specific feedback).

  METHODOLOGY: (1) Read plan + design artifacts once, (2) Correctness: task-architecture mapping + constraint compliance, (3) Completeness: requirement traceability + gap detection, (4) Robustness: edge cases + failure modes + resource limits, (5) Per-dimension verdict.
  OUTPUT_FORMAT: L1 YAML per-dimension PASS/FAIL + overall, L2 per-dimension analysis.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify (Unified)

## Execution Model
- **TRIVIAL**: Lead-direct. Quick validation scan across all 3 dimensions.
- **STANDARD**: Spawn 1 analyst. Systematic check of all 3 dimensions in single context.
- **COMPLEX**: Spawn 1 analyst with maxTurns:40. Deep check across all 3 dimensions with module-level granularity.

Note: Previously spawned 3 parallel analysts (one per dimension). Unified approach reads plan ONCE, checks all dimensions in a single ~200K context window. This eliminates redundant artifact loading and inter-dimension context loss.

## Methodology

### 1. Read Plan and Design Artifacts
Load all inputs into a single analyst context:
- **plan-strategy**: Complete execution plan with phases, tasks, checkpoints
- **design-architecture**: Architecture spec with components, responsibilities, dependencies
- **plan-interface**: Interface contracts (producer-consumer data types)
- **pre-design-validate**: Original requirements (completeness matrix + requirements document)
- **design-risk**: Risk assessment with RPN scores and mitigations (if available)

**Context Persistence Note (C-02)**: In COMPLEX pipelines, P0 output may be compacted by the time P4 runs. Lead MUST extract the original requirements from P0 into the analyst's spawn prompt. If PT (Permanent Task) exists, Lead reads requirements from PT metadata. Otherwise, Lead re-reads pre-design-validate L1 from its context.

### 2. Dimension A: Correctness Check

Verify the plan correctly implements the architecture, respects constraints, and has no logical contradictions.

#### 2a. Task-Architecture Mapping
For each implementation task, verify:
- Maps to exactly 1 architecture component
- Implements the correct responsibility (not a different component's job)
- Uses the correct interface contracts

##### Mapping Verification Matrix
| Task ID | Target Component | Component Responsibility | Task Description | Match? | Evidence |
|---------|-----------------|------------------------|-----------------|--------|----------|
| T1 | Auth Module | Handle user authentication | "Implement JWT token service" | YES | JWT is auth mechanism |
| T2 | Data Layer | Manage database access | "Create API endpoints" | NO | API endpoints are presentation, not data |

A NO match indicates a mapping error -- the task is implementing the wrong component's responsibility.

##### Component Coverage Check
After mapping, verify:
- Every architecture component has >=1 mapped task (gaps = plan incompleteness, route to Dimension B)
- No task maps to a non-existent component (phantom component = plan-architecture mismatch)
- No component has >5 tasks mapped to it (over-decomposition = consider merging tasks)

#### 2b. Dependency Chain Verification
Compare plan dependency chains against interface contracts:
- Producer tasks produce what consumer tasks expect
- No missing intermediate tasks
- No dependency on non-existent task output

For each producer-consumer pair:
1. **Identify producer output**: What does the producer task claim to produce?
2. **Identify consumer input**: What does the consumer task expect?
3. **Type check**: Do output types match input types?
4. **Format check**: Are file paths, naming conventions, and data formats compatible?
5. **Timing check**: Can the producer complete before the consumer needs the data?

A chain break occurs when producer doesn't actually produce the claimed output, consumer expects data from a non-existent task, or an intermediate task was removed during planning. Report ALL chain breaks.

#### 2c. Contradiction Detection
Search for logical contradictions across ALL task pairs:

| Category | Example | Severity |
|----------|---------|----------|
| Ownership conflict | Tasks T1 and T3 both modify `auth.ts` | Critical |
| Type mismatch | T1 outputs JSON, T2 expects YAML | High |
| Agent mismatch | Task needs Bash but assigned to analyst | High |
| Timing conflict | T1 depends on T2, but T2 is in a later phase | High |
| Naming inconsistency | T1 calls it "userId", T2 calls it "user_id" | Medium |
| Redundant task | T1 and T4 implement same functionality | Low |

For N tasks, there are N*(N-1)/2 pairs to check. Systematic coverage required for STANDARD/COMPLEX.

#### 2d. Constraint Compliance
Verify plan respects all constraints:
- Max 4 teammates per phase
- File ownership non-overlapping
- Tier classification matches actual task count

#### 2e. Correctness Verdict
- **PASS**: Zero contradictions, zero constraint violations, every task maps to valid component
- **Conditional PASS**: Minor findings (naming, style) that don't affect correctness. Set `correctness: PASS` with warnings.
- **FAIL**: Any ownership conflict, type mismatch, missing mapping, or constraint violation

### 3. Dimension B: Completeness Check

Verify the plan covers ALL requirements, architecture components, and scenarios.

#### 3a. Build Traceability Matrix

| Requirement | Task(s) | Covered? | Evidence |
|-------------|---------|----------|----------|
| REQ-1: scope item | task-A, task-B | yes | Files: x.md, y.md |
| REQ-2: constraint | -- | no | No task addresses this |

##### Coverage Classification
| Status | Meaning | Counts Toward Coverage? |
|--------|---------|------------------------|
| Fully covered | Task(s) implement entire requirement | Yes (100%) |
| Partially covered | Task(s) implement part of requirement | Yes (50%) |
| Indirectly covered | Requirement satisfied by side effect | Yes (100%) but flagged |
| Deferred | Explicitly out of scope | Yes (excluded from denominator) |
| Uncovered | No task addresses this requirement | No |

##### Traceability Quality Criteria
- Every requirement has at least 1 task OR explicit deferral note
- Every task maps to at least 1 requirement (orphan tasks = scope creep)
- Evidence column shows specific files or mechanisms, not vague descriptions
- Multi-requirement tasks flagged (risk of task being too large)

#### 3b. Architecture Coverage
For each design-architecture component:

| Component | Has Task? | Interface Covered? | Risk Mitigated? | Status |
|-----------|-----------|-------------------|-----------------|--------|
| Auth Module | Yes (T1, T2) | Yes (3 contracts) | Yes (session hijack) | COMPLETE |
| Data Layer | Yes (T3) | Partial (1 of 2) | No | GAP |
| API Gateway | No | -- | -- | MISSING |

Cross-reference verification per component:
1. Implementation tasks exist (from plan-decomposition)
2. Interface contracts exist for all component boundaries (from plan-interface)
3. Risk mitigations exist for component-specific risks (from plan-strategy)
4. All three must be present for COMPLETE status

#### 3c. Missing Scenario Identification

| Scenario Type | Check | Common Gaps |
|--------------|-------|-------------|
| Error handling | Task has error recovery approach | Missing rollback on DB write failure |
| Edge cases | Boundary conditions considered | Empty list, null input, max size |
| Integration | Cross-task handoff points tested | Missing integration test task |
| Configuration | Config changes documented | New env vars not in config task |
| Migration | Data format changes have migration plan | Schema change without migration |
| Rollback | Every phase has rollback strategy | Missing rollback for phase 3 |

##### Gap Severity Classification
| Severity | Definition | Impact on PASS/FAIL |
|----------|-----------|---------------------|
| Critical | Core requirement completely uncovered | Automatic FAIL |
| High | Architecture component missing tasks | Automatic FAIL |
| Medium | Scenario partially covered, risk acknowledged | Warning only |
| Low | Nice-to-have scenario not addressed | Information only |

#### 3d. Completeness Verdict
- **Coverage threshold**: Requirement coverage >=90% AND architecture coverage >=90% for PASS
- **Relaxed (with justification)**: >=80% acceptable IF all uncovered items have explicit deferral rationale
- Report: requirement_coverage %, architecture_coverage %, uncovered counts

### 4. Dimension C: Robustness Check

Challenge the plan against edge cases, failures, security, and resource constraints.

#### 4a. Edge Case Generation

**Risk-driven** (default when design-risk available):
- Start from identified risks, generate scenarios that trigger each, verify plan has mitigation

**Systematic** (when no risk assessment available):
- For each task input: test empty, null, malformed, oversized, missing
- For each dependency: test timeout, error, partial result, stale data
- For each resource: test exhaustion, contention, unavailability

##### Edge Case Template Per Task
```
Inputs:
  - Normal: {expected input}
  - Empty: What happens with no input? -> {behavior}
  - Malformed: What if input schema is wrong? -> {behavior}
  - Oversized: What if input exceeds expected size? -> {behavior}

Dependencies:
  - Available: {normal flow}
  - Unavailable: What if dependency task failed? -> {recovery}
  - Partial: What if dependency produced incomplete output? -> {recovery}
  - Stale: What if dependency output is from a previous run? -> {detection}

Resources:
  - Normal: {expected resource usage}
  - Exhausted: What if context window is full? -> {behavior}
  - Contention: What if another agent is using same file? -> {behavior}
```

#### 4b. Failure Mode Simulation
For each task, simulate:

**Complete Failure** (task produces nothing):
- Which downstream tasks are blocked?
- Can the task be retried? (max 3 iterations)
- Is there an alternative approach?
- Blast radius: how many other tasks are affected?

**Partial Failure** (task produces incomplete output):
- Can consumers handle partial data? (graceful degradation)
- How does the consumer know the data is incomplete?
- Retry with narrower scope? Skip incomplete parts?

**Silent Failure** (task appears to succeed but output is wrong):
- How is incorrect output detected? (tests, review, verification)
- If undetected, how far does the wrong output propagate?
- What checks can catch this before downstream consumption?

**Resource Exhaustion** (task runs out of turns, context, time):
- Detection: maxTurns reached, timeout, context overflow signal
- Recovery: partial output salvage, task splitting, resource increase
- Prevention: task complexity estimation in plan-decomposition

##### Failure Propagation Analysis
Map how a single task failure cascades through the dependency graph:
1. Identify the failed task
2. List all tasks that directly depend on it (first-order impact)
3. List tasks that depend on those tasks (second-order impact)
4. Calculate total blast radius (% of plan affected)
5. If blast radius >50%: flag as critical risk, recommend adding redundancy

#### 4c. Security Challenge

| Security Concern | What to Check | Plan Element |
|-----------------|---------------|-------------|
| Credential exposure | API keys, tokens in file content or commits? | Task outputs, git operations |
| Permission escalation | Agent uses tools beyond its profile? | Agent assignments in plan |
| Input injection | Untrusted inputs used in Bash commands? | Implementer tasks with user input |
| Data leakage | Sensitive data exposed in logs/output? | Logging tasks, output artifacts |
| Race condition | Parallel tasks modify shared state? | File ownership, shared resources |
| Supply chain | Unverified dependencies installed? | External research, package tasks |

Security findings escalation:
- **Critical**: Automatic FAIL regardless of other checks
- **High**: FAIL unless explicit mitigation is in the plan
- **Medium**: Warning, include in L2 but does not block PASS

#### 4d. Resource Constraint Verification
Confirm plan operates within system limits:
- Max 4 teammates per execution phase
- Context window budget per agent (~200K tokens)
- File size limits for Read/Write operations
- Git operations won't corrupt repository state

#### 4e. Robustness Verdict
- **FAIL**: Any unmitigated critical or high severity finding
- **Conditional PASS**: Only medium/low severity findings with documented mitigations
- **PASS**: No findings, or all findings are low severity with trivial mitigation

### 5. Produce Per-Dimension Verdicts
- Each dimension independently PASS, Conditional PASS, or FAIL
- Overall = AND of all 3 dimensions (Conditional PASS counts as PASS)
- FAIL includes dimension-specific feedback for plan revision
- Every verdict must cite specific evidence (task IDs, requirement references)

## Decision Points

### Tier Assessment (Unified)
- **TRIVIAL**: 1-3 tasks, 1-3 requirements, low risk. Lead performs all 3 dimension checks sequentially. Quick enough to not need agent spawn.
- **STANDARD**: 4-8 tasks, 4-10 requirements, moderate risk. Spawn 1 analyst. Systematic check of all 3 dimensions with matrices and per-task analysis.
- **COMPLEX**: 9+ tasks, 10+ requirements, high risk (external dependencies, data mutations). Spawn 1 analyst with maxTurns:40. Deep check with module-level granularity across all 3 dimensions.

### Verification Depth Selection
| Depth | Tier | Correctness | Completeness | Robustness |
|-------|------|-------------|--------------|------------|
| Surface | TRIVIAL | Task-component name matching | Requirement list scan | Quick "what if" per task |
| Contract | STANDARD | + dependency chain + contradiction pairs | + traceability matrix + architecture coverage | + failure mode simulation + security checklist |
| Deep | COMPLEX | + data type flow + implicit assumptions | + gap severity + cross-reference verification | + propagation analysis + resource constraints |

### PASS vs FAIL Thresholds (Per Dimension)
**Correctness**:
- PASS: Zero contradictions, zero constraint violations
- Conditional PASS: Minor findings (naming, style) that don't affect correctness
- FAIL: Ownership conflict, type mismatch, missing mapping, constraint violation

**Completeness**:
- PASS: Requirement coverage >=90% AND architecture coverage >=90%
- Conditional PASS: >=80% with explicit deferral rationale for all gaps
- FAIL: Coverage below threshold or critical requirement uncovered

**Robustness**:
- PASS: No findings or all low severity
- Conditional PASS: Medium/low findings with documented mitigations
- FAIL: Any unmitigated critical or high severity finding

### Risk Focus Selection (Robustness Dimension)
- **design-risk with high-RPN risks**: Focus on tasks implementing risky components
- **design-risk not executed** (TRIVIAL/STANDARD): Use systematic edge case checklist
- **design-risk found no significant risks**: Abbreviated robustness check, focus on resource constraints

### Coverage Threshold Decision (Completeness Dimension)
- **Strict (default)**: >=90% for both requirement and architecture coverage
- **Relaxed (with justification)**: >=80% acceptable IF uncovered items are explicitly deferred in pre-design-validate output

### DPS Template
For STANDARD/COMPLEX tiers, construct the delegation prompt:
- **Context**: Paste plan-strategy L1+L2, design-architecture L1, plan-interface L1, pre-design-validate L1, design-risk L1 (if available). Include environment constraints: "Opus 4.6 ~200K context, max 4 teammates, tmux Agent Teams."
- **Task**: "Validate the plan across 3 dimensions: (A) Correctness -- verify each task correctly implements its architecture component, check dependency chains against interface contracts, detect contradictions across all task pairs, verify constraint compliance. (B) Completeness -- build requirement-to-task traceability matrix, check architecture component coverage, identify missing scenarios and error handling gaps. Calculate coverage percentages. (C) Robustness -- generate edge case scenarios per task, simulate failure modes (complete/partial/silent/resource), check security implications, verify resource constraints (4 teammates, ~200K tokens, file limits). Report per-dimension PASS/FAIL with evidence."
- **Constraints**: Read-only analysis. No modifications. All verdicts must cite specific evidence (task IDs, requirement references). Use sequential-thinking for systematic edge case generation.
- **Expected Output**: L1 YAML with correctness/completeness/robustness verdicts. L2 per-dimension analysis with mapping matrices, traceability matrix, and edge case scenarios.
- **Delivery**: Upon completion, send L1 summary to Lead via SendMessage. Include: status (PASS/FAIL), files changed count, key metrics. L2 detail stays in agent context.

## Failure Handling

### Critical Contradiction Found (Correctness)
- **Action**: Set `correctness: FAIL`. Report ALL contradictions (not just the first).
- **Routing**: Route to plan domain for revision. Include specific fix recommendations per contradiction.
- **Priority**: Ownership conflicts and type mismatches are blocking. Naming inconsistencies are non-blocking.

### Architecture Spec Missing or Incomplete
- **Cause**: design-architecture didn't produce component structure for all modules
- **Action**: Verify against available components. Flag unverifiable tasks with `status: SKIP`.
- **Routing**: If >30% of tasks are unverifiable, route back to design-architecture.

### Interface Contracts Not Available
- **Cause**: plan-interface didn't complete (partial output)
- **Action**: Skip dependency chain verification for missing contracts. Set `dependency_check: partial`.
- **Impact**: Correctness verdict is degraded but still useful for mapping and contradiction checks.

### Requirements Not Available (Context Loss)
- **Cause**: P0 requirements compacted from context, no PT, no saved output
- **Action**: Set `completeness: FAIL` with reason "requirements unavailable"
- **Routing**: Route to Lead for recovery. Lead must restore requirements before completeness can run.
- **Prevention**: Always use PT metadata for requirements persistence.

### Coverage Below Threshold (<90%)
- **Action**: Set `completeness: FAIL`. Report ALL uncovered requirements with gap details.
- **Routing**: Route to plan-decomposition for additional task creation.
- **Include**: Specific recommendations per uncovered requirement.

### Architecture Components Have No Tasks
- **Action**: Critical FAIL on completeness. Missing components mean incomplete implementation.
- **Routing**: Route to plan-decomposition for task creation for missing components.

### Design-Risk Not Available (Robustness)
- **Cause**: design-risk was not executed (skipped in TRIVIAL/STANDARD tiers)
- **Action**: Use systematic edge case generation instead of risk-driven. Set `risk_source: generic`.
- **Impact**: Robustness check is less focused but still functional.

### Unmitigable Risk Found
- **Cause**: A failure scenario has no possible mitigation within current plan
- **Action**: Set `robustness: FAIL` with specific risk details.
- **Routing**: Route to plan-strategy for rollback strategy, or design-architecture for architectural change.

### Security Finding Requires Plan Restructuring
- **Cause**: Security concern is architectural (e.g., sensitive data flows through public channel)
- **Action**: Set `robustness: FAIL` with security finding. Route to design-architecture for redesign.
- **Never accept**: Security findings as "known risks" without explicit mitigation plan.

### Analyst Exhausted Turns
- **Cause**: COMPLEX tier with deep analysis across all 3 dimensions
- **Action**: Report findings so far. Set `overall: PARTIAL`. Include which dimensions/checks were NOT completed.
- **Routing**: PARTIAL is treated as FAIL for pipeline continuation. Lead may re-invoke with focused scope.

### Orphan Tasks Detected (Task Without Requirement)
- **Severity**: Medium (doesn't cause FAIL by itself)
- **Action**: Flag in L2 findings. Orphan tasks indicate scope creep or decomposition error.

### All Checks Pass But Plan Has Single Point of Failure
- **Action**: Flag as high severity robustness finding. Recommend adding redundancy.
- **Impact**: Does not automatically FAIL but strongly recommends plan revision.

### All Checks Pass But Plan Feels Wrong
- **Cause**: Automated checks pass but analyst has qualitative concerns
- **Action**: Include qualitative concerns in L2 with `severity: low`. Don't FAIL on qualitative-only concerns.

## Anti-Patterns

### DO NOT: Fix the Plan During Verification
Verification is read-only. If you find a problem, REPORT it -- don't propose a fix in the verification output. Fixing is plan domain's job. Verification that fixes is verification that rubber-stamps.

### DO NOT: Verify Only the Happy Path
Correctness means the plan works when everything goes RIGHT. But contradictions often hide in error paths and edge cases. Robustness explicitly tests UNHAPPY paths. If every edge case concludes "this will work fine," the analysis is insufficiently adversarial.

### DO NOT: Accept Ambiguous Task Descriptions
If a task description is vague enough that it COULD implement two different components, that's a mapping error. Flag it -- ambiguity causes implementation drift.

### DO NOT: Accept Vague Coverage Claims
"Task T1 generally covers REQ-3" is not adequate traceability. The matrix must show specific files or mechanisms that implement the requirement.

### DO NOT: Verify Completeness Without Original Requirements
Reconstructing requirements from memory or task descriptions is circular verification. Always use the original pre-design-validate output.

### DO NOT: Ignore Architecture Coverage
Requirement coverage alone is insufficient. A plan can cover all requirements but miss an architecture component (e.g., requirements don't mention "logging" but architecture has a logging component).

### DO NOT: Count Deferred Requirements as Gaps
Requirements explicitly marked "out of scope" in pre-design-validate are NOT gaps. Exclude them from the coverage denominator.

### DO NOT: Accept "We'll Handle It at Runtime"
Every failure scenario must have a documented mitigation IN the plan. Deferring failure handling to execution is hoping the problem does not occur.

### DO NOT: Ignore Resource Constraints
The 4-teammate limit, ~200K context window, and maxTurns caps are HARD constraints. Plans assuming unlimited resources will fail at execution.

### DO NOT: Skip Security for Internal Tools
Even internal pipeline tools (.claude/ changes, hook scripts) can have security implications.

### DO NOT: Generate Redundant Edge Cases
"Input is null" and "input is undefined" and "input is missing" are the same edge case. Group similar scenarios to avoid wasting analyst turns.

### DO NOT: Rate All Findings as Critical
Severity inflation makes triage impossible. Reserve "critical" for genuine plan-breaking issues.

### DO NOT: Ignore Constraint Violations for TRIVIAL Tiers
Even TRIVIAL plans must respect the 4-teammate limit and file ownership rules. These are platform constraints, not complexity-dependent.

### DO NOT: Stop at First Failure
Find ALL issues across all 3 dimensions. Multiple findings in a single verification run save pipeline iterations (fix all at once rather than fix-verify-fix-verify).

### DO NOT: Check Correctness Without Architecture Reference
Correctness is defined as "plan matches architecture." Without the architecture spec, there's no reference to check against. Route back to design -- don't verify against assumptions.

### DO NOT: Run Verification Before Plan is Final
The plan must be complete (all 3 plan domain skills done: decomposition, interface, strategy) before verification makes sense. Checking an in-progress plan finds false gaps.

### DO NOT: Accept <90% Coverage Without Justification
The 90% threshold exists because missing even 1 critical requirement can cause pipeline failure. Every uncovered item needs explicit justification for deferral.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-strategy | Complete execution plan | L1 YAML: `phases[].{tasks[], parallel, checkpoint}` |
| design-architecture | Architecture specification | L1 YAML: `components[].{name, responsibility, dependencies[]}` |
| plan-interface | Interface contracts | L1 YAML: `contracts[].{producer, consumer, data_type}` |
| pre-design-validate | Original requirements | L1 YAML: `completeness_matrix`, L2: requirements document |
| design-risk | Risk assessment with RPN scores | L1 YAML: `risks[].{description, rpn, mitigation}` |
| PT metadata | Persisted requirements (if available) | Task metadata with requirements key |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-decompose | Validated plan (all 3 dimensions PASS) | All dimensions PASS or Conditional PASS |
| plan domain | Dimension-specific failure feedback | Any dimension FAIL |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Correctness FAIL (contradictions) | plan-decomposition / plan-strategy | All findings with severity + fix recommendations |
| Correctness FAIL (architecture missing) | design-architecture | List of unverifiable tasks |
| Correctness FAIL (contracts missing) | plan-interface | List of missing contracts |
| Completeness FAIL (coverage gaps) | plan-decomposition | Uncovered requirements + recommendations |
| Completeness FAIL (requirements lost) | Lead for recovery | Error reason, recovery instructions |
| Completeness FAIL (missing components) | plan-decomposition | Missing component list |
| Robustness FAIL (unmitigated risk) | plan-strategy | Risk details + mitigation recommendation |
| Robustness FAIL (security concern) | design-architecture | Security finding + redesign recommendation |
| Robustness FAIL (resource constraints) | plan-strategy | Constraint details + adjustment needed |
| Analyst incomplete | Self (re-invoke) or Lead | Partial analysis + remaining scope |

## Quality Gate
- All 3 dimensions evaluated with evidence
- Every PASS/FAIL verdict cites specific evidence (task IDs, requirement references)
- Correctness: zero ownership conflicts, zero type mismatches, all constraints satisfied
- Completeness: traceability matrix complete, requirement coverage >=90%, architecture coverage >=90%
- Robustness: every task has >=1 edge case analyzed, top failure modes have recovery, no unmitigated security concerns
- Overall verdict = AND of 3 dimensions (Conditional PASS counts as PASS)

## Output

### L1
```yaml
domain: plan-verify
skill: verify
correctness: PASS|FAIL
completeness: PASS|FAIL
robustness: PASS|FAIL
overall: PASS|FAIL
requirement_coverage: 0
architecture_coverage: 0
edge_cases: 0
findings:
  - dimension: correctness|completeness|robustness
    type: mapping|dependency|contradiction|constraint|coverage|gap|edge-case|failure|security|resource
    severity: critical|high|medium|low
    description: ""
    evidence: ""
```

### L2
Per-dimension analysis:
- Correctness: Task-architecture mapping matrix, dependency chain verification, contradiction report, constraint compliance
- Completeness: Traceability matrix with coverage percentages, architecture coverage table, gap report with severity
- Robustness: Edge case scenarios per task, failure mode analysis with recovery plans, security assessment, resource validation

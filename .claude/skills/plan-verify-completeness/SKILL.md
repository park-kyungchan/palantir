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

## Decision Points

### Tier Assessment for Completeness Checking
- **TRIVIAL**: 1-3 requirements, 1-2 architecture components. Lead checks coverage directly by listing each requirement and its task.
- **STANDARD**: 4-10 requirements, 3-5 components. Spawn 1 analyst for systematic traceability matrix construction.
- **COMPLEX**: 10+ requirements, 6+ components. Spawn 2-4 analysts: one for requirement coverage, another for architecture coverage.

### Parallel Execution with Other Plan-Verify Skills
Completeness runs in parallel with correctness and robustness. Each checks a different property:
- **Correctness**: Plan implements the RIGHT things (spec compliance)
- **Completeness**: Plan implements ALL things (coverage)
- **Robustness**: Plan handles BAD things (failure resilience)

Lead spawns all 3 simultaneously for STANDARD/COMPLEX. For TRIVIAL, Lead runs sequentially.

### Coverage Threshold Decision
- **Strict (default)**: Requirement coverage >=90% AND architecture coverage >=90% for PASS
- **Relaxed (with justification)**: Requirement coverage >=80% acceptable IF all uncovered items are documented with explicit deferral rationale
- **When to relax**: When uncovered requirements are explicitly marked as "future scope" or "out of scope" in pre-design-validate output

### Completeness Scope Decision
What counts as "covered":
- **Direct coverage**: A task explicitly implements the requirement
- **Indirect coverage**: A task's side effects satisfy the requirement (e.g., "API logging" is covered by a middleware task that logs all requests)
- **Partial coverage**: A task addresses part of a requirement but not all (counts as 50% coverage for that requirement)
- **Deferred coverage**: Requirement explicitly marked as out of scope (counts as covered for PASS/FAIL but flagged in L2)

### Context Persistence Challenge (C-02)
In long pipelines, P0 requirements may be compacted from Lead's context by P5:
- **If PT exists**: Lead reads requirements from PT metadata (most reliable)
- **If PT doesn't exist**: Lead re-reads pre-design-validate output from saved plans
- **If neither available**: FAIL with reason "cannot verify completeness without original requirements" -- route to Lead for recovery
- **Critical**: Always pass the FULL original requirements to the analyst. Abbreviated requirements cause false positives (uncovered requirements missed because they weren't in the analyst's context).

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

#### Traceability Matrix Quality Criteria
A good traceability matrix has:
- Every requirement has at least 1 task OR explicit deferral note
- Every task maps to at least 1 requirement (orphan tasks = scope creep)
- Evidence column shows specific file(s) or mechanism, not vague descriptions
- Multi-requirement tasks are flagged (risk of task being too large)

#### Coverage Classification
| Status | Meaning | Counts Toward Coverage? |
|--------|---------|------------------------|
| Fully covered | Task(s) implement entire requirement | Yes (100%) |
| Partially covered | Task(s) implement part of requirement | Yes (50%) |
| Indirectly covered | Requirement satisfied by side effect | Yes (100%) but flagged |
| Deferred | Explicitly out of scope | Yes (excluded from denominator) |
| Uncovered | No task addresses this requirement | No |

### 3. Check Architecture Coverage
For each design-architecture component:
- Does at least 1 task implement this component?
- Are all interface contracts addressed by tasks?
- Are all risk mitigations included in the plan?

#### Architecture Gap Detection
| Component | Has Task? | Interface Covered? | Risk Mitigated? | Status |
|-----------|-----------|-------------------|-----------------|--------|
| Auth Module | Yes (T1, T2) | Yes (3 contracts) | Yes (session hijack) | COMPLETE |
| Data Layer | Yes (T3) | Partial (1 of 2) | No | GAP |
| API Gateway | No | -- | -- | MISSING |

- **COMPLETE**: Component fully represented in plan
- **GAP**: Component partially represented -- specific elements missing
- **MISSING**: Component has no corresponding tasks at all (critical failure)

#### Cross-Reference Verification
For each architecture component, verify:
1. Implementation tasks exist (from plan-decomposition)
2. Interface contracts exist for all component boundaries (from plan-interface)
3. Risk mitigations exist for component-specific risks (from plan-strategy)
4. All three must be present for COMPLETE status

### 4. Identify Missing Scenarios
Check for uncovered situations:
- Error handling: Does each task have error recovery?
- Edge cases: Are boundary conditions addressed?
- Integration: Are cross-task integration steps planned?

#### Missing Scenario Checklist
For each task, verify these scenario types are addressed:

| Scenario Type | Check | Common Gaps |
|--------------|-------|-------------|
| Error handling | Task has error recovery approach | Missing rollback on DB write failure |
| Edge cases | Boundary conditions considered | Empty list, null input, max size |
| Integration | Cross-task handoff points tested | Missing integration test task |
| Configuration | Config changes documented | New env vars not in config task |
| Migration | Data format changes have migration plan | Schema change without migration |
| Rollback | Every phase has rollback strategy | Missing rollback for phase 3 |

#### Gap Severity Classification
| Severity | Definition | Impact on PASS/FAIL |
|----------|-----------|---------------------|
| Critical | Core requirement completely uncovered | Automatic FAIL |
| High | Architecture component missing tasks | Automatic FAIL |
| Medium | Scenario partially covered, risk acknowledged | Warning, does not FAIL alone |
| Low | Nice-to-have scenario not addressed | Information only |

### 5. Report Coverage Metrics
- Requirement coverage: tasks/requirements x 100%
- Architecture coverage: implemented components/total components x 100%
- Target: both >=90% for PASS

## Failure Handling

### Requirements Not Available (Context Loss)
- **Cause**: P0 requirements compacted from context, no PT, no saved output
- **Action**: Set `status: FAIL` with reason "requirements unavailable for completeness check"
- **Routing**: Route to Lead for recovery. Lead must restore requirements before completeness can run.
- **Prevention**: Always use PT metadata for requirements persistence

### Coverage Below Threshold (<90%)
- **Action**: Set `status: FAIL`. Report ALL uncovered requirements with gap details.
- **Routing**: Route to plan domain (plan-decomposition) for additional task creation.
- **Include**: Specific recommendations for each uncovered requirement (which component should address it, estimated task complexity).

### Architecture Components Have No Tasks
- **Action**: Critical FAIL. Missing components mean incomplete implementation.
- **Routing**: Route to plan-decomposition for task creation for missing components.
- **Impact**: Cannot proceed to orchestration without full component coverage.

### Analyst Exhausted Turns
- **Action**: Report partial traceability matrix. Set `status: PARTIAL`.
- **Routing**: PARTIAL treated as FAIL for pipeline. Lead may re-invoke with focused scope (only unchecked requirements).

### Orphan Tasks Detected (Task Without Requirement)
- **Severity**: Medium (doesn't cause FAIL by itself)
- **Action**: Flag in L2 findings. Orphan tasks indicate scope creep or decomposition error.
- **Recommendation**: Either map to an existing requirement or remove the task.

## Anti-Patterns

### DO NOT: Count Deferred Requirements as Gaps
Requirements explicitly marked "out of scope" in pre-design-validate are NOT gaps. Exclude them from the coverage denominator. Flagging deferred items as gaps inflates the gap count unnecessarily.

### DO NOT: Accept Vague Coverage Claims
"Task T1 generally covers REQ-3" is not adequate traceability. The matrix must show specific files or mechanisms that implement the requirement.

### DO NOT: Verify Completeness Without Original Requirements
Reconstructing requirements from memory or from task descriptions is circular verification (verifying the plan against itself). Always use the original pre-design-validate output.

### DO NOT: Ignore Architecture Coverage
Requirement coverage alone is insufficient. A plan can cover all requirements but miss an architecture component (e.g., requirements don't explicitly mention "logging" but the architecture has a logging component).

### DO NOT: Run Completeness Before Plan is Final
The plan must be complete (all 3 plan domain skills done: decomposition, interface, strategy) before completeness checking makes sense. Checking an in-progress plan finds false gaps.

### DO NOT: Accept <90% Coverage Without Justification
The 90% threshold exists because missing even 1 critical requirement can cause pipeline failure. If coverage is below 90%, every uncovered item needs explicit justification for why it can be deferred.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-strategy | Complete execution plan | L1 YAML: `phases[].{tasks[], parallel}` |
| pre-design-validate | Original requirements | L1 YAML: `completeness_matrix`, L2: requirements document |
| design-architecture | Architecture components | L1 YAML: `components[].{name, responsibility}` |
| PT metadata | Persisted requirements (if available) | Task metadata with requirements key |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-decompose | Completeness PASS verdict | All 3 plan-verify PASS |
| plan-decomposition | Gap report with uncovered requirements | FAIL verdict |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Requirements missing (context loss) | Lead for recovery | Error reason |
| Coverage below 90% | plan-decomposition | Uncovered requirements + recommendations |
| Architecture gaps | plan-decomposition | Missing component list |
| Analyst incomplete | Self (re-invoke) or Lead | Partial matrix + remaining scope |

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

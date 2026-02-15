---
name: plan-verify-correctness
description: |
  [P5·PlanVerify·Correctness] Logical correctness and spec compliance validator. Checks plan correctly implements architecture, respects constraints, and has no logical contradictions.

  WHEN: plan domain complete (all 3 skills done). Plan ready for validation challenge.
  DOMAIN: plan-verify (skill 1 of 3). Parallel-capable: correctness ∥ completeness ∥ robustness.
  INPUT_FROM: plan-strategy (complete plan), design-architecture (architecture to verify against), plan-interface (interface contracts).
  OUTPUT_TO: orchestration-decompose (if all plan-verify PASS) or plan domain (if FAIL, revision).

  METHODOLOGY: (1) Read plan and architecture spec, (2) Check each task implements correct architecture component, (3) Verify dependency chains match interface contracts, (4) Detect logical contradictions between tasks, (5) Verify constraint compliance (file limits, teammate limits).
  OUTPUT_FORMAT: L1 YAML correctness verdict per task, L2 markdown analysis with evidence.
user-invocable: true
disable-model-invocation: false
---

# Plan Verify — Correctness

## Execution Model
- **TRIVIAL**: Lead-direct. Quick correctness scan.
- **STANDARD**: Spawn analyst. Systematic specification compliance check.
- **COMPLEX**: Spawn 2-4 analysts. Divide by architecture module.

## Decision Points

### Tier Assessment for Correctness Verification
- **TRIVIAL**: 1-3 tasks, each mapping to a single architecture component. Lead verifies directly by checking task-to-component mapping.
- **STANDARD**: 4-8 tasks with cross-component dependencies. Spawn 1 analyst for systematic specification compliance verification.
- **COMPLEX**: 9+ tasks across 3+ architecture modules. Spawn 2-4 analysts, each verifying a non-overlapping module cluster. Reduces verification blind spots.

### Parallel Execution with Other Plan-Verify Skills
All 3 plan-verify skills (correctness, completeness, robustness) CAN run in parallel since they:
- Read the same inputs but check different properties
- Produce independent verdicts
- Have no data dependencies between them

Lead should spawn all 3 plan-verify analysts simultaneously when tier is STANDARD or COMPLEX. For TRIVIAL, Lead performs all 3 checks sequentially (quick enough to not need parallelism).

### Verification Depth Selection
How deep to verify depends on risk:
- **Surface check** (TRIVIAL): Verify task names and descriptions match architecture component names. Check file assignments make sense.
- **Contract check** (STANDARD): Verify task descriptions match architecture decisions AND interface contracts. Check dependency chains match producer-consumer relationships.
- **Deep check** (COMPLEX): All of the above PLUS verify data types flow correctly through dependency chains, check for implicit assumptions not documented in contracts, and simulate edge cases in dependency ordering.

### PASS vs FAIL Threshold
- **PASS**: Zero contradictions found across all tasks. Zero constraint violations. Every task maps to a valid architecture component.
- **Conditional PASS**: Minor findings (e.g., naming inconsistency, redundant task) that don't affect correctness. Set `status: PASS` with warnings in findings[].
- **FAIL**: Any ownership conflict, type mismatch, missing task-component mapping, or constraint violation. Requires plan revision.

When to use conditional PASS:
- Finding severity is LOW (naming, style, documentation)
- Finding does not affect execution behavior
- Fixing the finding would not change any task's implementation

## Methodology

### 1. Load Plan and Architecture
Read plan-strategy (complete implementation plan) and design-architecture (approved architecture).

### 2. Task-Architecture Mapping
For each implementation task, verify:
- Maps to exactly 1 architecture component
- Implements the correct responsibility (not a different component's job)
- Uses the correct interface contracts

**DPS — Analyst Spawn Template:**
- **Context**: Paste plan-strategy L1 (complete execution plan with phases/tasks), design-architecture L1 (components with responsibilities), and plan-interface L1 (interface contracts — needed for dependency chain verification per Step 3).
- **Task**: "Verify each task maps to correct architecture component. Check dependency chains: producer tasks produce what consumers expect (using interface contracts). Detect contradictions: file ownership conflicts, type mismatches, agent capability mismatches. Verify constraint compliance."
- **Constraints**: Read-only. No modifications.
- **Expected Output**: L1 YAML correctness verdict per task with findings[]. L2 mapping verification and contradiction report.

#### Mapping Verification Matrix
| Task ID | Target Component | Component Responsibility | Task Description | Match? | Evidence |
|---------|-----------------|------------------------|-----------------|--------|----------|
| T1 | Auth Module | Handle user authentication | "Implement JWT token service" | YES | JWT is auth mechanism |
| T2 | Data Layer | Manage database access | "Create API endpoints" | NO | API endpoints are presentation, not data |

A NO match indicates a mapping error — the task is implementing the wrong component's responsibility.

#### Component Coverage Check
After mapping, verify:
- Every architecture component has >=1 mapped task (gaps = plan incompleteness -> route to completeness check)
- No task maps to a non-existent component (phantom component -> plan-architecture mismatch)
- No component has >5 tasks mapped to it (over-decomposition -> consider merging tasks)

### 3. Dependency Chain Verification
Compare plan dependency chains against interface contracts:
- Producer tasks produce what consumer tasks expect
- No missing intermediate tasks
- No dependency on non-existent task output

#### Dependency Chain Verification Protocol
For each producer-consumer pair in the dependency graph:
1. **Identify producer output**: What does the producer task claim to produce? (from plan-decomposition L1)
2. **Identify consumer input**: What does the consumer task expect? (from plan-interface contracts)
3. **Type check**: Do output types match input types? (e.g., JSON object with fields X,Y,Z)
4. **Format check**: Are file paths, naming conventions, and data formats compatible?
5. **Timing check**: Can the producer complete before the consumer needs the data? (from plan-strategy phase ordering)

#### Chain Break Detection
A chain break occurs when:
- Producer task does not actually produce the claimed output (task description doesn't match interface)
- Consumer task expects data from a task that doesn't exist in the plan
- Intermediate task in the chain was removed or reassigned during planning
- Report ALL chain breaks — even one can cause cascading execution failures

### 4. Contradiction Detection
Search for logical contradictions:
- Task A modifies file X, Task B also modifies file X (ownership conflict)
- Task A assumes data format Y, Task B produces format Z (type mismatch)
- Task A requires capability C, assigned agent lacks tool C (agent mismatch)

#### Contradiction Categories
| Category | Example | Severity | Resolution |
|----------|---------|----------|------------|
| Ownership conflict | Tasks T1 and T3 both modify `auth.ts` | Critical | Merge tasks or split file |
| Type mismatch | T1 outputs JSON, T2 expects YAML | High | Fix interface contract |
| Agent mismatch | Task needs Bash but assigned to analyst | High | Reassign agent type |
| Timing conflict | T1 depends on T2, but T2 is in a later phase | High | Reorder phases |
| Naming inconsistency | T1 calls it "userId", T2 calls it "user_id" | Medium | Standardize naming |
| Redundant task | T1 and T4 implement same functionality | Low | Remove duplicate |

#### Systematic Contradiction Search
Rather than ad-hoc review, check ALL possible pairs:
- For N tasks, there are N*(N-1)/2 pairs to check for conflicts
- For TRIVIAL (<=3 tasks): 3 pairs — Lead can check directly
- For STANDARD (4-8 tasks): 6-28 pairs — analyst does systematic check
- For COMPLEX (9+ tasks): 36+ pairs — multiple analysts divide the pair space

### 5. Constraint Compliance
Verify plan respects all constraints:
- Max 4 teammates per phase
- File ownership non-overlapping
- Tier classification matches actual task count

## Failure Handling

### Critical Contradiction Found
- **Action**: Set `status: FAIL`. Report ALL contradictions (not just the first).
- **Routing**: Route to plan domain for revision. Include specific fix recommendations per contradiction.
- **Priority**: Ownership conflicts and type mismatches are blocking. Naming inconsistencies are non-blocking.

### Architecture Spec Missing or Incomplete
- **Cause**: design-architecture didn't produce component structure for all modules
- **Action**: Verify against available components. Flag unverifiable tasks with `check: mapping, status: SKIP`.
- **Routing**: Report gap to Lead. If >30% of tasks are unverifiable: route back to design-architecture.

### Interface Contracts Not Available
- **Cause**: plan-interface didn't complete (partial output)
- **Action**: Skip dependency chain verification for missing contracts. Set `dependency_check: partial`.
- **Impact**: Correctness verdict is degraded but still useful for mapping and contradiction checks.

### Analyst Exhausted Turns
- **Cause**: COMPLEX tier with many task pairs to check
- **Action**: Report findings so far. Set `status: PARTIAL`. Include which pairs were NOT checked.
- **Routing**: Plan-verify PASS requires ALL 3 skills to PASS. PARTIAL is treated as FAIL for pipeline continuation.

### All Checks Pass But Plan Feels Wrong
- **Cause**: Automated checks pass but analyst has qualitative concerns (e.g., "this approach is fragile")
- **Action**: Include qualitative concerns in L2 findings with `severity: low`. Don't FAIL on qualitative-only concerns.
- **Routing**: Plan-verify completeness and robustness may catch what correctness misses.

## Anti-Patterns

### DO NOT: Verify Only the Happy Path
Correctness means the plan works when everything goes RIGHT. But contradictions often hide in error paths and edge cases. Check dependency chains for failure scenarios, not just success.

### DO NOT: Accept Ambiguous Task Descriptions
If a task description is vague enough that it COULD implement two different components, that's a mapping error. Flag it — ambiguity causes implementation drift.

### DO NOT: Ignore Constraint Violations for TRIVIAL Tiers
Even TRIVIAL plans must respect the 4-teammate limit and file ownership rules. These are platform constraints, not complexity-dependent.

### DO NOT: Fix the Plan During Verification
Verification is read-only. If you find a contradiction, REPORT it — don't propose a fix in the verification output. Fixing is plan domain's job. Verification that fixes is verification that rubber-stamps.

### DO NOT: Check Correctness Without Architecture Reference
Correctness is defined as "plan matches architecture." Without the architecture spec, there's no reference to check against. If architecture is missing, route back to design — don't verify against assumptions.

### DO NOT: Stop at First Failure
Find ALL contradictions, not just the first one. Multiple findings in a single verification run save pipeline iterations (fix all at once rather than fix-verify-fix-verify).

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-strategy | Complete execution plan | L1 YAML: `phases[].{tasks[], parallel, checkpoint}` |
| design-architecture | Architecture specification | L1 YAML: `components[].{name, responsibility, dependencies[]}` |
| plan-interface | Interface contracts | L1 YAML: `contracts[].{producer, consumer, data_type}` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-decompose | Correctness PASS verdict | All 3 plan-verify skills PASS |
| plan domain | FAIL with contradiction report | Any correctness finding is critical/high |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Contradictions found | plan domain (strategy/decomposition) | All findings with severity and fix recommendations |
| Architecture spec missing | design-architecture | List of unverifiable tasks |
| Contracts missing | plan-interface | List of missing contracts |

## Quality Gate
- Every task maps to correct architecture component
- Zero ownership conflicts
- Zero type mismatches between producer-consumer pairs
- All constraints satisfied

## Output

### L1
```yaml
domain: plan-verify
skill: correctness
status: PASS|FAIL
tasks_checked: 0
contradictions: 0
constraint_violations: 0
findings:
  - task: ""
    check: mapping|dependency|contradiction|constraint
    status: PASS|FAIL
    detail: ""
```

### L2
- Task-architecture mapping verification
- Contradiction report with evidence
- Constraint compliance matrix

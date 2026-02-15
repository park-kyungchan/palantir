---
name: plan-verify-impact
description: |
  [P4·PlanVerify·ImpactContainment] Confirms checkpoint containment against propagation chains for unmitigated paths.

  WHEN: After plan-impact complete. Wave 4 parallel with pv-static/behavioral/relational.
  DOMAIN: plan-verify (skill 4 of 5). Parallel with pv-static/behavioral/relational.
  INPUT_FROM: plan-impact (execution sequence with checkpoints), research-coordinator (audit-impact L3 propagation paths).
  OUTPUT_TO: plan-verify-coordinator (containment verdict with unmitigated path evidence).

  METHODOLOGY: (1) Build checkpoint inventory from plan-impact sequence, (2) Build propagation inventory from audit-impact L3, (3) Verify each path intercepted by correctly-positioned checkpoint with matching criteria, (4) Classify gaps: unmitigated (no checkpoint), late (after terminal), insufficient (weak criteria), (5) Verdict: PASS (all HIGH contained), FAIL (HIGH unmitigated or >3 total gaps).
  OUTPUT_FORMAT: L1 YAML containment verdict, L2 path-checkpoint mapping with gap classification.
user-invocable: false
disable-model-invocation: false
---

# Plan Verify — Impact Containment

## Execution Model
- **TRIVIAL**: Lead-direct. Inline check that each propagation path has an intercepting checkpoint. No agent spawn.
- **STANDARD**: Spawn analyst (maxTurns:20). Systematic cross-reference of checkpoints against propagation paths.
- **COMPLEX**: Spawn analyst (maxTurns:30). Deep path-by-path containment analysis with cascade simulation across all propagation chains.

Note: P4 validates PLANS (pre-execution). This skill verifies that the execution sequence safely contains predicted change propagation. It does NOT verify execution results or actual impact.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn agent with `team_name` parameter. Agent delivers via SendMessage.
- **Delivery**: Agent writes result to `/tmp/pipeline/p4-pv-impact.md`, sends micro-signal: `PASS|paths:{N}|unmitigated:{N}|ref:/tmp/pipeline/p4-pv-impact.md`.

## Decision Points

### Containment Threshold Interpretation
Path containment status determines verdict routing.
- **All HIGH paths CONTAINED AND zero UNMITIGATED**: PASS. Route to plan-verify-coordinator.
- **All HIGH paths CONTAINED AND UNMITIGATED are LOW-only (count <= 3)**: CONDITIONAL_PASS. Route with risk annotation.
- **Any HIGH path UNMITIGATED or LATE**: FAIL. Route to plan-impact for fix.
- **Default**: If > 50% of paths lack containment, always FAIL (systematic checkpoint gap).

### Propagation Graph Scale
Path count determines spawn parameters.
- **< 10 paths**: STANDARD analyst (maxTurns:20). Full path-by-path containment check.
- **10-25 paths**: COMPLEX analyst (maxTurns:30). Prioritize HIGH-severity and deep (depth >= 3) paths first.
- **> 25 paths**: COMPLEX analyst (maxTurns:30). Full HIGH path check, sample MEDIUM/LOW. Flag PARTIAL if < 100% verified.

## Methodology

### Analyst Delegation DPS
- **Context**: Paste plan-impact L1 execution sequence (phases[], checkpoints[], rollback_boundaries[]). Paste research-coordinator audit-impact L3 propagation paths (paths[], origin, chain[], severity, depth).
- **Task**: "Map each propagation path to intercepting checkpoints. Verify checkpoint position (before terminal node) and criteria match (tests for specific propagation type). Classify gaps as UNMITIGATED, LATE, or INSUFFICIENT. Flag circular paths requiring dual checkpoints."
- **Constraints**: Analyst agent (Read-only, no Bash). maxTurns:20 (STANDARD) or 30 (COMPLEX). Verify only listed propagation paths.
- **Expected Output**: L1 YAML: total_paths, contained_count, unmitigated_count, late_checkpoint_count, verdict, findings[]. L2: containment matrix with path evidence.
- **Delivery**: SendMessage to Lead: `PASS|paths:{N}|unmitigated:{N}|ref:/tmp/pipeline/p4-pv-impact.md`

#### Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Verify each propagation path has an intercepting checkpoint inline. No criteria validation.
**STANDARD**: Single analyst, maxTurns:20. Full containment matrix with position and criteria validation.
**COMPLEX**: Single analyst, maxTurns:30. Full matrix + cascade simulation + circular path detection.

### 1. Read Plan-Impact Execution Sequence
Load plan-impact output to extract:
- Execution phases: ordered sequence of task groups
- Checkpoints: verification gates between phases (what they check, pass criteria)
- Containment claims: which propagation paths each checkpoint claims to contain
- Rollback boundaries: points where partial execution can be safely reverted

Build a **checkpoint inventory**: every checkpoint with its position in the sequence and containment scope.

### 2. Read Audit-Impact L3 Propagation Paths
Load audit-impact L3 output from research-coordinator:
- Propagation paths: chains of files/components affected by a change
- Path severity: HIGH (crosses module boundary), MEDIUM (within module), LOW (isolated)
- Cascade depth: how many hops from origin to terminal node
- Origin nodes: files where changes originate

Build a **propagation inventory**: every path as an ordered chain with severity and depth.

### 3. Verify Checkpoint Containment
For each propagation path, check:
- Is there at least one checkpoint that intercepts this path?
- Does the checkpoint appear BEFORE the path reaches its terminal node?
- Does the checkpoint's pass criteria detect the specific propagation being contained?

Build a containment matrix:

| Propagation Path | Severity | Depth | Intercepting Checkpoint | Position Valid? | Criteria Match? | Status |
|-----------------|----------|-------|------------------------|----------------|----------------|--------|
| auth.ts -> session.ts -> api.ts | HIGH | 2 | CP-1 (after auth phase) | Yes | Yes (auth test) | CONTAINED |
| config.json -> *.ts (broadcast) | HIGH | 1 | CP-2 (after config phase) | Yes | Partial (tests 3/5 consumers) | PARTIAL |
| util.ts -> db.ts -> cache.ts | MEDIUM | 2 | -- | -- | -- | UNMITIGATED |

**CONTAINED**: Checkpoint exists, positioned correctly, criteria match propagation type.
**PARTIAL**: Checkpoint exists but criteria do not fully cover the propagation scope.
**UNMITIGATED**: No checkpoint intercepts this propagation path.

### 4. Identify Unmitigated Impact Paths
Three categories of containment gaps:

**Unmitigated paths**: Propagation paths with no intercepting checkpoint.
- Risk: Changes propagate unchecked through the dependency chain during execution.
- Severity: Inherits the path severity (HIGH/MEDIUM/LOW from audit-impact).

**Late checkpoints**: Checkpoints that appear AFTER the propagation path has already reached its terminal node.
- Risk: By the time the checkpoint runs, the propagation damage is already done.
- Severity: HIGH if the path severity is HIGH, MEDIUM otherwise.

**Insufficient criteria**: Checkpoints that intercept the path but do not test for the specific propagation.
- Risk: The checkpoint passes even when the propagation has occurred unchecked.
- Severity: MEDIUM (checkpoint exists but is ineffective for this path).

For each gap, record:
- Propagation path (origin -> intermediate -> terminal)
- Gap type (UNMITIGATED, LATE, INSUFFICIENT)
- Path severity from audit-impact L3
- Evidence: specific path and checkpoint references
- Recommended checkpoint position (for LATE gaps)

### 5. Report Containment Verdict
Produce final verdict with evidence:

**PASS criteria**:
- All HIGH-severity paths have CONTAINED status
- Zero UNMITIGATED paths of any severity
- Late and insufficient checkpoints total <= 2 (all MEDIUM severity)

**Conditional PASS criteria**:
- All HIGH-severity paths CONTAINED
- UNMITIGATED paths exist but are LOW-severity only
- Total unmitigated count <= 3

**FAIL criteria**:
- Any HIGH-severity path UNMITIGATED, OR
- Any HIGH-severity path has LATE checkpoint, OR
- Total unmitigated count > 3 regardless of severity, OR
- >50% of paths lack containment (systematic checkpoint gap)

## Failure Handling

### Audit-Impact L3 Not Available
- **Cause**: research-coordinator did not produce audit-impact L3 output.
- **Action**: FAIL with `reason: missing_upstream`. Cannot verify containment without propagation paths.
- **Route**: Lead for re-routing to research-coordinator.

### Plan-Impact Output Incomplete
- **Cause**: plan-impact produced execution sequence but missing checkpoints or containment claims.
- **Action**: FAIL with `reason: incomplete_plan`. Report which phases lack checkpoints.
- **Route**: plan-impact for completion.

### No Propagation Paths in Audit
- **Cause**: audit-impact found zero propagation paths (fully isolated changes).
- **Action**: PASS with `paths: 0`, `unmitigated: 0`. No containment verification needed.
- **Route**: plan-verify-coordinator with trivial confirmation.

### Circular Propagation Path
- **Cause**: A propagation path forms a cycle (A -> B -> C -> A).
- **Action**: Flag as HIGH-severity finding. Circular paths require TWO checkpoints minimum (entry and re-entry points).
- **Route**: Include in findings. If no checkpoint covers both entry and re-entry, this is FAIL.

### Analyst Exhausted Turns
- **Cause**: Large propagation graph exceeds analyst budget.
- **Action**: Report partial containment analysis with percentage of paths verified. Set `status: PARTIAL`.
- **Route**: plan-verify-coordinator with partial flag and unverified path list.

## Anti-Patterns

### DO NOT: Verify Execution Results
P4 verifies PLANS, not outcomes. Check that checkpoints are positioned and specified to contain propagation paths. Do not simulate execution or predict whether checkpoints will actually catch problems.

### DO NOT: Accept Position-Only Checkpoint Validation
A checkpoint in the right position is necessary but not sufficient. Verify that the checkpoint criteria actually test for the specific propagation type. A generic "run all tests" checkpoint at the right position may miss specific propagation detection.

### DO NOT: Ignore Low-Severity Paths
Even LOW-severity paths should be reported if unmitigated. While they do not cause FAIL individually, accumulated low-severity gaps indicate weak containment strategy.

### DO NOT: Treat Rollback Boundaries as Checkpoints
Rollback boundaries are recovery mechanisms, not containment mechanisms. A rollback point after a propagation path means you can recover, but the propagation still occurred. Containment means prevention or detection BEFORE propagation completes.

### DO NOT: Create or Modify Checkpoints
If containment gaps exist, REPORT them with evidence. Do not propose new checkpoints or reposition existing ones. Execution sequence revision is the plan domain's responsibility.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-impact | Execution sequence with checkpoints | L1 YAML: phases[] with checkpoints[], rollback_boundaries[]. L2: containment claims per path |
| research-coordinator | Audit-impact L3 propagation paths | L3: paths[] with origin, chain[], severity, depth |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| plan-verify-coordinator | Containment verdict with evidence | Always (Wave 4 -> Wave 4.5 consolidation) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing audit-impact L3 | Lead | Which upstream missing |
| Incomplete plan-impact | plan-impact | Phases lacking checkpoints |
| Circular propagation | Included in findings | Cycle details and checkpoint requirements |
| Analyst exhausted | plan-verify-coordinator | Partial analysis + unverified paths |

## Quality Gate
- Every propagation path from audit-impact checked for checkpoint coverage
- Checkpoint position validated (appears BEFORE path terminal node)
- Checkpoint criteria validated (tests for specific propagation type)
- All gaps classified by type (UNMITIGATED/LATE/INSUFFICIENT) and severity
- Circular propagation paths detected and flagged
- Every finding has evidence citing specific paths and checkpoint IDs
- Verdict (PASS/FAIL) with explicit counts and severity thresholds

## Output

### L1
```yaml
domain: plan-verify
skill: plan-verify-impact
total_paths: 0
contained_count: 0
partial_count: 0
unmitigated_count: 0
late_checkpoint_count: 0
verdict: PASS|CONDITIONAL_PASS|FAIL
findings:
  - type: unmitigated|late|insufficient|circular
    path: ""
    severity: HIGH|MEDIUM|LOW
    evidence: ""
```

### L2
- Containment matrix: propagation path vs checkpoint mapping
- Unmitigated path analysis with severity and cascade depth
- Late checkpoint analysis with recommended repositioning
- Insufficient criteria analysis with specificity gaps
- Circular propagation report (if any)
- Coverage statistics: contained/partial/unmitigated counts
- Verdict justification with threshold comparisons

---
name: orchestrate-behavioral
description: |
  Plans gate/monitor/aggregate checkpoints at wave boundaries with measurable pass/fail criteria. Assigns checkpoint types: gate (blocks), monitor (warns), aggregate (collects) with failure escalation paths.

  WHEN: After plan-verify-coordinator complete (all PASS). Parallel with orchestrate-static/relational/impact.
  CONSUMES: plan-verify-coordinator (verified plan L3 via $ARGUMENTS).
  PRODUCES: L1 YAML checkpoint schedule with type counts, L2 rationale per checkpoint → orchestrate-coordinator.
user-invocable: false
disable-model-invocation: false
---

# Orchestrate — Behavioral (WHERE)

## Execution Model
- **TRIVIAL**: Skip (orchestration simplified for trivial tiers).
- **STANDARD**: Spawn 1 analyst. Systematic checkpoint identification across execution phases.
- **COMPLEX**: Spawn 1 analyst with maxTurns:25. Deep checkpoint analysis with failure propagation awareness.

## Phase-Aware Execution
- **P2+ (active Team)**: Spawn analyst with `team_name` parameter. Agent delivers result via SendMessage micro-signal per conventions.md protocol.
- **Delivery**: Write full result to `/tmp/pipeline/p5-orch-behavioral.md`. Send micro-signal to Lead via SendMessage: `PASS|checkpoints:{N}|ref:/tmp/pipeline/p5-orch-behavioral.md`.

## Decision Points

### Checkpoint Type Selection
When placing a checkpoint at a transition point:
- **Wave boundary with downstream blockers** (fan-out >= 2): Use gate checkpoint. Blocks until all tasks PASS.
- **Wave boundary with independent downstream**: Use aggregate checkpoint. Requires N-of-M tasks PASS.
- **Non-boundary transition** (mid-wave handoff): Use monitor checkpoint. Logs only, does not block.
- **Domain boundary** (P5->P6, P6->P7): Always gate checkpoint regardless of other factors.

### Checkpoint Density Control
When checkpoint count exceeds 2 per wave boundary:
- **If priority scores differ by >= 3**: Keep highest-priority only at that boundary. Merge others into monitor.
- **If priority scores within 2**: Consolidate into single aggregate checkpoint covering both criteria.
- **Maximum**: 1 gate + 1 monitor per wave boundary. Consolidate further if exceeded.

### Failure Escalation Depth
When defining fail_action per checkpoint:
- **Gate checkpoint FAIL**: Retry failed task (max 2 retries), then route to Lead for re-planning.
- **Monitor checkpoint FAIL**: Log warning + continue. Flag in L2 for post-execution review.
- **Aggregate checkpoint partial FAIL** (< N-of-M): Retry failed subset (max 1 retry), then escalate.

## Methodology

### 1. Read Verified Plan
Load plan-verify-coordinator L3 output via `$ARGUMENTS` path. Extract:
- Task list with execution phases and wave assignments
- Dependency graph showing producer-consumer relationships
- File change manifest per task
- Risk assessment findings (if available from plan-verify)

For STANDARD/COMPLEX tiers, construct the delegation prompt for the analyst with:
- **Context**: Paste verified plan L3 content. Include pipeline constraints: max 4 parallel teammates per wave, max 3 iterations per phase, Phase-Aware execution model (P2+ requires SendMessage).
- **Task**: "Identify WHERE verification checkpoints should be placed in the execution flow. For each checkpoint: define pass/fail criteria, map to wave boundary, specify what data to check. Focus on critical transitions where failure propagation risk is highest."
- **Constraints**: Read-only analysis. No modifications. Every checkpoint must have measurable criteria. Map each checkpoint to a specific wave boundary.
- **Expected Output**: L1 YAML checkpoint schedule. L2 rationale per checkpoint with wave mapping.
- **Delivery**: Write full result to `/tmp/pipeline/p5-orch-behavioral.md`. Send micro-signal to Lead via SendMessage: `PASS|checkpoints:{N}|ref:/tmp/pipeline/p5-orch-behavioral.md`.

#### Step 1 Tier-Specific DPS Variations
**TRIVIAL**: Skip — Lead places 1 implicit gate checkpoint between P6 execution and P7 verify.
**STANDARD**: Single DPS to analyst. maxTurns:15. Place checkpoints at domain boundaries only (P5->P6, P6->P7). Omit priority scoring.
**COMPLEX**: Full DPS as above. maxTurns:25. Deep checkpoint analysis with priority scoring and failure propagation awareness across all wave boundaries.

### 2. Identify Critical Transition Points
Scan the execution flow for points where verification adds the most value:

#### Transition Categories
| Category | Description | Example |
|----------|-------------|---------|
| Wave boundary | Between parallel execution waves | After Wave 6.1 code completes, before Wave 6.2 cascade |
| Producer-consumer handoff | Data flows from one task to another | Implementer A outputs module, Implementer B imports it |
| Domain boundary | Crossing from one pipeline domain to another | P5 orchestration -> P6 execution |
| Critical path junction | Where multiple dependency chains converge | 3 parallel tasks feed into 1 integration task |
| Risk mitigation point | After a task flagged as high-risk | After security-sensitive file modifications |

#### Transition Priority Scoring
For each transition point, score priority (1-5):
- **Blast radius** (1-5): How many downstream tasks fail if this checkpoint is missed?
- **Recoverability** (1-5 inverted): How hard is it to recover from undetected failure here?
- **Frequency** (1-5): How often does this type of transition cause issues historically?
- **Total**: Sum of 3 scores. Checkpoints with total >= 10 are mandatory.

### 3. Define Checkpoint Criteria
For each identified checkpoint, specify:

| Field | Description | Example |
|-------|-------------|---------|
| checkpoint_id | Unique identifier | CP-01 |
| location | Wave boundary or transition | After Wave 6.1, before Wave 6.2 |
| criteria | Measurable pass/fail conditions | All implementer tasks report PASS |
| data_checked | Specific artifacts to verify | File change manifest, test results |
| pass_action | What happens on PASS | Proceed to next wave |
| fail_action | What happens on FAIL | Retry failed task (max 3), then escalate |

#### Checkpoint Types
- **Gate checkpoint**: Blocks downstream execution until PASS. Used at wave boundaries.
- **Monitor checkpoint**: Logs status but does not block. Used for non-critical transitions.
- **Aggregate checkpoint**: Requires N-of-M tasks to pass. Used for parallel wave completion.

### 4. Map Checkpoints to Wave Boundaries
Align each checkpoint with a specific wave boundary in the execution schedule:
- Every wave boundary should have at least 1 gate checkpoint
- Wave boundaries with parallel task completion need aggregate checkpoints
- Domain boundaries (P5->P6, P6->P7) should have gate checkpoints
- Non-boundary checkpoints (mid-wave) should be monitor type only

#### Wave-Checkpoint Matrix
| Wave | Checkpoint | Type | Criteria Summary |
|------|-----------|------|-----------------|
| After Wave 5 | CP-01 | Gate | All 4 dimension skills PASS |
| After Wave 5.5 | CP-02 | Gate | Coordinator produces valid execution plan |
| After Wave 6.1 | CP-03 | Aggregate | N/N implementers report PASS |
| After Wave 6.2 | CP-04 | Gate | Impact analysis complete |

### 5. Output Checkpoint Schedule
Produce complete schedule with:
- Ordered list of checkpoints by execution sequence
- Wave mapping for each checkpoint
- Pass/fail criteria with measurable conditions
- Failure escalation path per checkpoint
- Summary: total checkpoints, gate count, monitor count, aggregate count

## Failure Handling

### Verified Plan Data Missing
- **Cause**: $ARGUMENTS path is empty or L3 file not found
- **Action**: Report FAIL. Signal: `FAIL|reason:plan-L3-missing|ref:/tmp/pipeline/p5-orch-behavioral.md`
- **Route**: Back to plan-verify-coordinator for re-export

### No Clear Wave Boundaries in Plan
- **Cause**: Plan lacks explicit wave/phase structure
- **Action**: Infer wave boundaries from dependency graph. Flag as assumption in L2.
- **Route**: Continue with inferred boundaries. Orchestrate-coordinator will validate.

### Excessive Checkpoints (>2 per wave boundary)
- **Cause**: Over-analysis creating checkpoint overhead
- **Action**: Consolidate to 1 gate + 1 monitor per boundary max. Merge redundant criteria.

## Anti-Patterns

### DO NOT: Create Checkpoints Without Measurable Criteria
"Check that everything looks good" is not a checkpoint. Every checkpoint must have specific, verifiable conditions (file exists, test passes, count matches).

### DO NOT: Place Checkpoints Mid-Task
Checkpoints belong at transitions BETWEEN tasks or waves, not during task execution. Mid-task checkpoints interfere with agent autonomy.

### DO NOT: Make Every Checkpoint a Gate
Gate checkpoints block execution. Overuse creates bottlenecks. Use monitor checkpoints for non-critical transitions.

### DO NOT: Ignore the Failure Escalation Path
Every checkpoint needs a defined action for FAIL. "Try again" is insufficient -- specify retry count, fallback, and escalation.

### DO NOT: Skip Domain Boundary Checkpoints
The P5->P6 and P6->P7 transitions are high-risk by nature. Always place gate checkpoints at domain boundaries.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify-coordinator | Verified plan L3 | File path via $ARGUMENTS: tasks, waves, dependencies |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestrate-coordinator | Checkpoint schedule | Always (WHERE dimension output) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan L3 missing | plan-verify-coordinator | Missing file path |
| No wave boundaries | orchestrate-coordinator | Inferred boundaries (flagged) |
| All checkpoints defined | orchestrate-coordinator | Complete schedule (normal flow) |

## Quality Gate
- Every wave boundary has at least 1 checkpoint
- Every checkpoint has measurable pass/fail criteria
- Every checkpoint has a defined failure escalation path
- Domain boundaries (P5->P6, P6->P7) have gate checkpoints
- No mid-task checkpoints
- Checkpoint count is proportional to plan complexity (not excessive)

## Output

### L1
```yaml
domain: orchestration
skill: behavioral
dimension: WHERE
checkpoint_count: 0
gate_count: 0
monitor_count: 0
aggregate_count: 0
checkpoints:
  - id: ""
    location: ""
    type: gate|monitor|aggregate
    criteria: ""
    fail_action: ""
```

### L2
- Checkpoint placement rationale per transition
- Priority scoring evidence
- Wave-checkpoint mapping visualization
- Failure escalation paths

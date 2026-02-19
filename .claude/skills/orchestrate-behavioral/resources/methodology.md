# Orchestrate-Behavioral — Methodology Reference

> Stage 3 detail for the orchestrate-behavioral skill. Loaded on demand.
> For shared protocols: see `.claude/resources/` (dps-construction-guide, failure-escalation-ladder, output-micro-signal-format).

## DPS Template: Checkpoint Analyst

Construct the analyst delegation prompt using these four fields:

**Context (D11 — cognitive focus first)**
```
INCLUDE:
  - Verified plan L3 content (task list, wave structure, dependency graph)
  - Pipeline constraints: max 4 parallel teammates per wave, max 3 iterations per phase
  - Phase-Aware execution model (P2+ requires SendMessage)
EXCLUDE:
  - Other orchestrate dimension outputs (static, relational, impact)
  - Historical rationale from plan-verify phases
  - Full pipeline state beyond this task's scope
Budget: Context field ≤ 30% of teammate effective context
```

**Task**
```
Identify WHERE verification checkpoints should be placed in the execution flow.
For each checkpoint: define pass/fail criteria, map to wave boundary, specify what
data to check. Focus on critical transitions where failure propagation risk is highest.
```

**Constraints**
```
Read-only analysis. No modifications to existing files.
Every checkpoint must have measurable criteria.
Map each checkpoint to a specific wave boundary.
```

**Expected Output**
```
L1 YAML checkpoint schedule.
L2 rationale per checkpoint with wave mapping.
Delivery (Four-Channel):
  Ch2: tasks/{team}/p5-orch-behavioral.md
  Ch3 → Lead: "PASS|checkpoints:{N}|ref:tasks/{team}/p5-orch-behavioral.md"
  Ch4 → orchestrate-coordinator: "READY|path:tasks/{team}/p5-orch-behavioral.md|fields:checkpoints,verification_criteria"
```

### Tier-Specific DPS Variations

| Tier | maxTurns | Scope |
|------|----------|-------|
| TRIVIAL | Skip | Lead places 1 implicit gate at P6→P7 boundary |
| STANDARD | 15 | Domain boundaries only (P5→P6, P6→P7). Omit priority scoring. |
| COMPLEX | 25 | Full analysis with priority scoring and failure propagation awareness across all wave boundaries |

## Transition Categories

Scan the execution flow for these point types:

| Category | Description | Example |
|----------|-------------|---------|
| Wave boundary | Between parallel execution waves | After Wave 6.1 code completes, before Wave 6.2 cascade |
| Producer-consumer handoff | Data flows from one task to another | Implementer A outputs module, Implementer B imports it |
| Domain boundary | Crossing from one pipeline domain to another | P5 orchestration → P6 execution |
| Critical path junction | Where multiple dependency chains converge | 3 parallel tasks feed into 1 integration task |
| Risk mitigation point | After a task flagged as high-risk | After security-sensitive file modifications |

## Priority Scoring Formula

For each transition point, score priority (1–5 per dimension):

| Dimension | Score | Interpretation |
|-----------|-------|----------------|
| Blast radius | 1–5 | How many downstream tasks fail if this checkpoint is missed? |
| Recoverability | 1–5 (inverted) | How hard is it to recover from undetected failure here? |
| Frequency | 1–5 | How often does this type of transition cause issues historically? |

**Rule**: Total = sum of 3 scores. Checkpoints with total >= 10 are mandatory.

## Checkpoint Criteria Fields

For each identified checkpoint, specify all six fields:

| Field | Description | Example |
|-------|-------------|---------|
| checkpoint_id | Unique identifier | CP-01 |
| location | Wave boundary or transition | After Wave 6.1, before Wave 6.2 |
| criteria | Measurable pass/fail conditions | All implementer tasks report PASS |
| data_checked | Specific artifacts to verify | File change manifest, test results |
| pass_action | What happens on PASS | Proceed to next wave |
| fail_action | What happens on FAIL | Retry failed task (max 2), then escalate |

## Wave-Checkpoint Matrix (Example)

| Wave | Checkpoint | Type | Criteria Summary |
|------|-----------|------|-----------------|
| After Wave 5 | CP-01 | Gate | All 4 dimension skills PASS |
| After Wave 5.5 | CP-02 | Gate | Coordinator produces valid execution plan |
| After Wave 6.1 | CP-03 | Aggregate | N/N implementers report PASS |
| After Wave 6.2 | CP-04 | Gate | Impact analysis complete |

Every wave boundary should have at least 1 gate checkpoint. Parallel task completion waves need aggregate checkpoints. Domain boundaries (P5→P6, P6→P7) always get gate checkpoints.

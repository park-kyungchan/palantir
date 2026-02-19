---
name: pre-design-validate
description: >-
  Validates requirement completeness across 5 dimensions and
  classifies gaps as critical, recommended, or nice-to-have.
  Returns to brainstorm on critical gaps. Use after
  pre-design-brainstorm completes when requirements exist but
  completeness is unverified. Reads from pre-design-brainstorm
  structured requirements with tier estimate. Produces
  completeness verdict for pre-design-feasibility on PASS, or
  gap report back to pre-design-brainstorm on FAIL. Strictness:
  strict by default (all 5 dimensions PASS), relaxed after 2
  iterations (4 of 5 PASS), auto-PASS at iteration 3. TRIVIAL:
  Lead-direct. STANDARD: 1 analyst (maxTurns: 15). COMPLEX: 2
  analysts split functional vs non-functional. DPS needs
  brainstorm L1 requirements list and tier estimate. Exclude
  user conversation history. Loops with pre-design-brainstorm
  (max 3 iterations per D15).
user-invocable: true
disable-model-invocation: true
---

# Pre-Design — Validate

## Execution Model
- **TRIVIAL**: Lead-direct. Quick 5-dimension completeness check.
- **STANDARD**: 1 analyst (run_in_background, maxTurns: 15). Systematic dimension-by-dimension.
- **COMPLEX**: 2 analysts (maxTurns: 15). Split: functional (scope+criteria) vs non-functional (constraints+errors+integration).

## Decision Points

### Tier Assessment
- **TRIVIAL**: ≤5 requirements, single module. Lead checks directly.
- **STANDARD**: 6-12 requirements, 1-2 modules. 1 analyst.
- **COMPLEX**: 13+ requirements, 3+ modules. 2 analysts split by dimension.

### Validation Strictness
- **Strict** (default): All 5 dimensions must PASS
- **Relaxed** (after 2 iterations): 4 of 5 PASS → proceed with documented gap
- **Auto-PASS** (iteration 3): Accept with all gaps documented

### Return vs Proceed
- **Return to brainstorm**: Critical dimension FAIL (scope or criteria missing)
- **Proceed**: Non-critical FAIL (constraints, error_handling, integration partially covered)
- **Heuristic**: If FAIL dimension can be inferred from context, add inferred requirement and proceed

### P0-P1 Context
Runs in P0-P1. TRIVIAL/STANDARD: local agents. COMPLEX: Team infra. Validation is READ-ONLY.

## Methodology
For detailed scoring guide and DPS: Read `resources/methodology.md`

Summary:
1. **Read** brainstorm output, identify covered dimensions
2. **Check** 5-dimension completeness matrix:

| Dimension | PASS Condition |
|-----------|---------------|
| Scope | ≥1 inclusion AND ≥1 exclusion |
| Constraints | ≥1 technical OR resource limit |
| Criteria | ≥1 testable acceptance criterion |
| Error Handling | ≥1 error scenario with recovery |
| Integration | All external dependencies listed |

3. **Identify** gaps for each FAIL dimension (what's missing, why it matters, suggested question)
4. **Report or iterate**: All PASS → feasibility. Any critical FAIL → brainstorm.

### Iteration Tracking (D15)
- `metadata.iterations.validate: N` in PT
- Iterations 1-2: strict (FAIL → brainstorm)
- Iteration 3: relaxed (proceed with gaps)
- Max: 3

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

| Failure | Level | Action |
|---------|-------|--------|
| Analyst tool error | L0 | Retry |
| Off-direction gap analysis | L1 | Nudge with corrected matrix |
| Analyst exhausted | L2 | Fresh analyst, reduced scope |
| Brainstorm output missing | L3 | Re-invoke brainstorm first |
| All 5 FAIL after 3 iterations | L4 | AskUserQuestion |

## Anti-Patterns

### DO NOT: Invent requirements to fill gaps
Report gaps — don't fabricate requirements to force PASS.

### DO NOT: Re-validate unchanged requirements
After FAIL → brainstorm, validate the UPDATED requirements, not old ones.

### DO NOT: Apply COMPLEX strictness to TRIVIAL tasks
For TRIVIAL: scope + criteria sufficient. Other dimensions optional.

### DO NOT: Block pipeline after 3 iterations
Accept and proceed — continued iteration has diminishing returns.

### DO NOT: Treat all dimensions equally
Scope and Criteria are critical. Constraints/Error Handling/Integration can be inferred during design.

### DO NOT: Validate against requirement summary
Analysts must receive COMPLETE document, not summary.

## Transitions

### Receives From
| Source | Data |
|--------|------|
| pre-design-brainstorm | Requirements doc (L1+L2) |

### Sends To
| Target | Condition |
|--------|-----------|
| pre-design-feasibility | All PASS or max iterations |
| pre-design-brainstorm | Critical dimension FAIL, iterations < 3 |

### Failure Routes
| Failure | Route | Data |
|---------|-------|------|
| Critical FAIL | brainstorm | Gap report + suggested questions |
| Non-critical FAIL (iter 3) | feasibility | Requirements + documented gaps |
| Missing input | Lead | Error details |

## Quality Gate
- Completeness matrix has explicit PASS/FAIL per dimension
- Every FAIL has actionable gap description
- No dimension left unchecked

## Output

### L1
```yaml
domain: pre-design
skill: validate
status: PASS|FAIL
completeness:
  scope: PASS|FAIL
  constraints: PASS|FAIL
  criteria: PASS|FAIL
  error_handling: PASS|FAIL
  integration: PASS|FAIL
gaps: 0
```

### L2
- Completeness matrix with per-dimension evidence
- Gap analysis for FAIL dimensions
- Iteration count and resolution status

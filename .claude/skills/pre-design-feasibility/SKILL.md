---
name: pre-design-feasibility
description: >-
  Verifies CC native implementability per requirement by checking
  cc-reference cache or spawning claude-code-guide for gaps.
  Scores each requirement as feasible, partial, or infeasible.
  Terminal pre-design skill. Use after pre-design-validate PASS
  when requirements are complete but CC feasibility unconfirmed.
  Reads from pre-design-validate validated requirements. Produces
  feasibility verdict for design-architecture on PASS, or routes
  back to pre-design-brainstorm for scope re-negotiation on FAIL.
  TRIVIAL: Lead-direct, cc-reference cache only. STANDARD: 1
  researcher (maxTurns: 20), cc-reference + claude-code-guide.
  COMPLEX: 2 researchers split core CC vs MCP/plugin capabilities.
  DPS needs validate-confirmed requirements and cc-reference cache
  path (memory/cc-reference/). Exclude brainstorm conversation
  history. Loops with pre-design-brainstorm on FAIL (max 3
  iterations per D15).
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Check against known CC capabilities via cc-reference cache.
- **STANDARD**: 1 researcher (run_in_background, maxTurns: 20). cc-reference + claude-code-guide fallback.
- **COMPLEX**: 2 researchers (maxTurns: 15-20). Split: core CC vs MCP/plugin capabilities.

## Decision Points

### Tier Classification
| Tier | Indicator | Action |
|------|-----------|--------|
| TRIVIAL | 1-2 obvious CC-native reqs | Lead checks cache directly |
| STANDARD | 3-6 reqs spanning capability categories | 1 researcher + cache + guide |
| COMPLEX | 7+ reqs OR novel CC capability questions | 2 researchers: core + MCP split |

### CC Capability Decision Tree
```
Requirement → Maps to known CC tool? → YES → cc-reference → feasible
                                     → NO → Hook/MCP/undocumented?
                                             → YES → claude-code-guide
                                             → NO → External/plugin?
                                                    → YES → WebSearch
                                                    → NO → COMPLEX, full research
```

### Skip Conditions
- All reqs = basic file ops (Read/Edit/Write/Glob/Grep) → skip (always feasible)
- All verified in prior pipeline run (same session) → skip (cite prior verdict)
- User explicitly skips → log override

> Skip does NOT apply if reqs involve hooks, MCP, or agent patterns — always verify.

### Partial Feasibility
```
Some infeasible with alternatives → PASS (with alternatives) → design-architecture
Some infeasible without alternatives:
  Non-critical → scope reduction → PASS (reduced)
  Critical → FAIL → brainstorm for re-scoping
  Iteration < 3 → re-iterate
All infeasible → Terminal FAIL → AskUserQuestion
```

## Methodology
For detailed DPS, scoring rubric, and alternatives: Read `resources/methodology.md`

Summary:
1. **Extract** technical requirements (file ops, shell, agents, MCP, hooks, skills)
2. **Map** each to CC capability. Priority: cc-reference → claude-code-guide → WebSearch
3. **Assess** verdict: feasible/partial/infeasible with weighted scoring
4. **Propose alternatives** for infeasible items
5. **Gate**: All feasible → PASS → design-architecture. Infeasible without alt → FAIL

### Iteration Tracking (D15)
- `metadata.iterations.feasibility: N` in PT
- Iterations 1-2: strict (infeasible without alt → FAIL → brainstorm)
- Iteration 3: relaxed (proceed with documented infeasible)
- Max: 3. Terminal FAIL after 3 → AskUserQuestion

## Failure Handling
For D12 escalation ladder: Read `~/.claude/resources/failure-escalation-ladder.md`

- **claude-code-guide unavailable**: → cc-reference cache (confidence: medium) → WebSearch (confidence: low)
- **cc-reference stale/missing**: → self-diagnose to refresh → retry feasibility
- **Ambiguous verdicts**: classify as `partial`, flag `poc_recommended: true`
- **All infeasible after 3 iterations**: → AskUserQuestion with 3 options (proceed reduced/modify/abandon)

## Anti-Patterns

### DO NOT: Trust stale CC reference as authoritative
Check cache freshness. If in doubt, supplement with claude-code-guide.

### DO NOT: Skip feasibility for "obviously possible"
Even simple reqs may have edge cases (file size limits, permissions, hook ordering).

### DO NOT: Spawn claude-code-guide per requirement
Batch questions into single session. Use cc-reference first.

### DO NOT: Mark partial as feasible
Partial = workaround needed. Must document approach, effort, and risk.

### DO NOT: Loop infinitely on infeasible
Max 3 iterations then AskUserQuestion.

### DO NOT: Assess without version context
Note target CC version/model. Features differ across versions.

## Transitions

### Receives From
| Source | Data |
|--------|------|
| pre-design-validate | Validated requirements (L1: PASS) |

### Sends To
| Target | Condition |
|--------|-----------|
| design-architecture | PASS (all feasible/partial with alternatives) |
| pre-design-brainstorm | FAIL (infeasible without alternatives, iter < 3) |

### Failure Routes
| Failure | Route | Data |
|---------|-------|------|
| All infeasible (3 iters) | User (AskUserQuestion) | Full list + alternatives |
| Cache + guide unavailable | self-diagnose | Stale cache details |
| Partial with low confidence | design-architecture | Risk flags, poc_recommended |

## Quality Gate
- Every requirement has explicit verdict (feasible/partial/infeasible)
- CC capability source cited per verdict
- No "unknown" verdicts remaining
- Infeasible items have documented alternatives or scope reduction
- Partial items have workaround + effort estimate
- Max 3 iteration limit enforced

## Output

### L1
```yaml
domain: pre-design
skill: feasibility
status: PASS|FAIL
iteration: 1
feasible: 0
partial: 0
infeasible: 0
items:
  - requirement: ""
    verdict: feasible|infeasible|partial
    confidence: high|medium|low
    cc_feature: ""
    source: cc-reference|claude-code-guide|web-docs
    alternative: ""
    poc_recommended: false
```

### L2
- Per-requirement verdict with CC capability mapping
- Scoring rubric results
- Alternatives with effort estimates
- Workaround details for partial items
- Risk flags for low-confidence verdicts

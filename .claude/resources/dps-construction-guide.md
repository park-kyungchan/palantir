# DPS Construction Guide

> Shared resource for skills that spawn analysts/implementers via Delegation Prompt Specification.

## DPS Structure

Every DPS must contain exactly 4 fields:

```yaml
Context:
  INCLUDE: [data the agent NEEDS to see]
  EXCLUDE: [data to NEVER include — saves context budget]
  Budget: "Context field ≤ 30% of teammate effective context"

Task: |
  Precise, actionable instruction string.
  Must be specific enough that the agent can complete without clarification.
  Include: what to do, what to produce, what format.

Constraints: |
  Tool restrictions (Read-only, no Bash, etc.)
  Scope boundaries (assigned directories only)
  Turn budget (maxTurns: N)

Expected Output: |
  L1: YAML fields for micro-signal
  L2: Detailed analysis/implementation report
```

## D11 Priority Rule

Context field construction follows **D11 priority**: cognitive focus > token efficiency.

- INCLUDE what helps the agent focus on the RIGHT task
- EXCLUDE what would distract or cause scope creep
- Budget: Context ≤ 30% of agent's effective context window

## Common INCLUDE Patterns

| Data Type | When to Include | Example |
|---|---|---|
| Upstream L1 YAML | Always for pipeline skills | research-codebase L1 pattern_inventory |
| File inventory | When agent needs to know scope | Glob results, file list |
| Interface contracts | Cross-task dependencies | plan-relational L2 contracts |
| Assigned scope | Multi-analyst splits | `scope_dirs: [src/api/, src/models/]` |

## Common EXCLUDE Patterns

| Data Type | Why Exclude |
|---|---|
| Other dimension results | Prevents cross-contamination bias |
| Pre-design conversation history | Stale, wastes context |
| Full pipeline state | Agent only needs its phase |
| ADR rationale / rejected alternatives | Not actionable |

## Delivery Instruction

Always end DPS with delivery instruction:
```
Delivery: SendMessage to Lead: "{STATUS}|{metrics}|ref:tasks/{team}/{file}"
```

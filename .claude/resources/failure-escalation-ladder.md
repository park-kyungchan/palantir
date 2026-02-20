# Failure Escalation Ladder (D12)

> Shared resource for all pipeline skills. Defines the 5-level escalation ladder for handling agent failures.

## Escalation Levels

| Level | Name | Trigger | Action | Context Cost |
|---|---|---|---|---|
| L0 | Retry | Tool error, transient failure | Re-invoke same agent, same scope | Minimal |
| L1 | Nudge | Incomplete output, partial results | Respawn with refined DPS instructions targeting gaps | Low (~200 tokens) |
| L2 | Respawn | Agent exhausted turns, systematic failure | Kill agent → spawn fresh with refined DPS | Medium (new agent context) |
| L3 | Restructure | Multi-agent conflict, scope overlap | Modify task partition, reassign | High (replanning) |
| L4 | Escalate | 3+ L2 failures, strategic ambiguity | AskUserQuestion with options | Blocks pipeline |

## Decision Rules

```
IF tool_error AND retry_count < 2:
  → L0: Retry same agent
ELIF partial_output AND missing_sections ≤ 2:
  → L1: Respawn with DPS targeting "complete sections: {list}"
ELIF agent_exhausted_turns OR output_quality < threshold:
  → L2: Respawn with:
    - Narrowed scope (if original was too broad)
    - Increased maxTurns (if turn-limited)
    - Simplified task (if complexity exceeded agent capacity)
ELIF multiple_agents_conflicting OR scope_overlap_detected:
  → L3: Restructure partition boundaries
ELIF L2_attempts ≥ 3 OR strategic_ambiguity:
  → L4: Escalate to user with:
    - What was attempted (summary)
    - Why it failed (diagnosis)
    - Options for resolution (2-3 choices)
```

## Failure Output Format

When routing a failure downstream:

```yaml
status: FAIL
failure_level: L0|L1|L2|L3|L4
failure_type: "{description}"
retry_count: N
partial_output: "{what was completed}"
missing: "{what was not completed}"
route_to: "{next skill or Lead}"
```

## Lead Autonomous Operation Safety

> [!IMPORTANT]
> For Lead autonomous operation (no user), L4 escalation is NOT available. Instead:
> - L4 → mark pipeline as BLOCKED
> - Write failure report to `tasks/pipeline-blocked.md`
> - Stop pipeline progression — do NOT guess user intent

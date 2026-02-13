# L3: DRY Violations Detail — Cross-Skill Analysis

## Phase 0 PT Check (Identical in 5 Skills)

The following block appears verbatim in brainstorming-pipeline, agent-teams-write-plan, plan-validation-pipeline, agent-teams-execution-plan, and verification-pipeline:

```
## Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to X.X    │     │
          ▼     ▼
        /permanent-tasks    Continue to X.X
        creates PT-v1       without PT
        → then X.X
```

Only the "Continue to X.X" label changes per skill. This is ~28 lines x 5 = 140 lines of duplication.

**Extraction proposal:** Move to `references/skill-common-patterns.md` with a single `## Phase 0: PERMANENT Task Check` section. Each skill references it: "Follow Phase 0 PT Check from skill-common-patterns.md. On completion, continue to Phase {N}.1."

## Clean Termination (Similar in 5 Skills)

Each skill has a Clean Termination section with:
1. Output Summary (varies per skill)
2. Shutdown Sequence: shutdown teammates → TeamDelete → artifacts preserved
3. "No auto-chaining to Phase {N+1}"

The shutdown sequence is ~10 lines identical. Output Summary varies but follows the same template:
```
## {skill-name} Complete (Phase {N})

**Feature:** {name}
**Complexity/Implementers/etc:** {varies}

**Artifacts:**
- PERMANENT Task (PT-v{N}) — ...
- Session artifacts: .agent/teams/{session-id}/

**Next:** Phase {N+1} — use /{next-skill}.
```

**Extraction proposal:** Define a Clean Termination template with parameterized fields.

## Error Handling Tables (80% Identical)

Common rows across all 5 skills:
- Spawn failure → Retry once, abort with notification
- Understanding verification 3x rejection → Abort, re-spawn
- Gate 3x iteration → Abort, present partial results
- Context compact → CLAUDE.md §9 recovery
- User cancellation → Graceful shutdown, preserve artifacts

Skill-specific rows:
- brainstorming: none (all common)
- write-plan: "No brainstorming output"
- validation: "Devils-advocate silent >20 min"
- execution: "Fix loop exhaustion", "Cross-boundary issue", "Context pressure"
- verification: "All tests fail", "Integrator conflict irreconcilable"

**Extraction proposal:** Define common error handling rows in shared reference. Each skill adds only its unique rows.

## Sequential Thinking Cross-Cutting (Identical Preamble)

All 5 skills have:
```
### Sequential Thinking

All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification.
```

Followed by a per-skill Agent × When table. The preamble is identical; the table varies.

**Extraction proposal:** Reference shared preamble. Keep per-skill tables inline.

## Compact Recovery (Identical in 5 Skills)

All 5 skills have:
```
### Compact Recovery
- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Teammate: {role}: {specific recovery instruction}
```

Lead recovery is identical. Teammate varies by role type.

## Dynamic Context Commands (Partial Overlap)

| Command | Skills Using It |
|---------|----------------|
| `head -3 CLAUDE.md` (Infra version) | All 5 pipeline |
| `ls docs/plans/` (Existing plans) | brainstorming, write-plan, validation, permanent-tasks |
| `git log --oneline` (Recent changes) | brainstorming, permanent-tasks |
| `git diff --name-only` (Git status) | execution, verification |
| `ls .agent/teams/*/global-context.md` | write-plan, validation, execution, verification |

## Total DRY Reduction Estimate

| Pattern | Current Lines | After Extraction | Savings |
|---------|--------------|------------------|---------|
| Phase 0 PT Check | 140 (28×5) | 5 (1 ref line ×5) + 28 (shared) | ~107 |
| Error Handling | 50 (10×5) | 15 (3 unique ×5) + 10 (shared) | ~25 |
| Clean Termination | 75 (15×5) | 25 (5 unique ×5) + 15 (shared) | ~35 |
| Sequential Thinking | 40 (8×5) | 20 (4 table ×5) + 3 (shared) | ~17 |
| Compact Recovery | 15 (3×5) | 5 (1 unique ×5) + 3 (shared) | ~7 |
| **TOTAL** | **320** | **~129 + 59 shared** | **~191** |

Net: ~2549 current → ~2358 after extraction + 59-line shared reference = ~191 lines saved (~7.5% reduction). The real benefit is maintenance: changes to Phase 0 logic update once vs 5 files.

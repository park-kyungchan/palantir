# T-2: Hook Reduction (8→3) — Implementation Detail

## Edit Strategy
Used whole-block replacement of the `"hooks": { ... }` object in settings.json.
This avoids trailing comma issues that would arise from surgical per-entry removal.

The 3 kept entries were copied verbatim from the source file:
- SubagentStart (spawn-time context injection — agent hasn't started, can't use NL)
- PreCompact (pre-compaction state snapshot — time-critical, agent can't self-trigger)
- SessionStart[compact] (post-compact recovery — agent has no context)

Additionally updated SessionStart statusMessage from "DIA recovery after compaction"
to "Recovery after compaction" for NLP consistency.

## Deleted Files (5)
```
.claude/hooks/on-subagent-stop.sh    (53 lines) — L1/L2 check on stop → NL
.claude/hooks/on-teammate-idle.sh    (52 lines) — L1/L2 blocking on idle → NL
.claude/hooks/on-task-completed.sh   (57 lines) — L1/L2 blocking on completion → NL
.claude/hooks/on-task-update.sh      (36 lines) — task lifecycle logging → Layer 2
.claude/hooks/on-tool-failure.sh     (35 lines) — tool failure logging → Layer 2
```

## Validation Results
```
$ jq . .claude/settings.json > /dev/null  → VALID
$ jq '.hooks | keys'                      → ["PreCompact", "SessionStart", "SubagentStart"]
$ jq '.hooks | length'                    → 3
$ ls .claude/hooks/*.sh                   → 3 files (on-pre-compact, on-session-compact, on-subagent-start)
```

Non-hook settings verified unchanged: env, permissions, enabledPlugins, language, teammateMode.

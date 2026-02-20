# Phase-Aware Execution Protocol

> Shared resource for all pipeline skills (P0–P8). Read by agent when skill-specific Phase-Aware section directs here.

## Execution Mode Routing

| Phase Range | Execution Mode | Notes |
|---|---|---|
| P0–P1 (Pre-Design + Design) | Background subagent (`run_in_background: true`, `context: fork`) | TRIVIAL may execute inline |
| P2–P7 (Research → Verify) | Background subagent (`run_in_background: true`, `context: fork`) | File-based output required |
| P8 (Delivery) | Fork agent via `context: fork` | Isolated delivery context |
| Homeostasis | Lead-direct or background subagent | No parallel coordination |

## Delivery Protocol

All subagents (P0–P8) follow the same file-based output protocol:

### Standard Subagent (P0–P7)
1. Agent writes full L2 output to `tasks/{work_dir}/{phase}-{skill}.md`
2. Agent writes micro-signal as first line of output file: `{STATUS}|{key_metrics}|ref:tasks/{work_dir}/{file}`
3. Lead reads output file on completion notification — detail file only if needed

### Fork Agent (P8)
- Skill with `context: fork` spawns isolated subagent
- Agent has full tool access but separate context
- Returns result to parent on completion

## Compaction Survival

> [!WARNING]
> After auto-compaction (~55K tokens), skill procedures may be lost from context. This document may need to be re-read if agent notices skill behavior drift.

If you suspect compaction has occurred:
1. Re-read this file and the parent SKILL.md
2. Resume from last known checkpoint
3. Do NOT start over — continue from where you left off

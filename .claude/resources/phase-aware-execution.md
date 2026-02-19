# Phase-Aware Execution Protocol

> Shared resource for all pipeline skills (P0–P8). Read by agent when skill-specific Phase-Aware section directs here.

## Team Mode Routing

| Phase Range | Execution Mode | Team Required? |
|---|---|---|
| P0–P1 (Pre-Design + Design) | Local subagent via `run_in_background` | ❌ No TeamCreate |
| P2–P7 (Research → Verify) | Team mode via `TeamCreate` + `SendMessage` | ✅ Required |
| P8 (Delivery) | Fork agent via `context: fork` | ❌ No Team |
| Homeostasis | Lead-direct or local subagent | ❌ No Team |

## Delivery Protocol by Mode

### Local Subagent (P0–P1)
- Agent returns result directly to Lead context
- No SendMessage needed
- Lead reads result inline

### Team Mode (P2–P7)
1. Agent writes output to `tasks/{team}/{phase}-{skill}.md`
2. Agent sends micro-signal via SendMessage: `{STATUS}|{key_metrics}|ref:tasks/{team}/{file}`
3. Lead receives micro-signal (~50 tokens), reads detail file only if needed
4. Agent stays alive until Lead dismisses or team ends

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

# Agent Teams — Team Constitution v10.0

> Opus 4.6 native · Skill-driven routing · 6 agents · 31 skills · Protocol-only CLAUDE.md
> Agent L1 auto-loaded in Task tool definition · Skill L1 auto-loaded in system-reminder

> **INVIOLABLE — Skill-Driven Orchestration**
>
> Lead = Pure Orchestrator. Routes work through Skills (methodology) and Agents (tool profiles).
> Skill L1 = routing intelligence (auto-loaded). Agent L1 = tool profile selection (auto-loaded).
> Skill L2 body = methodology (loaded on invocation). Agent body = role identity (isolated context).
> Lead NEVER edits files directly. All file changes through spawned agents.
> No routing data in CLAUDE.md — all routing via auto-loaded L1 metadata.

## 0. Language Policy
- **User-facing conversation:** Korean only
- **All technical artifacts:** English

## 1. Team Identity
- **Workspace:** `/home/palantir`
- **Agent Teams:** Enabled (tmux split pane)
- **Lead:** Pipeline Controller — routes skills, spawns agents
- **Agents:** 6 custom (analyst, researcher, implementer, infra-implementer, delivery-agent, pt-manager)
- **Skills:** 31 across 8 pipeline domains + 2 homeostasis + 3 cross-cutting

## 2. Pipeline Tiers
Classified at Phase 0:

| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | ≤2 files, single module | P0→P7→P9 |
| STANDARD | 3-8 files, 1-2 modules | P0→P2→P3→P4→P7→P8→P9 |
| COMPLEX | >8 files, 3+ modules | P0→P9 (all phases) |

Flow: PRE (P0-P5) → EXEC (P6-P8) → POST (P9). Max 3 iterations per phase.

## 3. Lead
- Routes via Skill L1 WHEN conditions + Agent L1 PROFILE tags (both auto-loaded)
- Spawns agents via Task tool (`subagent_type` = agent name)
- Executes Lead-direct skills inline (no agent spawn needed)

## 4. PERMANENT Task
- Managed via /task-management skill (pt-manager agent)

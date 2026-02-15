# Agent Teams — Team Constitution v10.9

> v10.9 · Opus 4.6 native · Skill-driven routing · 6 agents · 44 skills · Protocol-only CLAUDE.md
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
- **Skills:** 44 across 8 pipeline domains + 5 homeostasis + 3 cross-cutting
- **Project Skills (DO NOT EDIT during INFRA):** 10 crowd_works project skills (D0·foundation, D1·drill+production, D2·eval) — separate project, excluded from manage-skills/RSI/homeostasis

## 2. Pipeline Tiers
Classified at Phase 0:

| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | ≤2 files, single module | P0→P6→P8 |
| STANDARD | 3 files, 1-2 modules | P0→P1→P2→P3→P6→P7→P8 |
| COMPLEX | ≥4 files, 2+ modules | P0→P8 (all phases) |

Flow: PRE (P0-P4) → EXEC (P5-P7) → POST (P8). Max 3 iterations per phase.

> Note: Skill WHEN conditions describe the COMPLEX (full) path. For TRIVIAL/STANDARD tiers, Lead overrides skill-level WHEN conditions and routes based on the tier table above.

## 2.1 Execution Mode by Phase
- **P0-P1 (PRE-DESIGN + DESIGN)**: Lead with local agents (run_in_background). No Team infrastructure (no TeamCreate/SendMessage). Brainstorm, validate, feasibility, architecture, interface, risk.
- **P2+ (RESEARCH through DELIVERY)**: Team infrastructure ONLY. TeamCreate, TaskCreate/Update, SendMessage. Local agents (`team_name` omitted) PROHIBITED. Lead MUST NOT use TaskOutput to read full agent results — use SendMessage for result exchange.

## 3. Lead
- Routes via Skill L1 WHEN conditions + Agent L1 PROFILE tags (both auto-loaded)
- Spawns agents via Task tool (`subagent_type` = agent name)
- Executes Lead-direct skills inline (no agent spawn needed)

## 4. PERMANENT Task (PT)
Single source of truth for active pipeline. Exactly 1 per pipeline.
- **Create**: Pipeline start (P0). Contains: tier, requirements, architecture decisions.
- **Read**: Teammates TaskGet [PERMANENT] for project context at spawn.
- **Update**: Each phase completion adds results to PT metadata (Read-Merge-Write).
- **Complete**: Only at final git commit (P8 delivery).
- Managed via /task-management skill (pt-manager agent).

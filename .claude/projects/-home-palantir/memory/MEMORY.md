# Claude Code Memory

## Next Session Action [PRIORITY] (2026-02-08)
- **RSI Loop continues** — NLP v6.0 conversion COMMITTED. Next options:
  1. SKL-004: `/brainstorming-pipeline` for plan-validation-pipeline (Phase 5 skill)
  2. Ontology Framework: T-1 (ObjectType) via `/brainstorming-pipeline`
  3. task-api-guideline.md NLP conversion (currently v4.0/530 lines, still has protocol markers)
- **Ontology handoff:** `docs/plans/2026-02-08-ontology-bridge-handoff.md` (b3c1012)
- **User decides next direction**

## Language Policy [PERMANENT] (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only (GC, directives, tasks, L1/L2/L3, gates, hooks, designs, CLAUDE.md, agent .md, MEMORY.md)
- CLAUDE.md §0 Language Policy
- Rationale: token efficiency for Opus 4.6, machine-readable consistency, cross-agent parsing

## Current Infrastructure State (v6.0) (2026-02-08)
- CLAUDE.md: v6.0 (171 lines, §0-§10) — NLP conversion from v5.1, PERMANENT Task integration, C-2.2 fixes
- task-api-guideline.md: v4.0 (~530 lines, §1-§14) — unchanged in this cycle
- agent-common-protocol.md: v2.0 (82 lines) — NLP + PT/TaskGet context receipt
- Agents: 6 types, 442 total lines (NLP v2.0), disallowedTools = TaskCreate+TaskUpdate only
- Skills: `/permanent-tasks` (250 lines, NEW), 3 pipeline skills with Phase 0 + NLP terminology
- Hooks: on-subagent-start.sh updated (67 lines, 3-path GC→PT logic), 8 total hooks hardened
- Verification: Natural language understanding verification (replaces TIER/LDAP protocol markers)
- MCP Tools: sequential-thinking (mandatory all), tavily/context7 (mandatory by phase), github (as needed)
- NLP v6.0 conversion: Phase 6 COMPLETE, Gate 6 APPROVED (2026-02-08)
- Detailed history: `memory/infrastructure-history.md`

## Skill Pipeline Status (2026-02-08)
| SKL | Skill | Phase | Status |
|-----|-------|-------|--------|
| 001 | `/brainstorming-pipeline` | P1-3 | DONE + NLP v6.0 + Phase 0 |
| 002 | `/agent-teams-write-plan` | P4 | DONE + NLP v6.0 + Phase 0 |
| 003 | `/agent-teams-execution-plan` | P6 | DONE + NLP v6.0 + Phase 0 |
| 004 | plan-validation-pipeline | P5 | **TODO — NEXT** |
| 005 | verification pipeline | P7-8 | TODO |
| 006 | delivery pipeline | P9 | TODO |
| NEW | `/permanent-tasks` | — | DONE (GC replacement skill) |
- Detailed history: `memory/skill-optimization-history.md`

## Skill Optimization Process [PERMANENT] (2026-02-07)
- **claude-code-guide agent research required**: Every skill optimization must investigate latest Claude Code features/Opus 4.6 optimization points relevant to that skill
- **Common improvements (all skills)**:
  1. Dynamic Context Injection (`!`shell``) — auto-inject relevant context at skill load
  2. `$ARGUMENTS` variable — receive user input directly in skill
  3. Opus 4.6 Measured Language — natural instructions, not excessive ALL CAPS/[MANDATORY]
  4. `argument-hint` frontmatter — autocomplete UX
- **Per-skill improvements**: Derived from claude-code-guide research (different each time)
- **Design file format**: Markdown + YAML frontmatter
- **Process**: claude-code-guide research → design doc → SKILL.md → validation → commit

## User Visibility — ASCII Visualization [PERMANENT] (2026-02-08)
- When updating orchestration-plan.md or reporting state changes, Lead outputs ASCII status visualization
- User co-monitors orchestration-plan.md — visual progress reporting is essential
- Include: phase pipeline, workstream progress bars, teammate status, key metrics
- Added to CLAUDE.md §6 "User Visibility — ASCII Status Visualization"

## BUG-001: permissionMode: plan blocks MCP tools [CRITICAL]
- researcher/architect with `permissionMode: plan` get stuck on MCP tool calls
- **Workaround: Always spawn with `mode: "default"`** (disallowedTools already blocks mutations)
- Details: `memory/agent-teams-bugs.md`

## BUG-002: Large-task teammates auto-compact before producing L1/L2 [HIGH]
- **Symptom:** Teammate receives directive with massive scope (e.g., 9-file integration + MCP research), context fills with file reads before any work begins, auto-compact triggers, teammate loses all context with zero artifacts saved
- **Root cause:** Directive prompt too large + reading many large files + MCP tool calls = context exhaustion before first write
- **Meta-Level fix (CLAUDE.md §6 Pre-Spawn Checklist):**
  - Gate S-1: Resolve ambiguity BEFORE spawning (ask user)
  - Gate S-2: >4 files → MANDATORY split into multiple tasks/teammates (Lead orchestrates, not teammate)
  - Gate S-3: Re-spawn after failure → directive MUST differ (same approach = same failure)
- **Key lesson:** Lead must split at orchestration level (multiple tasks + multiple teammates), NOT tell a single teammate to "self-split internally"
- **Details:** 3x failure in RTDI Sprint — monolithic 9-file directive → compact → re-spawn same → compact again → finally split into 3 parallel tasks

## Ontology Framework Status (2026-02-08)
- **Architecture:** Layer 1 (Claude Code CLI + Agent Teams) + Layer 2 (Ontology Framework)
- **Layer 2 scope:** General-purpose Ontology Framework mimicking Palantir Foundry
- **First domain:** TBD (user decides during brainstorming)
- **Handoff:** `docs/plans/2026-02-08-ontology-bridge-handoff.md` (b3c1012)
- **Reference files:** `park-kyungchan/palantir/Ontology-Definition/docs/bridge-reference/` (5 files, 3842 lines)
- **Topics:** T-1 ObjectType → T-2 LinkType → T-3 ActionType → T-4 Integration
- **Critical correction:** Entities are NOT Claude native capabilities — Framework is domain-agnostic
- **Brainstorming = learning:** User progressively learns Ontology/Foundry through sessions

## Deferred Work
- CH-002~005: `docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml`
- Agent memory initialization: Create MEMORY.md templates for each agent type

## Topic Files Index
- `memory/infrastructure-history.md` — DIA evolution (v1→v4), Agent Teams redesign, Task API investigation, Ontology
- `memory/skill-optimization-history.md` — SKL-001/002/003 detailed records
- `memory/agent-teams-bugs.md` — BUG-001 details and workaround

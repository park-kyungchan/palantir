# Claude Code Memory

## Permanent Rules

### Language Policy (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only
- Rationale: token efficiency for Opus 4.6, cross-agent parsing consistency

### Skill Optimization Process (2026-02-07)
- claude-code-guide agent research required for every skill optimization
- Common improvements: Dynamic Context Injection, $ARGUMENTS, Opus 4.6 Measured Language, argument-hint frontmatter
- Per-skill improvements derived from claude-code-guide research (different each time)
- Process: claude-code-guide research → design doc → SKILL.md → validation → commit

### claude-code-guide Output Management (2026-02-11)
- claude-code-guide agent has NO Write tool → output stored only in volatile /tmp
- **Lead must read output immediately after task completion** — /tmp/ files are cleaned up on a timer
- If output is lost: use `resume` parameter to retrieve from agent context
- Never substitute domain knowledge for CC research — always re-request if output is lost

### Pre-Orchestration Agent Description Reading (2026-02-11)
- Before ANY orchestration, Lead must read `.claude/references/agent-catalog.md` Level 1 (up to boundary marker, ~227L)
- Level 2 (~1186L) read only when needing category detail or fallback evaluation
- 27 agents (22 workers + 5 coordinators) across 10 categories
- Purpose: understand routing model, coordinator descriptions, spawn conditions
- This is mandatory — never orchestrate from summary tables or memory alone
- CLAUDE.md §6 "Before Spawning" directs this read → auto-recovery after compaction

### ASCII Status Visualization (2026-02-08)
- Lead outputs ASCII visualization when updating orchestration-plan.md or reporting state
- Include: phase pipeline, workstream progress bars, teammate status, key metrics

## Current INFRA State (v9.0, 2026-02-11)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v9.0 | ~378L | D-001~D-017 integrated, 42 agents, 13 categories, reference-heavy |
| task-api-guideline.md | v6.0 | 118L | NLP consolidated (was 537L, 78% reduction) |
| agent-common-protocol.md | v4.0 | ~180L | +Memory, +Error (D-017), +Output, +Handoff (D-011) |
| agent-catalog.md | v3.0 | ~1882L | Two-Level (L1 ~280L + L2 ~1600L), 42 agents (34W+8C) |
| Agents | v5.0 | 42 files | 34 workers + 8 coordinators, 13 categories |
| References | v1.0 | 3 new | gate-evaluation-standard (D-008), ontological-lenses (D-010), coordinator-shared-protocol (D-013) |
| Settings | — | ~84L | MCP Tool Search auto:7 enabled |
| Hooks | 4 total | ~220L | SubagentStart, PreCompact (hookOutput), SessionStart, PostToolUse |
| Observability | — | — | `.agent/observability/{slug}/` (rtd-index, events.jsonl, registry) |

### Skills (10 total)

| SKL | Skill | Phase | Notes |
|-----|-------|-------|-------|
| 001 | `/brainstorming-pipeline` | P1-3 | +D-001 tier routing, +architecture-coordinator (COMPLEX) |
| 002 | `/agent-teams-write-plan` | P4 | +D-001 tier routing, +planning-coordinator (COMPLEX), +D-012 |
| 003 | `/agent-teams-execution-plan` | P6 | +contract-reviewer, +regression-reviewer, +D-012/D-014 |
| 004 | `/plan-validation-pipeline` | P5 | +D-001 tier routing, +validation-coordinator (COMPLEX) |
| 005 | `/verification-pipeline` | P7-8 | +D-001 tier awareness, +contract-tester |
| 006 | `/delivery-pipeline` | P9 | 422L + RTD |
| 007 | `/rsil-review` | — | 549L, 8 Lenses, Meta-Cognition |
| 008 | `/rsil-global` | — | 452L, auto-invoke, Three-Tier |
| — | `/permanent-tasks` | — | RTD + Cross-Cutting (CH-5) |

### RSIL Quality Data
- RSIL INFRA Score: 5.9→9.5/10 (+61%, 5 cycles, Baseline→C4→C5)
- Dimensions: Static 10/10, Relational 9/10, Behavioral 9.5/10
- Cumulative: 92 findings, 93% acceptance (11 reviews: 1 global, 4 narrow, 6 retroactive)
- Cycle 7: 20 new (integration 7 + protocol 13), 6 FIX + 7 WARN all applied, 7 INFO noted
- CC Optimization (Task #23): MCP Tool Search, RTD dedup, protocol expansion, PreCompact hookOutput
- Tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`
- Agent memory: `~/.claude/agent-memory/rsil/MEMORY.md`
- All audit targets COMPLETE (S-1~S-4, S-6, S-7)

### Agents-Driven Workflow (PT #4→#5→v9.0, 2026-02-11)
- 42 agents (34 workers + 8 coordinators), 13 categories — `.claude/references/agent-catalog.md` (1882L Two-Level)
- P1: One Agent = One Responsibility — WHEN/WHY/HOW framework
- Layer 1/2 Boundary: `.claude/references/layer-boundary-model.md` (Coordinator Orchestration section added)
- CLAUDE.md §6: Agent Selection and Routing (6-step), Coordinator Management (Mode 1+3)
- 8 coordinators: research, verification, architecture, planning, validation, execution, testing, infra-quality
- D-001~D-017: Pipeline Tiers, Full Decomposition, Gate Standard, Ontological Lenses, Error Taxonomy
- New references: gate-evaluation-standard.md (D-008), ontological-lenses.md (D-010), coordinator-shared-protocol.md (D-013)
- INFRA v9.0: 17 Decisions integrated across 6 batches, 378L CLAUDE.md (reference-heavy)

### Known Bugs

| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | CLAUDE.md §6 Pre-Spawn Checklist (S-1/S-2/S-3 gates) |
| BUG-003 | MEDIUM | $CLAUDE_SESSION_ID unavailable in hooks (GH #17188) | AD-29: SubagentStart stdin SID → session-registry.json |
| BUG-004 | HIGH | No cross-agent compaction notification | tmux monitoring + H-3 incremental L1 + protocol self-report |

Details: `memory/agent-teams-bugs.md`

## Next Topics

### Ontology Communication Protocol [ALWAYS ACTIVE] (2026-02-10)

Active whenever Ontology/Foundry concepts arise. User = concept-level decision-maker.
4-step pattern: **TEACH → IMPACT ASSESS → RECOMMEND → ASK**
Reference: `.claude/references/ontology-communication-protocol.md`

### Ontology PLS — Deferred to New Session (2026-02-10)

All phases complete (P0-P3), no implementation needed. PT #3 archived.
Next: T-0 brainstorming via `/brainstorming-pipeline`.
13 architecture decisions (AD-1~AD-13), 15 corrections applied, 10 deferred.
Details + complete document index (30+ files): `memory/ontology-pls.md`

### Other Deferred Work
- CH-002~005: `docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml`
- Agent memory initialization: MEMORY.md templates for each agent type (CC research confirmed 15-20% savings)
- ~~MCP Tool Search~~: DONE (auto:7 in settings.json)
- O-A: Phase 0 DRY (~132L savings, 3 variants across 8 skills)
- O-C: Cross-Cutting DRY (~60L savings)
- Observability Dashboard: `/brainstorming-pipeline` topic (reads events.jsonl + rtd-index.md)
- COW v2.0: End-to-end testing with sample images, .claude.json MCP cleanup

## Topic Files Index
- `memory/infrastructure-history.md` — Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` — SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` — BUG-001~BUG-003 details and workarounds
- `memory/ontology-pls.md` — Ontology PLS full handoff (30+ connected docs, AD-1~AD-13, brainstorming chain T-0~T-4)

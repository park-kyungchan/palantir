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
- 43 agents (35 workers + 8 coordinators) across 13 categories
- Purpose: understand routing model, coordinator descriptions, spawn conditions
- This is mandatory — never orchestrate from summary tables or memory alone
- CLAUDE.md §6 "Before Spawning" directs this read → auto-recovery after compaction

### ASCII Status Visualization (2026-02-08)
- Lead outputs ASCII visualization when updating orchestration-plan.md or reporting state
- Include: phase pipeline, workstream progress bars, teammate status, key metrics

### Dual Environment: Claude Code CLI vs Warp (2026-02-13)
- **Claude Code CLI (tmux)**: Agent Teams multi-instance. Reads CLAUDE.md as constitution. Full pipeline with spawned teammates.
- **Warp Agent (Oz)**: Single-instance. Reads CLAUDE.md + WARP.md + Warp Manage Rules. Lead↔Teammate role switching.
- **Bridge files** (both environments read): CLAUDE.md, MEMORY.md, WARP.md, agent .md, SKILL.md
- **Warp-only**: 4 Manage Rules (not visible to Claude Code CLI)
- WARP.md (`/home/palantir/WARP.md`) = compact single-instance protocol + tool mapping

### Warp Manage Rules Configuration (2026-02-13)
4 Rules in Warp's Manage Rules (replace all prior rules):
- **Rule 1: Session Bootstrap** — Model identity, session start reads, language, core mandates
- **Rule 2: Warp Single-Instance Execution** — Lead↔Teammate switching, persona binding, output, pipeline tiers
- **Rule 3: Warp Tool Mapping** — Warp native tools → INFRA pattern mapping (plan, TODO, grep, edit, shell, review, PR)
- **Rule 4: Verification & Context Engineering** — Step-by-step verification, V1-V6 checks, context preservation, WARP.md maintenance
- Active task rule: 장기 작업 시 Rule 5로 추가, 완료 후 삭제

## Current INFRA State (v9.0 + Phase 6, 2026-02-13)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v9.0+ | ~394L | D-001~D-017, §10 fork exception (pt-manager, delivery-agent, rsil-agent) |
| task-api-guideline.md | v6.0 | 118L | NLP consolidated (was 537L, 78% reduction) |
| agent-common-protocol.md | v4.1 | ~200L | +§Task API fork exception (3 agents listed) |
| agent-catalog.md | v3.0 | ~1882L | Two-Level (L1 ~280L + L2 ~1600L), 43 agents (35W+8C) |
| Agents | v6.0 | 46 files | 35 workers + 8 coordinators + 3 fork agents, 13 categories |
| Fork Agents | v1.0 | 3 files | pt-manager (full API), delivery-agent (−Create), rsil-agent (−Create) |
| Coordinators | Template B | 8 files | memory:project, color, disallowedTools:[4], protocol refs standardized |
| References | v1.0 | 3 new | gate-evaluation-standard (D-008), ontological-lenses (D-010), coordinator-shared-protocol (D-013) |
| Settings | — | ~84L | MCP Tool Search auto:7 enabled |
| Hooks | 4 total | ~220L | SubagentStart, PreCompact (hookOutput), SessionStart, PostToolUse |
| Observability | — | — | `.agent/observability/{slug}/` (rtd-index, events.jsonl, registry) |

### Skills (10 total: 5 coordinator-based + 4 fork-based + 1 solo)

| SKL | Skill | Phase | Type | Notes |
|-----|-------|-------|------|-------|
| 001 | `/brainstorming-pipeline` | P1-3 | coord | §A/§B/§C/§D template, 612L |
| 002 | `/agent-teams-write-plan` | P4 | coord | §A/§B/§C/§D template, 372L |
| 003 | `/agent-teams-execution-plan` | P6 | coord | §A/§B/§C/§D template, 671L |
| 004 | `/plan-validation-pipeline` | P5 | coord | §A/§B/§C/§D template, 436L |
| 005 | `/verification-pipeline` | P7-8 | coord | §A/§B/§C/§D template, 553L |
| 006 | `/delivery-pipeline` | P9 | fork | context:fork, agent:delivery-agent, 499L |
| 007 | `/rsil-review` | — | fork | context:fork, agent:rsil-agent, 8 Lenses |
| 008 | `/rsil-global` | — | fork | context:fork, agent:rsil-agent, Three-Tier |
| — | `/permanent-tasks` | — | fork | context:fork, agent:pt-manager, PT lifecycle |

### RSIL Quality Data
- RSIL INFRA Score: 5.9→9.5/10 (+61%, 5 cycles, Baseline→C4→C5)
- Dimensions: Static 10/10, Relational 9/10, Behavioral 9.5/10
- Cumulative: 92 findings, 93% acceptance (11 reviews: 1 global, 4 narrow, 6 retroactive)
- Cycle 7: 20 new (integration 7 + protocol 13), 6 FIX + 7 WARN all applied, 7 INFO noted
- CC Optimization (Task #23): MCP Tool Search, RTD dedup, protocol expansion, PreCompact hookOutput
- Tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`
- Agent memory: `~/.claude/agent-memory/rsil/MEMORY.md`
- All audit targets COMPLETE (S-1~S-4, S-6, S-7)

### Agents-Driven Workflow (PT #4→#5→v9.0+P6, 2026-02-13)
- 46 agent files (35 workers + 8 coordinators + 3 fork agents), 13 categories
- Agent catalog: `.claude/references/agent-catalog.md` (1882L Two-Level)
- P1: One Agent = One Responsibility — WHEN/WHY/HOW framework
- Layer 1/2 Boundary: `.claude/references/layer-boundary-model.md`
- CLAUDE.md §6: Agent Selection and Routing (6-step), Coordinator Management (Mode 1+3)
- CLAUDE.md §10: Fork exception — pt-manager, delivery-agent, rsil-agent get Task API access
- 8 coordinators (Template B): memory:project, color, disallowedTools:[TaskCreate,TaskUpdate,Edit,Bash]
- 3 fork agents: pt-manager (full API), delivery-agent (−TaskCreate), rsil-agent (−TaskCreate)
- 5 coordinator SKILL.md: §A Phase 0 / §B Core / §C Interface / §D Cross-Cutting template
- 4 fork SKILL.md: context:fork + agent: frontmatter → fork agent .md binding
- D-001~D-017: Pipeline Tiers, Full Decomposition, Gate Standard, Ontological Lenses, Error Taxonomy
- Skill Opt v9.0 Phase 6 output: `palantir_coding/.agent/teams/skill-opt-v9-p6/phase-6/`
- Verification report: `palantir_coding/.agent/teams/skill-opt-v9-p6/phase-6/verifier/L2-verification-report.md`

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

All phases complete (P0-P3), no implementation needed. Archived.
Next: T-0 brainstorming via `/brainstorming-pipeline`.
13 architecture decisions (AD-1~AD-13), 15 corrections applied, 10 deferred.
Details + complete document index (30+ files): `memory/ontology-pls.md`

### Other Deferred Work
- Observability Dashboard: `/brainstorming-pipeline` topic (reads events.jsonl + rtd-index.md)

## Topic Files Index
- `memory/infrastructure-history.md` — Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` — SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` — BUG-001~BUG-003 details and workarounds
- `memory/ontology-pls.md` — Ontology PLS full handoff (30+ connected docs, AD-1~AD-13, brainstorming chain T-0~T-4)

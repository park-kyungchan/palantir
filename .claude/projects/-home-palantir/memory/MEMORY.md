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

### ASCII Status Visualization (2026-02-08)
- Lead outputs ASCII visualization when updating orchestration-plan.md or reporting state
- Include: phase pipeline, workstream progress bars, teammate status, key metrics

## Current INFRA State (v7.0, 2026-02-10)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v7.0 | ~206L | §6 Observability RTD, §9 RTD recovery |
| task-api-guideline.md | v6.0 | 118L | NLP consolidated (was 537L, 78% reduction) |
| agent-common-protocol.md | v3.0 | ~108L | L1/L2 PT Goal Linkage (optional) |
| Agents | v2.0 | ~460L | 6 types, RTD awareness |
| Hooks | 4 total | — | SubagentStart, PreCompact, SessionStart, PostToolUse (async) |
| Observability | — | — | `.agent/observability/{slug}/` (rtd-index, events.jsonl, registry) |

### Skills (10 total)

| SKL | Skill | Phase | Notes |
|-----|-------|-------|-------|
| 001 | `/brainstorming-pipeline` | P1-3 | NLP v6.0 + Phase 0 + RTD |
| 002 | `/agent-teams-write-plan` | P4 | NLP v6.0 + Phase 0 + RTD |
| 003 | `/agent-teams-execution-plan` | P6 | NLP v6.0 + Phase 0 + RTD |
| 004 | `/plan-validation-pipeline` | P5 | NLP v6.0 + Phase 0 + RTD |
| 005 | `/verification-pipeline` | P7-8 | NLP v6.0 + Phase 0 + INFRA RSI + RTD |
| 006 | `/delivery-pipeline` | P9 | 422L + RTD |
| 007 | `/rsil-review` | — | 549L, 8 Lenses, Meta-Cognition |
| 008 | `/rsil-global` | — | 452L, auto-invoke, Three-Tier |
| — | `/permanent-tasks` | — | RTD + Cross-Cutting (CH-5) |

### RSIL Quality Data
- Cumulative: 72 findings, 92% acceptance (9 reviews: 1 global, 4 narrow, 4 retroactive)
- Tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`
- Agent memory: `~/.claude/agent-memory/rsil/MEMORY.md`
- Remaining audit targets: S-5 brainstorming (done S-1), S-6 CLAUDE.md, S-7 agent-common-protocol+hooks

### Known Bugs

| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | CLAUDE.md §6 Pre-Spawn Checklist (S-1/S-2/S-3 gates) |
| BUG-003 | MEDIUM | $CLAUDE_SESSION_ID unavailable in hooks (GH #17188) | AD-29: SubagentStart stdin SID → session-registry.json |

Details: `memory/agent-teams-bugs.md`

## Next Topics

### Ontology Framework — Brainstorming Chain

Layer 2 (Ontology Framework) is the next major initiative. Entry via `/brainstorming-pipeline`.
Layer 1 achievement ~70% (RTDI assessment). Layer 2 = 0% → ~30% of full vision.

| Topic | Name | Input Docs | Depends On | Output |
|-------|------|-----------|------------|--------|
| T-0 | RTDI Layer 2 Strategy | `rtdi-codebase-assessment.md` + `ontology-bridge-handoff.md` | — | L2 scope, bootstrap domain, migration strategy |
| T-1 | ObjectType + Property + Struct | T-0 output + `bridge-reference/` (5 files) | T-0 | ObjectType schema, Property system, Struct definitions |
| T-2 | LinkType + Interface | T-1 output + existing L1 cross-refs | T-1 | LinkType schema, Interface contracts |
| T-3 | ActionType + Pre/Postconditions | T-1 output + pipeline phase definitions | T-1 | ActionType schema, guard/effect system |
| T-4 | Framework Integration | T-1~T-3 outputs + current INFRA state | T-1,T-2,T-3 | Runtime integration architecture |

Key docs:
- WHY: `docs/plans/2026-02-10-rtdi-codebase-assessment.md` (660L, 6 gaps, 8 success criteria)
- WHAT: `docs/plans/2026-02-08-ontology-bridge-handoff.md` (~450L, T-1~T-4 definitions)
- HOW: `docs/plans/2026-02-10-ontology-sequential-protocol.md` (~418L, T-0~T-4 calling protocol)
- Bridge Reference: `park-kyungchan/palantir/Ontology-Definition/docs/bridge-reference/` (5 files, 3842L)
- 6 Layer 1 structural gaps: NL assertion fragility, unstructured state, knowledge fragmentation, validation without enforcement, agent attribution (BUG-003), ripple detection
- 8 deferred items mapped to Ontology components (see assessment §8)

### Other Deferred Work
- CH-002~005: `docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml`
- Agent memory initialization: MEMORY.md templates for each agent type
- Observability Dashboard: `/brainstorming-pipeline` topic (reads events.jsonl + rtd-index.md)
- COW v2.0: End-to-end testing with sample images, .claude.json MCP cleanup

## Topic Files Index
- `memory/infrastructure-history.md` — Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` — SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` — BUG-001~BUG-003 details and workarounds

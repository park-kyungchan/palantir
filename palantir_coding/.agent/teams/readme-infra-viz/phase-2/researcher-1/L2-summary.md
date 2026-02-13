## Summary

Complete inventory of `.claude/` INFRA v9.0: 43 agent definitions (35 workers + 8 coordinators across 14 categories), 10 skill playbooks, 4 lifecycle hooks, 9 reference documents, 2 settings files, and CLAUDE.md v9.0 (317L). All components mapped with inter-relationships: skill-to-agent spawning, hook-to-event binding, reference-to-consumer paths, and full P0-P9 pipeline flow.

## Domain 1: Agent Inventory (43 Agents)

| # | Category | Phase | Type | Agents | Count |
|---|----------|-------|------|--------|-------|
| 1 | Research | P2 | Worker | codebase-researcher, external-researcher, auditor | 3 |
| 2 | Verification | P2b | Worker | static-verifier, relational-verifier, behavioral-verifier, impact-verifier | 4 |
| 3 | Architecture | P3 | Worker | structure-architect, interface-architect, risk-architect, architect (legacy) | 4 |
| 4 | Planning | P4 | Worker | decomposition-planner, interface-planner, strategy-planner, plan-writer (legacy) | 4 |
| 5 | Validation | P5 | Worker | correctness-challenger, completeness-challenger, robustness-challenger | 3 |
| 6 | Review | P6 | Worker | devils-advocate, spec-reviewer, code-reviewer, contract-reviewer, regression-reviewer | 5 |
| 7 | Implementation | P6 | Worker | implementer, infra-implementer | 2 |
| 8 | Testing | P7 | Worker | tester, contract-tester | 2 |
| 9 | Integration | P8 | Worker | integrator | 1 |
| 10 | INFRA Quality | X-cut | Worker | infra-static-analyst, infra-relational-analyst, infra-behavioral-analyst, infra-impact-analyst | 4 |
| 11 | Impact | P2d/6+ | Worker | dynamic-impact-analyst | 1 |
| 12 | Audit | G3-G8 | Worker | gate-auditor | 1 |
| 13 | Monitoring | P6+ | Worker | execution-monitor | 1 |
| C | Coordinators | Various | Coordinator | research-, verification-, architecture-, planning-, validation-, execution-, testing-, infra-quality-coordinator | 8 |
| **Total** | | | | | **43** |

**Key patterns:**
- All agents block TaskCreate/TaskUpdate (Lead-only)
- Two agents use `permissionMode: acceptEdits`: implementer, integrator
- Color coding: cyan=research, yellow=verification/testing, green=implementation, blue=architecture/planning, red=review/audit, orange=review-readonly, magenta=integration/impact/monitoring, white=INFRA
- MaxTurns range: 15 (gate-auditor) to 100 (implementer, integrator)

## Domain 2: Skills Inventory (10 Skills)

| # | Skill | Phase | Lines | Coordinator(s) | Description |
|---|-------|-------|-------|-----------------|-------------|
| 1 | brainstorming-pipeline | P0-3 | 490 | research-coordinator | Feature idea to researched architecture |
| 2 | agent-teams-write-plan | P4 | 262 | planning-coordinator | Architecture to implementation plan |
| 3 | plan-validation-pipeline | P5 | 313 | validation-coordinator | Plan challenge via challengers |
| 4 | agent-teams-execution-plan | P6 | 511 | execution-coordinator | Plan to working code with review |
| 5 | verification-pipeline | P7-8 | 419 | testing-coordinator | Testing + integration |
| 6 | delivery-pipeline | P9 | 341 | Lead-only | Git commit, archive, MEMORY |
| 7 | rsil-global | Post | 337 | Lead-only | INFRA health assessment |
| 8 | rsil-review | Any | 406 | Lead-only | Quality review, 8 lenses |
| 9 | permanent-tasks | X-cut | 198 | Lead-only | PT create/update (Read-Merge-Write) |
| 10 | palantir-dev | Standalone | 97 | N/A | Programming language learning |
| | **Total** | | **3,374** | | |

## Domain 3: Infrastructure Components

### Hooks (4 scripts, ~416L total)

| Hook | Event | Script | Lines | Timeout | Mode | Purpose |
|------|-------|--------|-------|---------|------|---------|
| H-1 | SubagentStart | on-subagent-start.sh | 93 | 10s | sync | Team context injection (PT/GC), RTD session registry |
| H-2 | PreCompact | on-pre-compact.sh | 123 | 30s | sync | Save task snapshot, warn missing L1/L2, RTD state snapshot |
| H-3 | SessionStart(compact) | on-session-compact.sh | 54 | 15s | once | RTD-centric recovery context injection |
| H-4 | PostToolUse | on-rtd-post-tool.sh | 146 | 5s | async | Capture all tool calls as JSONL events |

### References (9 documents, ~2,643L total)

| Ref | Document | Version | Lines | Decision Source | Purpose |
|-----|----------|---------|-------|-----------------|---------|
| R-1 | agent-catalog.md | v3.0 | 1,489 | D-002, D-005 | Two-level agent catalog (L1 ~280L + L2 ~1200L) |
| R-2 | agent-common-protocol.md | v4.0 | 247 | D-009, D-011, D-017 | Shared teammate procedures |
| R-3 | coordinator-shared-protocol.md | v1.0 | 135 | D-013 | Coordinator management protocol |
| R-4 | gate-evaluation-standard.md | v1.0 | 151 | D-008 | Universal gate structure and tier criteria |
| R-5 | ontological-lenses.md | v1.0 | 84 | D-010, D-005 | ARE/RELATE/DO/IMPACT 4-lens framework |
| R-6 | task-api-guideline.md | v6.0 | 80 | — | NLP-consolidated Task API guide |
| R-7 | layer-boundary-model.md | v1.0 | 130 | AD-15 | NL vs structural solution boundary |
| R-8 | ontology-communication-protocol.md | v1.0 | 318 | — | TEACH/IMPACT/RECOMMEND/ASK pattern |
| R-9 | pipeline-rollback-protocol.md | v1.0 | 74 | GAP-5 | Supported rollback paths (P5-P8 to earlier) |

### Settings

| File | Lines | Key Contents |
|------|-------|--------------|
| settings.json | 84 | 6 env vars, 7 deny permissions, 4 hook configs, 2 plugins, Korean language, opus-4-6 model |
| settings.local.json | 29 | 10 allow permissions, 8 MCP JSON servers (oda-ontology, tavily, cow-*) |

### CLAUDE.md

- **Version:** v9.0 (Team Constitution)
- **Lines:** 317
- **Key Sections:** Language Policy (0), Team Identity (1), Phase Pipeline (2), Roles (3), Communication (4), File Ownership (5), How Lead Operates (6), Tools (7), Safety (8), Recovery (9), Integrity Principles (10)
- **Decisions integrated:** D-001 through D-017

### Agent Memory (7 persistent memory files)

| Path | Role |
|------|------|
| agent-memory/implementer/MEMORY.md | Implementer lessons |
| agent-memory/tester/MEMORY.md | Tester lessons |
| agent-memory/integrator/MEMORY.md | Integrator lessons |
| agent-memory/researcher/MEMORY.md | Researcher lessons |
| agent-memory/devils-advocate/MEMORY.md | DA lessons |
| agent-memory/rsil/MEMORY.md | RSIL lessons |
| agent-memory/architect/MEMORY.md | Architect lessons (+lead-arch-redesign.md) |

## Domain 4: Relationship Map

### Skill-to-Agent Spawning

| Skill | Coordinator | Workers Spawned |
|-------|-------------|-----------------|
| brainstorming-pipeline | research-coordinator | codebase-researcher, external-researcher, auditor |
| brainstorming-pipeline | architecture-coordinator (COMPLEX) | structure-architect, interface-architect, risk-architect |
| agent-teams-write-plan | planning-coordinator (COMPLEX) | decomposition-planner, interface-planner, strategy-planner |
| plan-validation-pipeline | validation-coordinator (COMPLEX) | correctness-challenger, completeness-challenger, robustness-challenger |
| plan-validation-pipeline | devils-advocate (TRIVIAL/STANDARD) | — (Lead-direct) |
| agent-teams-execution-plan | execution-coordinator | implementer, infra-implementer, spec-reviewer, code-reviewer |
| verification-pipeline | testing-coordinator | tester, contract-tester, integrator |
| rsil-global/review | infra-quality-coordinator | infra-static/relational/behavioral/impact-analyst |

### Hook-to-Event Binding

| Event | Hook Script | Consumers |
|-------|-------------|-----------|
| SubagentStart | on-subagent-start.sh | All spawned agents (context injection) |
| PreCompact | on-pre-compact.sh | Lead (state preservation) |
| SessionStart(compact) | on-session-compact.sh | Lead (recovery) |
| PostToolUse | on-rtd-post-tool.sh | Observability system (events.jsonl) |

### Reference-to-Consumer Paths

| Reference | Primary Consumers |
|-----------|-------------------|
| agent-catalog.md | Lead (routing decisions) |
| agent-common-protocol.md | All 43 agents |
| coordinator-shared-protocol.md | 8 coordinators |
| gate-evaluation-standard.md | Lead, gate-auditor |
| ontological-lenses.md | 4 INFRA analysts, 3 architecture agents |
| task-api-guideline.md | Lead, all agents (via TaskList/TaskGet) |
| layer-boundary-model.md | Lead, RSIL skills |
| ontology-communication-protocol.md | Lead (when Ontology topics arise) |
| pipeline-rollback-protocol.md | validation/verification/execution skills |

### Pipeline Flow with Agent Types

```
P0 (Lead-only: Tier Classification)
 |
P1 (Lead-only: Discovery)
 |
P2 (Research) ──────── research-coordinator → codebase/external/auditor
 |
P2b (Verification) ── verification-coordinator → static/relational/behavioral-verifier
 |                                               impact-verifier
P2d (Impact) ──────── dynamic-impact-analyst (Lead-direct)
 |
P3 (Architecture) ─── architecture-coordinator → structure/interface/risk-architect
 |                     OR architect (legacy, TRIVIAL/STANDARD)
P4 (Design) ───────── planning-coordinator → decomposition/interface/strategy-planner
 |                     OR plan-writer (legacy, TRIVIAL/STANDARD)
P5 (Validation) ───── validation-coordinator → correctness/completeness/robustness-challenger
 |                     OR devils-advocate (legacy, TRIVIAL/STANDARD)
P6 (Implementation) ─ execution-coordinator → implementer + infra-implementer
 |                     + spec-reviewer, code-reviewer, contract-reviewer, regression-reviewer
P6+ (Monitoring) ──── execution-monitor (Lead-direct, parallel with P6)
 |
P7 (Testing) ──────── testing-coordinator → tester + contract-tester
 |
P8 (Integration) ──── testing-coordinator → integrator (conditional: 2+ implementers)
 |
P9 (Delivery) ─────── Lead-only (delivery-pipeline skill)
 |
Post ──────────────── rsil-global / rsil-review (INFRA quality, cross-cutting)
                      infra-quality-coordinator → 4 INFRA analysts
```

## PT Goal Linkage

All findings directly support the README.md INFRA v9.0 visualization goal by providing exhaustive component inventory and relationship data for the architect phase.

## Evidence Sources

- 43 agent files read: `/home/palantir/.claude/agents/*.md`
- 10 skill files read: `/home/palantir/.claude/skills/*/SKILL.md`
- 4 hook files read: `/home/palantir/.claude/hooks/on-*.sh`
- 9 reference files read: `/home/palantir/.claude/references/*.md`
- 2 settings files read: `/home/palantir/.claude/settings.json`, `settings.local.json`
- CLAUDE.md read: `/home/palantir/.claude/CLAUDE.md` (317L)
- .claude.json read: `/home/palantir/.claude.json` (MCP servers, project config)
- Line counts verified via Grep count for all files

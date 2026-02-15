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
- Process: claude-code-guide research -> design doc -> SKILL.md -> validation -> commit

### claude-code-guide Output Management (2026-02-11)
- claude-code-guide agent has NO Write tool -> output stored only in volatile /tmp
- **Lead must read output immediately after task completion** -- /tmp/ files are cleaned up on a timer
- If output is lost: use `resume` parameter to retrieve from agent context
- Never substitute domain knowledge for CC research -- always re-request if output is lost

### ASCII Status Visualization (2026-02-08)
- Lead outputs ASCII visualization when updating orchestration-plan.md or reporting state
- Include: phase pipeline, workstream progress bars, teammate status, key metrics

### Environment: Claude Code CLI (2026-02-13)
- **Claude Code CLI (tmux)**: Agent Teams multi-instance. Reads CLAUDE.md as constitution. Full pipeline with spawned teammates.
- teammateMode: tmux (settings.json)

## Current INFRA State (v10.6 Integration, 2026-02-15)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v10.6 | 48L | Protocol-only + tier routing override note |
| Agents | v10.5 | 6 files | 2 haiku+memory:none (delivery,pt-mgr), 4 memory:project, all color |
| Skills | v10.6 | 35 dirs | Integration fixes: verify sub-routing, research FAIL paths, cascade boundary |
| Settings | v10.6 | ~110L | teammateMode:tmux, alwaysThinkingEnabled, matcher expanded |
| Hooks | 5 total | ~285L | SRC log mv (not rm), matcher "implementer|infra-implementer" |
| Agent Memory | -- | 6 files | +infra-integration-audit.md, +srp-analysis.md |

### Architecture (v10 Native Optimization)
- **Routing**: Skill L1 auto-loaded in system-reminder, Agent L1 auto-loaded in Task tool definition
- **L1 (frontmatter)**: WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY -- routing intelligence, 1024 chars max
- **L2 (body)**: Execution Model + Methodology (5 steps) + Quality Gate + Output -- loaded on invocation
- **CLAUDE.md**: Protocol-only (43L), zero routing data -- all routing via auto-loaded metadata
- **Lead**: Pure Orchestrator, never edits files directly, routes via skills+agents

### Skills (35 total: 28 pipeline + 4 homeostasis + 3 cross-cutting)

| Domain | Skills | Phase |
|--------|--------|-------|
| pre-design | brainstorm, validate, feasibility | P0-P1 |
| design | architecture, interface, risk | P2 |
| research | codebase, external, audit | P3 |
| plan | decomposition, interface, strategy | P4 |
| plan-verify | correctness, completeness, robustness | P5 |
| orchestration | decompose, assign, verify | P6 |
| execution | code, infra, **impact, cascade**, review | P7 |
| verify | structure, content, consistency, quality, cc-feasibility | P8 |
| homeostasis | manage-infra, manage-skills, **manage-codebase, self-improve** | X-cut |
| cross-cutting | delivery-pipeline, pipeline-resume, task-management | P9/X-cut |

### Pipeline Tiers

| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | <=2 files, single module | P0->P7->P9 |
| STANDARD | 3-8 files, 1-2 modules | P0->P2->P3->P4->P7->P8->P9 |
| COMPLEX | >8 files, 3+ modules | P0->P9 (all phases) |

### Known Bugs

| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | Keep prompts focused, avoid context bloat |
| BUG-004 | HIGH | No cross-agent compaction notification | tmux monitoring + protocol self-report |

Details: `memory/agent-teams-bugs.md`

## Next Topics

### Ontology Communication Protocol [ALWAYS ACTIVE] (2026-02-10)

Active whenever Ontology/Foundry concepts arise. User = concept-level decision-maker.
4-step pattern: **TEACH -> IMPACT ASSESS -> RECOMMEND -> ASK**

### Ontology PLS -- Deferred (2026-02-10)
All phases complete (P0-P3). Next: T-0 brainstorming. Details: `memory/ontology-pls.md`

### Meta-Cognition INFRA Update -- Largely Implemented (2026-02-14)
Core ideas from meta-cognition brainstorming have been implemented in v10:
- CLAUDE.md Protocol-Only transition: DONE (43L)
- Homeostasis System: DONE (manage-infra + manage-skills + 5 verify-* skills)
- Self-describing components (frontmatter routing): DONE (31 skills with full L1/L2)
- Root Exemption Zone concept: Applied in manage-skills self-management detection
Remaining: Enhanced Frontmatter v2 (routing/meta_cognition blocks) NOT adopted -- using native fields only.
Details: `memory/meta-cognition-infra.md`

## Session History

### RSI L3 — Context Engineering + Delegation Prompt Engineering (2026-02-15, branch: test)
Progressive Deep-Dive RSI: L1(structure)→L2(integration)→**L3(logic)** — first logic-level self-improvement.
- **L3 Diagnosis**: 3 parallel analysts, 59 findings (3C/12H/21M/23L) across hooks/agents/skills
- **Iter 1**: Delegation Prompt Standard (DPS) — 8 agent-spawning skills, avg quality 2.1→4.2/5
- **Iter 2**: Tool-Agent Mismatch — C-01 cascade grep→analyst, AGT-01 impact researcher→analyst, H-01~H-04 executor annotations
- **Iter 3**: Hook Logic Bugs — CRITICAL-01 parallel SRC log collision (mv removed), HIGH-01 jq fallback
- Key insight: Skill L2 says WHAT to do, not HOW to delegate. DPS (Context/Task/Constraints/Output) bridges the Lead→Agent isolation boundary.
- Diagnostic reports: `agent-memory/analyst/{hooks-deep-analysis,agent-definition-audit,skill-l2-logic-audit}.md`
- Remaining queue: Iter 4 (FAIL paths, 10 skills), Iter 5 (data persistence C-02)
- Total: 13 files changed + 3 diagnostic reports, commits 4eac475 + f6c4813

### v10.6 Integration Deep-Dive (2026-02-15, branch: test)
- Integration audit: 7.1/10 (vs 9.2 component health), 21 findings (2 HIGH, 7 MEDIUM)
- SRP analysis: 35 skills graded (28 A, 4 B+, 1 B, 1 C+), no splits needed
- INT-20 fix: SRC log mv instead of rm (parallel implementer data preservation)
- INT-10 fix: SubagentStop matcher expanded to "implementer|infra-implementer"
- INT-07 fix: claude-code-guide fallback standardized across 3 skills
- INT-05 fix: CLAUDE.md tier routing override note added
- INT-15 fix: verify-* failure sub-routing specified (5 skills)
- INT-18 fix: research-codebase/external FAIL paths added
- SRP fix: execution-cascade .claude/ boundary documented
- Settings: teammateMode:tmux, alwaysThinkingEnabled:true, model explicit
- Total: 15 files changed, commit 15cb1e8

### v10.5 RSI — Recursive Self-Improvement (2026-02-15, branch: test)
5 iterations, ~50 files changed. Health score: 9.2/10. Severity: 47→20→6 (converged).
**Iter 1** (7 waves): Hook bugs (jq boolean, basename, wc-l, pipefail), agent L2+color+memory, L3 removal. 35 files.
**Iter 2** (2 waves): CLAUDE.md v10.5, pt-manager model:haiku, once:true removed, cc-ref cache.
**Iter 3** (3 waves): Hook robustness (grep scope→git root, dedup, dep-cap, cleanup), P6a→P6, P0-1→P0, delivery-agent haiku+memory:none, bidirectional I/O fixes. 13 files.
**Iter 4** (3 waves): Hook timeout:30, P0-P2 run_in_background, manage-skills domain count, cc-guide fallback. 10 files.
**Iter 5**: Final sweep — 0 HIGH, 0 MEDIUM remaining. statusMessage UX. RSI loop terminated.

### v10.4 SRC — Smart Reactive Codebase (2026-02-14, branch: test)
- **SRC**: Automatic impact analysis system for code changes during pipeline execution
- Architecture: Two-Stage Hook (PostToolUse→/tmp log, SubagentStop→Lead inject) — ADR-SRC-1
- 3 new skills: execution-impact (P7.3), execution-cascade (P7.4), manage-codebase (homeostasis)
- 2 new hooks: on-file-change.sh (async file logger), on-implementer-done.sh (impact injector)
- CLAUDE.md v10.3: Section 2.1 added (P0-P2 Lead-only, P3+ Team infrastructure)
- Execution domain renumbered: 5 skills (code→infra→impact→cascade→review)
- self-improve: disable-model-invocation → false (user request, budget 93%)
- RSI pass: execution-code trimmed 1071→859, bidirectionality fixes, numbering corrected
- Design docs: src-architecture.md (1037L, 7 ADRs), src-interfaces.md, src-risk-assessment.md
- Full COMPLEX pipeline: P0→P2 (Lead-only) → P7 (3 teammates) → P8 → P9
- Total: 11 files changed/created

### v10.3 Description Quality Optimization (2026-02-14, branch: test)
- All 32 skill descriptions trimmed to ≤1024 chars (zero L1 truncation)
- Canonical structure enforced: [Tag] -> WHEN -> DOMAIN -> I/O -> METHODOLOGY -> OUTPUT_FORMAT
- Removed from L1: ONTOLOGY_LENS (5), CLOSED_LOOP (8), MAX_TEAMMATES (25)
- Budget: 86% -> 82% (26,315 of 32,000 chars), 5,685 chars headroom
- CC reference cache updated: semantic routing mechanics, budget analysis
- claude-code-guide delta research: transformer-based routing, no priority mechanism
- manage-skills audit: 32/32 skills, all domains covered, no gaps
- Total: 35 files changed, +156 -196 lines

### v10.2 CC Native Compliance + Context Engineering (2026-02-14, branch: test)
- Removed 12 non-native `input_schema` fields and 3 `confirm` fields across skills
- Fixed 4 pipeline skills with `disable-model-invocation: true` breaking Lead routing
- Added `argument-hint` to 4 user-invocable skills (brainstorm, delivery, resume, task-mgmt)
- Discovered and reverted `context: fork` safety risk (replaces agent body with skill L2)
- Fixed verify-cc-feasibility native field reference lists (was self-inconsistent)
- Deep CC context engineering research: loading order, field semantics, budget mechanics
- Total: 17 files changed

### v10.1 INFRA Cleanup + L2 Body Design (2026-02-14, branch: test)
- Removed all RTD dead code from 3 hooks
- Removed stale Skill(orchestrate) permission from settings.json
- Rewrote pipeline-resume from RTD to Task API
- Fixed TIER_BEHAVIOR in 5 skills (removed coordinator/architect references)
- Deleted 17 orphaned agent-memory directories + rsil-review-output.md
- Fixed domain count in CLAUDE.md and manage-skills
- **Wrote comprehensive L2 bodies for all 30 skills** (task-management already had one)
- Ran manage-skills: 27 UPDATE, 0 CREATE, 0 DELETE -- all domains fully covered
- Total: 42 files changed, +1415 / -800 lines

## Topic Files Index
- `memory/infrastructure-history.md` -- Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` -- SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` -- BUG-001~BUG-004 details and workarounds
- `memory/ontology-pls.md` -- Ontology PLS full handoff (30+ connected docs, AD-1~AD-13)
- `memory/meta-cognition-infra.md` -- Meta-Cognition INFRA Update handoff (14 decisions)
- `memory/context-engineering.md` -- CC native field reference, context loading order, critical findings
- `memory/cc-reference/` -- Machine-readable CC native reference (4 files):
  - `native-fields.md` -- Skill + Agent frontmatter field tables, flag combos, permissionMode details
  - `context-loading.md` -- Session loading order, L1 budget, invocation flow, compaction, context budget
  - `hook-events.md` -- All 14 hook events, types, input/output format, matchers, our configuration
  - `arguments-substitution.md` -- $ARGUMENTS, dynamic context injection, env vars, argument-hint

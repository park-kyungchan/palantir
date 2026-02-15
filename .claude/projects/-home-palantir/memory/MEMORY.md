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

### Dual Environment: Claude Code CLI vs Warp (2026-02-13)
- **Claude Code CLI (tmux)**: Agent Teams multi-instance. Reads CLAUDE.md as constitution. Full pipeline with spawned teammates.
- **Warp Agent (Oz)**: Single-instance. Reads CLAUDE.md + WARP.md + Warp Manage Rules. Lead<->Teammate role switching.
- **Bridge files** (both environments read): CLAUDE.md, MEMORY.md, WARP.md, agent .md, SKILL.md
- **Warp-only**: 4 Manage Rules (not visible to Claude Code CLI)
- WARP.md (`/home/palantir/WARP.md`) = compact single-instance protocol + tool mapping

### Warp Manage Rules Configuration (2026-02-13)
4 Rules in Warp's Manage Rules (replace all prior rules):
- **Rule 1: Session Bootstrap** -- Model identity, session start reads, language, core mandates
- **Rule 2: Warp Single-Instance Execution** -- Lead<->Teammate switching, persona binding, output, pipeline tiers
- **Rule 3: Warp Tool Mapping** -- Warp native tools -> INFRA pattern mapping (plan, TODO, grep, edit, shell, review, PR)
- **Rule 4: Verification & Context Engineering** -- Step-by-step verification, V1-V6 checks, context preservation, WARP.md maintenance
- Active task rule: 장기 작업 시 Rule 5로 추가, 완료 후 삭제

## Current INFRA State (v10.5 RSI, 2026-02-15)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v10.3 | 47L | Protocol-only + Section 2.1 (P0-P2 Lead-only rule) |
| Agents | v10.5 | 6 files | All: color, memory:project, expanded L2 bodies |
| Skills | v10.5 | 35 dirs | L3 refs removed, L2 fixes, 31 auto-loaded |
| Settings | -- | ~109L | 9 permissions, 5 hooks |
| Hooks | 5 total | ~280L | Bug fixes: FC-1 jq boolean, ID-3 basename, ID-6 wc-l, CX-3 pipefail |
| Agent Memory | -- | 4 dirs | implementer, infra-implementer, researcher, analyst |

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

### v10.5 RSI Iteration 1 — Code-Logic Self-Improvement (2026-02-15, branch: test)
- **RSI Loop**: RESEARCH→DIAGNOSE→IMPLEMENT→VERIFY autonomous cycle on all .claude/ files
- 7 implementation waves: W1(hook hardening), W2(skill L2), W3(agent expand), CC(audit), W1.5(hook bugs), W4(L3+colors), W5(cc-ref)
- Hook bugs fixed: FC-1 jq `//` boolean, ID-3 basename collision→2-component awk, ID-6 wc-l empty, CX-3 pipefail×3
- Agents: all 6 gained color field + expanded L2 bodies + memory:project (delivery-agent, pt-manager new)
- Skills: 15 L3 OUTPUT_FORMAT refs removed, 8 L2 body fixes (verify lens, task-mgmt tag, delivery QG)
- cc-reference cache: all 4 files updated (SRC hooks, context:fork fix, budget numbers, argument-hint)
- CC audit findings cached for Iteration 2: haiku model for analyst/pt-manager, TaskCompleted hook, rules/ modularization
- Total: ~35 files changed across 5 hooks + 6 agents + 16 skills + 4 cc-reference

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

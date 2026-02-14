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

## Current INFRA State (v10.1, 2026-02-14)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v10.0 | 43L | Protocol-only, no routing data |
| Agents | v10.0 | 6 files | analyst(B), researcher(C), implementer(D), infra-implementer(E), delivery-agent(F), pt-manager(G) |
| Skills | v10.2 | 31 dirs | Full L2 + native field compliance (no non-native fields) |
| Settings | -- | ~84L | 9 permissions, MCP Tool Search auto:7 |
| Hooks | 3 total | ~148L | SubagentStart, PreCompact, SessionStart (RTD code removed) |
| Agent Memory | -- | 3 dirs | implementer, infra-implementer, researcher only |

### Architecture (v10 Native Optimization)
- **Routing**: Skill L1 auto-loaded in system-reminder, Agent L1 auto-loaded in Task tool definition
- **L1 (frontmatter)**: WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY -- routing intelligence, 1024 chars max
- **L2 (body)**: Execution Model + Methodology (5 steps) + Quality Gate + Output -- loaded on invocation
- **CLAUDE.md**: Protocol-only (43L), zero routing data -- all routing via auto-loaded metadata
- **Lead**: Pure Orchestrator, never edits files directly, routes via skills+agents

### Skills (31 total: 26 pipeline + 2 homeostasis + 3 cross-cutting)

| Domain | Skills | Phase |
|--------|--------|-------|
| pre-design | brainstorm, validate, feasibility | P0-P1 |
| design | architecture, interface, risk | P2 |
| research | codebase, external, audit | P3 |
| plan | decomposition, interface, strategy | P4 |
| plan-verify | correctness, completeness, robustness | P5 |
| orchestration | decompose, assign, verify | P6 |
| execution | code, infra, review | P7 |
| verify | structure, content, consistency, quality, cc-feasibility | P8 |
| homeostasis | manage-infra, manage-skills | X-cut |
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

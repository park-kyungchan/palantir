# Agent Teams Infrastructure — Detailed History

## Agent Teams Infrastructure Redesign (2026-02-07)

### Design Completed
- File: `docs/plans/2026-02-07-agent-teams-infra-redesign-design.yaml` (1644 lines, 9 sections)
- Full infrastructure deletion + rebuild for Agent Teams native architecture
- Opus 4.6 Only, CLI-Native (Claude Max X20, API-Free)

### Key Decisions (DD-001 ~ DD-016)
- 9-Phase Shift-Left Pipeline (70-80% Pre-Execution)
- Lead = Pipeline Controller (High Control, approves every gate)
- Dynamic Teammate Spawning (6 agent types: researcher, architect, devils-advocate, implementer, tester, integrator)
- [PERMANENT] Semantic Integrity Guard (Teammate-Level + Lead-Level DIA)
- L1/L2/L3 File-Based Handoff (not in-memory summary)
- Teammate as Sub-Orchestrator (parallel subagents + self-orchestration)
- Task API Guideline rewritten from scratch with [PERMANENT] integration
- Lead's DIA: code-level logic detection + real-time orchestration adjustment
- Superpowers plugin PRESERVED for future enhancement

### Implementation Completed (2026-02-07)
- Branch: `feat/agent-teams-infra-redesign` (3 commits)
- Phase A: Deleted 2,476 files (skills, agents, refs, rules, CLAUDE.md, .agent/)
- Phase B: Created 10 files (CLAUDE.md v1.0, settings.json, task-api-guideline, 6 agents, .agent/teams/)
- Phase C: 10/10 validation checks PASSED
- Backup at: `.claude/backups/v7.3-pre-agent-teams/`
- Implementation Plan: `docs/plans/2026-02-07-agent-teams-infra-migration.md`

### Smoke Test PASSED (2026-02-07)
- Full pipeline: TeamCreate→TaskCreate→Spawn→Execute→Gate→Shutdown→TeamDelete
- 13/13 test items PASSED

## Task API Deep Investigation (2026-02-07)
- task-api-guideline.md v1.0→v1.1 (4 new sections)
- Findings report: `.agent/teams/task-api-investigation/phase-2/task-api-findings.md`
- ISS-001 [HIGH]: Completed task files may auto-delete from disk (trigger unknown)
- ISS-002 [MED]: TaskGet shows raw blockedBy (includes completed), TaskList filters correctly
- ISS-003 [HIGH]: Task orphaning on context clear (use Team scope always)
- ISS-004 [LOW]: highwatermark can be stale vs actual max ID
- Dependency: addBlockedBy/addBlocks = bidirectional auto-sync, blocker completion ≠ auto-removal

## DIA Evolution History
### v2.0 — DIA Enforcement (2026-02-07)
- 3-Protocol: CIP (Context Injection) + DIAVP (Impact Verification) + Lead-Only Task API
- 8 GAPs resolved: GAP-001~008
- Key insight: "Protocol ≠ Enforcement" — disallowedTools for hard, IAS echo-back for soft

### v3.0 — LDAP (2026-02-07)
- CH-001: Layer 3 LDAP (GAP-003a interconnection + GAP-003b ripple)
- Design: `docs/plans/2026-02-07-ch001-ldap-design.yaml`
- Plan: `docs/plans/2026-02-07-ch001-ldap-implementation.md`
- Commit: `b363232` — 7 files, 179 insertions, 4 deletions

### v3.1 — MCP Mandatory (2026-02-07)
- CLAUDE.md §7: sequential-thinking, tavily, context7, github
- 6 agent .md files updated with MCP tool instructions

### v4.0 — Team Memory + Context Delta + Hooks (2026-02-07)
- CH-006: Team Memory + Context Delta + Hook Enhancement
- 12 files modified across 5 migration steps
- 4-Layer DIA: CIP → DIAVP → LDAP → Hooks
- Key ADRs: AD-001~AD-005
- Architecture: `.agent/teams/ch006-dia-v4/`

## Superpowers Plugin Compatibility Analysis (2026-02-07)
- Report: `docs/plans/2026-02-07-superpowers-agent-teams-compatibility-analysis.md`
- 14 skills: 3 INCOMPATIBLE, 3 CONFLICTS, 1 OVERLAPS, 2 ADAPTABLE, 5 COMPATIBLE
- Recommended: Option C (Replace Workflow Chain Only)

## Ontology Definition Enhancement (2026-02-06)
### Completed Work
- Phase 1 Core Primitives: ObjectType, Property, SharedProperty
- 6 files (6,226 lines): ObjectType.md, Property.md, SharedProperty.md, DEFINITIONS.md, TAXONOMY.md, NAMING_AUDIT.md
- WF-1 Gap Report: 10 gaps (G1-G10), 9 resolved, G3 deferred to Phase 2
### Key Decisions
- Formal Definition = NC/SC/BC structure
- Quantitative thresholds: OT(Property≥3, Link≥2, query>30%), SP promotion(OT≥3, semantics 100%)
- Interface apiName: camelCase (official), session PascalCase = violation
### Verification: V1 PASS | V2 FIXED | V3 FIXED | V4 PASS (27 fixes)
### Next: Phase 2 (LinkType, Interface), codebase migration

## INFRA v7.0 Integration Sprint — DELIVERED (2026-02-10)
- **WS-A:** task-api-guideline.md v5.0 (537L) → v6.0 (118L), 78% reduction
  - Commit: 15521ec — 10→7 sections, 49/52 BRs preserved, 3 delegated to CLAUDE.md
- **WS-B:** RSIL Audit S-2~S-4, 36 findings across 3 reviews, 27 APPLIED
  - S-2: write-plan + validation (15 findings, all APPLIED, P4-R1/R2/P5-R1/R2 backlog cleared)
  - S-3: permanent-tasks (11 findings, 5 APPLIED, 265→273L)
  - S-4: execution-plan (10 findings, 7 APPLIED, 597→604L)
- 4 SKILL.md modified: write-plan (+8L), validation (+7L), permanent-tasks (+8L), execution-plan (+7L)
- Key patterns: PT disambiguation (RA-R1-3), Phase 0 frontmatter (P-5), Evidence Sources (P-1), DP-{N} naming
- Sessions: infra-v7-integration (P1-3, P6 WS-A, WS-B S-2~S-4)

## RTD System + INFRA v7.0 — DELIVERED (2026-02-10)
- Commit: 06c179d — 26 files changed, 1915 insertions, 89 deletions
- Architecture: 4-Layer Observability
  - Layer 0: events.jsonl (async PostToolUse hook, 8-field JSONL per tool call)
  - Layer 1: rtd-index.md (Lead-maintained, WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS entries)
  - Layer 2: Enhanced DIA (L1 pt_goal_link + L2 PT Goal Linkage)
  - Layer 3: Recovery (PreCompact snapshot + SessionStart RTD injection)
- 23 files, ~360 lines: 2 created, 21 modified
  - Hooks: on-rtd-post-tool.sh (NEW 147L), 3 hooks extended/rewritten, settings.json PostToolUse async
  - CLAUDE.md v7.0: §6 Observability RTD + directory spec, §9 RTD recovery rewrite
  - Protocol v3.0: L1/L2 PT Goal Linkage (optional, backward-compatible)
  - 7 skills × RTD Index template, 6 agents × RTD awareness
- Key decisions: AD-12~AD-29 (18 total), AD-29 ($CLAUDE_SESSION_ID best-effort)
- Plan: `docs/plans/2026-02-10-rtd-system-implementation.md` (1244L)
- Sessions: rtd-system (P1-3), rtd-write-plan (P4), rtd-validation (P5), rtd-execution (P6)

## COW Pipeline v2.0 — DELIVERED (2026-02-09)
- Commit: 0e603f3 — 149 files changed, 4857 insertions, 36181 deletions
- Architecture: Python SDK + CLI wrapper (Triple-Layer Verification)
  - L1: gemini-3-pro-image-preview (visual), L2: gemini-3-pro-preview (reasoning), L3: Opus 4.6 (logic)
- Package: `cow/core/` (SDK) + `cow/cli.py` (CLI) + `cow/config/` (config)
- 12 new files (~1536 lines), deleted cow-cli/ + cow-mcp/ + outputs/ (~36K lines)
- Tech: google-genai SDK v1.62.0, PIL Image, Mathpix v3/text, XeLaTeX multi-pass
- Key decisions: AD-8 (model role separation), AD-9 (fail-stop, no fallback)
- Plans: `docs/plans/2026-02-09-cow-v2-design.md` (778L) + `cow-v2-implementation.md` (2498L)
- Previous v1.0: Superseded (was c14d592, MCP server-centric, 53 files/7367L)

## INFRA v15 — DELIVERED (2026-02-20)
- PR: #69 (feat/infra-v15), squash merged — 29 files, 317+/2360- (net -2043L)
- Pipeline: 4 waves (W1-W4), 10/10 tasks ALL PASS
- Key deliverables:
  - PT description-first: description = primary state store (replaces metadata + state.md)
  - Per-Agent DPS profiles: minimal DPS templates with token targets (coordinator 80, analyst 100, implementer 150, infra-implementer 200)
  - 3-Tier Data Access: TaskList (coordination) → TaskGet (knowledge) → Read disk (metadata, Lead-only)
  - Coordinator demoted: Sub-Orchestrator → Synthesis Worker (removed silently-dropped Task() tools)
  - All agents explicit model:sonnet (prevent Opus 10x cost inheritance)
  - CLAUDE.md §3-§5 rewritten: Spawn Rules simplified, DPS v5→per-Agent profiles, all metadata→description
  - dps-construction-guide.md fully rewritten with per-Agent templates
  - DLAT SKILL.md + methodology.md: state.md→PT, DLAT_BASE→WORK_DIR
  - freewheelin skill deleted, pipeline-resume disabled from auto-load
  - 9 deprecated ref_*.md + CC_SECTIONS.md tombstoned
- Decisions: D01-D06 (3-Tier Data Access, metadata=Lead-only, tool-level enforcement, PT description=primary)

## INFRA v14 — DELIVERED (2026-02-20)
- Architecture: Single-session (removed Agent Teams/tmux multi-session)
- CLAUDE.md: v14, 193L, "Pipeline Architecture v14" title, Two-Channel Handoff [D17]
- Terminology: "Teammate" removed; only "Subagent" + "Work Directory" concepts remain
- DPS template: removed `COMM_PROTOCOL` section (P2P messaging gone)
- Cost model: 3 subagents ≈ 440K tokens (was 800K for teammates)
- Spawn pattern: all spawns use `run_in_background:true` + `context:fork` + `model:sonnet`
- Agents: 7 files, all subagent-only (no AT-mode dual-mode agents)
- Memory: MEMORY.md + ref_teams.md + ref_agents.md updated; pipeline-bugs.md created
- State: `~/.claude/doing-like-agent-teams/projects/infra-single-session-refactor/`

## INFRA v13 — DELIVERED (2026-02-20)
- PR: #66 (feat/infra-v13), commit: 3b77698 — 15 files, 692 insertions, 1216 deletions
- Pipeline: DLAT (P0→P6→P7→P8, P1-P5 skipped by user directive), CONDITIONAL_PASS
- Key deliverables:
  - CLAUDE.md: Semantic Integrity INVIOLABLE block + verify-coordinator P7 row + 200-250L policy
  - NEW: verify-coordinator (P7 synthesis coordinator — fills coordinator gap)
  - NEW: manage-codebase (Homeostasis — project source file cleanup domain)
  - NEW: ce-pre-grep-block.sh (BLOCKING exit 2 hook — Grep without path parameter)
  - DELETED: agent-organizer.md (wrong YAML, Haiku model, non-existent agents)
  - verify-* skills (5 files): refactored to project-independent scope
  - execution-cascade: semantic ambiguity resolved
  - pre-design-feasibility: CC constraint pre-check step added
- Requirements: 14 total (REQ-001~014), 12 implemented, 2 deferred (REQ-012 RSIL format, REQ-013 PT schema)
- State: `~/.claude/doing-like-agent-teams/projects/infra-v13-design/session-summary.md`

## RSIL System — DELIVERED (2026-02-09)
- P1→P6→P9 complete (P7-8 skipped, markdown-only)
- Two-Skill System: `/rsil-global` (452L, auto-invoke) + `/rsil-review` (549L, user-invoke)
- Shared Foundation: 8 Lenses + AD-15 + Boundary Test (~85L embedded copy per skill)
- Agent Memory: `~/.claude/agent-memory/rsil/MEMORY.md` (53L seed, 4-section schema)
- Tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`
- Plan: `docs/plans/2026-02-09-rsil-system.md` (1231L, 26 specs)
- Architecture Decisions: AD-6~AD-11

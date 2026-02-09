# Claude Code Memory

## COW Pipeline — DELIVERED (2026-02-09)
- **Status:** Phase 1-6 COMPLETE, Phase 7-8 DEFERRED, Phase 9 DELIVERED
- **Commit:** c14d592 — 53 files, 7367 lines added
- **Package:** `cow/cow-mcp/` (Python, FastMCP, Pydantic 2.0)
- **6 MCP Servers:** cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage
- **33 Python files** + .mcp.json registration
- **Tech:** Mathpix API v3, Gemini 3-pro-preview, XeLaTeX+kotex, FastMCP (MCP SDK v1.26.0)
- **Pipeline artifacts:** `.agent/teams/cow-pipeline-redesign/` (GC-v6, PT-v4, 3 gate records)
- **Plan:** `docs/plans/2026-02-09-cow-pipeline-redesign.md` (1274L)
- **Key deviations:** FastMCP (DEV-1), setuptools.build_meta (DEV-2), cow_ prefix (DEV-4)
- **First test:** Session cbcc34036137 — blacklabel_circle_9.png, 6-stage end-to-end complete (17KB PDF)
- **Code fixes applied:** ocr/client.py (full params + opts_conflict fix), vision/gemini.py (model name fix)
- **Docs cleanup:** 14 old Mathpix docs deleted → single `docs/mathpix-api-reference.md` (923L)
- **Known bug:** BUG-COW-1 — Stage 5 Python raw string `\!` breaks TikZ `blue!15` syntax
- **Next steps:** BUG-COW-1 systematic fix + more test images + iterative pipeline improvement

### Pending options (user decides):
  1. Ontology Framework T-1 brainstorming (`docs/plans/2026-02-08-ontology-bridge-handoff.md`)
  2. task-api-guideline.md NLP conversion (v4.0/530 lines)
  3. P4-R1/R2, P5-R1/R2 backlog (30 lines across 2 skills)

## Language Policy [PERMANENT] (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only (GC, directives, tasks, L1/L2/L3, gates, hooks, designs, CLAUDE.md, agent .md, MEMORY.md)
- CLAUDE.md §0 Language Policy
- Rationale: token efficiency for Opus 4.6, machine-readable consistency, cross-agent parsing

## Current Infrastructure State (v6.0) (2026-02-09)
- CLAUDE.md: v6.2 (~178 lines, §0-§10) — v6.1 + /rsil-global auto-invoke after §2 Phase Pipeline table
- task-api-guideline.md: v4.0 (~530 lines, §1-§14) — unchanged in this cycle
- agent-common-protocol.md: v2.1 (84 lines) — v2.0 + RSI fix: PT task list scope clarification
- Agents: 6 types, 442 total lines (NLP v2.0), disallowedTools = TaskCreate+TaskUpdate only
- Skills: 7 pipeline skills + `/permanent-tasks` + `/rsil-review` + `/rsil-global` (NEW — auto-invoke INFRA health)
- Hooks: 3 lifecycle hooks (SubagentStart, PreCompact, SessionStart) — reduced from 8
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
| 004 | `/plan-validation-pipeline` | P5 | DONE + NLP v6.0 + Phase 0 |
| 005 | `/verification-pipeline` | P7-8 | DONE + NLP v6.0 + Phase 0 + INFRA RSI |
| 006 | `/delivery-pipeline` | P9 | DONE (422L) — Phase 6 COMPLETE, Gate 6 APPROVED |
| 007 | `/rsil-review` | — | DONE (549L) — Meta-Cognition framework, 8 Lenses, REFINED via RSIL System |
| 008 | `/rsil-global` | — | DONE (452L) — Auto-invoke INFRA health, Three-Tier Observation Window |
| — | `/permanent-tasks` | — | DONE (GC replacement skill) |
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

## RSIL System — DELIVERED (2026-02-09)
- **Status:** DELIVERED — P1→P6→P9 complete (P7-8 skipped, markdown-only)
- **Two-Skill System:** `/rsil-global` (452L, auto-invoke via CLAUDE.md §2) + `/rsil-review` (549L, user-invoke)
- **Shared Foundation:** 8 Lenses + AD-15 + Boundary Test (~85L embedded copy per skill, verified identical)
- **CLAUDE.md §2:** 5-line NL discipline for auto-invoke trigger
- **Agent Memory:** `~/.claude/agent-memory/rsil/MEMORY.md` (53L seed, 4-section schema)
- **Tracker:** `docs/plans/2026-02-08-narrow-rsil-tracker.md` (283L, G-{N}/P-R{N} namespacing)
- **Plan:** `docs/plans/2026-02-09-rsil-system.md` (1231L, 26 specs)
- **Architecture Decisions:** AD-6~AD-11 (findings-only, three-tier, BREAK via AskUser, tracker namespacing, embedded copy, shared memory)
- **Sessions:** rsil-system (P1-3), rsil-write-plan (P4), rsil-validation (P5), rsil-execution (P6)
- **Cumulative data:** 24 findings, 79% acceptance

## Deferred Work
- CH-002~005: `docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml`
- Agent memory initialization: Create MEMORY.md templates for each agent type

## Topic Files Index
- `memory/infrastructure-history.md` — DIA evolution (v1→v4), Agent Teams redesign, Task API investigation, Ontology
- `memory/skill-optimization-history.md` — SKL-001/002/003 detailed records
- `memory/agent-teams-bugs.md` — BUG-001 details and workaround

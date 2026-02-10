# Claude Code Memory

## RTD System + INFRA v7.0 — DELIVERED (2026-02-10)
- **Status:** Phase 0→1→2→3→4→5→6→9 COMPLETE (P7-8 skipped, markdown-only)
- **Commit:** TBD (pending Phase 9 commit)
- **Architecture:** 4-Layer Observability
  - Layer 0: events.jsonl (async PostToolUse hook, 8-field JSONL per tool call)
  - Layer 1: rtd-index.md (Lead-maintained, WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS entries)
  - Layer 2: Enhanced DIA (L1 pt_goal_link + L2 PT Goal Linkage)
  - Layer 3: Recovery (PreCompact snapshot + SessionStart RTD injection)
- **23 files, ~360 lines:** 2 created, 21 modified
  - Hooks: on-rtd-post-tool.sh (NEW 147L), 3 hooks extended/rewritten, settings.json PostToolUse async
  - CLAUDE.md v7.0: §6 Observability RTD + directory spec, §9 RTD recovery rewrite
  - Protocol v3.0: L1/L2 PT Goal Linkage (optional, backward-compatible)
  - 7 skills × RTD Index template, 6 agents × RTD awareness
- **Key decisions:** AD-12~AD-29 (18 total), AD-29 ($CLAUDE_SESSION_ID doesn't exist — best-effort)
- **Phase 5 amendments:** AD-29 (session registry limitation), CH-5 (permanent-tasks Cross-Cutting)
- **RTD Pilot:** 5 DPs dogfooded during own implementation, ~120 tok/entry validated
- **2 implementers:** Impl-1 (hooks+config 8 files) ∥ Impl-2 (docs 15 files), zero overlap
- **Gate 6:** G6-1~G6-7 ALL PASS, interface consistency verified
- **Plan:** `docs/plans/2026-02-10-rtd-system-implementation.md` (1244L)
- **Sessions:** rtd-system (P1-3), rtd-write-plan (P4), rtd-validation (P5), rtd-execution (P6)
- **Observability:** `.agent/observability/rtd-system/` (pilot data persists)

## COW Pipeline v2.0 — DELIVERED (2026-02-09)
- **Status:** Phase 4→5→6→9 COMPLETE (P7-8 skipped per user mandate)
- **Commit:** 0e603f3 — 149 files changed, 4857 insertions, 36181 deletions
- **Architecture:** Python SDK + CLI wrapper (Triple-Layer Verification)
  - L1: gemini-3-pro-image-preview (visual), L2: gemini-3-pro-preview (reasoning), L3: Opus 4.6 (logic)
- **Package:** `cow/core/` (SDK) + `cow/cli.py` (CLI) + `cow/config/` (config)
- **12 new files** (~1536 lines): gemini_loop, ocr, diagram, layout_design, layout_verify, compile, cli, models, profiles, 3x __init__
- **Deleted:** cow-cli/ (~90 files), cow-mcp/ (~33 files), outputs/, artifacts (~36K lines)
- **Tech:** google-genai SDK v1.62.0 (sync API), PIL Image, Mathpix v3/text, XeLaTeX multi-pass
- **Key decisions:** AD-8 (model role separation), AD-9 (fail-stop, no fallback), CH-01/02/03 (Phase 5 amendments)
- **Pipeline artifacts:** `.agent/teams/cow-v2-{write-plan,validation,execution}/`
- **Plans:** `docs/plans/2026-02-09-cow-v2-design.md` (778L) + `cow-v2-implementation.md` (2498L)
- **4 implementers:** Foundation → {Extraction, Layout} parallel → CLI+Cleanup
- **Gate 6:** All 7 criteria PASS, FROZEN CONTRACT verified
- **Previous v1.0:** Superseded (was c14d592, MCP server-centric, 53 files/7367L)
- **Next steps:** End-to-end integration testing with sample images, MCP server cleanup in .claude.json

### Pending options (user decides):
  1. Ontology Framework T-1 brainstorming (`docs/plans/2026-02-08-ontology-bridge-handoff.md`)
  2. task-api-guideline.md NLP conversion (v4.0/530 lines)
  3. .claude.json MCP server entries cleanup (remove v1.0 cow-* servers)

## Language Policy [PERMANENT] (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only (GC, directives, tasks, L1/L2/L3, gates, hooks, designs, CLAUDE.md, agent .md, MEMORY.md)
- CLAUDE.md §0 Language Policy
- Rationale: token efficiency for Opus 4.6, machine-readable consistency, cross-agent parsing

## Current Infrastructure State (v7.0) (2026-02-10)
- CLAUDE.md: v7.0 (~206 lines, §0-§10) — v6.2 + §6 Observability RTD + §6 observability dir + §9 RTD recovery
- task-api-guideline.md: v4.0 (~530 lines, §1-§14) — unchanged
- agent-common-protocol.md: v3.0 (~108 lines) — v2.1 + L1/L2 PT Goal Linkage (optional)
- Agents: 6 types (~460 lines) — v2.0 + RTD awareness (pt_goal_link + auto-capture notice)
- Skills: 7 pipeline skills + `/permanent-tasks` + `/rsil-review` + `/rsil-global` — all 7 pipeline skills + permanent-tasks have RTD Index template
- Hooks: 4 lifecycle hooks (SubagentStart, PreCompact, SessionStart, **PostToolUse NEW**) — PostToolUse async, captures ALL tools
- Observability: `.agent/observability/{project-slug}/` — rtd-index.md, events.jsonl, session-registry.json, snapshots/
- Verification: Natural language understanding verification (unchanged)
- MCP Tools: sequential-thinking (mandatory all), tavily/context7 (mandatory by phase), github (as needed)
- Detailed history: `memory/infrastructure-history.md`

## Skill Pipeline Status (2026-02-10)
| SKL | Skill | Phase | Status |
|-----|-------|-------|--------|
| 001 | `/brainstorming-pipeline` | P1-3 | DONE + NLP v6.0 + Phase 0 + RTD template |
| 002 | `/agent-teams-write-plan` | P4 | DONE + NLP v6.0 + Phase 0 + RTD template |
| 003 | `/agent-teams-execution-plan` | P6 | DONE + NLP v6.0 + Phase 0 + RTD template |
| 004 | `/plan-validation-pipeline` | P5 | DONE + NLP v6.0 + Phase 0 + RTD template |
| 005 | `/verification-pipeline` | P7-8 | DONE + NLP v6.0 + Phase 0 + INFRA RSI + RTD template |
| 006 | `/delivery-pipeline` | P9 | DONE (422L) + RTD template |
| 007 | `/rsil-review` | — | DONE (549L) — Meta-Cognition framework, 8 Lenses |
| 008 | `/rsil-global` | — | DONE (452L) — Auto-invoke INFRA health, Three-Tier |
| — | `/permanent-tasks` | — | DONE + RTD template (CH-5: new Cross-Cutting section) |
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
- Observability Dashboard UI: Separate /brainstorming-pipeline (reads events.jsonl + rtd-index.md)
- RSIL Audit S-2~S-7: Resume after INFRA v7.0 (tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`)

## Topic Files Index
- `memory/infrastructure-history.md` — DIA evolution (v1→v4), Agent Teams redesign, Task API investigation, Ontology
- `memory/skill-optimization-history.md` — SKL-001/002/003 detailed records
- `memory/agent-teams-bugs.md` — BUG-001 details and workaround

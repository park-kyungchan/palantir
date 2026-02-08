# Claude Code Memory

## Next Session Action [PRIORITY] (2026-02-08)
- **Ontology Framework T-1 brainstorming** — 사용자가 다음 세션에서 시작 예정
- **실행:** `/brainstorming-pipeline Ontology Framework T-1: ObjectType 정의 시스템 설계`
- **핸드오프:** `docs/plans/2026-02-08-ontology-bridge-handoff.md` (b3c1012, 421 lines, 9 user decisions)
- **참조:** `bridge-reference/` (5 files, 3842 lines) — T-1용 bridge-ref-objecttype.md (1016L)
- **Topic 순서:** T-1 ObjectType → T-2 LinkType → T-3 ActionType → T-4 Integration
- **세션 종료 시 상태 보고 완료:** ASCII 시각화로 전체 현황 + Topic별 시작 가이드 제공됨
- **Other pending options (user decides):**
  1. SKL-006: delivery pipeline — Phase 6 COMPLETE, RSIL + delivery pending
  2. task-api-guideline.md NLP conversion (v4.0/530 lines)

## Language Policy [PERMANENT] (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only (GC, directives, tasks, L1/L2/L3, gates, hooks, designs, CLAUDE.md, agent .md, MEMORY.md)
- CLAUDE.md §0 Language Policy
- Rationale: token efficiency for Opus 4.6, machine-readable consistency, cross-agent parsing

## Current Infrastructure State (v6.0) (2026-02-08)
- CLAUDE.md: v6.1 (172 lines, §0-§10) — v6.0 + RSI fix: PT directive embedding clarification
- task-api-guideline.md: v4.0 (~530 lines, §1-§14) — unchanged in this cycle
- agent-common-protocol.md: v2.1 (84 lines) — v2.0 + RSI fix: PT task list scope clarification
- Agents: 6 types, 442 total lines (NLP v2.0), disallowedTools = TaskCreate+TaskUpdate only
- Skills: 7 pipeline skills + `/permanent-tasks` + `/rsil-review` (561L, NEW — Meta-Cognition framework)
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
| 007 | `/rsil-review` | — | DONE (561L) — Meta-Cognition framework, 8 Lenses |
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

## RSIL Framework [PERMANENT] (2026-02-08)
- **Skill:** `/rsil-review` (561 lines) — Meta-Cognition-Level quality review framework
- **Design:** Universal Framework × $ARGUMENTS = target-specific review (no hardcoding)
- **Architecture:** Static Layer (Lenses, Layer defs, AD-15) + Dynamic ($ARGUMENTS + !`shell`) + Lead R-0 Synthesis
- **8 Meta-Research Lenses** (distilled from pilot data, universally applicable):
  - L1: TRANSITION INTEGRITY — 상태 전이 명시적/검증 가능?
  - L2: EVALUATION GRANULARITY — 다중 기준 개별 증거?
  - L3: EVIDENCE OBLIGATION — 산출물이 과정 증거 요구?
  - L4: ESCALATION PATHS — 중대 발견에 적절한 에스컬레이션?
  - L5: SCOPE BOUNDARIES — scope 경계 접근 처리?
  - L6: CLEANUP ORDERING — 해체 선행조건 순서화?
  - L7: INTERRUPTION RESILIENCE — 중단 대비 중간 상태 보존?
  - L8: NAMING CLARITY — 식별자 모든 context에서 명확?
- **Lenses evolve:** 새 패턴 발견 시 L9, L10 추가 가능
- **Pilot data:** 8 findings, 50% acceptance (tracker: `docs/plans/2026-02-08-narrow-rsil-tracker.md`)
- **Handoff (for future brainstorming):** `docs/plans/2026-02-08-narrow-rsil-handoff.md`

## Deferred Work
- CH-002~005: `docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml`
- Agent memory initialization: Create MEMORY.md templates for each agent type

## Topic Files Index
- `memory/infrastructure-history.md` — DIA evolution (v1→v4), Agent Teams redesign, Task API investigation, Ontology
- `memory/skill-optimization-history.md` — SKL-001/002/003 detailed records
- `memory/agent-teams-bugs.md` — BUG-001 details and workaround

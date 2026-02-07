# Claude Code Memory

## Language Policy [PERMANENT] (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only (GC, directives, tasks, L1/L2/L3, gates, hooks, designs, CLAUDE.md, agent .md, MEMORY.md)
- CLAUDE.md v3.2 §0 Language Policy added
- Rationale: token efficiency for Opus 4.6, machine-readable consistency, cross-agent parsing

## CH-006 DIA v4.0 COMPLETED (2026-02-07)
- DIA v3.1 → v4.0: Team Memory + Context Delta + Hook Enhancement (Layer 4)
- Pipeline: brainstorming Phase 1→2→3 (researcher-1, architect-1), then Lead direct implementation
- 12 files modified across 5 migration steps (bottom-up: hooks → settings → task-api → CLAUDE.md → agents)
- CLAUDE.md: v4.0 (§3 Lead/Teammate duties, §4 formats, §6 Team Memory + Delta, [PERMANENT] Layer 4 + duties #8/#9/#4a)
- task-api-guideline.md: v4.0 (§11 CIP delta + IP-010, §13 Team Memory, §14 Context Delta)
- Hooks: on-teammate-idle.sh (NEW), on-task-completed.sh (NEW), on-subagent-start.sh (enhanced GC inject)
- settings.json: TeammateIdle + TaskCompleted entries added (7 hook events total)
- 6 agent .md: ACK format enhanced, TEAM-MEMORY read/write/relay instructions per tool access
- 4-Layer DIA: CIP (delivery) → DIAVP (comprehension) → LDAP (systemic) → Hooks (production, LLM-independent)
- Key ADRs: AD-001 (Direct Edit implementer/integrator only, Lead relay others), AD-002 (Hook=Speed Bump), AD-003 (5-condition fallback), AD-004 (REPLACED op), AD-005 (devils-advocate read-only)
- Architecture artifacts preserved at: docs/plans/ not created (CH-006 used .agent/teams/ch006-dia-v4/)

### Current Infrastructure State (v4.0 — DIA + LDAP + Team Memory + Context Delta + Hooks)
- CLAUDE.md: v4.0 (~340 lines, §0 Language + all DIA v4 additions)
- task-api-guideline.md: v4.0 (~530 lines, §13 Team Memory, §14 Context Delta)
- Agents: 6 types, all with TEAM-MEMORY instructions + enhanced ACK format
- Hooks: 7 events (SubagentStart, SubagentStop, PostToolUse:TaskUpdate, PreCompact, SessionStart:compact, TeammateIdle, TaskCompleted)
- 4-Layer DIA: CIP → DIAVP → LDAP → Hooks

## Ontology Definition Enhancement (2026-02-06)

### Completed Work
- Phase 1 Core Primitives: ObjectType, Property, SharedProperty 정의 문서 고도화
- 6개 파일 생성 (6,226줄 총): ObjectType.md, Property.md, SharedProperty.md, DEFINITIONS.md, TAXONOMY.md, NAMING_AUDIT.md
- 11-section template: formal_definition(NC/SC/BC), official_definition, semantic_definition, structural_schema, quantitative_decision_matrix, validation_rules, canonical_examples, anti_patterns, integration_points, migration_constraints, runtime_caveats
- WF-1 Gap Report: 10개 gap 식별 (G1-G10), 9개 해소, G3(LinkType vs FK) Phase 2 이관
- NAMING_AUDIT: session 파일에서 53 violations + 4 warnings 발견

### Key Decisions
- Formal Definition = Necessary/Sufficient/Boundary Conditions 구조
- Quantitative thresholds: OT판단(Property≥3, Link≥2, 조회>30%), SP승격(OT≥3, 의미100%)
- Interface apiName: camelCase (공식), session 파일의 PascalCase는 위반
- Status enum: ACTIVE, EXPERIMENTAL, DEPRECATED만 확인됨 (EXAMPLE/ENDORSED 미검증)
- SharedProperty: GA (NOT Beta)
- session 원본 파일: 보존 (수정하지 않음)

### Verification Results (2026-02-06)
- V1 Structural: PASS | V2 Cross-Ref: FAIL→FIXED | V3 Official Doc: FAIL→FIXED | V4 Logic: PASS
- 27 fixes applied across 5 files

### Critical Corrections (V3 Official Doc)
- Interface는 local property(권장) 또는 SharedProperty로 구성 가능 (SharedProperty 필수 아님!)
- apiName: 변경 가능 (Overview page) 하나 강력 비권장
- PK: OSv2에서 변경 가능하나 기존 edits 전부 삭제됨
- Decimal: standalone property base type 아님 (Struct field에서만 유효)
- Action forbidden params: Float, Double, Decimal + Byte, Short, geo time-series

### Next Steps
- Phase 2: LinkType, Interface 정의 문서
- 코드베이스 마이그레이션: ObjectType 후보 식별 → 승인 → Property 정의 → SP 승격

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

### Current Infrastructure State (v2.0 — DIA Enforcement)
- CLAUDE.md: v2.0 Team Constitution (~221 lines, 8 sections + enhanced [PERMANENT] with WHY)
- task-api-guideline.md: v2.0 (338 lines, 12 sections — §11 DIA Protocol, §12 TASK_LIST_ID)
- Agents: 6 types, all with `memory: user`, DIA protocol, TaskCreate/TaskUpdate in disallowedTools
- Hooks: 5 scripts in `.claude/hooks/` (SubagentStart/Stop, TaskUpdate, PreCompact, SessionStart:compact)
- Settings: hooks config added to `.claude/settings.json`
- [PERMANENT]: WHY reasoning + enforcement mechanism + failure handling + cross-references
- Team outputs: `.agent/teams/{session-id}/`

### Agent Teams Smoke Test PASSED (2026-02-07)
- Full pipeline: TeamCreate→TaskCreate→Spawn→Execute→Gate→Shutdown→TeamDelete
- 13/13 test items PASSED

### Task API Deep Investigation (2026-02-07)
- task-api-guideline.md v1.0→v1.1 (4 new sections: Storage Architecture, Known Issues, Metadata Ops, Dependency Behavior)
- Findings report: `.agent/teams/task-api-investigation/phase-2/task-api-findings.md`
- ISS-001 [HIGH]: Completed task files may auto-delete from disk (trigger unknown)
- ISS-002 [MED]: TaskGet shows raw blockedBy (includes completed), TaskList filters correctly
- ISS-003 [HIGH]: Task orphaning on context clear (use Team scope always)
- ISS-004 [LOW]: highwatermark can be stale vs actual max ID
- Dependency: addBlockedBy/addBlocks = bidirectional auto-sync, blocker completion ≠ auto-removal
- Cross-agent: All CRUD operations work across Lead↔Teammate in team scope
- Metadata: merge, overwrite, null=delete all verified
- tmux mouse scroll: `~/.tmux.conf` created (mouse on, history 50000, vi mode)

### DIA Enforcement v2.0 Implemented (2026-02-07)
- 3-Protocol Architecture: CIP (Context Injection) + DIAVP (Impact Verification) + Lead-Only Task API
- 8 GAPs resolved: GAP-001~008 (read verification, understanding verification, context propagation, etc.)
- Verification Tiers: TIER 0 (devils-advocate exempt), TIER 1 (implementer/integrator, 6 IAS, 10 RC), TIER 2 (architect/tester, 4 IAS, 7 RC), TIER 3 (researcher, 3 IAS, 5 RC)
- Two-Gate Flow: Gate A (Impact) → Gate B (Plan) for implementer/integrator
- Enhanced [PERMANENT]: WHY reasoning, enforcement mechanism, failure escalation, cross-references
- Agent `memory: user` field: persistent cross-session learning for all 6 agent types
- Hooks: SubagentStart/Stop lifecycle logging, TaskUpdate tracking, PreCompact state save, SessionStart:compact DIA recovery
- Key insight: "Protocol ≠ Enforcement" — disallowedTools for hard enforcement, IAS echo-back for soft enforcement

### CH-001 LDAP Implementation COMPLETED (2026-02-07)
- Design: `docs/plans/2026-02-07-ch001-ldap-design.yaml` (553 lines)
- Plan: `docs/plans/2026-02-07-ch001-ldap-implementation.md` (757 lines)
- Commit: `b363232` — 7 files, 179 insertions, 4 deletions
- DIA v2.0 → v3.0: Layer 3 LDAP (GAP-003a interconnection + GAP-003b ripple)
- Pipeline: Phase 1→6→6.V→9, single implementer, 3 tasks (A:core, B:agents, C:validation)
- LDAP Bootstrap: Protocol applied during its own implementation (self-referential success)
- DIA Results: RC 10/10 PASS, LDAP Q1(INTERCONNECTION_MAP) STRONG, Q2(RIPPLE_TRACE) STRONG
- Gate 6: 7/7 criteria PASS, V1-V5 cross-references validated
- Output: `.agent/teams/ch001-ldap/` (orchestration-plan, global-context, phase-6 gate-record, L1/L2)

### Current Infrastructure State (v3.0 — DIA + LDAP)
- CLAUDE.md: v3.0 (~247 lines, LDAP in §3, §4, [PERMANENT] §7+§2a)
- task-api-guideline.md: v3.0 (~408 lines, §11 Layer 3 LDAP block)
- Agents: 5 types with Phase 1.5 (implementer/integrator HIGH:2Q, architect MAXIMUM:3Q+alt, tester/researcher MEDIUM:1Q)
- devils-advocate: TIER 0 exempt, no Phase 1.5 (unchanged)
- 3-Layer DIA: CIP (delivery) → DIAVP (comprehension) → LDAP (systemic impact)
- Key lesson: Implementation plan §5/§6 had intentional placeholder differences in [CHALLENGE-RESPONSE] format (`{defense}` in protocol def vs `{defense with specific evidence}` in agent instructions) — this is correct abstraction-level separation, not a bug

### Superpowers Plugin Compatibility Analysis (2026-02-07)
- Report: `docs/plans/2026-02-07-superpowers-agent-teams-compatibility-analysis.md`
- 14 skills analyzed: 3 INCOMPATIBLE, 3 CONFLICTS, 1 OVERLAPS, 2 ADAPTABLE, 5 COMPATIBLE
- Core workflow chain (writing-plans → executing-plans / subagent-driven-dev) is INCOMPATIBLE
- TodoWrite vs TaskCreate: 5 skills affected
- Ephemeral vs persistent agents: 3 skills affected
- Recommended: Option C (Replace Workflow Chain Only) — minimal scope, preserve solo-mode
- CH-001 plan (757 lines) serves as Agent Teams plan format precedent

### Superpowers Skill Optimization — SKL-001 brainstorming-pipeline COMPLETED (2026-02-07)
- Strategy: Option 3 (Split) — brainstorming (solo, untouched) + brainstorming-pipeline (Agent Teams, new)
- Design: `docs/plans/2026-02-07-brainstorming-pipeline-design.md` (9 sections)
- SKILL.md: `.claude/skills/brainstorming-pipeline/SKILL.md` (custom skill, ~350 lines)
- Scope: Phase 1-3 only (Discovery → Research → Architecture), Clean Termination
- DIA: Delegated to CLAUDE.md [PERMANENT] (skill specifies tier/intensity, not protocol)
- Output: global-context.md versioned (v1→v2→v3), L1/L2/L3 per phase
- Output Format Standard: YAML (structured) + Markdown (narrative) — NOT XML. Token efficiency > verbosity.

### Superpowers Skill Optimization — SKL-002 agent-teams-write-plan COMPLETED (2026-02-07)
- Strategy: Option 3 (Split) — writing-plans (solo, untouched) + agent-teams-write-plan (Agent Teams, new)
- Design: `docs/plans/2026-02-07-agent-teams-write-plan-design.md` (1,122 lines, 9 sections)
- SKILL.md: `.claude/skills/agent-teams-write-plan/SKILL.md` (274 lines)
- Scope: Phase 4 only (Detailed Design), brainstorming-pipeline 출력 전용 입력
- Pipeline: Input Discovery → Team Setup → Architect Spawn+DIA → Plan Generation → Gate 4 → Clean Termination
- Template: 10-section CH-001 format (§1-§10), parametric + generalized
- Key innovations: Verification Level tags (AD-3), AC-0 mandatory (AD-4), V6 Code Plausibility (AD-5), Read-First-Write-Second (AD-10), 4-layer task-context (AD-7)
- GC versioning: brainstorming GC-v3 input → write-plan GC-v4 output
- DIA: TIER 2 + LDAP MAXIMUM (3Q+alt) for architect, delegated to CLAUDE.md [PERMANENT]
- Full brainstorming-pipeline execution: Phase 1→2→3, researcher-1 + architect-1, 3 gates all PASSED
- Session artifacts: `.agent/teams/agent-teams-write-plan/` (GC-v3, phase-1~3 gate records, L1/L2/L3)

### Skill Optimization Process — Reusable Pattern [PERMANENT]
- **claude-code-guide agent 필수 조사**: 매 스킬 개선 시 해당 스킬 특성에 맞는 최신 Claude Code 기능/Opus 4.6 최적화 포인트를 반드시 조사
- **공통 개선사항 (전 스킬 적용)**:
  1. Dynamic Context Injection (`!`shell``) — 스킬 로딩 시 자동으로 관련 context 주입. 스킬별 다른 shell 명령.
  2. `$ARGUMENTS` 변수 — 사용자 입력을 skill에서 직접 수신
  3. Opus 4.6 Measured Language — 과도한 ALL CAPS/[MANDATORY] 대신 자연스러운 지시문
  4. `argument-hint` frontmatter — autocomplete UX 개선
- **스킬별 고유 개선사항**: claude-code-guide agent 조사 결과에서 도출 (매번 다름)
- **Design file format**: Markdown + YAML frontmatter (전 스킬 공통)
- **순서**: brainstorming-pipeline(done) → writing-plans → verification → execution skills → ...

### Superpowers Skill Optimization — SKL-003 execution-pipeline COMPLETED (2026-02-07)
- Strategy: Option 3 (Split) — executing-plans (solo, untouched) + execution-pipeline (Agent Teams, new)
- Design: `docs/plans/2026-02-07-execution-pipeline-design.md` (~610 lines, 13 sections)
- SKILL.md: `.claude/skills/execution-pipeline/SKILL.md` (~532 lines)
- Scope: Phase 6 only (Implementation), agent-teams-write-plan 출력 전용 입력
- Pipeline: Input Discovery → Team Setup → Adaptive Spawn+DIA → Task Execution+Review → Gate 6 → Clean Termination
- Key Architecture Decisions (AD-1~AD-8):
  - AD-1: UQ resolution (fix loop=3 fixed, final review=conditional, manipulation=3-layer, context=per-task checkpoint)
  - AD-2: Adaptive spawn via connected components algorithm, min(components, 4) implementers
  - AD-3: Two-stage review Option B (implementer delegation, 58% Lead context savings)
  - AD-4: Cross-boundary 4-stage escalation protocol
  - AD-5: Gate 6 per-task(G6-1~5) + cross-task(G6-6~7) + 3-layer defense
  - AD-6: GC-v4→v5 delta
  - AD-7: Clean termination (no auto-chain to Phase 7)
  - AD-8: SKILL.md design (follows precedent skills pattern)
- brainstorming-pipeline execution: Phase 1→2→3, researcher-1 + architect-1, 3 gates PASSED
- DIA: architect RC 7/7 PASS, LDAP MAXIMUM 4/4 STRONG
- Phase 4 skipped: skill-draft.md deployed directly as SKILL.md
- Session artifacts: `.agent/teams/execution-pipeline/` (GC-v3, phase-1~3 gate records, L1/L2/L3)

### MCP Tools Mandatory Usage (2026-02-07)
- CLAUDE.md v3.0→v3.1: Added §7 "MCP Tools — Mandatory Usage"
- sequential-thinking: Mandatory for ALL agents in ALL phases (analysis, judgment, design, gate, verification)
- tavily: Mandatory in Phase 2-4, as needed in other phases (latest docs, API changes, best practices)
- context7: Mandatory in Phase 2/4/6, as needed in others (library documentation lookup)
- github: Mandatory in Phase 2, as needed in others (repo exploration, issue/PR context)
- 6 agent .md files updated: tavily + context7 tools added to ALL agents, execution instructions strengthened
- Key principle: "외부 자료 비교/분석/검증은 Lead를 포함한 모든 Teammates가 수행"

### Current Infrastructure State (v3.1 — DIA + LDAP + MCP Mandatory)
- CLAUDE.md: v3.1 (~300 lines, §7 MCP Tools Mandatory Usage added)
- Agents: 6 types, ALL with sequential-thinking + context7 + tavily tools
- §번호 변경: Safety Rules §7→§8, Compact Recovery §8→§9

### Agent Teams Skill Pipeline (Current State)
- `/brainstorming-pipeline` (SKL-001): Phase 1-3 — DONE
- `/agent-teams-write-plan` (SKL-002): Phase 4 — DONE
- `/execution-pipeline` (SKL-003): Phase 6 — DONE
- Phase 5 (plan-validation): TODO
- Phase 7-8 (verification/integration pipeline): TODO
- Phase 9 (delivery): TODO

### BUG-001: permissionMode: plan blocks MCP tools [CRITICAL]
- `permissionMode: plan` teammates (researcher, architect) stuck on MCP tool calls
- **Workaround: 스폰 시 항상 `mode: "default"` 지정** (disallowedTools가 이미 mutation 차단)
- 상세: `memory/agent-teams-bugs.md` 참조

### CH-006 DIA v4.0 진행 중 (2026-02-07)
- Scope: Team Memory(실시간 공유) + Context Delta + Hook GC Verification
- Approach: Lead 직접 구현 (brainstorming P1-3 후)
- Phase 1: COMPLETE, Phase 2: IN PROGRESS (researcher-1)
- Artifacts: `.agent/teams/ch006-dia-v4/`

### Next Steps
- CH-006 DIA v4.0 완료 → plan-validation (Phase 5) 스킬
- CH-002~005: Deferred (see docs/plans/2026-02-07-ch002-ch005-deferred-design.yaml)

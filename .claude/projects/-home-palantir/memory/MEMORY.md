# Claude Code Memory

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

### Next Steps
- PR creation (user decision)
- Superpowers plugin adaptation for Agent Teams compatibility
- Agent memory initialization: create MEMORY.md templates for each agent type

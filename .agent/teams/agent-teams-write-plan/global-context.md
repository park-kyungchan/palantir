---
version: GC-v3
created: 2026-02-07
feature: agent-teams-write-plan
complexity: MEDIUM
---

# Global Context — agent-teams-write-plan

## Scope

**Goal:** `writing-plans`의 Agent Teams 최적화 버전인 `agent-teams-write-plan` 커스텀 스킬을 생성하여 Phase 4 (Detailed Design)를 orchestrate한다.

**In Scope:**
- Phase 4 전용 스킬 (Detailed Design → 구현 계획 문서 생성)
- brainstorming-pipeline 출력 (GC-v3 + architecture artifacts) 입력
- Architect teammate (1명) spawn + DIA v3.0 (TIER 2 + LDAP MAXIMUM: 3Q+alt)
- CH-001 포맷 기반 구현 계획 문서 생성 (10개 섹션)
- 이중 저장: `docs/plans/` (장기 보존) + `.agent/teams/{session-id}/` (L1/L2/L3)
- GC-v3 → GC-v4 업데이트 (Phase 4 완료 반영)
- Skill Optimization Process [PERMANENT] 적용 (Dynamic Context Injection, $ARGUMENTS, argument-hint)
- Design document + SKILL.md 생성

**Out of Scope:**
- Phase 5, Phase 6+, 원본 writing-plans 수정, 독립 사용, devils-advocate 검증

**Approach:** Architect가 CH-001 포맷으로 구현 계획을 직접 작성. Lead는 DIA 검증 + Gate 4 평가만 수행.

**Success Criteria:**
- SKILL.md 1개 파일 생성
- Design document 1개 생성
- brainstorming-pipeline과 자연스럽게 연결되는 파이프라인
- 기존 파일 0개 수정

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: COMPLETE (Gate 3 APPROVED)

## Architecture Decisions

### AD-1: Architect as plan author (not Lead)
CLAUDE.md §2 mandates architect for Phase 4. Delegate Mode preserved. DIA verification enabled.

### AD-2: 10-section template from CH-001
Proven format with 1 successful precedent. Generalizes well with parametric fields.

### AD-3: Verification Level tags in §5
Compensates for architect's Read-only tool constraint. Signals confidence to implementers.
Levels: READ_VERIFIED > PATTERN_BASED > DESIGN_ONLY

### AD-4: AC-0 mandatory in every task
Every TaskCreate definition must include AC-0 (Plan Verification Step).
Implementer verifies plan accuracy against current file state before applying changes.

### AD-5: V6 Code Plausibility in §7
New 6th validation category. Checks code blocks reference real files, imports exist,
function signatures match, line numbers correct. Mandatory in every plan.

### AD-6: Hybrid auto-discovery input
Auto-scan `.agent/teams/*/global-context.md` for Phase 3 COMPLETE + user confirm.
Or accept explicit $ARGUMENTS session-id/path.

### AD-7: 4-layer task-context for architect
GC-v3 (full embedding) + L2-summary (inline) + L3 path (reference) + CH-001 (exemplar).
Ensures context continuity across brainstorming→write-plan sessions.

### AD-8: Clean termination at Phase 4
No auto-chain to Phase 5. Pipeline ordering (4→5→6) prevents stale GC.

### AD-9: GC-v4 delta specification
6 new sections (Implementation Plan Reference, Task Decomposition, File Ownership Map,
Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy).
2 updated (Pipeline Status, Decisions Log). Rest preserved.

### AD-10: Read-First-Write-Second workflow
Architect reads target files before writing §5 Change Specifications.
Maximizes accuracy within tool constraints.

## Component Map

### Skill File: `.claude/skills/agent-teams-write-plan/SKILL.md`
- Frontmatter: name, description, argument-hint
- Dynamic Context: auto-inject pipeline output scan, existing plans, infra version
- Phases: 4.1 Input Discovery → 4.2 Team Setup → 4.3 Architect Spawn+DIA → 4.4 Plan Generation → 4.5 Gate 4 → Clean Termination
- Cross-Cutting: sequential-thinking, error handling, compact recovery
- Principles + Never lists

### Design Document: `docs/plans/2026-02-07-agent-teams-write-plan-design.md`
- 9 sections: Problem Statement, Architecture Overview, Phase 4 Workflow, Plan Template (10-section), GC Delta, Clean Termination, Cross-Cutting, Comparison, SKILL.md Draft
- Appendix: 10 Architecture Decisions (AD-1~AD-10)

### 10-Section Implementation Plan Template
§1 Orchestration Overview → §2 GC Update Template → §3 File Ownership → §4 TaskCreate Definitions → §5 Change Specifications → §6 Test Strategy → §7 Validation Checklist → §8 Commit Strategy → §9 Gate Criteria → §10 Summary

## Interface Contracts

### Input Interface (from brainstorming-pipeline)
- GC-v3 with Phase 3: COMPLETE
- phase-3/architect-1/L3-full/architecture-design.md
- Required GC-v3 sections: Scope, Component Map, Interface Contracts

### Output Interface (to Phase 5/6)
- GC-v4 with Phase 4: COMPLETE
- docs/plans/YYYY-MM-DD-{feature}.md (10-section plan)
- .agent/teams/{session}/phase-4/architect-1/L1/L2/L3

### DIA Interface
- TIER 2 (4 IAS, 7 RC) + LDAP MAXIMUM (3Q + alt)
- Protocol delegated to CLAUDE.md [PERMANENT] §7

## Research Findings

### writing-plans 원칙 분석

**보존할 원칙 (6):** DRY, YAGNI, TDD, exact file paths, complete code in plan, bite-sized task granularity, frequent commits, exact commands with expected output, plan saved to docs/plans/

**대체할 요소 (7):**
- TodoWrite → TaskCreate (Lead-only)
- Single-engineer → Multi-implementer pipeline
- 2-5 min steps → Phase-level tasks with acceptance criteria
- executing-plans handoff → Phase 6-8 pipeline
- git worktree → shared workspace + file ownership
- "For Claude" header → "For Lead" header
- Execution choice → pipeline continuation

### CH-001 포맷 분석

**범용 섹션 (8):** §1 Orchestration Overview, §2 GC Template, §3 File Ownership, §4 TaskCreate Definitions, §7 Validation Checklist, §8 Commit Strategy, §9 Gate Criteria, §10 Summary

### Pipeline 연결
brainstorming-pipeline → TeamDelete → artifacts preserved → user invokes agent-teams-write-plan → reads GC-v3 + L1/L2/L3 → TeamCreate new team → architect spawned → produces plan → Gate 4 → GC-v4 → Clean Termination

## Claude Code Optimization Points

### Dynamic Context Injection
- `!`command`` syntax: shell commands executed at skill load time
- Pattern: auto-scan .agent/teams/*/global-context.md for Phase 3 COMPLETE

### Skill Frontmatter
- argument-hint: "[brainstorming-session-id or path]"
- context: fork NOT used — Lead needs full conversation context

### Opus 4.6 Measured Language
- Natural instructions over ALL CAPS/[MANDATORY]

## Codebase Constraints
- brainstorming-pipeline does TeamDelete at termination → write-plan must TeamCreate new team
- .agent/teams/{session-id}/ artifacts survive TeamDelete
- Architect agent: plan mode, Write tool, no Edit/Bash
- DIA TIER 2 + LDAP MAXIMUM is highest intensity for architect

## Constraints
- DIA v3.0 enforcement (CIP + DIAVP + LDAP)
- Skill Optimization Process [PERMANENT] 적용 필수
- brainstorming-pipeline 출력 전용 입력
- CH-001 format as precedent
- 원본 superpowers:writing-plans 보존

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Phase 4 only (no Phase 5) | 단일 목적 집중 | P1 |
| D-2 | brainstorming-pipeline 출력 전용 | 복잡도 감소 | P1 |
| D-3 | CH-001 포맷 기반 출력 | 검증된 precedent | P1 |
| D-4 | Architect가 직접 생성 (Option A) | Lead 변환 불필요 | P1 |
| D-5 | 이중 저장 (docs/plans/ + .agent/teams/) | 장기 보존 + 세션 L1/L2/L3 | P1 |
| D-6 | 10-section 범용 템플릿 | CH-001 8섹션 + 5 신규 → 통합 | P2 |
| D-7 | Hybrid auto-discovery 입력 | 자동 탐색 + 사용자 확인 | P2 |
| D-8 | context: fork 미사용 | Lead orchestration 필요 | P2 |
| D-9 | Verification Level + AC-0 + V6 + Read-First | LDAP Q2 보완 메커니즘 4개 | P3 |
| D-10 | 4-layer task-context | LDAP Q1 context bridge | P3 |

## Gaps and Risks
| # | Gap/Risk | Severity | Mitigation |
|---|----------|----------|------------|
| G-1 | CH-001 is only precedent (sample=1) | MEDIUM | Parametric template design |
| G-2 | Session continuity between skills | LOW | Auto-discovery + user confirm |
| G-3 | Architect format compliance | LOW | Template + CH-001 example |
| G-4 | TDD for non-code tasks | LOW | §6 conditional |
| R-1 | Cross-session context loss | MEDIUM | 4-layer injection + CIP+DIAVP+LDAP |
| R-2 | Architect code accuracy | MEDIUM | Verification Level + AC-0 + V6 |
| R-3 | Post-Gate 4 rework | LOW | Pipeline ordering + GC versioning |

## Phase 4 Entry Requirements — SATISFIED
- Design document: `docs/plans/2026-02-07-agent-teams-write-plan-design.md`
- SKILL.md draft: In design document §9
- 10 Architecture Decisions: AD-1~AD-10
- All GC-v2 Phase 3 Architecture Input requirements met (7/7)

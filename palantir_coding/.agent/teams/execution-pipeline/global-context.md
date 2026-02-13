---
version: GC-v3
created: 2026-02-07
feature: execution-pipeline
complexity: COMPLEX
---

# Global Context — execution-pipeline

## Scope

**Goal:** `executing-plans` + `subagent-driven-development` 2개 INCOMPATIBLE 스킬을 대체하는 `execution-pipeline` Agent Teams 네이티브 스킬을 생성하여 Phase 6 (Implementation)을 orchestrate한다.

**In Scope:**
- Phase 6 전용 스킬 (Implementation — implementer가 코드 작성)
- agent-teams-write-plan 출력 (GC-v4 + 10-section implementation plan) 입력
- Adaptive implementer 관리 (1-4명, task 수/의존성에 따라 동적 결정)
- DIA v3.0 enforcement (implementer: TIER 1, LDAP HIGH: 2Q)
- File Ownership enforcement (non-overlapping, CLAUDE.md §5)
- Gate 6에 two-stage review 통합 (spec compliance + code quality)
- Reviewer를 implementer의 Sub-Orchestrator subagent로 위임 (Option B)
- GC-v4 → GC-v5 업데이트 (Phase 6 완료 반영)
- 이중 저장: `.agent/teams/{session-id}/` (L1/L2/L3)
- Clean Termination (no auto-chain to Phase 7)

**Out of Scope:**
- Phase 7 (Testing), Phase 8 (Integration), Phase 5 (Plan Validation)
- verification-pipeline (별도 스킬로 설계 예정)
- 원본 executing-plans / subagent-driven-development 수정
- git worktree 관리

**Approach:** Lead가 implementation plan의 §1 + §3 + §4를 읽고, Adaptive로 implementer 수를 결정하여 spawn. 각 implementer는 DIA 검증 후 §5 Change Specifications를 실행. Implementer가 Sub-Orchestrator로 spec-reviewer + code-reviewer subagent를 디스패치하여 자체 fix loop 수행. Gate 6에서 Lead가 per-task + cross-task 검증.

**Success Criteria:**
- SKILL.md 1개 파일 생성
- Design document 1개 생성
- agent-teams-write-plan과 자연스럽게 연결되는 파이프라인
- 기존 파일 0개 수정
- superpowers의 two-stage review + fix loop 개념 통합

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: COMPLETE (Gate 3 APPROVED — RC 7/7, LDAP 4/4 STRONG)
- Phase 4: SKIPPED (skill-draft.md deployed directly as SKILL.md)
- Phase 9: COMPLETE (Delivery)

## Research Findings

### 보존 대상 (11 patterns from superpowers)
1. Two-stage review (spec compliance → code quality, ordered)
2. Context curation (task-specific context per implementer)
3. "Do Not Trust the Report" (reviewer 결과를 무조건 신뢰하지 않음)
4. Fix loop (reviewer issues → implementer fixes → re-review)
5. Self-review (implementer가 자체 검토 후 제출)
6. Pre-work Q&A (implementer가 불명확한 점 먼저 질문)
7. Stop on blocker (해결 불가 시 즉시 보고)
8. Critical plan review (plan 결함 발견 시 보고)
9. Fresh context (task당 깨끗한 context)
10. Final whole-project review (전체 구현 후 통합 리뷰, optional)
11. Ordered review (spec → quality 순서 고정)

### 대체 대상 (11 elements)
1. TodoWrite → TaskCreate (Lead-only)
2. Human checkpoint → Gate 6 (Lead DIA protocol)
3. Ephemeral subagent → Persistent implementer teammate
4. Sequential-only → Adaptive parallel (1-4)
5. Same-session controller → Delegate Lead
6. Finishing chain → Clean Termination
7. Worktree → Shared workspace + File Ownership
8. No DIA → TIER 1 + LDAP HIGH
9. No GC → CIP injection (GC-v4)
10. Flat tasks → Dependency-aware (blockedBy/blocks)
11. No ownership → Non-overlapping file sets

### Implementer Agent 분석
- Tools: Read/Glob/Grep/Edit/Write/Bash + TaskList/TaskGet + sequential-thinking + context7
- DIA: TIER 1 (6 IAS, 10 RC) + LDAP HIGH (2Q), Gate A → Gate B
- Sub-Orchestrator: Can spawn subagents via Task tool (depth=1) — reviewer dispatch mechanism
- File Ownership: non-overlapping, concurrent edit FORBIDDEN, violation → [STATUS] BLOCKED
- Context Pressure: L1/L2/L3 at ~75%, CONTEXT_PRESSURE report

### Adaptive Spawn Algorithm
- Input: plan §3 (File Ownership) + §4 (TaskCreate Definitions)
- Metric: independent file cluster count (non-overlapping task groups)
- Rule: ≤5 tasks → 1-2 implementers, 6+ independent tasks → 3-4 implementers
- DIA overhead: 5-22K tokens per implementer
- Max: 4 implementers (CLAUDE.md §2)

### Two-Stage Review Integration (Option B: Implementer Delegation)
- Implementer dispatches spec-reviewer + code-reviewer as ephemeral subagents
- Fix loop within implementer scope (max 3 iterations per stage)
- Reviewers: DIA exempt (read-only, no mutation)
- Quality assurance: Prompt Template + Lead Override + Re-review Loop
- Gate 6: Per-task (spec+quality+self-test+ownership) → Cross-task (interface+integration+optional final)

### Gate 6 Structure
- **Per-task evaluation:** Implementer reports (L1/L2) + review results + self-test evidence
- **Cross-task evaluation:** Lead directly checks interface consistency, file ownership boundaries, integration points
- **Optional final review:** Whole-project review subagent for complex features
- **Result:** APPROVE → GC-v5 + Clean Termination / ITERATE (max 3) → fixes / ABORT

## Claude Code Optimization Points (from claude-code-guide research)

### Dynamic Context Injection
- Plan discovery: `!`ls docs/plans/*-implementation.md 2>/dev/null``
- Git status: `!`cd /home/palantir && git diff --name-only 2>/dev/null``
- Session detection: `!`ls -d .agent/teams/*/orchestration-plan.md 2>/dev/null``

### $ARGUMENTS
- session-id with auto-detect fallback
- argument-hint: "[session-id or empty for auto-detect]"

### Multi-Implementer Monitoring
- Primary: tmux split panes (visual, 0 tokens)
- Secondary: TaskList every 15 min (~500 tokens)
- Deep dive: Read L1 only on blocker (~2K tokens)
- Timeout: >30 min silence → message, >40 min → escalate

### Skill Configuration
- context: fork NOT used (Lead inline orchestration)
- model: opus (all instances)

## Codebase Constraints
- agent-teams-write-plan outputs GC-v4 + 10-section plan → execution-pipeline input
- Implementer agent: full tool access (Edit/Write/Bash), DIA mandatory
- File Ownership: CLAUDE.md §5, integrator is only cross-boundary role
- code-reviewer subagent: superpowers template-based, read-only

## Constraints
- DIA v3.0 enforcement (CIP + DIAVP + LDAP)
- Skill Optimization Process [PERMANENT] 적용 필수
- agent-teams-write-plan 출력 전용 입력
- CLAUDE.md §5 File Ownership Rules 준수
- Implementer: TIER 1 (6 IAS, 10 RC) + LDAP HIGH (2Q)
- Reviewers: ephemeral subagent, DIA exempt
- 원본 executing-plans / subagent-driven-development 보존

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Phase 6 only (no Phase 7/8) | verify 스킬들을 별도 verification-pipeline으로 분리 | P1 |
| D-2 | agent-teams-write-plan 출력 전용 | 파이프라인 연속성 보장 | P1 |
| D-3 | Adaptive implementer (1-4) | task 수/의존성에 따른 동적 결정 | P1 |
| D-4 | Gate 6에 two-stage review 통합 | spec compliance + code quality를 Gate에서 검증 | P1 |
| D-5 | code-reviewer를 subagent로 활용 | 기존 superpowers agent 재사용 | P1 |
| D-6 | Option B: Implementer delegation | review를 implementer Sub-Orchestrator에 위임 | P2 |
| D-7 | Reviewer ephemeral, DIA exempt | read-only mutation 없음, prompt template 품질 보장 | P2 |
| D-8 | Fix loop max 3 iterations per stage | 무한 루프 방지 | P2 |
| D-9 | Gate 6 = per-task + cross-task 2단계 | implementer 보고 + Lead 직접 검증 | P2 |

## Gaps and Risks (RESOLVED)
| # | Gap/Risk | Severity | Resolution (Phase 3) |
|---|----------|----------|---------------------|
| G-1 | Implementer review result 조작 | MEDIUM | AD-1 UQ-3: 3-Layer Defense (automated+self-report+spot-check) |
| G-2 | Context pressure with multiple tasks | MEDIUM | AD-1 UQ-4: Per-task checkpoint + Pre-Compact Obligation |
| G-3 | Final whole-project review | LOW | AD-1 UQ-2: Conditional (Lead judgment) |
| G-4 | Fix loop 3회 제한 | LOW | AD-1 UQ-1: Fixed 3 per stage |
| UQ-1~4 | All resolved | — | See AD-1 in architecture-design.md §2 |

## Architecture Decisions (Phase 3)
| # | Decision | Summary |
|---|----------|---------|
| AD-1 | UQ Resolution | fix loop=3 fixed, final review=conditional, manipulation=3-layer, context=per-task checkpoint |
| AD-2 | Adaptive Spawn | Connected components algorithm, min(components, 4) implementers |
| AD-3 | Two-Stage Review | Option B (implementer delegation), 58% Lead context savings |
| AD-4 | Cross-Boundary | 4-stage escalation protocol |
| AD-5 | Gate 6 | Per-task(G6-1~5) + cross-task(G6-6~7) + 3-layer defense |
| AD-6 | GC Delta | v4→v5 (Phase 6 results, interfaces, Phase 7 entry) |
| AD-7 | Clean Termination | No auto-chain, artifact preservation |
| AD-8 | SKILL.md Design | Follows brainstorming-pipeline + agent-teams-write-plan precedent |

## Deliverables
- SKILL.md: `.claude/skills/execution-pipeline/SKILL.md` (~532 lines)
- Design doc: `docs/plans/2026-02-07-execution-pipeline-design.md` (~610 lines)
- Full artifacts: `.agent/teams/execution-pipeline/`

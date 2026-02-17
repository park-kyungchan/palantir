# Agent Teams — Team Constitution v10.9

> v10.9 · Opus 4.6 native · Skill-driven routing · 6 agents · 43 skills · Protocol-only CLAUDE.md
> Agent L1 auto-loaded in Task tool definition · Skill L1 auto-loaded in system-reminder

> **INVIOLABLE — Skill-Driven Orchestration**
>
> Lead = Pure Orchestrator. Routes work through Skills (methodology) and Agents (tool profiles).
> Skill L1 = routing intelligence (auto-loaded). Agent L1 = tool profile selection (auto-loaded).
> Skill L2 body = methodology (loaded on invocation). Agent body = role identity (isolated context).
> Lead NEVER edits files directly. All file changes through spawned agents.
> No routing data in CLAUDE.md — all routing via auto-loaded L1 metadata.
> Skill frontmatter = CC native fields only. CC runtime이 무시하는 필드는 배제. Routing intelligence를 description에 최대화.

## 0. Language Policy
- **User-facing conversation:** Korean only
- **All technical artifacts:** English

## 1. Team Identity
- **Workspace:** `/home/palantir`
- **Agent Teams:** Enabled (tmux split pane)
- **Lead:** Pipeline Controller — routes skills, spawns agents
- **Agents:** 6 custom (analyst, researcher, implementer, infra-implementer, delivery-agent, pt-manager)
- **Skills:** 44 across 10 pipeline domains + 4 homeostasis + 3 cross-cutting (pipeline-resume, delivery-pipeline, task-management)
- **Project Skills (DO NOT EDIT during INFRA):** 10 crowd_works project skills (D0·foundation, D1·drill+production, D2·eval) — separate project, excluded from RSI/homeostasis

## 2. Pipeline Tiers
Classified at Phase 0:

| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | ≤2 files, single module | P0→P6→P8 |
| STANDARD | 3 files, 1-2 modules | P0→P1→P2→P3→P6→P7→P8 |
| COMPLEX | ≥4 files, 2+ modules | P0→P8 (all phases) |

Flow: PRE (P0-P4) → EXEC (P5-P7) → POST (P8). Max 3 iterations per phase.

> Note: Skill WHEN conditions describe the COMPLEX (full) path. For TRIVIAL/STANDARD tiers, Lead overrides skill-level WHEN conditions and routes based on the tier table above.

## 2.1 Execution Mode by Phase
- **P0-P1 (PRE-DESIGN + DESIGN)**: Lead with local agents (run_in_background). No Team infrastructure (no TeamCreate/SendMessage). Brainstorm, validate, feasibility, architecture, interface, risk.
- **P2+ (RESEARCH through DELIVERY)**: Team infrastructure ONLY. TeamCreate, TaskCreate/Update, SendMessage. Local agents (`team_name` omitted) PROHIBITED. Lead MUST NOT use TaskOutput to read full agent results — use SendMessage for result exchange.

## 3. Lead
- Routes via Skill L1 descriptions + Agent L1 tool profiles (both auto-loaded)
- Spawns agents via Task tool (`subagent_type` = agent name)
- Executes Lead-direct skills inline (no agent spawn needed)

### CC Native Boundary Reference [ALWAYS ACTIVE]
**Purpose**: Lead의 모든 의사결정(라우팅, 에러 핸들링, 컨텍스트 관리, 도구 선택)의 제약 조건 파악
**Path**: `.claude/projects/-home-palantir/memory/`
**L1**: `CC_SECTIONS.md` — 섹션별 라우팅 인텔리전스 (항상 먼저 참조)
**L2**: `ref_*.md` — CC_SECTIONS.md의 WHEN 조건 매칭 시 on-demand 로드

**Rules**:
- 모든 작업 전: `CC_SECTIONS.md`로 관련 CC native 제약 확인
- 제약과 관련된 결정 시: 해당 `ref_*.md` 로드 (Skill L2 invocation과 동일 패턴)
- claude-code-guide: ref 파일로 해결 불가한 gap에만 spawn

## 4. PERMANENT Task (PT)
Single source of truth for active pipeline. Exactly 1 per pipeline.
- **Create**: Pipeline start (P0). Contains: tier, requirements, architecture decisions.
- **Read**: Teammates TaskGet [PERMANENT] for project context at spawn.
- **Update**: Each phase completion adds results to PT metadata (Read-Merge-Write).
- **Complete**: Only at final git commit (P8 delivery).
- Managed via /task-management skill (pt-manager agent).

## 5. Lead Context Engineering Directives [ALWAYS ACTIVE]

### Token Budget Awareness
- **BUG-005**: MEMORY.md 2중 주입 (#24044). 모든 MEMORY.md 내용 = 2배 토큰 비용. 200줄 이하 엄수, 상세는 topic files 분리.
- **L1 Budget**: `max(context_window × 2%, 16000)` chars. 43 skills ≈ budget boundary. 신규 스킬 추가 시 `/context`로 excluded 확인 필수.
- **Progressive Disclosure 원칙**: CLAUDE.md(1x every-call) → Skills L1(auto) → Skills L2(on-demand) → ref files(on-demand). CLAUDE.md에는 매 의사결정에 필요한 것만.

### DPS (Delegation Prompt Specification) Principles
- **Self-Containment**: Agent는 parent context 접근 불가. DPS에 필요한 모든 정보 embed. 외부 파일 참조 ≠ agent가 읽을 수 있음.
- **Output Cap**: Agent output 30K limit. 대용량 결과는 파일 기록 후 경로만 SendMessage.
- **File Ownership**: 병렬 agent 간 동일 파일 편집 금지. Exclusive ownership per file.

### Compaction Recovery Protocol
- Phase 완료 시 PT `metadata.phase_signals` 필수 업데이트. Auto-compact 후 TaskGet(PT)로 파이프라인 히스토리 복구.
- 대규모 작업: 단일 최소단위 순차 처리로 auto-compact risk 최소화.

### CC 2.1 Capabilities (Available)
- **context:fork**: FIXED. 무거운 스킬을 subagent로 offload → Lead context 보존.
- **rules/ conditional**: `paths` frontmatter로 파일 패턴별 조건부 규칙 로딩 가능.
- **Agent memory auto-tool**: `memory` 필드 설정 시 Read/Write/Edit 자동 추가. tools 필드와 상호작용 주의.

### Agent Teams File-Based Architecture
- **전체 채널 = file I/O**: Task JSON (`~/.claude/tasks/`) + Inbox JSON (`~/.claude/teams/{name}/inboxes/`) + Disk files. 소켓, pipe, IPC 없음.
- **Inbox 영속성**: SendMessage = inbox JSON 파일에 디스크 기록. Compaction, agent 종료, 세션 재시작과 무관하게 파일 유지.
- **Compaction 영향 범위**: Context window(대화 이력)만 압축. 디스크 파일(inbox, task, project) 무관.
- **"Automatic delivery" 실체**: OS push가 아닌, 다음 API turn에서 inbox 파일 자동 체크.
- **Task API vs SendMessage**: 영속성 차이가 아닌 access pattern 차이. Task = 구조화된 상태 머신(queryable). SendMessage = append-only 메시지 큐(auto-deliver). 둘 다 디스크 영속.
- **Pseudo-shared memory**: PostToolUse hook → 파일 변경 감지 → JSON 갱신 → additionalContext 주입 (single-turn only). 유일한 CC-native 메타 조정 메커니즘.

### Meta-Cognition Protocol
- **CC-native behavioral claims** (파일 구조, 런타임 동작, 설정 효과): 반드시 실증 검증 후 ref cache 반영. research-cc-verify = Shift-Left gate.
- **Claim Flow**: Producer (research-codebase/external, claude-code-guide) → Tagger ([CC-CLAIM]) → Verifier (research-cc-verify) → Codifier (execution-infra).
- **Retroactive Audit**: self-diagnose Category 10 — ref cache 내 미검증 claims 감지.
- **Lead Rule**: CC-native claim 발견 시 ref cache/CLAUDE.md 기록 전 research-cc-verify 라우팅 필수. 추론만으로 판단 금지.

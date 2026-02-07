# Claude Code Agent Teams — Architecture & Design Reference

> **Purpose**: WSL2 + tmux + Claude Code Agent Teams 환경 구축 및 대규모 아키텍처 개선 설계를 위한 Brainstorming & Socratic Q&A 기반 문서
> **Target Runtime**: WSL2 (Ubuntu) + tmux + Claude Code CLI
> **Model**: claude-opus-4-6

---

## 1. Agent Teams 핵심 아키텍처

### 1.1 Four-Component Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Team Lead                          │
│  (Main Claude Code Session)                          │
│  - 팀 생성/스폰/태스크 할당/결과 종합                    │
│  - 팀 수명 동안 고정 (변경 불가)                        │
├─────────────────────────────────────────────────────┤
│              Teammates (N개)                          │
│  - 각자 독립된 context window 보유                     │
│  - CLAUDE.md, MCP 서버 로드 O                         │
│  - Lead의 대화 히스토리 상속 X                          │
├─────────────────────────────────────────────────────┤
│            Shared Task List                           │
│  - 전체 에이전트에 가시적인 중앙 작업 큐                  │
│  - 상태: pending → in_progress → completed            │
│  - 의존성 추적 + 자동 언블로킹                          │
├─────────────────────────────────────────────────────┤
│           Mailbox (Inbox System)                      │
│  - Direct messaging (1:1)                            │
│  - Broadcast (1:All, 비용 = 팀 크기에 비례)             │
│  - 자동 메시지 배달 + idle 알림                         │
└─────────────────────────────────────────────────────┘
```

### 1.2 로컬 스토리지 경로

- Team config: `~/.claude/teams/{team-name}/config.json`
- Task list: `~/.claude/tasks/{team-name}/`
- 관련 환경변수: `CLAUDE_CODE_TEAM_NAME`, `CLAUDE_CODE_AGENT_ID`, `CLAUDE_CODE_AGENT_TYPE`

### 1.3 Agent Teams vs Subagents 비교

| 특성 | Subagents | Agent Teams |
|------|-----------|-------------|
| Context | 독립 window → 결과만 요약 반환 | 독립 window → 완전 독립 |
| Communication | main agent에게만 결과 보고 | 팀원 간 직접 메시징 |
| Coordination | main agent가 모든 작업 관리 | 공유 태스크 리스트 + 자기조율 |
| Best for | 결과만 필요한 집중 태스크 | 토론/협업이 필요한 복잡한 작업 |
| Token cost | 낮음 (요약 반환) | 높음 (각 팀원 = 별도 Claude 인스턴스) |

---

## 2. WSL2 + tmux 환경 설정

### 2.1 Prerequisites

```bash
# WSL2 Ubuntu 환경
sudo apt update && sudo apt install -y tmux git

# Claude Code CLI 설치 확인
claude --version
```

### 2.2 Agent Teams 활성화

```bash
# 방법 1: 환경변수 (일회성)
export CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1

# 방법 2: settings.json (영구 설정 — 권장)
# 파일 위치: ~/.claude/settings.json
```

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

### 2.3 Display Mode 설정

| Mode | 동작 | 설정값 |
|------|------|--------|
| `auto` (기본값) | tmux 내부이면 split pane, 아니면 in-process | `"teammateMode": "auto"` |
| `tmux` | split pane 강제 (tmux/iTerm2 자동 감지) | `"teammateMode": "tmux"` |
| `in-process` | 모든 팀원을 메인 터미널에서 실행 | `"teammateMode": "in-process"` |

**WSL2 + tmux 조합에서는 `"auto"` 또는 `"tmux"`를 사용**

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "auto"
}
```

세션별 오버라이드:

```bash
claude --teammate-mode tmux
```

### 2.4 Split Pane 미지원 환경 (주의)

- VS Code 통합 터미널 ❌
- Windows Terminal ❌
- Ghostty ❌
- **WSL2 내 tmux에서 직접 실행해야 split pane 동작 ✅**

---

## 3. 키보드 단축키 & 운영 커맨드

### 3.1 Agent Teams 단축키

| 단축키 | 동작 |
|--------|------|
| `Shift+↑/↓` | 팀원 선택 (진행상황 보기/메시지 전송) |
| `Enter` | 선택한 팀원의 전체 세션 보기 |
| `Escape` | 팀원의 현재 턴 인터럽트 |
| `Ctrl+T` | 공유 태스크 리스트 토글 |
| `Shift+Tab` | Delegate Mode 진입/해제 |

### 3.2 Delegate Mode (핵심 패턴)

- `Shift+Tab`으로 활성화
- Lead가 **코드를 직접 건드리지 못하게 제한**
- 허용 동작: 스폰, 메시징, 셧다운, 태스크 관리만
- 목적: Lead가 직접 구현하는 안티패턴 방지

### 3.3 필수 Slash Commands

| 커맨드 | 기능 |
|--------|------|
| `/compact [focus]` | 대화 압축 (커스텀 포커스 가능) |
| `/clear` | 히스토리 완전 삭제 |
| `/effort` | 모델 effort level 설정 (low/medium/high/max) |
| `/context` | 컨텍스트 사용량 (skills, agents, MCP별) |
| `/hooks` | 인터랙티브 훅 관리 |
| `/mcp` | MCP 서버 관리 |
| `/agents` | 서브에이전트 관리 |
| `/rewind` | 코드 변경 되돌리기 |
| `/add-dir` | 세션 중 디렉토리 추가 |

---

## 4. 팀 생성 패턴 & 프롬프트 설계

### 4.1 자연어 팀 생성 예시

```
# 패턴 1: 역할 기반 팀
I'm designing a CLI tool that helps developers track TODO comments.
Create an agent team: one teammate on UX, one on technical architecture,
one playing devil's advocate.

# 패턴 2: 병렬 리팩토링 팀
Create a team with 4 teammates to refactor these modules in parallel.
Use Opus for each teammate.

# 패턴 3: 보안 감사 팀
Create a team that looks for security vulnerabilities in our app and fixes them.
```

### 4.2 Best Use Cases

- **다각도 리서치/리뷰**: 여러 관점에서 동시 탐색
- **병렬 코드 리뷰**: 보안/성능/테스트 커버리지 등 서로 다른 렌즈
- **가설 경쟁 디버깅**: 적대적 토론 방식
- **크로스 레이어 피처 개발**: frontend / backend / tests 각각 다른 팀원 담당
- **신규 모듈/피처**: 팀원별 독립 조각 소유

### 4.3 Anti-Patterns (회피 대상)

- 순서가 중요한 순차 태스크
- 같은 파일 동시 편집 → 덮어쓰기 충돌
- 과도하게 모호한 프롬프트 (예: "Build me an app")
- 교차 의존성이 많은 태스크
- 단순/루틴 작업 (토큰 비용 대비 비효율)
- 장시간 무감독 방치

---

## 5. Communication & Coordination 메커니즘

### 5.1 메시징 모델

```
Direct Message: Lead ↔ Teammate, Teammate ↔ Teammate
Broadcast: 1 → All (비용 = 팀 크기에 비례)
Shared Task List: 전체 가시, claim/dependency 추적
```

- 모든 메시지는 **송신자 + 수신자 양쪽 context window에서 토큰 소비**
- Task claiming: **file locking**으로 race condition 방지
- Lead가 명시적 할당 OR 팀원이 다음 unassigned/unblocked 태스크 self-claim

### 5.2 Plan Approval 워크플로우

```
[위험한 작업 시]
1. 팀원 → read-only 모드로 작업
2. 팀원 → 플랜 작성
3. 팀원 → Lead에게 승인 요청 전송
4. Lead → 초기 프롬프트 기반으로 자율적 승인 판단
5. 승인 후 → 팀원 구현 시작
```

---

## 6. Context Management 전략

### 6.1 Context Compaction

- `/compact` 수동 트리거, context ~75% 도달 시 자동 트리거
- 커스텀 포커스: `/compact only keep the names of the websites we reviewed`
- CLAUDE.md에 "Compact Instructions" 섹션으로 영구 보존 규칙 설정
- `/context`로 현재 사용량 확인

### 6.2 CLAUDE.md 설계 원칙

- 프로젝트 루트 + `~/.claude/CLAUDE.md` (글로벌)에서 자동 로드
- **150-200줄 이내** 권장
- "Compact Instructions" 섹션 필수 포함 → compaction 시 보존할 내용 지정
- **AGENTS.md**: Claude Code 아직 미지원 (GitHub issue #6235), 워크어라운드: `ln -s AGENTS.md CLAUDE.md`

---

## 7. Infinite Loop Harness 패턴 (대규모 병렬 작업)

> Carlini C Compiler Project에서 검증된 패턴

### 7.1 Core Loop

```bash
#!/bin/bash
while true; do
    COMMIT=$(git rev-parse --short=6 HEAD)
    LOGFILE="agent_logs/agent_${COMMIT}.log"
    claude --dangerously-skip-permissions \
           -p "$(cat AGENT_PROMPT.md)" \
           --model claude-opus-4-6 &> "$LOGFILE"
done
```

> ⚠️ `--dangerously-skip-permissions` → **반드시 컨테이너 내부에서만 실행**

### 7.2 Git 기반 분산 조율 아키텍처

```
┌──────────────────────────────┐
│     Bare Git Repository      │
│        (Upstream)            │
│     /upstream (mounted)      │
└──────────┬───────────────────┘
           │
    ┌──────┼──────┬──────┬─────┐
    ▼      ▼      ▼      ▼     ▼
 Agent1  Agent2 Agent3 Agent4  ...
 Docker  Docker Docker Docker
  │        │      │      │
  └── /workspace (local clone)
```

- 오케스트레이션 에이전트 없음 — 각 인스턴스가 독립적으로 작업 식별
- Task claiming: `current_tasks/` 디렉토리에 lock 파일 작성
- 충돌 시 git synchronization이 두 번째 에이전트에게 다른 태스크 선택 강제
- 완료 시: pull → merge → push → lock 파일 제거

### 7.3 LLM 에이전트용 Test Harness 설계 원칙

| 원칙 | 설명 |
|------|------|
| Context Window 오염 방지 | 테스트 출력 최소화, 몇 줄만 출력, 상세는 파일 로깅 |
| ERROR 그레핑 | 에러 시 같은 줄에 `ERROR` + 사유 출력 → `grep` 가능 |
| 집계 통계 사전 계산 | Claude가 재계산하지 않도록 |
| Time Blindness 대응 | Claude는 시간 감각 없음 → 진행률 출력 최소화, `--fast` 옵션 (1-10% 샘플) |
| Deterministic Subsample | 에이전트별 결정적 샘플 + VM간 랜덤 → 일관된 회귀 감지 + 전체 커버리지 |
| Self-Orientation | 신규 에이전트용 README/progress 파일 상시 업데이트 |

### 7.4 Specialized Agent Roles (검증된 패턴)

- **Code Deduplication Agent** — LLM의 중복 구현 통합
- **Performance Agent** — 속도 최적화
- **Code Efficiency Agent** — 출력 코드 품질 최적화
- **Design Critique Agent** — 개발자 관점 리뷰
- **Documentation Agent** — 문서 유지보수

---

## 8. Settings.json 전체 구성 참조

### 8.1 설정 우선순위 (높음 → 낮음)

1. Enterprise managed policies (`managed-settings.json`)
2. Command-line arguments
3. Local project (`.claude/settings.local.json`, gitignored)
4. Shared project (`.claude/settings.json`, committed)
5. User global (`~/.claude/settings.json`)

### 8.2 WSL2 Agent Teams 권장 settings.json

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  },
  "teammateMode": "auto",
  "model": "claude-opus-4-6"
}
```

### 8.3 Permission Modes

| Mode | 동작 |
|------|------|
| `default` | 첫 사용 시 프롬프트 |
| `acceptEdits` | 파일 편집 자동 수락 |
| `bypassPermissions` | 모든 권한 체크 스킵 (컨테이너 전용) |

### 8.4 Hook System 이벤트

- `PreToolUse`, `PostToolUse`, `PostToolUseFailure`
- `PermissionRequest`, `UserPromptSubmit`, `Stop`
- `SessionStart`, `PreCompact`, `SubagentStop`
- Matcher: 정규식 (예: `Edit|Write`, `Notebook.*`)
- Exit code 2 → PreToolUse에서 tool 사용 차단
- 타임아웃: 10분, 세션 시작 시 캡처 (mid-session 변경 불가)

### 8.5 MCP 통합

- Project scope: `.mcp.json` (프로젝트 루트)
- User scope: `claude mcp add` → `~/.claude.json`
- Enterprise scope: `managed-mcp.json`
- Tool Search (v2.1.7): MCP 도구가 context window 10% 초과 시 동적 로드

### 8.6 Custom Subagents 정의

- 위치: `~/.claude/agents/` (user) 또는 `.claude/agents/` (project)
- 형식: Markdown + YAML frontmatter
- 지원: 커스텀 프롬프트, 도구 제한, 권한 모드, 훅, 스킬, 영구 메모리
- 모델 제어: `CLAUDE_CODE_SUBAGENT_MODEL` 환경변수

---

## 9. Adaptive Thinking (Effort Levels)

| Level | 용도 |
|-------|------|
| `low` | 단순 태스크, 빠른 응답 |
| `medium` | 일반 작업, overthinking 방지 |
| `high` (기본값) | 복잡한 추론 |
| `max` | 최대 깊이 추론 |

- CLI: `/effort` 커맨드
- API: `thinking: {type: "adaptive"}`

---

## 10. Practical Workflow: WSL2 + tmux + Agent Teams

### 10.1 세션 시작 흐름

```bash
# 1. WSL2 터미널 진입
wsl

# 2. tmux 세션 생성
tmux new -s agent-team

# 3. 프로젝트 디렉토리 이동
cd ~/your-project

# 4. Claude Code 실행
claude

# 5. 자연어로 팀 생성
> Create a team with 4 teammates:
> 1. architecture-review: analyze current codebase structure
> 2. security-audit: find vulnerabilities
> 3. performance-opt: identify bottlenecks
> 4. test-coverage: assess and improve tests
```

### 10.2 팀 모니터링 워크플로우

```
Shift+↑/↓ → 팀원 선택
Enter     → 전체 세션 보기
Ctrl+T    → 태스크 리스트 확인
Shift+Tab → Delegate Mode 토글
```

### 10.3 Git Worktrees 병행 전략

```bash
# 메인 브랜치에서 worktree 생성
git worktree add ../project-security security-audit
git worktree add ../project-perf performance-opt
git worktree add ../project-test test-improvement

# 각 worktree에서 독립 Agent Team 또는 단일 세션 실행 가능
```

### 10.4 실전 최적화 팁

- Sonnet은 탐색/서브에이전트용, Opus는 구현/최종 판단용으로 분리
- 2-4명의 팀원이 **서로 다른 파일을 다루는 직교적 문제**에 최적
- Delegate Mode를 기본으로 사용하여 Lead의 직접 구현 방지
- `/compact`로 주기적 컨텍스트 정리
- CLAUDE.md에 팀 역할과 규칙을 명시하여 각 팀원이 자동 로드

---

## 11. Known Limitations

- 세션 재개 시 in-process 팀원 복원 불가 (`/resume`, `/rewind`)
- 태스크 상태 지연 — 팀원이 완료 마킹을 누락할 수 있음
- 세션당 1팀만 가능, 중첩 팀 불가 (팀원이 자체 팀 생성 불가)
- Lead 고정 (팀원 승격 불가)
- Split pane은 tmux 또는 iTerm2 필수

---

## 12. Socratic Q&A Brainstorming을 위한 시작 질문

> 이 질문들을 Local Claude Code에 입력하여 아키텍처 설계 대화를 시작하세요.

1. "현재 코드베이스의 가장 큰 아키텍처적 약점 3가지를 식별하고, 각각에 대해 Agent Team 역할을 제안해줘."
2. "이 프로젝트에 Agent Teams를 적용할 때, 같은 파일 충돌을 방지하기 위한 모듈 경계를 어떻게 설계해야 할까?"
3. "Delegate Mode에서 Lead가 효과적으로 판단하려면, CLAUDE.md에 어떤 아키텍처 의사결정 기준을 명시해야 할까?"
4. "현재 코드베이스를 분석해서, 병렬로 안전하게 리팩토링할 수 있는 독립적인 모듈 그룹을 찾아줘."
5. "Plan Approval 워크플로우를 활용해서, 대규모 아키텍처 변경의 위험을 최소화하는 단계별 전략을 설계해줘."

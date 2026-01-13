# Boris Cherny 워크플로 구현 가이드

> **심층 분석 결과:** Claude Code v2.1.6 Thread-Centric Agent Infrastructure
> **목표:** 실제 구현 가능한 상태까지 도달

---

## 1. 현재 구현 상태 (Stage A: SCAN 결과)

### ✅ 이미 구현됨

| 기능 | 파일 위치 | Boris 패턴 |
|------|----------|-----------|
| PostToolUse Auto-format | `.claude/hooks/auto-format.sh` | Pattern 10 |
| Session Health Monitor | `.claude/hooks/session-health.sh` | Pattern 12 |
| Parallel Notification | `.claude/hooks/parallel-notify.sh` | SubagentStop |
| PreCompact Context Save | `.claude/hooks/pre-compact.sh` | V2.1.x Resume |
| commit-push-pr Command | `.claude/commands/commit-push-pr.md` | Pattern 6 |
| ODA Governance Hooks | `settings.json` PreToolUse | Security |

### ❌ 새로 구현됨 (이 세션에서)

| 기능 | 파일 위치 | 설명 |
|------|----------|------|
| mprocs 병렬 세션 | `boris-workflow/mprocs.yaml` | 5개 터미널 관리 |
| Workspace 격리 스크립트 | `boris-workflow/setup-workspaces.sh` | Git worktree 자동화 |
| Auto-format 활성화 | `.claude/hooks/.format-config.json` | false → true |
| Slack MCP 예제 | `boris-workflow/mcp-slack-example.json` | 알림 통합 |

---

## 2. 즉시 실행 가능한 설정

### 2.1 병렬 세션 시작 (mprocs)

```bash
# Step 1: mprocs 설치
cargo install mprocs
# 또는
brew install pvolok/mprocs/mprocs  # macOS

# Step 2: 워크스페이스 초기화
~/.claude/boris-workflow/setup-workspaces.sh \
    git@github.com:your/repository.git \
    ~/workspace

# Step 3: 병렬 세션 시작
mprocs --config ~/.claude/boris-workflow/mprocs.yaml
```

### 2.2 키보드 단축키 (네이티브)

| 단축키 | 기능 | 사용 시점 |
|--------|------|----------|
| `Shift+Tab×2` | Plan Mode 진입 | 복잡한 작업 전 |
| `Shift+Tab` | Auto-accept 토글 | 빠른 실행 시 |
| `Esc+Esc` | Rewind (변경 취소) | 실수 복구 시 |
| `Ctrl+C` | 현재 작업 중단 | 루프 탈출 |

### 2.3 핵심 명령어

```bash
# Git 워크플로 자동화 (Boris가 하루 수십 번 사용)
/commit-push-pr

# 코드 검토
/audit

# 심층 분석
/deep-audit

# 계획 수립
/plan
```

---

## 3. 고급 설정

### 3.1 Slack 알림 통합

`.mcp.json`에 추가:

```json
{
  "mcpServers": {
    "slack": {
      "type": "http",
      "url": "https://slack.mcp.anthropic.com/mcp"
    }
  }
}
```

**설정 단계:**
1. https://api.slack.com/apps 에서 앱 생성
2. OAuth 권한 설정 (chat:write, channels:read)
3. Claude Code에서 `/slack` 명령어 사용

### 3.2 데스크톱 알림 활성화

```bash
# Linux
sudo apt install libnotify-bin

# macOS (기본 지원)
# Windows (PowerShell toast 지원)

# 테스트
notify-send "Claude Code" "Session completed"
```

### 3.3 Auto-format 커스터마이징

`.claude/hooks/.format-config.json`:
```json
{
  "auto_format_enabled": true,
  "formatters": {
    "python": { "tool": "black", "args": "--line-length 100" },
    "javascript": { "tool": "prettier" }
  }
}
```

---

## 4. Boris Cherny 워크플로 Best Practices

### 4.1 세션 관리 원칙

1. **"Kill early, start fresh"**
   - 막힌 세션은 빨리 종료
   - 컨텍스트 복구보다 새 시작이 효율적

2. **"One task, one session"**
   - 세션당 하나의 목표
   - 워크트리로 격리

3. **"Plan before execute"**
   - Plan Mode(Shift+Tab×2)로 먼저 계획
   - Auto-accept는 단순 작업에만

### 4.2 프롬프트 작성 규칙

```
❌ 나쁜 예: "코드 전체를 분석해서 문제점을 찾고 수정해줘"
✅ 좋은 예: "src/auth.py의 login 함수에서 토큰 만료 처리 추가"
```

- 200단어 이하
- 구체적인 파일/함수 지정
- 하나의 작업 단위

### 4.3 권한 관리

```bash
# 절대 사용 금지
claude --dangerously-skip-permissions  # ❌

# 대신 사용
# settings.json의 permissions.allow에 추가  # ✅
```

---

## 5. 트러블슈팅

### Q: mprocs 세션이 시작되지 않음
```bash
# 워크트리 확인
cd ~/workspace/repo-main && git worktree list

# 수동 생성
git worktree add ../repo-feature feature/dev
```

### Q: Auto-format이 작동하지 않음
```bash
# 포매터 설치 확인
which black prettier

# 설정 확인
cat ~/.claude/hooks/.format-config.json | jq '.auto_format_enabled'
# 출력: true
```

### Q: 알림이 오지 않음
```bash
# Linux
notify-send --version

# 테스트
~/.claude/hooks/parallel-notify.sh
```

---

## 6. 파일 구조 요약

```
/home/palantir/.claude/
├── boris-workflow/           # 새로 생성됨 ✨
│   ├── mprocs.yaml          # 병렬 세션 설정
│   ├── setup-workspaces.sh  # 워크스페이스 초기화
│   ├── mcp-slack-example.json
│   ├── README.md
│   └── IMPLEMENTATION-GUIDE.md (이 파일)
│
├── hooks/
│   ├── .format-config.json  # auto_format_enabled: true ✨
│   ├── auto-format.sh       # Boris Pattern 10
│   ├── session-health.sh    # Boris Pattern 12
│   ├── parallel-notify.sh   # Subagent 알림
│   └── pre-compact.sh       # V2.1.x Resume
│
├── commands/
│   ├── commit-push-pr.md    # 핵심 명령어
│   ├── audit.md
│   ├── deep-audit.md
│   └── plan.md
│
└── settings.json            # 전체 훅 설정
```

---

## 7. 다음 단계

1. **즉시 실행:**
   ```bash
   mprocs --config ~/.claude/boris-workflow/mprocs.yaml
   ```

2. **Slack 연동 (선택):**
   - Anthropic Slack MCP 설정
   - 또는 Webhook 기반 커스텀 알림

3. **워크플로 최적화:**
   - 자주 쓰는 패턴을 `/commands`로 추가
   - 팀 규칙을 `CLAUDE.md`에 문서화

---

> **참고:** 이 가이드는 문서 심층 분석 결과입니다.
> 실제 Boris Cherny의 워크플로를 기반으로 현재 워크스페이스에 맞게 구현되었습니다.

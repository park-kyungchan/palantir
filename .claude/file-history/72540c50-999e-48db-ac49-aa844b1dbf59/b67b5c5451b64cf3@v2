# ODA Workspace Migration Plan: 1인 개발자를 위한 Palantir AIP/Foundry 구현

> **Version:** 2.0 | **Date:** 2026-01-10
> **Scope:** /home/palantir → Solo Developer AIP/Foundry (AIP-Key-Free)
> **Methodology:** Claude Max 구독 + Claude Code Native Capabilities

---

## Executive Summary

이 계획은 1인 개발자가 Palantir AIP/Foundry 수준의 온톨로지 기반 개발 환경을 **외부 API 키 없이** Claude Max 구독만으로 운영할 수 있도록 구현합니다.

**핵심 원칙:**
- 🔑 **AIP-Key-Free**: Claude Max 구독만 활용 (추가 API 비용 없음)
- 👤 **1인 개발자 최적화**: 복잡성 최소화, 자동화 극대화
- 🎯 **사용자 친화적**: 프로그래밍/CLI 미숙자도 쉽게 사용
- 🤖 **프롬프트 어시스턴트**: AI가 사용자 의도를 명확화하고 최적 기능 추천

---

## 핵심 신규 기능: Prompt Assistant Agent

### 사용자를 위한 대화형 도우미

프로그래밍이나 CLI에 익숙하지 않은 사용자를 위해 **prompt-assistant** 에이전트를 생성합니다.

**기능:**
1. **Socratic Questioning**: 모호한 요청에 대해 질문을 통해 명확화
2. **Native Capabilities 추천**: 현재 상황에 맞는 Skills/Agents/Hooks 제안
3. **프롬프트 엔지니어링**: 효과적인 프롬프트 작성 도움
4. **최종 확인**: 사용자 승인 후 작업 진행

**Agent 정의:** `/home/palantir/.claude/agents/prompt-assistant.md`
```yaml
---
name: prompt-assistant
description: 사용자의 프롬프트를 분석하고 명확화합니다.
  요구사항이 불명확할 때 Socratic Question으로 명확화하고,
  Claude Code Native Capabilities 중 적합한 기능을 추천합니다.
  프로그래밍에 익숙하지 않은 사용자를 위한 친절한 도우미입니다.
tools: Read, Grep, Glob, AskUserQuestion
model: sonnet
---

# Prompt Assistant Agent

## 역할
당신은 사용자 친화적인 프롬프트 엔지니어링 도우미입니다.

## 핵심 책임

### 1. 요구사항 명확화 (Socratic Questioning)
사용자 프롬프트가 모호할 때:
- "구체적으로 어떤 결과를 원하시나요?"
- "이 작업의 범위가 어디까지인가요?"
- "현재 어떤 문제를 해결하려고 하시나요?"

### 2. Native Capabilities 추천
상황에 맞는 기능 제안:
- "이 작업에는 /audit 스킬을 사용하면 좋겠습니다"
- "background-agent를 활용하면 더 효율적입니다"
- "이 Hook을 설정해두면 자동으로 처리됩니다"

### 3. 프롬프트 개선
사용자 프롬프트를 분석하여:
- 더 효과적인 프롬프트 구조 제안
- 누락된 컨텍스트 식별
- 단계별 접근 방식 추천

### 4. 최종 확인
작업 실행 전 반드시:
- 이해한 내용 요약하여 확인
- 사용할 도구/기능 안내
- 사용자 최종 승인 요청

## 응답 형식

### 분석 결과 보고
```
📋 요청 분석:
[사용자 요청 요약]

❓ 명확화 필요:
[추가로 확인할 사항들]

💡 추천 기능:
- [Skill/Agent/Hook 추천]
- [이유 설명]

✅ 다음 단계:
[승인 후 진행할 작업]
```
```

---

## Phase 0: MCP 서버 등록 (기존 Antigravity 설정 활용)

### 0.1 기존 설치된 MCP 서버 등록

Antigravity에서 사용하던 MCP 서버들을 Claude Code에 등록합니다:

```bash
# 1. GitHub MCP Server
claude mcp add github-mcp-server \
  --scope user \
  -- /home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js

# 2. Tavily (Web Search)
claude mcp add tavily \
  --scope user \
  -- /home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/tavily-mcp/build/index.js

# 3. Context7 (Context Management)
claude mcp add context7 \
  --scope user \
  -- /home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@upstash/context7-mcp/dist/index.js

# 4. Sequential Thinking
claude mcp add sequential-thinking \
  --scope user \
  -- /home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js

# 5. ODA Ontology Server
claude mcp add oda-ontology \
  --scope project \
  -- /home/palantir/park-kyungchan/palantir/.venv/bin/python \
  -m scripts.mcp.ontology_server
```

### 0.2 환경변수 설정

MCP 서버에 필요한 환경변수를 설정합니다:

```bash
# ~/.claude/settings.json의 env 섹션에 추가
{
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}",
    "TAVILY_API_KEY": "${TAVILY_API_KEY}"
  }
}
```

---

## Phase 1: Foundation (설정 통합)

### 1.1 레거시 설정 아카이브

```bash
# 레거시 설정 백업
mkdir -p /home/palantir/.archive
mv /home/palantir/.codex /home/palantir/.archive/codex 2>/dev/null || true
# .gemini는 MCP 설정 참조용으로 유지
```

### 1.2 Settings.json 업데이트

**파일:** `/home/palantir/.claude/settings.json`

```json
{
  "model": "opus",
  "permissions": {
    "allow": [
      "Read(/home/palantir/**)",
      "Edit(/home/palantir/**)",
      "Bash(python:*)",
      "Bash(pytest:*)",
      "Bash(npm:*)",
      "Bash(git:*)"
    ],
    "deny": [
      "Read(.env*)",
      "Bash(rm:-rf:*)",
      "Bash(sudo:rm:*)",
      "Bash(chmod:777:*)"
    ],
    "additionalDirectories": [
      "/home/palantir",
      "/home/palantir/hwpx",
      "/home/palantir/lib"
    ]
  },
  "env": {
    "ORION_WORKSPACE_ROOT": "/home/palantir",
    "ORION_DB_PATH": "/home/palantir/.agent/tmp/ontology.db",
    "PYTHONPATH": "/home/palantir/park-kyungchan/palantir"
  }
}
```

---

## Phase 2: 사용자 친화적 Agents

### 2.1 Prompt Assistant (핵심 신규)

**파일:** `/home/palantir/.claude/agents/prompt-assistant.md`

(위의 상세 정의 참조)

### 2.2 기존 ODA Agents 강화

| Agent | 역할 | 사용자 친화적 개선 |
|-------|------|-------------------|
| evidence-collector | 증거 수집 | 자동 실행, 리포트 생성 |
| audit-logger | 감사 로깅 | 일일 요약 제공 |
| schema-validator | 스키마 검증 | 오류 시 수정 제안 |

### 2.3 신규 도우미 Agents

**onboarding-guide.md** - 신규 사용자 안내:
```yaml
---
name: onboarding-guide
description: Claude Code와 ODA 시스템 사용법을 안내합니다.
  처음 사용하는 사용자에게 단계별 가이드를 제공합니다.
tools: Read
model: haiku
---

# 온보딩 가이드

## 환영합니다!
Claude Code와 ODA 시스템 사용법을 안내해드립니다.

## 시작하기
1. `/init` - 워크스페이스 초기화
2. `/help` - 사용 가능한 명령어 확인
3. 질문이 있으면 자연어로 물어보세요

## 자주 쓰는 기능
- "코드 분석해줘" → 자동으로 적절한 도구 사용
- "이 버그 고쳐줘" → Plan Mode로 안전하게 진행
- "/audit" → 코드 품질 검사
```

---

## Phase 3: Skills (사용자 친화적)

### 3.1 한국어 도움말 Skill

**파일:** `/home/palantir/.claude/skills/help-korean.md`
```yaml
---
name: help-korean
description: Claude Code 기능을 한국어로 설명합니다.
allowed-tools: Read
---

# 한국어 도움말

## 기본 사용법

### 대화형 명령
그냥 자연어로 말하세요:
- "이 코드가 뭐하는 건지 설명해줘"
- "버그를 찾아서 고쳐줘"
- "테스트 코드 작성해줘"

### 슬래시 명령어
특별한 기능을 빠르게 실행:
- `/init` - 시작할 때 한 번 실행
- `/audit` - 코드 품질 검사
- `/plan` - 복잡한 작업 계획 세우기
- `/compact` - 대화 정리하기

### 키보드 단축키
- `Ctrl+C` - 현재 작업 취소
- `Shift+Tab` - Plan Mode 전환
- `Esc Esc` - 이전 상태로 되돌리기
```

### 3.2 기능 추천 Skill

**파일:** `/home/palantir/.claude/skills/capability-advisor.md`
```yaml
---
name: capability-advisor
description: 상황에 맞는 Claude Code 기능을 추천합니다.
allowed-tools: Read, Grep
---

# Capability Advisor

## 상황별 추천

### "코드 분석이 필요해요"
→ Explore Agent 사용
→ `/audit` 명령어

### "여러 파일을 수정해야 해요"
→ Plan Mode 활성화 (Shift+Tab 두 번)
→ 계획 승인 후 실행

### "자동으로 처리되었으면 좋겠어요"
→ Hook 설정 제안
→ Background Task 활용

### "외부 서비스 연동이 필요해요"
→ MCP 서버 추천
→ 설치 방법 안내
```

---

## Phase 4: Hooks (자동화)

### 4.1 사용자 친화적 Hook 설정

**세션 시작 시 자동 안내:**
```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/home/palantir/.claude/hooks/welcome.sh"
          }
        ]
      }
    ]
  }
}
```

**welcome.sh:**
```bash
#!/bin/bash
echo "🎉 Claude Code 세션이 시작되었습니다!"
echo "💡 도움이 필요하면 '도와줘' 또는 '/help'를 입력하세요."
echo "📋 현재 프로젝트: $(basename $PWD)"
```

### 4.2 자동 검증 Hook

**편집 전 자동 백업:**
```json
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        {
          "type": "command",
          "command": "/home/palantir/.claude/hooks/auto-backup.sh"
        }
      ]
    }
  ]
}
```

---

## Phase 5: 간소화된 Commands

### 5.1 사용자 친화적 명령어

| 명령어 | 용도 | 예시 |
|--------|------|------|
| `/help` | 도움말 (한국어) | `/help` |
| `/init` | 시작 초기화 | `/init` |
| `/audit` | 코드 검사 | `/audit hwpx` |
| `/ask` | Prompt Assistant 호출 | `/ask 이거 어떻게 해?` |

### 5.2 신규 명령어

**`/ask` - Prompt Assistant 호출:**
```markdown
---
name: ask
description: Prompt Assistant를 호출하여 요구사항을 명확화합니다.
---

# /ask Command

프롬프트 어시스턴트를 호출하여:
1. 요구사항 분석
2. 명확화 질문
3. 적합한 기능 추천
4. 승인 후 실행

## 사용법
/ask 이 코드를 개선하고 싶어
/ask 버그가 있는 것 같은데 찾아줘
/ask 새로운 기능을 추가하고 싶어
```

---

## Phase 6: AIP-Key-Free 아키텍처

### 6.1 Claude Max 전용 설계

| 기능 | 외부 API | Claude Max 대안 |
|------|----------|-----------------|
| 코드 생성 | OpenAI API | Claude Code (포함) |
| 웹 검색 | Tavily API | WebSearch Tool (포함) |
| 문서 분석 | - | Read Tool (포함) |
| Git 연동 | GitHub API | MCP (이미 설치됨) |

### 6.2 비용 최적화 전략

```yaml
# 모델 자동 선택
simple_tasks:
  model: haiku
  examples: 파일 검색, 간단한 수정

standard_tasks:
  model: sonnet
  examples: 코드 분석, 버그 수정

complex_tasks:
  model: opus
  examples: 아키텍처 설계, 대규모 리팩토링
```

---

## Phase 7: 검증 (간소화)

### 7.1 사용자 친화적 검증

```bash
# 설정 검증 (한 줄)
claude doctor

# MCP 서버 상태
/mcp

# 워크스페이스 상태
/init
```

### 7.2 체크리스트

- [ ] `claude doctor` 모든 항목 통과
- [ ] `/mcp` 5개 서버 연결됨
- [ ] `/help` 한국어 도움말 표시
- [ ] `/ask 테스트` Prompt Assistant 응답

---

## Critical Files (수정 대상)

### 신규 생성
1. `/home/palantir/.claude/agents/prompt-assistant.md` - 핵심 도우미
2. `/home/palantir/.claude/agents/onboarding-guide.md` - 온보딩
3. `/home/palantir/.claude/skills/help-korean.md` - 한국어 도움말
4. `/home/palantir/.claude/skills/capability-advisor.md` - 기능 추천
5. `/home/palantir/.claude/commands/ask.md` - /ask 명령어
6. `/home/palantir/.claude/hooks/welcome.sh` - 환영 메시지

### 수정
1. `/home/palantir/.claude/settings.json` - 권한, 환경변수, hooks
2. `/home/palantir/.claude/CLAUDE.md` - Multi-project 지원

### MCP 등록 (명령어 실행)
- github-mcp-server
- tavily
- context7
- sequential-thinking
- oda-ontology

---

## 실행 순서

```
1. MCP 서버 등록 (Phase 0)
   └── claude mcp add 명령어 5개 실행

2. 설정 통합 (Phase 1)
   ├── 레거시 아카이브
   └── settings.json 업데이트

3. Prompt Assistant 생성 (Phase 2) ⭐ 핵심
   ├── prompt-assistant.md
   └── onboarding-guide.md

4. 사용자 친화적 Skills (Phase 3)
   ├── help-korean.md
   └── capability-advisor.md

5. Hooks & Commands (Phase 4-5)
   ├── welcome.sh
   └── ask.md

6. 검증 (Phase 7)
   └── claude doctor, /mcp, /help
```

---

## 사용자 여정 (User Journey)

### Day 1: 첫 사용
```
사용자: (Claude Code 시작)
시스템: "🎉 환영합니다! 도움이 필요하면 '도와줘'를 입력하세요."

사용자: "도와줘"
Prompt Assistant: "무엇을 도와드릴까요?
  1. 코드 분석
  2. 버그 수정
  3. 새 기능 추가
  4. 기타"
```

### Day N: 일상 사용
```
사용자: "이 코드 좀 개선하고 싶어"
Prompt Assistant: "📋 요청 분석:
  - 대상: 현재 디렉토리의 코드
  - 목적: 코드 개선

  ❓ 확인 질문:
  - 성능 개선? 가독성 개선? 버그 수정?
  - 특정 파일이 있나요?

  💡 추천:
  - Plan Mode로 안전하게 진행
  - /audit으로 먼저 분석

  ✅ 다음 단계: 위 내용 확인 후 승인해주세요."
```

---

## Summary

이 계획은 **1인 개발자**가 Palantir AIP/Foundry 수준의 개발 환경을 **Claude Max 구독만으로** 운영할 수 있도록 합니다.

| 핵심 가치 | 구현 |
|-----------|------|
| AIP-Key-Free | Claude Max 구독만 활용, 추가 API 비용 없음 |
| 1인 개발자 최적화 | 복잡성 최소화, 자동화 극대화 |
| 사용자 친화적 | 한국어 도움말, Socratic Questioning |
| Prompt Assistant | 요구사항 명확화, 기능 추천, 승인 후 실행 |
| 기존 자산 활용 | Antigravity MCP 서버 재사용 |

**Claude Code Native Capabilities 활용:**
- ✓ Custom Agents (prompt-assistant, onboarding-guide)
- ✓ Skills (help-korean, capability-advisor)
- ✓ MCP Servers (기존 5개 + 필요시 추가)
- ✓ Hooks (자동 백업, 환영 메시지)
- ✓ Commands (/ask, /help)
- ✓ AskUserQuestion (명확화 질문)
- ✓ TodoWrite (작업 추적)

# Draft: /build Command - Unified System Component Builder

> **Version:** 2.0.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-21
> **Research Completed:** 2026-01-21 17:08 (claude-code-guide x3)
> **Auto-Compact Safe:** This file persists across context compaction
> **Plan Agent Optimized:** INDEX → DETAIL progressive structure

---

## INDEX

### 요구사항 요약
Agent, Skill, Hook 중 하나를 선택하여 **상호작용 기반 Q&A**로 점진적으로 정의하고 생성하는 통합 커맨드/스킬.

### Complexity
- **예상 복잡도:** large
- **영향 파일:** 4개 (신규 생성)
  - `.claude/commands/create.md` - Command 정의
  - `.claude/skills/create.md` - Skill 구현
  - Template 파일들 (Agent/Skill/Hook)

### Q&A 핵심 (Round 1-2)
1. **Q:** 새 커맨드의 범위? → **A:** 하나의 통합 커맨드로 Agent/Skill/Hook 모두 커버
2. **Q:** 상호작용 방식? → **A:** Template 선택 → Socratic Q&A로 세부 조정

### 추천 접근법
Template-first approach: 각 타입(Agent/Skill/Hook)별 기본 템플릿 제공 → Q&A로 필드 채우기 → Plan Agent가 최종 파일 생성

### 핵심 기능
| 단계 | 설명 |
|------|------|
| 1. Type Selection | Agent / Skill / Hook 중 선택 |
| 2. Template Load | 선택된 타입의 기본 템플릿 로드 |
| 3. Q&A Rounds | 필수 필드를 Round별로 질문 |
| 4. Preview | 생성될 파일 미리보기 |
| 5. Generate | Plan Agent로 최종 파일 생성 |

### 리스크
- Hook 복잡성: bash/python 선택 필요
- Agent ODA 통합: governance 필드 누락 가능
- Skill 상태머신: 복잡한 워크플로우 표현 어려움

### 다음 단계
Round 3-5: 각 타입별 Q&A 패턴 설계

---

## DETAIL: Q&A 전체 로그 {#qa-log}

### Round 1 (2026-01-21 17:00)
**Q:** 새 커맨드/스킬의 범위는 어디까지인가요?
**A:** 기존 /plan-draft 확장이 아닌, Agent/Skill/Hook을 전문적으로 다루는 **하나의 통합 커맨드** 생성

### Round 2 (2026-01-21 17:05)
**Q:** 3개의 draft 커맨드 중 어떤 것부터?
**A:** 3개 분리가 아닌, **하나의 통합 커맨드**로 Agent/Skill/Hook 중 선택하여 상호작용하며 생성

---

## DETAIL: Component Templates {#templates}

### Agent Template
```yaml
---
name: {agent_name}
description: {role_description}
tools: [Read, Grep, Glob]  # Default minimal
skills:
  accessible: []
  via_delegation: []
oda_context:
  role: {gate | controller | logger | validator | executor}
  stage_access: [A, B, C]
  evidence_required: {true | false}
  audit_integration: {true | false}
  governance_mode: {strict | standard}
  proposal_mandate: {REQUIRED | OPTIONAL}
integrates_with:
  agents: []
  hooks: []
model: {haiku | sonnet | opus}
context: {standard | fork}
---

# {Agent Name}

## Purpose
{detailed_description}

## Behavior
{behavioral_rules}
```

### Skill Template
```yaml
---
skill_name: {skill_name}
description: {purpose}
user_invocable: {true | false}
allowed_tools: [Read, Grep, Glob, Task, Edit, Write]
context: {standard | fork}
model: {sonnet | opus}
version: "1.0.0"
---

# /{skill_name} Command

## Purpose
{description}

## Execution Flow
1. {step1}
2. {step2}
...

## Output Format
{output_structure}
```

### Hook Template (Bash)
```bash
#!/bin/bash
# {Hook Name} - {HookType}
#
# File: .claude/hooks/{path}/{name}.sh
# Version: 1.0.0
# Trigger: {PreToolUse | PostToolUse} on {tool_name}
#
# Purpose:
#   {description}

set -euo pipefail

# Read input
INPUT=$(cat)

# Extract fields
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Logic here
{logic}

# Output
echo '{"hookSpecificOutput":{"permissionDecision":"allow"}}'
```

### Hook Template (Python)
```python
#!/usr/bin/env python3
"""
{Hook Name} - {HookType}

File: .claude/hooks/{path}/{name}.py
Version: 1.0.0
Trigger: {PreToolUse | PostToolUse} on {tool_name}
"""

import sys
import json
from pathlib import Path

def main():
    input_data = json.load(sys.stdin)
    tool_name = input_data.get("tool_name", "")

    # Logic here
    {logic}

    # Output
    result = {
        "hookSpecificOutput": {
            "permissionDecision": "allow"
        }
    }
    print(json.dumps(result))

if __name__ == "__main__":
    main()
```

---

## DETAIL: Comprehensive Q&A Patterns (claude-code-guide Research) {#qa-patterns}

> **Source:** Official Claude Code documentation research via claude-code-guide agent (2026-01-21)

### Agent Q&A Flow (Comprehensive - 15 Rounds)

#### Round 1-3: Core Identity
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 1 | Agent 이름? | text | lowercase, numbers, hyphens only, max 64 chars |
| 2 | Agent 설명? | text | Claude가 delegation 결정에 사용, "proactively" 포함 시 자동 트리거 |
| 3 | 자동 모델 호출 비활성화? | boolean | true: 수동 호출만, false: Claude 자동 호출 |

#### Round 4-6: Tool Configuration
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 4 | 허용 도구? | multiSelect | Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch, Task, Skill, TodoWrite, AskUserQuestion, NotebookEdit |
| 5 | 금지 도구? | multiSelect | (tools 설정과 배타적) |
| 6 | MCP 도구 접근? | multiSelect | mcp__namespace__tool_name 형식 |

#### Round 7-9: ODA Context (Governance)
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 7 | ODA 역할? | select | gate, controller, logger, validator, executor, chain_controller, schema_gate, anti_hallucination, audit_trail, mutation_control |
| 8 | 스테이지 접근? | multiSelect | A (SCAN), B (TRACE), C (VERIFY) |
| 9 | 거버넌스 설정? | grouped | evidence_required (bool), audit_integration (true/false/self), governance_mode (strict/inherit/warn), proposal_mandate (REQUIRED/OPTIONAL/FORBIDDEN) |

#### Round 10-12: Execution Context
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 10 | 모델? | select | haiku (fast), sonnet (balanced), opus (maximum), inherit |
| 11 | 컨텍스트 모드? | select | standard (shared), fork (isolated) |
| 12 | 권한 모드? | select | default, acceptEdits, dontAsk, bypassPermissions, plan |

#### Round 13-15: Integration & Features
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 13 | 연동 Agent? | multiSelect | 기존 .claude/agents/ 목록 |
| 14 | 연동 Hook 이벤트? | multiSelect | PreToolUse, PostToolUse, PreCompact, SessionStart, SessionEnd, SubagentStart, SubagentStop |
| 15 | V2.1.7+ 기능? | multiSelect | task_decomposer, context_budget_manager, resume_support, ultrathink_mode, llm_native_routing, mcp_proposal_integration |

---

### Skill Q&A Flow (Comprehensive - 12 Rounds)

#### Round 1-3: Identity & Invocation
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 1 | Skill 이름? | text | lowercase-with-hyphens, max 64 chars → /slash-command |
| 2 | 설명? | text | Claude 자동 호출 트리거에 사용 |
| 3 | 호출 방식? | grouped | user-invocable (bool): /메뉴 표시, disable-model-invocation (bool): 자동 호출 비활성화 |

#### Round 4-6: Execution Configuration
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 4 | 컨텍스트 모드? | select | standard (inline), fork (subagent 실행) |
| 5 | fork 시 Agent 타입? | select | Explore (haiku, read-only), Plan (read-only), general-purpose (full), 커스텀 에이전트 |
| 6 | 모델? | select | haiku, sonnet, opus, inherit |

#### Round 7-9: Tool & Permission
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 7 | 허용 도구? | multiSelect | Read, Grep, Glob, Bash, Edit, Write, WebFetch, WebSearch, Task, Skill, TodoWrite, AskUserQuestion |
| 8 | 인자 힌트? | text | 예: [issue-number], [filename] [format] |
| 9 | Skill 전용 Hook? | grouped | PreToolUse, PostToolUse, Stop 이벤트 |

#### Round 10-12: Content & Features
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 10 | 컨텐츠 타입? | select | reference (지식), task (워크플로우), background (숨은 컨텍스트) |
| 11 | 동적 명령 사용? | boolean | !`command` 문법으로 실행 전 데이터 주입 |
| 12 | 확장 사고 모드? | boolean | "ultrathink" 키워드 포함 → 31,999 토큰 확장 |

---

### Hook Q&A Flow (Comprehensive - 14 Rounds)

#### Round 1-3: Identity & Type
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 1 | Hook 이름? | text | 설명적 이름 (예: security-validator, audit-logger) |
| 2 | Hook 이벤트? | select | PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit, SessionStart, SessionEnd, SubagentStop, Stop, PreCompact, Setup, Notification |
| 3 | 구현 언어? | select | Bash, Python |

#### Round 4-6: Trigger Configuration
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 4 | Matcher 패턴? | text | 도구 이름 regex (예: Bash, Edit\|Write, mcp__github__.*, .*) |
| 5 | 타임아웃? | number | 초 단위 (기본 60) |
| 6 | Hook 타입? | select | command (스크립트), prompt (LLM 평가) |

#### Round 7-10: Input/Output (PreToolUse 전용)
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 7 | 권한 결정? | select | allow (자동 승인), deny (차단), ask (사용자 확인) |
| 8 | updatedInput 사용? | boolean | 도구 파라미터 수정 (tool_input 필드 변경) |
| 9 | additionalContext 사용? | boolean | Claude 컨텍스트에 정보 주입 |
| 10 | 입력 필드 접근? | multiSelect | session_id, tool_name, tool_input, tool_use_id, transcript_path, cwd, permission_mode |

#### Round 11-14: Output & Advanced
| Round | Question | Type | Options/Constraints |
|-------|----------|------|---------------------|
| 11 | 출력 필드? | multiSelect | continue (bool), stopReason, suppressOutput, systemMessage, hookSpecificOutput |
| 12 | 실행 차단 가능? | boolean | decision: "block" (PostToolUse, Stop, SubagentStop) |
| 13 | 환경 변수 사용? | multiSelect | CLAUDE_PROJECT_DIR, CLAUDE_PLUGIN_ROOT, CLAUDE_CODE_REMOTE, CLAUDE_ENV_FILE |
| 14 | 로그 경로? | text | .agent/logs/{name}.log |

---

### Hook Events Reference (Full List)

| Event | Matcher | Blocking | additionalContext | Use Case |
|-------|---------|----------|-------------------|----------|
| PreToolUse | ✅ tool regex | allow/deny/ask | ✅ | 도구 실행 전 검증/수정 |
| PostToolUse | ✅ tool regex | block | ✅ | 실행 후 검증/로깅 |
| PermissionRequest | ✅ tool regex | allow/deny | ❌ | 권한 요청 자동 처리 |
| UserPromptSubmit | ❌ | block | ✅ | 사용자 입력 전처리 |
| SessionStart | ✅ source | ❌ | ✅ | 세션 초기화 |
| SessionEnd | ❌ | ❌ | ❌ | 세션 정리 |
| SubagentStop | ❌ | block | ❌ | 서브에이전트 종료 제어 |
| Stop | ❌ | block | ❌ | 세션 종료 방지 |
| PreCompact | ✅ trigger | ❌ | ❌ | 컨텍스트 압축 전 처리 |
| Setup | ✅ trigger | ❌ | ✅ | 환경 설정 |
| Notification | ✅ type | ❌ | ❌ | 알림 로깅 |

---

## DETAIL: Plan Agent Integration {#plan-agent}

### Draft → Plan Flow
```
/create → Q&A → Draft 저장 → /plan --draft create_{type}_{name}
```

### Draft File Format (Plan Agent Optimized)
```markdown
# Create Draft: {type} - {name}

## INDEX (Plan Agent reads first)
- Type: {Agent | Skill | Hook}
- Name: {name}
- Status: READY_FOR_GENERATION
- Fields Completed: {N}/10

## Resolved Fields
| Field | Value | Round |
|-------|-------|-------|
| name | {value} | 1 |
| role | {value} | 2 |
...

## Template Preview
{filled_template}

## Generation Instructions
1. Create file at: {target_path}
2. Register in: {registry_if_applicable}
3. Test with: {test_command}
```

---

## DETAIL: File Structure {#file-structure}

### New Files to Create
```
.claude/
├── commands/
│   └── create.md          # Command definition (user-facing)
├── skills/
│   └── create.md          # Skill implementation
└── templates/
    ├── agent.yaml         # Agent template
    ├── skill.yaml         # Skill template
    ├── hook-bash.sh       # Bash hook template
    └── hook-python.py     # Python hook template
```

### Draft Storage
```
.agent/plans/
└── create_drafts/
    ├── agent_{name}.md
    ├── skill_{name}.md
    └── hook_{name}.md
```

---

---

## DETAIL: Research Summary (claude-code-guide) {#research-summary}

### Agent Fields Discovered (30+ fields)
- **Core**: name, description, disable-model-invocation
- **Tools**: tools, disallowedTools, mcp_tools
- **Skills**: skills.accessible, skills.via_delegation, skills.auto_trigger
- **ODA Context**: role (9 types), stage_access, evidence_required, audit_integration, governance_mode, proposal_mandate
- **Execution**: model, context, permissionMode
- **Integration**: integrates_with.agents, integrates_with.hooks
- **V2.1.7+**: v21x_features, context_management, ultrathink_config

### Skill Fields Discovered (15+ fields)
- **Identity**: name, description, version
- **Invocation**: user-invocable, disable-model-invocation, argument-hint
- **Execution**: model, context, agent (for fork), allowed-tools
- **Features**: hooks (scoped), $ARGUMENTS, !`dynamic commands`, ultrathink
- **Content Types**: reference, task workflow, background context

### Hook Fields Discovered (40+ fields)
- **11 Event Types**: PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit, SessionStart, SessionEnd, SubagentStop, Stop, PreCompact, Setup, Notification
- **Registration**: matcher (regex), type (command/prompt), command, timeout
- **Input**: session_id, tool_name, tool_input, tool_use_id, transcript_path, cwd, permission_mode
- **Output**: continue, stopReason, suppressOutput, systemMessage, hookSpecificOutput
- **Native Capabilities**: updatedInput, additionalContext, permissionDecision, decision (block)

---

## Metadata

- Created: 2026-01-21 17:00
- Last Updated: 2026-01-21 17:10
- Q&A Rounds: 5 (User) + 3 (Research Agents)
- Status: IN_PROGRESS → READY_FOR_IMPLEMENTATION
- Research: ✅ Completed (claude-code-guide x3)
- Next: /build command and skill file generation

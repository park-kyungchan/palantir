---
name: tool-config
description: |
  Shared parameter module for tool allowlist/denylist configuration.
  Used by: Agent, Skill builders
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Tool Configuration Parameter Module

> **Purpose:** 컴포넌트에서 사용 가능한 도구 설정
> **Caller:** agent-builder, skill-builder

---

## Parameters Covered

| Parameter | Type | Values | Version | Conflict |
|-----------|------|--------|---------|----------|
| `allowed-tools` | array | Tool names | V2.0+ | disallowed-tools |
| `disallowed-tools` | array | Tool names | V2.0+ | allowed-tools |
| `tools` (Agent) | array | Tool names | V2.0+ | - |

---

## Available Tools (V2.1.19)

### Core Tools

| Tool | Category | Description |
|------|----------|-------------|
| `Read` | File | 파일 읽기 |
| `Write` | File | 파일 쓰기 (새 파일) |
| `Edit` | File | 파일 편집 (기존 파일) |
| `Glob` | Search | 파일 패턴 검색 |
| `Grep` | Search | 내용 검색 |
| `Bash` | System | 쉘 명령 실행 |

### Agent & Task Tools

| Tool | Category | Description |
|------|----------|-------------|
| `Task` | Agent | 서브에이전트 생성 |
| `TaskCreate` | Task | 작업 생성 |
| `TaskUpdate` | Task | 작업 업데이트 |
| `TaskList` | Task | 작업 목록 |
| `TaskGet` | Task | 작업 상세 |

### Interaction Tools

| Tool | Category | Description |
|------|----------|-------------|
| `AskUserQuestion` | User | 사용자 질문 |
| `WebFetch` | Web | URL 컨텐츠 가져오기 |
| `WebSearch` | Web | 웹 검색 |

### Specialized Tools

| Tool | Category | Description |
|------|----------|-------------|
| `NotebookEdit` | Jupyter | 노트북 편집 |
| `Skill` | Skill | 스킬 실행 |
| `EnterPlanMode` | Mode | 플랜 모드 진입 |
| `ExitPlanMode` | Mode | 플랜 모드 종료 |

### MCP Tools (Dynamic)

| Pattern | Description |
|---------|-------------|
| `mcp__*` | MCP 서버 제공 도구 |
| `mcp__github-mcp-server__*` | GitHub MCP 도구 |
| `mcp__context7__*` | Context7 문서 도구 |

---

## Round 1: Configuration Mode

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "도구 접근 방식을 선택하세요:",
        "header": "Tool Access",
        "options": [
            {
                "label": "모든 도구 허용 (Recommended)",
                "description": "모든 도구 사용 가능 (기본값)"
            },
            {
                "label": "허용 목록 지정 (allowlist)",
                "description": "특정 도구만 허용"
            },
            {
                "label": "제외 목록 지정 (denylist)",
                "description": "특정 도구만 제외"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-tool-config-mode"}
)
```

---

## Round 2: Allowlist Selection (Conditional)

> **Condition:** "허용 목록 지정" 선택 시

### Q&A Flow

```python
if mode == "allowlist":
    response = AskUserQuestion(
        questions=[{
            "question": "허용할 도구를 선택하세요 (복수 선택 가능):",
            "header": "Allow",
            "options": [
                {"label": "Read", "description": "파일 읽기"},
                {"label": "Write + Edit", "description": "파일 쓰기/편집"},
                {"label": "Glob + Grep", "description": "파일/내용 검색"},
                {"label": "Bash", "description": "쉘 명령 실행"}
            ],
            "multiSelect": True
        }],
        metadata={"source": "build-tool-allowlist"}
    )
```

### Preset Bundles

| Preset | Tools Included |
|--------|----------------|
| `read-only` | Read, Glob, Grep |
| `file-ops` | Read, Write, Edit, Glob, Grep |
| `full-access` | All tools |
| `exploration` | Read, Glob, Grep, Task |
| `build` | Read, Write, Edit, Glob, Grep, Bash |

---

## Round 3: Denylist Selection (Conditional)

> **Condition:** "제외 목록 지정" 선택 시

### Q&A Flow

```python
if mode == "denylist":
    response = AskUserQuestion(
        questions=[{
            "question": "제외할 도구를 선택하세요 (복수 선택 가능):",
            "header": "Deny",
            "options": [
                {"label": "Bash", "description": "쉘 명령 실행 금지"},
                {"label": "Write + Edit", "description": "파일 수정 금지"},
                {"label": "Task", "description": "서브에이전트 생성 금지"},
                {"label": "Web*", "description": "웹 접근 금지"}
            ],
            "multiSelect": True
        }],
        metadata={"source": "build-tool-denylist"}
    )
```

---

## Conflict Resolution

```python
# allowed-tools와 disallowed-tools는 동시 사용 불가
if allowed_tools and disallowed_tools:
    raise ConfigError(
        "allowed-tools와 disallowed-tools는 동시에 지정할 수 없습니다. "
        "하나만 선택하세요."
    )
```

---

## Output Format

### Return to Caller

```yaml
tool_config:
  mode: "allowlist"           # "all", "allowlist", "denylist"
  allowed_tools:              # Only if mode=allowlist
    - Read
    - Glob
    - Grep
    - AskUserQuestion
  disallowed_tools: null      # Only if mode=denylist
```

### YAML Frontmatter Fragment

```yaml
# For allowlist
allowed-tools:
  - Read
  - Glob
  - Grep
  - AskUserQuestion

# For denylist
disallowed-tools:
  - Bash
  - Write
  - Edit
```

---

## Common Patterns

### Read-Only Analyzer

```yaml
allowed-tools:
  - Read
  - Glob
  - Grep
```

### Builder with File Access

```yaml
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
```

### User-Interactive Skill

```yaml
allowed-tools:
  - Read
  - Grep
  - Glob
  - AskUserQuestion
  - Task
```

### No External Access

```yaml
disallowed-tools:
  - WebFetch
  - WebSearch
  - Bash
```

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | `allowed-tools`, `disallowed-tools` |
| V2.1+ | MCP tools support (`mcp__*`) |
| V2.1.16+ | Task tools added (TaskCreate, etc.) |

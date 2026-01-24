# /build Skill - Interactive Component Builder

> **Version:** 2.0.0 | **Context:** standard | **Model:** sonnet
> **user-invocable:** true | **argument-hint:** ["concept"] | [agent|skill|hook] [--resume id]

---

## Purpose

Enhanced builder with two modes:
1. **Concept Mode**: `/build "concept-name"` - Three-phase research, roadmap, and build
2. **Direct Mode**: `/build agent|skill|hook` - Traditional Q&A rounds

---

## Three-Phase Pattern Overview

```
┌───────────────────────────────────────────────────────────┐
│ /build "Progressive-Disclosure" (Concept Mode)            │
├───────────────────────────────────────────────────────────┤
│                                                           │
│ PHASE 0: RESEARCH (Delegated to build-research.md)        │
│   └─ Task(subagent_type="claude-code-guide")              │
│      └─ Discover all relevant capabilities                │
│      └─ Save to .agent/builds/{id}/research.json          │
│                                                           │
│ PHASE 1: ROADMAP (L1/L2/L3 Progressive Disclosure)        │
│   ├─ L1: Summary (500 tokens)                             │
│   │   "Found 12 capabilities across 3 categories"         │
│   ├─ L2: Index (complexity levels)                        │
│   │   Level 0/50/100 options                              │
│   └─ L3: Details (on-demand via Read)                     │
│                                                           │
│ PHASE 2: BUILD (Multi-round Selection)                    │
│   ├─ Round 1: Target complexity level (0/50/100)          │
│   ├─ Round 2-N: Feature selection (4 per round)           │
│   └─ Generate artifacts                                   │
│                                                           │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│ /build agent|skill|hook (Direct Mode)                     │
├───────────────────────────────────────────────────────────┤
│ Traditional Q&A rounds for component creation             │
│ (See Phase 3: Type Selection below)                       │
└───────────────────────────────────────────────────────────┘
```

---

## Initialization

Parse `$ARGUMENTS` to determine build mode:

```python
args = "$ARGUMENTS".strip()
build_mode = None
concept = None
component_type = None
resume_id = None

# Priority 1: Resume flag
if "--resume" in args:
    parts = args.split("--resume")
    resume_id = parts[1].strip().split()[0] if len(parts) > 1 else None
    build_mode = "resume"

# Priority 2: Concept mode (quoted string)
elif args.startswith('"') or args.startswith("'"):
    concept = args.strip('"').strip("'")
    build_mode = "concept"

# Priority 3: Direct mode (agent/skill/hook)
elif args.split()[0] in ["agent", "skill", "hook"] if args else False:
    component_type = args.split()[0]
    build_mode = "direct"

# Priority 4: No args → prompt selection
else:
    build_mode = "select"
```

### Build Mode Decision Tree

| Input | Mode | Next Phase |
|-------|------|------------|
| `--resume pd-a1b2` | resume | Load state from `.agent/builds/{id}/` |
| `"Progressive-Disclosure"` | concept | Phase 0: Research |
| `agent` | direct | Phase 3: Type Selection (skip to agent) |
| (empty) | select | Phase 3: Type Selection (prompt) |

---

## Phase 0: Research (Concept Mode Only)

**Triggered by:** `/build "concept-name"`

### 0.1 Delegate to build-research.md

```python
# Invoke build-research skill for Phase 0
# This skill:
# 1. Generates build_id (e.g., "pro-a1b2")
# 2. Delegates to claude-code-guide
# 3. Saves research.json
# 4. Returns L1 summary

# The skill handles all research logic internally
# Main Agent receives L1 summary with:
# - buildId
# - complexityOptions (Level 0/50/100)
# - l2Path for detailed research
```

### 0.2 Research Output (L1 Summary)

After build-research.md completes:

```yaml
buildId: "pro-a1b2"
concept: "Progressive-Disclosure"
summary: "Found 14 capabilities across 4 categories"
status: success
complexityOptions:
  - level: 0
    name: "Basic"
    capabilities: 4
  - level: 50
    name: "Recommended"
    capabilities: 9
  - level: 100
    name: "Full"
    capabilities: 14
l2Path: ".agent/builds/pro-a1b2/research.json"
nextActionHint: "Select complexity level"
```

→ Proceed to Phase 1: Roadmap

---

## Phase 1: Roadmap (Concept Mode Only)

**Triggered after:** Phase 0 completes with L1 summary

### 1.1 Complexity Level Selection

```
AskUserQuestion(
  questions=[{
    "question": "어떤 복잡도 레벨을 선택하시겠습니까?",
    "header": "Complexity",
    "options": [
      {"label": "Level 0 - Basic (4 capabilities)", "description": "Essential features: L1/L2 format, basic validation"},
      {"label": "Level 50 - Recommended (9 capabilities)", "description": "Production-ready: priority system, output preservation"},
      {"label": "Level 100 - Full (14 capabilities)", "description": "All features: context optimization, lazy loading"},
      {"label": "Custom - Manual Selection", "description": "Choose individual capabilities"}
    ],
    "multiSelect": false
  }]
)
```

### 1.2 Roadmap Presentation (Based on Selection)

After level selection, present the roadmap from research.json:

```markdown
## Build Roadmap: {concept}

**Build ID:** `{buildId}`
**Selected Level:** {level} ({name})
**Capabilities:** {count}

### Included Capabilities

| ID | Name | Category | Description |
|----|------|----------|-------------|
| S1 | pd-inject | skill | Core L1/L2 format injection |
| H1 | pre-task-inject | hook | Format enforcement |
| ... | ... | ... | ... |

### Dependencies Resolved
- [S1] → [S2], [H1] (automatically included)

### Next Steps
Proceed to Phase 2: Build to generate files?
```

### 1.3 Roadmap Confirmation

```
AskUserQuestion(
  questions=[{
    "question": "Roadmap을 확인하셨나요? 빌드를 진행하시겠습니까?",
    "header": "Confirm",
    "options": [
      {"label": "Yes, proceed to build", "description": "Generate files for selected capabilities"},
      {"label": "Change level", "description": "Select different complexity level"},
      {"label": "Custom selection", "description": "Manually add/remove capabilities"},
      {"label": "Save roadmap only", "description": "Exit without building"}
    ],
    "multiSelect": false
  }]
)
```

→ If "Yes", proceed to Phase 2: Build
→ If "Custom selection", proceed to multi-round capability selection

---

## Phase 2: Build (Concept Mode Multi-Round Selection)

**Triggered after:** Phase 1 confirmation

### 2.1 Capability Selection (If Custom or Level 50+)

For levels with many capabilities, batch into rounds (4 options per round):

**Round 1: Skills**
```
AskUserQuestion(
  questions=[{
    "question": "포함할 Skill을 선택하세요",
    "header": "Skills",
    "options": [
      {"label": "[S1] pd-inject (Required)", "description": "Core L1/L2 format injection"},
      {"label": "[S2] priority-handler", "description": "Priority-based reading strategy"},
      {"label": "[S3] token-estimator", "description": "Section token estimation"},
      {"label": "[S4] recommended-read", "description": "Auto-populate recommendedRead"}
    ],
    "multiSelect": true
  }]
)
```

**Round 2: Agents**
```
AskUserQuestion(
  questions=[{
    "question": "포함할 Agent를 선택하세요",
    "header": "Agents",
    "options": [
      {"label": "[A1] l1l2-validator", "description": "Validates L1/L2 output format"},
      {"label": "[A2] progressive-reader", "description": "Reads L2 sections on-demand"},
      {"label": "Skip agents", "description": "No agents needed"}
    ],
    "multiSelect": true
  }]
)
```

**Round 3: Hooks**
```
AskUserQuestion(
  questions=[{
    "question": "포함할 Hook을 선택하세요",
    "header": "Hooks",
    "options": [
      {"label": "[H1] pre-task-inject (Required)", "description": "Injects L1/L2 format"},
      {"label": "[H2] post-task-validate", "description": "Validates L1 compliance"},
      {"label": "[H3] priority-alert", "description": "CRITICAL priority notification"},
      {"label": "[H4] output-preserve", "description": "Preserves L2 files"}
    ],
    "multiSelect": true
  }]
)
```

### 2.2 Selection Persistence

Save selections to `.agent/builds/{buildId}/selection.json`:

```json
{
  "buildId": "pro-a1b2",
  "selectedLevel": 50,
  "selectedCapabilities": ["S1", "S2", "A1", "H1", "H2", "H3"],
  "rounds": [
    {"roundNumber": 1, "category": "skills", "selected": ["S1", "S2"]},
    {"roundNumber": 2, "category": "agents", "selected": ["A1"]},
    {"roundNumber": 3, "category": "hooks", "selected": ["H1", "H2", "H3"]}
  ],
  "status": "selection_complete",
  "timestamp": "2026-01-23T15:00:00Z"
}
```

### 2.3 File Generation

Generate files for selected capabilities:

```python
for capability in selected_capabilities:
    template = load_template(capability.category)
    content = render_template(template, capability)
    write_file(capability.output_path, content)

# Save artifacts list
artifacts = {
    "buildId": build_id,
    "generated_files": [
        {"path": ".claude/skills/pd-inject.md", "type": "skill"},
        {"path": ".claude/hooks/pre-task-inject.sh", "type": "hook"},
        ...
    ],
    "timestamp": datetime.now().isoformat()
}
save_json(f".agent/builds/{build_id}/artifacts.json", artifacts)
```

### 2.4 Build Complete Summary

```markdown
## Build Complete: {concept}

**Build ID:** `{buildId}`
**Generated Files:** {count}

### Files Created

| Type | Path | Status |
|------|------|--------|
| skill | .claude/skills/pd-inject.md | ✅ Created |
| hook | .claude/hooks/pre-task-inject.sh | ✅ Created |
| ... | ... | ... |

### Test Commands

```bash
# Test skill
/pd-inject "test input"

# Test hook (triggered automatically on Task tool)
```

### Resume Command
```
/build --resume {buildId}
```
```

---

## Phase 3: Type Selection (Direct Mode)

If `component_type` is None and `resume_name` is None:

```
AskUserQuestion(
  questions=[{
    "question": "어떤 컴포넌트를 생성하시겠습니까?",
    "header": "Type",
    "options": [
      {"label": "Agent (Recommended)", "description": "Specialized subagent with ODA governance"},
      {"label": "Skill", "description": "Reusable /command workflow"},
      {"label": "Hook", "description": "Event-driven script"}
    ],
    "multiSelect": false
  }]
)
```

---

## Phase 4: Q&A Execution (Direct Mode)

### Agent Builder (15 Rounds)

#### Rounds 1-3: Core Identity
```
AskUserQuestion(
  questions=[
    {
      "question": "Agent 이름을 입력하세요 (예: security-validator)",
      "header": "Name",
      "options": [
        {"label": "직접 입력", "description": "lowercase, hyphens, max 64 chars"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `name` (text validation: `^[a-z][a-z0-9-]{0,63}$`)

```
AskUserQuestion(
  questions=[
    {
      "question": "Agent 설명을 입력하세요",
      "header": "Description",
      "options": [
        {"label": "직접 입력", "description": "Claude 자동 호출 트리거에 사용. 'proactively' 포함 시 자동 활성화"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `description`

```
AskUserQuestion(
  questions=[
    {
      "question": "Claude 자동 호출을 비활성화하시겠습니까?",
      "header": "Auto-invoke",
      "options": [
        {"label": "No (Recommended)", "description": "Claude가 적절할 때 자동 호출"},
        {"label": "Yes", "description": "수동 호출만 허용"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `disable-model-invocation` (boolean)

#### Rounds 4-6: Tool Configuration
```
AskUserQuestion(
  questions=[
    {
      "question": "허용할 도구를 선택하세요",
      "header": "Tools",
      "options": [
        {"label": "Read-only (Recommended)", "description": "Read, Grep, Glob"},
        {"label": "Standard", "description": "Read, Grep, Glob, Bash, Edit, Write"},
        {"label": "Full", "description": "All tools including Task, WebSearch"},
        {"label": "Custom", "description": "직접 선택"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ If "Custom" selected, show multiSelect for individual tools

#### Rounds 7-9: ODA Context
```
AskUserQuestion(
  questions=[
    {
      "question": "ODA 역할을 선택하세요",
      "header": "ODA Role",
      "options": [
        {"label": "validator", "description": "입력/출력 검증"},
        {"label": "executor", "description": "액션 실행"},
        {"label": "gate", "description": "접근 제어"},
        {"label": "controller", "description": "워크플로우 제어"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `oda_context.role`

```
AskUserQuestion(
  questions=[
    {
      "question": "접근 가능한 스테이지를 선택하세요",
      "header": "Stages",
      "options": [
        {"label": "A (SCAN)", "description": "파일 탐색, 구조 분석"},
        {"label": "B (TRACE)", "description": "임포트 검증, 시그니처 확인"},
        {"label": "C (VERIFY)", "description": "품질 검사, 테스트 실행"}
      ],
      "multiSelect": true
    }
  ]
)
```

→ Collect: `oda_context.stage_access`

#### Rounds 10-12: Execution Context
```
AskUserQuestion(
  questions=[
    {
      "question": "사용할 모델을 선택하세요",
      "header": "Model",
      "options": [
        {"label": "haiku (Recommended)", "description": "빠른 응답, 간단한 작업"},
        {"label": "sonnet", "description": "균형잡힌 성능"},
        {"label": "opus", "description": "최대 품질, 복잡한 작업"}
      ],
      "multiSelect": false
    }
  ]
)
```

→ Collect: `model`

#### Rounds 13-15: Integration
```
AskUserQuestion(
  questions=[
    {
      "question": "연동할 Hook 이벤트를 선택하세요",
      "header": "Hooks",
      "options": [
        {"label": "None", "description": "Hook 연동 없음"},
        {"label": "PreToolUse", "description": "도구 실행 전 검증"},
        {"label": "PostToolUse", "description": "도구 실행 후 로깅"},
        {"label": "SubagentStop", "description": "서브에이전트 종료 제어"}
      ],
      "multiSelect": true
    }
  ]
)
```

---

### Skill Builder (12 Rounds)

#### Rounds 1-3: Identity
- name, description, user-invocable

#### Rounds 4-6: Execution
- context (standard/fork), agent type (if fork), model

#### Rounds 7-9: Tools
- allowed-tools, argument-hint, hooks

#### Rounds 10-12: Features
- content-type, dynamic-commands (!`cmd`), ultrathink

---

### Hook Builder (14 Rounds)

#### Rounds 1-3: Identity
- name, event-type, language (Bash/Python)

#### Rounds 4-6: Trigger
- matcher pattern, timeout, type (command/prompt)

#### Rounds 7-10: Input/Output (PreToolUse)
- permissionDecision, updatedInput, additionalContext, input fields

#### Rounds 11-14: Advanced
- output fields, blocking capability, env vars, log path

---

## Phase 5: Draft Generation

After all rounds, generate draft file:

```markdown
# Build Draft: {type} - {name}

## INDEX
- Type: {Agent | Skill | Hook}
- Name: {collected_name}
- Status: READY_FOR_GENERATION
- Rounds Completed: {N}/{total}

## Collected Fields
| Field | Value | Round |
|-------|-------|-------|
{field_table}

## Generated Preview
```{yaml_or_code}
{template_with_values}
```

## Target Path
{output_path}

## Test Command
{test_command}
```

Save to: `.agent/plans/create_drafts/{type}_{name}.md`

---

## Phase 6: Confirmation & Generation

```
AskUserQuestion(
  questions=[{
    "question": "생성된 미리보기를 확인하셨나요? 파일을 생성하시겠습니까?",
    "header": "Confirm",
    "options": [
      {"label": "Yes, generate", "description": "파일 생성 진행"},
      {"label": "Edit fields", "description": "Q&A 다시 진행"},
      {"label": "Save draft only", "description": "드래프트만 저장"}
    ],
    "multiSelect": false
  }]
)
```

On "Yes, generate":
1. Write file to target path
2. Update settings.json if Hook (add to hooks array)
3. Show success message with test command

---

## Templates Reference

### Agent Template
```yaml
---
name: {name}
description: {description}
tools: {tools}
oda_context:
  role: {role}
  stage_access: {stages}
  evidence_required: {bool}
  governance_mode: {mode}
model: {model}
context: {context}
---

# {Name} Agent

## Purpose
{description}

## Behavior
{behavior_rules}
```

### Skill Template
```yaml
---
skill_name: {name}
description: {description}
user_invocable: {bool}
allowed_tools: {tools}
context: {context}
model: {model}
---

# /{name} Command

## Purpose
{description}

## Execution Flow
1. {step}
```

### Hook Template (Bash)
```bash
#!/bin/bash
# {name} - {event_type}
# Trigger: {event_type} on {matcher}

set -euo pipefail
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""')

# Logic
{logic}

echo '{"hookSpecificOutput":{"permissionDecision":"{decision}"}}'
```

### Hook Template (Python)
```python
#!/usr/bin/env python3
"""
{name} - {event_type}
Trigger: {event_type} on {matcher}
"""
import sys, json

def main():
    data = json.load(sys.stdin)
    # Logic
    {logic}
    print(json.dumps({"hookSpecificOutput": {"permissionDecision": "{decision}"}}))

if __name__ == "__main__":
    main()
```

---

## Error Handling

| Error | Action |
|-------|--------|
| Invalid name format | Re-prompt with validation hint |
| Draft not found (resume) | List available drafts |
| File already exists | Ask overwrite confirmation |
| Settings.json parse error | Manual hook registration hint |

---

## State Persistence

Draft auto-saves after each round:
- Location: `.agent/plans/create_drafts/{type}_{name}.md`
- Format: Markdown with YAML frontmatter
- Resume: `/build --resume {type}_{name}`

---

## Integration Points

| System | Integration |
|--------|-------------|
| /plan | Draft handoff for complex builds |
| settings.json | Hook auto-registration |
| ODA Registry | Agent registration (future) |
| Template System | Base templates for all types |

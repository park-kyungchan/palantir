---
name: build
description: |
  Interactive Component Builder (Modular Architecture v2.2).
  Two modes: Concept Mode for research-driven builds, Direct Mode for Q&A component creation.
  Delegates to specialized builders and shared parameter modules.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "2.2.0"
argument-hint: ["concept"] | [agent|skill|hook] [--resume id]
---

# /build Skill - Interactive Component Builder

> **Version:** 2.2.0 | **Architecture:** Modular Orchestrator

---

## Purpose

Orchestrates component creation through two modes:

| Mode | Trigger | Flow |
|------|---------|------|
| **Concept** | `/build "concept-name"` | Research → Roadmap → Multi-round Build |
| **Direct** | `/build agent\|skill\|hook` | Q&A Rounds → Generation |

---

## Architecture

```
SKILL.md (Orchestrator ~250 lines)
    │
    ├─► builders/           (Component-specific Q&A)
    │   ├── agent-builder.md
    │   ├── skill-builder.md
    │   └── hook-builder.md
    │
    ├─► parameters/         (Shared parameter modules)
    │   ├── model-selection.md
    │   ├── context-mode.md
    │   ├── tool-config.md
    │   ├── hook-config.md
    │   ├── permission-mode.md
    │   └── task-params.md
    │
    └─► templates/          (Output schemas)
        ├── agent-template.yaml
        ├── skill-template.yaml
        ├── hook-bash-template.sh
        └── hook-python-template.py
```

---

## Mode Detection

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

### Mode Decision Tree

| Input | Mode | Next Action |
|-------|------|-------------|
| `--resume pd-a1b2` | resume | Load `.agent/builds/{id}/state.json` |
| `"Progressive-Disclosure"` | concept | Phase 0: Research Delegation |
| `agent` | direct | Delegate to `builders/agent-builder.md` |
| `skill` | direct | Delegate to `builders/skill-builder.md` |
| `hook` | direct | Delegate to `builders/hook-builder.md` |
| (empty) | select | Prompt Type Selection |

---

## Phase 0-2: Concept Mode

### Phase 0: Research Delegation

```python
# Delegate to /build-research skill
# Input: concept name
# Output: L1 summary with build_id, complexity options, l2_path

research_result = invoke_skill("build-research", concept)

# Result structure:
# {
#   "buildId": "pro-a1b2",
#   "summary": "Found N capabilities across M categories",
#   "complexityOptions": [
#     {"level": 0, "name": "Basic", "count": 4},
#     {"level": 50, "name": "Recommended", "count": 9},
#     {"level": 100, "name": "Full", "count": 14}
#   ],
#   "l2Path": ".agent/builds/pro-a1b2/research.json"
# }
```

### Phase 1: Roadmap Selection

```
AskUserQuestion(
  questions=[{
    "question": "어떤 복잡도 레벨을 선택하시겠습니까?",
    "header": "Complexity",
    "options": [
      {"label": "Level 0 - Basic", "description": "Essential features only"},
      {"label": "Level 50 - Recommended", "description": "Production-ready"},
      {"label": "Level 100 - Full", "description": "All features"},
      {"label": "Custom", "description": "Manual capability selection"}
    ],
    "multiSelect": false
  }]
)
```

### Phase 2: Build Execution

Multi-round capability selection (batched by category):
- Round 1: Skills selection
- Round 2: Agents selection
- Round 3: Hooks selection

Generate files using templates from `templates/`.

---

## Phase 3: Type Selection (Direct Mode)

If `build_mode == "select"`:

```
AskUserQuestion(
  questions=[{
    "question": "어떤 컴포넌트를 생성하시겠습니까?",
    "header": "Type",
    "options": [
      {"label": "Agent (Recommended)", "description": "Specialized subagent"},
      {"label": "Skill", "description": "Reusable /command workflow"},
      {"label": "Hook", "description": "Event-driven script"}
    ],
    "multiSelect": false
  }]
)
```

---

## Phase 4: Builder Delegation

### Agent Builder

```python
# Delegate to builders/agent-builder.md
# This builder handles:
# - Rounds 1-3: Core Identity (name, description, auto-invoke)
# - Rounds 4-6: Tool Configuration (delegate to parameters/tool-config.md)
# - Rounds 7-9: Context & Subagent (delegate to parameters/context-mode.md)
# - Rounds 10-12: Model & Execution (delegate to parameters/model-selection.md)
# - Rounds 13-15: Output & Governance

collected = delegate_to_builder("agent-builder", state)
```

### Skill Builder

```python
# Delegate to builders/skill-builder.md
# This builder handles:
# - Rounds 1-3: Identity & Access Control
# - Rounds 4-6: Execution Context (delegate to parameters/context-mode.md)
# - Rounds 7-9: Tool Configuration (delegate to parameters/tool-config.md)
# - Rounds 10-12: Advanced Features

collected = delegate_to_builder("skill-builder", state)
```

### Hook Builder

```python
# Delegate to builders/hook-builder.md
# This builder handles:
# - Rounds 1-3: Identity & Event Type
# - Rounds 4-6: Trigger Configuration (delegate to parameters/hook-config.md)
# - Rounds 7-10: Input/Output Configuration
# - Rounds 11-14: Advanced Configuration

collected = delegate_to_builder("hook-builder", state)
```

---

## Phase 5: Draft Generation

After all rounds complete, generate draft:

```python
draft_path = f".agent/plans/create_drafts/{component_type}_{name}.md"

# Load appropriate template
template_path = f"templates/{component_type}-template.yaml"
if component_type == "hook":
    template_path = f"templates/hook-{language}-template.{ext}"

# Render template with collected values
content = render_template(template_path, collected)

# Save draft
save_draft(draft_path, {
    "type": component_type,
    "name": name,
    "status": "READY_FOR_GENERATION",
    "collected": collected,
    "preview": content,
    "target_path": get_target_path(component_type, name)
})
```

---

## Phase 6: Confirmation & Generation

```
AskUserQuestion(
  questions=[{
    "question": "생성된 미리보기를 확인하셨나요? 파일을 생성하시겠습니까?",
    "header": "Confirm",
    "options": [
      {"label": "Yes, generate", "description": "Create file at target path"},
      {"label": "Edit fields", "description": "Re-run specific Q&A rounds"},
      {"label": "Save draft only", "description": "Save for later completion"}
    ],
    "multiSelect": false
  }]
)
```

### On "Yes, generate"

```python
# 1. Write to target path
target_path = get_target_path(component_type, name)
write_file(target_path, content)

# 2. Hook-specific: Register in settings.json
if component_type == "hook":
    register_hook_in_settings(hook_config)

# 3. Report success
print(f"✅ Created: {target_path}")
print(f"Test command: {get_test_command(component_type, name)}")
```

---

## State Management

### State File Structure

```json
{
  "buildId": "pro-a1b2",
  "mode": "concept|direct",
  "componentType": "agent|skill|hook",
  "currentPhase": 4,
  "currentRound": 7,
  "collected": {
    "name": "my-agent",
    "description": "...",
    "model": "sonnet"
  },
  "timestamp": "2026-01-24T12:00:00Z"
}
```

### Resume Flow

```python
if build_mode == "resume":
    state = load_state(f".agent/builds/{resume_id}/state.json")

    if not state:
        # List available drafts
        drafts = glob(".agent/builds/*/state.json")
        show_available_drafts(drafts)
        return

    # Resume from last checkpoint
    phase = state["currentPhase"]
    round = state["currentRound"]
    continue_from(phase, round, state)
```

### Auto-Save

State auto-saves after each round:

```python
def on_round_complete(round_num, collected_value):
    state["currentRound"] = round_num + 1
    state["collected"][field_name] = collected_value
    save_state(state)
```

---

## Target Paths

| Type | Path |
|------|------|
| Agent | `.claude/agents/{name}.md` |
| Skill | `.claude/skills/{name}/SKILL.md` |
| Hook (Bash) | `.claude/hooks/{name}.sh` |
| Hook (Python) | `.claude/hooks/{name}.py` |

---

## Error Handling

| Error | Recovery |
|-------|----------|
| Invalid name | Re-prompt with validation hint (`^[a-z][a-z0-9-]{0,63}$`) |
| Draft not found | List available drafts |
| File exists | Ask overwrite confirmation |
| Builder error | Show error, allow retry |

---

## Integration Points

| System | Integration |
|--------|-------------|
| `/build-research` | Concept mode research delegation |
| `builders/*.md` | Component-specific Q&A |
| `parameters/*.md` | Shared parameter selection |
| `templates/*` | Output file templates |
| `settings.json` | Hook auto-registration |

---

## Parameter Module Compatibility (V2.2.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.2.0: builders 및 templates와 통합 |
| `hook-config.md` | ✅ | Hook builder 통합 |
| `permission-mode.md` | ✅ | Component-specific permission handling |
| `task-params.md` | ✅ | Build-research task delegation |

### Version History

| Version | Change |
|---------|--------|
| 2.1.0 | V2.1.19 Spec 호환 |
| 2.2.0 | Concept Mode + Parameter Module Architecture |

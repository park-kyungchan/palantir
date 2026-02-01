---
name: build
description: |
  Interactive Component Builder (Modular Architecture v3.0).
  Two modes: Concept Mode for research-driven builds, Direct Mode for Q&A component creation.
  Delegates to specialized builders and shared parameter modules.

  Core Capabilities:
  - Concept Mode: Research-driven multi-phase component creation
  - Direct Mode: Q&A-based rapid component generation
  - Builder Delegation: Specialized builders for agents, skills, hooks
  - Template System: Configurable output templates

  Output Format:
  - L1: Build session summary (YAML)
  - L2: Component specification detail (Markdown)
  - L3: Generated component files

  Pipeline Position:
  - Standalone utility skill
  - Delegates to /build-research for concept research
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: ["concept"] | [agent|skill|hook] [--resume id]
allowed-tools:
  - Read
  - Write
  - Glob
  - Grep
  - Task
  - mcp__sequential-thinking__sequentialthinking
  - AskUserQuestion
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/build-finalize.sh"
      timeout: 60000

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 3
  delegation_strategy: "phase-based"
  strategies:
    phase_based:
      description: "Delegate by build phase (research, Q&A, generation)"
      use_when: "Concept mode with multi-phase workflow"
    builder_based:
      description: "Delegate to specialized builders"
      use_when: "Direct mode component creation"
  sub_agent_permissions:
    - Read
    - Write
    - Glob
    - AskUserQuestion
  output_paths:
    l1: ".agent/prompts/{slug}/build/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/build/l2_index.md"
    l3: ".agent/prompts/{slug}/build/l3_details/"
  return_format:
    l1: "Build summary with component type and generation status (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/build/l2_index.md"
    l3_path: ".agent/prompts/{slug}/build/l3_details/"
    requires_l2_read: false
    next_action_hint: "Generated files in .claude/{type}s/"

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Single component, direct mode
    moderate: 2    # Concept mode, basic research
    complex: 3     # Concept mode, multi-component generation
  synchronization_strategy: "sequential"  # Build phases are sequential
  aggregation_strategy: "chain"           # Each phase feeds next

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "Component name follows ^[a-z][a-z0-9-]{0,63}$ pattern"
    - "All required fields are collected"
    - "Selected options are valid for component type"
  refinement_triggers:
    - "Invalid component name"
    - "Missing required configuration"
    - "Template rendering error"
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /build Skill - Interactive Component Builder

> **Version:** 3.0.0 | **Architecture:** EFL Sub-Orchestrator

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Workload Slug 생성 (표준)

```bash
# Source centralized slug generator
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Slug 결정 (독립 스킬 - 항상 새 workload 생성)
# Build는 항상 새 세션으로 시작

CONCEPT="${1:-build}"
TOPIC="build-${CONCEPT}"

# Workload ID 생성
WORKLOAD_ID=$(generate_workload_id "$TOPIC")
SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")

# 디렉토리 구조 초기화
BUILD_DIR=".agent/builds/${SLUG}"
mkdir -p "${BUILD_DIR}"

# Workload 활성화
set_active_workload "$WORKLOAD_ID"

echo "🔨 Build session initialized: $SLUG"
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Purpose

Orchestrates component creation through two modes:

| Mode | Trigger | Flow |
|------|---------|------|
| **Concept** | `/build "concept-name"` | Research → Roadmap → Multi-round Build |
| **Direct** | `/build agent\|skill\|hook` | Q&A Rounds → Generation |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Target Paths

| Type | Path |
|------|------|
| Agent | `.claude/agents/{name}.md` |
| Skill | `.claude/skills/{name}/SKILL.md` |
| Hook (Bash) | `.claude/hooks/{name}.sh` |
| Hook (Python) | `.claude/hooks/{name}.py` |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Error Handling

| Error | Recovery |
|-------|----------|
| Invalid name | Re-prompt with validation hint (`^[a-z][a-z0-9-]{0,63}$`) |
| Draft not found | List available drafts |
| File exists | Ask overwrite confirmation |
| Builder error | Show error, allow retry |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Integration Points

| System | Integration |
|--------|-------------|
| `/build-research` | Concept mode research delegation |
| `builders/*.md` | Component-specific Q&A |
| `parameters/*.md` | Shared parameter selection |
| `templates/*` | Output file templates |
| `settings.json` | Hook auto-registration |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


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
| 3.0.0 | EFL Pattern Integration (P1-P6), disable-model-invocation: true, context: fork |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## EFL Pattern Implementation (V3.0.0)

### P1: Skill as Sub-Orchestrator

This skill operates as a Sub-Orchestrator, delegating work to specialized builders:

```
/build (Main Orchestrator)
    │
    ├─► /build-research (Phase 0 Agent)
    │   └─► claude-code-guide subagent
    │
    ├─► builders/agent-builder.md (Phase 4 Agent)
    ├─► builders/skill-builder.md (Phase 4 Agent)
    └─► builders/hook-builder.md (Phase 4 Agent)
```

### P6: Agent Internal Feedback Loop

All delegated builders include self-validation:

```javascript
// Builder prompt template includes P6
const builderPrompt = `
## Internal Feedback Loop (P6 - REQUIRED)
1. Collect user responses
2. Self-validate collected values:
   - Name follows ^[a-z][a-z0-9-]{0,63}$ pattern
   - Required fields are not empty
   - Selected options are valid
3. If validation fails, retry (max 3 times)
4. Output collected values after validation passes
`
```

### Post-Compact Recovery

Reference: `.claude/skills/shared/post-compact-recovery.md`

```javascript
if (isPostCompactSession()) {
  const slug = await getActiveWorkload()
  const buildState = await Read(`.agent/builds/${slug}/state.json`)

  if (!buildState) {
    return { error: "Build state not found", recovery: "Start new build session" }
  }

  // Resume from last checkpoint
  resumeFromState(buildState)
}
```

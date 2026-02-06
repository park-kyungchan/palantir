---
name: build
description: |
  Interactive Component Builder (Modular Architecture v3.0).
  Two modes: Concept Mode for research-driven builds, Direct Mode for Q&A component creation.
  Delegates to specialized builders and shared parameter modules.
user-invocable: true
model: opus
version: "3.2.0"
argument-hint: '"concept" | agent|skill|hook [--resume id]'
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
      once: true
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/build-finalize.sh"
      timeout: 60000

# =============================================================================
# EFL Pattern Configuration
# =============================================================================

# P1: Skill as Sub-Orchestrator
agent_delegation:
  enabled: true
  mode: "sub_orchestrator"
  default_mode: false  # Only in Concept Mode
  optional_delegation:
    concept_mode:
      enabled: true
      description: "Delegate to /build-research for capability inventory"
      trigger: "concept argument"
    direct_mode:
      enabled: false
      description: "Q&A-based, no delegation needed"

# P2: Parallel Agent Configuration
parallel_agent_config:
  enabled: false
  deviation_reason: |
    Q&A workflow is inherently sequential.
    Each question depends on previous answers.

# P3: Synthesis Configuration
synthesis_config:
  phase_3a_l2_horizontal:
    enabled: true
    validation_criteria:
      - parameter_collection_completeness
      - cross_builder_consistency
      - naming_convention_compliance
  phase_3b_l3_vertical:
    enabled: true
    validation_criteria:
      - generated_file_syntax_valid
      - template_rendering_accuracy
      - hook_registration_correct

# P6: Agent Internal Feedback Loop
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "V1: All required parameters collected"
    - "V2: Generated file syntax valid"
    - "V3: Naming conventions followed"
    - "V4: Cross-references resolved"

# P4: Selective Feedback
selective_feedback:
  enabled: true
  phase: "generation_complete"
  severity_filter: "warning"
  feedback_classification:
    auto_fix: ["V2", "V3"]  # Syntax and naming auto-fix
    user_confirm: ["V1", "V4"]  # Missing params, unresolved refs

# P5: Review Gate
review_gate:
  enabled: true
  phase: "pre_write"
  criteria:
    - "all_parameters_collected"
    - "template_rendered"
    - "validation_passed"
  auto_approve: false
---

# /build Skill - Interactive Component Builder

> **Version:** 3.0.0 | **Model:** opus

---

## Overview

| Aspect | Description |
|--------|-------------|
| **Purpose** | Generate agents, skills, and hooks via Q&A workflow |
| **Modes** | Concept Mode (research-driven) / Direct Mode (Q&A-based) |
| **Output** | L1: Summary (YAML) / L2: Spec (MD) / L3: Generated files |

---

## Cross-Skill Integration

| Skill | Relationship |
|-------|--------------|
| `/build-research` | Concept mode research delegation |
| `builders/*.md` | Component-specific Q&A modules |
| `parameters/*.md` | Shared parameter selection |
| `templates/*` | Output file templates |

---

## Workload Slug Generation

```bash
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/slug-generator.sh"
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

CONCEPT="${1:-build}"
TOPIC="build-${CONCEPT}"
WORKLOAD_ID=$(generate_workload_id "$TOPIC")
SLUG=$(generate_slug_from_workload "$WORKLOAD_ID")
BUILD_DIR=".agent/builds/${SLUG}"
mkdir -p "${BUILD_DIR}"
set_active_workload "$WORKLOAD_ID"
```

---

## Architecture

```
SKILL.md (Orchestrator)
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

```python
args = "$ARGUMENTS".strip()
build_mode = None

# Priority 1: Resume flag
if "--resume" in args:
    resume_id = args.split("--resume")[1].strip().split()[0]
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

## Concept Mode (Phase 0-2)

### Phase 0: Research Delegation

```python
research_result = invoke_skill("build-research", concept)
# Returns: buildId, summary, complexityOptions, l2Path
```

### Phase 1: Roadmap Selection

```python
AskUserQuestion(questions=[{
    "question": "어떤 복잡도 레벨을 선택하시겠습니까?",
    "header": "Complexity",
    "options": [
      {"label": "Level 0 - Basic", "description": "Essential features only"},
      {"label": "Level 50 - Recommended", "description": "Production-ready"},
      {"label": "Level 100 - Full", "description": "All features"}
    ],
    "multiSelect": False
}])
```

### Phase 2: Build Execution

Multi-round capability selection by category:
- Round 1: Skills selection
- Round 2: Agents selection
- Round 3: Hooks selection

---

## Direct Mode (Phase 3-6)

### Phase 3: Type Selection

```python
AskUserQuestion(questions=[{
    "question": "어떤 컴포넌트를 생성하시겠습니까?",
    "header": "Type",
    "options": [
      {"label": "Agent (Recommended)", "description": "Specialized subagent"},
      {"label": "Skill", "description": "Reusable /command workflow"},
      {"label": "Hook", "description": "Event-driven script"}
    ],
    "multiSelect": False
}])
```

### Phase 4: Builder Delegation

| Builder | Rounds |
|---------|--------|
| `agent-builder.md` | 1-3: Identity, 4-6: Tools, 7-9: Context, 10-12: Model, 13-15: Output |
| `skill-builder.md` | 1-3: Identity, 4-6: Context, 7-9: Tools, 10-12: Advanced |
| `hook-builder.md` | 1-3: Identity, 4-6: Trigger, 7-10: I/O, 11-14: Advanced |

### Phase 5: Draft Generation

```python
draft_path = f".agent/plans/create_drafts/{component_type}_{name}.md"
template_path = f"templates/{component_type}-template.yaml"
content = render_template(template_path, collected)
save_draft(draft_path, {"type": component_type, "name": name, "preview": content})
```

### Phase 6: Confirmation & Generation

```python
# On "Yes, generate"
target_path = get_target_path(component_type, name)
write_file(target_path, content)
if component_type == "hook":
    register_hook_in_settings(hook_config)
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
  "collected": { "name": "my-agent", "model": "sonnet" },
  "timestamp": "2026-01-24T12:00:00Z"
}
```

### Resume Flow

```python
if build_mode == "resume":
    state = load_state(f".agent/builds/{resume_id}/state.json")
    continue_from(state["currentPhase"], state["currentRound"], state)
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

## Version History

| Version | Change |
|---------|--------|
| 2.1.0 | V2.1.19 Spec compatibility |
| 2.2.0 | Concept Mode + Parameter Module Architecture |
| 3.0.0 | Frontmatter normalization, MCP tool inclusion, duplicate removal |

**End of Skill Definition**

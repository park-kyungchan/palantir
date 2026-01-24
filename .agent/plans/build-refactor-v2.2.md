# /build Skill Refactoring Plan v2.2

> **Status**: Draft - Pending User Approval
> **Created**: 2026-01-24
> **Author**: Claude Code Agent
> **Scope**: Complete restructuring with shared parameter modules

---

## 1. Executive Summary

### Problem Statement
- Current `/build` SKILL.md: **1,676 lines** (3.35x over 500-line guideline)
- Cyclomatic Complexity: **35+** (High - maintenance difficult)
- Parameter duplication across Agent/Skill/Hook builders
- **130+ parameters** need systematic coverage (V1.x ~ V2.1.19)

### Solution
**Hybrid Modular Architecture** with:
1. Main orchestrator (routing + state)
2. Component-specific builders (Agent/Skill/Hook)
3. **Shared parameter modules** (DRY principle)
4. Template system

---

## 2. Target Architecture

```
.claude/skills/build/
├── SKILL.md                     # Orchestrator (~250 lines)
│                                # Model: opus
│                                # Responsibility: Mode detection + delegation
│
├── builders/                    # Component-specific logic only
│   ├── agent-builder.md         # Agent Q&A (~300 lines)
│   │                            # Model: sonnet | context: fork
│   ├── skill-builder.md         # Skill Q&A (~250 lines)
│   │                            # Model: sonnet | context: fork
│   └── hook-builder.md          # Hook Q&A (~300 lines)
│                                # Model: sonnet | context: fork
│
├── parameters/                  # 🆕 Shared parameter modules (DRY)
│   ├── model-selection.md       # model: haiku|sonnet|opus (~50 lines)
│   ├── context-mode.md          # context: standard|fork (~60 lines)
│   ├── tool-config.md           # allowed/disallowed-tools (~80 lines)
│   ├── hook-config.md           # type, matcher, once, timeout (~100 lines)
│   ├── permission-mode.md       # permissionMode options (~50 lines)
│   └── task-params.md           # run_in_background, resume, max_turns (~70 lines)
│
├── templates/
│   ├── agent-template.yaml      # Agent output schema
│   ├── skill-template.yaml      # Skill output schema
│   ├── hook-bash-template.sh    # Bash hook template
│   └── hook-python-template.py  # Python hook template
│
└── helpers/
    ├── validation.sh            # Input validation utilities
    └── state-manager.sh         # Draft persistence
```

---

## 3. Parameter Module Specification

### 3.1 Parameter to Module Mapping

| Module | Used By | Parameters Covered |
|--------|---------|-------------------|
| `model-selection.md` | Agent, Skill, Task | `model`, `fallback-model` |
| `context-mode.md` | Skill, Agent | `context`, `agent` (when fork) |
| `tool-config.md` | Agent, Skill | `allowed-tools`, `disallowed-tools`, `tools` |
| `hook-config.md` | Skill, Agent, Settings | `type`, `matcher`, `once`, `timeout`, `command`, `prompt` |
| `permission-mode.md` | Agent, CLI | `permissionMode`, `--permission-mode` |
| `task-params.md` | Task delegation | `run_in_background`, `resume`, `max_turns`, `allowed_tools` |

### 3.2 Detailed Parameter Coverage

#### model-selection.md
```yaml
parameters:
  - name: model
    type: enum
    values: [haiku, sonnet, opus, inherit]
    default: inherit
    version: V2.0+

  - name: fallback-model
    type: enum
    version: V2.1+
    context: Print mode only
```

#### context-mode.md
```yaml
parameters:
  - name: context
    type: enum
    values: [standard, fork]
    default: standard
    version: V2.0+

  - name: agent
    type: string
    values: [Explore, Plan, general-purpose, custom]
    dependency: context=fork
    version: V2.0+
```

#### tool-config.md
```yaml
parameters:
  - name: allowed-tools
    type: array
    values: [Read, Write, Edit, Bash, Grep, Glob, Task, WebFetch, WebSearch, AskUserQuestion, NotebookEdit, TaskCreate, TaskUpdate, TaskList, TaskGet, ...]
    version: V2.0+

  - name: disallowed-tools
    type: array
    conflict: allowed-tools
    version: V2.0+

  - name: tools (Agent)
    type: array
    version: V2.0+
```

#### hook-config.md
```yaml
parameters:
  - name: type
    type: enum
    values: [command, prompt]
    version: V2.1+

  - name: matcher
    type: string (regex)
    patterns: [exact, OR, wildcard, domain, glob]
    version: V2.1+

  - name: once
    type: boolean
    default: false
    version: V2.1.16+

  - name: timeout
    type: number (ms)
    default: 60000
    version: V2.1+

  - name: command
    type: string
    dependency: type=command

  - name: prompt
    type: string
    dependency: type=prompt
    supported_events: [Stop, SubagentStop]
```

#### permission-mode.md
```yaml
parameters:
  - name: permissionMode
    type: enum
    values: [default, acceptEdits, dontAsk, bypassPermissions, plan]
    default: default
    version: V2.0+
```

#### task-params.md
```yaml
parameters:
  - name: run_in_background
    type: boolean
    default: false
    version: V2.1.16+

  - name: resume
    type: string (agent ID)
    version: V2.1+

  - name: max_turns
    type: number
    version: V2.1+

  - name: allowed_tools
    type: array
    version: V2.1+
```

---

## 4. Execution Phases

### Phase 1: Directory Structure (1 hour)
- [ ] Create `builders/` directory
- [ ] Create `parameters/` directory
- [ ] Create `templates/` directory
- [ ] Create `helpers/` directory

### Phase 2: Parameter Modules (3-4 hours)
- [ ] `model-selection.md` - Model Q&A flow
- [ ] `context-mode.md` - Context + Agent Q&A flow
- [ ] `tool-config.md` - Tool allowlist/denylist Q&A
- [ ] `hook-config.md` - Hook type, matcher, once, timeout Q&A
- [ ] `permission-mode.md` - Permission mode Q&A
- [ ] `task-params.md` - Task delegation params Q&A

### Phase 3: Component Builders (4-5 hours)
- [ ] `agent-builder.md` - Agent-specific rounds (name, description, skills injection)
- [ ] `skill-builder.md` - Skill-specific rounds (argument-hint, user-invocable)
- [ ] `hook-builder.md` - Hook-specific rounds (event type, input/output schema)

### Phase 4: Main Orchestrator (2-3 hours)
- [ ] Refactor SKILL.md to ~250 lines
- [ ] Implement parameter module delegation
- [ ] Implement builder delegation
- [ ] Implement resume/state management

### Phase 5: Templates & Helpers (2 hours)
- [ ] Extract templates from current SKILL.md
- [ ] Create validation helpers
- [ ] Create state management helpers

### Phase 6: Integration Testing (2-3 hours)
- [ ] Test each parameter module independently
- [ ] Test each builder with parameter modules
- [ ] Test full flows (Concept → Build → Generate)
- [ ] Test resume functionality

**Total Estimated: 14-18 hours**

---

## 5. Parameter Module Design Pattern

### Structure
```markdown
---
name: {parameter-module-name}
description: Shared parameter selection for {purpose}
context: fork
model: haiku  # Lightweight for simple Q&A
---

# {Parameter Module Name}

## Purpose
{Why this module exists and when it's called}

## Round 1: {First Parameter}
AskUserQuestion(...)

## Round 2: {Second Parameter}
AskUserQuestion(...)

## Output Format
{What this module returns to the calling builder}
```

### Caller Pattern
```markdown
# In skill-builder.md

## Round 6: Model Selection
<!-- Delegate to shared module -->
The model selection is handled by the shared parameter module.
Call: parameters/model-selection.md
Pass: component_type="skill"
Receive: { model: "sonnet" }

## Round 7: Context Mode
<!-- Delegate to shared module -->
Call: parameters/context-mode.md
Pass: component_type="skill"
Receive: { context: "fork", agent: "Explore" }
```

---

## 6. Verification Checklist

### User Experience
- [ ] `/build agent` produces same output
- [ ] `/build skill` produces same output
- [ ] `/build hook` produces same output
- [ ] `/build "concept"` triggers research flow
- [ ] `/build --resume id` restores state correctly
- [ ] All 130+ parameters are selectable

### Code Quality
- [ ] Main SKILL.md < 300 lines
- [ ] Each builder < 400 lines
- [ ] Each parameter module < 100 lines
- [ ] No parameter duplication across files
- [ ] Clear module interfaces

### Parameter Coverage (V1.x ~ V2.1.19)
- [ ] All Skill frontmatter fields covered
- [ ] All Agent frontmatter fields covered
- [ ] All Hook configuration fields covered
- [ ] All Task tool parameters covered
- [ ] V2.1.16+ features: `once`, `run_in_background`
- [ ] V2.1.19 features: `$0`, `$1` indexed arguments

---

## 7. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Module interface mismatch | HIGH | Define strict input/output contracts |
| State loss between modules | MEDIUM | Centralized state in SKILL.md |
| Parameter version conflicts | MEDIUM | Version annotations in each module |
| Testing complexity | MEDIUM | Unit test each module independently |

### Rollback Plan
1. Keep backup: `SKILL.md.v2.1.0.bak`
2. Git branch: `feature/build-refactor-v2.2`
3. Atomic commits per phase
4. Revert to working state at any phase boundary

---

## 8. Dependencies

### Related Skills
- `/build-research` - Existing, no changes needed
- `/clarify` - Can feed into `/build`, parallel development OK
- `/orchestrate` - Can decompose complex builds

### System Requirements
- Claude Code V2.1.16+ (for `once` parameter)
- yq (for YAML processing in helpers)

---

## 9. Approval Request

### Summary of Changes
1. **Split 1,676-line monolith** → Modular architecture (~1,200 lines total, distributed)
2. **Add parameters/ directory** → DRY principle, single source of truth
3. **130+ parameters covered** → V1.x through V2.1.19 complete

### Benefits
- Maintainability: Update parameters in one place
- Testability: Unit test each module
- Extensibility: Add new parameters/builders easily
- Model optimization: haiku for params, sonnet for builders, opus for orchestration

### Request
**Please approve this plan to proceed with implementation.**

---

> **Next Steps After Approval:**
> 1. Execute Phase 1 (Directory Structure)
> 2. Execute Phase 2 (Parameter Modules) - Can be parallelized
> 3. Execute remaining phases sequentially

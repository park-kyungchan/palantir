# Subagent Access Control Reference

> **Version:** 1.0 | **For:** LLM-Agnostic Governance Layer (Phase 3)
> **Path:** `.claude/references/subagent-access.md`

---

## 1. Overview

This document defines the access control matrix for subagents operating under ODA governance.
It ensures that all subagents have appropriate access to Skills, Hooks, and Native Agents.

### Design Principles

```yaml
principles:
  LEAST_PRIVILEGE: Subagents get minimum required access
  EXPLICIT_GRANT: Access must be declared in frontmatter
  ODA_AWARE: All subagents understand governance context
  AUDIT_TRAIL: All access is logged
```

---

## 2. Subagent Types and Base Capabilities

### 2.1 Native Subagent Types

| Type | Purpose | Base Tools | Context Mode |
|------|---------|-----------|--------------|
| **Explore** | Codebase analysis, pattern discovery | Read, Grep, Glob | fork |
| **Plan** | Structured planning, phased breakdown | Read, Grep, Glob, TodoWrite | fork |
| **general-purpose** | Complex multi-step execution | All tools | standard or fork |

### 2.2 Specialized Agent Types

Defined in `.claude/agents/*.md` with explicit tool declarations.

| Agent | Model | Tools | ODA Role |
|-------|-------|-------|----------|
| schema-validator | haiku | Read, Grep, Glob | Schema Gate |
| evidence-collector | haiku | Read, Grep, Glob, Bash | Anti-Hallucination |
| action-executor | sonnet | Read, Bash, Grep | Mutation Control |
| audit-logger | haiku | Read, Bash, Write | Audit Trail |
| prompt-assistant | sonnet | Read, Grep, Glob, AskUserQuestion, Task, WebSearch, TodoWrite | Chain Controller |
| onboarding-guide | haiku | Read | User Support |

---

## 3. Tool Access Matrix

### 3.1 Core Tools

| Tool | Explore | Plan | general-purpose | schema-validator | evidence-collector | action-executor | audit-logger | prompt-assistant |
|------|---------|------|-----------------|------------------|-------------------|-----------------|--------------|------------------|
| Read | Yes | Yes | Yes | Yes | Yes | Yes | Yes | Yes |
| Grep | Yes | Yes | Yes | Yes | Yes | Yes | - | Yes |
| Glob | Yes | Yes | Yes | Yes | Yes | - | - | Yes |
| Edit | - | - | Yes | - | - | - | - | - |
| Write | - | - | Yes | - | - | - | Yes | - |
| Bash | - | - | Yes | - | Yes | Yes | Yes | - |

### 3.2 Extended Tools

| Tool | Explore | Plan | general-purpose | prompt-assistant |
|------|---------|------|-----------------|------------------|
| WebSearch | Yes | - | Yes | Yes |
| WebFetch | - | - | Yes | - |
| TodoWrite | - | Yes | Yes | Yes |
| Task | - | Yes | Yes | Yes |
| AskUserQuestion | - | - | Yes | Yes |
| Skill | - | - | Yes | - |

### 3.3 MCP Tools

All MCP tools (GitHub, Context7, ODA-Ontology, etc.) are available to:
- general-purpose subagent (full access)
- Specialized agents with explicit `mcp-access: true` in frontmatter

---

## 4. Skill Access Matrix

### 4.1 ODA Skills

| Skill | Explore | Plan | general-purpose | Required Context |
|-------|---------|------|-----------------|------------------|
| oda-audit | Invoke via delegation | - | Direct | target_path |
| oda-plan | - | Direct | Direct | requirements |
| oda-governance | - | Invoke via delegation | Direct | target_path |
| capability-advisor | Direct | - | Direct | - |
| help-korean | - | - | Direct | - |

### 4.2 Skill Invocation Patterns

**Direct Invocation:**
```python
# Subagent has direct access
Skill(skill="oda-plan", args="<requirements>")
```

**Delegation Invocation:**
```python
# Subagent requests through Task
Task(
    description="Run governance check",
    prompt="Execute /governance on target path",
    subagent_type="general-purpose"
)
```

---

## 5. Hook Access Matrix

### 5.1 Hook Types

| Hook | Trigger | Available To |
|------|---------|--------------|
| PreToolUse | Before tool execution | All subagents (automatic) |
| PostToolUse | After tool execution | All subagents (automatic) |
| SessionStart | Session begins | Main orchestrator only |
| SessionEnd | Session ends | Main orchestrator only |

### 5.2 Hook Read Access

Subagents can READ hook configurations for context:

```python
# Check what hooks are configured
Read(".claude/hooks/PreToolUse/")
Read(".claude/hooks/PostToolUse/")
```

### 5.3 Hook Modification Access

Only the main orchestrator (via Proposal workflow) can modify hooks.

---

## 6. ODA Component Access

### 6.1 Agent Invocation Matrix

| Invoking Agent | Can Invoke | Method |
|----------------|-----------|--------|
| prompt-assistant | All agents | Task tool delegation |
| schema-validator | evidence-collector | Reference in output |
| evidence-collector | audit-logger | Reference in output |
| action-executor | schema-validator, audit-logger | Chained execution |
| Explore subagent | evidence-collector | Auto-integration |
| Plan subagent | schema-validator | Auto-integration |

### 6.2 ODA Context Propagation

Every subagent receives ODA context automatically:

```yaml
oda_context:
  workspace_root: /home/palantir/park-kyungchan/palantir
  governance_mode: block  # Inherited from main
  evidence_required: true  # Always for Stage A/B/C
  audit_enabled: true  # Always

  # Subagent-specific
  parent_stage: A | B | C  # If within 3-Stage Protocol
  session_id: <inherited>
  actor_id: <subagent_type>_agent
```

---

## 7. Access Declaration Syntax

### 7.1 Agent Frontmatter

```yaml
---
name: my-agent
description: Agent description

# Tool access (explicit declaration)
tools: Read, Grep, Glob, Bash

# Skill access (explicit declaration)
skills:
  - oda-audit
  - oda-governance

# ODA context (explicit declaration)
oda_context:
  role: schema_validation
  stage_access: [A, B]
  evidence_required: true
  audit_integration: true

# Native capabilities
context: fork  # or standard
model: haiku  # or sonnet

# Optional: MCP access
mcp_access: false  # Default, set true for MCP tools
---
```

### 7.2 Skill Frontmatter

```yaml
---
name: my-skill
description: Skill description

# Tool access
allowed-tools: Read, Grep, Glob, TodoWrite

# Agent delegation
agent: Explore  # or Plan, general-purpose

# ODA integration
oda_context:
  protocol_stage: A  # Primary stage
  evidence_collection: true
  governance_check: pre_execution

# Execution mode
context: fork
user-invocable: true  # or false for internal skills
---
```

---

## 8. Access Inheritance Rules

### 8.1 Inheritance Chain

```
Main Orchestrator (CLAUDE.md)
    │
    ├── Subagent (Task tool)
    │     └── Inherits: governance_mode, session_id, audit_settings
    │
    └── Skill (Skill tool)
          └── Inherits: workspace_root, evidence_context
```

### 8.2 Override Rules

| Setting | Can Override? | Default Inheritance |
|---------|--------------|---------------------|
| governance_mode | No (security) | block |
| evidence_required | No (anti-hallucination) | true |
| audit_enabled | No (compliance) | true |
| tools | Yes (restriction only) | Per frontmatter |
| context | Yes | fork for skills |

---

## 9. Security Boundaries

### 9.1 Blocked Access (All Subagents)

```yaml
blocked_patterns:
  - rm -rf
  - sudo rm
  - chmod 777
  - DROP TABLE
  - eval(
  - exec(

blocked_actions:
  - Direct database modification (bypassing Actions)
  - Schema changes without Proposal
  - Hook modification
  - Config file deletion
```

### 9.2 Proposal-Required Actions

These require explicit Proposal workflow regardless of subagent type:

| Action | Proposal Type | Approver |
|--------|--------------|----------|
| Schema modification | schema.modify | Human or Senior Agent |
| Database migration | database.migrate | Human |
| Security changes | security.change | Human |
| Hook modification | config.hook_update | Human |

---

## 10. Debugging Access Issues

### 10.1 Common Access Errors

| Error | Cause | Resolution |
|-------|-------|------------|
| `ToolNotAvailable` | Tool not in frontmatter | Add to `tools:` list |
| `SkillAccessDenied` | Skill not accessible | Use delegation pattern |
| `GovernanceBlock` | Blocked pattern detected | Review and modify operation |
| `EvidenceMissing` | No files_viewed | Read files before proceeding |

### 10.2 Access Log Location

```
.agent/logs/access_control.log
.agent/tmp/audit_YYYYMMDD.jsonl
```

### 10.3 Verification Commands

```python
# Check subagent access
Read(".claude/agents/<agent-name>.md")

# Check skill access
Read(".claude/skills/<skill-name>.md")

# Check hook configuration
Read(".claude/hooks/")
```

---

## 11. Quick Reference Card

### For Subagent Authors

1. Declare tools explicitly in frontmatter
2. Use `context: fork` for isolated execution
3. Reference evidence-collector for file tracking
4. Follow 3-Stage Protocol for complex operations

### For Skill Authors

1. Set `allowed-tools` explicitly
2. Choose appropriate `agent:` type
3. Define `oda_context` for governance integration
4. Set `user-invocable` appropriately

### For Main Orchestrator

1. Delegate to appropriate subagent type
2. Pass ODA context in delegation prompt
3. Collect and synthesize subagent results
4. Log all delegations through audit-logger

---

> **See Also:**
> - `.claude/references/native-capabilities.md` - Full capability reference
> - `.claude/references/3-stage-protocol.md` - Protocol execution guide
> - `.claude/CLAUDE.md` - Main orchestrator documentation

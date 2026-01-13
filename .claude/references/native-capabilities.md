# Native Capabilities Reference

> **Version:** 2.0 | **For:** Subagent Execution Context
> **Path:** `.claude/references/native-capabilities.md`
> **LLM-Agnostic:** Yes (Phase 3 Governance Layer)

---

## 0. ODA Governance Context

Every subagent operates under ODA governance. Key context variables:

```yaml
oda_context:
  workspace_root: /home/palantir/park-kyungchan/palantir
  database_path: .agent/tmp/ontology.db
  memory_path: .agent/memory/semantic/
  schemas_path: .agent/schemas/
  governance_mode: block  # off | warn | block

core_principles:
  SCHEMA_FIRST: ObjectTypes are canonical; mutations follow schema
  ACTION_ONLY: State changes ONLY through registered Actions
  AUDIT_FIRST: All operations logged with evidence
  ZERO_TRUST: Verify files/imports before ANY mutation
```

### Subagent ODA Integration Points

| Integration Point | Description | Required |
|------------------|-------------|----------|
| Evidence Collection | Track files_viewed via evidence-collector | Yes |
| Schema Validation | Validate against ObjectTypes via schema-validator | For mutations |
| Action Execution | Use registered Actions via action-executor | For state changes |
| Audit Logging | Log operations via audit-logger | Yes |

---

## 1. Context Management

### 1.1 Context Types

| Type | Frontmatter | Behavior | Use Case |
|------|-------------|----------|----------|
| **Standard** | (default) | Shares main conversation context | Simple tasks, quick queries |
| **Fork** | `context: fork` | Isolated execution environment | Deep analysis, planning, audit |

### 1.2 Forked Context Benefits
```yaml
# Skill/Agent frontmatter
context: fork
```

- **Isolation:** Analysis doesn't pollute main conversation
- **Memory Efficiency:** Context discarded after completion
- **Deep Exploration:** Read many files without overflow
- **Clean Return:** Only structured results return to caller

### 1.3 When to Use Fork
| Scenario | Context |
|----------|---------|
| 3-Stage Protocol execution | `fork` |
| Codebase exploration (50+ files) | `fork` |
| Planning with many alternatives | `fork` |
| Quick file read | standard |
| Simple code edit | standard |

---

## 2. Subagent Types

### 2.1 Available Subagents

| Subagent | Specialization | ODA Stage | Model Hint |
|----------|---------------|-----------|------------|
| **Explore** | Codebase analysis, file discovery | Stage A: SCAN | Fast, thorough |
| **Plan** | Structured planning, breakdown | Stage B: TRACE | Methodical |
| **general-purpose** | Complex multi-step operations | Stage C: VERIFY | Balanced |

### 2.2 Invocation Patterns

**Via Task Tool:**
```python
Task(
    description="Analyze authentication module",
    prompt="Explore all auth-related files and document patterns",
    subagent_type="Explore"  # or "Plan", "general-purpose"
)
```

**Via Skill Frontmatter:**
```yaml
---
name: my-skill
agent: Explore  # Auto-delegates to Explore subagent
context: fork
---
```

### 2.3 Subagent Selection Guide

| Task Type | Subagent | Reason |
|-----------|----------|--------|
| "Find all usages of X" | Explore | Pattern discovery |
| "How does Y work?" | Explore | Understanding flow |
| "Create implementation plan" | Plan | Structured breakdown |
| "Design solution for Z" | Plan | Multi-phase planning |
| "Implement feature A" | general-purpose | Execution focus |
| "Fix and test bug B" | general-purpose | End-to-end task |

---

## 3. Tool Capabilities

### 3.1 Core Tools

| Tool | Purpose | Evidence Impact |
|------|---------|-----------------|
| `Read` | File content access | Adds to `files_viewed` |
| `Grep` | Pattern search | Adds matched files/lines |
| `Glob` | File discovery | Documents file patterns |
| `Edit` | File modification | Requires prior Read |
| `Write` | File creation | Use sparingly |
| `Bash` | Command execution | For git, npm, etc. |

### 3.2 Extended Tools

| Tool | Purpose | When to Use |
|------|---------|-------------|
| `WebSearch` | Current information | Latest docs, techniques |
| `WebFetch` | URL content retrieval | Specific page analysis |
| `TodoWrite` | Task tracking | Multi-step workflows |
| `Task` | Subagent delegation | Complex subtasks |
| `AskUserQuestion` | User clarification | Ambiguous requests |

### 3.3 TodoWrite Integration

**Status Mapping to ODA:**
```yaml
pending      → PENDING
in_progress  → IN_PROGRESS
completed    → COMPLETED
```

**Usage Pattern:**
```python
TodoWrite(todos=[
    {"content": "Stage A: SCAN", "status": "completed", "activeForm": "Scanning codebase"},
    {"content": "Stage B: TRACE", "status": "in_progress", "activeForm": "Tracing dependencies"},
    {"content": "Stage C: VERIFY", "status": "pending", "activeForm": "Verifying quality"}
])
```

**Rules:**
- Only ONE task `in_progress` at a time
- Mark complete IMMEDIATELY after finishing
- Update status in real-time

---

## 4. Evidence Collection

### 4.1 Automatic Tracking

| Tool Call | Evidence Generated |
|-----------|-------------------|
| `Read(file.py)` | `files_viewed: [file.py]` |
| `Grep(pattern)` | `files_matched: [...], lines: [...]` |
| `Glob(*.py)` | `files_discovered: [...]` |

### 4.2 Manual Documentation

When making claims, reference evidence:
```markdown
## Evidence
- files_viewed: scripts/ontology/registry.py (lines 40-80)
- code_snippet: `class OntologyRegistry:` at line 42
- claim_supported: "Registry uses singleton pattern"
```

### 4.3 Minimum Evidence by Stage

| Stage | Minimum Requirements |
|-------|---------------------|
| A: SCAN | 3+ files viewed |
| B: TRACE | 5+ files, line references |
| C: VERIFY | All previous + code snippets |

### 4.4 Anti-Hallucination Rule

```python
# CRITICAL: Every stage must have evidence
if stage.passed and not evidence.get("files_viewed"):
    raise AntiHallucinationError("Stage passed without file evidence")
```

---

## 5. Agent Chaining Patterns

### 5.1 Sequential Chain

```
User Request
    │
    ▼
[Explore Agent] ─── Stage A: Understand codebase
    │
    ▼
[Plan Agent] ────── Stage B: Design solution
    │
    ▼
[general-purpose] ─ Stage C: Execute & verify
    │
    ▼
Result to User
```

**Implementation:**
```python
# Step 1: Explore
explore_result = Task(
    description="Analyze current state",
    subagent_type="Explore"
)

# Step 2: Plan (depends on Step 1)
plan_result = Task(
    description=f"Design solution based on: {explore_result}",
    subagent_type="Plan"
)

# Step 3: Execute (depends on Step 2)
execute_result = Task(
    description=f"Implement: {plan_result}",
    subagent_type="general-purpose"
)
```

### 5.2 Parallel Chain

```
User Request
    │
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
[WebSearch]   [Read Docs]   [Grep Code]
    │              │              │
    └──────────────┴──────────────┘
                   │
                   ▼
            [Synthesize]
                   │
                   ▼
            Result to User
```

**Use Case:** Information gathering from multiple sources

### 5.3 Controller Pattern

**prompt-assistant** acts as Agent Chain Controller:
```
Analyze → Delegate → Synthesize → Respond

1. ANALYZE: Parse user intent
2. DELEGATE: Call appropriate subagents
3. SYNTHESIZE: Merge results (local > external)
4. RESPOND: Present findings
```

---

## 6. Hooks Integration

### 6.1 Hook Types

| Hook | Trigger | Purpose |
|------|---------|---------|
| `PreToolUse` | Before tool execution | Validation, blocking |
| `PostToolUse` | After tool execution | Logging, tracking |

### 6.2 Evidence Tracking Hook

```json
{
  "PostToolUse": [
    {
      "matcher": "Read|Grep|Glob",
      "hooks": [
        {
          "type": "command",
          "command": "python scripts/claude/evidence_tracker.py"
        }
      ]
    }
  ]
}
```

### 6.3 Blocked Patterns Hook

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "block",
          "pattern": "rm -rf|sudo rm|chmod 777|DROP TABLE",
          "message": "Blocked: Dangerous operation"
        }
      ]
    }
  ]
}
```

---

## 7. ODA Schema Quick Reference

### 7.1 ObjectTypes Summary

| ObjectType | Key Properties | Links |
|------------|---------------|-------|
| **Agent** | name, role, capabilities | assigned_tasks (1:N) |
| **Task** | title, priority, task_status | assigned_to, depends_on |
| **Proposal** | action_type, payload, status | - |

### 7.2 Task Status Flow

```
PENDING → IN_PROGRESS → COMPLETED
              │
              └──→ BLOCKED
              └──→ CANCELLED
```

### 7.3 Proposal Status Flow

```
DRAFT → PENDING → APPROVED → EXECUTED
            │
            └──→ REJECTED
            └──→ CANCELLED
```

### 7.4 Priority Levels

```python
class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"      # default
    HIGH = "high"
    CRITICAL = "critical"
```

---

## 8. Integration Points

### 8.1 With Existing Agents

| Agent | Integration | Reference | ODA Role |
|-------|-------------|-----------|----------|
| schema-validator | Validates ObjectType compliance | `.claude/agents/schema-validator.md` | Schema Gate |
| evidence-collector | Tracks files_viewed, lines | `.claude/agents/evidence-collector.md` | Anti-Hallucination |
| audit-logger | Records all operations | `.claude/agents/audit-logger.md` | Audit Trail |
| action-executor | Executes validated actions | `.claude/agents/action-executor.md` | Mutation Control |
| prompt-assistant | Clarifies requests, chains agents | `.claude/agents/prompt-assistant.md` | Chain Controller |
| onboarding-guide | User guidance (Korean) | `.claude/agents/onboarding-guide.md` | User Support |

### 8.2 With Existing Skills

| Skill | Usage | Reference | ODA Stage |
|-------|-------|-----------|-----------|
| oda-audit | `/audit <path>` | `.claude/skills/oda-audit.md` | A/B/C Full |
| oda-plan | `/plan <requirements>` | `.claude/skills/oda-plan.md` | B Focus |
| oda-governance | `/governance` | `.claude/skills/oda-governance.md` | Pre-execution |
| capability-advisor | Auto-recommend | `.claude/skills/capability-advisor.md` | Discovery |
| help-korean | `/help` in Korean | `.claude/skills/help-korean.md` | User Support |

### 8.3 Canonical Paths

```yaml
workspace_root: /home/palantir/park-kyungchan/palantir
database_path: .agent/tmp/ontology.db
memory_path: .agent/memory/semantic/
schemas_path: .agent/schemas/
agents_path: .claude/agents/
skills_path: .claude/skills/
references_path: .claude/references/
hooks_path: .claude/hooks/
```

### 8.4 Cross-Reference Guide

When a subagent needs to invoke another component:

```markdown
## Invoking an Agent from Skill
# In your skill execution, reference the agent:
Read(".claude/agents/schema-validator.md")
# Then follow the agent's protocol

## Invoking a Skill from Agent
# Use the Skill tool with skill name:
Skill(skill="oda-audit", args="<target_path>")

## Accessing Hooks
# Hooks are auto-triggered, but can be referenced:
Read(".claude/hooks/<hook-type>/")
```

---

## 9. Quick Decision Matrix

### When to Fork Context
- [ ] Reading 10+ files
- [ ] Running 3-Stage Protocol
- [ ] Deep codebase exploration
- [ ] Complex planning session

### When to Delegate to Subagent
- [ ] Task requires specialized focus
- [ ] Parallel information gathering needed
- [ ] Complex multi-step operation
- [ ] Want isolated execution

### When to Use TodoWrite
- [ ] 3+ step task
- [ ] User-visible progress tracking
- [ ] ODA Stage progression
- [ ] Multi-phase implementation

---

## 10. Example: Complete 3-Stage Execution

```python
# Stage A: SCAN with Explore
TodoWrite([{"content": "Stage A: SCAN", "status": "in_progress", "activeForm": "Scanning"}])

explore_result = Task(
    description="Scan target codebase for patterns",
    subagent_type="Explore",
    prompt="Read all relevant files, document structure"
)

TodoWrite([{"content": "Stage A: SCAN", "status": "completed", "activeForm": "Scanning"}])

# Stage B: TRACE with Plan
TodoWrite([{"content": "Stage B: TRACE", "status": "in_progress", "activeForm": "Tracing"}])

plan_result = Task(
    description="Design implementation based on scan",
    subagent_type="Plan",
    prompt=f"Create phased plan from: {explore_result}"
)

TodoWrite([{"content": "Stage B: TRACE", "status": "completed", "activeForm": "Tracing"}])

# Stage C: VERIFY with general-purpose
TodoWrite([{"content": "Stage C: VERIFY", "status": "in_progress", "activeForm": "Verifying"}])

# Execute and validate
result = execute_plan(plan_result)
run_quality_checks()

TodoWrite([{"content": "Stage C: VERIFY", "status": "completed", "activeForm": "Verifying"}])
```

---

## 11. Subagent Access Matrix (Quick Reference)

For detailed access control, see `.claude/references/subagent-access.md`.

### Tool Access by Subagent Type

| Subagent | Core Tools | Extended Tools | ODA Components |
|----------|-----------|----------------|----------------|
| Explore | Read, Grep, Glob | WebSearch | evidence-collector |
| Plan | Read, Grep, Glob, TodoWrite | Task | schema-validator |
| general-purpose | All Core | All Extended | All ODA |
| Specialized Agents | Per frontmatter `tools:` | Per frontmatter | Per `oda_context:` |

### Skill Access by Subagent Type

| Subagent | Direct Skills | Via Delegation | Hooks |
|----------|--------------|----------------|-------|
| Explore | capability-advisor | oda-audit | PostToolUse |
| Plan | oda-plan | oda-governance | PreToolUse |
| general-purpose | All | All | All |

---

> **Note:** This reference is optimized for subagent context.
> For full ODA documentation, see `/home/palantir/.claude/CLAUDE.md`
> For access control details, see `.claude/references/subagent-access.md`

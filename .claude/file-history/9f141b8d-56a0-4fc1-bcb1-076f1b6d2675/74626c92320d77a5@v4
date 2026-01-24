# /build Command - Unified System Component Builder

> **Version:** 5.0.0 | **Type:** Cascading Interactive Builder + Concept Mode
> **Scope:** Concept Research, Agent, Skill, Hook, Runtime-Chaining
> **Claude Code Compatibility:** V2.1.15+

---

## Purpose

Create and orchestrate system components through **5 distinct build modes**:

```
/build "concept"  →  Research → Roadmap → Multi-select Build (NEW)
/build agent      →  Agent + Skills + Hooks (Cascade)
/build skill      →  Skill + Hooks (Cascade)
/build hook       →  Hook (Standalone)
/build chain      →  Runtime Orchestration Pattern
```

## Usage

```bash
# Concept Mode (NEW) - Three-Phase Pattern
/build "Progressive-Disclosure"    # Research capabilities → Roadmap → Build
/build "token-budgeting"           # Research → Select complexity → Generate
/build --resume pd-a1b2            # Resume from .agent/builds/{id}/

# Direct Mode - Traditional Q&A
/build                    # Interactive type selection
/build agent              # Full cascade: Agent → Skills → Hooks
/build skill              # Partial cascade: Skill → Hooks
/build hook               # Single component: Hook only
/build chain              # Runtime chaining pattern definition
/build --standalone       # Disable cascade
```

---

# SECTION 0: CONCEPT MODE (NEW)

## Concept Mode Overview

When you provide a **quoted concept name**, the build command uses a **three-phase approach**:

```
┌───────────────────────────────────────────────────────────┐
│ /build "Progressive-Disclosure"                           │
├───────────────────────────────────────────────────────────┤
│ PHASE 0: RESEARCH                                         │
│ ├─ Delegate to claude-code-guide agent                    │
│ ├─ Discover all relevant capabilities                     │
│ └─ Save to .agent/builds/{id}/research.json               │
├───────────────────────────────────────────────────────────┤
│ PHASE 1: ROADMAP                                          │
│ ├─ Present L1 summary (≤500 tokens)                       │
│ ├─ Show complexity levels (0/50/100)                      │
│ └─ User selects target level                              │
├───────────────────────────────────────────────────────────┤
│ PHASE 2: BUILD                                            │
│ ├─ Multi-round capability selection (4 per round)         │
│ ├─ Dependency resolution                                  │
│ └─ Generate files → .agent/builds/{id}/artifacts.json     │
└───────────────────────────────────────────────────────────┘
```

## Concept Mode Q&A Flow

### Round 1: Complexity Level Selection

```
AskUserQuestion(
  questions=[{
    "question": "어떤 복잡도 레벨을 선택하시겠습니까?",
    "header": "Level",
    "options": [
      {"label": "Level 0 - Basic", "description": "Core features only (4 capabilities)"},
      {"label": "Level 50 - Recommended", "description": "Production-ready (9 capabilities)"},
      {"label": "Level 100 - Full", "description": "All features (14 capabilities)"},
      {"label": "Custom Selection", "description": "Choose individual capabilities"}
    ],
    "multiSelect": false
  }]
)
```

### Rounds 2-N: Capability Selection (Custom or batched)

```
# Skills batch (max 4 options per round)
AskUserQuestion(
  questions=[{
    "question": "포함할 Skill을 선택하세요",
    "header": "Skills",
    "options": [
      {"label": "[S1] core-feature", "description": "Required base capability"},
      {"label": "[S2] enhancement", "description": "Optional enhancement"},
      {"label": "[S3] integration", "description": "Third-party integration"},
      {"label": "Skip skills", "description": "No additional skills"}
    ],
    "multiSelect": true
  }]
)
```

## State Persistence

All concept mode state is saved in `.agent/builds/{build_id}/`:

```
.agent/builds/
├── master/
│   ├── capability_index.json    # Master capability reference
│   └── complexity_levels.json   # Level 0/50/100 definitions
└── {build_id}/
    ├── research.json            # Phase 0 output
    ├── selection.json           # Phase 1-2 selections
    └── artifacts.json           # Phase 2 generated files
```

## Resume Support

```bash
# Resume an incomplete build
/build --resume pd-a1b2

# Lists available drafts if id not found
/build --resume
```

---

---

# SECTION 1: AGENTS

## Agent Overview

Agents are **specialized subagents** with focused capabilities, tool restrictions, and optional model selection.

### Agent Architecture

```
┌─────────────────────────────────────────────────────────┐
│  AGENT                                                  │
│  ├── Identity: name, description                        │
│  ├── Tools: allowed[], disallowed[], mcp[]              │
│  ├── Execution: model, context, permissionMode          │
│  ├── Integration: skills[], hooks[]                     │
│  └── Cascade: → Skills → Hooks                          │
└─────────────────────────────────────────────────────────┘
```

### Agent Q&A Rounds (15 + Cascade)

| Category | Rounds | Fields |
|----------|--------|--------|
| Core Identity | 1-3 | name, description, disable-model-invocation |
| Tool Config | 4-6 | tools, disallowedTools, mcp_tools |
| Execution | 7-9 | model, context, permissionMode |
| Integration | 10-12 | skills[], hooks[], customInstructions |
| Advanced | 13-15 | maxTurns, timeout, v21x_features |
| **Cascade** | 16+ | → Skill Q&A → Hook Q&A |

### Agent Fields Reference

```yaml
# === Core (Required) ===
name: string              # Unique identifier (e.g., "code-reviewer")
description: string       # When Claude should delegate to this agent

# === Tools ===
tools: string[]           # Allowed: Read, Grep, Glob, Task, Edit, Write, Bash...
disallowedTools: string[] # Explicitly denied tools
mcp_tools: string[]       # MCP server tools (mcp__server__tool)

# === Execution ===
model: enum               # sonnet | opus | haiku | inherit
context: enum             # standard | fork (V2.1.x+)
permissionMode: enum      # auto | confirm | deny

# === Integration ===
skills: string[]          # Skills preloaded into agent context
hooks:                    # Agent-level hooks
  PreToolUse: string[]
  PostToolUse: string[]
  SubagentStart: string[]
  SubagentStop: string[]

# === Optional ===
disable-model-invocation: bool  # Prevent auto-delegation
maxTurns: number          # Max turns before stopping
customInstructions: string # Additional system prompt
```

### Agent Invocation Patterns

```yaml
# Automatic Delegation (Claude decides)
description: "Reviews code for security vulnerabilities"
# → Claude auto-delegates when user asks about security review

# Explicit Invocation (User/Skill requests)
prompt: "Use the code-reviewer agent to analyze this file"

# Programmatic (SDK)
agents:
  code-reviewer:
    description: "..."
    tools: [Read, Grep, Glob]
```

### Agent Output Location

```
.claude/agents/{name}.md
```

---

# SECTION 2: SKILLS

## Skill Overview

Skills are **reusable workflows** invoked via `/command` or automatically by Claude based on description matching.

### Skill Architecture

```
┌─────────────────────────────────────────────────────────┐
│  SKILL                                                  │
│  ├── Identity: name, description, user-invocable        │
│  ├── Execution: context, agent, model                   │
│  ├── Tools: allowed-tools, argument-hint                │
│  ├── Control: disable-model-invocation, once            │
│  └── Cascade: → Hooks                                   │
└─────────────────────────────────────────────────────────┘
```

### Skill Q&A Rounds (13 + Cascade)

| Category | Rounds | Fields |
|----------|--------|--------|
| Identity | 1-3 | name, description, user-invocable |
| Execution | 4-6 | context, agent, model |
| Tools | 7-9 | allowed-tools, argument-hint |
| Control | 10-11 | disable-model-invocation, once |
| Features | 12-13 | content-type, ultrathink |
| **Cascade** | 14+ | → Hook Q&A |

### Skill Fields Reference

```yaml
# === Core (Required) ===
name: string              # Becomes /name command
description: string       # Displayed in skill list & auto-delegation

# === Execution ===
user-invocable: bool      # Can user invoke directly? (default: true)
context: enum             # standard | fork
agent: string             # Agent type when context: fork (Explore, Plan, general-purpose)
model: enum               # sonnet | opus | haiku

# === Tools ===
allowed-tools: string[]   # Tools available during execution
argument-hint: string     # Autocomplete hint for $ARGUMENTS

# === Control (V2.1.x+) ===
disable-model-invocation: bool  # Prevent Claude from auto-invoking
once: bool                # Run only once per session

# === Integration ===
parent_agent: string      # If created via Agent cascade
hooks:
  PreToolUse: string[]
  PostToolUse: string[]
```

### Skill Context Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `standard` | Inline in current conversation | Knowledge injection, templates |
| `fork` | Isolated subagent context | Focused tasks, exploration |

```yaml
# Standard Context - inline execution
---
name: code-style
description: Code style guidelines
context: standard
---

# Fork Context - isolated subagent
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---
```

### Skill Output Location

```
.claude/skills/{name}.md
```

---

# SECTION 3: HOOKS

## Hook Overview

Hooks are **event-driven scripts** that execute at specific lifecycle points.

### Hook Architecture

```
┌─────────────────────────────────────────────────────────┐
│  HOOK                                                   │
│  ├── Identity: name, event, language                    │
│  ├── Trigger: matcher, timeout, type                    │
│  ├── Input/Output: JSON schema                          │
│  ├── Control: blocking, once                            │
│  └── Attachment: agent | skill | global                 │
└─────────────────────────────────────────────────────────┘
```

### Hook Q&A Rounds (16)

| Category | Rounds | Fields |
|----------|--------|--------|
| Identity | 1-3 | name, event-type, language |
| Trigger | 4-6 | matcher, timeout, type |
| Input/Output | 7-10 | permission, updatedInput, additionalContext |
| Output Schema | 11-13 | output-fields, blocking, json-schema |
| Advanced | 14-16 | env-vars, logging, once |

### Hook Event Types (12 Total)

| Event | Trigger Point | Attachable To | Key Outputs |
|-------|---------------|---------------|-------------|
| `SessionStart` | Session begins | Global | env persistence |
| `SessionEnd` | Session ends | Global | cleanup |
| `Setup` | Repository init | Global | project setup |
| `UserPromptSubmit` | User sends prompt | Global | validation, context |
| `PreToolUse` | Before tool | Agent, Skill, Global | allow/deny/modify |
| `PostToolUse` | After tool success | Agent, Skill, Global | validation, formatting |
| `PostToolUseFailure` | After tool failure | Agent, Skill, Global | error handling |
| `PermissionRequest` | Permission prompt | Global | auto-approve/deny |
| `PreCompact` | Before context compact | Global | state preservation |
| `Notification` | System notification | Global | custom alerts |
| `SubagentStart` | Subagent begins | Agent | setup, monitoring |
| `SubagentStop` | Subagent ends | Agent | cleanup, validation |
| `Stop` | Session/agent stops | Global | completion check |

### Hook Types (V2.1.x+)

| Type | Description | Language |
|------|-------------|----------|
| `command` | Shell command execution | bash, python, node |
| `prompt` | LLM-based evaluation | N/A (uses model) |

### Hook Fields Reference

```yaml
# === Identity ===
name: string              # Hook identifier
event: enum               # One of 12 event types

# === Trigger ===
matcher: string           # Regex pattern (e.g., "Bash|Edit|Write")
timeout: number           # Milliseconds (default: 60000)
type: enum                # command | prompt

# === For type: command ===
command: string           # Shell command
language: enum            # bash | python | node

# === For type: prompt (V2.1.x+) ===
prompt: string            # LLM evaluation prompt

# === Output Schema (JSON) ===
output_schema:
  continue: bool          # Continue execution?
  stopReason: string      # Why stopped
  suppressOutput: bool    # Hide from transcript
  systemMessage: string   # Display to user
  permissionDecision: enum # allow | deny | ask (PreToolUse)
  additionalContext: string # Inject into Claude context
  updatedInput: object    # Modify tool input

# === Control ===
blocking: bool            # Block until complete?
once: bool                # Run only once per session

# === Attachment ===
attached_to:
  type: enum              # agent | skill | global
  name: string            # Parent component name
```

### Hook Lifecycle Flow

```
SessionStart
    ↓
UserPromptSubmit ←──────────────────┐
    ↓                               │
PreToolUse → [Tool] → PostToolUse   │
    ↓              ↘ PostToolUseFailure
    ↓                               │
Stop ───────────────────────────────┘
    ↓ (if continue: false)
SessionEnd
```

### Hook Output Locations

| Attachment | Path Pattern |
|------------|--------------|
| Agent-attached | `.claude/hooks/{agent_name}/{hook_name}.{ext}` |
| Skill-attached | `.claude/hooks/{skill_name}/{hook_name}.{ext}` |
| Global | `.claude/hooks/global/{hook_name}.{ext}` |

---

# SECTION 4: RUNTIME CHAINING

## Runtime Chaining Overview

Runtime Chaining defines **execution-time orchestration patterns** for coordinating multiple components.

### Key Constraint (Native Limitation)

```
┌────────────────────────────────────────────────────────────┐
│  ⚠️  DIRECT CHAINING NOT SUPPORTED                        │
│                                                            │
│  ❌ Skill → Skill (direct call)                           │
│  ❌ Agent → Agent (nested spawn)                          │
│  ❌ Hook → Hook (direct trigger)                          │
│                                                            │
│  ✅ ORCHESTRATOR PATTERN REQUIRED                         │
│  Main Agent/Session coordinates all delegations            │
└────────────────────────────────────────────────────────────┘
```

### Runtime Chaining Q&A Rounds (12)

| Category | Rounds | Fields |
|----------|--------|--------|
| Pattern Type | 1-2 | pattern_type, name |
| Components | 3-5 | agents[], skills[], hooks[] |
| Execution | 6-8 | mode, parallelization, error_handling |
| Data Flow | 9-10 | input_mapping, output_aggregation |
| Advanced | 11-12 | retry_policy, timeout, notifications |

### Supported Orchestration Patterns

#### Pattern 1: Sequential Delegation

```yaml
pattern: sequential
name: code-review-pipeline
description: "Sequential code review workflow"

steps:
  - component: agent/code-reviewer
    input: "$user_request"
    output: "$review_result"

  - component: agent/security-scanner
    input: "$review_result"
    output: "$security_result"

  - component: skill/generate-report
    input:
      review: "$review_result"
      security: "$security_result"

orchestration: |
  1. code-reviewer analyzes code
  2. security-scanner checks vulnerabilities
  3. generate-report synthesizes findings
```

#### Pattern 2: Parallel Fan-Out

```yaml
pattern: parallel
name: multi-aspect-review
description: "Parallel analysis with result synthesis"

fan_out:
  - component: agent/style-checker
    input: "$code"
  - component: agent/security-scanner
    input: "$code"
  - component: agent/test-validator
    input: "$code"

fan_in:
  aggregator: skill/synthesize-results
  strategy: merge_all  # merge_all | first_success | majority_vote
```

#### Pattern 3: Conditional Branching

```yaml
pattern: conditional
name: smart-review
description: "Condition-based workflow routing"

condition:
  evaluate: "file_type"
  branches:
    - when: "*.py"
      then: agent/python-reviewer
    - when: "*.ts"
      then: agent/typescript-reviewer
    - default:
      then: agent/general-reviewer
```

#### Pattern 4: Event-Driven Chain

```yaml
pattern: event_driven
name: validation-pipeline
description: "Hook-based validation chain"

events:
  PreToolUse:
    matcher: "Edit|Write"
    action: hook/validate-changes
    on_success: continue
    on_failure: block

  PostToolUse:
    matcher: "Edit|Write"
    action: hook/auto-format
    then: hook/run-linter

  Stop:
    action: hook/completion-check
    type: prompt
    prompt: "Verify all tasks completed successfully"
```

#### Pattern 5: Phased Workflow (SDK)

```yaml
pattern: phased
name: development-workflow
description: "Multi-phase development with session management"

phases:
  - name: investigation
    mode: read_only
    components:
      - agent: Explore
        tools: [Read, Grep, Glob]
    output: "$findings"

  - name: planning
    mode: read_only
    components:
      - agent: Plan
        input: "$findings"
    output: "$plan"
    user_approval: required

  - name: implementation
    mode: full_access
    components:
      - agent: general-purpose
        input: "$plan"
    hooks:
      PostToolUse: [auto-format, lint-check]

  - name: verification
    mode: read_only
    components:
      - agent: test-runner
      - agent: code-reviewer
    parallelization: true

session_management:
  resume_enabled: true
  fork_enabled: true
  checkpoint_after_phase: true
```

### Runtime Chaining Fields Reference

```yaml
# === Identity ===
name: string              # Chain identifier
description: string       # What this chain does
pattern: enum             # sequential | parallel | conditional | event_driven | phased

# === Components ===
components:
  agents: string[]        # Agents involved
  skills: string[]        # Skills involved
  hooks: string[]         # Hooks involved

# === Execution ===
mode: enum                # read_only | full_access | mixed
parallelization: bool     # Enable parallel execution
error_handling: enum      # stop_on_first | continue_all | retry

# === Data Flow ===
input_mapping:
  variable: source        # Map inputs to components
output_aggregation:
  strategy: enum          # merge_all | first_success | custom
  custom_aggregator: string

# === Advanced ===
retry_policy:
  max_retries: number
  backoff: enum           # linear | exponential
timeout: number           # Total chain timeout (ms)
notifications:
  on_start: bool
  on_complete: bool
  on_error: bool

# === Session (SDK) ===
session_management:
  resume_enabled: bool    # Allow session resume
  fork_enabled: bool      # Allow session fork
  checkpoint_after_phase: bool
```

### Orchestration Best Practices

| Scenario | Pattern | Reason |
|----------|---------|--------|
| Code review pipeline | Sequential | Each step depends on previous |
| Multi-aspect analysis | Parallel | Independent checks |
| File-type specific | Conditional | Different handlers |
| Auto-validation | Event-driven | Hook-based, deterministic |
| Complex development | Phased | Session management, checkpoints |

### Runtime Chain Output Location

```
.claude/chains/{name}.yaml
```

---

# CASCADING BUILD FLOW

## Full Cascade Example

```
/build agent

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔧 AGENT Q&A (15 rounds)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
→ Q1-15: Agent configuration...

📦 CASCADE: Add Skills?
→ "예, Skills 추가"

  ┌──────────────────────────────────────────────────────┐
  │ 🔧 SKILL Q&A (13 rounds)                             │
  │ → Q1-13: Skill configuration...                      │
  │                                                      │
  │ 📦 CASCADE: Add Hooks?                               │
  │ → "예"                                                │
  │   ┌────────────────────────────────────────────────┐ │
  │   │ 🔧 HOOK Q&A (16 rounds)                        │ │
  │   └────────────────────────────────────────────────┘ │
  └──────────────────────────────────────────────────────┘

📦 Add Agent-Level Hooks?
→ "예"
  ┌──────────────────────────────────────────────────────┐
  │ 🔧 HOOK Q&A (16 rounds)                              │
  └──────────────────────────────────────────────────────┘

📦 Define Runtime Chain?
→ "예"
  ┌──────────────────────────────────────────────────────┐
  │ 🔗 CHAIN Q&A (12 rounds)                             │
  │ → Pattern: sequential                                │
  │ → Components: [agent, skills, hooks]                 │
  └──────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ BUILD COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Generated:
├── Agent: code-reviewer
│   ├── Skill: quick-review
│   │   └── Hook: review-logger
│   ├── Skill: deep-review
│   ├── Hook: agent-monitor
│   └── Chain: review-pipeline (sequential)

Files:
├── .claude/agents/code-reviewer.md
├── .claude/skills/quick-review.md
├── .claude/skills/deep-review.md
├── .claude/hooks/code-reviewer/review-logger.py
├── .claude/hooks/code-reviewer/agent-monitor.py
└── .claude/chains/review-pipeline.yaml
```

---

# CROSS-REFERENCE SYSTEM

## Auto-Generated References

When cascade completes, files include proper cross-references:

**Agent → Skills, Hooks, Chains:**
```yaml
# .claude/agents/code-reviewer.md
skills:
  - quick-review
  - deep-review
hooks:
  SubagentStart: [agent-monitor]
chains:
  - review-pipeline
```

**Skill → Hooks, Parent:**
```yaml
# .claude/skills/quick-review.md
parent_agent: code-reviewer
hooks:
  PostToolUse: [review-logger]
```

**Chain → Components:**
```yaml
# .claude/chains/review-pipeline.yaml
components:
  agents: [code-reviewer]
  skills: [quick-review, deep-review]
  hooks: [review-logger, agent-monitor]
```

---

# FLAGS & OPTIONS

| Flag | Description |
|------|-------------|
| `--standalone` | Disable cascade, single component only |
| `--resume <name>` | Resume incomplete draft |
| `--dry-run` | Preview without creating files |
| `--template <path>` | Use custom template |
| `--no-chain` | Skip runtime chain prompt |

---

# V2.1.x+ FEATURES SUMMARY

| Feature | Section | Description |
|---------|---------|-------------|
| `context: fork` | Skill | Isolated subagent execution |
| `type: prompt` | Hook | LLM-based hook evaluation |
| `PostToolUseFailure` | Hook | Tool failure handling |
| `once` | Hook/Skill | Single execution per session |
| Runtime Chaining | Chain | Orchestration patterns |
| Session fork | Chain | Alternative path exploration |

---

# NOTES

- All Q&A can be skipped with defaults
- Draft auto-saves after each round
- Cascade can be cancelled at any prompt
- Cross-references automatically maintained
- Runtime chains are YAML-based for SDK integration
- Direct chaining unsupported by design (use Orchestrator pattern)

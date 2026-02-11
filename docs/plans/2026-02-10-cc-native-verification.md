# CC-Native Agent Teams Verification

> Date: 2026-02-10
> Purpose: Verify INFRA v7.0 design against Claude Code native capabilities
> Method: context7 + claude-code-guide research + local INFRA audit

---

## 1. Frontmatter Capabilities (RQ-1)

### What CC Provides

Agent definition files (`.claude/agents/*.md`) support these YAML frontmatter fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | String | Yes | Unique agent identifier (lowercase + hyphens) |
| `description` | String | Yes | When Claude should delegate to this agent |
| `tools` | String[] | No | **Allowlist** — agent can ONLY use these tools. Omit = inherit all |
| `disallowedTools` | String[] | No | **Denylist** — removed from inherited or specified tools |
| `model` | String | No | `opus`, `sonnet`, `haiku`, or `inherit` (default: inherit) |
| `permissionMode` | String | No | `default`, `acceptEdits`, `delegate`, `dontAsk`, `bypassPermissions`, `plan` |
| `maxTurns` | Integer | No | Maximum agentic turns before stopping |
| `memory` | String | No | Persistent memory scope: `user`, `project`, or `local` |
| `color` | String | No | Terminal display color |
| `skills` | String[] | No | Skills to load into agent context at startup |
| `mcpServers` | Object | No | MCP servers available to this agent |
| `hooks` | Object | No | Agent-scoped lifecycle hooks (PreToolUse, PostToolUse, Stop) |

**Resolution priority:**
1. CLI `--agents` flag (session-only, highest)
2. Project `.claude/agents/` (team-shared)
3. User `~/.claude/agents/` (personal)
4. Plugin-provided agents
5. Built-in agents (Explore, Plan, general-purpose, etc.)

**No hard limit** on number of registered agents.

### What We Use (16 agents)

All 16 agents use these frontmatter fields:
- `name`, `description`, `model`, `permissionMode`, `memory`, `color`, `maxTurns`, `tools`, `disallowedTools`

### What We're Missing

| Field | Status | Impact |
|-------|--------|--------|
| `skills` | **NOT USED** | Could inject skill content at spawn — eliminates need for "Read agent-common-protocol.md" instructions |
| `mcpServers` | **NOT USED** | Could scope MCP servers per agent (e.g., only researcher gets tavily) |
| `hooks` | **NOT USED** | Could add agent-scoped hooks (e.g., implementer-specific PreToolUse validation) |

### Redundancy Found

We specify BOTH `tools` (allowlist) AND `disallowedTools` (denylist) on every agent. This is redundant — if `tools` is already an allowlist, `disallowedTools` only matters for tools inherited from parent when `tools` is omitted. Since we explicitly list `tools`, our `disallowedTools: [TaskCreate, TaskUpdate]` is technically unnecessary (those aren't in the `tools` list anyway).

**However**, this may serve as defense-in-depth if CC implementation treats `tools` as additive rather than exclusive. Keep both as safety measure.

---

## 2. Communication Model (RQ-2)

### What CC Provides

**SendMessage types:**

| Type | Direction | Description |
|------|-----------|-------------|
| `message` | One-to-one | DM to specific teammate by name |
| `broadcast` | One-to-all | Message all teammates (expensive) |
| `shutdown_request` | Lead → Teammate | Request graceful shutdown |
| `shutdown_response` | Teammate → Lead | Approve/reject shutdown |
| `plan_approval_response` | Lead → Teammate | Approve/reject plan from `plan` mode agents |

**Key communication characteristics:**
- **Peer-to-peer supported:** Agents CAN message each other directly without Lead mediation
- **Automatic delivery:** Messages delivered as new conversation turns
- **Idle notifications:** System automatically sends idle notifications when teammate turns end
- **Peer DM visibility:** When peer-to-peer DMs happen, Lead gets a brief summary in idle notification
- **No polling needed:** Messages arrive automatically

### What We Use

- `message` (Lead ↔ Teammate): Primary communication channel
- `broadcast` (Lead → All): Phase transition announcements
- `shutdown_request/response`: Team lifecycle management

### What We're Missing

| Capability | Status | Impact |
|------------|--------|--------|
| **Peer-to-peer DMs** | **NOT USED** | Could enable implementer↔implementer coordination without Lead mediation. Our CLAUDE.md §4 restricts to Lead ↔ Teammate only. |
| `plan_approval_response` | **NOT USED** | Could enable Lead to approve plans from teammates in `plan` mode. But BUG-001 blocks plan mode for MCP users. |

### Design Decision Validation

Our CLAUDE.md §4 enforces hub-and-spoke communication (Lead mediates all). This is a **deliberate design choice** for control/traceability, not a CC limitation. CC supports direct peer messaging.

**Trade-off:** Hub-and-spoke provides observability and prevents conflicts, but adds latency for inter-implementer coordination. For 4-implementer scenarios, this is a valid concern.

---

## 3. Task API Constraints (RQ-3)

### What CC Provides

**TaskCreate fields:**

| Field | Required | Description |
|-------|----------|-------------|
| `subject` | Yes | Brief imperative title |
| `description` | Yes | Detailed task description |
| `activeForm` | No (recommended) | Present continuous form for spinner display |
| `metadata` | No | Arbitrary key-value pairs (merge semantics) |

**TaskUpdate fields:**

| Field | Description |
|-------|-------------|
| `status` | `pending` → `in_progress` → `completed` (or `deleted`) |
| `owner` | Assign to specific agent name |
| `subject` | Update title |
| `description` | Update description |
| `activeForm` | Update spinner text |
| `metadata` | Merge metadata (set key to null to delete) |
| `addBlocks` | Add task IDs this blocks |
| `addBlockedBy` | Add task IDs that block this |

**Task scope:**
- Team scope: `~/.claude/tasks/{team-name}/`
- Session scope: `~/.claude/tasks/{sessionId}/`
- No documented hard limit on task count
- **Cross-team isolation:** Teammates can only see their own team's tasks

**Critical constraint:** `blockedBy` and `blocks` are NOT available as TaskCreate fields — they must be set via TaskUpdate after creation.

### What We Use

- All TaskCreate fields (subject, description, activeForm, metadata)
- All TaskUpdate fields
- PERMANENT Task pattern (subject "[PERMANENT] {feature}")
- `disallowedTools` on teammates to enforce Lead-only task creation

### What We're Missing

Nothing significant. Our Task API usage is comprehensive.

### Cross-Team Task Access Problem (Confirmed)

Our CLAUDE.md §6 "Assigning Work" acknowledges this limitation:
> "teammates in a team context can only access their team's task list, not the main list where the PT lives"

This is a **confirmed CC constraint**, not a design bug. Our workaround (embedding PT content directly in directives) is correct.

---

## 4. Architecture Details (RQ-4)

### What CC Provides

**Agent spawning:**
- Agents are separate Claude Code sessions (not tmux splits)
- Each agent gets its own context window
- Agent .md content is injected into the agent's system prompt at spawn
- Agents do NOT see Lead's full conversation history (isolated context)
- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` enables the agent teams feature

**teammateMode setting:**
- `"teammateMode": "auto"` in settings.json (we use this)
- Controls how Claude decides to spawn teammates vs work alone
- `auto` = Claude decides based on task complexity
- Other values: `always`, `never`

**Auto-compact behavior:**
- Teammates have independent context windows
- Each teammate can compact independently
- PreCompact hook fires for the agent being compacted
- No way for Lead to prevent teammate compaction

**Context consumption:**
- Agent .md file content is injected into the agent's system prompt
- CLAUDE.md is also loaded (if present)
- Total system prompt = CLAUDE.md + agent .md + tool descriptions + CC system prompt
- Larger agent .md files consume more of the agent's context budget

### What We Use

- `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` (enabled)
- `teammateMode: auto` (in settings.json)
- 4 hooks: SubagentStart, PreCompact, PostToolUse (async), SessionStart(compact)
- PreCompact saves task snapshots and RTD state
- SubagentStart injects PT guidance or GC version

### What We're Missing / Risks

| Issue | Severity | Description |
|-------|----------|-------------|
| **Agent .md size budget** | MEDIUM | Our 16 agents range from 45-67 lines each. Each agent loads: ~206L CLAUDE.md + ~50L agent .md + ~108L agent-common-protocol.md (via read instruction) = ~364L minimum. This is manageable. |
| **BUG-002 (confirmed)** | HIGH | Large-task teammates auto-compact before writing L1/L2. Our PreCompact hook + §6 Pre-Spawn Checklist mitigates this. |
| **No lazy-loading** | LOW | No way to lazy-load parts of agent definitions. Full content injected at spawn. |

### Hook Integration Details

**Supported hook events (confirmed via CC docs):**

| Event | Fires When | Our Usage |
|-------|-----------|-----------|
| `SubagentStart` | Agent spawned | Context injection |
| `PreCompact` | Before context compaction | State preservation |
| `PostToolUse` | After any tool call | RTD event capture (async) |
| `SessionStart` | Session begins (with matchers) | Compact recovery |
| `PreToolUse` | Before tool call | **NOT USED** (available) |
| `Stop` | Agent stops | **NOT USED** (available) |

**Agent-scoped hooks** (via `.claude/agents/*.md` frontmatter `hooks:` field) are available but we don't use them. These could add per-agent validation.

---

## 5. Skills Integration (RQ-5)

### What CC Provides

- Skills are loaded into agent context at startup via `skills:` frontmatter field
- Skills can invoke any agent type via the Task tool
- The `subagent_type` parameter in Task tool maps to agent `name` field
- Skills can restrict which agents to spawn: `Task(researcher, architect)` syntax
- A skill CAN dynamically choose agent type based on task analysis

### What We Use

- 10 custom skills (brainstorming-pipeline through permanent-tasks)
- Skills invoke agents through Task tool in their SKILL.md prompts
- Skills don't use the `skills:` frontmatter field on agents

### What We're Missing

| Capability | Status | Impact |
|------------|--------|--------|
| **`skills:` in agent frontmatter** | NOT USED | Could preload agent-common-protocol.md content directly, eliminating the "Read and follow agent-common-protocol.md" instruction |
| **Task(agent) restriction syntax** | NOT USED | Could restrict which agents implementers can sub-spawn (e.g., `Task(spec-reviewer, code-reviewer)` only) |

### Opportunity: Skills-as-Context

The `skills:` frontmatter field could replace our current pattern of "Read and follow agent-common-protocol.md" — instead, we'd create a skill containing the protocol and inject it at spawn. This would:
1. Eliminate one Read tool call per agent spawn
2. Guarantee protocol content is in context (not dependent on agent reading it)
3. Reduce context window pollution from Read results

---

## 6. Context Management (RQ-6)

### What CC Provides

**Context budget per agent:**
- System prompt: CLAUDE.md + agent .md + tools + CC system prompt
- Working context: messages, tool calls/results
- `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000` (our setting)
- `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS=100000` (our setting)
- `MAX_MCP_OUTPUT_TOKENS=100000` (our setting)
- `BASH_MAX_OUTPUT_LENGTH=200000` (our setting)

**No lazy-loading mechanism** — entire agent .md is injected at spawn.

**Auto-compact behavior:**
- Triggered when context approaches limit
- Independent per agent (teammate compaction doesn't affect Lead)
- PreCompact hook fires before compaction
- After compaction, session appears as "continued from previous conversation"

### What We Use

- Pre-Spawn Checklist (§6): Scope checks before spawning (S-1/S-2/S-3 gates)
- L1/L2/L3 file system for state persistence across compaction
- PreCompact hook for state preservation
- SessionStart(compact) hook for recovery guidance
- Agent-common-protocol.md §"If You Lose Context" section

### Context Efficiency Analysis

| Agent Type | .md Size (lines) | tools Count | Context Pressure |
|------------|-------------------|-------------|------------------|
| implementer | 58 | 14 | HIGH (full toolset) |
| integrator | 53 | 14 | HIGH (full toolset) |
| architect | 56 | 12 | MEDIUM |
| plan-writer | 56 | 12 | MEDIUM |
| devils-advocate | 49 | 12 | MEDIUM |
| tester | 56 | 13 | MEDIUM-HIGH |
| codebase-researcher | 52 | 9 | LOW |
| external-researcher | 56 | 14 | MEDIUM |
| auditor | 53 | 9 | LOW |
| static-verifier | 67 | 12 | MEDIUM |
| relational-verifier | 68 | 12 | MEDIUM |
| behavioral-verifier | 68 | 12 | MEDIUM |
| spec-reviewer | 48 | 8 | LOW |
| code-reviewer | 45 | 8 | LOW |
| execution-monitor | 57 | 9 | LOW |
| dynamic-impact-analyst | 54 | 9 | LOW |

All agents also load CLAUDE.md (~206 lines) as system prompt. Total system context per agent:
- LOW: ~250-260L system + tools
- MEDIUM: ~262-274L system + tools
- HIGH: ~264L system + full toolset

This is within acceptable bounds. No agent .md exceeds 70 lines.

---

## 7. Model Configuration (RQ-7)

### What CC Provides

- Model can be specified per agent via `model:` frontmatter field
- Valid values: `opus`, `sonnet`, `haiku`, `inherit` (default)
- Model can also be overridden via Task tool `model:` parameter at spawn time
- Task tool `model:` overrides agent frontmatter `model:`

**Model IDs (as of 2026-02-10):**
- `opus` → claude-opus-4-6
- `sonnet` → claude-sonnet-4-5-20250929
- `haiku` → claude-haiku-4-5-20251001

### What We Use

ALL 16 agents specify `model: opus`. Our CLAUDE.md header says "All instances: claude-opus-4-6".

### What We Could Use Better

| Agent Type | Current | Recommendation | Rationale |
|------------|---------|----------------|-----------|
| spec-reviewer | opus | **sonnet** | Read-only, pattern matching task |
| code-reviewer | opus | **sonnet** | Read-only, pattern matching task |
| execution-monitor | opus | **sonnet** | Polling + alerting, no deep reasoning |
| auditor | opus | **sonnet** | Inventory + classification, structured output |
| All others | opus | opus (keep) | Need deep reasoning for architecture/implementation |

**Cost implications:** Switching 4 read-only agents to sonnet would reduce per-agent cost by ~60% for those roles, while maintaining quality for their structured tasks.

**Risk:** Sonnet may miss subtle architectural issues that opus would catch. For Phase 6+ review agents (spec-reviewer, code-reviewer), this trade-off is debatable.

---

## 8. Gap Analysis: Our Design vs CC Capabilities

### Features We Use Well

| Feature | Our Usage | Assessment |
|---------|-----------|------------|
| Agent .md definitions | 16 well-structured agents | EXCELLENT |
| tools allowlist | Per-agent tool scoping | EXCELLENT |
| disallowedTools | TaskCreate/TaskUpdate restriction | GOOD (redundant but safe) |
| Hook system | 4 hooks (SubagentStart, PreCompact, PostToolUse, SessionStart) | EXCELLENT |
| Task API | PERMANENT Task pattern, versioned PT | EXCELLENT |
| L1/L2/L3 system | Proactive state persistence | EXCELLENT |
| Team Memory | Section-per-role structure | GOOD |
| RTD Observability | Decision points, event capture | EXCELLENT |
| Model selection | Consistent opus usage | OK (could optimize) |

### Features We Underutilize

| Feature | CC Capability | Our Usage | Gap |
|---------|--------------|-----------|-----|
| `skills:` frontmatter | Inject skills at spawn | Not used | HIGH — could replace "Read protocol.md" pattern |
| `mcpServers:` frontmatter | Scope MCP per agent | Not used | MEDIUM — could limit tavily to researchers only |
| `hooks:` in agent frontmatter | Agent-scoped hooks | Not used | LOW — global hooks suffice currently |
| Peer-to-peer messaging | Direct agent-to-agent DMs | Not used | MEDIUM — could speed up inter-implementer coordination |
| Model diversity | Per-agent model selection | All opus | MEDIUM — cost optimization opportunity |
| `Task(agent)` restriction | Restrict sub-spawning | Not used | LOW — implementers already restricted by tools list |
| PreToolUse hook | Validate before tool execution | Not used | LOW — could add safety checks |
| Stop hook | Agent shutdown handler | Not used | LOW — could ensure L1/L2 save on stop |

### Features with Known Issues

| Feature | Issue | Status |
|---------|-------|--------|
| `permissionMode: plan` | BUG-001: Blocks MCP tools | Workaround: always use "default" |
| Teammate auto-compact | BUG-002: L1/L2 lost | Workaround: Pre-Spawn Checklist |
| `$CLAUDE_SESSION_ID` | BUG-003: Not available in hooks | Workaround: stdin session_id |

---

## 9. Recommendations for INFRA Overhaul

### Priority 1 (High Impact, Low Effort)

#### R-1: Use `skills:` frontmatter to inject agent-common-protocol

**Current:** Each agent .md starts with "Read and follow `.claude/references/agent-common-protocol.md`"
**Proposed:** Create a skill from agent-common-protocol.md and add to each agent's `skills:` field

```yaml
# In each agent .md:
skills:
  - agent-common-protocol
```

**Benefits:**
- Guarantees protocol is in context (no Read call needed)
- Saves ~1 tool call per agent spawn
- More reliable than "Read and follow" instruction

#### R-2: Diversify model selection for cost optimization

**Current:** All 16 agents use `model: opus`
**Proposed:** Use sonnet for read-only, structured-output agents

| Agent | Change | Savings |
|-------|--------|---------|
| spec-reviewer | opus → sonnet | ~60% per use |
| code-reviewer | opus → sonnet | ~60% per use |
| execution-monitor | opus → sonnet | ~60% per use |
| auditor | opus → sonnet | ~60% per use |

**Risk mitigation:** Test with sonnet first on non-critical paths. Keep opus for agents requiring deep reasoning.

#### R-3: Remove redundant `disallowedTools`

**Current:** Every agent has both `tools:` (allowlist) and `disallowedTools: [TaskCreate, TaskUpdate]`
**Proposed:** Remove `disallowedTools` since `tools:` already acts as exclusive allowlist

**Risk:** Low — but verify CC behavior treats `tools:` as exclusive (not additive). If uncertain, keep both.

### Priority 2 (Medium Impact, Medium Effort)

#### R-4: Add Stop hook for L1/L2 safety net

**Current:** L1/L2 persistence depends on agent following instructions
**Proposed:** Add agent-scoped `Stop` hook that warns about missing L1/L2 files

```yaml
# In implementer.md, tester.md, etc.:
hooks:
  Stop:
    - type: command
      command: "/home/palantir/.claude/hooks/on-agent-stop.sh"
      timeout: 10
```

#### R-5: Enable selective peer-to-peer messaging

**Current:** All communication through Lead (hub-and-spoke)
**Proposed:** Allow peer DMs between implementers working on adjacent files

**Implementation:** Document in CLAUDE.md §4 that peer DMs are permitted for:
- Interface contract questions between implementers
- Quick file ownership boundary queries
- NOT for design decisions (those still go through Lead)

#### R-6: Scope MCP servers per agent

**Current:** All MCP servers available to all agents
**Proposed:** Use `mcpServers:` frontmatter to limit access

| Agent Type | Should Have | Should NOT Have |
|------------|-------------|-----------------|
| codebase-researcher | sequential-thinking | tavily, context7, github |
| external-researcher | sequential-thinking, tavily, context7 | github |
| implementer | All | — |
| devils-advocate | sequential-thinking, tavily, context7 | github |

**Note:** This may be blocked if `mcpServers:` in agent frontmatter requires defining server configs inline rather than referencing existing ones. Needs testing.

### Priority 3 (Low Impact, Variable Effort)

#### R-7: Add PreToolUse hook for safety validation

Validate destructive Bash commands at the hook level, not just via CLAUDE.md §8 instructions.

#### R-8: Investigate `teammateMode` optimization

Currently `auto` — experiment with explicit control to prevent unnecessary teammate spawning in solo phases (P0, P1, P9).

#### R-9: Test `$CLAUDE_CODE_TASK_LIST_ID` for cross-session persistence

Ensure task lists persist correctly when using env var for session continuity.

---

## 10. Summary Table

| RQ | Key Finding | Action Needed |
|----|-------------|---------------|
| RQ-1 | `skills:`, `mcpServers:`, `hooks:` in frontmatter unused | R-1, R-6 |
| RQ-2 | Peer-to-peer messaging available but unused | R-5 |
| RQ-3 | Task API fully utilized, cross-team isolation confirmed | None |
| RQ-4 | Hook system well-used, Stop hook opportunity | R-4 |
| RQ-5 | `skills:` frontmatter → protocol injection opportunity | R-1 |
| RQ-6 | Agent .md sizes acceptable, no lazy-load available | None |
| RQ-7 | All-opus is suboptimal for read-only agents | R-2 |
| Cross-cutting | `disallowedTools` redundant with `tools:` allowlist | R-3 |

### Verification Status

| INFRA Component | CC-Native Alignment | Notes |
|-----------------|---------------------|-------|
| CLAUDE.md v7.0 | **STRONG** | Well-aligned with CC capabilities |
| Agent definitions (16) | **GOOD** | Missing skills/mcpServers fields |
| Hooks (4) | **STRONG** | Using 4 of 6 available hook events |
| Task API usage | **STRONG** | Comprehensive PERMANENT Task pattern |
| Communication model | **MODERATE** | Hub-and-spoke is deliberate but limits peer coordination |
| Model strategy | **WEAK** | All-opus is expensive for read-only agents |
| Skills integration | **MODERATE** | Skills exist but don't leverage agent frontmatter injection |

# Context Engineering — CC Native Mechanics (2026-02-14)

## Context Loading Order
1. CLAUDE.md → persistent memory, survives compaction, re-injected automatically
2. Skill L1 descriptions → loaded in system-reminder as part of Skill tool definition
3. SessionStart hooks → `hookSpecificOutput.additionalContext` injected into context
4. Agent L1 descriptions → loaded in Task tool definition
5. SubagentStart hooks → `hookSpecificOutput.additionalContext` injected into spawned instance (teammate/subagent)
6. Conversation messages → user + assistant turns

## Skill Native Fields (Verified 2026-02-14)
- `name`: string (lowercase, hyphens, max 64 chars)
- `description`: string (multi-line, max 1024 chars) — L1 routing intelligence
- `argument-hint`: string (e.g., "[topic]") — shown to user in skill list
- `user-invocable`: boolean — appears in /slash-command list
- `disable-model-invocation`: boolean — if true, L1 description NOT loaded into context
- `allowed-tools`: list — restricts tools available during skill execution
- `model`: enum (sonnet, opus, haiku, inherit)
- `context`: enum (fork) — DANGER: replaces agent body with skill L2 body
- `agent`: string — routes skill execution to named agent
- `hooks`: object — skill-specific hook configuration

## Agent Native Fields (Verified 2026-02-14)
- `name`, `description`: identity fields
- `tools`, `disallowedTools`: tool access control
- `model`: enum (sonnet, opus, haiku)
- `permissionMode`: enum (default, plan, bypassPermissions, etc.)
- `maxTurns`: number — limits agent conversation turns
- `skills`: list — preloads FULL content (L1+L2) at agent startup
- `mcpServers`: list — MCP server access
- `hooks`: object — agent-specific hook configuration
- `memory`: object — persistent memory configuration
- `color`: string — UI color coding

## Critical Findings

### disable-model-invocation: true = INVISIBLE to Lead
When a skill has `disable-model-invocation: true`, its L1 description is NOT loaded into the Skill tool definition. This means Lead cannot route to it via semantic matching. Only user can invoke via /slash-command.

**Impact**: 4 pipeline skills (design-architecture, plan-decomposition, orchestration-decompose, execution-code) were invisible. Fixed 2026-02-14.

### context: fork = Agent Body REPLACED
When `context: fork` is set on a skill, invoking that skill causes the L2 body to become the subagent's system prompt, REPLACING the agent's .md body entirely. Agent safety constraints, role identity, and tool guidance are LOST.

**Decision**: Do NOT use context:fork for skills that route to agents with safety-critical body content. Reverted from delivery-pipeline and task-management (2026-02-14).

### Non-Native Fields Silently Ignored
Fields like `input_schema`, `confirm`, `working_dir`, `timeout`, `env` are silently ignored by CC. They consume description budget but provide zero functionality.

**Impact**: 12 skills had `input_schema`, 3 had `confirm`. All removed 2026-02-14.

### $ARGUMENTS Auto-Append
If skill body does NOT contain `$ARGUMENTS` placeholder, user input is auto-appended as: `ARGUMENTS: <user_input>`. If body contains `$ARGUMENTS`, it's substituted in-place.

### Agent `skills` Field = Full Preload
Setting `skills: [skill-name]` in agent frontmatter preloads the FULL skill content (L1+L2) into the agent at startup. This is powerful but consumes context budget.

### SLASH_COMMAND_TOOL_CHAR_BUDGET
Setting in settings.json. Default 16000. We use 32000. Controls total chars for all skill L1 descriptions in system-reminder. With 27 auto-loaded skills, budget usage:
- Pre-v10.3: ~31,555 raw chars → CC truncated to ~27,648 effective (86% budget)
- Post-v10.3: all 27 descriptions trimmed to ≤1024 chars → zero truncation, ~24,000 effective (75% budget)
- **Safe** with ~8KB headroom for new auto-loaded skills

### Description Optimization (v10.3, 2026-02-14)
All 32 skill descriptions rewritten to ≤1024 chars. Zero truncation in L1.
- Canonical structure: [Tag] summary → WHEN → DOMAIN → INPUT_FROM → OUTPUT_TO → METHODOLOGY → OUTPUT_FORMAT
- Removed from L1: ONTOLOGY_LENS (5 verify-*), CLOSED_LOOP (8 skills), MAX_TEAMMATES (25 skills)
- Merged: PREREQUISITE into WHEN condition
- Kept selectively: TIER_BEHAVIOR (routing-relevant), CONSTRAINT (critical only)
- Result: Lead sees FULL description for every auto-loaded skill — no information loss from truncation

### Semantic Routing Mechanics (2026-02-14 delta, claude-code-guide)
- Claude uses pure transformer reasoning for skill selection (not keyword matching)
- "Use when:" trigger language improves user-facing skill activation
- Our WHEN: field serves equivalent purpose for pipeline routing (Lead reads as ordering metadata)
- No skill priority/weight mechanism — budget exclusion likely FIFO
- Excluded skills still invocable via /slash-command by user

### Agent `memory` Configuration (2026-02-14)
- 4 of 6 agents configured: analyst, researcher, implementer, infra-implementer (`memory: project`)
- 2 without memory: delivery-agent (terminal), pt-manager (procedural)
- Existing MEMORY.md files: implementer (3KB), researcher (8KB)
- Auto-loaded at agent startup: first 200 lines of agent's MEMORY.md

### Agent `maxTurns` Configuration (2026-02-14)
All 6 agents configured. One turn = one agentic loop iteration (multiple tool calls per turn).
- analyst=25, researcher=30, infra-implementer=35, implementer=50
- delivery-agent=20, pt-manager=20 (focused/terminal roles)

### SRC (Smart Reactive Codebase) Feasibility (2026-02-14)
CC native capabilities verified for SRC implementation:
- PostToolUse hook with `Edit|Write` regex matcher: YES
- Hook `async: true` for non-blocking grep operations: YES
- Hook `timeout` configurable (default 60s): YES
- SubagentStop hook for post-implementer trigger: YES (can block with exit 2)
- additionalContext for per-turn impact injection: YES (single turn only)
- Recursive skill chaining via Lead routing: YES (not native recursion)
- `.claude/rules/*.md` for path-scoped codebase rules: YES (new discovery)
- Persistent knowledge via MEMORY.md: YES (auto-loaded, 200 line limit)
- Overall verdict: FULLY FEASIBLE, no blockers

## Unexplored Opportunities
- `allowed-tools` on skills: could restrict tools during specific skill execution
- ~~Async hooks / prompt-based hooks / agent-based hooks~~ **DISCOVERED** (2026-02-15): `type: "prompt"` = single-turn LLM eval (default 10s, configurable model), `type: "agent"` = multi-turn subagent with tools (max 50 turns, default 60s). Both return `{"ok": bool, "reason": "..."}`. See cc-reference/hook-events.md for full details + example config.
- `$ARGUMENTS` explicit substitution in skill L2 bodies
- ~~`TaskCompleted` hook: quality gate before task completion~~ SubagentStop verified (SRC feasibility)
- `TeammateIdle` hook: ensure agents complete work before going idle
- Agent `hooks` in frontmatter: role-specific validation (vs global cross-agent hooks)
- ~~Description optimization: trim to <=1024 chars~~ DONE in v10.3
- Skill `hooks` in frontmatter: skill-scoped hooks (v2.1.0+, currently unused)
- `.claude/rules/*.md` path-scoped rules: potential for codebase-specific impact rules
- **Shell preprocessing** (`` !`command` ``): already documented in cc-reference/arguments-substitution.md. Potential: live codebase injection in more skills.
- **`CLAUDE_CODE_EFFORT_LEVEL`** (2026-02-15): Opus 4.6 thinking depth control (low/medium/high/max). Replaces MAX_THINKING_TOKENS. Could optimize cost for simpler pipeline phases.
- **`CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`** (2026-02-15): Compaction threshold override (1-100%). Could tune per-session compaction timing for long pipelines.
- **128K output tokens** (2026-02-15): Opus 4.6 supports `CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000` (4x default 32K). Useful for large code generation or analysis output.

# CC Context Loading Mechanics
<!-- Last verified: 2026-02-16 via claude-code-guide, globs fix, CC 64K cap, compaction buffer noted -->
<!-- Update policy: Re-verify after CC version updates -->

## Session Start Loading Order
1. System prompt (CC base instructions)
2. CLAUDE.md chain: global (~/.claude/CLAUDE.md) + project (.claude/CLAUDE.md) + local (CLAUDE.md) + project-memory (projects/*/memory/MEMORY.md)
2.5. `.claude/rules/*.md` — supplements CLAUDE.md (does not replace), loaded when matching files are referenced
3. Skill L1 descriptions aggregated into Skill tool definition (system-reminder)
4. Agent L1 descriptions loaded into Task tool definition
5. SessionStart hooks fire, additionalContext injected
6. Conversation begins

## CLAUDE.md Loading
- Multiple files loaded simultaneously (not override, concatenation)
- Hierarchy: `~/.claude/CLAUDE.md` (user global) > `.claude/CLAUDE.md` (project) > `CLAUDE.md` (repo root) > `*/CLAUDE.md` (directory-scoped)
- Project memory: `.claude/projects/{project-hash}/memory/MEMORY.md` auto-loaded
- All survive compaction (re-injected automatically)
- Max recommended: keep total under 2000 tokens for efficiency

## Rules Directory (.claude/rules/)
- Supplements CLAUDE.md (does NOT replace it)
- All `.md` files in `rules/` are auto-discovered and loaded recursively
- Loading order: User-level rules (`~/.claude/rules/`) then Project-level (`./.claude/rules/`)
- Supports YAML frontmatter with `globs` field for conditional loading
- Path-specific example: `globs: ["src/api/**/*.ts"]` only loads when working with those files
- **Known bug**: Official docs reference `paths` field but it is broken in user-level rules (~/.claude/rules/). Use `globs` instead (GitHub #17204, #21858)
- Rules without `globs` frontmatter are loaded globally (same as CLAUDE.md content)
- Survives compaction (re-injected automatically, same as CLAUDE.md)

## Skill L1 Budget
- Formula: `max(context_window_tokens * 2% * 4, 16000)` characters
- Override: `SLASH_COMMAND_TOOL_CHAR_BUDGET` env var
- Our setting: 32000 chars (in settings.json)
- Skills with `disable-model-invocation: true` are EXCLUDED from budget
- If budget exceeded: skills excluded likely FIFO (no priority/weight mechanism exists)
- Excluded skills still invocable via /slash-command by user (just invisible to AI)
- Our budget usage: 35 skills, 4 have disable-model-invocation:true, so ~31 L1s loaded
- Post-optimization (v10.3+): all 31 auto-loaded descriptions ≤1024 chars → zero truncation

## Skill Invocation Flow
1. Claude sees Skill tool with all eligible L1 descriptions (budget-constrained)
2. Semantic matching: user request mapped to skill description
3. Claude calls Skill tool with skill name + arguments
4. L2 body loaded into context (replaces L1 for that execution turn)
5. `$ARGUMENTS` substituted in L2 body
6. Dynamic context injection (`!backtick-commands`) executed
7. Skill executes (only ONE skill active at a time)
8. After completion: L2 body removed, L1 description remains for future turns

## Agent Spawning Flow
1. Lead calls Task tool with `subagent_type` parameter
2. Agent lookup order: project agents (.claude/agents/) > user agents (~/.claude/agents/) > plugin agents > built-in agents
3. Agent receives: agent .md body (as system prompt) + CLAUDE.md chain + task prompt
4. Agent does NOT receive: parent conversation history, parent skill context
5. If agent has `skills` field: FULL skill content (L1+L2) preloaded at startup
6. If agent has `memory` field: MEMORY.md first 200 lines auto-loaded into system prompt
7. SubagentStart hook fires after spawn (can inject additionalContext)
8. Agent runs independently until maxTurns or task completion

## Compaction Behavior
1. Triggered: auto (context ~80% full) or manual (/compact)
2. PreCompact hook fires (can save state, inject warnings)
3. Conversation summarized by CC, old tool outputs cleared
4. CLAUDE.md chain re-injected automatically
5. Skill L1 descriptions re-injected automatically
6. SessionStart hook fires with `compact` matcher
7. Fresh context with ~30-50% capacity recovered
- Compaction buffer: ~33K tokens reserved (reduced from 45K in earlier versions)
- Compaction does NOT trigger at exact threshold — actual trigger may vary ±5%
8. Active teammates NOT notified of parent compaction (BUG-004)

## Hook Context Injection
- `hookSpecificOutput.additionalContext`: injected as system-level context
- Supported on all hook events that return output
- Multiple hooks' additionalContext values concatenated (order: declaration order)
- NOT visible in conversation transcript (system-level injection)
- Survives the current turn only (not persisted across turns)

## additionalContext Lifecycle (verified 2026-02-14)
- Scope: SINGLE TURN only (per hook invocation)
- NOT visible to spawned subagents (unless injected via SubagentStart hook)
- Does NOT survive compaction (SessionStart hook output has known bug: not re-injected after compact)
- Multiple hooks in same turn: values concatenated in declaration order
- Practical size: ~2-8KB observed, no hard documented limit
- Use MEMORY.md for cross-session persistence (additionalContext is ephemeral)

## Context Budget Estimation
- Total context: model-dependent (Opus 4.6 = 200K tokens)
- CLAUDE.md: persistent (~200-500 tokens typical)
- Skill L1 aggregate: persistent (~3000-8000 tokens depending on count)
- Agent L1 aggregate: persistent in Task tool definition (~1500-3000 tokens)
- Conversation history: grows per turn, cleared on compaction
- Tool outputs: largest consumer, cleared on compaction

## Context Budget Environment Variables (verified 2026-02-15)

| Variable | Default | Range/Values | Description |
|----------|---------|-------------|-------------|
| `CLAUDE_CODE_MAX_OUTPUT_TOKENS` | 32000 | max 128000 (Opus 4.6) | Max output tokens per response (API max 128K, CC runtime caps at 64K) |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | ~95% | 1-100 | Compaction trigger threshold percentage |
| `MAX_THINKING_TOKENS` | 31999 | 0 to disable | Thinking budget (legacy, see EFFORT_LEVEL) |
| `CLAUDE_CODE_EFFORT_LEVEL` | high | low/medium/high/max | Opus 4.6 thinking depth (replaces MAX_THINKING_TOKENS) |
| `CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS` | (model default) | number | File read token limit override |
| `MAX_MCP_OUTPUT_TOKENS` | 25000 | number (warns at 10000) | MCP tool output limit |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | dynamic | number | Skill L1 total char budget override |

### SLASH_COMMAND_TOOL_CHAR_BUDGET Dynamic Scaling
- Formula: `max(context_window_tokens * 2% * 4, 16000)` characters
- Fallback: 16000 chars (when dynamic scaling is insufficient)
- Override: set env var explicitly (we use 32000 in settings.json)
- Opus 4.6 (200K context): dynamic default = `200000 * 0.02 * 4 = 16000` chars → our 32000 override active

### Agent Context Isolation Environment Variables
- `CLAUDE_CODE_TEAM_NAME`: auto-set for teammates (identifies team membership)
- `CLAUDE_CODE_PLAN_MODE_REQUIRED`: auto-set when agent spawned with `mode: "plan"` (plan approval flow)
- `CLAUDE_CODE_SUBAGENT_MODEL`: override model for spawned subagents

## Critical Constraints
- `context: fork` forks subagent with skill L2 as task (agent .md body preserved as system prompt)
- Agent `skills` field preloads FULL content (L1+L2), not just descriptions (context expensive)
- Skill description > 1024 chars truncated (METHODOLOGY section usually lost first)
- Only ONE skill active at a time (no parallel skill execution within same agent)
- `$ARGUMENTS` works in skill body only, NOT in frontmatter
- Agent body is isolated: no access to Lead's conversation, skills, or other agents' context
- MEMORY.md 200-line limit: lines 201+ silently truncated in agent system prompt
- Compaction buffer: ~33K tokens reserved (hardcoded, not configurable)

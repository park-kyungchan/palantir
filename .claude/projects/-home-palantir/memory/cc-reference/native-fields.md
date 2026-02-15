# CC Native Fields Reference
<!-- Last verified: 2026-02-15 via claude-code-guide, 128K output + effort level + field freeze noted 2026-02-15 -->
<!-- Update policy: Re-verify after CC version updates -->

## Skill Frontmatter Fields (SKILL.md)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | no | directory name | Lowercase, numbers, hyphens. Max 64 chars |
| description | string | recommended | none | L1 routing intelligence. Max 1024 chars. Multi-line via YAML `\|` |
| argument-hint | string | no | none | Shown in autocomplete. E.g., `[topic]`, `[file] [format]` |
| user-invocable | boolean | no | true | If false, hidden from `/` menu. Claude can still auto-invoke |
| disable-model-invocation | boolean | no | false | If true, description NOT loaded into context. User-only |
| allowed-tools | list | no | all | Restricts tools available during skill execution |
| model | enum | no | inherit | Values: sonnet, opus, haiku, inherit |
| context | enum | no | none | Values: fork. Forks subagent with skill L2 as task prompt |
| agent | string | no | general-purpose | Which subagent type when context=fork |
| hooks | object | no | none | Skill-scoped hooks (PreToolUse, PostToolUse, etc.) |

### Output Token Limits (verified 2026-02-15)
- Opus 4.6: max 128K output tokens (`CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000`)
- Default: 32K output tokens if not overridden
- `CLAUDE_CODE_EFFORT_LEVEL` (low/medium/high/max) replaces `MAX_THINKING_TOKENS` for Opus 4.6

### Shell Preprocessing in Skills
- Skills support `` !`command` `` syntax in body (below `---`)
- Commands execute at load time, output replaces placeholder
- See arguments-substitution.md for full details

### Field Freeze Note (2026-02-15)
- No NEW frontmatter fields introduced since Feb 2026
- All fields listed below remain current and verified

### Non-Native Fields (Silently Ignored)
- input_schema, confirm, working_dir, timeout, env
- Any custom fields (routing, meta_cognition, ontology_lens)
- Custom keys in frontmatter are parsed by YAML but NOT consumed by CC runtime

### Flag Combinations

| disable-model-invocation | user-invocable | Result |
|--------------------------|----------------|--------|
| false (default) | true (default) | Claude + user can both invoke |
| true | true | User-only (Claude completely blocked, L1 not loaded) |
| false | false | Claude-only (hidden from / menu) |
| true | false | Dead skill (nobody can invoke) |

### Our Usage Pattern
- Pipeline entry skills (brainstorm, delivery, task-management): `disable-model-invocation: true` + `user-invocable: true`
- Homeostasis skills (manage-infra, manage-skills): `disable-model-invocation: false` (Claude auto-invokes)
- All 35 skills use: name, description, user-invocable, disable-model-invocation
- 7 skills use: argument-hint (brainstorm, delivery, resume, self-improve, task-management, manage-codebase, pipeline-resume)
- 0 skills use: context, agent, allowed-tools, model, hooks (all routing done via Lead)

### Semantic Routing Mechanics (2026-02-14 delta)
- Claude uses pure transformer reasoning for skill selection (not keyword matching or embeddings)
- All auto-loaded skill descriptions visible to Lead every request as part of Skill tool definition
- Skills with `disable-model-invocation: true` completely invisible to Lead (user /slash-command only)
- "Use when:" trigger language improves activation for user-facing skills
- Our WHEN: field serves same purpose for pipeline routing (Lead reads as ordering metadata)
- Excluded skills (budget overflow) still invocable via /slash-command by user
- No skill priority/weight mechanism exists — exclusion likely FIFO when budget exceeded

## Agent Frontmatter Fields (.claude/agents/*.md)

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| name | string | yes | none | Agent identifier for subagent_type matching |
| description | string | yes | none | L1 profile. Loaded in Task tool definition |
| tools | list | no | all | Tool allowlist (explicit list = ONLY these tools) |
| disallowedTools | list | no | none | Tool denylist (block specific tools) |
| model | enum | no | inherit | Values: sonnet, opus, haiku. Omit to inherit from parent. Aliases point to latest (e.g., haiku = Haiku 4.5). Per-agent cost optimization |
| permissionMode | enum | no | default | Values: default, acceptEdits, delegate, dontAsk, bypassPermissions, plan |
| maxTurns | number | no | unlimited | One turn = one agentic loop iteration (multiple tool calls per turn) |
| skills | list | no | none | Array of skill names. Full skill content (L1+L2) injected at agent startup. Does NOT share L1 budget -- uses agent's own context window. Useful for specialized domain knowledge |
| mcpServers | list | no | none | MCP server access configuration |
| hooks | object | no | none | Agent-scoped hooks (cleaned up when agent finishes) |
| memory | enum | no | none | Values: user (~/.claude/agent-memory/), project (.claude/agent-memory/), local (.claude/agent-memory-local/) |
| color | string | no | none | UI color coding |

### permissionMode Details

| Value | Behavior |
|-------|----------|
| default | Normal permission flow (inherits project settings) |
| acceptEdits | Auto-accept file edits, still ask for Bash |
| delegate | Delegate to parent's permission settings |
| dontAsk | Auto-accept everything except dangerous commands |
| bypassPermissions | Skip all permission checks (requires flag) |
| plan | Read-only + plan-only mode. WARNING: blocks MCP tools (BUG-001) |

### tools vs disallowedTools
- `tools` = allowlist (ONLY listed tools work). If omitted, all tools available
- `disallowedTools` = denylist (block specific tools). Rest remain available
- If both specified: tools takes precedence, disallowedTools ignored
- Tool names: exact match against CC tool registry (Read, Write, Edit, Glob, Grep, Bash, Task, TaskCreate, TaskUpdate, TaskGet, TaskList, AskUserQuestion, WebSearch, WebFetch, plus MCP tool names)

### Our Usage Pattern
- All 6 agents use: name, description, tools (explicit allowlist), maxTurns
- 4 agents use: memory: project (analyst, researcher, implementer, infra-implementer). 2 agents use: memory: none (delivery-agent, pt-manager)
- 6 agents use: color (visual distinction in tmux)
- 2 agents use: model (pt-manager: `model: haiku`, delivery-agent: `model: haiku` for cost optimization)
- 2 agents use: hooks (implementer, infra-implementer: PostToolUse + PostToolUseFailure for file change tracking)
- 0 agents use: permissionMode, skills, mcpServers, disallowedTools
- 0 agents use: `.claude/rules/*.md` (all rules in CLAUDE.md and skill descriptions currently)
- MCP tools referenced via full name in tools list: `mcp__sequential-thinking__sequentialthinking`

## Modular Rules (.claude/rules/*.md) (discovered 2026-02-14, updated 2026-02-15)

Path-specific rule files with optional frontmatter:
- Location: `.claude/rules/*.md` (recursive auto-discovery)
- Supplements CLAUDE.md (does NOT replace it)
- Frontmatter fields: `paths` (array of glob patterns to scope rule to specific files/dirs)
- Example: `paths: ["src/api/**/*.ts"]` only loads when working with those files
- Rules without `paths` frontmatter are loaded globally (same as CLAUDE.md content)
- Loading order: User-level (`~/.claude/rules/`) then Project-level (`./.claude/rules/`)
- Body: markdown instructions applied when matching files are in context
- No `description` or routing metadata — purely instructional
- Survives compaction (re-injected automatically, same as CLAUDE.md)

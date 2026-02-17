# CC Architecture — Section Descriptions

> **ALWAYS READ** at session start for INFRA work, CC field validation, or user CC questions.
> Like Skill L1 frontmatter, this provides routing intelligence for on-demand file reading.
> Full content (L2) loaded only when WHEN condition matches current task.

**Path**: `.claude/projects/-home-palantir/memory/`

| ID | File | WHEN | Description |
|----|------|------|-------------|
| R1 | `ref_runtime_security.md` | Tool errors, permission blocks, sandbox issues | Agentic loop, 20+ tools, deny→ask→allow, 4 path types, 4 security layers |
| R2 | `ref_config_context.md` | Settings conflicts, context overflow, compaction, **context editing**, **1M context beta** | 5-layer config, CLAUDE.md injection, 200K context, ~95% compaction, session map, context editing beta, server-side compaction API (compact_20260112), 1M context beta |
| R3 | `ref_hooks.md` | Hook creation, debugging, event handling | 14 events, 3 handler types (command/prompt/agent), I/O contract, exit codes, 6 scopes |
| R4 | `ref_skills.md` | Skill field validation, invocation issues, routing | Frontmatter fields, $ARGUMENTS, shell preprocessing, L1 budget, disambiguation, Skills API (REST CRUD), enterprise governance, agentskills.io spec, 500-line body limit |
| R5 | `ref_agents.md` | Agent field validation, spawning, subagent limits | Agent fields, permissionMode, memory config, subagent comparison, 30K output cap, Claude Agent SDK (renamed), memory/hooks/skills agent fields, Task(agent_type) restriction, delegate/dontAsk modes |
| R6 | `ref_teams.md` | Agent Teams coordination, task sharing | File-based channels, inbox messaging, task DAG, heartbeat 5min, known limitations |
| R7 | `ref_model_integration.md` | Model selection, cost tuning, MCP/plugin setup | Effort levels, cost benchmarks, MCP server types, tool search, plugin marketplace, Opus 4.6, adaptive thinking, fast mode 6x, effort parameter GA, 128K output, web search versioned type |
| R8 | `ref_community.md` | External tool evaluation, community patterns | agnix linter, claude-flow, superpowers, 10 post-Opus 4.6 community tools |
| R9 | `ref_analytics.md` | Monitoring, analytics, cost tracking, OTel | CC Analytics API, Usage & Cost API, OTel metrics/events, Admin API overview |

## Routing Shortcuts

| Task | Read Order |
|------|-----------|
| INFRA field validation | R4 (skills) → R5 (agents) → R3 (hooks) |
| Permission/sandbox error | R1 (security section) |
| Context overflow / compaction | R2 (context section) |
| Hook failure diagnosis | R3 → R2 (hook context injection) |
| Cost optimization | R7 + R9 (model/cost + analytics) |
| Dashboard/monitoring setup | R9 (analytics) |
| Context management API | R2 (config + context editing) |
| Agent Teams debugging | R6 → R2 (task sharing + context) |
| User CC architecture question | Relevant R-file, explain from reference |
| Gap not covered | Spawn claude-code-guide agent |

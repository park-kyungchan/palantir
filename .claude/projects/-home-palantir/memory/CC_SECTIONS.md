# CC Architecture — Section Descriptions

> **ALWAYS READ** at session start for INFRA work, CC field validation, or user CC questions.
> Like Skill L1 frontmatter, this provides routing intelligence for on-demand file reading.
> Full content (L2) loaded only when WHEN condition matches current task.

**Path**: `.claude/projects/-home-palantir/memory/`

| ID | File | WHEN | Description |
|----|------|------|-------------|
| R1 | `ref_runtime_security.md` | Tool errors, permission blocks, sandbox issues | Agentic loop, 20+ tools, deny→ask→allow, 4 path types, 4 security layers |
| R2 | `ref_config_context.md` | Settings conflicts, context overflow, compaction, **rules/ directory**, **complete settings reference** | 5-layer config, CLAUDE.md injection, rules/ conditional paths, 33+ settings fields, 6 managed-only fields, 25+ env vars, 200K context, ~95% compaction, session map, context editing beta, BUG-005 (MEMORY.md dual injection) |
| R3 | `ref_hooks.md` | Hook creation, debugging, event handling | 14 events, 3 handler types (command/prompt/agent), I/O contract, exit codes, 6 scopes |
| R4 | `ref_skills.md` | Skill field validation, invocation issues, routing | Frontmatter fields, $ARGUMENTS, shell preprocessing, L1 budget (drop order opaque), disambiguation, Skills API, agentskills.io spec, 500-line soft limit, **context:fork FIXED (CC 2.1)**, non-native fields (metadata/compatibility) |
| R5 | `ref_agents.md` | Agent field validation, spawning, subagent limits | Agent fields, permissionMode, memory config (auto-adds Read/Write/Edit), subagent comparison, 30K output cap, hooks augment globals, BUG-005 (MEMORY.md dual injection), Stop→SubagentStop confirmed |
| R6 | `ref_teams.md` | File-based coordination, Task API patterns, Work Directory setup | Task API (TaskCreate/TaskUpdate/TaskGet), Work Directory conventions, CLAUDE_CODE_TASK_LIST_ID cross-session sharing, task DAG with file-lock concurrency, micro-signal handoff patterns |
| R7 | `ref_model_integration.md` | Model selection, cost tuning, MCP/plugin setup, **commands/ legacy** | Effort levels, cost benchmarks, MCP server types, tool search, **plugin manifest/LSP/marketplace/lifecycle**, commands/ vs skills/, Opus 4.6, Sonnet 4.6, fast mode 6x, 128K output |
| R8 | `ref_community.md` | External tool evaluation, community patterns | agnix linter, claude-flow, superpowers, 10 post-Opus 4.6 community tools |

## Routing Shortcuts

| Task | Read Order |
|------|-----------|
| INFRA field validation | R4 (skills) → R5 (agents) → R3 (hooks) |
| Permission/sandbox error | R1 (security section) |
| Context overflow / compaction | R2 (context section) |
| Hook failure diagnosis | R3 → R2 (hook context injection) |
| Cost optimization | R7 (model/cost) |
| Context management API | R2 (config + context editing) |
| Task API / Work Directory setup | R6 (coordination patterns) |
| User CC architecture question | Relevant R-file, explain from reference |
| Plugin/marketplace setup | R7 (plugin manifest, lifecycle, LSP) |
| Rules/conditional loading | R2 (rules/ directory, paths frontmatter) |
| Settings field lookup | R2 (complete settings reference table) |
| Gap not covered | Spawn claude-code-guide agent |

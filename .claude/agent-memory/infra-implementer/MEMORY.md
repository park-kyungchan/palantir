# Infra Implementer Memory

## Key Patterns
- Always read target file before editing (Edit tool requirement)
- Use absolute paths only (agent cwd resets between bash calls, and we have no Bash)
- Verify edits by re-reading after modification
- Check cross-references after every change (CLAUDE.md <-> agents <-> skills)

## Reference Locations
- CC native reference: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/`
  - native-fields.md, context-loading.md, hook-events.md, arguments-substitution.md
- Context engineering findings: `/home/palantir/.claude/projects/-home-palantir/memory/context-engineering.md`
- INFRA state: MEMORY.md Current INFRA State section

## Rules Directory
- `/home/palantir/.claude/rules/conventions.md` -- shared agent conventions (no paths: frontmatter = global load)
- Loaded for ALL agents automatically, survives compaction
- When extracting from agent bodies to rules/, verify no YAML frontmatter added to rules file

## Common Pitfalls
- Skill description field max 1024 chars before truncation -- put routing intelligence first
- Non-native frontmatter fields silently ignored by CC (no error, no effect)
- permissionMode: plan blocks MCP tools (BUG-001)
- context: fork on skills replaces agent body -- avoid for safety-critical agents

## CC Reference Cache Updates
- 2026-02-15: RSI Iter 2 -- added agent `model` (aliases to latest), `skills` (uses agent context, not L1 budget)
- 2026-02-15: RSI Iter 2 -- added TaskCompleted/TeammateIdle hook events, agent hook type details
- 2026-02-15: RSI Iter 2 -- added .claude/rules/ directory details (supplements CLAUDE.md, paths glob)
- 2026-02-17: ref_model_integration -- Opus 4.6 spec, effort GA, pricing table, web search, tool token overhead
- 2026-02-17: ref_agents -- Claude Agent SDK rename, built-in Bash agent, AUTOCOMPACT env var, scope priority
- 2026-02-17: Added context editing beta, server-side compaction API, tool token overhead, PTC, tool search to ref_config_context.md + ref_runtime_security.md
- When updating cc-reference, always cross-reference between native-fields.md and context-loading.md for consistency

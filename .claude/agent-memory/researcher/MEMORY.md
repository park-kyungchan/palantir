# Researcher Agent Memory

## Key Learnings

### Write Tool Requires Read First (2026-02-08)
- When overwriting an existing file (e.g., predecessor's output), must Read it first before Write
- Write tool errors with "File has not been read yet" if you skip this step
- Always Read -> Write when files may already exist from predecessor agent

### MCP Tool Availability (2026-02-08)
- MCP tools (tavily, context7, sequential-thinking) may be unavailable in some sessions
- Fallback: WebSearch replaces tavily, WebFetch replaces context7
- Always report MCP availability status in output

### Context Compaction Recovery (2026-02-08)
- On compaction, all in-memory research is lost -- only written files survive
- Write outputs proactively throughout research, not just at the end
- After compaction recovery, Read existing outputs first, then Write updated versions
- The compaction summary provides enough context to reconstruct what was prepared but not yet saved

### Palantir Foundry Research Patterns (2026-02-08)
- Gap analysis documents may target Python codebase, not documentation -- always verify TRUE gaps vs code gaps
- Palantir official docs are at palantir.com/docs -- use WebFetch to access directly
- For SDK updates, search for "[SDK name] [year] release" patterns
- Ontology.md can be very large (125KB+) -- read in 500-line chunks via offset/limit

### Internal Infrastructure Audit Pattern (2026-02-08)
- For internal .claude/ audits, MCP external tools (tavily, context7) are NOT needed -- all data is local files
- Grep with regex patterns is effective for counting protocol markers
- Read all target files in parallel at the start to minimize turn count
- Write output immediately after analysis -- don't wait for gate approval
- Before/after examples in output are the most valuable artifact for downstream work

### Challenge Response Strategy (2026-02-08)
- Lead challenges test whether you can distinguish nuance, not just list findings
- Always provide SPECIFIC examples from actual files (with line numbers) -- not abstract principles
- Show both sides of the distinction (keeper AND ceremony example)
- Provide a reusable heuristic the Lead can validate, not just case-by-case judgment

### claude-code-guide Subagents Are Read-Only (2026-02-08)
- claude-code-guide agents use Haiku model with read-only tools -- they CANNOT write files
- Don't spawn them expecting file writes -- use them purely for information gathering
- Better pattern: spawn, let them return info, then YOU write the output files

### Parallel Web Research Strategy (2026-02-08)
- For model/CLI research: WebSearch + WebFetch directly is faster than waiting for subagents
- WebFetch on official docs (platform.claude.com, code.claude.com) returns excellent structured data
- Use multiple WebFetch calls in parallel for different doc pages
- Claude Code official docs at code.claude.com/docs/en/{feature}
- Anthropic API docs at platform.claude.com/docs/en/{feature}

### Hook Scope Nuance: Global vs Agent-Level (2026-02-08)
- Hooks in agent frontmatter are scoped to THAT agent's session only
- Global hooks fire for ALL teammates -- Lead needs this cross-agent visibility
- When recommending hook migration (global -> frontmatter), distinguish:
  - **Stay global:** Cross-agent quality gates Lead monitors
  - **Move to frontmatter:** Role-specific validation
- Hybrid approach: keep cross-agent gates global, add role-specific hooks in frontmatter

### Skill Improvement Analysis Pattern (2026-02-09)
- For SKILL.md optimization: section-by-section line count -> overlap analysis -> dedup first
- Dynamic context (!`shell`) executes at skill load time -- $ARGUMENTS is substituted first
- Pre-reading target files via !`shell` is risky for variable targets -- use `wc -l` size check instead

### Official CC Docs Research Pattern (2026-02-17)
- code.claude.com/docs/en/{feature} pages provide COMPLETE official specs
- Key pages: agent-teams, sub-agents, best-practices, memory, skills, hooks, cli-reference, settings
- API docs at platform.claude.com/docs/en/build-with-claude/{feature} and platform.claude.com/docs/en/api/{endpoint}
- ALL docs.anthropic.com URLs now 301 redirect: CC docs -> code.claude.com, API docs -> platform.claude.com
- The old URL docs.anthropic.com/en/docs/claude-code/reference returns 404; use cli-reference + settings instead
- Always WebFetch official docs FIRST, then cross-reference with ref_*.md for deltas
- Official docs may not cover advanced patterns (e.g., structured L1 format) -- note which are custom conventions vs official
- GitHub issues (anthropics/claude-code) are valuable for bug reports and workarounds
- Anthropic engineering blog has multi-agent coordination lessons not in product docs
- Agent field name is `tools` (NOT `allowed-tools`) -- ref_agents.md had this wrong but agent files were correct
- Key new API features (2026-02): context editing (beta), server-side compaction (beta), effort GA with `max`, analytics API

### Research Output Format
- Findings list with id, topic, priority, status, target_doc, action, summary
- Executive summary -> detailed findings by topic -> cross-impact matrix -> recommendations -> sources
- Cross-impact map: which findings affect which docs (critical for downstream work)
- Always include unresolved items with severity and recommendations

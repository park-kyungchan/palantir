# Researcher Agent Memory

## Key Learnings

### Write Tool Requires Read First (2026-02-08)
- When overwriting an existing file (e.g., predecessor's L1/L2), must Read it first before Write
- Write tool errors with "File has not been read yet" if you skip this step
- Always Read → Write when files may already exist from predecessor agent

### MCP Tool Availability (2026-02-08)
- MCP tools (tavily, context7, sequential-thinking) may be unavailable in some sessions
- Fallback: WebSearch replaces tavily, WebFetch replaces context7
- Always report MCP availability status in L2 MCP Tools Usage Report

### Context Compaction Recovery (2026-02-08)
- On compaction, all in-memory research is lost — only L1/L2/L3 files survive
- Write L1/L2 proactively throughout research, not just at the end
- After compaction recovery, Read existing L1/L2 first, then Write updated versions
- The compaction summary provides enough context to reconstruct what was prepared but not yet saved

### Palantir Foundry Research Patterns (2026-02-08)
- Gap analysis documents may target Python codebase, not documentation — always verify TRUE gaps vs code gaps
- Palantir official docs are at palantir.com/docs — use WebFetch to access directly
- For SDK updates, search for "[SDK name] [year] release" patterns
- Ontology.md can be very large (125KB+) — read in 500-line chunks via offset/limit

### Internal Infrastructure Audit Pattern (2026-02-08)
- For internal .claude/ audits, MCP external tools (tavily, context7) are NOT needed — all data is local files
- Grep with regex patterns is effective for counting protocol markers: `\[([A-Z_]+)\]`
- Read all target files in parallel at the start to minimize turn count
- Write L1/L2 immediately after analysis — don't wait for gate approval
- Before/after examples in L2 are the most valuable artifact for downstream architect
- Classification heuristic for "keeper vs ceremony": remove marker → check ambiguity → check hook dependency → check if LLM-to-LLM only

### Challenge Response Strategy (2026-02-08)
- Lead challenges test whether you can distinguish nuance, not just list findings
- Always provide SPECIFIC examples from actual files (with line numbers) — not abstract principles
- Show both sides of the distinction (keeper AND ceremony example)
- Provide a reusable heuristic the Lead can validate, not just case-by-case judgment

### Priority Rating Requires Migration Risk Analysis (2026-02-08)
- When rating improvement priorities, consider DESIGN INTENT not just migration risk
- If a feature is explicitly documented as "replacement" for another (e.g., PT replaces GC), the dual-track itself is HIGH priority to resolve — even if migration touches many files
- Quantify the ongoing cognitive load of the dual-track, not just the one-time migration cost
- Lead will challenge medium ratings on items with clear design intent contradictions
- Evidence pattern: cite the exact file+line where replacement intent is stated

### claude-code-guide Subagents Are Read-Only (2026-02-08)
- claude-code-guide agents use Haiku model with read-only tools — they CANNOT write files
- Don't spawn them expecting file writes — use them purely for information gathering
- They get stuck in TeammateIdle loops if hooks check for L1/L2 files (the hook checks the parent agent's directory)
- Better pattern: spawn, let them return info, then YOU write the L1/L2/L3 files

### Parallel Web Research Strategy (2026-02-08)
- For model/CLI research: WebSearch + WebFetch directly is faster than waiting for subagents
- WebFetch on official docs (platform.claude.com, code.claude.com) returns excellent structured data
- Use multiple WebFetch calls in parallel for different doc pages
- Claude Code official docs at code.claude.com/docs/en/{feature}
- Anthropic API docs at platform.claude.com/docs/en/{feature}

### RSIL Analysis Pattern (2026-02-08)
- Cross-reference: feature inventory (docs) × current INFRA files (local) = gap analysis
- Read settings.json, agent .md files, and skill SKILL.md to understand current state
- Categorize opportunities as H/M/L priority based on: effort vs impact + backward compatibility + Layer 2 forward-compat
- Cross-impact matrix in L2 is the most valuable artifact — shows which opportunities affect which files

### Hook Scope Nuance: Global vs Agent-Level (2026-02-08)
- Hooks in agent frontmatter are scoped to THAT agent's session only
- Global hooks (e.g., on-task-completed, on-teammate-idle) fire for ALL teammates — Lead needs this cross-agent visibility
- When recommending hook migration (global → frontmatter), distinguish:
  - **Stay global:** Cross-agent quality gates Lead monitors (L1/L2 existence, task completion checks)
  - **Move to frontmatter:** Role-specific validation (e.g., implementer file ownership, tester test-result checks)
- Hybrid approach: keep cross-agent gates global, add role-specific hooks in frontmatter
- Lead flagged this as a gap in H-3 recommendation — architect should address in Phase 3

### Artifact Signal Analysis Pattern (2026-02-09)
- When researching session artifact structures, use `find` + `wc -l` to build size inventories across ALL sessions
- Gate records are the highest signal-per-token artifact (9-116L YAML, structured)
- L1-index.yaml is second best (26-149L, finding summaries with cross-impact)
- L2/L3 are context-expensive — only read selectively when Tier 1 flags anomalies
- Always quantify artifact sizes across multiple sessions to identify distribution ranges (not just one example)
- The inventory itself becomes evidence for the L2 summary tables

### Ultrathink in Skills — Documentation Contradiction (2026-02-09)
- Skills docs (code.claude.com/docs/en/skills): "To enable extended thinking in a skill, include the word 'ultrathink' anywhere in your skill content"
- Common-workflows docs: "Phrases like 'think', 'ultrathink' are interpreted as regular prompt instructions and don't allocate thinking tokens"
- Resolution: The skills doc is specific to skills context; common-workflows is about user prompts
- Opus 4.6 uses adaptive reasoning with /effort — ultrathink in skills may set max thinking budget
- Always flag contradictions to architect for verification rather than picking one interpretation

### Skill Improvement Analysis Pattern (2026-02-09)
- For SKILL.md optimization: section-by-section line count → overlap analysis → dedup first
- Positive statements + negative counterparts = merge candidates (60% overlap found in /rsil-review)
- Dynamic context (!`shell`) executes at skill load time — $ARGUMENTS is substituted first
- Pre-reading target files via !`shell` is risky for variable targets — use `wc -l` size check instead
- Agent memory integration = read at Dynamic Context + write at terminal phase

### Research Output Format
- L1-index.yaml: findings list with id, topic, priority, status, target_doc, action, summary
- L2-summary.md: executive summary → detailed findings by topic → cross-impact matrix → recommendations → sources → MCP usage
- Cross-impact map: which findings affect which docs (critical for downstream architect)
- Always include unresolved items with severity and recommendations

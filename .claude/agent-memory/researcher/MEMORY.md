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

### Research Output Format
- L1-index.yaml: findings list with id, topic, priority, status, target_doc, action, summary
- L2-summary.md: executive summary → detailed findings by topic → cross-impact matrix → recommendations → sources → MCP usage
- Cross-impact map: which findings affect which docs (critical for downstream architect)
- Always include unresolved items with severity and recommendations

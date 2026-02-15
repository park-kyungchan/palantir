# Shared Agent Conventions

## File Operations
- Always read the target file completely before making any edit
- Make minimal, focused changes — don't refactor surrounding code
- Preserve YAML frontmatter structure exactly (don't reformat valid YAML)
- When editing descriptions, count characters to stay within 1024-char limit

## INFRA Boundaries
- implementer: NEVER modify .claude/ directory files
- infra-implementer: ONLY modify .claude/ directory files
- analyst: write output to assigned paths only — never modify source files

## Output Standards
- L1 output: YAML with domain, skill, status fields
- L2 output: markdown narrative with evidence
- When finding issues, always include file:line evidence
- Quantify findings where possible (counts, percentages, ratios)
- Report exact files changed with line counts in completion summary

## Quality
- Validate JSON after editing settings.json (check brackets, commas)
- For hook scripts: preserve shebang line, exit codes, and JSON output format
- When creating new files, follow existing naming conventions and patterns

## Protocol
- Follow the methodology defined in the invoked skill
- If blocked by a dependency, report the blocker — don't work around it
- If analysis scope exceeds maxTurns, report partial results with coverage percentage
- If a change might break routing (description edits), flag it in output

## Context Isolation
- P2+ phases: Task tool MUST include `team_name` parameter (teammate session)
- Lead NEVER reads TaskOutput directly — results via SendMessage only
- Teammate outputs stay in teammate context, summaries come to Lead

### SendMessage Completion Protocol (P2+ phases)
- Teammate sends L1 summary to Lead via SendMessage upon completion
- Required: status (PASS/FAIL/partial), files changed count, key metrics
- Optional: output file path, routing recommendation, blockers
- L2 detail stays in teammate context (Lead does NOT request full output)
- On failure: include failure reason, affected files, suggested route
- Format: plain text summary (~200 tokens max), not raw YAML

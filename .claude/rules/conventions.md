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
- Teammate writes full L1/L2 result to `/tmp/pipeline/{phase}-{skill}.md`
- Teammate sends micro-signal to Lead via SendMessage:
  `{STATUS}|files:{N}|ref:/tmp/pipeline/{phase}-{skill}.md`
- Required signal fields: status (PASS/FAIL/partial), files count, ref path
- Optional: `route:{next-skill}`, `blocker:{summary}`
- Lead reads ref file ONLY when routing decision needs detail
- On failure: `FAIL|reason:{brief}|ref:/tmp/pipeline/{path}`
- Max signal size: ~50 tokens (keep minimal for Lead context budget)

### Pipeline State Checkpoint (Compaction Recovery)
- Lead writes `/tmp/pipeline-state.md` after each major phase boundary
- Contents: tier, current_phase, completed phases with key routing signals
- PT metadata stores compact phase signals via TaskUpdate (survives session loss)
- On compaction recovery: Read `/tmp/pipeline-state.md` + TaskGet(PT) to restore context
- Checkpoint format: one line per completed phase: `{phase}: {STATUS}|{key_signal}`

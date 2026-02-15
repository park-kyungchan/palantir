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

## Coordinator Pattern (P2, P4, P5)
- Coordinator skills consolidate parallel dimension outputs into tiered format
- L1 index.md: Lead always reads (routing metadata)
- L2 summary.md: Lead reads for routing decisions
- L3 per-dimension files: Passed to downstream teammates via $ARGUMENTS (Lead never reads)
- Indirect bidirectional link: skill-A → coordinator → skill-B is VALID (not a broken link)
- Output path convention: `/tmp/pipeline/{phase}-coordinator/`

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
- Teammate sends micro-signal to Lead via SendMessage

**Signal format**: `{STATUS}|{dimension-metric}|ref:{path}`

**Field ordering** (mandatory then optional):
1. `STATUS`: PASS | FAIL | partial (required)
2. Dimension metric (required, phase-specific — see table)
3. `ref:/tmp/pipeline/{phase}-{skill}.md` (required)
4. `route:{next-skill}` (optional, routing hint)
5. `blocker:{summary}` (optional, FAIL only)

**Dimension-aware metrics by phase**:

| Phase | Metric Key | Example |
|-------|-----------|---------|
| P2 audit | `hotspots:{N}` or `chains:{N}` or `paths:{N}` | `PASS\|hotspots:3\|ref:...` |
| P3 plan | `tasks:{N}` | `PASS\|tasks:8\|ref:...` |
| P4 verify | `verdict:{PASS/FAIL}` | `PASS\|verdict:PASS\|ref:...` |
| P5 orch | `waves:{N}\|tasks:{N}` | `PASS\|waves:3\|tasks:12\|ref:...` |
| P6 exec | `files:{N}` | `PASS\|files:5\|ref:...` |
| P7 verify | `issues:{N}` | `PASS\|issues:0\|ref:...` |
| Homeostasis | `health:{N}` or `findings:{N}` | `PASS\|health:87\|ref:...` |

**Error taxonomy** (FAIL signals):
`FAIL|type:{error-type}|reason:{brief}|ref:{path}`
Error types: `missing-input` | `quality-gate` | `timeout` | `dependency`

- Lead reads ref file ONLY when routing decision needs detail
- Max signal size: ~50 tokens (keep minimal for Lead context budget)

### Pipeline State Checkpoint (Compaction Recovery)
- Lead writes `/tmp/pipeline-state.md` after each major phase boundary
- Contents: tier, current_phase, completed phases with key routing signals
- PT metadata stores compact phase signals via TaskUpdate (survives session loss)
- On compaction recovery: Read `/tmp/pipeline-state.md` + TaskGet(PT) to restore context

**Checkpoint micro-format** (one line per completed phase, pending omitted):
```
tier: {TRIVIAL|STANDARD|COMPLEX}
phase: {current_phase}
---
P0: {STATUS}|reqs:{N}|tier:{confirmed_tier}
P1: {STATUS}|components:{N}|risks:{N}
P2: {STATUS}|hotspots:{N}|chains:{N}
P3: {STATUS}|tasks:{N}
P4: {STATUS}|verdict:{PASS/FAIL}
P5: {STATUS}|waves:{N}|tasks:{N}
P6: {STATUS}|files:{N}
P7: {STATUS}|issues:{N}
P8: {STATUS}|commit:{hash}
```
- Uses same dimension metrics as SendMessage signals for consistency
- Enables Lead to reconstruct full pipeline context after compaction

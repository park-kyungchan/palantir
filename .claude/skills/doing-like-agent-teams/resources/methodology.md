# Doing Like Agent Teams — Detailed Methodology

> On-demand reference. DPS templates, state file format, synthesis DPS, recovery protocol.

## Agent Subdirectory Map

| Agent Profile | Subdirectory | Typical Phases |
|---------------|-------------|----------------|
| analyst | `{DLAT_BASE}/analyst/` | P1-P5, P7 |
| researcher | `{DLAT_BASE}/researcher/` | P2 |
| coordinator | `{DLAT_BASE}/coordinator/` | All (synthesis) |
| implementer | `{DLAT_BASE}/implementer/` | P6 |
| infra-implementer | `{DLAT_BASE}/infra-implementer/` | P6 |
| delivery-agent | `{DLAT_BASE}/delivery-agent/` | P8 |

## Single-Session Adaptation Map

| Agent Teams | Single-Session Equivalent |
|-------------|--------------------------|
| Teammates (team mode) | Background subagents (`run_in_background:true`) — no P2P |
| TeamCreate + task list | Coordinator manages session-local tracking |
| SendMessage (P2P) | File-based handoff via work directory |
| `~/.claude/tasks/{team}/` | `{DLAT_BASE}/` |
| Permanent Task (PT) | `{DLAT_BASE}/state.md` |
| Lead orchestrates | Coordinator subagent orchestrates |
| 4-channel protocol | 2-channel: file write (Ch2) + completion notification (Ch3) |

## Common DPS Header

Every phase DPS starts with this header. Per-phase templates below specify only the delta fields.

```
DLAT_BASE: {base_path}
OUTPUT_PATH: {DLAT_BASE}/{agent_name}/{phase}-{task}-{n}.md
Write complete output to OUTPUT_PATH. Create directory if needed.
Format: YAML L1 header + Markdown L2.
Constraints: maxTurns as specified. model: "sonnet".
```

**Validation**: Before spawning, Lead verifies:
1. `DLAT_BASE` directory exists on disk
2. `OUTPUT_PATH` starts with `DLAT_BASE/`
3. Agent subdirectory exists (create if missing)
If any check fails → create directory first, then spawn.

## Per-Phase DPS Deltas

### P0 Pre-Design
```
Context: [User requirements from $ARGUMENTS]
Task: [brainstorm|validate|feasibility]
OUTPUT_PATH: {DLAT_BASE}/analyst/p0-{task}-{n}.md
Constraints: Read-only analysis. maxTurns: 20.
```

### P1 Design
```
Context: Read {DLAT_BASE}/coordinator/p0-synthesis.md for requirements.
Task: [architecture|interface|risk]
OUTPUT_PATH: {DLAT_BASE}/analyst/p1-{task}-{n}.md
Constraints: Read-only analysis. maxTurns: 20.
```

### P2 Research
```
Context: Read {DLAT_BASE}/coordinator/p1-synthesis.md for architecture decisions.
Task: [codebase|external|audit-static|audit-behavioral|audit-relational|audit-impact]
OUTPUT_PATH: {DLAT_BASE}/{analyst|researcher}/p2-{task}-{n}.md
Constraints: Read-only. Glob→Grep→Read sequence. maxTurns: 25.
```
Note: codebase/audit tasks → `analyst/`, external → `researcher/`.

### P3 Plan
```
Context: Read {DLAT_BASE}/coordinator/p2-synthesis.md
Task: [static|behavioral|relational|impact] dimension plan
OUTPUT_PATH: {DLAT_BASE}/analyst/p3-{task}-{n}.md
Constraints: Read-only. maxTurns: 25.
```

### P4 Plan Verify
```
Context: Read {DLAT_BASE}/analyst/p3-{dimension}-{n}.md + {DLAT_BASE}/coordinator/p2-synthesis.md
Task: Verify {dimension} dimension plan.
OUTPUT_PATH: {DLAT_BASE}/analyst/p4-{task}-{n}.md
Constraints: Analysis only. maxTurns: 20.
```

### P5 Orchestrate
```
Context: Read {DLAT_BASE}/coordinator/p4-synthesis.md
Task: [static|behavioral|relational|impact] orchestration dimension.
OUTPUT_PATH: {DLAT_BASE}/analyst/p5-{task}-{n}.md
Constraints: Analysis only. maxTurns: 20.
```

### P6 Execution
```
Context: Read {DLAT_BASE}/coordinator/p5-synthesis.md
Task: Implement [assigned tasks from plan].
OUTPUT_PATH: {DLAT_BASE}/{implementer|infra-implementer}/p6-{task}-{n}.md (change manifest)
Constraints: Edit only assigned files. maxTurns: 40.
```

### P7 Verify
```
Context: Read {DLAT_BASE}/coordinator/p6-synthesis.md
Task: [structural-content|consistency|quality|cc-feasibility] verification.
OUTPUT_PATH: {DLAT_BASE}/analyst/p7-{task}-{n}.md
Constraints: Read-only scan. maxTurns: 25.
```

### P8 Delivery
```
Context: P7 all-PASS confirmed. Read {DLAT_BASE}/state.md for session history.
Task: Create git commit + archive session to MEMORY.md.
OUTPUT_PATH: {DLAT_BASE}/delivery-agent/p8-delivery-{n}.md
Constraints: User confirmation required before git operations.
```

## Synthesis Subagent DPS

Use when >=3 substantial output files need consolidation:
```
DLAT_BASE: {base_path}
Context: Phase {N} complete. Read these files:
  - {DLAT_BASE}/{agent1}/{file1}
  - {DLAT_BASE}/{agent2}/{file2}
  - {DLAT_BASE}/{agent3}/{file3}
  [... up to 5 files per synthesis subagent]
Task: Unified synthesis — (1) Key findings per file, (2) Cross-file patterns,
  (3) Conflicts/gaps, (4) Recommendation for next phase.
OUTPUT_PATH: {DLAT_BASE}/coordinator/p{N}-synthesis.md
Constraints: Read-only. maxTurns: 15.
```

For >5 files: split into groups of 3-5, spawn multiple synthesis subagents, then one meta-synthesis.

## State File Format

Located at `{DLAT_BASE}/state.md`. All paths relative to DLAT_BASE.

**Creation timing**: Lead creates `state.md` at P0 Step 5, BEFORE forking coordinator. This file's existence serves as the DLAT_BASE initialization gate.

```markdown
# DLAT Session State
session_id: {timestamp}
project_slug: {slug}
base_path: ~/.claude/doing-like-agent-teams/projects/{slug}
started: {ISO date}
current_phase: P{N}

## Phases
- [x] P0 Pre-Design → coordinator/p0-synthesis.md
- [x] P1 Design → coordinator/p1-synthesis.md
- [ ] P2 Research (in progress)

## Active Wave
- Wave 2a: [task descriptions]

## Completed Output Files
- P0/brainstorm: analyst/p0-brainstorm-1.md
- P0/synthesis: coordinator/p0-synthesis.md
- P1/architecture: analyst/p1-architecture-1.md
- P1/synthesis: coordinator/p1-synthesis.md

## Failed Tasks
- (none)

## Escalation Log
- (none)
```

**Update frequency**: After every wave completion. Batch multiple sub-wave completions into a single Write when waves complete within the same coordinator turn.

## Recovery Protocol

After compaction or session restart:
1. Read `{DLAT_BASE}/state.md`
2. Identify `current_phase` and last completed synthesis
3. Verify synthesis files exist: `ls {DLAT_BASE}/coordinator/p*-synthesis.md`
4. Resume from current phase using synthesis files as context
5. Never re-run completed phases

**Cross-session resume**: Same project_slug → read existing state.md → continue.

## Cleanup

After successful P8 delivery, work directory is preserved for audit.
- Archive: `mv {DLAT_BASE} {DLAT_BASE}-archived-{date}`
- Clean: `rm -rf {DLAT_BASE}` (only after confirming git commit)
- Coordinator does NOT auto-delete — human decision.

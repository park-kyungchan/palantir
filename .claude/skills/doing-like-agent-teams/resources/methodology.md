# Doing Like Agent Teams — Detailed Methodology

> On-demand reference. Contains DPS templates per phase, state file format, synthesis subagent DPS, and recovery protocol.

## Per-Phase DPS Templates

### P0 Pre-Design
```
Context: [User requirements from $ARGUMENTS]
Task: [brainstorm|validate|feasibility] — single phase task only.
Constraints: Read-only analysis. maxTurns: 20.
OUTPUT_PATH: /tmp/dlat-p0-{task}-{n}.md
Write complete output to OUTPUT_PATH. Format: YAML L1 header + Markdown L2.
```

### P1 Design
```
Context: P0 synthesis path: [/tmp/dlat-p0-synthesis.md] — read this file for requirements.
Task: [architecture|interface|risk] — single phase task only.
Constraints: Read-only analysis. maxTurns: 20.
OUTPUT_PATH: /tmp/dlat-p1-{task}-{n}.md
Write complete output to OUTPUT_PATH. Format: component list + ADRs.
```

### P2 Research
```
Context: P1 synthesis path: [path] — read for architecture decisions.
Task: [codebase|external|audit-static|audit-behavioral|audit-relational|audit-impact]
Constraints: Read-only. Glob→Grep→Read sequence. maxTurns: 25.
OUTPUT_PATH: /tmp/dlat-p2-{task}-{n}.md
Write findings with file:line references to OUTPUT_PATH.
```

### P3 Plan
```
Context: P2 coordinator synthesis path: [path]
Task: [static|behavioral|relational|impact] dimension plan only.
Constraints: Read-only analysis. maxTurns: 25.
OUTPUT_PATH: /tmp/dlat-p3-{task}-{n}.md
```

### P4 Plan Verify
```
Context: P3 {dimension} plan path: [path] + P2 coordinator output: [path]
Task: Verify {dimension} dimension plan.
Constraints: Analysis only, no modifications. maxTurns: 20.
OUTPUT_PATH: /tmp/dlat-p4-{task}-{n}.md
```

### P5 Orchestrate
```
Context: P4 coordinator output path: [path]
Task: [static|behavioral|relational|impact] orchestration dimension.
Constraints: Analysis only. maxTurns: 20.
OUTPUT_PATH: /tmp/dlat-p5-{task}-{n}.md
```

### P6 Execution
```
Context: P5 coordinator execution plan path: [path]
Task: Implement [assigned tasks from plan].
Constraints: Edit only assigned files. maxTurns: 40.
OUTPUT_PATH: /tmp/dlat-p6-{task}-{n}.md (change manifest)
```

### P7 Verify
```
Context: P6 change manifest path: [path]
Task: [structural-content|consistency|quality|cc-feasibility] verification.
Constraints: Read-only scan. maxTurns: 25.
OUTPUT_PATH: /tmp/dlat-p7-{task}-{n}.md
```

### P8 Delivery
```
Context: P7 all-PASS confirmation. Session state: [/tmp/dlat-state-{session}.md]
Task: Create git commit + archive session to MEMORY.md.
Constraints: User confirmation required before git operations.
OUTPUT_PATH: /tmp/dlat-p8-delivery-{n}.md (commit hash + archive confirmation)
```

## Synthesis Subagent DPS

Use when >3 output files need synthesis (triggers coordinator spawning this):
```
Context: Phase {N} complete. Output files:
  - [path1]
  - [path2]
  - [path3]
  - [path4]
Task: Read all files. Produce unified synthesis covering:
  (1) Key findings per file, (2) Cross-file patterns, (3) Conflicts/gaps,
  (4) Recommendation for next phase.
Constraints: Read-only. maxTurns: 15.
OUTPUT_PATH: /tmp/dlat-p{N}-synthesis.md
```

## State File Format

```markdown
# DLAT Session State
session_id: {timestamp}
started: {ISO date}
current_phase: P{N}

## Phases
- [x] P0 Pre-Design → /tmp/dlat-p0-synthesis.md
- [x] P1 Design → /tmp/dlat-p1-synthesis.md
- [ ] P2 Research (in progress)

## Active Subagents
- Wave 2a: [agentId1, agentId2, agentId3]

## Completed Output Files
- P0/brainstorm: /tmp/dlat-p0-brainstorm-1.md
- P0/validate: /tmp/dlat-p0-validate-1.md
- P0/synthesis: /tmp/dlat-p0-synthesis.md

## Failed Tasks
- (none)

## D12 Escalation Log
- (none)
```

## Recovery Protocol (after compaction)

If coordinator compacts mid-pipeline:
1. Read `/tmp/dlat-state-{session}.md`
2. Identify `current_phase`
3. Check which output files exist (listed in state file)
4. Re-derive context from synthesis files (not raw wave outputs)
5. Continue from current phase

Never re-run completed phases. Resume from synthesis files only.

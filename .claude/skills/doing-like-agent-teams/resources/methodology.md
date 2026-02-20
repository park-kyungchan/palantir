# Doing Like Agent Teams — Detailed Methodology

> On-demand reference. DPS templates, synthesis DPS, recovery protocol.

## Agent Subdirectory Map

| Agent Profile | Subdirectory | Typical Phases |
|---------------|-------------|----------------|
| analyst | `{WORK_DIR}/analyst/` | P1-P5, P7 |
| researcher | `{WORK_DIR}/researcher/` | P2 |
| coordinator | `{WORK_DIR}/coordinator/` | All (synthesis) |
| implementer | `{WORK_DIR}/implementer/` | P6 |
| infra-implementer | `{WORK_DIR}/infra-implementer/` | P6 |
| delivery-agent | `{WORK_DIR}/delivery-agent/` | P8 |

## Single-Session Adaptation Map

| Agent Teams | Single-Session Equivalent |
|-------------|--------------------------|
| Teammates (team mode) | Background subagents (`run_in_background:true`) — no P2P |
| TeamCreate + task list | Coordinator manages session-local tracking |
| SendMessage (P2P) | File-based handoff via work directory |
| `~/.claude/tasks/{team}/` | `{WORK_DIR}/` |
| Permanent Task (PT) | PT description (TaskGet-accessible) |
| Lead orchestrates | Lead orchestrates, coordinator synthesizes (N→1) |
| 4-channel protocol | 2-channel: file write (Ch2) + completion notification (Ch3) |

## Per-Agent DPS Profiles

DPS = task-unique information ONLY. Agent body already defines output format, read-before-edit rules, scope boundaries, and error handling. Duplicating these in DPS wastes agent context window.

### Minimal DPS Templates

**analyst / researcher (read-only agents)**:
```
OBJECTIVE: {1 sentence — what to analyze/research}
READ: {comma-separated full file paths}
OUTPUT: {full output file path}
```

**coordinator (synthesis agent)**:
```
OBJECTIVE: Synthesize P{N} {dimension list} (N-to-1)
INPUT: [{path1}, {path2}, ...]
OUTPUT: {full output file path}
```

**implementer / infra-implementer (edit agents)**:
```
OBJECTIVE: {what to implement/modify}
PLAN:
1. {file_path}: {specific change}
2. {file_path}: {specific change}
OUTPUT: {full output file path}
[CRITERIA: {only for complex multi-section reworks}]
[TEST: {test command, implementer only}]
```

**delivery-agent (terminal agent)**:
```
OBJECTIVE: Deliver pipeline results — {scope summary}
CRITERIA: {what to commit, what to exclude}
```

### Token Targets

| Agent | Max DPS Tokens | Rationale |
|-------|----------------|-----------|
| coordinator | 80 | Reads INPUT files for full context |
| analyst | 100 | Reads files specified in READ |
| researcher | 100 | Uses MCP tools for discovery |
| delivery-agent | 100 | Reads PT for context |
| implementer | 150 | PLAN needs step detail |
| infra-implementer | 200 | PLAN may need old→new values |

## Per-Phase DPS Deltas

### P0 Pre-Design
```
OBJECTIVE: {brainstorm|validate|feasibility} for {project description}
READ: {user requirements file or inline}
OUTPUT: {WORK_DIR}/analyst/p0-{task}-{n}.md
```

### P1 Design
```
OBJECTIVE: {architecture|interface|risk} analysis
READ: {WORK_DIR}/coordinator/p0-synthesis.md
OUTPUT: {WORK_DIR}/analyst/p1-{task}-{n}.md
```

### P2 Research
```
OBJECTIVE: {codebase|external|audit-*} research/audit
READ: {WORK_DIR}/coordinator/p1-synthesis.md
OUTPUT: {WORK_DIR}/{analyst|researcher}/p2-{task}-{n}.md
```

### P3 Plan
```
OBJECTIVE: {static|behavioral|relational|impact} dimension plan
READ: {WORK_DIR}/coordinator/p2-synthesis.md
OUTPUT: {WORK_DIR}/analyst/p3-{task}-{n}.md
```

### P4 Plan Verify
```
OBJECTIVE: Verify {dimension} plan
READ: {WORK_DIR}/analyst/p3-{dimension}-{n}.md, {WORK_DIR}/coordinator/p2-synthesis.md
OUTPUT: {WORK_DIR}/analyst/p4-{task}-{n}.md
```

### P5 Orchestrate
```
OBJECTIVE: {dimension} orchestration
READ: {WORK_DIR}/coordinator/p4-synthesis.md
OUTPUT: {WORK_DIR}/analyst/p5-{task}-{n}.md
```

### P6 Execution
```
OBJECTIVE: Implement {assigned tasks from plan}
PLAN:
1. {file}: {change}
OUTPUT: {WORK_DIR}/{implementer|infra-implementer}/p6-{task}-{n}.md
```

### P7 Verify
```
OBJECTIVE: {structural-content|consistency|quality|cc-feasibility} verification
READ: {WORK_DIR}/coordinator/p6-synthesis.md
OUTPUT: {WORK_DIR}/analyst/p7-{task}-{n}.md
```

### P8 Delivery
```
OBJECTIVE: Deliver pipeline results
CRITERIA: P7 all-PASS confirmed. Commit scope: {file list}
OUTPUT: {WORK_DIR}/delivery-agent/p8-delivery-{n}.md
```

## Synthesis Subagent DPS

Use when >=3 substantial output files need consolidation:
```
OBJECTIVE: Synthesize P{N} outputs (N-to-1)
INPUT: [{path1}, {path2}, ..., {pathN}]
OUTPUT: {WORK_DIR}/coordinator/p{N}-synthesis.md
```

For >5 files: split into groups of 3-5, spawn multiple synthesis subagents, then one meta-synthesis.

## Recovery Protocol

After compaction or session restart:
1. `TaskGet(PT)` — read PT description for pipeline state
2. Identify current_phase and completed phases from PT
3. Verify synthesis files exist: `ls {WORK_DIR}/coordinator/p*-synthesis.md`
4. Resume from current phase using synthesis files as context
5. Never re-run completed phases

**Cross-session resume**: Same TASK_LIST_ID → `TaskGet(PT)` → continue from last phase.

## Cleanup

After successful P8 delivery, work directory is preserved for audit.
- Archive: `mv {WORK_DIR} {WORK_DIR}-archived-{date}`
- Clean: `rm -rf {WORK_DIR}` (only after confirming git commit)
- Coordinator does NOT auto-delete — human decision.

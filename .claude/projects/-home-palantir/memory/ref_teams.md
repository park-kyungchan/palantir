# File-Based Coordination & Task API

> Updated: 2026-02-20 (v14 single-session architecture)
> Previously: Agent Teams reference. Retained filename for CC_SECTIONS.md link compatibility.

---

## 1. Overview

In v14 single-session architecture, all coordination is file-based:
- **Lead** spawns subagents via Task tool (`run_in_background:true`, `context:fork`, `model:sonnet`)
- **Subagents** write output to Work Directory files
- **Lead** reads micro-signals (Ch3) for orchestration decisions; reads Ch2 files only for ENFORCE

There is no P2P messaging, no inbox, no TeamCreate. All coordination is Task API + file I/O.

---

## 2. Task API Reference

### TaskCreate
```json
{
  "title": "Short task name",
  "description": "Full context for subagent",
  "status": "pending",
  "blocked_by": []
}
```

### TaskUpdate
```json
{
  "id": "task-id",
  "status": "in_progress | completed | failed",
  "metadata": { "key": "value" }
}
```

### TaskGet
```
TaskGet [PERMANENT]   → retrieves PT (Permanent Task) by keyword match
TaskGet <id>          → retrieves specific task
```

### TaskList
Returns all tasks for the current task list. Use for OBSERVE mode.

### Dependency Tracking (DAG)

Tasks support `blocked_by` for dependency ordering:
- `blocked_by: [task-id]` → task stays pending until blocker completes
- Bidirectional auto-sync: `addBlockedBy`/`addBlocks` both update the DAG
- Completing a blocker does NOT auto-remove it from `blocked_by` (field remains, status gates execution)

**Known issue (ISS-002)**: TaskGet shows raw `blocked_by` (includes completed), but TaskList filters correctly.

---

## 3. Work Directory Convention

Each pipeline uses a persistent Work Directory for file-based output:

```
~/.claude/doing-like-agent-teams/projects/{pipeline-name}/
├── exec/
│   ├── t1-output.md       # Subagent T1 output
│   ├── t2-output.md       # Subagent T2 output
│   └── coordinator.md     # Coordinator synthesis
└── session-summary.md     # Phase signals (compaction recovery)
```

**Pattern**: DPS specifies output path → subagent writes → sends micro-signal → Lead reads path.

---

## 4. Two-Channel Handoff Protocol [D17]

| Channel | Content | Who Reads |
|---------|---------|-----------|
| Ch2 (files) | Full output, evidence, analysis | Consumer subagents (via file path in DPS) |
| Ch3 (micro-signals) | PASS/FAIL + key findings (~50-100 tokens) | Lead (OBSERVE/ENFORCE) |

Lead accumulates ONLY Ch3 micro-signals. Reads Ch2 only when ENFORCE requires verification.
**Anti-pattern**: Lead reading full subagent output and re-embedding in next DPS = Data Relay Tax.

### Micro-Signal Format (Ch3)

```
STATUS: PASS | FAIL | PARTIAL
KEY: [one-line finding]
OUTPUT: /path/to/output/file.md
```

---

## 5. Cross-Session Task Sharing

`CLAUDE_CODE_TASK_LIST_ID` in settings.json `env` block enables shared task list across independent sessions:

```json
"env": {
  "CLAUDE_CODE_TASK_LIST_ID": "my-project"
}
```

Use for orchestrator + validator session pattern (different terminals, same task list).

---

## 6. Permanent Task (PT)

Single source of truth for the active pipeline:
- **Create**: P0 pipeline start via `pt-manager` agent
- **Read**: `TaskGet [PERMANENT]` — subagents call at spawn for project context. Lead calls after auto-compact for compaction recovery.
- **Update**: Each phase completion writes to PT metadata (Read-Merge-Write pattern)
- **Complete**: Only at final git commit (P8 delivery)

**Key PT metadata fields**:
```json
{
  "tier": "TRIVIAL|STANDARD|COMPLEX",
  "phase_signals": { "P0": "PASS", "P6": "..." },
  "iterations": { "skill_name": 1 },
  "escalations": { "skill_name": "L1|reason" },
  "user_directives": [],
  "thinking_insights": []
}
```

**Compaction recovery**: After auto-compact, Lead calls `TaskGet(PT)` to restore full pipeline context.

---

## 7. Known Task API Issues

| ID | Severity | Issue | Mitigation |
|----|----------|-------|-----------|
| ISS-001 | HIGH | Completed task files may auto-delete from disk (trigger unknown) | Use Team scope always; store results in Work Directory |
| ISS-002 | MED | TaskGet shows raw blockedBy (includes completed); TaskList filters correctly | Use TaskList for dependency checking |
| ISS-003 | HIGH | Task orphaning on context clear | Always use consistent task list ID |
| ISS-004 | LOW | highwatermark can be stale vs actual max ID | Don't rely on highwatermark for sequencing |

---

## 8. Historical: Agent Teams (v7–v13)

Prior to v14, the system used Agent Teams (multi-session tmux):
- **TeamCreate** → teammates spawned in tmux panes
- **SendMessage** → inbox-based P2P messaging
- **TeammateIdle** hook → notified lead when teammate went idle
- File structure: `~/.claude/teams/{team-name}/inboxes/*.json` + `~/.claude/tasks/{team-name}/*.json`

**Removed in v14**: TeamCreate, SendMessage, spawn (teammate), broadcast, requestShutdown, approveShutdown, claimTask (teammate self-claim), TeammateIdle hook. All replaced by file-based output + micro-signal pattern.

For historical AT architecture details, see `infrastructure-history.md`.

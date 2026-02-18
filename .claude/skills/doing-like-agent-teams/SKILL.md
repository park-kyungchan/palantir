---
name: doing-like-agent-teams
description: >
  Mirrors Agent Teams pipeline methodology in a single CC session.
  Uses context:fork to isolate coordinator subagent — coordinator runs full
  COMPLEX-tier pipeline (P0→P8) using background subagents instead of teammates.
  Teammates→background subagents (run_in_background:true). TeamCreate/SendMessage→
  file-based coordination (OUTPUT_PATH). PT→session-local task tracking.
  Main context receives synthesis summaries only. Single session ALWAYS
  COMPLEX tier regardless of task size. Quality top priority over speed.
  WHEN: any multi-step work in a single session needing Agent Teams discipline.
context: fork
agent: coordinator
domain: orchestration
input_from: user (task scope + requirements)
output_to: Lead main context (synthesis summary + output file paths)
---

# Doing Like Agent Teams

Mirrors Agent Teams Mode in a single CC session. `context:fork` forks a coordinator subagent that manages the full pipeline. Main context (Lead) receives only final synthesis — all phase management stays isolated in coordinator's context.

**Single session rule**: ALL work treated as COMPLEX tier (P0→P8 full pipeline). No shortcuts to TRIVIAL/STANDARD. Quality over speed.

## Single-Session Adaptation Map

| Agent Teams | Single-Session Equivalent | Constraint |
|-------------|--------------------------|------------|
| Teammates (team mode) | Background subagents (`run_in_background:true`) | No P2P messaging between agents |
| TeamCreate + task list | Session-local task tracking (coordinator manages) | No cross-session persistence |
| SendMessage (P2P) | File-based handoff (OUTPUT_PATH) | Agents write results to files, coordinator reads |
| Permanent Task (PT) | Coordinator maintains state in a session state file | Lost on compaction — save to disk frequently |
| Lead orchestrates | Coordinator subagent orchestrates | Main context sees summaries only |
| 4-channel protocol | 2-channel: file write (Ch2) + completion notification (Ch3) | No PT (Ch1) or P2P signal (Ch4) |

## Execution Flow (context:fork)

```
User invokes skill
  → context:fork creates coordinator subagent
  → Coordinator runs full COMPLEX pipeline:

  P0 Pre-Design: spawn 3 background subagents (brainstorm/validate/feasibility)
    → read outputs → synthesize → proceed

  P1 Design: spawn 3 background subagents (architecture/interface/risk)
    → read outputs → synthesize → proceed

  P2 Research: spawn parallel research subagents
    → read outputs → audit subagents → synthesize → proceed

  P3 Plan: spawn 4 dimension plan subagents (parallel)
    → read outputs → synthesize → proceed

  P4 Plan Verify: spawn 4+1 verify subagents (parallel + coordinator)
    → read outputs → verify → proceed

  P5 Orchestrate: spawn 4+1 orchestrate subagents
    → read outputs → build execution plan → proceed

  P6 Execution: spawn implementer/infra subagents per plan
    → read outputs → proceed

  P7 Verify: spawn verify subagents (structural/consistency/quality/feasibility)
    → read outputs → gate decision → proceed

  P8 Delivery: spawn delivery-agent subagent
    → commit + archive

  Coordinator writes final synthesis to /tmp/session-summary-{ts}.md
  Returns summary path to Lead main context
```

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`
> Full phase protocol details: read `resources/methodology.md`

## Coordinator State File

Coordinator maintains `/tmp/dlat-state-{session}.md` throughout pipeline:
```
Session: {id}
Current phase: P{N}
Wave: {N}
Completed phases: [P0, P1, ...]
Output files: {phase: path}
Failed subagents: []
```
Update after every wave. Survives subagent termination. Enables phase recovery.

> State file format and recovery protocol: read `resources/methodology.md`

## Subagent Dispatch Protocol

For each phase:
1. **Plan**: coordinator lists tasks → assigns agent profiles → names OUTPUT_PATHs
2. **Dispatch**: spawn all independent tasks in parallel (`run_in_background:true`, `model:"sonnet"`)
3. **Collect**: wait for completion notifications → read each OUTPUT_PATH → quality check
4. **Synthesize**: write phase synthesis to state file → proceed to next phase
5. **Gate**: if phase FAIL → apply D12 escalation within coordinator context

**DPS requirement**: Every DPS must include:
```
OUTPUT_PATH: /tmp/dlat-{phase}-{task}-{n}.md
Write your complete output to OUTPUT_PATH before finishing.
```

> DPS templates per phase: read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Wave Capacity

- Max parallel subagents per wave: **5** (context + system limit)
- Phases with >5 tasks: split into sub-waves (wave 1a, 1b, ...)
- Coordinator never reads full subagent output in context — always via OUTPUT_PATH file read
- If >3 output files need synthesis → spawn synthesis subagent with file path list

## Failure Handling

| Failure | Level | Coordinator Action |
|---------|-------|-------------------|
| Subagent empty output | L0 Retry | Re-spawn same DPS |
| Output fails quality gate | L1 Nudge | Re-spawn with corrected DPS + failure reason |
| Subagent OOM / compacted | L2 Respawn | Fresh spawn, narrower scope |
| Phase gate FAIL | L3 Restructure | Revise task decomposition, re-run phase |
| 3+ L2 failures same task | L4 Escalate | Write escalation to state file → return to Lead |

> Escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

- **Skipping phases**: COMPLEX tier requires all P0-P8. No shortcutting to P6 direct.
- **Lead as relay**: Main context reading wave outputs and re-embedding in next DPS. Coordinator handles this.
- **Missing OUTPUT_PATH**: Subagent completes but coordinator cannot find result.
- **Coordinator context bloat**: Coordinator reading 10+ full output files into context. Spawn synthesis subagent instead.
- **No state file**: Coordinator loses pipeline state on compaction. Write state after every wave.
- **Same-file parallel edit**: Two subagents assigned to same file → corruption.
- **Assuming P2P**: Subagents cannot SendMessage each other. All coordination via coordinator + files.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| User | Task scope, requirements, success criteria | Natural language via $ARGUMENTS |
| Previous partial run | State file | `/tmp/dlat-state-{session}.md` |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| Background subagents | DPS with OUTPUT_PATH | Each phase wave dispatch |
| Lead main context | Session summary path + stats | After P8 delivery |

> D17 Note: Single-session 2-channel only (Ch2 OUTPUT_PATH files, Ch3 completion notification). Ch1 PT and Ch4 P2P not available.

## Quality Gate

- [ ] ALL phases P0-P8 executed (COMPLEX tier, no shortcuts)
- [ ] Coordinator uses context:fork (main context protected)
- [ ] Every DPS includes OUTPUT_PATH
- [ ] State file updated after each wave (compaction resilience)
- [ ] Max 5 parallel subagents per wave
- [ ] Coordinator writes synthesis (not raw file content) to main context return
- [ ] All subagents spawned with `model: "sonnet"`

## Output

### Coordinator returns to main context
```yaml
session_summary:
  phases_completed: [P0, P1, ..., P8]
  total_subagents: N
  failed_tasks: []
  state_file: /tmp/dlat-state-{session}.md
  synthesis_file: /tmp/dlat-synthesis-{session}.md
```

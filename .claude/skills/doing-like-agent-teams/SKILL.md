---
name: doing-like-agent-teams
description: >
  Mirrors Agent Teams pipeline methodology in a single CC session.
  Uses context:fork to isolate coordinator subagent — coordinator runs P1-P5
  after Lead completes P0 (scan + dialogue). Background subagents instead of teammates.
  Teammates→background subagents (run_in_background:true). TeamCreate/SendMessage→
  file-based coordination (persistent work directory). PT→session-local task tracking.
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

Mirrors Agent Teams Mode in a single CC session. `context:fork` forks a coordinator subagent that manages the full pipeline. Main context (Lead) receives only final synthesis.

**Single session rule**: ALL work = COMPLEX tier (P0-P8 full pipeline). No shortcuts.

## Work Directory

```
DLAT_BASE = ~/.claude/doing-like-agent-teams/projects/{project_slug}

{DLAT_BASE}/
  state.md                              # Pipeline state (compaction-resilient)
  {agent_name}/                         # Per-agent output subdirectory
    {phase}-{task}-{n}.md               # Individual task output
  coordinator/                          # Coordinator synthesis outputs
    {phase}-synthesis.md                # Phase synthesis
  session-summary.md                    # Final pipeline summary
```

**Path variables**: `DLAT_BASE`, `OUTPUT_PATH` (`{DLAT_BASE}/{agent_name}/{phase}-{task}-{n}.md`), `STATE_PATH` (`{DLAT_BASE}/state.md`).

**Project slug**: Kebab-case from task description. Enables cross-session resume.

**Directory initialization**: Lead creates dirs via Bash BEFORE forking coordinator (coordinator lacks Bash):
```bash
mkdir -p ~/.claude/doing-like-agent-teams/projects/{slug}/{analyst,researcher,coordinator,implementer,infra-implementer,delivery-agent}
```

## Execution Flow

```
User invokes skill → Lead runs P0 → Lead creates work dirs → context:fork coordinator

Lead (P0 Pre-Design):
  1. Codebase scan (Glob/Grep/Read) → map current state
  2. User dialogue with accurate context
  3. Spawn brainstorm/validate subagents for open requirements
  4. Create work directory structure (Bash)
  5. **P0 Gate — DLAT_BASE Verification** (MANDATORY):
     - Verify: `ls {DLAT_BASE}/state.md` OR `ls {DLAT_BASE}/coordinator/`
     - If NOT exists → BLOCK all spawns until directory is created
     - Write initial `state.md` with project_slug and started timestamp
  6. Fork coordinator with P0 synthesis + DLAT_BASE

Coordinator (P1-P5):
  P1 Design:     3 subagents (architecture/interface/risk) → synthesis
  P2 Research:   parallel research subagents → synthesis
  P3 Plan:       4 dimension subagents → synthesis
  P4 Plan Verify: 4+1 verify subagents → synthesis
  P5 Orchestrate: 4+1 orchestrate subagents → execution plan
  → Returns P5 synthesis path to Lead

Lead (P6-P8):
  P6 Execution:  spawn implementer/infra subagents per P5 plan
  P7 Verify:     spawn verify subagents → gate decision
  P8 Delivery:   spawn delivery-agent → commit + archive
```

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`
> DPS templates + state file format: read `resources/methodology.md`

## Subagent Dispatch Protocol

> All spawns: `run_in_background: true` + `context: "fork"` + `model: "sonnet"`.
> Lead reads ONLY coordinator's final return. Individual subagent outputs NEVER enter Lead's context.

Per phase:
0. **Pre-spawn validation**: Verify `DLAT_BASE` directory exists. If not → execute `mkdir -p` first. Every OUTPUT_PATH in the DPS MUST be an absolute path starting with `{DLAT_BASE}/`.
1. **Plan**: list tasks, assign agent profiles, name OUTPUT_PATHs
2. **Dispatch**: spawn ALL independent tasks in parallel
3. **Collect**: wait for notifications → quality check via OUTPUT_PATH read
   - **<=2 outputs OR all files <=50 lines**: read directly
   - **>=3 outputs with substantial content**: spawn synthesis subagent
     → writes `{DLAT_BASE}/coordinator/{phase}-synthesis.md`
     → coordinator reads synthesis only
4. **Synthesize**: update state.md → proceed
5. **Gate**: FAIL → D12 escalation

**DPS requirement** (every DPS must include):
```
DLAT_BASE: ~/.claude/doing-like-agent-teams/projects/{project_slug}
OUTPUT_PATH: {DLAT_BASE}/{agent_name}/{phase}-{task}-{n}.md
Write your complete output to OUTPUT_PATH before finishing.
```

> DPS templates per phase: read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Wave Capacity

- Max parallel subagents per wave: **5**
- Phases with >5 tasks: split into sub-waves
- Coordinator reads from OUTPUT_PATH files, never from subagent return values
- Synthesis subagent for >=3 substantial outputs per wave

## Failure Handling

| Failure | Level | Action |
|---------|-------|--------|
| Empty output | L0 Retry | Re-spawn same DPS |
| Quality gate fail | L1 Nudge | Re-spawn with correction |
| OOM / compacted | L2 Respawn | Narrower scope |
| Phase gate FAIL | L3 Restructure | Revise decomposition |
| 3+ L2 same task | L4 Escalate | Write to state.md → return to Lead |

> Escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

- **Skipping phases**: COMPLEX tier requires all P0-P8.
- **Lead as relay**: Main context reading wave outputs. Coordinator handles all inter-phase data.
- **Coordinator context bloat**: Reading 10+ output files directly. Use synthesis subagent.
- **No state updates**: State lost on compaction. Update state.md after every wave.
- **Same-file parallel edit**: Two subagents on same file → corruption.
- **Assuming P2P**: Subagents cannot message each other. Coordinator + files only.
- **Writing to /tmp/** [BLOCK]: ALL outputs MUST use DLAT_BASE paths. `/tmp/` is volatile and causes data loss. If a subagent DPS lacks OUTPUT_PATH starting with DLAT_BASE, the DPS is INVALID — do not spawn.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| User | Task scope, requirements | Natural language |
| Previous run | State file | `{DLAT_BASE}/state.md` |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| Subagents | DPS with OUTPUT_PATH | Each wave dispatch |
| Lead main context | Summary path + stats | After P8 |

> 2-channel only: Ch2 (OUTPUT_PATH files) + Ch3 (completion notification).

## Quality Gate

- [ ] ALL phases P0-P8 executed (no shortcuts)
- [ ] DLAT_BASE directory created BEFORE first subagent spawn
- [ ] No outputs written to /tmp/ — all in DLAT_BASE
- [ ] Work dirs created by Lead (Bash) before coordinator fork
- [ ] Every spawn: `run_in_background:true` + `context:fork` + `model:"sonnet"`
- [ ] Every DPS includes DLAT_BASE and OUTPUT_PATH
- [ ] State file updated after each wave
- [ ] Max 5 parallel subagents per wave
- [ ] Synthesis subagent for >=3 substantial outputs per wave
- [ ] Each agent writes ONLY to its own subdirectory

## Output

```yaml
session_summary:
  phases_completed: [P0, P1, ..., P8]
  total_subagents: N
  failed_tasks: []
  work_directory: ~/.claude/doing-like-agent-teams/projects/{project_slug}
  state_file: ~/.claude/doing-like-agent-teams/projects/{project_slug}/state.md
  summary_file: ~/.claude/doing-like-agent-teams/projects/{project_slug}/session-summary.md
```

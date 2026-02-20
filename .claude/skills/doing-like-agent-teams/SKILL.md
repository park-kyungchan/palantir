---
name: doing-like-agent-teams
description: >-
  Single-session pipeline execution methodology. Lead orchestrates P0-P8 phases
  wave-by-wave using background subagents (run_in_background:true + context:fork +
  model:sonnet). File-based coordination via persistent WORK_DIR. PT =
  compaction-resilient context source. Coordinator = synthesis-only (N→1).
  WHEN: any multi-step work requiring structured pipeline execution (P0-P8).
  Reads from: user task scope + requirements (new run) or PT + WORK_DIR (resume).
  Produces: WORK_DIR output tree, PT phase-state updates, session-summary.md.
  On FAIL: D12 escalation (L0 retry → L4 human), record in PT ## Escalations.
  DPS needs: PT_ID + OUTPUT_PATH + phase context. Coordinator: PT_ID + file paths.
  Exclude: embedding output content in DPS — pass OUTPUT_PATH references only.
  Constraint: COMPLEX tier always (P0-P8, no shortcuts). Quality over speed.
user-invocable: true
disable-model-invocation: false
---

# Doing Like Agent Teams

Core pipeline execution methodology for single-session architecture. Lead orchestrates P0-P8 wave-by-wave. `context:fork` is used selectively to spawn a coordinator for N→1 synthesis (not pipeline orchestration). Lead context receives only micro-signals and synthesis file paths.

**Single session rule**: ALL work = COMPLEX tier (P0-P8 full pipeline). No shortcuts.

## Work Directory

```
WORK_DIR = ~/.claude/doing-like-agent-teams/projects/{project_slug}

{WORK_DIR}/
  {agent_name}/                         # Per-agent output subdirectory
    {phase}-{task}-{n}.md               # Individual task output
  coordinator/                          # Coordinator synthesis outputs
    {phase}-synthesis.md                # Phase synthesis
  session-summary.md                    # Final pipeline summary
```

**Path variables**: `WORK_DIR`, `OUTPUT_PATH` (`{WORK_DIR}/{agent_name}/{phase}-{task}-{n}.md`).

**Project slug**: Kebab-case from task description. Enables cross-session resume.

**Directory initialization**: Lead creates dirs via Bash BEFORE forking coordinator (coordinator lacks Bash):
```bash
mkdir -p ~/.claude/doing-like-agent-teams/projects/{slug}/{analyst,researcher,coordinator,implementer,infra-implementer,delivery-agent}
```

## Execution Flow

```
User invokes skill → Lead runs P0 → Lead orchestrates P1-P5 (wave-by-wave) → Lead runs P6-P8

Lead (P0 Pre-Design):
  1. Codebase scan (Glob/Grep/Read) → map current state
  2. User dialogue with accurate context
  3. Spawn brainstorm/validate subagents for open requirements
  4. Create work directory structure (Bash)
  5. **P0 Gate — WORK_DIR Verification** (MANDATORY):
     - Verify: `ls {WORK_DIR}/coordinator/`
     - If NOT exists → BLOCK all spawns until directory is created

Lead (P1-P5) — Deferred Spawn Pattern [CLAUDE.md §3]:
  Per phase:
    1. Lead spawns N analysts in parallel (run_in_background:true + context:fork)
       Each analyst: reads specific files → writes to {WORK_DIR}/analyst/p{N}-{dim}.md
    2. Lead receives N micro-signals (auto-notification)
    3. If N<=2 OR all outputs<=50L: Lead reads directly and decides
       If N>=3 with substantial content: Lead forks coordinator for synthesis
         - Coordinator DPS: PT_ID + N file paths as $ARGS (DPS body ≤200 chars)
         - Coordinator writes: {WORK_DIR}/coordinator/p{N}-synthesis.md
         - Coordinator returns: "{STATUS}|ref:{p{N}-synthesis.md}"
    4. Lead updates PT → next phase

  P1 (Design):    3 analysts [architecture, interface, risk]
  P2 (Research):  ⚠ ALWAYS get canonical skill list via: grep -n "2.0 Phase Definitions" ~/.claude/CLAUDE.md
    Step 1 — evaluation-criteria (MANDATORY FIRST: runs before all other P2 analysts)
    Step 2 — Wave A (parallel): research-codebase, research-external
    Step 3 — Wave B (parallel): audit-static, audit-behavioral, audit-relational, audit-impact
    Step 4 — Synthesis: research-coordinator (N→1, all P2 outputs → p2-synthesis.md)
  P3 (Plan):      4 analysts [plan-static, plan-behavioral, plan-relational, plan-impact]
                  → coordinator synthesis (validate-coordinator equivalent)
  P4 (Plan Verify): 6 analysts [validate-syntactic, validate-semantic,
                    validate-behavioral, validate-consumer, validate-relational,
                    validate-impact] → validate-coordinator → PASS/FAIL gate (max 2×)
  P5 (Orchestrate): 4 analysts [orchestrate-static, orchestrate-behavioral,
                    orchestrate-relational, orchestrate-impact]
                    → orchestrate-coordinator → Lead writes p5-execution-plan.md
                    Writes: {WORK_DIR}/coordinator/p5-execution-plan.md

Lead (P6-P8):
  P6 Execution:  spawn implementer/infra subagents per P5 plan
  P7 Verify:     spawn 6 validate-* analysts in parallel (syntactic, semantic,
                 behavioral, consumer, relational, impact)
                 → collect all 6 micro-signals (PASS and FAIL alike)
                 → spawn validate-coordinator with ALL 6 file paths + conditional Lead D-decisions in DPS
                 → coordinator returns unified verdict → gate decision
                 ⚠ NEVER read individual analyst outputs — FAIL micro-signals go directly to coordinator
  P8 Delivery:   spawn delivery-agent → commit + archive
```

> Phase-aware routing: read `.claude/resources/phase-aware-execution.md`
> DPS templates + work directory format: read `resources/methodology.md`

## Phase-Gated Skill Loading [CRITICAL — Context Engineering]

**Rule**: Read ONLY current phase's SKILL.md L1 frontmatters BEFORE spawning that phase's analysts.
Never load future phase skills until you are at that phase.

**Step 1 — Get canonical skill list for the phase**:
```bash
# Find §2.0 Phase Definitions table dynamically (line-number-independent)
grep -n "2.0 Phase Definitions" ~/.claude/CLAUDE.md
# → returns line N → then: Read ~/.claude/CLAUDE.md offset:N limit:20
```

**Step 2 — Read only current phase's L1 frontmatters**:
```bash
sed -n '/^---$/,/^---$/p' ~/.claude/skills/$skill/SKILL.md | head -20
```
Run this for each skill in the current phase. Stop at `---` (end of frontmatter).

**Why**: Each full SKILL.md L2 body loads ~200 lines into context. Loading P1+P2+P3 skills all at once = ~600+ wasted lines before any work starts. Phase-gated loading caps overhead to ~20 lines per skill per phase.

**P2 Special Rule**: evaluation-criteria MUST be invoked before research-codebase/research-external.
evaluation-criteria L1 states: "First P2 skill invoked before research-codebase and research-external."

## L1-First Routing

Before spawning any agent or loading any skill L2 body:
1. **Read L1 only** (frontmatter or system-reminder) → make routing decision
2. **Load L2** (skill SKILL.md body) ONLY after routing decision is confirmed
3. **Load L3** (resources/*.md) ONLY during execution, not during planning

For skills NOT auto-loaded: read only frontmatter lines (1 to closing `---`) first.
Never load full L2 body to "understand the skill" before deciding to use it.
This prevents context inflation from skills that may not be used.

## Subagent Dispatch Protocol

> All spawns: `run_in_background: true` + `context: "fork"` + `model: "sonnet"`.
> Lead reads ONLY coordinator's final return. Individual subagent outputs NEVER enter Lead's context.

Per phase:
0. **Pre-spawn validation**: Verify `WORK_DIR` directory exists. If not → execute `mkdir -p` first. Every OUTPUT_PATH in the DPS MUST be an absolute path starting with `{WORK_DIR}/`.
1. **Plan**: list tasks, assign agent profiles, name OUTPUT_PATHs
2. **Dispatch**: spawn ALL independent tasks in parallel
3. **Collect**: wait for notifications → quality check via OUTPUT_PATH read
   - **<=2 outputs OR all files <=50 lines**: Lead reads directly
   - **>=3 outputs with substantial content**: Lead forks coordinator (synthesis only)
     → Coordinator DPS: PT_ID + $ARGS=[file_paths] (body ≤200 chars, no content embed)
     → Coordinator writes `{WORK_DIR}/coordinator/{phase}-synthesis.md`
     → Coordinator returns micro-signal → Lead reads synthesis file only if ENFORCE requires
4. **Synthesize**: update PT → proceed
5. **Gate**: FAIL → D12 escalation

## Coordinator DPS Pattern

Coordinator is **synthesis-only** (N→1). Coordinator CANNOT spawn in parallel (CC limitation).
Fork coordinator ONLY when N>=3 substantial analyst outputs need cross-cutting synthesis.

### Per-Agent Minimal DPS Profiles

**Analyst DPS (≤200 char body)**:
```
OBJECTIVE: {task description}
CONTEXT: TaskGet(PT_ID) for project context
INPUT: {files to read}
OUTPUT_PATH: {WORK_DIR}/{agent_name}/{phase}-{task}-{n}.md
Write output to OUTPUT_PATH. Return: "{STATUS}|ref:{OUTPUT_PATH}"
```

**Coordinator DPS (≤200 char body)**:
```
OBJECTIVE: Synthesize P{N} outputs (N-to-1)
CONTEXT: TaskGet(PT_ID) for project context
INPUT: $ARGUMENTS=[{WORK_DIR}/analyst/p{N}-dim1.md, ...]
OUTPUT_PATH: {WORK_DIR}/coordinator/p{N}-synthesis.md
Write synthesis to OUTPUT_PATH. Return: "{STATUS}|ref:{OUTPUT_PATH}"
```

**Why minimal**: Every subagent reads PT directly for full project context.
DPS content duplication = context waste. Pass references, not content.
Lead must NOT embed phase findings in the DPS — subagents read PT directly.

> DPS templates per phase: read `resources/methodology.md`
> DPS construction guide: read `.claude/resources/dps-construction-guide.md`

## Wave Capacity

- Max parallel subagents per wave: **5**
- Phases with >5 tasks: split into sub-waves
- Coordinator reads from OUTPUT_PATH files, never from subagent return values
- Synthesis subagent for >=3 substantial outputs per wave

## Prompt Caching Awareness

### Cache-Aware Lead Discipline
- Between waves: Lead uses ONLY TaskGet/TaskUpdate (metadata operations)
- Do NOT read output files between waves — trust micro-signals
- This keeps Lead context stable → maximizes fork prefix reuse across waves

### Tight Coordinator Spawn
- Spawn coordinator IMMEDIATELY after analyst wave completes
- Do NOT update PT BEFORE coordinator spawn
- This maximizes Sonnet cache reuse from analyst wave

### Model Separation = Cache Separation
- Lead (Opus) and subagents (Sonnet) have separate cache namespaces
- Within a Sonnet wave: subagent 2-N get cache hits on subagent 1's prefix
- This is a structural advantage of background subagent architecture

## PT as Universal Context Source

### For Subagents
Every DPS MUST include: "TaskGet(PT_ID) for project context before starting work."
Subagents read PT to understand:
- What is the overall project goal?
- What phase am I in?
- What were the user's requirements?
- What decisions have been made?

### For Lead (Auto-Compact Recovery)
After compaction: TaskGet(PT) restores:
- All user requirements [REQ-01..N]
- Architecture decisions
- Phase signals (what's done, what's pending)
- Iteration counts and thinking insights

### For Quality
PT is not just tracking — it is the quality backbone.
Every decision, every requirement, every insight is recorded.
This enables consistent direction across auto-compact boundaries.

## Dependency-Aware Micro Task Decomposition

When Lead invokes `/task-management`, decompose pipeline work into dependency-aware micro tasks using the Task API.

### Pattern: Wave-Based Task Graph

```
PT (Permanent Task) = pipeline source of truth
  └── W1 (verify/research — no dependencies)
       ├── T1: verify-A
       ├── T2: verify-B  ──────┐
       └── T3: verify-C  ──┐   │
                            ▼   ▼
  └── W2 (research — blocked by W1)
       ├── T4: research-X (addBlockedBy: [T1, T2, T3])
       └── T5: analyze-Y  (addBlockedBy: [T1, T2])
                            │
                            ▼
  └── W3 (implement — blocked by W2)
       ├── T6: implement-A (addBlockedBy: [T4])
       ├── T7: implement-B (addBlockedBy: [T4])
       └── T8: implement-C (addBlockedBy: [T5])
                            │
                            ▼
  └── W4 (verify — blocked by W3)
       └── T9: final-verify (addBlockedBy: [T6, T7, T8])
                            │
                            ▼
  └── W5 (delivery — blocked by W4)
       └── T10: commit     (addBlockedBy: [T9])
```

### Execution Protocol

1. **Decompose**: Map pipeline phases to waves. Each wave = set of independent tasks.
2. **Register**: `TaskCreate` each task with complete metadata (phase, domain, agent, wave).
3. **Chain**: `TaskUpdate(addBlockedBy)` for cross-wave dependencies. Within a wave = no dependencies.
4. **Dispatch**: Per wave, `TaskUpdate(in_progress)` + spawn subagents in parallel.
5. **Collect**: On completion, `TaskUpdate(completed)` → next wave's tasks auto-unblock.
6. **Gate**: Before advancing wave, verify all prior wave tasks = completed.

### Task Metadata Convention

Each work task includes:
```json
{
  "phase": "P6",
  "domain": "execution",
  "wave": 3,
  "agent": "infra-implementer",
  "parent": "{PT_task_id}"
}
```

### Anti-Patterns
- **No dependencies**: Creating tasks without `addBlockedBy` loses ordering guarantees.
- **Cross-wave parallelism**: Spawning W3 tasks before W2 completes violates dependency graph.
- **Monolithic tasks**: One task per wave defeats the purpose. Decompose to atomic units.

## Failure Handling

| Failure | Level | Action |
|---------|-------|--------|
| Empty output | L0 Retry | Re-spawn same DPS |
| Quality gate fail | L1 Nudge | Re-spawn with correction |
| OOM / compacted | L2 Respawn | Narrower scope |
| Phase gate FAIL | L3 Restructure | Revise decomposition |
| 3+ L2 same task | L4 Escalate | Update PT → return to Lead |

> Escalation ladder: read `.claude/resources/failure-escalation-ladder.md`

## Anti-Patterns

- **Lead as relay**: Lead reading full wave outputs and embedding them in DPS. Pass OUTPUT_PATH references only.
- **Coordinator context bloat**: Reading 10+ output files directly. Use synthesis subagent.
- **No PT updates**: Context lost on compaction. Update PT after every wave.
- **Same-file parallel edit**: Two subagents on same file → corruption.
- **Coordinator as P1-P5 orchestrator** [BLOCK]: Coordinator = synthesis only (N→1).
  Coordinator CANNOT spawn in parallel (CC runtime constraint). Lead handles all wave
  orchestration. Fork coordinator ONLY for synthesis of >=3 substantial outputs.
- **DPS content duplication**: Never embed PT content in coordinator DPS.
  Pass PT_ID reference. Coordinator calls TaskGet(PT_ID) directly.
- **Writing to /tmp/** [BLOCK]: ALL outputs MUST use WORK_DIR paths. `/tmp/` is volatile and causes data loss. If a subagent DPS lacks OUTPUT_PATH starting with WORK_DIR, the DPS is INVALID — do not spawn.
- **Phase-Gated violation** [BLOCK]: Loading P3/P4 skill L2 bodies while executing P2 = pure context waste. Load ONLY current phase's SKILL.md L1 frontmatters (sed head -20). Canonical skill list per phase: CLAUDE.md §2.0 Phase Definitions (grep -n "2.0 Phase Definitions" ~/.claude/CLAUDE.md).
- **P2 skill count underestimate** [BLOCK]: P2 has 8 skills (not 2-3). Spawning only research-codebase + research-external misses all 4 audit dimensions (static/behavioral/relational/impact) and the mandatory research-coordinator synthesis. Always check CLAUDE.md §2.0 Phase Definitions (grep -n "2.0 Phase Definitions" ~/.claude/CLAUDE.md) for authoritative P2 skill list.
- **evaluation-criteria order violation** [BLOCK]: evaluation-criteria MUST run FIRST in P2, before research-codebase and research-external. Its L1 frontmatter explicitly states this ordering requirement. Skipping it or running it in parallel with other P2 analysts violates P2 protocol.
- **Verify FAIL investigation** [BLOCK]: On FAIL micro-signal from any verify analyst (e.g., "FAIL|crits:4/5|failing:CRIT-2"), Lead MUST NOT read the analyst output file to investigate. Spawn validate-coordinator immediately with all N file paths (PASS and FAIL alike). For known CRIT override scenarios, embed CONDITIONAL D-decisions in coordinator DPS: "If dim X FAIL with reason Y → evaluate if Z is acceptable alternative — if yes, treat as CONDITIONAL_PASS." Coordinator reads the file, evaluates actual failure mode, and applies or rejects the override. Root cause: CRIT-level FAIL triggers "investigation instinct" — this is Data Relay Tax in disguise. Trust coordinator to analyze and decide.

## Transitions

### Receives From
| Source | Data | Format |
|--------|------|--------|
| User | Task scope, requirements | Natural language |
| Previous run | PT + work directory | `TaskGet(PT_ID)` + `{WORK_DIR}/` |

### Sends To
| Target | Data | Trigger |
|--------|------|---------|
| Subagents | DPS with OUTPUT_PATH | Each wave dispatch |
| Lead main context | Summary path + stats | After P8 |

> 2-channel only: Ch2 (OUTPUT_PATH files) + Ch3 (completion notification).

## Quality Gate

- [ ] ALL phases P0-P8 executed (no shortcuts)
- [ ] WORK_DIR directory created BEFORE first subagent spawn
- [ ] No outputs written to /tmp/ — all in WORK_DIR
- [ ] Work dirs created by Lead (Bash) before coordinator fork
- [ ] Every spawn: `run_in_background:true` + `context:fork` + `model:"sonnet"`
- [ ] Every DPS includes WORK_DIR and OUTPUT_PATH
- [ ] Every DPS instructs subagent to TaskGet(PT_ID) for project context
- [ ] PT updated after each wave
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
  summary_file: ~/.claude/doing-like-agent-teams/projects/{project_slug}/session-summary.md
```

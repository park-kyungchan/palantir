# Interface Design — PT-Centric Contract + CLAUDE.md §10 Modification

## 1. PT-Centric Interface Contract

### 1.1 Design Principle

**PT = sole cross-phase source of truth.** Every skill reads PT for project context
and writes PT with phase results. GC demoted to session-scoped scratch — holds only
ephemeral execution state that no downstream skill consumes for logic decisions.

**L2 Downstream Handoff = phase-to-phase bridge.** Replaces 9 GC "Phase N Entry
Requirements" sections. Each coordinator's L2 §Downstream Handoff provides structured
context for the next phase. Skills read predecessor L2 files by path, not through GC.

### 1.2 Per-Skill Interface Table

#### Coordinator-Based Skills (5 Pipeline Core)

| Skill | Phase | PT READ Sections | PT WRITE Sections | L2 IN (predecessor) | L2 OUT (successor) |
|-------|-------|-----------------|-------------------|--------------------|--------------------|
| brainstorming-pipeline | P1-3 | User Intent (seed), Constraints | Creates PT-v1: User Intent, Codebase Impact Map, Architecture Decisions, Phase Status, Constraints | None (pipeline start) | research-coord/L2, arch-coord/L2 |
| agent-teams-write-plan | P4 | User Intent, Impact Map, Arch Decisions, Constraints | PT-v{N+1}: Phase Status=P4, Implementation Plan (pointer to L3) | arch-coord/L2 §Downstream Handoff | planning-coord/L2 |
| plan-validation-pipeline | P5 | User Intent, Arch Decisions, Constraints, Impl Plan pointer | PT-v{N+1}: Phase Status=P5, Validation Verdict | planning-coord/L2 §Downstream Handoff | validation-coord/L2 |
| agent-teams-execution-plan | P6 | User Intent, Impact Map, Arch Decisions, Impl Plan, Constraints | PT-v{N+1}: Phase Status=P6, Implementation Results (pointer to L3) | planning-coord/L2, validation-coord/L2 | exec-coord/L2 |
| verification-pipeline | P7-8 | User Intent, Impact Map, Impl Results pointer, Constraints | PT-v{N+1}: Phase Status=P7/P8, Verification Summary | exec-coord/L2 §Downstream Handoff | testing-coord/L2 |

#### Fork-Based Skills (4 Lead-Only + RSIL)

| Skill | Agent | PT READ Sections | PT WRITE Sections | $ARGUMENTS | Dynamic Context |
|-------|-------|-----------------|-------------------|------------|-----------------|
| permanent-tasks | pt-manager | Full PT (for merge) | PT-v{N+1}: Any (user-directed) | Update content/instructions | `!cat` current PT state |
| delivery-pipeline | delivery-agent | All sections (final consolidation) | PT-vFinal: Phase Status=DELIVERED, metrics | Session ID, options | File tree, git log, L2 paths |
| rsil-global | rsil-agent | Phase Status, Constraints | None (findings-only) or PT-v{N+1} if actionable | Target scope, observation budget | .agent/ tree, CLAUDE.md excerpt |
| rsil-review | rsil-agent | Phase Status | PT-v{N+1}: Phase Status with review results | Target file(s), scope | .agent/ tree, recent changes |

### 1.3 PT Section Schema

PT holds lean pointers, not bulk data (per D-012 and CC research §9.3).

```yaml
# PT Structure (PERMANENT Task description)
user_intent: "1-3 sentence goal"
codebase_impact_map:
  modules: [{name, files, dependencies}]
  interfaces: [{from, to, contract}]
  risk_hotspots: [{file, reason}]
architecture_decisions:
  - {id: "AD-N", decision, rationale, status}
phase_status:
  P1: {status: COMPLETE, gate_record: "phase-1/gate-record.yaml"}
  P2: {status: COMPLETE, l2_path: "phase-2/research-coord/L2-summary.md"}
  # ... one entry per phase
constraints:
  - {id: "C-N", constraint, source}
implementation_plan:
  l3_path: "phase-4/planning-coord/L3-full/"
  task_count: N
  file_ownership: [{file, owner}]
implementation_results:
  l3_path: "phase-6/exec-coord/L3-full/"
  summary: "1-2 sentence"
validation_verdict: "PASS | CONDITIONAL_PASS | FAIL"
verification_summary:
  test_count: N
  pass_rate: "N%"
  l2_path: "phase-7/testing-coord/L2-summary.md"
budget_constraints:
  max_spawns: N
  max_phases: N
```

**Key design choice:** `phase_status` entries contain `l2_path` pointers to the
authoritative L2 file for that phase. This is how skills find predecessor output
without GC mediation. The path pattern is deterministic:
`.agent/teams/{session-id}/phase-{N}/{coordinator}/L2-summary.md`

### 1.4 GC Scratch-Only Role

GC retains exactly 3 concerns — all session-scoped, none consumed by downstream skills:

| GC Concern | Content | Why Not PT |
|------------|---------|------------|
| Execution Metrics | spawn_count, spawn_log, timing data | Too verbose; session-specific |
| Gate Records (embedded) | Inline gate summaries | PT holds pointer to gate-record.yaml files |
| Version Marker | `gc_version: N` | Dynamic Context reads this for session discovery |

**What GC loses (9 sections eliminated):**
- Phase 3 Input → brainstorming arch-coord/L2 §Downstream Handoff
- Phase 4 Entry Requirements → arch-coord/L2 §Downstream Handoff
- Phase 5 Validation Targets → planning-coord/L2 §Downstream Handoff
- Phase 6 Entry Conditions → planning-coord/L2 §Downstream Handoff
- Phase 7 Entry Conditions → exec-coord/L2 §Downstream Handoff
- Phase 9 Entry Conditions → testing-coord/L2 §Downstream Handoff
- Research Findings → research-coord/L2 (direct read)
- Codebase Constraints → PT §Constraints (migrated at discovery time)
- Interface Changes → PT §Codebase Impact Map (migrated at execution gate)

**What GC loses (2 sections migrated to PT):**
- Codebase Constraints → merged into PT §Constraints by brainstorming at Gate 2
- Interface Changes → merged into PT §Codebase Impact Map by execution at Gate 6

### 1.5 L2 Downstream Handoff as Phase Bridge

The existing `## Downstream Handoff` section in agent-common-protocol.md (6 categories:
Decisions Made, Risks Identified, Interface Contracts, Constraints, Open Questions,
Artifacts Produced) already provides the mechanism. The redesign makes it the **primary**
phase-to-phase data channel:

**Current flow (GC-mediated):**
```
brainstorming writes "Phase 4 Entry Requirements" to GC-v3
  → write-plan reads GC-v3 §Phase 4 Entry Requirements
```

**New flow (L2-mediated):**
```
brainstorming's arch-coord writes L2 §Downstream Handoff
  → write-plan reads arch-coord/L2 §Downstream Handoff
  → Path provided by PT §phase_status.P3.l2_path
```

**Skill discovery protocol:**
1. Skill reads PT via TaskGet
2. PT §phase_status.P{N-1}.l2_path gives predecessor L2 location
3. Skill reads predecessor L2 §Downstream Handoff for entry context
4. Skill validates entry conditions from §Downstream Handoff content
5. No GC intermediary needed

This eliminates the GC version chain as a data bus. GC no longer carries cross-phase
state — only session-scoped scratch.

### 1.6 PT Versioning Protocol

**Version semantics:** PT-v{N} where N increases monotonically. Not every phase
produces a version bump — only phases that write to PT.

| PT Version | Writer Skill | What Changes |
|------------|-------------|-------------|
| PT-v1 | brainstorming (via /permanent-tasks) | Creates: User Intent, Impact Map, Arch Decisions, Constraints, Phase Status |
| PT-v2 | write-plan (Gate 4) | Adds: Implementation Plan pointer, File Ownership, Phase Status P4=COMPLETE |
| PT-v3 | validation (Gate 5) | Adds: Validation Verdict, Phase Status P5=COMPLETE. Only if CONDITIONAL_PASS adds mitigations to Constraints |
| PT-v4 | execution (Gate 6) | Adds: Implementation Results pointer, Phase Status P6=COMPLETE |
| PT-v5 | verification (Gate 7/8) | Adds: Verification Summary, Phase Status P7/P8=COMPLETE |
| PT-vFinal | delivery (§9.2 Op-1) | Adds: Final metrics, all phases COMPLETE, subject → "DELIVERED" |
| PT-v{N+1} | rsil-review (§R-4) | Updates Phase Status with RSIL results (optional, post-delivery) |
| PT-v{N+1} | permanent-tasks (any time) | Any section update (user-directed, mid-pipeline) |

**Read-Merge-Write protocol (unchanged):** TaskGet → read current → merge changes →
TaskUpdate. PT is always a refined current state, never an append-only log.

**Version tracking:** orchestration-plan.md tracks each coordinator's/agent's confirmed
PT version. When PT bumps, Lead sends context updates to active agents.

### 1.7 Fork Skill Interface Pattern

Fork skills have a fundamentally different interface — no GC, no team context, no
conversation history. Their interface is:

```
$ARGUMENTS (primary input — literal-substituted before fork)
  + Dynamic Context (session state — !commands resolved before fork)
  + PT (cross-phase state — read via TaskGet from fork agent)
  = Complete execution context
```

**Fork-to-PT contract:**
- Fork agent reads PT via TaskGet (sees main session's task list — **assumed, see dependency below**)
- Fork agent writes PT via TaskUpdate (D-10 exception)
- Fork agent writes L1/L2/L3 to its assigned output directory
- Fork agent does NOT write GC (no GC awareness)
- Fork agent does NOT join a team (no SendMessage, no team context)

**CRITICAL DEPENDENCY — Task List Scope (Open Question #3):**
This contract assumes fork agents share the main session's task list, enabling
TaskGet/TaskUpdate on the PERMANENT Task. P2 flagged this as Critical Unknown #3:
"Which task list does fork agent see?" If fork agents see an isolated task list:
- **Impact:** The entire fork-to-PT interface (C-4) breaks. Fork agents cannot
  read or write PT.
- **Fallback:** Dynamic Context injects PT content via `!command` pre-fork
  (read-only). Fork agents return PT changes as output text. Lead applies changes
  manually via TaskUpdate. This preserves functionality but adds Lead overhead
  and eliminates the clean fork-to-PT contract.
- **Resolution:** Requires CC research or empirical test before implementation.
  Flagged for risk-architect-1's open question tracking.

**Fork output handoff:**
- Lead receives fork agent's return value (skill output)
- Lead reads fork agent's L1/L2/L3 for detailed results
- Lead incorporates results into orchestration-plan.md

## 2. CLAUDE.md §10 Modification Design

### 2.1 Current Rule

CLAUDE.md §10 line 364:
```
Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
```

agent-common-protocol.md §Task API lines 74-76:
```
Tasks are read-only for you: use TaskList and TaskGet to check status, find your
assignments, and read the PERMANENT Task for project context. Task creation and
updates are Lead-only (enforced by tool restrictions).
```

### 2.2 Proposed Modification

**CLAUDE.md §10 — Lead responsibilities, first bullet:**

```markdown
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions),
  except for Lead-delegated fork agents (pt-manager, delivery-agent) which receive
  explicit Task API access via their agent .md frontmatter. Fork agents execute
  skills that Lead invokes — they are extensions of Lead's intent, not independent
  actors. Fork Task API access is:
  - pt-manager: TaskCreate + TaskUpdate (creates and maintains PT)
  - delivery-agent: TaskUpdate only (marks PT as DELIVERED)
  - rsil-agent: TaskUpdate only (updates PT Phase Status with review results)
```

**agent-common-protocol.md §Task API — replacement text:**

```markdown
## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your
assignments, and read the PERMANENT Task for project context. Task creation and
updates are Lead-only (enforced by tool restrictions).

**Exception — Fork-context agents:** If your agent .md frontmatter does NOT include
TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access.
This applies only to Lead-delegated fork agents (pt-manager, delivery-agent,
rsil-agent). You are an extension of Lead's intent — use Task API only for the
specific PT operations defined in your skill's instructions.
```

### 2.3 Scope Boundaries

The exception is tightly scoped:

| Boundary | Definition |
|----------|-----------|
| **Who qualifies** | Only agents listed in CLAUDE.md §10 fork agent enumeration (currently: pt-manager, delivery-agent, rsil-agent) |
| **How access is granted** | Agent .md frontmatter omits TaskCreate/TaskUpdate from `disallowedTools`. NL rule in CLAUDE.md §10 documents the policy |
| **What they can do** | pt-manager: Create + Update PT. delivery-agent: Update PT (final status). rsil-agent: Update PT (review results) |
| **What they cannot do** | Create non-PT tasks. Update tasks not identified as PT. Assign tasks to agents. Any task operation outside their skill's defined scope |
| **Enforcement** | Primary: `disallowedTools` frontmatter. Secondary: NL instructions in agent .md body. Tertiary: CLAUDE.md §10 policy statement |

### 2.4 Audit Trail

Fork Task API operations are auditable through:

1. **PostToolUse hook:** Automatically captures all TaskCreate/TaskUpdate calls to events.jsonl
2. **PT version chain:** Each update bumps version, visible in TaskGet
3. **L1/L2 output:** Fork agent writes operation log to its L1-index.yaml
4. **Skill invocation record:** Lead's orchestration-plan.md logs which skill invoked which fork agent

No additional audit mechanism needed — existing observability infrastructure covers
fork agent Task API operations.

### 2.5 Safeguards

| Safeguard | Mechanism |
|-----------|-----------|
| Agent enumeration is explicit | CLAUDE.md §10 lists exactly which agents have exception. Adding a new fork agent requires updating CLAUDE.md §10 |
| Fork agents start clean | No conversation history = no accumulated context drift |
| Lead invokes, agent executes | Fork agents only run when Lead invokes their skill. No autonomous activation |
| Single-responsibility | Each fork agent has exactly one skill's scope. pt-manager only manages PT, delivery-agent only delivers, rsil-agent only reviews |
| Fallback to Lead | If fork agent fails, Lead can perform the operation manually (graceful degradation) |

### 2.6 rsil-agent Note

rsil-agent is shared between rsil-global and rsil-review. Its Task API access
(TaskUpdate only) is needed by rsil-review §R-4 (PT Phase Status update).
rsil-global typically does not update PT but having TaskUpdate available enables
the rare case where actionable findings need to be recorded in PT.

This sharing is safe because:
- Both skills use the same agent with different $ARGUMENTS
- The agent .md defines tool access once, applicable to both invocations
- rsil-global's instructions say "findings-only" — the NL constraint limits behavior
  even though the tool is available

## 3. Interface Dependency Map (RELATE Lens)

### 3.1 Skill-to-PT Dependency

```
                      ┌─────────────────────────────┐
                      │     PERMANENT Task (PT)      │
                      │                              │
                      │  User Intent                 │
                      │  Codebase Impact Map         │
          Creates ──→ │  Architecture Decisions      │ ←── Read by ALL
     (brainstorming)  │  Phase Status                │
                      │  Constraints                 │
                      │  Implementation Plan (ptr)   │
                      │  Implementation Results (ptr)│
                      │  Validation Verdict          │
                      │  Verification Summary        │
                      │  Budget Constraints          │
                      └───────────┬─────────────────┘
                                  │
              ┌───────────────────┼───────────────────┐
              │                   │                     │
         Write (gate)        Write (fork)          Read-only
              │                   │                     │
    ┌─────────┼─────────┐  ┌─────┼──────┐      ┌──────┼──────┐
    │ write   │ execu-  │  │ pt- │ deli-│      │ vali-│ veri-│
    │ -plan   │ tion    │  │ mgr │ very │      │ dation│ fication│
    └─────────┴─────────┘  └─────┴──────┘      └──────┴──────┘
```

### 3.2 L2 Handoff Chain

```
brainstorming ──L2──→ write-plan ──L2──→ validation
                                    │
                                    └──L2──→ execution ──L2──→ verification ──L2──→ delivery
```

Each arrow = coordinator L2 §Downstream Handoff consumed by next skill.
PT §phase_status.P{N}.l2_path provides the discovery path.

### 3.3 Cardinality Analysis

| Relationship | Cardinality | Notes |
|-------------|:-----------:|-------|
| Skill → PT | N:1 | All skills read/write same PT instance |
| Skill → GC | 5:1 | Only 5 pipeline skills touch GC (scratch only) |
| Skill → predecessor L2 | 1:1 or 1:2 | execution reads planning + validation L2 |
| Fork skill → PT | 1:1 | Direct TaskGet/TaskUpdate |
| Fork skill → GC | 0 | No GC interaction |
| Coordinator → workers | 1:N | N varies by category (2-4 workers) |
| PT → L3 detail | 1:N | PT holds pointers to N phase L3 directories |

### 3.4 Coupling Assessment

**Tight coupling (acceptable):**
- All skills depend on PT schema — this is by design (single source of truth)
- L2 Downstream Handoff 6-category structure — standardized by protocol

**Loose coupling (desired):**
- Skills don't depend on GC state from other skills
- Fork skills completely decoupled from team context
- L2 paths are deterministic (no runtime discovery needed beyond PT)

**Coupling risk:**
- PT schema changes affect all 9 skills simultaneously (Big Bang addresses this)
- L2 §Downstream Handoff format changes affect all coordinators (protocol-referenced, single change point)

## 4. Migration Path

### 4.1 GC Section Fate

| Current GC Section | Action | Destination |
|-------------------|--------|------------|
| Scope | ELIMINATE | PT §User Intent (already authoritative) |
| Phase Pipeline Status | KEEP (scratch) | GC scratch — Dynamic Context reads it |
| Constraints | ELIMINATE | PT §Constraints (already authoritative) |
| Decisions Log | ELIMINATE | PT §Architecture Decisions |
| Research Findings | ELIMINATE | research-coord/L2 (direct read) |
| Codebase Constraints | MIGRATE → PT | PT §Constraints (merged at Gate 2) |
| Phase 3 Input | ELIMINATE | research-coord/L2 §Downstream Handoff |
| Architecture Summary | ELIMINATE | arch-coord/L2 (direct read) |
| Architecture Decisions | ELIMINATE | PT §Architecture Decisions |
| Phase N Entry Reqs (×5) | ELIMINATE | predecessor coordinator/L2 §Downstream Handoff |
| Phase 5 Validation Targets | ELIMINATE | planning-coord/L2 §Downstream Handoff |
| Implementation Plan Ref | ELIMINATE | PT §Implementation Plan (pointer) |
| Task Decomposition | ELIMINATE | planning-coord/L3 (direct read) |
| File Ownership Map | ELIMINATE | PT §Implementation Plan.file_ownership |
| Commit Strategy | ELIMINATE | planning-coord/L2 §Downstream Handoff |
| Implementation Results | KEEP (scratch) | GC scratch — summary pointer in PT |
| Interface Changes | MIGRATE → PT | PT §Codebase Impact Map (merged at Gate 6) |
| Gate Records (embedded) | KEEP (scratch) | GC scratch — PT points to gate-record.yaml |
| Verification Results | KEEP (scratch) | GC scratch — summary pointer in PT |

**Result:** 14 unique section types → **3 final steady-state** after all gate transitions:
- 3 kept as scratch (execution metrics, gate record embeds, version marker)
- 2 migrated to PT at specific gates (Codebase Constraints at Gate 2, Interface Changes
  at Gate 6) — these exist transiently in GC until their gate writes them to PT, then
  are not carried forward. The advertised "14→3" count is the final steady-state.
- 9 eliminated via L2 Downstream Handoff or PT pointers

### 4.2 Skill Discovery Protocol Change

**Before:** Skills discover predecessor state via GC version scan
```
§4.1 Discovery: scans for global-context.md with "Phase 3: COMPLETE"
```

**After:** Skills discover predecessor state via PT + L2 path
```
§4.1 Discovery:
  1. TaskGet PT → read §phase_status.P3.status (== COMPLETE)
  2. PT §phase_status.P3.l2_path → read arch-coord/L2 §Downstream Handoff
  3. Validate entry conditions from Downstream Handoff content
```

### 4.3 Simultaneous Deployment (Big Bang)

All changes deploy together:
1. 9 SKILL.md files (new interface sections)
2. CLAUDE.md §10 (fork agent exception)
3. agent-common-protocol.md §Task API (fork exception clause)
4. 3 new agent .md files (pt-manager, delivery-agent, rsil-agent)
5. 8 coordinator .md files (Template B convergence, frontmatter)

No phased migration — GC is either the state bus or it isn't. Partial migration
would create ambiguity about which data source is authoritative.

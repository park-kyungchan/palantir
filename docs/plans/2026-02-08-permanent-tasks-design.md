# PERMANENT Task — Design Document

> **Date:** 2026-02-08
> **Status:** APPROVED (brainstorming complete)
> **Scope:** GC replacement + `/permanent-tasks` skill + infrastructure migration
> **Strategic Context:** Palantir Ontology/Foundry migration fundamental INFRA

---

## Operational Constraints for Lead

These constraints are mandatory for all pipeline execution based on this design.

### Teammate Limits
- **Max 2 teammates spawned concurrently** (local PC memory constraint)
- If more than 2 workstreams exist, execute sequentially — never exceed 2 simultaneous
- Prefer spawning 1 teammate at a time when task complexity is high

### Task Granularity
- **Split tasks maximally.** Every independently verifiable unit of work should be its own task
- A single file change = 1 task (when feasible)
- Never combine unrelated file changes into one task
- Err on the side of too many small tasks rather than too few large ones

### Shift-Left Philosophy
- **Invest 80%+ effort in research, design, and planning phases (Phase 1-5)**
- Execution (Phase 6-8) should be mechanical — all decisions made in pre-execution
- Every teammate must use sequential-thinking for all non-trivial reasoning
- Every teammate must use MCP tools (tavily, context7) for verification
- claude-code-guide research is mandatory before any skill or protocol design

### Token Policy
- **Claude Max X20 subscription — no token conservation.**
- Use maximum context for thorough analysis
- Do not abbreviate, summarize, or skip steps to save tokens
- Full sequential-thinking chains, full MCP research, full DIA protocol execution
- Prefer thoroughness over speed in every trade-off

### Execution Style
- Sequential and thorough — no rushing
- Complete one task fully before starting the next
- Gate evaluations must be exhaustive, not sampled
- Spot-checks become full-checks

---

## 1. Problem Statement

### Current State
The Agent Teams infrastructure uses `global-context.md` (GC) as the shared context document
for pipeline execution. GC has three fundamental limitations:

1. **Pipeline-scoped lifespan** — GC is created per-team and destroyed on TeamDelete.
   Cross-session knowledge is lost.
2. **No user requirement reflection** — GC is set at Phase 1 and has no systematic mechanism
   for incorporating user's dynamic mid-work requirement changes.
3. **No authoritative codebase relationship data** — DIA Layer 3 (LDAP) challenges teammates
   about "interconnection maps" and "ripple traces", but neither Lead nor teammates have a
   reference data source for these relationships. Both sides operate on guesswork.

### Target State
Replace GC with a **PERMANENT Task** — a Task API entity (Task #1) that serves as the
Single Source of Truth for the entire pipeline. It combines user intent, codebase impact
mapping, architecture decisions, and pipeline state into one queryable, updatable document.

### Core Value Proposition
*"When any change happens anywhere in the codebase, Lead can assess its impact across the
ENTIRE codebase by referencing the PERMANENT Task's Codebase Impact Map, and ensure all
affected areas are improved together — not just the directly changed module."*

This is the foundational infrastructure for Palantir Ontology/Foundry migration. Ontology
is fundamentally about entity relationships; the Codebase Impact Map is the seed of that
relationship model applied to the codebase itself.

---

## 2. Concept Model

PERMANENT Task replaces `global-context.md` entirely.

```
┌─────────────────────────────────────────┐
│          PERMANENT Task (Task #1)        │
│  ═══════════════════════════════════════ │
│  User Intent (refined, not accumulated)  │
│  Codebase Impact Map (core value)        │
│  Architecture Decisions                  │
│  Phase Status                            │
│  Constraints                             │
│  ═══════════════════════════════════════ │
│  Version: PT-v{N} (monotonic)            │
│  Status: in_progress (until all done)    │
└──────────────┬──────────────────────────┘
               │ TaskGet (read)
     ┌─────────┼─────────┐
     ▼         ▼         ▼
 Teammate-1  Teammate-2  Teammate-N
 (TaskGet)   (TaskGet)   (TaskGet)
```

### GC vs PERMANENT Task Comparison

| Aspect | GC (current) | PERMANENT Task (new) |
|--------|-------------|----------------------|
| Storage | `.md` file | Task API (JSON on disk) |
| Delivery | Lead embeds full content in Directive (CIP) | Teammate reads via TaskGet (self-serve) |
| Update | Lead edits file | Lead does Read-Merge-Write (TaskUpdate) |
| User requirements | Not supported | `/permanent-tasks` skill for real-time reflection |
| Persistence | Dies with TeamDelete | L2 archive + MEMORY.md integration |
| Ripple analysis | Weak (no reference data) | Core purpose (Codebase Impact Map) |
| Directive size | Large (full GC embedded) | Small (Task ID only) — reduces BUG-002 risk |

---

## 3. PERMANENT Task Description Structure

The description follows this fixed structure. Lead maintains it via Read-Merge-Write.
Opus 4.6 intelligently consolidates on every update — no append-only accumulation.

```markdown
## [PERMANENT] — PT-v{N}

### User Intent
What the user wants to achieve. Refined current state only — no version history.
Opus 4.6 consolidates on every update: deduplication, contradiction resolution,
abstraction elevation. Always a clean, coherent document.

### Codebase Impact Map
The authoritative reference for module/file dependencies and ripple paths.
Lead uses this for LDAP challenge generation.
Teammates use this for Impact Analysis.
Lead uses this for mid-work requirement change impact assessment.

- Module Dependencies: A → B → C (directional)
- Ripple Paths: Change X → affects {Y, Z}
- Interface Boundaries: contract points between modules
- Risk Hotspots: high ripple-risk areas

### Architecture Decisions
Confirmed design decisions with rationale. Refined state, not log.

### Phase Status
Pipeline progress. Phase-by-phase COMPLETE/IN_PROGRESS/PENDING.

### Constraints
Technical constraints, project rules, Safety Rules.
```

### Consolidation Rules (for Opus 4.6 Read-Merge-Write)

When updating the PERMANENT Task description:
1. **Deduplicate** — same intent expressed differently → merge into one
2. **Resolve contradictions** — old requirement vs new requirement → keep latest intent
3. **Elevate abstraction** — 3 specific requests that share a principle → consolidate
4. **Result**: Always a refined current state. Never an append-only log.

---

## 4. `/permanent-tasks` Skill Design

### Frontmatter

```yaml
---
name: permanent-tasks
description: "Reflect conversation context and user requirements into the
  PERMANENT Task. Creates if none exists, updates via Read-Merge-Write if
  one exists. Use mid-work when requirements change or evolve."
argument-hint: "[requirement description or context]"
---
```

### Execution Flow

```
User: /permanent-tasks {arguments}
         │
         ▼
    TaskList → search for subject containing "[PERMANENT]"
         │
    ┌────┴────┐
  not found   found
    │           │
    ▼           ▼
  CREATE      READ-MERGE-WRITE
    │           │
    │           ├─ 1. TaskGet → current description
    │           ├─ 2. sequential-thinking:
    │           │    Extract requirements from conversation + $ARGUMENTS
    │           │    Consolidate with existing content
    │           │    (deduplicate, resolve contradictions, elevate abstraction)
    │           ├─ 3. Assess Impact Map update necessity
    │           ├─ 4. Bump version PT-v{N} → PT-v{N+1}
    │           ├─ 5. TaskUpdate(description: refined whole)
    │           └─ 6. Impact analysis → teammate notification decision
    │
    ▼
  sequential-thinking:
    Extract from full conversation + $ARGUMENTS:
    User Intent, Impact Map draft, Constraints
    │
    ▼
  TaskCreate:
    subject: "[PERMANENT] {feature/project name}"
    status: in_progress
    description: Section 3 structure
    │
    ▼
  Output summary to user
```

### Teammate Notification Decision (on UPDATE)

```
PT-v{N} → PT-v{N+1} change occurred
         │
         ▼
  Lead: sequential-thinking for impact analysis
         │
    ┌────┴────┐
  CRITICAL   LOW
    │          │
    ▼          ▼
  Immediate   Next task only
  SendMessage  Update description
  [CONTEXT-    (no notification)
   UPDATE]
  + Task ID
```

- **CRITICAL**: Impact Map ripple paths include files owned by currently active teammates
- **LOW**: Change affects areas unrelated to current in-progress work

---

## 5. Pipeline Skill Integration (Phase 0)

All pipeline skills gain a Phase 0 step that runs before their main logic.

### Phase 0: PERMANENT Task Initialization

```
Skill invoked ($ARGUMENTS received)
         │
         ▼
  TaskList → search for "[PERMANENT]" in subject
         │
    ┌────┴────┐
  not found   found
    │           │
    ▼           ▼
  AskUser:     TaskGet → read PT
  "Create       │
  PERMANENT     ▼
  Task?"      Continue to Phase {N}.1
    │
  ┌─┴─┐
 Yes   No
  │     │
  ▼     ▼
Create  Continue
PT-v1   without PT
```

### Affected Skills

| Skill | Current Init | New Init |
|-------|-------------|----------|
| `/brainstorming-pipeline` | Phase 1.1 Discovery | Phase 0 → Phase 1.1 |
| `/agent-teams-write-plan` | Phase 4.1 Input Discovery | Phase 0 → Phase 4.1 |
| `/agent-teams-execution-plan` | Phase 6.1 Input Discovery | Phase 0 → Phase 6.1 |

Phase 0 is lightweight (~500 tokens: TaskList + optional TaskGet). It does not
spawn teammates or require DIA verification.

---

## 6. CIP/DIA Protocol Changes (GC → PT)

### Layer 1: CIP (Context Injection Protocol)

```
Current: Lead embeds full global-context.md in every [DIRECTIVE]
New:     Lead includes PERMANENT Task ID in [DIRECTIVE]
         Teammate calls TaskGet to read full content
```

**Benefits:**
- Directive size dramatically reduced (no full GC embedding)
- BUG-002 (context overload) risk reduced — lighter directives
- Teammates always access latest version (not a cached copy)

**What stays:**
- task-context.md still embedded in Directive (individual assignment info)
- Impact Analysis submission obligation
- Lead verification obligation

### Layer 2: DIAVP (Impact Verification)

```
Current: Teammate reads GC from Directive, submits [IMPACT-ANALYSIS]
New:     Teammate calls TaskGet(PT ID), reads PT, submits [IMPACT-ANALYSIS]
         RC checklist adds: "PT-v{N} version confirmed"
```

### Layer 3: LDAP (Adversarial Challenge)

```
Current: Lead generates challenge questions from own judgment (no reference data)
New:     Lead generates challenges from PERMANENT Task's Codebase Impact Map
         — authoritative reference for interconnections and ripple paths
```

This is the most significant qualitative improvement. LDAP currently operates on guesswork.
With the Impact Map, challenges and defenses are grounded in documented relationships.

### Layer 4: Hooks

```
Current: on-subagent-start.sh injects GC version via additionalContext
New:     Injects PERMANENT Task ID + PT-v{N}
```

### Context Delta Protocol

```
Current: GC-v{old} → GC-v{new}, ADDED/CHANGED/REMOVED sections
New:     PT-v{old} → PT-v{new}, same delta structure
         Delivery: SendMessage [CONTEXT-UPDATE] + "TaskGet for PT-v{new}"
         Response: [ACK-UPDATE] PT-v{new} confirmed. Impact: {desc}. Action: {CONTINUE|PAUSE}
```

### Updated Communication Formats

```
[DIRECTIVE] Phase {N}: {task} | Files: {list} | PT-ID: {task_id} | PT-v{ver}
[CONTEXT-UPDATE] PT-v{old} → PT-v{new} | Delta: {summary} | TaskGet for full content
[ACK-UPDATE] PT-v{new} confirmed. Items: {count}. Impact: {desc}. Action: {CONTINUE|PAUSE|NEED_CLARIFICATION}
```

---

## 7. PERMANENT Task Lifecycle

```
Work Start                   Mid-Work                        Work End
──────────                  ────────                        ────────

Phase 0 or                  /permanent-tasks                Lead termination
/permanent-tasks             $ARGUMENTS                     procedure
     │                           │                              │
     ▼                           ▼                              ▼
TaskCreate                  Read-Merge-Write              ┌─ L2 Archive ──┐
"[PERMANENT] ..."           PT-v{N} → PT-v{N+1}          │ Save final PT │
PT-v1                            │                        │ state to L2   │
status: in_progress              ▼                        └───────┬───────┘
     │                      Impact analysis                       │
     ▼                      CRITICAL? → notify teammates          ▼
Teammate spawn:                                           ┌─ MEMORY.md ──┐
Directive includes                                        │ 3-5 line key │
PT Task ID                                                │ decision sum  │
                                                          └───────┬───────┘
                                                                  │
                                                                  ▼
                                                          ┌─ ARCHIVE.md ─┐
                                                          │ ## {date}     │
                                                          │ {feature}     │
                                                          │ Full L2 detail│
                                                          └──────────────┘
```

### Lead Archive Procedure (at work end)

1. TaskGet → read PERMANENT Task final description
2. Save to `.agent/teams/{session-id}/phase-{N}/L2-summary.md`
3. Update MEMORY.md with 3-5 line key decisions summary (within 200-line limit)
4. Append to `memory/ARCHIVE.md` with date + feature name + detailed content
5. TaskUpdate → status: `completed` (after all subtasks done)
6. TeamDelete → Task files deleted (preserved in ARCHIVE.md)

### Memory Architecture

```
MEMORY.md (200 lines, auto-loaded in system prompt)
├── Current state, active bugs, policies, next action
├── Single reference: memory/ARCHIVE.md
└── No topic file proliferation

memory/ARCHIVE.md (unlimited, accessed via Read when needed)
├── ## 2026-02-08 — {feature name}
│   └── Full L2 content from PERMANENT Task
├── ## 2026-02-07 — {previous feature}
│   └── ...
└── Sectioned by date + feature, searchable via Grep
```

---

## 8. Infrastructure Migration Plan

### File Change Matrix

| # | File | Action | Change Description |
|---|------|--------|-------------------|
| M-1 | `.claude/skills/permanent-tasks/SKILL.md` | CREATE | New skill per Section 4 |
| M-2 | `.claude/CLAUDE.md` | MODIFY | Replace all GC references with PT. §3, §4, §6, §9 |
| M-3 | `.claude/references/task-api-guideline.md` | MODIFY | §11(DIA), §13(Team Memory), §14(Context Delta) GC→PT |
| M-4 | `.claude/references/agent-common-protocol.md` | MODIFY | Context Receipt: GC embedding parse → TaskGet(PT ID) |
| M-5 | `.claude/skills/brainstorming-pipeline/SKILL.md` | MODIFY | Add Phase 0, GC-v1 creation → PT-v1 |
| M-6 | `.claude/skills/agent-teams-write-plan/SKILL.md` | MODIFY | Add Phase 0, GC version refs → PT version |
| M-7 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | MODIFY | Add Phase 0, GC-v4 refs → PT refs |
| M-8 | `.claude/hooks/on-subagent-start.sh` | MODIFY | GC version → PT-v{N} + Task ID injection |
| M-9 | `.claude/projects/-home-palantir/memory/MEMORY.md` | MODIFY | Topic file cleanup, ARCHIVE.md reference |
| M-10 | `.claude/projects/-home-palantir/memory/ARCHIVE.md` | CREATE | Consolidate existing topic files |

### Files NOT Changed

| File | Reason |
|------|--------|
| 6x agent .md | TaskGet already in tools. No disallowedTools change needed |
| on-teammate-idle.sh | L1/L2 validation unrelated to PT |
| on-task-completed.sh | Same |
| on-tool-failure.sh | Same |
| settings.json | No change needed |

### Recommended Task Split for Implementation

Given max 2 concurrent teammates and shift-left philosophy:

```
Task 1:  CREATE permanent-tasks/SKILL.md (independent, no dependencies)
Task 2:  MODIFY CLAUDE.md — GC→PT reference replacement
Task 3:  MODIFY task-api-guideline.md — §11, §13, §14 updates
Task 4:  MODIFY agent-common-protocol.md — Context Receipt procedure
Task 5:  MODIFY brainstorming-pipeline/SKILL.md — Phase 0 addition
Task 6:  MODIFY agent-teams-write-plan/SKILL.md — Phase 0 addition
Task 7:  MODIFY agent-teams-execution-plan/SKILL.md — Phase 0 addition
Task 8:  MODIFY on-subagent-start.sh — PT injection
Task 9:  MODIFY MEMORY.md — topic cleanup
Task 10: CREATE memory/ARCHIVE.md — consolidate topic files
```

**Dependency chain:**
- Task 1: independent (can start immediately)
- Task 2: independent (can start immediately)
- Task 3: depends on Task 2 (CLAUDE.md defines protocol, guideline follows)
- Task 4: depends on Task 2 (protocol terms defined in CLAUDE.md)
- Tasks 5-7: depend on Task 1 + Task 4 (skill references PT skill + protocol)
- Task 8: depends on Task 2 (hook reads protocol terms from CLAUDE.md)
- Tasks 9-10: independent (can start anytime)

**Suggested execution order (max 2 concurrent):**
```
Round 1: Task 1 (SKILL.md) + Task 2 (CLAUDE.md)     ← parallel, independent
Round 2: Task 3 (guideline) + Task 4 (common proto)  ← parallel, both depend on T2
Round 3: Task 5 (brainstorm) + Task 6 (write-plan)   ← parallel, depend on T1+T4
Round 4: Task 7 (exec-plan) + Task 8 (hook)          ← parallel
Round 5: Task 9 (MEMORY) + Task 10 (ARCHIVE)         ← parallel, independent
```

---

## 9. Feasibility Verification Items

These must be verified via claude-code-guide research before implementation.

| # | Item | Question | Impact if Negative |
|---|------|----------|-------------------|
| F-1 | TaskList filtering | Can TaskList filter by subject containing "[PERMANENT]"? | Full list traversal needed (low cost given small task count) |
| F-2 | description size limit | Practical size limit for Task description? | If limited: split Impact Map to separate file, PT holds path reference |
| F-3 | metadata for versioning | Can TaskUpdate metadata store PT version number? | Version tracked in description text instead (minor inconvenience) |
| F-4 | Cross-session Task access | Can a PERMANENT Task created in one session be accessed from another? | Requires same team scope or CLAUDE_CODE_TASK_LIST_ID |
| F-5 | Dynamic Context + TaskGet | Can skill `!` backtick syntax call TaskGet? | If not: Phase 0 handles PT loading instead of dynamic injection |

### Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| description grows too large | Split Impact Map to file; PT holds path only |
| TaskList has no filter | Traverse all tasks, match subject (task count is small) |
| Cross-session scope mismatch | Use CLAUDE_CODE_TASK_LIST_ID env var for shared scope |
| Teammate ignores TaskGet | on-subagent-start.sh injects PT Task ID; DIA Layer 2 verifies |

---

## 10. Verification Criteria

### After Implementation

1. `/permanent-tasks "test requirement"` → creates [PERMANENT] task with PT-v1
2. `/permanent-tasks "updated requirement"` → Read-Merge-Write updates to PT-v2
3. `/brainstorming-pipeline` → Phase 0 detects PT, asks user, proceeds
4. Teammate spawn → Directive contains PT Task ID (not full GC content)
5. Teammate → TaskGet(PT ID) succeeds, reads full description
6. Lead LDAP challenge → references Impact Map data (not guesswork)
7. Pipeline completion → L2 archive + MEMORY.md + ARCHIVE.md all updated
8. No file references `global-context.md` in any active infrastructure file
9. All GC-v{N} references replaced with PT-v{N}
10. `wc -l` on CLAUDE.md → no increase from GC→PT migration (neutral or reduced)

### Semantic Integrity Check

- Every section of the old GC structure has a corresponding location in PT structure
- No information loss during GC→PT migration
- DIA 4-Layer protocol fully functional with PT as source
- Teammate Impact Analysis quality equal or improved (due to Impact Map reference)

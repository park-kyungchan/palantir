# Interface Design — Phase 4 Interface Planner

> interface-planner-1 · Phase 4 · Skill Optimization v9.0
> Deliverables: §C content (9 skills), §10 modification, GC migration, naming contract

---

## 1. §C Interface Section Content — All 9 Skills

### Design Principle

Every skill gets a new **§C) Interface Section** with 3 fixed headers: **Input**, **Output**, **Next**.
Content under each header is variant-specific (coordinator-based vs fork-based).
This is the PT-centric contract (D-7) made concrete at the skill level.

### 1.1 Coordinator-Based Skills

#### brainstorming-pipeline

```markdown
## C) Interface

### Input
- **$ARGUMENTS:** Feature description or topic (seed for User Intent)
- **No predecessor L2:** This is the pipeline start — no prior phase output
- **No prior PT:** This skill creates the PERMANENT Task (via /permanent-tasks at Gate 1)

### Output
- **PT-v1** (created via /permanent-tasks): User Intent, Codebase Impact Map, Architecture Decisions, Phase Status (P1-P3=COMPLETE), Constraints
- **L1/L2/L3:** research-coordinator L1/L2/L3, architecture-coordinator L1/L2/L3 (COMPLEX) or researcher/architect L1/L2/L3 (STANDARD)
- **Gate records:** gate-record.yaml for Gates 1, 2, 3
- **GC scratch:** Phase Pipeline Status, execution metrics, version marker (session-scoped only)

### Next
Invoke `/agent-teams-write-plan "$ARGUMENTS"`.
Write-plan needs:
- PT §phase_status.P3.status == COMPLETE
- PT §phase_status.P3.l2_path → arch-coordinator/L2 §Downstream Handoff (contains Architecture Decisions, Constraints, Interface Contracts, Risks)
```

#### agent-teams-write-plan

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Architecture Decisions, §Constraints
- **Predecessor L2:** arch-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P3.l2_path)
  - Contains: Decisions Made, Risks Identified, Interface Contracts, Constraints, Open Questions, Artifacts Produced
- **CH-001 exemplar:** `docs/plans/2026-02-07-ch001-ldap-implementation.md` (10-section format reference)

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Implementation Plan (l3_path, task_count, file_ownership), §phase_status.P4=COMPLETE
- **L1/L2/L3:** planning-coordinator L1/L2/L3 (COMPLEX) or architect L1/L2/L3 (STANDARD)
- **Gate record:** gate-record.yaml for Gate 4
- **Implementation plan file:** `docs/plans/{date}-{feature}-implementation.md` (10-section format)
- **GC scratch:** Phase Pipeline Status update (session-scoped only)

### Next
Invoke `/plan-validation-pipeline "$ARGUMENTS"`.
Validation needs:
- PT §phase_status.P4.status == COMPLETE
- PT §phase_status.P4.l2_path → planning-coordinator/L2 §Downstream Handoff (contains Task Decomposition, File Ownership, Validation Targets, Commit Strategy)
- PT §implementation_plan.l3_path → detailed plan for challenge
```

#### plan-validation-pipeline

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Architecture Decisions, §Constraints, §Implementation Plan (pointer to L3)
- **Predecessor L2:** planning-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P4.l2_path)
  - Contains: Task Decomposition, File Ownership Map, Phase 5 Validation Targets, Commit Strategy
- **Implementation plan file:** path from PT §implementation_plan.l3_path

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Validation Verdict (PASS | CONDITIONAL_PASS | FAIL), §phase_status.P5=COMPLETE. If CONDITIONAL_PASS: adds mitigations to §Constraints
- **L1/L2/L3:** validation-coordinator L1/L2/L3 (COMPLEX) or devils-advocate L1/L2/L3 (STANDARD)
- **Gate record:** gate-record.yaml for Gate 5
- **GC scratch:** Phase Pipeline Status update (session-scoped only)

### Next
If PASS or CONDITIONAL_PASS: invoke `/agent-teams-execution-plan "$ARGUMENTS"`.
If FAIL: return to `/agent-teams-write-plan` for plan revision.
Execution needs:
- PT §phase_status.P4.status == COMPLETE (reads plan)
- PT §validation_verdict (PASS or CONDITIONAL_PASS)
- PT §phase_status.P4.l2_path → planning-coordinator/L2 (for plan context)
- PT §phase_status.P5.l2_path → validation-coordinator/L2 §Downstream Handoff (for validation conditions)
```

#### agent-teams-execution-plan

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Architecture Decisions, §Implementation Plan (l3_path, file_ownership), §Constraints
- **Predecessor L2 (dual):**
  - planning-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P4.l2_path) — plan details
  - validation-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P5.l2_path) — validation conditions
- **Implementation plan file:** path from PT §implementation_plan.l3_path

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Implementation Results (l3_path, summary), §phase_status.P6=COMPLETE, updates §Codebase Impact Map if interface changes detected at Gate 6
- **L1/L2/L3:** execution-coordinator L1/L2/L3, per-implementer L1/L2/L3
- **Gate record:** gate-record.yaml for Gate 6
- **Implemented source files:** per file_ownership assignment
- **GC scratch:** Phase Pipeline Status, execution metrics (session-scoped only)

### Next
Invoke `/verification-pipeline "$ARGUMENTS"`.
Verification needs:
- PT §phase_status.P6.status == COMPLETE
- PT §phase_status.P6.l2_path → execution-coordinator/L2 §Downstream Handoff (contains Implementation Results, Interface Changes, Test Targets)
- PT §implementation_results.l3_path → detailed implementation output
```

#### verification-pipeline

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Implementation Results (pointer to L3), §Constraints
- **Predecessor L2:** execution-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P6.l2_path)
  - Contains: Implementation Results, Interface Changes from Spec, Test Coverage Targets, Phase 7 Entry Conditions

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Verification Summary (test_count, pass_rate, l2_path), §phase_status.P7=COMPLETE, §phase_status.P8=COMPLETE (if Phase 8 runs)
- **L1/L2/L3:** testing-coordinator L1/L2/L3, per-tester/integrator L1/L2/L3
- **Gate records:** gate-record.yaml for Gate 7, Gate 8 (conditional)
- **GC scratch:** Phase Pipeline Status updates (session-scoped only)

### Next
Invoke `/delivery-pipeline "$ARGUMENTS"`.
Delivery needs:
- PT §phase_status with P7==COMPLETE (and P8==COMPLETE if applicable)
- PT §phase_status.P7.l2_path → testing-coordinator/L2 §Downstream Handoff (contains Verification Results, Phase 9 Entry Conditions)
```

### 1.2 Fork-Based Skills

#### delivery-pipeline

```markdown
## Interface

### Input
- **$ARGUMENTS:** Feature name, session ID, or delivery options
- **Dynamic Context:** File tree, git log, gate record paths, ARCHIVE templates, L2 paths (pre-rendered before fork)
- **PT** (via TaskGet): All sections — final consolidation read for delivery summary

### Output
- **PT-vFinal** (via TaskUpdate): §phase_status all phases COMPLETE, subject → "[DELIVERED] {feature}", final metrics summary
- **ARCHIVE.md:** Consolidated session artifact archive
- **MEMORY.md:** Updated with pipeline learnings (Read-Merge-Write)
- **Git commit:** Staged implementation files committed
- **PR:** Created via `gh pr create` (if user approves)
- **Terminal summary:** Delivery status with commit hash, PR URL, archived artifact count

### RISK-8 Fallback
If fork sees isolated task list (TaskList returns empty despite PT existing):
- Skip PT-based discovery. Use Dynamic Context (which pre-renders PT content before fork).
- Skip TaskUpdate for PT-vFinal. Report "PT update needed" in terminal summary for Lead to apply manually.
- All other operations (git, ARCHIVE, MEMORY) proceed normally.
```

#### rsil-global

```markdown
## Interface

### Input
- **$ARGUMENTS:** Optional concern description, observation budget override
- **Dynamic Context:** .agent/ directory tree, CLAUDE.md excerpt, git diff (recent changes), RSIL agent memory (pre-rendered before fork)
- **PT** (via TaskGet, optional): §Phase Status (for pipeline awareness), §Constraints

### Output
- **Tracker update:** `~/.claude/agent-memory/rsil/` narrow tracker (append findings)
- **Agent memory update:** `~/.claude/agent-memory/rsil/MEMORY.md` (universal Lens patterns only)
- **Terminal summary:** Observation type (A/B/C), tier reached (1/2/3), findings count by severity, score delta
- **PT-v{N+1}** (via TaskUpdate, rare): Only if actionable findings require §Constraints update

### RISK-8 Fallback
PT access is OPTIONAL for rsil-global. If isolated task list:
- Skip PT read. Use Dynamic Context for pipeline awareness (pre-rendered).
- Skip PT update (rare case eliminated). Report in terminal summary if findings would warrant PT update.
- Core assessment fully functional without PT.
```

#### rsil-review

```markdown
## Interface

### Input
- **$ARGUMENTS:** Target file(s) path, review scope description
- **Dynamic Context:** .agent/ directory tree, recent git changes, narrow tracker, RSIL agent memory (pre-rendered before fork)
- **PT** (via TaskGet, optional): §Phase Status (pipeline awareness)

### Output
- **Corrections applied:** FIX items applied to target files via Edit (after user approval at R-3)
- **Tracker update:** `~/.claude/agent-memory/rsil/` narrow tracker (findings + corrections)
- **Agent memory update:** `~/.claude/agent-memory/rsil/MEMORY.md` (universal Lens patterns)
- **PT-v{N+1}** (via TaskUpdate): §Phase Status updated with review results (R-4)
- **Terminal summary:** Findings by severity (FIX/WARN/INFO), corrections applied count, score

### RISK-8 Fallback
If isolated task list:
- Skip PT read. Use Dynamic Context for pipeline awareness.
- Skip R-4 PT update. Report "PT update needed: {review results}" in terminal summary for Lead.
- All other operations (R-0~R-3, corrections, tracker, memory) proceed normally.
```

#### permanent-tasks

```markdown
## Interface

### Input
- **$ARGUMENTS:** Update content, requirements description, or context payload
- **Dynamic Context:** Infrastructure version, recent changes (git log), plans list, orchestration-plan.md (pre-rendered before fork)
- **PT** (via TaskGet, if exists): Full PT content for Read-Merge-Write merge

### Output
- **PT-v1** (via TaskCreate, if CREATE): New PERMANENT Task with User Intent, Codebase Impact Map, Architecture Decisions, Phase Status, Constraints, Budget Constraints
- **PT-v{N+1}** (via TaskUpdate, if UPDATE): Merged/refined current state — never append-only
- **Terminal summary:** CREATE vs UPDATE status, PT version, key changes summary, notification needs for Lead relay

### RISK-8 Fallback — CRITICAL
permanent-tasks IS the PT lifecycle manager. If isolated task list:
- TaskList/TaskGet in wrong scope → cannot discover or read PT
- TaskCreate creates PT in wrong list → Lead cannot find it
- **Fallback:** $ARGUMENTS must carry full PT content. Fork agent writes PT content to a file (`permanent-tasks-output.md`). Lead reads file and applies via TaskUpdate/TaskCreate manually.
- This is the HIGHEST IMPACT RISK-8 scenario. Pre-deployment validation MUST test this case.
```

---

## 2. §10 Modification — Exact Implementation Text

### 2.1 CLAUDE.md §10 Change

**File:** `.claude/CLAUDE.md`
**Section:** `## 10. Integrity Principles`, Lead responsibilities, first bullet

**Current text (to find and replace):**

```
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
```

**New text (replacement):**

```
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions),
  except for Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)
  which receive explicit Task API access via their agent .md frontmatter. Fork
  agents execute skills that Lead invokes — they are extensions of Lead's intent,
  not independent actors. Fork Task API scope:
  - pt-manager: TaskCreate + TaskUpdate (creates and maintains PT)
  - delivery-agent: TaskUpdate only (marks PT as DELIVERED)
  - rsil-agent: TaskUpdate only (updates PT with review results)
```

**Validation:** After modification, the 3 agent names MUST match the 4-way naming contract (§4).

### 2.2 agent-common-protocol.md §Task API Change

**File:** `.claude/references/agent-common-protocol.md`
**Section:** `## Task API` (currently lines 74-76)

**Current text (to find and replace):**

```
Tasks are read-only for you: use TaskList and TaskGet to check status, find your
assignments, and read the PERMANENT Task for project context. Task creation and
updates are Lead-only (enforced by tool restrictions).
```

**New text (replacement):**

```
Tasks are read-only for you: use TaskList and TaskGet to check status, find your
assignments, and read the PERMANENT Task for project context. Task creation and
updates are Lead-only (enforced by tool restrictions).

**Exception — Fork-context agents:** If your agent .md frontmatter does NOT include
TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access.
This applies only to Lead-delegated fork agents (pt-manager, delivery-agent,
rsil-agent). You are an extension of Lead's intent — use Task API only for the
specific PT operations defined in your skill's instructions.
```

**Validation:** The 3 agent names MUST match the 4-way naming contract (§4). The exception paragraph must be ADDITIVE (append after existing text, don't replace it).

### 2.3 3-Layer Enforcement Summary

| Layer | Mechanism | Location | Role |
|-------|-----------|----------|------|
| **Primary** | `disallowedTools` frontmatter | Each agent .md file | Tool-level gating (CC enforces) |
| **Secondary** | NL instruction in agent .md body | Agent .md §Constraints, §Never | Behavioral guidance for agent |
| **Tertiary** | Policy statement in CLAUDE.md §10 | `.claude/CLAUDE.md` | System-wide documentation |

**Per-Agent Enforcement:**

| Agent | disallowedTools | NL Constraint | §10 Reference |
|-------|----------------|---------------|---------------|
| pt-manager | `[]` (empty — full Task API) | "Use TaskCreate for [PERMANENT] tasks only" + "Never create duplicate" | "TaskCreate + TaskUpdate" |
| delivery-agent | `[TaskCreate]` | "No TaskCreate — you can only update existing tasks" | "TaskUpdate only" |
| rsil-agent | `[TaskCreate]` | "No TaskCreate — only read tasks and update PT version" | "TaskUpdate only" |

---

## 3. GC Migration Per-Skill Specs

### Migration Principle

For each coordinator-based skill: remove GC writes that carry cross-phase state (replaced by PT + L2), keep GC writes that serve as session scratch only. Replace GC reads with PT + L2 discovery protocol.

### 3.1 brainstorming-pipeline (Most Complex — 3 GC versions)

**GC Writes to REMOVE:**

| Gate | Current GC Write | Replacement |
|------|-----------------|-------------|
| Gate 1 (L230-246) | CREATE GC-v1: Research Findings section placeholder | Not needed — research-coord/L2 holds findings |
| Gate 2 (L377-387) | UPDATE → GC-v2: Research Findings, Codebase Constraints, Phase 3 Input | Research Findings → research-coord/L2. Codebase Constraints → PT §Constraints (merged via /permanent-tasks). Phase 3 Input → research-coord/L2 §Downstream Handoff |
| Gate 3 (L500-511) | UPDATE → GC-v3: Architecture Summary, Architecture Decisions, Phase 4 Entry Requirements | Architecture Summary → arch-coord/L2. Architecture Decisions → PT §Architecture Decisions. Phase 4 Entry Requirements → arch-coord/L2 §Downstream Handoff |

**GC Writes to KEEP (scratch):**

| Gate | GC Write | Why Keep |
|------|----------|----------|
| Gate 1 (L230-246) | Frontmatter (version, pt_version, created, feature, tier) | Session metadata — Dynamic Context reads gc_version |
| Gate 1 (L230-246) | Scope, Phase Pipeline Status, Constraints, Decisions Log | Scratch — authoritative versions in PT |

**GC Reads — None** (brainstorming is pipeline start, reads no predecessor GC).

**Implementation instruction:** At Gates 2 and 3, replace GC UPDATE instructions with: "Verify PT §phase_status updated via /permanent-tasks. Verify coordinator L2 §Downstream Handoff written." Keep Gate 1 GC CREATE but remove cross-phase sections from the template (keep only scratch sections).

### 3.2 agent-teams-write-plan

**GC Reads to REPLACE:**

| Step | Current GC Read | New Discovery |
|------|----------------|---------------|
| Discovery (L91) | Scan for `Phase 3: COMPLETE` in GC | TaskGet PT → §phase_status.P3.status == COMPLETE |
| V-1 (L106) | `global-context.md` exists with `Phase 3: COMPLETE` | PT exists (TaskGet succeeds) AND §phase_status.P3.status == COMPLETE |
| V-3 (L108) | GC-v3 contains Scope, Component Map, Interface Contracts | PT §Architecture Decisions + arch-coord/L2 §Downstream Handoff contain equivalent |
| Phase 4.2 (L123) | Copy GC-v3 to session dir | No longer needed — read L2 directly from path |
| Directive (L166) | Embed GC-v3 in architect directive | Embed PT excerpt + arch-coord/L2 §Downstream Handoff excerpt instead |

**GC Writes to REMOVE:**

| Gate | Current GC Write | Replacement |
|------|-----------------|-------------|
| Gate 4 (L263-265) | ADD to GC-v4: Implementation Plan Reference, Task Decomposition, File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy | Implementation Plan → PT §implementation_plan (pointer). Task Decomposition → planning-coord/L3. File Ownership → PT §implementation_plan.file_ownership. Phase 5/6 Entry Conditions → planning-coord/L2 §Downstream Handoff. Commit Strategy → planning-coord/L2 §Downstream Handoff |

**GC Writes to KEEP:** Phase Pipeline Status update (scratch).

### 3.3 plan-validation-pipeline

**GC Reads to REPLACE:**

| Step | Current GC Read | New Discovery |
|------|----------------|---------------|
| Discovery (L91) | Scan for `Phase 4: COMPLETE` | TaskGet PT → §phase_status.P4.status == COMPLETE |
| V-1 (L110) | `global-context.md` with `Phase 4: COMPLETE` | PT exists AND §phase_status.P4.status == COMPLETE |
| V-4 (L113) | GC-v4 contains Scope, Phase 4 decisions, task breakdown | PT §Implementation Plan + planning-coord/L2 §Downstream Handoff |
| Phase 5.2 (L128) | Copy GC-v4 to session dir | No longer needed — read L2 directly |

**GC Writes to REMOVE:**

| Gate | Current GC Write | Replacement |
|------|-----------------|-------------|
| Gate 5 (L312-315) | Phase 5 status + conditional Constraints mitigations + conditional version bump | Phase 5 status → PT §phase_status.P5. Constraints mitigations → PT §Constraints update via /permanent-tasks |

**GC Writes to KEEP:** Phase Pipeline Status update (scratch).

### 3.4 agent-teams-execution-plan

**GC Reads to REPLACE:**

| Step | Current GC Read | New Discovery |
|------|----------------|---------------|
| Discovery (L97) | Scan for `Phase 4: COMPLETE` or `Phase 5: COMPLETE` | TaskGet PT → §phase_status.P4.status AND §phase_status.P5.status |
| V-1 (L119) | `global-context.md` with Phase 4/5 COMPLETE | PT exists AND §phase_status checks |
| Phase 6.2 (L135) | Copy GC-v4 to session dir | No longer needed — read L2 directly |

**GC Writes to REMOVE:**

| Gate | Current GC Write | Replacement |
|------|-----------------|-------------|
| Phase 6.7 (L553-580) | UPDATE → GC-v5: Phase Pipeline Status (P6), Implementation Results, Interface Changes, Gate 6 Record, Phase 7 Entry Conditions | Implementation Results → PT §implementation_results. Interface Changes → PT §codebase_impact_map update. Gate 6 Record → scratch (PT points to gate-record.yaml). Phase 7 Entry Conditions → exec-coord/L2 §Downstream Handoff |

**GC Writes to KEEP:** Phase Pipeline Status (scratch), Gate 6 record embed (scratch).

### 3.5 verification-pipeline

**GC Reads to REPLACE:**

| Step | Current GC Read | New Discovery |
|------|----------------|---------------|
| V-1 (L116) | `global-context.md` with `Phase 6: COMPLETE` | TaskGet PT → §phase_status.P6.status == COMPLETE |
| Phase 7.2 (L149) | Copy GC-v5 to session dir | No longer needed — read L2 directly |

**GC Writes to REMOVE:**

| Gate | Current GC Write | Replacement |
|------|-----------------|-------------|
| Gate 7 (L317) | `Phase 7: COMPLETE` | PT §phase_status.P7 = COMPLETE |
| Gate 8 (L427) | `Phase 8: COMPLETE` | PT §phase_status.P8 = COMPLETE |
| Termination (L445-462) | Verification Results, Phase 9 Entry Conditions | Verification Results → PT §verification_summary. Phase 9 Entry Conditions → testing-coord/L2 §Downstream Handoff |

**GC Writes to KEEP:** Phase Pipeline Status inline updates (scratch).

### 3.6 delivery-pipeline (Fork — GC Fallback Removal)

**Current:** V-1 fallback (L127): "PT exists with Phase 7/8 COMPLETE — OR — GC exists"

**New:** Remove GC fallback entirely. PT is the sole authority.
- If PT §phase_status.P7.status != COMPLETE → abort with "Phase 7 not complete. Run /verification-pipeline first."
- No GC read path remains.

### 3.7 Fork Skills Without GC (No Changes Needed)

rsil-global, rsil-review, permanent-tasks: No current GC interaction. No migration needed.

---

## 4. 4-Way Naming Consistency Contract

### 4.1 Canonical Name Registry

| Canonical Name | Location 1: Skill `agent:` | Location 2: Agent .md Filename | Location 3: CLAUDE.md §10 | Location 4: agent-common-protocol.md §Task API |
|:--------------:|:-------------------------:|:------------------------------:|:-------------------------:|:-----------------------------------------------:|
| `pt-manager` | `agent: pt-manager` | `.claude/agents/pt-manager.md` | `pt-manager` | `pt-manager` |
| `delivery-agent` | `agent: delivery-agent` | `.claude/agents/delivery-agent.md` | `delivery-agent` | `delivery-agent` |
| `rsil-agent` | `agent: rsil-agent` | `.claude/agents/rsil-agent.md` | `rsil-agent` | `rsil-agent` |

### 4.2 Enforcement Points

1. **Skill frontmatter `agent:` field** — Determines which agent .md CC loads at fork time. Typo = fork resolution failure (FM-1). This is the PRIMARY reference — all other locations must match this.

2. **Agent .md filename** — Must be `{canonical-name}.md` in `.claude/agents/`. CC resolves `agent: "{name}"` to `.claude/agents/{name}.md`. No aliases, no subdirectories.

3. **CLAUDE.md §10** — Policy documentation only. Does not affect runtime behavior. Must list all 3 names for auditability and team awareness.

4. **agent-common-protocol.md §Task API** — Policy documentation only. Fork agents read this at startup. Must list all 3 names so fork agents can self-verify their exception status.

### 4.3 Pre-Deployment Validation Checklist

| # | Check | How to Verify |
|---|-------|---------------|
| 1 | Skill `agent:` matches agent .md filename | `grep -h "^agent:" .claude/skills/*/SKILL.md` → extract names → verify each has `.claude/agents/{name}.md` |
| 2 | §10 lists same 3 names | Read CLAUDE.md §10 → extract parenthetical names → compare to skill `agent:` values |
| 3 | §Task API lists same 3 names | Read agent-common-protocol.md §Task API exception → extract parenthetical names → compare |
| 4 | Agent .md `name:` frontmatter matches filename | For each agent .md: `name:` field must equal filename without `.md` |
| 5 | No extra fork agents unnamed in §10 | Count agent .md files with `disallowedTools: []` or without TaskCreate/TaskUpdate in disallowedTools → must be exactly 3 |

### 4.4 Change Protocol

When adding a new fork agent:
1. Create agent .md in `.claude/agents/`
2. Update skill SKILL.md frontmatter with `agent:` field
3. Update CLAUDE.md §10 named agent list
4. Update agent-common-protocol.md §Task API exception paragraph
5. Run validation checklist (§4.3)

When renaming a fork agent: update ALL 4 locations atomically (Big Bang applies).

---

## 5. PT Discovery Protocol — Implementation Spec

### 5.1 Coordinator-Based Skill Discovery (Replaces GC Scan)

**Current pattern (to be replaced):**
```
Phase N.1 Discovery:
  1. Search for global-context.md in session directories
  2. Scan GC for "Phase {N-1}: COMPLETE"
  3. Read GC sections for entry context
  4. Copy GC to new session directory
```

**New pattern (PT + L2 discovery):**
```
Phase N.1 Discovery:
  1. TaskGet on PERMANENT Task → read full PT
  2. Verify: PT §phase_status.P{N-1}.status == COMPLETE
  3. Read: PT §phase_status.P{N-1}.l2_path → predecessor L2 location
  4. Read: predecessor L2 §Downstream Handoff for entry context
  5. Validate: entry conditions from Downstream Handoff content match expectations
```

**Path pattern:** `.agent/teams/{session-id}/phase-{N}/{coordinator-or-role}/L2-summary.md`

**Error handling:**
- PT not found (TaskGet fails) → "No PERMANENT Task. Run /permanent-tasks first."
- phase_status missing → "Phase {N-1} not complete. Run {predecessor skill} first."
- l2_path missing or file not found → "Predecessor L2 not available. Check Phase {N-1} output."

### 5.2 Fork-Based Skill Discovery

Fork skills use a simpler discovery pattern — no L2 chain:

```
Phase 0: PERMANENT Task Check
  1. TaskList → find [PERMANENT] task
  2. TaskGet → read PT content
  3. Verify: relevant §phase_status entries present
  4. Proceed with skill workflow using PT context + $ARGUMENTS + Dynamic Context
```

**Fallback (RISK-8 — isolated task list):**
```
Phase 0: PERMANENT Task Check (Fallback)
  1. TaskList returns empty → no PT visible
  2. Check $ARGUMENTS for embedded PT context (Lead may have injected it)
  3. Check Dynamic Context for pre-rendered PT content
  4. If both empty → AskUserQuestion for context or abort with guidance
```

---

## Evidence Sources

| Source | Lines Read | Key Extractions |
|--------|:---------:|-----------------|
| interface-architect L3 | 412L | PT schema (§1.3), per-skill contract (§1.2), §10 text (§2.2), GC migration (§4), L2 chain (§1.5) |
| structure-architect L3 | 754L | §C template skeleton (§1.2-1.3), fork frontmatter (§1.3), per-skill delta (§6.2-6.3) |
| risk-architect L3 | 662L | Fork agent .md designs (§1), risk register (§2), failure modes (§4), phased adoption (§5) |
| arch-coord L2 | 221L | Consolidated decisions, constraints, downstream handoff |
| dependency-matrix.md | 326L | GC evidence per-skill (§6), coupling assessment (§7), file inventory (§8) |
| 9 SKILL.md files | 4,430L total | GC read/write operations with line references, current interface patterns |

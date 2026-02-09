---
design_id: SKL-002-AGENT-TEAMS-WRITE-PLAN
version: "1.0"
date: "2026-02-07"
author: "architect-1 (Phase 3)"
status: DRAFT
parent: "Agent Teams Infrastructure v3.0 (DIA + LDAP)"
scope: "New custom skill — Phase 4 Detailed Design Orchestrator"
format: "Markdown + YAML frontmatter"
related:
  - "docs/plans/2026-02-07-brainstorming-pipeline-design.md (SKL-001)"
  - "docs/plans/2026-02-07-ch001-ldap-implementation.md (CH-001 — template precedent)"
  - ".claude/skills/brainstorming-pipeline/SKILL.md (upstream skill)"
  - ".claude/CLAUDE.md (Team Constitution v3.0)"
---

# agent-teams-write-plan — Skill Design Document

## 1. Problem Statement

### Current State

The `writing-plans` skill (superpowers v4.2.0) produces implementation plans for a **single executor** reading linearly. It targets "an engineer with zero context" and chains to `executing-plans` or `subagent-driven-development` for execution.

**Compatibility Analysis (G-07):** writing-plans CONFLICTS with Agent Teams because:
- Uses `TodoWrite` instead of Task API
- Assumes single executor, not Lead + N implementers
- Chains to `executing-plans` which is INCOMPATIBLE with Agent Teams pipeline
- No DIA verification of the plan author
- No file ownership model for multi-implementer coordination

### Solution: Phase 4 Orchestrator Skill

| Skill | Mode | Status |
|-------|------|--------|
| `writing-plans` (superpowers) | Solo mode — unchanged | PRESERVE |
| `agent-teams-write-plan` (custom) | Agent Teams Phase 4 orchestrator | NEW |

The new skill takes brainstorming-pipeline output (GC-v3 + architecture artifacts) and orchestrates an architect teammate to produce a CH-001-format implementation plan with 10 standardized sections.

### Design Principles

1. **Phase 4 Only** — Detailed Design. Takes GC-v3 input, produces implementation plan + GC-v4 output.
2. **brainstorming-pipeline Successor** — Consumes Phase 3 output. Clean handoff via file-based artifacts.
3. **Architect as Author** — Dedicated architect teammate produces the plan. Lead orchestrates + verifies.
4. **CH-001 Template Generalized** — 10-section universal template derived from the proven CH-001 format.
5. **DIA Delegation** — Skill specifies TIER 2 + LDAP MAXIMUM. Protocol execution delegated to CLAUDE.md [PERMANENT].
6. **Dual-Save** — `docs/plans/` (permanent) + `.agent/teams/` (session L1/L2/L3).
7. **Clean Termination** — No auto-chaining. User controls Phase 5 invocation.
8. **writing-plans Principles Preserved** — DRY, YAGNI, TDD, exact paths, complete code, bite-sized granularity.

---

## 2. Architecture Overview

```
agent-teams-write-plan (Lead executes this skill)
│
├── 4.1 Input Discovery + Validation ────── Lead Only, LDAP: NONE
│   ├── Dynamic Context Injection (auto-discover brainstorming output)
│   ├── $ARGUMENTS parsing (optional explicit session-id)
│   ├── GC-v3 validation (Phase 3 COMPLETE?)
│   └── User confirmation of input source
│
├── 4.2 Team Setup ───────────────────────── Lead Only
│   ├── TeamCreate
│   ├── Copy GC-v3 to new session directory
│   └── Create orchestration-plan.md
│
├── 4.3 Architect Spawn + DIA ────────────── architect(1), LDAP: MAXIMUM(3Q+alt)
│   ├── Spawn architect-1 (plan mode)
│   ├── [DIRECTIVE] + [INJECTION] (GC-v3 + task-context)
│   ├── DIA: TIER 2 (4 IAS, 7 RC) + LDAP MAXIMUM (3Q + alt)
│   └── [PLAN] approval
│
├── 4.4 Plan Generation ──────────────────── architect(1) executes
│   ├── Read architecture-design.md + codebase
│   ├── Produce 10-section implementation plan
│   ├── Dual-save: docs/plans/ + L1/L2/L3
│   └── [STATUS] COMPLETE
│
├── 4.5 Gate 4 ───────────────────────────── Lead evaluates
│   ├── 8-criteria gate checklist
│   ├── Plan presentation to user
│   ├── User approval
│   ├── GC-v3 → GC-v4 update
│   └── gate-record.yaml
│
└── Clean Termination
    ├── Output summary to user
    ├── Architect shutdown
    └── TeamDelete
```

### DIA Responsibility Matrix

| Phase | Agent | DIA Tier | LDAP Intensity | Protocol Source |
|-------|-------|----------|----------------|----------------|
| 4 | architect | TIER 2 (4 IAS, 7 RC) | MAXIMUM (3Q + alt) | CLAUDE.md [PERMANENT] §7 |

### Output Directory Structure

```
.agent/teams/{new-session-id}/
├── orchestration-plan.md
├── global-context.md              # Copied from brainstorming, updated to GC-v4
├── phase-4/
│   ├── gate-record.yaml
│   └── architect-1/
│       ├── L1-index.yaml
│       ├── L2-summary.md
│       ├── L3-full/
│       │   └── implementation-plan.md  # Also saved to docs/plans/
│       └── task-context.md
```

---

## 3. Phase 4 Workflow (Full Script)

### 4.1 Input Discovery + Validation

Lead performs input discovery using Dynamic Context Injection output and $ARGUMENTS.

**Discovery Logic:**

```
IF $ARGUMENTS is a valid session directory path:
  → Use directly, validate GC-v3 exists
ELSE IF $ARGUMENTS is a session-id string:
  → Resolve to .agent/teams/{$ARGUMENTS}/global-context.md
ELSE:
  → Parse Dynamic Context Injection output
  → Find directories with GC-v3 where Phase 3: COMPLETE
  → IF exactly 1 candidate: present to user for confirmation
  → IF multiple candidates: present list via AskUserQuestion
  → IF 0 candidates: inform user, suggest running brainstorming-pipeline first
```

**Validation Checks:**

| # | Check | Failure Action |
|---|-------|----------------|
| V-1 | GC-v3 exists and contains `Phase 3: COMPLETE` | Abort with message |
| V-2 | Architecture design file exists in phase-3/architect-1/L3-full/ | Abort with message |
| V-3 | GC-v3 has required sections (Scope, Component Map, Interface Contracts) | Abort with message |

Use `sequential-thinking` to evaluate validation results before proceeding.

### 4.2 Team Setup

```
TeamCreate:
  team_name: "{feature-name}-write-plan"

Create orchestration-plan.md:
  feature: {feature-name}
  current_phase: 4
  gc_version: GC-v3 (copied from brainstorming)
  source_session: {brainstorming-session-id}
  gate_history:
    phase_1: APPROVED (from brainstorming)
    phase_2: APPROVED (from brainstorming)
    phase_3: APPROVED (from brainstorming)

Copy GC-v3 to new session directory (or reference original path).
```

### 4.3 Architect Spawn + DIA

**Spawn Configuration:**

```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}-write-plan"
  name: "architect-1"
  mode: "plan"
```

**[DIRECTIVE] Construction:**

```
[DIRECTIVE] Phase 4: Produce implementation plan for {feature-name}
Files: {target scope from GC-v3 Component Map}
[INJECTION] GC-v3:
{--- full global-context.md v3 embedded ---}

task-context.md:

## Phase 4 Assignment — architect-1

### Objective
Produce a 10-section implementation plan following the CH-001 format.
Dual-save to docs/plans/ and L1/L2/L3.

### Input Artifacts (Read these first)
1. **GC-v3** (embedded above) — project scope, decisions, architecture
2. **Architecture Design**: {brainstorming-session}/phase-3/architect-1/L2-summary.md (inline below)
   {--- L2-summary.md content embedded ---}
3. **Architecture Detail**: {brainstorming-session}/phase-3/architect-1/L3-full/architecture-design.md
   → Read this file with Read tool before starting
4. **CH-001 Exemplar**: docs/plans/2026-02-07-ch001-ldap-implementation.md
   → Read this file to understand the 10-section format

### 10-Section Template Structure
Follow this exact structure for the implementation plan:

§1 Orchestration Overview
§2 global-context.md Update Template (GC-v3→v4 delta)
§3 File Ownership Assignment
§4 TaskCreate Definitions
§5 Change Specifications
§6 Test Strategy
§7 Validation Checklist
§8 Commit Strategy
§9 Gate Criteria
§10 Summary

See §4 of the design document for detailed section specifications.

### Read-First-Write-Second Workflow
When writing §5 Change Specifications:
1. Read each target file with Read tool to confirm current state
2. Record exact line numbers and surrounding context for insertion points
3. Write code blocks matching existing patterns (imports, naming, indentation)
4. Tag each specification with Verification Level:
   - READ_VERIFIED: Code confirmed against Read output
   - PATTERN_BASED: Code following observed codebase patterns
   - DESIGN_ONLY: Architecture-level spec, needs implementer verification

### Plan Document Header
```markdown
# {Feature Name} Implementation Plan

> **For Lead:** Orchestrate via CLAUDE.md Phase Pipeline.
> Do NOT use superpowers:executing-plans.

**Goal:** {one sentence}
**Architecture:** {2-3 sentences}
**Design Source:** {path to architecture-design.md}
```

### Deliverables
1. `docs/plans/YYYY-MM-DD-{feature-name}.md` — complete 10-section plan
2. L1-index.yaml, L2-summary.md, L3-full/implementation-plan.md (copy of plan)

### Constraints
- Use Read tool to verify all file references before writing specs
- Use sequential-thinking for every design decision
- Each TaskCreate task must have AC-0: Plan Verification Step
- §7 must include V6: Code Plausibility category
```

**DIA Flow (CLAUDE.md [PERMANENT] §7):**

1. Architect → `[STATUS] CONTEXT_RECEIVED GC-v3`
2. Architect → `[IMPACT-ANALYSIS]` (TIER 2: 4 sections, 7 RC items)
3. Lead → RC checklist verification (7 items)
4. Lead → `[CHALLENGE]` LDAP MAXIMUM (3Q + ALTERNATIVE_DEMAND)
   - Q1-Q3: Three categories from INTERCONNECTION_MAP, SCOPE_BOUNDARY,
     RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, ASSUMPTION_PROBE
   - +ALT: "Propose one alternative plan decomposition and defend current"
5. Architect → `[CHALLENGE-RESPONSE]` for each
6. Lead → `[IMPACT_VERIFIED] Proceed.` or `[IMPACT_REJECTED]` (max 3)

All agents use `sequential-thinking` throughout.

### 4.4 Plan Generation

After [IMPACT_VERIFIED], architect proceeds:

1. Read architecture-design.md (Phase 3 L3)
2. Read CH-001 exemplar for format reference
3. Read target codebase files (Glob/Grep/Read)
4. Use `sequential-thinking` for:
   - Task decomposition (Component Map → tasks)
   - File ownership assignment (Interface Contracts → boundaries)
   - Change specification (Architecture Decisions → concrete edits)
   - Test strategy design
   - Validation checklist construction
5. Write implementation plan to `docs/plans/`
6. Write L1/L2/L3 to session directory
7. Report `[STATUS] Phase 4 | COMPLETE`

### 4.5 Gate 4

**Gate 4 Criteria:**

| # | Criterion |
|---|-----------|
| G4-1 | Implementation plan exists in docs/plans/ AND L3-full/ |
| G4-2 | Plan follows 10-section template structure |
| G4-3 | All §5 Change Specifications reference real files (verified via Read) |
| G4-4 | §3 File Ownership is non-overlapping across implementers |
| G4-5 | §4 TaskCreate tasks have AC-0 (Plan Verification Step) |
| G4-6 | §7 Validation Checklist includes V6 (Code Plausibility) |
| G4-7 | §5 Change Specifications have Verification Level tags |
| G4-8 | Plan satisfies GC-v3 "Phase 4 Entry Requirements" |

Use `sequential-thinking` to evaluate all criteria.

**User Review:**

Present plan summary to user:
```markdown
## Implementation Plan Ready for Review

**Feature:** {name}
**Plan:** docs/plans/YYYY-MM-DD-{feature}.md
**Tasks:** {count} tasks across {count} implementers
**Files:** {count} files ({create} new, {modify} modified)

**Task Summary:**
| # | Subject | Implementer | Files |
|---|---------|-------------|-------|
{task table}

Would you like to review the full plan before I approve Gate 4?
```

If user requests changes → relay to architect (max 3 iterations).
If user approves → proceed.

**On APPROVE:**
1. Update GC-v3 → GC-v4 (see §5 of this design)
2. Write `phase-4/gate-record.yaml`
3. Proceed to Clean Termination

**On ITERATE (max 3):**
- Specific revision instructions to architect
- Reference exact sections needing change

---

## 4. Implementation Plan Template (10-Section)

This is the generalized template that the Phase 4 architect produces. Each section below defines purpose, structure, and parameterizable elements.

### §1 Orchestration Overview

**Purpose:** Give Lead a complete picture of pipeline structure, teammate allocation, and execution sequence for Phase 6+.

**Structure:**

```markdown
## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure
{ASCII diagram showing which phases are used}
{Justification for phase selection}

### Teammate Allocation
| Role | Count | Agent Type | File Ownership | Phase |
|------|-------|-----------|----------------|-------|
{rows per teammate type}

**WHY {count} {role}:** {justification — tight coupling? independent modules? complexity?}

### Execution Sequence
{Step-by-step with DIA protocol inline}
{Show TeamCreate → TaskCreate → Spawn → DIA → Execute → Gate → Shutdown → TeamDelete}
```

**Parameterizable:** Phase list, teammate count+type, DIA version, sequence steps.

### §2 global-context.md Update Template

**Purpose:** Define the GC-v{N-1} → GC-v{N} delta so Lead knows exactly what to add/update after Gate.

**Structure:**

```markdown
## 2. global-context.md Update Template

### New Sections (ADD to GC-v{N-1})
{Markdown blocks for each new section}

### Updated Sections (MODIFY in GC-v{N-1})
{Section name + new content}

### Preserved Sections (NO CHANGE)
{List of sections carried forward unchanged}
```

**Parameterizable:** Version numbers, section contents.

### §3 File Ownership Assignment

**Purpose:** Assign non-overlapping file sets to implementers. Define interface contracts for cross-boundary interactions.

**Structure:**

```markdown
## 3. File Ownership Assignment

### implementer-{N}: {responsibility domain}
| File | Operation | Notes |
|------|-----------|-------|
{files owned}

### Interface Contracts (if multi-implementer)
| Interface | Provider | Consumer | Contract |
|-----------|----------|----------|----------|
{shared interfaces}

### Read-Only References
| File | Referenced By |
|------|--------------|
{files needed for Read but not modified}
```

**For single implementer:** Simplified to single table (like CH-001 §3).

### §4 TaskCreate Definitions

**Purpose:** Define tasks for Lead to create via TaskCreate. Each task is a self-contained unit with clear acceptance criteria.

**Structure per task:**

```markdown
### Task {ID}: {Subject}

subject: "{descriptive title}"

description: |
  ## Objective
  {What this task accomplishes}

  ## Context in Global Pipeline
  - Phase: {N}
  - Upstream: {what feeds this task}
  - Downstream: {what consumes this task's output}

  ## Detailed Requirements
  See §5 "{section reference}" for exact specifications.

  ## File Ownership
  {file list with operations}

  ## Dependency Chain
  - blockedBy: [{task IDs}]
  - blocks: [{task IDs}]

  ## Acceptance Criteria
  AC-0: Before applying §5 specs, Read each target file and verify
        line numbers and surrounding context match current state.
        On mismatch, report [STATUS] BLOCKED to Lead.
  AC-1: {specific, verifiable criterion}
  AC-2: {specific, verifiable criterion}
  ...

activeForm: "{present progressive description}"
```

**AC-0 is mandatory** for every task — the Plan Verification Step. This compensates for architect's inability to run code during plan creation.

### §5 Change Specifications

**Purpose:** Exact code-level specifications for each task. The architect reads target files and produces precise location + content specifications.

**Structure for MODIFY operations:**

```markdown
### {TaskID}-{N}: {target file} — {description}

**Location:** After `{surrounding context}` (line {N}), BEFORE `{surrounding context}` (line {N}).

**Verification Level:** READ_VERIFIED | PATTERN_BASED | DESIGN_ONLY

**Insert:** / **Change from:** / **Change to:** / **Remove:**
{exact content block with code fence}
```

**Structure for CREATE operations:**

```markdown
### {TaskID}-{N}: {new file path} — {description}

**Purpose:** {why this file exists}
**Verification Level:** DESIGN_ONLY

**Scaffold:**
{exact initial content — complete, not placeholder}

**Import Relationships:**
- Imports from: {list with paths}
- Imported by: {list with paths}
```

**Structure for DELETE operations:**

```markdown
### {TaskID}-{N}: {file path} — DELETE

**Justification:** {why deletion is safe}
**Verification Level:** READ_VERIFIED

**Downstream Impact:**
- Files that imported this: {list}
- Required cleanup: {list of edits in other files}
```

**Verification Level tags** signal confidence to implementers:
- **READ_VERIFIED:** Architect read the target file and confirmed context. High confidence.
- **PATTERN_BASED:** Architect observed codebase patterns and extrapolated. Medium confidence.
- **DESIGN_ONLY:** Architecture-level specification. Implementer must verify before applying. Low confidence — implementer should Read target file and adapt.

### §6 Test Strategy

**Purpose:** Define testing approach for Phase 7 entry. Conditional — only for code-producing tasks.

**Structure:**

```markdown
## 6. Test Strategy

### Test Scope
- Unit tests: {list}
- Integration tests: {list}
- E2E tests: {list, if applicable}

### Per-Task Test Requirements
| Task | Test Files | Test Type | Coverage Target |
|------|-----------|-----------|-----------------|
{rows}

### TDD Cycle (for implementers)
Each task follows:
1. Write failing test
2. Verify test fails
3. Implement minimal code
4. Verify test passes
5. Commit

### Phase 7 Entry Conditions
- [ ] All unit tests passing
- [ ] Integration test coverage ≥ {threshold}
- [ ] No known failures
- [ ] {feature-specific conditions}
```

**Conditional:** For infrastructure-only changes (like CH-001), this section may state "N/A — infrastructure change, no test phase" with justification.

### §7 Validation Checklist

**Purpose:** Cross-reference integrity checks. Ensures consistency across all modified files.

**Structure (6-category pattern):**

```markdown
## 7. Validation Checklist

### V1: Format Consistency
- [ ] {string/format that must match across files}
Expected: `{exact string}`
Locations: {file list}

### V2: Matrix Consistency
- [ ] {table values that must match across files}

### V3: Assignment Consistency
- [ ] {role-specific or context-specific values}

### V4: Version Numbers
- [ ] {version strings in all files}

### V5: Definition Consistency
- [ ] {semantic definitions that must match}

### V6: Code Plausibility
- [ ] All §5 code blocks reference files that exist (Glob verification)
- [ ] Import/require statements reference existing modules
- [ ] Function signatures match existing interface contracts
- [ ] Line numbers in §5 match actual file state (Read verification)
- [ ] DESIGN_ONLY specs flagged for implementer verification
```

**V6 is mandatory** — compensates for architect's inability to execute code.

### §8 Commit Strategy

**Purpose:** Define git commit approach for implementer(s).

**Structure:**

```markdown
## 8. Commit Strategy

### Recommended: {Single Commit | Per-Task Commits}
**Justification:** {tight coupling → single | independent tasks → per-task}

### Commit Template
{Exact git commands with commit message}
```

### §9 Gate Criteria

**Purpose:** Define Phase 6 gate evaluation criteria for Lead.

**Structure:**

```markdown
## 9. Gate Criteria

### Phase 6 Gate
| # | Criterion | Check Method |
|---|-----------|-------------|
| 1 | All files created/modified correctly | Read each file |
| 2 | Cross-references pass V1-V6 | Validation checklist |
| 3 | No broken formatting | Visual inspection |
| 4 | L1/L2/L3 handoff files written | Check output directory |
| 5 | Git commit clean | git status |
| 6 | {feature-specific criteria} | {method} |

### Result Thresholds
- ALL PASS → APPROVE → next phase
- 1-2 FAIL (non-critical) → ITERATE → implementer fixes
- 3+ FAIL → REJECT → re-evaluate approach
```

### §10 Summary

**Purpose:** Metadata table for quick reference.

**Structure:**

```markdown
## 10. Summary

| Item | Value |
|------|-------|
| Pipeline | {phase list} |
| Teammates | {count and types} |
| TaskCreate entries | {count} |
| Files modified | {count} |
| Files created | {count} |
| Estimated lines | {count} |
| DIA Protocol | {version} |
| Commit strategy | {approach} |
| Gate criteria | {count} items |
```

---

## 5. GC-v3 → GC-v4 Delta Specification

At Gate 4 APPROVE, Lead updates GC-v3 to GC-v4 with these changes:

### New Sections (ADD)

```markdown
## Implementation Plan Reference
- Plan document: `docs/plans/YYYY-MM-DD-{feature-name}.md`
- Design source: `{brainstorming-session}/phase-3/architect-1/L3-full/architecture-design.md`
- Plan session: `{write-plan-session}/phase-4/architect-1/`

## Task Decomposition
| Task | Subject | Implementer | blockedBy | Files |
|------|---------|-------------|-----------|-------|
{from §4 of implementation plan}

## File Ownership Map
| Implementer | Files Owned | Operation |
|-------------|------------|-----------|
{from §3 of implementation plan}

## Phase 6 Entry Conditions
{from §9 of implementation plan — prerequisites for implementers}

## Phase 5 Validation Targets
{from §7 of implementation plan — verifiable assertions for devils-advocate}

## Commit Strategy
{from §8 of implementation plan}
```

### Updated Sections (MODIFY)

```markdown
## Phase Pipeline Status
- Phase 1: COMPLETE
- Phase 2: COMPLETE
- Phase 3: COMPLETE (Gate 3 APPROVED)
- Phase 4: COMPLETE (Gate 4 APPROVED)
- Phase 5: PENDING (plan validation)

## Decisions Log
{Add Phase 4 decisions: D-{N+1}, D-{N+2}, ...}
```

### Preserved Sections (NO CHANGE)

- Scope (Goal, In/Out Scope, Approach, Success Criteria)
- Constraints
- Research Findings
- Codebase Constraints
- Architecture Decisions
- Component Map
- Interface Contracts
- Phase 4 Entry Requirements (mark as SATISFIED in comment)

### Version Header Update

```yaml
---
version: GC-v4
---
```

---

## 6. Clean Termination

After Gate 4 APPROVE:

### Output Summary

Present to user:

```markdown
## agent-teams-write-plan Complete (Phase 4)

**Feature:** {feature-name}
**Complexity:** {level}

**Implementation Plan:**
- `docs/plans/YYYY-MM-DD-{feature}.md` (permanent)
- `{session-dir}/phase-4/architect-1/L3-full/implementation-plan.md` (session)

**Plan Summary:**
- Tasks: {count} tasks across {count} implementers
- Files: {create} new, {modify} modified
- Test strategy: {summary}
- Commit strategy: {single|per-task}

**Artifacts:**
- global-context.md (GC-v4)
- orchestration-plan.md
- Phase 4: architect L1/L2/L3

**Location:** .agent/teams/{session-id}/

**Next:** Phase 5 (Plan Validation) — use the plan-validation skill.
Input: GC-v4 + implementation plan from docs/plans/.
```

### Shutdown Sequence

```
1. Shutdown architect-1: SendMessage type: "shutdown_request"
   Wait for shutdown_response (approve)
2. TeamDelete — cleans team coordination files
3. Artifacts in .agent/teams/{session-id}/ are preserved
```

---

## 7. Cross-Cutting Requirements

### Sequential Thinking

All agents (Lead and architect) use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, design, and verification.

| Agent | When |
|-------|------|
| Lead (4.1) | Input validation, candidate selection |
| Lead (4.3) | DIA verification, LDAP challenge generation |
| Lead (4.5) | Gate 4 evaluation, GC-v4 construction |
| Architect (4.4) | Task decomposition, file ownership, change specs, test strategy |

### Error Handling

| Situation | Response |
|-----------|----------|
| No brainstorming output found | Inform user, suggest running brainstorming-pipeline |
| GC-v3 missing required sections | Abort with specific missing section list |
| Architect spawn failure | Retry once, then abort with user notification |
| DIA 3x rejection | Abort architect, re-spawn with enhanced context |
| Gate 4 3x iteration | Abort phase, present partial results to user |
| Context compact | Follow CLAUDE.md §8 Compact Recovery |
| User cancellation | Graceful shutdown architect, preserve artifacts |

### Compact Recovery

Follows CLAUDE.md §8:

**Lead recovery:**
1. Read orchestration-plan.md
2. Read task list
3. Read phase-4/gate-record.yaml (if exists)
4. Read architect-1 L1 index
5. Re-inject [DIRECTIVE]+[INJECTION] with latest GC-v{N}

**Architect recovery:**
1. Receive [INJECTION] from Lead
2. Read own L1 → L2 → L3 as needed
3. Re-submit [IMPACT-ANALYSIS]
4. Wait for [IMPACT_VERIFIED]

---

## 8. Comparison: writing-plans vs agent-teams-write-plan

| Aspect | writing-plans (solo) | agent-teams-write-plan (Agent Teams) |
|--------|---------------------|--------------------------------------|
| Target reader | "Engineer with zero context" | Lead (orchestrator) + implementer teammates |
| Input | Brainstorming design doc / spec | GC-v3 + architecture artifacts (brainstorming-pipeline) |
| Plan author | Lead directly | Architect teammate (DIA verified) |
| Task format | TodoWrite steps (2-5 min each) | TaskCreate blocks (6-field, acceptance criteria) |
| File ownership | N/A (single executor) | Explicit per-implementer assignment |
| Verification | None (author = executor) | DIA TIER 2 + LDAP MAXIMUM + Gate 4 |
| Template | Free-form with TDD steps | 10-section standardized (CH-001 derived) |
| Code in plan | Complete code blocks | Complete code blocks + Verification Level tags |
| Test strategy | TDD inline per step | Separate §6 with Phase 7 entry conditions |
| Validation | None | §7 with V1-V6 (including Code Plausibility) |
| Execution handoff | executing-plans / subagent-driven-dev | Clean termination → Phase 5 → Phase 6 pipeline |
| Output location | docs/plans/ only | docs/plans/ + .agent/teams/ L1/L2/L3 |
| Context evolution | None | GC-v3 → GC-v4 |
| DRY/YAGNI/TDD | Preserved | Preserved |
| Exact paths | Required | Required |
| Frequent commits | Required | Required (§8 Commit Strategy) |

---

## 9. SKILL.md Complete Draft

The following is the complete content for `.claude/skills/agent-teams-write-plan/SKILL.md`:

```markdown
---
name: agent-teams-write-plan
description: Use after brainstorming-pipeline to produce a detailed implementation plan (Phase 4). Takes GC-v3 + architecture artifacts as input, spawns an architect to create a 10-section CH-001-format plan. Requires Agent Teams mode and CLAUDE.md v3.0+.
argument-hint: "[brainstorming-session-id or path]"
---

# Agent Teams Write Plan

Phase 4 (Detailed Design) orchestrator. Transforms brainstorming-pipeline architecture output into a concrete implementation plan through a DIA-verified architect teammate.

**Announce at start:** "I'm using agent-teams-write-plan to orchestrate Phase 4 (Detailed Design) for this feature."

**Core flow:** Input Discovery → Team Setup → Architect Spawn + DIA → Plan Generation → Gate 4 → Clean Termination

## When to Use

```
Have architecture output from brainstorming-pipeline?
├── Working in Agent Teams mode? ─── no ──→ Use /writing-plans (solo)
├── yes
├── GC-v3 with Phase 3 COMPLETE? ── no ──→ Run /brainstorming-pipeline first
├── yes
└── Use /agent-teams-write-plan
```

**vs. writing-plans (solo):** This skill spawns an architect teammate with full DIA verification (TIER 2 + LDAP MAXIMUM). Solo writing-plans has the Lead write the plan directly with no verification. Use this when the feature complexity justifies the overhead.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Previous Pipeline Output:**
!`ls -d /home/palantir/.agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Existing Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS

---

## Phase 4.1: Input Discovery + Validation

LDAP intensity: NONE (Lead-only step). No teammates spawned yet.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find brainstorming-pipeline output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 3: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found brainstorming output at {path}. Use this?"
5. If no candidates, inform user: "No brainstorming-pipeline output found. Run /brainstorming-pipeline first."

### Validation

After identifying the source directory, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with `Phase 3: COMPLETE` | Abort: "GC-v3 not found or Phase 3 not complete" |
| V-2 | `phase-3/architect-1/L3-full/architecture-design.md` exists | Abort: "Architecture design not found" |
| V-3 | GC-v3 contains Scope, Component Map, Interface Contracts sections | Abort: "GC-v3 missing required sections: {list}" |

Use `sequential-thinking` to evaluate validation results.

On all checks PASS → proceed to 4.2.

---

## Phase 4.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-write-plan"
```

Create orchestration-plan.md and copy GC-v3 to new session directory.

---

## Phase 4.3: Architect Spawn + DIA

DIA: TIER 2 + LDAP MAXIMUM (3Q + alternative). Protocol execution follows CLAUDE.md [PERMANENT] §7.

Use `sequential-thinking` for all Lead decisions in this phase.

### Spawn

```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}-write-plan"
  name: "architect-1"
  mode: "plan"
```

### [DIRECTIVE] Construction

The directive must include these 4 context layers:

1. **GC-v3 full embedding** — the entire global-context.md (CIP protocol)
2. **Phase 3 Architect L2-summary.md** — embedded inline in task-context for architecture narrative
3. **Architecture Design path** — `{source}/phase-3/architect-1/L3-full/architecture-design.md` for architect to Read
4. **CH-001 Exemplar path** — `docs/plans/2026-02-07-ch001-ldap-implementation.md` for format reference

Task-context must instruct architect to:
- Read architecture-design.md and CH-001 exemplar before starting
- Follow the 10-section template (§1-§10)
- Use Read-First-Write-Second workflow for §5
- Tag all §5 specs with Verification Level
- Include AC-0 in every §4 task
- Include V6 Code Plausibility in §7
- Dual-save plan to docs/plans/ and L3-full/
- Use sequential-thinking for all design decisions

### DIA Flow

1. Architect confirms context receipt
2. Architect submits Impact Analysis (TIER 2: 4 sections, 7 RC)
3. Lead verifies RC checklist
4. Lead issues LDAP challenge (MAXIMUM: 3Q + ALTERNATIVE_DEMAND)
   - Q1-Q3: Context-specific questions from 7 LDAP categories
   - +ALT: "Propose one alternative plan decomposition and defend current"
5. Architect defends with specific evidence
6. Lead verifies or rejects (max 3 attempts)

All agents use `sequential-thinking` throughout.

---

## Phase 4.4: Plan Generation

After [IMPACT_VERIFIED], architect produces the implementation plan.

Architect works with: Read, Glob, Grep, Write, sequential-thinking.

**Expected output:**

```
docs/plans/YYYY-MM-DD-{feature-name}.md
  → Complete 10-section implementation plan

.agent/teams/{session-id}/phase-4/architect-1/
├── L1-index.yaml    (≤50 lines — tasks, files, decisions, risks)
├── L2-summary.md    (≤200 lines — design narrative, trade-offs)
└── L3-full/
    └── implementation-plan.md  (copy of docs/plans/ file)
```

Architect reports `[STATUS] Phase 4 | COMPLETE` via SendMessage.

---

## Phase 4.5: Gate 4

Use `sequential-thinking` for all gate evaluation.

### Criteria

| # | Criterion |
|---|-----------|
| G4-1 | Plan exists in docs/plans/ and L3-full/ |
| G4-2 | Plan follows 10-section template |
| G4-3 | §5 specs reference real files (spot-check via Read) |
| G4-4 | §3 file ownership is non-overlapping |
| G4-5 | §4 tasks all have AC-0 |
| G4-6 | §7 includes V6 Code Plausibility |
| G4-7 | §5 specs have Verification Level tags |
| G4-8 | Plan satisfies GC-v3 Phase 4 Entry Requirements |

### User Review

Present plan summary to user before final approval:

```markdown
## Implementation Plan Ready

**Feature:** {name}
**Plan:** docs/plans/{filename}
**Tasks:** {N} tasks, {M} implementers
**Files:** {create} new, {modify} modified

Shall I proceed with Gate 4 approval?
```

### On APPROVE
1. GC-v3 → GC-v4 (add Implementation Plan Reference, Task Decomposition,
   File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets,
   Commit Strategy; update Phase Pipeline Status)
2. Write phase-4/gate-record.yaml
3. Proceed to Clean Termination

### On ITERATE (max 3)
- Relay specific revision instructions to architect
- Architect revises and resubmits

---

## Clean Termination

After Gate 4 APPROVE:

### Output Summary

```markdown
## agent-teams-write-plan Complete (Phase 4)

**Feature:** {name}
**Complexity:** {level}

**Implementation Plan:** docs/plans/{filename}
**Artifacts:** .agent/teams/{session-id}/

**Next:** Phase 5 (Plan Validation) — validates the implementation plan.
Input: GC-v4 + plan document.
```

### Shutdown

1. Shutdown architect-1: `SendMessage type: "shutdown_request"`
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting

### Sequential Thinking
All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, design, and verification.

### Error Handling
| Situation | Response |
|-----------|----------|
| No brainstorming output | Inform user, suggest /brainstorming-pipeline |
| GC-v3 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| DIA 3x rejection | Abort architect, re-spawn |
| Gate 4 3x iteration | Abort, present partial results |
| Context compact | CLAUDE.md §8 recovery |
| User cancellation | Graceful shutdown, preserve artifacts |

### Compact Recovery
- Lead: orchestration-plan → task list → gate records → L1 → re-inject
- Architect: receive injection → read L1/L2/L3 → re-submit Impact Analysis

## Key Principles

- DRY, YAGNI, TDD — preserved from writing-plans
- Exact file paths always — even more critical with multiple implementers
- Complete code in plan — with Verification Level tags for confidence signaling
- AC-0 mandatory — every task starts with plan-vs-reality verification
- V6 Code Plausibility — compensates for architect's inability to run code
- Sequential thinking always — structured reasoning at every decision point
- DIA delegated — CLAUDE.md [PERMANENT] owns protocol, skill owns orchestration
- Clean termination — no auto-chaining to Phase 5
- Dual-save — docs/plans/ (permanent) + .agent/teams/ (session)

## Never

- Skip DIA verification for the architect
- Auto-chain to Phase 5 after termination
- Proceed past Gate 4 without all criteria met
- Let the architect write to Task API
- Skip input validation (GC-v3 must exist with Phase 3 COMPLETE)
- Omit AC-0 from any TaskCreate definition
- Omit V6 from the validation checklist
- Write §5 specs without reading target files first
```

---

## Appendix: Key Design Decisions

| ID | Decision | Rationale | Source |
|----|----------|-----------|--------|
| AD-1 | Architect as plan author (not Lead) | CLAUDE.md §2 mandates architect for Phase 4. Delegate Mode preserved. DIA verification enabled. | CLAUDE.md §2, §3 |
| AD-2 | 10-section template from CH-001 | Proven format with 1 successful precedent. Generalizes well with parametric fields. | CH-001 analysis (researcher-1 Domain 2) |
| AD-3 | Verification Level tags in §5 | Compensates for architect's Read-only tool constraint. Signals confidence to implementers. | LDAP Q2 defense |
| AD-4 | AC-0 mandatory in every task | Ensures implementer verifies plan accuracy against current file state before applying changes. | LDAP Q2 defense |
| AD-5 | V6 Code Plausibility in §7 | Adds code-level verification category beyond cross-reference checks. | LDAP Q2 defense |
| AD-6 | Hybrid auto-discovery input | Flexible: auto-scan + user confirm or explicit $ARGUMENTS path. | researcher-1 recommendation |
| AD-7 | 4-layer task-context for architect | GC-v3 (full) + L2-summary (inline) + L3 path (reference) + CH-001 (exemplar). Ensures context continuity across sessions. | LDAP Q1 defense |
| AD-8 | Clean termination at Phase 4 | No auto-chain. Phase ordering (4→5→6) prevents stale GC. | LDAP Q3 defense |
| AD-9 | GC-v4 delta specification | 6 new sections, 2 updated, rest preserved. Standard delta pattern. | researcher-1 Domain 3 |
| AD-10 | Read-First-Write-Second workflow | Architect reads target files before writing §5 specs. Maximizes accuracy within tool constraints. | LDAP Q2 defense |

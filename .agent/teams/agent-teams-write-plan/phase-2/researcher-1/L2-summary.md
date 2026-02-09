# L2 Summary — agent-teams-write-plan Research

> Phase 2 | researcher-1 | 2026-02-07

## Domain 1: writing-plans Core Principles Analysis

### Source
`.claude/plugins/cache/claude-plugins-official/superpowers/4.2.0/skills/writing-plans/SKILL.md` (117 lines)

### Principles to PRESERVE

The original skill establishes 6 core principles that remain valid in Agent Teams context:

1. **DRY / YAGNI / TDD / Frequent commits** — Engineering philosophy. Applies regardless of execution model.
2. **Exact file paths always** — Critical for implementer teammates who have "zero context." Even more important in multi-agent context where ambiguity causes cross-boundary conflicts.
3. **Complete code in plan** — Not "add validation" but actual code blocks. Prevents implementer interpretation drift.
4. **Exact commands with expected output** — Enables deterministic verification by implementer and Lead.
5. **Bite-sized task granularity** — Original uses 2-5 min steps. Agent Teams equivalent: each TaskCreate entry has clear acceptance criteria and bounded scope.
6. **Plan saved to `docs/plans/`** — Permanent artifact location. Agent Teams adds `.agent/teams/` as session-level L1/L2/L3.

### Elements to REPLACE

| Original | Agent Teams Replacement | Why |
|----------|------------------------|-----|
| Target: "engineer with zero context" | Target: Lead + implementer teammates | Lead orchestrates, implementers execute with DIA verification |
| Plan header: "For Claude: Use executing-plans" | Plan header: "For Lead: Orchestrate via CLAUDE.md pipeline" | Lead is the consumer, not a solo executor |
| TodoWrite for step tracking | TaskCreate via Lead (teammates read-only) | Task API replaces todo system |
| 2-5 min steps | Phase-level tasks with acceptance criteria | Granularity shifts from human-time to task-scope |
| Execution choice (subagent vs parallel) | Pipeline continuation (Phase 6→7→8) | Agent Teams has defined phase progression |
| git worktree isolation | Shared workspace + file ownership rules | CLAUDE.md §5 governs file boundaries |
| Step-by-step TDD cycle per feature | TDD principle preserved but execution delegated to implementer | Implementer applies TDD within their task scope |

### Key Insight

The original writing-plans assumes a **single executor reading linearly**. Agent Teams plans are consumed by **Lead (orchestrator) + N implementers (parallel executors)**. This means:
- Plan must be **decomposable** into independent tasks (not linear steps)
- Each task must be **self-contained** with file ownership, acceptance criteria, dependencies
- Cross-task integrity must be **explicitly validated** (validation checklist)

---

## Domain 2: CH-001 Plan Format Analysis + Template Design

### Source
`docs/plans/2026-02-07-ch001-ldap-implementation.md` (757 lines, 10 sections)

### Section-by-Section Analysis

| § | Section | Lines | Universal? | Notes |
|---|---------|-------|------------|-------|
| 1 | Orchestration Overview | 1-67 | YES (parameterize) | Pipeline structure, teammate allocation table, execution sequence diagram — all universal. CH-001's "simplified pipeline" and "single implementer + WHY" are parametric instances |
| 2 | global-context.md Template | 68-127 | YES | GC is the Agent Teams coordination mechanism. Template structure (Summary, Reference, Decisions, Scope, Cross-Ref, Teammates, Status) is universal |
| 3 | File Ownership Assignment | 128-144 | YES | Table format (File, Ownership, Operation) is universal. Becomes more critical with multiple implementers |
| 4 | TaskCreate Definitions | 145-272 | YES (structure) | 6-field structure (subject, description with Objective/Context/Requirements/Ownership/Dependencies/Acceptance Criteria, activeForm) is universal. CH-001's 3 tasks are instance-specific |
| 5 | Edit Specifications — Task A | 273-393 | STRUCTURE yes, CONTENT no | Pattern: Location → Insert/Change with exact content. Structure universal, content feature-specific |
| 6 | Edit Specifications — Task B | 394-486 | Same as §5 | Same pattern applied to different files |
| 7 | Validation Checklist | 487-681 | YES (pattern) | 5 validation categories (V1: format consistency, V2: matrix consistency, V3: assignment consistency, V4: version numbers, V5: definition consistency). Category pattern is universal, specific items are feature-dependent |
| 8 | Commit Strategy | 682-719 | YES | Single vs per-task commit options with exact commands. Universal pattern |
| 9 | Gate Criteria | 720-740 | YES | 7 criteria (artifacts, quality, issues, conflicts, L1/L2/L3, git). Mostly universal |
| 10 | Summary | 741-757 | YES | Metadata table. Universal |

### Proposed Generalized Template (10 sections)

Based on CH-001 analysis + gap identification from LDAP challenge defense:

```
§1  Orchestration Overview
    - Pipeline phases (variable: which phases used, justification)
    - Teammate allocation table (variable: count, types, WHY)
    - Execution sequence diagram
    - DIA protocol version applicable

§2  global-context.md Update Template
    - GC-v{N-1} → GC-v{N} delta specification
    - New sections to add (Implementation Plan Ref, Task Decomposition, etc.)
    - Sections to update (Phase Status)

§3  File Ownership Assignment
    - Per-implementer file assignment table
    - Operation type per file (CREATE / MODIFY / DELETE)
    - Multi-implementer: interface contract between implementer scopes
    - Read-only files listed explicitly

§4  TaskCreate Definitions
    - Per-task blocks with 6-field structure:
      subject, description (Objective, Context, Detailed Requirements ref,
      File Ownership, Dependency Chain, Acceptance Criteria), activeForm
    - Dependency graph (blockedBy / blocks)

§5  Change Specifications (per-task)
    - For MODIFY: Location → Change (line refs, before/after)
    - For CREATE: File purpose, scaffold, initial content, import relationships
    - For DELETE: Justification, downstream impact
    - Complete code blocks (not descriptions)
    - Exact file paths with line numbers

§6  Test Strategy [NEW — absent in CH-001]
    - Test file locations per task
    - Test types (unit / integration / e2e)
    - Phase 7 entry conditions
    - Coverage expectations
    - TDD cycle instructions for implementer

§7  Validation Checklist
    - Cross-reference integrity checks (5-category pattern from CH-001)
    - Per-category: items to verify, expected values, check locations
    - Phase 5 verifiable assertions (if Phase 5 follows)

§8  Commit Strategy
    - Single commit (recommended for tight coupling)
    - Per-task commits (for independent tasks)
    - Exact git commands with message templates

§9  Gate Criteria
    - Phase 6 gate evaluation criteria
    - Result thresholds (ALL PASS / 1-2 FAIL / 3+ FAIL)
    - Phase 7/8 entry conditions

§10 Summary
    - Metadata table (pipeline, teammates, tasks, files, lines, DIA, commits, gates)
```

---

## Domain 3: brainstorming-pipeline → agent-teams-write-plan Interface

### Source
- `.claude/skills/brainstorming-pipeline/SKILL.md` (481 lines)
- `docs/plans/2026-02-07-brainstorming-pipeline-design.md` (755 lines)

### GC-v3 Output Structure (What brainstorming-pipeline produces)

From design §5.4 "GC-v3 Additions":

```markdown
## Architecture Decisions
{Synthesized from architect L1/L2}

## Component Map
{Component list with responsibilities}

## Interface Contracts
{Key interfaces between components}

## Phase 4 Entry Requirements
{What Detailed Design needs — feeds into writing-plans skill}

## Phase Pipeline Status
- Phase 1: COMPLETE
- Phase 2: COMPLETE
- Phase 3: COMPLETE (Gate 3 APPROVED)
- Phase 4: PENDING (use writing-plans skill)
```

Plus earlier sections from GC-v1/v2:
- Scope (Goal, In/Out Scope, Approach, Success Criteria, Complexity)
- Constraints
- Decisions Log
- Research Findings
- Codebase Constraints
- Phase 3 Architecture Input

### What architect needs from GC-v3 for Phase 4

The architect teammate in agent-teams-write-plan consumes GC-v3 to produce the implementation plan. Key inputs:

1. **Component Map** → decompose into implementer tasks
2. **Interface Contracts** → define file ownership boundaries (which implementer owns which interface)
3. **Architecture Decisions** → translate design choices into concrete edit/create specifications
4. **Phase 4 Entry Requirements** → explicit checklist of what the architect must address
5. **Scope** → bound the implementation plan scope
6. **Research Findings** → technical constraints that affect implementation approach
7. **Codebase Constraints** → existing patterns/APIs to reuse or avoid

### GC-v3 → GC-v4 Delta (What agent-teams-write-plan must add)

GC-v4 is produced at Gate 4 (Phase 4 completion). It must add:

| Section | Content | Source |
|---------|---------|--------|
| Implementation Plan Reference | `docs/plans/YYYY-MM-DD-<feature>.md` path | Architect output |
| Task Decomposition Summary | Task count, brief per-task description, dependency graph | From §4 TaskCreate Definitions |
| File Ownership Map | implementer-{N} → [file list] mapping | From §3 |
| Phase 6 Entry Conditions | Prerequisites for implementers to begin | From §9 Gate Criteria |
| Phase 5 Validation Targets | Verifiable assertions for devils-advocate | From §7 |
| Commit Strategy | Selected approach (single/per-task) | From §8 |
| Pipeline Status | Phase 4: COMPLETE (Gate 4 APPROVED), Phase 5: PENDING | Updated |

Sections preserved from GC-v3 (no modification):
- Architecture Decisions, Component Map, Interface Contracts
- Scope, Constraints, Decisions Log
- Research Findings, Codebase Constraints

### Pipeline Connection Points

```
brainstorming-pipeline                 agent-teams-write-plan
─────────────────────                  ──────────────────────
Phase 3 Gate 3 APPROVE
  → GC-v3 written
  → architect shutdown
  → TeamDelete
  → "Next: Phase 4 — use
     writing-plans skill"
                                        User invokes skill
                                        Lead reads GC-v3 + architect L1/L2/L3
                                        Phase 4 begins (TeamCreate)
                                        architect-1 spawned (new instance)
                                        DIA: TIER 2 + LDAP MAXIMUM
                                        architect produces implementation plan
                                        Gate 4 → GC-v4
                                        Clean Termination
                                        "Next: Phase 5 — plan validation"
```

Key design consideration: brainstorming-pipeline does `TeamDelete` at termination, so agent-teams-write-plan must `TeamCreate` a new team. The `.agent/teams/{session-id}/` artifacts survive TeamDelete — only coordination files are cleaned. The new skill reads artifacts from the previous session directory.

### Input Discovery Mechanism

The skill needs to locate brainstorming-pipeline output. Options:
1. **$ARGUMENTS** — user provides session-id or directory path
2. **Auto-discovery** — scan `.agent/teams/*/global-context.md` for latest GC-v3 with Phase 3 COMPLETE
3. **Hybrid** — auto-discover, present to user for confirmation

Recommendation: **Hybrid** — auto-discover + confirm. Same pattern as brainstorming-pipeline's Dynamic Context Injection.

---

## Recommendations for Phase 3 Architect

1. **Template structure**: Use the 10-section generalized template from Domain 2 analysis. This extends CH-001's proven 10-section structure with Test Strategy (§6) and expanded Change Specifications (§5).

2. **Preserve writing-plans principles**: DRY, YAGNI, TDD, exact paths, complete code, bite-sized granularity. These translate directly to TaskCreate acceptance criteria quality.

3. **Input mechanism**: Hybrid auto-discovery of brainstorming-pipeline output. Dynamic Context Injection for session directory, GC version, infrastructure state.

4. **DIA delegation**: Same pattern as brainstorming-pipeline — skill specifies tier/intensity (TIER 2 + LDAP MAXIMUM for architect), protocol execution delegated to CLAUDE.md [PERMANENT] §7.

5. **Output dual-save**: Implementation plan to `docs/plans/` (permanent) + L1/L2/L3 to `.agent/teams/` (session). GC-v3→v4 update at Gate 4.

6. **Clean termination**: No auto-chaining to Phase 5. User controls next step. Same pattern as brainstorming-pipeline.

7. **Skill Optimization Process [PERMANENT]**: Apply Dynamic Context Injection, $ARGUMENTS, argument-hint, measured language. Separate claude-code-guide investigation will provide additional optimizations.

## Gaps and Risks

| # | Gap/Risk | Severity | Mitigation |
|---|----------|----------|------------|
| G-1 | CH-001 is the only precedent — sample size 1 | MEDIUM | Template designed with parameterization for flexibility. Validate with hypothetical scenarios |
| G-2 | Session-id continuity between brainstorming-pipeline and write-plan | LOW | Auto-discovery + user confirmation covers this |
| G-3 | Architect may produce plan in wrong format | LOW | Skill provides exact template structure + CH-001 as example reference |
| G-4 | TDD integration unclear for non-code tasks | LOW | §6 Test Strategy is conditional — only for code-producing tasks |

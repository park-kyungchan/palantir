# Lead Architecture Redesign — Implementation Plan

> **For Lead:** This plan is designed for Agent Teams native execution with 2 infra-implementers.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.

**Goal:** Implement the Hybrid Coordinator Model (5 coordinators + 5 Lead-direct categories)
to resolve the BN-1→BN-3→BN-4 cascade. Reduce Lead's mandatory catalog read from 976L to
~300L (69%). Reduce per-task Phase 6 context cost by 71% through coordinator-mediated review dispatch.

**Architecture Source:** `.agent/teams/lead-arch-redesign/phase-3/architect-1/L3-full/architecture-design.md`
**Design Source:** `docs/plans/2026-02-11-lead-architecture-redesign.md`

**Pipeline:** Phase 6 (Infrastructure) — 2 infra-implementers, zero file overlap.

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

This is an **infrastructure pipeline** — all changes are .claude/ configuration files:

```
Phase 1: Discovery        — Lead reads this plan (YOU ARE HERE)
Phase 6: Implementation   — 2 infra-implementers execute parallel workstreams
Phase 6.V: Verification   — Lead validates cross-references and consistency
Phase 9: Delivery          — Lead commits and cleans up
```

### Teammate Allocation

| Role | Count | Agent Type | Tasks | Files |
|------|-------|-----------|-------|-------|
| Implementer A | 1 | `infra-implementer` | T-1, T-2, T-5, T-7, T-9 | 27 files |
| Implementer B | 1 | `infra-implementer` | T-3, T-4, T-6, T-8, T-10 | 7 files |

**WHY 2 implementers:**
- Zero file overlap between workstreams (verified: no shared files)
- Co-locality: Impl-A owns coordinator CREATE + catalog + execution-plan + routing (creator+consumer chain)
- Co-locality: Impl-B owns CLAUDE.md + common-protocol + remaining skills (constitution+protocol chain)
- §6 Interface Contracts (COORDINATOR REFERENCE TABLE) eliminates cross-implementer dependencies

### Task Dependency Graph

```
Implementer A:               Implementer B:
T-1 (5 coordinators)         T-3 (CLAUDE.md §6 + table)
  │                             │
  ├─→ T-2 (catalog)            ├─→ T-6 (brainstorming skill)
  │                             │
  ├─→ T-5 (execution skill)    ├─→ T-8 (write-plan + validation skills)
  │                             │
  ├─→ T-7 (verification skill) T-4 (common-protocol)
  │                             │
  └─→ T-9 (20 agent routing)   └─→ T-10 (layer-boundary)

No cross-implementer dependencies.
Both receive COORDINATOR REFERENCE TABLE (§6) for shared content.
```

### Execution Sequence

```
Lead:   TeamCreate("{feature}-execution")
Lead:   TaskCreate × 10 (T-1 through T-10)
Lead:   Spawn infra-implementer-1 (Implementer A)
Lead:   Spawn infra-implementer-2 (Implementer B)
Lead:   Send [DIRECTIVE] + [INJECTION] (COORDINATOR REFERENCE TABLE + task context)
        ┌──────────────────────────────────────────────────────┐
        │ Understanding Verification (per CLAUDE.md §6, §10)    │
        │                                                        │
        │ Implementer: Reads PT + plan, explains understanding   │
        │ Lead: 1-3 probing questions (Impact Map grounded)      │
        │ Implementer: Defends with specific evidence            │
        │ Lead: Verifies or rejects (max 3 attempts)             │
        │ Implementer: Shares plan, Lead approves → execution    │
        └──────────────────────────────────────────────────────┘
        Implementers: Execute tasks in dependency order
        Implementers: Self-verify → Write L1/L2/L3
        Implementers: Report completion
Lead:   Gate Review (cross-reference validation, §7)
Lead:   Commit (single commit)
Lead:   Shutdown teammates → TeamDelete
```

---

## 2. global-context.md Template

> Lead: Create this as `.agent/teams/{session-id}/global-context.md` at TeamCreate time.

```yaml
---
version: GC-v1
project: Lead Architecture Redesign — Hybrid Coordinator Model
pipeline: Infrastructure (Phase 1 → 6 → 6.V → 9)
current_phase: 6
---
```

```markdown
# Global Context — Lead Architecture Redesign

## Project Summary
Implement the Hybrid Coordinator Model to resolve the BN-1→BN-3→BN-4 cascade.
5 category-level coordinators for multi-agent categories via flat peer messaging (Mode 1).
5 categories remain Lead-direct. Lead catalog read: 976L → ~300L (69% reduction).
Phase 6 per-task context cost: 71% reduction through execution-coordinator review dispatch.

## Architecture Reference
- Phase 3: `.agent/teams/lead-arch-redesign/phase-3/architect-1/L3-full/architecture-design.md`
- Phase 1: `docs/plans/2026-02-11-lead-architecture-redesign.md`
- Implementation: `docs/plans/2026-02-11-lead-architecture-redesign-implementation.md`

## Key Decisions
- AD-8: 5 coordinators (not 10) — single-agent categories don't benefit
- AD-9: execution-coordinator manages cross-category review dispatch
- AD-10: Two-Level Catalog (Level 1 ~300L + Level 2 ~680L)
- AD-11: Delegated understanding verification
- AD-12: Defensive Three-Mode Design (Mode 1 primary)
- AD-13: Standard coordinator template

## Scope
34 files: 5 CREATE + 29 MODIFY. All .claude/ infrastructure. No hooks, no app code.

## Active Teammates
- infra-implementer-1: T-1, T-2, T-5, T-7, T-9 (27 files)
- infra-implementer-2: T-3, T-4, T-6, T-8, T-10 (7 files)
```

---

## 3. File Ownership Assignment

### Implementer A (infra-implementer-1) — 27 files

| # | File | Operation | Task |
|---|------|-----------|------|
| 1 | `.claude/agents/research-coordinator.md` | CREATE | T-1 |
| 2 | `.claude/agents/verification-coordinator.md` | CREATE | T-1 |
| 3 | `.claude/agents/execution-coordinator.md` | CREATE | T-1 |
| 4 | `.claude/agents/testing-coordinator.md` | CREATE | T-1 |
| 5 | `.claude/agents/infra-quality-coordinator.md` | CREATE | T-1 |
| 6 | `.claude/references/agent-catalog.md` | MODIFY | T-2 |
| 7 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | MODIFY | T-5 |
| 8 | `.claude/skills/verification-pipeline/SKILL.md` | MODIFY | T-7 |
| 9-28 | `.claude/agents/*.md` (20 agent files) | MODIFY | T-9 |

### Implementer B (infra-implementer-2) — 7 files

| # | File | Operation | Task |
|---|------|-----------|------|
| 29 | `.claude/CLAUDE.md` | MODIFY | T-3 |
| 30 | `.claude/references/agent-common-protocol.md` | MODIFY | T-4 |
| 31 | `.claude/skills/brainstorming-pipeline/SKILL.md` | MODIFY | T-6 |
| 32 | `.claude/skills/agent-teams-write-plan/SKILL.md` | MODIFY | T-8 |
| 33 | `.claude/skills/plan-validation-pipeline/SKILL.md` | MODIFY | T-8 |
| 34 | `.claude/references/layer-boundary-model.md` | MODIFY | T-10 |

---

## 4. TaskCreate Definitions

> Lead: Create these 10 tasks via TaskCreate after TeamCreate.

### Task 1: Create 5 Coordinator Agent Definitions

```
subject: "Create 5 coordinator .md files (research, verification, execution, testing, infra-quality)"
description: |
  Create 5 new coordinator agent files following the AD-13 template.
  See §5.1 in implementation plan for COMPLETE file content.
  Each coordinator has: YAML frontmatter (tools: Read, Glob, Grep, Write, TaskList, TaskGet,
  sequential-thinking; disallowed: TaskCreate, TaskUpdate, Edit, Bash), Role, Before Starting
  Work, Worker Management, Communication Protocol, Failure Handling, Output Format, Constraints.
  execution-coordinator is the most complex (Review Dispatch Protocol).
  Files: .claude/agents/{research,verification,execution,testing,infra-quality}-coordinator.md
  blockedBy: []
  blocks: [T-2, T-5, T-7, T-9]
  AC-0: Verify plan §5.1 before writing
  AC-1: All 5 files have identical YAML tool set (AD-13)
  AC-2: execution-coordinator has Review Dispatch Protocol section
  AC-3: All reference agent-common-protocol.md
activeForm: "Creating 5 coordinator agent definitions"
```

### Task 2: Restructure agent-catalog.md into Two-Level Catalog

```
subject: "Restructure agent-catalog.md into Two-Level Catalog (AD-10)"
description: |
  Restructure the 977-line agent-catalog.md into Level 1 (~300L, Lead reads) + Level 2 (~680L, on-demand).
  See §5.2 in implementation plan for restructure specification.
  Level 1: P1 Framework + WHEN + Chain + 5 Coordinator Descriptions + Lead-Direct summaries
    + Agent Matrix + Spawn Quick Reference
  Level 2: "## Agent Full Descriptions (Level 2)" header + current 22 agent descriptions
    reorganized by category (10 category sections)
  File: .claude/references/agent-catalog.md
  blockedBy: [T-1]
  blocks: []
  AC-0: Verify plan §5.2 before editing
  AC-1: Level 1 (first ~300L) contains all coordinator descriptions
  AC-2: Level 2 header clearly separates mandatory vs on-demand reading
  AC-3: All existing agent descriptions preserved (reorganized, not deleted)
  AC-4: Total file size ~975L (similar to current)
activeForm: "Restructuring agent-catalog.md into Two-Level Catalog"
```

### Task 3: Revise CLAUDE.md (Custom Agents Reference + §4 + §6)

```
subject: "Revise CLAUDE.md Custom Agents Reference table, §4 Communication, and §6 How Lead Operates"
description: |
  Three changes to CLAUDE.md:
  1. Custom Agents Reference (lines 15-41): Replace with two sub-tables (Coordinated + Lead-Direct)
     + coordinator spawning rules. Title: "27 Agents, 10 Categories, Hybrid Coordinator Model"
  2. §4 Communication: Rewrite to include coordinator communication flows
  3. §6 How Lead Operates (lines 108-193): Complete rewrite with coordinator routing model
  See §5.3 in implementation plan for complete replacement text.
  File: .claude/CLAUDE.md
  blockedBy: []
  blocks: [T-6, T-8]
  AC-0: Verify plan §5.3 before editing
  AC-1: Custom Agents Reference has Coordinated + Lead-Direct sub-tables
  AC-2: §4 has coordinator communication flows
  AC-3: §6 has Agent Selection and Routing with coordinator route
  AC-4: §6 has Coordinator Management subsection
  AC-5: §6 Before Spawning references "Level 1, first ~300 lines"
activeForm: "Revising CLAUDE.md for coordinator model"
```

### Task 4: Update agent-common-protocol.md

```
subject: "Add 'Working with Coordinators' section to agent-common-protocol.md"
description: |
  Insert new "Working with Coordinators" section after "When You Receive a Task Assignment"
  (after line 20, before the "---" separator).
  See §5.4 in implementation plan for section content.
  File: .claude/references/agent-common-protocol.md
  blockedBy: []
  blocks: []
  AC-0: Verify plan §5.4 before editing
  AC-1: Section placed between "When You Receive a Task Assignment" and "When Context Changes Mid-Work"
  AC-2: Covers: coordinator as primary contact, Lead emergency contact, fallback protocol
activeForm: "Updating agent-common-protocol.md with coordinator section"
```

### Task 5: Update execution-plan SKILL.md for Coordinator Model

```
subject: "Update agent-teams-execution-plan SKILL.md for execution-coordinator model (AD-9)"
description: |
  This is the highest-risk change. Rewrite §6.2-6.7 for coordinator-mediated execution.
  The inner loop (implement → review → fix) moves into execution-coordinator's context.
  See §5.5 in implementation plan for detailed section-by-section specs.
  Key changes:
  - §6.2: Add execution-coordinator to spawn sequence
  - §6.3: Coordinator spawn + delegated verification + review template injection
  - §6.4: Rewrite as coordinator-managed (biggest change)
  - §6.5: Coordinator handles day-to-day monitoring, Lead handles escalation
  - §6.6: Gate 6 reads coordinator consolidated L1/L2
  - §6.7: Shutdown includes coordinator
  - Cross-Cutting: Update agent list
  - Never list: Update
  File: .claude/skills/agent-teams-execution-plan/SKILL.md
  blockedBy: [T-1]
  blocks: []
  AC-0: Verify plan §5.5 before editing
  AC-1: §6.2 spawns execution-coordinator
  AC-2: §6.3 includes review template injection in coordinator directive
  AC-3: §6.4 inner loop managed by coordinator (Lead receives consolidated reports)
  AC-4: Spec-reviewer/code-reviewer prompt templates remain in SKILL.md
  AC-5: Fix loop rules (max 3) enforced by coordinator
activeForm: "Updating execution-plan SKILL.md for coordinator model"
```

### Task 6: Update brainstorming-pipeline SKILL.md

```
subject: "Update brainstorming-pipeline SKILL.md Phase 2 for research-coordinator"
description: |
  Update Phase 2 (Deep Research) orchestration to use research-coordinator.
  See §5.6 in implementation plan for section-by-section specs.
  Phase 3 (Architecture) is UNCHANGED — architect is Lead-direct.
  File: .claude/skills/brainstorming-pipeline/SKILL.md
  blockedBy: [T-3]
  blocks: []
  AC-0: Verify plan §5.6 before editing
  AC-1: §2.2 spawns research-coordinator first
  AC-2: §2.3 coordinator distributes research questions
  AC-3: §2.4 coordinator monitors progress
  AC-4: §2.5 Gate 2 reads coordinator consolidated L1/L2
  AC-5: Phase 3 section unchanged
activeForm: "Updating brainstorming-pipeline for research-coordinator"
```

### Task 7: Update verification-pipeline SKILL.md

```
subject: "Update verification-pipeline SKILL.md for testing-coordinator"
description: |
  Update Phase 7-8 orchestration to use testing-coordinator.
  See §5.7 in implementation plan for section-by-section specs.
  File: .claude/skills/verification-pipeline/SKILL.md
  blockedBy: [T-1]
  blocks: []
  AC-0: Verify plan §5.7 before editing
  AC-1: Phase 7.3 spawns testing-coordinator
  AC-2: Testing-coordinator manages tester (Phase 7) then integrator (Phase 8)
  AC-3: Sequential lifecycle enforced by coordinator
  AC-4: Gate 7/8 reads coordinator consolidated L1/L2
activeForm: "Updating verification-pipeline for testing-coordinator"
```

### Task 8: Update write-plan and plan-validation SKILL.md files

```
subject: "Update write-plan and plan-validation SKILL.md for coordinator references"
description: |
  Minor §6 reference updates to both skills. Architect and devils-advocate are Lead-direct,
  so orchestration logic is unchanged. Only update references to §6 routing model.
  See §5.8 in implementation plan for specific changes.
  Files: .claude/skills/agent-teams-write-plan/SKILL.md,
         .claude/skills/plan-validation-pipeline/SKILL.md
  blockedBy: [T-3]
  blocks: []
  AC-0: Verify plan §5.8 before editing
  AC-1: Any reference to "10 categories" updated to reflect coordinator model
  AC-2: Spawning rules reference coordinator routing where relevant
activeForm: "Updating write-plan and plan-validation skills"
```

### Task 9: Update 20 Agent .md Routing Instructions

```
subject: "Update routing instructions in 20 agent .md files for coordinator-aware routing"
description: |
  Mechanical routing update across 20 agent .md files.
  See §5.9 in implementation plan for pattern + file list.
  Pattern A (18 files): "Message Lead with:" → "Message your coordinator (or Lead if assigned directly) with:"
  Pattern B (2 files: spec-reviewer, code-reviewer):
    "Message Lead confirming" → "Message your coordinator (or Lead if assigned directly) confirming"
  Excluded: devils-advocate.md (no "Message Lead" pattern), execution-monitor.md (Lead-direct, keep current)
  Files: 20 agent .md files (see §5.9 for complete list)
  blockedBy: [T-1, T-4]
  blocks: []
  AC-0: Verify plan §5.9 before editing
  AC-1: All 20 files have coordinator-aware routing
  AC-2: devils-advocate.md and execution-monitor.md NOT modified
  AC-3: Pattern is consistent across all 20 files
activeForm: "Updating routing in 20 agent .md files"
```

### Task 10: Update layer-boundary-model.md

```
subject: "Add coordinator dimension to layer-boundary-model.md"
description: |
  Add coordinator orchestration as a new dimension in the 5-Dimension Coverage model.
  See §5.10 in implementation plan for specific content.
  File: .claude/references/layer-boundary-model.md
  blockedBy: []
  blocks: []
  AC-0: Verify plan §5.10 before editing
  AC-1: Coordinator dimension added with Layer 1 (NL, flat model) and Layer 2 (structural, state machine)
activeForm: "Updating layer-boundary-model.md with coordinator dimension"
```

---

## 5. Edit Specifications

### 5.1 Task 1: Create 5 Coordinator Agent Definitions [VL-HIGH]

All 5 coordinators share the AD-13 template (same YAML frontmatter, same tool set).
Category-specific content differs. **Write complete file content as shown below.**

#### 5.1.1 research-coordinator.md — CREATE

**File:** `.claude/agents/research-coordinator.md`

```markdown
---
name: research-coordinator
description: |
  Manages parallel research across codebase, external, and audit domains.
  Distributes research questions, monitors progress, consolidates findings.
  Spawned in Phase 2 (Deep Research). Max 1 instance.
model: opus
permissionMode: default
memory: user
color: cyan
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
# Research Coordinator

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You coordinate parallel research across your category's workers (codebase-researcher,
external-researcher, auditor). You distribute research questions by domain, monitor
progress, consolidate findings into a unified research report, and report to Lead.

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- Your understanding of the research scope and questions
- Which worker types you expect to need (local, external, audit)
- How you plan to distribute questions across workers

## Worker Management
Lead pre-spawns your workers and informs you of their names. You manage them via SendMessage.

### Assigning Work
For each worker:
1. Send a work assignment with: research question, scope, expected deliverables
2. Include the Impact Map excerpt (from your directive) for their verification
3. Verify their understanding with 1-2 probing questions focused on:
   - Research scope (do they know what to look for?)
   - Methodology (are they using the right approach for this domain?)
4. Report verification status to Lead

### Monitoring Progress
- Read worker L1/L2 files periodically to track progress
- If a worker is silent for >20 min, send a status query
- If a worker reports blocking issues, evaluate and relay to Lead if needed

### Consolidating Results
After all workers report completion:
1. Read all worker L2 summaries
2. Cross-reference findings across domains
3. Identify gaps requiring additional research
4. Write consolidated L1/L2/L3 with unified findings

## Communication Protocol
- **You → Workers:** Work assignments, probing questions, course corrections
- **Workers → You:** Understanding confirmation, progress reports, completion reports
- **You → Lead:** Verification status, consolidated findings, blocking issues
- **Lead → You:** Scope updates, PT version changes, shutdown requests

## Failure Handling
- **Worker unresponsive (>20 min):** Send status query. >30 min: alert Lead.
- **Worker quality insufficient:** Send specific correction. Max 3 attempts, then alert Lead.
- **Own context pressure:** Write L1/L2 immediately, alert Lead for re-spawn.
- **Worker reports cross-domain need:** Evaluate if within your category. If not, relay to Lead.

## Output Format
- **L1-index.yaml:** Consolidated findings, per-worker summary, gaps identified
- **L2-summary.md:** Unified research narrative with per-domain sections, Evidence Sources
- **L3-full/:** Worker L1/L2 copies, raw data, cross-reference analysis

## Constraints
- Coordination only — no code modification, no infrastructure file edits
- No task creation/updates (Lead-only)
- Write is for L1/L2/L3 output files only
- Write L1/L2/L3 proactively
```

#### 5.1.2 verification-coordinator.md — CREATE

**File:** `.claude/agents/verification-coordinator.md`

```markdown
---
name: verification-coordinator
description: |
  Manages parallel verification across static, relational, and behavioral dimensions.
  Distributes verification scope, cross-references findings, consolidates scores.
  Spawned in Phase 2b (Verification). Max 1 instance.
model: opus
permissionMode: default
memory: user
color: cyan
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
# Verification Coordinator

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You coordinate parallel verification across your category's workers (static-verifier,
relational-verifier, behavioral-verifier). You distribute verification dimensions,
cross-reference findings between dimensions, and consolidate into a unified report.

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- Your understanding of the verification scope and target documents
- Which dimensions need verification
- The authoritative sources you'll verify against

## Worker Management
Lead pre-spawns your workers and informs you of their names. You manage them via SendMessage.

### Assigning Work
For each verifier:
1. Send dimension assignment with: documents to verify, authoritative sources, scope
2. Include the Impact Map excerpt (from your directive) for their verification
3. Verify their understanding with 1-2 probing questions:
   - Do they know what claims to check?
   - Do they understand which sources are authoritative?
4. Report verification status to Lead

### Monitoring Progress
- Read worker L1/L2 files periodically to track progress
- If a worker is silent for >20 min, send a status query

### Cross-Dimension Synthesis
After workers report findings:
1. Check if a structural error (static) implies relational errors
2. Check if a behavioral finding contradicts structural claims
3. Flag cross-dimension inconsistencies in consolidated report

### Consolidating Results
1. Read all worker L2 summaries
2. Perform cross-dimension synthesis
3. Compute per-dimension scores
4. Write consolidated L1/L2/L3

## Communication Protocol
- **You → Workers:** Dimension assignments, probing questions, corrections
- **Workers → You:** Understanding confirmation, progress, findings
- **You → Lead:** Verification status, consolidated findings with scores
- **Lead → You:** Scope updates, PT changes, shutdown requests

## Failure Handling
- **Worker unresponsive (>20 min):** Send status query. >30 min: alert Lead.
- **Worker quality insufficient:** Send specific correction. Max 3 attempts, then alert Lead.
- **Own context pressure:** Write L1/L2 immediately, alert Lead for re-spawn.

## Output Format
- **L1-index.yaml:** Per-dimension scores, cross-dimension findings, `pt_goal_link:` where applicable
- **L2-summary.md:** Unified verification narrative, dimension scores, Evidence Sources
- **L3-full/:** Worker L2 copies, cross-dimension analysis, raw verification data

## Constraints
- Coordination only — no code modification, no infrastructure file edits
- No task creation/updates (Lead-only)
- Write is for L1/L2/L3 output files only
- Write L1/L2/L3 proactively
```

#### 5.1.3 execution-coordinator.md — CREATE

**File:** `.claude/agents/execution-coordinator.md`

This is the **most complex coordinator** — manages the full Phase 6 lifecycle including
two-stage review dispatch via peer messaging (AD-9).

```markdown
---
name: execution-coordinator
description: |
  Manages full Phase 6 implementation lifecycle including two-stage review dispatch.
  Coordinates implementers, dispatches spec-reviewer and code-reviewer via peer messaging,
  manages fix loops, and provides consolidated reporting to Lead.
  Spawned in Phase 6 (Implementation). Max 1 instance.
model: opus
permissionMode: default
memory: user
color: yellow
maxTurns: 100
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
# Execution Coordinator

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You manage the full Phase 6 implementation lifecycle: task distribution to implementers,
two-stage review dispatch (spec-reviewer + code-reviewer) via peer messaging, fix loop
management, and consolidated progress reporting to Lead. Your single responsibility is
"ensuring code changes are implemented correctly through the implementation-review lifecycle."

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- Your understanding of the implementation plan scope
- The task distribution strategy (per component grouping from Lead's directive)
- The review dispatch protocol (spec → code, fix loop rules)
- How you'll handle cross-boundary escalation

## Worker Management
Lead pre-spawns all workers: implementers (1-4), spec-reviewer (1-2), code-reviewer (1-2).
Lead informs you of all worker names. You manage them via SendMessage.

### Verifying Implementer Understanding
For each implementer:
1. Send task assignment with: plan §5 spec, file ownership, review expectations
2. Include the Impact Map excerpt (from your directive) for their verification
3. Verify understanding with 1-2 probing questions focused on:
   - Interconnection awareness (how do their files connect to the system?)
   - Failure reasoning (what breaks if their changes are wrong?)
4. Approve implementer's plan before execution begins
5. Report verification status to Lead

### Task Lifecycle (per task)
Use `sequential-thinking` for each stage transition decision.

```
1. Send task assignment to implementer:
   "Implement Task {N}: {spec from plan §5}"
   Include: file ownership, acceptance criteria, review expectations

2. Implementer executes → reports completion to you:
   "Task {N} complete: {summary, self-review report, files changed}"

3. Stage 1 — Spec Review:
   Construct review request from template (in your directive):
   Send to spec-reviewer via SendMessage:
   "Review Task {N} implementation against specification.
    Specification: {plan §5 spec for this task}
    Implementer Report: {self-review report}
    Files to Inspect: {files within implementer's ownership}"

4. spec-reviewer responds: PASS or FAIL
   - FAIL → relay fix instructions to implementer (max 3 iterations)
   - 3x FAIL → escalate to Lead as BLOCKED
   - PASS → proceed to Stage 2

5. Stage 2 — Code Review:
   Construct review request from template (in your directive):
   Send to code-reviewer via SendMessage:
   "Review Task {N} for code quality and production readiness.
    Implementer Report: {self-review report}
    Plan/Requirements: {plan §5 spec for this task}
    Files to Inspect: {files within implementer's ownership}"

6. code-reviewer responds: PASS or FAIL
   - FAIL → relay fix instructions to implementer (max 3 iterations)
   - 3x FAIL → escalate to Lead as BLOCKED
   - PASS → task complete

7. Send consolidated report to Lead:
   "Task {N}: PASS
    - Spec review: PASS ({iteration_count} iterations)
    - Quality review: PASS
    - Files: {list}
    Proceeding to Task {N+1}."
```

### Task Ordering
- For dependent tasks within same implementer: enforce topological order
- For independent tasks across implementers: allow parallel execution
- Track task status: pending → in_progress → review → complete

## Communication Protocol
- **You → Implementers:** Task assignments, fix instructions, continuation orders
- **You → Reviewers:** Review requests (constructed from templates in your directive)
- **Implementers → You:** Completion reports, blocking issues, context pressure alerts
- **Reviewers → You:** Review results (PASS/FAIL with evidence)
- **You → Lead:** Consolidated progress reports, escalations, completion report
- **Lead → You:** Scope updates, PT changes, intervention, shutdown

## Failure Handling
- **Implementer unresponsive (>30 min):** Send status query. >40 min: alert Lead.
- **Reviewer unresponsive (>15 min):** Alert Lead for re-dispatch.
- **Fix loop exhausted (3x):** Report BLOCKED to Lead with evidence.
- **Cross-boundary need:** Implementer needs file outside ownership → escalate to Lead
  immediately. Never attempt cross-boundary resolution.
- **Own context pressure:** Write L1/L2 immediately, alert Lead for re-spawn.

## Output Format
- **L1-index.yaml:** Per-task summary (status, review results, files), overall progress
- **L2-summary.md:** Implementation narrative with per-task review results (include
  reviewer raw output), Evidence Sources
- **L3-full/:** Implementer L1/L2 copies, reviewer outputs, consolidated diffs

## Constraints
- Coordination only — no code modification, no infrastructure file edits
- No task creation/updates (Lead-only)
- Write is for L1/L2/L3 output files only
- Never attempt cross-boundary resolution (Lead or integrator only)
- Fix loop max 3 per review stage, then escalate
- Spec review must PASS before dispatching code review
- Write L1/L2/L3 proactively
```

#### 5.1.4 testing-coordinator.md — CREATE

**File:** `.claude/agents/testing-coordinator.md`

```markdown
---
name: testing-coordinator
description: |
  Manages sequential testing and integration lifecycle.
  Coordinates tester then integrator in strict order.
  Spawned in Phase 7-8 (Testing & Integration). Max 1 instance.
model: opus
permissionMode: default
memory: user
color: cyan
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
# Testing Coordinator

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You manage the sequential testing and integration lifecycle. In Phase 7, you coordinate
tester(s) for test execution. In Phase 8, you coordinate the integrator for cross-boundary
merges. Tester MUST complete before integrator starts — you enforce this ordering.

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- Your understanding of the test scope and acceptance criteria
- The integration points (if Phase 8 applies)
- The sequential lifecycle plan (Phase 7 → Phase 8)

## Worker Management
Lead pre-spawns workers and informs you of their names. You manage them via SendMessage.

### Phase 7: Test Execution
1. Send test scope to tester: targets, acceptance criteria, interface specs
2. Include Impact Map excerpt for tester verification
3. Verify tester understanding (1-2 probing questions on test coverage strategy)
4. Monitor tester progress (read L1/L2)
5. On tester completion: consolidate test results, report to Lead

### Phase 8: Integration (conditional — only if 2+ implementers in Phase 6)
1. After Phase 7 completes: send integration scope to integrator
2. Include: Phase 6 outputs, Phase 7 results, interface specs
3. Verify integrator understanding (1-2 probing questions on merge strategy)
4. Integrator submits plan → you review and approve (or relay to Lead for complex cases)
5. Monitor integrator progress (read L1/L2)
6. On integrator completion: consolidate integration report, report to Lead

## Communication Protocol
- **You → Workers:** Test/integration assignments, probing questions, corrections
- **Workers → You:** Understanding confirmation, progress, completion reports
- **You → Lead:** Phase 7/8 consolidated results, escalations
- **Lead → You:** Scope updates, PT changes, shutdown requests

## Failure Handling
- **Worker unresponsive (>20 min):** Send status query. >30 min: alert Lead.
- **Test failures found:** Consolidate results, report to Lead for user decision.
- **Integration conflicts:** Relay to Lead for cross-boundary resolution guidance.
- **Own context pressure:** Write L1/L2 immediately, alert Lead for re-spawn.

## Output Format
- **L1-index.yaml:** Test results summary (pass/fail/skip), integration status
- **L2-summary.md:** Test narrative, failure analysis, integration report, Evidence Sources
- **L3-full/:** Worker L1/L2 copies, test results, integration logs

## Constraints
- Coordination only — no code modification, no infrastructure file edits
- No task creation/updates (Lead-only)
- Tester MUST complete before integrator starts (strict ordering)
- Write is for L1/L2/L3 output files only
- Write L1/L2/L3 proactively
```

#### 5.1.5 infra-quality-coordinator.md — CREATE

**File:** `.claude/agents/infra-quality-coordinator.md`

```markdown
---
name: infra-quality-coordinator
description: |
  Manages parallel INFRA quality analysis across 4 dimensions.
  Coordinates static, relational, behavioral, and impact analysts.
  Spawned cross-cutting (any phase). Max 1 instance.
model: opus
permissionMode: default
memory: user
color: cyan
maxTurns: 50
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
# INFRA Quality Coordinator

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.

## Role
You coordinate parallel INFRA quality analysis across 4 dimensions: static (naming,
config), relational (coupling, dependencies), behavioral (lifecycle, protocol), and
impact (ripple prediction). All 4 dimensions can run in parallel. You consolidate
per-dimension scores into a unified INFRA quality score.

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- Your understanding of the INFRA analysis scope
- Which dimensions need analysis (may not always be all 4)
- The target files/components for analysis

## Worker Management
Lead pre-spawns analysts and informs you of their names. You manage them via SendMessage.

### Assigning Work
For each analyst:
1. Send dimension assignment with: target scope, analysis criteria
2. Include the Impact Map excerpt for their domain
3. Verify understanding (1-2 probing questions on analysis approach)
4. Report verification status to Lead

### Monitoring Progress
- All 4 dimensions run independently — no ordering constraint
- Read worker L1/L2 files periodically
- If a worker is silent for >20 min, send a status query

### Score Aggregation
After all analysts report:
1. Collect per-dimension scores
2. Compute weighted average:
   - Static: weight 1.0 (foundational)
   - Relational: weight 1.0 (foundational)
   - Behavioral: weight 0.9
   - Impact: weight 0.8 (predictive, inherently uncertain)
3. Cross-dimension synthesis (structural errors may imply relational issues)
4. Write consolidated L1/L2/L3

## Communication Protocol
- **You → Workers:** Dimension assignments, probing questions
- **Workers → You:** Understanding confirmation, findings, scores
- **You → Lead:** Consolidated INFRA score, per-dimension findings
- **Lead → You:** Scope updates, shutdown requests

## Failure Handling
- **Worker unresponsive (>20 min):** Send status query. >30 min: alert Lead.
- **Worker quality insufficient:** Send specific correction. Max 3 attempts, then alert Lead.
- **Own context pressure:** Write L1/L2 immediately, alert Lead for re-spawn.

## Output Format
- **L1-index.yaml:** Per-dimension scores, weighted average, critical findings
- **L2-summary.md:** INFRA quality narrative, per-dimension analysis, Evidence Sources
- **L3-full/:** Worker L2 copies, cross-dimension synthesis, score calculation

## Constraints
- Coordination only — no code modification, no infrastructure file edits
- No task creation/updates (Lead-only)
- Write is for L1/L2/L3 output files only
- Write L1/L2/L3 proactively
```

---

### 5.2 Task 2: Restructure agent-catalog.md [VL-MED]

**File:** `.claude/references/agent-catalog.md` (currently 977L)

**Restructure Strategy:** Same file, two-level structure with clear boundary header.

#### Level 1 Content (~300L) — Preserved + New

The first ~300 lines of the restructured file should contain:

1. **P1 Framework** (~14L) — PRESERVE from current lines 1-14 (no change)
2. **WHEN to Spawn** (~30L) — UPDATE: add coordinator routing decision
   - Before the existing WHEN table, add:
   ```markdown
   ### Routing Decision
   Before checking WHEN triggers, determine routing:
   - Category has a coordinator (Research, Verification, Implementation, Testing, INFRA Quality)?
     → Route through coordinator. Lead spawns coordinator + pre-spawns workers.
   - Category is Lead-direct (Impact, Architecture, Planning, Review, Monitoring)?
     → Lead spawns and manages agent directly.
   ```
3. **Agent Dependency Chain** (~25L) — UPDATE: add coordinator layer
   ```markdown
   ### Dependency Chain (with Coordinator Layer)
   P2: Lead → research-coordinator → {codebase-researcher, external-researcher, auditor}
   P2b: Lead → verification-coordinator → {static-verifier, relational-verifier, behavioral-verifier}
   P2d: Lead → impact-verifier, dynamic-impact-analyst (direct)
   P3: Lead → architect (direct)
   P4: Lead → plan-writer (direct) OR architect (direct)
   P5: Lead → devils-advocate (direct)
   P6: Lead → execution-coordinator → {implementer(s), spec-reviewer, code-reviewer}
   P6+: Lead → execution-monitor (direct)
   P7: Lead → testing-coordinator → {tester}
   P8: Lead → testing-coordinator → {integrator}
   X-CUT: Lead → infra-quality-coordinator → {4 INFRA analysts}
   ```
4. **Coordinator Descriptions** (5 × ~25L = ~125L) — NEW
   For each coordinator, include:
   ```markdown
   #### {name}-coordinator
   **Role:** {1-line description}
   **Workers:** {agent list}
   **Phase:** {phase(s)}
   **When:** {spawn trigger}
   **Protocol:** Lead assigns scope → coordinator distributes → monitors → consolidates → reports
   **Tools:** Read, Glob, Grep, Write, TaskList, TaskGet, sequential-thinking
   **Key capability:** {category-specific, e.g., "Cross-category review dispatch via peer messaging" for execution-coordinator}
   ```
5. **Lead-Direct Agent Summaries** (~75L) — CONDENSE from current Full Descriptions
   For each Lead-direct agent (architect, plan-writer, impact-verifier, dynamic-impact-analyst,
   devils-advocate, execution-monitor), include a ~10L summary:
   ```markdown
   #### architect (Lead-direct)
   **Role:** {1-line from current description}
   **Phase:** 3, 4
   **When:** {from current WHEN section}
   **Tools:** {tool list}
   ```
   Note about review agents:
   ```markdown
   #### Review Agents (spec-reviewer, code-reviewer)
   Dispatched by execution-coordinator during Phase 6 (via peer messaging),
   or by Lead directly in other contexts. See execution-coordinator description.
   ```
6. **Agent Matrix** (~30L) — UPDATE to include 5 coordinators
7. **Spawn Quick Reference** (~30L) — UPDATE with coordinator spawn template:
   ```markdown
   ### Coordinator Spawn Template
   Task(subagent_type="{name}-coordinator", name="{id}", mode="default", team_name="{team}")
   Directive includes: PT context, Impact Map excerpt, worker names (after pre-spawn),
   task scope, verification criteria, category-specific context.
   For execution-coordinator: also include review prompt templates and fix loop rules.
   ```

#### Level 2 Boundary

After Level 1 content, insert clear separator:

```markdown
---

## Agent Full Descriptions (Level 2)

> **Reading guide:** Level 2 is read on-demand by coordinators (to understand their workers)
> or by Lead (when needing category detail or in fallback mode).
> Lead's mandatory pre-orchestration read covers Level 1 only (first ~300 lines).
```

#### Level 2 Content (~680L) — Reorganized

Move current "Agent Full Descriptions" content into category-organized sections:

```markdown
### Category 1: Research
{codebase-researcher full description from current}
{external-researcher full description from current}
{auditor full description from current}

### Category 2: Verification
{static-verifier, relational-verifier, behavioral-verifier}

### Category 3: Impact
{impact-verifier, dynamic-impact-analyst}

### Category 4: Architecture
{architect}

### Category 5: Planning
{plan-writer}

### Category 6: Review
{devils-advocate, spec-reviewer, code-reviewer}

### Category 7: Implementation
{implementer, infra-implementer}

### Category 8: Testing & Integration
{tester, integrator}

### Category 9: INFRA Quality
{infra-static-analyst, infra-relational-analyst, infra-behavioral-analyst, infra-impact-analyst}

### Category 10: Monitoring
{execution-monitor}
```

**No content deletion** — all 22 current agent descriptions are preserved, just reorganized
by category with category headers. Estimated total: ~975L (similar to current 977L).

---

### 5.3 Task 3: Revise CLAUDE.md [VL-HIGH]

**File:** `.claude/CLAUDE.md`

Three edit operations on this file:

#### 5.3.1 Custom Agents Reference (Replace lines 15-41)

**old_string:**
```markdown
### Custom Agents Reference — 22 Agents, 10 Categories

All agents registered in `.claude/agents/*.md`. Use exact `subagent_type` to spawn.

**Phase dependency chain:** P2 Research → P2b Verification → P2d Impact → P3 Architecture → P4 Design → P5 Validation → P6 Implementation ↔ P6+ Monitoring → P7 Testing → P8 Integration
> P2b can overlap P2 (verify as research arrives). P2d can overlap P3 (impact alongside architecture).

| # | Category | Phase | `subagent_type` agents | When to spawn |
|---|----------|-------|------------------------|---------------|
| 1 | Research | 2 | `codebase-researcher` · `external-researcher` · `auditor` | Local code · Web docs · Inventory/gaps |
| 2 | Verification | 2b | `static-verifier` · `relational-verifier` · `behavioral-verifier` | Schema claims · Dependency claims · Action/rule claims |
| 3 | Impact | 2d, 6+ | `impact-verifier` · `dynamic-impact-analyst` | Correction cascade · Pre-impl change prediction |
| 4 | Architecture | 3, 4 | `architect` | ADRs, risk matrices, component design |
| 5 | Planning | 4 | `plan-writer` | File assignments, interface specs, task breakdown |
| 6 | Review | 5, 6 | `devils-advocate` · `spec-reviewer` · `code-reviewer` | Challenge design · Spec compliance · Code quality |
| 7 | Implementation | 6 | `implementer` · `infra-implementer` | App source code · .claude/ infrastructure files |
| 8 | Testing & Integration | 7, 8 | `tester` · `integrator` | Test creation/execution · Cross-boundary merge |
| 9 | INFRA Quality | Cross-cutting | `infra-static-analyst` · `infra-relational-analyst` · `infra-behavioral-analyst` · `infra-impact-analyst` | Config/naming · Coupling · Lifecycle · Ripple analysis |
| — | Monitoring | 6+ | `execution-monitor` | Real-time drift/deadlock detection during P6 |
| — | Built-in | any | `claude-code-guide` | CC docs/features (not a custom agent) |

**Spawning rules:**
- `subagent_type`: exact name from table — never generic built-ins (Explore, general-purpose)
- `mode: "default"` always (BUG-001: `plan` blocks MCP tools)
- Team context: include `team_name` and `name` parameters
- Core (pipeline-spawned): architect, devils-advocate, implementer, infra-implementer, tester, integrator
- Extended (Lead per need): all 16 others — tool matrix in `agent-catalog.md`
```

**new_string:**
```markdown
### Custom Agents Reference — 27 Agents, 10 Categories, Hybrid Coordinator Model

All agents registered in `.claude/agents/*.md`. Use exact `subagent_type` to spawn.

**Phase dependency chain:** P2 Research → P2b Verification → P2d Impact → P3 Architecture → P4 Design → P5 Validation → P6 Implementation ↔ P6+ Monitoring → P7 Testing → P8 Integration
> P2b can overlap P2 (verify as research arrives). P2d can overlap P3 (impact alongside architecture).

**Coordinated Categories (route through coordinator):**

| # | Category | Phase | Coordinator | Workers | When |
|---|----------|-------|-------------|---------|------|
| 1 | Research | 2 | `research-coordinator` | `codebase-researcher` · `external-researcher` · `auditor` | 2+ research questions |
| 2 | Verification | 2b | `verification-coordinator` | `static-verifier` · `relational-verifier` · `behavioral-verifier` | Multi-dimension verification |
| 7 | Implementation | 6 | `execution-coordinator` | `implementer` · `infra-implementer` + `spec-reviewer` · `code-reviewer` | Implementation plan ready |
| 8 | Testing | 7, 8 | `testing-coordinator` | `tester` · `integrator` | Phase 6 output ready |
| 9 | INFRA Quality | X-CUT | `infra-quality-coordinator` | `infra-static-analyst` · `infra-relational-analyst` · `infra-behavioral-analyst` · `infra-impact-analyst` | INFRA analysis needed |

**Lead-Direct Categories (Lead manages directly):**

| # | Category | Phase | `subagent_type` agents | When |
|---|----------|-------|------------------------|------|
| 3 | Impact | 2d, 6+ | `impact-verifier` · `dynamic-impact-analyst` | Correction cascade · Change prediction |
| 4 | Architecture | 3, 4 | `architect` | ADRs, risk matrices, component design |
| 5 | Planning | 4 | `plan-writer` | File assignments, interface specs |
| 6 | Review | 5, 6 | `devils-advocate` · `spec-reviewer` · `code-reviewer` | Challenge design · Spec/code quality |
| — | Monitoring | 6+ | `execution-monitor` | Real-time drift detection |
| — | Built-in | any | `claude-code-guide` | CC docs/features (not custom) |

> Note: spec-reviewer and code-reviewer are dispatched by execution-coordinator during
> Phase 6 via peer messaging, or by Lead directly in other contexts.

**Spawning rules:**
- `subagent_type`: exact name from tables — never generic built-ins (Explore, general-purpose)
- `mode: "default"` always (BUG-001: `plan` blocks MCP tools)
- Team context: include `team_name` and `name` parameters
- **Coordinator spawn:** Lead spawns coordinator + pre-spawns workers, informs coordinator of worker names
- **Lead-direct spawn:** Lead spawns agent directly (unchanged from current)
- Core (pipeline-spawned): coordinators + architect, devils-advocate, implementer, infra-implementer, tester, integrator
- Extended (Lead per need): remaining agents — tool matrix in `agent-catalog.md`
```

#### 5.3.2 §4 Communication (Replace entire section)

**old_string:**
```markdown
## 4. Communication

Communication flows in three directions:

**Lead → Teammate:** Task assignments with PERMANENT Task ID and task-specific context,
feedback and corrections, probing questions to verify understanding (grounded in the
Codebase Impact Map), approvals or rejections, context updates when PT version changes.

**Teammate → Lead:** Understanding of assigned task (referencing Impact Map), status updates,
implementation plans (before code changes), responses to probing questions, blocking issues.

**Lead → All:** Phase transition announcements.
```

**new_string:**
```markdown
## 4. Communication

Communication flows through coordinators for coordinated categories and directly for Lead-direct:

**Lead → Coordinator:** Work scope with PT context and Impact Map excerpt, probing questions,
approvals, context updates when PT version changes. Coordinator relays to workers.

**Lead → Lead-Direct Agent:** Task assignments with full PT context and Impact Map,
probing questions, approvals, context updates. Same as current direct management.

**Coordinator → Lead:** Consolidated progress reports, verification status, escalations,
completion reports with worker output summaries.

**Coordinator → Workers:** Work assignments, probing questions (using Impact Map excerpt),
fix instructions (from review feedback), continuation orders.

**Workers → Coordinator:** Understanding confirmation, progress updates, completion reports,
blocking issues.

**Lead → All:** Phase transition announcements.

**Emergency:** Lead can message any agent directly, bypassing coordinator, when needed.
```

#### 5.3.3 §6 How Lead Operates (Replace entire section, lines 108-193)

**old_string:**
```markdown
## 6. How Lead Operates

### Agent Selection Flow
1. **Parse request** → identify work type (research, design, implementation, review, verification)
2. **Select category** → match to one of 10 categories in Custom Agents Reference
3. **Choose agent** → pick specific agent from category (use WHEN column)
4. **Check spawn readiness** → §6 Before Spawning criteria (clarity, scope, different approach)
5. **Construct directive** → use template from agent-catalog.md § Spawn Quick Reference
6. **Include PT context** → embed PT-v{N} essentials (user intent, impact map, constraints)
7. **Spawn** → `Task(subagent_type="{name}", name="{id}", mode="default", team_name="{team}")`
8. **Verify understanding** → probing questions from Impact Map

### Before Spawning
Read `.claude/references/agent-catalog.md` (§Agent Full Descriptions) before any orchestration cycle.
Understand each agent's full capabilities, tool matrix, and spawn conditions — never
orchestrate from summary tables or memory alone.

Evaluate three concerns: Is the requirement clear enough? (If not, ask the user.)
Is the scope manageable? (If >4 files, split into multiple tasks.
If total estimated read load exceeds 6000 lines, split further.) After a failure,
is the new approach different? (Same approach = same failure.)
Scale teammate count by module or research domain count. Lead only for Phases 1 and 9.

### Assigning Work
Include the PERMANENT Task ID (PT-v{N}) and task-specific context in every assignment.
Embed the essential PT content (user intent, impact map summary, constraints) directly
in the directive — teammates in a team context can only access their team's task list,
not the main list where the PT lives. When the PERMANENT Task changes, send context
updates to affected teammates with the new version number and relevant content changes.

### Verifying Understanding
After a teammate explains their understanding, ask 1-3 open-ended questions appropriate
to their role to test depth of comprehension. Ground your questions in the PERMANENT Task's
Codebase Impact Map — reference documented module dependencies and ripple paths rather
than relying on intuition alone. Focus on interconnection awareness, failure reasoning,
and interface impact. For architecture phases (3/4), also ask for alternative approaches.
If understanding remains insufficient after 3 attempts, re-spawn with clearer context.
Understanding must be verified before approving any implementation plan.

### Monitoring Progress
Read teammate L1/L2/L3 files and compare against the Phase 4 design. Use the Codebase
Impact Map to trace whether changes in one area have unintended effects on dependent modules.
Log cosmetic deviations, re-inject context for interface changes, re-plan for architectural
changes. No gate approval while any teammate has stale context.

### Observability (RTD)
Lead maintains real-time documentation through the RTD system:
- Write an rtd-index.md entry at each Decision Point (gate approvals, task assignments,
  architecture decisions, conflict resolutions, context updates)
- Update `.agent/observability/{slug}/current-dp.txt` before each DP's associated actions
- Read rtd-index.md alongside L1/L2/L3 when monitoring progress — it provides the
  temporal dimension that Impact Map queries need
- The PostToolUse hook automatically captures all tool calls to events.jsonl — no
  manual event logging needed

### Phase Gates
Before approving a phase transition: Do all output artifacts exist? Does quality meet
the next phase's entry conditions? Are there unresolved critical issues? Are L1/L2/L3 generated?

### Status Visualization
When updating orchestration-plan.md, output ASCII status visualization including phase
pipeline, workstream progress, teammate status, and key metrics.

### Coordination Infrastructure
- **PERMANENT Task:** Subject "[PERMANENT] {feature}", task ID assigned at creation
  (find via TaskList). Versioned PT-v{N} (monotonically increasing). Contains: User Intent,
  Codebase Impact Map, Architecture Decisions, Phase Status, Constraints. Lead tracks each
  teammate's confirmed PT version in orchestration-plan.md.
- **L1/L2/L3:** L1 = index (YAML, ≤50 lines). L2 = summary (MD, ≤200 lines). L3 = full detail (directory).
- **Team Memory:** `.agent/teams/{session-id}/TEAM-MEMORY.md`, section-per-role structure.
- **Output directory:**
  ```
  .agent/teams/{session-id}/
  ├── orchestration-plan.md, TEAM-MEMORY.md
  └── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
  ```
- **Observability directory:**
  ```
  .agent/observability/
  ├── .current-project           # Active project slug
  └── {project-slug}/
      ├── manifest.json, rtd-index.md, current-dp.txt, session-registry.json
      └── events/{session}.jsonl
  ```
  Lead initializes at pipeline start. Hooks populate automatically.
  Persists across sessions for project-scoped observability.
```

**new_string:**
```markdown
## 6. How Lead Operates

### Agent Selection and Routing
1. **Parse request** → identify work type (research, design, implementation, review, verification)
2. **Select category** → match to one of 10 categories in Custom Agents Reference
3. **Route decision:**
   - Coordinated categories (1, 2, 7, 8, 9) → route through coordinator
   - Lead-direct categories (3, 4, 5, 6, Monitoring) → spawn agent directly
4. **For coordinator route:**
   a. Coordinator not spawned → spawn coordinator + pre-spawn workers, inform coordinator
   b. Coordinator active → SendMessage with work assignment
   c. Include: PT context, Impact Map excerpt, task details, verification criteria
   d. For execution-coordinator: include review prompt templates and fix loop rules
5. **For Lead-direct route:**
   a. Spawn agent directly (same as current)
   b. Include: PT context, full Impact Map, task details
6. **Verify understanding:**
   - Coordinator: Lead verifies (1-3 probing questions from Impact Map)
   - Workers: Coordinator verifies (1-2 questions, using Impact Map excerpt from Lead)
   - Lead-direct agent: Lead verifies (1-3 probing questions, same as current)

### Before Spawning
Read `.claude/references/agent-catalog.md` (Level 1, first ~300 lines) before any
orchestration cycle. Understand coordinator capabilities, routing model, and worker
summaries — never orchestrate from summary tables or memory alone. Read Level 2
on-demand for category detail.

Evaluate three concerns: Is the requirement clear enough? (If not, ask the user.)
Is the scope manageable? (If >4 files, split into multiple tasks.
If total estimated read load exceeds 6000 lines, split further.) After a failure,
is the new approach different? (Same approach = same failure.)
Scale teammate count by module or research domain count. Lead only for Phases 1 and 9.

### Coordinator Management
Lead tracks active coordinators in orchestration-plan.md:
- Coordinator name, category, workers managed, current task status
- PT version confirmed by coordinator

When a coordinator reports completion:
1. Read coordinator's consolidated L1/L2
2. Evaluate quality against gate criteria
3. Approve, iterate, or escalate

If coordinator becomes unresponsive (>5 min no message):
1. Send status query
2. If no response in 5 more min: switch to Lead-direct mode (Mode 3 fallback)
3. Workers already pre-spawned — Lead messages them directly

### Cross-Cutting Operations (Always Lead-Direct)
These operations bypass coordinators regardless of category:
- **Gate evaluation:** Lead reads cross-category artifacts, evaluates criteria
- **PERMANENT Task updates:** Lead sends to coordinators, who relay to workers
- **Cross-category escalation:** Lead mediates when work crosses category boundaries
- **Emergency intervention:** Lead can message any agent directly when needed

### Assigning Work
Include the PERMANENT Task ID (PT-v{N}) and task-specific context in every assignment.
Embed the essential PT content (user intent, impact map summary, constraints) directly
in the directive — teammates in a team context can only access their team's task list,
not the main list where the PT lives. When the PERMANENT Task changes, send context
updates to affected coordinators, who relay to their workers.

### Verifying Understanding
After a coordinator or Lead-direct agent explains their understanding, ask 1-3 open-ended
questions appropriate to their role to test depth of comprehension. Ground your questions
in the PERMANENT Task's Codebase Impact Map. Focus on interconnection awareness, failure
reasoning, and interface impact. For architecture phases (3/4), also ask for alternative approaches.
If understanding remains insufficient after 3 attempts, re-spawn with clearer context.
Coordinators verify their workers' understanding using Impact Map excerpts provided by Lead.
Lead retains gate-level quality assurance via spot-checks.

### Monitoring Progress
For coordinated categories: read coordinator L1/L2 for consolidated progress.
For Lead-direct agents: read agent L1/L2 directly (unchanged).
Use the Codebase Impact Map to trace cross-category effects.
Log cosmetic deviations, re-inject context for interface changes, re-plan for architectural
changes. No gate approval while any coordinator or agent has stale context.

### Observability (RTD)
Lead maintains real-time documentation through the RTD system:
- Write an rtd-index.md entry at each Decision Point (gate approvals, task assignments,
  architecture decisions, conflict resolutions, context updates)
- Update `.agent/observability/{slug}/current-dp.txt` before each DP's associated actions
- Read rtd-index.md alongside L1/L2/L3 when monitoring progress — it provides the
  temporal dimension that Impact Map queries need
- The PostToolUse hook automatically captures all tool calls to events.jsonl — no
  manual event logging needed

### Phase Gates
Before approving a phase transition: Do all output artifacts exist? Does quality meet
the next phase's entry conditions? Are there unresolved critical issues? Are L1/L2/L3 generated?
For coordinated categories, gate artifacts include coordinator's consolidated L1/L2
plus spot-check of selected worker L1/L2.

### Status Visualization
When updating orchestration-plan.md, output ASCII status visualization including phase
pipeline, workstream progress, teammate status, and key metrics.

### Coordination Infrastructure
- **PERMANENT Task:** Subject "[PERMANENT] {feature}", task ID assigned at creation
  (find via TaskList). Versioned PT-v{N} (monotonically increasing). Contains: User Intent,
  Codebase Impact Map, Architecture Decisions, Phase Status, Constraints. Lead tracks each
  coordinator's and Lead-direct agent's confirmed PT version in orchestration-plan.md.
- **L1/L2/L3:** L1 = index (YAML, ≤50 lines). L2 = summary (MD, ≤200 lines). L3 = full detail (directory).
- **Team Memory:** `.agent/teams/{session-id}/TEAM-MEMORY.md`, section-per-role structure.
- **Output directory:**
  ```
  .agent/teams/{session-id}/
  ├── orchestration-plan.md, TEAM-MEMORY.md
  └── phase-{N}/ → gate-record.yaml, {role}-{id}/ → L1, L2, L3-full/, task-context.md
  ```
- **Observability directory:**
  ```
  .agent/observability/
  ├── .current-project           # Active project slug
  └── {project-slug}/
      ├── manifest.json, rtd-index.md, current-dp.txt, session-registry.json
      └── events/{session}.jsonl
  ```
  Lead initializes at pipeline start. Hooks populate automatically.
  Persists across sessions for project-scoped observability.
```

---

### 5.4 Task 4: Update agent-common-protocol.md [VL-HIGH]

**File:** `.claude/references/agent-common-protocol.md`

**Action:** INSERT new section after line 20 (after "doing anything else."), before the `---` separator at line 21.

**old_string:**
```markdown
Make sure you understand the scope, constraints, and who will consume your output before
doing anything else.

---

## When Context Changes Mid-Work
```

**new_string:**
```markdown
Make sure you understand the scope, constraints, and who will consume your output before
doing anything else.

---

## Working with Coordinators

Some categories use coordinators to manage workflow. If your work is assigned through
a coordinator (not Lead directly):

- **Your coordinator is your primary contact.** Report progress, issues, and
  completion to the coordinator, not to Lead.
- **Lead may still contact you directly** for cross-cutting operations (PT updates,
  emergency intervention, gate spot-checks).
- **If coordinator becomes unresponsive:** Message Lead directly. Lead will manage
  you in fallback mode (Mode 3).
- **Understanding verification:** Your coordinator verifies your understanding using
  Impact Map context. Answer their probing questions with the same rigor as you
  would for Lead.
- **Review agents:** If you receive a review request from execution-coordinator,
  respond to execution-coordinator with your review results.

---

## When Context Changes Mid-Work
```

---

### 5.5 Task 5: Update execution-plan SKILL.md [VL-HIGH]

**File:** `.claude/skills/agent-teams-execution-plan/SKILL.md`

This is the **highest-risk modification**. Six section-level changes.

#### 5.5.1 §6.2 Team Setup (MODIFY)

**old_string:**
```markdown
## Phase 6.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-execution"
```

Create orchestration-plan.md and copy GC-v4 to new session directory.

Read the implementation plan fully:
- §1 (Orchestration Overview): understand scope and task count
- §3 (File Ownership Assignment): extract file sets per task
- §4 (TaskCreate Definitions): extract all tasks with dependencies
- §5 (Change Specifications): understand what each task implements
```

**new_string:**
```markdown
## Phase 6.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-execution"
```

Create orchestration-plan.md and copy GC-v4 to new session directory.

Read the implementation plan fully:
- §1 (Orchestration Overview): understand scope, task count, and coordinator usage
- §3 (File Ownership Assignment): extract file sets per task
- §4 (TaskCreate Definitions): extract all tasks with dependencies
- §5 (Change Specifications): understand what each task implements

Determine if this plan uses coordinators (check §1 for coordinator references).
If coordinators are used, prepare review prompt templates for execution-coordinator
(see Spec-Reviewer and Code-Reviewer prompts in §6.4).
```

#### 5.5.2 §6.3 Adaptive Spawn + Verification (MODIFY)

After the existing "### Implementer Spawn + Verification" section (line 184), INSERT
a new section for execution-coordinator. The existing implementer spawn text remains but
gets a conditional wrapper.

**old_string:**
```markdown
### Implementer Spawn + Verification

For each implementer:

```
Task tool:
  subagent_type: "implementer"
  team_name: "{feature-name}-execution"
  name: "implementer-{N}"
  mode: "default"
```

#### [DIRECTIVE] Construction

The directive must include these context layers:

1. **PERMANENT Task ID** — `PT-ID: {task_id} | PT-v{N}` so implementer can call TaskGet for full context
2. **GC-v4 full embedding** — the entire global-context.md (session-level artifacts)
3. **Task-context.md** — assignment, file ownership, task list, plan §5 specs for assigned tasks
4. **Review instructions** — two-stage review protocol, fix loop rules, reviewer prompt templates
5. **Implementation plan path** — for implementer to Read directly

Task-context must instruct implementer to:
- Read the PERMANENT Task via TaskGet for full project context (user intent, impact map)
- Read the implementation plan before starting (especially §5 for their tasks)
- Execute tasks in topological order within their component
- Run self-review after each task (completeness, quality, YAGNI, testing per §6.4 flow)
- Report to Lead for spec-reviewer and code-reviewer dispatch (two-stage, ordered)
- Include reviewer raw output in L2-summary.md
- Write L1/L2/L3 after each task completion (Pre-Compact Obligation)
- Report completion per task with structured report
- Report immediately if cross-boundary issue found

#### Understanding Verification

1. Implementer reads PERMANENT Task via TaskGet and confirms context receipt
2. Implementer explains their understanding of the task to Lead
3. Lead asks 1-3 probing questions grounded in the Codebase Impact Map,
   covering interconnections, failure modes, and dependency risks
4. Implementer defends with specific evidence
5. Lead verifies or rejects (max 3 attempts)
6. Once understanding is verified: implementer shares their plan, Lead approves → execution begins

All agents use `sequential-thinking` throughout.
```

**new_string:**
```markdown
### Coordinator + Worker Spawn

**If plan uses execution-coordinator (default for 2+ tasks):**

1. Spawn execution-coordinator:
```
Task tool:
  subagent_type: "execution-coordinator"
  team_name: "{feature-name}-execution"
  name: "exec-coord"
  mode: "default"
```

2. Pre-spawn all workers (implementers + reviewers):
```
Task tool:
  subagent_type: "implementer"          # or "infra-implementer"
  team_name: "{feature-name}-execution"
  name: "implementer-{N}"
  mode: "default"

Task tool:
  subagent_type: "spec-reviewer"
  team_name: "{feature-name}-execution"
  name: "spec-rev"
  mode: "default"

Task tool:
  subagent_type: "code-reviewer"
  team_name: "{feature-name}-execution"
  name: "code-rev"
  mode: "default"
```

3. Inform coordinator of worker names via SendMessage.

**If plan uses Lead-direct management (single simple task):**

Spawn implementer directly (skip coordinator). Use existing Lead-managed flow.

#### [DIRECTIVE] Construction — Execution Coordinator

The coordinator directive must include:

1. **PERMANENT Task ID** — `PT-ID: {task_id} | PT-v{N}`
2. **GC-v4 full embedding** — the entire global-context.md
3. **Implementation plan path** — for coordinator to Read directly
4. **Task assignments** — per-implementer task lists with file ownership
5. **Impact Map excerpt** — for coordinator to use in worker verification
6. **Review prompt templates** — spec-reviewer and code-reviewer prompts (see §6.4)
7. **Fix loop rules** — max 3 per stage, escalate to Lead on exhaustion
8. **Worker names** — all pre-spawned workers by role

Task-context must instruct coordinator to:
- Read the implementation plan (especially §5 for all tasks)
- Verify each implementer's understanding (using Impact Map excerpt)
- Approve implementer plans before execution begins
- Manage task lifecycle: assign → implement → spec-review → code-review → complete
- Dispatch reviewers via peer messaging (SendMessage, not Task tool)
- Manage fix loops (max 3 per stage)
- Send consolidated progress reports to Lead after each task completion
- Escalate cross-boundary issues to Lead immediately
- Write L1/L2/L3 proactively (Pre-Compact Obligation)

#### [DIRECTIVE] Construction — Workers

Each implementer's directive must include:

1. **PT context** — embedded by coordinator (from Lead's directive)
2. **Task assignment** — specific tasks, file ownership, acceptance criteria
3. **Coordinator name** — "Your coordinator is: {exec-coord}. Report to them."
4. **Implementation plan path** — for implementer to Read directly

Each reviewer's directive must include:
- "You will receive review requests from execution-coordinator via SendMessage.
  Respond to the coordinator with your review results."

#### Understanding Verification (Delegated)

1. Lead verifies execution-coordinator's understanding:
   - Coordinator explains scope, task distribution, review protocol
   - Lead asks 1-3 probing questions from Impact Map
   - Lead approves or rejects (max 3 attempts)
2. Coordinator verifies each implementer's understanding:
   - Implementer explains assigned tasks and file scope
   - Coordinator asks 1-2 probing questions from Impact Map excerpt
   - Coordinator reports verification status to Lead
3. Lead spot-checks verification quality at Gate 6

All agents use `sequential-thinking` throughout.
```

#### 5.5.3 §6.4 Task Execution + Review (MODIFY)

**old_string:** (lines 231-346, the entire Phase 6.4 section)

Replace the section header and flow with coordinator-mediated version.
The spec-reviewer and code-reviewer prompt templates REMAIN in the SKILL.md
but are now included in the coordinator directive rather than dispatched by Lead.

**new_string for the flow section (replace lines 231-253):**

```markdown
## Phase 6.4: Task Execution + Review

Execution-coordinator manages the inner loop. Lead monitors via consolidated reports.

### Coordinator-Managed Execution Flow (per task)

```
Execution-coordinator manages (Lead receives consolidated reports only):

1. Coordinator → implementer: "Implement Task {N}: {spec from plan §5}"
2. Implementer executes within file ownership boundary
3. Implementer → coordinator: "Task {N} complete: {summary, self-review, files}"
4. Coordinator dispatches spec-reviewer (Stage 1) via SendMessage:
   Constructs prompt from template below + task spec + implementer report
   ├── PASS → proceed to Stage 2
   └── FAIL → coordinator relays fix to implementer (max 3)
             └── 3x FAIL → coordinator reports BLOCKED to Lead
5. Coordinator dispatches code-reviewer (Stage 2) via SendMessage:
   Constructs prompt from template below + task spec + implementer report
   ├── PASS → task complete
   └── FAIL → coordinator relays fix to implementer (max 3)
             └── 3x FAIL → coordinator reports BLOCKED to Lead
6. Coordinator writes per-task update to L1/L2 (Pre-Compact Obligation)
7. Coordinator → Lead: "Task {N}: PASS. Spec: PASS. Quality: PASS. Proceeding."
8. Coordinator proceeds to next task in topological order
```

**The spec-reviewer and code-reviewer prompt templates remain unchanged below.**
They are included in the execution-coordinator's directive at spawn time,
and the coordinator constructs review requests from them via SendMessage.
```

**The existing Spec-Reviewer Subagent Prompt and Code-Reviewer Subagent Prompt
sections (lines 255-303) remain UNCHANGED** — they are proven working text.
Only update the introductory line:

**old_string:**
```markdown
### Spec-Reviewer Subagent Prompt

Lead dispatches via Task tool (spec-reviewer):
```

**new_string:**
```markdown
### Spec-Reviewer Prompt Template

Execution-coordinator constructs review request from this template (via SendMessage):
```

**old_string:**
```markdown
### Code-Reviewer Subagent Prompt

Lead dispatches via Task tool (code-reviewer):
```

**new_string:**
```markdown
### Code-Reviewer Prompt Template

Execution-coordinator constructs review request from this template (via SendMessage):
```

**The Implementer Completion Report Format section (lines 307-346) remains UNCHANGED.**
Update only the introductory context:

**old_string:**
```markdown
### Implementer Completion Report Format
```

**new_string:**
```markdown
### Implementer Completion Report Format

Implementers send this report to execution-coordinator (not Lead):
```

#### 5.5.4 §6.5 Monitoring (MODIFY)

**old_string:**
```markdown
## Phase 6.5: Monitoring + Issue Resolution

### Monitoring Cadence

| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| tmux visual | 0 tokens | Continuous | Always (primary) |
| TaskList | ~500 tokens | Every 15 min | Periodic check |
| Read L1 | ~2K tokens | On demand | When blocker reported |
| SendMessage query | ~200 tokens | On silence | >30 min no update |
```

**new_string:**
```markdown
## Phase 6.5: Monitoring + Issue Resolution

### Monitoring Cadence

Execution-coordinator handles day-to-day monitoring of implementers and reviewers.
Lead monitors the coordinator and handles escalation.

| Method | Cost | Frequency | When |
|--------|------|-----------|------|
| tmux visual | 0 tokens | Continuous | Always (primary) |
| Read coordinator L1 | ~1K tokens | Every 15 min | Periodic progress check |
| SendMessage to coordinator | ~200 tokens | On silence | >15 min no coordinator update |
| Read worker L1 (spot-check) | ~2K tokens | On demand | When quality concern or escalation |
```

#### 5.5.5 §6.6 Gate 6 (MODIFY — minor)

In the Per-Task Evaluation section, update the method column:

**old_string:**
```markdown
### Per-Task Evaluation

For each implementer's completion report:
```

**new_string:**
```markdown
### Per-Task Evaluation

For each task in coordinator's consolidated report (or implementer's report if Lead-direct):
```

In the Spot-Check section, add coordinator context:

**old_string:**
```markdown
### Spot-Check (Risk-Proportional Sampling)

Per implementer, select the highest-risk task and:
```

**new_string:**
```markdown
### Spot-Check (Risk-Proportional Sampling)

Per implementer (via coordinator's consolidated L2 or direct L2), select the highest-risk task and:
```

#### 5.5.6 §6.7 Clean Termination (MODIFY — minor)

**old_string:**
```markdown
### Shutdown Sequence

1. Shutdown all implementers: `SendMessage type: "shutdown_request"` to each
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`
```

**new_string:**
```markdown
### Shutdown Sequence

1. Shutdown execution-coordinator: `SendMessage type: "shutdown_request"`
   (coordinator writes final L1/L2/L3 before shutdown)
2. Shutdown all workers: `SendMessage type: "shutdown_request"` to each
   implementer, spec-reviewer, code-reviewer
3. `TeamDelete` — cleans team coordination files
4. Artifacts preserved in `.agent/teams/{session-id}/`
```

#### 5.5.7 Cross-Cutting Requirements (MODIFY — minor)

In the Sequential Thinking table:

**old_string:**
```markdown
| Agent | When |
|-------|------|
| Lead | Adaptive spawn calculation, understanding verification, probing questions, Gate 6, issue resolution |
| Implementer | Impact analysis, plan submission, complex implementation decisions, self-review |
```

**new_string:**
```markdown
| Agent | When |
|-------|------|
| Lead | Routing decision, coordinator verification, Gate 6, escalation handling |
| Coordinator | Worker verification, task lifecycle decisions, review dispatch, progress assessment |
| Implementer | Impact analysis, plan submission, complex implementation decisions, self-review |
```

#### 5.5.8 Never List (ADD items)

**old_string:**
```markdown
- Spawn more than 4 implementers
```

**new_string:**
```markdown
- Spawn more than 4 implementers
- Bypass execution-coordinator for implementer task management (except Lead-direct fallback)
- Let coordinator dispatch code-reviewer before spec-reviewer passes
- Skip coordinator verification of implementer understanding
```

---

### 5.6 Task 6: Update brainstorming-pipeline SKILL.md [VL-MED]

**File:** `.claude/skills/brainstorming-pipeline/SKILL.md`

Phase 2 orchestration changes. Phase 3 (Architecture) is **UNCHANGED** — architect is Lead-direct.

#### 5.6.1 §2.2 Team Setup (MODIFY)

After existing TeamCreate, add coordinator awareness:

```markdown
If spawning 2+ researchers, use research-coordinator:
1. Spawn research-coordinator first
2. Pre-spawn researchers (based on research scope)
3. Inform coordinator of researcher names
4. Coordinator distributes research questions and manages progress
```

#### 5.6.2 §2.3 Researcher Spawn + Verification (MODIFY)

Update the spawn flow to include coordinator option:

**Add before existing spawn template:**

```markdown
### Coordinator-Mediated Research (when 2+ researchers)

1. Spawn research-coordinator:
```
Task tool:
  subagent_type: "research-coordinator"
  team_name: "{feature-name}"
  name: "research-coord"
  mode: "default"
```

2. Coordinator directive includes: research scope, Impact Map excerpt,
   expected worker types, output paths

3. Pre-spawn researchers (same as current, but inform coordinator of names)

4. Verification: Lead verifies coordinator → coordinator verifies researchers

### Single Researcher (unchanged)
```

#### 5.6.3 §2.4 Research Execution (MODIFY)

Add coordinator monitoring path:

```markdown
**With coordinator:** Coordinator monitors researcher progress, consolidates findings.
Lead reads coordinator L1/L2 for consolidated progress (not individual researcher L2s).

**Without coordinator (single researcher):** Lead monitors directly (unchanged).
```

#### 5.6.4 §2.5 Gate 2 (MODIFY)

Update evaluation source:

```markdown
**With coordinator:** Lead reads coordinator's consolidated L1/L2.
Spot-check: Read one selected researcher L2 to verify consolidation quality.

**Without coordinator:** Lead reads researcher L2 directly (unchanged).
```

---

### 5.7 Task 7: Update verification-pipeline SKILL.md [VL-MED]

**File:** `.claude/skills/verification-pipeline/SKILL.md`

#### 5.7.1 Phase 7.3 Tester Spawn (MODIFY)

Add testing-coordinator option:

```markdown
### Coordinator-Mediated Testing (when plan uses coordinator)

1. Spawn testing-coordinator:
```
Task tool:
  subagent_type: "testing-coordinator"
  team_name: "{feature-name}-verification"
  name: "test-coord"
  mode: "default"
```

2. Pre-spawn tester(s) and inform coordinator of names

3. Coordinator directive includes: Phase 6 output paths, test targets,
   acceptance criteria, interface specs, Impact Map excerpt

4. Verification: Lead verifies coordinator → coordinator verifies tester
```

#### 5.7.2 Phase 7.4 Test Execution (MODIFY)

Add coordinator monitoring:

```markdown
**With coordinator:** Testing-coordinator manages tester, monitors progress,
consolidates test results. Lead reads coordinator L1/L2.

**Without coordinator (single tester, simple plan):** Lead manages directly (unchanged).
```

#### 5.7.3 Phase 8.1 Integrator Spawn (MODIFY)

Add coordinator management:

```markdown
**With testing-coordinator active:** Coordinator manages integrator spawn and lifecycle.
Tester MUST complete before integrator starts (coordinator enforces).

**Without coordinator:** Lead manages integrator directly (unchanged).
```

#### 5.7.4 Gate 7/8 (MODIFY)

Update evaluation source similar to Gate 2:

```markdown
**With coordinator:** Lead reads coordinator's consolidated L1/L2.
Spot-check: Read selected worker L2 to verify consolidation quality.
```

---

### 5.8 Task 8: Update write-plan and plan-validation SKILL.md [VL-LOW]

**Files:**
- `.claude/skills/agent-teams-write-plan/SKILL.md`
- `.claude/skills/plan-validation-pipeline/SKILL.md`

Both architect and devils-advocate are **Lead-direct** — their orchestration logic is unchanged.

#### write-plan SKILL.md Changes

Search for any references to "CLAUDE.md §6" agent selection flow and verify they remain
compatible with the new coordinator routing model. If the skill references "10 categories"
or "22 agents", update to "27 agents" and note the coordinator model.

Specific changes:
- Any reference to "Choose agent → pick specific agent from category" should add
  "or route through coordinator for coordinated categories"
- If spawn instructions reference the old Agent Selection Flow steps, update step numbers

#### plan-validation SKILL.md Changes

Same as write-plan: verify references to §6 and agent selection are compatible.
devils-advocate is Lead-direct, so no orchestration changes needed.

---

### 5.9 Task 9: Update 20 Agent .md Routing [VL-LOW]

**Pattern-based mechanical update across 20 files.**

#### Pattern A: "Message Lead with:" (18 files)

**old_string pattern:**
```
Message Lead with:
```

**new_string pattern:**
```
Message your coordinator (or Lead if assigned directly) with:
```

**Files (18):**
1. `.claude/agents/codebase-researcher.md`
2. `.claude/agents/external-researcher.md`
3. `.claude/agents/auditor.md`
4. `.claude/agents/static-verifier.md`
5. `.claude/agents/relational-verifier.md`
6. `.claude/agents/behavioral-verifier.md`
7. `.claude/agents/implementer.md`
8. `.claude/agents/infra-implementer.md`
9. `.claude/agents/tester.md`
10. `.claude/agents/integrator.md`
11. `.claude/agents/infra-static-analyst.md`
12. `.claude/agents/infra-relational-analyst.md`
13. `.claude/agents/infra-behavioral-analyst.md`
14. `.claude/agents/infra-impact-analyst.md`
15. `.claude/agents/architect.md`
16. `.claude/agents/plan-writer.md`
17. `.claude/agents/impact-verifier.md`
18. `.claude/agents/dynamic-impact-analyst.md`

**Example (implementer.md):**

old:
```markdown
## Before Starting Work
Read PERMANENT Task via TaskGet. Message Lead with:
- What files you'll change, which interfaces are affected
```

new:
```markdown
## Before Starting Work
Read PERMANENT Task via TaskGet. Message your coordinator (or Lead if assigned directly) with:
- What files you'll change, which interfaces are affected
```

#### Pattern B: "Message Lead confirming" (2 files)

**old_string pattern:**
```
Message Lead confirming
```

**new_string pattern:**
```
Message your coordinator (or Lead if assigned directly) confirming
```

**Files (2):**
19. `.claude/agents/spec-reviewer.md`
20. `.claude/agents/code-reviewer.md`

#### Excluded Files (NOT modified)

- `.claude/agents/devils-advocate.md` — No "Message Lead" pattern exists. Lead-direct, exempt.
- `.claude/agents/execution-monitor.md` — Lead-direct always. Keep current routing.

#### Verification

After all 20 files updated, run:
```
grep -l "Message Lead with:" .claude/agents/*.md
```
Expected: 0 results (all converted to coordinator-aware routing)

```
grep -l "Message your coordinator" .claude/agents/*.md
```
Expected: 20 results (all 20 updated files)

---

### 5.10 Task 10: Update layer-boundary-model.md [VL-LOW]

**File:** `.claude/references/layer-boundary-model.md`

Add a new dimension to the 5-Dimension Coverage model:

**INSERT after the last dimension entry:**

```markdown
### Dimension 6: Agent Coordination

| Aspect | Layer 1 (NL) | Layer 2 (Structural) |
|--------|-------------|---------------------|
| Coordinator model | Flat peer messaging (Mode 1) | State machine with guards/rollback |
| Worker discovery | Directive-embedded names | Schema-validated agent registry |
| Understanding verification | NL probing questions via Impact Map | Formal competency assessment |
| Failure recovery | Lead-direct fallback (Mode 3) | Automatic failover with state transfer |
| Cross-category routing | NL routing rules in §6 | Entity-based orchestration graph |

**Current implementation:** Layer 1 only (Hybrid Coordinator Model, AD-8 through AD-13)
**Layer 2 deferred to:** Ontology/Foundry structured orchestration
```

---

## 6. Interface Contracts

### COORDINATOR REFERENCE TABLE

This table is the **shared interface contract** between Implementer A and Implementer B.
Both implementers receive this verbatim in their directives. Neither reads the other's output.

| Coordinator | `subagent_type` | Workers | Phase | Key Protocol |
|-------------|----------------|---------|-------|-------------|
| research-coordinator | `research-coordinator` | codebase-researcher, external-researcher, auditor | 2 | Distribute questions → consolidate findings |
| verification-coordinator | `verification-coordinator` | static-verifier, relational-verifier, behavioral-verifier | 2b | Distribute dimensions → cross-dimension synthesis |
| execution-coordinator | `execution-coordinator` | implementer(s), spec-reviewer, code-reviewer | 6 | Task lifecycle + review dispatch via peer messaging |
| testing-coordinator | `testing-coordinator` | tester, integrator | 7-8 | Sequential: tester MUST complete before integrator |
| infra-quality-coordinator | `infra-quality-coordinator` | 4 INFRA analysts | X-CUT | Parallel 4-dimension analysis → weighted score |

### Tool Set (All Coordinators — AD-13)

```yaml
tools: [Read, Glob, Grep, Write, TaskList, TaskGet, mcp__sequential-thinking__sequentialthinking]
disallowedTools: [TaskCreate, TaskUpdate, Edit, Bash]
```

### Lead-Direct Categories (unchanged)

| Category | Agent(s) | Phase | Routing |
|----------|----------|-------|---------|
| Impact | impact-verifier, dynamic-impact-analyst | 2d, 6+ | Lead spawns directly |
| Architecture | architect | 3, 4 | Lead spawns directly |
| Planning | plan-writer | 4 | Lead spawns directly |
| Review | devils-advocate, spec-reviewer, code-reviewer | 5, 6 | Lead-direct (reviewers also dispatched by exec-coord in P6) |
| Monitoring | execution-monitor | 6+ | Lead spawns directly |

### Routing Rule (for §6 and agent .md files)

```
"Message your coordinator (or Lead if assigned directly) with:"
```

This routing rule is used in:
- 20 agent .md files (T-9)
- agent-common-protocol.md "Working with Coordinators" section (T-4)
- CLAUDE.md §6 routing model (T-3)

### Cross-Implementer Timing

Implementer A and B have **zero dependencies** on each other's output.
Both receive:
1. This COORDINATOR REFERENCE TABLE (verbatim, in directive)
2. The Phase 3 architecture document (for full context)
3. This implementation plan (for task-specific §5 specs)

---

## 7. Validation Checklist (Lead — Phase 6.V)

### V-1: Coordinator .md Structural Consistency

- [ ] All 5 coordinator .md files exist in `.claude/agents/`
- [ ] All 5 have identical YAML tool set (AD-13 template)
- [ ] All 5 reference `agent-common-protocol.md`
- [ ] execution-coordinator has Review Dispatch Protocol
- [ ] testing-coordinator has sequential lifecycle enforcement
- [ ] infra-quality-coordinator has score aggregation weights

### V-2: Agent-Catalog Two-Level Structure

- [ ] Level 1 (first ~300 lines) contains all 5 coordinator descriptions
- [ ] Level 1 contains Lead-direct agent summaries
- [ ] `## Agent Full Descriptions (Level 2)` header clearly separates levels
- [ ] Level 2 has all 22 agent descriptions organized by category
- [ ] Total file size ~975L (no content lost)

### V-3: CLAUDE.md Consistency

- [ ] Custom Agents Reference has "27 Agents, 10 Categories, Hybrid Coordinator Model"
- [ ] Coordinated Categories table has 5 coordinators
- [ ] Lead-Direct Categories table has remaining categories
- [ ] §4 Communication has coordinator flows
- [ ] §6 has "Agent Selection and Routing" with coordinator route
- [ ] §6 has "Coordinator Management" subsection
- [ ] §6 "Before Spawning" references "Level 1, first ~300 lines"
- [ ] §6 "Phase Gates" mentions coordinator consolidated L1/L2

### V-4: Common Protocol

- [ ] "Working with Coordinators" section exists after "When You Receive a Task Assignment"
- [ ] Section covers: primary contact, Lead emergency, fallback, verification, review agents

### V-5: Execution-Plan SKILL.md

- [ ] §6.2 mentions coordinator awareness
- [ ] §6.3 has coordinator spawn + delegated verification
- [ ] §6.4 has coordinator-managed inner loop
- [ ] Review templates remain in SKILL.md (not moved)
- [ ] §6.5 has coordinator monitoring cadence
- [ ] §6.6 reads coordinator consolidated L1/L2
- [ ] §6.7 shutdown includes coordinator
- [ ] Never list includes coordinator-related rules

### V-6: Skill Consistency

- [ ] brainstorming-pipeline has research-coordinator option for Phase 2
- [ ] verification-pipeline has testing-coordinator option for Phase 7-8
- [ ] write-plan and plan-validation reference updated §6 model
- [ ] No skill references "old" direct-only model exclusively

### V-7: Agent Routing

```bash
grep -l "Message your coordinator" .claude/agents/*.md
```
Expected: 25 results (20 updated agents + 5 new coordinators)

```bash
grep -l "Message Lead with:" .claude/agents/*.md
```
Expected: 0 results

### V-8: Layer-Boundary Model

- [ ] Coordinator dimension added (Dimension 6)
- [ ] Layer 1/Layer 2 distinction clear

### V-9: No Circular References

- [ ] Coordinator .md files reference common-protocol (not catalog)
- [ ] Catalog references coordinator .md files (not circular)
- [ ] CLAUDE.md §6 references catalog Level 1 (not coordinator .md directly)

---

## 8. Commit Strategy

> The infra-implementers have Write/Edit access and Lead commits.

**Single commit after all edits pass validation:**

```bash
git add \
  .claude/agents/research-coordinator.md \
  .claude/agents/verification-coordinator.md \
  .claude/agents/execution-coordinator.md \
  .claude/agents/testing-coordinator.md \
  .claude/agents/infra-quality-coordinator.md \
  .claude/references/agent-catalog.md \
  .claude/CLAUDE.md \
  .claude/references/agent-common-protocol.md \
  .claude/skills/agent-teams-execution-plan/SKILL.md \
  .claude/skills/brainstorming-pipeline/SKILL.md \
  .claude/skills/verification-pipeline/SKILL.md \
  .claude/skills/agent-teams-write-plan/SKILL.md \
  .claude/skills/plan-validation-pipeline/SKILL.md \
  .claude/references/layer-boundary-model.md \
  .claude/agents/codebase-researcher.md \
  .claude/agents/external-researcher.md \
  .claude/agents/auditor.md \
  .claude/agents/static-verifier.md \
  .claude/agents/relational-verifier.md \
  .claude/agents/behavioral-verifier.md \
  .claude/agents/implementer.md \
  .claude/agents/infra-implementer.md \
  .claude/agents/tester.md \
  .claude/agents/integrator.md \
  .claude/agents/infra-static-analyst.md \
  .claude/agents/infra-relational-analyst.md \
  .claude/agents/infra-behavioral-analyst.md \
  .claude/agents/infra-impact-analyst.md \
  .claude/agents/architect.md \
  .claude/agents/plan-writer.md \
  .claude/agents/impact-verifier.md \
  .claude/agents/dynamic-impact-analyst.md \
  .claude/agents/spec-reviewer.md \
  .claude/agents/code-reviewer.md

git commit -m "feat(infra): Hybrid Coordinator Model — 5 coordinators for multi-agent categories

Implement AD-8 through AD-13 from Lead Architecture Redesign:
- 5 coordinator agents (research, verification, execution, testing, infra-quality)
- Two-Level Catalog (Level 1 ~300L mandatory + Level 2 ~680L on-demand)
- CLAUDE.md §6 rewrite: coordinator routing model, delegated verification
- execution-plan SKILL.md: coordinator-mediated review dispatch (71% Lead context savings)
- 20 agent .md files: coordinator-aware routing
- agent-common-protocol.md: 'Working with Coordinators' section

Architecture: docs/plans/2026-02-11-lead-architecture-redesign.md
Design: .agent/teams/lead-arch-redesign/phase-3/architect-1/L3-full/architecture-design.md

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## 9. Gate Criteria (Lead Evaluation)

### Phase 6 Gate (after both implementers report COMPLETE)

| # | Criterion | Check Method |
|---|-----------|-------------|
| 1 | All 5 coordinator .md files created with correct structure | Read each, verify AD-13 template |
| 2 | agent-catalog.md has Two-Level structure | Read first 300L (Level 1) + verify Level 2 header |
| 3 | CLAUDE.md has coordinator routing model | Read §6, verify routing decision tree |
| 4 | Common protocol has coordinator section | Read, verify "Working with Coordinators" |
| 5 | execution-plan SKILL.md has coordinator-mediated flow | Read §6.3-6.4, verify coordinator inner loop |
| 6 | All 3 updated skills reference coordinator model | Read each, verify consistency |
| 7 | 20 agent .md files have coordinator-aware routing | Grep verification (V-7) |
| 8 | Layer-boundary-model has coordinator dimension | Read, verify Dimension 6 |
| 9 | Cross-references pass V-1 through V-9 | Run validation checklist (§7) |
| 10 | L1/L2/L3 handoff files written by both implementers | Check output directories |
| 11 | No broken markdown formatting | Visual inspection of key files |

**Gate result:**
- ALL PASS → APPROVE → Phase 9 (Delivery)
- 1-2 FAIL (non-critical) → ITERATE → affected implementer fixes
- 3+ FAIL → REJECT → re-evaluate approach

---

## 10. Summary

| Item | Value |
|------|-------|
| Pipeline | Infrastructure (Phase 1 → 6 → 6.V → 9) |
| Teammates | 2 infra-implementers (zero file overlap) |
| TaskCreate entries | 10 (T-1 through T-10) |
| Files created | 5 coordinator .md files |
| Files modified | 29 (.claude/ infrastructure) |
| Total files | 34 |
| Hooks changed | 0 (AD-15 inviolable) |
| Estimated lines added | ~400 (5 coordinators) |
| Estimated lines modified | ~300 (skills, CLAUDE.md, catalog, protocol) |
| Commit strategy | Single commit |
| Gate criteria | 11 items (§9) |
| Key risk | T-5 execution-plan rewrite (highest complexity) |
| Key benefit | 69% catalog read reduction, 71% Phase 6 context savings |

---
name: plan-validation-pipeline
description: "Phase 0 (PT Check) + Phase 5 (Plan Validation) — spawns devils-advocate to challenge Phase 4 design. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to Phase 4 output]"
---

# Plan Validation Pipeline

Phase 5 (Plan Validation) orchestrator. Challenges the implementation plan from Phase 4 through a devils-advocate teammate before committing to implementation.

**Announce at start:** "I'm using plan-validation-pipeline to orchestrate Phase 5 (Plan Validation) for this feature."

**Core flow:** PT Check → Input Discovery → Team Setup → Validation Spawn (tier-routed) → Challenge Execution → Gate 5 → Clean Termination

## When to Use

```
Have an implementation plan from agent-teams-write-plan?
├── Working in Agent Teams mode? ─── no ──→ Review the plan manually
├── yes
├── PT with Phase 4 COMPLETE? ── no ──→ Run /agent-teams-write-plan first
├── yes
└── Use /plan-validation-pipeline
```

**Why validate?** Phase 5 is the last checkpoint before implementation. Catching design flaws here costs a fraction of finding them during Phase 6 execution. The devils-advocate applies structured critique that the architect (who wrote the plan) cannot objectively apply to their own work.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Pipeline Session Directories:**
!`ls -d /home/palantir/.agent/teams/*/ 2>/dev/null | while read d; do echo "$(basename "$d"): $(ls "$d"phase-*/gate-record.yaml 2>/dev/null | wc -l) gates"; done`

**Implementation Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS

---

## A) Phase 0: PERMANENT Task Check

Lightweight step (~500 tokens). No teammates spawned, no verification required.

Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

```
TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to B)     │     │
          ▼     ▼
        /permanent-tasks    Continue to B)
        creates PT-v1       without PT
        → then B)
```

If a PERMANENT Task exists, read it via TaskGet. Its content (user intent, codebase impact map,
architecture decisions, phase status, constraints) provides authoritative cross-phase context.
Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to B) Core Workflow.

If a PERMANENT Task exists but `$ARGUMENTS` describes a different feature than the PT's
User Intent, ask the user to clarify which feature to work on before proceeding.

---

## B) Phase 5: Core Workflow

### 5.1 Input Discovery + Validation

No teammates spawned. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

#### Discovery (PT + L2)

1. **TaskGet** on PERMANENT Task → read full PT
2. **Verify:** PT §phase_status.P4.status == COMPLETE
3. **Read:** PT §phase_status.P4.l2_path → planning-coordinator/L2 location
4. **Read:** planning-coordinator/L2 §Downstream Handoff for entry context
5. If `$ARGUMENTS` provides a session-id or path, use that directly
6. If multiple candidates found, present options via `AskUserQuestion`
7. If PT not found or Phase 4 not complete: "Phase 4 not complete. Run /agent-teams-write-plan first."

#### Rollback Detection

Check for `rollback-record.yaml` in downstream phase directories (phase-6/, phase-7/):
- If found: read rollback context (revision targets, prior-attempt lessons) per `pipeline-rollback-protocol.md` §3
- Include rollback context in challenger directives (what was attempted, why rolled back, areas to focus on)
- If not found: proceed normally

#### Validation

| # | Check | On Failure |
|---|-------|------------|
| V-1 | PT exists with §phase_status.P4.status == COMPLETE | Abort: "Phase 4 not complete. Run /agent-teams-write-plan first" |
| V-2 | Implementation plan exists in `docs/plans/` | Abort: "Implementation plan not found" |
| V-3 | Plan follows 10-section template (§1-§10) including architecture decisions, file ownership, and change specifications | Abort: "Plan missing required sections: {list}" |
| V-4 | PT §Implementation Plan + planning-coordinator/L2 §Downstream Handoff contain required context | Abort: "Phase 4 design context not available" |

Use `sequential-thinking` to evaluate validation results.

On all checks PASS → proceed to 5.2.

---

### 5.2 Team Setup

```
TeamCreate:
  team_name: "{feature-name}-validation"
```

Create orchestration-plan.md in new session directory.
Create TEAM-MEMORY.md with Lead and devils-advocate sections.

---

### 5.3 Validation Spawn

Devils-advocate is exempt from the understanding check — critical analysis itself demonstrates comprehension. Phase 5 is the adversarial challenge by design.

Use `sequential-thinking` for all Lead decisions in this phase.

#### Tier-Based Routing (D-001/D-005)

| Tier | Route | Agents |
|------|-------|--------|
| STANDARD | Lead-direct | Single `devils-advocate` |
| COMPLEX | Coordinator | `validation-coordinator` + correctness-challenger, completeness-challenger, robustness-challenger |

> TRIVIAL tier skips Phase 5 entirely.

#### Spawn (STANDARD — Lead-direct)

```
Task tool:
  subagent_type: "devils-advocate"
  team_name: "{feature-name}-validation"
  name: "devils-advocate-1"
  mode: "default"
```

#### Spawn (COMPLEX — Coordinator Route)

```
1. Spawn validation-coordinator (subagent_type: "validation-coordinator")
2. Pre-spawn: correctness-challenger, completeness-challenger, robustness-challenger
3. Each challenger focuses on specific challenge categories (C-1/C-2 correctness,
   C-3/C-4 completeness, C-5/C-6 robustness)
4. Coordinator consolidates into unified verdict
```
For COMPLEX tier, follow CLAUDE.md §6 Coordinator Management protocol.

#### [DIRECTIVE] Construction

The directive must include these context layers:

1. **PERMANENT Task ID** (PT-v{N}) — devils-advocate reads full context via TaskGet
2. **Implementation plan path** — `docs/plans/{plan-file}` for devils-advocate to Read
3. **Predecessor L2 path** — planning-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P4.l2_path)
4. **Challenge scope instructions** — what to focus critique on

Task-context must instruct devils-advocate to:
- Read the PERMANENT Task via TaskGet for full project context
- Read the implementation plan fully before starting critique
- Read the predecessor L2 §Downstream Handoff for Phase 4 design rationale
- Use `sequential-thinking` for every challenge analysis
- Use `mcp__tavily__search` to find real-world failure cases as evidence
- Use `mcp__context7__query-docs` to verify library/framework claims in the plan
- Apply all 6 challenge categories systematically
- Assign severity ratings (CRITICAL/HIGH/MEDIUM/LOW) with evidence
- Propose specific mitigations for every flaw found
- Deliver a final verdict: PASS, CONDITIONAL_PASS, or FAIL
- Write L1/L2/L3 output files

#### Getting Started

1. Devils-advocate reads the PERMANENT Task via TaskGet for full project context
2. Devils-advocate confirms context receipt to Lead
3. No understanding check needed — the critical analysis itself proves comprehension
4. Devils-advocate proceeds directly to challenge execution

---

### 5.4 Challenge Execution

Devils-advocate works with: Read, Glob, Grep, Write, sequential-thinking, context7, tavily.

#### Challenge Categories

The devils-advocate must exercise all 6 categories against the implementation plan:

| # | Category | Focus |
|---|----------|-------|
| C-1 | **Correctness** | Does the plan solve the stated problem from Phase 1 Scope Statement? |
| C-2 | **Completeness** | Missing requirements, edge cases, error handling, rollback scenarios? |
| C-3 | **Consistency** | Do different parts of the plan contradict each other? File ownership vs. specs? |
| C-4 | **Feasibility** | Can tasks be implemented within stated constraints? Are estimates realistic? |
| C-5 | **Robustness** | What happens when things go wrong? Failure modes, recovery paths? |
| C-6 | **Interface Contracts** | Are all interfaces between implementers explicit and compatible? |

#### Challenge Targets

For each section of the implementation plan:

- **Architecture decisions:** Are they justified? Were alternatives fairly evaluated?
- **Task decomposition:** Is the dependency graph correct? Are tasks properly isolated?
- **File ownership:** Are boundaries clean? Any hidden cross-boundary dependencies?
- **Change specifications:** Are specs complete enough for an implementer to work from?
- **Acceptance criteria:** Are they testable? Is AC-0 (plan verification) present?
- **Risk assessment:** Are risks properly identified? Are mitigations realistic?
- **Verification strategy:** Does V6 (Code Plausibility) cover enough ground?

#### Expected Output

```
.agent/teams/{session-id}/phase-5/devils-advocate-1/
├── L1-index.yaml    (YAML, ≤50 lines — challenges with severity ratings)
├── L2-summary.md    (Markdown, ≤200 lines — challenge narrative, verdict, Evidence Sources)
└── L3-full/
    └── challenge-report.md  (full detailed challenge analysis)
```

Devils-advocate reports completion with their verdict (PASS, CONDITIONAL_PASS, or FAIL) to Lead via SendMessage.

---

### 5.5 Gate 5

Use `sequential-thinking` for all gate evaluation.

#### Criteria

| # | Criterion |
|---|-----------|
| G5-1 | Challenge report (L1/L2/L3) exists |
| G5-2 | All 6 challenge categories exercised |
| G5-3 | Severity ratings are evidence-based (specific references to plan sections) |
| G5-4 | Mitigations proposed for every HIGH+ issue |
| G5-5 | Final verdict provided with justification |
| G5-6 | No CRITICAL issues left unresolved |

#### Verdict Evaluation

Read the devils-advocate's L2-summary.md and L3-full/challenge-report.md:

**PASS (no critical or high issues):**
- Plan is sound. Proceed to Phase 6.

**CONDITIONAL_PASS (high issues with accepted mitigations):**
- Present identified issues and proposed mitigations to user.
- Ask user: "Accept mitigations and proceed, or return to Phase 4?"
- If accepted: Document accepted mitigations.
- If rejected: Execute rollback P5→P4 per `pipeline-rollback-protocol.md` with revision targets.

**FAIL (critical issues found):**
- Before presenting to user, Lead sends a re-verification message to devils-advocate
  requesting specific evidence and confirmation for each CRITICAL finding. This multi-turn
  exchange ensures CRITICAL verdicts are grounded.
- Present critical issues to user with clear explanation.
- Execute rollback P5→P4 per `pipeline-rollback-protocol.md`.
- Include specific sections that need revision in `rollback-record.yaml` revision_targets.

#### User Review

Present challenge summary to user before final gate decision:

```markdown
## Plan Validation Results

**Feature:** {name}
**Verdict:** {PASS|CONDITIONAL_PASS|FAIL}

**Issues Found:**
- Critical: {count}
- High: {count}
- Medium: {count}
- Low: {count}

**Top Issues:**
1. {highest severity issue summary}
2. {next issue}
3. {next issue}

Shall I proceed with Gate 5 approval?
```

#### Gate Audit (COMPLEX only)

Mandatory for COMPLEX tier (see `gate-evaluation-standard.md` §6).
Spawn `gate-auditor` with G5 criteria and evidence paths (challenge report, L1/L2).
Compare verdicts per §6 procedure. On disagreement → escalate to user.

#### On APPROVE

1. Update PERMANENT Task (PT-v{N} → PT-v{N+1}) via `/permanent-tasks`:
   - Add §Validation Verdict: {PASS | CONDITIONAL_PASS}
   - Update §phase_status.P5 = COMPLETE with l2_path
   - If CONDITIONAL_PASS: add accepted mitigations to §Constraints
2. Write `phase-5/gate-record.yaml`
3. Update GC scratch: Phase Pipeline Status (session-scoped only)
4. Proceed to Clean Termination

#### On ITERATE (max 3)

- If challenge quality is insufficient: relay specific critique improvement instructions
- Devils-advocate revises and resubmits
- Re-evaluate Gate 5

#### On FAIL (verdict FAIL with user agreement)

- Do not create Gate 5 APPROVED record
- Write `phase-5/gate-record.yaml` with result: ITERATE_TO_P4
- Present user with specific revision targets for Phase 4
- Clean termination (no Phase 6 entry)

---

### Clean Termination

After Gate 5 decision:

#### Output Summary

```markdown
## plan-validation-pipeline Complete (Phase 5)

**Feature:** {name}
**Verdict:** {PASS|CONDITIONAL_PASS|FAIL}

**Challenge Summary:**
- Categories exercised: 6/6
- Critical issues: {count}
- High issues: {count}
- Mitigations accepted: {count}

**Artifacts:**
- PERMANENT Task (PT-v{N}) — updated with validation verdict
- Session artifacts: .agent/teams/{session-id}/
- Challenge Report: .agent/teams/{session-id}/phase-5/devils-advocate-1/L3-full/challenge-report.md

**Next:** {verdict-dependent}
- PASS/CONDITIONAL_PASS → Phase 6 (Implementation) — use /agent-teams-execution-plan
- FAIL → Phase 4 (Redesign) — use /agent-teams-write-plan with revision targets
```

#### Shutdown

1. Shutdown devils-advocate-1: `SendMessage type: "shutdown_request"`
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

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

---

## D) Cross-Cutting

Follow CLAUDE.md §6 (Agent Selection and Routing), §9 (Compact Recovery), §10 (Integrity Principles) for all protocol decisions.
Follow `coordinator-shared-protocol.md` for coordinator management when COMPLEX tier is active.
Follow `gate-evaluation-standard.md` §6 for gate audit requirements.
Follow `pipeline-rollback-protocol.md` for rollback procedures.
All agents use `sequential-thinking` for analysis, judgment, and verification.
Task descriptions follow `task-api-guideline.md` v6.0 §3 for field requirements.

### Skill-Specific Error Handling

| Situation | Response |
|-----------|----------|
| PT not found or Phase 4 not complete | Inform user, suggest /agent-teams-write-plan |
| Implementation plan not found | Abort with guidance |
| Devils-advocate silent >20 min | Send status query |
| Challenge quality too low (Gate 5 iterate) | Re-direct with specific improvement instructions |

---

## Key Principles

- **Adversarial integrity** — devils-advocate must genuinely challenge, not rubber-stamp
- **Evidence-based critique** — every severity rating must reference specific plan sections
- **MCP-verified** — use tavily and context7 to back claims with real documentation
- **Mitigations always** — identifying problems without solutions is incomplete
- **Verdict-driven gating** — FAIL blocks Phase 6 entry, CONDITIONAL_PASS requires user consent
- **Sequential thinking always** — structured reasoning at every decision point
- **Protocol delegated** — CLAUDE.md owns verification rules, skill owns orchestration
- **Clean termination** — no auto-chaining to Phase 6
- **Artifacts preserved** — all outputs survive in `.agent/teams/{session-id}/`

## Never

- Skip spawning devils-advocate (the challenge must come from a separate agent)
- Auto-approve a FAIL verdict (user must decide)
- Auto-chain to Phase 6 after termination
- Proceed past Gate 5 without all criteria met
- Let devils-advocate modify project files (Write access is for L1/L2/L3 output only)
- Accept challenges without evidence (vague "this might fail" is not a valid critique)
- Suppress critical issues to achieve PASS verdict

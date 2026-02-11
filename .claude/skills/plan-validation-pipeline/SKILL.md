---
name: plan-validation-pipeline
description: "Phase 0 (PT Check) + Phase 5 (Plan Validation) — spawns devils-advocate to challenge Phase 4 design. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to Phase 4 output]"
---

# Plan Validation Pipeline

Phase 5 (Plan Validation) orchestrator. Challenges the implementation plan from Phase 4 through a devils-advocate teammate before committing to implementation.

**Announce at start:** "I'm using plan-validation-pipeline to orchestrate Phase 5 (Plan Validation) for this feature."

**Core flow:** Input Discovery → Team Setup → Devils-Advocate Spawn → Challenge Execution → Gate 5 → Clean Termination

## When to Use

```
Have an implementation plan from agent-teams-write-plan?
├── Working in Agent Teams mode? ─── no ──→ Review the plan manually
├── yes
├── GC-v4 with Phase 4 COMPLETE? ── no ──→ Run /agent-teams-write-plan first
├── yes
└── Use /plan-validation-pipeline
```

**Why validate?** Phase 5 is the last checkpoint before implementation. Catching design flaws here costs a fraction of finding them during Phase 6 execution. The devils-advocate applies structured critique that the architect (who wrote the plan) cannot objectively apply to their own work.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Previous Pipeline Output:**
!`ls -d /home/palantir/.agent/teams/*/global-context.md 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "---"; echo "Dir: $dir"; head -8 "$f"; echo ""; done`

**Implementation Plans:**
!`ls /home/palantir/docs/plans/ 2>/dev/null`

**Infrastructure Version:**
!`head -3 /home/palantir/.claude/CLAUDE.md 2>/dev/null`

**Feature Input:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check

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
to 5.1    │     │
          ▼     ▼
        /permanent-tasks    Continue to 5.1
        creates PT-v1       without PT
        → then 5.1
```

If a PERMANENT Task exists, its content (user intent, codebase impact map, prior decisions)
provides additional context for Phase 5 validation. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 5.1.

If a PERMANENT Task exists but `$ARGUMENTS` describes a different feature than the PT's
User Intent, ask the user to clarify which feature to work on before proceeding.

---

## Phase 5.1: Input Discovery + Validation

No teammates spawned. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find agent-teams-write-plan output:

1. Look for `.agent/teams/*/global-context.md` files with `Phase 4: COMPLETE`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found Phase 4 output at {path}. Use this?"
5. If no candidates, inform user: "No Phase 4 output found. Run /agent-teams-write-plan first."

### Validation

After identifying the source, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with `Phase 4: COMPLETE` | Abort: "GC-v4 not found or Phase 4 not complete" |
| V-2 | Implementation plan exists in `docs/plans/` | Abort: "Implementation plan not found" |
| V-3 | Plan follows 10-section template (§1-§10) including architecture decisions, file ownership, and change specifications | Abort: "Plan missing required sections: {list}" |
| V-4 | GC-v4 contains Scope, Phase 4 decisions, and implementation task breakdown | Abort: "GC-v4 missing required context sections" |

Use `sequential-thinking` to evaluate validation results.

On all checks PASS → proceed to 5.2.

---

## Phase 5.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-validation"
```

Create orchestration-plan.md and copy GC-v4 to new session directory.
Create TEAM-MEMORY.md with Lead and devils-advocate sections.

---

## Phase 5.3: Devils-Advocate Spawn

Devils-advocate is exempt from the understanding check — critical analysis itself demonstrates comprehension. Phase 5 is the adversarial challenge by design.

Use `sequential-thinking` for all Lead decisions in this phase.

### Spawn

```
Task tool:
  subagent_type: "devils-advocate"
  team_name: "{feature-name}-validation"
  name: "devils-advocate-1"
  mode: "default"
```

> Devils-advocate is a Lead-direct agent (CLAUDE.md §6). No coordinator involved —
> Lead spawns and manages the devils-advocate directly.

### [DIRECTIVE] Construction

The directive must include these context layers:

1. **PERMANENT Task ID** (PT-v{N}) — devils-advocate reads full context via TaskGet
2. **Implementation plan path** — `docs/plans/{plan-file}` for devils-advocate to Read
3. **Phase 3 architecture path** — if available, for cross-referencing design intent
4. **Challenge scope instructions** — what to focus critique on

Task-context must instruct devils-advocate to:
- Read the PERMANENT Task via TaskGet for full project context
- Read the implementation plan fully before starting critique
- Read the architecture design from Phase 3 (if available) for cross-reference
- Use `sequential-thinking` for every challenge analysis
- Use `mcp__tavily__search` to find real-world failure cases as evidence
- Use `mcp__context7__query-docs` to verify library/framework claims in the plan
- Apply all 6 challenge categories systematically
- Assign severity ratings (CRITICAL/HIGH/MEDIUM/LOW) with evidence
- Propose specific mitigations for every flaw found
- Deliver a final verdict: PASS, CONDITIONAL_PASS, or FAIL
- Write L1/L2/L3 output files

### Getting Started

1. Devils-advocate reads the PERMANENT Task via TaskGet for full project context
2. Devils-advocate confirms context receipt to Lead
3. No understanding check needed — the critical analysis itself proves comprehension
4. Devils-advocate proceeds directly to challenge execution

---

## Phase 5.4: Challenge Execution

Devils-advocate works with: Read, Glob, Grep, Write, sequential-thinking, context7, tavily.

### Challenge Categories

The devils-advocate must exercise all 6 categories against the implementation plan:

| # | Category | Focus |
|---|----------|-------|
| C-1 | **Correctness** | Does the plan solve the stated problem from Phase 1 Scope Statement? |
| C-2 | **Completeness** | Missing requirements, edge cases, error handling, rollback scenarios? |
| C-3 | **Consistency** | Do different parts of the plan contradict each other? File ownership vs. specs? |
| C-4 | **Feasibility** | Can tasks be implemented within stated constraints? Are estimates realistic? |
| C-5 | **Robustness** | What happens when things go wrong? Failure modes, recovery paths? |
| C-6 | **Interface Contracts** | Are all interfaces between implementers explicit and compatible? |

### Challenge Targets

For each section of the implementation plan:

- **Architecture decisions:** Are they justified? Were alternatives fairly evaluated?
- **Task decomposition:** Is the dependency graph correct? Are tasks properly isolated?
- **File ownership:** Are boundaries clean? Any hidden cross-boundary dependencies?
- **Change specifications:** Are specs complete enough for an implementer to work from?
- **Acceptance criteria:** Are they testable? Is AC-0 (plan verification) present?
- **Risk assessment:** Are risks properly identified? Are mitigations realistic?
- **Verification strategy:** Does V6 (Code Plausibility) cover enough ground?

### Expected Output

```
.agent/teams/{session-id}/phase-5/devils-advocate-1/
├── L1-index.yaml    (YAML, ≤50 lines — challenges with severity ratings)
├── L2-summary.md    (Markdown, ≤200 lines — challenge narrative, verdict, Evidence Sources)
└── L3-full/
    └── challenge-report.md  (full detailed challenge analysis)
```

Devils-advocate reports completion with their verdict (PASS, CONDITIONAL_PASS, or FAIL) to Lead via SendMessage.

---

## Phase 5.5: Gate 5

Use `sequential-thinking` for all gate evaluation.

### Criteria

| # | Criterion |
|---|-----------|
| G5-1 | Challenge report (L1/L2/L3) exists |
| G5-2 | All 6 challenge categories exercised |
| G5-3 | Severity ratings are evidence-based (specific references to plan sections) |
| G5-4 | Mitigations proposed for every HIGH+ issue |
| G5-5 | Final verdict provided with justification |
| G5-6 | No CRITICAL issues left unresolved |

### Verdict Evaluation

Read the devils-advocate's L2-summary.md and L3-full/challenge-report.md:

**PASS (no critical or high issues):**
- Plan is sound. Proceed to Phase 6.
- GC-v4 stays as-is, add Phase 5 status.

**CONDITIONAL_PASS (high issues with accepted mitigations):**
- Present identified issues and proposed mitigations to user.
- Ask user: "Accept mitigations and proceed, or return to Phase 4?"
- If accepted: Document accepted mitigations in GC update.
- If rejected: Return to Phase 4 with specific revision targets.

**FAIL (critical issues found):**
- Before presenting to user, Lead sends a re-verification message to devils-advocate
  requesting specific evidence and confirmation for each CRITICAL finding. This multi-turn
  exchange ensures CRITICAL verdicts are grounded.
- Present critical issues to user with clear explanation.
- Must return to Phase 4 for redesign.
- Include specific sections that need revision.

### User Review

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

### On APPROVE

1. Update global-context.md:
   - Add `Phase 5: COMPLETE (Gate 5 APPROVED, Verdict: {verdict})`
   - If CONDITIONAL_PASS: add accepted mitigations to Constraints section
   - Bump version if mitigations added (GC-v4 → GC-v5, preserving all prior sections)
2. Write `phase-5/gate-record.yaml`
3. Proceed to Clean Termination

### On ITERATE (max 3)

- If challenge quality is insufficient: relay specific critique improvement instructions
- Devils-advocate revises and resubmits
- Re-evaluate Gate 5

### On FAIL (verdict FAIL with user agreement)

- Do not create Gate 5 APPROVED record
- Write `phase-5/gate-record.yaml` with result: ITERATE_TO_P4
- Present user with specific revision targets for Phase 4
- Clean termination (no Phase 6 entry)

---

## Clean Termination

After Gate 5 decision:

### Output Summary

```markdown
## plan-validation-pipeline Complete (Phase 5)

**Feature:** {name}
**Verdict:** {PASS|CONDITIONAL_PASS|FAIL}

**Challenge Summary:**
- Categories exercised: 6/6
- Critical issues: {count}
- High issues: {count}
- Mitigations accepted: {count}

**Artifacts:** .agent/teams/{session-id}/
**Challenge Report:** .agent/teams/{session-id}/phase-5/devils-advocate-1/L3-full/challenge-report.md

**Next:** {verdict-dependent}
- PASS/CONDITIONAL_PASS → Phase 6 (Implementation) — use /agent-teams-execution-plan
- FAIL → Phase 4 (Redesign) — use /agent-teams-write-plan with revision targets
```

### Shutdown

1. Shutdown devils-advocate-1: `SendMessage type: "shutdown_request"`
2. `TeamDelete` — cleans team coordination files
3. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting Requirements

### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
- DP-1: Devils-advocate spawn
- DP-2: Verdict evaluation
- DP-3: User review decision
- DP-4: Gate 5 evaluation

### Sequential Thinking

All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification.

| Agent | When |
|-------|------|
| Lead (5.1) | Input validation, candidate evaluation |
| Lead (5.5) | Gate evaluation, verdict assessment, user presentation |
| Devils-advocate | Every challenge analysis, severity assessment, mitigation design |

### Error Handling

| Situation | Response |
|-----------|----------|
| No Phase 4 output found | Inform user, suggest /agent-teams-write-plan |
| GC-v4 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| Devils-advocate silent >20 min | Send status query |
| Challenge quality too low (Gate 5 iterate) | Re-direct with specific improvement instructions |
| Gate 5 3x iteration | Abort, present partial challenge results to user |
| Context compact | CLAUDE.md §9 recovery |
| User cancellation | Graceful shutdown, preserve artifacts |

### Compact Recovery

- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Devils-advocate: receive fresh context from Lead → read own L1/L2/L3 → resume challenge (no understanding check needed)

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
- Task descriptions follow task-api-guideline.md v6.0 §3 for field requirements

## Never

- Skip spawning devils-advocate (the challenge must come from a separate agent)
- Auto-approve a FAIL verdict (user must decide)
- Auto-chain to Phase 6 after termination
- Proceed past Gate 5 without all criteria met
- Let devils-advocate modify project files (Write access is for L1/L2/L3 output only)
- Accept challenges without evidence (vague "this might fail" is not a valid critique)
- Suppress critical issues to achieve PASS verdict

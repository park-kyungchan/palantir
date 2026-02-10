---
name: verification-pipeline
description: "Phase 7-8 verification — spawns testers to validate Phase 6 implementation, then an integrator for cross-boundary merges. Takes Phase 6 output as input. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to Phase 6 output]"
---

# Verification Pipeline

Phase 7 (Testing) + Phase 8 (Integration) orchestrator. Verifies implementation against design specs through tester teammates, then resolves cross-boundary conflicts through an integrator.

**Announce at start:** "I'm using verification-pipeline to orchestrate Phase 7-8 (Testing + Integration) for this feature."

**Core flow:** PT Check (Lead) → Input Discovery → Team Setup → Tester Spawn → Test Execution → Gate 7 → Integrator Spawn (conditional) → Integration → Gate 8 → Clean Termination

## When to Use

```
Have Phase 6 implementation output?
├── Working in Agent Teams mode? ─── no ──→ Run tests manually
├── yes
├── GC-v5 with Phase 6 COMPLETE? ── no ──→ Run /agent-teams-execution-plan first
├── yes
├── Multiple implementers in Phase 6?
│   ├── yes ──→ Full pipeline (Phase 7 + Phase 8)
│   └── no ──→ Phase 7 only (skip integrator — no cross-boundary merges needed)
└── Use /verification-pipeline
```

**Why both phases?** Tester output (what passes, what fails, which interfaces are verified) directly feeds the integrator's merge strategy. Combining them in one skill avoids context loss between phases.

## Dynamic Context

The following is auto-injected when this skill loads. Use it for Input Discovery.

**Phase 6 Output:**
!`ls -d /home/palantir/.agent/teams/*/phase-6/*/L1-index.yaml 2>/dev/null | while read f; do dir=$(dirname "$f"); echo "--- $(basename $(dirname $(dirname "$dir"))) / $(basename "$dir")"; head -5 "$f"; echo ""; done`

**Gate Records:**
!`ls -t /home/palantir/.agent/teams/*/phase-*/gate-record.yaml 2>/dev/null | head -3`

**Implementation Plans:**
!`ls /home/palantir/docs/plans/*-implementation.md /home/palantir/docs/plans/*-plan.md 2>/dev/null || true`

**Git Status:**
!`cd /home/palantir && git diff --name-only 2>/dev/null | head -20`

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
to 7.1    │     │
          ▼     ▼
        /permanent-tasks    Continue to 7.1
        creates PT-v1       without PT
        → then 7.1
```

If a PERMANENT Task exists, its content (user intent, codebase impact map, prior decisions)
provides additional context for verification. Use it alongside the Dynamic Context above.

If the user opts to create one, invoke `/permanent-tasks` with `$ARGUMENTS` — it will handle
the TaskCreate and return a summary. Then continue to Phase 7.1.

---

## Phase 7.1: Input Discovery + Validation

No teammates spawned. Lead-only step.

Use `sequential-thinking` before every judgment in this phase.

### Discovery

Parse the Dynamic Context above to find Phase 6 execution output:

1. Look for `.agent/teams/*/phase-6/gate-record.yaml` with `result: APPROVED`
2. If `$ARGUMENTS` provides a session-id or path, use that directly
3. If multiple candidates found, present options via `AskUserQuestion`
4. If single candidate, confirm with user: "Found Phase 6 output at {path}. Use this?"
5. If no candidates, inform user: "No Phase 6 output found. Run /agent-teams-execution-plan first."

### Validation

After identifying the source, verify:

| # | Check | On Failure |
|---|-------|------------|
| V-1 | `global-context.md` exists with `Phase 6: COMPLETE` | Abort: "GC-v5 not found or Phase 6 not complete" |
| V-2 | Phase 6 `gate-record.yaml` with `result: APPROVED` | Abort: "Phase 6 gate not approved" |
| V-3 | At least one implementer L1/L2 exists in `phase-6/` | Abort: "No implementer output found" |
| V-4 | Implementation plan exists in `docs/plans/` | Abort: "Design spec not found for test reference" |

### Component Analysis

Count implementers from Phase 6 gate record to determine pipeline shape:

```
Implementer count from Phase 6
     │
┌────┴────┐
1 impl     2+ impl
│           │
▼           ▼
Phase 7     Phase 7 + Phase 8
only        (full pipeline)
```

Use `sequential-thinking` to evaluate validation results.

On all checks PASS → proceed to 7.2.

---

## Phase 7.2: Team Setup

```
TeamCreate:
  team_name: "{feature-name}-verification"
```

Create orchestration-plan.md and copy GC-v5 to new session directory.
Create TEAM-MEMORY.md with Lead, tester, and integrator (if applicable) sections.

---

## Phase 7.3: Tester Spawn + Verification

Use `sequential-thinking` for all Lead decisions in this phase.

### Adaptive Tester Count

```
Phase 6 independent component groups
     │
┌────┴────┐
1 group    2+ groups
│           │
▼           ▼
1 tester   2 testers
            (one per group)
```

### Spawn

For each tester:

```
Task tool:
  subagent_type: "tester"
  team_name: "{feature-name}-verification"
  name: "tester-{N}"
  mode: "default"
```

### Directive Construction

The directive must include these context layers:

1. **PERMANENT Task summary** — embed essential PT content (user intent, impact map, constraints) directly in the directive. Teammates in team context cannot access the main task list.
2. **Phase 6 implementer outputs** — paths to L1/L2 files for the tester's assigned component
3. **Design spec path** — `docs/plans/{plan-file}` for acceptance criteria reference
4. **Test scope instructions** — which components to test, which interfaces to verify

Task-context must instruct tester to:
- Read the design spec (Phase 4 plan) for acceptance criteria and interface contracts
- Read Phase 6 implementer L2 summaries for implementation context
- Use `sequential-thinking` for test strategy decisions
- Use `mcp__context7__query-docs` to verify testing framework APIs
- Design tests covering: acceptance criteria, interface contracts, edge cases, error conditions
- Execute tests and capture results
- Analyze failures with root cause identification
- Write L1/L2/L3 output files
- Report completion with pass/fail summary to Lead via SendMessage

### Verifying Understanding

After tester confirms receipt:
1. Tester explains their test strategy in their own words
2. Lead asks 1 probing question grounded in the Impact Map:
   - Example: "Given that module X depends on Y's output format, what specific contract tests will you write?"
3. On satisfactory answer → tester proceeds
4. On insufficient answer → clarify and re-ask (max 3 attempts)

---

## Phase 7.4: Test Execution

Testers work with: Read, Glob, Grep, Write, Bash, sequential-thinking, context7, tavily.

### Test Design Protocol

For each assigned component:

1. **Read** the implementation (Phase 6 outputs) and design spec (Phase 4 plan)
2. **Design** test suite using sequential-thinking:
   - Acceptance criteria tests (every AC from Phase 4 §4)
   - Interface contract tests (every contract from Phase 4 §3)
   - Edge case tests (derived from Impact Map ripple paths)
   - Error condition tests (failure modes from Phase 4 §8)
3. **Write** test files to L3-full/ directory
4. **Execute** tests via Bash (language-appropriate test runner)
5. **Analyze** failures — root cause, affected modules, fix recommendations

### Expected Output

```
.agent/teams/{session-id}/phase-7/tester-{N}/
├── L1-index.yaml    (YAML, ≤50 lines — test files, pass/fail, coverage)
├── L2-summary.md    (Markdown, ≤200 lines — test narrative + failure analysis)
└── L3-full/
    ├── test files (*.test.*, *_test.*, test_*.*)
    ├── test-results.log
    └── coverage-report.md (if applicable)
```

Tester reports completion with pass/fail summary to Lead via SendMessage.

---

## Phase 7.5: Gate 7

Use `sequential-thinking` for all gate evaluation.

### Criteria

| # | Criterion | Method |
|---|-----------|--------|
| G7-1 | All acceptance criteria from Phase 4 have corresponding tests | Cross-reference plan §4 ACs with test files |
| G7-2 | Interface contracts tested | Verify contract tests exist for each Phase 4 §3 interface |
| G7-3 | Coverage analysis present (what's tested, what's intentionally excluded with rationale) | Read L2-summary.md |
| G7-4 | Failure analysis quality (root causes identified, fix recommendations provided) | Read L2 failure section |
| G7-5 | Tester L1/L2/L3 artifacts exist | Check file existence |

### Test Result Evaluation

Read tester L2-summary.md:

**ALL PASS:**
- Proceed to Phase 8 (or Clean Termination if single implementer)
- Add Phase 7 status to GC

**FAILURES FOUND:**
- Present failure summary to user
- Ask: "Accept failures and proceed to integration, or return to Phase 6 for fixes?"
- If accepted: Document known failures in GC, proceed
- If rejected: Return to Phase 6 with specific fix targets

### On APPROVE

1. Update GC: Add `Phase 7: COMPLETE (Gate 7 APPROVED)`
2. Write `phase-7/gate-record.yaml`
3. If single implementer → skip to Clean Termination
4. If multiple implementers → proceed to Phase 8.1

### On ITERATE (max 3)

- If test quality insufficient: relay specific improvement instructions
- Tester revises and resubmits
- Re-evaluate Gate 7

---

## Phase 8.1: Integrator Spawn + Verification

**Conditional phase** — only runs if Phase 6 had 2+ implementers with separate file ownership boundaries. If Phase 6 had a single implementer, skip to Clean Termination.

Use `sequential-thinking` for all Lead decisions in this phase.

### Spawn

```
Task tool:
  subagent_type: "integrator"
  team_name: "{feature-name}-verification"
  name: "integrator-1"
  mode: "default"
```

### Directive Construction

The directive must include these context layers:

1. **PERMANENT Task summary** — embed essential PT content directly in directive
2. **Phase 6 implementer L1/L2 paths** — all implementer outputs for conflict detection
3. **Phase 7 tester L2 path** — test results informing merge priorities
4. **Design spec path** — interface contracts that must be preserved
5. **File ownership map** — from Phase 6, which implementer owned which files

Task-context must instruct integrator to:
- Read all Phase 6 implementer L1/L2/L3 outputs
- Read Phase 7 tester results
- Identify conflicts (file overlaps, interface mismatches, dependency issues)
- Submit integration plan to Lead before any file modifications
- Resolve conflicts preserving both implementers' intent
- Run integration tests after each batch of resolutions
- Write discoveries to TEAM-MEMORY.md (own section)
- Write L1/L2/L3 output files
- Report completion to Lead via SendMessage

### Verifying Understanding

After integrator confirms receipt:
1. Integrator explains the conflicts they've identified
2. Lead asks 2 probing questions grounded in the Impact Map:
   - Example: "Trace the dependency chain from module A to C — what happens if the merge changes B's interface?"
   - Example: "How will you verify the merge doesn't break the tested interfaces from Phase 7?"
3. On satisfactory answers → integrator submits plan → Lead approves → execution begins

---

## Phase 8.2: Integration Execution

Integrator works with: Read, Glob, Grep, Edit, Write, Bash, sequential-thinking, context7, tavily.

### Integration Protocol

1. **Read** all implementer L1/L2/L3 from Phase 6
2. **Read** tester results from Phase 7
3. **Identify** conflicts using sequential-thinking:
   - File-level: multiple implementers modified adjacent code
   - Interface-level: incompatible contracts between components
   - Dependency-level: ripple effects from Impact Map
4. **Submit plan** to Lead: conflicts found, resolution strategy per conflict, affected files, risk level
5. **Resolve** conflicts with documented rationale (use Edit tool)
6. **Test** integration after each batch (use Bash for test runners)
7. **Verify** against Phase 4 interface specs

### Conflict Resolution Principles

1. Preserve both implementers' intent when possible
2. Irreconcilable conflict → escalate to Lead
3. Document every resolution decision in L2
4. Verify resolved code against Phase 4 interface specs
5. Run integration tests after each resolution batch

### Expected Output

```
.agent/teams/{session-id}/phase-8/integrator-1/
├── L1-index.yaml    (YAML, ≤50 lines — conflicts, resolutions, test results)
├── L2-summary.md    (Markdown, ≤200 lines — integration narrative + rationale)
└── L3-full/
    ├── conflict-resolution-log.md
    ├── integration-test-results.log
    └── merged-diff.patch (if applicable)
```

Integrator reports completion to Lead via SendMessage.

---

## Phase 8.3: Gate 8

Use `sequential-thinking` for all gate evaluation.

### Criteria

| # | Criterion | Method |
|---|-----------|--------|
| G8-1 | All identified conflicts resolved with documented rationale | Read L2 conflict resolution section |
| G8-2 | Integration tests pass | Read L3 test results |
| G8-3 | Phase 4 interface contracts preserved post-merge | Cross-reference spec vs. merged code |
| G8-4 | No unauthorized cross-boundary modifications | Verify changes within integrator's scope |
| G8-5 | Integrator L1/L2/L3 artifacts exist | Check file existence |

### On APPROVE

1. Update GC: Add `Phase 8: COMPLETE (Gate 8 APPROVED)`
2. Write `phase-8/gate-record.yaml`
3. Proceed to Clean Termination

### On ITERATE (max 3)

- Specific fix instructions to integrator
- Integrator revises and resubmits
- Re-evaluate Gate 8

---

## Clean Termination

After final gate decision (Gate 7 for single-implementer, Gate 8 for multi-implementer):

### GC Update

Add to global-context.md:

```markdown
## Phase Pipeline Status
- Phase 7: COMPLETE (Gate 7 APPROVED)
- Phase 8: COMPLETE (Gate 8 APPROVED) / SKIPPED (single implementer)

## Verification Results
- Tests: {pass}/{total} ({pass rate}%)
- Coverage: {summary}
- Failures resolved: {count}
- Integration conflicts: {count} (if Phase 8 ran)

## Phase 9 Entry Conditions
- All tests passing
- All conflicts resolved (if applicable)
- Known issues: {list or "none"}
```

### Output Summary

```markdown
## verification-pipeline Complete (Phase 7-8)

**Feature:** {name}
**Testers:** {count}
**Integrator:** {yes/no (skipped if single implementer)}

**Test Results:**
- Pass: {count}
- Fail: {count}
- Coverage: {summary}

**Integration:** {conflicts resolved or "N/A — single implementer"}

**Gate 7:** APPROVED
**Gate 8:** APPROVED / SKIPPED

**Artifacts:** .agent/teams/{session-id}/
**Global Context:** GC-v6

**Next:** Phase 9 (Delivery) — Lead-only phase. Commit, PR, documentation.
```

### Shutdown

1. Shutdown testers: `SendMessage type: "shutdown_request"` to each
2. Shutdown integrator (if spawned): `SendMessage type: "shutdown_request"`
3. `TeamDelete` — cleans team coordination files
4. Artifacts preserved in `.agent/teams/{session-id}/`

---

## Cross-Cutting Requirements

### RTD Index

At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)

Decision Points for this skill:
- DP: Tester spawn
- DP: Test evaluation
- DP: Integrator spawn
- DP: Integration review
- DP: Gate 7/8 evaluation

### Sequential Thinking

All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification.

| Agent | When |
|-------|------|
| Lead (7.1) | Input validation, component analysis |
| Lead (7.3) | Understanding verification, tester count decision |
| Lead (7.5) | Gate 7 evaluation, test result assessment |
| Lead (8.1) | Understanding verification, plan approval |
| Lead (8.3) | Gate 8 evaluation, conflict resolution assessment |
| Tester | Test strategy design, failure analysis, coverage decisions |
| Integrator | Conflict identification, resolution strategy, ripple analysis |

### Error Handling

| Situation | Response |
|-----------|----------|
| No Phase 6 output found | Inform user, suggest /agent-teams-execution-plan |
| GC-v5 incomplete | Abort with missing section list |
| Spawn failure | Retry once, abort with notification |
| Tester silent >20 min | Send status query |
| All tests fail | Present to user, suggest return to Phase 6 |
| Integrator conflict irreconcilable | Escalate to user with options |
| Gate 7/8 3x iteration | Abort, present partial results to user |
| Context compact | CLAUDE.md §9 recovery |
| User cancellation | Graceful shutdown, preserve artifacts |

### Compact Recovery

- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Tester: receive fresh context from Lead → read own L1/L2/L3 → resume testing
- Integrator: receive fresh context from Lead → read own L1/L2/L3 → resume integration

---

## Key Principles

- **Test behavior, not implementation** — verify what the code does, not how it does it
- **Evidence-based coverage** — every test gap must be justified with rationale
- **Sequential phases** — testers complete before integrator starts (P7 feeds P8)
- **Conditional integration** — skip Phase 8 if single implementer (no cross-boundary merges)
- **Conflict resolution documented** — every merge decision has rationale in L2
- **Sequential thinking always** — structured reasoning at every decision point
- **PT in directive** — embed essential PERMANENT Task content in directives (teammates can't access main task list)
- **Protocol delegated** — CLAUDE.md owns verification rules, skill owns orchestration
- **Clean termination** — no auto-chaining to Phase 9
- **Artifacts preserved** — all outputs survive in `.agent/teams/{session-id}/`

## Never

- Skip testing (even for "obvious" implementations)
- Let integrator modify files without Lead-approved plan
- Start Phase 8 before Phase 7 gate approval
- Auto-chain to Phase 9 after termination
- Proceed past Gate 7 or Gate 8 without all criteria met
- Accept test results without coverage analysis
- Let integrator merge without documented conflict resolution rationale
- Trust test pass rates without reading failure analysis
- Spawn integrator for single-implementer scenarios (no conflicts to resolve)

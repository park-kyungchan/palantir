---
name: verification-pipeline
description: "Phase 7-8 verification — spawns testers to validate Phase 6 implementation, then an integrator for cross-boundary merges. Takes Phase 6 output as input. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "[session-id or path to Phase 6 output]"
---

# Verification Pipeline

Phase 7 (Testing) + Phase 8 (Integration) orchestrator. Verifies implementation against design specs through tester teammates, then resolves cross-boundary conflicts through an integrator.

**Announce at start:** "I'm using verification-pipeline to orchestrate Phase 7-8 (Testing + Integration) for this feature."

**Core flow:** PT Check (Lead) → Input Discovery → Team Setup → Coordinator + Worker Spawn → Coordinator-Managed Testing → Gate 7 → Coordinator-Managed Integration (conditional) → Gate 8 → Clean Termination

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

### Rollback Detection

Check for `rollback-record.yaml` in downstream phase directories (phase-8/):
- If found: read rollback context (revision targets, prior-attempt lessons) per `pipeline-rollback-protocol.md` §3
- Include rollback context in tester directives (what was attempted, why rolled back, areas to focus on)
- If not found: proceed normally

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
Create TEAM-MEMORY.md with Lead, testing-coordinator, tester, and integrator (if applicable) sections.

---

## Phase 7.3: Testing Coordinator Spawn + Worker Pre-Spawn

Use `sequential-thinking` for all Lead decisions in this phase.

### Pipeline Tier Awareness (D-001)

> TRIVIAL tier skips Phase 7 entirely. STANDARD tier runs Phase 7 only (no Phase 8).
> COMPLEX tier runs full Phase 7 + Phase 8.

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

COMPLEX tier: add contract-tester for interface verification
```

### Testing Coordinator Spawn

```
Task tool:
  subagent_type: "testing-coordinator"
  team_name: "{feature-name}-verification"
  name: "test-coord"
  mode: "default"
```

#### [DIRECTIVE] for Testing Coordinator

Include these context layers:

1. **PERMANENT Task content** — embed essential PT content (user intent, impact map, constraints)
2. **Phase 6 implementer outputs** — paths to L1/L2 files per component
3. **Design spec path** — `docs/plans/{plan-file}` for acceptance criteria reference
4. **Test scope instructions** — which components to test, which interfaces to verify
5. **Phase 8 conditional trigger** — integrator needed if 2+ implementers in Phase 6
6. **Worker names** — sent via follow-up message after worker pre-spawn

### Worker Pre-Spawn

After testing-coordinator confirms ready, pre-spawn workers:

```
# Testers (per adaptive tester count)
Task(subagent_type="tester", name="tester-{N}",
     mode="default", team_name="{feature}-verification")

# Contract Tester (D-005 — COMPLEX tier only, interface contract verification)
Task(subagent_type="contract-tester", name="contract-test",
     mode="default", team_name="{feature}-verification")

# Integrator (conditional — only if 2+ implementers)
Task(subagent_type="integrator", name="integrator-1",
     mode="default", team_name="{feature}-verification")
```

Worker directives include:
- "Your coordinator is: test-coord. Report progress and completion to your coordinator."
- PT content (embedded) — user intent, impact map, constraints
- Phase 6 output paths for test reference
- Design spec path for acceptance criteria

After workers spawned, inform coordinator:
```
SendMessage to test-coord:
  "Workers spawned: tester-1, [tester-2], [integrator-1].
   Begin worker verification and test execution."
```

### Understanding Verification (Delegated — AD-11)

```
Level 1: Lead verifies testing-coordinator
  - Full Impact Map context
  - 1-2 probing questions about test + integration strategy
  - Coordinator explains their management plan

Level 2: Testing-coordinator verifies workers
  - 1-2 questions per worker using Impact Map excerpt
  - Reports verification status to Lead
```

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
3. **Write** test files to TWO locations:
   a. **Project test directory** — following discovered conventions (committable, CI-discoverable)
   b. **L3-full/** — copy for session archival
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

Read testing-coordinator's consolidated L2-summary.md (includes tester results):

**ALL PASS:**
- Proceed to Phase 8 (or Clean Termination if single implementer)
- Add Phase 7 status to GC

**FAILURES FOUND:**
- Present failure summary to user
- Ask: "Accept failures and proceed to integration, or return to Phase 6 for fixes?"
- If accepted: Document known failures in GC, proceed
- If rejected: Execute rollback P7→P6 per `pipeline-rollback-protocol.md` with specific fix targets

### Gate Audit (STANDARD/COMPLEX)

Optional for STANDARD, mandatory for COMPLEX (see `gate-evaluation-standard.md` §6).
If audit required: spawn `gate-auditor` with G7 criteria and evidence paths.
Compare verdicts per §6 procedure. On disagreement → escalate to user.

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

## Phase 8.1: Integration Phase (Coordinator-Managed)

**Conditional phase** — only runs if Phase 6 had 2+ implementers with separate file ownership
boundaries. If Phase 6 had a single implementer, skip to Clean Termination.

Use `sequential-thinking` for all Lead decisions in this phase.

### Coordinator Transition

Testing-coordinator is already active from Phase 7. Integrator was pre-spawned in Phase 7.3.
No new spawning needed.

Lead sends transition message to testing-coordinator:
```
SendMessage to test-coord:
  "Phase 7 Gate APPROVED. Transition to Phase 8.
   Integration scope: {file ownership boundaries from Phase 6}
   Tester results: {path to Phase 7 output}
   Begin integrator management."
```

### Coordinator Manages Integration

Testing-coordinator:
1. Assigns integration scope to integrator with: Phase 6 outputs, Phase 7 test results,
   file ownership map, design spec interface contracts
2. Verifies integrator understanding (1-2 probing questions from Impact Map excerpt)
3. Reviews integrator's plan before approving execution
4. Monitors integration progress
5. Reports to Lead for Gate 8 evaluation

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
| G8-6 | Testing-coordinator consolidated L2 exists | Check file existence |

### Gate Audit (COMPLEX only)

Mandatory for COMPLEX tier (see `gate-evaluation-standard.md` §6).
Spawn `gate-auditor` with G8 criteria and evidence paths (integrator L2, merge results).
Compare verdicts per §6 procedure. On disagreement → escalate to user.

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

1. Shutdown testing-coordinator: `SendMessage type: "shutdown_request"`
   (coordinator signals workers to stop)
2. Shutdown remaining workers directly if still active
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
- **Sequential phases** — testers complete before integrator starts, enforced by testing-coordinator
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

# Sections 6-10: Execution Strategy, Validation, Risk, Commit, Rollback

> Strategy Planner · Phase 4 · Skill Optimization v9.0
> Sections: §6 (Execution Sequence), §7 (Validation Checklist), §8 (Risk Mitigation),
> §9 (Commit Strategy), §10 (Rollback & Recovery)

---

## 6. Execution Sequence

### Implementer Roster (from §3 File Ownership)

| ID | Role | Agent Type | Files | Coupling Group |
|----|------|-----------|:-----:|----------------|
| impl-a1 | Fork Implementer 1 | `implementer` | 4 | fork-cluster-1: pt-manager.md (CREATE), permanent-tasks SKILL (MODIFY), delivery-agent.md (CREATE), delivery-pipeline SKILL (MODIFY) |
| impl-a2 | Fork Implementer 2 | `implementer` | 3 | fork-cluster-2: rsil-agent.md (CREATE), rsil-global SKILL (MODIFY), rsil-review SKILL (MODIFY) |
| impl-b | Skill Implementer | `implementer` | 5 | coord-skills: 5 coordinator-based SKILL.md |
| infra-c | Coord Convergence | `infra-implementer` | 8 | coord-convergence: 8 coordinator .md (Template B) |
| infra-d | Protocol Editor | `infra-implementer` | 2 | protocol-pair: CLAUDE.md §10 + agent-common-protocol.md |
| verifier | Cross-Ref Verifier | `integrator` | 0 (reads all) | verification: V6a checks + 8 cross-file reference checks |

### Dependency DAG (Concrete)

```
Wave 1: Implementation (all 5 implementers start simultaneously)
  ├── infra-d: CLAUDE.md §10 + protocol (2 files)           ── parallel ──┐
  ├── infra-c: 8 coordinator .md (Template B)                ── parallel ──┤
  ├── impl-a1: pt-manager.md → permanent-tasks SKILL         ── internal ──┤
  │             delivery-agent.md → delivery-pipeline SKILL   ── sequence ──┤
  ├── impl-a2: rsil-agent.md → rsil-global SKILL             ── internal ──┤
  │             → rsil-review SKILL                           ── sequence ──┤
  └── impl-b: 5 coordinator SKILL.md                         ── parallel ──┘
                                                                            │
Wave 2: Cross-Reference Verification (after ALL Wave 1 complete)            │
  └── verifier: V6a checks + cross-file refs ◄──────────────────────────────┘
                          │
Wave 3: Pre-Deploy Functional Validation (A → B → C → D)
  └── Lead executes ◄────┘
                │
Wave 4: Atomic Commit
  └── Lead or designated implementer ◄────┘
```

### Wave 1: Implementation (5 parallel tracks)

All 5 implementers spawn simultaneously. No cross-implementer dependencies exist because fork agent .md and fork SKILL.md are co-located within the same implementer (impl-a1, impl-a2).

| Implementer | Internal Ordering | Files (in order) | Est. Effort |
|-------------|-------------------|------------------|:-----------:|
| impl-a1 | Sequential: CREATE agent .md first, then MODIFY skills | 1. pt-manager.md (CREATE) 2. permanent-tasks SKILL.md (MODIFY) 3. delivery-agent.md (CREATE) 4. delivery-pipeline SKILL.md (MODIFY) | HIGH — 4 files, 2 creates |
| impl-a2 | Sequential: CREATE agent .md first, then MODIFY skills | 1. rsil-agent.md (CREATE) 2. rsil-global SKILL.md (MODIFY) 3. rsil-review SKILL.md (MODIFY) | MEDIUM — 3 files, 1 create (shared agent) |
| impl-b | Any order (independent) | 5 coordinator-based SKILL.md (brainstorming, write-plan, validation, execution, verification) | HIGH — 5 files, all modify |
| infra-c | Any order (independent) | 8 coordinator .md (Template B convergence) | MEDIUM — 8 files, all modify (formulaic) |
| infra-d | Sequential: §10 first | 1. CLAUDE.md §10 (MODIFY) 2. agent-common-protocol.md §Task API (MODIFY) | LOW — 2 files, small changes |

**Why co-location eliminates Wave 1→2 split:**
The abstract design had Wave 1 (foundation) → Wave 2 (skills) with a cross-wave dependency: fork skills depend on fork agent .md for the `agent:` field. By assigning both the agent .md (CREATE) and its consuming skill (MODIFY) to the same implementer, the dependency becomes an internal ordering concern. The implementer creates the agent .md first, then modifies the skill — no cross-implementer coordination needed.

**Internal ordering for impl-a1 and impl-a2:**
Each creates their agent .md file(s) BEFORE modifying the corresponding skill(s). This ensures the `agent:` frontmatter reference is valid at the implementer's self-verification step. The directive to each implementer must explicitly state: "Create agent .md files first, then modify SKILL.md files."

**Parallel execution constraints:**
- All 5 implementers work on non-overlapping file sets → zero conflict risk
- infra-d finishes fastest (2 small changes) — will idle while others complete
- impl-a1 takes longest (4 files, 2 creates) — the critical path of Wave 1
- No cross-implementer communication needed during Wave 1

### Wave 2: Cross-Reference Verification

**Trigger:** All 5 implementers report completion.

**Agent:** verifier (integrator type, reads all 22 files, owns none)

**Verification tasks (8 checks, mapping to §7):**

| # | Check | V-ref | Files Involved |
|---|-------|:-----:|----------------|
| 1 | YAML frontmatter parse | V1 | All 20 files with frontmatter |
| 2 | Required keys present | V2 | All 20 files (type-specific key sets) |
| 3 | Fork `agent:` → agent .md exists | V3 | 4 fork SKILL.md → 3 agent .md |
| 4 | §10 names → agent .md exists | V3 | CLAUDE.md → 3 agent .md |
| 5 | Protocol names → §10 names match | V3 | agent-common-protocol.md ↔ CLAUDE.md |
| 6 | Template section ordering | V4 | 9 SKILL.md (5 coord + 4 fork template) |
| 7 | disallowedTools match spec | V5 | 11 agent .md (3 fork + 8 coordinator) |
| 8 | V6a additional: mode, memory, context | V6a | 9 SKILL.md + 11 agent .md |

**Gate:** ALL 8 checks PASS → proceed to Wave 3. Any failure → fix-loop (implementer fixes, verifier re-checks).

### Wave 3: Pre-Deploy Functional Validation (A → B → C → D)

**Executor:** Lead (not a spawned agent — Lead invokes skills directly)

Sequential, ordered by risk. Full specification in §8 Pre-Deploy Validation Sequence.

```
A: V6a structural (redundant with Wave 2, confirms no regression)
   → custom agent resolution test
   → task list scope test
   → fork spawn mechanism test
        ↓
B: /rsil-global functional test (lowest risk fork)
        ↓
C: /rsil-review + /permanent-tasks functional test (medium risk)
   [if C fix touches rsil-agent.md → re-run B]
        ↓
D: /delivery-pipeline functional test (highest risk, fork last)
```

**Gate:** ALL phases A-D PASS → proceed to Wave 4.

### Wave 4: Atomic Commit

**Executor:** Lead or designated implementer with Bash access.

1. Stage all 22 files (§9 explicit `git add` command)
2. Commit with structured message (§9 template)
3. Post-commit verification: `/rsil-global` + `git diff HEAD~1 --stat`

### Timeline Summary

```
Time →
 ┌────────────────────────────────────────┐
 │ Wave 1: Implementation (5 parallel)     │
 │ infra-d ██░░░░░░░░░░░░░░░░░░░░░░░░░░  │ (fastest — 2 files)
 │ infra-c ██████████████░░░░░░░░░░░░░░░  │ (8 formulaic files)
 │ impl-a2 ██████████████████░░░░░░░░░░░  │ (3 files, 1 create)
 │ impl-b  ████████████████████████░░░░░  │ (5 files, all modify)
 │ impl-a1 ██████████████████████████████  │ (4 files, 2 creates — critical path)
 └────────────────────────┬───────────────┘
                          │ all 5 complete
 ┌────────────────────────▼───────────────┐
 │ Wave 2: Verification (verifier)         │
 │ 8 cross-ref checks ███████             │
 └────────────────────────┬───────────────┘
                          │ all 8 pass
 ┌────────────────────────▼───────────────┐
 │ Wave 3: Pre-Deploy (Lead)               │
 │ A ██ → B ███ → C ████ → D ███         │
 └────────────────────────┬───────────────┘
                          │ all pass
 ┌────────────────────────▼───────────────┐
 │ Wave 4: Commit                          │
 │ git add + commit ██                    │
 └────────────────────────────────────────┘
```

### Cross-File Dependency Matrix (Concrete)

```
                    Depends On →
                    §10    protocol  fork-agent  coord.md  fork-skill  coord-skill
                    (d)    (d)       (a1,a2)     (c)       (a1,a2)     (b)
§10 mod (d)          —      —          —          —          —           —
protocol (d)         —      —          —          —          —           —
fork agent (a1,a2)   —      —          —          —          —           —
coordinator (c)      —     weak        —          —          —           —
fork SKILL (a1,a2)   —      —        INTERNAL     —          —           —
coord SKILL (b)      —      —          —        weak         —           —

Legend: INTERNAL = dependency co-located in same implementer (resolved internally)
        weak = consistency dependency (pre-existing names unchanged)
        — = no dependency
```

**Key insight:** The STRONG dependency from the abstract design (fork SKILL → fork agent .md) is now INTERNAL — resolved within impl-a1 and impl-a2 via internal ordering. No cross-implementer STRONG dependencies exist, enabling full Wave 1 parallelism.

---

## 7. Validation Checklist

> All checks apply to the 22+ target files in the Big Bang commit.
> V1-V5 are automatable (V6a). V6 splits into automated + manual.

### V1: YAML Frontmatter Parseability

Extract YAML between `---` markers and parse. Every file with frontmatter must parse cleanly.

- [ ] 9 SKILL.md files: `.claude/skills/{name}/SKILL.md`
  - brainstorming-pipeline, agent-teams-write-plan, plan-validation-pipeline,
    agent-teams-execution-plan, verification-pipeline, delivery-pipeline,
    rsil-global, rsil-review, permanent-tasks
- [ ] 8 coordinator .md files: `.claude/agents/{name}.md`
  - research-coordinator, verification-coordinator, architecture-coordinator,
    planning-coordinator, validation-coordinator, execution-coordinator,
    testing-coordinator, infra-quality-coordinator
- [ ] 3 fork agent .md files (NEW): `.claude/agents/{name}.md`
  - pt-manager, delivery-agent, rsil-agent

**Method:** `python3 -c "import yaml, sys; yaml.safe_load(sys.stdin.read())"` on extracted frontmatter.
**Pass criterion:** Zero parse errors across 20 files.

### V2: Required Frontmatter Keys

| File Type | Required Keys |
|-----------|--------------|
| Coordinator-based SKILL.md (5) | `name`, `description`, `argument-hint` |
| Fork-based SKILL.md (4) | `name`, `description`, `argument-hint`, `context: fork`, `agent` |
| Coordinator agent .md (8) | `name`, `description`, `model`, `permissionMode`, `memory: project`, `color`, `maxTurns`, `tools`, `disallowedTools` |
| Fork agent .md (3) | `name`, `description`, `model`, `permissionMode`, `memory: user`, `color`, `maxTurns`, `tools`, `disallowedTools` |

**Method:** grep for each required key in extracted frontmatter.
**Pass criterion:** All required keys present in all 20 files. No unexpected key omissions.

### V3: Cross-File Reference Accuracy

| Reference | Source Files | Target | Check |
|-----------|-------------|--------|-------|
| Fork `agent:` field | 4 fork SKILL.md | `.claude/agents/{value}.md` | File exists |
| §10 agent names | CLAUDE.md §10 | `.claude/agents/{name}.md` | All 3 files exist |
| Protocol agent names | agent-common-protocol.md | CLAUDE.md §10 list | Names match exactly |
| Coordinator `subagent_type` refs | 5 coordinator SKILL.md | `.claude/agents/{name}.md` | Agent files exist |
| Fork agent `disallowedTools` | 3 fork agent .md | §10 scope | Matches specification |

**Method:** grep + file existence check.
**Pass criterion:** Zero dangling references. Zero name mismatches.

Specific checks:
- [ ] `permanent-tasks` SKILL.md `agent: "pt-manager"` → `.claude/agents/pt-manager.md` exists
- [ ] `delivery-pipeline` SKILL.md `agent: "delivery-agent"` → `.claude/agents/delivery-agent.md` exists
- [ ] `rsil-global` SKILL.md `agent: "rsil-agent"` → `.claude/agents/rsil-agent.md` exists
- [ ] `rsil-review` SKILL.md `agent: "rsil-agent"` → `.claude/agents/rsil-agent.md` exists
- [ ] CLAUDE.md §10 lists exactly: `pt-manager`, `delivery-agent`, `rsil-agent`
- [ ] agent-common-protocol.md §Task API lists same 3 names

### V4: Template Section Ordering

**Coordinator-based skills (5)** must follow this heading order:
```
# {Title}
## When to Use
## Dynamic Context
## A) Phase 0: PERMANENT Task Check
## B) Phase {N}: {workflow}
## C) Interface Section
## D) Cross-Cutting
## Key Principles
## Never
```

**Fork-based skills (4)** must follow this heading order:
```
# {Title}
## When to Use
## Dynamic Context
## Phase 0: PERMANENT Task Check
## {Core Workflow sections}
## Interface
## Cross-Cutting
## Key Principles
## Never
```

**Method:** Extract `## ` headings from each SKILL.md, verify order matches template.
**Pass criterion:** All 9 skills follow their template's section ordering.

### V5: disallowedTools Consistency

| Agent File | Expected `disallowedTools` | Rationale |
|-----------|---------------------------|-----------|
| pt-manager.md | `[]` (empty) | Full Task API — D-10 exception for PT creation |
| delivery-agent.md | `[TaskCreate]` | TaskUpdate only — marks DELIVERED |
| rsil-agent.md | `[TaskCreate]` | TaskUpdate only — updates PT Phase Status |
| All 8 coordinator .md | `[TaskCreate, TaskUpdate, Edit, Bash]` | Read-only + Write for L1/L2/L3 |

**Method:** Parse `disallowedTools` from each frontmatter, compare against expected.
**Pass criterion:** Exact match for all 11 agent files.

### V6: Code Plausibility

**V6a — Automated (integrated into V1-V5 above + additional):**
- [ ] All checks from V1-V5 pass
- [ ] `mode: "default"` in all skill spawn examples (BUG-001)
- [ ] No `mode: "plan"` anywhere in spawn parameters
- [ ] `memory: project` for all 8 coordinators (ADR-S3)
- [ ] `memory: user` for all 3 fork agents
- [ ] `context: fork` present in all 4 fork SKILL.md frontmatter
- [ ] `context: fork` absent from all 5 coordinator SKILL.md frontmatter

**V6b — Manual Semantic Review (during P6 two-stage review):**
- [ ] V6b-1: NL instruction consistency — skill body instructions don't contradict agent .md body
- [ ] V6b-2: Voice consistency — fork skills use 2nd person ("You do X"), coordinator skills use 3rd person ("Lead does X")
- [ ] V6b-3: Cross-cutting completeness — coordinator skills have 1-line CLAUDE.md references (ADR-S8), fork skills have inline error handling
- [ ] V6b-4: Behavioral plausibility — error paths are logically reachable, recovery instructions are sound
- [ ] V6b-5: Interface Section content matches C-1~C-5 contracts from interface-architect L3

---

## 8. Risk Mitigation Strategy

### Overview

4 active risks tracked from Phase 3 architecture. Each risk has: primary mitigation, fallback, residual risk assessment, and implementation touchpoints.

### RISK-2: PT Fork Loses Conversation History (MED-HIGH, CERTAIN)

**Affects:** permanent-tasks skill (pt-manager fork agent)

**3-layer mitigation (by invocation context):**

| Layer | Context | Mitigation | Coverage |
|-------|---------|------------|----------|
| 1 | Pipeline auto-invocation | $ARGUMENTS carries structured context from Phase 0 code. Dynamic Context provides git log, plans, infrastructure version. | FULL — no degradation |
| 2 | Manual with rich $ARGUMENTS | User provides `/permanent-tasks "Detailed description of changes..."`. Dynamic Context supplements. | PARTIAL — depends on user input quality |
| 3 | Manual with sparse $ARGUMENTS | pt-manager uses AskUserQuestion to probe for missing context. Reads git log, existing PT, plans directory for supplemental context. | DEGRADED — more interactive, slower |

**Implementation touchpoints:**
- pt-manager.md §Context Sources: priority order ($ARGUMENTS → Dynamic Context → TaskList/TaskGet → AskUserQuestion)
- pt-manager.md §Error Handling: `$ARGUMENTS empty → extract from Dynamic Context; if insufficient, AskUserQuestion`
- permanent-tasks SKILL.md §Dynamic Context: must include `!git log --oneline -20`, `!ls docs/plans/`, infrastructure version

**Residual risk:** Users accustomed to Lead-in-context (rich conversation history) will experience context richness step-down in manual invocation. Accept — document in skill description.

### RISK-3: Delivery Fork Complexity (MEDIUM, HIGH likelihood)

**Affects:** delivery-pipeline skill (delivery-agent fork agent)

**4-layer mitigation:**

1. **No nested skill invocation:** delivery-agent.md explicitly states: "If no PERMANENT Task found, inform user: 'Please run /permanent-tasks first.' Do NOT invoke /permanent-tasks." Eliminates double-fork problem entirely.

2. **Idempotent operations:** Each of the 7 delivery operations is designed for safe re-run:
   - ARCHIVE.md write: overwrite-safe (Write tool is atomic)
   - MEMORY.md merge: Read-Merge-Write pattern (rerunnable)
   - Git commit: naturally atomic (fails cleanly if nothing staged)
   - Session discovery: deterministic (same input → same output)

3. **User confirmation gates:** 5+ AskUserQuestion checkpoints. No operation proceeds without explicit user approval. User can abort at any gate.

4. **Fork-last validation:** delivery-pipeline is Phase D in pre-deploy validation — tested LAST, after simpler forks (B: rsil-global, C: rsil-review + permanent-tasks) prove stable.

**Fallback:** If delivery fork proves unreliable in validation, revert delivery-pipeline to Lead-in-context execution while keeping the other 3 skills as fork. Partial adoption is safe because delivery-pipeline has no downstream consumers.

**Residual risk:** Fork termination between MEMORY.md write and git commit leaves dirty state. Recovery: user re-runs `/delivery-pipeline` — discovery algorithm picks up partial state.

### RISK-5: Big Bang 22+ Files (HIGH, MEDIUM likelihood)

**Affects:** All 22+ files committed atomically (D-8 mandate)

**5-layer mitigation:**

1. **V6a automated structural validation (pre-deploy Phase A):**
   - YAML frontmatter parseability for all 20 frontmatter files
   - Required keys presence check
   - Cross-file reference accuracy (no dangling agent references)
   - Template section ordering
   - disallowedTools consistency with §10 specification
   - `mode: "default"` everywhere (BUG-001)

2. **Non-overlapping file ownership:** Each implementer owns a distinct file set. No concurrent edits to the same file. Integrator resolves cross-boundary issues after primary implementation.

3. **Cross-reference verification (Wave 3):** After all files written, systematic verification of every cross-file reference before commit.

4. **Atomic commit:** Single `git commit` — all-or-nothing. Easy rollback via `git revert HEAD`.

5. **Smoke test sequence (pre-deploy B→C→D):** Functional validation of fork skills in risk order. Catches runtime issues that structural checks miss.

**Residual risk:** Subtle NL instruction conflicts may not surface until next pipeline run. Detected by `/rsil-global` post-commit assessment.

### RISK-8: Task List Scope in Fork (MEDIUM, MEDIUM likelihood)

**Affects:** All 4 fork skills (pt-manager most critical, delivery-agent second, rsil-agent least)

**Primary plan (fork agents share main session's task list):**
- Fork agents call TaskList → see [PERMANENT] task → TaskGet for content
- C-4 contract (fork-to-PT direct) works as designed
- Pre-deploy Phase A explicitly tests this assumption

### RISK-8 Fallback Delta

If pre-deploy Phase A reveals fork agents see ISOLATED task list:

**Delta changes (~50 lines across 8 files):**

| File | Primary Plan | Delta (Fallback) |
|------|-------------|-------------------|
| permanent-tasks SKILL.md | Phase 0 uses TaskList to discover PT | Dynamic Context injects PT task ID via `!command`; $ARGUMENTS carries PT-ID; TaskGet with explicit ID |
| delivery-pipeline SKILL.md | Phase 0 uses TaskList | Same — Dynamic Context + $ARGUMENTS PT-ID |
| rsil-global SKILL.md | Phase 0 uses TaskList (optional) | Skip PT discovery; rely on Dynamic Context only |
| rsil-review SKILL.md | Phase 0 uses TaskList (optional) | Same as rsil-global |
| pt-manager.md | TaskList in Step 1 | Accept $ARGUMENTS PT-ID; if absent, AskUserQuestion for PT-ID |
| delivery-agent.md | TaskList in Phase 0 | Accept $ARGUMENTS PT-ID; if absent, warn user |
| rsil-agent.md | TaskList optional | No change needed — PT is supplemental context |
| CLAUDE.md §10 | No change | No change |

**Impact assessment:**
- pt-manager: MODERATE degradation — loses autonomous PT discovery, requires $ARGUMENTS to carry PT-ID. Layer 3 mitigation (AskUserQuestion) still functional.
- delivery-agent: MODERATE — same as pt-manager. User provides PT-ID or agent asks.
- rsil-agent: MINIMAL — PT is optional context for both rsil-global and rsil-review.
- Coordinator skills: ZERO impact — they don't use fork, PT access unchanged.

**Decision point:** Phase A pre-deploy validation determines which path to take. The delta is small enough to implement within Phase 6 fix-loop if needed.

### Pre-Deploy Validation Sequence (A → B → C → D)

**Phase A: Structural + Infrastructure Validation**

| Step | Test | Pass Criterion | Failure Response |
|------|------|----------------|-----------------|
| A1 | V6a automated checks (§7 V1-V5) | Zero failures across 20 files | Fix files → re-run A1 |
| A2 | Custom agent resolution | Create minimal fork skill with `agent: "pt-manager"`, invoke → agent .md loads correctly | RISK-1 fallback: `agent: general-purpose` with inline instructions |
| A3 | Task list scope | Fork agent calls TaskList → sees [PERMANENT] task | RISK-8 delta: switch to $ARGUMENTS PT-ID passing |
| A4 | Fork spawn mechanism | `context: fork` in frontmatter → CC creates fork correctly | Critical failure — investigate CC platform behavior |

**Phase B: rsil-global Functional Test (lowest risk)**

| Step | Test | Pass Criterion | Failure Response |
|------|------|----------------|-----------------|
| B1 | Invoke `/rsil-global` | Fork loads rsil-agent.md, Dynamic Context renders, skill executes | Fix rsil-global SKILL.md or rsil-agent.md → re-run B |
| B2 | PT interaction (if applicable) | rsil-agent can read PT via TaskGet | If fails AND A3 passed: investigate agent-specific issue |

**Phase C: rsil-review + permanent-tasks Functional Test (medium risk)**

| Step | Test | Pass Criterion | Failure Response |
|------|------|----------------|-----------------|
| C1 | Invoke `/permanent-tasks "test"` | pt-manager creates/updates PT via Task API | Fix pt-manager.md or permanent-tasks SKILL.md → re-run C1 |
| C2 | Invoke `/rsil-review` (narrow scope) | rsil-agent spawns research agents via Task tool (OQ-1 validation) | If spawning fails: rsil-review falls back to sequential in-agent execution |

**Shared file awareness rule:** If Phase C fix modifies `rsil-agent.md` → **re-run Phase B** (rsil-global uses same agent). delivery-agent.md and pt-manager.md are NOT shared — Phase D fixes never regress B or C.

**Phase D: delivery-pipeline Functional Test (highest risk)**

| Step | Test | Pass Criterion | Failure Response |
|------|------|----------------|-----------------|
| D1 | Invoke `/delivery-pipeline` (mock) | delivery-agent loads, Dynamic Context renders, Phase 0 PT check works | Fix delivery-pipeline SKILL.md or delivery-agent.md → re-run D |
| D2 | User gate interaction | AskUserQuestion works in fork context | If fails: delivery falls back to Lead-in-context |

**Note:** Full delivery validation requires pipeline artifacts (gate records, L1/L2, etc.). Phase D is a PARTIAL test — validates fork mechanism, not full delivery workflow. Full validation occurs in first real pipeline run post-commit.

---

## 9. Commit Strategy

### Approach: Big Bang Atomic Commit (D-8)

All 22+ files committed in a single atomic `git commit`. No per-file or per-wave commits.

### Pre-Commit Gate

Before staging: ALL of the following must pass:
1. V6a automated checks (§7 V1-V5, V6a) — ZERO failures
2. Pre-deploy validation A → B → C → D — ALL phases pass
3. No uncommitted work-in-progress files outside the 22+ target set

### Staging Command

```bash
git add \
  .claude/CLAUDE.md \
  .claude/references/agent-common-protocol.md \
  .claude/agents/pt-manager.md \
  .claude/agents/delivery-agent.md \
  .claude/agents/rsil-agent.md \
  .claude/agents/research-coordinator.md \
  .claude/agents/verification-coordinator.md \
  .claude/agents/architecture-coordinator.md \
  .claude/agents/planning-coordinator.md \
  .claude/agents/validation-coordinator.md \
  .claude/agents/execution-coordinator.md \
  .claude/agents/testing-coordinator.md \
  .claude/agents/infra-quality-coordinator.md \
  .claude/skills/brainstorming-pipeline/SKILL.md \
  .claude/skills/agent-teams-write-plan/SKILL.md \
  .claude/skills/plan-validation-pipeline/SKILL.md \
  .claude/skills/agent-teams-execution-plan/SKILL.md \
  .claude/skills/verification-pipeline/SKILL.md \
  .claude/skills/delivery-pipeline/SKILL.md \
  .claude/skills/rsil-global/SKILL.md \
  .claude/skills/rsil-review/SKILL.md \
  .claude/skills/permanent-tasks/SKILL.md
```

**22 files total.** Explicit file list — no `git add .` or `git add -A` (safety protocol).

### Commit Message Template

```
feat(infra): skill optimization v9.0 — fork agents, PT-centric interface, coordinator convergence

Redesign 9 skills with 2 template variants (coordinator-based + fork-based):
- 3 NEW fork agent .md files (pt-manager, delivery-agent, rsil-agent)
- PT-centric interface: PT = sole cross-phase source of truth (GC 14→3)
- 8 coordinator .md converged to Template B (768→402L, -48%)
- CLAUDE.md §10 fork agent exception (3-layer enforcement)
- agent-common-protocol.md §Task API fork exception clause
- L2 Downstream Handoff replaces GC Phase N Entry Requirements
- All 9 skills gain new Interface Section (C-1~C-5 contracts)

Architecture: .agent/teams/skill-opt-v9/phase-3/ (149 evidence, 30 decisions)
Design: .agent/teams/skill-opt-v9/phase-4/ (10-section plan)

Files: 9 SKILL.md + 8 coordinator .md + 3 NEW agent .md + CLAUDE.md + protocol = 22

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Post-Commit

After successful commit:
1. Run `/rsil-global` — lightweight INFRA health assessment on the committed changes
2. Verify `git log --oneline -1` shows expected commit message
3. `git diff HEAD~1 --stat` to confirm exactly 22 files changed

---

## 10. Rollback & Recovery

### Two Rollback Domains

The Big Bang commit creates two distinct recovery domains with different mechanisms.

### Domain 1: Pre-Commit Rollback (during validation Waves 3-4)

Files are written to disk but NOT yet committed. Recovery is straightforward because no git history to manage.

**Escalation ladder (try in order):**

| Level | When | Action | Impact |
|-------|------|--------|--------|
| L1: Fix-and-retry | Specific file(s) fail validation | Edit the failing file(s), re-run failed validation step | Minimal — only touches failing files |
| L2: Selective checkout | Fix requires starting over for specific files | `git checkout -- .claude/agents/rsil-agent.md .claude/skills/rsil-global/SKILL.md` | Moderate — reverts specific files to pre-implementation state |
| L3: Full checkout | Fundamental architecture failure (Phase A reveals fork mechanism broken) | `git checkout -- .claude/` | Maximum — reverts ALL changes, triggers architecture fallback |

**Phase A failure is qualitatively different:**
If Phase A reveals that custom agent resolution, task list scope, or fork mechanism doesn't work, the response is NOT a file fix — it's an architecture-level fallback:
- RISK-1 fallback: Use `agent: general-purpose` with inline agent instructions in skill body. 3 agent .md files become unused, skill bodies grow ~30-50L each.
- RISK-8 fallback: Apply RISK-8 Fallback Delta (§8) — ~50 lines across 8 files.
- Both fallbacks are implementable within the same pipeline session (fix-loop).

**Shared file awareness rule:**
`rsil-agent.md` is shared between Phase B (rsil-global) and Phase C (rsil-review). If a Phase C fix modifies rsil-agent.md → **must re-run Phase B**. Other agent files (delivery-agent.md, pt-manager.md) are NOT shared — their fixes don't regress earlier validation phases.

### Domain 2: Post-Commit Rollback

After `git commit`, recovery uses standard git mechanisms.

**Primary: `git revert HEAD`**
- Creates a new commit that undoes all 22 file changes
- Atomic — reverts everything in one operation
- No external state to unwind (no database, no API keys, no deployed services)
- Safe to execute at any time after commit

**When to use:**
- Post-commit smoke test (`/rsil-global`) reveals critical INFRA breakage
- First real pipeline run reveals fundamental skill execution failure
- User discovers unintended behavioral change in any skill

**Partial failure handling:**
If 20 of 22 files are correct but 2 have issues:
- Do NOT `git revert HEAD` (that loses 20 correct files)
- Instead: fix the 2 files → create a NEW commit (fix commit, not amend)
- Only use full revert if the issues are systemic (cross-cutting contract violation)

### Fork-Back-to-Lead-Context Contingency

If RISK-8 triggers (fork agents can't access task list) and the RISK-8 Fallback Delta is insufficient:

**Per-skill fork-back procedure:**

| Skill | Fork-Back Action | Impact |
|-------|-----------------|--------|
| permanent-tasks | Remove `context: fork` + `agent:` from frontmatter. Skill body returns to Lead-in-context execution. pt-manager.md becomes unused. | LOW — permanent-tasks worked in Lead-in-context before |
| rsil-global | Same — remove fork frontmatter. rsil-agent.md becomes unused for this skill. | LOW — rsil-global worked in Lead-in-context before |
| rsil-review | Same — remove fork frontmatter. | LOW — rsil-review worked in Lead-in-context before |
| delivery-pipeline | Same — remove fork frontmatter. delivery-agent.md becomes unused. | LOW — delivery-pipeline worked in Lead-in-context before |

**Key insight:** Fork-back is always safe because all 4 skills worked in Lead-in-context mode before this optimization. The fork architecture is an IMPROVEMENT, not a prerequisite. Reverting to Lead-in-context restores previous behavior with zero functional loss.

**Fork-back is a NEW commit** (not a revert):
- Remove fork frontmatter fields from affected SKILL.md files
- Keep all other changes (coordinator convergence, Interface Sections, PT-centric interface, §10 modification)
- The 3 fork agent .md files become unused but harmless — remove in a follow-up cleanup commit

### Recovery Decision Tree

```
Post-commit issue detected
    │
    ├─ Systemic (affects all skills)?
    │   └─ YES → git revert HEAD → investigate → re-plan
    │
    ├─ Isolated to specific files?
    │   └─ YES → fix files → new commit
    │
    ├─ Fork-specific (only fork skills broken)?
    │   └─ YES → fork-back-to-Lead-context → new commit
    │        (keeps coordinator convergence + PT-centric interface)
    │
    └─ Uncertain scope?
        └─ Run /rsil-global for systematic assessment → decide based on findings
```

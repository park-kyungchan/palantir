# Superpowers Plugin v4.2.0 — Agent Teams Compatibility Analysis

> **Date:** 2026-02-07
> **Author:** Lead (Opus 4.6)
> **Status:** RESEARCH COMPLETE — Pending design phase
> **Scope:** 14 skills, 1 agent, all supporting files analyzed
> **Plugin:** [obra/superpowers](https://github.com/obra/superpowers) v4.2.0
> **Target:** Agent Teams Infrastructure v3.0 (DIA Enforcement + LDAP)

---

## 1. Executive Summary

Superpowers plugin was designed for **single-agent** Claude Code sessions. Agent Teams operates
as a **multi-agent persistent pipeline** with DIA protocol, phase gates, and file ownership rules.

**14 skills analyzed → 5 compatibility categories:**

| Category | Count | Skills | Action |
|----------|-------|--------|--------|
| INCOMPATIBLE | 3 | executing-plans, subagent-driven-development, writing-plans | Redesign or replace |
| CONFLICTS | 3 | using-git-worktrees, finishing-a-development-branch, using-superpowers | Significant adaptation |
| OVERLAPS | 1 | brainstorming | Role mapping needed |
| ADAPTABLE | 2 | requesting-code-review, dispatching-parallel-agents | Minor adaptation |
| COMPATIBLE | 5 | test-driven-development, systematic-debugging, receiving-code-review, verification-before-completion, writing-skills | Usable as-is or minimal change |

**Key Finding:** The 3 INCOMPATIBLE skills form the **core workflow chain**
(writing-plans → executing-plans / subagent-driven-development). Breaking this chain
requires designing an Agent Teams-native workflow replacement.

---

## 2. Plugin Inventory

### 2.1 Skills (14)

| # | Skill | Lines | Supporting Files | Invocation Type |
|---|-------|-------|------------------|-----------------|
| 1 | brainstorming | 55 | — | User-triggered |
| 2 | dispatching-parallel-agents | 181 | — | Situational |
| 3 | executing-plans | 85 | — | Plan handoff |
| 4 | finishing-a-development-branch | 201 | — | End-of-work |
| 5 | receiving-code-review | 214 | — | Reactive |
| 6 | requesting-code-review | 106 | code-reviewer.md (147 lines) | Post-implementation |
| 7 | subagent-driven-development | 243 | implementer-prompt.md, spec-reviewer-prompt.md, code-quality-reviewer-prompt.md | Plan execution |
| 8 | systematic-debugging | 297 | root-cause-tracing.md, defense-in-depth.md, condition-based-waiting.md, tests, scripts | Bug investigation |
| 9 | test-driven-development | 372 | testing-anti-patterns.md | Implementation discipline |
| 10 | using-git-worktrees | 219 | — | Workspace setup |
| 11 | using-superpowers | 88 | — | Meta (skill router) |
| 12 | verification-before-completion | 140 | — | Quality gate |
| 13 | writing-plans | 117 | — | Plan creation |
| 14 | writing-skills | 656 | anthropic-best-practices.md, testing-skills-with-subagents.md, graphviz-conventions.dot, render-graphs.js, persuasion-principles.md, examples/ | Meta (skill creation) |

### 2.2 Agents (1)

| Agent | Description | Model |
|-------|-------------|-------|
| code-reviewer | Senior code reviewer for plan alignment + quality | inherit |

---

## 3. Detailed Compatibility Analysis

### 3.1 INCOMPATIBLE Skills (Action: Redesign/Replace)

#### G-01: executing-plans

**Superpowers Design:**
- Single agent reads plan, creates TodoWrite, executes batches of 3
- Human reviews between batches
- References worktree setup
- Linear execution model

**Agent Teams Conflicts:**
| Aspect | Superpowers | Agent Teams | Conflict |
|--------|-------------|-------------|----------|
| Task tracking | TodoWrite | TaskCreate/TaskList (Lead-only write) | API mismatch |
| Execution model | Single agent, batched | Multi-teammate, phase-gated | Architecture |
| Review | Human between batches | Lead DIA protocol + gate | Process |
| Context | Self-contained agent | CIP injection + global-context.md | Protocol |
| Workspace | Git worktree | Shared workspace + file ownership | Workspace model |
| Verification | Human checkpoint | Phase 7 (tester) + Phase 6.V | Quality model |
| Handoff | N/A | L1/L2/L3 files | Missing |

**Assessment:** Fundamental architecture mismatch. Cannot be adapted — must be redesigned
as Agent Teams-native workflow or deprecated in favor of CLAUDE.md pipeline instructions.

#### G-02: subagent-driven-development

**Superpowers Design:**
- Controller dispatches ephemeral subagent per task (via Task tool)
- Two-stage review: spec compliance → code quality
- Fresh subagent = no context pollution
- Uses TodoWrite for tracking

**Agent Teams Conflicts:**
| Aspect | Superpowers | Agent Teams | Conflict |
|--------|-------------|-------------|----------|
| Agent lifecycle | Ephemeral (per task) | Persistent (tmux, per phase) | Lifecycle |
| Agent dispatch | Task tool (general-purpose) | Task tool with team_name | Dispatch method |
| Context | Controller provides full text | Lead injects global-context + task-context | Context model |
| Review | Ephemeral reviewer subagents | Lead DIA + code-reviewer agent | Review model |
| Task tracking | TodoWrite | TaskCreate (Lead-only) | API mismatch |
| Communication | Return value | SendMessage (async) | Communication |
| Pre-work protocol | None | [IMPACT-ANALYSIS] + [CHALLENGE] (LDAP) | Missing DIA |

**Assessment:** The ephemeral subagent pattern conflicts with Agent Teams' persistent teammate
model. The two-stage review (spec + quality) is conceptually valuable but must be integrated
into the Agent Teams pipeline (potentially as Phase 6.R review within Phase 6, or as
code-reviewer agent subprocess within Lead gate evaluation).

#### G-03: writing-plans

**Superpowers Design:**
- Creates plan with TodoWrite task structure
- Task granularity: 2-5 minute steps (write test, run test, implement, commit)
- Header references executing-plans / subagent-driven-development for execution
- Plan format: per-engineer steps with exact commands

**Agent Teams Conflicts:**
| Aspect | Superpowers | Agent Teams | Conflict |
|--------|-------------|-------------|----------|
| Plan consumer | Single engineer | Lead → multi-teammate pipeline | Audience |
| Task granularity | 2-5 min steps | Phase-level tasks (hours) | Granularity |
| Task format | TodoWrite entries | TaskCreate definitions (subject, description, activeForm) | Format |
| Execution handoff | "Use executing-plans" | Lead reads plan → orchestrates pipeline | Handoff |
| Context | Plan file only | global-context.md + task-context.md per teammate | Context model |
| File ownership | Not specified | Lead assigns non-overlapping file sets | Missing |
| DIA integration | None | [INJECTION], [IMPACT-ANALYSIS], [CHALLENGE] | Missing |
| Gate criteria | Not specified | Phase gate checklist | Missing |

**Assessment:** writing-plans output format is incompatible with Agent Teams input requirements.
The plan structure needs an additional "Agent Teams Execution Plan" template alongside (or
replacing) the current single-engineer template. We already demonstrated this adaptation
in the CH-001 LDAP implementation plan (757 lines, 10 sections).

---

### 3.2 CONFLICTS Skills (Action: Significant Adaptation)

#### G-04: using-git-worktrees

**Superpowers Design:**
- Creates isolated worktrees per feature branch
- Directory selection: .worktrees/ → CLAUDE.md → ask user
- Safety: verify .gitignore, clean baseline tests
- Used by: brainstorming, subagent-driven-development, executing-plans

**Agent Teams Conflict:**
- Agent Teams operates in **shared workspace** (`/home/palantir`)
- File isolation via **ownership rules** (Lead assigns, no concurrent editing)
- Worktree isolation is unnecessary and creates coordination overhead
- Teammates cannot independently create worktrees (no permission)
- Phase 9 (Delivery) handles branch management

**Adaptation Options:**
1. **DISABLE for Agent Teams:** using-git-worktrees is irrelevant when Agent Teams is active.
   Skills that reference it (executing-plans, subagent-driven-development) are already INCOMPATIBLE.
2. **PRESERVE for solo mode:** When not in Agent Teams mode, worktrees remain useful.
3. **CONDITIONAL:** Add a check — if Agent Teams detected (team config exists), skip worktree setup.

#### G-05: finishing-a-development-branch

**Superpowers Design:**
- Verify tests → present 4 options (merge, PR, keep, discard) → cleanup worktree
- Called by: executing-plans, subagent-driven-development

**Agent Teams Conflict:**
- Phase 9 (Delivery) is Lead-only — handles commit, PR, cleanup
- Test verification is Phase 7 (tester teammate)
- Worktree cleanup is irrelevant (shared workspace)
- "Present options to human" conflicts with Lead-driven pipeline

**Adaptation Options:**
1. **MAP to Phase 9:** Lead invokes finishing-a-development-branch in Phase 9 after all gates pass.
   Remove worktree cleanup steps. Keep test verification + 4 options as user-facing delivery.
2. **PRESERVE for solo mode:** Useful outside Agent Teams.

#### G-06: using-superpowers (Meta Skill Router)

**Superpowers Design:**
- "Invoke skill BEFORE any response" — 1% chance mandate
- Skill check → announce → follow skill exactly
- Uses TodoWrite for checklists
- Priority: process skills first, implementation skills second

**Agent Teams Conflict:**
- DIA protocol (CIP + DIAVP + LDAP) must execute BEFORE any skill invocation
- Teammates receive [DIRECTIVE] with [INJECTION] — skill invocation is NOT the first action
- "1% chance" broad check conflicts with structured pipeline phases
- Skill triggers are user-message-driven; Agent Teams is directive-driven
- TodoWrite usage incompatible (Lead-only TaskCreate)

**Adaptation Options:**
1. **SCOPE RESTRICTION:** using-superpowers applies to **Lead in Phase 1 (Discovery)** and
   **user-facing solo sessions** only. Teammates follow DIA protocol first, then may reference
   applicable development practice skills (TDD, debugging) during execution.
2. **PRIORITY OVERRIDE:** In Agent Teams mode, DIA protocol takes priority over skill invocation.
   Skill router becomes secondary guidance, not primary mandate.

---

### 3.3 OVERLAPS (Action: Role Mapping)

#### G-07: brainstorming

**Superpowers Design:**
- Collaborative design exploration with user
- One question at a time, multiple choice
- Output: design document in docs/plans/
- Leads to: worktree setup → writing-plans → execution

**Agent Teams Overlap:**
- Phase 1 (Discovery): Lead explores problem with user
- Phase 2 (Research): researcher teammates investigate
- Phase 3 (Architecture): architect designs solution

**Adaptation:**
- brainstorming maps to **Phase 1** (Lead ↔ User interaction)
- Lead CAN use brainstorming principles during Phase 1
- The design output format is compatible (docs/plans/ YAML/MD)
- Post-brainstorming chain (worktree → writing-plans → execution) must be replaced with
  Agent Teams pipeline (research → architecture → design → validate → implement)

---

### 3.4 ADAPTABLE Skills (Action: Minor Adaptation)

#### G-08: requesting-code-review

**Superpowers Design:**
- Dispatch code-reviewer subagent (via Task tool)
- Provide git SHAs, plan reference, description
- Act on Critical/Important/Minor feedback

**Agent Teams Adaptation:**
- code-reviewer agent (superpowers:code-reviewer) is already registered as an agent type
- Lead can dispatch as sub-orchestration during Phase 6 gate evaluation
- OR implementer can dispatch as subagent (Sub-Orchestrator capability)
- Template (code-reviewer.md) is reusable without modification
- Only change: context injection (add global-context reference to review prompt)

#### G-09: dispatching-parallel-agents

**Superpowers Design:**
- Task tool for 2+ independent problems
- One agent per problem domain
- Review + integrate results

**Agent Teams Adaptation:**
- Agent Teams supports parallel teammates (up to 4 implementers)
- dispatching-parallel-agents principles align with Agent Teams' sub-orchestrator pattern
- Teammates can use Task tool for parallel subagents within their scope
- Only change: parallel agent results must go through DIA review (Lead gate)

---

### 3.5 COMPATIBLE Skills (Action: Usable As-Is or Minimal Change)

#### G-10: test-driven-development

**Assessment:** Role-agnostic TDD discipline. Implementer and tester teammates can follow
TDD cycle (RED-GREEN-REFACTOR) during their execution phases. No Agent Teams conflicts.

**Applicable to:** implementer (Phase 6), tester (Phase 7)

#### G-11: systematic-debugging

**Assessment:** Role-agnostic debugging process. Tester teammates use during Phase 7.
Implementer can use during Phase 6 when encountering test failures.

**Applicable to:** implementer (Phase 6), tester (Phase 7)

#### G-12: receiving-code-review

**Assessment:** Process for handling review feedback. Implementer can follow when receiving
Lead review feedback or code-reviewer agent output. Compatible with Agent Teams'
[REJECTED] → revise → resubmit cycle.

**Applicable to:** implementer (Phase 6), integrator (Phase 8)

#### G-13: verification-before-completion

**Assessment:** "Evidence before claims" discipline. Directly supports Agent Teams'
[IMPACT_VERIFIED] and gate evaluation. Teammates should verify before reporting
[STATUS] COMPLETE. Lead should verify before gate APPROVE.

**Applicable to:** All roles

#### G-14: writing-skills

**Assessment:** Meta-skill for creating new skills. TDD-based skill creation process.
Compatible with Agent Teams — not workflow-dependent.

**Applicable to:** Lead (when creating/modifying skills)

---

## 4. Cross-Cutting Concerns

### 4.1 TodoWrite vs TaskCreate

**5 skills reference TodoWrite:**
- using-superpowers (line 33: "Create TodoWrite todo per item")
- executing-plans (implicit: "Create TodoWrite")
- subagent-driven-development (line 98: "Create TodoWrite")
- writing-plans (indirect, via execution handoff)
- writing-skills (line 598: "Use TodoWrite to create todos")

**Agent Teams replacement:** TaskCreate (Lead-only) + TaskList/TaskGet (all read)

**Impact:** Any skill that instructs "Create TodoWrite" will fail for teammates
(disallowedTools). Must be rewritten to "Lead creates TaskCreate entries" or
"Report task items to Lead for TaskCreate".

### 4.2 Ephemeral vs Persistent Agents

**3 skills use ephemeral Task tool subagents:**
- subagent-driven-development (implementer, spec-reviewer, code-quality-reviewer)
- requesting-code-review (code-reviewer)
- dispatching-parallel-agents (multiple)

**Agent Teams model:** Persistent tmux teammates with DIA protocol.

**Hybrid allowed:** Teammates CAN spawn ephemeral subagents via Task tool (Sub-Orchestrator).
This means requesting-code-review and dispatching-parallel-agents can work within Agent Teams
as teammate-level sub-orchestration. Only subagent-driven-development's full pipeline is incompatible.

### 4.3 Workflow Chain Dependencies

```
brainstorming
    └→ using-git-worktrees [REQUIRED]
        └→ writing-plans
            ├→ executing-plans [REQUIRED]
            │   └→ finishing-a-development-branch [REQUIRED]
            └→ subagent-driven-development [REQUIRED]
                ├→ requesting-code-review
                └→ finishing-a-development-branch [REQUIRED]
```

**Breaking the chain:** If writing-plans output format changes for Agent Teams,
the entire downstream chain (executing-plans, subagent-driven-development,
finishing-a-development-branch) must be adapted or replaced.

### 4.4 "your human partner" References

Multiple skills reference "your human partner" as the authority figure:
- receiving-code-review: "Conflicts with your human partner's prior decisions"
- systematic-debugging: "your human partner's Signals"
- test-driven-development: "Ask your human partner"
- writing-skills: "your human partner's rule"

**Agent Teams mapping:** In Agent Teams, "your human partner" maps to:
- For Lead: the actual human user
- For Teammates: the Lead (pipeline controller)
- Skill text needs no change — the role mapping is conceptual

### 4.5 Skill-to-Agent-Type Mapping

| Skill | Lead | researcher | architect | implementer | tester | integrator | devils-advocate |
|-------|------|-----------|-----------|-------------|--------|------------|-----------------|
| brainstorming | Phase 1 | — | — | — | — | — | — |
| test-driven-development | — | — | — | Primary | Primary | — | — |
| systematic-debugging | — | — | — | When needed | Primary | — | — |
| verification-before-completion | Gate eval | — | — | Pre-report | Pre-report | Pre-report | — |
| receiving-code-review | — | — | — | On rejection | — | On rejection | — |
| requesting-code-review | Gate eval | — | — | Sub-orch | — | Sub-orch | — |
| dispatching-parallel-agents | — | Sub-orch | — | Sub-orch | — | — | — |
| writing-skills | When needed | — | — | — | — | — | — |
| writing-plans | Phase 1 | — | — | — | — | — | — |
| executing-plans | INCOMPATIBLE | — | — | — | — | — | — |
| subagent-driven-dev | INCOMPATIBLE | — | — | — | — | — | — |
| using-git-worktrees | CONFLICTS | — | — | — | — | — | — |
| finishing-a-dev-branch | Phase 9 | — | — | — | — | — | — |
| using-superpowers | Phase 1 only | — | — | — | — | — | — |

---

## 5. Recommendation Summary

### 5.1 Priority Actions

| Priority | Action | Scope | Effort |
|----------|--------|-------|--------|
| P1-HIGH | Design Agent Teams-native plan format template | writing-plans | Medium |
| P1-HIGH | Design Agent Teams-native execution workflow | Replace executing-plans + subagent-driven-dev | High |
| P2-MED | Add Agent Teams conditional to using-superpowers | using-superpowers | Low |
| P2-MED | Add Agent Teams mode check to using-git-worktrees | using-git-worktrees | Low |
| P2-MED | Map finishing-a-development-branch to Phase 9 | finishing-a-development-branch | Low |
| P3-LOW | Document skill-to-agent-type mapping | New reference doc | Medium |
| P3-LOW | Add TodoWrite → TaskCreate migration notes | All affected skills | Low |

### 5.2 Approach Options

**Option A: Fork and Adapt (RECOMMENDED)**
- Fork superpowers plugin locally
- Add Agent Teams-specific sections to applicable skills
- Add conditional logic ("If in Agent Teams mode, do X instead of Y")
- Preserve solo-mode compatibility
- Estimated scope: 5-7 skill modifications

**Option B: Agent Teams Overlay**
- Keep superpowers plugin unchanged
- Create Agent Teams-specific wrapper skills in `.claude/skills/`
- Wrappers reference superpowers skills for compatible portions
- Override incompatible portions with Agent Teams-native logic
- Estimated scope: 3-4 new wrapper skills

**Option C: Replace Workflow Chain Only**
- Replace only the INCOMPATIBLE workflow chain (writing-plans → executing-plans → finishing)
- Keep all other skills unchanged
- Write Agent Teams-native equivalents in `.claude/skills/` or `.claude/references/`
- Estimated scope: 2-3 new files

### 5.3 Risk Assessment

| Risk | Severity | Mitigation |
|------|----------|------------|
| Plugin updates override local changes | HIGH | Option A: use fork. Option B/C: overlay unaffected. |
| Skill invocation confusion (which version?) | MEDIUM | Clear naming: `superpowers:X` (original) vs custom |
| Solo mode regression | LOW | Conditional checks preserve solo-mode behavior |
| DIA protocol bypass via skill invocation | HIGH | using-superpowers priority override in Agent Teams |

---

## 6. Detailed Gap Specifications

### G-01 through G-14 gap IDs are referenced throughout this document.

**Summary table:**

| Gap | Skill | Category | Root Cause |
|-----|-------|----------|------------|
| G-01 | executing-plans | INCOMPATIBLE | Single-agent batch model vs multi-agent pipeline |
| G-02 | subagent-driven-development | INCOMPATIBLE | Ephemeral subagent vs persistent teammate |
| G-03 | writing-plans | INCOMPATIBLE | Plan format targets single engineer |
| G-04 | using-git-worktrees | CONFLICTS | Worktree isolation vs shared workspace |
| G-05 | finishing-a-development-branch | CONFLICTS | Worktree cleanup + options vs Phase 9 |
| G-06 | using-superpowers | CONFLICTS | "1% mandate" vs DIA protocol priority |
| G-07 | brainstorming | OVERLAPS | Maps to Phase 1 with chain dependency |
| G-08 | requesting-code-review | ADAPTABLE | Sub-orchestration compatible |
| G-09 | dispatching-parallel-agents | ADAPTABLE | Parallel pattern compatible |
| G-10 | test-driven-development | COMPATIBLE | Role-agnostic discipline |
| G-11 | systematic-debugging | COMPATIBLE | Role-agnostic process |
| G-12 | receiving-code-review | COMPATIBLE | Feedback handling process |
| G-13 | verification-before-completion | COMPATIBLE | Evidence-before-claims discipline |
| G-14 | writing-skills | COMPATIBLE | Meta-skill, not workflow-dependent |

---

## 7. Next Steps

1. **User decision:** Choose approach (Option A / B / C) from §5.2
2. **Design phase:** Create detailed design document for chosen approach
3. **CH-001 dependency:** This work can proceed independently of CH-001 LDAP implementation
4. **Implementation:** Follow Agent Teams pipeline (Phase 2 → 6) for actual changes

---

## Appendix A: Plugin File Inventory

```
superpowers/4.2.0/
├── .claude-plugin/
│   ├── plugin.json (name, version, author, license)
│   └── marketplace.json
├── agents/
│   └── code-reviewer.md (49 lines)
├── skills/
│   ├── brainstorming/SKILL.md (55 lines)
│   ├── dispatching-parallel-agents/SKILL.md (181 lines)
│   ├── executing-plans/SKILL.md (85 lines)
│   ├── finishing-a-development-branch/SKILL.md (201 lines)
│   ├── receiving-code-review/SKILL.md (214 lines)
│   ├── requesting-code-review/
│   │   ├── SKILL.md (106 lines)
│   │   └── code-reviewer.md (147 lines)
│   ├── subagent-driven-development/
│   │   ├── SKILL.md (243 lines)
│   │   ├── implementer-prompt.md (79 lines)
│   │   ├── spec-reviewer-prompt.md (62 lines)
│   │   └── code-quality-reviewer-prompt.md (21 lines)
│   ├── systematic-debugging/
│   │   ├── SKILL.md (297 lines)
│   │   ├── root-cause-tracing.md
│   │   ├── defense-in-depth.md
│   │   ├── condition-based-waiting.md
│   │   ├── condition-based-waiting-example.ts
│   │   ├── find-polluter.sh
│   │   ├── CREATION-LOG.md
│   │   └── test-*.md (3 test files)
│   ├── test-driven-development/
│   │   ├── SKILL.md (372 lines)
│   │   └── testing-anti-patterns.md
│   ├── using-git-worktrees/SKILL.md (219 lines)
│   ├── using-superpowers/SKILL.md (88 lines)
│   ├── verification-before-completion/SKILL.md (140 lines)
│   ├── writing-plans/SKILL.md (117 lines)
│   └── writing-skills/
│       ├── SKILL.md (656 lines)
│       ├── anthropic-best-practices.md
│       ├── testing-skills-with-subagents.md
│       ├── graphviz-conventions.dot
│       ├── render-graphs.js
│       ├── persuasion-principles.md
│       └── examples/CLAUDE_MD_TESTING.md
├── commands/
├── docs/
├── hooks/
├── lib/
└── tests/
```

## Appendix B: CH-001 Plan as Agent Teams Format Precedent

The restructured CH-001 LDAP implementation plan (`docs/plans/2026-02-07-ch001-ldap-implementation.md`)
serves as the first example of an Agent Teams-native plan format. Key sections that would
become the template for a `writing-plans` Agent Teams adaptation:

1. Orchestration Overview (Lead instructions, pipeline structure, execution sequence)
2. global-context.md template
3. File Ownership Assignment
4. TaskCreate Definitions (subject, description, activeForm, blockedBy, blocks)
5. Edit Specifications (per-task detailed content)
6. Validation Checklist
7. Commit Strategy
8. Gate Criteria

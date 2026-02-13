# L2 Summary — Risk Architecture: Fork Agent Designs & Risk Register

## Summary

Designed 3 fork agent .md files (pt-manager, delivery-agent, rsil-agent) with complete frontmatter, tool justification, and NL constraints. **ADR-S8 applied:** all agent .md bodies include inline Error Handling, Key Principles, and Never sections — fork agents are self-contained without relying on external references for operational constraints. Produced a 9-item risk register with severity × likelihood scoring, mitigation strategies, and cascade analysis. Resolved 3 open questions: fork agent spawning (YES, 85% confidence), template variant count (2, not 3), GC elimination timeline (remove in v9.0). Recommended phased validation sequence (A→D) within the Big Bang deployment constraint. RISK-4 (skills preload) verdict: DEFER.

## Fork Agent Designs

### pt-manager (permanent-tasks fork)

| Aspect | Value |
|--------|-------|
| Tools granted | TaskList, TaskGet, **TaskCreate**, **TaskUpdate**, AskUserQuestion, Read, Glob, Grep, Write |
| Task API | Full (D-10 exception — ONLY agent with TaskCreate) |
| maxTurns | 30 |
| Key design | No conversation history → 3-layer mitigation: pipeline=full, manual-rich=partial, manual-sparse=interactive |
| Risk mitigation | AskUserQuestion probes for missing context; Dynamic Context supplements |
| ADR-S8 inline | Error Handling (7 cases), Key Principles (5), Never list (7 prohibitions) |

### delivery-agent (delivery-pipeline fork)

| Aspect | Value |
|--------|-------|
| Tools granted | TaskList, TaskGet, **TaskUpdate**, AskUserQuestion, **Bash**, Edit, Write, Read, Glob, Grep |
| Task API | Update only (no TaskCreate) |
| maxTurns | 50 |
| Key design | No nested /permanent-tasks invocation — abort if no PT found |
| Risk mitigation | Idempotent operations, user gates for all external actions, recovery via re-run |
| ADR-S8 inline | Error Handling (9 cases), Key Principles (7), Never list (10 prohibitions) |

### rsil-agent (shared rsil-global + rsil-review fork)

| Aspect | Value |
|--------|-------|
| Tools granted | TaskList, TaskGet, **TaskUpdate**, **Task** (agent spawning), AskUserQuestion, Edit, Write, Read, Glob, Grep |
| Task API | Update only |
| maxTurns | 50 |
| Key design | Shared agent for 2 skills — agent .md defines ceiling, skill body constrains behavior |
| Verdict rationale | 80%+ tool overlap, NL constrains Task tool usage per skill |
| Trade-off | rsil-global gets Task tool it rarely needs (~5% Tier 3 runs) — acceptable per implementer pattern |
| ADR-S8 inline | Error Handling (10 cases), Key Principles (7), Never list (9 prohibitions) |

## Risk Register

| ID | Risk | Severity | Likelihood | Mitigation | Cascade |
|----|------|----------|------------|------------|---------|
| RISK-1 | Custom agent resolution failure | HIGH | LOW | Pre-deploy validation test + fallback (agent: general-purpose) | Blocks D-11; D-9 survives with fallback |
| RISK-2 | PT fork loses conversation history | MED-HIGH | CERTAIN | 3-layer: pipeline=full, manual-rich=partial, manual-sparse=interactive | Affects permanent-tasks only |
| RISK-3 | Delivery fork complexity | MEDIUM | HIGH | Eliminate nested skills, idempotent ops, phased validation (fork last) | Fallback to Lead-in-context if fails |
| RISK-4 | Skills preload token cost | LOW | CERTAIN | DEFER — 3,250L cost vs marginal benefit | None |
| RISK-5 | Big Bang 22+ files | HIGH | MEDIUM | Pre-commit YAML validation, atomic commit, smoke test sequence, git revert rollback | Full INFRA if failure |
| RISK-6 | Fork agent crash recovery | MEDIUM | LOW | Idempotent operations, disk state checkpoints, re-run recovery | Isolated per fork |
| RISK-7 | Fork state corruption | MEDIUM | LOW | Atomic Task API, atomic Write, Read-Merge-Write, git checkout rollback | Isolated per fork |
| RISK-8 | Task list scope confusion | MEDIUM | MEDIUM | Pre-deploy validation + fallback (pass PT ID via $ARGUMENTS) | Blocks pt-manager + delivery Phase 0 |
| ~~RISK-9~~ | ~~SendMessage scope~~ | — | — | **ELIMINATED** — SendMessage removed from pt-manager (cross-lens resolution) | — |

## Open Question Verdicts

| # | Question | Verdict | Rationale |
|---|----------|---------|-----------|
| OQ-1 | Can fork agent spawn subagents via Task tool? | **YES (85% confidence)** | Task tool is standard CC tool, frontmatter controls access, one-shot spawns don't need team context. Pre-deploy validation required. Fallback: rsil-review stays Lead-in-context. |
| OQ-2 | Template variant count? | **2 variants** (coordinator + fork) | Delivery complexity is in skill body, not template structure. Same fork template applies. |
| OQ-3 | GC elimination timeline? | **Remove in v9.0** | L2 Downstream Handoff already operational. Big Bang = right time for atomic interface change. GC becomes optional session scratch. |

## Phased Validation Strategy

```
Phase A: VALIDATE         Phase B: LOW RISK        Phase C: MEDIUM RISK      Phase D: HIGH RISK
┌────────────────┐       ┌───────────────┐        ┌──────────────────┐      ┌──────────────────┐
│ 3 agent .md    │       │ rsil-global   │        │ rsil-review      │      │ delivery-pipeline│
│ Test fork+agent│──OK──→│ fork deploy   │──OK───→│ permanent-tasks  │─OK──→│ fork deploy      │
│ Task list scope│       │ (lowest risk) │        │ fork deploy      │      │ (highest risk)   │
│ Agent spawning │       └───────────────┘        └──────────────────┘      └──────────────────┘
└────────────────┘
   FAIL → fallback architecture (agent: general-purpose)
```

Note: This is a TESTING sequence. D-8 Big Bang means all files committed together.

## PT Goal Linkage

| PT Decision | This Work's Contribution | Status |
|-------------|-------------------------|--------|
| D-9 (4 skills → fork) | All 4 fork agents designed with tools, permissions, constraints | DESIGNED |
| D-10 (Task API exception) | pt-manager = only agent with TaskCreate. delivery-agent + rsil-agent = TaskUpdate only | DESIGNED |
| D-11 (3 new agent .md) | Full frontmatter + body for pt-manager, delivery-agent, rsil-agent | DESIGNED |
| D-14 (GC reduction) | GC elimination in v9.0 recommended (OQ-3 resolved) | DECIDED |

## Evidence Sources

| Source | What It Provided |
|--------|------------------|
| Phase 3 phase-context.md | Architecture scope, 6 items, constraints |
| Phase 2 research-coord L2 | 117 evidence points, 4-domain synthesis, Downstream Handoff |
| Phase 2 codebase-researcher-2 L2 | Fork mechanism details, per-skill feasibility, D-10/D-11 design |
| permanent-tasks SKILL.md (279L) | Step 2A conversation dependency, Task API usage patterns |
| delivery-pipeline SKILL.md (471L) | 5+ user gates, git ops, nested skill invocation, multi-session |
| rsil-global SKILL.md (452L) | Tier 1-3 observation, rare agent spawning, lightweight budget |
| rsil-review SKILL.md (549L) | R-1 parallel agent spawning, Edit for FIX items |
| Design doc §9 (CC research) | Fork frontmatter syntax, tool access control, skills preload |
| implementer.md, execution-monitor.md, devils-advocate.md | Existing agent .md patterns (frontmatter, body structure) |
| agent-common-protocol.md | Shared procedures, Task API section, L1/L2/L3 canonical format |
| ontological-lenses.md | IMPACT lens framework (change/ripple analysis) |

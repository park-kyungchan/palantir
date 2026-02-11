# Implementation Plan — Lead Architecture Redesign (Selective Coordinator Model)

**Date:** 2026-02-11
**Phase:** 4 (Detailed Design) — Implementation Plan
**Architecture:** `.agent/teams/lead-arch-redesign/phase-3/architect-1/L3-full/architecture-design.md`
**Detailed Specs:** `.agent/teams/lead-arch-write-plan/phase-4/architect-A/specs-impl-A.md` (Impl-A) + `architect-B/specs-impl-B.md` (Impl-B)
**ADRs:** AD-8 (5 Coordinators), AD-9 (Execution Cross-Category), AD-10 (Two-Level Catalog), AD-11 (Delegated Verification), AD-12 (Three-Mode Design), AD-13 (Coordinator Template)

---

## §1 Orchestration Overview

| Dimension | Value |
|-----------|-------|
| Tasks | 10 (T-1 through T-10) |
| Implementers | 2 (Impl-A: coordinator infrastructure, Impl-B: CLAUDE.md + protocol + skills) |
| Files CREATE | 5 (coordinator .md) |
| Files MODIFY | 28 (catalog, CLAUDE.md, protocol, 4 skills, layer-boundary, 20 agent .md) |
| Files NO_CHANGE | 1 (settings.json — verified) |
| Estimated Delta | +1100 lines across 33 files |
| Critical Path | T-1 → T-2 → T-3 → T-5/T-6/T-7/T-8/T-10 |

**Strategy:** Two independent implementers with non-overlapping file sets. Impl-A owns coordinator CREATE + agent routing infrastructure. Impl-B owns CLAUDE.md + shared protocol + pipeline skill updates.

---

## §2 Dependency Graph

```
T-1 (5 coordinators CREATE) ──── ROOT
  ├── T-2 (catalog restructure)
  │     └── T-3 (CLAUDE.md §6 + §3 + Custom Agents Ref)
  │           ├── T-5 (execution-plan SKILL rewrite)
  │           ├── T-6 (brainstorming-pipeline Phase 2)
  │           ├── T-7 (verification-pipeline Phase 7-8)
  │           ├── T-8 (write-plan + plan-validation notes)
  │           └── T-10 (layer-boundary + settings.json)
  ├── T-4 (agent-common-protocol.md)
  │     └── T-9 (20 agent .md routing)
  ├── T-5 (also blockedBy T-1 directly)
  ├── T-7 (also blockedBy T-1 directly)
  └── T-9 (also blockedBy T-1 directly)

Impl-A chain: T-1 → T-2 → {T-5, T-7, T-9} (parallel within Impl-A after T-1)
Impl-B chain: waits for T-1, T-2 → T-3 → {T-6, T-8, T-10} (parallel within Impl-B after T-3)
Cross-impl: T-4 (Impl-B) blockedBy T-1 (Impl-A). T-9 (Impl-A) blockedBy T-4 (Impl-B).
```

**Execution order:**
1. T-1 (Impl-A) — root, no dependencies
2. T-2 (Impl-A) + T-4 (Impl-B) — parallel after T-1
3. T-3 (Impl-B) — after T-2
4. T-5, T-7 (Impl-A) + T-6, T-8, T-10 (Impl-B) — parallel within each impl
5. T-9 (Impl-A) — after T-4

---

## §3 File Ownership Assignment

### Implementer-A (Coordinator Infrastructure)

| # | File | Action | Task |
|---|------|--------|------|
| 1 | .claude/agents/research-coordinator.md | CREATE | T-1 |
| 2 | .claude/agents/verification-coordinator.md | CREATE | T-1 |
| 3 | .claude/agents/execution-coordinator.md | CREATE | T-1 |
| 4 | .claude/agents/testing-coordinator.md | CREATE | T-1 |
| 5 | .claude/agents/infra-quality-coordinator.md | CREATE | T-1 |
| 6 | .claude/references/agent-catalog.md | MODIFY | T-2 |
| 7 | .claude/skills/agent-teams-execution-plan/SKILL.md | MODIFY | T-5 |
| 8 | .claude/skills/verification-pipeline/SKILL.md | MODIFY | T-7 |
| 9-28 | .claude/agents/{20 worker agents}.md | MODIFY | T-9 |

**Total: 27 files (5 CREATE + 22 MODIFY)**

### Implementer-B (Constitution + Protocol + Skills)

| # | File | Action | Task |
|---|------|--------|------|
| 1 | .claude/CLAUDE.md | MODIFY | T-3 |
| 2 | .claude/references/agent-common-protocol.md | MODIFY | T-4 |
| 3 | .claude/skills/brainstorming-pipeline/SKILL.md | MODIFY | T-6 |
| 4 | .claude/skills/agent-teams-write-plan/SKILL.md | MODIFY | T-8 |
| 5 | .claude/skills/plan-validation-pipeline/SKILL.md | MODIFY | T-8 |
| 6 | .claude/references/layer-boundary-model.md | MODIFY | T-10 |
| 7 | .claude/settings.json | NO_CHANGE | T-10 |

**Total: 6 files MODIFY + 1 NO_CHANGE**

**Overlap verification:** ZERO files shared between implementers.

---

## §4 TaskCreate Definitions

All tasks include AC-0 (plan verification). Full definitions with complete AC lists in L3 specs.

### T-1: Create 5 Coordinator Agent Definitions [Impl-A, ROOT]

- **Files:** 5 CREATE (.claude/agents/{name}-coordinator.md)
- **blockedBy:** none | **blocks:** T-2, T-5, T-7, T-9
- **VL:** HIGH | **ADRs:** AD-8, AD-9, AD-11, AD-12, AD-13
- **AC key:** All 5 files have AD-13 template (7 tools, 4 disallowedTools, 8 standard sections)
- **Full spec:** specs-impl-A.md §5.1-§5.5

### T-2: Restructure agent-catalog.md (Two-Level) [Impl-A]

- **Files:** 1 MODIFY (agent-catalog.md — full restructure)
- **blockedBy:** T-1 | **blocks:** T-3
- **VL:** MED | **ADRs:** AD-10
- **AC key:** Level 1 ≤320L, Level 2 by category, 27-agent matrix, boundary marker comment
- **Full spec:** specs-impl-A.md T-2 §5

### T-3: Rewrite CLAUDE.md §6 + Custom Agents Ref + §3 [Impl-B, CRITICAL]

- **Files:** 1 MODIFY (CLAUDE.md — 3 edits)
- **blockedBy:** T-1, T-2 | **blocks:** T-5, T-6, T-7, T-8
- **VL:** HIGH | **Criticality:** HIGHEST
- **AC key:** 27 Agents table, 3-tier §3 Roles, 6-step routing in §6, Mode 1/3 coordinator management
- **Full spec:** specs-impl-B.md T-3 (T3-S1, T3-S2, T3-S3)

### T-4: Add Coordinator Routing to agent-common-protocol.md [Impl-B]

- **Files:** 1 MODIFY (agent-common-protocol.md — 2 edits)
- **blockedBy:** T-1 | **blocks:** T-9
- **VL:** HIGH
- **AC key:** Routing note overlay, "Working with Coordinators" section with 6 rules
- **Full spec:** specs-impl-B.md T-4 (T4-S1, T4-S2)

### T-5: Rewrite execution-plan SKILL.md §6.3-6.4 [Impl-A]

- **Files:** 1 MODIFY (execution-plan SKILL.md — 7 edits)
- **blockedBy:** T-1 | **blocks:** none
- **VL:** HIGH (§6.3), MED (§6.4+)
- **AC key:** Coordinator spawn + worker pre-spawn, AD-11 delegated verification, review templates stay in SKILL.md
- **Full spec:** specs-impl-A.md T-5 §5.1-§5.7

### T-6: Update brainstorming-pipeline Phase 2 [Impl-B]

- **Files:** 1 MODIFY (brainstorming-pipeline SKILL.md — 4 edits)
- **blockedBy:** T-1, T-3 | **blocks:** none
- **VL:** MED
- **AC key:** Routing decision table (1 researcher → direct, 2+ → coordinator), two paths in §2.3
- **Full spec:** specs-impl-B.md T-6 (T6-S1 through T6-S4)

### T-7: Update verification-pipeline Phase 7-8 [Impl-A]

- **Files:** 1 MODIFY (verification-pipeline SKILL.md — 8 edits)
- **blockedBy:** T-1 | **blocks:** none
- **VL:** MED
- **AC key:** testing-coordinator spawn, worker pre-spawn, coordinator-managed integration
- **Full spec:** specs-impl-A.md T-7 §5.1-§5.8

### T-8: Add Lead-Direct Notes to write-plan + plan-validation [Impl-B]

- **Files:** 2 MODIFY (1 edit each)
- **blockedBy:** T-3 | **blocks:** none
- **VL:** LOW
- **AC key:** Informational notes only, no logic changes
- **Full spec:** specs-impl-B.md T-8 (T8-S1, T8-S2)

### T-9: Update Routing in 20 Agent .md Files [Impl-A]

- **Files:** 20 MODIFY (3 patterns)
- **blockedBy:** T-1 | **blocks:** none
- **VL:** MED
- **AC key:** Pattern A (18 files): "Message your coordinator (or Lead if assigned directly)"; Pattern B (2 files): dual-mode dispatcher; 2 exempt (devils-advocate, execution-monitor); secondary implementer.md change
- **Note:** dynamic-impact-analyst.md has variant text — adapt pattern
- **Full spec:** specs-impl-A.md T-9 §5

### T-10: Layer-Boundary + settings.json [Impl-B]

- **Files:** 1 MODIFY + 1 NO_CHANGE
- **blockedBy:** T-1, T-3 | **blocks:** none
- **VL:** MED (layer-boundary), LOW (settings verification)
- **AC key:** "Coordinator Orchestration (Layer 1)" section validates NL-only approach
- **Full spec:** specs-impl-B.md T-10 (T10-S1, T10-S2)

---

## §5 Change Specifications

Full specs for all 10 tasks with complete old_string/new_string content in L3:
- **Impl-A:** `.agent/teams/lead-arch-write-plan/phase-4/architect-A/specs-impl-A.md` (1901L)
- **Impl-B:** `.agent/teams/lead-arch-write-plan/phase-4/architect-B/specs-impl-B.md` (922L)

### Shared Interface Contract (COORDINATOR REFERENCE TABLE)

| Coordinator | `subagent_type` | Manages | Phase |
|-------------|-----------------|---------|-------|
| research-coordinator | `research-coordinator` | codebase-researcher, external-researcher, auditor | P2 |
| verification-coordinator | `verification-coordinator` | static/relational/behavioral-verifier | P2b |
| execution-coordinator | `execution-coordinator` | implementer, infra-implementer + review dispatch | P6 |
| testing-coordinator | `testing-coordinator` | tester, integrator | P7-8 |
| infra-quality-coordinator | `infra-quality-coordinator` | 4 INFRA analysts | X-cut |

**Shared AD-13 template:** 7 tools (Read/Glob/Grep/Write/TaskList/TaskGet/sequential-thinking), 4 disallowedTools (TaskCreate/TaskUpdate/Edit/Bash), Mode 1 flat coordinator, Mode 3 Lead-direct fallback.

### Spec Summary by Task

| Task | Specs | Total Edits | Key Content |
|------|-------|-------------|-------------|
| T-1 | §5.1-§5.5 | 5 files CREATE | 5 complete coordinator .md files (~170L each) |
| T-2 | §5 | 1 full rewrite | Level 1 ~300L complete + Level 2 reorganization |
| T-3 | T3-S1, T3-S2, T3-S3 | 3 edits | Custom Agents 27 table, §3 3-tier, §6 ~105L rewrite |
| T-4 | T4-S1, T4-S2 | 2 edits | Routing note + Working with Coordinators section |
| T-5 | §5.1-§5.7 | 7 edits | §6.3 coordinator spawn + §6.4 mediated execution |
| T-6 | T6-S1 to T6-S4 | 4 edits | Phase 2 routing + coordinator/direct paths |
| T-7 | §5.1-§5.8 | 8 edits | Phase 7.3 coordinator + Phase 8.1 transition |
| T-8 | T8-S1, T8-S2 | 2 edits | Lead-direct informational notes |
| T-9 | 3 patterns | 21 edits | 18 Pattern A + 2 Pattern B + 1 secondary |
| T-10 | T10-S1, T10-S2 | 1 edit + verify | Layer 1 evidence section + settings.json check |

---

## §6 Interface Contracts

| Interface | Provider | Consumer | Contract |
|-----------|----------|----------|----------|
| Coordinator table (5 rows) | T3-S1 (Impl-B) | T-1, T-2 (Impl-A) | Exact `subagent_type` names |
| §3 Coordinator role | T3-S2 (Impl-B) | T4-S2, T-9 (Impl-A) | "Follow agent-common-protocol.md" |
| §6 routing model | T3-S3 (Impl-B) | T-5, T-6, T-7, T-8 | Category numbers (1,2,7,8,9 coordinated; 3,4,5,6,10 direct) |
| Common protocol routing | T4 (Impl-B) | T-9 (Impl-A) | "Message your coordinator" pattern |
| Coordinator .md content | T-1 (Impl-A) | T-2 catalog Level 2 | Body copied to Level 2 entries |
| Level 1 catalog | T-2 (Impl-A) | T3-S3 §6 Before Spawning | "Level 1 (~300L)" reference |
| exec-coord protocol | T-1 (Impl-A) | T-5 (Impl-A) | Review dispatch matches §6.4 |
| test-coord protocol | T-1 (Impl-A) | T-7 (Impl-A) | Tester→integrator lifecycle |

**Cross-implementer dependencies:** T-3 (B) after T-2 (A). T-9 (A) after T-4 (B).

---

## §7 Validation Checklist

| # | Check | Method |
|---|-------|--------|
| V-1 | All 5 coordinator .md exist with AD-13 template | Glob + Read frontmatter |
| V-2 | agent-catalog.md Level 1 ≤320L with boundary marker | Read + count |
| V-3 | CLAUDE.md §6 has 6-step routing + coordinator management | Read §6 |
| V-4 | agent-common-protocol.md has routing note + Coordinators section | Read |
| V-5 | execution-plan §6.3 has coordinator spawn + AD-11 delegation | Read |
| V-6 | **Code Plausibility** — old_string values match current file content | Read each target, verify old_string exists at expected location |
| V-7 | Grep "Message Lead with:" returns 0 in 20 updated files | Grep verification |
| V-8 | Cross-file coordinator names consistent | Cross-reference T-1 names across T-2, T-3, T-5, T-7, T-9 |

---

## §8 Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| R-1: Coordinator adds context overhead | MED | Mode 3 fallback. maxTurns capped per coordinator. |
| R-2: Coordinator-worker messaging failure | MED | Mode 3 auto-transition after 10min silence. |
| R-3: Stale old_string references | HIGH | AC-0 verifies current file state before every edit. |
| R-4: Cross-implementer interface mismatch | MED | Shared COORDINATOR REFERENCE TABLE in both specs. |
| R-5: dynamic-impact-analyst.md variant text | LOW | Noted in T-9; implementer adapts pattern. |
| R-6: Catalog restructure is full rewrite | MED | T-2 provides complete Level 1 content verbatim. |

---

## §9 Rollback Strategy

All changes are within `.claude/` infrastructure (NL instruction files):

1. **Git revert** — single commit can be cleanly reverted
2. **No runtime deps** — coordinator .md files are inert until explicitly spawned
3. **Backward compatible** — agents without coordinator routing fall back to Lead-direct
4. **Settings unchanged** — no configuration rollback needed

---

## §10 Commit Strategy

**Single commit** after all 10 tasks complete and Gate 6 passes:

```
feat(infra): Lead Architecture Redesign — Selective Coordinator Model

5 coordinators (AD-8), Two-Level Catalog (AD-10), delegated verification (AD-11),
defensive three-mode design (AD-12). 33 files changed (5 CREATE, 28 MODIFY).

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

---

## Architecture Decision Traceability

| AD | Reflected In | Tasks |
|----|--------------|-------|
| AD-8 (5 coordinators) | Coordinator table, routing model, all skills | T-1, T-2, T-3 |
| AD-9 (execution-coordinator cross-category) | Review dispatch protocol, Phase 6 rewrite | T-1, T-5 |
| AD-10 (Two-Level Catalog) | Catalog restructure, §6 Before Spawning | T-2, T-3 |
| AD-11 (Delegated verification) | 3-tier verification, skill rewrites | T-3, T-5, T-7 |
| AD-12 (Three-Mode Design) | Mode 1 + Mode 3 in §6, coordinator failure handling | T-3, T-1 |
| AD-13 (Coordinator template) | 5 coordinator .md files, shared tool set | T-1 |

## Plan Decisions (Phase 4)

| ID | Decision | Rationale |
|----|----------|-----------|
| PD-1 | Routing as overlay note (not individual edits) | DRY — single note at protocol top |
| PD-2 | settings.json NO_CHANGE | Coordinators discovered by directory scan |
| PD-3 | §6 Mode 1 + Mode 3 only (no Mode 2) | AD-12 Mode 2 is future opt-in |

# Skill Optimization v9.0 — Implementation Plan (§1-§3)

> **For Lead:** This plan is designed for Agent Teams Phase 6 execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
> Follow execution-coordinator dispatch for multi-implementer coordination.

**Goal:** Restructure all 9 pipeline skills (2 template variants), converge 8 coordinator .md files (Template B), create 3 fork agent .md files, and modify CLAUDE.md §10 + agent-common-protocol.md — Big Bang atomic commit of 22 files.

**Architecture Source:** Phase 3 consolidated artifacts:
- `phase-3/arch-coord/L2-summary.md` (221L unified report)
- `phase-3/structure-architect-1/L3-full/structure-design.md` (754L)
- `phase-3/interface-architect-1/L3-full/interface-design.md` (412L)
- `phase-3/risk-architect-1/L3-full/risk-design.md` (662L)

**Pipeline:** COMPLEX tier — full Phase 6 with execution-coordinator.

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

```
Phase 6: Implementation   — 5 implementers execute in parallel (22 files)
Phase 6.V: Verification   — Cross-reference validation (Task V)
Phase 9: Delivery          — Atomic commit + smoke test (RISK-5 mitigation)
```

### Teammate Allocation

| Role | ID | Agent Type | File Count | Coupling Group | Phase |
|------|----|-----------|:----------:|----------------|-------|
| Fork Implementer 1 | impl-a1 | `implementer` | 4 | fork-cluster-1 | 6 |
| Fork Implementer 2 | impl-a2 | `implementer` | 3 | fork-cluster-2 | 6 |
| Skill Implementer | impl-b | `implementer` | 5 | coord-skills | 6 |
| Coordinator Convergence | infra-c | `infra-implementer` | 8 | coord-convergence | 6 |
| Protocol Editor | infra-d | `infra-implementer` | 2 | protocol-pair | 6 |
| Cross-Ref Verifier | verifier | `integrator` | 0 (reads all) | verification | 6.V |

**WHY 5 implementers (not 1 or 2):**
- 22 files across 5 coupling groups with distinct concerns
- BUG-002 scope gate: max 4 files per implementer where possible
- Fork coupling constraint: fork skill `agent:` ↔ fork agent .md filename must be co-located
- Coordinator coupling is loose (pre-existing names) → safe to separate from skills
- Parallel execution reduces total pipeline time

**WHY split fork into A1+A2 (not single 7-file implementer):**
- 7 files exceeds BUG-002 scope gate
- rsil-agent is shared by 2 skills → must stay together (A2)
- pt-manager + delivery-agent have separate skill pairs → group together (A1)
- No cross-pair coupling between A1 and A2 beyond shared fork template pattern

### Execution Sequence

```
Lead:   TeamCreate("skill-opt-v9-p6")
Lead:   TaskCreate x 6 (Tasks A1, A2, B, C, D, V — see §4)
Lead:   Spawn execution-coordinator
        ┌──────────────────────────────────────────────────────────────┐
        │ Parallel Implementation (all 5 implementers)                 │
        │                                                              │
        │  D (protocol-pair)     ──→ §10 + §Task API edits            │
        │  A1 (fork-cluster-1)   ──→ pt-mgr + perm-tasks + del-agent  │
        │                             + del-pipeline                   │
        │  A2 (fork-cluster-2)   ──→ rsil-agent + rsil-global         │
        │                             + rsil-review                    │
        │  B (coord-skills)      ──→ 5 coordinator-based SKILL.md     │
        │  C (coord-convergence) ──→ 8 coordinator .md files          │
        │                                                              │
        │  Each: Understanding verification → Plan → Execute → Review  │
        └──────────────────────────────────────────────────────────────┘
Lead:   Gate 6a: Per-implementer completion (exec-coordinator reports)
Lead:   Spawn verifier (Task V — cross-reference validation)
        ┌──────────────────────────────────────────────────────────────┐
        │ Cross-Reference Verification                                  │
        │  - All subagent_type refs resolve to agent .md files          │
        │  - All agent: fields match fork agent .md filenames           │
        │  - §10 fork agent names match actual files                    │
        │  - Coordinator worker lists consistent                        │
        │  - Interface Section contracts consistent across skills       │
        └──────────────────────────────────────────────────────────────┘
Lead:   Gate 6b: Verification PASS
Lead:   Phase 9: Atomic commit (single git commit, 22 files)
Lead:   Smoke test sequence (RISK-5): A→B→C→D per risk-architect §5
```

---

## 2. Architecture Summary

> Full details: `phase-3/arch-coord/L2-summary.md` (221L).
> This section condenses key decisions. Implementers should read P3 L3 files for depth.

### Key Architecture Decisions

| ID | Decision | Impact |
|----|----------|--------|
| ADR-S1 | 2 template variants: coordinator-based (5 skills) + fork-based (4 skills) | Template is structural guidance, not literal dedup. 61-75% unique per skill |
| D-7 | PT-centric interface: PT = sole cross-phase source of truth | New §C Interface Section in all 9 skills. GC 14→3 sections |
| D-11 | 3 fork agent .md files: pt-manager, delivery-agent, rsil-agent | NEW files. Full designs in risk-architect L3 §1 |
| D-13 | Coordinator .md convergence to Template B (768→402L, -48%) | 8 files modified. Unified frontmatter + 5-section body |
| C-5 | CLAUDE.md §10 exception for 3 named fork agents | 3-layer enforcement: frontmatter → agent .md NL → CLAUDE.md |
| D-14 | GC reduction: 14→3 sections (9 eliminated, 2 migrated to PT) | Skills no longer write/read GC for cross-phase state |
| ADR-S5 | Shared rsil-agent for rsil-global + rsil-review | 1 agent .md, skill body differentiates behavior |
| ADR-S8 | Fork cross-cutting is inline, not 1-line CLAUDE.md references | Fork agents have no CLAUDE.md in context |

### Interface Contracts (must-satisfy)

| Contract | Definition | Authority |
|----------|-----------|-----------|
| C-1 | Per-skill PT Read/Write mapping | interface-architect L3 §1.2 |
| C-2 | L2 Downstream Handoff chain (replaces GC) | interface-architect L3 §1.5 |
| C-3 | GC scratch-only (3 concerns: metrics, gate records, version) | interface-architect L3 §1.4 |
| C-4 | Fork-to-PT Direct (TaskGet/TaskUpdate from fork) | interface-architect L3 §1.7 |
| C-5 | §10 exception (3 named agents, 3-layer enforcement) | interface-architect L3 §2 |

### Per-Skill Delta Summary

| Skill | Template | Unique | Shared | New | Target Lines |
|-------|:--------:|:------:|:------:|:---:|:------------:|
| brainstorming-pipeline | Coord | 65% | 15% | 20% | ~613L |
| agent-teams-write-plan | Coord | 61% | 24% | 16% | ~362L |
| plan-validation-pipeline | Coord | 64% | 20% | 15% | ~434L |
| agent-teams-execution-plan | Coord | 69% | 12% | 18% | ~692L |
| verification-pipeline | Coord | 64% | 16% | 20% | ~574L |
| delivery-pipeline | Fork | 74% | 11% | 15% | ~471L |
| rsil-global | Fork | 75% | 10% | 15% | ~452L |
| rsil-review | Fork | 73% | 8% | 19% | ~549L |
| permanent-tasks | Fork | 72% | 13% | 16% | ~279L |

### Active Risks

| ID | Sev | Risk | Mitigation | Owner |
|----|-----|------|------------|-------|
| RISK-2 | MED-HIGH | PT fork loses conversation history | 3-layer: pipeline/rich/interactive | A1 (permanent-tasks spec) |
| RISK-3 | MEDIUM | Delivery fork complexity | No nested skills, idempotent, fork last in smoke test | A1 (delivery-pipeline spec) |
| RISK-5 | HIGH | Big Bang 22+ files | YAML validation, atomic commit, smoke test, rollback | Lead (Phase 9) |
| RISK-8 | MEDIUM | Task list scope in fork | Pre-deploy validation + $ARGUMENTS fallback | A1, A2 (all fork specs) |

---

## 3. File Ownership Map

### Coupling Groups

| Group | Constraint | Type | Files |
|-------|-----------|------|:-----:|
| fork-cluster-1 | Skill `agent:` ↔ agent .md filename; delivery-agent removes /permanent-tasks nesting | Tight | 4 |
| fork-cluster-2 | Shared rsil-agent ↔ rsil-global + rsil-review skills | Tight | 3 |
| coord-skills | Skill §A references coordinator `subagent_type` (pre-existing names) | Loose | 5 |
| coord-convergence | All 8 coordinators converge to single Template B pattern | Internal | 8 |
| protocol-pair | §10 agent names ↔ §Task API agent names | Tight | 2 |
| verification | Cross-group reference validation (post-implementation) | Post-hoc | 0 |

### Complete File Ownership Table

| # | File Path | Owner | Op | Coupling Group | Depends On |
|---|-----------|-------|----|----------------|------------|
| 1 | `.claude/agents/pt-manager.md` | impl-a1 | CREATE | fork-cluster-1 | — |
| 2 | `.claude/skills/permanent-tasks/SKILL.md` | impl-a1 | MODIFY | fork-cluster-1 | #1 (agent caps) |
| 3 | `.claude/agents/delivery-agent.md` | impl-a1 | CREATE | fork-cluster-1 | — |
| 4 | `.claude/skills/delivery-pipeline/SKILL.md` | impl-a1 | MODIFY | fork-cluster-1 | #3 (agent caps) |
| 5 | `.claude/agents/rsil-agent.md` | impl-a2 | CREATE | fork-cluster-2 | — |
| 6 | `.claude/skills/rsil-global/SKILL.md` | impl-a2 | MODIFY | fork-cluster-2 | #5 (agent caps) |
| 7 | `.claude/skills/rsil-review/SKILL.md` | impl-a2 | MODIFY | fork-cluster-2 | #5 (agent caps) |
| 8 | `.claude/skills/brainstorming-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills | — |
| 9 | `.claude/skills/agent-teams-write-plan/SKILL.md` | impl-b | MODIFY | coord-skills | — |
| 10 | `.claude/skills/plan-validation-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills | — |
| 11 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | impl-b | MODIFY | coord-skills | — |
| 12 | `.claude/skills/verification-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills | — |
| 13 | `.claude/agents/research-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 14 | `.claude/agents/verification-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 15 | `.claude/agents/architecture-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 16 | `.claude/agents/planning-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 17 | `.claude/agents/validation-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 18 | `.claude/agents/execution-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 19 | `.claude/agents/testing-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 20 | `.claude/agents/infra-quality-coordinator.md` | infra-c | MODIFY | coord-convergence | — |
| 21 | `.claude/CLAUDE.md` | infra-d | MODIFY | protocol-pair | — |
| 22 | `.claude/references/agent-common-protocol.md` | infra-d | MODIFY | protocol-pair | — |

### Ownership Verification

```
impl-a1:  4 files (2 CREATE + 2 MODIFY)  ✓ ≤4 guideline
impl-a2:  3 files (1 CREATE + 2 MODIFY)  ✓ ≤4 guideline
impl-b:   5 files (0 CREATE + 5 MODIFY)  ⚠ exceeds 4, justified: same template variant
infra-c:  8 files (0 CREATE + 8 MODIFY)  ⚠ exceeds 4, justified: small files (38-83L), highly templated
infra-d:  2 files (0 CREATE + 2 MODIFY)  ✓ lightweight (~15 lines total change)
verifier: 0 files (reads all 22)          ✓ read-only verification
──────────────────────────────────────────
Total:    22 files, 0 overlap             ✓ non-overlapping ownership
```

### Cross-Reference Verification Scope (Task V)

After all 5 implementers complete, the integrator (verifier) validates:

| Check | Source | Target | Expected Match |
|-------|--------|--------|---------------|
| Fork skill `agent:` field | 4 fork SKILL.md frontmatter | `.claude/agents/{name}.md` exists | 4 pairs (3 unique agents) |
| Fork skill tool assumptions | 4 fork SKILL.md body | Agent .md `tools:` list | Skill doesn't assume unavailable tools |
| §10 fork agent names | CLAUDE.md §10 | `.claude/agents/{name}.md` exists | 3 names: pt-manager, delivery-agent, rsil-agent |
| §Task API fork agent names | agent-common-protocol.md | CLAUDE.md §10 names | Same 3 names in both files |
| Skill §A `subagent_type` refs | 5 coord SKILL.md §A | `.claude/agents/{name}.md` exists | All coordinator + worker names resolve |
| Coordinator .md §Workers | 8 coordinator .md | Worker agent .md files exist | All worker names resolve |
| Interface Section consistency | All 9 SKILL.md §C | PT schema (interface-architect L3 §1.3) | Read/write sections match contract |
| Coordinator frontmatter | 8 coordinator .md | Template B schema (structure-architect L3 §5.2) | memory:project, disallowedTools:4-item, color present |

### Task Dependency Graph

```
                    ┌──── impl-a1 (fork-cluster-1) ────┐
                    │                                    │
                    ├──── impl-a2 (fork-cluster-2) ────┤
                    │                                    │
Phase 6 start ─────├──── impl-b  (coord-skills)   ────├──→ verifier (Task V) ──→ Gate 6
                    │                                    │
                    ├──── infra-c (coord-convergence)───┤
                    │                                    │
                    └──── infra-d (protocol-pair)  ─────┘
```

All 5 implementers are independent (no mutual file dependencies). Task V depends on all 5 completing. Gate 6 depends on Task V passing.

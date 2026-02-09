---
version: GC-v5
created: 2026-02-08
feature: skl006-delivery-pipeline
complexity: MEDIUM
---

# Global Context — SKL-006: Delivery Pipeline + RSIL

## Scope

**Goal:** Create SKL-006 (Phase 9 Delivery Pipeline) + push entire .claude/ INFRA to the marginal capability boundary of Opus 4.6 + Claude Code CLI v2.1.37 + Agent Teams.

**In Scope:**
- SKL-006 SKILL.md — Phase 9 delivery (commit, PR, PT→MEMORY/ARCHIVE migration, session cleanup)
- RSIL — Push Layer 1 INFRA to maximum capability boundary. ALL technically feasible improvements implemented.
- Layer 2 forward-compatibility — ensure Ontology Framework migration compatibility

**Out of Scope:**
- Layer 2 (Ontology Framework) implementation — covers anything beyond Layer 1 limits
- Topics T-1~T-4 execution

**RSIL Boundary Rule:** If it's technically feasible within Opus 4.6 + CC v2.1.37, implement it. Only defer to Layer 2 what Layer 1 cannot do.

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: COMPLETE (Gate 3 APPROVED)
- Phase 4: COMPLETE (Gate 4 APPROVED)
- Phase 5: COMPLETE (Gate 5 APPROVED, Verdict: CONDITIONAL_PASS → mitigations accepted)
- Phase 6: COMPLETE (Gate 6 APPROVED — 7/7 criteria PASS)

## Architecture Summary (from Phase 3)

### SKL-006 Design
- 3 sub-phases: 9.1 Consolidation → 9.2 Delivery → 9.3 Cleanup
- Lead-only, terminal, 4 user confirmations
- Multi-session discovery (cross-session is default)
- ARCHIVE.md in session directory
- Post-rejection recovery for MEMORY.md

### RSIL Catalog (ALL items — feasibility to be re-evaluated in Phase 4)

**Confirmed in-sprint:**
- IMP-002: on-session-compact.sh NLP (~10L)
- IMP-003: on-subagent-start.sh NLP (~5L)
- IMP-004: ARCHIVE.md resolved by SKL-006
- H-1: Agent MEMORY.md templates (~50L)
- IMP-010: Snapshot cleanup in SKL-006

**Re-evaluate for feasibility (user directive: push to marginal line):**
- IMP-001: task-api-guideline.md NLP (530→~200L) — large but correctness fix
- IMP-005: Skill DRY extraction (~191L savings) — coordination needed
- IMP-006: GC→PT full migration — architectural, affects 5 skills
- H-2: Skills preload in agent frontmatter
- H-3: Hooks in agent/skill frontmatter (scope vs global tradeoff)
- H-4: Prompt/agent hooks for quality gates
- H-6: Effort parameter strategy (CC CLI feasibility unclear)
- H-7: Task(agent_type) restrictions
- IMP-011: API key security (env vars)

**Defer to Layer 2 only:**
- Domain-specific gate criteria parameterization
- Ontology-aware delivery checklists
- Domain abstraction layer between skill orchestration and domain logic

## Phase 2 Research Findings

### R-1: Opus 4.6 + Claude Code CLI v2.1.37
- 200K context (1M beta), 128K output, adaptive thinking, effort parameter
- 14 hook events (3 handler types: command/prompt/agent)
- Task(agent_type) restrictions, skills preload, hooks in frontmatter
- delegate mode, agent memory persistence, statusLine

### R-2: INFRA Pattern Analysis
- 24 files, ~4845 lines, 6 categories
- 32+ protocol markers in task-api-guideline.md
- ~276 lines DRY violations across 5 pipeline skills
- GC→PT dual-track contradicts design intent
- Multi-session discovery is standard (each skill creates separate session dir)

## Architecture Decisions
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | Comprehensive scope (Step 1-4) | Full delivery coverage | P1 |
| D-2 | Full INFRA RSIL to marginal line | User directive: push to Layer 1 limits | P1/P3 |
| D-3 | claude-code-guide mandatory | Accurate feasibility assessment required | P1 |
| D-4 | Layer 2 forward-compatible | Future Ontology migration | P1 |
| D-5 | Shift-Left philosophy | Maximize research/architecture effort | P1 |
| D-6 | IMP-006 GC→PT upgraded to HIGH | Dual-track contradicts design intent | P2 |
| D-7 | Auto-compact improvement in RSIL | researcher-1 compact highlighted need | P2 |
| D-8 | 3 sub-phases for SKL-006 | Natural operation clustering | P3 |
| D-9 | User-confirmed git, never auto-commit | CLAUDE.md §8 safety | P3 |
| D-10 | ARCHIVE.md in session dir | Session-scoped, not project-permanent | P3 |
| D-11 | PT→MEMORY via Read-Merge-Write | Reuses /permanent-tasks pattern | P3 |
| D-12 | Multi-session discovery as default | Each skill creates separate session dir | P3 |
| D-13 | Always offer PR | User preference | P3 |
| D-14 | Consolidation before Delivery | Commit message quality, single clean commit | P3 |

## Constraints
- Phase 9 is Lead-only (no teammates)
- NLP v6.0 native, 0 protocol markers
- Backward-compatible with existing skills
- Layer 2 forward-compatible
- Push to marginal line — only defer what Layer 1 genuinely cannot do

## Implementation Plan Reference
- **Plan:** `docs/plans/2026-02-08-skl006-delivery-pipeline.md` (769 lines, 10 sections)
- **Session:** `.agent/teams/skl006-write-plan/phase-4/architect-1/`

## Task Decomposition
| # | Task | Owner | Dependencies |
|---|------|-------|-------------|
| T-1 | Create SKL-006 SKILL.md | Impl-A | None |
| T-2 | Hook reduction 8→3 | Impl-B | None |
| T-3 | Hook NLP conversion | Impl-B | None |
| T-4 | NL-MIGRATE L1/L2 to agent .md | Impl-B | T-2 |
| T-5 | Agent MEMORY.md templates | Impl-B | None |
| T-6 | Cross-workstream validation | Lead | T-1~T-5 |

## File Ownership Map
| Implementer | Files | Operations |
|-------------|-------|-----------|
| A (SKL-006) | `.claude/skills/delivery-pipeline/SKILL.md` | 1 CREATE (~380L) |
| B (RSIL) | settings.json, 5 hook .sh (delete), 2 hook .sh (modify), 6 agent .md (modify), 2 MEMORY.md (create) | 5 DELETE, 9 MODIFY, 2 CREATE |

## Commit Strategy
- Single commit, Conventional Commits format
- All changes atomic — no partial delivery

## Phase 5 Validation Targets
- SKL-006 structural completeness (Phase 0 pattern, 3 sub-phases, user confirmations)
- Hook reduction correctness (settings.json integrity, no orphan references)
- NL reminder consistency across 6 agent .md files
- File ownership non-overlap verification

## Phase 6 Results
- Tasks completed: 6/6 (T-1~T-6)
- Files created: 3 (SKILL.md 422L, tester/MEMORY.md, integrator/MEMORY.md)
- Files modified: 9 (settings.json, 2 hooks, 6 agent .md, CLAUDE.md)
- Files deleted: 5 (on-subagent-stop/teammate-idle/task-completed/task-update/tool-failure .sh)
- Implementers: 2 (impl-A: SKL-006, impl-B: RSIL)
- Two-stage review: ALL PASS
- Phase 5 mitigations H-1 and H-2: IMPLEMENTED
- Gate 6 session: `.agent/teams/skl006-execution/`

## Phase 7 Entry Conditions
- Infrastructure changes (not application code) — testing is structural verification
- Test targets: settings.json validity, hook file existence, agent .md consistency, SKILL.md structure
- Integration points: hooks ↔ settings.json, agent .md ↔ CLAUDE.md ↔ agent-common-protocol.md

# L2 Summary — Decomposition Planner (§1-§5 COMPLETE)

## Summary

Decomposed the Skill Optimization v9.0 architecture (149 evidence, 30 decisions, 5 contracts from Phase 3, plus 2 interface-planner deliverables from Phase 4) into 6 implementation tasks across 5 coupling groups covering 22 files. The plan uses 5 parallel implementers (3 `implementer` + 2 `infra-implementer`) plus 1 post-hoc `integrator` for cross-reference verification. All implementers run in parallel with zero mutual file dependencies. Enhanced with interface-planner data: verbatim §C Interface Section content for all 9 skills and GC migration tables with exact line references for all 5 coordinator-based skills.

Key design decisions: (1) splitting the 7-file fork cluster into A1(4)+A2(3) for BUG-002 safety while preserving tight coupling, (2) keeping coordinator-based skills (impl-b) separate from coordinator .md files (infra-c) since coordinator names are pre-existing identifiers (loose coupling), (3) including a CH-001-style cross-reference verification task with 8 explicit checks, and (4) embedding GC migration line references directly in Task B description so the implementer has exact locations to modify.

## Task Breakdown (§4)

| Task | Owner | Files | Type | Coupling Group |
|------|-------|:-----:|------|----------------|
| D | infra-d | 2 | infra-implementer | protocol-pair |
| A1 | impl-a1 | 4 | implementer | fork-cluster-1 |
| A2 | impl-a2 | 3 | implementer | fork-cluster-2 |
| B | impl-b | 5 | implementer | coord-skills |
| C | infra-c | 8 | infra-implementer | coord-convergence |
| V | verifier | 0 (reads 22) | integrator | verification |

**Dependency:** D/A1/A2/B/C all parallel → V → Gate 6

Each task includes AC-0 (plan-vs-reality verification) requiring the implementer to read current file state before editing, confirming insertion points and section structure match the plan.

## File Ownership Map (§3)

22 files across 5 coupling groups, zero overlap:
- **fork-cluster-1** (4 files): pt-manager.md + permanent-tasks SKILL + delivery-agent.md + delivery-pipeline SKILL — tight coupling (skill `agent:` ↔ agent filename)
- **fork-cluster-2** (3 files): rsil-agent.md + rsil-global SKILL + rsil-review SKILL — tight coupling (shared agent ADR-S5)
- **coord-skills** (5 files): 5 coordinator-based SKILL.md — loose coupling to coordinators (pre-existing names)
- **coord-convergence** (8 files): 8 coordinator .md → Template B — internal coupling (same pattern)
- **protocol-pair** (2 files): CLAUDE.md §10 + agent-common-protocol.md — tight coupling (same 3 agent names)

## Per-File Specifications (§5) — Enhanced

All 22 files specified with:
- **Operation type:** CREATE (3 new agent .md) or MODIFY (19 existing files)
- **Verification Level:** VL-1 (6 files: small/well-defined), VL-2 (5 files: moderate with cross-refs), VL-3 (11 files: new or major restructure)
- **RISK-8 Fallback Delta:** All 7 fork-related files include $ARGUMENTS fallback subsection
- **§C Interface Section:** Verbatim content from interface-architect L3 §1 for all 9 skills
- **GC Migration Tables:** Per-skill tables with exact line references from dependency-matrix.md §6 (5 coordinator-based skills)
- **Cross-reference requirements:** Per-file listing of what must match other files

### Key Per-File Decisions

| Decision | Rationale |
|----------|-----------|
| Fork agents specified from risk-architect L3 §1 (verbatim) | Complete designs available, no additional design needed |
| Fork skills: voice change + restructure, preserve core logic | 72-75% content is unique, template changes are structural |
| Coordinator .md: gap analysis table drives per-file delta | 5 need body restructure (Template A→B), 3 need frontmatter-only |
| Coordinator skills: common changes + per-skill unique notes | New §C Interface Section is the primary structural addition |
| GC migration: line-reference tables per coordinator skill | Exact locations from dependency-matrix.md §6 eliminate guesswork |

## PT Goal Linkage

| PT Decision | §4/§5 Contribution |
|-------------|-------------------|
| D-7 (PT-centric) | All 9 skill specs include new §C Interface Section with PT Read/Write contract |
| D-8 (Big Bang) | 22-file atomic commit, Task V validates cross-references before commit |
| D-11 (3 fork agents) | Tasks A1+A2 create 3 agent .md files from risk-architect L3 §1 |
| D-13 (Coordinator convergence) | Task C converges 8 coordinators to Template B with gap analysis |
| D-14 (GC 14→3) | All 5 coordinator skill specs include GC migration tables with line refs |
| C-5 (§10 exception) | Task D applies exact text from interface-architect L3 §2.1-2.2 |
| RISK-8 ($ARGUMENTS fallback) | All fork file specs include fallback delta subsections |

## Downstream Handoff

**For execution-coordinator (Phase 6):**
- Read `L3-full/sections-4-5.md` for all task descriptions and per-file specs
- Read `L3-full/sections-1-2-3.md` for orchestration overview, architecture summary, file ownership map
- 6 tasks: D, A1, A2, B, C (parallel) → V (depends on all)
- 5 implementers + 1 verifier, zero file overlap, all parallel-safe
- Each task description contains embedded acceptance criteria and architecture references

## Evidence Sources

| Source | Count | Key References |
|--------|:-----:|----------------|
| Phase 3 architecture (read) | 4 | arch-coord L2, structure/interface/risk architect L3 |
| Phase 4 interface-planner (read) | 2 | interface-design.md §1-§5, dependency-matrix.md §6-§8 |
| Current file reads (verification) | 14 | 8 coordinator .md, 4 fork skill headers, 2 protocol sections |
| CH-001 exemplar (format) | 1 | Task structure, cross-reference verification pattern |
| Sequential-thinking (design) | 3 | §3 ownership, Q1/Q2 AD-11, §4/§5 batching |
| **Total** | **24** | |

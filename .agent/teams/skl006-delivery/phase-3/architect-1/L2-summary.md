# L2 Summary: SKL-006 Delivery Pipeline + RSIL Catalog Architecture

**Architect:** architect-1
**Date:** 2026-02-08
**Consumer:** Lead (Gate 3), Phase 4 architect, Phase 5 devils-advocate

---

## Executive Summary

SKL-006 is a Lead-only, terminal phase skill with 3 sub-phases: Consolidation (PT final update, MEMORY migration, ARCHIVE creation), Delivery (git commit, optional PR), and Cleanup (artifact archival, task list). It requires 4 user confirmation points, spawns no teammates, and produces no "Next" phase. The RSIL catalog identifies 5 in-sprint items (2 hook NLP fixes, ARCHIVE.md resolution, agent MEMORY templates, snapshot cleanup) and defers 8+ items including the large task-api-guideline.md NLP conversion and skill DRY extraction.

---

## Architecture Decision Summary

| AD | Decision | Key Rationale |
|----|----------|---------------|
| AD-1 | 3 sub-phases (Consolidation → Delivery → Cleanup) | Natural operation clustering, clear ordering |
| AD-2 | User-confirmed git operations, never auto-commit | CLAUDE.md §8 safety, external visibility |
| AD-3 | ARCHIVE.md in session directory | Session-scoped record, not permanent project artifact |
| AD-4 | PT→MEMORY via Read-Merge-Write | Reuses /permanent-tasks pattern, selective extraction |
| AD-5 | Preserve artifacts, clean transients | L1/L2/L3 have downstream value, snapshots don't |
| AD-6 | 5 RSIL in-sprint, 8+ deferred | SKL-006 enablers + quick wins only, defer large scope |
| AD-7 | No skill DRY extraction this sprint | High coordination risk, modest benefit (7.5%) |
| AD-8 | Support both GC and PT input discovery | Backward compat until GC→PT migration completes |

---

## SKL-006 Design Highlights

**Unique characteristics vs other pipeline skills:**
- Lead-only (no TeamCreate, no teammates, no understanding verification)
- Terminal (no "Next: Phase N+1" guidance)
- External-facing (git operations, MEMORY.md persistence)
- 4 user confirmation points (MEMORY review, commit, PR, cleanup)

**Phase structure:**
- 9.1 Consolidation: Final PT update → PT→MEMORY migration → ARCHIVE.md creation
- 9.2 Delivery: Git commit (user-confirmed) → PR (optional, user-confirmed)
- 9.3 Cleanup: Session artifact cleanup (user-confirmed) → Task list cleanup

**Input discovery:** Finds latest completed pipeline via gate records. Supports both PT-based and GC-based sessions. Handles missing plan gracefully (warn, don't abort).

**ARCHIVE.md template:** Structured record with gate summary, key decisions, implementation metrics, deviations, lessons learned, team composition.

---

## RSIL Catalog Summary

### In-Sprint (5 items)
1. **IMP-002** on-session-compact.sh NLP — 1 file, ~10 lines
2. **IMP-003** on-subagent-start.sh NLP — 1 file, ~5 lines
3. **IMP-004** ARCHIVE.md reference — resolved by SKL-006 existence (0 changes)
4. **H-1** Agent MEMORY.md templates — up to 5 new files, ~50 lines total
5. **IMP-010** Pre-compact snapshot cleanup — integrated into SKL-006 Phase 9.3

### Deferred (8+ items)
- IMP-001: task-api-guideline.md NLP (530→200L) — separate terminal work
- IMP-005/008: Skill DRY extraction (~191 lines) — dedicated sprint needed
- IMP-006: GC→PT full migration — architectural, affects all 5 pipeline skills
- H-2/H-3/H-4/H-7: New Claude Code features — require careful testing per feature
- H-6: Effort parameter — not configurable in Claude Code CLI

---

## Risk Assessment

6 identified risks, none CRITICAL unmitigated. Highest: R-2 (accidental secret in commit, score 8) mitigated by explicit exclude list per CLAUDE.md §8. R-1 (MEMORY.md corruption, score 6) mitigated by user preview and git recovery.

---

## Layer 2 Forward-Compatibility

SKL-006 is fully domain-agnostic. ARCHIVE.md template, MEMORY migration, git operations, and cleanup all work for any domain. Ontology Framework sessions will benefit from H-1 agent memory templates. Future Layer 2 extensions can add domain-specific ARCHIVE sections without modifying the base skill.

---

## Implementation Scope Estimate

| Component | Files | Lines | Effort |
|-----------|-------|-------|--------|
| SKL-006 SKILL.md | 1 new | ~350-400 | Primary |
| Hook NLP (IMP-002/003) | 2 modified | ~15 changed | Quick win |
| Agent MEMORY.md templates (H-1) | Up to 5 new | ~50 total | Quick win |
| CLAUDE.md clarification | 0-1 modified | ~5 | Optional |

**Total:** 1 new skill + 2 hook fixes + 5 memory templates = 8 files, ~420 new lines

---

## Items Requiring User Input (for Lead to relay)

1. ARCHIVE.md location: session directory vs docs/ ?
2. RSIL sprint scope: 5 items confirmed?
3. PR behavior: always offer, or only on non-main branches?
4. Multi-session: single session discovery or cross-session?

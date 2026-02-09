# L3: Phase 9 Delivery Pipeline Requirements

## Entry Conditions (from verification-pipeline Clean Termination)

```
## Phase 9 Entry Conditions
- All tests passing
- All conflicts resolved (if applicable)
- Known issues: {list or "none"}
```

Phase 9 receives:
- PT-v{final} with Phase 7 (and optionally 8) COMPLETE
- GC-v{final} with full phase pipeline status
- All L1/L2/L3 artifacts from phases 2-8
- Implementation plan in docs/plans/
- orchestration-plan.md (session state)
- TEAM-MEMORY.md (session knowledge)
- Git working tree with all code changes (unstaged/staged/committed varies)

## Operations (Derived from Analysis)

### Op-1: Final PT Update
- Mark all phases COMPLETE in Phase Status
- Add final metrics (files created/modified, test pass rate, etc.)
- This is the last PT version

### Op-2: PT → MEMORY.md Migration
- Extract durable lessons from PT into `~/.claude/projects/-home-palantir/memory/MEMORY.md`
- Keep: User intent summary, architecture decisions, key constraints, bug discoveries
- Discard: Transient phase status, session-specific paths, teammate assignments
- Use selective extraction, not copy-paste

### Op-3: ARCHIVE.md Creation
**Currently undefined.** Proposed template:

```markdown
# Pipeline Archive — {Feature Name}

## Summary
- Feature: {name}
- Dates: {start} → {end}
- Phases: {1-8|9} completed
- Complexity: {SIMPLE|MEDIUM|COMPLEX}

## Gate Record Summary
| Phase | Gate | Result | Date |
|-------|------|--------|------|
| 1 | G1 | APPROVED | {date} |
| ... | ... | ... | ... |

## Key Decisions
| # | Decision | Phase | Rationale |
|---|----------|-------|-----------|
| D-1 | {decision} | P{N} | {rationale} |

## Metrics
- Files created: {N}
- Files modified: {N}
- Tests: {pass}/{total}
- Implementers used: {N}
- Total pipeline iterations: {N}

## Deviations from Plan
- {any deviations noted during execution}

## Lessons Learned
- {extracted from TEAM-MEMORY.md and PT}
```

Location: `.agent/teams/{session-id}/ARCHIVE.md` or `docs/archives/{date}-{feature}.md`?
CLAUDE.md says "Archive to MEMORY.md + ARCHIVE.md" — suggests ARCHIVE.md is session-level, not permanent. So `.agent/teams/{session-id}/ARCHIVE.md`.

### Op-4: Git Operations
Per CLAUDE.md §8 Safety:
- Never force push main. Never skip hooks. No secrets in commits.
- Stage specific files (not git add -A)
- Commit with descriptive message
- Optionally create PR (user-confirmed)

**Current git patterns from codebase:**
```
git log --oneline -5:
09ba73f feat(skill): SKL-005 verification-pipeline + INFRA RSI fixes
50ce36d feat(skill): SKL-004 plan-validation-pipeline NLP v6.0 + Phase 0 + PT integration
6f253f7 feat(infra): NLP v6.0 — natural language DIA + PERMANENT Task integration
b3c1012 docs(ontology): Ontology Framework brainstorming handoff + restructured reference files
7abd080 docs(design): PERMANENT Task — GC replacement + /permanent-tasks skill
```

Pattern: `{type}({scope}): {description}` — standard Conventional Commits.

### Op-5: Session Cleanup
- Archive .agent/teams/{session-id}/ key files (orchestration-plan, gate records, L1/L2)
- Clean pre-compact snapshot files (29+ accumulated)
- Clean task list (completed tasks may auto-delete per ISS-001)
- Preserve: L1/L2/L3 directories, ARCHIVE.md, gate-record.yaml files
- Delete: pre-compact-tasks-*.json, tool-failures.log, compact-events.log, teammate-lifecycle.log

### Op-6: User Summary
Present final report:
```
## Pipeline Delivery Complete

**Feature:** {name}
**Duration:** {estimate}
**Phases:** 1-9 COMPLETE

**Deliverables:**
- Code changes: {file list}
- Commit: {hash} (branch: {name})
- PR: {URL if created}
- ARCHIVE: .agent/teams/{session-id}/ARCHIVE.md
- MEMORY: Updated with lessons learned

**Metrics:**
- {key metrics from ARCHIVE}
```

## Phase 9 Characteristics

| Aspect | Value |
|--------|-------|
| Zone | POST-EXEC |
| Teammate | Lead only (no spawned agents) |
| Effort | medium |
| Entry | Phase 7 (or 8) COMPLETE |
| Exit | Git commit/PR + ARCHIVE + MEMORY update |
| User Interaction | High (confirm commit, PR options, cleanup scope) |

Phase 9 is unique: it's the only phase that interacts heavily with external systems (git) and persists knowledge beyond the session (MEMORY.md). All other phases are session-scoped.

## Existing Skill Termination Patterns (for Consistency)

All skills end with:
1. GC update → final version
2. Output Summary → user-facing report
3. Shutdown → teammates → TeamDelete → preserve artifacts
4. "Next: Phase {N+1}" guidance

Phase 9 has no "Next" — it's the terminal phase. Instead:
1. Final PT update
2. PT → MEMORY.md + ARCHIVE.md
3. Git operations (user-confirmed)
4. Session cleanup (user-confirmed)
5. Final summary (no "Next" — complete)

## Missing Pieces for Phase 9 Design

1. **ARCHIVE.md template** — proposed above, needs user approval
2. **Cleanup scope** — which .agent/teams/ files to keep? User preference.
3. **PR default** — always offer, never auto-create? User preference.
4. **MEMORY.md update strategy** — append new section or merge into existing? Likely Read-Merge-Write per /permanent-tasks pattern.
5. **Multi-session continuity** — if pipeline spans multiple sessions, how does Phase 9 find all artifacts?

# Lead Architecture Redesign — Architect Agent Notes

## Phase 3 Architecture (2026-02-11)

### Key Patterns Learned
- **Selective > uniform when interface uniformity is already broken:** D-2 chose 10 coordinators for uniformity, but 4 cross-cutting Lead-direct patterns already break uniformity. Evidence-based refinement to 5 coordinators reduces overhead without losing the broken benefit.
- **Peer messaging solves cross-category dispatch:** The 3→7 hop problem with naive coordinators is solved by letting execution-coordinator message reviewers directly (peer-to-peer). Key insight: review agents are "services" that respond to whoever messages them.
- **Quantify per-task, not just per-session:** Total token savings (53%) is less compelling than per-task savings (71% in Phase 6 inner loop). Per-task savings compound: 5 tasks × 2,500 saved = 12,500 tokens.
- **Coordinator verification delegation:** Lead verifies coordinators, coordinators verify workers. Impact Map excerpt enables category-scoped verification. Gate spot-checks catch quality degradation.
- **Three-mode defensive design needs zero extra implementation:** Flat (primary) + nested (enhancement) + Lead-direct (fallback) are all natural consequences of the architecture. No conditional code needed.
- **Level 1/Level 2 catalog split by offset, not by file:** Single file with Read limit parameter avoids cross-reference fragility of separate files.

### Coordinator Architecture Principles
- Coordinators need Read/Glob/Grep/Write/TaskList/TaskGet + sequential-thinking, NOT Edit/Bash
- execution-coordinator is the most complex (manages implementation + review lifecycle)
- Single-agent categories don't benefit from coordinators (1→1 doesn't reduce Lead burden)
- Review agents are services, not a coordinated category — dispatched by execution-coordinator in P6
- Coordinator failure → automatic Lead-direct fallback (workers already pre-spawned)

### Risk Patterns
- execution-coordinator complexity → detailed template + injected review prompt templates from Lead
- Skill migration complexity → phased rollout (execution-plan first, then brainstorming, then others)
- Intent relay degradation → full PT context in coordinator directive (not summarized)
- Coordinator context pressure → Pre-Compact Obligation (same as implementers)

## Phase 4 Detailed Design (2026-02-11)

### Key Patterns Learned
- **Co-locality principle for implementer split:** Place the creator and primary consumer of shared artifacts (coordinator .md files) in the same implementer scope. This eliminates the need for cross-implementer reading of each other's output. The test: does any implementer need to read a file created by the other? If yes, reconsider the split.
- **COORDINATOR REFERENCE TABLE as verbatim shared interface:** When two parallel implementers need identical shared content, provide it verbatim in §6 Interface Contracts. Neither reads the other's output. Zero coordination overhead — the plan IS the coordination mechanism.
- **Complete file content for CREATE tasks:** For infrastructure .md files where the entire structure matters (not just code), providing the COMPLETE file content (not just key sections) in §5 eliminates interpretation variance. ~65-110L per coordinator file, provided in full.
- **CLAUDE.md §6 complete rewrite strategy:** When a section undergoes fundamental restructuring (direct agent management → coordinator routing), provide the complete replacement text rather than incremental edits. The old structure doesn't map to the new structure — atomic replacement is safer.
- **Grep-based verification for mechanical tasks:** T-9 (20 agent routing updates) uses pattern-based specification with grep verification: "25 matches for new pattern, 0 matches for old pattern." This is the right approach for high-count, low-complexity changes.
- **File count correction discipline:** Architecture said 37, analysis showed 34. Three files removed with explicit justification per file (settings.json: auto-discovered; devils-advocate: no pattern; execution-monitor: Lead-direct). Document the delta, don't silently adjust.

### Implementation Plan Design Principles (new)
- For plans with both CREATE and MODIFY: provide complete file content for CREATE, old_string→new_string for MODIFY
- §6 Interface Contracts should include a shared reference table that both implementers use verbatim
- VL grading by task: VL-HIGH for structural changes (T-1,T-3,T-4,T-5), VL-MED for section changes (T-2,T-6,T-7), VL-LOW for mechanical updates (T-8,T-9,T-10)
- 9-point validation checklist covers: structural consistency, size constraints, content consistency, section presence, flow correctness, cross-skill consistency, pattern verification, dimension presence, circular reference absence
- Co-locality split produces better load balance (27+7 files) than creator-vs-consumer split when the creator has downstream tasks that consume the created files

### Risk Patterns (new)
- T-5 execution-plan rewrite is HIGHEST risk → compensated with detailed old/new strings and preserved review templates
- Catalog restructure (T-2) is MEDIUM risk → clear Level 1/2 boundary with content preservation
- Mechanical routing errors (T-9) are LOW risk → pattern-based with grep verification
- Cross-implementer timing is NONE risk → zero dependencies via COORDINATOR REFERENCE TABLE

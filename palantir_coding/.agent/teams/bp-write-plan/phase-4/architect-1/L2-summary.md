## Summary

Implementation plan for brainstorming-pipeline P0/P1 flow redesign. 25 edit specifications across 5 sequential tasks targeting a single file (SKILL.md, 672L → ~575L). Implements 8 Architecture Decisions plus 4 compression options (A-hybrid, B-hybrid, C, G).

## Plan Design

### Decomposition Strategy

Section-ordered (top-to-bottom) rather than AD-ordered. Rationale:
- Edit tool `old_string` matching is safest when processing top-to-bottom
- AD-6 alone touches 12 scattered locations — section ordering handles each inline as its section is processed
- AC-0 reads contiguous blocks, not scattered locations
- AD traceability preserved by tagging each spec with source AD(s)

### Task Structure

| Task | Scope | Specs | Key ADs |
|------|-------|-------|---------|
| A | Header + Phase 0 + Phase 1.1 | S-1 to S-5 | AD-1, AD-4, AD-6, AD-7 |
| B | Phase 1.2 through 1.3.5 | S-6 to S-10 | AD-2, AD-3, AD-6 |
| C | Phase 1.4 + Gate 1 | S-11 to S-17 | AD-4, AD-5, AD-6, Compression |
| D | Phase 2/3 + Cross-Cutting | S-18 to S-25 | AD-6, AD-8, AD-2 adj |
| E | Verification | — | All |

### Compression Budget

| Source | Savings |
|--------|---------|
| Mandatory (8 ADs) | ~55L |
| Option A-hybrid (GC-v1) | ~14L |
| Option B-hybrid (orchestration-plan) | ~8L |
| Option C (gate-record) | ~10L |
| Option G (Gate 1 criteria) | ~8L |
| **Total** | **~95L → ~577L** |

### Key Design Decisions

1. **Single infra-implementer:** One file, no parallelization opportunity, Edit+Write tools sufficient.
2. **Hybrid template compression:** YAML frontmatter as code block (syntax-sensitive), body as field list (Opus 4.6 can generate from field names).
3. **[Sub-skill] annotation:** Gate 1 /permanent-tasks invocation explicitly marked with control flow notes.
4. **VL-1 for deletions, VL-2 for insertions/rewrites:** Deletions are exact (character-perfect), insertions allow minor formatting flexibility.
5. **V6 Code Plausibility:** Included since skill cannot be "run" to verify — recommend monitoring first 3 pipeline runs.

## Verification Design

13 cross-reference checks (V-1 to V-13) covering all 8 ADs, GC structure, pt_version, tier rename, P2/P3 logic preservation, and Clean Termination stability. V6 plausibility checks decision tree terminal states, dependency chains, and reference integrity.

## Risk Assessment

8 risks identified. Highest severity: R-2 (feasibility false positives, MEDIUM) mitigated by soft gate with override, R-7 (edit tool mismatches, MEDIUM) mitigated by section-ordered execution and AC-0.

4 Phase 5 targets challenge key assumptions: SKILL.md is Lead-only, GC body consumed by section name, /permanent-tasks returns control, architecture line counts correct.

## PT Goal Linkage

- AD-1 through AD-8: Direct implementation of architecture decisions from Phase 3
- GC-v3 scope: All 8 issues (H1-H3, M1, L1-L3) addressed
- Line budget: 672L → ~575L (within ≤578L target)
- Downstream compatibility: GC structure preserved, /permanent-tasks interface unchanged

## Evidence Sources

- Architecture design: `.agent/teams/bp-skill-enhance/phase-3/architect-1/L3-full/architecture-design.md` (710L, 8 ADs + migration guide)
- Current SKILL.md: `.claude/skills/brainstorming-pipeline/SKILL.md` (672L, read in full for Read-First-Write-Second compliance)
- CH-001 exemplar: `docs/plans/2026-02-07-ch001-ldap-implementation.md` (10-section template reference)
- GC-v3: `.agent/teams/bp-skill-enhance/global-context.md` (scope, constraints, research findings)
- Agent memory: `~/.claude/agent-memory/architect/MEMORY.md` (template design principles, VL tags, AC-0 pattern)

# L2 Summary — Architecture Design v2 (NLP + PERMANENT Task Integration)

**Architect:** architect-2 | **Phase:** 3 (Revision) | **GC:** v4 | **Date:** 2026-02-08

---

## What This Design Does

Upgrades architect-1's L3 architecture design (NLP conversion) to fully integrate the
PERMANENT Task design. The result is a standalone L3-v2 with complete rewritten text for
all 8 files (CLAUDE.md, agent-common-protocol.md, 6 agent .md files), plus DIA v6.0
specification, deduplication plan, and 12-task implementation breakdown.

## What Changed from Original L3 (architect-1)

### Three New Architecture Decisions

**AD-7: GC → PERMANENT Task.** The fundamental context delivery change. global-context.md
is replaced by a Task API entity (Task #1). Lead includes PT Task ID in directives instead
of embedding full GC content. Teammates self-serve via TaskGet. This reduces directive size
(BUG-002 mitigation), ensures latest version access, and enables self-recovery.

**AD-8: Impact Map in DIA v6.0.** LDAP probing questions and teammate defenses are now
grounded in the Codebase Impact Map from the PERMANENT Task — an authoritative reference
for module dependencies and ripple paths. This is the most significant qualitative DIA
improvement: evidence-based verification replaces guesswork.

**AD-9: Self-Recovery via TaskGet.** After context loss, teammates can call TaskGet on
the PERMANENT Task for immediate self-recovery (find it via TaskList subject search).
Lead is informed but not in the critical recovery path. DIA integrity preserved through
mandatory understanding reconfirmation.

### Six Preserved Decisions (AD-1 through AD-6)

All six original decisions preserved. Three enhanced:
- AD-2: +2 lines for PT lifecycle in §10 (create/maintain/archive)
- AD-3: Communication groups adapted for PT (Task ID in directives)
- AD-5: DIA v6.0 questions grounded in Impact Map data

### Line Count Impact

| | Current (v5.1) | Original L3 (v1) | This L3 (v2) | Δ v5.1→v2 |
|---|---|---|---|---|
| **Total** | **847** | **525** | **543** | **-36%** |
| CLAUDE.md | 207 | 132 | 136 | -34% |
| common-protocol | 79 | 48 | 52 | -34% |
| 6 agent .md | 561 | 345 | 355 | -37% |

**Net cost: +18 lines** over original L3 for PT + Impact Map integration.
All 28/28 original CLAUDE.md behaviors + 13/13 common-protocol behaviors preserved.
5 new PT-specific behaviors + 2 new common-protocol behaviors added.

### Implementation Task Breakdown Change

Original L3: 4 tasks, 2-4 implementers, T1∥T2 → T3∥T4.
This L3: 12 tasks, max 2 concurrent, 6 rounds. Aligned with permanent-tasks-design Section 8.

10 tasks from PT design (SKILL.md CREATE, CLAUDE.md, task-api-guideline, common-protocol,
3 skills, hook, MEMORY.md, ARCHIVE.md) + 2 agent .md tasks from original L3. T3 excluded
(separate terminal).

## Key Trade-offs

1. **Self-serve vs. control:** TaskGet gives teammates autonomy. DIA Layer 2 (Impact
   Analysis) and hooks (PT version injection) provide verification without embedding.

2. **+18 lines for PT integration:** Accepted. The capability gains (self-serve, Impact Map,
   self-recovery) significantly outweigh 2 lines per file average.

3. **12 tasks vs. 4:** More DIA overhead, but Token Policy (no conservation, Claude Max X20)
   makes per-file granularity affordable for higher review quality.

4. **Impact Map empty in early phases:** Acceptable. Impact Map populates progressively
   (empty→partial→mature by Phase 4). Lead uses judgment in early phases.

## What's in L3-full/

`architecture-design-v2.md` — the complete standalone design document containing:
- 9 Architecture Decisions (AD-1~AD-9)
- Complete rewritten text for CLAUDE.md v6.0 (136 lines)
- Complete rewritten text for agent-common-protocol.md v2.0 (52 lines)
- Complete rewritten text for all 6 agent .md files (355 lines total)
- DIA v6.0 specification with Impact Map grounded verification model
- Deduplication plan (GC→PT reference cleanup)
- 12-task implementation breakdown with dependency graph
- 9-risk assessment with mitigations
- Appendix A: Full line count projection
- Appendix B: Change delta from original L3 (every text change documented)

## Files Written

| File | Size | Description |
|------|------|-------------|
| L1-index.yaml | ~124 lines | Architecture decisions, deliverables, counts |
| L2-summary.md | ~95 lines | This file — change narrative and trade-offs |
| L3-full/architecture-design-v2.md | ~780 lines | Complete design with all rewritten text |

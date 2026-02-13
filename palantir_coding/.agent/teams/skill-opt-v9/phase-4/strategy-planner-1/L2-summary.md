# L2 Summary — Strategy Planner (§6-§10)

## Summary

Produced 5 FINAL plan sections (§6-§10) for the Skill Optimization v9.0 Big Bang commit of 22 files. Key design decisions: 4-wave execution with 5 parallel implementers in Wave 1 (co-location of fork agent .md + SKILL.md eliminates cross-implementer dependencies), V6 Code Plausibility split into V6a automated (5 checks gating commit) and V6b manual semantic (5 checks in P6 review), two distinct rollback domains (pre-commit fix-and-retry vs post-commit git revert), and RISK-8 single-plan-with-delta approach (~50 lines across 8 files if fork agents see isolated task list).

## §6 Execution Sequence (FINAL)

4-wave execution with 5+1 agents. Co-location of fork agent .md and fork SKILL.md within the same implementer eliminates the abstract design's Wave 1→2 cross-implementer dependency:

| Wave | Content | Agents | Parallel | Depends On |
|------|---------|:------:|:--------:|:----------:|
| W1: Implementation | All 22 files (5 parallel tracks) | impl-a1, impl-a2, impl-b, infra-c, infra-d | Yes (5 tracks) | None |
| W2: Verification | 8 cross-ref checks (V6a) | verifier | Sequential | W1 |
| W3: Pre-deploy | A → B → C → D functional validation | Lead | Sequential (risk-ordered) | W2 |
| W4: Commit | Atomic git commit | Lead | Single | W3 |

**Implementer assignments:**

| ID | Type | Files | Coupling Group | Internal Order |
|----|------|:-----:|----------------|----------------|
| impl-a1 | implementer | 4 | fork-cluster-1 (pt-manager, permanent-tasks, delivery-agent, delivery-pipeline) | CREATE .md → MODIFY SKILL |
| impl-a2 | implementer | 3 | fork-cluster-2 (rsil-agent, rsil-global, rsil-review) | CREATE .md → MODIFY SKILL |
| impl-b | implementer | 5 | coord-skills (5 coordinator-based SKILL.md) | Any order |
| infra-c | infra-implementer | 8 | coord-convergence (8 coordinator .md) | Any order |
| infra-d | infra-implementer | 2 | protocol-pair (CLAUDE.md §10 + protocol) | §10 first |
| verifier | integrator | 0 | verification (reads all, owns none) | After W1 |

**Critical path:** impl-a1 (4 files, 2 creates). **Zero cross-implementer dependencies** in Wave 1.

## §7 Validation Checklist

6 validation items (V1-V6), with V6 split into automated (V6a) and manual (V6b):

- **V1:** YAML frontmatter parseability — 20 files, python yaml.safe_load
- **V2:** Required frontmatter keys — per file type (skill/coordinator/fork agent)
- **V3:** Cross-file reference accuracy — agent: fields, §10 naming, subagent_type refs
- **V4:** Template section ordering — heading order matches coordinator/fork template
- **V5:** disallowedTools consistency — matches §10 exception scope exactly
- **V6a:** Automated structural (BUG-001 mode:default, memory:project/user, context:fork presence)
- **V6b:** Manual semantic (NL consistency, voice, cross-cutting completeness, behavioral plausibility, C-1~C-5 contract match)

V6a gates pre-deploy Phase A. V6b integrates into execution-coordinator's two-stage review.

## §8 Risk Mitigation Strategy

| Risk | Sev | Primary Mitigation | Fallback | Residual |
|------|-----|--------------------|----------|----------|
| RISK-2 | MED-HIGH | 3-layer: pipeline auto / rich $ARGS / AskUserQuestion | N/A (by-design) | Manual invocation context step-down |
| RISK-3 | MEDIUM | No nested skills + idempotent ops + fork-last + user gates | Revert delivery to Lead-in-context | Fork termination dirty state |
| RISK-5 | HIGH | V6a validation + non-overlapping ownership + atomic commit | git revert HEAD | Subtle NL conflicts undetected until next run |
| RISK-8 | MEDIUM | Primary assumes shared task list; delta branch if isolated | $ARGUMENTS PT-ID passing (~50L delta) | pt-manager loses autonomous discovery |

Pre-deploy validation A→B→C→D refined: V6a structural checks are Phase A PRECONDITION (YAML must parse before testing fork behavior). Shared file awareness: rsil-agent.md fix in Phase C → re-run Phase B.

## §9 Commit Strategy

Big Bang atomic: explicit `git add` of 22 named files → single `git commit` with structured message. Pre-commit gate: V6a + pre-deploy validation must ALL pass. Post-commit: `/rsil-global` + `git diff HEAD~1 --stat` verification.

## §10 Rollback & Recovery

Two domains:
- **Pre-commit:** L1 fix-and-retry → L2 selective `git checkout` → L3 full `git checkout -- .claude/` (architecture fallback)
- **Post-commit:** `git revert HEAD` (systemic) or fix commit (isolated) or fork-back-to-Lead-context (fork-specific)

Fork-back is always safe — all 4 fork skills worked in Lead-in-context mode before. Recovery decision tree provided.

## PT Goal Linkage

| Decision/Risk | Section | Contribution |
|---------------|---------|-------------|
| D-8 (Big Bang) | §6, §9 | Wave structure ensures atomic delivery, explicit file list |
| D-10 (§10 Exception) | §7 V5, §8 RISK-8 | disallowedTools verification + fork task list validation |
| D-11 (Fork Agents) | §8 RISK-2/3, §10 | History loss mitigation + fork-back contingency |
| D-13 (Template B) | §6 W1, §7 V2 | Coordinator convergence in parallel track + frontmatter validation |
| RISK-5 | §7, §8, §9, §10 | V6a gates commit; atomic commit; git revert fallback |
| RISK-8 | §8 delta, §10 | Single-plan-with-delta; fork-back-to-Lead-context |

## Evidence Sources

| Source | Used For |
|--------|----------|
| risk-architect L3 §1-5 (662L) | Fork agent specs, risk register, failure modes, phased adoption |
| arch-coord L2 (221L) | Unified architecture, per-skill delta, cross-lens synthesis |
| structure-architect L3 §1,5,6 (754L) | Template variants, coordinator convergence, section classification |
| interface-architect L3 §1-4 (412L) | PT contract, §10 modification, GC migration, dependency map |
| phase-context.md (107L) | Phase 4 objective, dependency order, constraints, risk summary |
| CH-001 exemplar §7-8 (130L) | Validation checklist format, commit strategy format |
| agent-common-protocol.md (247L) | L1/L2 canonical format, Downstream Handoff structure |

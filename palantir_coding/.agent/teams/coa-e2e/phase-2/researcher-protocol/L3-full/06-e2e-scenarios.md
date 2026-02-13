# E2E Scenario Walkthroughs — COA Protocols in Action

## Scenario 1: Happy Path (P1→P9, Single Implementer)

**Setup:** Simple feature, 1 researcher, 1 architect, 1 implementer, 1 tester, 1 integrator.

```
PHASE 1 (Lead only):
  No COA protocols active — Lead-only phase.

PHASE 2 (researcher-1):
  T+0:  Spawn + DIA verification
  T+5:  [IMPACT_VERIFIED] → begins research
  T+7:  [SELF-LOCATE] P2 | Task 1/1 | Step: reading source files | Progress: 20% | MCP: 1 | Docs: missing
        → COA-1: Lead creates 1-row sub-workflow table
        → COA-3: Docs: missing at first SL — acceptable
  T+15: [SELF-LOCATE] P2 | Task 1/1 | Step: analyzing patterns | Progress: 50% | MCP: 3 | Docs: current
        → COA-1: ON_TRACK
        → COA-3: Docs: current ✓
        → COA-5: MCP: 3 at 50% — healthy for Required phase
  T+25: [SELF-LOCATE] P2 | Task 1/1 | Step: writing L3 specs | Progress: 85% | MCP: 5 | Docs: current
  T+30: [STATUS] Phase 2 | COMPLETE
        → Gate 2 evaluation: sub-workflow ON_TRACK, L1/L2/L3 exist, MCP reported

PHASE 3-5: Similar pattern, single teammate each.

PHASE 6 (implementer-1):
  T+0:  Spawn + DIA (TIER 1, Gate A + Gate B)
  T+8:  [IMPACT_VERIFIED], [PLAN] submitted + [APPROVED]
  T+10: [SELF-LOCATE] P6 | Task 1/2 | Step: implementing module A | Progress: 25% | MCP: 1 | Docs: current
  T+20: [SELF-LOCATE] P6 | Task 1/2 | Step: running self-tests | Progress: 70% | MCP: 3 | Docs: current
  T+25: [SELF-LOCATE] P6 | Task 2/2 | Step: starting task 2 | Progress: 0% | MCP: 3 | Docs: current
        → COA-3: Task boundary checkpoint — L1/L2 updated with Task 1 results
  T+35: [STATUS] Phase 6 | COMPLETE

PHASE 7-9: Standard flow. COA protocols active for tester and integrator.

RESULT: Clean pipeline. No anomalies detected, no re-verification needed.
COA overhead: ~15 [SELF-LOCATE] messages total (~1200 tokens) + documentation checkpoints (~2000 tokens).
```

## Scenario 2: Multi-Implementer Phase 6 with Anomaly

**Setup:** Complex feature, 3 parallel implementers in Phase 6.

```
T+0:   Lead spawns implementer-1, implementer-2, implementer-3
       All complete DIA (TIER 1 + LDAP HIGH)
T+8:   All verified, plans approved

T+10:  COA-1 Sub-Workflow Table:
       | Teammate | Task | Step | Progress | Last SL | Docs | MCP | Status |
       |----------|------|------|----------|---------|------|-----|--------|
       | impl-1 | 1/3 | reading source | 15% | 0min | missing | 0 | ON_TRACK |
       | impl-2 | 1/2 | reading plan §5 | 10% | 0min | missing | 0 | ON_TRACK |
       | impl-3 | 1/1 | reading source | 20% | 0min | missing | 1 | ON_TRACK |

T+20:  impl-1: [SELF-LOCATE] P6 | Task 1/3 | Step: implementing | Progress: 40% | MCP: 2 | Docs: current
       impl-3: [SELF-LOCATE] P6 | Task 1/1 | Step: writing tests | Progress: 60% | MCP: 3 | Docs: current
       impl-2: (SILENCE — no self-locate for 12 minutes)

T+27:  impl-2 still silent (19 min since last SL)
       COA-1: impl-2 → ATTENTION
       COA-4 triggered:
       Lead: [REVERIFY] Phase 6 | Level 1 | Target: implementer-2 | Reason: >15min silence

T+28:  impl-2: [SELF-LOCATE] P6 | Task 1/2 | Step: debugging complex parsing | Progress: 30% | MCP: 0 | Docs: stale
       → Docs: stale → COA-3: Lead sends documentation reminder
       → MCP: 0 at 30% → below threshold (50%), monitor
       Lead: "implementer-2: update L1/L2 with current progress before continuing."

T+30:  impl-2: [SELF-LOCATE] P6 | Task 1/2 | Step: debugging parsing | Progress: 35% | MCP: 0 | Docs: current
       (Docs updated, but MCP still 0)

T+40:  impl-2: [SELF-LOCATE] P6 | Task 1/2 | Step: implementing parser | Progress: 55% | MCP: 0 | Docs: current
       → COA-5: MCP = 0 at 55% in Required phase (context7 Required for P6)
       → COA-4 RV-2:
       Lead: [REVERIFY] Phase 6 | Level 2 | Target: implementer-2 | Reason: MCP usage below minimum (COA-5) | Question: MCP count is 0 at 55%. Phase 6 requires context7. Have you verified library API usage?

T+41:  impl-2: [REVERIFY-RESPONSE] P6 | Level 2 | I've been implementing from the plan §5 spec without checking the actual API docs. Let me verify the parser library API via context7 now.

T+45:  impl-2: [SELF-LOCATE] P6 | Task 1/2 | Step: implementing parser (API verified) | Progress: 65% | MCP: 2 | Docs: current
       → ON_TRACK. Problem caught before completion.

RESULT: COA system detected 2 issues (silence + MCP gap) and resolved both during execution.
Without COA: impl-2 would have completed with potentially incorrect API usage, caught in Phase 7.
```

## Scenario 3: Lead Compact Recovery During Phase 6

**Setup:** 2 implementers working. Lead's context compacts.

```
T+0:   impl-1 and impl-2 working normally
T+20:  COA-1 Sub-Workflow Table (in orchestration-plan.md):
       | impl-1 | Task 2/3 | implementing module B | 30% | 2min | current | 4 | ON_TRACK |
       | impl-2 | Task 1/2 | running self-tests | 80% | 1min | current | 3 | ON_TRACK |

T+21:  *** LEAD AUTO-COMPACT ***

T+22:  Lead recovers: reads orchestration-plan.md
       → Sees sub-workflow table from T+20 (last written state)
       → Knows: impl-1 was on Task 2/3 at 30%, impl-2 was on Task 1/2 at 80%

T+23:  Lead sends RV-1 to both implementers (post-recovery re-establishment):
       [REVERIFY] Phase 6 | Level 1 | Target: implementer-1 | Reason: Lead recovery
       [REVERIFY] Phase 6 | Level 1 | Target: implementer-2 | Reason: Lead recovery

T+24:  impl-1: [SELF-LOCATE] P6 | Task 2/3 | Step: implementing module B handlers | Progress: 45% | MCP: 5 | Docs: current
       impl-2: [SELF-LOCATE] P6 | Task 2/2 | Step: starting task 2 | Progress: 5% | MCP: 4 | Docs: current
       → Lead updates sub-workflow table with live data
       → Gap: impl-2 completed Task 1 and started Task 2 during compact (T+20 to T+24)
       → Mitigation: impl-2's L1/L2 (COA-3) contain Task 1 results. Lead reads L1 to catch up.

T+25:  Lead reads impl-2's L1-index.yaml → sees Task 1 completed with results
       → Sub-workflow fully re-established. Normal monitoring resumes.

RESULT: 3-minute recovery gap. Sub-workflow table + L1/L2 artifacts fill the gap.
Without COA: Lead would have no idea where implementers are after compact. Would need to send
ad-hoc queries to each, losing more time.
```

## Scenario 4: DIA Rejection 3x → Re-Spawn

**Setup:** implementer-1 fails Impact Analysis 3 times.

```
T+0:   implementer-1 spawned, receives [DIRECTIVE] + [INJECTION]
T+1:   [STATUS] Phase 6 | CONTEXT_RECEIVED | GC-v4
T+3:   [IMPACT-ANALYSIS] Phase 6 | Attempt 1/3
       → Lead reviews: RC-05 (interface signatures) FAIL, RC-07 (downstream chain) FAIL
       → [IMPACT_REJECTED] Attempt 1/3

T+5:   [IMPACT-ANALYSIS] Phase 6 | Attempt 2/3
       → Lead reviews: RC-05 fixed, RC-07 still FAIL
       → [IMPACT_REJECTED] Attempt 2/3

T+7:   [IMPACT-ANALYSIS] Phase 6 | Attempt 3/3
       → Lead reviews: RC-07 still shows incorrect understanding
       → [IMPACT_REJECTED] Attempt 3/3. ABORT.

T+8:   Lead shuts down implementer-1.
       → COA-1: Row removed from sub-workflow table (or marked TERMINATED)
       → COA-3: No L1/L2 to recover (failed at DIA, never started work)

T+9:   Lead re-spawns new implementer-1 with enhanced context (Gate S-3: Post-Failure Divergence)
       New directive includes: additional context about downstream chain, specific examples.

T+10:  New implementer-1: [STATUS] Phase 6 | CONTEXT_RECEIVED | GC-v4
T+12:  [IMPACT-ANALYSIS] Phase 6 | Attempt 1/3
       → RC-07 now shows correct understanding (enhanced context worked)
T+13:  [IMPACT_VERIFIED] Proceed.
T+15:  [PLAN] submitted → [APPROVED]
T+16:  [SELF-LOCATE] P6 | Task 1/3 | Step: reading source | Progress: 10% | MCP: 0 | Docs: missing
       → COA-1: New row in sub-workflow table. Fresh start.

RESULT: COA protocols handle the re-spawn seamlessly. Sub-workflow table tracks the replacement.
No COA-specific failure mode — standard DIA rejection + re-spawn works as designed.
```

## Scenario 5: Mid-Phase Scope Change

**Setup:** User adds rate limiting requirement during Phase 6.

```
T+0:   impl-1 working on Task 2/3 (auth module). Everything ON_TRACK.

T+15:  User: "Add rate limiting to auth endpoints"
       Lead bumps GC-v4 → GC-v5:
       ADDED §Scope: rate_limiting: "Rate limit all auth endpoints to 100 req/min"
       CHANGED §Phase_6: task_count: 3 → 4 (new task for rate limiter)

T+16:  Lead evaluates: which teammates affected?
       → impl-1: YES (working on auth module, directly affected)
       → impl-2: NO (working on unrelated module)
       Lead sends [CONTEXT-UPDATE] GC-v4 → GC-v5 to impl-1 only.

T+17:  impl-1: [ACK-UPDATE] GC-v5 received. Items: 2/2. Impact: rate limiting affects my auth handler directly. Action: PAUSE.

T+18:  COA-4 triggered (Scope Change → RV-2):
       Lead: [REVERIFY] Phase 6 | Level 2 | Target: implementer-1 | Reason: scope change (rate limiting) | Question: How does the rate limiting requirement change your implementation approach for the auth handler? Will you need additional files or interface changes?

T+19:  impl-1: [REVERIFY-RESPONSE] P6 | Level 2 | Rate limiting requires a new middleware file (src/auth/rate_limiter.py) and a config change (config/rate_limits.yaml). Auth handler interface needs a rate_config parameter. This is an interface change — other consumers of auth handler will need updates.

T+20:  Lead evaluates: interface change confirmed.
       → Updates task-context for impl-1 (expanded file ownership + new task)
       → Checks: does interface change affect impl-2? No — different module.
       → Lead: "Acknowledged. File ownership expanded. Submit revised [PLAN] for the updated scope."

T+21:  impl-1: [PLAN] Phase 6 | Files: src/auth/handler.py, src/auth/rate_limiter.py (NEW), config/rate_limits.yaml (NEW) | Changes: add rate limiter middleware, update handler interface | Risk: medium (interface change)
       Lead: [APPROVED] Proceed.

T+22:  impl-1: [SELF-LOCATE] P6 | Task 2/4 | Step: implementing rate limiter | Progress: 10% | MCP: 5 | Docs: current
       → COA-1: Updated row reflects new task count (4 instead of 3)

RESULT: Scope change smoothly integrated. COA-4 ensured comprehension of scope change impact.
COA-2 self-locate shows updated task count. COA-3 ensures pre-change work documented.
```

## Scenario 6: Skill Chaining (brainstorming → write-plan → validation → execution)

**Setup:** Full pipeline across 4 skill invocations.

```
SKILL 1: /brainstorming-pipeline
  Phase 1: Lead only (no COA active)
  Phase 2: researcher-1 spawned
    COA-2: [SELF-LOCATE] messages track research progress
    COA-1: 1-row sub-workflow table in orchestration-plan.md
    COA-3: researcher writes L1/L2 at milestones (Docs: current in SL)
    COA-5: tavily + context7 usage tracked (MCP: count in SL)
    COA-4: not triggered (no anomalies)
    Gate 2: sub-workflow ON_TRACK ✓, L1/L2/L3 exist ✓, MCP reported ✓
  Phase 3: architect-1 spawned
    COA-2: [SELF-LOCATE] at design milestones
    COA-1: 1-row sub-workflow
    COA-3: architect writes L1/L2 at component boundaries
    COA-5: tavily Required → tracked in MCP field
    COA-4: not triggered
    Gate 3: APPROVED
  Clean Termination: shutdown + TeamDelete
  Output: GC-v3 + architecture artifacts

SKILL 2: /agent-teams-write-plan
  Phase 4: architect-1 spawned (new team)
    COA-2: [SELF-LOCATE] at plan section completion points
    COA-1: 1-row sub-workflow
    COA-3: architect writes L1/L2 as plan sections completed
    COA-5: tavily + context7 Required → tracked
    COA-4: not triggered
    Gate 4: APPROVED
  Clean Termination: shutdown + TeamDelete
  Output: GC-v4 + implementation plan

SKILL 3: /plan-validation-pipeline
  Phase 5: devils-advocate-1 spawned (TIER 0 exempt)
    COA-2: start + completion only (minimal frequency)
    COA-1: 1-row sub-workflow (mostly ON_TRACK, short execution)
    COA-3: devils-advocate writes L1/L2 (challenge findings)
    COA-5: As needed phase — EXEMPT from MCP minimum
    COA-4: not triggered (TIER 0 exempt from re-verification)
    Gate 5: Verdict CONDITIONAL_PASS → user accepts mitigations
  Clean Termination: shutdown + TeamDelete
  Output: GC-v4 (no bump if PASS) or GC-v5 (if mitigations added)

SKILL 4: /agent-teams-execution-plan
  Phase 6: impl-1, impl-2 spawned (2 independent components)
    COA-2: [SELF-LOCATE] at task boundaries + milestones (most active phase)
    COA-1: 2-row sub-workflow table — parallel progress tracking
    COA-3: both write L1/L2 at task boundaries, triggered by SL checkpoints
    COA-5: context7 Required → impl-1: MCP=4 (healthy), impl-2: MCP=0 at 60% → RV-2 triggered
    COA-4: impl-2 MCP gap detected → RV-2 → resolved (impl-2 uses context7)
    Gate 6: per-task + cross-task evaluation, sub-workflow all ON_TRACK
  Clean Termination: shutdown + TeamDelete
  Output: GC-v5 + implemented code

CROSS-SKILL COA CONTINUITY:
- Each skill creates a fresh team → fresh sub-workflow table (COA-1)
- GC version carries across skills (v1→v3→v4→v5)
- L3-full/ from each skill feeds next skill's input
- COA protocols restart per skill (fresh self-location sequence)
- No COA state crosses team boundaries — each team is independent
```

## Summary: COA Protocols Per Scenario

| Scenario | COA-2 (SL) | COA-1 (SW) | COA-3 (Doc) | COA-4 (RV) | COA-5 (MCP) |
|----------|-----------|-----------|------------|-----------|------------|
| 1. Happy Path | 15 SLs | 1-row table | Checkpoints met | Not triggered | Healthy |
| 2. Multi-Impl | 20+ SLs | 3-row table | 1 stale caught | RV-1 + RV-2 | Gap caught at 55% |
| 3. Compact Recovery | Recovery SLs | Table rebuilt | L1/L2 fill gap | RV-1 post-recovery | Counts preserved in L2 |
| 4. DIA Rejection | Fresh start SLs | Row replaced | No L1/L2 (pre-work) | Not applicable | Fresh count |
| 5. Scope Change | Updated counts | Updated row | Pre-change save | RV-2 scope check | May trigger new research |
| 6. Skill Chain | Per-skill SLs | Per-skill tables | Cross-skill L3 | Per-skill scope | Phase-based Required |

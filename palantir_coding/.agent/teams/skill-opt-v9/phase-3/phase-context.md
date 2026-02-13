# Phase 3 Context — Skill Optimization v9.0

## Feature
9 skills + related agents deep redesign for INFRA v9.0 alignment.
Context:fork revolution for 4 Lead-only skills.
20+ files, Big Bang simultaneous change. COMPLEX tier.

## Architecture Scope (6 items)
1. **2 skill template variants:** Coordinator-based (5 Pipeline Core) + Fork-based (4 Lead-Only+RSIL)
2. **PT-centric interface contract:** per-skill read/write sections, GC scratch-only role
3. **3 fork agent .md designs:** pt-manager, delivery-agent, rsil-agent (tools, permissions, memory)
4. **CLAUDE.md §10 modification:** "Lead-delegated fork agents" exception rule
5. **Coordinator .md convergence:** Template B pattern, frontmatter completion, protocol references
6. **Per-skill delta from template:** unique orchestration logic per skill

## Key Research Findings (117 evidence points)
- 18.3% extractable duplication (808L of 4,426L): 358L IDENTICAL + 450L SIMILAR
- 3 skill families: Pipeline Core (5), Lead-Only (2), RSIL (2)
- Top extraction: Phase 0 PT Check (~210L), Input Discovery (~140L)
- 60-80% of each skill is unique orchestration logic
- GC 14→3 sections: 2 migrate PT + 9 eliminate via L2 Downstream Handoff + 3 keep
- Fork: all 4 FEASIBLE (rsil-global LOW → rsil-review MED → permanent-tasks MED-HIGH → delivery HIGH)
- Task API: frontmatter-enforced, not platform-level (D-12)
- Custom agents in fork FEASIBLE (D-15, CC research confirmed)
- Two-Template Problem: 5 verbose (93L avg) vs 3 lean (39L avg), 175L duplication
- 25 frontmatter gaps across 8 coordinators

## Decisions (D-1~D-15)
D-1: Exclude palantir-dev | D-2: All Deep Redesign | D-3: A+B only (Spawn+Prompt)
D-4: No compression target (YAGNI) | D-5: Common 1x CC research | D-6: Precision Refocus 4-section
D-7: PT-centric interface (GC→session scratch) | D-8: Big Bang | D-9: 4 skills→context:fork
D-10: CLAUDE.md §10 modification | D-11: 3 new fork agent .md
D-12: Task API frontmatter-enforced | D-13: Template B convergence
D-14: GC 14→3 reduction | D-15: Custom agents in fork FEASIBLE

## Risks to Address
- RISK-2 (MED-HIGH): permanent-tasks fork loses conversation history
- RISK-3 (MED): delivery-pipeline fork complexity (5+ user gates, git ops)
- RISK-4 (LOW): Skills preload token cost (400-600L) — unfavorable ratio

## Open Questions
1. Can fork agent spawn subagents via Task tool? (blocks rsil-review fork)
2. Should RSIL skills share one rsil-agent or have separate agents?
3. Skills preload for coordinators: adopt or defer?
4. Template design: 2 variants or 3 (coordinator + fork-simple + fork-complex)?
5. GC elimination timeline: Phase N Entry Requirements removed in v9.0 or phased?

## Constraints
- YAGNI only (no compression target)
- Big Bang (simultaneous, interface consistency)
- BUG-001: mode "default" always
- Worker agent .md files NOT in scope
- Fork agents start clean — no conversation history inheritance

## Key Reference Files
- Design file: docs/plans/2026-02-12-skill-optimization-v9-design.md (11 P1 decisions, CC research §9)
- Phase 2 consolidated: .agent/teams/skill-opt-v9/phase-2/research-coord/L2-summary.md
- Fork analysis: .agent/teams/skill-opt-v9/phase-2/codebase-researcher-2/L2-summary.md
- Coordinator audit: .agent/teams/skill-opt-v9/phase-2/auditor-1/L2-summary.md
- Duplication analysis: .agent/teams/skill-opt-v9/phase-2/codebase-researcher-1/L2-summary.md
- 9 skill files: .claude/skills/*/SKILL.md
- 8 coordinator agents: .claude/agents/*-coordinator.md
- CLAUDE.md §10: .claude/CLAUDE.md
- agent-common-protocol.md: .claude/references/agent-common-protocol.md

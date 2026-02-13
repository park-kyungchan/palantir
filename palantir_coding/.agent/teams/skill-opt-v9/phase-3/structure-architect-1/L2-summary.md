# L2 Summary — Structural Design (Items 1, 5, 6)

## Summary

Designed 2 skill template variants (coordinator-based for 5 Pipeline Core skills, fork-based for 4 Lead-Only+RSIL skills), a unified coordinator .md template converging all 8 coordinators to Template B pattern (768L→402L, -48%), and per-skill delta analysis mapping each of 9 skills to its template with unique/shared/new section classification. 8 structural ADRs produced. Key finding: template extraction yields ~18% structural consistency but 60-80% of each skill is genuinely unique orchestration logic that cannot be templated.

## Template Variant Design (Item 1)

### Coordinator-Based Template (5 Pipeline Core Skills)

Structural skeleton with 4 D-6 sections plus shared prologue:
- **Prologue:** Frontmatter → Title → Announce → When to Use → Dynamic Context
- **A) Spawn:** Phase 0 PT Check (IDENTICAL template) → Input Discovery (SIMILAR) → Team Setup (IDENTICAL) → Tier-Based Routing (SIMILAR) → Spawn Parameters (SIMILAR) → Directive Construction (UNIQUE) → Understanding Verification (SIMILAR)
- **B) Core Workflow:** Entirely UNIQUE per skill (60-80% of content)
- **C) Interface:** NEW section — Input (PT + predecessor L2) → Output (PT update + L1/L2/L3) → Next
- **D) Cross-Cutting:** RTD (IDENTICAL) + Error Handling (SIMILAR) + Clean Termination (SIMILAR) + Key Principles (SIMILAR) + Never (SIMILAR)

Consumer: Lead (reads skill, orchestrates teammates). Voice: third person.

### Fork-Based Template (4 Lead-Only+RSIL Skills)

Simplified skeleton — no spawn/team/gate sections:
- **Prologue:** Frontmatter (+ `context: fork`, `agent: "{name}"`) → Title → Announce → When to Use → Dynamic Context
- **Phase 0:** PT Check (IDENTICAL template, fork agent executes)
- **Core Workflow:** Entirely UNIQUE per skill (72-75% of content)
- **Interface:** Input ($ARGUMENTS + Dynamic Context + PT) → Output (file artifacts + terminal summary)
- **Cross-Cutting:** Error Handling + Key Principles + Never

Consumer: Fork agent (skill body IS operating instruction). Voice: second person.

**ADR-S1:** 2 templates, not 3 — fork complexity varies in content, not structure.

## Coordinator .md Convergence (Item 5)

Unified template: Template B pattern (reference protocols, retain only unique logic).

**Frontmatter unified (fills 25 gaps):**
- `memory: project` for all 8 (was: "user" for 5, missing for 3)
- `color:` assigned to 3 missing (arch=purple, plan=orange, valid=yellow)
- `disallowedTools:` 4-item for all 8 (+Edit +Bash for 3 lean coordinators)
- `skills:`, `hooks:`, `mcpServers:` all DEFERRED (YAGNI)

**Body unified (5 sections):**
1. Role (unique) — 2 protocol references at top
2. Before Starting Work (unique)
3. How to Work (unique, 0-45L depending on coordinator)
4. Output Format (unique schema notes)
5. Constraints (unique additions to base)

**Reduction:** 768L → 402L (-48%, -366L). Execution-coordinator retains longest "How to Work" (~45L) for two-stage review dispatch unique logic.

**ADR-S3:** memory: project for all. **ADR-S4:** skills preload DEFERRED.

## Per-Skill Delta (Item 6)

| Skill | Template | Unique % | Template-as-is % | New % |
|-------|:--------:|:--------:|:-----------------:|:-----:|
| brainstorming-pipeline | Coordinator | 65% | 15% | 20% |
| agent-teams-write-plan | Coordinator | 61% | 24% | 16% |
| plan-validation-pipeline | Coordinator | 64% | 20% | 15% |
| agent-teams-execution-plan | Coordinator | 69% | 12% | 18% |
| verification-pipeline | Coordinator | 64% | 16% | 20% |
| delivery-pipeline | Fork | 74% | 11% | 15% |
| rsil-global | Fork | 75% | 10% | 15% |
| rsil-review | Fork | 73% | 8% | 19% |
| permanent-tasks | Fork | 72% | 13% | 16% |

All 9 skills get a NEW Interface Section (C) per D-7 PT-centric interface.
Fork skills: no Team Setup, no Spawn, no Understanding Verification, no Gate Evaluation, no RTD.
See L3-full/structure-design.md §6.2-6.3 for complete per-skill section inventory.

## Structural ADRs

| ID | Decision | Rationale |
|----|----------|-----------|
| ADR-S1 | 2 templates, not 3 | Fork complexity varies in content, not structure |
| ADR-S2 | Template B convergence, execution-coordinator extended | 45L unique logic justified |
| ADR-S3 | memory: project for all 8 coordinators | Project-scoped learning |
| ADR-S4 | Skills preload DEFERRED | Token cost unfavorable; Dynamic Context better |
| ADR-S5 | Shared rsil-agent for both RSIL skills | Same tools; skill body differentiates |
| ADR-S6 | Interface Section (C) is NEW for all 9 skills | D-7 needs structural home |
| ADR-S7 | Phase 0 stays in fork skills | Fork agent needs PT context |
| ADR-S8 | Cross-Cutting 1-liners for coordinator-based only | Fork keeps inline |

## PT Goal Linkage

| PT Decision | Structural Design | Status |
|-------------|-------------------|--------|
| D-6 (Precision Refocus) | 4-section structure implemented in both templates | DESIGNED |
| D-7 (PT-centric Interface) | New Interface Section (C) for all 9 skills | DESIGNED |
| D-8 (Big Bang) | All 9 + 8 + 3 + CLAUDE.md simultaneously | CONSTRAINT NOTED |
| D-9 (4 skills → fork) | Fork-based template with `context: fork` + `agent:` | DESIGNED |
| D-11 (3 new agent .md) | Agent mapping: pt-manager, delivery-agent, rsil-agent | MAPPED |
| D-13 (Template B convergence) | Unified coordinator template, 768L→402L | DESIGNED |

## Evidence Sources

| Source | Count | Key Evidence |
|--------|:-----:|-------------|
| P2 research outputs (4 L2 files) | 117 points | Duplication matrix, fork feasibility, coordinator audit |
| Skill files read | 5 of 9 | brainstorming, write-plan, delivery, rsil-global, permanent-tasks |
| Coordinator agents read | 3 of 8 | execution (Template A), architecture (Template B), research (Template A) |
| Protocol files read | 3 | agent-common-protocol, coordinator-shared-protocol, ontological-lenses |
| Design doc | 1 | §3 Precision Refocus, §9 CC Research — frontmatter fields, fork mechanism |
| Phase 3 context | 1 | Scope, decisions, constraints, open questions |

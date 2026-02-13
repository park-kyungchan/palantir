# L2 Summary — Phase 2 Research Consolidated Report

## Summary

Phase 2 research across 4 domains (3 workers) is complete with 117 evidence points. Key findings: 18.3% extractable duplication across 9 skills (808L), dual PT/GC state machine with clear migration path, all 4 Lead-only skills feasible for context:fork with varying risk, and 25 frontmatter gaps + 175L protocol duplication across 8 coordinator .md files. The most impactful cross-domain discovery is that Task API restriction is frontmatter-enforced (not platform-level), making D-10 feasible without CC platform changes. Skills naturally cluster into 3 structural families (Pipeline Core, Lead-Only, RSIL) that map to different template and isolation strategies.

## Domain 1: Skill Duplication Analysis (codebase-researcher-1)

**18.3% extractable duplication** (808L of 4,426L total):
- IDENTICAL (358L, 8.1%): Phase 0 PT Check (~210L across 7 skills), RTD Index (~72L), Team Setup (~25L), Sequential Thinking (~27L), Announce (~9L)
- SIMILAR (450L, 10.2%): Input Discovery (~140L), Clean Termination (~75L), Error Handling (~54L), Gate structure (~40L), Key Principles (~36L)
- 60-80% of each skill is unique orchestration logic — cannot be templated

**3 Skill Families** (structural similarity clustering):
1. **Pipeline Core** (5 skills: brainstorming, write-plan, validation, execution, verification) — share 15 of 19 section types, highest mutual duplication, coordinator-based
2. **Lead-Only** (2 skills: delivery, permanent-tasks) — no spawn/team patterns, fork candidates
3. **RSIL** (2 skills: rsil-global, rsil-review) — share Phase 0 + cross-cutting only, unique lens/tier logic, fork candidates

Full duplication matrix with section presence heatmap: `phase-2/codebase-researcher-1/L2-summary.md`

## Domain 2: GC Interface Mapping (codebase-researcher-1)

**Dual State Machine:**
- GC: session-level, version chain v1→v7, written by 5 pipeline skills at gate transitions
- PT: project-level, version chain v1→vFinal, written by 5 skills (permanent-tasks, brainstorming, write-plan, execution, delivery)
- 3 skills never touch GC: rsil-global, rsil-review, permanent-tasks (clean fork candidates)

**PT↔GC Overlap:** 6 data categories overlap, PT authoritative for 5 of 6

**Migration Path (D-7):**
- **2 migrate to PT:** Codebase Constraints → PT §Constraints, Interface Changes → PT §Impact Map
- **9 eliminate:** Phase N Entry Requirements → replaced by L2 Downstream Handoff mechanism
- **5 keep in GC:** Execution metrics, GC version marker — too verbose or session-specific for PT

Full GC flow diagram and dependency map: `phase-2/codebase-researcher-1/L2-summary.md`

## Domain 3: context:fork Prototype (codebase-researcher-2)

**Fork Mechanism:** Exists in CC, documented in skills-reference.md. Fork agent starts clean (no conversation history), receives rendered Dynamic Context + $ARGUMENTS + agent .md body.

**CRITICAL FINDING: Task API is frontmatter-enforced, not platform-level.** All 43 agents have `disallowedTools: [TaskCreate, TaskUpdate]`. Creating new agent .md WITHOUT these restrictions grants full Task API. This is the D-10 exception mechanism — no CC platform change needed.

**Per-Skill Fork Feasibility:**

| Skill | Risk | Verdict | Key Blocker |
|-------|------|---------|-------------|
| rsil-global | LOW | HIGHLY FEASIBLE | Rare Tier 3 agent spawning |
| rsil-review | MEDIUM | FEASIBLE | Spawns 2 parallel agents from fork |
| permanent-tasks | MEDIUM-HIGH | FEASIBLE WITH DEGRADATION | Conversation history loss |
| delivery-pipeline | HIGH | FEASIBLE BUT COMPLEX | 5+ user gates, git ops, nested skills |

**3 New Agent .md Files (D-11):**
- `pt-manager`: full Task API (Create+Update), AskUserQuestion
- `delivery-agent`: TaskUpdate, Bash (git), Edit, AskUserQuestion
- `rsil-agent`: TaskUpdate, Task (agent spawning), Edit, AskUserQuestion (shared by both RSIL skills)

**6 Critical Unknowns (require CC research):**
1. Can `agent:` field reference custom `.claude/agents/{name}.md`? (prerequisite for D-11)
2. Can fork agent spawn subagents via Task tool?
3. Which task list does fork agent see?
4. Nested skill invocation behavior from fork?
5. Fork return model (full output or summary)?
6. Fork lifecycle (terminate or persist)?

Full per-skill analysis and D-10 modification design: `phase-2/codebase-researcher-2/L2-summary.md`

## Domain 4: Coordinator Agent .md Audit (auditor-1)

**25 frontmatter field gaps** across 8 coordinators (96 data points):
- 0/8 have `skills:` preload, 0/8 have agent-scoped `hooks:`
- 3 missing `memory:`, `color:`, incomplete `disallowedTools:` (architecture, planning, validation)

**Two-Template Problem (CRITICAL):**
- Template A (5 coordinators: research, verification, execution, testing, infra-quality): avg 93L body, inlines shared protocol, does NOT reference coordinator-shared-protocol.md — 175L total duplication
- Template B (3 coordinators: architecture, planning, validation): avg 39L body, properly references both shared protocols
- Convergence target: Template B pattern (reference protocols, retain only unique logic)

**8 Optimization Targets:** Template Unification (CRITICAL), Frontmatter Completion (HIGH), Protocol Reference Fix (HIGH), Skills Preload Evaluation (HIGH, design decision), plus 4 lower-priority items

Full frontmatter matrix, body content analysis, and per-coordinator detail: `phase-2/auditor-1/L2-summary.md`

## Cross-Domain Synthesis

4 key cross-domain connections discovered:

1. **Skill families ↔ Fork strategy (D1↔D3):** The 3 skill families map directly to isolation strategies. Pipeline Core (5) = coordinator-based, stay in Lead context. Lead-Only (2) + RSIL (2) = fork candidates. The fork candidates are exactly the 3 GC non-users (D2↔D3), making the PT-centric migration cleaner — no GC state to migrate for fork skills.

2. **Duplication symmetry (D1↔D4):** The Two-Template Problem in coordinator .md files mirrors the duplication problem in skills. Both stem from the same root cause: inconsistent use of shared protocol references. The fix is the same: reference shared protocols, retain only unique content.

3. **Template variant design (D1+D3+D4):** Phase 3 needs to design at least 2 skill template variants:
   - **Coordinator-based template** (5 Pipeline Core skills): Spawn section with coordinator + worker pre-spawn, Directive section with PT + L2 references, Interface with GC + PT read/write
   - **Fork-based template** (4 Lead-Only + RSIL skills): Fork frontmatter (`context: fork`, `agent:`), Directive section with $ARGUMENTS + Dynamic Context, Interface with PT-only (no GC)

4. **GC elimination path (D2+D1):** 9 of 14 GC-only sections are "Phase N Entry Requirements" consumed once by the next phase. These can be replaced by the L2 Downstream Handoff mechanism already in agent-common-protocol.md. Combined with 2 PT migrations, this reduces GC from 14 unique section types to 3 (execution metrics, gate records, version marker).

## PT Goal Linkage

| PT Decision | Research Finding | Status |
|-------------|-----------------|--------|
| D-6 (Precision Refocus) | 808L skill dedup + 175L coordinator dedup = 983L total addressable | DATA READY |
| D-7 (PT-centric Interface) | 2 migrate + 9 eliminate + 3 keep → GC reduced from 14 to 3 section types | DATA READY |
| D-9 (4 skills → fork) | All 4 feasible: LOW → MEDIUM → MEDIUM-HIGH → HIGH risk | VALIDATED |
| D-10 (CLAUDE.md §10) | Frontmatter-enforced, not platform-level; modification path clear | VALIDATED |
| D-11 (3 new fork agents) | pt-manager, delivery-agent, rsil-agent — tool requirements mapped | DESIGN INPUT READY |
| D-13 (Coordinator Protocol) | 5/8 missing reference → 175L removable duplication | DATA READY |

## Evidence Sources

| Source Category | Count | Key Sources |
|----------------|-------|-------------|
| Skill files read | 9 | All SKILL.md files (4,426L total) |
| Agent .md files read | 51 | 8 coordinators + 43 agents for disallowedTools audit |
| Protocol files | 2 | agent-common-protocol.md, coordinator-shared-protocol.md |
| CC documentation | 3 | skills-reference.md, sub-agents.md, design doc §9 |
| Configuration files | 1 | settings.json |
| **Total evidence points** | **117** | Across 3 workers |

## Downstream Handoff

### Decisions Made (forward-binding)
- 3 skill families identified: Pipeline Core (5), Lead-Only (2), RSIL (2) — template design must account for all 3
- Task API restriction is frontmatter-enforced — D-10 needs NL modification only (CLAUDE.md §10 + agent-common-protocol.md), no platform change
- Template B (lean, protocol-referencing) is the convergence target for coordinator .md files
- GC reduction path: 14 section types → 3 (via 2 PT migrations + 9 L2 Downstream Handoff eliminations)

### Risks Identified (must-track)
- **RISK-1 (HIGH):** 6 critical unknowns about fork mechanism remain — custom agent resolution (#1) is a prerequisite for D-11. If `agent:` only supports built-in types, fork-agent architecture needs complete redesign. **Recommend: CC research in Phase 3 before architecture decisions.** **Fallback architecture identified:** use `agent: general-purpose` + `allowed-tools` in skill frontmatter to carry tool restrictions, with all agent instructions in skill body. Loses agent .md separation but functionally works (70% confidence custom resolution works; fallback available if not).
- **RISK-2 (MEDIUM-HIGH):** permanent-tasks fork loses conversation history — degraded experience for manual (non-pipeline) invocation. Fallback: stay Lead-in-context with lightweight GC scratch.
- **RISK-3 (MEDIUM):** delivery-pipeline fork is complex (5+ user gates, git ops, nested skills) — may need phased adoption (fork last, validate simpler skills first).
- **RISK-4 (LOW):** Skills preload token cost (400-600L per skill) vs. phase awareness benefit — unfavorable ratio. Dynamic Context Injection is the better alternative.

### Interface Contracts (must-satisfy)
- Skill template must produce: L1-index.yaml, L2-summary.md with Downstream Handoff, L3-full/ directory
- Fork skills interface via: $ARGUMENTS (primary input), Dynamic Context (session state), PT (cross-phase state)
- Coordinator-based skills interface via: PT (authoritative), predecessor L2 (phase handoff), GC (session scratch only)

### Constraints (must-enforce)
- 60-80% of each skill is unique orchestration logic — template extraction limited to ~18% shared sections
- Big Bang approach (D-8) requires all 9 skills + 8 coordinator .md + 3 new agent .md changed simultaneously
- BUG-001: mode "default" always (no plan mode for fork agents either)
- Fork agents start clean — no conversation history inheritance

### Open Questions (requires resolution)
1. Can `agent:` field reference custom `.claude/agents/{name}.md`? (blocks D-11 design)
2. Can fork agent spawn subagents via Task tool? (blocks rsil-review fork)
3. Should RSIL skills share one `rsil-agent` or have separate agents?
4. Skills preload for coordinators: adopt or defer? (token cost vs. awareness trade-off)
5. Template design: 2 variants (coordinator + fork) or 3 (coordinator + fork-simple + fork-complex)?
6. GC elimination timeline: can Phase N Entry Requirements be removed in v9.0 or phased?

### Artifacts Produced
- `phase-2/codebase-researcher-1/L1-index.yaml` — Duplication + GC quantification
- `phase-2/codebase-researcher-1/L2-summary.md` — Full analysis with heatmap + flow diagrams
- `phase-2/codebase-researcher-1/L3-full/domain1-duplication-analysis.md` — Raw duplication matrix
- `phase-2/codebase-researcher-1/L3-full/domain2-gc-interface-mapping.md` — GC/PT dependency map
- `phase-2/codebase-researcher-2/L1-index.yaml` — Fork feasibility verdicts
- `phase-2/codebase-researcher-2/L2-summary.md` — Full fork analysis + D-10/D-11 design
- `phase-2/codebase-researcher-2/L3-full/fork-mechanism-analysis.md` — Detailed mechanism report
- `phase-2/auditor-1/L1-index.yaml` — Coordinator frontmatter matrix
- `phase-2/auditor-1/L2-summary.md` — Full audit + optimization targets
- `phase-2/auditor-1/L3-full/` — 3 raw data files (frontmatter, body content, optimization targets)
- `phase-2/research-coord/L1-index.yaml` — Consolidated index (this file's companion)
- `phase-2/research-coord/L2-summary.md` — This file
- `phase-2/research-coord/progress-state.yaml` — Coordinator recovery state

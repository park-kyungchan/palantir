# Phase 4 Context — Skill Optimization v9.0 (Detailed Design)

## PERMANENT Task
- **Task ID:** #1
- **Version:** PT-v2
- **Action:** All planners must call `TaskGet(1)` before starting work

## Phase 4 Objective
Transform Phase 3 architecture (149 evidence, 30 decisions, 5 contracts) into a concrete
10-section implementation plan with file-level task decomposition, interface specs, and
execution strategy for Big Bang atomic commit of 22+ files.

## Architecture Input Summary

### 2 Template Variants (ADR-S1)
- **Coordinator-based** (5 skills: brainstorming, write-plan, validation, execution, verification):
  Prologue + A)Spawn + B)Core Workflow + C)Interface + D)Cross-Cutting. Consumer: Lead.
- **Fork-based** (4 skills: delivery, permanent-tasks, rsil-global, rsil-review):
  Prologue (context:fork, agent:) + Phase 0 + Core Workflow + Interface + Cross-Cutting. Consumer: Fork agent.

### PT-Centric Interface (C-1~C-5)
- C-1: PT Read/Write (N:1) — all 9 skills share one PT via TaskGet/TaskUpdate
- C-2: L2 Downstream Handoff chain — replaces 9 GC sections
- C-3: GC scratch-only (3 concerns: metrics, gate records, version)
- C-4: Fork-to-PT Direct (TaskGet/TaskUpdate from fork, depends on RISK-8)
- C-5: §10 Exception (3 named agents, 3-layer enforcement)

### 3 Fork Agent .md (D-11)
- pt-manager: TaskCreate+Update, maxTurns 30, 3-layer history mitigation
- delivery-agent: TaskUpdate only, maxTurns 50, no nested skills, 6 user gates
- rsil-agent (shared): TaskUpdate+Task, maxTurns 50, skill body differentiates

### Coordinator Convergence (D-13)
- Template B: 768→402L (-48%), 5-section body, unified frontmatter
- memory: project (all 8), disallowedTools: 4-item (all 8)
- execution-coordinator retains 45L unique review dispatch logic

### CLAUDE.md §10 Modification (C-5)
- Add exception clause for 3 named fork agents
- 3-layer enforcement: frontmatter → agent .md NL → CLAUDE.md
- agent-common-protocol.md §Task API also updated

### Per-Skill Delta
| Skill | Template | Unique | Shared | New |
|-------|:--------:|:------:|:------:|:---:|
| brainstorming-pipeline | Coord | 65% | 15% | 20% |
| agent-teams-write-plan | Coord | 61% | 24% | 16% |
| plan-validation-pipeline | Coord | 64% | 20% | 15% |
| agent-teams-execution-plan | Coord | 69% | 12% | 18% |
| verification-pipeline | Coord | 64% | 16% | 20% |
| delivery-pipeline | Fork | 74% | 11% | 15% |
| rsil-global | Fork | 75% | 10% | 15% |
| rsil-review | Fork | 73% | 8% | 19% |
| permanent-tasks | Fork | 72% | 13% | 16% |

## Impact Map Excerpt (Phase 4-Relevant)

### File Categories (22+ files)
1. **9 SKILL.md** — `.claude/skills/{name}/SKILL.md`
2. **8 Coordinator .md** — `.claude/agents/{name}.md`
3. **3 Fork Agent .md (NEW)** — `.claude/agents/{pt-manager,delivery-agent,rsil-agent}.md`
4. **1 CLAUDE.md** — §10 modification
5. **1 agent-common-protocol.md** — §Task API fork exception

### Dependency Order for Planning
1. Template design (shared skeleton) → per-skill customization
2. Interface contracts (C-1~C-5) → skill Interface Section content
3. Fork agent .md specs → fork skill Prologue content
4. Coordinator Template B → coordinator .md file specs
5. §10 modification → enforcement verification

### Cross-File Dependencies
- Skill §A (Spawn) references agent .md (subagent_type must match)
- Skill §C (Interface) references PT schema and L2 Handoff chain
- Coordinator .md references coordinator-shared-protocol.md
- Fork skill references fork agent .md (agent: field)
- §10 exception must name exactly 3 agents matching fork agent .md filenames

## Constraints (Must-Enforce)
- Big Bang: all 22+ files committed atomically (D-8)
- YAGNI: no speculative features (D-4)
- 60-80% unique per skill — template is structural guidance, not dedup
- BUG-001: mode "default" always in all skill spawn examples
- Fork agents start clean — no conversation history
- Pre-deploy validation A→B→C→D CRITICAL before production commit
- Worker agent .md files NOT in scope (coordinators only)

## Active Risks (Must-Track)
| ID | Sev | Risk | Mitigation |
|----|-----|------|------------|
| RISK-2 | MED-HIGH | PT fork history loss | 3-layer mitigation in pt-manager |
| RISK-3 | MEDIUM | Delivery fork complexity | Fork last, no nested skills |
| RISK-5 | HIGH | Big Bang 22+ files | YAML validation, atomic commit, rollback |
| RISK-8 | MEDIUM | Task list scope in fork | Pre-deploy validation + $ARGUMENTS fallback |

## Key Reference Files
- arch-coord L2: `.agent/teams/skill-opt-v9/phase-3/arch-coord/L2-summary.md` (221L)
- structure-architect L3: `.agent/teams/skill-opt-v9/phase-3/structure-architect-1/L3-full/structure-design.md` (754L)
- interface-architect L3: `.agent/teams/skill-opt-v9/phase-3/interface-architect-1/L3-full/interface-design.md` (412L)
- risk-architect L3: `.agent/teams/skill-opt-v9/phase-3/risk-architect-1/L3-full/risk-design.md` (662L)
- CH-001 exemplar: `docs/plans/2026-02-07-ch001-ldap-implementation.md` (10-section format reference)

## Planner Work Distribution
- **decomposition-planner:** Task breakdown (§1-§4), file ownership (§3), per-skill specs (§5)
- **interface-planner:** Interface contracts (§C in each skill), cross-file dependencies, PT schema specs
- **strategy-planner:** Execution sequence (§6), risk mitigation (§8), rollback strategy, pre-deploy validation

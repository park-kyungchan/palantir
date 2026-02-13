# L2 Summary — Phase 3 Architecture Consolidated Report

## Summary

Phase 3 architecture is complete across 3 workers (structure, interface, risk) producing a unified design for the Skill Optimization v9.0 feature. The architecture defines: 2 skill template variants (coordinator-based for 5 Pipeline Core skills + fork-based for 4 Lead-Only/RSIL skills), a PT-centric interface contract replacing GC as the cross-phase state bus (14→3 GC sections), 3 fork agent .md designs (pt-manager, delivery-agent, rsil-agent), CLAUDE.md §10 modification with 3-layer enforcement, coordinator .md convergence to Template B (768→402L, -48%), and a 9-item risk register with phased validation strategy. 149 total evidence points. 1 cross-lens conflict resolved (pt-manager SendMessage removed).

## Unified Architecture Design

### 1. Two Skill Template Variants (ADR-S1)

**Coordinator-based** (5 Pipeline Core: brainstorming, write-plan, validation, execution, verification):
- Prologue + A)Spawn + B)Core Workflow + C)Interface + D)Cross-Cutting
- Consumer: Lead (reads skill, orchestrates teammates). Voice: third person.
- Spawn section: Phase 0 PT Check (IDENTICAL template) → Input Discovery (SIMILAR) → Team Setup (IDENTICAL) → Tier-Based Routing (SIMILAR) → Spawn Parameters → Directive Construction (UNIQUE) → Understanding Verification
- Interface: PT-v{N} + predecessor L2 → PT-v{N+1} + own L2 + GC scratch
- Cross-cutting: 1-line references to CLAUDE.md sections

**Fork-based** (4 Lead-Only/RSIL: delivery, permanent-tasks, rsil-global, rsil-review):
- Prologue (`context: fork`, `agent:`) + Phase 0 + Core Workflow + Interface + Cross-Cutting
- Consumer: Fork agent (skill body IS operating instruction). Voice: second person.
- No spawn/team/gate/RTD sections. Fork IS the spawn.
- Interface: $ARGUMENTS + Dynamic Context + PT via TaskGet → file artifacts + terminal summary
- Cross-cutting: INLINE error handling and principles (ADR-S8: no CLAUDE.md 1-liners)

**Per-skill uniqueness:** 61-75% unique orchestration logic across all 9 skills. Template covers ~18% shared skeleton. Section Classification heatmap in structure-architect L3 §6.4.

### 2. PT-Centric Interface Contract (D-7)

**PT = sole cross-phase source of truth.** All 9 skills read PT for context, write PT with results.

Per-skill contract table: interface-architect L3 §1.2 (complete read/write mapping for all 9 skills).

**PT schema (lean pointers per D-012):**
- `phase_status.P{N}.l2_path` → discovery mechanism for predecessor L2
- `implementation_plan.l3_path`, `implementation_results.l3_path` → bulk data in L3
- PT holds 1-2 sentence summaries + paths, not full data

**GC reduction (D-14): 14→3 final steady-state.**
- 9 ELIMINATE: Phase N Entry Requirements → L2 Downstream Handoff
- 2 MIGRATE to PT: Codebase Constraints (Gate 2), Interface Changes (Gate 6)
- 3 KEEP as scratch: execution metrics, gate records, version marker

**Skill discovery protocol change:**
- Before: GC version scan ("Phase N: COMPLETE")
- After: TaskGet PT → `phase_status.P{N}.l2_path` → read predecessor L2 §Downstream Handoff

### 3. Three Fork Agent .md Designs (D-11)

| Agent | Skill(s) | Task API | maxTurns | Key Design |
|-------|----------|----------|:--------:|------------|
| pt-manager | permanent-tasks | TaskCreate + TaskUpdate | 30 | 3-layer history loss mitigation, AskUserQuestion for missing context |
| delivery-agent | delivery-pipeline | TaskUpdate only | 50 | No nested skill invocation, 6 user confirmation gates, idempotent ops |
| rsil-agent | rsil-global + rsil-review (shared) | TaskUpdate + Task (spawning) | 50 | Shared agent, skill body differentiates behavior, 85% spawning confidence |

**Cross-lens conflict resolved (CLC-1):** SendMessage REMOVED from pt-manager. Fork agents have no team context (interface-architect C-4, structure-architect fork template). Lead relays CRITICAL PT change notifications manually. RISK-9 eliminated.

**memory: user** for all 3 fork agents (cross-project reuse). **memory: project** for coordinators (project-specific patterns).

Full agent .md specifications (frontmatter + body): risk-architect L3 §1.

### 4. CLAUDE.md §10 Modification (D-10)

**Precise change:** Exception clause added to §10 first bullet:
```
...except for Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)
which receive explicit Task API access via their agent .md frontmatter.
```

**Per-agent scope:** pt-manager (Create+Update), delivery-agent (Update), rsil-agent (Update).

**3-layer enforcement:** Frontmatter `disallowedTools` (primary) → agent .md NL (secondary) → CLAUDE.md §10 (tertiary).

**agent-common-protocol.md §Task API** also updated with fork-context exception paragraph.

**Audit trail:** Existing PostToolUse hook + PT version chain + L1/L2 output. No new mechanism needed.

Full modification text: interface-architect L3 §2.

### 5. Coordinator .md Convergence (D-13)

All 8 coordinators converge to **Template B** (lean, protocol-referencing).

**Frontmatter unified (fills 25 gaps):**
- `memory: project` (all 8), `color:` (3 added), `disallowedTools:` 4-item (all 8)
- `skills:`, `hooks:`, `mcpServers:` all DEFERRED (YAGNI, ADR-S4)

**Body unified (5 sections):** Role, Before Starting Work, How to Work, Output Format, Constraints.
- Shared protocol: 2 reference lines at top (replaces ~175L inlined protocol)
- execution-coordinator retains longest "How to Work" (~45L unique review dispatch logic)

**Reduction: 768L → 402L (-48%, -366L).** Per-coordinator breakdown in structure-architect L3 §5.2.

### 6. Per-Skill Delta Summary

| Skill | Template | Unique | Template | New |
|-------|:--------:|:------:|:--------:|:---:|
| brainstorming-pipeline | Coordinator | 65% | 15% | 20% |
| agent-teams-write-plan | Coordinator | 61% | 24% | 16% |
| plan-validation-pipeline | Coordinator | 64% | 20% | 15% |
| agent-teams-execution-plan | Coordinator | 69% | 12% | 18% |
| verification-pipeline | Coordinator | 64% | 16% | 20% |
| delivery-pipeline | Fork | 74% | 11% | 15% |
| rsil-global | Fork | 75% | 10% | 15% |
| rsil-review | Fork | 73% | 8% | 19% |
| permanent-tasks | Fork | 72% | 13% | 16% |

All 9 get NEW Interface Section (C). Full per-skill section inventory: structure-architect L3 §6.2-6.3.

## Risk Summary

### Active Risks (4 primary)

| ID | Risk | Sev | Like | Mitigation |
|----|------|-----|------|------------|
| RISK-2 | PT fork loses conversation history | MED-HIGH | CERTAIN | 3-layer: pipeline/rich/interactive |
| RISK-3 | Delivery fork complexity | MEDIUM | HIGH | No nested skills, idempotent, fork last |
| RISK-5 | Big Bang 22+ files | HIGH | MEDIUM | YAML validation, atomic commit, smoke test, rollback |
| RISK-8 | Task list scope in fork | MEDIUM | MEDIUM | Pre-deploy validation + $ARGUMENTS fallback |

### Open Questions Resolved

| # | Question | Verdict |
|---|----------|---------|
| OQ-1 | Fork agent subagent spawning? | YES (85%, pre-deploy validation) |
| OQ-2 | Template variant count? | 2 variants (coordinator + fork) |
| OQ-3 | GC elimination timeline? | Remove in v9.0 |
| OQ-4 | Skills preload? | DEFER (3,250L cost vs marginal benefit) |
| OQ-5 | Shared vs separate RSIL agents? | Shared rsil-agent (ADR-S5) |

### Pre-Deployment Validation (CRITICAL)

Before Big Bang commit, validate in sequence:
A) Custom agent resolution + task list scope + fork spawning
B) rsil-global (lowest risk fork)
C) rsil-review + permanent-tasks (medium risk)
D) delivery-pipeline (highest risk, fork last)

## Cross-Lens Synthesis

### Alignment Verified (no conflicts after CLC-1 resolution)

1. **Structure ↔ Interface:** Template §C (Interface Section) format cleanly holds interface contract content. Authority rule: interface content wins, structure format wins.
2. **Structure ↔ Risk:** 2 template variants confirmed by both ADR-S1 and OQ-2. Shared rsil-agent confirmed by both ADR-S5 and risk analysis.
3. **Interface ↔ Risk:** §10 exception scope matches fork agent tool permissions exactly. Fork-to-PT contract (C-4) depends on task list scope (RISK-8).
4. **ADR-S8 relay:** Fork agents need inline cross-cutting in agent .md body. Risk-architect's designs already satisfy this — each agent .md has inline error handling, principles, constraints, and "Never" lists.

### One Dependency Remains

**Task list scope (RISK-8):** Interface-architect assumes fork agents share main session's task list. Risk-architect identifies this as MEDIUM risk with pre-deploy validation gate. If fork agents see isolated task list: C-4 contract breaks, pt-manager Phase 0 fails. Fallback: pass PT task ID via $ARGUMENTS.

## PT Goal Linkage

| PT Decision | Architecture Contribution | Status |
|-------------|--------------------------|--------|
| D-6 (Precision Refocus) | 4-section template design for both variants | DESIGNED |
| D-7 (PT-centric Interface) | Complete per-skill read/write contract, PT schema, discovery protocol | DESIGNED |
| D-8 (Big Bang) | Risk mitigation (RISK-5), phased validation within atomic commit | MITIGATED |
| D-9 (4 skills → fork) | Fork template + 3 agent .md designs + phased adoption | DESIGNED |
| D-10 (§10 modification) | Exact change text, 3-layer enforcement, audit trail | DESIGNED |
| D-11 (3 fork agents) | pt-manager, delivery-agent, rsil-agent — full frontmatter + body | DESIGNED |
| D-12 (Lean PT) | Pointer-based schema, bulk data in L3 | DESIGNED |
| D-13 (Template B convergence) | 768→402L, unified frontmatter, 5-section body | DESIGNED |
| D-14 (GC 14→3) | Migration map: 9 eliminate + 2 migrate + 3 keep | DESIGNED |
| D-15 (Custom agents FEASIBLE) | Primary path confirmed, RISK-1 defense-in-depth | VALIDATED |

## Evidence Sources

| Source Category | Count | Key Sources |
|----------------|:-----:|-------------|
| Structure architect | 130 | 9 skills (5 read directly), 8 coordinators (3 read directly), P2 research, protocols |
| Interface architect | 8 | CLAUDE.md §10, agent-common-protocol §Task API, P2 GC mapping, CC research |
| Risk architect | 11 | 4 fork skill files, 3 existing agent .md patterns, P2 fork analysis, CC research |
| **Total** | **149** | Across 3 workers + coordinator cross-reference |

## Downstream Handoff

### Decisions Made (forward-binding)
- 2 template variants: coordinator-based (5 skills) + fork-based (4 skills)
- PT-centric interface: PT = sole cross-phase source of truth, GC = session scratch only
- 3 fork agent .md files: pt-manager (Create+Update), delivery-agent (Update), rsil-agent (Update+Task)
- §10 modification: 3 named agents, 3-layer enforcement, existing audit trail
- 8 coordinators → Template B (768→402L), memory: project, disallowedTools: 4-item
- GC elimination in v9.0: 9 sections removed, 2 migrated, 3 kept
- Skills preload DEFERRED (ADR-S4, RISK-4)
- Shared rsil-agent for rsil-global + rsil-review (ADR-S5)
- Fork cross-cutting is inline, not 1-line references (ADR-S8)
- SendMessage removed from pt-manager (CLC-1 resolution)

### Risks Identified (must-track)
- RISK-2: permanent-tasks conversation history loss (CERTAIN, 3-layer mitigation)
- RISK-3: delivery-pipeline fork complexity (HIGH likelihood, fork last)
- RISK-5: Big Bang 22+ files (MEDIUM likelihood, pre-commit validation + rollback)
- RISK-8: Task list scope in fork (MEDIUM, pre-deploy validation CRITICAL)
- OQ-1: Fork spawning 85% confidence — pre-deploy validation required

### Interface Contracts (must-satisfy)
- C-1: Per-skill PT Read/Write (interface-architect L3 §1.2)
- C-2: L2 Downstream Handoff chain (interface-architect L3 §1.5)
- C-3: GC scratch-only role (interface-architect L3 §1.4)
- C-4: Fork-to-PT Direct via TaskGet/TaskUpdate (interface-architect L3 §1.7)
- C-5: §10 exception for 3 named fork agents (interface-architect L3 §2)
- Template §C format: Input → Output → Next (structure-architect L3 §1.2-1.3)

### Constraints (must-enforce)
- Big Bang: all 22+ files committed atomically (D-8)
- YAGNI: no speculative features (D-4)
- 60-80% unique per skill — template is structural guidance, not literal deduplication
- BUG-001: mode "default" always
- Fork agents start clean — no conversation history
- Pre-deploy validation sequence (A→B→C→D) is CRITICAL before production commit

### Open Questions (requires resolution)
- Task list scope in fork (RISK-8): requires CC research or empirical test before implementation. If isolated → C-4 fallback to $ARGUMENTS PT-ID passing.
- Fork return model: full output or summary? (not blocking — affects skill terminal summary design only)

### Artifacts Produced
- `phase-3/structure-architect-1/` — L1, L2, L3 (template designs, coordinator convergence, per-skill delta, heatmap)
- `phase-3/interface-architect-1/` — L1, L2, L3 (PT contract, §10 modification, dependency map, migration path)
- `phase-3/risk-architect-1/` — L1, L2, L3 (3 agent .md designs, risk register, failure modes, validation strategy)
- `phase-3/arch-coord/` — L1, L2 (this consolidated report), L3 (progress-state.yaml)

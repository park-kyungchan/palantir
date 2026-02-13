# Skill Optimization v9.0 — Implementation Plan

> **For Lead:** This plan is designed for Agent Teams Phase 6 execution.
> Read this file, then orchestrate using CLAUDE.md Phase Pipeline protocol.
> Follow execution-coordinator dispatch for multi-implementer coordination.

**Goal:** Restructure all 9 pipeline skills (2 template variants), converge 8 coordinator .md files (Template B), create 3 fork agent .md files, and modify CLAUDE.md §10 + agent-common-protocol.md — Big Bang atomic commit of 22 files.

**Architecture Source:** Phase 3 consolidated artifacts:
- `phase-3/arch-coord/L2-summary.md` (221L unified report)
- `phase-3/structure-architect-1/L3-full/structure-design.md` (754L)
- `phase-3/interface-architect-1/L3-full/interface-design.md` (412L)
- `phase-3/risk-architect-1/L3-full/risk-design.md` (662L)

**Pipeline:** COMPLEX tier — full Phase 6 with execution-coordinator.

---

## 1. Orchestration Overview (Lead Instructions)

### Pipeline Structure

```
Phase 6: Implementation   — 5 implementers execute in parallel (22 files)
Phase 6.V: Verification   — Cross-reference validation (Task V)
Phase 9: Delivery          — Atomic commit + smoke test (RISK-5 mitigation)
```

### Teammate Allocation

| Role | ID | Agent Type | File Count | Coupling Group | Phase |
|------|----|-----------|:----------:|----------------|-------|
| Fork Implementer 1 | impl-a1 | `implementer` | 4 | fork-cluster-1 | 6 |
| Fork Implementer 2 | impl-a2 | `implementer` | 3 | fork-cluster-2 | 6 |
| Skill Implementer | impl-b | `implementer` | 5 | coord-skills | 6 |
| Coordinator Convergence | infra-c | `infra-implementer` | 8 | coord-convergence | 6 |
| Protocol Editor | infra-d | `infra-implementer` | 2 | protocol-pair | 6 |
| Cross-Ref Verifier | verifier | `integrator` | 0 (reads all) | verification | 6.V |

**WHY 5 implementers (not 1 or 2):**
- 22 files across 5 coupling groups with distinct concerns
- BUG-002 scope gate: max 4 files per implementer where possible
- Fork coupling constraint: fork skill `agent:` ↔ fork agent .md filename must be co-located
- Coordinator coupling is loose (pre-existing names) → safe to separate from skills
- Parallel execution reduces total pipeline time

**WHY split fork into A1+A2 (not single 7-file implementer):**
- 7 files exceeds BUG-002 scope gate
- rsil-agent is shared by 2 skills → must stay together (A2)
- pt-manager + delivery-agent have separate skill pairs → group together (A1)
- No cross-pair coupling between A1 and A2 beyond shared fork template pattern

### Execution Sequence

```
Lead:   TeamCreate("skill-opt-v9-p6")
Lead:   TaskCreate x 6 (Tasks A1, A2, B, C, D, V — see §4)
Lead:   Spawn execution-coordinator
        ┌──────────────────────────────────────────────────────────────┐
        │ Parallel Implementation (all 5 implementers)                 │
        │                                                              │
        │  D (protocol-pair)     ──→ §10 + §Task API edits            │
        │  A1 (fork-cluster-1)   ──→ pt-mgr + perm-tasks + del-agent  │
        │                             + del-pipeline                   │
        │  A2 (fork-cluster-2)   ──→ rsil-agent + rsil-global         │
        │                             + rsil-review                    │
        │  B (coord-skills)      ──→ 5 coordinator-based SKILL.md     │
        │  C (coord-convergence) ──→ 8 coordinator .md files          │
        │                                                              │
        │  Each: Understanding verification → Plan → Execute → Review  │
        └──────────────────────────────────────────────────────────────┘
Lead:   Gate 6a: Per-implementer completion (exec-coordinator reports)
Lead:   Spawn verifier (Task V — cross-reference validation)
        ┌──────────────────────────────────────────────────────────────┐
        │ Cross-Reference Verification (8 checks across all 22 files)  │
        └──────────────────────────────────────────────────────────────┘
Lead:   Gate 6b: Verification PASS
Lead:   Phase 9: Atomic commit (single git commit, 22 files)
Lead:   Smoke test sequence (RISK-5): A→B→C→D per risk-architect §5
```

---

## 2. Architecture Summary

> Full details: `phase-3/arch-coord/L2-summary.md` (221L).

### Key Architecture Decisions

| ID | Decision | Impact |
|----|----------|--------|
| ADR-S1 | 2 template variants: coordinator-based (5 skills) + fork-based (4 skills) | Template is structural guidance, not literal dedup. 61-75% unique per skill |
| D-7 | PT-centric interface: PT = sole cross-phase source of truth | New §C Interface Section in all 9 skills. GC 14→3 sections |
| D-11 | 3 fork agent .md files: pt-manager, delivery-agent, rsil-agent | NEW files. Full designs in risk-architect L3 §1 |
| D-13 | Coordinator .md convergence to Template B (768→402L, -48%) | 8 files modified. Unified frontmatter + 5-section body |
| C-5 | CLAUDE.md §10 exception for 3 named fork agents | 3-layer enforcement: frontmatter → agent .md NL → CLAUDE.md |
| D-14 | GC reduction: 14→3 sections (9 eliminated, 2 migrated to PT) | Skills no longer write/read GC for cross-phase state |
| ADR-S5 | Shared rsil-agent for rsil-global + rsil-review | 1 agent .md, skill body differentiates behavior |
| ADR-S8 | Fork cross-cutting is inline, not 1-line CLAUDE.md references | Fork agents have no CLAUDE.md in context |

### Interface Contracts (must-satisfy)

| Contract | Definition | Authority |
|----------|-----------|-----------|
| C-1 | Per-skill PT Read/Write mapping | interface-planner L3 §1 |
| C-2 | L2 Downstream Handoff chain (replaces GC) | interface-planner L3 dependency-matrix §5 |
| C-3 | GC scratch-only (3 concerns: metrics, gate records, version) | interface-planner L3 §3 |
| C-4 | Fork-to-PT Direct (TaskGet/TaskUpdate from fork) | interface-planner L3 §1.2 |
| C-5 | §10 exception (3 named agents, 3-layer enforcement) | interface-planner L3 §2 |
| C-6 | 4-way naming (3 agents × 4 locations consistency) | interface-planner L3 §4 |

### Active Risks

| ID | Sev | Risk | Mitigation | Owner |
|----|-----|------|------------|-------|
| RISK-2 | MED-HIGH | PT fork loses conversation history | 3-layer: pipeline/rich/interactive | A1 (permanent-tasks spec) |
| RISK-3 | MEDIUM | Delivery fork complexity | No nested skills, idempotent, fork last in smoke test | A1 (delivery-pipeline spec) |
| RISK-5 | HIGH | Big Bang 22+ files | YAML validation, atomic commit, smoke test, rollback | Lead (Phase 9) |
| RISK-8 | MEDIUM | Task list scope in fork | Pre-deploy validation + $ARGUMENTS fallback | A1, A2 (all fork specs) |

---

## 3. File Ownership Map

### Coupling Groups

| Group | Constraint | Type | Files |
|-------|-----------|------|:-----:|
| fork-cluster-1 | Skill `agent:` ↔ agent .md filename; delivery-agent removes /permanent-tasks nesting | Tight | 4 |
| fork-cluster-2 | Shared rsil-agent ↔ rsil-global + rsil-review skills | Tight | 3 |
| coord-skills | Skill §A references coordinator `subagent_type` (pre-existing names) | Loose | 5 |
| coord-convergence | All 8 coordinators converge to single Template B pattern | Internal | 8 |
| protocol-pair | §10 agent names ↔ §Task API agent names | Tight | 2 |
| verification | Cross-group reference validation (post-implementation) | Post-hoc | 0 |

### Complete File Ownership Table

| # | File Path | Owner | Op | Coupling Group |
|---|-----------|-------|----|----------------|
| 1 | `.claude/agents/pt-manager.md` | impl-a1 | CREATE | fork-cluster-1 |
| 2 | `.claude/skills/permanent-tasks/SKILL.md` | impl-a1 | MODIFY | fork-cluster-1 |
| 3 | `.claude/agents/delivery-agent.md` | impl-a1 | CREATE | fork-cluster-1 |
| 4 | `.claude/skills/delivery-pipeline/SKILL.md` | impl-a1 | MODIFY | fork-cluster-1 |
| 5 | `.claude/agents/rsil-agent.md` | impl-a2 | CREATE | fork-cluster-2 |
| 6 | `.claude/skills/rsil-global/SKILL.md` | impl-a2 | MODIFY | fork-cluster-2 |
| 7 | `.claude/skills/rsil-review/SKILL.md` | impl-a2 | MODIFY | fork-cluster-2 |
| 8 | `.claude/skills/brainstorming-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills |
| 9 | `.claude/skills/agent-teams-write-plan/SKILL.md` | impl-b | MODIFY | coord-skills |
| 10 | `.claude/skills/plan-validation-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills |
| 11 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | impl-b | MODIFY | coord-skills |
| 12 | `.claude/skills/verification-pipeline/SKILL.md` | impl-b | MODIFY | coord-skills |
| 13 | `.claude/agents/research-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 14 | `.claude/agents/verification-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 15 | `.claude/agents/architecture-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 16 | `.claude/agents/planning-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 17 | `.claude/agents/validation-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 18 | `.claude/agents/execution-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 19 | `.claude/agents/testing-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 20 | `.claude/agents/infra-quality-coordinator.md` | infra-c | MODIFY | coord-convergence |
| 21 | `.claude/CLAUDE.md` | infra-d | MODIFY | protocol-pair |
| 22 | `.claude/references/agent-common-protocol.md` | infra-d | MODIFY | protocol-pair |

### Ownership Verification

```
impl-a1:  4 files (2 CREATE + 2 MODIFY)  ✓ ≤4 guideline
impl-a2:  3 files (1 CREATE + 2 MODIFY)  ✓ ≤4 guideline
impl-b:   5 files (0 CREATE + 5 MODIFY)  ⚠ exceeds 4, justified: same template variant
infra-c:  8 files (0 CREATE + 8 MODIFY)  ⚠ exceeds 4, justified: small files (38-83L), highly templated
infra-d:  2 files (0 CREATE + 2 MODIFY)  ✓ lightweight (~15 lines total change)
verifier: 0 files (reads all 22)          ✓ read-only verification
──────────────────────────────────────────
Total:    22 files, 0 overlap             ✓ non-overlapping ownership
```

### Task Dependency Graph

```
                    ┌──── impl-a1 (fork-cluster-1) ────┐
                    │                                    │
                    ├──── impl-a2 (fork-cluster-2) ────┤
                    │                                    │
Phase 6 start ─────├──── impl-b  (coord-skills)   ────├──→ verifier (Task V) ──→ Gate 6
                    │                                    │
                    ├──── infra-c (coord-convergence)───┤
                    │                                    │
                    └──── infra-d (protocol-pair)  ─────┘
```

---

## 4. Task Breakdown

> Full task descriptions with AC-0 acceptance criteria:
> `phase-4/decomposition-planner-1/L3-full/section-4-tasks.md`

### Task Summary Table

| Task | Owner | Agent Type | Files | Description | Internal Order |
|------|-------|-----------|:-----:|-------------|----------------|
| D | infra-d | infra-implementer | 2 | §10 + §Task API fork exception | — |
| A1 | impl-a1 | implementer | 4 | pt-manager + permanent-tasks + delivery-agent + delivery-pipeline | CREATE agents first, then MODIFY skills |
| A2 | impl-a2 | implementer | 3 | rsil-agent + rsil-global + rsil-review | CREATE agent first, then MODIFY skills |
| B | impl-b | implementer | 5 | 5 coordinator-based SKILL.md restructure | Smallest to largest (build template familiarity) |
| C | infra-c | infra-implementer | 8 | 8 coordinator .md Template B convergence | — |
| V | verifier | integrator | 0→22 | Cross-reference validation (8 checks) | After D+A1+A2+B+C complete |

### Key Acceptance Criteria (All Tasks)

**AC-0 (universal):** Read current file content BEFORE editing. Verify insertion points and section structure match the plan. If discrepancy found, report before proceeding.

**Task D ACs:** §10 names exactly pt-manager/delivery-agent/rsil-agent. Protocol names match §10. Same 3 agents in both files.

**Task A1 ACs:** Agent .md frontmatter matches risk-architect L3 §1.1/§1.2. Skills have `context:fork` + `agent:` field. Second-person voice. §Interface section with PT contract. RISK-8 fallback. delivery-pipeline does NOT invoke /permanent-tasks (RISK-3). BUG-001: mode "default".

**Task A2 ACs:** BOTH skills reference `agent:"rsil-agent"` (ADR-S5 shared agent). rsil-global stays within ~2000 token budget. rsil-review R-1 uses Task tool for spawning. §Interface + RISK-8 fallback. Skill body differentiates behavior.

**Task B ACs:** All 5 skills have §A (Spawn) + §B (Core Workflow) + §C (Interface) + §D (Cross-Cutting). Phase 0 PT Check identical across all 5. GC writes REMOVED. GC reads replaced by PT + L2 discovery. 60-80% unique content preserved.

**Task C ACs:** All 8 have memory:project, color assigned, 4-item disallowedTools. Protocol references (lines 1-2). 5-section body. Template A coordinators: remove inlined boilerplate (→ coordinator-shared-protocol.md). execution-coordinator retains ~45L unique review dispatch.

**Task V ACs:** 8 checks all PASS. Zero naming mismatches. File:line evidence for each finding.

---

## 5. Per-File Specifications

> **Full per-file detail (737L) with current→target state, structural changes, cross-references, VL tags, RISK-8 deltas:**
> `phase-4/decomposition-planner-1/L3-full/section-5-specs.md`
>
> **Interface contracts (§C content, §10 text, GC migration, naming contract — 541L):**
> `phase-4/interface-planner-1/L3-full/interface-design.md`

### Verification Levels Summary

| VL | Count | Files |
|----|:-----:|-------|
| VL-1 (visual inspection) | 6 | CLAUDE.md, protocol, architecture-coord, planning-coord, validation-coord |
| VL-2 (cross-reference) | 5 | research-coord, verification-coord, execution-coord, testing-coord, infra-quality-coord |
| VL-3 (full spec validation) | 11 | 3 new agent .md, 4 fork SKILL.md, 4 complex coord SKILL.md (brainstorming excluded from VL-3→VL-3) |

### §10 Modification (Task D — Exact Text)

**CLAUDE.md §10, first bullet — REPLACE:**
```
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
```
**WITH:**
```
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions),
  except for Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)
  which receive explicit Task API access via their agent .md frontmatter. Fork
  agents execute skills that Lead invokes — they are extensions of Lead's intent,
  not independent actors. Fork Task API scope:
  - pt-manager: TaskCreate + TaskUpdate (creates and maintains PT)
  - delivery-agent: TaskUpdate only (marks PT as DELIVERED)
  - rsil-agent: TaskUpdate only (updates PT with review results)
```

**agent-common-protocol.md §Task API — APPEND after existing text:**
```
**Exception — Fork-context agents:** If your agent .md frontmatter does NOT include
TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access.
This applies only to Lead-delegated fork agents (pt-manager, delivery-agent,
rsil-agent). You are an extension of Lead's intent — use Task API only for the
specific PT operations defined in your skill's instructions.
```

### Fork Agent .md Key Specs (Tasks A1+A2 — CREATE)

| Agent | Skill(s) | model | maxTurns | memory | disallowedTools | Key Tools |
|-------|----------|:-----:|:--------:|:------:|:---------------:|-----------|
| pt-manager | permanent-tasks | opus | 30 | user | `[]` (full Task API) | Read, Glob, Grep, Write, TaskList, TaskGet, TaskCreate, TaskUpdate, AskUserQuestion |
| delivery-agent | delivery-pipeline | opus | 50 | user | `[TaskCreate]` | Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion |
| rsil-agent | rsil-global + rsil-review | opus | 50 | user | `[TaskCreate]` | Read, Glob, Grep, Edit, Write, Task, TaskList, TaskGet, TaskUpdate, AskUserQuestion |

**Source:** risk-architect L3 §1 (complete frontmatter + body designs, ~100L each).
**All:** `permissionMode: default` (BUG-001), `color:` assigned.

### §C Interface Section Content (All 9 Skills)

> Full §C per skill: `phase-4/interface-planner-1/L3-full/interface-design.md` §1

**Coordinator-based format (5 skills):**
```
## C) Interface
### Input   — PT-v{N} sections read + predecessor L2 path
### Output  — PT-v{N+1} sections written + L1/L2/L3 + gate records
### Next    — Successor skill + its entry requirements
```

**Fork-based format (4 skills):**
```
## Interface
### Input   — $ARGUMENTS + Dynamic Context + PT (via TaskGet)
### Output  — PT update + file artifacts + terminal summary
### RISK-8 Fallback — behavior if task list isolated
```

**Per-Skill PT Version Chain:**

| Skill | PT Read | PT Write | Version |
|-------|---------|----------|:-------:|
| brainstorming-pipeline | — (creates PT) | PT-v1: User Intent, Impact Map, Arch Decisions, Phase Status, Constraints | v1 |
| agent-teams-write-plan | User Intent, Impact Map, Arch Decisions, Constraints | PT-v{N+1}: adds §Implementation Plan, §phase_status.P4=COMPLETE | v2 |
| plan-validation-pipeline | User Intent, Arch Decisions, Constraints, Impl Plan | PT-v{N+1}: adds §Validation Verdict, §phase_status.P5=COMPLETE | v3 |
| agent-teams-execution-plan | User Intent, Impact Map, Arch Decisions, Impl Plan, Constraints | PT-v{N+1}: adds §Impl Results, §phase_status.P6=COMPLETE | v4 |
| verification-pipeline | User Intent, Impact Map, Impl Results, Constraints | PT-v{N+1}: adds §Verification Summary, §phase_status.P7/P8=COMPLETE | v5 |
| delivery-pipeline | All sections | PT-vFinal: §phase_status all COMPLETE, subject→"[DELIVERED]" | vFinal |
| permanent-tasks | Full PT (for merge) | PT-v{N+1}: any section (user-directed, Read-Merge-Write) | v{N+1} |
| rsil-global | Phase Status, Constraints | None typically (or PT-v{N+1} if actionable) | optional |
| rsil-review | Phase Status | PT-v{N+1}: Phase Status with review results | v{N+1} |

### GC Migration Summary (5 Coordinator Skills)

> Full per-skill GC migration specs: `phase-4/interface-planner-1/L3-full/interface-design.md` §3

| Skill | GC Writes Removed | GC Reads Replaced | GC Kept (scratch) |
|-------|:-----------------:|:-----------------:|:-----------------:|
| brainstorming | 6 sections (Gates 2-3) | 0 (pipeline start) | 3 sections (Gate 1) |
| write-plan | 6 sections (Gate 4) | 5 operations (discovery+directive) | 1 section (status) |
| validation | 2 sections (Gate 5) | 4 operations (discovery) | 1 section (status) |
| execution | 5 sections (termination) | 3 operations (discovery) | 2 sections (status+gate) |
| verification | 3 sections (Gates 7-8+term) | 2 operations (V-1+copy) | 1 section (status) |
| delivery | 0 | 1 GC fallback REMOVED | 0 |
| **Total** | **22 removed** | **15 replaced** | **8 kept** |

### Coordinator .md Gap Analysis (Task C)

| Coordinator | memory | color | disallowedTools | Body Restructure | Current→Target |
|-------------|:------:|:-----:|:---------------:|:----------------:|:--------------:|
| research | user→project | OK | OK | Template A→B (remove 5 inlined sections) | 105→~45L |
| verification | user→project | OK | OK | Template A→B (remove 5 inlined sections) | 107→~48L |
| architecture | ADD project | ADD purple | ADD Edit,Bash | Minor (already Template B) | 61→~38L |
| planning | ADD project | ADD orange | ADD Edit,Bash | Minor (already Template B) | 58→~40L |
| validation | ADD project | ADD yellow | ADD Edit,Bash | Minor (already Template B) | 60→~40L |
| execution | user→project | OK | OK | Template A→B (retain ~45L unique review dispatch) | 151→~83L |
| testing | user→project | OK | OK | Template A→B (remove 5 inlined sections) | 98→~55L |
| infra-quality | user→project | OK | OK | Template A→B (remove 5 inlined sections) | 113→~53L |

### 4-Way Naming Contract

| Canonical Name | Skill `agent:` | Agent .md Filename | CLAUDE.md §10 | agent-common-protocol.md |
|:--------------:|:--------------:|:------------------:|:-------------:|:------------------------:|
| `pt-manager` | `agent: pt-manager` | `pt-manager.md` | `pt-manager` | `pt-manager` |
| `delivery-agent` | `agent: delivery-agent` | `delivery-agent.md` | `delivery-agent` | `delivery-agent` |
| `rsil-agent` | `agent: rsil-agent` | `rsil-agent.md` | `rsil-agent` | `rsil-agent` |

---

## 6. Execution Sequence

### Dependency DAG

```
Layer 0 (Foundation — no cross-dependencies):
  ├── CLAUDE.md §10 modification (infra-d, 1 file)
  ├── agent-common-protocol.md §Task API (infra-d, 1 file)
  ├── 3 NEW fork agent .md (impl-a1: 2, impl-a2: 1)
  └── 8 coordinator .md (infra-c, 8 files)

Layer 1 (Skills — depends on Layer 0 for consistency):
  ├── 4 fork SKILL.md (impl-a1: 2, impl-a2: 2)
  └── 5 coordinator SKILL.md (impl-b, 5 files)

Layer 2 (Verification — depends on Layer 1):
  └── Cross-reference validation (verifier, reads all 22)

Layer 3 (Pre-deploy — depends on Layer 2):
  └── Functional validation A → B → C → D (Lead)

Layer 4 (Commit):
  └── Atomic git commit (Lead)
```

### Concrete Implementer Wave Mapping

| Wave | Item | Implementer | Files | Type |
|------|------|------------|:-----:|------|
| 1a | §10 + protocol | infra-d | 2 | MODIFY |
| 1b | pt-manager.md + delivery-agent.md | impl-a1 | 2 | CREATE |
| 1b | rsil-agent.md | impl-a2 | 1 | CREATE |
| 1c | 8 coordinator .md | infra-c | 8 | MODIFY |
| 2a | permanent-tasks + delivery-pipeline SKILL | impl-a1 | 2 | MODIFY |
| 2a | rsil-global + rsil-review SKILL | impl-a2 | 2 | MODIFY |
| 2b | 5 coordinator SKILL.md | impl-b | 5 | MODIFY |
| 3 | Cross-reference verification | verifier | 0→22 | READ |
| 4 | Pre-deploy A→B→C→D | Lead | — | TEST |
| 5 | Atomic commit | Lead | 22 | COMMIT |

**Critical execution note:** All 5 implementers (impl-a1, impl-a2, impl-b, infra-c, infra-d) START SIMULTANEOUSLY. The Layer 0→1 dependency is INTERNAL to impl-a1 and impl-a2: each creates the agent .md first (Wave 1b), then modifies the skill (Wave 2a). This is sequential WITHIN the implementer, not a cross-implementer constraint. impl-b, infra-c, and infra-d have no internal wave ordering.

### Cross-File Dependency Matrix

```
                    Depends On →
                    §10  protocol  fork-agent  coord.md  fork-skill  coord-skill
§10 modification     —     —          —          —          —            —
protocol mod         —     —          —          —          —            —
fork agent .md       —     —          —          —          —            —
coordinator .md      —    weak        —          —          —            —
fork SKILL.md        —     —        STRONG       —          —            —
coord SKILL.md       —     —          —        weak         —            —

Legend: STRONG = hard data dependency (agent .md must exist for fork resolution)
        weak = consistency dependency (should be settled for coherence)
        — = no dependency
```

---

## 7. Validation Checklist

> All checks apply to the 22 target files. V1-V5 are automatable (V6a).

### V1: YAML Frontmatter Parseability
Parse YAML between `---` markers for all 20 frontmatter files (9 SKILL + 8 coordinator + 3 fork agent).
**Method:** `python3 -c "import yaml, sys; yaml.safe_load(sys.stdin.read())"` on extracted frontmatter.
**Pass:** Zero parse errors.

### V2: Required Frontmatter Keys
| File Type | Required Keys |
|-----------|--------------|
| Coordinator SKILL.md (5) | `name`, `description`, `argument-hint` |
| Fork SKILL.md (4) | `name`, `description`, `argument-hint`, `context: fork`, `agent` |
| Coordinator agent .md (8) | `name`, `description`, `model`, `permissionMode`, `memory: project`, `color`, `maxTurns`, `tools`, `disallowedTools` |
| Fork agent .md (3) | `name`, `description`, `model`, `permissionMode`, `memory: user`, `color`, `maxTurns`, `tools`, `disallowedTools` |

### V3: Cross-File Reference Accuracy
- [ ] 4 fork SKILL.md `agent:` → `.claude/agents/{value}.md` exists
- [ ] CLAUDE.md §10 lists exactly: pt-manager, delivery-agent, rsil-agent → all 3 exist
- [ ] agent-common-protocol.md §Task API lists same 3 names
- [ ] 5 coordinator SKILL.md subagent_type refs → agent .md files exist
- [ ] Fork agent disallowedTools matches §10 scope

### V4: Template Section Ordering
**Coordinator-based (5):** `# Title` → `When to Use` → `Dynamic Context` → `A) Phase 0` → `B) Phase {N}` → `C) Interface` → `D) Cross-Cutting` → `Key Principles` → `Never`
**Fork-based (4):** `# Title` → `When to Use` → `Dynamic Context` → `Phase 0` → `{Core}` → `Interface` → `Cross-Cutting` → `Key Principles` → `Never`

### V5: disallowedTools Consistency
| Agent | Expected |
|-------|----------|
| pt-manager | `[]` (full Task API) |
| delivery-agent | `[TaskCreate]` |
| rsil-agent | `[TaskCreate]` |
| 8 coordinators | `[TaskCreate, TaskUpdate, Edit, Bash]` |

### V6: Code Plausibility
**V6a (automated):** V1-V5 + `mode:"default"` everywhere + `memory:project` for coordinators + `memory:user` for fork agents + `context:fork` present/absent correctly.

**V6b (manual semantic — during P6 two-stage review):**
- V6b-1: NL instruction consistency (skill body ↔ agent .md body)
- V6b-2: Voice consistency (fork=2nd person, coordinator=3rd person)
- V6b-3: Cross-cutting completeness (coordinator=1-line refs, fork=inline)
- V6b-4: Behavioral plausibility (error paths reachable, recovery sound)
- V6b-5: §C Interface matches C-1~C-6 contracts

---

## 8. Risk Mitigation Strategy

### RISK-2: PT Fork Loses Conversation History (MED-HIGH, CERTAIN)
**Affects:** permanent-tasks (pt-manager). **3-layer mitigation:**
1. **Pipeline auto-invocation:** $ARGUMENTS carries structured context. Dynamic Context supplements.
2. **Manual with rich $ARGUMENTS:** User provides detailed description. Dynamic Context supplements.
3. **Manual with sparse $ARGUMENTS:** pt-manager uses AskUserQuestion to probe for missing context.
**Touchpoints:** pt-manager.md §Context Sources, permanent-tasks SKILL.md §Dynamic Context.

### RISK-3: Delivery Fork Complexity (MEDIUM, HIGH likelihood)
**Affects:** delivery-pipeline (delivery-agent). **4-layer mitigation:**
1. No nested skill invocation (CRITICAL: delivery-agent NEVER invokes /permanent-tasks)
2. Idempotent operations (Write is atomic, Read-Merge-Write is rerunnable)
3. User confirmation gates (5+ AskUserQuestion checkpoints)
4. Fork-last validation (Phase D in pre-deploy)
**Fallback:** Revert delivery-pipeline to Lead-in-context while keeping other 3 fork skills.

### RISK-5: Big Bang 22+ Files (HIGH, MEDIUM likelihood)
**5-layer mitigation:**
1. V6a automated validation (YAML parse, keys, cross-refs, ordering)
2. Non-overlapping file ownership (§3)
3. Cross-reference verification (Task V)
4. Atomic commit (single `git commit`)
5. Smoke test sequence (pre-deploy B→C→D)

### RISK-8: Task List Scope in Fork (MEDIUM, MEDIUM likelihood)
**Primary:** Fork agents share main session's task list → C-4 contract works.
**Fallback Delta (~50L across 8 files):** $ARGUMENTS carries PT task ID. Dynamic Context pre-renders TaskList output. Fork agent parses rendered output.
**Impact:** pt-manager MODERATE degradation, delivery-agent MODERATE, rsil-agent MINIMAL.
**Decision point:** Phase A pre-deploy validation determines which path.

### Pre-Deploy Validation Sequence (A → B → C → D)

| Phase | Test | Pass Criterion | Failure Response |
|-------|------|----------------|-----------------|
| A1 | V6a automated checks | Zero failures | Fix → re-run |
| A2 | Custom agent resolution | Fork skill loads agent .md | RISK-1 fallback |
| A3 | Task list scope | Fork sees [PERMANENT] task | RISK-8 delta |
| A4 | Fork spawn mechanism | `context:fork` creates fork | Critical — investigate |
| B | rsil-global functional | Fork executes correctly | Fix rsil-global/rsil-agent |
| C1 | permanent-tasks functional | pt-manager creates/updates PT | Fix pt-manager/perm-tasks |
| C2 | rsil-review spawning | rsil-agent spawns via Task tool | Fallback: sequential |
| D | delivery-pipeline functional | delivery-agent loads, PT check works | Fallback: Lead-in-context |

**Shared file rule:** rsil-agent.md fix in Phase C → re-run Phase B.

---

## 9. Commit Strategy

### Pre-Commit Gate
ALL must pass: V6a zero failures + Pre-deploy A→B→C→D all pass + no WIP files outside 22 target set.

### Staging Command
```bash
git add \
  .claude/CLAUDE.md \
  .claude/references/agent-common-protocol.md \
  .claude/agents/pt-manager.md \
  .claude/agents/delivery-agent.md \
  .claude/agents/rsil-agent.md \
  .claude/agents/research-coordinator.md \
  .claude/agents/verification-coordinator.md \
  .claude/agents/architecture-coordinator.md \
  .claude/agents/planning-coordinator.md \
  .claude/agents/validation-coordinator.md \
  .claude/agents/execution-coordinator.md \
  .claude/agents/testing-coordinator.md \
  .claude/agents/infra-quality-coordinator.md \
  .claude/skills/brainstorming-pipeline/SKILL.md \
  .claude/skills/agent-teams-write-plan/SKILL.md \
  .claude/skills/plan-validation-pipeline/SKILL.md \
  .claude/skills/agent-teams-execution-plan/SKILL.md \
  .claude/skills/verification-pipeline/SKILL.md \
  .claude/skills/delivery-pipeline/SKILL.md \
  .claude/skills/rsil-global/SKILL.md \
  .claude/skills/rsil-review/SKILL.md \
  .claude/skills/permanent-tasks/SKILL.md
```

### Commit Message
```
feat(infra): skill optimization v9.0 — fork agents, PT-centric interface, coordinator convergence

Redesign 9 skills with 2 template variants (coordinator-based + fork-based):
- 3 NEW fork agent .md files (pt-manager, delivery-agent, rsil-agent)
- PT-centric interface: PT = sole cross-phase source of truth (GC 14→3)
- 8 coordinator .md converged to Template B (768→402L, -48%)
- CLAUDE.md §10 fork agent exception (3-layer enforcement)
- agent-common-protocol.md §Task API fork exception clause
- L2 Downstream Handoff replaces GC Phase N Entry Requirements
- All 9 skills gain new Interface Section (C-1~C-6 contracts)

Files: 9 SKILL.md + 8 coordinator .md + 3 NEW agent .md + CLAUDE.md + protocol = 22

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

### Post-Commit
1. Run `/rsil-global` — INFRA health assessment
2. `git log --oneline -1` — verify commit message
3. `git diff HEAD~1 --stat` — confirm exactly 22 files changed

---

## 10. Rollback & Recovery

### Domain 1: Pre-Commit (during validation Waves 3-4)

| Level | When | Action |
|-------|------|--------|
| L1: Fix-and-retry | Specific file(s) fail | Edit failing files, re-run validation |
| L2: Selective checkout | Need fresh start for specific files | `git checkout -- .claude/agents/rsil-agent.md ...` |
| L3: Full checkout | Fundamental architecture failure | `git checkout -- .claude/` — triggers fallback |

**Phase A failure → architecture fallback:**
- RISK-1: Use `agent: general-purpose` with inline instructions. 3 agent .md become unused.
- RISK-8: Apply delta (~50L across 8 files).

### Domain 2: Post-Commit

**Primary:** `git revert HEAD` (atomic, creates new revert commit).
**When:** /rsil-global reveals critical breakage, or first pipeline run reveals fundamental failure.
**Partial failure:** Fix 2 broken files → new commit (don't revert 20 correct files).

### Fork-Back Contingency

If fork proves unreliable for specific skills:

| Skill | Action | Impact |
|-------|--------|--------|
| permanent-tasks | Remove `context:fork` + `agent:` from frontmatter | LOW — worked before |
| rsil-global | Same | LOW |
| rsil-review | Same | LOW |
| delivery-pipeline | Same | LOW |

**Key insight:** Fork-back is always safe. All 4 skills worked in Lead-in-context before.
Fork-back keeps: coordinator convergence, §C Interface Sections, PT-centric interface, §10 modification.
Fork-back removes: only `context:fork` + `agent:` frontmatter fields. Agent .md files become unused but harmless.

### Recovery Decision Tree

```
Post-commit issue detected
    │
    ├─ Systemic (affects all skills)?
    │   └─ YES → git revert HEAD → investigate → re-plan
    │
    ├─ Isolated to specific files?
    │   └─ YES → fix files → new commit
    │
    ├─ Fork-specific (only fork skills broken)?
    │   └─ YES → fork-back-to-Lead-context → new commit
    │
    └─ Uncertain scope?
        └─ Run /rsil-global for assessment → decide
```

---

## Appendix: L3 Reference Index

| Planner | File | Lines | Content |
|---------|------|:-----:|---------|
| decomposition | `phase-4/decomposition-planner-1/L3-full/sections-1-2-3.md` | 225 | §1-§3 full detail |
| decomposition | `phase-4/decomposition-planner-1/L3-full/section-4-tasks.md` | 348 | §4 full task descriptions with ACs |
| decomposition | `phase-4/decomposition-planner-1/L3-full/section-5-specs.md` | 737 | §5 full per-file specs (22 files) |
| interface | `phase-4/interface-planner-1/L3-full/dependency-matrix.md` | 326 | Cross-file dependencies, coupling assessment |
| interface | `phase-4/interface-planner-1/L3-full/interface-design.md` | 541 | §C content, §10 text, GC migration, naming contract |
| strategy | `phase-4/strategy-planner-1/L3-full/sections-6-through-10.md` | 536 | §6-§10 full detail |
| **Total** | | **2,713** | |

# Cross-File Dependency Matrix — Skill Optimization v9.0

> Interface Planner · Phase 4 · 22+ files, 7 reference categories

---

## 1. Agent Reference Matrix (Skill → Agent .md via subagent_type / agent:)

### Coordinator-Based Skills

| Skill | subagent_type References | Tier Routing |
|-------|------------------------|--------------|
| brainstorming-pipeline | `research-coordinator`, `codebase-researcher`, `external-researcher`, `auditor`, `architect`, `architecture-coordinator`, `structure-architect`, `interface-architect`, `risk-architect`, `gate-auditor` | STANDARD: Lead-direct (researcher, architect). COMPLEX: coordinator route |
| agent-teams-write-plan | `architect`, `planning-coordinator`, `decomposition-planner`, `interface-planner`, `strategy-planner`, `gate-auditor` | STANDARD: `architect`. COMPLEX: `planning-coordinator` + 3 planners |
| plan-validation-pipeline | `devils-advocate`, `validation-coordinator`, `correctness-challenger`, `completeness-challenger`, `robustness-challenger`, `gate-auditor` | STANDARD: `devils-advocate`. COMPLEX: `validation-coordinator` + 3 challengers |
| agent-teams-execution-plan | `execution-coordinator`, `implementer`, `spec-reviewer`, `code-reviewer`, `contract-reviewer`, `regression-reviewer`, `execution-monitor`, `gate-auditor` | Always coordinator route. COMPLEX adds contract-rev, regression-rev, exec-monitor |
| verification-pipeline | `testing-coordinator`, `tester`, `contract-tester`, `integrator`, `gate-auditor` | Always coordinator route. COMPLEX adds `contract-tester` |

### Fork-Based Skills

| Skill | `agent:` Field | Agent .md File | Agents Spawned FROM Fork |
|-------|:-------------:|:--------------:|--------------------------|
| permanent-tasks | `pt-manager` | `.claude/agents/pt-manager.md` | None |
| delivery-pipeline | `delivery-agent` | `.claude/agents/delivery-agent.md` | None |
| rsil-global | `rsil-agent` | `.claude/agents/rsil-agent.md` | `codebase-researcher` (Tier 3 only, rare) |
| rsil-review | `rsil-agent` | `.claude/agents/rsil-agent.md` | `claude-code-guide` + `codebase-researcher` (R-1, always) |

**Key constraint:** Fork `agent:` field MUST exactly match the agent .md filename (without `.md` extension). Mismatch = fork resolution failure.

---

## 2. Protocol Reference Matrix (Agent .md → Protocol Files)

| Agent Category | Protocol References | Reference Type |
|----------------|-------------------|----------------|
| 8 coordinators | `agent-common-protocol.md` + `coordinator-shared-protocol.md` | Body line 1-2 (mandatory read instructions) |
| 35 workers | `agent-common-protocol.md` | Body line 1 (mandatory read instruction) |
| 3 fork agents | `agent-common-protocol.md` §Task API exception | Partial reference (fork-context agents paragraph) |

### Specific References

| Source File | Target File | Reference Section | Coupling |
|------------|------------|-------------------|----------|
| All 8 coordinator .md | `.claude/references/agent-common-protocol.md` | Full protocol | TIGHT |
| All 8 coordinator .md | `.claude/references/coordinator-shared-protocol.md` | Full protocol | TIGHT |
| All coordinator .md | CLAUDE.md §6 | "Agent Selection and Routing" | MEDIUM |
| All worker .md | `.claude/references/agent-common-protocol.md` | Full protocol | TIGHT |
| 3 fork agent .md | `.claude/references/agent-common-protocol.md` | §Task API (exception clause) | MEDIUM |

---

## 3. §10 Named Agent References (CLAUDE.md + agent-common-protocol.md)

### Current State (to be modified)

| Source File | Current Text | Line Ref |
|------------|-------------|----------|
| CLAUDE.md §10 | "Only Lead creates and updates tasks (enforced by disallowedTools restrictions)." | §10 bullet 1 |
| agent-common-protocol.md | "Tasks are read-only for you...Task creation and updates are Lead-only" | §Task API, L74-76 |

### New State (after modification)

| Source File | References These Agents | Reference Type |
|------------|------------------------|----------------|
| CLAUDE.md §10 | `pt-manager`, `delivery-agent`, `rsil-agent` | Named exception list |
| agent-common-protocol.md §Task API | `pt-manager`, `delivery-agent`, `rsil-agent` | Fork-context exception paragraph |

**4-Way Naming Contract (must be identical across all 4 locations):**

| Canonical Name | Skill `agent:` | Agent .md Filename | CLAUDE.md §10 | agent-common-protocol.md §Task API |
|:-------------:|:--------------:|:-----------------:|:-------------:|:----------------------------------:|
| `pt-manager` | `agent: pt-manager` | `pt-manager.md` | `pt-manager` | `pt-manager` |
| `delivery-agent` | `agent: delivery-agent` | `delivery-agent.md` | `delivery-agent` | `delivery-agent` |
| `rsil-agent` | `agent: rsil-agent` | `rsil-agent.md` | `rsil-agent` | `rsil-agent` |

---

## 4. PT Schema References (Skill §C → PT Sections)

### Per-Skill PT Read/Write Contract

| Skill | PT READ Sections | PT WRITE Sections | PT Version |
|-------|-----------------|-------------------|:----------:|
| brainstorming-pipeline | User Intent (seed from $ARGUMENTS), Constraints | Creates PT-v1: User Intent, Codebase Impact Map, Architecture Decisions, Phase Status, Constraints | v1 |
| agent-teams-write-plan | User Intent, Impact Map, Arch Decisions, Constraints | PT-v{N+1}: Phase Status=P4 COMPLETE, Implementation Plan (L3 pointer), File Ownership | v2 |
| plan-validation-pipeline | User Intent, Arch Decisions, Constraints, Impl Plan pointer | PT-v{N+1}: Phase Status=P5 COMPLETE, Validation Verdict. If CONDITIONAL: add mitigations to Constraints | v3 |
| agent-teams-execution-plan | User Intent, Impact Map, Arch Decisions, Impl Plan, Constraints | PT-v{N+1}: Phase Status=P6 COMPLETE, Implementation Results (L3 pointer) | v4 |
| verification-pipeline | User Intent, Impact Map, Impl Results pointer, Constraints | PT-v{N+1}: Phase Status=P7/P8 COMPLETE, Verification Summary | v5 |
| delivery-pipeline | All sections (final consolidation) | PT-vFinal: Phase Status=DELIVERED, final metrics, subject → "DELIVERED" | vFinal |
| permanent-tasks | Full PT (for merge) | PT-v{N+1}: Any section (user-directed, Read-Merge-Write) | v{N+1} |
| rsil-global | Phase Status, Constraints | None typically (findings-only) or PT-v{N+1} if actionable | optional |
| rsil-review | Phase Status | PT-v{N+1}: Phase Status with review results | v{N+1} |

### PT Section Schema (Reference for §C Content)

```yaml
user_intent: "1-3 sentence goal"
codebase_impact_map:
  modules: [{name, files, dependencies}]
  interfaces: [{from, to, contract}]
  risk_hotspots: [{file, reason}]
architecture_decisions:
  - {id: "AD-N", decision, rationale, status}
phase_status:
  P1: {status, gate_record, l2_path}
  # ... one entry per phase
constraints:
  - {id: "C-N", constraint, source}
implementation_plan:
  l3_path: "phase-4/.../L3-full/"
  task_count: N
  file_ownership: [{file, owner}]
implementation_results:
  l3_path: "phase-6/.../L3-full/"
  summary: "1-2 sentence"
validation_verdict: "PASS | CONDITIONAL_PASS | FAIL"
verification_summary:
  test_count: N
  pass_rate: "N%"
  l2_path: "phase-7/.../L2-summary.md"
budget_constraints:
  max_spawns: N
```

---

## 5. L2 Handoff Chain (Phase-to-Phase Bridge)

```
brainstorming ──[research-coord/L2 + arch-coord/L2]──→ write-plan
                                                          │
                                    ┌──[planning-coord/L2]──→ validation
                                    │                          │
                                    └──[planning-coord/L2]──→ execution ←─[validation-coord/L2]
                                                                 │
                                                    [exec-coord/L2]──→ verification
                                                                          │
                                                              [testing-coord/L2]──→ delivery
```

### L2 Discovery Protocol (NEW — replaces GC scan)

```
1. Skill reads PT via TaskGet
2. PT §phase_status.P{N-1}.l2_path → predecessor L2 location
3. Skill reads predecessor L2 §Downstream Handoff
4. Skill validates entry conditions from Handoff content
```

Path pattern: `.agent/teams/{session-id}/phase-{N}/{coordinator}/L2-summary.md`

### Per-Skill L2 Input/Output

| Skill | L2 IN (reads predecessor) | L2 OUT (writes own) |
|-------|--------------------------|---------------------|
| brainstorming | None (pipeline start) | research-coord/L2, arch-coord/L2 |
| write-plan | arch-coord/L2 §Downstream Handoff | planning-coord/L2 |
| validation | planning-coord/L2 §Downstream Handoff | validation-coord/L2 |
| execution | planning-coord/L2 + validation-coord/L2 §Downstream Handoff | exec-coord/L2 |
| verification | exec-coord/L2 §Downstream Handoff | testing-coord/L2 |
| delivery | testing-coord/L2 §Downstream Handoff | None (terminal) |

Fork skills (permanent-tasks, rsil-global, rsil-review): No L2 chain participation.

---

## 6. GC Read/Write Map (Current State — Migration Evidence)

### Per-Skill GC Operations (Extracted from Skill Read)

#### brainstorming-pipeline

| Gate/Step | GC Operation | GC Sections Written |
|-----------|-------------|---------------------|
| Gate 1 Step 2 (L230-246) | CREATE GC-v1 | Frontmatter (version, pt_version, created, feature, tier), Scope, Phase Pipeline Status, Constraints, Decisions Log |
| Gate 2 On APPROVE (L377-387) | UPDATE → GC-v2 | Research Findings, Codebase Constraints, Phase 3 Input |
| Gate 3 On APPROVE (L500-511) | UPDATE → GC-v3 | Architecture Summary, Architecture Decisions, Phase 4 Entry Requirements |

**GC sections to REMOVE:** Research Findings (→ research-coord/L2), Codebase Constraints (→ PT §Constraints at Gate 2), Phase 3 Input (→ research-coord/L2 §Downstream Handoff), Architecture Summary (→ arch-coord/L2), Architecture Decisions (→ PT §Architecture Decisions), Phase 4 Entry Requirements (→ arch-coord/L2 §Downstream Handoff)

**GC sections to KEEP:** Scope (→ scratch, but PT §User Intent is authoritative), Phase Pipeline Status (scratch), Decisions Log (scratch, PT §Architecture Decisions is authoritative)

**GC sections to MIGRATE:** Codebase Constraints → PT §Constraints (at Gate 2)

#### agent-teams-write-plan

| Gate/Step | GC Operation | GC Sections Read/Written |
|-----------|-------------|--------------------------|
| Phase 4.1 Discovery (L91) | READ | Scans for `Phase 3: COMPLETE` in GC |
| V-1 (L106) | READ | `global-context.md` exists with `Phase 3: COMPLETE` |
| V-3 (L108) | READ | GC-v3 contains Scope, Component Map, Interface Contracts |
| Phase 4.2 (L123) | COPY | Copy GC-v3 to new session directory |
| Directive (L166) | EMBED | GC-v3 full embedding in architect directive |
| Gate 4 On APPROVE (L263-265) | UPDATE → GC-v4 | ADD: Implementation Plan Reference, Task Decomposition, File Ownership Map, Phase 6 Entry Conditions, Phase 5 Validation Targets, Commit Strategy; UPDATE: Phase Pipeline Status |

**GC reads to REPLACE:** Discovery scan (→ PT §phase_status.P3.status), V-1 check (→ PT §phase_status.P3.status == COMPLETE), V-3 check (→ arch-coord/L2 §Downstream Handoff content), GC-v3 embedding (→ embed PT + arch-coord/L2 instead)

**GC writes to REMOVE:** Implementation Plan Reference (→ PT §implementation_plan), Task Decomposition (→ planning-coord/L3), File Ownership Map (→ PT §implementation_plan.file_ownership), Phase 6 Entry Conditions (→ planning-coord/L2 §Downstream Handoff), Phase 5 Validation Targets (→ planning-coord/L2 §Downstream Handoff), Commit Strategy (→ planning-coord/L2 §Downstream Handoff)

#### plan-validation-pipeline

| Gate/Step | GC Operation | GC Sections Read/Written |
|-----------|-------------|--------------------------|
| Phase 5.1 Discovery (L91) | READ | Scans for `Phase 4: COMPLETE` in GC |
| V-1 (L110) | READ | `global-context.md` exists with `Phase 4: COMPLETE` |
| V-4 (L113) | READ | GC-v4 contains Scope, Phase 4 decisions, implementation task breakdown |
| Phase 5.2 (L128) | COPY | Copy GC-v4 to new session directory |
| Gate 5 On APPROVE (L312-315) | UPDATE | ADD: `Phase 5: COMPLETE (Gate 5 APPROVED, Verdict: {verdict})`; if CONDITIONAL_PASS: add mitigations to Constraints; conditional bump GC-v4 → GC-v5 |

**GC reads to REPLACE:** Discovery scan (→ PT §phase_status.P4.status), V-1 (→ PT check), V-4 (→ planning-coord/L2 §Downstream Handoff), GC copy (→ no longer needed, read L2 directly)

**GC writes to REMOVE:** Phase 5 status update (→ PT §phase_status.P5), Constraints mitigations (→ PT §Constraints update)

#### agent-teams-execution-plan

| Gate/Step | GC Operation | GC Sections Read/Written |
|-----------|-------------|--------------------------|
| Phase 6.1 Discovery (L97) | READ | Scans for `Phase 4: COMPLETE` or `Phase 5: COMPLETE` in GC |
| V-1 (L119) | READ | `global-context.md` exists with Phase 4 or 5 COMPLETE |
| Phase 6.2 (L135) | COPY | Copy GC-v4 to new session directory |
| Phase 6.7 (L553-580) | UPDATE → GC-v5 | ADD: Phase Pipeline Status (P6 COMPLETE), Implementation Results, Interface Changes from Phase 4 Spec, Gate 6 Record, Phase 7 Entry Conditions |

**GC reads to REPLACE:** Discovery scan (→ PT §phase_status.P4/P5.status), V-1 (→ PT check), GC copy (→ no longer needed)

**GC writes to REMOVE:** Implementation Results (→ PT §implementation_results), Interface Changes (→ PT §codebase_impact_map update at Gate 6), Gate 6 Record (→ scratch, PT points to gate-record.yaml), Phase 7 Entry Conditions (→ exec-coord/L2 §Downstream Handoff)

#### verification-pipeline

| Gate/Step | GC Operation | GC Sections Read/Written |
|-----------|-------------|--------------------------|
| V-1 (L116) | READ | `global-context.md` exists with `Phase 6: COMPLETE` |
| Phase 7.2 (L149) | COPY | Copy GC-v5 to new session directory |
| Gate 7 On APPROVE (L317) | UPDATE | ADD: `Phase 7: COMPLETE (Gate 7 APPROVED)` |
| Gate 8 On APPROVE (L427) | UPDATE | ADD: `Phase 8: COMPLETE (Gate 8 APPROVED)` |
| Clean Termination (L445-462) | UPDATE | ADD: Phase Pipeline Status (P7/P8), Verification Results, Phase 9 Entry Conditions |

**GC reads to REPLACE:** V-1 (→ PT §phase_status.P6.status), GC copy (→ no longer needed)

**GC writes to REMOVE:** Verification Results (→ PT §verification_summary), Phase 9 Entry Conditions (→ testing-coord/L2 §Downstream Handoff)

**GC writes to KEEP (scratch):** Phase Pipeline Status inline updates (P7, P8)

#### Fork Skills (delivery, rsil-global, rsil-review, permanent-tasks)

| Skill | GC Read | GC Write |
|-------|---------|----------|
| delivery-pipeline | V-1 fallback: "PT exists with Phase 7/8 COMPLETE — OR — GC exists" (L127) | None |
| rsil-global | None | None |
| rsil-review | None | None |
| permanent-tasks | None | None |

**delivery-pipeline note:** GC is a fallback for PT. In the new model, PT is primary. GC fallback is eliminated — if PT doesn't have Phase 7/8 COMPLETE, abort.

---

## 7. Coupling Strength Assessment

### TIGHT Coupling (breaking change = cascade)

| Dependency | Why Tight | Change Impact |
|-----------|-----------|---------------|
| Fork skill `agent:` → agent .md filename | Fork resolution breaks on mismatch | 1 skill + 1 agent .md |
| §10 named agents → agent .md filenames | Policy-enforcement mismatch | CLAUDE.md + agent-common-protocol.md + 3 agent .md |
| PT section headers → all 9 skills | Skills parse PT by header names | All 9 skills + permanent-tasks template |
| L2 §Downstream Handoff format → all coordinators | All coordinators write this; all skills read it | 8 coordinator .md + agent-common-protocol.md |
| Coordinator .md → coordinator-shared-protocol.md | Protocol reference is load-bearing | 8 coordinators + 1 protocol file |

### MEDIUM Coupling (change requires coordination)

| Dependency | Why Medium | Change Impact |
|-----------|-----------|---------------|
| Skill subagent_type → agent .md | Agent catalog has canonical names | Skill + CLAUDE.md agent table |
| PT version chain → skill gate transitions | Version bump must happen at correct gates | All pipeline skills |
| L2 path pattern → PT phase_status.l2_path | Deterministic path: `.agent/teams/{session}/phase-{N}/{coordinator}/L2-summary.md` | All pipeline skills |

### LOOSE Coupling (independent change)

| Dependency | Why Loose | Change Impact |
|-----------|-----------|---------------|
| Fork skill Dynamic Context commands | Resolved before fork, no cross-file dependency | Individual skill only |
| Skill unique workflow content | Self-contained within each skill | Individual skill only |
| Coordinator unique "How to Work" logic | Self-contained within each coordinator .md | Individual coordinator only |

---

## 8. File Change Inventory (Big Bang Scope)

| # | File | Change Type | Dependencies |
|---|------|-------------|-------------|
| 1 | `.claude/skills/brainstorming-pipeline/SKILL.md` | MODIFY: add §C, remove GC writes, update discovery | §4 PT schema, §5 L2 chain |
| 2 | `.claude/skills/agent-teams-write-plan/SKILL.md` | MODIFY: add §C, remove GC reads/writes, update discovery | §4 PT schema, §5 L2 chain |
| 3 | `.claude/skills/plan-validation-pipeline/SKILL.md` | MODIFY: add §C, remove GC reads/writes, update discovery | §4 PT schema, §5 L2 chain |
| 4 | `.claude/skills/agent-teams-execution-plan/SKILL.md` | MODIFY: add §C, remove GC reads/writes, update discovery | §4 PT schema, §5 L2 chain |
| 5 | `.claude/skills/verification-pipeline/SKILL.md` | MODIFY: add §C, remove GC reads/writes, update discovery | §4 PT schema, §5 L2 chain |
| 6 | `.claude/skills/delivery-pipeline/SKILL.md` | MODIFY: add §C, add fork frontmatter, rewrite for fork voice | §3 naming, §4 PT schema |
| 7 | `.claude/skills/rsil-global/SKILL.md` | MODIFY: add §C, add fork frontmatter | §3 naming, §4 PT schema |
| 8 | `.claude/skills/rsil-review/SKILL.md` | MODIFY: add §C, add fork frontmatter | §3 naming, §4 PT schema |
| 9 | `.claude/skills/permanent-tasks/SKILL.md` | MODIFY: add §C, add fork frontmatter, rewrite for fork voice | §3 naming, §4 PT schema |
| 10 | `.claude/agents/pt-manager.md` | CREATE | §3 naming contract |
| 11 | `.claude/agents/delivery-agent.md` | CREATE | §3 naming contract |
| 12 | `.claude/agents/rsil-agent.md` | CREATE | §3 naming contract |
| 13 | `.claude/CLAUDE.md` | MODIFY: §10 fork exception | §3 naming contract |
| 14 | `.claude/references/agent-common-protocol.md` | MODIFY: §Task API exception | §3 naming contract |
| 15-22 | `.claude/agents/{8 coordinators}.md` | MODIFY: Template B convergence | §2 protocol refs |

**Total: 22 files** (9 SKILL + 3 new agent + 1 CLAUDE.md + 1 protocol + 8 coordinator)

---

## Evidence Sources

| Source | Lines Read | Key Extractions |
|--------|:---------:|-----------------|
| brainstorming-pipeline SKILL.md | 613L | GC-v1 create (L230-246), GC-v2 update (L377-387), GC-v3 update (L500-511) |
| agent-teams-write-plan SKILL.md | 362L | GC-v3 read (L91,106,108), GC-v4 write (L263-265), GC embed (L166) |
| plan-validation-pipeline SKILL.md | 434L | GC-v4 read (L91,110,113), GC-v5 conditional write (L312-315) |
| agent-teams-execution-plan SKILL.md | 692L | GC read (L97,119), GC-v5 write (L553-580) |
| verification-pipeline SKILL.md | 575L | GC read (L116), GC writes at G7/G8/termination (L317,427,445-462) |
| delivery-pipeline SKILL.md | 472L | GC fallback read (L127), no GC writes |
| rsil-global SKILL.md | 453L | No GC interaction |
| rsil-review SKILL.md | 549L | No GC interaction |
| permanent-tasks SKILL.md | 280L | No GC interaction |
| interface-architect L3 | 412L | PT schema (§1.3), GC migration map (§4.1), §10 text (§2.2) |
| structure-architect L3 | 754L | Template skeletons (§1.2-1.3), fork frontmatter mapping (§1.3) |
| risk-architect L3 | 662L | Fork agent .md designs (§1), naming contract (§1.1-1.3) |

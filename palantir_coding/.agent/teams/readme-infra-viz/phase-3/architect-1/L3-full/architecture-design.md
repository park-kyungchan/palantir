# README.md Architecture Design — INFRA v9.0 Visualization

## 1. Complete Section Hierarchy

```
# Palantir Development Workspace — Agent Teams INFRA v9.0
  [Badges row]
  [One-liner description in English]
  [Korean subtitle]

  ## Table of Contents

  ## 1. System Architecture
  ## 2. Pipeline Flow
    ### 2.1 Phase Dependency Chain
    ### 2.2 Pipeline Tiers
    ### 2.3 Rollback Paths
  ## 3. Agents (43)
    ### 3.1 Overview
    ### 3.2 Coordinators (8)
    ### 3.3 Workers by Category (35)
      <details> Category 1: Research (3) — P2
      <details> Category 2: Verification (4) — P2b
      <details> Category 3: Architecture (4) — P3
      <details> Category 4: Planning (4) — P4
      <details> Category 5: Validation (3) — P5
      <details> Category 6: Review (5) — P6
      <details> Category 7: Implementation (2) — P6
      <details> Category 8: Testing (2) — P7
      <details> Category 9: Integration (1) — P8
      <details> Category 10: INFRA Quality (4) — X-cut
      <details> Category 11: Impact (1) — P2d/6+
      <details> Category 12: Audit (1) — G3-G8
      <details> Category 13: Monitoring (1) — P6+
      <details> Category 14: Built-in (1) — any
    ### 3.4 Tool Distribution Matrix
  ## 4. Skills (10)
    ### 4.1 Pipeline Phase Coverage
    ### 4.2 Skill Reference
    ### 4.3 Skill-to-Coordinator Mapping
  ## 5. Hooks (4)
    ### 5.1 Lifecycle Events
    ### 5.2 Hook Reference
    ### 5.3 Hook Data Dependencies
  ## 6. References (9)
    ### 6.1 Reference Catalog
    ### 6.2 Consumer Network
  ## 7. Configuration
    ### 7.1 Settings Hierarchy
    ### 7.2 Environment Variables
    ### 7.3 MCP Servers
    ### 7.4 Permissions
  ## 8. Observability (RTD)
  ## 9. Agent Memory
  ## 10. CLAUDE.md Constitution
  ## 11. Directory Tree
    <details> Complete .claude/ file listing (78 files)
  ## 12. Key Concepts
    ### 12.1 L1/L2/L3 Progressive Disclosure
    ### 12.2 PERMANENT Task
    ### 12.3 Ontological Lenses
    ### 12.4 Pipeline Tier Routing
    ### 12.5 Coordinator Management Modes
  ## Version History
```

---

## 2. ASCII Diagram Drafts

### 2.1 Hero Diagram — System Architecture (Section 1)

```
┌──────────────────────── PERMANENT TASK (PT-v{N}) ─────────────────────────┐
│  User Intent · Codebase Impact Map · Architecture Decisions · Constraints │
└──────────────────────────────────┬────────────────────────────────────────┘
                                   │
┌──────────────────────────────────┴────────────────────────────────────────┐
│                        LEAD  (Pipeline Controller)                        │
│  Pure Orchestrator · Spawns Agents · Manages Gates · Never Edits Files    │
│                                                                           │
│  Skills(10) ◄── orchestrate ──► Hooks(4) ──► Observability(RTD)          │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────────────────────┘
   │      │      │      │      │      │      │      │
 ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐ ┌─┴──┐
 │Res │ │Ver │ │Arc │ │Pln │ │Val │ │Exe │ │Tst │ │INF │  8 Coordinators
 │ P2 │ │P2b │ │ P3 │ │ P4 │ │ P5 │ │ P6 │ │P7-8│ │X-ct│  (category mgrs)
 │ 3W │ │ 4W │ │ 3W │ │ 3W │ │ 3W │ │6+W │ │ 3W │ │ 4W │
 └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘ └────┘

 Lead-Direct: dynamic-impact-analyst · execution-monitor · gate-auditor · devils-advocate

┌───────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐
│  References (9)   │  │ Agent Memory (7) │  │  Configuration (3 files)   │
│  Protocols+Stds   │  │ Cross-session    │  │  settings + .claude.json   │
└───────────────────┘  └──────────────────┘  └────────────────────────────┘
```

**Legend (below the diagram in markdown, not in the code block):**

| Abbrev | Coordinator | Phase | Workers |
|--------|------------|-------|---------|
| Res | research-coordinator | P2 | 3: codebase-researcher, external-researcher, auditor |
| Ver | verification-coordinator | P2b | 4: static/relational/behavioral/impact-verifier |
| Arc | architecture-coordinator | P3 | 3: structure/interface/risk-architect |
| Pln | planning-coordinator | P4 | 3: decomposition/interface/strategy-planner |
| Val | validation-coordinator | P5 | 3: correctness/completeness/robustness-challenger |
| Exe | execution-coordinator | P6 | 6+: implementer(s), infra-implementer, 4 reviewers |
| Tst | testing-coordinator | P7-8 | 3: tester, contract-tester, integrator |
| INF | infra-quality-coordinator | X-cut | 4: infra-static/relational/behavioral/impact-analyst |

### 2.2 Pipeline Flow Diagram (Section 2.1)

```
╔═══════════════════════════════════════════════════════════════════════════╗
║  PRE (70-80% effort)                                                     ║
║                                                                          ║
║  P0 ─── Lead: Tier Classification ──────────── permanent-tasks skill     ║
║         (TRIVIAL / STANDARD / COMPLEX)                                   ║
║                                                                          ║
║  P1 ─── Lead: Discovery ───────────────────── brainstorming-pipeline     ║
║                                                                          ║
║  P2 ─── research-coordinator ──────────────── brainstorming-pipeline     ║
║         ├── codebase-researcher                                          ║
║         ├── external-researcher                                          ║
║         └── auditor                                                      ║
║                                                                          ║
║  P2b ── verification-coordinator ──────────── (COMPLEX only)             ║
║         ├── static-verifier     (ARE)                                    ║
║         ├── relational-verifier (RELATE)     can overlap with P2         ║
║         ├── behavioral-verifier (DO)                                     ║
║         └── impact-verifier     (IMPACT)                                 ║
║                                                                          ║
║  P2d ── dynamic-impact-analyst ────────────── (Lead-direct)              ║
║         (change cascade prediction)          can overlap with P3         ║
║                                                                          ║
║  P3 ─── architecture-coordinator ──────────── brainstorming-pipeline     ║
║         ├── structure-architect  (ARE)        (COMPLEX)                  ║
║         ├── interface-architect  (RELATE)     OR architect (STD/TRIV)    ║
║         └── risk-architect       (IMPACT)                                ║
║                                                                          ║
║  P4 ─── planning-coordinator ──────────────── agent-teams-write-plan     ║
║         ├── decomposition-planner             (COMPLEX)                  ║
║         ├── interface-planner                 OR plan-writer (STD/TRIV)  ║
║         └── strategy-planner                                             ║
║                                                                          ║
║  P5 ─── validation-coordinator ────────────── plan-validation-pipeline   ║
║         ├── correctness-challenger            (COMPLEX)                  ║
║         ├── completeness-challenger           OR devils-advocate (STD)   ║
║         └── robustness-challenger                                        ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  EXEC                                                                    ║
║                                                                          ║
║  P6 ─── execution-coordinator ─────────────── agent-teams-execution-plan ║
║         ├── implementer(s)     [1-4]                                     ║
║         ├── infra-implementer  [0-2]                                     ║
║         ├── spec-reviewer      (Stage 1 review)                          ║
║         ├── code-reviewer      (Stage 2 review)                          ║
║         ├── contract-reviewer                                            ║
║         └── regression-reviewer                                          ║
║                                                                          ║
║  P6+ ── execution-monitor ─────────────────── (Lead-direct, parallel)    ║
║         (drift, conflict, budget detection)                              ║
║                                                                          ║
║  P7 ─── testing-coordinator ───────────────── verification-pipeline      ║
║         ├── tester(s)      [1-2]                                         ║
║         └── contract-tester [1]                                          ║
║                                                                          ║
║  P8 ─── testing-coordinator ───────────────── verification-pipeline      ║
║         └── integrator [1]                    (conditional: 2+ impl)     ║
╠═══════════════════════════════════════════════════════════════════════════╣
║  POST                                                                    ║
║                                                                          ║
║  P9 ─── Lead-only ─────────────────────────── delivery-pipeline          ║
║         (consolidate, commit, archive, MEMORY)                           ║
║                                                                          ║
║  Post ── Lead-only ────────────────────────── rsil-global (auto-invoke)  ║
║          infra-quality-coordinator             rsil-review (on-demand)   ║
║          ├── infra-static-analyst   (ARE)                                ║
║          ├── infra-relational-analyst(RELATE)                            ║
║          ├── infra-behavioral-analyst(DO)                                ║
║          └── infra-impact-analyst   (IMPACT)                             ║
╚═══════════════════════════════════════════════════════════════════════════╝

Gate Points: G0─G1─G2─G2b─G3─G4─G5─G6─G7─G8─G9
             [+ gate-auditor at G3-G8 for COMPLEX tier]
```

### 2.3 Pipeline Tiers Table (Section 2.2)

| Tier | Criteria | Phases | Gate Depth |
|------|----------|--------|------------|
| TRIVIAL | ≤2 files, single module | P0→P6→P9 | 3-item |
| STANDARD | 3-8 files, 1-2 modules | P0→P2→P3→P4→P6→P7→P9 | 5-item |
| COMPLEX | >8 files, 3+ modules | All phases P0→P9 | 7-10 item |

**Tier branching visualization (inline with the tiers table):**

```
TRIVIAL:    P0 ──────────────────────────── P6 ──────────────── P9
STANDARD:   P0 ── P2 ── P3 ── P4 ────────── P6 ── P7 ───────── P9
COMPLEX:    P0 ── P2 ── P2b ── P2d ── P3 ── P4 ── P5 ── P6 ── P6+ ── P7 ── P8 ── P9 ── Post
```

### 2.4 Rollback Paths (Section 2.3)

```
P5 ──FAIL──► P4  (critical design flaws)
P6 ──FAIL──► P4  (design inadequacy)
P6 ──FAIL──► P3  (architecture insufficient — requires user confirm)
P7 ──FAIL──► P6  (code changes needed)
P7 ──FAIL──► P4  (design flaws revealed by tests)
P8 ──FAIL──► P6  (implementation fixes needed)

Rule: Rollback >2 phases requires user confirmation
```

### 2.5 Skill Coverage Timeline (Section 4.1)

```
Phase:  P0    P1    P2    P3    P4    P5    P6   P6+   P7    P8    P9   Post

        ├─────brainstorming-pipeline─────┤
                                   ├──write-plan──┤
                                               ├─validation─┤
                                                      ├──execution-plan──┤
                                                                  ├─verification──┤
                                                                              ├delivery┤
                                                                                    ├rsil-global┤
        ├──────────────────── permanent-tasks (cross-cutting) ──────────────────────┤
                              rsil-review (any phase, on-demand)
                              palantir-dev (standalone, not pipeline)
```

### 2.6 Hook Lifecycle Diagram (Section 5.1)

```
Session Timeline
════════════════════════════════════════════════════════════════════════

[Agent Spawn]                 [Tool Call]              [Compaction]
     │                             │                        │
     ▼                             ▼                        ▼
on-subagent-start.sh      on-rtd-post-tool.sh       on-pre-compact.sh
(sync, 10s)               (async, 5s)               (sync, 30s)
• Context injection        • JSONL event capture      • Task snapshot
• Session registry         • Agent name resolve       • Missing L1/L2 warn
• Lifecycle log            • DP association           • RTD state snapshot
                                                           │
                                                           ▼
                                                    on-session-compact.sh
                                                    (sync, 15s, once)
                                                    • Recovery context
                                                    • RTD-enhanced or generic
```

### 2.7 Hook Data Dependencies (Section 5.3)

```
on-subagent-start.sh ──writes──► session-registry.json ──read-by──► on-rtd-post-tool.sh
                                                                     (resolves agent name)

Lead ──writes──► current-dp.txt ──read-by──► on-rtd-post-tool.sh
                                              (associates DP with events)

on-pre-compact.sh ──reads──► rtd-index.md ──snapshot──► snapshots/
on-session-compact.sh ──reads──► rtd-index.md ──injects──► recovery context
```

### 2.8 Reference Consumer Network (Section 6.2)

```
Reference                          Consumers                         Criticality
──────────────────────────────────────────────────────────────────────────────────
agent-common-protocol.md ─────────► ALL 43 agents                    CRITICAL
task-api-guideline.md ────────────► ALL 43 agents (TaskList/TaskGet) HIGH
agent-catalog.md ─────────────────► Lead (routing decisions)         CRITICAL
gate-evaluation-standard.md ──────► Lead, gate-auditor, all skills   HIGH
coordinator-shared-protocol.md ───► 8 coordinators                   HIGH
ontological-lenses.md ────────────► 4 INFRA + 3 arch agents          MEDIUM
pipeline-rollback-protocol.md ────► 3 skills (validation/exec/verif) MEDIUM
layer-boundary-model.md ──────────► Lead, RSIL skills                LOW
ontology-communication-protocol.md► Lead (domain-specific)           LOW
```

### 2.9 Configuration Hierarchy (Section 7.1)

```
.claude.json (project-level)
│  MCP servers: github, context7, sequential-thinking, tavily
│
▼ merged with
.claude/settings.json (team-level)
│  env vars, hooks(4), plugins(2), language:Korean, model:opus-4-6
│  permissions.deny: protected files + blocked commands
│
▼ overridden by
.claude/settings.local.json (local overrides)
   permissions.allow: Bash, MCP tools, TaskCreate/TaskUpdate
   MCP JSON servers(8): oda-ontology, tavily, cow-*, etc.
```

### 2.10 Observability Event Flow (Section 8)

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│  Lead writes │────►│ .current-project │────►│ All hooks read project  │
│  at pipeline │     │ .agent/obs/      │     │ slug for file paths     │
│  start       │     └──────────────────┘     └─────────────────────────┘
└──────────────┘

┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│  Lead writes │────►│  current-dp.txt  │────►│ PostToolUse associates  │
│  before DPs  │     │                  │     │ events with decisions   │
└──────────────┘     └──────────────────┘     └─────────────────────────┘

┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│ SubagentStart│────►│ session-registry │────►│ PostToolUse resolves    │
│ hook fires   │     │   .json          │     │ session → agent name    │
└──────────────┘     └──────────────────┘     └─────────────────────────┘

┌──────────────┐     ┌──────────────────┐     ┌─────────────────────────┐
│ PostToolUse  │────►│ events/{sid}     │────►│ execution-monitor reads │
│ captures all │     │   .jsonl         │     │ for drift detection     │
│ tool calls   │     └──────────────────┘     └─────────────────────────┘
```

---

## 3. Table Format Templates

### 3.1 Agent Per-Category Table (inside collapsible)

```markdown
<details>
<summary><strong>Category N: {Name} ({count} agents) — Phase {P}</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| agent-name | NN | Read, Glob, Grep, ... | One-line description |

</details>
```

### 3.2 Coordinator Overview Table

```markdown
| Coordinator | Phase | Workers Managed | MaxTurns |
|-------------|-------|-----------------|----------|
| research-coordinator | P2 | codebase-researcher, external-researcher, auditor | 50 |
```

### 3.3 Skill Reference Table

```markdown
| Skill | Phase | Lines | Coordinator | Description |
|-------|-------|-------|-------------|-------------|
| brainstorming-pipeline | P0-3 | 490 | research-coordinator | Feature to architecture |
```

### 3.4 Hook Reference Table

```markdown
| Event | Script | Mode | Timeout | Purpose |
|-------|--------|------|---------|---------|
| SubagentStart | on-subagent-start.sh | sync | 10s | Context injection |
```

### 3.5 Reference Catalog Table

```markdown
| Document | Version | Lines | Decision Source | Primary Consumers |
|----------|---------|-------|-----------------|-------------------|
| agent-catalog.md | v3.0 | 1,489 | D-002, D-005 | Lead |
```

### 3.6 Tool Distribution Matrix

```markdown
| Tool | Workers | Coordinators | Total |
|------|---------|--------------|-------|
| Read | 35 | 8 | 43 |
| Edit | 5 | 0 | 5 |
| Bash | 4 | 0 | 4 |
```

### 3.7 Environment Variables Table

```markdown
| Variable | Value | Purpose |
|----------|-------|---------|
| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | "1" | Enable Agent Teams |
```

### 3.8 CLAUDE.md Section Map Table

```markdown
| Section | Title | Content Summary |
|---------|-------|-----------------|
| 0 | Language Policy | Korean user-facing, English technical |
```

### 3.9 Decision Integration Table

```markdown
| Decision | Title | Integrated In |
|----------|-------|---------------|
| D-001 | Pipeline Tiers | CLAUDE.md §2, all skills |
```

---

## 4. GitHub Rendering Decisions

### 4.1 Code Blocks
- All ASCII diagrams: triple backticks with NO language tag
  ```
  (diagram here)
  ```
- Language-tagged blocks only for actual code (bash, yaml, markdown)

### 4.2 Collapsible Sections
Total: 16 collapsible `<details>` sections:
- 14 agent categories (Section 3.3) — default closed
- 1 complete directory tree (Section 11) — default closed
- 1 detailed pipeline diagram (Section 2.1) — default OPEN

Format:
```html
<details>
<summary><strong>Section Title (key stat)</strong></summary>

Content here (markdown renders inside details)

</details>
```

Important: blank line after `<summary>` tag and before closing `</details>` for markdown rendering.

### 4.3 Badges
Top of file, below title:

```markdown
![Agents](https://img.shields.io/badge/Agents-43-blue)
![Skills](https://img.shields.io/badge/Skills-10-green)
![Hooks](https://img.shields.io/badge/Hooks-4-orange)
![References](https://img.shields.io/badge/References-9-purple)
![Files](https://img.shields.io/badge/Files-78-red)
![Lines](https://img.shields.io/badge/Lines-~10K-lightgrey)
![Version](https://img.shields.io/badge/INFRA-v9.0-brightgreen)
```

### 4.4 Table of Contents
Manual markdown links. Example:
```markdown
## Table of Contents

- [1. System Architecture](#1-system-architecture)
- [2. Pipeline Flow](#2-pipeline-flow)
  - [2.1 Phase Dependency Chain](#21-phase-dependency-chain)
  - [2.2 Pipeline Tiers](#22-pipeline-tiers)
  ...
```

GitHub auto-generates anchors from headings: lowercase, spaces→hyphens, strip special chars.

### 4.5 No Nested Details
`<details>` inside `<details>` renders inconsistently across GitHub clients. All collapsible sections are single-depth only.

### 4.6 Horizontal Rules
Use `---` between major sections for visual separation. Not inside collapsible sections.

---

## 5. Complete File Coverage Mapping

Every one of the 78 infrastructure files appears in at least one section:

### Agents (43 files) → Section 3

| File | Category Section |
|------|------------------|
| `.claude/agents/codebase-researcher.md` | 3.3 Cat 1: Research |
| `.claude/agents/external-researcher.md` | 3.3 Cat 1: Research |
| `.claude/agents/auditor.md` | 3.3 Cat 1: Research |
| `.claude/agents/static-verifier.md` | 3.3 Cat 2: Verification |
| `.claude/agents/relational-verifier.md` | 3.3 Cat 2: Verification |
| `.claude/agents/behavioral-verifier.md` | 3.3 Cat 2: Verification |
| `.claude/agents/impact-verifier.md` | 3.3 Cat 2: Verification |
| `.claude/agents/structure-architect.md` | 3.3 Cat 3: Architecture |
| `.claude/agents/interface-architect.md` | 3.3 Cat 3: Architecture |
| `.claude/agents/risk-architect.md` | 3.3 Cat 3: Architecture |
| `.claude/agents/architect.md` | 3.3 Cat 3: Architecture (legacy) |
| `.claude/agents/decomposition-planner.md` | 3.3 Cat 4: Planning |
| `.claude/agents/interface-planner.md` | 3.3 Cat 4: Planning |
| `.claude/agents/strategy-planner.md` | 3.3 Cat 4: Planning |
| `.claude/agents/plan-writer.md` | 3.3 Cat 4: Planning (legacy) |
| `.claude/agents/correctness-challenger.md` | 3.3 Cat 5: Validation |
| `.claude/agents/completeness-challenger.md` | 3.3 Cat 5: Validation |
| `.claude/agents/robustness-challenger.md` | 3.3 Cat 5: Validation |
| `.claude/agents/devils-advocate.md` | 3.3 Cat 6: Review |
| `.claude/agents/spec-reviewer.md` | 3.3 Cat 6: Review |
| `.claude/agents/code-reviewer.md` | 3.3 Cat 6: Review |
| `.claude/agents/contract-reviewer.md` | 3.3 Cat 6: Review |
| `.claude/agents/regression-reviewer.md` | 3.3 Cat 6: Review |
| `.claude/agents/implementer.md` | 3.3 Cat 7: Implementation |
| `.claude/agents/infra-implementer.md` | 3.3 Cat 7: Implementation |
| `.claude/agents/tester.md` | 3.3 Cat 8: Testing |
| `.claude/agents/contract-tester.md` | 3.3 Cat 8: Testing |
| `.claude/agents/integrator.md` | 3.3 Cat 9: Integration |
| `.claude/agents/infra-static-analyst.md` | 3.3 Cat 10: INFRA Quality |
| `.claude/agents/infra-relational-analyst.md` | 3.3 Cat 10: INFRA Quality |
| `.claude/agents/infra-behavioral-analyst.md` | 3.3 Cat 10: INFRA Quality |
| `.claude/agents/infra-impact-analyst.md` | 3.3 Cat 10: INFRA Quality |
| `.claude/agents/dynamic-impact-analyst.md` | 3.3 Cat 11: Impact |
| `.claude/agents/gate-auditor.md` | 3.3 Cat 12: Audit |
| `.claude/agents/execution-monitor.md` | 3.3 Cat 13: Monitoring |
| `.claude/agents/research-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/verification-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/architecture-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/planning-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/validation-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/execution-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/testing-coordinator.md` | 3.2 Coordinators |
| `.claude/agents/infra-quality-coordinator.md` | 3.2 Coordinators |

### Skills (10 files) → Section 4

| File | Skill Table Row |
|------|-----------------|
| `.claude/skills/brainstorming-pipeline/SKILL.md` | 4.2 Row 1 |
| `.claude/skills/agent-teams-write-plan/SKILL.md` | 4.2 Row 2 |
| `.claude/skills/plan-validation-pipeline/SKILL.md` | 4.2 Row 3 |
| `.claude/skills/agent-teams-execution-plan/SKILL.md` | 4.2 Row 4 |
| `.claude/skills/verification-pipeline/SKILL.md` | 4.2 Row 5 |
| `.claude/skills/delivery-pipeline/SKILL.md` | 4.2 Row 6 |
| `.claude/skills/rsil-global/SKILL.md` | 4.2 Row 7 |
| `.claude/skills/rsil-review/SKILL.md` | 4.2 Row 8 |
| `.claude/skills/permanent-tasks/SKILL.md` | 4.2 Row 9 |
| `.claude/skills/palantir-dev/SKILL.md` | 4.2 Row 10 |

### Hooks (4 files) → Section 5

| File | Hook Table Row |
|------|----------------|
| `.claude/hooks/on-subagent-start.sh` | 5.2 Row 1 |
| `.claude/hooks/on-pre-compact.sh` | 5.2 Row 2 |
| `.claude/hooks/on-session-compact.sh` | 5.2 Row 3 |
| `.claude/hooks/on-rtd-post-tool.sh` | 5.2 Row 4 |

### References (9 files) → Section 6

| File | Reference Table Row |
|------|---------------------|
| `.claude/references/agent-catalog.md` | 6.1 Row 1 |
| `.claude/references/agent-common-protocol.md` | 6.1 Row 2 |
| `.claude/references/coordinator-shared-protocol.md` | 6.1 Row 3 |
| `.claude/references/gate-evaluation-standard.md` | 6.1 Row 4 |
| `.claude/references/ontological-lenses.md` | 6.1 Row 5 |
| `.claude/references/task-api-guideline.md` | 6.1 Row 6 |
| `.claude/references/layer-boundary-model.md` | 6.1 Row 7 |
| `.claude/references/ontology-communication-protocol.md` | 6.1 Row 8 |
| `.claude/references/pipeline-rollback-protocol.md` | 6.1 Row 9 |

### Settings + Config (3 files) → Section 7

| File | Section |
|------|---------|
| `.claude/settings.json` | 7.1, 7.2, 7.4 |
| `.claude/settings.local.json` | 7.1, 7.3, 7.4 |
| `.claude.json` | 7.1, 7.3 |

### CLAUDE.md (1 file) → Section 10

| File | Section |
|------|---------|
| `.claude/CLAUDE.md` | 10 (full section map + decision matrix) |

### Agent Memory (8 files) → Section 9

| File | Memory Table Row |
|------|------------------|
| `.claude/agent-memory/implementer/MEMORY.md` | 9 Row 1 |
| `.claude/agent-memory/tester/MEMORY.md` | 9 Row 2 |
| `.claude/agent-memory/integrator/MEMORY.md` | 9 Row 3 |
| `.claude/agent-memory/researcher/MEMORY.md` | 9 Row 4 |
| `.claude/agent-memory/devils-advocate/MEMORY.md` | 9 Row 5 |
| `.claude/agent-memory/rsil/MEMORY.md` | 9 Row 6 |
| `.claude/agent-memory/architect/MEMORY.md` | 9 Row 7 |
| `.claude/agent-memory/architect/lead-arch-redesign.md` | 9 Row 8 (topic file) |

**Total: 43 + 10 + 4 + 9 + 3 + 1 + 8 = 78 files. All covered.**

---

## 6. Estimated README Length

| Section | Lines | Collapsible | Visible Lines |
|---------|-------|-------------|---------------|
| Title + badges + ToC | 30 | No | 30 |
| 1. System Architecture | 80 | No | 80 |
| 2. Pipeline Flow | 90 | Diagram open | 90 |
| 3. Agents (43) | 255 | 14 categories closed | ~50 |
| 4. Skills (10) | 60 | No | 60 |
| 5. Hooks (4) | 65 | No | 65 |
| 6. References (9) | 65 | No | 65 |
| 7. Configuration | 60 | No | 60 |
| 8. Observability | 45 | No | 45 |
| 9. Agent Memory | 30 | No | 30 |
| 10. CLAUDE.md | 45 | No | 45 |
| 11. Directory Tree | 85 | Closed | ~5 |
| 12. Key Concepts | 60 | No | 60 |
| Version History | 15 | No | 15 |
| **Total** | **~985** | | **~700** |

Estimated total: ~985 lines (full), ~700 lines visible with collapsible sections closed.

---

## 7. Architecture Decisions Summary

| AD | Decision | Rationale | Alternative Rejected |
|----|----------|-----------|---------------------|
| AD-1 | Architecture-First ordering | Visual grasp before detail | Concept-first (requires reading abstractions before seeing system) |
| AD-2 | Collapsible `<details>` for dense content | 14 categories = ~205 hidden lines | Single mega-table (horizontal scroll, overwhelming) |
| AD-3 | 4-5 column table max | No horizontal scroll on standard GitHub | 8-column full tables (poor mobile experience) |
| AD-4 | English-primary, Korean parenthetical | Monospace alignment requires single-width chars | Full bilingual (doubles every heading, breaks diagrams) |
| AD-5 | Hero simplified ~25 lines | Must fit one screen | Full 60-line detailed pipeline as hero (too much for first view) |
| AD-6 | Pipeline Tiers in Section 2 | Context-adjacent > separate section | Separate "Concepts" section before architecture (breaks visual-first) |
| AD-7 | 78-file coverage guarantee via Directory Tree | Section 11 = completeness verification | Trust implicit coverage (risk of silent omission) |

---

## 8. Implementer Guidance

### Content to Generate

The implementer should produce a single file: `/home/palantir/README.md`

The implementer must:
1. Read ALL research L3 files for accurate data (agent inventory, skills inventory, infrastructure inventory, relationship map)
2. Follow this architecture design for section ordering, diagram specifications, and table formats
3. Verify all 78 files appear in the Directory Tree (Section 11) — use the coverage mapping in Section 5 above as a checklist
4. Test mental rendering: every `<details>` tag has proper blank lines, every code block is closed, every table has header separator row

### Data Sources per Section

| Section | Primary Data Source |
|---------|---------------------|
| 1. System Architecture | This design (hero diagram draft) |
| 2. Pipeline Flow | relationship-map.md §4 + this design |
| 3. Agents | agent-inventory.md (complete data) |
| 4. Skills | skills-inventory.md (complete data) |
| 5. Hooks | infrastructure-inventory.md §1 |
| 6. References | infrastructure-inventory.md §2 |
| 7. Configuration | infrastructure-inventory.md §3 |
| 8. Observability | relationship-map.md §5 |
| 9. Agent Memory | infrastructure-inventory.md §5 |
| 10. CLAUDE.md | infrastructure-inventory.md §4 |
| 11. Directory Tree | Glob `.claude/**/*` for current state |
| 12. Key Concepts | CLAUDE.md §2, §6, §10 + references |

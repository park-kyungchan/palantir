# Palantir Development Workspace — Agent Teams INFRA v9.0

> Opus 4.6-native multi-agent orchestration system for Claude Code
> (Opus 4.6 네이티브 다중 에이전트 오케스트레이션 시스템)

![Version](https://img.shields.io/badge/INFRA-v9.0-brightgreen)
![Agents](https://img.shields.io/badge/Agents-43-blue)
![Skills](https://img.shields.io/badge/Skills-10-green)
![Hooks](https://img.shields.io/badge/Hooks-4-orange)
![References](https://img.shields.io/badge/References-9-purple)
![Lines](https://img.shields.io/badge/Lines-~10K-lightgrey)

---

## Table of Contents

- [1. System Architecture](#1-system-architecture)
- [2. Pipeline Flow](#2-pipeline-flow)
  - [2.1 Phase Dependency Chain](#21-phase-dependency-chain)
  - [2.2 Pipeline Tiers](#22-pipeline-tiers)
  - [2.3 Rollback Paths](#23-rollback-paths)
- [3. Agents (43)](#3-agents-43)
  - [3.1 Overview](#31-overview)
  - [3.2 Coordinators (8)](#32-coordinators-8)
  - [3.3 Workers by Category (35)](#33-workers-by-category-35)
  - [3.4 Tool Distribution Matrix](#34-tool-distribution-matrix)
- [4. Skills (10)](#4-skills-10)
  - [4.1 Pipeline Phase Coverage](#41-pipeline-phase-coverage)
  - [4.2 Skill Reference](#42-skill-reference)
- [5. Hooks (4)](#5-hooks-4)
  - [5.1 Lifecycle Events](#51-lifecycle-events)
  - [5.2 Hook Reference](#52-hook-reference)
  - [5.3 Hook Data Dependencies](#53-hook-data-dependencies)
- [6. References (9)](#6-references-9)
  - [6.1 Reference Catalog](#61-reference-catalog)
  - [6.2 Consumer Network](#62-consumer-network)
- [7. Configuration](#7-configuration)
  - [7.1 Settings Hierarchy](#71-settings-hierarchy)
  - [7.2 Environment Variables](#72-environment-variables)
  - [7.3 MCP Servers](#73-mcp-servers)
  - [7.4 Permissions](#74-permissions)
- [8. Observability (RTD)](#8-observability-rtd)
- [9. Agent Memory](#9-agent-memory)
- [10. CLAUDE.md Constitution](#10-claudemd-constitution)
- [11. Directory Tree](#11-directory-tree)
- [12. Key Concepts](#12-key-concepts)
  - [12.1 L1/L2/L3 Progressive Disclosure](#121-l1l2l3-progressive-disclosure)
  - [12.2 PERMANENT Task](#122-permanent-task)
  - [12.3 Ontological Lenses](#123-ontological-lenses)
  - [12.4 Pipeline Tier Routing](#124-pipeline-tier-routing)
  - [12.5 Coordinator Management Modes](#125-coordinator-management-modes)
- [Version History](#version-history)

---

## 1. System Architecture

```
+--------------------- PERMANENT TASK (PT-v{N}) ----------------------+
|  User Intent . Codebase Impact Map . Architecture Decisions . Constraints  |
+-----------------------------------+------------------------------------+
                                    |
+-----------------------------------+------------------------------------+
|                        LEAD  (Pipeline Controller)                     |
|  Pure Orchestrator . Spawns Agents . Manages Gates . Never Edits Files |
|                                                                        |
|  Skills(10) <-- orchestrate --> Hooks(4) --> Observability(RTD)        |
+--+------+------+------+------+------+------+------+-------------------+
   |      |      |      |      |      |      |      |
 +-+-+  +-+-+  +-+-+  +-+-+  +-+-+  +-+-+  +-+-+  +-+-+
 |Res|  |Ver|  |Arc|  |Pln|  |Val|  |Exe|  |Tst|  |INF|  8 Coordinators
 | P2|  |P2b|  | P3|  | P4|  | P5|  | P6|  |P78|  |Xct|  (category mgrs)
 | 3W|  | 4W|  | 4W|  | 4W|  | 3W|  |6+W|  | 3W|  | 4W|
 +---+  +---+  +---+  +---+  +---+  +---+  +---+  +---+

 Lead-Direct: dynamic-impact-analyst . execution-monitor
              gate-auditor . devils-advocate

+-------------------+  +------------------+  +----------------------------+
|  References (9)   |  | Agent Memory (8) |  |  Configuration (3 files)   |
|  Protocols+Stds   |  | Cross-session    |  |  settings + .claude.json   |
+-------------------+  +------------------+  +----------------------------+
```

| Abbrev | Coordinator | Phase | Workers |
|--------|-------------|-------|---------|
| Res | research-coordinator | P2 | codebase-researcher, external-researcher, auditor |
| Ver | verification-coordinator | P2b | static/relational/behavioral/impact-verifier |
| Arc | architecture-coordinator | P3 | structure/interface/risk-architect, architect (legacy) |
| Pln | planning-coordinator | P4 | decomposition/interface/strategy-planner, plan-writer (legacy) |
| Val | validation-coordinator | P5 | correctness/completeness/robustness-challenger |
| Exe | execution-coordinator | P6 | implementer(s), infra-implementer, 4 reviewers |
| Tst | testing-coordinator | P7-8 | tester, contract-tester, integrator |
| INF | infra-quality-coordinator | X-cut | infra-static/relational/behavioral/impact-analyst |

---

## 2. Pipeline Flow

### 2.1 Phase Dependency Chain

<details open>
<summary><strong>Full Pipeline Diagram (PRE / EXEC / POST)</strong></summary>

```
+=========================================================================+
|  PRE (70-80% effort)                                                    |
|                                                                         |
|  P0 --- Lead: Tier Classification ----------- permanent-tasks skill     |
|         (TRIVIAL / STANDARD / COMPLEX)                                  |
|                                                                         |
|  P1 --- Lead: Discovery -------------------- brainstorming-pipeline     |
|                                                                         |
|  P2 --- research-coordinator --------------- brainstorming-pipeline     |
|         +-- codebase-researcher                                         |
|         +-- external-researcher                                         |
|         +-- auditor                                                     |
|                                                                         |
|  P2b -- verification-coordinator ----------- (COMPLEX only)             |
|         +-- static-verifier     (ARE)                                   |
|         +-- relational-verifier (RELATE)    can overlap with P2         |
|         +-- behavioral-verifier (DO)                                    |
|         +-- impact-verifier     (IMPACT)                                |
|                                                                         |
|  P2d -- dynamic-impact-analyst ------------- (Lead-direct)              |
|         (change cascade prediction)         can overlap with P3         |
|                                                                         |
|  P3 --- architecture-coordinator ----------- brainstorming-pipeline     |
|         +-- structure-architect  (ARE)       (COMPLEX)                  |
|         +-- interface-architect  (RELATE)    OR architect (STD/TRIV)    |
|         +-- risk-architect       (IMPACT)                               |
|                                                                         |
|  P4 --- planning-coordinator --------------- agent-teams-write-plan     |
|         +-- decomposition-planner            (COMPLEX)                  |
|         +-- interface-planner                OR plan-writer (STD/TRIV)  |
|         +-- strategy-planner                                            |
|                                                                         |
|  P5 --- validation-coordinator ------------- plan-validation-pipeline   |
|         +-- correctness-challenger           (COMPLEX)                  |
|         +-- completeness-challenger          OR devils-advocate (STD)   |
|         +-- robustness-challenger                                       |
+=====+===================================================================+
      |
+=====+=================================================================+
|  EXEC                                                                 |
|                                                                       |
|  P6 --- execution-coordinator ------------ agent-teams-execution-plan |
|         +-- implementer(s)     [1-4]                                  |
|         +-- infra-implementer  [0-2]                                  |
|         +-- spec-reviewer      (Stage 1 review)                       |
|         +-- code-reviewer      (Stage 2 review)                       |
|         +-- contract-reviewer                                         |
|         +-- regression-reviewer                                       |
|                                                                       |
|  P6+ -- execution-monitor ---------------- (Lead-direct, parallel)    |
|         (drift, conflict, budget detection)                           |
|                                                                       |
|  P7 --- testing-coordinator --------------- verification-pipeline     |
|         +-- tester(s)      [1-2]                                      |
|         +-- contract-tester [1]                                       |
|                                                                       |
|  P8 --- testing-coordinator --------------- verification-pipeline     |
|         +-- integrator [1]                  (conditional: 2+ impl)    |
+=====+=================================================================+
      |
+=====+=================================================================+
|  POST                                                                 |
|                                                                       |
|  P9 --- Lead-only ------------------------- delivery-pipeline         |
|         (consolidate, commit, archive)                                |
|                                                                       |
|  Post - Lead-only ------------------------- rsil-global (auto)        |
|         infra-quality-coordinator           rsil-review (on-demand)   |
|         +-- infra-static-analyst   (ARE)                              |
|         +-- infra-relational-analyst(RELATE)                          |
|         +-- infra-behavioral-analyst(DO)                              |
|         +-- infra-impact-analyst   (IMPACT)                           |
+===================================================================+

Gate Points: G0-G1-G2-G2b-G3-G4-G5-G6-G7-G8-G9
             [+ gate-auditor at G3-G8 for COMPLEX tier]
```

</details>

### 2.2 Pipeline Tiers

| Tier | Criteria | Phases | Gate Depth |
|------|----------|--------|------------|
| TRIVIAL | <=2 files, single module | P0->P6->P9 | 3-item |
| STANDARD | 3-8 files, 1-2 modules | P0->P2->P3->P4->P6->P7->P9 | 5-item |
| COMPLEX | >8 files, 3+ modules | All phases P0->P9 | 7-10 item |

```
TRIVIAL:    P0 --------------------------------- P6 ------------------- P9
STANDARD:   P0 -- P2 -- P3 -- P4 -------------- P6 -- P7 ------------ P9
COMPLEX:    P0 -- P2 -- P2b -- P2d -- P3 -- P4 -- P5 -- P6 -- P6+ -- P7 -- P8 -- P9 -- Post
```

### 2.3 Rollback Paths

```
P5 --FAIL--> P4  (critical design flaws)
P6 --FAIL--> P4  (design inadequacy)
P6 --FAIL--> P3  (architecture insufficient -- requires user confirm)
P7 --FAIL--> P6  (code changes needed)
P7 --FAIL--> P4  (design flaws revealed by tests)
P8 --FAIL--> P6  (implementation fixes needed)

Rule: Rollback >2 phases requires user confirmation
```

---

## 3. Agents (43)

### 3.1 Overview

| Metric | Value |
|--------|-------|
| Total agents | 43 |
| Workers | 35 |
| Coordinators | 8 |
| Categories | 14 |
| Min maxTurns | 15 (gate-auditor) |
| Max maxTurns | 100 (implementer, integrator) |
| Agents with Bash | 4 |
| Agents with Edit | 5 |
| Agents with Write | 39 |
| Agents with WebSearch | 5 |

### 3.2 Coordinators (8)

| Coordinator | Phase | Workers | MaxTurns |
|-------------|-------|---------|----------|
| research-coordinator | P2 | codebase-researcher, external-researcher, auditor | 50 |
| verification-coordinator | P2b | static/relational/behavioral/impact-verifier | 40 |
| architecture-coordinator | P3 | structure/interface/risk-architect | 40 |
| planning-coordinator | P4 | decomposition/interface/strategy-planner | 40 |
| validation-coordinator | P5 | correctness/completeness/robustness-challenger | 40 |
| execution-coordinator | P6 | implementer(s), infra-implementer, 4 reviewers | 80 |
| testing-coordinator | P7-8 | tester, contract-tester, integrator | 50 |
| infra-quality-coordinator | X-cut | 4 infra analysts (ARE/RELATE/DO/IMPACT) | 40 |

All coordinators share: Read, Glob, Grep, Write, sequential-thinking. They follow `coordinator-shared-protocol.md` and `agent-common-protocol.md`.

### 3.3 Workers by Category (35)

<details>
<summary><strong>Category 1: Research (3 agents) -- Phase 2</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| codebase-researcher | 50 | Read, Glob, Grep, Write, seq-thinking | Local codebase exploration |
| external-researcher | 50 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily, context7 | Web-based documentation research |
| auditor | 50 | Read, Glob, Grep, Write, seq-thinking | Systematic artifact analysis, inventory/gap |

</details>

<details>
<summary><strong>Category 2: Verification (4 agents) -- Phase 2b</strong></summary>

| Agent | MaxTurns | Lens | Key Tools | Description |
|-------|----------|------|-----------|-------------|
| static-verifier | 40 | ARE | Read, Glob, Grep, Write, WebSearch, tavily | Structural/schema claims |
| relational-verifier | 40 | RELATE | Read, Glob, Grep, Write, WebSearch, tavily | Relationship/dependency claims |
| behavioral-verifier | 40 | DO | Read, Glob, Grep, Write, WebSearch, tavily | Action/rule/behavior claims |
| impact-verifier | 40 | IMPACT | Read, Glob, Grep, Write, WebSearch, tavily | Correction cascade analysis |

</details>

<details>
<summary><strong>Category 3: Architecture (4 agents) -- Phase 3</strong></summary>

| Agent | MaxTurns | Lens | Key Tools | Description |
|-------|----------|------|-----------|-------------|
| structure-architect | 30 | ARE | Read, Glob, Grep, Write, context7, tavily | Component structure, module boundaries |
| interface-architect | 30 | RELATE | Read, Glob, Grep, Write, context7, tavily | API contracts, cross-module interfaces |
| risk-architect | 30 | IMPACT | Read, Glob, Grep, Write, context7, tavily | Risk assessment, failure modes |
| architect | 50 | All | Read, Glob, Grep, Write, context7, tavily | Legacy general-purpose (STD/TRIV) |

</details>

<details>
<summary><strong>Category 4: Planning (4 agents) -- Phase 4</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| decomposition-planner | 30 | Read, Glob, Grep, Write, context7, tavily | Task breakdown, file assignments |
| interface-planner | 30 | Read, Glob, Grep, Write, context7, tavily | Interface contracts, dependency ordering |
| strategy-planner | 30 | Read, Glob, Grep, Write, context7, tavily | Implementation sequencing, risk mitigation |
| plan-writer | 50 | Read, Glob, Grep, Write, context7, tavily | Legacy 10-section implementation planner |

</details>

<details>
<summary><strong>Category 5: Validation (3 agents) -- Phase 5</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| correctness-challenger | 25 | Read, Glob, Grep, Write, seq-thinking | Logical correctness, spec compliance |
| completeness-challenger | 25 | Read, Glob, Grep, Write, seq-thinking | Gap analysis, missing elements |
| robustness-challenger | 25 | Read, Glob, Grep, Write, seq-thinking | Edge cases, failure modes, security |

</details>

<details>
<summary><strong>Category 6: Review (5 agents) -- Phase 6</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| devils-advocate | 30 | Read, Glob, Grep, Write, context7, tavily | Design validator, critical reviewer |
| spec-reviewer | 20 | Read, Glob, Grep, seq-thinking | Spec compliance (no Write -- SendMessage only) |
| code-reviewer | 20 | Read, Glob, Grep, seq-thinking | Quality/architecture/safety (no Write) |
| contract-reviewer | 20 | Read, Glob, Grep, Write, Edit, seq-thinking | Interface contract compliance |
| regression-reviewer | 20 | Read, Glob, Grep, Write, Edit, seq-thinking | Regression and side-effect detection |

</details>

<details>
<summary><strong>Category 7: Implementation (2 agents) -- Phase 6</strong></summary>

| Agent | MaxTurns | Permission | Key Tools | Description |
|-------|----------|------------|-----------|-------------|
| implementer | 100 | acceptEdits | Read, Glob, Grep, Edit, Write, Bash, context7, tavily | App source code, full tool access |
| infra-implementer | 50 | default | Read, Glob, Grep, Edit, Write, seq-thinking | .claude/ infrastructure files only |

</details>

<details>
<summary><strong>Category 8: Testing (2 agents) -- Phase 7</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| tester | 50 | Read, Glob, Grep, Write, Bash, context7, tavily | Test writer and executor |
| contract-tester | 30 | Read, Glob, Grep, Write, Edit, Bash, context7, tavily | Interface contract test writer |

</details>

<details>
<summary><strong>Category 9: Integration (1 agent) -- Phase 8</strong></summary>

| Agent | MaxTurns | Permission | Key Tools | Description |
|-------|----------|------------|-----------|-------------|
| integrator | 100 | acceptEdits | Read, Glob, Grep, Edit, Write, Bash, context7, tavily | Cross-boundary merger, conflict resolver |

</details>

<details>
<summary><strong>Category 10: INFRA Quality (4 agents) -- Cross-cutting</strong></summary>

| Agent | MaxTurns | Lens | Key Tools | Description |
|-------|----------|------|-----------|-------------|
| infra-static-analyst | 30 | ARE | Read, Glob, Grep, Write, seq-thinking | Config/naming/reference integrity |
| infra-relational-analyst | 30 | RELATE | Read, Glob, Grep, Write, seq-thinking | Dependency/coupling mapping |
| infra-behavioral-analyst | 30 | DO | Read, Glob, Grep, Write, seq-thinking | Lifecycle/protocol compliance |
| infra-impact-analyst | 40 | IMPACT | Read, Glob, Grep, Write, seq-thinking | Change ripple prediction |

</details>

<details>
<summary><strong>Category 11: Impact (1 agent) -- Phase 2d, 6+</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| dynamic-impact-analyst | 30 | Read, Glob, Grep, Write, seq-thinking | Change cascade prediction before implementation |

</details>

<details>
<summary><strong>Category 12: Audit (1 agent) -- G3-G8</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| gate-auditor | 15 | Read, Glob, Grep, Write, seq-thinking | Independent gate evaluation (no Edit/Bash) |

</details>

<details>
<summary><strong>Category 13: Monitoring (1 agent) -- Phase 6+</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| execution-monitor | 40 | Read, Glob, Grep, Write, seq-thinking | Real-time drift/conflict/budget detection |

</details>

<details>
<summary><strong>Category 14: Built-in (1 agent) -- Any phase</strong></summary>

| Agent | MaxTurns | Key Tools | Description |
|-------|----------|-----------|-------------|
| claude-code-guide | -- | (CC built-in) | Claude Code docs/features (not a custom agent) |

</details>

### 3.4 Tool Distribution Matrix

| Tool | Workers | Coordinators | Total |
|------|---------|--------------|-------|
| Read | 35 | 8 | 43 |
| Glob | 35 | 8 | 43 |
| Grep | 35 | 8 | 43 |
| Write | 31 | 8 | 39 |
| Edit | 5 | 0 | 5 |
| Bash | 4 | 0 | 4 |
| seq-thinking | 35 | 8 | 43 |
| tavily | 16 | 0 | 16 |
| context7 | 13 | 0 | 13 |
| WebSearch | 5 | 0 | 5 |

---

## 4. Skills (10)

### 4.1 Pipeline Phase Coverage

```
Phase:  P0    P1    P2    P3    P4    P5    P6   P6+   P7    P8    P9   Post

        +-------brainstorming-pipeline-------+
                                       +--write-plan--+
                                                   +-validation-+
                                                          +--execution-plan--+
                                                                      +-verification--+
                                                                                  +delivery+
                                                                                        +rsil-global+
        +------------------ permanent-tasks (cross-cutting) -------------------+
                              rsil-review (any phase, on-demand)
                              palantir-dev (standalone, not pipeline)
```

### 4.2 Skill Reference

| Skill | Phase | Lines | Coordinator | Description |
|-------|-------|-------|-------------|-------------|
| brainstorming-pipeline | P0-3 | 490 | research-coord, arch-coord | Feature idea to architecture |
| agent-teams-write-plan | P4 | 262 | planning-coordinator | Architecture to implementation plan |
| plan-validation-pipeline | P5 | 313 | validation-coordinator | Last checkpoint before implementation |
| agent-teams-execution-plan | P6 | 511 | execution-coordinator | Plan to working code with review |
| verification-pipeline | P7-8 | 419 | testing-coordinator | Test execution and integration |
| delivery-pipeline | P9 | 341 | Lead-only | Consolidate, commit, archive |
| rsil-global | Post | 337 | Lead-only | INFRA health assessment (auto) |
| rsil-review | Any | 406 | Lead-only | Targeted quality review (on-demand) |
| permanent-tasks | X-cut | 198 | Lead-only | PT create/update via Read-Merge-Write |
| palantir-dev | -- | 97 | N/A | Programming language learning support |

**Total skill lines: ~3,374**

---

## 5. Hooks (4)

### 5.1 Lifecycle Events

```
Session Timeline
====================================================================

[Agent Spawn]                 [Tool Call]              [Compaction]
     |                             |                        |
     v                             v                        v
on-subagent-start.sh      on-rtd-post-tool.sh       on-pre-compact.sh
(sync, 10s)               (async, 5s)               (sync, 30s)
- Context injection        - JSONL event capture      - Task snapshot
- Session registry         - Agent name resolve       - Missing L1/L2 warn
- Lifecycle log            - DP association           - RTD state snapshot
                                                           |
                                                           v
                                                    on-session-compact.sh
                                                    (sync, 15s, once)
                                                    - Recovery context
                                                    - RTD-enhanced or generic
```

### 5.2 Hook Reference

| Event | Script | Mode | Timeout | Lines | Purpose |
|-------|--------|------|---------|-------|---------|
| SubagentStart | on-subagent-start.sh | sync | 10s | 93 | Context injection for new agents |
| PreCompact | on-pre-compact.sh | sync | 30s | 123 | Preserve state before compaction |
| SessionStart | on-session-compact.sh | sync, once | 15s | 54 | RTD-centric compact recovery |
| PostToolUse | on-rtd-post-tool.sh | async | 5s | 146 | Capture all tool calls as JSONL |

**Total hook lines: ~416**

### 5.3 Hook Data Dependencies

```
on-subagent-start.sh --writes--> session-registry.json --read-by--> on-rtd-post-tool.sh
                                                                     (resolves agent name)

Lead --writes--> current-dp.txt --read-by--> on-rtd-post-tool.sh
                                              (associates DP with events)

on-pre-compact.sh --reads--> rtd-index.md --snapshot--> snapshots/
on-session-compact.sh --reads--> rtd-index.md --injects--> recovery context
```

---

## 6. References (9)

### 6.1 Reference Catalog

| Document | Version | Lines | Decision Source |
|----------|---------|-------|-----------------|
| agent-catalog.md | v3.0 | 1,489 | D-002, D-005 |
| agent-common-protocol.md | v4.0 | 247 | D-009, D-011, D-017 |
| coordinator-shared-protocol.md | v1.0 | 135 | D-013 |
| gate-evaluation-standard.md | v1.0 | 151 | D-008 |
| ontological-lenses.md | v1.0 | 84 | D-010, D-005 |
| task-api-guideline.md | v6.0 | 80 | -- |
| layer-boundary-model.md | v1.0 | 130 | AD-15 |
| ontology-communication-protocol.md | v1.0 | 318 | -- |
| pipeline-rollback-protocol.md | v1.0 | 74 | GAP-5 |

**Total reference lines: ~2,708**

### 6.2 Consumer Network

```
Reference                             Consumers                     Criticality
---------------------------------------------------------------------------
agent-common-protocol.md -----------> ALL 43 agents                 CRITICAL
task-api-guideline.md --------------> ALL 43 agents (TaskList/Get)  HIGH
agent-catalog.md -------------------> Lead (routing decisions)      CRITICAL
gate-evaluation-standard.md --------> Lead, gate-auditor, skills    HIGH
coordinator-shared-protocol.md -----> 8 coordinators                HIGH
ontological-lenses.md --------------> 4 INFRA + 3 arch agents      MEDIUM
pipeline-rollback-protocol.md ------> 3 skills (val/exec/verif)    MEDIUM
layer-boundary-model.md ------------> Lead, RSIL skills             LOW
ontology-communication-protocol.md -> Lead (domain-specific)        LOW
```

---

## 7. Configuration

### 7.1 Settings Hierarchy

```
.claude.json (project-level)
|  MCP servers: github, context7, sequential-thinking, tavily
|
v merged with
.claude/settings.json (team-level)
|  env vars, hooks(4), plugins(2), language:Korean, model:opus-4-6
|  permissions.deny: protected files + blocked commands
|
v overridden by
.claude/settings.local.json (local overrides)
   permissions.allow: Bash, MCP tools, TaskCreate/TaskUpdate
   MCP JSON servers(8): oda-ontology, tavily, cow-*, etc.
```

### 7.2 Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | "1" | Enable Agent Teams mode |
| CLAUDE_CODE_MAX_OUTPUT_TOKENS | "128000" | Max output token limit |
| CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS | "100000" | File read token limit |
| MAX_MCP_OUTPUT_TOKENS | "100000" | MCP tool output limit |
| BASH_MAX_OUTPUT_LENGTH | "200000" | Bash output limit |
| ENABLE_TOOL_SEARCH | "auto:7" | MCP tool search with threshold 7 |

### 7.3 MCP Servers

**Project-level** (`.claude.json`): github-mcp-server, context7, sequential-thinking, tavily

**Local-level** (`.claude/settings.local.json`): oda-ontology, tavily, cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage

### 7.4 Permissions

**Denied (settings.json):**
- Read: `.env*`, `**/secrets/**`, `**/*credentials*`, `**/.ssh/id_*`
- Bash: `rm -rf *`, `sudo rm *`, `chmod 777 *`

**Allowed (settings.local.json):**
- `Bash(*)`, MCP tools (sequential-thinking, context7, WebFetch, WebSearch)
- `TaskCreate`, `TaskUpdate`, `Skill(orchestrate)`

---

## 8. Observability (RTD)

```
+-------------+     +-----------------+     +-------------------------+
| Lead writes |---->| .current-project|---->| All hooks read project  |
| at pipeline |     | .agent/obs/     |     | slug for file paths     |
| start       |     +-----------------+     +-------------------------+
+-------------+

+-------------+     +-----------------+     +-------------------------+
| Lead writes |---->|  current-dp.txt |---->| PostToolUse associates  |
| before DPs  |     |                 |     | events with decisions   |
+-------------+     +-----------------+     +-------------------------+

+-------------+     +-----------------+     +-------------------------+
| SubagentSt. |---->| session-registry|---->| PostToolUse resolves    |
| hook fires  |     |   .json         |     | session -> agent name   |
+-------------+     +-----------------+     +-------------------------+

+-------------+     +-----------------+     +-------------------------+
| PostToolUse |---->| events/{sid}    |---->| execution-monitor reads |
| captures all|     |   .jsonl        |     | for drift detection     |
+-------------+     +-----------------+     +-------------------------+
```

**Observability directory structure:**

```
.agent/observability/
+-- .current-project              # Active project slug
+-- {project-slug}/
    +-- manifest.json             # Project metadata
    +-- rtd-index.md              # Decision point history
    +-- current-dp.txt            # Current decision point
    +-- session-registry.json     # Session-to-agent mapping
    +-- events/{session}.jsonl    # Per-session tool call events
    +-- snapshots/                # Pre-compact state snapshots
```

---

## 9. Agent Memory

Persistent cross-session memory stored in `~/.claude/agent-memory/`.

| Path | Role | Contents |
|------|------|----------|
| `agent-memory/implementer/MEMORY.md` | implementer | Cross-file editing patterns, DIA protocol, structural optimization |
| `agent-memory/tester/MEMORY.md` | tester | Testing cross-session lessons |
| `agent-memory/integrator/MEMORY.md` | integrator | Integration cross-session lessons |
| `agent-memory/researcher/MEMORY.md` | researcher | Research cross-session lessons |
| `agent-memory/devils-advocate/MEMORY.md` | devils-advocate | Validation cross-session lessons |
| `agent-memory/rsil/MEMORY.md` | rsil | RSIL audit lessons and quality data |
| `agent-memory/architect/MEMORY.md` | architect | Architecture cross-session lessons |
| `agent-memory/architect/lead-arch-redesign.md` | architect | Architecture redesign topic file |

**Pattern:** Agents read MEMORY.md at start, update at end via Read-Merge-Write. Only coordinators write to shared category memory.

---

## 10. CLAUDE.md Constitution

**Path:** `.claude/CLAUDE.md` | **Version:** v9.0 | **Lines:** ~317

| Section | Title | Content Summary |
|---------|-------|-----------------|
| Header | Custom Agents Reference | 43 agents, 14 categories, phase chain, tiers, spawning rules |
| 0 | Language Policy | Korean user-facing, English technical |
| 1 | Team Identity | Workspace, Agent Teams config, Lead/Teammates |
| 2 | Phase Pipeline | Phase-agent mapping, tiers (D-001), gate standard |
| 3 | Roles | Lead (orchestrator), Coordinators (managers), Teammates (workers) |
| 4 | Communication | Lead<->Teammate, Lead->All directional flows |
| 5 | File Ownership | Non-overlapping sets, integrator exception |
| 6 | How Lead Operates | Agent Selection (6-step), Coordinator Mgmt (Mode 1+3), Spawning, Understanding Verification, Monitoring, RTD, Gates, Status, Infrastructure |
| 7 | Tools | sequential-thinking, tavily, context7, github |
| 8 | Safety | Blocked commands, protected files, git safety |
| 9 | Recovery | Lead recovery (RTD-centric), Teammate recovery |
| 10 | Integrity Principles | Lead and Teammate responsibilities |

**Decisions integrated:** D-001 (Pipeline Tiers), D-002 (Skills vs Agents), D-003 (Skill Routing), D-005 (Domain Decomposition), D-008 (Gate Evaluation), D-009 (Agent Memory), D-010 (Ontological Lenses), D-011 (Cross-Phase Handoff), D-012 (PT Scalability), D-013 (Coordinator Protocol), D-014 (Observability/RTD), D-015 (Output Standardization), D-016 (Constitution Redesign), D-017 (Error Handling)

---

## 11. Directory Tree

<details>
<summary><strong>Complete .claude/ file listing (78 infrastructure files)</strong></summary>

```
.claude/
+-- CLAUDE.md                                          # Team Constitution v9.0 (~317L)
|
+-- agents/                                            # 43 agent definitions
|   +-- architect.md                                   # Legacy general-purpose architect
|   +-- architecture-coordinator.md                    # P3 coordinator
|   +-- auditor.md                                     # Systematic artifact analyst
|   +-- behavioral-verifier.md                         # DO lens verifier
|   +-- code-reviewer.md                               # Quality/architecture reviewer
|   +-- codebase-researcher.md                         # Local codebase explorer
|   +-- completeness-challenger.md                     # Gap analysis challenger
|   +-- contract-reviewer.md                           # Interface contract reviewer
|   +-- contract-tester.md                             # Interface contract tester
|   +-- correctness-challenger.md                      # Logical correctness challenger
|   +-- decomposition-planner.md                       # Task breakdown planner
|   +-- devils-advocate.md                             # Design validator / critical reviewer
|   +-- dynamic-impact-analyst.md                      # Change cascade predictor
|   +-- execution-coordinator.md                       # P6 coordinator
|   +-- execution-monitor.md                           # Real-time drift detector
|   +-- external-researcher.md                         # Web-based doc researcher
|   +-- gate-auditor.md                                # Independent gate evaluator
|   +-- impact-verifier.md                             # IMPACT lens verifier
|   +-- implementer.md                                 # App source code implementer
|   +-- infra-behavioral-analyst.md                    # DO lens INFRA analyst
|   +-- infra-impact-analyst.md                        # IMPACT lens INFRA analyst
|   +-- infra-implementer.md                           # .claude/ infrastructure implementer
|   +-- infra-quality-coordinator.md                   # Cross-cutting INFRA coordinator
|   +-- infra-relational-analyst.md                    # RELATE lens INFRA analyst
|   +-- infra-static-analyst.md                        # ARE lens INFRA analyst
|   +-- integrator.md                                  # Cross-boundary merger
|   +-- interface-architect.md                         # RELATE lens architect
|   +-- interface-planner.md                           # Interface contract planner
|   +-- plan-writer.md                                 # Legacy implementation planner
|   +-- planning-coordinator.md                        # P4 coordinator
|   +-- regression-reviewer.md                         # Regression/side-effect reviewer
|   +-- relational-verifier.md                         # RELATE lens verifier
|   +-- research-coordinator.md                        # P2 coordinator
|   +-- risk-architect.md                              # IMPACT lens architect
|   +-- robustness-challenger.md                       # Edge case/security challenger
|   +-- spec-reviewer.md                               # Spec compliance reviewer
|   +-- static-verifier.md                             # ARE lens verifier
|   +-- strategy-planner.md                            # Implementation strategy planner
|   +-- structure-architect.md                         # ARE lens architect
|   +-- tester.md                                      # Test writer and executor
|   +-- testing-coordinator.md                         # P7-8 coordinator
|   +-- validation-coordinator.md                      # P5 coordinator
|   +-- verification-coordinator.md                    # P2b coordinator
|
+-- hooks/                                             # 4 lifecycle hooks (~416L)
|   +-- on-subagent-start.sh                           # SubagentStart: context injection
|   +-- on-pre-compact.sh                              # PreCompact: state preservation
|   +-- on-session-compact.sh                          # SessionStart: compact recovery
|   +-- on-rtd-post-tool.sh                            # PostToolUse: JSONL event capture
|
+-- references/                                        # 9 reference documents (~2,708L)
|   +-- agent-catalog.md                               # Two-level agent catalog (v3.0)
|   +-- agent-common-protocol.md                       # Shared teammate protocol (v4.0)
|   +-- coordinator-shared-protocol.md                 # Coordinator protocol (v1.0)
|   +-- gate-evaluation-standard.md                    # Gate criteria standard (v1.0)
|   +-- layer-boundary-model.md                        # L1/L2 boundary model (v1.0)
|   +-- ontological-lenses.md                          # ARE/RELATE/DO/IMPACT (v1.0)
|   +-- ontology-communication-protocol.md             # Ontology TEACH pattern (v1.0)
|   +-- pipeline-rollback-protocol.md                  # Rollback procedures (v1.0)
|   +-- task-api-guideline.md                          # Task API guide (v6.0)
|
+-- skills/                                            # 10 orchestration skills (~3,374L)
|   +-- brainstorming-pipeline/SKILL.md                # P0-3: Feature to architecture
|   +-- agent-teams-write-plan/SKILL.md                # P4: Architecture to plan
|   +-- plan-validation-pipeline/SKILL.md              # P5: Plan validation
|   +-- agent-teams-execution-plan/SKILL.md            # P6: Plan to code
|   +-- verification-pipeline/SKILL.md                 # P7-8: Testing + integration
|   +-- delivery-pipeline/SKILL.md                     # P9: Consolidate and commit
|   +-- rsil-global/SKILL.md                           # Post: INFRA health assessment
|   +-- rsil-review/SKILL.md                           # Any: Targeted quality review
|   +-- permanent-tasks/SKILL.md                       # X-cut: PT create/update
|   +-- palantir-dev/SKILL.md                          # Standalone: Language learning
|
+-- agent-memory/                                      # 8 persistent memory files
|   +-- implementer/MEMORY.md
|   +-- tester/MEMORY.md
|   +-- integrator/MEMORY.md
|   +-- researcher/MEMORY.md
|   +-- devils-advocate/MEMORY.md
|   +-- rsil/MEMORY.md
|   +-- architect/MEMORY.md
|   +-- architect/lead-arch-redesign.md                # Topic file
|
+-- settings.json                                      # Team-level settings (~84L)
+-- settings.local.json                                # Local overrides (~29L)

.claude.json                                           # Project-level MCP config
```

**File counts:** 43 agents + 10 skills + 4 hooks + 9 references + 3 settings + 1 CLAUDE.md + 8 agent memory = **78 files**

</details>

---

## 12. Key Concepts

### 12.1 L1/L2/L3 Progressive Disclosure

Every agent produces output in three layers for context efficiency (budokki: context gwan-ri):

| Layer | Format | Size | Purpose |
|-------|--------|------|---------|
| L1 | YAML index | <=50 lines | Machine-scannable summary (agent, phase, status, timestamp) |
| L2 | MD summary | <=200 lines | Human-readable narrative with Evidence Sources section |
| L3 | Directory | Unlimited | Full work product (designs, diffs, analysis) |

Lead reads L1/L2 for monitoring. L3 for deep context injection into directives.

### 12.2 PERMANENT Task

The single source of truth for a pipeline, created via the `permanent-tasks` skill.

- **Subject format:** `[PERMANENT] {feature name}`
- **Versioned:** PT-v{N} (monotonically increasing)
- **Contains:** User Intent, Codebase Impact Map, Architecture Decisions, Phase Status, Constraints
- **Maintained via:** Read-Merge-Write (refined current state, not an append-only log)
- **Consumed by:** All agents via TaskGet; Lead embeds key content in spawn directives

### 12.3 Ontological Lenses

Four complementary perspectives for systematic analysis (derived from Palantir Ontology):

| Lens | Question | Agent Mapping |
|------|----------|---------------|
| ARE | What exists? (static structure) | infra-static-analyst, structure-architect, static-verifier |
| RELATE | How do they connect? (dependencies) | infra-relational-analyst, interface-architect, relational-verifier |
| DO | What actions/rules apply? (behavior) | infra-behavioral-analyst, behavioral-verifier |
| IMPACT | What changes propagate? (ripple effects) | infra-impact-analyst, risk-architect, impact-verifier |

### 12.4 Pipeline Tier Routing

Every pipeline is classified at Phase 0 into one of three tiers (D-001). The tier determines which phases are executed and the gate evaluation depth:

- **TRIVIAL:** Minimal overhead -- skip research, validation, testing, integration phases
- **STANDARD:** Balanced -- skip verification, validation, integration phases
- **COMPLEX:** Full rigor -- all phases active, gate-auditor at G3-G8

### 12.5 Coordinator Management Modes

| Mode | Name | Description |
|------|------|-------------|
| Mode 1 | Flat Coordinator | Lead spawns coordinator + workers; coordinator manages via SendMessage |
| Mode 3 | Lead-Direct Fallback | If coordinator is unresponsive (>10 min), Lead manages workers directly |

Transition from Mode 1 to Mode 3 is seamless -- workers are pre-spawned and simply receive messages from Lead instead of the coordinator.

---

## Version History

| Version | Date | Description |
|---------|------|-------------|
| INFRA v9.0 | 2026-02-11 | D-001~D-017 integrated, 43 agents, 14 categories, 6 autonomy gaps closed |
| INFRA v8.0 | 2026-02-10 | Selective Coordinator model, 27 agents, Two-Level Catalog |
| INFRA v7.0 | 2026-02-09 | COW v2.0 pipeline, RTD observability, RSIL system |
| v7.1.0 | 2026-01-25 | Workload-Scoped Outputs, Hierarchical Orchestration (pre-Agent Teams) |

---

*Powered by Claude Code with Agent Teams | Model: claude-opus-4-6 | 43 agents across 14 categories*

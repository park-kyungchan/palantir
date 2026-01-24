# Skills Reference Guide

> **Version:** 1.0 | **Date:** 2026-01-24
> **Total Skills:** 18

---

## Quick Reference Table

| # | Skill | Model | User-Invocable | disable-model | mode | Version |
|---|-------|-------|----------------|---------------|------|---------|
| 1 | clarify | sonnet | ✓ | - | - | 1.0.0 |
| 2 | plan-draft | sonnet | ✓ | - | - | 2.1.8 |
| 3 | explore-l1l2l3 | haiku | ✓ | - | ✓ | 1.1.0 |
| 4 | plan-l1l2l3 | sonnet | ✓ | - | ✓ | 1.1.0 |
| 5 | build | sonnet | ✓ | ✓ | - | 1.1.0 |
| 6 | build-research | haiku | ✓ | ✓ | - | 1.1.0 |
| 7 | docx-automation | sonnet | ✓ | - | - | 1.1.0 |
| 8 | commit-push-pr | sonnet | ✓ | ✓ | - | 1.1.0 |
| 9 | workers | haiku | ✓ | - | - | 1.1.0 |
| 10 | orchestrate | opus | ✓ | ✓ | - | 1.0.0 |
| 11 | assign | haiku | ✓ | ✓ | - | 1.1.0 |
| 12 | collect | haiku | ✓ | ✓ | - | 1.1.0 |
| 13 | worker-start | sonnet | ✓ | ✓ | - | 1.1.0 |
| 14 | worker-task | sonnet | ✓ | ✓ | - | 1.1.0 |
| 15 | worker-done | haiku | ✓ | ✓ | - | 1.1.0 |
| 16 | pd-injector | haiku | ✓ | - | - | 1.1.0 |
| 17 | pd-analyzer | haiku | ✓ | - | - | 1.0.0 |
| 18 | pd-forked-task | haiku | ✓ | ✓ | - | 1.0.0 |

---

## Skill Categories

### Category 1: User-Facing (Primary)

#### clarify
```yaml
name: clarify
description: PE 기법을 적용하여 사용자 요청을 반복적으로 개선
user-invocable: true
context: fork
model: sonnet
version: "1.0.0"
```
**Purpose:** Prompt Engineering loop for request clarification

#### plan-draft
```yaml
name: plan-draft
description: |
  사용자의 프롬프트를 분석하고 명확화합니다.
  요구사항이 불명확할 때 Socratic Question으로 명확화하고,
  Claude Code Native Capabilities 중 적합한 기능을 추천합니다.
user-invocable: true
model: sonnet
allowed-tools: Read, Grep, Glob, AskUserQuestion, Task, WebSearch, TodoWrite
version: "2.1.8"
```
**Purpose:** Pre-planning clarification via Socratic Q&A

#### explore-l1l2l3
```yaml
name: explore-l1l2l3
description: |
  Explore codebase with Progressive Disclosure L1/L2/L3 output format.
  Analyze code structure, find patterns, and discover files efficiently.
  Returns token-efficient summaries with lazy-loading detail sections.
  Use when asking about codebase structure, file locations, or code patterns.
user-invocable: true
mode: true
context: fork
agent: Explore
model: haiku
version: "1.1.0"
```
**Purpose:** Token-efficient codebase exploration

#### plan-l1l2l3
```yaml
name: plan-l1l2l3
description: |
  Create implementation plans with Progressive Disclosure L1/L2/L3 output format.
  Design step-by-step implementation guides with dependencies and risk analysis.
  Returns structured plans with lazy-loading detail sections.
  Use when planning features, refactoring, or multi-step implementations.
user-invocable: true
mode: true
context: fork
agent: Plan
model: sonnet
version: "1.1.0"
```
**Purpose:** Structured implementation planning

---

### Category 2: Build & Automation

#### build
```yaml
name: build
description: |
  Build agents, skills, hooks with Three-Phase Pattern.
  Phase 1 (Research): Delegates to build-research subagent.
  Phase 2 (Design): Creates implementation plan.
  Phase 3 (Build): Generates artifacts.
  Use for creating new Claude Code components.
user-invocable: true
disable-model-invocation: true
model: sonnet
version: "1.1.0"
```
**Purpose:** Three-phase component building

#### build-research
```yaml
name: build-research
description: |
  Internal research phase for /build command.
  Searches documentation, analyzes patterns, gathers context.
  Returns structured research results for build planning.
  Internal helper for L1/L2/L3 format analysis.
user-invocable: true
disable-model-invocation: true
model: haiku
version: "1.1.0"
```
**Purpose:** Research phase helper for build

#### docx-automation
```yaml
name: docx-automation
description: |
  Generate DOCX documents from pipeline results or structured data.
  Uses python-docx library for Word document generation.
  Supports template-based reports, batch exports, and custom styling.
  Use when user asks to create Word documents, export reports, or generate DOCX files.
user-invocable: true
model: sonnet
version: "1.1.0"
```
**Purpose:** Word document generation

#### commit-push-pr
```yaml
name: commit-push-pr
description: |
  Boris Cherny Pattern 6: Commit changes, push to remote, create/update PR.
  All-in-one git workflow command used dozens of times daily.
  Automates: git add → git commit → git push → gh pr create.
  Use when ready to commit and share changes with the team.
user-invocable: true
disable-model-invocation: true
model: sonnet
argument-hint: [commit message]
version: "1.1.0"
```
**Purpose:** Complete git workflow automation

---

### Category 3: Multi-Terminal Orchestration

#### orchestrate
```yaml
name: orchestrate
description: |
  Multi-terminal task orchestration for parallel execution.
  Coordinates Terminal-B, C, D workers for independent tasks.
  Creates task files, monitors progress, resolves dependencies.
  Use for complex multi-file implementations requiring parallelism.
user-invocable: true
disable-model-invocation: true
model: opus
version: "1.0.0"
```
**Purpose:** Main orchestrator for parallel execution

#### workers
```yaml
name: workers
description: |
  Check status of all worker terminals in multi-terminal orchestration.
  Display pending tasks, completed tasks, and blocked dependencies.
  Show real-time progress dashboard for Terminal B, C, D workers.
  Use when monitoring parallel task execution or checking worker availability.
user-invocable: true
model: haiku
version: "1.1.0"
```
**Purpose:** Worker status dashboard

#### assign
```yaml
name: assign
description: |
  Assign task to specific worker terminal (B, C, D).
  Creates task YAML file in pending directory.
  Generates unique task ID and sets up dependencies.
  Internal command for Orchestrator task distribution.
user-invocable: true
disable-model-invocation: true
model: haiku
version: "1.1.0"
```
**Purpose:** Task assignment to workers

#### collect
```yaml
name: collect
description: |
  Collect and aggregate results from completed worker tasks.
  Reads completed task files, merges outputs, generates summary.
  Updates progress tracker with aggregated status.
  Use after workers complete parallel tasks.
user-invocable: true
disable-model-invocation: true
model: haiku
version: "1.1.0"
```
**Purpose:** Result aggregation from workers

---

### Category 4: Worker Execution

#### worker-start
```yaml
name: worker-start
description: |
  Worker terminal skill - Load context and execute assigned task.
  Initialize worker terminal (B, C, D) with global context and task file.
  Verify dependencies, execute steps, update progress tracker.
  Use in Terminal-B/C/D to start assigned parallel task execution.
user-invocable: true
disable-model-invocation: true
model: sonnet
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
version: "1.1.0"
```
**Purpose:** Worker initialization

#### worker-task
```yaml
name: worker-task
description: |
  Execute assigned worker task from a YAML prompt file.
  Used in multi-terminal orchestration for parallel task execution.
  Reads task steps, checks dependencies, updates progress, and reports results.
  Internal worker command for Terminal-B, C, D task processing.
user-invocable: true
disable-model-invocation: true
model: sonnet
argument-hint: [task-file-path]
allowed-tools: Read, Grep, Glob, Edit, Write, Bash
version: "1.1.0"
```
**Purpose:** Task execution from YAML

#### worker-done
```yaml
name: worker-done
description: |
  Report task completion and update progress tracker.
  Move task file from pending to completed, update _progress.yaml.
  Generate L1 completion report for Orchestrator (Terminal-A).
  Use in worker terminals after completing assigned task.
user-invocable: true
disable-model-invocation: true
model: haiku
allowed-tools: Read, Edit, Write, Bash
version: "1.1.0"
```
**Purpose:** Task completion reporting

---

### Category 5: Progressive Disclosure Helpers

#### pd-injector
```yaml
name: pd-injector
description: |
  동적 컨텍스트 주입 데모 스킬.
  !`command` 구문을 사용하여 실행 시점에 데이터를 주입합니다.
  Git 상태, 파일 내용, 환경 정보를 프롬프트에 자동 삽입합니다.
  Internal helper for L1/L2/L3 format analysis.
user-invocable: true
model: haiku
version: "1.1.0"
```
**Purpose:** Dynamic context injection

#### pd-analyzer
```yaml
name: pd-analyzer
description: |
  Progressive-Disclosure 분석기.
  L1/L2/L3 형식으로 분석 결과를 반환합니다.
  Internal helper for L1/L2/L3 format analysis.
user-invocable: true
model: haiku
version: "1.0.0"
```
**Purpose:** L1/L2/L3 format analysis

#### pd-forked-task
```yaml
name: pd-forked-task
description: |
  Forked Task execution with isolated context.
  Runs subagent in fork mode for deep analysis.
  Returns structured L1/L2/L3 output.
user-invocable: true
disable-model-invocation: true
context: fork
model: haiku
version: "1.0.0"
```
**Purpose:** Isolated forked execution

---

## Model Distribution

```
┌─────────────────────────────────────────────┐
│ Model Usage Distribution                     │
├─────────────────────────────────────────────┤
│ opus   │ ██                            1 (6%)│
│ sonnet │ ████████████████████         9 (50%)│
│ haiku  │ ████████████████             8 (44%)│
└─────────────────────────────────────────────┘
```

---

## Invocation Patterns

### Direct User Invocation
```
/clarify "requirement"
/explore-l1l2l3 "pattern"
/build "component"
/commit-push-pr "message"
```

### Mode Commands (Plan Mode)
```
/explore-l1l2l3  → Shows in Mode Commands
/plan-l1l2l3     → Shows in Mode Commands
```

### Internal Only (disable-model-invocation)
```
/build-research  → Only via /build
/worker-start    → Only in worker terminals
/worker-task     → Only via orchestrator
/worker-done     → Only after task completion
/assign          → Only via orchestrator
/collect         → Only via orchestrator
```

---

> **Document Generated:** 2026-01-24
> **Skills Count:** 18 | **Categories:** 5

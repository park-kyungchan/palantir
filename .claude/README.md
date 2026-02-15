# .claude/ INFRA — Complete Reference

> **Version:** v10.8 | **Engine:** Claude Opus 4.6 | **Mode:** Agent Teams (tmux)
> **Purpose:** This document is the authoritative reference for the entire `.claude/` infrastructure.
> Use it to understand how the system works and to provide precise feedback to the Lead agent.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [CLAUDE.md — Team Constitution](#3-claudemd--team-constitution)
4. [Pipeline Phases & Tiers](#4-pipeline-phases--tiers)
5. [Agents](#5-agents)
6. [Skills](#6-skills)
7. [Hooks](#7-hooks)
8. [Settings](#8-settings)
9. [SRC — Smart Reactive Codebase](#9-src--smart-reactive-codebase)
10. [Context Engineering](#10-context-engineering)
11. [Agent Memory System](#11-agent-memory-system)
12. [Directory Layout](#12-directory-layout)
13. [Feedback Guide](#13-feedback-guide)

---

## 1. System Overview

This is a **skill-driven, agent-orchestrated pipeline** built on top of Claude Code CLI.
The Lead agent acts as a **pure orchestrator** — it never edits files directly. All work
flows through **Skills** (methodology definitions) executed by **Agents** (tool profiles).

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                     USER REQUEST                                │
  └──────────────────────────┬──────────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    LEAD (Orchestrator)                           │
  │                                                                 │
  │  Reads: Skill L1 (system-reminder) + Agent L1 (Task tool def)  │
  │  Does:  Route → Spawn → Monitor → Iterate                      │
  │  Never: Edit files, Run bash, Access web                        │
  └───────┬──────────┬──────────┬──────────┬───────────┬────────────┘
          │          │          │          │           │
          ▼          ▼          ▼          ▼           ▼
      ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
      │Analyst │ │Research│ │ Impl   │ │InfraIm│ │Deliver│
      │  (B)   │ │  (C)   │ │  (D)   │ │  (E)  │ │  (F)  │
      └────────┘ └────────┘ └────────┘ └────────┘ └────────┘
       Magenta    Yellow      Green       Red       Cyan

       + PT Manager (G) — Blue — Task lifecycle management
```

### Key Principles

- **Skill L1** (frontmatter description, ≤1024 chars) = routing intelligence, auto-loaded
- **Skill L2** (body) = methodology, loaded only on invocation
- **Agent L1** (frontmatter description) = tool profile, auto-loaded in Task tool
- **Agent L2** (body) = role identity + constraints, isolated per-agent context
- **CLAUDE.md** = protocol-only (48 lines), zero routing data

---

## 2. Architecture

### Data Flow — Full COMPLEX Pipeline

```
 PRE-DESIGN (P0)              DESIGN (P1)                RESEARCH (P2)
 ┌─────────────────┐          ┌─────────────────┐        ┌─────────────────┐
 │ brainstorm       │──PASS──▶│ architecture     │──────▶│ codebase        │
 │ validate         │         │ interface        │       │ external        │
 │ feasibility      │         │ risk             │       │ audit           │
 └─────────────────┘          └─────────────────┘        └────────┬────────┘
                                                                  │
 ┌─────────────────────────────────────────────────────────────────┘
 │
 ▼
 PLAN (P3)                    PLAN-VERIFY (P4)           ORCHESTRATION (P5)
 ┌─────────────────┐          ┌─────────────────┐        ┌─────────────────┐
 │ decomposition    │──PASS──▶│ correctness  ∥   │──ALL──▶│ decompose       │
 │ interface        │         │ completeness ∥   │ PASS  │ assign          │
 │ strategy         │         │ robustness       │       │ verify          │
 └─────────────────┘          └─────────────────┘        └────────┬────────┘
                                                                  │
 ┌─────────────────────────────────────────────────────────────────┘
 │
 ▼
 EXECUTION (P6)               VERIFY (P7)                DELIVERY (P8)
 ┌─────────────────┐          ┌─────────────────┐        ┌─────────────────┐
 │ code       ∥    │──DONE──▶│ structure        │──ALL──▶│ delivery-       │
 │ infra      ∥    │         │ content          │ PASS  │ pipeline        │
 │ impact          │         │ consistency      │       │                 │
 │ cascade         │         │ quality          │       │ git commit      │
 │ review          │         │ cc-feasibility   │       │ MEMORY.md       │
 └─────────────────┘          └─────────────────┘        └─────────────────┘

 HOMEOSTASIS (Cross-cutting)
 ┌──────────────────────────────────────────────────┐
 │ manage-infra    manage-skills    manage-codebase  │
 │ self-diagnose   self-implement                    │
 └──────────────────────────────────────────────────┘
```

### Context Loading Order

```
 ① CLAUDE.md ──────────────────────────▶ Lead system prompt (persistent)
 ② Skill L1 descriptions ─────────────▶ system-reminder (Skill tool)
 ③ SessionStart hooks ─────────────────▶ additionalContext injection
 ④ Agent L1 descriptions ─────────────▶ Task tool definition
 ⑤ SubagentStart hooks ────────────────▶ Spawned agent context
 ⑥ Conversation messages ──────────────▶ User + Assistant turns
```

---

## 3. CLAUDE.md — Team Constitution

**Location:** `.claude/CLAUDE.md` | **Size:** 48 lines | **Role:** Protocol-only

The constitution defines behavioral rules, not routing data. All routing is handled
by auto-loaded L1 metadata from Skills and Agents.

### Sections

| Section | Content |
|---------|---------|
| Header | Version, model, component counts, inviolable principle |
| §0 Language | Korean (user-facing), English (artifacts) |
| §1 Identity | Workspace, team mode, Lead role, agent/skill counts |
| §2 Tiers | TRIVIAL/STANDARD/COMPLEX classification + phase routing |
| §2.1 Execution Mode | P0-P1: local agents only. P2+: Team infrastructure |
| §3 Lead | Routing mechanism (L1 WHEN + PROFILE), spawn protocol |
| §4 PERMANENT Task | Managed via /task-management |

### Inviolable Principle

```
Lead = Pure Orchestrator
├── Routes work through Skills (methodology) and Agents (tool profiles)
├── Skill L1 = routing intelligence (auto-loaded)
├── Agent L1 = tool profile selection (auto-loaded)
├── Lead NEVER edits files directly
└── No routing data in CLAUDE.md
```

---

## 4. Pipeline Phases & Tiers

### Tier Classification (at Phase 0)

```
┌──────────────────────────────────────────────────────────────────┐
│  TRIVIAL   │  ≤2 files, single module                           │
│            │  P0 ──────────────────────────────▶ P6 ────▶ P8    │
├────────────┼────────────────────────────────────────────────────┤
│  STANDARD  │  3 files, 1-2 modules                              │
│            │  P0 ──▶ P1 ──▶ P2 ──▶ P3 ──▶ P6 ──▶ P7 ──▶ P8   │
├────────────┼────────────────────────────────────────────────────┤
│  COMPLEX   │  ≥4 files, 2+ modules                              │
│            │  P0 ▶ P1 ▶ P2 ▶ P3 ▶ P4 ▶ P5 ▶ P6 ▶ P7 ▶ P8    │
└──────────────────────────────────────────────────────────────────┘
```

### Phase Reference

| Phase | Name | Skills | Mode |
|-------|------|--------|------|
| P0 | Pre-Design | brainstorm, validate, feasibility | Lead + local agents |
| P1 | Design | architecture, interface, risk | Lead + local agents |
| P2 | Research | codebase, external, audit | Team infrastructure |
| P3 | Plan | decomposition, interface, strategy | Team infrastructure |
| P4 | Plan-Verify | correctness, completeness, robustness | Team infrastructure |
| P5 | Orchestration | decompose, assign, verify | Team infrastructure |
| P6 | Execution | code, infra, impact, cascade, review | Team infrastructure |
| P7 | Verify | structure, content, consistency, quality, cc-feasibility | Team infrastructure |
| P8 | Delivery | delivery-pipeline | Team infrastructure |
| X | Homeostasis | manage-infra, manage-skills, manage-codebase, self-diagnose, self-implement | Any |
| X | Cross-cutting | task-management, pipeline-resume | Any |

### Execution Mode

```
  P0 ─── P1           P2 ─── P3 ─── P4 ─── P5 ─── P6 ─── P7 ─── P8
  ▀▀▀▀▀▀▀▀▀           ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
  Lead + Local         Team Infrastructure (tmux split pane)
  run_in_background    TeamCreate, SendMessage, TaskCreate/Update
  No TeamCreate        Proper teammate coordination
```

---

## 5. Agents

Six custom agents, each with a unique tool profile and color.

### Agent Registry

```
 ┌──────────────────────────────────────────────────────────────────────────────┐
 │  Agent              │ Profile │ Color   │ Model  │ Memory  │ MaxTurns │
 ├──────────────────────────────────────────────────────────────────────────────┤
 │  analyst            │ B       │ Magenta │ Opus   │ project │    25    │
 │  researcher         │ C       │ Yellow  │ Opus   │ project │    30    │
 │  implementer        │ D       │ Green   │ Opus   │ project │    50    │
 │  infra-implementer  │ E       │ Red     │ Opus   │ project │    35    │
 │  delivery-agent     │ F       │ Cyan    │ Haiku  │ none    │    20    │
 │  pt-manager         │ G       │ Blue    │ Haiku  │ none    │    20    │
 └──────────────────────────────────────────────────────────────────────────────┘
```

### Profile Capability Matrix

```
  Tool Access    │ analyst │ researcher │ implementer │ infra-impl │ delivery │ pt-mgr │
 ────────────────┼─────────┼────────────┼─────────────┼────────────┼──────────┼────────┤
  Read           │    ✓    │     ✓      │      ✓      │     ✓      │    ✓     │   ✓    │
  Glob           │    ✓    │     ✓      │      ✓      │     ✓      │    ✓     │   ✓    │
  Grep           │    ✓    │     ✓      │      ✓      │     ✓      │    ✓     │   ✓    │
  Edit           │    ✗    │     ✗      │      ✓      │     ✓      │    ✓     │   ✗    │
  Write          │    ✓    │     ✓      │      ✓      │     ✓      │    ✓     │   ✓    │
  Bash           │    ✗    │     ✗      │      ✓      │     ✗      │    ✓     │   ✗    │
  WebSearch      │    ✗    │     ✓      │      ✗      │     ✗      │    ✗     │   ✗    │
  WebFetch       │    ✗    │     ✓      │      ✗      │     ✗      │    ✗     │   ✗    │
  context7       │    ✗    │     ✓      │      ✗      │     ✗      │    ✗     │   ✗    │
  tavily         │    ✗    │     ✓      │      ✗      │     ✗      │    ✗     │   ✗    │
  seq-thinking   │    ✓    │     ✓      │      ✓      │     ✓      │    ✗     │   ✗    │
  TaskCreate     │    ✗    │     ✗      │      ✗      │     ✗      │    ✗     │   ✓    │
  TaskUpdate     │    ✗    │     ✗      │      ✗      │     ✗      │    ✓     │   ✓    │
  TaskGet/List   │    ✗    │     ✗      │      ✗      │     ✗      │    ✓     │   ✓    │
  AskUserQuestion│    ✗    │     ✗      │      ✗      │     ✗      │    ✓     │   ✓    │
  Task (spawn)   │    ✗    │     ✗      │      ✗      │     ✗      │    ✗     │   ✗    │
```

### Agent Detail Cards

#### analyst (Profile B — ReadAnalyzeWrite)

```
  ┌─ Magenta ──────────────────────────────────────────────────────┐
  │  PURPOSE: Codebase analysis + structured documentation          │
  │  SCOPE:   Read source, search patterns, produce L1/L2/L3 docs  │
  │  KEY:     sequential-thinking for multi-factor analysis         │
  │  LIMIT:   Cannot modify files, run commands, or access web      │
  │  USE FOR: Verification, auditing, design analysis, planning     │
  └─────────────────────────────────────────────────────────────────┘
```

#### researcher (Profile C — ReadAnalyzeWriteWeb)

```
  ┌─ Yellow ───────────────────────────────────────────────────────┐
  │  PURPOSE: Web-enabled research + documentation                  │
  │  SCOPE:   Read code + search web + fetch docs + produce output  │
  │  KEY:     context7 (library docs), tavily (broad search)        │
  │  LIMIT:   Cannot modify files or run commands                   │
  │  USE FOR: External doc lookup, API validation, pattern research │
  └─────────────────────────────────────────────────────────────────┘
```

#### implementer (Profile D — CodeImpl)

```
  ┌─ Green ────────────────────────────────────────────────────────┐
  │  PURPOSE: Source code implementation + testing                   │
  │  SCOPE:   Read/Edit/Write source files + Bash for tests/builds  │
  │  KEY:     Only agent with Bash access. Full read-write-execute  │
  │  LIMIT:   Cannot modify .claude/ files. No web access           │
  │  USE FOR: Application code, tests, builds, scripts              │
  └─────────────────────────────────────────────────────────────────┘
```

#### infra-implementer (Profile E — InfraImpl)

```
  ┌─ Red ──────────────────────────────────────────────────────────┐
  │  PURPOSE: .claude/ infrastructure file modification             │
  │  SCOPE:   Read/Edit/Write .claude/ files (agents, skills, etc.) │
  │  KEY:     Edit without Bash — safe for configuration changes    │
  │  LIMIT:   Cannot run shell commands. Cannot validate by exec    │
  │  USE FOR: Agent/skill creation, settings changes, hook edits    │
  └─────────────────────────────────────────────────────────────────┘
```

#### delivery-agent (Profile F — ForkDelivery)

```
  ┌─ Cyan ─────────────────────────────────────────────────────────┐
  │  PURPOSE: Pipeline delivery (git commit + MEMORY.md archive)    │
  │  SCOPE:   Consolidate outputs, commit, update PT                │
  │  KEY:     Haiku model (cost-efficient). TaskUpdate only          │
  │  LIMIT:   No TaskCreate. No .claude/ file modification          │
  │  SAFETY:  User confirmation required for ALL external actions   │
  └─────────────────────────────────────────────────────────────────┘
```

#### pt-manager (Profile G — ForkPT)

```
  ┌─ Blue ─────────────────────────────────────────────────────────┐
  │  PURPOSE: Task lifecycle management + ASCII visualization       │
  │  SCOPE:   PT management, batch task creation, status tracking   │
  │  KEY:     Haiku model. Full Task API (Create + Update)          │
  │  LIMIT:   Cannot Edit files or run Bash commands                │
  │  OUTPUT:  ASCII pipeline visualizations in Korean               │
  └─────────────────────────────────────────────────────────────────┘
```

---

## 6. Skills

33 skills across 10 domains. Each skill has L1 (routing frontmatter) and L2 (methodology body).

### Skill Inventory by Domain

```
 DOMAIN            │ PHASE │ SKILLS                                         │ COUNT
 ──────────────────┼───────┼────────────────────────────────────────────────┼──────
 pre-design        │ P0    │ brainstorm, validate, feasibility              │   3
 design            │ P1    │ architecture, interface, risk                  │   3
 research          │ P2    │ codebase, external, audit                     │   3
 plan              │ P3    │ decomposition, interface, strategy             │   3
 plan-verify       │ P4    │ correctness, completeness, robustness          │   3
 orchestration     │ P5    │ decompose, assign, verify                     │   3
 execution         │ P6    │ code, infra, impact, cascade, review          │   5
 verify            │ P7    │ structure, content, consistency, quality,      │   5
                   │       │ cc-feasibility                                 │
 homeostasis       │ X-cut │ manage-infra, manage-skills, manage-codebase, │   5
                   │       │ self-diagnose, self-implement                  │
 cross-cutting     │ X-cut │ delivery-pipeline, pipeline-resume,           │   3
                   │       │ task-management                                │
 ──────────────────┼───────┼────────────────────────────────────────────────┼──────
                   │       │                                        TOTAL: │  33
```

### Skill Routing Flags

Skills have two critical routing flags:

| Flag | Effect when `true` |
|------|--------------------|
| `user-invocable` | Appears in `/slash-command` list for user to invoke |
| `disable-model-invocation` | L1 description NOT loaded into context — Lead cannot route to it |

```
 ┌──────────────────────────────────────────────────────────────────────────┐
 │  ROUTING VISIBILITY                                                      │
 │                                                                          │
 │  Auto-loaded (Lead can route):  28 skills  │  dmi=false, ui=true/false  │
 │  User-only (Lead invisible):     4 skills  │  dmi=true                  │
 │                                                                          │
 │  User-only skills:                                                       │
 │    /brainstorm          — Pipeline entry point, user initiates           │
 │    /delivery-pipeline   — Terminal phase, user triggers                  │
 │    /pipeline-resume     — Session recovery, user triggers                │
 │    /task-management     — Task ops, user triggers                        │
 │                                                                          │
 │  Auto-only (not user-invocable):  2 skills                              │
 │    execution-impact     — Triggered by SRC hook, Lead routes             │
 │    execution-cascade    — Triggered by impact results, Lead routes       │
 └──────────────────────────────────────────────────────────────────────────┘
```

### Skill L1 Description Structure

Every auto-loaded skill description follows a canonical structure:

```
[Tag] One-line summary sentence.

WHEN: Trigger condition for this skill.
DOMAIN: domain-name (skill N of M). Sequence or parallel info.
INPUT_FROM: upstream skill(s) providing input.
OUTPUT_TO: downstream skill(s) receiving output.

METHODOLOGY: (1) step, (2) step, (3) step, (4) step, (5) step.
OUTPUT_FORMAT: L1 format description, L2 format description.
```

All descriptions are capped at **≤1024 characters** to avoid L1 truncation.
Total budget: 32,000 chars (`SLASH_COMMAND_TOOL_CHAR_BUDGET`), current usage ~75%.

### Skill L2 Body Structure

```
# Skill Name

## Execution Model
- TRIVIAL: behavior
- STANDARD: behavior
- COMPLEX: behavior

## Methodology
### 1. First Step
### 2. Second Step
### 3. Third Step
### 4. Fourth Step
### 5. Fifth Step

## Quality Gate
- Gate criteria list

## Output
### L1 (YAML summary)
### L2 (Detailed report)
```

### Delegation Prompt Standard (DPS)

19 agent-spawning skills include a DPS template in their L2 body:

```
For STANDARD/COMPLEX tiers, construct the delegation prompt with:
- Context:  What the agent needs to know (file lists, prior outputs)
- Task:     What the agent must do (specific deliverable)
- Constraints: What the agent must NOT do (boundaries, limits)
- Expected Output: What the agent must produce (format, location)
```

### Complete Skill Reference Table

| # | Skill | Domain | Phase | User-Invocable | Auto-Loaded | Agent Spawned |
|---|-------|--------|-------|----------------|-------------|---------------|
| 1 | pre-design-brainstorm | pre-design | P0 | /brainstorm | No | analyst |
| 2 | pre-design-validate | pre-design | P0 | /pre-design-validate | Yes | analyst |
| 3 | pre-design-feasibility | pre-design | P0 | /pre-design-feasibility | Yes | researcher |
| 4 | design-architecture | design | P1 | /design-architecture | Yes | analyst |
| 5 | design-interface | design | P1 | /design-interface | Yes | analyst |
| 6 | design-risk | design | P1 | /design-risk | Yes | analyst |
| 7 | research-codebase | research | P2 | /research-codebase | Yes | analyst |
| 8 | research-external | research | P2 | /research-external | Yes | researcher |
| 9 | research-audit | research | P2 | /research-audit | Yes | analyst |
| 10 | plan-decomposition | plan | P3 | /plan-decomposition | Yes | analyst |
| 11 | plan-interface | plan | P3 | /plan-interface | Yes | analyst |
| 12 | plan-strategy | plan | P3 | /plan-strategy | Yes | analyst |
| 13 | plan-verify-correctness | plan-verify | P4 | /plan-verify-correctness | Yes | analyst |
| 14 | plan-verify-completeness | plan-verify | P4 | /plan-verify-completeness | Yes | analyst |
| 15 | plan-verify-robustness | plan-verify | P4 | /plan-verify-robustness | Yes | analyst |
| 16 | orchestration-decompose | orchestration | P5 | /orchestration-decompose | Yes | Lead-direct |
| 17 | orchestration-assign | orchestration | P5 | /orchestration-assign | Yes | Lead-direct |
| 18 | orchestration-verify | orchestration | P5 | /orchestration-verify | Yes | Lead-direct |
| 19 | execution-code | execution | P6 | /execution-code | Yes | implementer |
| 20 | execution-infra | execution | P6 | /execution-infra | Yes | infra-implementer |
| 21 | execution-impact | execution | P6 | No | Yes | analyst |
| 22 | execution-cascade | execution | P6 | No | Yes | implementer |
| 23 | execution-review | execution | P6 | /execution-review | Yes | analyst |
| 24 | verify-structure | verify | P7 | /verify-structure | Yes | analyst |
| 25 | verify-content | verify | P7 | /verify-content | Yes | analyst |
| 26 | verify-consistency | verify | P7 | /verify-consistency | Yes | analyst |
| 27 | verify-quality | verify | P7 | /verify-quality | Yes | analyst |
| 28 | verify-cc-feasibility | verify | P7 | /verify-cc-feasibility | Yes | researcher |
| 29 | manage-infra | homeostasis | X | /manage-infra | Yes | analyst |
| 30 | manage-skills | homeostasis | X | /manage-skills | Yes | analyst |
| 31 | manage-codebase | homeostasis | X | /manage-codebase | Yes | analyst |
| 32 | self-diagnose | homeostasis | X | /self-diagnose | Yes | analyst |
| 33 | self-implement | homeostasis | X | /self-implement | Yes | infra-implementer |
| 34 | delivery-pipeline | cross-cutting | P8 | /delivery-pipeline | No | delivery-agent |
| 35 | pipeline-resume | cross-cutting | X | /pipeline-resume | No | Lead-direct |
| 36 | task-management | cross-cutting | X | /task-management | No | pt-manager |

---

## 7. Hooks

5 hook scripts responding to 4 distinct Claude Code events.

### Hook Event Flow

```
 ┌─ SESSION LIFECYCLE ────────────────────────────────────────────────────────┐
 │                                                                            │
 │  SessionStart(compact)                                                     │
 │  └── on-session-compact.sh                                                 │
 │      Injects recovery instructions:                                        │
 │      "TaskList → TaskGet [PERMANENT] → Send context to teammates"          │
 │                                                                            │
 │  PreCompact                                                                │
 │  └── on-pre-compact.sh                                                     │
 │      Snapshots task list state to /tmp/ before context loss                │
 │                                                                            │
 ├─ AGENT LIFECYCLE ──────────────────────────────────────────────────────────┤
 │                                                                            │
 │  SubagentStart (all agents)                                                │
 │  └── on-subagent-start.sh                                                  │
 │      Logs agent spawn + injects PT context for team members                │
 │                                                                            │
 │  SubagentStop (implementer|infra-implementer only)                         │
 │  └── on-implementer-done.sh                                                │
 │      SRC Stage 2: Reads change log, greps dependents, injects impact alert │
 │                                                                            │
 ├─ FILE CHANGE TRACKING ────────────────────────────────────────────────────┤
 │                                                                            │
 │  PostToolUse (Edit|Write)                                                  │
 │  └── on-file-change.sh  [async]                                            │
 │      SRC Stage 1: Silently appends changed file path to session log        │
 │                                                                            │
 └────────────────────────────────────────────────────────────────────────────┘
```

### Hook Detail Table

| Hook Script | Event | Matcher | Async | Timeout | Output |
|-------------|-------|---------|-------|---------|--------|
| on-session-compact.sh | SessionStart | `compact` | No | 15s | additionalContext |
| on-pre-compact.sh | PreCompact | (all) | No | 30s | Log file |
| on-subagent-start.sh | SubagentStart | (all) | No | 10s | additionalContext |
| on-implementer-done.sh | SubagentStop | `implementer\|infra-implementer` | No | 30s | additionalContext |
| on-file-change.sh | PostToolUse | `Edit\|Write` | Yes | 5s | Silent (log only) |

### Hook Robustness Features

All hooks implement:
- `set -euo pipefail` — strict error handling
- jq-preferred extraction with grep fallback
- Empty field guards (`[[ -z "$VAR" ]] && exit 0`)
- JSON escaping for output safety
- `/tmp/` ephemeral storage (session-scoped, auto-cleanup)

---

## 8. Settings

**Location:** `.claude/settings.json` | **Size:** ~110 lines

### Key Configuration

```
 ┌─ ENVIRONMENT ───────────────────────────────────────────────────────────┐
 │  CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS  = 1       (Team mode enabled)    │
 │  CLAUDE_CODE_MAX_OUTPUT_TOKENS         = 128000  (4x default)           │
 │  CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS = 100000                       │
 │  MAX_MCP_OUTPUT_TOKENS                 = 100000                         │
 │  BASH_MAX_OUTPUT_LENGTH                = 200000                         │
 │  ENABLE_TOOL_SEARCH                    = auto:7                         │
 │  SLASH_COMMAND_TOOL_CHAR_BUDGET        = 32000   (2x default 16000)     │
 └─────────────────────────────────────────────────────────────────────────┘

 ┌─ MODEL & MODE ──────────────────────────────────────────────────────────┐
 │  model                   = claude-opus-4-6                               │
 │  teammateMode            = tmux                                          │
 │  alwaysThinkingEnabled   = true                                          │
 │  defaultMode             = delegate                                      │
 └─────────────────────────────────────────────────────────────────────────┘

 ┌─ PERMISSIONS ───────────────────────────────────────────────────────────┐
 │  ALLOW:                                                                  │
 │    Bash(*)                                                               │
 │    mcp__sequential-thinking__sequentialthinking                          │
 │    WebFetch(domain:github.com)                                           │
 │    WebFetch(domain:raw.githubusercontent.com)                            │
 │    WebSearch                                                             │
 │    mcp__context7__resolve-library-id                                     │
 │    mcp__context7__query-docs                                             │
 │    mcp__tavily__search                                                   │
 │    TaskUpdate, TaskCreate                                                │
 │                                                                          │
 │  DENY:                                                                   │
 │    Read(.env*), Read(**/secrets/**), Read(**/*credentials*)              │
 │    Read(**/.ssh/id_*), Bash(rm -rf *), Bash(sudo rm *)                  │
 │    Bash(chmod 777 *)                                                     │
 └─────────────────────────────────────────────────────────────────────────┘
```

---

## 9. SRC — Smart Reactive Codebase

Automatic impact analysis system for code changes during pipeline execution.

### Two-Stage Architecture

```
  Stage 1: Silent Logger                 Stage 2: Impact Injector
  ┌──────────────────────────┐           ┌──────────────────────────┐
  │  EVENT: PostToolUse      │           │  EVENT: SubagentStop     │
  │  MATCH: Edit|Write       │           │  MATCH: implementer|     │
  │  MODE:  async            │           │         infra-implementer│
  │                          │           │  MODE:  sync (blocking)  │
  │  on-file-change.sh       │           │  on-implementer-done.sh  │
  │  ┌──────────────────┐   │           │  ┌──────────────────┐   │
  │  │ Extract file_path │   │           │  │ Read change log  │   │
  │  │ Append to logfile │   │           │  │ Deduplicate files│   │
  │  │ (atomic write)    │   │           │  │ Grep dependents  │   │
  │  └──────────────────┘   │           │  │ Build summary    │   │
  │         │                │           │  │ Inject to Lead   │   │
  │         ▼                │           │  └──────────────────┘   │
  │  /tmp/src-changes-       │──────────▶│         │                │
  │       {session}.log      │  (reads)  │         ▼                │
  └──────────────────────────┘           │  additionalContext:      │
                                         │  "SRC IMPACT ALERT:      │
                                         │   3 files changed,       │
                                         │   2 dependents..."       │
                                         └──────────────────────────┘
                                                    │
                                                    ▼
                                         Lead routes to:
                                         /execution-impact
                                         /execution-cascade
```

### SRC Data Flow

```
  implementer edits file.ts
       │
       ▼ (PostToolUse: Edit)
  on-file-change.sh ──▶ /tmp/src-changes-{sid}.log
       │                  "2026-02-15T12:00:00  Edit  /path/file.ts"
       │
       ▼ (SubagentStop: implementer)
  on-implementer-done.sh
       │
       ├── Read /tmp/src-changes-{sid}.log
       ├── Deduplicate: sort -u
       ├── Grep reverse refs in .claude/ and project root
       │   (max 8 dependents, 10s timeout per search)
       ├── Build summary (max 800 chars)
       └── Output: additionalContext → Lead
            │
            ▼
       Lead reads "SRC IMPACT ALERT"
       └── Routes to /execution-impact (analyst)
            └── Routes to /execution-cascade (implementer)
                 └── Re-triggers SRC (convergence loop, max 3 iterations)
```

---

## 10. Context Engineering

### How Lead Routes to Skills

```
  Lead receives user request or pipeline state
       │
       ▼
  Scan Skill L1 descriptions (auto-loaded in system-reminder)
       │
       ├── Match WHEN condition to current pipeline state
       ├── Match DOMAIN to determine phase appropriateness
       ├── Read INPUT_FROM to verify upstream data exists
       └── Select skill with best semantic match
            │
            ▼
  Invoke skill (L2 body loaded into context)
       │
       ▼
  L2 Execution Model determines tier behavior
       │
       ├── TRIVIAL: Lead executes inline
       ├── STANDARD: Spawn 1 agent per DPS template
       └── COMPLEX: Spawn multiple agents per DPS template
            │
            ▼
  Select agent via Agent L1 PROFILE tag (auto-loaded in Task tool)
       │
       ├── Profile B (analyst): Read + Analyze + Write
       ├── Profile C (researcher): + Web access
       ├── Profile D (implementer): + Edit + Bash
       ├── Profile E (infra-impl): + Edit (no Bash)
       ├── Profile F (delivery): + Task API (Update only)
       └── Profile G (pt-manager): + Task API (Create + Update)
```

### L1/L2 Loading Mechanics

```
                              ┌────────────────────┐
                              │   SKILL DEFINITION  │
                              │    (SKILL.md file)  │
                              └────────┬───────────┘
                                       │
                    ┌──────────────────┴───────────────────┐
                    │                                       │
              ┌─────▼─────┐                          ┌─────▼─────┐
              │    L1      │                          │    L2      │
              │ Frontmatter│                          │    Body    │
              │ (≤1024ch)  │                          │ (unlimited)│
              └─────┬──────┘                          └─────┬──────┘
                    │                                       │
                    ▼                                       ▼
           AUTO-LOADED at                          LOADED on invocation
           session start                           (Skill tool call)
           in system-reminder                      into active context
                    │                                       │
                    ▼                                       ▼
           Lead sees ALL 27                        Lead sees ONE skill
           skill summaries                         full methodology
           simultaneously                          at a time
```

### Critical Constraints

| Constraint | Value | Impact |
|------------|-------|--------|
| L1 max chars | 1024 per skill | Truncation if exceeded |
| L1 total budget | 32,000 chars | All 27 auto-loaded skills must fit |
| L1 current usage | ~75% (~24,000) | ~8,000 chars headroom |
| L2 no char limit | Unlimited | But consumes context window |
| Agent MEMORY.md | 200 lines auto-loaded | First 200 lines only |
| maxTurns per agent | 20-50 | One turn = one agentic loop |

---

## 11. Agent Memory System

Persistent knowledge storage per agent, auto-loaded at startup.

### Memory Directory Structure

```
 .claude/agent-memory/
 ├── analyst/
 │   ├── MEMORY.md                     (auto-loaded, 200 line limit)
 │   ├── agent-definition-audit.md     (RSI L4 diagnostic)
 │   ├── hooks-deep-analysis.md        (RSI L3/L4 diagnostic)
 │   ├── skill-l2-logic-audit.md       (RSI L3 diagnostic)
 │   ├── infra-audit-v3.md             (RSI v10.5 audit)
 │   ├── infra-audit-v3-iter4.md       (RSI v10.5 iteration)
 │   ├── infra-audit-v3-final.md       (RSI v10.5 final)
 │   ├── infra-integration-audit.md    (v10.6 integration audit)
 │   ├── srp-analysis.md               (SRP grading of 35 skills)
 │   ├── impact-analysis-gap-report.md (SRC gap analysis)
 │   ├── src-architecture.md           (SRC design doc)
 │   ├── src-interfaces.md             (SRC interface spec)
 │   ├── src-risk-assessment.md        (SRC risk analysis)
 │   └── src-validate-report.md        (SRC validation)
 ├── implementer/                      (MEMORY.md if exists)
 ├── infra-implementer/                (MEMORY.md if exists)
 └── researcher/                       (MEMORY.md if exists)
```

### Memory Configuration per Agent

| Agent | `memory` field | Effect |
|-------|---------------|--------|
| analyst | `project` | MEMORY.md auto-loaded (200 lines) |
| researcher | `project` | MEMORY.md auto-loaded (200 lines) |
| implementer | `project` | MEMORY.md auto-loaded (200 lines) |
| infra-implementer | `project` | MEMORY.md auto-loaded (200 lines) |
| delivery-agent | `none` | No persistent memory (terminal role) |
| pt-manager | `none` | No persistent memory (procedural role) |

---

## 12. Directory Layout

```
 .claude/
 ├── CLAUDE.md                          Team constitution (48 lines)
 ├── README.md                          This file
 ├── settings.json                      Global settings (~110 lines)
 │
 ├── agents/                            Agent definitions (6 files)
 │   ├── analyst.md                       Profile B · Magenta
 │   ├── researcher.md                    Profile C · Yellow
 │   ├── implementer.md                   Profile D · Green
 │   ├── infra-implementer.md             Profile E · Red
 │   ├── delivery-agent.md                Profile F · Cyan
 │   └── pt-manager.md                    Profile G · Blue
 │
 ├── skills/                            Skill definitions (33 dirs)
 │   ├── pre-design-brainstorm/SKILL.md   P0 · Pipeline entry
 │   ├── pre-design-validate/SKILL.md     P0
 │   ├── pre-design-feasibility/SKILL.md  P0
 │   ├── design-architecture/SKILL.md     P1
 │   ├── design-interface/SKILL.md        P1
 │   ├── design-risk/SKILL.md             P1
 │   ├── research-codebase/SKILL.md       P2
 │   ├── research-external/SKILL.md       P2
 │   ├── research-audit/SKILL.md          P2
 │   ├── plan-decomposition/SKILL.md      P3
 │   ├── plan-interface/SKILL.md          P3
 │   ├── plan-strategy/SKILL.md           P3
 │   ├── plan-verify-correctness/SKILL.md P4
 │   ├── plan-verify-completeness/SKILL.md P4
 │   ├── plan-verify-robustness/SKILL.md  P4
 │   ├── orchestration-decompose/SKILL.md P5
 │   ├── orchestration-assign/SKILL.md    P5
 │   ├── orchestration-verify/SKILL.md    P5
 │   ├── execution-code/SKILL.md          P6
 │   ├── execution-infra/SKILL.md         P6
 │   ├── execution-impact/SKILL.md        P6
 │   ├── execution-cascade/SKILL.md       P6
 │   ├── execution-review/SKILL.md        P6
 │   ├── verify-structure/SKILL.md        P7
 │   ├── verify-content/SKILL.md          P7
 │   ├── verify-consistency/SKILL.md      P7
 │   ├── verify-quality/SKILL.md          P7
 │   ├── verify-cc-feasibility/SKILL.md   P7
 │   ├── manage-infra/SKILL.md            Homeostasis
 │   ├── manage-skills/SKILL.md           Homeostasis
 │   ├── manage-codebase/SKILL.md         Homeostasis
 │   ├── self-diagnose/SKILL.md           Homeostasis
 │   ├── self-implement/SKILL.md          Homeostasis
 │   ├── delivery-pipeline/SKILL.md       P8 · Terminal
 │   ├── pipeline-resume/SKILL.md         Cross-cutting
 │   └── task-management/SKILL.md         Cross-cutting
 │
 ├── hooks/                             Hook scripts (5 files + lib/)
 │   ├── on-file-change.sh               PostToolUse(Edit|Write) · async
 │   ├── on-implementer-done.sh           SubagentStop(implementer) · sync
 │   ├── on-pre-compact.sh                PreCompact · sync
 │   ├── on-session-compact.sh            SessionStart(compact) · sync
 │   ├── on-subagent-start.sh             SubagentStart · sync
 │   └── lib/                             Shared hook utilities
 │
 ├── agent-memory/                      Persistent agent knowledge
 │   ├── analyst/                         14 files (MEMORY.md + diagnostics)
 │   ├── implementer/                     MEMORY.md
 │   ├── infra-implementer/               MEMORY.md
 │   └── researcher/                      MEMORY.md
 │
 ├── projects/                          Project-scoped memory
 │   └── -home-palantir/
 │       └── memory/
 │           ├── MEMORY.md                Lead's persistent memory (200L limit)
 │           ├── context-engineering.md   CC native mechanics reference
 │           ├── infrastructure-history.md Version history
 │           ├── skill-optimization-history.md SKL records
 │           ├── agent-teams-bugs.md      Known bugs + workarounds
 │           ├── ontology-pls.md          Ontology PLS handoff
 │           ├── meta-cognition-infra.md  Meta-cognition decisions
 │           └── cc-reference/            Machine-readable CC reference
 │               ├── native-fields.md       Field tables + flag combos
 │               ├── context-loading.md     Loading order + budget
 │               ├── hook-events.md         All 14 hook events
 │               └── arguments-substitution.md  $ARGUMENTS + env vars
 │
 ├── cache/                             Cached artifacts
 │   └── changelog.md
 │
 ├── tasks/                             Task API storage (team-scoped)
 └── teams/                             Team configurations
```

---

## 13. Feedback Guide

This section helps you give precise, actionable feedback to the Lead agent.

### How to Reference Components

When giving feedback, use the exact component path or identifier:

| Component | Reference Format | Example |
|-----------|-----------------|---------|
| Skill | `/skill-name` or `skills/skill-name/SKILL.md` | `/execution-code` |
| Agent | `agents/agent-name.md` | `agents/analyst.md` |
| Hook | `hooks/hook-name.sh` | `hooks/on-file-change.sh` |
| Setting | `settings.json → key.subkey` | `settings.json → env.SLASH_COMMAND_TOOL_CHAR_BUDGET` |
| Phase | `P{N}` | `P6` (execution) |
| Domain | domain name | `verify` domain |
| Constitution | `CLAUDE.md §{N}` | `CLAUDE.md §2.1` |

### Feedback Templates

#### Skill Feedback

```
Skill: /skill-name
Issue: [describe what's wrong or could be better]
Affected: L1 (routing) | L2 (methodology) | both
Severity: CRITICAL | HIGH | MEDIUM | LOW
Suggestion: [your proposed change]
```

#### Agent Feedback

```
Agent: agents/agent-name.md
Issue: [tool missing? wrong constraints? behavior problem?]
Affected: frontmatter (tools/model/memory) | body (guidelines/constraints)
Suggestion: [your proposed change]
```

#### Pipeline Flow Feedback

```
Phase: P{N} → P{M}
Issue: [routing gap? missing handoff? wrong sequence?]
Affected skills: [list]
Current behavior: [what happens now]
Expected behavior: [what should happen]
```

#### Hook Feedback

```
Hook: hooks/hook-name.sh
Event: [which CC event]
Issue: [bug? missing feature? performance?]
Reproduction: [steps to trigger]
```

### Common Feedback Scenarios

| Scenario | What to Tell Lead |
|----------|-------------------|
| Skill produces wrong output | "Run /verify-quality on skill-name" |
| Agent uses wrong tool | "Check agents/name.md tools list vs Profile requirements" |
| Pipeline skips a phase | "Check tier classification — should this be STANDARD not TRIVIAL?" |
| Hook not firing | "Check settings.json hooks → matcher regex for event-name" |
| L1 description unclear | "Run /verify-content on skill-name, description needs WHEN/DOMAIN" |
| New skill needed | "Run /manage-skills to detect domain gaps" |
| INFRA health check | "Run /manage-infra for full integrity scan" |
| Self-improvement | "Run /self-diagnose [focus-area] for INFRA diagnosis, then /self-implement for fixes" |

### Known Bugs to Be Aware Of

| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | Keep prompts focused |
| BUG-004 | HIGH | No cross-agent compaction notification | tmux monitoring |

### Quick Commands

| Command | Purpose |
|---------|---------|
| `/brainstorm [topic]` | Start a new pipeline from scratch |
| `/self-diagnose [focus]` | INFRA health diagnosis (entry point for self-improvement) |
| `/manage-infra` | Full INFRA health check |
| `/manage-skills` | Skill gap detection and management |
| `/delivery-pipeline` | Commit and archive pipeline results |
| `/pipeline-resume [phase]` | Resume interrupted pipeline |
| `/task-management [action]` | Task lifecycle operations |

---

*Generated from .claude/ INFRA v10.9 — 6 agents, 33 skills, 5 hooks*

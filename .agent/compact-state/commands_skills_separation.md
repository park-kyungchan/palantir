# Commands/Skills Separation Plan

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | medium |
| Total Tasks | 16 |
| Files Affected | 21 |
| Migration Pattern | Thin Wrapper + SSOT Skills |

## Requirements

Commands/Skills 분리 - commands/는 thin wrapper로, skills/는 실제 구현으로 분리. DRY 원칙 준수.

### Goals
1. **DRY Principle:** Zero duplication between commands and skills
2. **Single Source of Truth (SSOT):** All protocol logic in skills/
3. **Thin Wrappers:** Commands are ~30 lines max, routing only
4. **Intent Auto-Discovery:** Skills have keyword-based triggers for natural language routing

---

## Current State Analysis

### Commands Directory (16 files)
| File | Lines | Classification | Needs Restructure |
|------|-------|----------------|-------------------|
| protocol.md | 639 | EXPLICIT_ONLY | YES - Primary |
| plan.md | 540 | AUTO_TRIGGERABLE | YES - Primary |
| deep-audit.md | 379 | EXPLICIT_ONLY | YES - Primary |
| audit.md | 293 | AUTO_TRIGGERABLE | YES - Primary |
| ask.md | 275 | AUTO_TRIGGERABLE | YES - Primary |
| execute.md | 200 | EXPLICIT_ONLY | YES - Primary |
| commit-push-pr.md | 189 | EXPLICIT_ONLY | NO - Utility |
| teleport.md | 152 | EXPLICIT_ONLY | NO - Utility |
| memory.md | 149 | AUTO_TRIGGERABLE | NO - Simple |
| quality-check.md | 141 | AUTO_TRIGGERABLE | NO - Simple |
| maintenance.md | 136 | EXPLICIT_ONLY | NO - Simple |
| memory-sync.md | 125 | EXPLICIT_ONLY | NO - Simple |
| consolidate.md | 123 | EXPLICIT_ONLY | NO - Simple |
| governance.md | 87 | AUTO_TRIGGERABLE | Partial |
| init.md | 75 | EXPLICIT_ONLY | NO - Simple |
| palantir-coding.md | 488 | AUTO_TRIGGERABLE | NO - Specialized |

### Skills Directory (5 files)
| File | Lines | User-Invocable | Status |
|------|-------|----------------|--------|
| oda-plan.md | 327 | NO | EXISTS - Keep |
| oda-governance.md | 308 | NO | EXISTS - Keep |
| oda-audit.md | 214 | NO | EXISTS - Keep |
| help-korean.md | 210 | (default) | EXISTS - Keep |
| capability-advisor.md | 206 | (default) | EXISTS - Keep |

---

## Tasks

| # | Phase | Task | Status |
|---|-------|------|--------|
| 1 | Extract | Create oda-ask.md from ask.md | PENDING |
| 2 | Extract | Create oda-deep-audit.md from deep-audit.md | PENDING |
| 3 | Extract | Create oda-protocol.md from protocol.md | PENDING |
| 4 | Extract | Create oda-execute.md from execute.md | PENDING |
| 5 | Enhance | Update oda-plan.md with intent triggers | PENDING |
| 6 | Enhance | Update oda-audit.md with intent triggers | PENDING |
| 7 | Enhance | Update oda-governance.md with intent triggers | PENDING |
| 8 | Wrapper | Replace ask.md with thin wrapper | PENDING |
| 9 | Wrapper | Replace plan.md with thin wrapper | PENDING |
| 10 | Wrapper | Replace audit.md with thin wrapper | PENDING |
| 11 | Wrapper | Replace deep-audit.md with thin wrapper | PENDING |
| 12 | Wrapper | Replace protocol.md with thin wrapper | PENDING |
| 13 | Wrapper | Replace execute.md with thin wrapper | PENDING |
| 14 | Wrapper | Update governance.md to thin wrapper | PENDING |
| 15 | Docs | Update CLAUDE.md Section 9.1 (Commands) | PENDING |
| 16 | Docs | Update CLAUDE.md Section 9.2 (Skills) | PENDING |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 1: Extract | 4 | 0 | PENDING |
| Phase 2: Enhance | 3 | 0 | PENDING |
| Phase 3: Wrapper | 7 | 0 | PENDING |
| Phase 4: Docs | 2 | 0 | PENDING |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/commands_skills_separation.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Thin Wrapper Template (30 lines max)

```markdown
---
name: <command>
description: <Brief 1-2 line description>
argument-hint: <hint>
delegates-to: oda-<command>
version: "2.2.0"
---

# /<command> Command

$ARGUMENTS

> Delegates to: `.claude/skills/oda-<command>.md`

## Quick Usage

```
/<command> <args>
```

## What This Command Does

- <Bullet point 1>
- <Bullet point 2>
- <Bullet point 3>

## Delegation

```python
Skill("oda-<command>", args="$ARGUMENTS")
```

## Related Commands

| Command | Purpose |
|---------|---------|
| /<related1> | <description> |

---

> **Implementation:** See `.claude/skills/oda-<command>.md` for full protocol.
```

---

## Skill Template with Intent Triggers

```yaml
---
name: <skill>
description: <Full description of protocol>
version: "2.1"

# Invocation control
user-invocable: false
command-alias: /<command>

# Intent matching (LLM-native routing)
intents:
  korean:
    - "<keyword1>"
    - "<keyword2>"
  english:
    - "<keyword1>"
    - "<keyword2>"

# Subagent configuration
context: fork
agent: <Explore|Plan|general-purpose>
allowed-tools: Read, Grep, Glob, Bash, Task, TodoWrite

# Protocol metadata
zone: <Pre-Mutation|Post-Mutation>
enforcement: <Stage C Quality Gate>
---

# <Skill Name> Skill

## [Full Protocol Implementation from commands/]
```

---

## Execution Strategy

### Parallel Execution Groups

| Group | Tasks | Can Parallelize |
|-------|-------|-----------------|
| Group 1: Extract | Tasks 1-4 | YES |
| Group 2: Enhance | Tasks 5-7 | YES |
| Group 3: Wrapper | Tasks 8-14 | YES (after Group 1-2) |
| Group 4: Docs | Tasks 15-16 | YES (after Group 3) |

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Extract | general-purpose | fork | 15K |
| Enhance | general-purpose | fork | 10K |
| Wrapper | general-purpose | fork | 5K |
| Docs | general-purpose | fork | 10K |

---

## Critical File Paths

```yaml
commands_to_restructure:
  - .claude/commands/ask.md (275 lines → 30 lines)
  - .claude/commands/plan.md (540 lines → 30 lines)
  - .claude/commands/audit.md (293 lines → 30 lines)
  - .claude/commands/deep-audit.md (379 lines → 30 lines)
  - .claude/commands/protocol.md (639 lines → 30 lines)
  - .claude/commands/execute.md (200 lines → 30 lines)
  - .claude/commands/governance.md (87 lines → 30 lines)

skills_to_create:
  - .claude/skills/oda-ask.md (NEW, ~275 lines)
  - .claude/skills/oda-deep-audit.md (NEW, ~379 lines)
  - .claude/skills/oda-protocol.md (NEW, ~639 lines)
  - .claude/skills/oda-execute.md (NEW, ~200 lines)

skills_to_enhance:
  - .claude/skills/oda-plan.md (add intents)
  - .claude/skills/oda-audit.md (add intents)
  - .claude/skills/oda-governance.md (add intents)

documentation:
  - .claude/CLAUDE.md (Section 9.1, 9.2 updates)
```

---

## Migration Metrics (Expected)

| Metric | Before | After |
|--------|--------|-------|
| Total command lines | ~2,500 | ~250 |
| Total skill lines | ~850 | ~2,500 |
| Logic duplication | High | Zero |
| Commands with full logic | 7 | 0 |
| Skills with intent triggers | 0 | 7 |

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Skill invocation path change | Medium | 30% | Update CLAUDE.md V4.0 section |
| Intent matching false positives | Low | 10% | Add confidence threshold |
| Lost functionality during migration | High | 20% | Phased migration, backup |

### Rollback Strategy

```yaml
rollback_plan:
  trigger: "Any skill invocation failure rate > 5%"
  steps:
    - git checkout HEAD~1 -- .claude/commands/
    - Keep new skills/ files (no conflict)
    - Update CLAUDE.md to use old paths
  time_to_rollback: "< 5 minutes"
```

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Phase 0-4 Analysis | af8e7e7, ae680b1, a3929cd, ae91d3c | completed | No |
| Phase 5 Synthesis | N/A | completed | No |
| Phase 6-8 Plan | N/A | in_progress | No |

---

## CLAUDE.md Updates Required

### Section 9.1 Changes (Slash Commands)

**FROM:**
```markdown
### 9.1 Slash Commands (Unified V2.1.8)

| Command | Version | Path | Description |
|---------|---------|------|-------------|
| `/ask` | V2.1.8 | `.claude/commands/ask.md` | Semantic Integrity Protocol, approval gate |
```

**TO:**
```markdown
### 9.1 Slash Commands (Thin Wrappers V2.2.0)

> **Architecture:** Commands delegate to Skills (DRY pattern)
> **Implementation:** `.claude/skills/oda-*.md` (Single Source of Truth)

| Command | Delegates To | Description |
|---------|--------------|-------------|
| `/ask` | `oda-ask` | Semantic Integrity Protocol |
| `/plan` | `oda-plan` | ODA 3-Stage Planning |
| `/audit` | `oda-audit` | Quick quality scan |
| `/deep-audit` | `oda-deep-audit` | RSIL deep analysis |
| `/execute` | `oda-execute` | Orchestrated execution |
| `/protocol` | `oda-protocol` | Direct 3-Stage Protocol |
| `/governance` | `oda-governance` | Governance compliance |

**Auto-Discovery:** Commands can be triggered via natural language.
```

### Section 9.2 Changes (Internal Skills)

**ADD:**
```markdown
### 9.2 Skills (Implementation Layer)

> **Single Source of Truth:** All protocol logic lives in skills/
> **User-Invocable:** false (accessed via commands)

| Skill | Path | Purpose |
|-------|------|---------|
| `oda-ask` | `.claude/skills/oda-ask.md` | Semantic Integrity Protocol |
| `oda-plan` | `.claude/skills/oda-plan.md` | ODA planning with 3-Stage |
| `oda-audit` | `.claude/skills/oda-audit.md` | 3-Stage audit engine |
| `oda-deep-audit` | `.claude/skills/oda-deep-audit.md` | RSIL synthesis pipeline |
| `oda-protocol` | `.claude/skills/oda-protocol.md` | Direct protocol execution |
| `oda-execute` | `.claude/skills/oda-execute.md` | Orchestrator enforcement |
| `oda-governance` | `.claude/skills/oda-governance.md` | Governance validation |
```

---

## Approval Request

**Plan Summary:**
- Extract 4 new skills from commands
- Enhance 3 existing skills with intent triggers
- Convert 7 commands to thin wrappers
- Update CLAUDE.md documentation

**Estimated Work:** 16 file operations across 4 phases

**Ready for approval?**

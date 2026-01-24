# /execute 전체 아키텍처 리팩토링

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Phases | 6 |
| Files Affected | 8 |
| New Files | 3 |
| Modified Files | 5 |

## Requirements

| # | Requirement | Priority |
|---|-------------|----------|
| R1 | ExecutionOrchestrator.py 생성 - 기존 모듈 통합 Facade | HIGH |
| R2 | PlanFile 모델 - Markdown 양방향 동기화 | HIGH |
| R3 | Result Verification 자동화 (is_summary_only 통합) | HIGH |
| R4 | Recovery Gate - 블로킹 로직 및 복구 옵션 | HIGH |
| R5 | /execute.md 간결화 (598행 → ~150행) | MEDIUM |
| R6 | __init__.py 생성 - 패키지화 | LOW |

## Analysis Summary

### Dual-Path Analysis Results

| Analysis | Source | Key Finding |
|----------|--------|-------------|
| **ODA Protocol (Explore)** | Agent a0068d9 | 8 modules exist but NO __init__.py, NO cross-module imports - each standalone |
| **Plan Subagent** | Agent a1a141c | Composition pattern recommended, Session-Scoped factory, Sync execution |

### Synthesis: Optimal Approach

| Aspect | ODA Finding | Plan Finding | Optimal Choice |
|--------|-------------|--------------|----------------|
| Pattern | Standalone modules | Composition (Facade) | **Composition Facade** |
| Instance | N/A | Session-Scoped Factory | **Session-Scoped** |
| Execution | Sync modules | Sync-ready | **Sync** |
| Plan Sync | Missing | Bidirectional PlanFile | **PlanFile Model** |
| Agent Track | Duplicate in 2 modules | Unified registry | **Unified in Orchestrator** |

## Phases

### Phase 1: Package Foundation
| Item | Detail |
|------|--------|
| **Goal** | Enable module imports via __init__.py |
| **Effort** | trivial |
| **Dependencies** | None |

**Tasks:**
1.  Create `lib/oda/planning/__init__.py` with exports
2.  Verify import paths work

**Files Affected:**
- `lib/oda/planning/__init__.py`

---

### Phase 2: PlanFile Model
| Item | Detail |
|------|--------|
| **Goal** | Bidirectional Markdown ↔ Python sync |
| **Effort** | medium |
| **Dependencies** | Phase 1 |

**Tasks:**
1.  Create `plan_file.py` with `PlanFile` dataclass
2.  Implement `from_markdown()` parser (regex-based)
3.  Implement `to_markdown()` serializer
4.  Handle Tasks table, Agent Registry section, Metadata
5.  Add validation after parse

**Files Affected:**
- `lib/oda/planning/plan_file.py`

---

### Phase 3: ExecutionOrchestrator Core
| Item | Detail |
|------|--------|
| **Goal** | Facade class integrating 3 managers |
| **Effort** | large |
| **Dependencies** | Phase 1, Phase 2 |

**Tasks:**
1.  Create `execution_orchestrator.py` skeleton
2.  Compose: OutputLayerManager, ContextBudgetManager, AgentRegistry
3.  Implement session-scoped factory `get_orchestrator()`
4.  Implement `load_plan()` using PlanFile
5.  Implement `execute_phase()` with delegation pipeline
6.  Integrate TaskDecomposer for scope checking

**Files Affected:**
- `lib/oda/planning/execution_orchestrator.py`
- `lib/oda/planning/agent_registry.py`

---

### Phase 4: Result Verification
| Item | Detail |
|------|--------|
| **Goal** | Auto-detect summary-only, access L2/L3 fallback |
| **Effort** | medium |
| **Dependencies** | Phase 3 |

**Tasks:**
1.  Implement `verify_result()` wrapping `output_layer_manager.is_summary_only()`
2.  Implement L2/L3 content access via `read_layer_auto()`
3.  Track verification status per agent
4.  Update Plan File with verification results

**Files Affected:**
- `lib/oda/planning/execution_orchestrator.py`

---

### Phase 5: Recovery Gate
| Item | Detail |
|------|--------|
| **Goal** | BLOCKING logic + recovery options |
| **Effort** | medium |
| **Dependencies** | Phase 4 |

**Tasks:**
1.  Implement `recovery_gate()` - returns RecoveryDecision
2.  Implement `block_and_recover()` - generates AskUserQuestion options
3.  Add recovery logging to `.agent/logs/recovery_gate.log`
4.  Implement 3-retry limit with user intervention prompt

**Files Affected:**
- `lib/oda/planning/execution_orchestrator.py`

---

### Phase 6: /execute.md Simplification
| Item | Detail |
|------|--------|
| **Goal** | Reduce pseudocode, reference ExecutionOrchestrator |
| **Effort** | small |
| **Dependencies** | Phase 3, 4, 5 |

**Tasks:**
1.  Remove inline pseudocode (Steps 5-7)
2.  Add ExecutionOrchestrator usage reference
3.  Keep: Overview, Role Declaration, Examples
4.  Target: ~150 lines (from 598)

**Files Affected:**
- `/home/palantir/.claude/commands/execute.md`

---

## Critical File Paths

```yaml
# New Files
new_files:
  - lib/oda/planning/__init__.py
  - lib/oda/planning/plan_file.py
  - lib/oda/planning/execution_orchestrator.py

# Modified Files
modified_files:
  - lib/oda/planning/agent_registry.py
  - /home/palantir/.claude/commands/execute.md

# Reference Files (Read-Only)
reference_files:
  - lib/oda/planning/output_layer_manager.py     # is_summary_only:648, verify_subagent_result:757
  - lib/oda/planning/context_budget_manager.py   # check_before_delegation:313
  - lib/oda/planning/task_decomposer.py          # should_decompose:143, decompose:171
  - lib/oda/planning/l2_synthesizer.py           # Markdown parsing patterns:286-326
  - lib/oda/planning/output_schemas.py           # Pydantic schemas for validation
```

## Risk Register

| # | Risk | Severity | Mitigation |
|---|------|----------|------------|
| R1 | Markdown parsing fragility | HIGH | Strict regex patterns, validation after parse |
| R2 | Duplicate agent state | MEDIUM | Consolidate to single registry in Orchestrator |
| R3 | Recovery Gate blocking loops | HIGH | 3-retry limit, always provide manual recovery option |
| R4 | Context overflow during delegation | MEDIUM | Pre-check with ContextBudgetManager |
| R5 | Plan File write conflicts | LOW | Atomic write with temp file |

## Success Criteria

1. [x] `from lib.oda.planning import ExecutionOrchestrator` imports successfully ✅
2. [x] Plan File round-trip: `from_markdown(to_markdown(plan)) == plan` ✅
3. [x] Summary-only detection works: `is_summary_only()` integrated in verify_result() ✅
4. [x] Recovery Gate blocks when result incomplete ✅
5. [x] /execute.md < 200 lines with same functionality ✅ (598→200 lines)

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 1: Package Foundation | 2 | 2 | ✅ COMPLETED |
| Phase 2: PlanFile Model | 5 | 5 | ✅ COMPLETED |
| Phase 3: ExecutionOrchestrator Core | 6 | 6 | ✅ COMPLETED |
| Phase 4: Result Verification | 4 | 4 | ✅ COMPLETED |
| Phase 5: Recovery Gate | 4 | 4 | ✅ COMPLETED |
| Phase 6: /execute.md Simplification | 4 | 4 | ✅ COMPLETED |

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/execute_architecture_refactoring.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING phase
4. Use subagent delegation pattern for implementation

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Codebase Analysis | a0068d9 | completed | No |
| Architecture Design | a1a141c | completed | No |

## Execution Strategy

### Parallel Execution Groups

| Group | Phases | Can Parallelize |
|-------|--------|-----------------|
| Group 1 | Phase 1 | Sequential (foundation) |
| Group 2 | Phase 2 | Sequential (depends on 1) |
| Group 3 | Phase 3-5 | Partially parallel (3 first, then 4-5) |
| Group 4 | Phase 6 | Sequential (after 3-5) |

### Subagent Delegation

| Phase | Subagent Type | Context | Budget |
|-------|---------------|---------|--------|
| Phase 1 | Direct (trivial) | standard | N/A |
| Phase 2 | general-purpose | fork | 15K |
| Phase 3 | general-purpose | fork | 32K (ULTRATHINK) |
| Phase 4 | general-purpose | fork | 15K |
| Phase 5 | general-purpose | fork | 15K |
| Phase 6 | Direct (small) | standard | N/A |

---

> **Approval Required:** Proceed with this 6-phase implementation plan?

---

> **Approval Required:** Proceed with this plan?

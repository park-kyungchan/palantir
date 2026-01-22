# Hook System V2.1.9+ Feature Integration Plan

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | LARGE |
| Total Phases | 6 |
| Files Affected | 6 |
| Estimated Duration | 2-3 sessions |

## Requirements Summary

### 목표
1. additionalContext 기능 통합 (orchestrator_enforcement.py, validate_task_result.py)
2. Setup Hook 신규 구현 (저장소 초기화 자동화)
3. once: true 설정 추가
4. ask_permission 플로우 구현
5. 보안 강화 (Pre-execution validation)

### Deep Audit 발견사항 기반
- V2.1.9 기능 0% 사용 → 100% 목표
- Setup Hook 부재 → 신규 생성
- Quality Gate: CONDITIONAL PASS (4 HIGH/MEDIUM issues)

---

## Implementation Phases

| # | Phase | Priority | Status | Files |
|---|-------|----------|--------|-------|
| 1 | additionalContext (orchestrator_enforcement.py) | HIGH | ✅ COMPLETED | orchestrator_enforcement.py, enforcement_config.yaml |
| 2 | additionalContext (validate_task_result.py) | HIGH | ✅ COMPLETED | validate_task_result.py, validate_task_config.yaml |
| 3 | Setup Hook 신규 구현 | MEDIUM | ✅ COMPLETED | setup.sh (NEW), settings.json |
| 4 | once: true 설정 추가 | MEDIUM | ✅ COMPLETED | settings.json |
| 5 | ask_permission 플로우 | HIGH | ✅ COMPLETED | orchestrator_enforcement.py, enforcement_config.yaml |
| 6 | 보안 강화 (Pre-execution) | HIGH | ✅ COMPLETED | orchestrator_enforcement.py |

---

## Phase Details

### Phase 1: additionalContext (orchestrator_enforcement.py)

**Files:**
- `/home/palantir/.claude/hooks/orchestrator_enforcement.py` (Line 233-260)
- `/home/palantir/.claude/hooks/config/enforcement_config.yaml` (After line 122)

**Changes:**
1. Replace simple systemMessage with structured hookSpecificOutput
2. Add additionalContext with delegation template
3. Include permissionDecision field

**Key Code Pattern:**
```python
output = {
    "decision": "block",
    "systemMessage": "[BLOCK] Complex operation detected.",
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "additionalContext": "## Delegation Required\n..."
    }
}
```

### Phase 2: additionalContext (validate_task_result.py)

**Files:**
- `/home/palantir/.claude/hooks/validate_task_result.py` (Line 308-325)
- `/home/palantir/.claude/hooks/config/validate_task_config.yaml` (After line 74)

**Changes:**
1. Add hookSpecificOutput to validation responses
2. Include L2/L3 paths in additionalContext
3. Add resume command guidance

### Phase 3: Setup Hook Implementation

**Files:**
- `/home/palantir/.claude/hooks/setup.sh` (NEW)
- `/home/palantir/.claude/settings.json` (SessionStart section)

**Purpose:**
- Auto-create .agent directories on session start
- Check database status
- Report workspace health via additionalContext

### Phase 4: once: true Configuration

**Files:**
- `/home/palantir/.claude/settings.json`

**Changes:**
- Add `"once": true` to welcome.sh hook
- Add `"once": true` to setup.sh hook

### Phase 5: ask_permission Flow

**Files:**
- `/home/palantir/.claude/hooks/orchestrator_enforcement.py` (Line 200-240)
- `/home/palantir/.claude/hooks/config/enforcement_config.yaml`

**Changes:**
1. Add permission_categories config (deny/ask/allow)
2. Map categories to permissionDecision values
3. Dangerous operations always "deny", borderline cases "ask"

### Phase 6: Security Hardening

**Files:**
- `/home/palantir/.claude/hooks/orchestrator_enforcement.py` (Line 14-30, 218-230)

**Changes:**
1. Import SecurityValidator from lib/oda/pai/hooks
2. Run security check BEFORE complexity check
3. Block critical security violations immediately

---

## Critical Paths

### Path A: additionalContext Foundation (Sequential)
```
Phase 1 → Phase 2 → Phase 5 → Phase 6
```

### Path B: Setup Hook (Parallel)
```
Phase 3 → Phase 4
```

Can execute Path B in parallel with Path A.

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| additionalContext injection bug (#14281) | MEDIUM | HIGH | Monitor context size |
| ask_permission bypass | LOW | CRITICAL | deny_cats checked first |
| Setup hook blocks session | LOW | HIGH | Always exit 0 |
| SecurityValidator false positives | MEDIUM | MEDIUM | Review DEFAULT_RULES |

---

## Quality Gates

### Phase 1-2 Quality Gate
- [ ] JSON output validates against Claude Code schema
- [ ] additionalContext renders in agent context
- [ ] permissionDecision values correct

### Phase 3-4 Quality Gate
- [ ] setup.sh exits 0 always
- [ ] once: true prevents re-execution
- [ ] Directories created correctly

### Phase 5-6 Quality Gate
- [ ] Dangerous ops always denied
- [ ] Borderline ops trigger ask
- [ ] SecurityValidator fallback works

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/hook_v2_1_9_integration.md`
2. Check TodoWrite for current phase status
3. Continue from first PENDING phase
4. Use parallel execution for independent phases

## Agent Registry

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Deep Audit Stage A | aa2512f | completed | No |
| Deep Audit Stage B | a7b5006 | completed | No |
| Deep Audit Stage C | a2b6421 | completed | No |
| Plan Subagent | aee52b6 | completed | No |
| Evidence Collector | ac90819 | running | Yes |

---

## Execution Strategy

### Parallel Execution Groups
- **Group 1 (Sequential):** Phase 1 → Phase 2 → Phase 5 → Phase 6
- **Group 2 (Parallel):** Phase 3 + Phase 4

### Subagent Delegation
| Phase | Subagent Type | Context | Budget |
|-------|---------------|---------|--------|
| Implementation | general-purpose | standard | 15K |
| Verification | Explore | fork | 5K |

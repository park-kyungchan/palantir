# Claude Code V2.1.x Feature Enhancement Plan

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-11
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | Medium (4 phases) |
| Total Tasks | 14 |
| Files to Create | 2 |
| Files to Modify | 5 |
| Priority | P0 (Feature Gap Closure) |

---

## Problem Statement

Deep-audit identified 4 gaps in Claude Code V2.1.x feature utilization:

1. **PreCompact hook missing** - No context preservation before Auto-Compact
2. **resume parameter unused** - Subagent continuation not implemented
3. **Missing hook events** - PermissionRequest, Notification not defined
4. **Stage C evidence incomplete** - QualityCheck schema lacks detail

---

## Phase 1: Hook Event Definitions (4 tasks)

### 1.1 Add PreCompact event type
- **File:** `lib/oda/pai/hooks/event_types.py`
- **Change:** Add `PRE_COMPACT = "PreCompact"` to HookEventType enum
- **Status:** [ ] PENDING

### 1.2 Add PermissionRequest event type
- **File:** `lib/oda/pai/hooks/event_types.py`
- **Change:** Add `PERMISSION_REQUEST = "PermissionRequest"` to enum
- **Status:** [ ] PENDING

### 1.3 Add Notification event type
- **File:** `lib/oda/pai/hooks/event_types.py`
- **Change:** Add `NOTIFICATION = "Notification"` to enum
- **Status:** [ ] PENDING

### 1.4 Update event bus mappings
- **File:** `lib/oda/pai/hooks/event_types.py`
- **Change:** Add mappings to `HOOK_TO_EVENT_BUS_MAPPING`
- **Status:** [ ] PENDING

---

## Phase 2: PreCompact Hook Implementation (3 tasks)

### 2.1 Create pre-compact handler script
- **File:** `/home/palantir/.claude/hooks/pre-compact.sh`
- **Change:** New script to save context state before Auto-Compact
- **Template:**
```bash
#!/bin/bash
# PreCompact Hook - Save context before compaction
# Pattern follows session-end.sh

CONTEXT_DIR="${HOME}/.agent/compact-state"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$CONTEXT_DIR"

# Save current todos
cp "${HOME}/.claude/todos/current.json" "$CONTEXT_DIR/todos_${TIMESTAMP}.json" 2>/dev/null

# Save plan file references
find "${HOME}/.agent/plans" -name "*.md" -newer "$CONTEXT_DIR/.last_compact" \
  -exec cp {} "$CONTEXT_DIR/" \; 2>/dev/null

# Update last compact marker
touch "$CONTEXT_DIR/.last_compact"

echo "Context saved to $CONTEXT_DIR"
```
- **Status:** [ ] PENDING

### 2.2 Register PreCompact hook in settings.json
- **File:** `/home/palantir/.claude/settings.json`
- **Change:** Add PreCompact to hooks configuration
- **Status:** [ ] PENDING

### 2.3 Integrate with SessionHealth
- **File:** `lib/oda/claude/session_health.py`
- **Change:** Add `snapshot_before_compact()` method
- **Status:** [ ] PENDING

---

## Phase 3: Resume Parameter Integration (4 tasks)

### 3.1 Add resume field to SubTask
- **File:** `lib/oda/planning/task_decomposer.py`
- **Change:** Add `resume: bool = False` and `task_id: str` to SubTask
- **Status:** [ ] PENDING

### 3.2 Update to_task_params method
- **File:** `lib/oda/planning/task_decomposer.py`
- **Change:** Include resume parameter in Task delegation
```python
def to_task_params(self) -> Dict[str, Any]:
    return {
        "description": self.description,
        "prompt": self.prompt,
        "subagent_type": self.subagent_type.value,
        "run_in_background": True,
        "resume": self.task_id if self.resume else None,  # NEW
    }
```
- **Status:** [ ] PENDING

### 3.3 Add plan file resume integration
- **File:** `/home/palantir/.claude/commands/plan.md`
- **Change:** Step 1.8 to include resume context in Quick Resume section
- **Status:** [ ] PENDING

### 3.4 Document in CLAUDE.md
- **File:** `/home/palantir/.claude/CLAUDE.md`
- **Change:** Add resume pattern to Section 2.3
- **Status:** [ ] PENDING

---

## Phase 4: Stage C Evidence Schema (3 tasks)

### 4.1 Create QualityCheck schema
- **File:** `lib/oda/ontology/evidence/quality_checks.py`
- **Change:** New Pydantic models for complete Stage C evidence
```python
from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class CheckStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

class QualityCheck(BaseModel):
    name: str  # "build", "tests", "lint", "typecheck"
    status: CheckStatus
    command: str
    output: Optional[str] = None
    coverage: Optional[str] = None
    duration_ms: Optional[int] = None

class Finding(BaseModel):
    severity: str  # CRITICAL, ERROR, WARNING, INFO
    category: str  # lint, test, type, build
    message: str
    file: str
    line: int
    auto_fixable: bool = False

class StageCEvidence(BaseModel):
    quality_checks: List[QualityCheck]
    findings: List[Finding] = []
    findings_summary: dict = {}
    critical_count: int = 0
    verification_commands: List[str] = []
```
- **Status:** [ ] PENDING

### 4.2 Update stage_requirements.py
- **File:** `lib/oda/claude/stage_requirements.py`
- **Change:** Import and reference QualityCheck schema
- **Status:** [ ] PENDING

### 4.3 Update 3-stage-protocol.md
- **File:** `.claude/references/3-stage-protocol.md`
- **Change:** Document enhanced Stage C evidence schema
- **Status:** [ ] PENDING

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1 | 4 | 4 | COMPLETED |
| 2 | 3 | 3 | COMPLETED |
| 3 | 4 | 4 | COMPLETED |
| 4 | 3 | 3 | COMPLETED |
| **Total** | **14** | **14** | **100%** |

---

## Execution Strategy

### Parallel Execution Groups

**Group A (Independent - can run in parallel):**
- Phase 1.1-1.4: Hook event definitions
- Phase 4.1: QualityCheck schema creation

**Group B (Sequential - depends on Group A):**
- Phase 2.1-2.3: PreCompact handler (depends on 1.1)
- Phase 3.1-3.4: Resume integration

**Group C (Integration - depends on Group B):**
- Phase 4.2-4.3: Schema integration

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Phase 1 | general-purpose | fork | 10K |
| Phase 2 | general-purpose | fork | 15K |
| Phase 3 | general-purpose | fork | 10K |
| Phase 4 | general-purpose | fork | 10K |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/claude_code_v21x_feature_enhancement.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Critical File Paths

```yaml
# Files to create
create:
  - /home/palantir/.claude/hooks/pre-compact.sh
  - lib/oda/ontology/evidence/quality_checks.py

# Files to modify
modify:
  - lib/oda/pai/hooks/event_types.py
  - /home/palantir/.claude/settings.json
  - lib/oda/claude/session_health.py
  - lib/oda/planning/task_decomposer.py
  - lib/oda/claude/stage_requirements.py

# Reference files
reference:
  - .claude/references/3-stage-protocol.md
  - /home/palantir/.claude/CLAUDE.md
```

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| PreCompact timing issues | HIGH | Test with manual compact before Auto-Compact |
| Resume context stale | MEDIUM | Add timestamp validation (>1 hour warning) |
| Hook event name mismatch | HIGH | Verify against Claude Code CLI docs |
| Schema backward compatibility | LOW | Use Optional fields |

---

## Comparison Matrix

| Aspect | ODA Protocol | Plan Subagent | Optimal |
|--------|--------------|---------------|---------|
| Schema alignment | Primary focus | Secondary | Use ODA (evidence schema) |
| Implementation steps | Rigid 3-stage | Flexible phases | Combine (4 phases with parallel groups) |
| Risk assessment | Governance-based | Experience-based | Combined (5 risks identified) |
| File organization | Module-based | Feature-based | Use ODA (lib/oda structure) |

---

## Approval Gate

- [ ] ODA governance passed (no blocked patterns)
- [ ] Architecture reviewed (follows existing patterns)
- [ ] User approved

---

> **Generated:** 2026-01-11 by /plan command
> **Method:** Dual-path analysis (ODA Protocol + Plan Subagent)

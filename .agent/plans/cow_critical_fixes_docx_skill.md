# cow/ Critical Fixes + DOCX Skill Implementation Plan

> **Version:** 1.1 | **Status:** COMPLETED | **Date:** 2026-01-19
> **Protocol:** orchestrator_protocol_v4.1.yaml (BLOCK enforcement)
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | **LARGE** |
| Total Tasks | 9 |
| Files Affected | 10 |
| Estimated Phases | 4 |

## Requirements Summary

From Deep Audit findings, fix 3 CRITICAL issues + implement DOCX Skill (Option 2):

1. **Issue 1:** Stage G (Human Review) Placeholder - `pipeline.py:1272-1301`
2. **Issue 2:** API Key Validation Missing - `config.py:809-823`
3. **Issue 3:** Silent Mathpix Fallback - `pipeline.py:945-964`
4. **Feature:** DOCX Skill Automation - Create `.claude/skills/docx-automation.md`

---

## Tasks

| # | Phase | Task | Status | Subagent |
|---|-------|------|--------|----------|
| 1 | 1 | Fix `is_valid()` to reject missing API keys | PENDING | general-purpose |
| 2 | 1 | Add `validate_api_keys()` method | PENDING | general-purpose |
| 3 | 2 | Implement fail-fast for Stage B (Mathpix) | PENDING | general-purpose |
| 4 | 2 | Add unit tests for Stage B validation | PENDING | general-purpose |
| 5 | 3 | Implement Stage G with ReviewQueueManager | PENDING | general-purpose |
| 6 | 3 | Add `_collect_review_items()` helper | PENDING | general-purpose |
| 7 | 3 | Add unit tests for Stage G | PENDING | general-purpose |
| 8 | 4 | Create DOCXExporter class | PENDING | general-purpose |
| 9 | 4 | Create docx-automation skill file | PENDING | general-purpose |

---

## Progress Tracking

| Phase | Description | Tasks | Completed | Status |
|-------|-------------|-------|-----------|--------|
| 1 | API Key Validation Fix | 2 | 0 | PENDING |
| 2 | Mathpix Fail-Fast | 2 | 0 | PENDING |
| 3 | Stage G Implementation | 3 | 0 | PENDING |
| 4 | DOCX Skill | 2 | 0 | PENDING |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/cow_critical_fixes_docx_skill.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Execution Strategy

### Parallel Execution Groups

```
[Sequential: Phase 1 → Phase 2 → Phase 3]
[Parallel with Phase 3: Phase 4]
```

- **Phase 1 → 2 → 3**: Sequential (dependencies exist)
- **Phase 4**: Can run parallel with Phase 3 (independent)

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Phase 1 (config.py) | general-purpose | standard | 15K |
| Phase 2 (pipeline.py Stage B) | general-purpose | standard | 15K |
| Phase 3 (pipeline.py Stage G) | general-purpose | standard | 15K |
| Phase 4 (DOCX skill) | general-purpose | standard | 15K |

---

## Critical File Paths

```yaml
files_to_modify:
  - path: /home/palantir/cow/src/mathpix_pipeline/config.py
    lines: [809-823]
    reason: "Fix is_valid() + add validate_api_keys()"

  - path: /home/palantir/cow/src/mathpix_pipeline/pipeline.py
    lines: [944-964, 1272-1301]
    reason: "Stage B fail-fast + Stage G implementation"

  - path: /home/palantir/cow/src/mathpix_pipeline/schemas/export.py
    lines: [32-39]
    reason: "Add DOCX to ExportFormat enum"

  - path: /home/palantir/cow/src/mathpix_pipeline/export/exporters/__init__.py
    reason: "Export DOCXExporter"

files_to_create:
  - path: /home/palantir/cow/src/mathpix_pipeline/export/exporters/docx_exporter.py
    reason: "New DOCX exporter class"

  - path: /home/palantir/.claude/skills/docx-automation.md
    reason: "Claude Code DOCX skill"

  - path: /home/palantir/cow/tests/export/test_docx_exporter.py
    reason: "DOCX exporter tests"

dependencies_to_add:
  - package: python-docx
    version: ">=0.8.11"
    file: /home/palantir/cow/requirements.txt
```

---

## Phase 1: API Key Validation Fix

### Task 1.1: Fix `is_valid()` method

**File:** `/home/palantir/cow/src/mathpix_pipeline/config.py:809-823`

**Current Problem:**
```python
def is_valid(self) -> bool:
    warnings = self.validate()
    critical_warnings = [w for w in warnings if "is outside valid range" in w or ...]
    return len(critical_warnings) == 0
```

**Solution:**
```python
def is_valid(self) -> bool:
    warnings = self.validate()
    critical_patterns = [
        "is outside valid range",
        "must be positive",
        "cannot be negative",
        "is not set",  # NEW: API key warnings
    ]
    critical_warnings = [
        w for w in warnings
        if any(pattern in w for pattern in critical_patterns)
    ]
    return len(critical_warnings) == 0
```

### Task 1.2: Add `validate_api_keys()` method

**Add after line 823:**
```python
def validate_api_keys(self) -> Tuple[bool, List[str]]:
    """Validate API keys are properly configured."""
    missing = []
    if not self.mathpix_app_id:
        missing.append("mathpix_app_id")
    if not self.mathpix_app_key:
        missing.append("mathpix_app_key")
    return len(missing) == 0, missing
```

---

## Phase 2: Mathpix Fail-Fast

### Task 2.1: Implement fail-fast for Stage B

**File:** `/home/palantir/cow/src/mathpix_pipeline/pipeline.py:944-964`

**Replace lenient warning with strict error:**
```python
if not hasattr(self, '_mathpix_client'):
    if self.mathpix_config is None:
        error_msg = (
            "Mathpix config not provided. Stage B (TextParse) requires "
            "valid Mathpix credentials. Set MATHPIX_APP_ID and MATHPIX_APP_KEY."
        )
        result.add_error(error_msg, PipelineStage.TEXT_PARSE)
        timing.complete(success=False, error=error_msg)
        return None  # Return None with ERROR, not warning
```

---

## Phase 3: Stage G Implementation

### Task 3.1: Implement `_run_stage_g()`

**File:** `/home/palantir/cow/src/mathpix_pipeline/pipeline.py:1272-1301`

**Replace placeholder with full implementation using existing `human_review/` module:**
- Import `ReviewQueueManager`, `ReviewTask`, `QueueConfig`
- Initialize `_review_queue` in `__init__`
- Collect items below confidence threshold
- Create and enqueue `ReviewTask`

### Task 3.2: Add `_collect_review_items()` helper

**Purpose:** Extract items from semantic graph that need human review based on confidence threshold.

### Task 3.3: Add `_create_review_task()` helper

**Purpose:** Create `ReviewTask` with appropriate priority based on confidence levels.

---

## Phase 4: DOCX Skill

### Task 4.1: Create DOCXExporter class

**File:** `/home/palantir/cow/src/mathpix_pipeline/export/exporters/docx_exporter.py`

**Pattern:** Follow `BaseExporter` from `base.py`:
- Implement `format`, `content_type`, `file_extension` properties
- Implement `export_to_bytes()` using python-docx
- Implement `export()` with proper error handling

### Task 4.2: Create docx-automation skill

**File:** `/home/palantir/.claude/skills/docx-automation.md`

**Pattern:** Follow existing skill template from `oda-objecttype.md`:
- YAML frontmatter with intents
- Purpose section
- CLI actions (/docx generate, /docx from-json)
- Integration with DOCXExporter

---

## Quality Gates

| Phase | Test Command | Expected Result |
|-------|--------------|-----------------|
| 1 | `pytest cow/tests/test_config.py -k api_key -v` | 2 tests PASS |
| 2 | `pytest cow/tests/test_pipeline.py -k stage_b -v` | 2 tests PASS |
| 3 | `pytest cow/tests/test_pipeline.py -k stage_g -v` | 3 tests PASS |
| 4 | `pytest cow/tests/export/test_docx_exporter.py -v` | 2 tests PASS |

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Phase 1 Analysis | a3cd644 | completed | No |
| Skill Pattern Search | a759136 | completed | No |
| Phase 1 Implementation | pending | pending | - |
| Phase 2 Implementation | pending | pending | - |
| Phase 3 Implementation | pending | pending | - |
| Phase 4 Implementation | pending | pending | - |

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Stage G integration with existing queue | Medium | High | Use existing ReviewQueueManager API |
| python-docx version compatibility | Low | Medium | Pin version >=0.8.11 |
| Test coverage gaps | Medium | Medium | Add comprehensive unit tests |
| Backward compatibility | Low | High | No breaking changes to public API |

---

## Approval Checklist

- [ ] Phase 1: API Key Validation Fix
- [ ] Phase 2: Mathpix Fail-Fast
- [ ] Phase 3: Stage G Implementation
- [ ] Phase 4: DOCX Skill
- [ ] All quality gates passed
- [ ] User approved plan

---

**Protocol Compliance:** orchestrator_protocol_v4.1.yaml (BLOCK enforcement active)

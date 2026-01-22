# Output Preservation Problem - Lightweight Solution

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | **small** (focused fix) |
| Total Tasks | 4 |
| Files Affected | 3 (2 new, 1 modify) |
| Lines of Code | ~150 lines total |

---

## Problem Statement

**Output Preservation Problem:**
```
병렬 Subagent 배포 → 대량 Output → Auto-Compact → 요약만 남음
→ Main Agent가 요약만으로 작업 → 데이터 손실
```

**Root Cause (from deep-audit):**
- `lib/oda/planning/` contains 5,079 lines - ALL DEAD CODE (no external imports)
- Core verification functions exist but are NEVER called
- No enforcement mechanism: PostToolUse Hook missing

---

## Solution Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  LIGHTWEIGHT ENFORCEMENT                        │
│                                                                 │
│  Task() result → PostToolUse Hook → Summary detected?           │
│                                          │                       │
│                            ┌─────────────┴─────────────┐        │
│                            No                          Yes       │
│                            ↓                           ↓        │
│                       Pass through              Write L2 file   │
│                                                 Return L1+path  │
│                                                                 │
│  /execute → Step 6 Verification → Summary only?                 │
│                                          │                       │
│                            ┌─────────────┴─────────────┐        │
│                            No                          Yes       │
│                            ↓                           ↓        │
│                       Proceed                    BLOCK + Guide  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tasks

| # | Phase | Task | Status | Files |
|---|-------|------|--------|-------|
| 1 | Core | Extract `is_summary_only()` to standalone module | ✅ completed | `lib/oda/planning/output_verification.py` |
| 2 | Hook | Create PostToolUse Hook with summary detection | ✅ completed | `.claude/hooks/output_preservation_hook.py` |
| 3 | Config | Add hook configuration + register in settings.json | ✅ completed | `.claude/hooks/config/output_preservation_config.yaml` |
| 4 | Execute | Integrate forced verification in /execute Step 6 | ✅ completed | `/home/palantir/.claude/commands/execute.md` |

---

## Phase 1: Core Module (output_verification.py)

**목적:** 핵심 로직만 추출하여 가볍고 의존성 없는 모듈 생성

**Source Reference:** `lib/oda/planning/output_layer_manager.py:625-812`

### Essential Code (~100 lines)

```python
# lib/oda/planning/output_verification.py

"""
Output Verification Module - Lightweight Edition
================================================

Extracted from output_layer_manager.py for Output Preservation enforcement.
Only includes essential functions:
- is_summary_only() - Summary detection
- verify_subagent_result() - Result verification
- read_layer_auto() - L2/L3 fallback access
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple

# ===== CONSTANTS =====
SUMMARY_INDICATORS = [
    r"^\s*✅\s+\w+\[",             # L1 Headline format
    r"^\s*⚠️\s+\w+\[",
    r"^\s*❌\s+\w+\[",
    r"summary\s*only",
    r"truncated",
    r"\.{3}\s*$",
    r"see\s+(L2|L3|full|detailed)",
    r"abbreviated",
]

COMPLETENESS_INDICATORS = [
    r"files_viewed\s*[=:]\s*\[",
    r"lines_referenced",
    r"## Critical Findings",
    r"## Recommendations",
    r"## Evidence",
]

MIN_COMPLETE_CHARS = 500
MIN_COMPLETE_LINES = 20


# ===== CORE FUNCTIONS =====

def is_summary_only(result: str) -> Tuple[bool, List[str]]:
    """Detect if result is a summary/headline."""
    reasons = []

    if not result or len(result.strip()) < 50:
        return True, ["empty_or_too_short"]

    # Check for summary indicators
    for pattern in SUMMARY_INDICATORS:
        if re.search(pattern, result, re.IGNORECASE | re.MULTILINE):
            reasons.append(f"pattern:{pattern[:20]}")

    # Check length thresholds
    if len(result) < MIN_COMPLETE_CHARS:
        reasons.append(f"short_chars:{len(result)}")

    if result.count('\n') + 1 < MIN_COMPLETE_LINES:
        reasons.append(f"few_lines:{result.count(chr(10)) + 1}")

    # Check for completeness (positive evidence)
    completeness_score = sum(
        1 for p in COMPLETENESS_INDICATORS
        if re.search(p, result, re.IGNORECASE | re.MULTILINE)
    )

    if completeness_score >= 2:
        return False, []

    return bool(reasons), reasons


def read_l2_file(agent_id: str, agent_type: str = "general") -> Optional[str]:
    """Read L2 structured report if exists."""
    patterns = [
        f".agent/outputs/{agent_type}/{agent_id}_structured.md",
        f".agent/outputs/{agent_type}/{agent_id}.md",
        f".agent/outputs/{agent_type.lower()}/{agent_id}_structured.md",
    ]
    for pattern in patterns:
        path = Path(pattern)
        if path.exists():
            return path.read_text()
    return None


def read_l3_file(agent_id: str) -> Optional[str]:
    """Read L3 raw output if exists."""
    import glob
    patterns = [
        f"/tmp/claude/**/tasks/{agent_id}.output",
        f"/tmp/claude-*/tasks/{agent_id}.output",
    ]
    for pattern in patterns:
        matches = glob.glob(pattern, recursive=True)
        if matches:
            return Path(matches[0]).read_text()
    return None


def verify_subagent_result(
    result: str,
    agent_id: str,
    agent_type: str = "general"
) -> Tuple[str, str]:
    """
    Verify result completeness, return detailed content if available.

    Returns:
        (content, status) where status is one of:
        - "complete": Original result is complete
        - "l2_accessed": Detailed L2 content retrieved
        - "l3_accessed": Detailed L3 content retrieved
        - "needs_redelegation": No detailed content, must re-delegate
    """
    is_summary, reasons = is_summary_only(result)

    if not is_summary:
        return result, "complete"

    # Try L2 first
    l2 = read_l2_file(agent_id, agent_type)
    if l2:
        return l2, "l2_accessed"

    # Try L3 fallback
    l3 = read_l3_file(agent_id)
    if l3:
        return l3, "l3_accessed"

    return result, "needs_redelegation"
```

---

## Phase 2: PostToolUse Hook (output_preservation_hook.py)

**목적:** Task 결과가 Summary일 때 자동으로 L2 생성 + L1 반환

### Hook Implementation (~40 lines)

```python
#!/usr/bin/env python3
"""
PostToolUse Hook: Output Preservation
=====================================
Triggers: Task tool completion
Action: Detect summary → Write L2 → Return L1 + guidance
"""

import json
import sys
from pathlib import Path

# Import lightweight verification
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib/oda/planning"))
from output_verification import is_summary_only

def main():
    hook_input = json.loads(sys.stdin.read())

    tool_name = hook_input.get("tool_name", "")
    tool_result = hook_input.get("tool_result", {})

    # Only process Task tool
    if tool_name != "Task":
        print(json.dumps({"continue": True}))
        return

    result_text = str(tool_result.get("result", ""))
    agent_id = tool_result.get("agent_id", "unknown")

    is_summary, reasons = is_summary_only(result_text)

    if not is_summary:
        # Complete result - pass through
        print(json.dumps({"continue": True}))
        return

    # Summary detected - write L2 and provide guidance
    l2_dir = Path(".agent/outputs/general")
    l2_dir.mkdir(parents=True, exist_ok=True)
    l2_path = l2_dir / f"{agent_id}_structured.md"
    l2_path.write_text(result_text)

    guidance = f"""
⚠️ **Output Preservation Alert**

Summary detected (reasons: {', '.join(reasons)})

**L2 Report saved:** `{l2_path}`
**Agent ID:** `{agent_id}`

To access full details:
- `Read("{l2_path}")`
- Or `Task(resume="{agent_id}")`
"""

    print(json.dumps({
        "continue": True,
        "additionalContext": guidance
    }))

if __name__ == "__main__":
    main()
```

---

## Phase 3: Hook Configuration

### Config File (~15 lines)

```yaml
# .claude/hooks/config/output_preservation_config.yaml

hook_name: output_preservation
version: "1.0.0"
enabled: true

triggers:
  - event: PostToolUse
    tool: Task

thresholds:
  min_chars: 500
  min_lines: 20

actions:
  on_summary_detected:
    - write_l2_report
    - inject_guidance
```

---

## Phase 4: /execute Integration

**목적:** Step 6에 강제 검증 로직 추가

### Changes to execute.md

Add to Step 6 (RESULT VERIFICATION):

```markdown
### Step 6: RESULT VERIFICATION (결과 검증) ★ ENFORCED

**V2.1.12 Enhancement:** Uses `output_verification.py` for forced detection.

```python
from lib.oda.planning.output_verification import verify_subagent_result

# After each Task completion
result, status = verify_subagent_result(task_output, agent_id, agent_type)

if status == "complete":
    update_todo_status(phase, "completed")

elif status in ("l2_accessed", "l3_accessed"):
    # Got detailed content - proceed
    task_output = result
    update_todo_status(phase, "completed", f"({status})")

elif status == "needs_redelegation":
    # BLOCK - cannot proceed without full results
    update_todo_content(
        phase,
        f"⚠️ BLOCKED: Summary only - Resume required | Agent: {agent_id}"
    )
    AskUserQuestion([{
        "question": "결과가 요약만 수신되었습니다. 어떻게 진행할까요?",
        "options": [
            {"label": "Resume Agent", "description": f"Task(resume='{agent_id}')"},
            {"label": "Re-execute Phase", "description": "처음부터 다시 실행"},
        ]
    }])
```

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1. Core | 1 | 1 | ✅ COMPLETED |
| 2. Hook | 1 | 1 | ✅ COMPLETED |
| 3. Config | 1 | 1 | ✅ COMPLETED |
| 4. Execute | 1 | 1 | ✅ COMPLETED |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/output_preservation_lightweight.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Execution Strategy

### Parallel Execution Groups

| Group | Phases | Mode |
|-------|--------|------|
| 1 | Phase 1 (Core) | Sequential - dependency |
| 2 | Phase 2, 3 (Hook + Config) | Parallel - independent |
| 3 | Phase 4 (Execute) | Sequential - requires 1-3 |

### Subagent Delegation

| Task | Subagent Type | Budget |
|------|---------------|--------|
| Create output_verification.py | general-purpose | 5K |
| Create hook + config | general-purpose | 5K |
| Update execute.md | general-purpose | 5K |

---

## Critical File Paths

```yaml
new_files:
  - lib/oda/planning/output_verification.py      # ~100 lines
  - .claude/hooks/output_preservation_hook.py    # ~40 lines
  - .claude/hooks/config/output_preservation_config.yaml  # ~15 lines

modified_files:
  - .claude/commands/execute.md                  # Step 6 update

reference_files:
  - lib/oda/planning/output_layer_manager.py:625-812  # Source for extraction
```

---

## Benefits

| Metric | Before | After |
|--------|--------|-------|
| Code Size | 5,079 lines (dead) | ~150 lines (active) |
| Enforcement | Advisory only | BLOCKING |
| Auto-Recovery | Manual | Automatic L2/L3 |
| Hook Integration | Missing | PostToolUse |

---

## Approval Checklist

- [ ] Plan reviewed
- [ ] Approach approved (lightweight extraction)
- [ ] Ready to proceed with implementation

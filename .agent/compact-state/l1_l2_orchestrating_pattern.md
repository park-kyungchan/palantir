# Plan: L1/L2 Orchestrating Pattern Enhancement

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-20
> **Auto-Compact Safe:** This file persists across context compaction
> **Draft Reference:** `.agent/plans/draft_l1_l2_orchestrating_pattern.md`

---

## Overview

| Item | Value |
|------|-------|
| Complexity | large |
| Total Phases | 5 |
| Files Affected | 10+ |
| Estimated Effort | medium-large |

---

## Requirements Summary

Main Agent의 Orchestrating-Role을 고도화하여:
1. Subagent 위임 시 **프롬프트로 L1/L2 출력형식을 강제**
2. L1(Summary+Index)만으로 Orchestrating
3. 필요 시 L2의 **특정 부분만** 참조하는 Loop 패턴 구현

---

## Synthesized Approach

### Analysis Comparison

| Aspect | ODA Protocol (a040c4e) | Explore (ac64cdf) | Optimal Synthesis |
|--------|------------------------|-------------------|-------------------|
| Schema Design | L1Output + L2IndexEntry Pydantic | Existing hooks already validate | **Use Pydantic for L1, leverage existing hook validation** |
| Prompt Injection | `_l1l2_template()` method | `pre_task_injection.py` exists | **Extend pre_task_injection.py + prompt_templates.py** |
| L2 Storage | PostToolUse write enhancement | Hook validates but doesn't create | **Enhance PostToolUse to create L2 files** |
| Integration | CLAUDE.md Section 2.11 | Skills reference L2/L3 access | **Update CLAUDE.md + skill templates** |

### Architecture Decision

```
┌─────────────────────────────────────────────────────────────────┐
│                   L1/L2 Orchestrating Flow                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Main Agent                                                     │
│      │                                                          │
│      ├─▶ Task(prompt + L1/L2 format enforced)                   │
│      │        │                                                 │
│      │        ▼                                                 │
│      │   PreToolUse Hook (force_background + L1/L2 inject)      │
│      │        │                                                 │
│      │        ▼                                                 │
│      │   Subagent executes                                      │
│      │        │                                                 │
│      │        ├─▶ Writes L2 to .agent/outputs/{type}/{id}.md    │
│      │        │                                                 │
│      │        └─▶ Returns L1 only (~500 tokens)                 │
│      │                │                                         │
│      │                ▼                                         │
│      │        PostToolUse Hook (validate + ensure L2 exists)    │
│      │                │                                         │
│      ◀────────────────┘                                         │
│      │                                                          │
│  Orchestrating Decision based on L1                             │
│      │                                                          │
│      ├─▶ status == "success" && !requiresL2Read?                │
│      │       └─▶ Proceed to next phase                          │
│      │                                                          │
│      └─▶ requiresL2Read == true?                                │
│              └─▶ Read(l2Path, offset, limit) ← from l2Index     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: L1/L2 Output Schema Definition
**Status:** ✅ COMPLETED (2026-01-20)
**Files:**
- `lib/oda/planning/output_schemas.py`

**Tasks:**
- [x] Add `L2IndexEntry` Pydantic model (anchor pattern: `^#[\w-]+$`, lines pattern: `^\d+-\d+$`)
- [x] Add `L1Output` Pydantic model with 500 token budget (summary: 200 chars max)
- [x] Add `L1OutputStatus` enum (success, partial, failed)
- [x] Register `l1` and `l1_output` in `SCHEMA_REGISTRY`
- [x] Add validation for anchor format (regex pattern)
- [x] Add `get_line_range()` helper method for selective L2 reading

**Verification:**
```
✓ L2IndexEntry: #findings, 50-120
✓ L1Output: task_abc123, status=success
✓ Line range for #findings: (50, 120)
✓ Schema registry: l1 -> L1Output
✓ Anchor validation works: ValidationError
```

**L1Output Schema:**
```yaml
taskId: str          # Unique task identifier
agentType: str       # Explore, Plan, general-purpose
summary: str         # max 200 chars
status: str          # success | partial | failed
findingsCount: int   # Total findings
criticalCount: int   # Critical findings
l2Index:             # List[L2IndexEntry]
  - anchor: "#findings"
    lines: "50-120"
    description: "Detailed findings"
l2Path: str          # .agent/outputs/{type}/{id}.md
nextActionHint: str  # max 150 chars
requiresL2Read: bool # Whether L2 reading recommended
```

---

### Phase 2: Prompt Template Enhancement
**Status:** pending
**Files:**
- `lib/oda/planning/prompt_templates.py`
- `.claude/hooks/l1l2/pre_task_injection.py`

**Tasks:**
- [ ] Create `_l1l2_template()` method in PromptTemplateBuilder
- [ ] Update `build_structured_prompt()` to include L1/L2 format
- [ ] Enhance `pre_task_injection.py` L1L2_CONSTRAINT constant
- [ ] Add task_id and agent_type placeholder substitution

---

### Phase 3: PostToolUse Hook Enhancement
**Status:** pending
**Files:**
- `.claude/hooks/l1l2/post-task-output.sh`

**Tasks:**
- [ ] Add `write_l2_file()` function
- [ ] Parse L2 content from subagent output
- [ ] Create `.agent/outputs/{type}/` directory structure
- [ ] Validate L1 structure compliance
- [ ] Add retry logic for L2 write failures

---

### Phase 4: CLAUDE.md Documentation
**Status:** pending
**Files:**
- `.claude/CLAUDE.md`

**Tasks:**
- [ ] Add Section 2.11: L1/L2 Orchestrating Loop
- [ ] Document L1/L2/L3 layer separation
- [ ] Add orchestrating decision flow
- [ ] Include L2 selective reading pattern

---

### Phase 5: Integration Testing & Skill Updates
**Status:** pending
**Files:**
- `.claude/skills/plan.md`
- `.claude/skills/audit.md`
- `.claude/commands/execute.md`

**Tasks:**
- [ ] Test basic flow: /plan generates L1 with l2Index
- [ ] Test selective read: Main Agent reads specific L2 section
- [ ] Test error handling: Invalid L1 format triggers warning
- [ ] Update skill templates to reference L1/L2 pattern
- [ ] Verify Auto-Compact survival of L2 files

---

## Critical File Paths

```yaml
schemas:
  - lib/oda/planning/output_schemas.py:113  # Add after ExecutionOutput

templates:
  - lib/oda/planning/prompt_templates.py:132  # _default_template method
  - .claude/hooks/l1l2/pre_task_injection.py:12  # L1L2_CONSTRAINT

hooks:
  - .claude/hooks/l1l2/post-task-output.sh:67  # validate_l2_exists
  - .claude/hooks/l1l2/force_background.py  # No changes needed

documentation:
  - .claude/CLAUDE.md  # Section 2.11 addition

skills:
  - .claude/skills/plan.md
  - .claude/skills/audit.md
  - .claude/commands/execute.md
```

---

## Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| L1 token overflow | High | Strict `max_length` in Pydantic fields |
| L2 write failure | High | PostToolUse retry logic, fallback to L3 |
| Anchor mismatch | Medium | Validation in PostToolUse hook |
| Backward compatibility | Medium | New schemas are additive |
| Auto-Compact L2 loss | Medium | Store in `.agent/outputs/` (permanent) |

---

## Quality Gates

| Gate | Pass Criteria |
|------|---------------|
| Schema Validation | L1Output Pydantic model validates |
| Token Budget | L1 output < 500 tokens |
| L2 Creation | File exists in `.agent/outputs/` after Task() |
| Anchor Consistency | All l2Index anchors exist as headings in L2 |
| Selective Read | `Read(path, offset, limit)` returns correct section |

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| ODA Protocol Analysis | a040c4e | completed | No |
| Explore Analysis | ac64cdf | completed | No |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/l1_l2_orchestrating_pattern.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING phase
4. Reference draft for Q&A history: `.agent/plans/draft_l1_l2_orchestrating_pattern.md`

---

## Approval Required

이 구현 계획을 승인하시겠습니까?

**다음 단계:**
- 승인 시: Phase 1부터 순차 구현 시작
- 수정 필요 시: 피드백 반영 후 계획 업데이트

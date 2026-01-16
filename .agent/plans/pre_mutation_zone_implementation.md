# Pre-Mutation Zone Implementation Plan

> **Version:** 1.0 | **Status:** APPROVED | **Date:** 2026-01-11
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | Large (6 phases) |
| Total Tasks | 27 |
| Files to Create | 11 |
| Files to Modify | 4 |
| Priority | P0 (Critical Path) |

---

## Phase 1: Layer 2 - References (6 tasks)

### 1.1 Create directory structure
```bash
mkdir -p /home/palantir/park-kyungchan/palantir/.claude/references/
```

### 1.2 native-capabilities.md
- **Path:** `.claude/references/native-capabilities.md`
- **Content:** Tool matrix, context modes (fork/standard), output budgets (5K/10K/15K)
- **Sources:** CLAUDE.md sections 2.4, 2.6, 7
- **Status:** [ ] PENDING

### 1.3 3-stage-protocol.md
- **Path:** `.claude/references/3-stage-protocol.md`
- **Content:** Stage A/B/C definitions, evidence schemas, anti-hallucination rules
- **Sources:** `.agent/rules/governance/three_stage_protocol.md`, `anti_hallucination.md`
- **Status:** [ ] PENDING

### 1.4 governance-rules.md
- **Path:** `.claude/references/governance-rules.md`
- **Content:** Blocked patterns, proposal flow, naming conventions, sensitive files
- **Sources:** `.agent/rules/governance/blocked_patterns.md`, `proposal_required.md`, `naming_conventions.md`
- **Status:** [ ] PENDING

### 1.5 pai-integration.md
- **Path:** `.claude/references/pai-integration.md`
- **Content:** PAI ObjectTypes, module structure, evidence types, safety rules
- **Sources:** `lib/oda/pai/` module structure
- **Status:** [ ] PENDING

### 1.6 delegation-patterns.md
- **Path:** `.claude/references/delegation-patterns.md`
- **Content:** Subagent prompt templates, decomposition rules, parallel execution patterns
- **Sources:** CLAUDE.md sections 2.1-2.6
- **Status:** [ ] PENDING

---

## Phase 2: Layer 3 - Skills (5 tasks)

### 2.1 Design /pre-check skill
- **Purpose:** Combined Stage A+B quick validation gate
- **Triggers:** Keywords ["pre-check", "검증", "validate"]
- **Output:** StageResult with files_viewed, imports_verified
- **Status:** [ ] PENDING

### 2.2 Implement /pre-check skill
- **Path:** `.claude/skills/pre-check.md`
- **Integration:** Register in SkillRouter
- **Status:** [ ] PENDING

### 2.3 Design /evidence-report skill
- **Purpose:** Generate audit trail from StageResult evidence
- **Output:** Markdown report with files_viewed, lines_referenced, code_snippets
- **Status:** [ ] PENDING

### 2.4 Implement /evidence-report skill
- **Path:** `.claude/skills/evidence-report.md`
- **Status:** [ ] PENDING

### 2.5 Update skill dependency graph
- **Path:** `.claude/references/skill-dependencies.md`
- **Content:** Mermaid diagram of skill invocation order
- **Status:** [ ] PENDING

---

## Phase 3: Layer 4 - Agents (3 tasks)

### 3.1 governance-gate.md
- **Path:** `.claude/agents/governance-gate.md`
- **Role:** Pre-execution governance check
- **Tools:** Read, Grep
- **Model:** haiku
- **Context:** standard
- **Status:** [ ] PENDING

### 3.2 proposal-manager.md
- **Path:** `.claude/agents/proposal-manager.md`
- **Role:** Hazardous action proposal workflow
- **Tools:** Read, Task
- **Model:** sonnet
- **Context:** fork
- **Status:** [ ] PENDING

### 3.3 rollback-controller.md
- **Path:** `.claude/agents/rollback-controller.md`
- **Role:** Undo failed mutations
- **Tools:** Read, Bash, Write
- **Model:** sonnet
- **Context:** fork
- **Status:** [ ] PENDING

---

## Phase 4: Trigger Detection Optimization (3 tasks)

### 4.1 Add keyword index
- **File:** `lib/oda/pai/skills/trigger_detector.py`
- **Change:** Add `_keyword_index: Dict[str, List[str]]` at registration
- **Impact:** O(1) keyword lookup vs O(n) scan
- **Status:** [ ] PENDING

### 4.2 Implement parallel phase detection
- **File:** `lib/oda/pai/skills/trigger_detector.py`
- **Change:** Run keyword/pattern/context matching in parallel
- **Method:** `asyncio.gather()` for independent phases
- **Status:** [ ] PENDING

### 4.3 Add async detect_parallel() method
- **File:** `lib/oda/pai/skills/trigger_detector.py`
- **Signature:** `async def detect_parallel(self, input_text: str) -> TriggerMatch`
- **Status:** [ ] PENDING

---

## Phase 5: Evidence Auto-Collection (4 tasks)

### 5.1 Design @auto_evidence decorator
- **Purpose:** Auto-capture files_viewed on Read/Grep/Glob operations
- **Location:** `lib/oda/ontology/evidence/collector.py`
- **Status:** [ ] PENDING

### 5.2 Implement auto_evidence decorator
- **File:** `lib/oda/ontology/evidence/collector.py`
- **Pattern:**
```python
@auto_evidence
def read_file(self, path: str) -> str:
    # Automatically adds path to evidence.files_viewed
    ...
```
- **Status:** [ ] PENDING

### 5.3 Convert files_viewed from list to set
- **File:** `lib/oda/ontology/evidence/collector.py`
- **Change:** `self._files_viewed: Set[str] = set()`
- **Benefit:** O(1) deduplication
- **Status:** [ ] PENDING

### 5.4 Add LRU cache for evidence
- **File:** `lib/oda/ontology/evidence/collector.py`
- **Change:** `@functools.lru_cache(maxsize=1000)`
- **Status:** [ ] PENDING

---

## Phase 6: Task Decomposer (4 tasks)

### 6.1 Create task_decomposer.py module
- **Path:** `lib/oda/planning/task_decomposer.py`
- **Status:** [ ] PENDING

### 6.2 Implement should_decompose() logic
- **Triggers:** SCOPE_KEYWORDS = ["전체", "모든", "all", "entire", "complete"]
- **Threshold:** FILE_THRESHOLD = 20
- **Status:** [ ] PENDING

### 6.3 Implement decompose() with token budget
- **Budgets:** Explore=5K, Plan=10K, general-purpose=15K
- **Output:** List[SubTask] with scope, budget, subagent_type
- **Status:** [ ] PENDING

### 6.4 Integrate with Main Agent flow
- **Location:** CLAUDE.md orchestration section
- **Pattern:** Auto-decompose before Task() delegation
- **Status:** [ ] PENDING

---

## Final Quality Gates (2 tasks)

### Run quality checks
- [ ] `pytest` - All tests pass
- [ ] `ruff check` - No linting errors
- [ ] `mypy` - Type checking passes

### Verify ODA governance compliance
- [ ] All new files follow naming conventions
- [ ] No blocked patterns introduced
- [ ] Evidence schemas properly documented

---

## Execution Strategy

### Parallel Execution Groups

**Group A (Independent - can run in parallel):**
- Phase 1.2-1.6: All 5 reference documents
- Phase 3.1-3.3: All 3 agent documents

**Group B (Sequential - depends on Group A):**
- Phase 2.1-2.5: Skills depend on references

**Group C (Code changes - sequential):**
- Phase 4.1 → 4.2 → 4.3
- Phase 5.1 → 5.2 → 5.3 → 5.4
- Phase 6.1 → 6.2 → 6.3 → 6.4

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| References (1.2-1.6) | general-purpose | fork | 10K each |
| Agents (3.1-3.3) | general-purpose | fork | 5K each |
| Skills (2.1-2.5) | Plan | fork | 10K each |
| Code changes (4-6) | general-purpose | fork | 15K each |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1 | 6 | 6 | COMPLETE |
| 2 | 5 | 5 | COMPLETE |
| 3 | 3 | 3 | COMPLETE |
| 4 | 3 | 3 | COMPLETE |
| 5 | 4 | 4 | COMPLETE |
| 6 | 4 | 4 | COMPLETE |
| Final | 2 | 2 | COMPLETE |
| **Total** | **27** | **27** | **100%** |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/pre_mutation_zone_implementation.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Critical File Paths

```yaml
# New files to create
references:
  - .claude/references/native-capabilities.md
  - .claude/references/3-stage-protocol.md
  - .claude/references/governance-rules.md
  - .claude/references/pai-integration.md
  - .claude/references/delegation-patterns.md

skills:
  - .claude/skills/pre-check.md
  - .claude/skills/evidence-report.md

agents:
  - .claude/agents/governance-gate.md
  - .claude/agents/proposal-manager.md
  - .claude/agents/rollback-controller.md

code:
  - lib/oda/planning/task_decomposer.py

# Files to modify
existing:
  - lib/oda/pai/skills/trigger_detector.py
  - lib/oda/ontology/evidence/collector.py
  - .claude/CLAUDE.md (orchestration section)
```

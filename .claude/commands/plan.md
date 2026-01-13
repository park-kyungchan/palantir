---
description: |
  Execute ODA 3-Stage Planning Protocol with Plan subagent comparison.
  Uses dual-path analysis: ODA Protocol + Claude Plan Agent → Optimal synthesis.
allowed-tools: Read, Grep, Glob, Bash, TodoWrite, Task, AskUserQuestion
argument-hint: <요구사항>
---

# /plan Command (Optimized with Plan Subagent)

Transform user requirements into an ODA-aligned implementation plan.
**Unique feature:** Compares ODA 3-Stage Protocol output with Claude's native Plan subagent for optimal synthesis.

## Arguments
$ARGUMENTS - The requirements to plan (in Korean or English)

---

## Execution Strategy: Dual-Path Analysis

This command runs **two parallel analyses** and synthesizes the best approach:

### Path 1: ODA 3-Stage Protocol
Uses internal `oda-plan` skill for schema-first, governance-compliant planning:
- Stage A: BLUEPRINT (Requirements Analysis)
- Stage B: INTEGRATION TRACE (Solution Design)
- Stage C: QUALITY GATE (Plan Validation)

### Path 2: Claude Plan Subagent
Uses native `Task(subagent_type="Plan")` for architectural analysis:
- Identifies critical files
- Considers trade-offs
- Provides implementation steps

### Synthesis: Best of Both
Compare outputs and extract:
- **ODA compliance** from Path 1
- **Architectural insights** from Path 2
- **Risk mitigation** from both

---

## Execution Flow

### Step 1: Initialize Tracking
```
TodoWrite:
- [ ] Parse requirements: $ARGUMENTS
- [ ] Check for scope keywords (decomposition check)
- [ ] Execute ODA 3-Stage Protocol (Path 1)
- [ ] Execute Plan Subagent analysis (Path 2)
- [ ] Synthesize optimal approach
- [ ] Present for user approval
```

### Step 1.5: Task Decomposition Check

**Purpose:** Ensure tasks stay within 32K token output budget for background subagents.

**Reference:** `lib/oda/planning/task_decomposer.py`

#### Scope Keyword Detection

Check if `$ARGUMENTS` contains scope keywords that indicate large-scale analysis:

| Language | Keywords |
|----------|----------|
| Korean | "전체", "모든", "완전한", "전부" |
| English | "all", "entire", "complete", "whole", "full", "every" |

#### Decomposition Logic

```python
# Reference: lib/oda/planning/task_decomposer.py
from lib.oda.planning.task_decomposer import (
    TaskDecomposer,
    SubagentType,
    should_decompose_task,
)

# Step 1.5a: Check if decomposition needed
requirements = "$ARGUMENTS"
scope = "<target_directory>"  # Inferred from requirements

if should_decompose_task(requirements, scope):
    # Decomposition triggers:
    # - Scope keywords detected in requirements
    # - File count > 20 (FILE_THRESHOLD)
    # - Directory count > 5 (DIRECTORY_THRESHOLD)

    decomposer = TaskDecomposer()
    subtasks = decomposer.decompose(requirements, scope, SubagentType.PLAN)

    # Step 1.5b: Deploy parallel subagents (Boris Cherny pattern)
    for subtask in subtasks:
        Task(
            subagent_type="Plan",
            prompt=subtask.prompt,  # Includes output budget constraint
            run_in_background=True,
            description=subtask.description[:50]
        )

    # Wait for all subtasks to complete before Step 2
    # Results will be synthesized in Step 3
```

#### Output Budget Warning

**CRITICAL:** All subagent prompts MUST include this constraint (auto-added by TaskDecomposer):

```markdown
## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED {budget} TOKENS.
Budget by subagent type:
- Explore: 5,000 tokens
- Plan: 10,000 tokens
- general-purpose: 15,000 tokens

Return ONLY: Key findings, critical paths, summary.
DO NOT include: Full file contents, verbose explanations.
Format: Bullet points with file:line references.
```

#### Decomposition Decision Matrix

| Condition | Action | Parallel Deployment |
|-----------|--------|---------------------|
| No scope keywords + <20 files | Skip to Step 2 | No |
| Scope keywords detected | Decompose by subdirectory | Yes |
| File count > 20 | Decompose by subdirectory | Yes |
| Directory count > 5 | Decompose by subdirectory | Yes |

### Step 1.8: Generate Persistent Plan File

**Purpose:** Create `.agent/plans/{slug}.md` for Auto-Compact survival.

**File Path Generation:**
```python
import re
from datetime import datetime

# Generate slug from requirements (first 50 chars, sanitized)
slug = re.sub(r'[^a-z0-9_]', '_', requirements[:50].lower())
slug = re.sub(r'_+', '_', slug).strip('_')
plan_path = f".agent/plans/{slug}.md"
```

**Plan File Template:**
```markdown
# {requirements_title}

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** {date}
> **Auto-Compact Safe:** This file persists across context compaction

## Overview
| Item | Value |
|------|-------|
| Complexity | {complexity} |
| Total Tasks | {task_count} |
| Files Affected | {file_count} |

## Requirements
{parsed_requirements}

## Tasks
| # | Phase | Task | Status |
|---|-------|------|--------|
{task_table}

## Progress Tracking
| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
{progress_table}

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/{slug}.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

## Execution Strategy

### Parallel Execution Groups
{parallel_groups}

### Subagent Delegation
| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
{delegation_table}

## Critical File Paths
```yaml
{file_paths_yaml}
```
```

**Integration with TodoWrite:**
```python
# Auto-sync plan file status with TodoWrite
todos = []
for task in plan_tasks:
    todos.append({
        "content": task.description,
        "status": task.status,  # pending, in_progress, completed
        "activeForm": task.active_form,
    })
TodoWrite(todos=todos)
```

**Plan File Updates:**
Update plan file progress when:
- Task status changes (via TodoWrite sync)
- Phase completes
- Errors occur (add to Findings section)

### Step 2: Parallel Analysis

**Prerequisite:** If Step 1.5 triggered decomposition, wait for subtask results before proceeding.

**Launch simultaneously:**

1. **ODA Protocol Path:**
   ```python
   # Invoke internal oda-plan skill
   # If decomposed: synthesize subtask results first
   Skill("oda-plan", args="$ARGUMENTS")
   ```

2. **Plan Subagent Path:**
   ```python
   # If NOT decomposed (single-scope task):
   Task(
       subagent_type="Plan",
       prompt="""Analyze requirements and design implementation: $ARGUMENTS

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 10000 TOKENS.
Return ONLY: Key findings, critical paths, summary.
Format: Bullet points with file:line references.""",
       description="Plan subagent analysis"
   )

   # If decomposed (from Step 1.5):
   # Skip this step - use synthesized results from decomposed subtasks
   ```

#### Handling Decomposed Results

If Step 1.5 deployed parallel subagents, synthesize results here:

```python
# Collect results from decomposed subtasks
decomposed_results = [
    # Results from each subdirectory analysis
    # Automatically collected from background tasks
]

# Synthesize into unified analysis
unified_analysis = synthesize_plan_results(decomposed_results)

# Use unified_analysis in Step 3 comparison
```

### Step 3: Comparison Matrix

| Aspect | ODA Protocol | Plan Subagent | Optimal |
|--------|--------------|---------------|---------|
| Schema alignment | ✓ Primary focus | Secondary | Use ODA |
| Architectural trade-offs | Basic | ✓ Detailed | Use Plan |
| Evidence collection | ✓ Mandatory | Optional | Use ODA |
| Phase breakdown | Rigid 3-stage | ✓ Flexible | Combine |
| Risk assessment | ✓ Governance-based | Experience-based | Combine |

### Step 4: Synthesis Template

```markdown
# Synthesized Implementation Plan

## 요구사항 (from $ARGUMENTS)
[Parsed requirements]

## 1. ODA Protocol Analysis
### Stage A Findings
[files_viewed, complexity, scope]

### Stage B Design
[ObjectTypes, Actions, phases]

### Stage C Quality Gates
[validation checklist]

## 2. Plan Subagent Insights
### Critical Files Identified
[files that will be affected]

### Architectural Considerations
[trade-offs, patterns, alternatives]

### Recommended Approach
[subagent's synthesis]

## 3. Optimal Synthesis
### Why This Approach
[Rationale combining both analyses]

### Implementation Phases
| Phase | ODA Compliance | Architectural Fit | Priority |
|-------|----------------|-------------------|----------|
| 1     | ✓              | ✓                 | HIGH     |

### Risk Mitigation
[Combined risk assessment]

## 4. Approval Gate
- [ ] ODA governance passed
- [ ] Architecture reviewed
- [ ] User approved
```

---

## Usage Examples

### Basic Usage
```
/plan 사용자 인증 기능 추가
```

### With Context
```
/plan Add pagination to task list API (must be compatible with existing frontend)
```

### Complex Requirement
```
/plan 다음 기능을 구현:
1. Task에 태그 추가 기능
2. 태그별 필터링
3. 태그 자동완성
```

---

## Evidence Requirements

This command enforces anti-hallucination:

- **Minimum 3 files** must be read before planning
- **Specific line references** required for claims
- **ObjectType mapping** must reference existing schemas

```python
if len(evidence.files_viewed) < 3:
    raise AntiHallucinationError("Insufficient file evidence for planning")
```

---

## Integration with Other Commands

| Scenario | Next Command |
|----------|--------------|
| Plan approved | Proceed with implementation |
| Need deeper analysis | `/deep-audit <target>` |
| Governance concern | `/governance` |
| Quality check needed | `/quality-check` |

---

## Native Capability Utilization

This command leverages:

| Capability | Usage |
|------------|-------|
| `Task(Plan)` | Architectural analysis subagent |
| `Skill(oda-plan)` | Internal ODA protocol (user-invocable: false) |
| `TodoWrite` | Progress tracking |
| `AskUserQuestion` | Clarification if requirements unclear |
| `EnterPlanMode` | For very complex multi-phase implementations |

---

## Output Format

Final output follows this structure:

```markdown
# 📋 Implementation Plan: [Title]

## Summary
- Complexity: small/medium/large
- Files affected: N
- Estimated phases: N

## Approach Comparison
| Analysis | Recommendation | Confidence |
|----------|----------------|------------|
| ODA Protocol | [summary] | HIGH |
| Plan Subagent | [summary] | HIGH |
| **Synthesis** | [optimal] | **HIGHEST** |

## Implementation Phases
[Detailed phases with quality gates]

## Risk Register
[Combined risk assessment]

## Approval Required
[ ] Proceed with this plan?
```

---

## Step 7: Update Plan File

After presenting results to user:

### 7.1 Update Plan File Status
```python
plan_content = Read(plan_path)
updated_content = update_plan_status(plan_content, completed_tasks)
Write(plan_path, updated_content)
```

### 7.2 Mark Completion in TodoWrite
```python
TodoWrite(todos=[
    {"content": task, "status": "completed", "activeForm": f"Completed {task}"}
    for task in completed_tasks
])
```

### 7.3 Plan File Status Values

| Status | When to Use |
|--------|-------------|
| `IN_PROGRESS` | Plan is being executed |
| `COMPLETED` | All tasks finished successfully |
| `PAUSED` | User requested pause |
| `BLOCKED` | Waiting for external dependency |
| `FAILED` | Critical error, requires review |

### 7.4 Auto-Compact Recovery

When context is compacted mid-execution:
1. Agent reads `.agent/plans/{slug}.md` to restore state
2. TodoWrite is repopulated from Tasks table
3. Execution resumes from first PENDING task

### 7.5 V2.1.x Resume Parameter Integration

**Agent ID Tracking for Subagent Continuation:**

When delegating to subagents, track agent IDs for potential resume:

```python
# Track agent IDs in plan file
agent_registry = {}

# When deploying subagent
result = Task(
    subagent_type="Explore",
    prompt="...",
    run_in_background=True,
    description="Phase 1 analysis"
)
# Store agent ID from result
agent_registry["phase_1_analysis"] = result.agent_id

# After Auto-Compact, resume using stored ID
from lib.oda.planning.task_decomposer import SubTask, SubagentType

subtask = SubTask(
    description="Continue Phase 1 analysis",
    prompt="Continue from previous state...",
    subagent_type=SubagentType.EXPLORE,
    scope="/path/to/scope",
    token_budget=5000,
)
subtask.mark_for_resume(agent_registry["phase_1_analysis"])

# Deploy with resume
Task(**subtask.to_task_params())  # Includes resume=agent_id
```

**Plan File Agent Registry Section:**

Add this section to plan files for resume tracking:

```markdown
## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Phase 1 Analysis | a1b2c3d | completed | No |
| Phase 2 Design | e4f5g6h | in_progress | Yes |
```

**Resume Eligibility Rules:**
- Only `in_progress` tasks can be resumed
- Agent ID must be less than 1 hour old
- Context window must have space for resumed output

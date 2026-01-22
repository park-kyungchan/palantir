---
description: |
  Execute approved plan with Orchestrator-mode enforcement.
  Ensures Main Agent delegates all work to Subagents.
  Includes automatic result verification and recovery gate.
  **[V2.1.9] Progressive-Disclosure Native - Auto L2 generation via PostToolUse Hook**
allowed-tools: Read, Grep, Glob, Bash, TodoWrite, Task, AskUserQuestion
argument-hint: [plan-file-path]

# V2.1.9 Features
v21x_features:
  progressive_disclosure: true    # Hook auto-generates L2
  suppress_verbose_output: true   # Verbose output hidden from transcript
  auto_l2_generation: true        # L2 structured reports created automatically
  context_efficient: true         # Main Agent context stays lean during execution
---

# /execute Command (Orchestrator Enforcement)

Execute an approved plan while **enforcing Orchestrator-only behavior**.
Main Agent is **prohibited from direct execution** - all work delegated to Subagents.

## Core Principle

```
┌─────────────────────────────────────────────────────────────────┐
│  🎯 ORCHESTRATOR MODE                                           │
│                                                                 │
│  Main Agent = Conductor                                         │
│  - Reads plan                                                   │
│  - Assigns Subagents                                            │
│  - Verifies results                                             │
│  - NEVER executes directly                                      │
│                                                                 │
│  Subagents = Performers                                         │
│  - Explore: Analysis (15K budget)                               │
│  - Plan: Design (25K budget)                                    │
│  - general-purpose: Implementation (32K budget)                 │
└─────────────────────────────────────────────────────────────────┘
```

## Arguments

$ARGUMENTS - Optional path to plan file (defaults to most recent IN_PROGRESS plan)

---

## 7-Step Execution Flow

### Step 1: ROLE DECLARATION (역할 선언)

**Purpose:** Inject Orchestrator identity into TodoWrite as persistent reminder.

**Mandatory First Todo Item:**
```markdown
🎯 ORCHESTRATOR MODE ACTIVE
   ├─ 직접 실행 금지: Edit, Write, 복잡한 Bash 사용 불가
   ├─ 모든 작업은 Task()로 Subagent에 위임
   └─ 결과 검증 필수: 요약만으로 진행 금지
```

**Implementation:**
```python
# MANDATORY: Role declaration MUST be first todo item
orchestrator_declaration = {
    "content": "🎯 ORCHESTRATOR: 직접 실행 금지 - Task()로 Subagent에 위임 | 결과 검증 필수",
    "status": "in_progress",  # Always in_progress to stay visible
    "activeForm": "Orchestrating execution - delegation only"
}

# This item NEVER gets marked as completed
# It persists throughout the entire /execute session
```

---

### Step 2: PLAN RETRIEVAL (Plan 읽기)

**Purpose:** Load the approved plan file for execution.

**Plan File Resolution:**
```python
import os
import glob
from datetime import datetime

def find_plan_file(argument=None):
    """
    Priority order:
    1. Explicit argument (if provided)
    2. Most recent IN_PROGRESS plan
    3. Ask user to select
    """
    if argument:
        return f".agent/plans/{argument}.md"

    # Find all plans
    plans = glob.glob(".agent/plans/*.md")

    # Filter to IN_PROGRESS
    in_progress = []
    for plan_path in plans:
        content = Read(plan_path)
        if "IN_PROGRESS" in content:
            mtime = os.path.getmtime(plan_path)
            in_progress.append((plan_path, mtime))

    if in_progress:
        # Sort by modification time, newest first
        in_progress.sort(key=lambda x: x[1], reverse=True)
        return in_progress[0][0]

    # No IN_PROGRESS plans - ask user
    return None  # Triggers AskUserQuestion
```

**Plan Parsing:**
```python
def parse_plan_file(plan_path):
    """
    Extract execution-relevant information:
    - Tasks table
    - Execution Strategy (Subagent assignments)
    - Critical File Paths
    - Agent Registry (if exists)
    """
    content = Read(plan_path)

    return {
        "tasks": extract_tasks_table(content),
        "strategy": extract_execution_strategy(content),
        "files": extract_critical_files(content),
        "agent_registry": extract_agent_registry(content)
    }
```

---

### Step 3: DELEGATION MAPPING (Subagent 할당)

**Purpose:** Determine optimal Subagent for each Phase.

**Delegation Rules:**

| Task Type | Keywords | Subagent | Budget |
|-----------|----------|----------|--------|
| Analysis | 분석, 탐색, 검토, analyze, explore, audit | Explore | 15K |
| Design | 설계, 계획, 아키텍처, design, plan, architecture | Plan | 25K |
| Implementation | 구현, 작성, 수정, implement, write, modify | general-purpose | 32K |
| Verification | 검증, 테스트, 확인, verify, test, check | general-purpose | 32K |

**Mapping Logic:**
```python
def map_task_to_subagent(task_description):
    """
    Determine subagent type based on task keywords.
    """
    task_lower = task_description.lower()

    # Analysis keywords
    if any(kw in task_lower for kw in ["분석", "탐색", "검토", "analyze", "explore", "audit", "scan"]):
        return ("Explore", 15000)

    # Design keywords
    if any(kw in task_lower for kw in ["설계", "계획", "아키텍처", "design", "plan", "architecture"]):
        return ("Plan", 25000)

    # Default: Implementation
    return ("general-purpose", 32000)
```

---

### Step 4: TODOWRITE GENERATION (TodoWrite 생성)

**Purpose:** Create comprehensive todo list with delegation info and verification requirements.

**Todo Item Format:**
```
[Phase N] {작업 설명}
  → Delegate to: {Subagent}:pending | Budget: {N}K
  → Verify: {검증 요구사항}
  | Files: {대상 파일} | Scope: {범위}
```

**Full TodoWrite Template:**
```python
def generate_execution_todos(plan_data):
    todos = []

    # 1. Orchestrator declaration (ALWAYS FIRST)
    todos.append({
        "content": "🎯 ORCHESTRATOR: 직접 실행 금지 - Task()로 Subagent에 위임 | 결과 검증 필수",
        "status": "in_progress",
        "activeForm": "Orchestrating execution - delegation only"
    })

    # 2. Phase todos
    for i, task in enumerate(plan_data["tasks"]):
        subagent, budget = map_task_to_subagent(task["description"])

        todos.append({
            "content": f"[Phase {i+1}] {task['description']} | → Delegate: {subagent}:pending | Budget: {budget//1000}K | Verify: Full Output 확보",
            "status": "pending",
            "activeForm": f"Delegating Phase {i+1} to {subagent}"
        })

    return todos
```

**Example Output:**
```
🎯 ORCHESTRATOR: 직접 실행 금지 - Task()로 Subagent에 위임 | 결과 검증 필수

[Phase 1] 코드베이스 구조 분석 | → Delegate: Explore:pending | Budget: 15K | Verify: Full Output 확보
[Phase 2] 변경 영향도 분석 | → Delegate: Explore:pending | Budget: 15K | Verify: Full Output 확보
[Phase 3] 구현 설계 검토 | → Delegate: Plan:pending | Budget: 25K | Verify: Full Output 확보
[Phase 4] 기능 구현 | → Delegate: general-purpose:pending | Budget: 32K | Verify: Full Output 확보
[Phase 5] 품질 검증 | → Delegate: general-purpose:pending | Budget: 32K | Verify: Full Output 확보
```

---

### Step 5: ORCHESTRATED EXECUTION (실행)

**Purpose:** Deploy Subagents for each Phase, track Agent IDs.

**Execution Loop:**
```python
from lib.oda.planning.output_layer_manager import OutputLayerManager

output_manager = OutputLayerManager()

for phase in pending_phases:
    # 5.1 Update todo to in_progress
    update_todo_status(phase, "in_progress")

    # 5.2 Deploy Subagent
    result = Task(
        subagent_type=phase["subagent"],
        prompt=generate_subagent_prompt(phase),
        description=f"Phase {phase['number']}: {phase['description'][:30]}",
        run_in_background=False  # Sequential for dependency tracking
    )

    # 5.3 Update todo with Agent ID
    update_todo_content(
        phase,
        f"[Phase {phase['number']}] {phase['description']} | → Delegate: {phase['subagent']}:{result.agent_id}"
    )

    # 5.4 Store in Agent Registry (for resume)
    store_agent_registry(phase["number"], result.agent_id, phase["subagent"])

    # 5.5 Proceed to Step 6 (Verification)
    verified_result = verify_result(result, result.agent_id, phase["subagent"])
```

**Subagent Prompt Template:**
```python
def generate_subagent_prompt(phase):
    return f"""
## Context
Operating under ODA governance with schema-first, action-only mutation pattern.
This is Phase {phase['number']} of the execution plan.

## Task
{phase['description']}

## Scope
Files: {phase['files']}
Budget: {phase['budget']} tokens maximum

## Required Output
- files_viewed: [list of files examined]
- changes_made: [list of modifications] OR findings: [list of analysis results]
- evidence: [specific line references]

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED {phase['budget']} TOKENS.
Return ONLY: Key findings, critical changes, summary.
Format: Bullet points with file:line references.

## IMPORTANT
- Provide COMPLETE results, not summaries
- Include all relevant details
- L2 Report will be generated from this output
"""
```

---

### Step 6: RESULT VERIFICATION (결과 검증) ★ V2.1.9 SIMPLIFIED

**Purpose:** Ensure Main Agent has access to FULL results via L2.

**V2.1.9 Change:** `progressive_disclosure_hook.py` automatically generates L2 reports.
Main Agent no longer needs manual verification - Hook handles this automatically.

**Reference:** `.claude/hooks/progressive_disclosure_hook.py`

**V2.1.9 Automatic Flow:**
```
Task result → Hook intercepts → L2 written → L1 headline returned
```

**Main Agent Receives:**
```
✅ GeneralPurpose[abc123]: Phase 4 complete, 3 files modified

## Subagent Result (Progressive-Disclosure)

**L1 Headline:**
✅ GeneralPurpose[abc123]: Phase 4 complete, 3 files modified

**L2 Report Available:**
Path: `.agent/outputs/general/abc123_structured.md`
To read full details: `Read(".agent/outputs/general/abc123_structured.md")`

**Agent ID (for resume):** `abc123`
```

**Verification Flow (Simplified):**
```python
def verify_result(task_result, agent_id, agent_type):
    """
    V2.1.9: Hook already generated L2. Just check if L2 exists.
    """
    # Hook provides L2 path in additionalContext
    l2_path = f".agent/outputs/{agent_type.lower()}/{agent_id}_structured.md"

    if Path(l2_path).exists():
        # L2 available - can access if details needed
        return task_result, "L2_AVAILABLE"

    # L2 not found (edge case) - use validate_task_result.py fallback
    return task_result, "VERIFY_MANUALLY"
```

**When to Read L2:**
- Phase requires detailed results for next phase
- Synthesis step needs complete information
- Verification of specific file changes

**When L1 Headline Sufficient:**
- Progress tracking (TodoWrite update)
- Simple pass/fail status
- Moving to next independent phase

**Summary Detection Patterns:**
```python
# Patterns indicating summary-only result:
SUMMARY_PATTERNS = [
    r"^\s*✅\s+\w+\[",           # L1 Headline format
    r"summary only",             # Explicit summary marker
    r"truncated",                # Truncation marker
]

# Size thresholds:
SUMMARY_THRESHOLDS = {
    "min_chars": 500,            # < 500 chars = likely summary
    "min_lines": 20,             # < 20 lines = likely summary
}
```

---

### Step 7: RECOVERY GATE (복구 게이트) ★ BLOCKING

**Purpose:** BLOCK progress if only summary available.

**HARD RULE: 요약만으로 다음 단계 진행 금지**

**Recovery Gate Logic:**
```python
def recovery_gate(verification_status, agent_id, phase):
    """
    BLOCKING GATE: Cannot proceed without full results.
    """
    if verification_status == "COMPLETE":
        # Mark phase as completed
        update_todo_status(phase, "completed", f"{phase['subagent']}:{agent_id} (done)")
        return True

    elif verification_status in ["L2_RECOVERED", "L3_RECOVERED"]:
        # Recovered from L2/L3 - can proceed
        update_todo_status(phase, "completed", f"{phase['subagent']}:{agent_id} ({verification_status})")
        return True

    else:  # NEEDS_RECOVERY
        # BLOCK: Cannot proceed
        handle_recovery_failure(agent_id, phase)
        return False

def handle_recovery_failure(agent_id, phase):
    """
    Block progress and guide recovery.
    """
    # Update todo with warning
    update_todo_content(
        phase,
        f"⚠️ BLOCKED: [Phase {phase['number']}] - 결과 검증 실패 | Agent: {phase['subagent']}:{agent_id}"
    )

    # Present recovery options
    AskUserQuestion([{
        "question": f"Phase {phase['number']} 결과가 요약만 수신되었습니다. 어떻게 진행할까요?",
        "header": "Recovery",
        "options": [
            {
                "label": "Resume Agent (Recommended)",
                "description": f"Task(resume='{agent_id}')로 중단된 Agent 재개"
            },
            {
                "label": "Re-execute Phase",
                "description": "해당 Phase를 처음부터 다시 실행"
            },
            {
                "label": "Manual L2 Read",
                "description": f"Read('.agent/outputs/{phase['subagent'].lower()}/{agent_id}.md')로 수동 확인"
            }
        ],
        "multiSelect": False
    }])
```

---

## TodoWrite Update Rules

### During Execution

| Event | Todo Update |
|-------|-------------|
| Phase 시작 | `status: in_progress`, `→ Delegate: {type}:pending` |
| Agent 배포 완료 | `→ Delegate: {type}:{agent_id}` |
| 결과 검증 성공 | `status: completed`, `{type}:{agent_id} (done)` |
| 검증 실패 | `⚠️ BLOCKED: ... | Agent: {type}:{agent_id}` |

### Example Progression

**Initial:**
```
[Phase 1] 코드 분석 | → Delegate: Explore:pending | Budget: 15K
```

**After Deployment:**
```
[Phase 1] 코드 분석 | → Delegate: Explore:a1b2c3d | Budget: 15K
```

**After Verification (Success):**
```
✅ [Phase 1] 코드 분석 | → Delegate: Explore:a1b2c3d (done)
```

**After Verification (Failure):**
```
⚠️ BLOCKED: [Phase 1] 코드 분석 | Agent: Explore:a1b2c3d - Resume 필요
```

---

## Auto-Compact Recovery

### Recovery from TodoWrite

After Auto-Compact, TodoWrite contains all necessary information:

```
🎯 ORCHESTRATOR: 직접 실행 금지 - Task()로 Subagent에 위임 | 결과 검증 필수

✅ [Phase 1] 코드 분석 | → Delegate: Explore:a1b2c3d (done)
✅ [Phase 2] 영향도 분석 | → Delegate: Explore:b2c3d4e (done)
⏳ [Phase 3] 설계 검토 | → Delegate: Plan:c3d4e5f | Budget: 25K
[Phase 4] 구현 | → Delegate: general-purpose:pending | Budget: 32K
```

**Recovery Steps:**
1. Find in_progress Phase: `[Phase 3]`
2. Extract Agent ID: `c3d4e5f`
3. Resume or verify: `Task(resume="c3d4e5f")` or check L2

### Integration with /recover

```python
# /execute automatically checks for recovery state
if check_recovery_needed():
    Skill(skill="recover")
    # Then resume /execute from interrupted phase
```

---

## Orchestrator Enforcement Rules

### Main Agent ALLOWED Actions

| Action | Allowed | Reason |
|--------|---------|--------|
| `Read` | ✅ | Information gathering |
| `Grep`, `Glob` | ✅ | Search |
| `TodoWrite` | ✅ | Progress tracking |
| `Task()` | ✅ | Subagent delegation |
| `AskUserQuestion` | ✅ | User interaction |

### Main Agent PROHIBITED Actions

| Action | Prohibited | Redirect |
|--------|------------|----------|
| `Edit` | ❌ | `Task(subagent_type="general-purpose")` |
| `Write` | ❌ | `Task(subagent_type="general-purpose")` |
| Complex `Bash` | ❌ | `Task(subagent_type="general-purpose")` |
| Direct implementation | ❌ | Delegate to Subagent |

### Enforcement Hook

**Reference:** `.claude/hooks/config/enforcement_config.yaml`

```yaml
enforcement_mode: BLOCK  # As of v2.1.6

# During /execute, these are blocked for Main Agent:
blocked_during_execute:
  - Edit
  - Write
  - NotebookEdit
  - Bash with > 200 chars
  - Bash with > 3 pipes
```

---

## Usage Examples

### Basic Usage (Auto-detect Plan)
```
/execute
```
→ Finds most recent IN_PROGRESS plan and executes

### Specific Plan
```
/execute user_authentication
```
→ Executes `.agent/plans/user_authentication.md`

### After /plan Approval
```
User: /plan 사용자 인증 기능 추가
Assistant: [Plan generated, awaiting approval]
User: 승인. /execute
Assistant: [Orchestrator mode activated, executing plan...]
```

---

## Integration with /plan

| Workflow Step | Command | Output |
|---------------|---------|--------|
| 1. Requirements | `/ask` | Clarified requirements |
| 2. Planning | `/plan` | Approved plan file |
| 3. Execution | `/execute` | Implemented changes |
| 4. Verification | `/quality-check` | Quality gates passed |

---

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| No plan found | No IN_PROGRESS plans | Ask user to run `/plan` first |
| Verification failed | Summary-only result | Resume agent or re-execute |
| Subagent timeout | Long-running task | Check L2/L3 for partial results |
| Context exhaustion | Too many parallel tasks | Reduce parallel execution |

---

## Progressive-Disclosure Integration

### L2 Report Generation

After each Phase completion:
```python
output_manager.write_structured_report(
    agent_id=agent_id,
    agent_type=subagent_type,
    task_description=phase["description"],
    result=task_result,
    status="completed"
)
# Creates: .agent/outputs/{type}/{agent_id}.md
```

### Layer Access Priority

1. **L1 (Main Context):** Headline only (~50 tokens)
2. **L2 (On-demand):** Structured report (~2000 tokens)
3. **L3 (Full recovery):** Raw output (unlimited)

---

## Evidence Requirements

This command enforces anti-hallucination:

- Each Phase MUST produce `files_viewed` evidence
- Results without evidence trigger verification failure
- Summary-only results are BLOCKED, not accepted

```python
def validate_evidence(result):
    if "files_viewed" not in result:
        return False, "Missing files_viewed evidence"
    if len(result["files_viewed"]) == 0:
        return False, "Empty files_viewed - no evidence collected"
    return True, "Evidence validated"
```

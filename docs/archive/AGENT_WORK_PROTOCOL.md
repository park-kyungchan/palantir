# AGENT WORK PROTOCOL v1.0

> **DOCUMENT TYPE**: Code-Level Execution Guide
> **TARGET**: Any LLM Agent (Model-Agnostic)
> **AMBIGUITY LEVEL**: ZERO - All instructions are explicit

---

## TABLE OF CONTENTS

1. [CRITICAL: READ FIRST](#1-critical-read-first)
2. [ENVIRONMENT SETUP](#2-environment-setup)
3. [ACTION EXECUTION PROTOCOL](#3-action-execution-protocol)
4. [AVAILABLE ACTIONS REFERENCE](#4-available-actions-reference)
5. [TASK TEMPLATES](#5-task-templates)
6. [ERROR HANDLING](#6-error-handling)
7. [VALIDATION RULES](#7-validation-rules)

---

## 1. CRITICAL: READ FIRST

### 1.1 ABSOLUTE RULES

```
RULE 1: NEVER modify files directly in scripts/ontology/storage/
RULE 2: NEVER execute SQL queries directly
RULE 3: ALL mutations MUST go through AgentExecutor
RULE 4: ALL hazardous actions create Proposals (not immediate execution)
RULE 5: ALWAYS check TaskResult.success before proceeding
```

### 1.2 FILE STRUCTURE YOU MUST KNOW

```
/home/palantir/orion-orchestrator-v2/
├── scripts/
│   ├── agent/                          # YOUR ENTRY POINT
│   │   ├── executor.py                 # AgentExecutor class
│   │   └── protocols.py                # ExecutionProtocol class
│   ├── ontology/
│   │   ├── actions.py                  # Action base classes
│   │   ├── ontology_types.py           # OntologyObject, Link, PropertyType
│   │   ├── objects/
│   │   │   ├── proposal.py             # Proposal object
│   │   │   ├── task_actions.py         # Task/Agent actions (REGISTERED)
│   │   │   └── core_definitions.py     # Basic definitions
│   │   └── storage/
│   │       ├── database.py             # Database connection
│   │       └── proposal_repository.py  # Proposal persistence
│   └── runtime/
│       └── kernel.py                   # Runtime kernel
└── data/
    └── ontology.db                     # SQLite database
```

### 1.3 WHAT YOU CAN DO

| Operation | Allowed | Method |
|-----------|---------|--------|
| Create Task | YES | `executor.execute_action("create_task", {...})` |
| Update Task | YES | `executor.execute_action("update_task", {...})` |
| Delete Task | YES (creates Proposal) | `executor.execute_action("delete_task", {...})` |
| Query Tasks | YES | (future: executor.query) |
| Direct DB Access | **NO** | FORBIDDEN |
| Direct File Edit | **NO** | FORBIDDEN |

---

## 2. ENVIRONMENT SETUP

### 2.1 INITIALIZATION SEQUENCE

```python
# FILE: Your execution script
# LOCATION: /home/palantir/orion-orchestrator-v2/

import sys
sys.path.insert(0, "/home/palantir/orion-orchestrator-v2")

import asyncio
from scripts.agent.executor import AgentExecutor, TaskResult

async def main():
    # STEP 1: Create executor
    executor = AgentExecutor()

    # STEP 2: Initialize (REQUIRED before any operation)
    init_result: TaskResult = await executor.initialize()

    # STEP 3: Check initialization success
    if not init_result.success:
        print(f"FATAL: Initialization failed: {init_result.message}")
        return

    # STEP 4: Ready to execute actions
    print("Executor ready")

if __name__ == "__main__":
    asyncio.run(main())
```

### 2.2 VERIFICATION CHECK

After initialization, verify with:

```python
actions_result = executor.list_actions()
print(f"Available actions: {actions_result.data['actions']}")
print(f"Hazardous actions: {actions_result.data['hazardous']}")
```

**Expected Output**:
```
Available actions: ['create_task', 'update_task', 'delete_task', 'assign_task', ...]
Hazardous actions: ['delete_task', 'bulk_create_tasks', 'deactivate_agent', 'deploy_service']
```

---

## 3. ACTION EXECUTION PROTOCOL

### 3.1 STANDARD EXECUTION FLOW

```
┌─────────────────────────────────────────────────────────────────┐
│                    ACTION EXECUTION FLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐              │
│  │ 1. CALL   │───►│ 2. CHECK  │───►│ 3. ROUTE  │              │
│  │ executor  │    │ governance│    │ by policy │              │
│  └───────────┘    └───────────┘    └─────┬─────┘              │
│                                          │                      │
│                    ┌─────────────────────┼─────────────────┐    │
│                    │                     │                 │    │
│                    ▼                     ▼                 ▼    │
│           ┌──────────────┐     ┌──────────────┐   ┌──────────┐ │
│           │ALLOW_IMMEDIATE│    │REQUIRE_PROPOSAL│  │  DENY    │ │
│           └───────┬──────┘     └───────┬──────┘   └────┬─────┘ │
│                   │                    │                │       │
│                   ▼                    ▼                ▼       │
│           ┌──────────────┐     ┌──────────────┐   ┌──────────┐ │
│           │Execute Action│     │Create Proposal│  │Return    │ │
│           │Return Result │     │Return prop_id │  │Error     │ │
│           └──────────────┘     └──────────────┘   └──────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 CODE TEMPLATE: Execute Action

```python
async def execute_action_safely(
    executor: AgentExecutor,
    action_type: str,
    params: dict,
    actor_id: str = "agent"
) -> TaskResult:
    """
    TEMPLATE: Safe action execution with full error handling.

    COPY THIS TEMPLATE EXACTLY for any action execution.
    """

    # STEP 1: Execute action
    result: TaskResult = await executor.execute_action(
        action_type=action_type,
        params=params,
        actor_id=actor_id
    )

    # STEP 2: Check result
    if not result.success:
        # HANDLE ERROR
        print(f"ERROR [{result.error_code}]: {result.message}")
        return result

    # STEP 3: Check if proposal was created (hazardous action)
    if result.proposal_id is not None:
        print(f"PROPOSAL CREATED: {result.proposal_id}")
        print("Action requires human approval before execution.")
        return result

    # STEP 4: Success - action executed
    print(f"SUCCESS: {result.message}")
    print(f"Created IDs: {result.data.get('created_ids', [])}")
    print(f"Modified IDs: {result.data.get('modified_ids', [])}")

    return result
```

### 3.3 TaskResult STRUCTURE

**ALWAYS expect this structure from executor methods**:

```python
@dataclass
class TaskResult:
    success: bool              # True if operation succeeded
    action_type: str           # Name of the action executed
    message: str               # Human-readable message
    data: Dict[str, Any]       # Action-specific data
    proposal_id: Optional[str] # Non-None if proposal was created
    error_code: Optional[str]  # Error code if success=False
    timestamp: datetime        # When result was created
```

**Possible Error Codes**:

| Error Code | Meaning | Action |
|------------|---------|--------|
| `NOT_INITIALIZED` | Executor not initialized | Call `executor.initialize()` |
| `ACTION_NOT_FOUND` | Action name invalid | Check `list_actions()` |
| `GOVERNANCE_DENIED` | Action not allowed | Check permissions |
| `VALIDATION_ERROR` | Parameters invalid | Fix parameters |
| `EXECUTION_FAILED` | Action failed | Check error message |
| `PROPOSAL_CREATION_FAILED` | Could not create proposal | Check database |

---

## 4. AVAILABLE ACTIONS REFERENCE

### 4.1 SAFE ACTIONS (Immediate Execution)

#### 4.1.1 create_task

**Purpose**: Create a new Task object

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `title` | string | YES | 1-255 chars |
| `description` | string | NO | max 5000 chars |
| `priority` | string | NO | "low", "medium", "high", "critical" |
| `assigned_to_id` | string | NO | Valid Agent ID |
| `tags` | list[string] | NO | - |
| `estimated_hours` | float | NO | > 0 |
| `due_date` | string | NO | ISO 8601, must be future |

**Example**:

```python
result = await executor.execute_action(
    action_type="create_task",
    params={
        "title": "Implement login feature",
        "description": "Add OAuth2 login",
        "priority": "high",
        "tags": ["auth", "frontend"],
        "estimated_hours": 8.0
    },
    actor_id="agent-001"
)

# SUCCESS: result.data["created_ids"] contains new task ID
task_id = result.data["created_ids"][0]
```

---

#### 4.1.2 update_task

**Purpose**: Update an existing Task

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `task_id` | string | YES | Existing Task ID |
| `title` | string | NO | 1-255 chars |
| `description` | string | NO | max 5000 chars |
| `priority` | string | NO | "low", "medium", "high", "critical" |
| `tags` | list[string] | NO | - |

**RULE**: At least one field besides `task_id` must be provided.

**Example**:

```python
result = await executor.execute_action(
    action_type="update_task",
    params={
        "task_id": "123e4567-e89b-12d3-a456-426614174000",
        "priority": "critical",
        "description": "Updated description"
    },
    actor_id="agent-001"
)
```

---

#### 4.1.3 assign_task

**Purpose**: Assign a Task to an Agent

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `task_id` | string | YES | Existing Task ID |
| `agent_id` | string | YES | Existing Agent ID |

**Example**:

```python
result = await executor.execute_action(
    action_type="assign_task",
    params={
        "task_id": "task-uuid-here",
        "agent_id": "agent-uuid-here"
    },
    actor_id="agent-001"
)
```

---

#### 4.1.4 unassign_task

**Purpose**: Remove Agent assignment from a Task

**Parameters**:

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | YES |

---

#### 4.1.5 complete_task

**Purpose**: Mark a Task as completed

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `task_id` | string | YES | Existing Task ID |
| `actual_hours` | float | NO | > 0 |
| `completion_notes` | string | NO | - |

---

#### 4.1.6 archive_task

**Purpose**: Archive a completed Task

**Parameters**:

| Parameter | Type | Required |
|-----------|------|----------|
| `task_id` | string | YES |

---

#### 4.1.7 create_agent

**Purpose**: Create a new Agent

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `name` | string | YES | 1-100 chars |
| `email` | string | NO | Valid email format |
| `role` | string | NO | Default: "agent" |
| `capabilities` | list[string] | NO | - |

---

### 4.2 HAZARDOUS ACTIONS (Create Proposal)

**THESE ACTIONS DO NOT EXECUTE IMMEDIATELY**
**THEY CREATE A PROPOSAL THAT REQUIRES HUMAN APPROVAL**

#### 4.2.1 delete_task

**Purpose**: Soft-delete a Task

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `task_id` | string | YES | Existing Task ID |
| `reason` | string | YES | max 500 chars |

**Example**:

```python
result = await executor.execute_action(
    action_type="delete_task",
    params={
        "task_id": "task-uuid-here",
        "reason": "Duplicate task, consolidated with task-xyz"
    },
    actor_id="agent-001"
)

# result.proposal_id is NOT None
# Action will NOT execute until proposal is approved
proposal_id = result.proposal_id
print(f"Proposal created: {proposal_id}")
print("Waiting for human approval...")
```

---

#### 4.2.2 bulk_create_tasks

**Purpose**: Create multiple Tasks atomically

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `tasks` | list[dict] | YES | 1-100 items, each must have `title` |

**Example**:

```python
result = await executor.execute_action(
    action_type="bulk_create_tasks",
    params={
        "tasks": [
            {"title": "Task 1", "priority": "high"},
            {"title": "Task 2", "priority": "medium"},
            {"title": "Task 3", "priority": "low"}
        ]
    },
    actor_id="agent-001"
)

# Creates proposal, does not execute immediately
```

---

#### 4.2.3 deactivate_agent

**Purpose**: Deactivate an Agent

**Parameters**:

| Parameter | Type | Required |
|-----------|------|----------|
| `agent_id` | string | YES |
| `reason` | string | YES |

---

#### 4.2.4 deploy_service

**Purpose**: Deploy a service to environment

**Parameters**:

| Parameter | Type | Required | Validation |
|-----------|------|----------|------------|
| `service_name` | string | YES | - |
| `version` | string | YES | Semver format (X.Y.Z) |
| `environment` | string | YES | "staging" or "production" |
| `rollback_version` | string | NO | Semver format |

---

## 5. TASK TEMPLATES

### 5.1 TEMPLATE: Create Single Task

```python
"""
TASK: Create a single task

INPUT:
- title: string (REQUIRED)
- description: string (OPTIONAL)
- priority: "low" | "medium" | "high" | "critical" (OPTIONAL, default: "medium")

OUTPUT:
- task_id: string (the created task's ID)
"""

import asyncio
import sys
sys.path.insert(0, "/home/palantir/orion-orchestrator-v2")

from scripts.agent.executor import AgentExecutor, TaskResult

async def create_single_task(
    title: str,
    description: str = "",
    priority: str = "medium"
) -> str:
    """Create a single task and return its ID."""

    # STEP 1: Initialize executor
    executor = AgentExecutor()
    init_result = await executor.initialize()
    if not init_result.success:
        raise RuntimeError(f"Init failed: {init_result.message}")

    # STEP 2: Validate inputs (explicit validation)
    if not title or not title.strip():
        raise ValueError("title cannot be empty")
    if len(title) > 255:
        raise ValueError("title cannot exceed 255 characters")
    if priority not in ["low", "medium", "high", "critical"]:
        raise ValueError(f"priority must be one of: low, medium, high, critical")

    # STEP 3: Execute action
    result: TaskResult = await executor.execute_action(
        action_type="create_task",
        params={
            "title": title.strip(),
            "description": description,
            "priority": priority
        },
        actor_id="template-agent"
    )

    # STEP 4: Handle result
    if not result.success:
        raise RuntimeError(f"Action failed: {result.message}")

    # STEP 5: Extract and return task ID
    created_ids = result.data.get("created_ids", [])
    if not created_ids:
        raise RuntimeError("Task created but no ID returned")

    return created_ids[0]

# USAGE:
# task_id = asyncio.run(create_single_task("My Task", "Description here", "high"))
```

---

### 5.2 TEMPLATE: Create Multiple Tasks (Hazardous)

```python
"""
TASK: Create multiple tasks (requires human approval)

INPUT:
- tasks: list of dicts, each with at least "title"

OUTPUT:
- proposal_id: string (the proposal awaiting approval)
"""

import asyncio
import sys
sys.path.insert(0, "/home/palantir/orion-orchestrator-v2")

from scripts.agent.executor import AgentExecutor, TaskResult
from typing import List, Dict

async def create_multiple_tasks(tasks: List[Dict[str, str]]) -> str:
    """Create multiple tasks via proposal."""

    # STEP 1: Initialize executor
    executor = AgentExecutor()
    init_result = await executor.initialize()
    if not init_result.success:
        raise RuntimeError(f"Init failed: {init_result.message}")

    # STEP 2: Validate inputs
    if not tasks:
        raise ValueError("tasks list cannot be empty")
    if len(tasks) > 100:
        raise ValueError("Cannot create more than 100 tasks at once")
    for i, task in enumerate(tasks):
        if "title" not in task or not task["title"]:
            raise ValueError(f"Task at index {i} missing required 'title'")

    # STEP 3: Execute action (creates proposal)
    result: TaskResult = await executor.execute_action(
        action_type="bulk_create_tasks",
        params={"tasks": tasks},
        actor_id="template-agent",
        priority="medium"
    )

    # STEP 4: Handle result
    if not result.success:
        raise RuntimeError(f"Action failed: {result.message}")

    # STEP 5: Return proposal ID
    if result.proposal_id is None:
        raise RuntimeError("Expected proposal but none created")

    return result.proposal_id

# USAGE:
# proposal_id = asyncio.run(create_multiple_tasks([
#     {"title": "Task 1"},
#     {"title": "Task 2", "priority": "high"}
# ]))
```

---

### 5.3 TEMPLATE: Delete Task (Hazardous)

```python
"""
TASK: Delete a task (requires human approval)

INPUT:
- task_id: string (REQUIRED)
- reason: string (REQUIRED)

OUTPUT:
- proposal_id: string (the proposal awaiting approval)
"""

import asyncio
import sys
sys.path.insert(0, "/home/palantir/orion-orchestrator-v2")

from scripts.agent.executor import AgentExecutor, TaskResult

async def delete_task(task_id: str, reason: str) -> str:
    """Delete a task via proposal."""

    # STEP 1: Initialize executor
    executor = AgentExecutor()
    init_result = await executor.initialize()
    if not init_result.success:
        raise RuntimeError(f"Init failed: {init_result.message}")

    # STEP 2: Validate inputs
    if not task_id or not task_id.strip():
        raise ValueError("task_id cannot be empty")
    if not reason or not reason.strip():
        raise ValueError("reason cannot be empty")
    if len(reason) > 500:
        raise ValueError("reason cannot exceed 500 characters")

    # STEP 3: Execute action (creates proposal)
    result: TaskResult = await executor.execute_action(
        action_type="delete_task",
        params={
            "task_id": task_id.strip(),
            "reason": reason.strip()
        },
        actor_id="template-agent",
        priority="high"  # Deletions should be high priority for quick review
    )

    # STEP 4: Handle result
    if not result.success:
        raise RuntimeError(f"Action failed: {result.message}")

    # STEP 5: Return proposal ID
    if result.proposal_id is None:
        raise RuntimeError("Expected proposal but none created")

    return result.proposal_id
```

---

### 5.4 TEMPLATE: Check Proposal Status

```python
"""
TASK: Check the status of a proposal

INPUT:
- proposal_id: string (REQUIRED)

OUTPUT:
- status: string ("pending", "approved", "rejected", "executed")
- details: dict
"""

import asyncio
import sys
sys.path.insert(0, "/home/palantir/orion-orchestrator-v2")

from scripts.agent.executor import AgentExecutor, TaskResult
from typing import Tuple, Dict, Any

async def check_proposal_status(proposal_id: str) -> Tuple[str, Dict[str, Any]]:
    """Check proposal status."""

    # STEP 1: Initialize executor
    executor = AgentExecutor()
    init_result = await executor.initialize()
    if not init_result.success:
        raise RuntimeError(f"Init failed: {init_result.message}")

    # STEP 2: Validate input
    if not proposal_id or not proposal_id.strip():
        raise ValueError("proposal_id cannot be empty")

    # STEP 3: Get proposal
    result: TaskResult = await executor.get_proposal(proposal_id.strip())

    # STEP 4: Handle result
    if not result.success:
        raise RuntimeError(f"Query failed: {result.message}")

    # STEP 5: Return status and details
    return result.data.get("status", "unknown"), result.data
```

---

## 6. ERROR HANDLING

### 6.1 ERROR HANDLING MATRIX

| Scenario | Error Code | Agent Action |
|----------|------------|--------------|
| Executor not initialized | `NOT_INITIALIZED` | Call `executor.initialize()` first |
| Unknown action name | `ACTION_NOT_FOUND` | Call `executor.list_actions()` to get valid names |
| Missing required param | `VALIDATION_ERROR` | Add the missing parameter |
| Invalid param value | `VALIDATION_ERROR` | Fix the value per validation rules |
| Action denied by governance | `GOVERNANCE_DENIED` | This action is not allowed |
| Database error | `EXECUTION_ERROR` | Retry after delay or report error |
| Proposal creation failed | `PROPOSAL_CREATION_FAILED` | Check database connectivity |

### 6.2 ERROR HANDLING TEMPLATE

```python
async def safe_execute(executor, action_type, params, actor_id="agent"):
    """
    ALWAYS use this wrapper for action execution.
    """
    try:
        result = await executor.execute_action(action_type, params, actor_id)

        if not result.success:
            # Log error details
            print(f"[ERROR] Action: {action_type}")
            print(f"[ERROR] Code: {result.error_code}")
            print(f"[ERROR] Message: {result.message}")

            # Specific error handling
            if result.error_code == "NOT_INITIALIZED":
                await executor.initialize()
                return await safe_execute(executor, action_type, params, actor_id)

            if result.error_code == "VALIDATION_ERROR":
                print(f"[ERROR] Fix these validation issues: {result.data}")
                return result

            if result.error_code == "ACTION_NOT_FOUND":
                available = executor.list_actions()
                print(f"[ERROR] Available actions: {available.data['actions']}")
                return result

        return result

    except Exception as e:
        print(f"[EXCEPTION] {type(e).__name__}: {str(e)}")
        return TaskResult(
            success=False,
            action_type=action_type,
            message=str(e),
            error_code="EXCEPTION"
        )
```

---

## 7. VALIDATION RULES

### 7.1 STRING VALIDATION

| Field | Rule | Example Valid | Example Invalid |
|-------|------|---------------|-----------------|
| title | 1-255 chars, non-empty | "Fix bug" | "" or "x"*256 |
| description | 0-5000 chars | "Long text..." | "x"*5001 |
| reason | 1-500 chars, non-empty | "Duplicate" | "" |
| email | Valid email format | "a@b.com" | "not-an-email" |

### 7.2 ENUM VALIDATION

| Field | Valid Values |
|-------|--------------|
| priority | "low", "medium", "high", "critical" |
| environment | "staging", "production" |
| task_status | "pending", "in_progress", "blocked", "completed", "cancelled" |

### 7.3 ID VALIDATION

| Field | Format | Example |
|-------|--------|---------|
| task_id | UUID v4 string | "123e4567-e89b-12d3-a456-426614174000" |
| agent_id | UUID v4 string | "123e4567-e89b-12d3-a456-426614174000" |
| proposal_id | UUID v4 string | "123e4567-e89b-12d3-a456-426614174000" |

### 7.4 DATE VALIDATION

| Field | Format | Rule |
|-------|--------|------|
| due_date | ISO 8601 | Must be in the future |

**Example**:
```python
from datetime import datetime, timezone, timedelta

# Valid: Tomorrow
due_date = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

# Invalid: Yesterday
# due_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
```

### 7.5 NUMERIC VALIDATION

| Field | Rule |
|-------|------|
| estimated_hours | > 0 |
| actual_hours | > 0 |
| bulk tasks count | 1-100 |

---

## APPENDIX A: QUICK REFERENCE

### A.1 Initialization One-Liner

```python
executor = AgentExecutor(); await executor.initialize()
```

### A.2 Check Available Actions

```python
print(executor.list_actions().data["actions"])
```

### A.3 Execute Safe Action

```python
result = await executor.execute_action("create_task", {"title": "X"}, "agent")
```

### A.4 Execute Hazardous Action

```python
result = await executor.execute_action("delete_task", {"task_id": "X", "reason": "Y"}, "agent")
print(f"Proposal: {result.proposal_id}")  # Needs human approval
```

### A.5 Check Proposal

```python
result = await executor.get_proposal("proposal-id")
print(result.data["status"])  # "pending", "approved", "rejected", "executed"
```

---

## APPENDIX B: COMMON MISTAKES

| Mistake | Correct Approach |
|---------|-----------------|
| Not calling `initialize()` | ALWAYS call `await executor.initialize()` first |
| Ignoring `result.success` | ALWAYS check `if result.success:` before proceeding |
| Expecting immediate delete | Hazardous actions create proposals, check `result.proposal_id` |
| Using wrong param names | Use EXACT param names from this document |
| Missing required params | Include ALL required params per action reference |
| Invalid priority value | Use lowercase: "low", "medium", "high", "critical" |

---

## APPENDIX C: FILE LOCATIONS CHEATSHEET

```
ENTRY POINT:     /home/palantir/orion-orchestrator-v2/scripts/agent/executor.py
PROTOCOLS:       /home/palantir/orion-orchestrator-v2/scripts/agent/protocols.py
ACTIONS:         /home/palantir/orion-orchestrator-v2/scripts/ontology/actions.py
TASK ACTIONS:    /home/palantir/orion-orchestrator-v2/scripts/ontology/objects/task_actions.py
PROPOSAL:        /home/palantir/orion-orchestrator-v2/scripts/ontology/objects/proposal.py
DATABASE:        /home/palantir/orion-orchestrator-v2/scripts/ontology/storage/database.py
REPOSITORY:      /home/palantir/orion-orchestrator-v2/scripts/ontology/storage/proposal_repository.py
```

---

**END OF PROTOCOL**

*Version 1.0 - For Any LLM Agent*

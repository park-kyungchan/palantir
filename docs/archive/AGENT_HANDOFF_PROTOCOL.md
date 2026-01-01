# CLAUDE ↔ GEMINI HANDOFF PROTOCOL v1.0

> **AGENTS**: Claude 4.5 Opus (Logic Core) + Gemini 3.0 Pro (Orchestrator)
> **ARCHITECTURE**: Palantir ODA Compliant Dual-Agent System
> **PURPOSE**: Unambiguous handoff protocol between agents

---

## 1. AGENT ROLE DEFINITIONS

### 1.1 GEMINI 3.0 PRO (Orchestrator)

```yaml
IDENTITY:
  role: Orchestrator
  model: Gemini 3.0 Pro (Native)
  ide: Antigravity IDE
  entry_point: /home/palantir/orion-orchestrator-v2/scripts/ontology/

RESPONSIBILITIES:
  - Phase 1 (Planning): Define Plans, generate Handoffs
  - Phase 4 (Consolidation): Analyze results, update Memory
  - Research: Use tavily for external knowledge
  - Schema Design: Define Ontology structure

TOOLS:
  - sequential-thinking: MANDATORY before significant actions
  - tavily: Web search for knowledge cutoff mitigation
  - context7: Library documentation lookup
  - read_file, write_to_file: File operations

FORBIDDEN:
  - Direct database mutations
  - Execution of hazardous actions without proposal
```

### 1.2 CLAUDE 4.5 OPUS (Logic Core)

```yaml
IDENTITY:
  role: Logic Core / Principal Architect
  model: Claude 4.5 Opus
  tool: Claude Code CLI
  entry_point: /home/palantir/orion-orchestrator-v2/scripts/agent/

RESPONSIBILITIES:
  - Phase 2 (Execution): Implement Plans, write code
  - Deep Reasoning: Complex logic, long-horizon tasks
  - Code Generation: Write production-quality code
  - Testing: Create and run tests

TOOLS:
  - Extended Thinking: Deep reasoning blocks
  - Read, Write, Edit: File operations
  - Bash: Command execution
  - Task: Subagent delegation

FORBIDDEN:
  - Planning without Gemini's input
  - Ignoring Handoff instructions
```

---

## 2. HANDOFF FILE FORMAT

### 2.1 GEMINI → CLAUDE HANDOFF

**Location**: `.agent/handoffs/pending/job_{id}_claude.md`

```markdown
# HANDOFF: [JOB_ID]

## METADATA
- From: Gemini 3.0 Pro (Orchestrator)
- To: Claude 4.5 Opus (Logic Core)
- Created: [ISO_8601_TIMESTAMP]
- Priority: [LOW | MEDIUM | HIGH | CRITICAL]
- Phase: EXECUTION

## OBJECTIVE
[Clear, unambiguous objective statement]

## CONTEXT
[All necessary context for execution]

## TASKS
### Task 1: [Task Name]
- File: [Exact file path]
- Action: [CREATE | MODIFY | DELETE]
- Details: [Specific instructions]
- Acceptance Criteria: [How to verify completion]

### Task 2: [Task Name]
...

## CONSTRAINTS
- [Constraint 1]
- [Constraint 2]

## EXPECTED OUTPUT
- [File 1]: [Description]
- [File 2]: [Description]

## ON COMPLETION
1. Create result file: `.agent/handoffs/completed/job_{id}_result.md`
2. Include: Status, Changes Made, Tests Run, Issues Found
```

### 2.2 CLAUDE → GEMINI RESULT

**Location**: `.agent/handoffs/completed/job_{id}_result.md`

```markdown
# RESULT: [JOB_ID]

## METADATA
- From: Claude 4.5 Opus (Logic Core)
- To: Gemini 3.0 Pro (Orchestrator)
- Completed: [ISO_8601_TIMESTAMP]
- Status: [SUCCESS | PARTIAL | FAILED]

## SUMMARY
[Brief summary of what was done]

## CHANGES MADE
### Files Created
- [File Path]: [Description]

### Files Modified
- [File Path]: [Description of changes]

### Files Deleted
- [File Path]: [Reason]

## TESTS RUN
- [Test Name]: [PASS | FAIL]

## ISSUES ENCOUNTERED
- [Issue 1]: [Resolution]

## PROPOSALS CREATED
- [Proposal ID]: [Action Type] - [Status]

## NEXT STEPS RECOMMENDED
- [Recommendation 1]
- [Recommendation 2]
```

---

## 3. EXECUTION PROTOCOLS BY AGENT

### 3.1 GEMINI EXECUTION PROTOCOL

```python
"""
GEMINI 3.0 PRO - Planning Phase Execution

This is the EXACT protocol Gemini MUST follow.
"""

# STEP 1: Output System Context Snapshot (MANDATORY)
"""
```xml
<system_context_snapshot>
    <meta_verification>
        <timestamp>{ISO_8601}</timestamp>
        <identity>
            <role>Antigravity (Advanced Agentic Coding)</role>
            <model>Gemini 3.0 Pro (Native)</model>
        </identity>
    </meta_verification>
    <reasoning_trace>
        <current_focus>{CURRENT_GOAL}</current_focus>
        <cognitive_state>FULL_CONTEXT_INJECTED</cognitive_state>
    </reasoning_trace>
</system_context_snapshot>
```
"""

# STEP 2: Use sequential-thinking before any significant action
"""
Call: sequential-thinking
Input: "I need to plan [OBJECTIVE]. Let me think through the steps..."
"""

# STEP 3: Research if needed
"""
Call: tavily
Query: "[Specific technical question]"
"""

# STEP 4: Read current state
"""
Call: read_file
Path: /home/palantir/orion-orchestrator-v2/scripts/ontology/plan.py
"""

# STEP 5: Create Plan (if designing new work)
"""
Call: write_to_file
Path: .agent/plans/plan_{timestamp}.json
Content:
{
    "plan_id": "plan-{uuid}",
    "objective": "[What we're trying to achieve]",
    "jobs": [
        {
            "job_id": "job-001",
            "title": "[Job Title]",
            "action_type": "[create_task | update_task | ...]",
            "params": {...},
            "assigned_to": "claude"
        }
    ]
}
"""

# STEP 6: Generate Handoff
"""
Call: write_to_file
Path: .agent/handoffs/pending/job_{id}_claude.md
Content: [Handoff content per format above]
"""

# STEP 7: Notify User
"""
Output: "Handoff created. Please switch to Claude and have it read:
.agent/handoffs/pending/job_{id}_claude.md"
"""
```

### 3.2 CLAUDE EXECUTION PROTOCOL

```python
"""
CLAUDE 4.5 OPUS - Execution Phase Protocol

This is the EXACT protocol Claude MUST follow.
"""

# STEP 1: Output CLI Context Snapshot (MANDATORY)
"""
```xml
<cli_context_snapshot>
    <meta_verification>
        <timestamp>{ISO_8601}</timestamp>
        <cwd>/home/palantir/orion-orchestrator-v2</cwd>
        <git_ref>{BRANCH} | {STATUS}</git_ref>
        <identity>Claude 4.5 Opus (Logic Core)</identity>
    </meta_verification>
    <runtime_telemetry>
        <verification_mode>STRICT_ODA</verification_mode>
        <active_task>{TASK_ID}</active_task>
    </runtime_telemetry>
</cli_context_snapshot>
```
"""

# STEP 2: Read Handoff File
"""
Tool: Read
Path: .agent/handoffs/pending/job_{id}_claude.md
"""

# STEP 3: Parse Tasks and Create TodoList
"""
Tool: TodoWrite
Content: [Parse tasks from handoff into todo items]
"""

# STEP 4: Execute Each Task
"""
FOR each task in handoff:
    a. Mark task as in_progress (TodoWrite)
    b. Read relevant files (Read)
    c. Think through implementation (Extended Thinking)
    d. Execute changes (Write/Edit)
    e. Verify changes (Bash: run tests if applicable)
    f. Mark task as completed (TodoWrite)
"""

# STEP 5: Create Result File
"""
Tool: Write
Path: .agent/handoffs/completed/job_{id}_result.md
Content: [Result per format above]
"""

# STEP 6: Notify User
"""
Output: "Execution complete. Result written to:
.agent/handoffs/completed/job_{id}_result.md

Please switch to Gemini for consolidation."
"""
```

---

## 4. AGENT-SPECIFIC TASK TEMPLATES

### 4.1 GEMINI: Create New Ontology Object Type

```markdown
# TASK: Define New Object Type

## GEMINI INSTRUCTIONS

1. Use sequential-thinking to design the object type
2. Research similar patterns using tavily if needed
3. Create the definition in core_definitions.py
4. Generate handoff for Claude to implement actions

## EXAMPLE OUTPUT

```python
# File: scripts/ontology/objects/core_definitions.py
# Add after existing classes:

class Project(OntologyObject):
    """
    ObjectType: Project
    Represents a container for related Tasks.
    """
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(default="")
    status: str = Field(default="active")
    owner_id: Optional[str] = Field(None, description="FK to Agent")

    # Links
    tasks: ClassVar[Link[Task]] = Link(
        target=Task,
        link_type_id="project_contains_task",
        cardinality=Cardinality.ONE_TO_MANY,
        description="Tasks belonging to this project"
    )
```

## HANDOFF TO CLAUDE
"Create actions for Project: CreateProjectAction, UpdateProjectAction, DeleteProjectAction (hazardous)"
```

### 4.2 CLAUDE: Implement New Action

```python
"""
TASK: Implement New Action

CLAUDE INSTRUCTIONS:

1. Read the handoff file
2. Locate the correct file (task_actions.py or create new)
3. Implement the action following the template
4. Register the action
5. Write tests
"""

# TEMPLATE: New Action Implementation

@register_action
class CreateProjectAction(ActionType[Project]):
    """
    Create a new Project object.

    Required params:
    - name: str (1-255 chars)

    Optional params:
    - description: str
    - owner_id: str (Agent ID)
    """
    api_name: ClassVar[str] = "create_project"
    object_type: ClassVar[Type[Project]] = Project
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[list] = [
        RequiredField("name"),
        MaxLength("name", 255),
        MaxLength("description", 5000),
    ]

    side_effects: ClassVar[list] = [
        LogSideEffect(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Project, List[EditOperation]]:
        project = Project(
            name=params["name"],
            description=params.get("description", ""),
            owner_id=params.get("owner_id"),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Project",
            object_id=project.id,
            changes=params,
        )

        return project, [edit]
```

---

## 5. CRITICAL COLLABORATION RULES

### 5.1 GEMINI RULES

```
RULE G1: ALWAYS output system_context_snapshot at start of response
RULE G2: ALWAYS use sequential-thinking before significant decisions
RULE G3: NEVER execute code directly - delegate to Claude
RULE G4: ALWAYS create handoff file before requesting Claude execution
RULE G5: Use tavily for any uncertainty about external libraries/APIs
```

### 5.2 CLAUDE RULES

```
RULE C1: ALWAYS output cli_context_snapshot at start of response
RULE C2: ALWAYS read handoff file before starting execution
RULE C3: ALWAYS use TodoWrite to track task progress
RULE C4: NEVER modify ontology schema without Gemini's handoff
RULE C5: ALWAYS create result file after execution
```

### 5.3 SHARED RULES

```
RULE S1: ALL file paths must be absolute or relative to /home/palantir/orion-orchestrator-v2
RULE S2: ALL timestamps in ISO 8601 format
RULE S3: ALL IDs in UUID v4 format
RULE S4: NO direct database mutations - use AgentExecutor
RULE S5: NO file creation outside project directory
```

---

## 6. HANDOFF DIRECTORY STRUCTURE

```
/home/palantir/orion-orchestrator-v2/.agent/
├── handoffs/
│   ├── pending/                    # Handoffs waiting for execution
│   │   ├── job_001_claude.md       # Gemini → Claude
│   │   └── job_002_gpt.md          # (Future: for other agents)
│   └── completed/                  # Completed handoffs
│       ├── job_001_result.md       # Claude → Gemini
│       └── job_002_result.md
├── plans/                          # Plan definitions
│   └── plan_2025-12-27.json
└── logs/                           # Execution logs
    └── execution_2025-12-27.log
```

---

## 7. COMMON WORKFLOWS

### 7.1 WORKFLOW: Add New Feature

```
┌─────────────────────────────────────────────────────────────────┐
│                    ADD NEW FEATURE WORKFLOW                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  USER                                                           │
│    │                                                            │
│    ▼                                                            │
│  ┌─────────────┐                                                │
│  │ "Add X      │                                                │
│  │  feature"   │                                                │
│  └──────┬──────┘                                                │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ GEMINI (Orchestrator)                                       ││
│  │ 1. sequential-thinking: Design approach                     ││
│  │ 2. tavily: Research if needed                               ││
│  │ 3. Create Plan JSON                                         ││
│  │ 4. Generate Handoff for Claude                              ││
│  │ 5. Output: "Switch to Claude"                               ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ CLAUDE (Logic Core)                                         ││
│  │ 1. Read Handoff                                             ││
│  │ 2. TodoWrite: Create task list                              ││
│  │ 3. FOR each task:                                           ││
│  │    - Read relevant files                                    ││
│  │    - Implement changes                                      ││
│  │    - Run tests if applicable                                ││
│  │ 4. Create Result file                                       ││
│  │ 5. Output: "Switch to Gemini"                               ││
│  └─────────────────────────────────────────────────────────────┘│
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ GEMINI (Consolidation)                                      ││
│  │ 1. Read Result file                                         ││
│  │ 2. Update Plan status                                       ││
│  │ 3. Update Memory/Insights                                   ││
│  │ 4. Report to User                                           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 WORKFLOW: Fix Bug

```
USER: "Fix bug in X"
           │
           ▼
    ┌──────────────┐
    │   GEMINI     │ 1. Analyze bug description
    │              │ 2. Locate relevant code
    │              │ 3. Create Handoff with:
    │              │    - Bug description
    │              │    - Suspected files
    │              │    - Acceptance criteria
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   CLAUDE     │ 1. Read Handoff
    │              │ 2. Investigate code
    │              │ 3. Create reproduction test
    │              │ 4. Fix bug
    │              │ 5. Run tests
    │              │ 6. Create Result
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │   GEMINI     │ 1. Review Result
    │              │ 2. Update insights
    │              │ 3. Report to User
    └──────────────┘
```

---

## 8. QUICK REFERENCE

### 8.1 Gemini Quick Actions

| Action | Command/Tool |
|--------|--------------|
| Deep thinking | `sequential-thinking` |
| Web search | `tavily` query |
| Library docs | `context7` lookup |
| Read file | `read_file` |
| Create handoff | `write_to_file` to `.agent/handoffs/pending/` |

### 8.2 Claude Quick Actions

| Action | Command/Tool |
|--------|--------------|
| Read handoff | `Read` tool |
| Track tasks | `TodoWrite` tool |
| Edit code | `Edit` tool |
| Create file | `Write` tool |
| Run command | `Bash` tool |
| Create result | `Write` to `.agent/handoffs/completed/` |

### 8.3 Handoff File Naming

```
Gemini → Claude:  job_{id}_claude.md
Claude → Gemini:  job_{id}_result.md
```

---

## APPENDIX: SAMPLE HANDOFF

### Gemini → Claude

```markdown
# HANDOFF: job-20251227-001

## METADATA
- From: Gemini 3.0 Pro (Orchestrator)
- To: Claude 4.5 Opus (Logic Core)
- Created: 2025-12-27T10:00:00Z
- Priority: HIGH
- Phase: EXECUTION

## OBJECTIVE
Implement a new `CompleteMultipleTasksAction` that allows completing multiple tasks at once.

## CONTEXT
- User requested bulk task completion feature
- This is a hazardous action (modifies multiple objects)
- Should follow existing BulkCreateTasksAction pattern

## TASKS

### Task 1: Create Action Class
- File: /home/palantir/orion-orchestrator-v2/scripts/ontology/objects/task_actions.py
- Action: MODIFY (add new class)
- Details:
  - Class name: `CompleteMultipleTasksAction`
  - api_name: "complete_multiple_tasks"
  - requires_proposal: True
  - Required params: task_ids (list of strings)
  - Optional params: completion_notes (string)
- Acceptance Criteria: Class compiles without errors

### Task 2: Register Action
- File: Same as Task 1
- Action: MODIFY
- Details: Add @register_action decorator
- Acceptance Criteria: Action appears in action_registry.list_actions()

### Task 3: Add Tests
- File: /home/palantir/orion-orchestrator-v2/tests/ontology/test_task_actions.py
- Action: CREATE or MODIFY
- Details: Add test for CompleteMultipleTasksAction validation
- Acceptance Criteria: Test passes

## CONSTRAINTS
- Maximum 50 tasks per bulk completion
- All task_ids must be valid UUIDs
- Action MUST require proposal (hazardous)

## EXPECTED OUTPUT
- Modified task_actions.py with new action
- Test file with at least one test

## ON COMPLETION
1. Create result file: .agent/handoffs/completed/job-20251227-001_result.md
2. Include: Files changed, tests run, any issues
```

### Claude → Gemini (Result)

```markdown
# RESULT: job-20251227-001

## METADATA
- From: Claude 4.5 Opus (Logic Core)
- To: Gemini 3.0 Pro (Orchestrator)
- Completed: 2025-12-27T10:45:00Z
- Status: SUCCESS

## SUMMARY
Implemented CompleteMultipleTasksAction with validation for max 50 tasks.

## CHANGES MADE

### Files Modified
- `/home/palantir/orion-orchestrator-v2/scripts/ontology/objects/task_actions.py`:
  Added CompleteMultipleTasksAction class (lines 820-890)

### Files Created
- `/home/palantir/orion-orchestrator-v2/tests/ontology/test_task_actions.py`:
  New test file with 3 tests

## TESTS RUN
- test_complete_multiple_tasks_validation: PASS
- test_complete_multiple_tasks_max_limit: PASS
- test_complete_multiple_tasks_requires_proposal: PASS

## ISSUES ENCOUNTERED
- None

## PROPOSALS CREATED
- N/A (implementation only, no runtime execution)

## NEXT STEPS RECOMMENDED
- Run full test suite: pytest tests/
- Update API documentation if exists
```

---

**END OF PROTOCOL**

*For Claude ↔ Gemini Collaboration*

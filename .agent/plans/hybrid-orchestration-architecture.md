# Hybrid Orchestration Architecture

> **Version:** 1.0
> **Date:** 2026-01-24
> **Purpose:** Native Task System + File-Based Worker Prompts Integration

---

## 1. Architecture Overview

### 1.1 Design Principle

**Hybrid Two-Layer System:**

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: NATIVE TASK SYSTEM (State + Dependencies)         │
│                                                             │
│  Tool: TaskCreate, TaskUpdate, TaskList, TaskGet           │
│  Data: ~/.claude/tasks/*.json (managed by Claude Code)     │
│  Purpose:                                                   │
│    - Status tracking (pending/in_progress/completed)       │
│    - Dependency management (blockedBy/blocks)              │
│    - Owner assignment (terminal-X)                         │
│    - Cross-session persistence via TASK_LIST_ID            │
└─────────────────────────────────────────────────────────────┘
                           │
                           │ Synchronized via skills
                           ▼
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: FILE-BASED PROMPTS (Instructions + Context)       │
│                                                             │
│  Location: .agent/prompts/                                 │
│  Files: _context.yaml, _progress.yaml, worker-X-task.yaml  │
│  Purpose:                                                   │
│    - Detailed work instructions                            │
│    - Global context sharing                                │
│    - Human-readable audit trail                            │
│    - Rich metadata (target files, completion criteria)     │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Why Hybrid?

| Feature | Native Task | File-Based | Hybrid Benefit |
|---------|-------------|------------|----------------|
| **Cross-session persistence** | ✅ Built-in | ❌ Ephemeral | Task state survives restarts |
| **Dependency tracking** | ✅ Built-in | ⚠️ Manual | Auto-blocking via `blockedBy` |
| **Rich instructions** | ⚠️ Limited | ✅ YAML format | Workers get detailed guidance |
| **Multi-terminal sync** | ✅ Shared list | ❌ File races | Best of both worlds |
| **Audit trail** | ⚠️ System-managed | ✅ Human-readable | Both automated + readable logs |

---

## 2. Data Model

### 2.1 Native Task Fields

```json
{
  "id": "1",
  "subject": "Implement /orchestrate skill",
  "description": "Create orchestration skill that...",
  "activeForm": "Implementing /orchestrate skill",
  "status": "pending",  // pending | in_progress | completed
  "owner": "terminal-b",
  "blockedBy": ["0"],
  "blocks": ["2", "3"],
  "metadata": {
    "promptFile": ".agent/prompts/pending/worker-b-task.yaml",
    "phaseId": "phase1",
    "priority": "P0"
  }
}
```

**Key Fields:**
- `subject`: Imperative form (e.g., "Implement feature")
- `activeForm`: Present continuous (e.g., "Implementing feature")
- `owner`: Terminal ID (e.g., "terminal-b", "terminal-c")
- `metadata.promptFile`: Link to YAML prompt file

### 2.2 File-Based Prompt Structure

```yaml
# .agent/prompts/worker-b-task.yaml
taskId: "1"  # Maps to Native Task ID
assignedTo: "terminal-b"
nativeTaskId: "1"  # Cross-reference

contextFile: ".agent/prompts/_context.yaml"
progressFile: ".agent/prompts/_progress.yaml"

scope:
  phaseId: "phase1"
  phaseName: "Session Registry Implementation"
  description: "Implement file-based session ID registry..."

targetFiles:
  - path: ".claude/hooks/session-start.sh"
    sections: ["Line 301+: Add current_session.json"]
    readOnly: false

referenceFiles:
  - path: ".claude/hooks/session-end.sh"
    reason: "See session termination pattern"

dependencies: []
blockedBy: []

completionCriteria:
  - "current_session.json created on session start"
  - "Directories: .agent/prompts/{pending,active,completed}"

globalContextChecklist:
  - question: "Does this add < 5ms overhead?"
    consideration: "Use cat heredoc, not jq"

outputFormat: "L1/L2/L3"
l2OutputPath: ".agent/outputs/Worker/phase1-session-registry.md"

onComplete:
  - "Update _progress.yaml: terminal-b.status = completed"
  - "Notify Orchestrator via TaskUpdate(status='completed')"
```

### 2.3 Context Files

**_context.yaml** (Global project context - READ ONLY for workers)

```yaml
version: "1.0"
project: "session-aware-worker-prompt-system"
orchestrator: "Terminal-A"

objectives:
  primary:
    - "Enable session tracking via file-based registry"
    - "Machine-readable worker prompts in YAML"
    - "Performance overhead < 5ms"

phases:
  phase1:
    id: "phase1"
    name: "Session Registry"
    owner: "Terminal-B"
    nativeTaskId: "1"
    status: "pending"
    dependencies: []

  phase2:
    id: "phase2"
    name: "Prompt Generation"
    owner: "Terminal-C"
    nativeTaskId: "2"
    status: "pending"
    dependencies: ["phase1"]

dependencyGraph: |
  phase1 (Task #1) → phase2 (Task #2) → phase3 (Task #3)

sharedRules:
  - "ALWAYS Read target file before modifying"
  - "Update _progress.yaml after completion"
  - "Report in L1/L2/L3 format"
```

**_progress.yaml** (Real-time status - UPDATED by workers)

```yaml
lastUpdated: "2026-01-24T08:30:00Z"

terminals:
  terminal-b:
    nativeTaskId: "1"
    status: "in_progress"
    currentPhase: "phase1"
    startedAt: "2026-01-24T08:25:00Z"
    lastActivity: "2026-01-24T08:30:00Z"

  terminal-c:
    nativeTaskId: "2"
    status: "idle"
    blockedBy: ["1"]  # Waiting for Task #1

phases:
  phase1:
    nativeTaskId: "1"
    status: "in_progress"
    owner: "terminal-b"
    startedAt: "2026-01-24T08:25:00Z"

  phase2:
    nativeTaskId: "2"
    status: "pending"
    owner: "terminal-c"
    blockedBy: ["phase1"]

completedTasks: []
blockers: []
```

---

## 3. Skill Responsibilities

### 3.1 /orchestrate (Orchestrator)

**Purpose:** Task decomposition + Native Task creation + Prompt file generation

**Input:**
```bash
/orchestrate "Implement session-aware worker prompt system"
```

**Operations:**
1. **Parse Requirements:** Break down complex task into phases
2. **Create Native Tasks:**
   ```javascript
   TaskCreate(subject="Phase 1: Session Registry", ...)  // Returns id="1"
   TaskCreate(subject="Phase 2: Prompt Generation", ...) // Returns id="2"
   TaskCreate(subject="Phase 3: Lifecycle", ...)         // Returns id="3"
   ```
3. **Set Dependencies:**
   ```javascript
   TaskUpdate(taskId="2", addBlockedBy=["1"])
   TaskUpdate(taskId="3", addBlockedBy=["2"])
   ```
4. **Generate Files:**
   - `.agent/prompts/_context.yaml` (global context)
   - `.agent/prompts/_progress.yaml` (initial state)
   - `.agent/prompts/pending/worker-b-task.yaml` (for Task #1)
   - `.agent/prompts/pending/worker-c-task.yaml` (for Task #2)
   - `.agent/prompts/pending/worker-d-task.yaml` (for Task #3)
5. **Link Tasks to Files:** Store `metadata.promptFile` in each Native Task

**Output:**
- Native Tasks created (visible via `TaskList`)
- Prompt files ready for workers
- Dependency graph logged

**Example:**
```
✅ Created 3 tasks with dependencies
✅ Generated 3 worker prompt files
✅ _context.yaml and _progress.yaml initialized

Next: Use /assign to assign tasks to terminals
```

---

### 3.2 /assign (Orchestrator)

**Purpose:** Assign Native Tasks to workers via `owner` field

**Input:**
```bash
/assign 1 terminal-b    # Assign Task #1 to Terminal B
/assign auto            # Auto-assign based on dependencies
```

**Operations:**
1. **Find Unassigned Tasks:** `TaskList()` → filter `owner == null`
2. **Check Dependencies:** Verify `blockedBy` is resolved
3. **Assign Owner:**
   ```javascript
   TaskUpdate(taskId="1", owner="terminal-b")
   ```
4. **Update _progress.yaml:**
   ```yaml
   terminals:
     terminal-b:
       nativeTaskId: "1"
       status: "idle"
   ```
5. **Notify Worker:** (Optional) Write notification file

**Modes:**
- **Manual:** `/assign <taskId> <terminal-id>`
- **Auto:** `/assign auto` (assigns first available task to first idle terminal)

**Output:**
```
✅ Task #1 assigned to terminal-b
✅ Task #2 assigned to terminal-c (blocked by #1)
✅ Task #3 assigned to terminal-d (blocked by #2)

Workers can now run: /worker start
```

---

### 3.3 /worker (Worker)

**Purpose:** Individual worker operations

**Subcommands:**

#### `/worker start [terminal-id]`
Pull-based task claiming.

**Operations:**
1. **Find My Tasks:** `TaskList()` → filter `owner == "terminal-b"`
2. **Check Blockers:** Verify `blockedBy` is empty
3. **Read Prompt File:**
   ```javascript
   task = TaskGet(taskId="1")
   promptFile = task.metadata.promptFile
   Read(promptFile)  // Get detailed instructions
   ```
4. **Update Status:**
   ```javascript
   TaskUpdate(taskId="1", status="in_progress")
   ```
5. **Update _progress.yaml:**
   ```yaml
   terminals:
     terminal-b:
       status: "in_progress"
       startedAt: "<now>"
   ```

**Output:**
```
✅ Claimed Task #1: Implement /orchestrate skill
📄 Instructions: .agent/prompts/pending/worker-b-task.yaml

Summary:
- Target files: .claude/skills/orchestrate/SKILL.md
- Dependencies: None (can start immediately)
- Output format: L1/L2/L3

Starting work...
```

#### `/worker status`
Show current task status.

**Operations:**
1. `TaskList()` → filter `owner == "terminal-b"`
2. Display: subject, status, blockedBy, progress

**Output:**
```
Terminal: terminal-b
Task #1: Implement /orchestrate skill
Status: in_progress
Started: 2026-01-24 08:25:00
Blocked by: None
Progress file: .agent/prompts/_progress.yaml
```

#### `/worker done`
Mark task as completed.

**Operations:**
1. `TaskGet()` → verify `status == "in_progress"`
2. `TaskUpdate(taskId="1", status="completed")`
3. Update `_progress.yaml`:
   ```yaml
   terminals:
     terminal-b:
       status: "idle"
       completedAt: "<now>"
   phases:
     phase1:
       status: "completed"
   completedTasks:
     - taskId: "1"
       completedAt: "<now>"
   ```
4. Move prompt file: `pending/ → completed/`
5. Generate L1 summary

**Output:**
```
✅ Task #1 marked as completed
✅ _progress.yaml updated
✅ Prompt file archived

L1 Summary:
taskId: 1
status: success
summary: "Orchestrate skill implemented with TaskCreate integration"
l2Path: .agent/outputs/Worker/orchestrate-implementation.md
```

---

### 3.4 /workers (Orchestrator)

**Purpose:** Monitor all workers + task distribution

**Operations:**
1. `TaskList()` → Get all tasks
2. Read `_progress.yaml` for real-time status
3. Detect:
   - **Orphan tasks:** `status == "pending"` + `owner == null`
   - **Conflicts:** Multiple tasks with same owner + status "in_progress"
   - **Blocked chains:** Tasks waiting on blocked tasks
4. Generate dashboard

**Output:**
```
=== Worker Dashboard ===

Terminals:
  terminal-b: [IN_PROGRESS] Task #1 (started 5m ago)
  terminal-c: [IDLE] Blocked by Task #1
  terminal-d: [IDLE] Blocked by Task #2

Tasks:
  #1: [IN_PROGRESS] Implement /orchestrate (owner: terminal-b)
  #2: [PENDING] Implement /assign (owner: terminal-c, blocked by #1)
  #3: [PENDING] Implement /worker (owner: terminal-d, blocked by #2)

Alerts:
  ⚠️  Task #4 is orphaned (no owner assigned)

Recommendations:
  - Wait for terminal-b to complete Task #1
  - Assign Task #4 via /assign
```

---

### 3.5 /collect (Orchestrator)

**Purpose:** Aggregate results + verify completion

**Operations:**
1. **Verify All Complete:**
   ```javascript
   TaskList() → filter status != "completed"
   if (incomplete.length > 0) {
     error("Tasks still pending: " + incomplete)
   }
   ```
2. **Read L1 Outputs:**
   ```bash
   for task in completedTasks:
     l2Path = task.metadata.l2OutputPath
     Read(l2Path) → Extract L1 summary
   ```
3. **Aggregate:**
   - Collect `files_viewed` from all tasks
   - Merge `summary` sections
   - Check for blockers/failures
4. **Generate Synthesis:**
   - Overall status (success/partial/failed)
   - Combined file list
   - Next actions

**Output:**
```
=== Collection Report ===

Completed Tasks: 3/3
  ✅ Task #1: Phase 1 - Session Registry
  ✅ Task #2: Phase 2 - Prompt Generation
  ✅ Task #3: Phase 3 - Lifecycle Management

Files Modified: 5
  - .claude/hooks/session-start.sh
  - .claude/hooks/task-pipeline/pd-task-interceptor.sh
  - .claude/hooks/task-pipeline/pd-task-processor.sh
  - .agent/prompts/_context.yaml
  - .agent/prompts/_progress.yaml

Overall Status: SUCCESS

Next: Run /commit-push-pr to create PR
```

---

## 4. Synchronization Protocol

### 4.1 Orchestrator → Worker Sync

```
Orchestrator (Terminal A):
  1. TaskCreate() → Native Task #1 created
  2. Write worker-b-task.yaml with metadata.nativeTaskId = "1"
  3. TaskUpdate(taskId="1", metadata={promptFile: "..."})
  4. TaskUpdate(taskId="1", owner="terminal-b")

Worker (Terminal B):
  1. /worker start
  2. TaskList() → Find owner="terminal-b"
  3. TaskGet("1") → Read metadata.promptFile
  4. Read .agent/prompts/pending/worker-b-task.yaml
  5. Execute work
  6. TaskUpdate(taskId="1", status="completed")
  7. Update _progress.yaml
```

### 4.2 Worker → Orchestrator Sync

```
Worker (Terminal B):
  1. /worker done
  2. TaskUpdate(taskId="1", status="completed")
  3. Update _progress.yaml: phase1.status = "completed"
  4. Move prompt file: pending/ → completed/

Orchestrator (Terminal A):
  1. /workers (periodically)
  2. TaskList() → Detect Task #1 is completed
  3. Read _progress.yaml → See terminal-b is idle
  4. Check Task #2: blockedBy=["1"] → Now unblocked!
  5. Notify terminal-c: "Task #2 ready to start"
```

### 4.3 Error Handling

| Scenario | Detection | Recovery |
|----------|-----------|----------|
| **Task/File Mismatch** | Task exists, prompt file missing | Regenerate file via /orchestrate |
| **Orphan Task** | `owner == null` + `status == "pending"` | /assign to available terminal |
| **Stale In-Progress** | `status == "in_progress"` > 1 hour | Manual `/worker done` or abort |
| **Circular Dependency** | A → B → A in `blockedBy` | Orchestrator validation error |
| **File Conflict** | Two terminals update _progress.yaml | Last-write wins (warn user) |

---

## 5. File Lifecycle

### 5.1 Prompt Files

```
/orchestrate creates files:
  .agent/prompts/pending/worker-b-task.yaml  (linked to Task #1)

/worker start reads file:
  Terminal B: Read worker-b-task.yaml

/worker done archives file:
  mv pending/worker-b-task.yaml → completed/

Audit:
  .agent/logs/prompt_lifecycle.log
  "2026-01-24T08:30:00Z | Completed: worker-b-task.yaml | Task #1"
```

### 5.2 Context Files

**_context.yaml:**
- Created by `/orchestrate`
- READ ONLY for workers
- Updated only by Orchestrator

**_progress.yaml:**
- Created by `/orchestrate`
- UPDATED by workers via `/worker done`
- READ by Orchestrator via `/workers`

---

## 6. Implementation Checklist

### Phase 1: Skills
- [ ] `/orchestrate` skill (TaskCreate + file generation)
- [ ] `/assign` skill (TaskUpdate owner)
- [ ] `/worker` skill (start/status/done)
- [ ] `/workers` skill (dashboard)
- [ ] `/collect` skill (aggregation)

### Phase 2: Hooks
- [ ] session-start.sh: Initialize prompts directories
- [ ] pd-task-interceptor.sh: Link Task to prompt file
- [ ] pd-task-processor.sh: Archive completed prompts
- [ ] task-sync.sh: Cross-terminal notification

### Phase 3: Testing
- [ ] Single-terminal workflow
- [ ] Multi-terminal parallel execution
- [ ] Dependency blocking
- [ ] Error recovery
- [ ] Performance < 5ms overhead

---

## 7. Example Workflow

```bash
# Terminal A (Orchestrator)
/orchestrate "Implement multi-terminal worker system"
# → Creates Tasks #1, #2, #3
# → Generates worker-{b,c,d}-task.yaml
# → Sets up dependencies

/assign auto
# → Task #1 → terminal-b
# → Task #2 → terminal-c (blocked by #1)
# → Task #3 → terminal-d (blocked by #2)

# Terminal B (Worker)
/worker start
# → Reads worker-b-task.yaml
# → Claims Task #1
# → Executes work
/worker done
# → Marks Task #1 complete
# → Unblocks Task #2

# Terminal C (Worker)
/worker start  # Now Task #2 is unblocked
# → Claims Task #2
# → Executes work
/worker done
# → Unblocks Task #3

# Terminal D (Worker)
/worker start  # Now Task #3 is unblocked
# → Claims Task #3
# → Executes work
/worker done

# Terminal A (Orchestrator)
/workers
# → All tasks completed

/collect
# → Aggregates results
# → Generates synthesis

/commit-push-pr
# → Creates PR with all changes
```

---

## 8. Migration from Legacy TodoWrite

**Before (TodoWrite):**
```javascript
TodoWrite(tasks=[
  {subject: "Task A", ...},
  {subject: "Task B", ...}
])
```

**After (Native Task + Hybrid):**
```javascript
// Orchestrator
TaskCreate(subject="Task A", ...)  // id="1"
TaskCreate(subject="Task B", ...)  // id="2"
TaskUpdate(taskId="2", addBlockedBy=["1"])

// Generate prompt files
Write(.agent/prompts/worker-b-task.yaml)
```

**Benefits:**
- ✅ Cross-session persistence
- ✅ Dependency auto-blocking
- ✅ Multi-terminal visibility
- ✅ Rich YAML instructions
- ✅ Audit trail

---

## Appendix: Native Task API Quick Reference

```javascript
// Create task
TaskCreate({
  subject: "Implement feature X",
  description: "Detailed requirements...",
  activeForm: "Implementing feature X"
})
// Returns: Task #1 created

// Update status
TaskUpdate({
  taskId: "1",
  status: "in_progress"  // pending | in_progress | completed
})

// Assign owner
TaskUpdate({
  taskId: "1",
  owner: "terminal-b"
})

// Set dependencies
TaskUpdate({
  taskId: "2",
  addBlockedBy: ["1"]  // Task #2 waits for Task #1
})

// Add metadata
TaskUpdate({
  taskId: "1",
  metadata: {
    promptFile: ".agent/prompts/pending/worker-b-task.yaml",
    phaseId: "phase1"
  }
})

// List all tasks
TaskList()
// Returns: [{id: "1", subject: "...", status: "...", owner: "..."}, ...]

// Get task details
TaskGet({taskId: "1"})
// Returns: Full task object with description, dependencies, metadata
```

---

**End of Architecture Document**

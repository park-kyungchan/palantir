---
name: assign
description: |
  Assign Native Tasks to worker terminals, update ownership, sync progress tracking.
  Supports Sub-Orchestrator mode for hierarchical task decomposition.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "3.0.0"
argument-hint: "<task-id> <terminal-id> [--sub-orchestrator] | auto"
---

# /assign - Task Assignment to Workers

> **Version:** 3.0.0
> **Role:** Assign Native Tasks to workers via owner field
> **Architecture:** Hybrid (TaskUpdate + _progress.yaml sync)
> **New:** Sub-Orchestrator mode for hierarchical decomposition

---

## 1. Purpose

**Task Assignment Agent** that:
1. Assigns Native Tasks to specific terminals via `TaskUpdate(owner=...)`
2. Updates workload-scoped `_progress.yaml`
3. Supports manual and auto-assignment modes
4. Validates dependencies before assignment
5. **NEW:** Enables Sub-Orchestrator mode for workers to decompose tasks

### 1.1 Workload Context Setup

```bash
# Source workload management modules
source "${WORKSPACE_ROOT:-.}/.claude/skills/shared/workload-files.sh"

# Get current active workload
ACTIVE_WORKLOAD=$(get_active_workload)
WORKLOAD_SLUG=$(get_active_workload_slug)

# Determine progress file path (workload-scoped or global fallback)
if [[ -n "$WORKLOAD_SLUG" ]]; then
    PROGRESS_PATH=$(get_workload_progress_path "$WORKLOAD_SLUG")
else
    PROGRESS_PATH=".agent/prompts/_progress.yaml"
fi
```

---

## 2. Invocation

### User Syntax

```bash
# Manual assignment
/assign 1 terminal-b          # Assign Task #1 to Terminal B
/assign 2 terminal-c          # Assign Task #2 to Terminal C

# Sub-Orchestrator mode (Worker can decompose task)
/assign 1 terminal-b --sub-orchestrator

# Auto assignment
/assign auto                  # Auto-assign all unassigned tasks

# Reassignment
/assign 1 terminal-d          # Reassign Task #1 to Terminal D
```

### Arguments

- `$0`: Task ID or "auto"
- `$1`: Terminal ID (e.g., "terminal-b", "terminal-c")
- `--sub-orchestrator` (optional): Enable Sub-Orchestrator mode for this worker

---

## 3. Execution Protocol

### 3.1 Mode: Manual Assignment

```javascript
function manualAssign(taskId, terminalId, options = {}) {
  // Parse options
  const isSubOrchestrator = options.subOrchestrator || false

  // 1. Validate task exists
  task = TaskGet({taskId})
  if (!task) {
    error(`Task #${taskId} not found`)
    return
  }

  // 2. Check if already assigned
  if (task.owner && task.owner !== "") {
    warn(`Task #${taskId} already assigned to ${task.owner}`)
    confirmReassign = askUser("Reassign to ${terminalId}? (y/n)")
    if (!confirmReassign) return
  }

  // 3. Check dependencies
  if (task.blockedBy && task.blockedBy.length > 0) {
    warn(`⚠️  Task #${taskId} is blocked by: ${task.blockedBy.join(', ')}`)

    // Check if blockers are completed
    allCompleted = true
    for (blockerId of task.blockedBy) {
      blocker = TaskGet({taskId: blockerId})
      if (blocker.status !== "completed") {
        allCompleted = false
        warn(`  - Task #${blockerId} (${blocker.status})`)
      }
    }

    if (!allCompleted) {
      info(`Task can be assigned but cannot start until blockers complete`)
    }
  }

  // 4. Determine hierarchy level
  const currentHierarchy = task.metadata?.hierarchyLevel || 0
  const newHierarchyLevel = isSubOrchestrator ? currentHierarchy : currentHierarchy

  // 5. Assign owner and set metadata
  TaskUpdate({
    taskId: taskId,
    owner: terminalId,
    metadata: {
      hierarchyLevel: newHierarchyLevel,
      subOrchestratorMode: isSubOrchestrator,
      canDecompose: isSubOrchestrator
    }
  })

  const modeLabel = isSubOrchestrator ? " (Sub-Orchestrator)" : ""
  console.log(`✅ Task #${taskId} assigned to ${terminalId}${modeLabel}`)

  // 6. Update _progress.yaml
  updateProgressFile(taskId, terminalId, task, isSubOrchestrator)

  // 7. Show next actions
  printNextActions(task, terminalId, isSubOrchestrator)
}
```

### 3.2 Mode: Auto Assignment

```javascript
function autoAssign() {
  // 1. Get all unassigned tasks
  allTasks = TaskList()
  unassigned = allTasks.filter(t => !t.owner || t.owner === "")

  if (unassigned.length === 0) {
    console.log("✅ All tasks already assigned")
    return
  }

  console.log(`Found ${unassigned.length} unassigned tasks`)

  // 2. Read _progress.yaml to find available terminals (workload-scoped)
  progressPath = getWorkloadProgressPath()  // Uses active workload or global fallback
  progressData = Read(progressPath)
  terminals = parseYAML(progressData).terminals || {}

  availableTerminals = Object.keys(terminals).filter(tid =>
    terminals[tid].status === "idle" &&
    !terminals[tid].currentTask
  )

  if (availableTerminals.length === 0) {
    // Generate terminal IDs based on task count
    availableTerminals = unassigned.map((t, i) =>
      `terminal-${String.fromCharCode(98 + i)}` // b, c, d, ...
    )
    console.log(`Generated ${availableTerminals.length} terminal IDs`)
  }

  // 3. Assignment strategy: Prioritize unblocked tasks
  assignments = []

  // First pass: Assign unblocked tasks
  unblockedTasks = unassigned.filter(t => !t.blockedBy || t.blockedBy.length === 0)
  for (let i = 0; i < Math.min(unblockedTasks.length, availableTerminals.length); i++) {
    assignments.push({
      taskId: unblockedTasks[i].id,
      terminalId: availableTerminals[i],
      canStart: true
    })
  }

  // Second pass: Assign blocked tasks to remaining terminals
  blockedTasks = unassigned.filter(t => t.blockedBy && t.blockedBy.length > 0)
  let terminalIndex = assignments.length
  for (task of blockedTasks) {
    if (terminalIndex >= availableTerminals.length) break
    assignments.push({
      taskId: task.id,
      terminalId: availableTerminals[terminalIndex],
      canStart: false
    })
    terminalIndex++
  }

  // 4. Execute assignments
  for (assignment of assignments) {
    TaskUpdate({
      taskId: assignment.taskId,
      owner: assignment.terminalId
    })

    task = TaskGet({taskId: assignment.taskId})
    updateProgressFile(assignment.taskId, assignment.terminalId, task)

    let status = assignment.canStart ? "🟢 Ready" : "🔴 Blocked"
    console.log(`${status} Task #${assignment.taskId} → ${assignment.terminalId}`)
  }

  // 5. Summary
  console.log(`\n=== Assignment Summary ===`)
  console.log(`Total assigned: ${assignments.length}`)
  console.log(`Can start now: ${assignments.filter(a => a.canStart).length}`)
  console.log(`Blocked: ${assignments.filter(a => !a.canStart).length}`)

  printWorkerInstructions(assignments)
}
```

### 3.3 Helper: updateProgressFile

```javascript
function updateProgressFile(taskId, terminalId, task, isSubOrchestrator = false) {
  // Read current progress (workload-scoped)
  progressPath = getWorkloadProgressPath()  // Uses active workload or global fallback
  let progressData = {}

  if (fileExists(progressPath)) {
    content = Read(progressPath)
    progressData = parseYAML(content)
  } else {
    progressData = {
      version: "1.0",
      projectId: "current-project",
      lastUpdated: new Date().toISOString(),
      terminals: {},
      phases: {},
      completedTasks: [],
      blockers: []
    }
  }

  // Update terminal info
  if (!progressData.terminals[terminalId]) {
    progressData.terminals[terminalId] = {
      role: isSubOrchestrator ? "Sub-Orchestrator" : "Worker",
      status: "idle",
      currentTask: null,
      assignedPhase: task.metadata?.phaseId || null,
      nativeTaskId: taskId,
      blockedBy: task.blockedBy || [],
      subOrchestratorMode: isSubOrchestrator,
      hierarchyLevel: task.metadata?.hierarchyLevel || 0,
      startedAt: null,
      completedAt: null
    }
  } else {
    progressData.terminals[terminalId].nativeTaskId = taskId
    progressData.terminals[terminalId].assignedPhase = task.metadata?.phaseId || null
    progressData.terminals[terminalId].blockedBy = task.blockedBy || []
    progressData.terminals[terminalId].subOrchestratorMode = isSubOrchestrator
    progressData.terminals[terminalId].hierarchyLevel = task.metadata?.hierarchyLevel || 0
    if (isSubOrchestrator) {
      progressData.terminals[terminalId].role = "Sub-Orchestrator"
    }
  }

  // Update phase info
  if (task.metadata?.phaseId) {
    progressData.phases[task.metadata.phaseId] = {
      nativeTaskId: taskId,
      status: task.status,
      owner: terminalId,
      subOrchestratorMode: isSubOrchestrator,
      startedAt: null,
      completedAt: null
    }
  }

  progressData.lastUpdated = new Date().toISOString()

  // Write back
  Edit({
    file_path: progressPath,
    old_string: content,
    new_string: toYAML(progressData)
  })
}
```

### 3.4 Helper: printNextActions

```javascript
function printNextActions(task, terminalId, isSubOrchestrator = false) {
  const modeLabel = isSubOrchestrator ? " (Sub-Orchestrator)" : ""
  console.log(`\n=== Next Actions for ${terminalId}${modeLabel} ===`)

  if (isSubOrchestrator) {
    console.log(`\n🔧 Sub-Orchestrator Mode Enabled:`)
    console.log(`  • Can decompose this task into subtasks`)
    console.log(`  • Use /orchestrate to break down complex work`)
    console.log(`  • Created subtasks will have hierarchyLevel = ${(task.metadata?.hierarchyLevel || 0) + 1}`)
  }

  if (task.blockedBy && task.blockedBy.length > 0) {
    console.log(`\n⏸️  Wait for blockers to complete:`)
    for (blockerId of task.blockedBy) {
      blocker = TaskGet({taskId: blockerId})
      console.log(`  - Task #${blockerId}: ${blocker.subject} (${blocker.status})`)
    }
    console.log(`\nWhen ready, run: /worker start`)
  } else {
    console.log(`\n✅ No blockers - ready to start!`)
    console.log(`\nRun in ${terminalId}:`)
    if (isSubOrchestrator) {
      console.log(`  /worker start  (can use /orchestrate if task needs decomposition)`)
    } else {
      console.log(`  /worker start`)
    }
  }

  // Show prompt file location
  if (task.metadata?.promptFile) {
    console.log(`\nPrompt file: ${task.metadata.promptFile}`)
  }
}
```

### 3.5 Helper: printWorkerInstructions

```javascript
function printWorkerInstructions(assignments) {
  console.log(`\n=== Worker Instructions ===\n`)

  // Group by can start
  let ready = assignments.filter(a => a.canStart)
  let blocked = assignments.filter(a => !a.canStart)

  if (ready.length > 0) {
    console.log(`🟢 Ready to Start (${ready.length}):\n`)
    for (assignment of ready) {
      task = TaskGet({taskId: assignment.taskId})
      console.log(`${assignment.terminalId}:`)
      console.log(`  /worker start`)
      console.log(`  → Task #${assignment.taskId}: ${task.subject}\n`)
    }
  }

  if (blocked.length > 0) {
    console.log(`🔴 Blocked (${blocked.length}):\n`)
    for (assignment of blocked) {
      task = TaskGet({taskId: assignment.taskId})
      console.log(`${assignment.terminalId}:`)
      console.log(`  (Wait for blockers to complete)`)
      console.log(`  → Task #${assignment.taskId}: ${task.subject}`)
      console.log(`  → Blocked by: ${task.blockedBy.join(', ')}\n`)
    }
  }
}
```

---

## 4. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **Task not found** | TaskGet returns null | Show available tasks via TaskList |
| **Invalid terminal ID** | N/A (any string allowed) | Warn about naming convention |
| **Circular dependency** | Detected in TaskGet | Cannot assign, notify user |
| **Progress file conflict** | File locked/corrupted | Regenerate from TaskList |

---

## 4.5. Sub-Orchestrator Mode

### 4.5.1 Overview

Sub-Orchestrator mode enables workers to **decompose assigned tasks** into subtasks, creating a hierarchical task structure.

**Use Cases:**
- Complex tasks that need further breakdown
- Worker has domain expertise to decompose optimally
- Dynamic decomposition based on runtime findings

### 4.5.2 Hierarchical Task Levels

```
Level 0 (Main):           /orchestrate by Main Orchestrator
    │
    ├─ Task #1 ──────────> Assigned to terminal-b (--sub-orchestrator)
    │   │
    │   └─ Level 1:       terminal-b runs /orchestrate
    │       ├─ Subtask #1.1
    │       ├─ Subtask #1.2
    │       └─ Subtask #1.3
    │
    └─ Task #2 ──────────> Assigned to terminal-c (regular worker)
```

### 4.5.3 Metadata Fields

When `--sub-orchestrator` is used, the following metadata is set:

```javascript
{
  hierarchyLevel: 0,           // Current level (0 = main, 1 = sub, 2 = sub-sub)
  subOrchestratorMode: true,   // Enables decomposition capability
  canDecompose: true           // Permission to create subtasks
}
```

### 4.5.4 Worker Capabilities

| Mode | Can Execute Task | Can Decompose | Subtask Level |
|------|------------------|---------------|---------------|
| Regular Worker | ✅ | ❌ | N/A |
| Sub-Orchestrator | ✅ | ✅ | hierarchyLevel + 1 |

### 4.5.5 Workflow Example

```bash
# 1. Main orchestrator creates tasks
/orchestrate "Implement authentication system"
# → Creates Task #1, #2, #3

# 2. Assign with Sub-Orchestrator mode
/assign 1 terminal-b --sub-orchestrator
# ✅ Task #1 assigned to terminal-b (Sub-Orchestrator)
# → hierarchyLevel: 0, canDecompose: true

# 3. Worker decomposes task (in terminal-b)
/worker start
# Worker reads task, decides to decompose
/orchestrate "Break down authentication into components"
# → Creates Subtask #1.1, #1.2, #1.3 with hierarchyLevel: 1

# 4. Sub-orchestrator assigns subtasks to itself or others
/assign 4 terminal-b    # Subtask #1.1
/assign 5 terminal-c    # Subtask #1.2
```

### 4.5.6 Progress Tracking

Sub-Orchestrator assignments are tracked in `_progress.yaml`:

```yaml
terminals:
  terminal-b:
    role: "Sub-Orchestrator"
    nativeTaskId: "1"
    subOrchestratorMode: true
    hierarchyLevel: 0
    status: "in_progress"
```

---

## 6. Example Usage

### Example 1: Manual Assignment

```bash
/assign 1 terminal-b
```

**Output:**
```
✅ Task #1 assigned to terminal-b

=== Next Actions for terminal-b ===
✅ No blockers - ready to start!

Run in terminal-b:
  /worker start

Prompt file: .agent/prompts/pending/worker-b-task.yaml
```

### Example 2: Auto Assignment

```bash
/assign auto
```

**Output:**
```
Found 3 unassigned tasks
Generated 3 terminal IDs

🟢 Ready Task #1 → terminal-b
🔴 Blocked Task #2 → terminal-c
🔴 Blocked Task #3 → terminal-d

=== Assignment Summary ===
Total assigned: 3
Can start now: 1
Blocked: 2

=== Worker Instructions ===

🟢 Ready to Start (1):

terminal-b:
  /worker start
  → Task #1: Implement session registry

🔴 Blocked (2):

terminal-c:
  (Wait for blockers to complete)
  → Task #2: Prompt file generation
  → Blocked by: 1

terminal-d:
  (Wait for blockers to complete)
  → Task #3: Lifecycle management
  → Blocked by: 2
```

### Example 3: Reassignment

```bash
/assign 1 terminal-d
```

**Output:**
```
⚠️  Task #1 already assigned to terminal-b
Reassign to terminal-d? (y/n): y

✅ Task #1 reassigned to terminal-d
✅ Updated _progress.yaml
```

### Example 4: Sub-Orchestrator Assignment

```bash
/assign 1 terminal-b --sub-orchestrator
```

**Output:**
```
✅ Task #1 assigned to terminal-b (Sub-Orchestrator)

=== Next Actions for terminal-b (Sub-Orchestrator) ===

🔧 Sub-Orchestrator Mode Enabled:
  • Can decompose this task into subtasks
  • Use /orchestrate to break down complex work
  • Created subtasks will have hierarchyLevel = 1

✅ No blockers - ready to start!

Run in terminal-b:
  /worker start  (can use /orchestrate if task needs decomposition)

Prompt file: .agent/prompts/pending/worker-b-task.yaml
```

**Sub-Orchestrator Workflow:**
```bash
# 1. Worker receives complex task with sub-orchestrator mode
/worker start b

# 2. If task is too complex, decompose it
/orchestrate "Break down feature X into subtasks"
# → Creates child Tasks #4, #5, #6 (hierarchyLevel = 1)

# 3. Optionally assign subtasks (or work on them directly)
/assign 4 terminal-b
/assign 5 terminal-c

# 4. Complete parent task when all subtasks done
/worker done
```

---

## 7. Integration Points

### 6.1 With /orchestrate

```bash
/orchestrate "Build feature X"
# → Creates Tasks #1, #2, #3

/assign auto
# → Assigns tasks to workers
```

### 6.2 With /worker

```bash
# After assignment
/worker start      # Worker claims assigned task
/worker done       # Frees up terminal for new assignment
```

### 6.3 With /workers

```bash
/workers           # View assignment status
# → Shows which terminals have which tasks
```

---

## 8. Testing Checklist

**Basic Assignment:**
- [ ] Manual assign unblocked task
- [ ] Manual assign blocked task
- [ ] Auto assign with 3 tasks
- [ ] Auto assign with more tasks than terminals
- [ ] Reassignment flow
- [ ] Progress file creation from scratch
- [ ] Progress file update
- [ ] Task not found error
- [ ] All tasks already assigned scenario

**Sub-Orchestrator Mode:**
- [ ] Assign with --sub-orchestrator flag
- [ ] Assign with --sub short flag
- [ ] hierarchyLevel metadata set correctly
- [ ] subOrchestratorMode in _progress.yaml
- [ ] printNextActions shows Sub-Orchestrator info
- [ ] Child tasks inherit correct hierarchyLevel

---

## Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: sonnet` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: Task update via owner field |
| `hook-config.md` | N/A | Skill 내 Hook 없음 |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | ✅ | Task assignment + dependency check |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Task assignment to workers |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |
| 3.0.0 | Sub-Orchestrator 모드 추가: --sub-orchestrator 플래그, hierarchyLevel 메타데이터, Worker 분해 권한 |

---

**End of Skill Documentation**

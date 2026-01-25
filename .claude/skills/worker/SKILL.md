---
name: worker
description: |
  Worker self-service commands (start, done, status, block).
user-invocable: true
disable-model-invocation: false
context: standard
model: sonnet
version: "3.1.0"
argument-hint: "<start|done|status|block> [b|c|d|terminal-id] [taskId]"
hooks:
  Setup:
    - type: command
      command: "/home/palantir/.claude/hooks/worker-preflight.sh"
      timeout: 10000
---

# /worker - Worker Self-Service Commands

> **Version:** 1.0
> **Role:** Self-service commands for workers (start, done, status, block)
> **Architecture:** Hybrid (Native Task System + File-Based Prompts)

---

## 1. Purpose

**Worker Self-Service Agent** that enables workers to:
1. Claim and start assigned tasks (`/worker start`)
2. Mark tasks as complete (`/worker done`)
3. Check current status and progress (`/worker status`)
4. Report blockers to orchestrator (`/worker block`)

---

## 2. Invocation

### User Syntax

```bash
# Start with terminal ID (RECOMMENDED)
/worker start b          # Start as terminal-b
/worker start c          # Start as terminal-c
/worker start b 16       # Start as terminal-b, specific task #16

# Start without terminal ID (requires env/session config)
/worker start
/worker start 3          # Start specific task #3

# Mark current task as done
/worker done
/worker done 3           # Mark specific task #3 as done

# Check status
/worker status
/worker status b         # Check terminal-b status
/worker status --all     # Show all assigned tasks

# Report blocker
/worker block "Need API docs"
/worker block 3 "Waiting for auth module"  # Block specific task
```

### Arguments

- `$0`: Subcommand (`start`, `done`, `status`, `block`)
- `$1`: Terminal ID (b, c, d) OR task ID OR reason
- `$2`: Optional task ID (when $1 is terminal ID)

### Terminal ID Shortcuts

| Shortcut | Full ID |
|----------|---------|
| `b` | `terminal-b` |
| `c` | `terminal-c` |
| `d` | `terminal-d` |
| `terminal-b` | `terminal-b` |

---

## 3. Worker Identity

```javascript
// Terminal shortcut mapping (also used in Main Router)
const TERMINAL_SHORTCUTS = {
  'b': 'terminal-b',
  'c': 'terminal-c',
  'd': 'terminal-d',
  'terminal-b': 'terminal-b',
  'terminal-c': 'terminal-c',
  'terminal-d': 'terminal-d'
}

function normalizeTerminalId(input) {
  // Convert shortcuts to full terminal ID
  if (!input) return null
  let lower = input.toLowerCase().trim()
  return TERMINAL_SHORTCUTS[lower] || input
}

function getWorkerId() {
  // Priority order for worker identification:

  // 1. Environment variable (set by orchestrator)
  if (process.env.WORKER_ID) {
    return normalizeTerminalId(process.env.WORKER_ID)
  }

  // 2. Session environment file (set by /worker start b)
  sessionEnvPath = ".claude/session-env/worker-id"
  if (fileExists(sessionEnvPath)) {
    let savedId = Read(sessionEnvPath).trim()
    return normalizeTerminalId(savedId)
  }

  // 3. Terminal context (if available)
  if (process.env.TERMINAL_ID) {
    return normalizeTerminalId(process.env.TERMINAL_ID)
  }

  // 4. Interactive prompt with clear options
  console.log(`
⚠️  Worker ID not configured.

Which terminal are you?
  b = terminal-b
  c = terminal-c
  d = terminal-d

Tip: Use "/worker start b" to set identity automatically.
`)

  // Use AskUserQuestion for structured input
  response = AskUserQuestion({
    questions: [{
      question: "Which terminal are you?",
      header: "Terminal",
      options: [
        { label: "terminal-b", description: "Worker B" },
        { label: "terminal-c", description: "Worker C" },
        { label: "terminal-d", description: "Worker D" }
      ],
      multiSelect: false
    }]
  })

  workerId = response.answers["Terminal"] || "terminal-b"

  // Save for session
  Bash("mkdir -p .claude/session-env")
  Write({
    file_path: sessionEnvPath,
    content: workerId
  })

  console.log(`✅ Worker ID set to: ${workerId}`)
  return workerId
}

function getMyTasks() {
  let workerId = getWorkerId()
  let allTasks = TaskList()

  // Filter tasks owned by this worker
  return allTasks.filter(t => t.owner === workerId)
}
```

---

## 4. Execution Protocol

### 4.1 /worker start

```javascript
function workerStart(specificTaskId = null) {
  let workerId = getWorkerId()
  console.log(`🚀 Worker ${workerId} starting task...`)

  // 1. Get my assigned tasks
  let myTasks = getMyTasks()

  if (myTasks.length === 0) {
    console.log(`
⚠️  No tasks assigned to ${workerId}

Ask the Orchestrator to assign tasks:
  /assign <taskId> ${workerId}

Or request auto-assignment:
  /assign auto
`)
    return { status: "no_tasks" }
  }

  // 2. Find task to start
  let taskToStart = null

  if (specificTaskId) {
    // Start specific task
    taskToStart = myTasks.find(t => t.id === specificTaskId)
    if (!taskToStart) {
      console.log(`❌ Task #${specificTaskId} is not assigned to you`)
      return { status: "not_assigned" }
    }
  } else {
    // Find first unblocked pending task
    let pendingTasks = myTasks.filter(t => t.status === "pending")

    for (task of pendingTasks) {
      let taskDetail = TaskGet({taskId: task.id})

      // Check if blockers are resolved
      if (!taskDetail.blockedBy || taskDetail.blockedBy.length === 0) {
        taskToStart = task
        break
      }

      // Check if blockers are completed
      let allBlockersComplete = true
      for (blockerId of taskDetail.blockedBy) {
        let blocker = TaskGet({taskId: blockerId})
        if (blocker.status !== "completed") {
          allBlockersComplete = false
          break
        }
      }

      if (allBlockersComplete) {
        taskToStart = task
        break
      }
    }

    if (!taskToStart) {
      // Check if there's an in-progress task
      let inProgressTask = myTasks.find(t => t.status === "in_progress")

      if (inProgressTask) {
        console.log(`
ℹ️  You already have a task in progress:

   Task #${inProgressTask.id}: ${inProgressTask.subject}

Continue working on it, or run \`/worker done\` when complete.
`)
        return showTaskDetails(inProgressTask)
      }

      // All pending tasks are blocked
      let blockedTasks = pendingTasks.filter(t => {
        let detail = TaskGet({taskId: t.id})
        return detail.blockedBy && detail.blockedBy.length > 0
      })

      console.log(`
⏳ All your tasks are blocked:

${blockedTasks.map(t => {
  let detail = TaskGet({taskId: t.id})
  return `  Task #${t.id}: Blocked by ${detail.blockedBy.join(', ')}`
}).join('\n')}

Wait for blockers to complete, or ask Orchestrator for help.
`)
      return { status: "blocked" }
    }
  }

  // 3. Check if task is blocked
  let taskDetail = TaskGet({taskId: taskToStart.id})

  if (taskDetail.blockedBy && taskDetail.blockedBy.length > 0) {
    let unblockedBlockers = []
    for (blockerId of taskDetail.blockedBy) {
      let blocker = TaskGet({taskId: blockerId})
      if (blocker.status !== "completed") {
        unblockedBlockers.push(`#${blockerId} (${blocker.status})`)
      }
    }

    if (unblockedBlockers.length > 0) {
      console.log(`
⚠️  Task #${taskToStart.id} is blocked by:
${unblockedBlockers.map(b => `  - Task ${b}`).join('\n')}

Wait for these tasks to complete first.
`)
      return { status: "blocked", blockedBy: unblockedBlockers }
    }
  }

  // 4. Update task status
  TaskUpdate({
    taskId: taskToStart.id,
    status: "in_progress"
  })

  // 5. Read and display prompt file
  let promptFile = findPromptFile(taskToStart.id)
  let promptContent = ""

  if (promptFile) {
    promptContent = Read(promptFile)
  }

  // 6. Display task details
  console.log(`
=== Task #${taskToStart.id}: ${taskToStart.subject} ===

Priority: ${taskDetail.metadata?.priority || 'P1'}
Status: 🔄 in_progress (just updated)
Assigned: ${workerId}

${promptFile ? `📄 Prompt File: ${promptFile}` : ''}

📋 Instructions:
────────────────────────────────────────
${promptContent ? extractInstructions(promptContent) : '(No specific instructions - check task description)'}
────────────────────────────────────────

📝 Task Description:
${taskDetail.description || '(No description)'}

Next steps:
1. Read the reference files listed above
2. Implement following the patterns
3. When done, run: /worker done
`)

  // 7. Update progress file
  updateProgressFile(workerId, taskToStart.id, "in_progress")

  return {
    status: "started",
    taskId: taskToStart.id,
    subject: taskToStart.subject
  }
}
```

### 4.2 /worker done

```javascript
function workerDone(specificTaskId = null) {
  let workerId = getWorkerId()
  console.log(`✅ Marking task as done...`)

  // 1. Find current task
  let myTasks = getMyTasks()
  let currentTask = null

  if (specificTaskId) {
    currentTask = myTasks.find(t => t.id === specificTaskId)
    if (!currentTask) {
      console.log(`❌ Task #${specificTaskId} is not assigned to you`)
      return { status: "not_assigned" }
    }
  } else {
    // Find in-progress task
    currentTask = myTasks.find(t => t.status === "in_progress")

    if (!currentTask) {
      console.log(`
⚠️  No in-progress task found.

Run \`/worker start\` to begin a task first.
`)
      return { status: "no_current_task" }
    }
  }

  // 2. Mark as completed
  TaskUpdate({
    taskId: currentTask.id,
    status: "completed"
  })

  // 3. Move prompt file to completed
  movePromptFile(currentTask.id, "pending", "completed")

  // 4. Update progress file
  updateProgressFile(workerId, currentTask.id, "completed")

  // 5. Calculate progress
  let allMyTasks = myTasks
  let completedTasks = allMyTasks.filter(t =>
    t.status === "completed" || t.id === currentTask.id
  )
  let totalTasks = allMyTasks.length
  let progressPercent = ((completedTasks.length / totalTasks) * 100).toFixed(1)

  // 6. Find next task
  let nextTask = allMyTasks.find(t =>
    t.status === "pending" && t.id !== currentTask.id
  )

  // 7. Check if next task is unblocked
  let nextTaskReady = false
  if (nextTask) {
    let nextDetail = TaskGet({taskId: nextTask.id})
    if (!nextDetail.blockedBy || nextDetail.blockedBy.length === 0) {
      nextTaskReady = true
    } else {
      // Check if all blockers completed
      nextTaskReady = nextDetail.blockedBy.every(bid => {
        let blocker = TaskGet({taskId: bid})
        return blocker.status === "completed"
      })
    }
  }

  // 8. Display completion message
  console.log(`
✅ Task #${currentTask.id} marked as completed!

📊 Progress: ${completedTasks.length}/${totalTasks} tasks complete (${progressPercent}%)

${'█'.repeat(Math.floor(progressPercent / 10))}${'░'.repeat(10 - Math.floor(progressPercent / 10))} ${progressPercent}%

${nextTask ? `
🔜 Next Task Available:
   Task #${nextTask.id}: ${nextTask.subject}
   Status: ${nextTaskReady ? '✅ Ready to start' : '⏳ Blocked'}

${nextTaskReady ? 'Run `/worker start` to begin next task.' : 'Waiting for blockers to complete.'}
` : `
🎉 All your tasks are complete!

Notify the Orchestrator:
  "All tasks for ${workerId} complete. Ready for /collect."
`}
`)

  return {
    status: "completed",
    taskId: currentTask.id,
    progress: `${completedTasks.length}/${totalTasks}`,
    nextTask: nextTask ? { id: nextTask.id, ready: nextTaskReady } : null
  }
}
```

### 4.3 /worker status

```javascript
function workerStatus(showAll = false) {
  let workerId = getWorkerId()

  // 1. Get my tasks
  let myTasks = getMyTasks()

  if (myTasks.length === 0) {
    console.log(`
=== Worker Status: ${workerId} ===

No tasks assigned.

Ask Orchestrator for task assignment:
  /assign <taskId> ${workerId}
`)
    return { status: "no_tasks" }
  }

  // 2. Categorize tasks
  let completed = myTasks.filter(t => t.status === "completed")
  let inProgress = myTasks.filter(t => t.status === "in_progress")
  let pending = myTasks.filter(t => t.status === "pending")

  // 3. Get current task details
  let currentTask = inProgress[0]
  let currentTaskDetail = currentTask ? TaskGet({taskId: currentTask.id}) : null

  // 4. Check for blockers
  let blockers = []
  for (task of pending) {
    let detail = TaskGet({taskId: task.id})
    if (detail.blockedBy && detail.blockedBy.length > 0) {
      for (blockerId of detail.blockedBy) {
        let blocker = TaskGet({taskId: blockerId})
        if (blocker.status !== "completed") {
          blockers.push({
            task: task.id,
            blockedBy: blockerId,
            blockerStatus: blocker.status
          })
        }
      }
    }
  }

  // 5. Display status
  console.log(`
=== Worker Status: ${workerId} ===

${currentTask ? `
Current Task: #${currentTask.id} ${currentTask.subject}
Status: 🔄 in_progress
${currentTaskDetail?.metadata?.startedAt ? `Started: ${currentTaskDetail.metadata.startedAt}` : ''}
` : `
Current Task: None
`}

Progress:
  ✅ Completed: ${completed.length} task(s)
  🔄 In Progress: ${inProgress.length} task(s)
  ⏳ Pending: ${pending.length} task(s)

${'█'.repeat(Math.floor((completed.length / myTasks.length) * 10))}${'░'.repeat(10 - Math.floor((completed.length / myTasks.length) * 10))} ${((completed.length / myTasks.length) * 100).toFixed(1)}%

${blockers.length > 0 ? `
⚠️  Blockers:
${blockers.map(b => `  - Task #${b.task} blocked by #${b.blockedBy} (${b.blockerStatus})`).join('\n')}
` : `
✅ No blockers reported.
`}
${showAll ? `
=== All Tasks ===

| ID | Subject | Status |
|----|---------|--------|
${myTasks.map(t => {
  let statusIcon = t.status === "completed" ? "✅" :
                   t.status === "in_progress" ? "🔄" : "⏳"
  return `| #${t.id} | ${t.subject.substring(0, 40)} | ${statusIcon} ${t.status} |`
}).join('\n')}
` : ''}
`)

  return {
    status: "ok",
    current: currentTask?.id || null,
    completed: completed.length,
    inProgress: inProgress.length,
    pending: pending.length,
    blockers: blockers
  }
}
```

### 4.4 /worker block

```javascript
function workerBlock(reason, specificTaskId = null) {
  let workerId = getWorkerId()

  if (!reason || reason.trim() === "") {
    console.log(`
❌ Please provide a blocker reason:

  /worker block "Description of the blocker"
`)
    return { status: "missing_reason" }
  }

  // 1. Find task to block
  let myTasks = getMyTasks()
  let taskToBlock = null

  if (specificTaskId) {
    taskToBlock = myTasks.find(t => t.id === specificTaskId)
  } else {
    // Block current in-progress task
    taskToBlock = myTasks.find(t => t.status === "in_progress")
  }

  if (!taskToBlock) {
    console.log(`
⚠️  No in-progress task to report blocker for.

Run \`/worker start\` first, then report blockers.
`)
    return { status: "no_current_task" }
  }

  // 2. Record blocker
  let now = new Date().toISOString()

  let blocker = {
    taskId: taskToBlock.id,
    worker: workerId,
    reason: reason,
    reportedAt: now,
    status: "open"
  }

  // 3. Update progress file with blocker
  addBlockerToProgress(blocker)

  // 4. Create blocker notification file
  let blockerNotification = `# Blocker Report

Task: #${taskToBlock.id} - ${taskToBlock.subject}
Worker: ${workerId}
Reported: ${now}

## Description

${reason}

## Requested Action

Please review and provide guidance or resolution.

## Task Context

${taskToBlock.description || '(No description available)'}
`

  let blockerPath = `.agent/outputs/blockers/blocker-${taskToBlock.id}-${Date.now()}.md`
  Bash(`mkdir -p .agent/outputs/blockers`)
  Write({
    file_path: blockerPath,
    content: blockerNotification
  })

  // 5. Display confirmation
  console.log(`
⚠️  Blocker Reported!

Task: #${taskToBlock.id} ${taskToBlock.subject}
Blocker: ${reason}
Reported: ${now}

📢 Orchestrator has been notified.
   Blocker file: ${blockerPath}

While waiting for resolution:
  - Check if you can work around the blocker
  - Document what you've tried
  - Consider working on another task: /worker start <taskId>
`)

  return {
    status: "blocker_reported",
    taskId: taskToBlock.id,
    reason: reason,
    blockerFile: blockerPath
  }
}
```

---

## 5. Helper Functions

### 5.1 findPromptFile

```javascript
function findPromptFile(taskId) {
  // Check pending directory
  let pendingFiles = Glob(`.agent/prompts/pending/*task*.yaml`)

  for (file of pendingFiles) {
    let content = Read(file)
    if (content.includes(`nativeTaskId: "${taskId}"`) ||
        content.includes(`taskId: "${taskId}"`)) {
      return file
    }
  }

  // Check by worker naming convention
  let workerFiles = Glob(`.agent/prompts/pending/worker-*-*.yaml`)
  for (file of workerFiles) {
    let content = Read(file)
    if (content.includes(`nativeTaskId: "${taskId}"`)) {
      return file
    }
  }

  return null
}
```

### 5.2 movePromptFile

```javascript
function movePromptFile(taskId, fromDir, toDir) {
  // Ensure target directory exists
  Bash(`mkdir -p .agent/prompts/${toDir}`)

  let promptFile = findPromptFile(taskId)

  if (!promptFile) {
    console.log(`ℹ️  No prompt file found for task #${taskId}`)
    return false
  }

  let filename = promptFile.split('/').pop()
  let destFile = `.agent/prompts/${toDir}/${filename}`

  Bash(`mv "${promptFile}" "${destFile}"`)
  console.log(`📁 Moved: ${promptFile} → ${destFile}`)

  return true
}
```

### 5.3 updateProgressFile

```javascript
function updateProgressFile(workerId, taskId, status) {
  let progressPath = ".agent/prompts/_progress.yaml"

  if (!fileExists(progressPath)) {
    console.log("ℹ️  Progress file not found, skipping update")
    return
  }

  let content = Read(progressPath)

  // Update terminal status
  let now = new Date().toISOString()

  if (status === "in_progress") {
    // Update startedAt
    content = content.replace(
      new RegExp(`(${workerId}:[\\s\\S]*?startedAt:)\\s*null`, 'm'),
      `$1 "${now}"`
    )
    content = content.replace(
      new RegExp(`(${workerId}:[\\s\\S]*?status:)\\s*"?idle"?`, 'm'),
      `$1 "working"`
    )
  } else if (status === "completed") {
    // Update completedAt
    content = content.replace(
      new RegExp(`(${workerId}:[\\s\\S]*?completedAt:)\\s*null`, 'm'),
      `$1 "${now}"`
    )
  }

  Write({
    file_path: progressPath,
    content: content
  })
}
```

### 5.4 addBlockerToProgress

```javascript
function addBlockerToProgress(blocker) {
  let progressPath = ".agent/prompts/_progress.yaml"

  if (!fileExists(progressPath)) {
    return
  }

  let content = Read(progressPath)

  // Find blockers section and add new blocker
  let blockerEntry = `
  - taskId: "${blocker.taskId}"
    worker: "${blocker.worker}"
    reason: "${blocker.reason}"
    reportedAt: "${blocker.reportedAt}"
    status: "open"`

  if (content.includes("blockers: []")) {
    content = content.replace("blockers: []", `blockers:${blockerEntry}`)
  } else if (content.includes("blockers:")) {
    content = content.replace(/blockers:/, `blockers:${blockerEntry}`)
  }

  Write({
    file_path: progressPath,
    content: content
  })
}
```

### 5.5 extractInstructions

```javascript
function extractInstructions(promptContent) {
  // Extract key sections from prompt YAML
  let lines = promptContent.split('\n')
  let instructions = []

  let inSection = false
  let sectionName = ""

  for (line of lines) {
    // Look for key sections
    if (line.match(/^##\s*(Objective|Instructions|Requirements|Completion Criteria)/i)) {
      inSection = true
      sectionName = line
      instructions.push(line)
      continue
    }

    if (inSection) {
      if (line.match(/^##/) && !line.match(/^##\s*(Objective|Instructions|Requirements|Completion Criteria)/i)) {
        inSection = false
        continue
      }
      instructions.push(line)
    }
  }

  return instructions.slice(0, 30).join('\n') // Limit output
}
```

---

## 6. Main Router

```javascript
// Terminal ID shortcuts mapping
const TERMINAL_SHORTCUTS = {
  'b': 'terminal-b',
  'c': 'terminal-c',
  'd': 'terminal-d',
  'terminal-b': 'terminal-b',
  'terminal-c': 'terminal-c',
  'terminal-d': 'terminal-d'
}

function parseTerminalId(param) {
  // Check if param is a terminal shortcut
  if (param && TERMINAL_SHORTCUTS[param.toLowerCase()]) {
    return TERMINAL_SHORTCUTS[param.toLowerCase()]
  }
  return null
}

function isTaskId(param) {
  // Task IDs are numeric strings
  return param && !isNaN(param) && parseInt(param) > 0
}

function worker(args) {
  // Parse subcommand
  let subcommand = args[0]?.toLowerCase()
  let param1 = args[1]  // Could be terminal ID or task ID
  let param2 = args[2]  // Could be task ID when param1 is terminal

  switch (subcommand) {
    case 'start':
      let terminalId = parseTerminalId(param1)
      let startTaskId = null

      if (terminalId) {
        // /worker start b [taskId]
        setWorkerId(terminalId)  // Set worker identity
        startTaskId = isTaskId(param2) ? param2 : null
      } else if (isTaskId(param1)) {
        // /worker start 16
        startTaskId = param1
      }
      // else: /worker start (no params)

      return workerStart(startTaskId)

    case 'done':
      let doneTerminalId = parseTerminalId(param1)
      let doneTaskId = null

      if (doneTerminalId) {
        setWorkerId(doneTerminalId)
        doneTaskId = isTaskId(param2) ? param2 : null
      } else if (isTaskId(param1)) {
        doneTaskId = param1
      }

      return workerDone(doneTaskId)

    case 'status':
      let statusTerminalId = parseTerminalId(param1)
      let showAll = param1 === '--all' || param2 === '--all'

      if (statusTerminalId) {
        setWorkerId(statusTerminalId)
      }

      return workerStatus(showAll)

    case 'block':
      // Check if first param is task ID
      let blockTaskId = null
      let reason = args.slice(1).join(' ')

      if (reason.match(/^\d+\s/)) {
        let parts = reason.split(/\s+/)
        blockTaskId = parts[0]
        reason = parts.slice(1).join(' ')
      }

      return workerBlock(reason, blockTaskId)

    default:
      console.log(`
=== /worker - Self-Service Commands ===

Usage:
  /worker start <b|c|d> [taskId]   Start as terminal-X (RECOMMENDED)
  /worker start [taskId]           Start assigned task
  /worker done [taskId]            Mark task as complete
  /worker status [b|c|d] [--all]   Show current status
  /worker block "reason"           Report a blocker

Terminal Shortcuts:
  b = terminal-b, c = terminal-c, d = terminal-d

Examples:
  /worker start b                  Start as terminal-b
  /worker start b 16               Start terminal-b on task #16
  /worker start c                  Start as terminal-c
  /worker done                     Complete current task
  /worker status b --all           Show all terminal-b tasks
  /worker block "Need API docs"
`)
      return { status: "help" }
  }
}

function setWorkerId(terminalId) {
  // Store worker ID in session for subsequent calls
  let sessionEnvPath = ".claude/session-env/worker-id"

  // Ensure directory exists
  Bash("mkdir -p .claude/session-env")

  Write({
    file_path: sessionEnvPath,
    content: terminalId
  })

  console.log(`🔧 Worker ID set to: ${terminalId}`)
}
```

---

## 7. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **No tasks assigned** | getMyTasks returns empty | Suggest /assign |
| **Task not assigned to worker** | Task owner mismatch | Show correct owner |
| **All tasks blocked** | All pending have blockers | List blockers, suggest wait |
| **Already in progress** | Task status check | Show current task info |
| **No current task for done** | No in_progress task | Suggest /worker start |
| **Missing blocker reason** | Empty reason string | Show usage example |
| **Prompt file not found** | Glob returns empty | Continue without prompt display |

---

## 8. Example Workflows

### 8.1 Complete Workflow (Recommended)

```bash
# 1. Start as terminal-b (RECOMMENDED - sets identity)
/worker start b

# 2. (Do the work on first assigned task...)

# 3. Mark complete
/worker done

# 4. Start next task (identity already set)
/worker start

# 5. Repeat until all tasks done
```

### 8.2 Start Specific Task

```bash
# Start terminal-b on task #16 specifically
/worker start b 16

# Or if identity already set:
/worker start 16
```

### 8.3 Multi-Terminal Parallel Execution

```bash
# Terminal B window:
/worker start b
# → Starts on Task #16

# Terminal C window (separate terminal):
/worker start c
# → Starts on Task #17

# Both work in parallel, checking blockedBy automatically
```

### 8.4 Handling Blockers

```bash
# 1. Start task
/worker start b

# 2. Encounter blocker
/worker block "Need database credentials for testing"

# 3. Work on different task
/worker start 5

# 4. When blocker resolved, return to original task
/worker start 3
```

### 8.5 Check Status

```bash
# Check my status (requires identity set)
/worker status

# Check specific terminal's status
/worker status b
/worker status c --all
```

---

## 9. Shift-Left Validation (Gate 5)

### 9.1 Purpose

Gate 5 validates task readiness **before** worker execution:
- Verifies all `blockedBy` dependencies are completed
- Checks target file access permissions
- Validates prompt file integrity
- Prevents workers from starting blocked/invalid tasks

### 9.2 Hook Integration

```yaml
hooks:
  Setup:
    - worker-preflight.sh  # Gate 5: Pre-execution Validation
```

### 9.3 Validation Checks

| Check | Description | Failure Action |
|-------|-------------|----------------|
| **BlockedBy Resolution** | All blocking tasks must be `completed` | Block task start |
| **Target File Access** | Files to modify must be writable | Block task start |
| **Parent Directory** | New file parents must exist | Warning |
| **Prompt File** | Valid task prompt (optional) | Warning |

### 9.4 Validation Results

| Result | Behavior | User Action |
|--------|----------|-------------|
| `passed` | ✅ Start task immediately | None required |
| `passed_with_warnings` | ⚠️ Start with warnings displayed | Review warnings |
| `failed` | ❌ Block task start | Resolve errors first |

### 9.5 Integration with /worker start

```
/worker start b
    │
    ▼
┌───────────────────────────┐
│  Gate 5: Pre-execution    │
│  - Check blockedBy        │
│  - Validate file access   │
│  - Check prompt file      │
└───────────────────────────┘
    │
    ├── PASSED ──▶ Start task, update status
    └── FAILED ──▶ Show errors, suggest resolution
```

---

## 10. Testing Checklist

**Terminal ID Shortcuts (NEW v3.0):**
- [ ] /worker start b - sets identity to terminal-b
- [ ] /worker start c - sets identity to terminal-c
- [ ] /worker start b 16 - terminal-b + specific task
- [ ] /worker status b - check terminal-b status
- [ ] /worker status c --all - terminal-c detailed

**Core Functionality:**
- [ ] /worker start - first task
- [ ] /worker start - specific task ID (numeric)
- [ ] /worker start - all tasks blocked
- [ ] /worker start - already in progress
- [ ] /worker done - mark complete
- [ ] /worker done - show next task
- [ ] /worker done - all tasks done
- [ ] /worker status - basic display
- [ ] /worker status --all - detailed display
- [ ] /worker block - with reason
- [ ] /worker block - without reason (error)

**Identity Management:**
- [ ] Worker ID detection (env var)
- [ ] Worker ID detection (session file)
- [ ] Worker ID from shortcut (b → terminal-b)
- [ ] Interactive prompt fallback

**File Operations:**
- [ ] Prompt file discovery
- [ ] Prompt file move on done
- [ ] Progress file update
- [ ] Session env file creation

**Gate 5 Validation (NEW v3.1):**
- [ ] Preflight hook executes on /worker start
- [ ] BlockedBy check blocks incomplete dependencies
- [ ] BlockedBy check passes when all deps complete
- [ ] Target file access validation works
- [ ] Parent directory warning for new files
- [ ] Validation logging to .agent/logs/validation_gates.log

---

## 10. Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| /worker start | <1s | TBD |
| /worker done | <500ms | TBD |
| /worker status | <500ms | TBD |
| /worker block | <500ms | TBD |

---

## Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: sonnet` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: Task delegation pattern |
| `hook-config.md` | ✅ | Setup hook: worker-preflight.sh (Gate 5) |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | ✅ | Task status + blockedBy management |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Worker self-service commands |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |
| 3.0.0 | Terminal ID shortcuts (b, c, d) 지원, `/worker start b` 형식 추가 |
| 3.1.0 | Gate 5 Shift-Left Validation 통합, Setup hook 추가 |

---

**End of Skill Documentation**

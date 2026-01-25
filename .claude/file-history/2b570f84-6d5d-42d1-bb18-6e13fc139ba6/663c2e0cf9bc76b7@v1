---
name: worker
description: |
  Worker self-service commands (start, done, status, block).
user-invocable: true
disable-model-invocation: false
context: standard
model: haiku
version: "2.1.0"
argument-hint: "<start|done|status|block> [taskId|reason]"
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
# Start next assigned task
/worker start
/worker start 3          # Start specific task #3

# Mark current task as done
/worker done
/worker done 3           # Mark specific task #3 as done

# Check status
/worker status
/worker status --all     # Show all assigned tasks

# Report blocker
/worker block "Need API docs"
/worker block 3 "Waiting for auth module"  # Block specific task
```

### Arguments

- `$0`: Subcommand (`start`, `done`, `status`, `block`)
- `$1`: Optional task ID or blocker reason

---

## 3. Worker Identity

```javascript
function getWorkerId() {
  // Priority order for worker identification:

  // 1. Environment variable (set by orchestrator)
  if (process.env.WORKER_ID) {
    return process.env.WORKER_ID
  }

  // 2. Session environment file
  sessionEnvPath = ".claude/session-env/worker-id"
  if (fileExists(sessionEnvPath)) {
    return Read(sessionEnvPath).trim()
  }

  // 3. Terminal context (if available)
  if (process.env.TERMINAL_ID) {
    return process.env.TERMINAL_ID
  }

  // 4. Interactive prompt (first time)
  console.log("⚠️  Worker ID not configured.")
  workerId = askUser("Enter your Worker ID (e.g., terminal-b):")

  // Save for session
  Write({
    file_path: sessionEnvPath,
    content: workerId
  })

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
function worker(args) {
  // Parse subcommand
  let subcommand = args[0]?.toLowerCase()
  let param = args.slice(1).join(' ')

  switch (subcommand) {
    case 'start':
      let startTaskId = param && !isNaN(param) ? param : null
      return workerStart(startTaskId)

    case 'done':
      let doneTaskId = param && !isNaN(param) ? param : null
      return workerDone(doneTaskId)

    case 'status':
      let showAll = param === '--all'
      return workerStatus(showAll)

    case 'block':
      // Check if first param is task ID
      let blockTaskId = null
      let reason = param

      if (param.match(/^\d+\s/)) {
        let parts = param.split(/\s+/)
        blockTaskId = parts[0]
        reason = parts.slice(1).join(' ')
      }

      return workerBlock(reason, blockTaskId)

    default:
      console.log(`
=== /worker - Self-Service Commands ===

Usage:
  /worker start [taskId]     Start assigned task
  /worker done [taskId]      Mark task as complete
  /worker status [--all]     Show current status
  /worker block "reason"     Report a blocker

Examples:
  /worker start              Start next available task
  /worker start 3            Start specific task #3
  /worker done               Complete current task
  /worker status --all       Show all assigned tasks
  /worker block "Need API docs"
`)
      return { status: "help" }
  }
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

### 8.1 Complete Workflow

```bash
# 1. Check what's assigned to me
/worker status

# 2. Start working
/worker start

# 3. (Do the work...)

# 4. Mark complete
/worker done

# 5. Start next task
/worker start
```

### 8.2 Handling Blockers

```bash
# 1. Start task
/worker start

# 2. Encounter blocker
/worker block "Need database credentials for testing"

# 3. Work on different task
/worker start 5

# 4. When blocker resolved, return to original task
/worker start 3
```

---

## 9. Testing Checklist

- [ ] /worker start - first task
- [ ] /worker start - specific task ID
- [ ] /worker start - all tasks blocked
- [ ] /worker start - already in progress
- [ ] /worker done - mark complete
- [ ] /worker done - show next task
- [ ] /worker done - all tasks done
- [ ] /worker status - basic display
- [ ] /worker status --all - detailed display
- [ ] /worker block - with reason
- [ ] /worker block - without reason (error)
- [ ] Worker ID detection (env var)
- [ ] Worker ID detection (session file)
- [ ] Prompt file discovery
- [ ] Prompt file move on done
- [ ] Progress file update

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
| `hook-config.md` | N/A | Skill 내 Hook 없음 |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | ✅ | Task status + blockedBy management |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Worker self-service commands |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |

---

**End of Skill Documentation**

---
name: worker
description: |
  Worker self-service commands (start, done, status, block).
  Supports Sub-Orchestrator mode for hierarchical task decomposition.

  **V5.0.0 Changes (EFL Integration):**
  - P1: Skill as Sub-Orchestrator (orchestrate, delegate, collect-sub commands)
  - P2: Parallel Agent Configuration (complexity-based subtask delegation)
  - P6: Agent Internal Feedback Loop (max 3 iterations for subtask validation)

user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "5.2.0"
argument-hint: "<start|done|status|block|orchestrate|delegate|collect-sub> [b|c|d|terminal-id] [taskId]"
allowed-tools:
  - Read
  - Write
  - Edit
  - Grep
  - Glob
  - Task
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000

# =============================================================================
# P1: Skill as Sub-Orchestrator (DEFAULT MODE)
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # Always operate as Sub-Orchestrator by default
  max_sub_agents: 3
  delegation_strategy: "complexity-based"
  strategies:
    orchestrate:
      description: "Decompose main task into subtasks for parallel execution"
      use_when: "Task complexity exceeds single-worker capacity"
    delegate:
      description: "Assign subtasks to sub-agents for execution"
      use_when: "Subtasks ready for parallel delegation"
    collect_sub:
      description: "Aggregate sub-agent results into L1 summary"
      use_when: "All subtasks completed"
  slug_orchestration:
    enabled: true
    source: "assigned task or active workload"
    action: "reuse upstream workload context"
  sub_agent_permissions:
    - Read
    - Write
    - Grep
    - Glob
    - Edit
  output_paths:
    l1: ".agent/prompts/{slug}/worker/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/worker/l2_index.md"
    l3: ".agent/prompts/{slug}/worker/l3_details/"
  return_format:
    l1: "Worker execution summary with completion status (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/worker/l2_index.md"
    l3_path: ".agent/prompts/{slug}/worker/l3_details/"
    requires_l2_read: false
    next_action_hint: "/worker done or /collect"
  description: |
    Worker ALWAYS operates as Sub-Orchestrator by default (default_mode: true).
    No --sub-orchestrator flag required. L1 returns to main context; L2/L3 saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # Single subtask
    moderate: 2    # 2-3 subtasks
    complex: 3     # 4+ subtasks
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  subtask_areas:
    - implementation
    - testing
    - documentation
  description: |
    Deploy multiple sub-agents in parallel for complex task execution.
    Agent count scales with detected subtask complexity.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    completeness:
      - "All subtasks identified and decomposed"
      - "Dependencies between subtasks mapped"
      - "Completion criteria defined for each subtask"
    quality:
      - "Subtask descriptions actionable"
      - "Evidence of completion verifiable"
      - "Output artifacts specified"
    internal_consistency:
      - "Parent-child task relationships maintained"
      - "Progress tracking accurate"
      - "L1 summary reflects actual subtask outputs"

hooks:
  Setup:
    - type: command
      command: "/home/palantir/.claude/hooks/worker-preflight.sh"
      timeout: 10000
    - type: command
      command: "source /home/palantir/.claude/skills/shared/validation-feedback-loop.sh"
      timeout: 5000
---

# /worker - Worker Self-Service Commands (EFL V5.0.0)

> **Version:** 5.0.0 (EFL Pattern)
> **Role:** Self-service commands for workers with EFL integration
> **Architecture:** Hybrid (Native Task System + File-Based Prompts)
> **EFL Features:** P1 Sub-Orchestrator, P2 Parallel Agents, P6 Internal Loop
> **Sub-Orchestrator Commands:** orchestrate, delegate, collect-sub

---

## 1. Purpose

**Worker Self-Service Agent** that enables workers to:
1. Claim and start assigned tasks (`/worker start`)
2. Mark tasks as complete (`/worker done`)
3. Check current status and progress (`/worker status`)
4. Report blockers to orchestrator (`/worker block`)
5. **NEW:** Decompose tasks into subtasks (`/worker orchestrate`)
6. **NEW:** Delegate subtasks to sub-agents (`/worker delegate`)
7. **NEW:** Collect and summarize sub-results (`/worker collect-sub`)

### 1.1 Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`

This skill has `agent_delegation.enabled: true` and `default_mode: true` in frontmatter.
**Auto-delegation is ALWAYS active** - the skill automatically operates as Sub-Orchestrator.

```javascript
// =============================================================================
// AUTO-DELEGATION CHECK (Executed at skill invocation)
// =============================================================================
// Reference: .claude/skills/shared/auto-delegation.md

function executeAutoDelegationCheck(userCommand, taskContext) {
  // 1. Read frontmatter config
  const delegationConfig = {
    enabled: true,           // From frontmatter: agent_delegation.enabled
    default_mode: true,      // From frontmatter: agent_delegation.default_mode
    max_sub_agents: 3,       // From frontmatter: agent_delegation.max_sub_agents
    strategy: "complexity-based"  // From frontmatter: agent_delegation.delegation_strategy
  }

  // 2. Check if auto-delegation should trigger
  if (delegationConfig.enabled && delegationConfig.default_mode) {
    console.log(`
=== Auto-Delegation Active ===
Mode: Sub-Orchestrator (default_mode: true)
Strategy: ${delegationConfig.strategy}
Max Sub-Agents: ${delegationConfig.max_sub_agents}
`)

    // 3. For complex tasks, analyze and delegate
    if (isComplexTask(taskContext)) {
      const complexity = analyzeTaskComplexity(taskContext)
      const agentCount = getAgentCountByComplexity(complexity)

      console.log(`Task Complexity: ${complexity} → Deploying ${agentCount} sub-agent(s)`)

      // 4. Execute delegation workflow
      return {
        delegated: true,
        complexity: complexity,
        agentCount: agentCount,
        workflow: "orchestrate → delegate → collect-sub"
      }
    }
  }

  // 5. Simple tasks execute directly (no delegation overhead)
  return { delegated: false, executeDirectly: true }
}

function isComplexTask(taskContext) {
  // Complex if: multiple files, multi-phase, integration required
  const complexityIndicators = [
    taskContext.fileCount > 3,
    taskContext.description?.includes("integration"),
    taskContext.description?.includes("refactor"),
    taskContext.estimatedLines > 200
  ]
  return complexityIndicators.filter(Boolean).length >= 2
}

function analyzeTaskComplexity(taskContext) {
  // Map to complexity levels from parallel_agent_config
  if (taskContext.fileCount > 10) return "complex"
  if (taskContext.fileCount > 5) return "moderate"
  return "simple"
}

function getAgentCountByComplexity(complexity) {
  // From frontmatter: parallel_agent_config.agent_count_by_complexity
  const mapping = { simple: 1, moderate: 2, complex: 3 }
  return mapping[complexity] || 1
}
```

**Auto-Delegation Behavior Summary:**

| Scenario | Behavior |
|----------|----------|
| `/worker start b` (simple task) | Execute directly, no delegation |
| `/worker start b` (complex task) | Auto-suggest: "Use `/worker orchestrate b` to decompose" |
| `/worker orchestrate b` | Decompose → create subtasks → ready for delegation |
| `/worker delegate b` | Assign subtasks to sub-agents |
| `/worker collect-sub b` | Aggregate results → L1 to main, L2/L3 to files |

### 1.2 Workload Context Setup

```javascript
// Source workload management modules (via helper functions)
// getWorkloadProgressPath() - returns workload-scoped or global path
// getActiveWorkloadSlug() - returns current active workload slug

function getWorkloadProgressPath() {
  // Try to get active workload slug
  const workloadSlug = getActiveWorkloadSlug()

  if (workloadSlug) {
    return `.agent/prompts/${workloadSlug}/_progress.yaml`
  }
  // Fallback to global path
  return ".agent/prompts/_progress.yaml"
}
```

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

# Sub-Orchestrator commands (only when assigned with --sub-orchestrator)
/worker orchestrate b    # Decompose current task into subtasks
/worker delegate b       # Delegate subtasks to sub-agents
/worker collect-sub b    # Collect sub-results and generate L1 summary
```

### Arguments

- `$0`: Subcommand (`start`, `done`, `status`, `block`, `orchestrate`, `delegate`, `collect-sub`)
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

  // 4. Generate completion manifest with integrity hashes
  let manifestResult = generateCompletionManifest(currentTask.id, workerId)

  // 5. Update progress file
  updateProgressFile(workerId, currentTask.id, "completed")

  // 6. Calculate progress
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
  // Get active workload to determine search path
  let activeWorkload = Bash(`source .claude/skills/shared/workload-files.sh && get_active_workload`).trim()

  let searchPaths = []

  if (activeWorkload) {
    // Get workload-specific prompt directory
    let workloadSlug = Bash(`source .claude/skills/shared/slug-generator.sh && generate_slug_from_workload "${activeWorkload}"`).trim()
    searchPaths.push(`.agent/prompts/${workloadSlug}/pending`)
  }

  // Fallback to global pending directory for backward compatibility
  searchPaths.push(`.agent/prompts/pending`)

  // Also check all workload directories
  let allWorkloads = Bash(`source .claude/skills/shared/workload-files.sh && list_workloads`).trim().split('\n')
  for (workload of allWorkloads) {
    if (workload && workload !== 'pending' && workload !== 'completed') {
      searchPaths.push(`.agent/prompts/${workload}/pending`)
    }
  }

  // Search in all paths
  for (searchPath of searchPaths) {
    let pendingFiles = Glob(`${searchPath}/*task*.yaml`)

    for (file of pendingFiles) {
      let content = Read(file)
      if (content.includes(`nativeTaskId: "${taskId}"`) ||
          content.includes(`taskId: "${taskId}"`)) {
        return file
      }
    }

    // Check by worker naming convention
    let workerFiles = Glob(`${searchPath}/worker-*-*.yaml`)
    for (file of workerFiles) {
      let content = Read(file)
      if (content.includes(`nativeTaskId: "${taskId}"`)) {
        return file
      }
    }
  }

  return null
}
```

### 5.2 movePromptFile

```javascript
function movePromptFile(taskId, fromDir, toDir) {
  let promptFile = findPromptFile(taskId)

  if (!promptFile) {
    console.log(`ℹ️  No prompt file found for task #${taskId}`)
    return false
  }

  // Extract workload directory from prompt file path
  // Path format: .agent/prompts/{workload-slug}/pending/worker-*.yaml
  let pathParts = promptFile.split('/')
  let workloadDir = pathParts.slice(0, -2).join('/')  // Remove /pending/filename

  // Determine destination directory (within same workload)
  let destDir = `${workloadDir}/${toDir}`

  // Ensure target directory exists
  Bash(`mkdir -p "${destDir}"`)

  let filename = promptFile.split('/').pop()
  let destFile = `${destDir}/${filename}`

  Bash(`mv "${promptFile}" "${destFile}"`)
  console.log(`📁 Moved: ${promptFile} → ${destFile}`)

  return true
}
```

### 5.3 updateProgressFile

```javascript
function updateProgressFile(workerId, taskId, status) {
  // Use workload-scoped progress path (active workload or global fallback)
  let progressPath = getWorkloadProgressPath()

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
  // Use workload-scoped progress path (active workload or global fallback)
  let progressPath = getWorkloadProgressPath()

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

### 5.5 generateCompletionManifest

```javascript
// =============================================================================
// Generate completion manifest with SHA256 hashes for all output files
// Uses semantic-integrity.sh shared module
// =============================================================================
function generateCompletionManifest(taskId, workerId) {
  console.log(`📋 Generating completion manifest for task #${taskId}...`)

  // 1. Get workload context
  let workloadSlug = getActiveWorkloadSlug()
  let outputDir = workloadSlug
    ? `.agent/prompts/${workloadSlug}/outputs/${workerId}`
    : `.agent/outputs/${workerId}`

  // Ensure output directory exists
  Bash(`mkdir -p "${outputDir}"`)

  // 2. Collect output files (all .md files created by this worker)
  let outputFiles = []

  // Check workload-specific outputs
  if (workloadSlug) {
    let workloadOutputs = Glob(`.agent/prompts/${workloadSlug}/outputs/${workerId}/*.md`)
    outputFiles = outputFiles.concat(workloadOutputs)
  }

  // Check global outputs (backward compatibility)
  let globalOutputs = Glob(`.agent/outputs/${workerId}/*.md`)
  outputFiles = outputFiles.concat(globalOutputs)

  // Also check for task-specific outputs
  let taskOutputs = Glob(`.agent/outputs/**/task-${taskId}-*.md`)
  outputFiles = outputFiles.concat(taskOutputs)

  // Deduplicate
  outputFiles = [...new Set(outputFiles)]

  if (outputFiles.length === 0) {
    console.log(`ℹ️  No output files found for task #${taskId}`)
    // Still generate manifest with empty outputs
  }

  // 3. Get upstream orchestrate artifact for context_hash
  let upstreamArtifact = ""
  if (workloadSlug) {
    upstreamArtifact = `.agent/prompts/${workloadSlug}/_context.yaml`
  }

  // 4. Call semantic-integrity.sh to generate manifest
  let outputFilesList = outputFiles.join(',')

  // Use Bash to call the shell function
  let manifestResult = Bash(`
    source .claude/skills/shared/semantic-integrity.sh 2>/dev/null
    generate_worker_manifest "${taskId}" "${workerId}" "${outputFilesList}" "orchestrate" "${upstreamArtifact}"
  `)

  let manifestPath = manifestResult.trim()

  if (manifestPath && !manifestPath.startsWith("ERROR")) {
    console.log(`✅ Manifest generated: ${manifestPath}`)

    // Log manifest summary
    let fileCount = outputFiles.length
    console.log(`   📁 Output files tracked: ${fileCount}`)

    if (upstreamArtifact) {
      console.log(`   🔗 Upstream context: ${upstreamArtifact}`)
    }

    return {
      success: true,
      manifestPath: manifestPath,
      outputFiles: outputFiles,
      fileCount: fileCount
    }
  } else {
    console.log(`⚠️  Manifest generation failed: ${manifestResult}`)
    return {
      success: false,
      error: manifestResult
    }
  }
}
```

### 5.6 extractInstructions

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

## 5.5. Sub-Orchestrator Functions

### 5.5.1 workerOrchestrate

```javascript
function workerOrchestrate(specificTaskId = null) {
  let workerId = getWorkerId()
  console.log(`🔧 Sub-Orchestrator ${workerId}: Decomposing task...`)

  // 1. Get current task
  let task = getCurrentTask(specificTaskId)
  if (!task) {
    console.log(`❌ No task to decompose`)
    return { status: "no_task" }
  }

  // 2. Check if Sub-Orchestrator mode is enabled
  // V5.1.0: Respect default_mode setting from skill config
  // If default_mode is true, always enable Sub-Orchestrator
  // Otherwise, check task metadata for explicit flag
  const defaultModeEnabled = true  // Set by agent_delegation.default_mode in frontmatter

  if (!defaultModeEnabled && !task.metadata?.subOrchestratorMode) {
    console.log(`❌ Sub-Orchestrator mode not enabled for this task`)
    console.log(`   Use: /assign ${task.id} ${workerId} --sub-orchestrator`)
    return { status: "mode_disabled" }
  }

  // Sub-Orchestrator always active when default_mode: true
  console.log(`✅ Sub-Orchestrator mode active (default_mode: ${defaultModeEnabled})`)

  // 3. Read task details and prompt
  let taskDetail = TaskGet({taskId: task.id})
  console.log(`
📋 Task to Decompose:
   ID: #${task.id}
   Subject: ${taskDetail.subject}
   Description: ${taskDetail.description}
`)

  // 4. Delegate to /orchestrate skill
  console.log(`\n🚀 Launching /orchestrate for task decomposition...`)
  console.log(`   Hierarchy Level: ${task.metadata.hierarchyLevel + 1}`)

  // Store parent task context
  let contextFile = `.agent/tmp/suborchestrator-context-${workerId}.json`
  Write({
    file_path: contextFile,
    content: JSON.stringify({
      parentTaskId: task.id,
      parentWorkerId: workerId,
      hierarchyLevel: task.metadata.hierarchyLevel + 1,
      timestamp: new Date().toISOString()
    }, null, 2)
  })

  console.log(`
✅ Ready to decompose task #${task.id}

Next Step:
  Run /orchestrate with your task breakdown
  Example: /orchestrate "Break down ${taskDetail.subject} into subtasks"

  Subtasks will be created with:
  - hierarchyLevel: ${task.metadata.hierarchyLevel + 1}
  - Parent: Task #${task.id}
`)

  return {
    status: "ready_to_orchestrate",
    taskId: task.id,
    hierarchyLevel: task.metadata.hierarchyLevel + 1
  }
}
```

### 5.5.2 workerDelegate

```javascript
function workerDelegate(specificTaskId = null) {
  let workerId = getWorkerId()
  console.log(`📤 Sub-Orchestrator ${workerId}: Delegating subtasks...`)

  // 1. Get current task
  let task = getCurrentTask(specificTaskId)
  if (!task) {
    console.log(`❌ No task found`)
    return { status: "no_task" }
  }

  // 2. Find subtasks (created by this worker's /orchestrate)
  let allTasks = TaskList()
  let subtasks = allTasks.filter(t =>
    t.metadata?.hierarchyLevel === (task.metadata?.hierarchyLevel || 0) + 1 &&
    t.metadata?.parentTaskId === task.id
  )

  if (subtasks.length === 0) {
    console.log(`❌ No subtasks found for Task #${task.id}`)
    console.log(`   Run /worker orchestrate first to create subtasks`)
    return { status: "no_subtasks" }
  }

  console.log(`
Found ${subtasks.length} subtasks to delegate:
${subtasks.map(st => `  - Task #${st.id}: ${st.subject}`).join('\n')}
`)

  // 3. Auto-assign subtasks
  console.log(`\n🔄 Auto-assigning subtasks...`)

  // Use /assign auto for subtasks
  console.log(`
Next Step:
  Use /assign to delegate subtasks:

  Option 1 (Auto):
    /assign auto

  Option 2 (Manual):
${subtasks.map((st, i) => `    /assign ${st.id} terminal-${String.fromCharCode(98 + i)}`).join('\n')}
`)

  return {
    status: "ready_to_delegate",
    subtaskCount: subtasks.length,
    subtasks: subtasks.map(st => st.id)
  }
}
```

### 5.5.3 workerCollectSub

```javascript
function workerCollectSub(specificTaskId = null) {
  let workerId = getWorkerId()
  console.log(`📥 Sub-Orchestrator ${workerId}: Collecting sub-results...`)

  // 1. Get current task
  let task = getCurrentTask(specificTaskId)
  if (!task) {
    console.log(`❌ No task found`)
    return { status: "no_task" }
  }

  // 2. Find subtasks
  let allTasks = TaskList()
  let subtasks = allTasks.filter(t =>
    t.metadata?.hierarchyLevel === (task.metadata?.hierarchyLevel || 0) + 1 &&
    t.metadata?.parentTaskId === task.id
  )

  if (subtasks.length === 0) {
    console.log(`❌ No subtasks found for Task #${task.id}`)
    return { status: "no_subtasks" }
  }

  // 3. Check completion status
  let completedSubtasks = subtasks.filter(st => st.status === "completed")
  let pendingSubtasks = subtasks.filter(st => st.status !== "completed")

  console.log(`
📊 Subtask Status:
   Total: ${subtasks.length}
   Completed: ${completedSubtasks.length}
   Pending: ${pendingSubtasks.length}
`)

  if (pendingSubtasks.length > 0) {
    console.log(`
⏸️  Cannot collect - pending subtasks:
${pendingSubtasks.map(st => `  - Task #${st.id}: ${st.subject} (${st.status})`).join('\n')}

Wait for all subtasks to complete before collecting.
`)
    return { status: "pending_subtasks", pending: pendingSubtasks.length }
  }

  // 4. Collect L2/L3 results from subtasks
  console.log(`\n📚 Collecting detailed results (L2/L3)...`)

  let l2Results = []
  let l3Results = []

  for (subtask of completedSubtasks) {
    let subtaskDetail = TaskGet({taskId: subtask.id})

    // Collect L2 (summary) and L3 (full details)
    l2Results.push({
      taskId: subtask.id,
      subject: subtaskDetail.subject,
      summary: subtaskDetail.description || "No summary available"
    })

    // L3: Full output files if available
    let outputPattern = `.agent/outputs/**/task-${subtask.id}-*.md`
    let outputFiles = Glob(outputPattern)

    if (outputFiles.length > 0) {
      let fullContent = Read(outputFiles[0])
      l3Results.push({
        taskId: subtask.id,
        file: outputFiles[0],
        content: fullContent
      })
    }
  }

  // 5. Generate L1 summary
  console.log(`\n✍️  Generating L1 summary for main orchestrator...`)

  let l1Summary = `# Task #${task.id} Completion Summary (L1)

## Overview
Completed ${completedSubtasks.length} subtasks via Sub-Orchestrator decomposition.

## Results Summary
${l2Results.map((r, i) => `
### Subtask ${i + 1}: ${r.subject}
${r.summary}
`).join('\n')}

## Detailed Reports
- L2 (Summaries): ${workloadSlug}/outputs/${workerId}/task-${task.id}-l2-summaries.md
- L3 (Full Details): ${workloadSlug}/outputs/${workerId}/task-${task.id}-l3-details.md

Generated: ${new Date().toISOString()}
`

  // 6. Save L1/L2/L3 to files (Workload-scoped)
  let workloadSlug = await getActiveWorkload() || 'global'
  let outputDir = `.agent/prompts/${workloadSlug}/outputs/${workerId}`
  Bash(`mkdir -p ${outputDir}`)

  // L1: Summary for main orchestrator
  let l1File = `${outputDir}/task-${task.id}-l1-summary.md`
  Write({ file_path: l1File, content: l1Summary })

  // L2: Subtask summaries
  let l2Content = l2Results.map(r => `## Task #${r.taskId}: ${r.subject}\n${r.summary}`).join('\n\n')
  let l2File = `${outputDir}/task-${task.id}-l2-summaries.md`
  Write({ file_path: l2File, content: l2Content })

  // L3: Full details
  let l3Content = l3Results.map(r => `## Task #${r.taskId}\nFile: ${r.file}\n\n${r.content}`).join('\n\n---\n\n')
  let l3File = `${outputDir}/task-${task.id}-l3-details.md`
  Write({ file_path: l3File, content: l3Content })

  // 7. Context Pollution Prevention - Validate L1 before returning
  let l1Validation = validateL1Summary(l1Summary)

  if (!l1Validation.isValid) {
    console.log(`\n⚠️  Context Pollution Prevention Triggered:`)
    l1Validation.warnings.forEach(w => console.log(`  ${w}`))

    // Sanitize L1 to prevent context overflow
    l1Summary = sanitizeL1Summary(l1Summary)
    Write({ file_path: l1File, content: l1Summary })  // Update sanitized version
    console.log(`  ✅ L1 sanitized and saved`)
  }

  console.log(`
✅ Collection Complete!

Files Generated:
  📄 L1 (Summary for Main): ${l1File} (${l1Validation.estimatedTokens} tokens)
  📄 L2 (Subtask Summaries): ${l2File}
  📄 L3 (Full Details): ${l3File}

Context Pollution Check: ${l1Validation.isValid ? '✅ PASSED' : '⚠️ SANITIZED'}

Next Step:
  /worker done ${task.id}  # Mark parent task as complete
`)

  // 8. Return safe result (only L1 reference, no L2/L3 content)
  return preventContextPollution({
    status: "collected",
    taskId: task.id,
    subtaskCount: completedSubtasks.length,
    files: { l1: l1File, l2: l2File, l3: l3File }
  })
}
```

### 5.5.4 getCurrentTask (Helper)

```javascript
function getCurrentTask(specificTaskId = null) {
  let workerId = getWorkerId()
  let myTasks = getMyTasks()

  if (specificTaskId) {
    return myTasks.find(t => t.id === specificTaskId)
  }

  // Get current in-progress task or first pending task
  let inProgress = myTasks.find(t => t.status === "in_progress")
  if (inProgress) return inProgress

  let pending = myTasks.find(t => t.status === "pending")
  return pending
}
```

### 5.5.5 Context Pollution Prevention (Helper)

```javascript
// =============================================================================
// Context Pollution Prevention
// =============================================================================
// Ensures L2/L3 content never leaks to Main Agent context
// Validates L1 summary size and content

const L1_MAX_TOKENS = 500       // Max tokens for L1 summary
const L1_MAX_CHARS = 2000       // Approximate char limit (4 chars/token)
const FORBIDDEN_L2L3_PATTERNS = [
  /## Task #\d+\n.*\n.*\n/gm,   // Full task details
  /```[\s\S]{500,}```/gm,       // Large code blocks
  /File:.*\.md\n\n[\s\S]+/gm    // File content dumps
]

function validateL1Summary(l1Summary) {
  let warnings = []
  let isValid = true

  // 1. Check length
  if (l1Summary.length > L1_MAX_CHARS) {
    warnings.push(`⚠️  L1 exceeds ${L1_MAX_CHARS} chars (${l1Summary.length} chars)`)
    isValid = false
  }

  // 2. Check for L2/L3 content patterns
  for (let pattern of FORBIDDEN_L2L3_PATTERNS) {
    if (pattern.test(l1Summary)) {
      warnings.push(`⚠️  L1 contains L2/L3 pattern: ${pattern.source.substring(0, 30)}...`)
      isValid = false
    }
  }

  // 3. Estimate token count (rough approximation)
  let estimatedTokens = Math.ceil(l1Summary.length / 4)
  if (estimatedTokens > L1_MAX_TOKENS) {
    warnings.push(`⚠️  Estimated tokens (${estimatedTokens}) exceeds limit (${L1_MAX_TOKENS})`)
    isValid = false
  }

  return { isValid, warnings, estimatedTokens }
}

function sanitizeL1Summary(l1Summary) {
  let sanitized = l1Summary

  // Remove large code blocks (keep only first 200 chars)
  sanitized = sanitized.replace(/```[\s\S]{200,}```/gm, '```[truncated]```')

  // Remove file content dumps
  sanitized = sanitized.replace(/File:.*\.md\n\n[\s\S]+/gm, '[File content stored in L3]')

  // Truncate if still too long
  if (sanitized.length > L1_MAX_CHARS) {
    sanitized = sanitized.substring(0, L1_MAX_CHARS - 50) + '\n\n[Truncated - see L2/L3 for details]'
  }

  return sanitized
}

function preventContextPollution(collectResult) {
  // Ensure only L1 reference is returned, never actual L2/L3 content
  let safeResult = {
    status: collectResult.status,
    taskId: collectResult.taskId,
    subtaskCount: collectResult.subtaskCount,
    // Only return file paths, not content
    l1File: collectResult.files?.l1 || null,
    l2File: collectResult.files?.l2 || null,  // Path only
    l3File: collectResult.files?.l3 || null,  // Path only
    // Validation metadata
    contextPollutionCheck: "passed",
    timestamp: new Date().toISOString()
  }

  // Never include: l2Content, l3Content, raw subtask details
  delete safeResult.l2Content
  delete safeResult.l3Content
  delete safeResult.subtaskDetails

  return safeResult
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

    case 'orchestrate':
      // /worker orchestrate b [taskId]
      let orchTerminalId = parseTerminalId(param1)
      let orchTaskId = null

      if (orchTerminalId) {
        setWorkerId(orchTerminalId)
        orchTaskId = isTaskId(param2) ? param2 : null
      } else if (isTaskId(param1)) {
        orchTaskId = param1
      }

      return workerOrchestrate(orchTaskId)

    case 'delegate':
      // /worker delegate b [taskId]
      let delegateTerminalId = parseTerminalId(param1)
      let delegateTaskId = null

      if (delegateTerminalId) {
        setWorkerId(delegateTerminalId)
        delegateTaskId = isTaskId(param2) ? param2 : null
      } else if (isTaskId(param1)) {
        delegateTaskId = param1
      }

      return workerDelegate(delegateTaskId)

    case 'collect-sub':
      // /worker collect-sub b [taskId]
      let collectTerminalId = parseTerminalId(param1)
      let collectTaskId = null

      if (collectTerminalId) {
        setWorkerId(collectTerminalId)
        collectTaskId = isTaskId(param2) ? param2 : null
      } else if (isTaskId(param1)) {
        collectTaskId = param1
      }

      return workerCollectSub(collectTaskId)

    default:
      console.log(`
=== /worker - Self-Service Commands ===

Basic Commands:
  /worker start <b|c|d> [taskId]     Start as terminal-X (RECOMMENDED)
  /worker start [taskId]             Start assigned task
  /worker done [taskId]              Mark task as complete
  /worker status [b|c|d] [--all]     Show current status
  /worker block "reason"             Report a blocker

Sub-Orchestrator Commands (when enabled):
  /worker orchestrate <b|c|d>        Decompose task into subtasks
  /worker delegate <b|c|d>           Delegate subtasks to sub-agents
  /worker collect-sub <b|c|d>        Collect sub-results (L1 summary)

Terminal Shortcuts:
  b = terminal-b, c = terminal-c, d = terminal-d

Examples:
  /worker start b                    Start as terminal-b
  /worker start b 16                 Start terminal-b on task #16
  /worker orchestrate b              Decompose current task (Sub-Orchestrator)
  /worker delegate b                 Delegate subtasks
  /worker collect-sub b              Collect and summarize
  /worker done                       Complete current task
  /worker status b --all             Show all terminal-b tasks
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

**Context Pollution Prevention (NEW v3.2):**
- [ ] validateL1Summary detects oversized L1
- [ ] validateL1Summary detects L2/L3 content patterns
- [ ] sanitizeL1Summary truncates large L1 content
- [ ] sanitizeL1Summary removes code block dumps
- [ ] preventContextPollution returns only file paths
- [ ] collect-sub never returns raw L2/L3 content
- [ ] L1 token estimate stays under 500

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
| 3.2.0 | Context Pollution Prevention: L1 검증, sanitize, L2/L3 격리 |
| 4.0.0 | Semantic Integrity Manifest: /worker done 시 SHA256 해시 manifest 자동 생성, Sub-Orchestrator 통합 |
| 5.0.0 | EFL Pattern Integration: P1 Sub-Orchestrator, P2 Parallel Agents, P6 Internal Loop |
| 5.1.0 | Default Sub-Orchestrator Mode: default_mode: true 설정으로 항상 Sub-Orchestrator 활성화 |
| 5.2.0 | Auto-Delegation Trigger: Shared module integration (.claude/skills/shared/auto-delegation.md), explicit auto-trigger logic in skill body |

---

**End of Skill Documentation**

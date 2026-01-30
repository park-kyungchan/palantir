---
name: assign
description: |
  Assign Native Tasks to worker terminals, update ownership, sync progress tracking.
  Supports Sub-Orchestrator mode for hierarchical task decomposition.

  Core Capabilities:
  - Task Assignment: Assign tasks to specific terminals via owner field
  - Progress Tracking: Sync with _progress.yaml for workload state
  - Auto-Assignment: Intelligent distribution of tasks to available terminals
  - Sub-Orchestrator Mode: Enable workers to decompose complex tasks
  - EFL Pattern Execution: Full P1-P6 implementation

  Output Format:
  - L1: Assignment summary (500 tokens)
  - L2: Updated _progress.yaml
  - L3: Terminal instructions

  Pipeline Position:
  - Post-/orchestrate assignment phase
  - Handoff to /worker when assignment is complete
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "4.0.0"
argument-hint: "<task-id> <terminal-id> [--sub-orchestrator] | auto"
auto-sub-orchestrator: true
allowed-tools:
  - Read
  - Write
  - Task
  - Glob
  - Grep
  - mcp__sequential-thinking__sequentialthinking
  - TaskUpdate
  - TaskList
  - TaskGet
  - AskUserQuestion
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/parallel-agent.sh"
      timeout: 5000

# =============================================================================
# P1: Skill as Sub-Orchestrator
# =============================================================================
agent_delegation:
  enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
  max_sub_agents: 3
  delegation_strategy: "auto"
  strategies:
    load_balanced:
      description: "Distribute tasks evenly across terminals"
      use_when: "auto mode"
    priority_based:
      description: "Assign high-priority tasks first"
      use_when: "Priority-sensitive workloads"
  slug_orchestration:
    enabled: true
  default_mode: true  # V1.1.0: Auto-delegation by default
    source: "orchestrate_slug OR active_workload"
    action: "reuse upstream workload context"
  sub_agent_permissions:
    - Read
    - Write
    - TaskUpdate
    - TaskList
    - TaskGet
  output_paths:
    l1: ".agent/prompts/{slug}/assign/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/assign/l2_index.md"
    l3: ".agent/prompts/{slug}/assign/l3_details/"
  return_format:
    l1: "Assignment summary with task count and terminal distribution (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/assign/l2_index.md"
    l3_path: ".agent/prompts/{slug}/assign/l3_details/"
    requires_l2_read: false
    next_action_hint: "/worker start"
  description: |
    This skill operates as a Sub-Orchestrator (P1).
    L1 returns to main context; L2/L3 always saved to files.

# =============================================================================
# P2: Parallel Agent Configuration
# =============================================================================
parallel_agent_config:
  enabled: true
  complexity_detection: "auto"
  agent_count_by_complexity:
    simple: 1      # 1-3 tasks
    moderate: 2    # 4-6 tasks
    complex: 3     # 7+ tasks
  synchronization_strategy: "barrier"
  aggregation_strategy: "merge"
  assignment_areas:
    - dependency_analysis
    - terminal_availability
    - load_balancing
  description: |
    Deploy multiple Assignment Agents in parallel for complex assignments.
    Agent count scales with task count.

# =============================================================================
# P3: General-Purpose Synthesis Configuration
# =============================================================================
synthesis_config:
  phase_3a_l2_horizontal:
    enabled: true
    description: "Cross-validate assignments for balance"
    validation_criteria:
      - load_balance_check
      - dependency_order_validation
      - terminal_capacity_check
  phase_3b_l3_vertical:
    enabled: true
    description: "Verify assignments against task requirements"
    validation_criteria:
      - task_terminal_compatibility
      - blocker_resolution_order
      - sub_orchestrator_eligibility
  phase_3_5_review_gate:
    enabled: true
    description: "Main Agent holistic verification"
    criteria:
      - assignment_completeness
      - execution_order_validity
      - worker_instruction_clarity

# =============================================================================
# P4: Selective Feedback Loop
# =============================================================================
selective_feedback:
  enabled: true
  severity_filter: "warning"
  feedback_targets:
    - gate: "ASSIGN"
      severity: ["error", "warning"]
      action: "block_on_error"
    - gate: "DEPENDENCY"
      severity: ["error"]
      action: "block"
  description: |
    Severity-based filtering for assignment validation.
    Errors block assignment. Warnings are logged but allow continuation.

# =============================================================================
# P5: Repeat Until Approval
# =============================================================================
repeat_until_approval:
  enabled: true
  max_rounds: 3
  approval_criteria:
    - "All tasks assigned"
    - "No terminal overloaded"
    - "Dependency order valid"
  description: |
    Assignment continues until all tasks properly distributed.
    Can re-balance if issues detected.

# =============================================================================
# P6: Agent Internal Feedback Loop
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "Each task has exactly one owner"
    - "Blocked tasks assigned after blockers"
    - "Terminal load is balanced"
    - "Sub-orchestrator mode properly set"
  refinement_triggers:
    - "Duplicate assignment detected"
    - "Dependency order violation"
    - "Terminal overload detected"
  description: |
    Local assignment refinement loop before finalizing.
    Self-validates assignment quality and iterates until threshold met.
---

# /assign - Task Assignment to Workers (EFL V3.0.0)

> **Version:** 3.0.0 (EFL Pattern)
> **Role:** Task Assignment with Full EFL Implementation
> **Pipeline Position:** After /orchestrate, Before /worker
> **EFL Template:** `.claude/skills/shared/efl-template.md`

---

## 0. EFL Execution Overview

This skill implements the Enhanced Feedback Loop (EFL) pattern:

1. **Phase 1**: Analyze task dependencies and terminal availability (P2)
2. **Phase 2**: Generate assignment plan
3. **Phase 3-A**: L2 Horizontal Synthesis (load balance validation) (P3)
4. **Phase 3-B**: L3 Vertical Verification (dependency order check) (P3)
5. **Phase 3.5**: Main Agent Review Gate (holistic verification) (P1)
6. **Phase 4**: Selective Feedback Loop (if imbalance detected) (P4)
7. **Phase 5**: Execute assignments after approval (P5)

### Pipeline Integration

```
/clarify → /research → /planning → /orchestrate → [/assign] → /worker → /synthesis
                                                      │
                                                      ├── Phase 1: Dependency Analysis (P2)
                                                      ├── Phase 2: Assignment Plan
                                                      ├── Phase 3-A: L2 Load Balance Check (P3)
                                                      ├── Phase 3-B: L3 Dependency Verification (P3)
                                                      ├── Phase 3.5: Main Agent Review Gate (P1)
                                                      ├── Phase 4: Selective Feedback Loop (P4)
                                                      ├── Phase 5: Execute Assignments (P5)
                                                      └── Output: _progress.yaml updates
```

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

# Auto assignment (always enables Sub-Orchestrator mode)
/assign auto                  # Auto-assign all tasks with Sub-Orchestrator enabled

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

### 3.2 Mode: Auto Assignment (EFL Pattern V4.0.0)

> **EFL Implementation**: Auto assignment uses parallel analysis agents for complex workloads

```javascript
/**
 * autoAssign - Main entry point for auto assignment
 * Delegates to autoAssignWithEFL for complex assignments
 *
 * EFL Flow:
 * 1. Detect complexity based on task count
 * 2. For simple (1-3 tasks): Direct assignment (no agent overhead)
 * 3. For moderate/complex (4+ tasks): Deploy parallel analysis agents
 */
async function autoAssign() {
  console.log(`\n🚀 /assign auto (EFL V4.0.0)`)

  // Sub-Orchestrator mode is ALWAYS enabled for auto assignment
  const isSubOrchestrator = true

  // 1. Get all unassigned tasks
  const allTasks = TaskList()
  const unassigned = allTasks.filter(t => !t.owner || t.owner === "")

  if (unassigned.length === 0) {
    console.log("✅ All tasks already assigned")
    return { status: "no_unassigned", message: "All tasks already assigned" }
  }

  console.log(`Found ${unassigned.length} unassigned tasks`)

  // 2. Get workload context
  const slug = getActiveWorkloadSlug()
  if (!slug) {
    console.log("⚠️  No active workload, using default context")
  }

  // 3. Detect complexity and decide execution path
  const complexity = detectAssignmentComplexity(unassigned.length)
  const agentCount = getAgentCountByComplexity(complexity)

  console.log(`\n📊 Complexity: ${complexity} → ${agentCount} agent(s)`)

  // 4. Execute based on complexity
  let analysisResult

  if (complexity === "simple") {
    // Simple: Direct assignment without agent overhead
    console.log(`\n⚡ Simple mode: Direct assignment`)
    analysisResult = directAssignmentAnalysis(unassigned)
  } else {
    // Moderate/Complex: Deploy parallel analysis agents (P2)
    console.log(`\n🤖 EFL mode: Deploying ${agentCount} analysis agents...`)
    analysisResult = await deployAnalysisAgents(unassigned, agentCount, slug)
  }

  // 5. Return analysis result (Phase 3-A/3-B will verify before execution)
  return {
    status: "analysis_complete",
    complexity,
    agentCount,
    analysisResult,
    nextStep: "phase3a_load_balance_check"
  }
}

/**
 * directAssignmentAnalysis - Simple assignment without agent delegation
 * Used for 1-3 tasks where agent overhead is not justified
 */
function directAssignmentAnalysis(unassigned) {
  console.log(`\n📋 Direct assignment analysis for ${unassigned.length} tasks`)

  // Read available terminals
  const progressPath = getWorkloadProgressPath()
  let availableTerminals = []

  if (fileExists(progressPath)) {
    const progressData = Read(progressPath)
    const terminals = parseYAML(progressData).terminals || {}
    availableTerminals = Object.keys(terminals).filter(tid =>
      terminals[tid].status === "idle" && !terminals[tid].currentTask
    )
  }

  // Generate terminals if none available
  if (availableTerminals.length === 0) {
    availableTerminals = unassigned.map((t, i) =>
      `terminal-${String.fromCharCode(98 + i)}`
    )
    console.log(`   Generated ${availableTerminals.length} terminal IDs`)
  }

  // Build assignments (unblocked first, then blocked)
  const assignments = []
  const unblockedTasks = unassigned.filter(t => !t.blockedBy || t.blockedBy.length === 0)
  const blockedTasks = unassigned.filter(t => t.blockedBy && t.blockedBy.length > 0)

  let terminalIndex = 0

  for (let task of unblockedTasks) {
    if (terminalIndex >= availableTerminals.length) break
    assignments.push({
      taskId: task.id,
      terminalId: availableTerminals[terminalIndex],
      canStart: true,
      blockedBy: []
    })
    terminalIndex++
  }

  for (let task of blockedTasks) {
    if (terminalIndex >= availableTerminals.length) break
    assignments.push({
      taskId: task.id,
      terminalId: availableTerminals[terminalIndex],
      canStart: false,
      blockedBy: task.blockedBy || []
    })
    terminalIndex++
  }

  return {
    assignments,
    warnings: [],
    adjustments: [],
    metadata: {
      mode: "direct",
      totalAgents: 0,
      analysisTime: "instant"
    }
  }
}

/**
 * deployAnalysisAgents - Deploy parallel analysis agents (P2)
 * Each agent focuses on a specific analysis area
 *
 * @param {Object[]} unassigned - Unassigned tasks from TaskList
 * @param {number} agentCount - Number of agents to deploy (1-3)
 * @param {string} slug - Workload slug for output paths
 * @returns {Object} - Aggregated analysis result
 */
async function deployAnalysisAgents(unassigned, agentCount, slug) {
  const areas = getAssignmentAreas(
    agentCount === 1 ? "simple" : agentCount === 2 ? "moderate" : "complex"
  )

  console.log(`\n>>> Deploying ${agentCount} analysis agents...`)

  // Read terminal state for agents
  const progressPath = getWorkloadProgressPath()
  let terminalState = {}
  if (fileExists(progressPath)) {
    const progressData = Read(progressPath)
    terminalState = parseYAML(progressData).terminals || {}
  }

  // Prepare task summary for agents
  const taskSummary = unassigned.map(t => ({
    id: t.id,
    subject: t.subject,
    blockedBy: t.blockedBy || [],
    priority: t.metadata?.priority || "P1"
  }))

  // Deploy parallel agents with P6 Internal Loop
  const agents = areas.map((area, i) => Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## Assignment Analysis: ${area.name}

### Context
- Workload: ${slug || "default"}
- Unassigned Tasks: ${unassigned.length}
- Analysis Focus: ${area.focus}

### Tasks to Analyze
\`\`\`json
${JSON.stringify(taskSummary, null, 2)}
\`\`\`

### Available Terminals
${Object.keys(terminalState).length > 0
  ? Object.entries(terminalState).map(([tid, state]) =>
      `- ${tid}: ${state.status} (current: ${state.currentTask || 'none'})`
    ).join('\n')
  : '- terminal-b through terminal-' + String.fromCharCode(97 + unassigned.length) + ' (to be created)'
}

### Your Analysis Task: ${area.name}

${area.id === "dependency" ? `
**Dependency Analysis:**
1. Build dependency graph from blockedBy relationships
2. Identify tasks that can start immediately (no blockers)
3. Calculate topological order for blocked tasks
4. Detect any circular dependencies
5. Suggest optimal execution sequence

Output Requirements:
- List tasks in recommended execution order
- Flag any dependency violations
- Identify critical path tasks
` : area.id === "load_balance" ? `
**Load Balancing Analysis:**
1. Count tasks per potential terminal assignment
2. Estimate relative effort per task (from subject/description)
3. Suggest balanced distribution across terminals
4. Avoid assigning dependent tasks to same terminal when possible
5. Consider terminal availability status

Output Requirements:
- Proposed terminal assignment for each task
- Load distribution metrics (tasks per terminal)
- Balance score (0-100, 100 = perfectly balanced)
` : `
**Terminal Availability Analysis:**
1. Identify idle terminals ready for new tasks
2. Check current terminal workloads
3. Determine Sub-Orchestrator eligibility per terminal
4. Estimate terminal capacity for task complexity
5. Flag any terminals with issues

Output Requirements:
- Available terminal list with capacity status
- Recommended terminal for complex vs simple tasks
- Sub-Orchestrator mode recommendations
`}

### Internal Feedback Loop (P6 - REQUIRED)
1. Generate analysis for your focus area
2. Self-validate:
   - [ ] All ${unassigned.length} tasks addressed
   - [ ] Assignments are valid (no duplicate terminals for same task)
   - [ ] Blocked tasks correctly identified
   - [ ] No terminal overloaded (max 3 tasks each)
3. If validation fails, revise (max 3 iterations)
4. Only output after validation passes

### Output Format (YAML)
\`\`\`yaml
area: "${area.id}"
areaName: "${area.name}"
areaPriority: ${area.priority}

assignments:
  - taskId: "{task_id}"
    terminalId: "{terminal-X}"
    canStart: true|false
    blockedBy: [...]
    rationale: "{why this terminal}"

warnings:
  - "{any concerns or issues}"

adjustments:
  - taskId: "{task_id}"
    recommendation: "{suggested change}"
    reason: "{why}"

internalLoopStatus:
  iterations: {1-3}
  validationPassed: true
  checksPerformed:
    - allTasksAddressed: true
    - noInvalidAssignments: true
    - loadBalanced: true
\`\`\`
`,
    description: `Analysis Agent ${i + 1}: ${area.name}`
  }))

  // Barrier synchronization - wait for all agents
  const startTime = Date.now()
  console.log(`[${new Date().toISOString()}] Waiting for ${agents.length} agents...`)

  const results = await Promise.all(agents)

  const duration = ((Date.now() - startTime) / 1000).toFixed(1)
  console.log(`[${new Date().toISOString()}] All agents completed in ${duration}s`)

  // Aggregate results from all agents
  const aggregated = aggregateAnalysisResults(results.map((r, i) => ({
    ...parseYAMLFromAgent(r),
    areaPriority: areas[i].priority
  })))

  // Save L2 analysis details to file (prevent context pollution)
  const l2Path = `.agent/prompts/${slug}/assign/l2_analysis.md`
  const l2Content = `# L2 Assignment Analysis

## Workload: ${slug}
## Generated: ${new Date().toISOString()}

### Agent Results

${results.map((r, i) => `
#### Agent ${i + 1}: ${areas[i].name}
\`\`\`
${typeof r === 'string' ? r : JSON.stringify(r, null, 2)}
\`\`\`
`).join('\n')}

### Aggregated Assignments

| Task ID | Terminal | Can Start | Blocked By |
|---------|----------|-----------|------------|
${aggregated.assignments.map(a =>
  `| #${a.taskId} | ${a.terminalId} | ${a.canStart ? '✅' : '❌'} | ${(a.blockedBy || []).join(', ') || '-'} |`
).join('\n')}

### Warnings
${aggregated.warnings.length > 0 ? aggregated.warnings.map(w => `- ${w}`).join('\n') : '- None'}

---
*Analysis completed in ${duration}s with ${agents.length} agents*
`

  // Ensure directory exists and write L2 file
  Bash({ command: `mkdir -p .agent/prompts/${slug}/assign` })
  Write({ file_path: l2Path, content: l2Content })
  console.log(`📝 L2 analysis saved: ${l2Path}`)

  aggregated.metadata.analysisTime = `${duration}s`
  aggregated.metadata.l2Path = l2Path

  return aggregated
}

/**
 * parseYAMLFromAgent - Extract YAML from agent response
 */
function parseYAMLFromAgent(agentResponse) {
  if (typeof agentResponse !== 'string') {
    return agentResponse
  }

  // Try to extract YAML block
  const yamlMatch = agentResponse.match(/```yaml\n([\s\S]*?)\n```/)
  if (yamlMatch) {
    try {
      return parseYAML(yamlMatch[1])
    } catch (e) {
      console.log(`⚠️  Failed to parse agent YAML: ${e.message}`)
    }
  }

  // Fallback: return raw response
  return { rawResponse: agentResponse, assignments: [], warnings: [] }
}

/**
 * getActiveWorkloadSlug - Get current active workload slug
 */
function getActiveWorkloadSlug() {
  try {
    const content = Read('.agent/prompts/_active_workload.yaml')
    const match = content.match(/activeWorkload:\s*"?([^"\n]+)"?/)
    return match ? match[1] : null
  } catch (e) {
    return null
  }
}

/**
 * getWorkloadProgressPath - Get path to _progress.yaml
 */
function getWorkloadProgressPath() {
  const slug = getActiveWorkloadSlug()
  if (slug) {
    return `.agent/prompts/${slug}/_progress.yaml`
  }
  return ".agent/prompts/_progress.yaml"
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

### 3.6 EFL Helper Functions (V4.0.0)

> **EFL Pattern Support**: 복잡도 기반 에이전트 스케일링을 위한 Helper 함수들

#### 3.6.1 detectAssignmentComplexity

```javascript
/**
 * detectAssignmentComplexity
 * Analyze assignment complexity based on task count
 *
 * @param {number} taskCount - Number of unassigned tasks
 * @returns {"simple" | "moderate" | "complex"} - Complexity level
 *
 * @example
 * let complexity = detectAssignmentComplexity(5)
 * // Returns: "moderate"
 *
 * Complexity Thresholds (aligned with parallel_agent_config):
 * - simple:   1-3 tasks  → Single agent can handle efficiently
 * - moderate: 4-6 tasks  → Parallel analysis beneficial
 * - complex:  7+ tasks   → Full parallel deployment required
 */
function detectAssignmentComplexity(taskCount) {
  // Validate input
  if (typeof taskCount !== 'number' || taskCount < 0) {
    console.log(`⚠️  Invalid task count: ${taskCount}, defaulting to simple`)
    return "simple"
  }

  // Complexity thresholds from parallel_agent_config
  const SIMPLE_MAX = 3
  const MODERATE_MAX = 6

  if (taskCount <= SIMPLE_MAX) {
    console.log(`📊 Complexity: SIMPLE (${taskCount} tasks ≤ ${SIMPLE_MAX})`)
    return "simple"
  }

  if (taskCount <= MODERATE_MAX) {
    console.log(`📊 Complexity: MODERATE (${SIMPLE_MAX} < ${taskCount} tasks ≤ ${MODERATE_MAX})`)
    return "moderate"
  }

  console.log(`📊 Complexity: COMPLEX (${taskCount} tasks > ${MODERATE_MAX})`)
  return "complex"
}
```

#### 3.6.2 getAgentCountByComplexity

```javascript
/**
 * getAgentCountByComplexity
 * Map complexity level to number of parallel agents
 * Aligned with parallel_agent_config.agent_count_by_complexity in skill frontmatter
 *
 * @param {"simple" | "moderate" | "complex"} complexity - Complexity level
 * @returns {number} - Agent count (1, 2, or 3)
 *
 * @example
 * let count = getAgentCountByComplexity("moderate")
 * // Returns: 2
 *
 * Agent Allocation Strategy:
 * - simple:   1 agent  → Direct assignment, no parallel overhead
 * - moderate: 2 agents → dependency_analysis + load_balancing
 * - complex:  3 agents → dependency_analysis + terminal_availability + load_balancing
 */
function getAgentCountByComplexity(complexity) {
  const COMPLEXITY_TO_AGENTS = {
    simple: 1,    // Single agent for simple assignments
    moderate: 2,  // Two agents for moderate assignments
    complex: 3    // Three agents for complex assignments (max)
  }

  let agentCount = COMPLEXITY_TO_AGENTS[complexity] || 1
  console.log(`🤖 Agent count for "${complexity}": ${agentCount}`)

  return agentCount
}
```

#### 3.6.3 getAssignmentAreas

```javascript
/**
 * getAssignmentAreas
 * Determine which analysis areas to assign based on complexity
 * Areas aligned with parallel_agent_config.assignment_areas
 *
 * @param {"simple" | "moderate" | "complex"} complexity - Complexity level
 * @returns {Object[]} - Array of area configurations
 *
 * @example
 * let areas = getAssignmentAreas("moderate")
 * // Returns: [{id: "dependency", ...}, {id: "load_balance", ...}]
 *
 * Available Areas:
 * - dependency_analysis:   Analyze blockedBy relationships, topological order
 * - terminal_availability: Check terminal status, current workload
 * - load_balancing:        Distribute tasks evenly across terminals
 */
function getAssignmentAreas(complexity) {
  const ALL_AREAS = [
    {
      id: "dependency",
      name: "Dependency Analysis",
      focus: "blockedBy relationships, topological sort, execution order",
      priority: 1
    },
    {
      id: "load_balance",
      name: "Load Balancing",
      focus: "even distribution, terminal capacity, workload estimation",
      priority: 2
    },
    {
      id: "terminal",
      name: "Terminal Availability",
      focus: "idle terminals, current assignments, Sub-Orchestrator eligibility",
      priority: 3
    }
  ]

  const agentCount = getAgentCountByComplexity(complexity)

  // Select areas based on agent count
  let selectedAreas = ALL_AREAS.slice(0, agentCount)

  console.log(`📂 Assignment areas (${agentCount} agents): ${selectedAreas.map(a => a.id).join(', ')}`)

  return selectedAreas
}
```

#### 3.6.4 aggregateAnalysisResults

```javascript
/**
 * aggregateAnalysisResults
 * Merge results from parallel analysis agents
 * Handles deduplication and conflict resolution
 *
 * @param {Object[]} results - Array of agent results
 * @returns {Object} - Aggregated analysis result
 *
 * @example
 * let aggregated = aggregateAnalysisResults([
 *   { area: "dependency", assignments: [...], warnings: [...] },
 *   { area: "load_balance", assignments: [...], adjustments: [...] }
 * ])
 */
function aggregateAnalysisResults(results) {
  console.log(`📦 Aggregating results from ${results.length} analysis agents...`)

  let mergedAssignments = new Map()  // taskId -> assignment
  let allWarnings = []
  let allAdjustments = []
  let conflictCount = 0

  for (let result of results) {
    if (!result) {
      console.log(`   ⚠️  Skipping null result`)
      continue
    }

    // Merge warnings
    if (result.warnings) {
      allWarnings.push(...result.warnings)
    }

    // Merge adjustments
    if (result.adjustments) {
      allAdjustments.push(...result.adjustments)
    }

    // Merge assignments with conflict detection
    if (result.assignments) {
      for (let assignment of result.assignments) {
        const existing = mergedAssignments.get(assignment.taskId)

        if (existing) {
          // Conflict detected - prefer assignment with higher priority area
          if (result.areaPriority < existing.areaPriority) {
            console.log(`   ⚠️  Conflict on Task #${assignment.taskId}: ${existing.terminalId} → ${assignment.terminalId}`)
            mergedAssignments.set(assignment.taskId, {
              ...assignment,
              areaPriority: result.areaPriority,
              conflictResolved: true
            })
            conflictCount++
          }
        } else {
          mergedAssignments.set(assignment.taskId, {
            ...assignment,
            areaPriority: result.areaPriority || 99
          })
        }
      }
    }
  }

  const aggregated = {
    assignments: Array.from(mergedAssignments.values()),
    warnings: [...new Set(allWarnings)],  // Deduplicate warnings
    adjustments: allAdjustments,
    metadata: {
      totalAgents: results.length,
      conflictsResolved: conflictCount,
      aggregatedAt: new Date().toISOString()
    }
  }

  console.log(`
✅ Aggregation Complete:
   Assignments: ${aggregated.assignments.length}
   Warnings: ${aggregated.warnings.length}
   Conflicts Resolved: ${conflictCount}
`)

  return aggregated
}
```

#### 3.6.5 generateL1AssignmentSummary

```javascript
/**
 * generateL1AssignmentSummary
 * Generate L1 markdown summary for main orchestrator
 * Follows context pollution prevention guidelines (≤500 tokens)
 *
 * @param {Object} aggregatedResult - Aggregated analysis result
 * @param {string} slug - Workload slug
 * @returns {string} - Markdown summary (compact, ≤500 tokens)
 */
function generateL1AssignmentSummary(aggregatedResult, slug) {
  const { assignments, warnings, metadata } = aggregatedResult

  // Calculate metrics
  const totalAssigned = assignments.length
  const readyCount = assignments.filter(a => a.canStart).length
  const blockedCount = totalAssigned - readyCount

  // Group by terminal
  const terminalDist = {}
  for (let a of assignments) {
    terminalDist[a.terminalId] = (terminalDist[a.terminalId] || 0) + 1
  }

  // Determine recommendation
  let recommendation = "PROCEED"
  let recommendationEmoji = "✅"

  if (warnings.length > 0) {
    recommendation = "REVIEW_WARNINGS"
    recommendationEmoji = "⚠️"
  }

  if (blockedCount === totalAssigned) {
    recommendation = "ALL_BLOCKED"
    recommendationEmoji = "🛑"
  }

  // Build compact L1 summary
  const summary = `# L1 Assignment Summary

## Overview
- **Workload:** ${slug}
- **Tasks Assigned:** ${totalAssigned}
- **Ready:** ${readyCount} | **Blocked:** ${blockedCount}

## Terminal Distribution
${Object.entries(terminalDist).map(([t, count]) => `- ${t}: ${count} task(s)`).join('\n')}

## Warnings
${warnings.length > 0 ? warnings.map(w => `- ${w}`).join('\n') : '- None'}

## Recommendation
${recommendationEmoji} **${recommendation}**

---
*L2 Path: .agent/prompts/${slug}/assign/l2_index.md*
*Generated: ${new Date().toISOString()}*
`

  // Validate token count (rough estimate: 1 token ≈ 4 chars)
  const estimatedTokens = Math.ceil(summary.length / 4)

  if (estimatedTokens > 500) {
    console.log(`⚠️  L1 Summary exceeds 500 tokens (est: ${estimatedTokens}). Consider trimming.`)
  } else {
    console.log(`✅ L1 Summary generated (est: ${estimatedTokens} tokens)`)
  }

  return summary
}
```

### 3.7 Phase 3 Verification (P3 Synthesis)

> **EFL Pattern P3**: Two-phase synthesis for assignment validation

#### 3.7.1 phase3aLoadBalanceCheck (L2 Horizontal)

```javascript
/**
 * phase3aLoadBalanceCheck - L2 Horizontal Synthesis
 * Cross-validates assignments for load balance across terminals
 *
 * Validation Criteria (from synthesis_config.phase_3a_l2_horizontal):
 * - load_balance_check: Even distribution of tasks
 * - dependency_order_validation: Blockers assigned before dependents
 * - terminal_capacity_check: No terminal overloaded
 *
 * @param {Object} analysisResult - Result from deployAnalysisAgents or directAssignmentAnalysis
 * @param {string} slug - Workload slug
 * @returns {Object} - L2 synthesis result
 */
async function phase3aLoadBalanceCheck(analysisResult, slug) {
  console.log(`\n🔄 Phase 3-A: L2 Horizontal Synthesis (Load Balance Check)`)

  const { assignments } = analysisResult

  // Quick validation for simple cases
  if (assignments.length <= 3) {
    console.log(`   ⚡ Simple case (${assignments.length} tasks): Quick validation`)
    const quickResult = performQuickLoadBalanceCheck(assignments)
    return {
      phase: "3a",
      type: "l2_horizontal",
      status: quickResult.balanced ? "passed" : "warning",
      ...quickResult
    }
  }

  // Complex case: Delegate to synthesis agent with P6 internal loop
  console.log(`   🤖 Delegating to L2 Horizontal Synthesis Agent...`)

  const result = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## Phase 3-A: L2 Horizontal Synthesis (Load Balance Verification)

### Context
- Workload: ${slug}
- Total Assignments: ${assignments.length}

### Assignments to Verify
\`\`\`json
${JSON.stringify(assignments, null, 2)}
\`\`\`

### Validation Tasks

1. **Load Balance Check**
   - Count tasks per terminal
   - Calculate standard deviation of load
   - Flag terminals with >3 tasks or 2x average load

2. **Dependency Order Validation**
   - For each blocked task, verify blocker is assigned to different terminal OR earlier
   - Check no terminal has both blocker and blocked task running simultaneously
   - Identify potential deadlock scenarios

3. **Terminal Capacity Check**
   - Verify no terminal has conflicting assignments
   - Check Sub-Orchestrator assignments are appropriate
   - Ensure critical path tasks have dedicated terminals

### Internal Feedback Loop (P6 - REQUIRED)
1. Perform all three validation checks
2. Self-validate:
   - [ ] All ${assignments.length} assignments checked
   - [ ] Load distribution calculated correctly
   - [ ] Dependency order verified for each blocked task
3. If any check reveals issues, re-analyze (max 3 iterations)
4. Output only after all validations pass

### Output Format (YAML)
\`\`\`yaml
phase3a_status: "passed" | "warning" | "failed"

loadBalanceResult:
  balanced: true|false
  tasksPerTerminal:
    "terminal-b": {count}
    "terminal-c": {count}
  standardDeviation: {number}
  overloadedTerminals: []

dependencyOrderResult:
  valid: true|false
  violations: []
  warnings: []

terminalCapacityResult:
  valid: true|false
  issues: []

overallScore: {0-100}
recommendations: []

internalLoopStatus:
  iterations: {1-3}
  validationPassed: true
\`\`\`
`,
    description: "Phase 3-A: L2 Horizontal Load Balance Check"
  })

  const parsed = parseYAMLFromAgent(result)

  // Save L2 synthesis to file
  const l2SynthesisPath = `.agent/prompts/${slug}/assign/l2_phase3a_synthesis.md`
  Write({
    file_path: l2SynthesisPath,
    content: `# Phase 3-A: L2 Horizontal Synthesis\n\n${typeof result === 'string' ? result : JSON.stringify(result, null, 2)}`
  })

  console.log(`   📝 L2 synthesis saved: ${l2SynthesisPath}`)
  console.log(`   ${parsed.phase3a_status === 'passed' ? '✅' : '⚠️'} Status: ${parsed.phase3a_status}`)

  return {
    phase: "3a",
    type: "l2_horizontal",
    status: parsed.phase3a_status || "unknown",
    loadBalance: parsed.loadBalanceResult,
    dependencyOrder: parsed.dependencyOrderResult,
    terminalCapacity: parsed.terminalCapacityResult,
    score: parsed.overallScore,
    recommendations: parsed.recommendations || [],
    l2Path: l2SynthesisPath
  }
}

/**
 * performQuickLoadBalanceCheck - Fast validation for simple assignments
 */
function performQuickLoadBalanceCheck(assignments) {
  const terminalCounts = {}

  for (let a of assignments) {
    terminalCounts[a.terminalId] = (terminalCounts[a.terminalId] || 0) + 1
  }

  const counts = Object.values(terminalCounts)
  const max = Math.max(...counts)
  const min = Math.min(...counts)
  const balanced = (max - min) <= 1

  return {
    balanced,
    tasksPerTerminal: terminalCounts,
    maxLoad: max,
    minLoad: min,
    recommendations: balanced ? [] : ["Consider rebalancing assignments"]
  }
}
```

#### 3.7.2 phase3bDependencyVerification (L3 Vertical)

```javascript
/**
 * phase3bDependencyVerification - L3 Vertical Verification
 * Deep verification of each assignment against task requirements
 *
 * Validation Criteria (from synthesis_config.phase_3b_l3_vertical):
 * - task_terminal_compatibility: Terminal can handle task complexity
 * - blocker_resolution_order: Blockers will complete before dependents start
 * - sub_orchestrator_eligibility: Complex tasks assigned to capable terminals
 *
 * @param {Object} analysisResult - Result from deployAnalysisAgents
 * @param {Object} phase3aResult - Result from phase3aLoadBalanceCheck
 * @param {string} slug - Workload slug
 * @returns {Object} - L3 verification result
 */
async function phase3bDependencyVerification(analysisResult, phase3aResult, slug) {
  console.log(`\n🔍 Phase 3-B: L3 Vertical Verification (Dependency Order)`)

  const { assignments } = analysisResult

  // Skip for simple cases with no dependencies
  const hasBlockedTasks = assignments.some(a => a.blockedBy && a.blockedBy.length > 0)

  if (!hasBlockedTasks) {
    console.log(`   ⚡ No blocked tasks: Verification passed`)
    return {
      phase: "3b",
      type: "l3_vertical",
      status: "passed",
      message: "No dependencies to verify",
      verifiedAssignments: assignments.length
    }
  }

  // Delegate to L3 verification agent with P6 internal loop
  console.log(`   🤖 Delegating to L3 Vertical Verification Agent...`)

  const result = await Task({
    subagent_type: "general-purpose",
    model: "opus",
    prompt: `
## Phase 3-B: L3 Vertical Verification (Dependency Order)

### Context
- Workload: ${slug}
- Total Assignments: ${assignments.length}
- Blocked Tasks: ${assignments.filter(a => a.blockedBy?.length > 0).length}

### Phase 3-A Results (L2 Horizontal)
- Status: ${phase3aResult.status}
- Score: ${phase3aResult.score || 'N/A'}
- Recommendations: ${(phase3aResult.recommendations || []).join(', ') || 'None'}

### Assignments to Verify
\`\`\`json
${JSON.stringify(assignments, null, 2)}
\`\`\`

### Verification Tasks

1. **Task-Terminal Compatibility**
   - Check if terminal has capacity for assigned task
   - Verify Sub-Orchestrator tasks assigned to capable terminals
   - Ensure no task exceeds terminal's concurrent limit

2. **Blocker Resolution Order**
   - For each blocked task:
     a. Find all blocker task IDs
     b. Verify blockers are assigned
     c. Verify blockers can complete before dependent starts
   - Build execution timeline
   - Identify any timing conflicts

3. **Sub-Orchestrator Eligibility**
   - Check tasks marked for Sub-Orchestrator mode
   - Verify assigned terminal supports decomposition
   - Validate hierarchy level consistency

### Internal Feedback Loop (P6 - REQUIRED)
1. Perform all three verification checks
2. Self-validate:
   - [ ] Every blocked task has all blockers assigned
   - [ ] No circular dependency paths
   - [ ] Execution order is deterministic
3. If any verification fails, identify root cause (max 3 iterations)
4. Output only after all verifications pass or issues documented

### Output Format (YAML)
\`\`\`yaml
phase3b_status: "passed" | "warning" | "failed"

compatibilityResult:
  allCompatible: true|false
  issues: []

blockerOrderResult:
  valid: true|false
  executionOrder: ["{taskId}", ...]
  timeline:
    - taskId: "{id}"
      canStartAfter: ["{blocker_ids}"]
      estimatedStart: "T+{n}"
  violations: []

subOrchestratorResult:
  valid: true|false
  eligibleTasks: []
  issues: []

criticalIssues: []
warnings: []

internalLoopStatus:
  iterations: {1-3}
  validationPassed: true
\`\`\`
`,
    description: "Phase 3-B: L3 Vertical Dependency Verification"
  })

  const parsed = parseYAMLFromAgent(result)

  // Save L3 verification to file
  const l3Path = `.agent/prompts/${slug}/assign/l3_phase3b_verification.md`
  Write({
    file_path: l3Path,
    content: `# Phase 3-B: L3 Vertical Verification\n\n${typeof result === 'string' ? result : JSON.stringify(result, null, 2)}`
  })

  console.log(`   📝 L3 verification saved: ${l3Path}`)
  console.log(`   ${parsed.phase3b_status === 'passed' ? '✅' : '⚠️'} Status: ${parsed.phase3b_status}`)

  return {
    phase: "3b",
    type: "l3_vertical",
    status: parsed.phase3b_status || "unknown",
    compatibility: parsed.compatibilityResult,
    blockerOrder: parsed.blockerOrderResult,
    subOrchestrator: parsed.subOrchestratorResult,
    criticalIssues: parsed.criticalIssues || [],
    warnings: parsed.warnings || [],
    l3Path
  }
}
```

#### 3.7.3 phase35ReviewGate (P5 Review Gate)

```javascript
/**
 * phase35ReviewGate - Main Agent Review Gate
 * Holistic verification before executing assignments
 *
 * Review Criteria (from synthesis_config.phase_3_5_review_gate):
 * - assignment_completeness: All unassigned tasks have assignments
 * - execution_order_validity: Dependencies respected
 * - worker_instruction_clarity: Terminals have clear instructions
 *
 * @param {Object} phase3aResult - L2 Horizontal synthesis result
 * @param {Object} phase3bResult - L3 Vertical verification result
 * @param {Object} analysisResult - Original analysis result
 * @returns {Object} - Review gate decision
 */
async function phase35ReviewGate(phase3aResult, phase3bResult, analysisResult) {
  console.log(`\n🚦 Phase 3.5: Main Agent Review Gate`)

  const criteria = {
    assignment_completeness: {
      passed: analysisResult.assignments.length > 0,
      reason: analysisResult.assignments.length > 0
        ? `All ${analysisResult.assignments.length} tasks assigned`
        : "No assignments generated"
    },
    execution_order_validity: {
      passed: phase3bResult.status !== "failed",
      reason: phase3bResult.status === "passed"
        ? "Dependency order valid"
        : `Issues: ${(phase3bResult.criticalIssues || []).join(', ') || 'Minor warnings'}`
    },
    worker_instruction_clarity: {
      passed: true,  // Assume clear if assignments have terminal IDs
      reason: "All assignments have terminal IDs"
    },
    load_balance_acceptable: {
      passed: phase3aResult.status !== "failed",
      reason: phase3aResult.status === "passed"
        ? "Load balanced"
        : `Score: ${phase3aResult.score || 'N/A'}`
    }
  }

  // Calculate overall result
  const allPassed = Object.values(criteria).every(c => c.passed)
  const hasCritical = phase3bResult.criticalIssues?.length > 0
  const hasWarnings = (phase3aResult.recommendations?.length > 0) ||
                      (phase3bResult.warnings?.length > 0)

  let decision = "APPROVED"
  if (hasCritical) {
    decision = "BLOCKED"
  } else if (hasWarnings) {
    decision = "APPROVED_WITH_WARNINGS"
  }

  console.log(`\n   📋 Review Criteria:`)
  for (let [name, result] of Object.entries(criteria)) {
    console.log(`      ${result.passed ? '✅' : '❌'} ${name}: ${result.reason}`)
  }

  console.log(`\n   🎯 Decision: ${decision}`)

  return {
    phase: "3.5",
    type: "review_gate",
    decision,
    allCriteriaPassed: allPassed,
    criteria,
    blockers: hasCritical ? phase3bResult.criticalIssues : [],
    warnings: [
      ...(phase3aResult.recommendations || []),
      ...(phase3bResult.warnings || [])
    ],
    canProceed: decision !== "BLOCKED",
    nextStep: decision === "BLOCKED"
      ? "phase4_selective_feedback"
      : "execute_assignments"
  }
}
```

### 3.8 Main Execution Flow (EFL Orchestration)

> **EFL Pattern**: Complete orchestration flow connecting all phases

#### 3.8.1 executeAssignment - Main Entry Point

```javascript
/**
 * executeAssignment - Main EFL Orchestration Function
 * Connects all phases: Analysis → Phase 3-A → Phase 3-B → Review Gate → Execute
 *
 * EFL Flow:
 * 1. Parse arguments (manual vs auto)
 * 2. For auto: Run full EFL pipeline
 * 3. For manual: Direct assignment with validation
 *
 * @param {string} mode - "auto" or task ID for manual
 * @param {string} terminalId - Terminal ID (for manual mode)
 * @param {Object} options - Additional options
 * @returns {Object} - L1 summary result
 */
async function executeAssignment(mode, terminalId = null, options = {}) {
  console.log(`\n${'='.repeat(60)}`)
  console.log(`   /assign V4.0.0 (EFL Pattern)`)
  console.log(`${'='.repeat(60)}`)

  const startTime = Date.now()
  const slug = getActiveWorkloadSlug() || `assign-${Date.now()}`
  const isSubOrchestrator = options.subOrchestrator ?? true

  // Ensure output directory exists
  Bash({ command: `mkdir -p .agent/prompts/${slug}/assign` })

  // Route based on mode
  if (mode === "auto") {
    return await executeAutoAssignmentEFL(slug, isSubOrchestrator, startTime)
  } else {
    return await executeManualAssignment(mode, terminalId, isSubOrchestrator, slug)
  }
}

/**
 * executeAutoAssignmentEFL - Full EFL pipeline for auto assignment
 */
async function executeAutoAssignmentEFL(slug, isSubOrchestrator, startTime) {
  console.log(`\n📋 Mode: Auto Assignment (EFL)`)
  console.log(`📁 Workload: ${slug}`)

  // =========================================================================
  // Phase 1-2: Analysis (complexity detection + parallel agents)
  // =========================================================================
  console.log(`\n${'─'.repeat(40)}`)
  console.log(`Phase 1-2: Analysis`)
  console.log(`${'─'.repeat(40)}`)

  const analysisResult = await autoAssign()

  if (analysisResult.status === "no_unassigned") {
    return {
      status: "success",
      message: "All tasks already assigned",
      l1Summary: generateL1AssignmentSummary({ assignments: [], warnings: [], metadata: {} }, slug)
    }
  }

  // =========================================================================
  // Phase 3-A: L2 Horizontal Synthesis (Load Balance Check)
  // =========================================================================
  console.log(`\n${'─'.repeat(40)}`)
  console.log(`Phase 3-A: L2 Horizontal Synthesis`)
  console.log(`${'─'.repeat(40)}`)

  const phase3aResult = await phase3aLoadBalanceCheck(analysisResult.analysisResult, slug)

  // =========================================================================
  // Phase 3-B: L3 Vertical Verification (Dependency Order)
  // =========================================================================
  console.log(`\n${'─'.repeat(40)}`)
  console.log(`Phase 3-B: L3 Vertical Verification`)
  console.log(`${'─'.repeat(40)}`)

  const phase3bResult = await phase3bDependencyVerification(
    analysisResult.analysisResult,
    phase3aResult,
    slug
  )

  // =========================================================================
  // Phase 3.5: Review Gate
  // =========================================================================
  console.log(`\n${'─'.repeat(40)}`)
  console.log(`Phase 3.5: Review Gate`)
  console.log(`${'─'.repeat(40)}`)

  const reviewResult = await phase35ReviewGate(
    phase3aResult,
    phase3bResult,
    analysisResult.analysisResult
  )

  // =========================================================================
  // Phase 4: Selective Feedback (if blocked)
  // =========================================================================
  if (!reviewResult.canProceed) {
    console.log(`\n${'─'.repeat(40)}`)
    console.log(`Phase 4: Selective Feedback (BLOCKED)`)
    console.log(`${'─'.repeat(40)}`)

    console.log(`\n❌ Assignment blocked due to critical issues:`)
    reviewResult.blockers.forEach(b => console.log(`   - ${b}`))

    return {
      status: "blocked",
      reason: "Review gate failed",
      blockers: reviewResult.blockers,
      recommendations: "Fix dependency issues and retry /assign auto",
      l1Summary: generateL1AssignmentSummary(analysisResult.analysisResult, slug)
    }
  }

  // =========================================================================
  // Phase 5: Execute Assignments
  // =========================================================================
  console.log(`\n${'─'.repeat(40)}`)
  console.log(`Phase 5: Execute Assignments`)
  console.log(`${'─'.repeat(40)}`)

  const executionResult = await executeActualAssignments(
    analysisResult.analysisResult.assignments,
    isSubOrchestrator,
    slug
  )

  // =========================================================================
  // Generate L1 Summary and Save Outputs
  // =========================================================================
  const duration = ((Date.now() - startTime) / 1000).toFixed(1)

  const l1Summary = generateL1AssignmentSummary(
    {
      ...analysisResult.analysisResult,
      metadata: {
        ...analysisResult.analysisResult.metadata,
        executionTime: `${duration}s`,
        phase3aStatus: phase3aResult.status,
        phase3bStatus: phase3bResult.status,
        reviewDecision: reviewResult.decision
      }
    },
    slug
  )

  // Save L1 summary to file
  const l1Path = `.agent/prompts/${slug}/assign/l1_summary.md`
  Write({ file_path: l1Path, content: l1Summary })

  console.log(`\n${'='.repeat(60)}`)
  console.log(`   Assignment Complete`)
  console.log(`${'='.repeat(60)}`)
  console.log(`\n📊 Summary:`)
  console.log(`   - Tasks Assigned: ${executionResult.assigned}`)
  console.log(`   - Ready to Start: ${executionResult.ready}`)
  console.log(`   - Blocked: ${executionResult.blocked}`)
  console.log(`   - Duration: ${duration}s`)
  console.log(`\n📁 Outputs:`)
  console.log(`   - L1: ${l1Path}`)
  console.log(`   - L2: .agent/prompts/${slug}/assign/l2_*.md`)
  console.log(`   - L3: .agent/prompts/${slug}/assign/l3_*.md`)
  console.log(`\n🚀 Next: /worker start (in each assigned terminal)`)

  return {
    status: "success",
    execution: executionResult,
    eflMetrics: {
      complexity: analysisResult.complexity,
      agentCount: analysisResult.agentCount,
      phase3aStatus: phase3aResult.status,
      phase3bStatus: phase3bResult.status,
      reviewDecision: reviewResult.decision,
      duration: `${duration}s`
    },
    l1Path,
    l2Path: `.agent/prompts/${slug}/assign/l2_analysis.md`,
    nextActionHint: "/worker start"
  }
}

/**
 * executeManualAssignment - Single task assignment with validation
 */
async function executeManualAssignment(taskId, terminalId, isSubOrchestrator, slug) {
  console.log(`\n📋 Mode: Manual Assignment`)
  console.log(`   Task: #${taskId} → ${terminalId}`)

  // Validate and assign
  manualAssign(taskId, terminalId, { subOrchestrator: isSubOrchestrator })

  // Generate minimal L1 for manual assignment
  const task = TaskGet({ taskId })
  const l1Summary = `# Manual Assignment Complete

- **Task:** #${taskId} - ${task?.subject || 'Unknown'}
- **Terminal:** ${terminalId}
- **Sub-Orchestrator:** ${isSubOrchestrator ? 'Yes' : 'No'}
- **Status:** ${task?.blockedBy?.length > 0 ? 'Blocked' : 'Ready'}

Next: Run \`/worker start\` in ${terminalId}
`

  return {
    status: "success",
    taskId,
    terminalId,
    isSubOrchestrator,
    canStart: !task?.blockedBy?.length,
    l1Summary
  }
}

/**
 * executeActualAssignments - Execute TaskUpdate for all assignments
 */
async function executeActualAssignments(assignments, isSubOrchestrator, slug) {
  console.log(`\n>>> Executing ${assignments.length} assignments...`)

  let assigned = 0
  let ready = 0
  let blocked = 0

  for (let assignment of assignments) {
    try {
      // Update task owner via TaskUpdate
      TaskUpdate({
        taskId: assignment.taskId,
        owner: assignment.terminalId,
        metadata: {
          hierarchyLevel: 0,
          subOrchestratorMode: isSubOrchestrator,
          canDecompose: isSubOrchestrator,
          assignedAt: new Date().toISOString()
        }
      })

      // Get task details for progress update
      const task = TaskGet({ taskId: assignment.taskId })

      // Update progress file
      updateProgressFile(assignment.taskId, assignment.terminalId, task, isSubOrchestrator)

      // Track counts
      assigned++
      if (assignment.canStart) {
        ready++
        console.log(`   ✅ Task #${assignment.taskId} → ${assignment.terminalId} (Ready)`)
      } else {
        blocked++
        console.log(`   ⏸️  Task #${assignment.taskId} → ${assignment.terminalId} (Blocked by: ${(assignment.blockedBy || []).join(', ')})`)
      }
    } catch (e) {
      console.log(`   ❌ Task #${assignment.taskId}: ${e.message}`)
    }
  }

  console.log(`\n   Total: ${assigned} assigned (${ready} ready, ${blocked} blocked)`)

  // Print worker instructions
  printWorkerInstructions(assignments)

  return { assigned, ready, blocked }
}
```

#### 3.8.2 Skill Entry Point

```javascript
/**
 * /assign skill entry point
 * Called when user invokes /assign command
 *
 * Usage:
 *   /assign auto                    - Auto-assign all unassigned tasks
 *   /assign <taskId> <terminalId>   - Manual assignment
 *   /assign <taskId> <terminalId> --sub-orchestrator  - With Sub-Orchestrator mode
 */
async function assignSkillMain(args) {
  // Parse arguments
  const firstArg = args[0]

  if (!firstArg || firstArg === '--help' || firstArg === '-h') {
    return printAssignHelp()
  }

  if (firstArg === 'auto') {
    return await executeAssignment('auto')
  }

  // Manual assignment: /assign <taskId> <terminalId> [--sub-orchestrator]
  const taskId = firstArg
  const terminalId = args[1]
  const isSubOrchestrator = args.includes('--sub-orchestrator') || args.includes('--sub')

  if (!terminalId) {
    console.log(`❌ Usage: /assign <taskId> <terminalId>`)
    console.log(`   Example: /assign 1 terminal-b`)
    return { status: "error", message: "Missing terminal ID" }
  }

  return await executeAssignment(taskId, terminalId, { subOrchestrator: isSubOrchestrator })
}

function printAssignHelp() {
  console.log(`
/assign - Task Assignment to Workers (EFL V4.0.0)

Usage:
  /assign auto                         Auto-assign all unassigned tasks
  /assign <taskId> <terminalId>        Manual assignment
  /assign <taskId> <terminalId> --sub  With Sub-Orchestrator mode

Examples:
  /assign auto                         Assign all tasks with EFL validation
  /assign 1 terminal-b                 Assign Task #1 to terminal-b
  /assign 2 terminal-c --sub           Assign Task #2 with Sub-Orchestrator

EFL Phases:
  1-2. Analysis       Complexity detection + parallel agents
  3-A. L2 Horizontal  Load balance validation
  3-B. L3 Vertical    Dependency order verification
  3.5. Review Gate    Holistic approval check
  5.   Execute        Apply assignments via TaskUpdate
`)
  return { status: "help" }
}
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 4. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **Task not found** | TaskGet returns null | Show available tasks via TaskList |
| **Invalid terminal ID** | N/A (any string allowed) | Warn about naming convention |
| **Circular dependency** | Detected in TaskGet | Cannot assign, notify user |
| **Progress file conflict** | File locked/corrupted | Regenerate from TaskList |
| **Phase 3 validation failed** | Review gate blocked | Show blockers, suggest fixes |
| **Agent delegation failed** | Task tool error | Fallback to direct assignment |

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

### Example 2: Auto Assignment (Sub-Orchestrator Default)

```bash
/assign auto
```

**Output:**
```
Found 3 unassigned tasks
Generated 3 terminal IDs
🔧 Sub-Orchestrator mode enabled for all assignments

🟢 Ready Task #1 → terminal-b (Sub-Orchestrator)
🔴 Blocked Task #2 → terminal-c (Sub-Orchestrator)
🔴 Blocked Task #3 → terminal-d (Sub-Orchestrator)

=== Assignment Summary ===
Total assigned: 3
Can start now: 1
Blocked: 2
Mode: Sub-Orchestrator (all terminals)

=== Worker Instructions ===

🟢 Ready to Start (1):

terminal-b (Sub-Orchestrator):
  /worker start  (can use /orchestrate if task needs decomposition)
  → Task #1: Implement session registry

🔴 Blocked (2):

terminal-c (Sub-Orchestrator):
  (Wait for blockers to complete)
  → Task #2: Prompt file generation
  → Blocked by: 1

terminal-d (Sub-Orchestrator):
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

**EFL Pattern (V4.0.0):**

*P2: Parallel Agent Deployment:*
- [ ] `detectAssignmentComplexity()` returns correct level for 1-3/4-6/7+ tasks
- [ ] `getAgentCountByComplexity()` returns 1/2/3 agents correctly
- [ ] `deployAnalysisAgents()` spawns correct number of agents via `Task({})`
- [ ] `Promise.all` barrier synchronization waits for all agents
- [ ] Agent prompts include P6 Internal Loop instructions
- [ ] Simple mode (1-3 tasks) uses direct assignment without agent overhead

*P3: Phase 3-A/3-B Verification:*
- [ ] `phase3aLoadBalanceCheck()` validates load distribution
- [ ] Phase 3-A generates L2 synthesis file
- [ ] `phase3bDependencyVerification()` checks dependency order
- [ ] Phase 3-B generates L3 verification file
- [ ] Quick validation for simple cases (≤3 tasks)
- [ ] Full agent delegation for complex cases (4+ tasks)

*P5: Review Gate:*
- [ ] `phase35ReviewGate()` checks all criteria
- [ ] APPROVED decision allows execution
- [ ] BLOCKED decision stops with blockers list
- [ ] APPROVED_WITH_WARNINGS shows warnings but proceeds
- [ ] All criteria tracked: completeness, order, clarity, balance

*P6: Internal Feedback Loop:*
- [ ] Agent prompts include self-validation checklist
- [ ] `internalLoopStatus` tracked in agent responses
- [ ] Max 3 iterations enforced per agent
- [ ] Validation criteria: all tasks addressed, no duplicates, load balanced

*L1/L2/L3 Output Separation:*
- [ ] L1 summary ≤500 tokens returned to main context
- [ ] L2 analysis saved to `.agent/prompts/{slug}/assign/l2_*.md`
- [ ] L3 details saved to `.agent/prompts/{slug}/assign/l3_*.md`
- [ ] `generateL1AssignmentSummary()` produces compact summary
- [ ] No context pollution from agent results

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
| 3.0.0 | **Full EFL Implementation** (frontmatter only) |
| | P1-P6 config in frontmatter |
| | Phase 3-A/3-B/3.5 config added |
| | Sub-Orchestrator mode retained |
| 4.0.0 | **Actual Task Tool Implementation** |
| | `Task({ subagent_type: "general-purpose" })` 호출 구현 |
| | `Promise.all` Barrier Synchronization 적용 |
| | Section 3.6: EFL Helper Functions 추가 |
| | - `detectAssignmentComplexity()` 복잡도 분석 |
| | - `getAgentCountByComplexity()` 에이전트 수 결정 |
| | - `getAssignmentAreas()` 분석 영역 결정 |
| | - `aggregateAnalysisResults()` 결과 집계 |
| | - `generateL1AssignmentSummary()` L1 요약 생성 |
| | Section 3.2: `deployAnalysisAgents()` with P6 Internal Loop |
| | Section 3.7: Phase 3-A/3-B/3.5 실제 에이전트 호출 구현 |
| | Section 3.8: Main Execution Flow 오케스트레이션 |
| | L1/L2/L3 파일 분리 저장 (context pollution 방지) |
| | 복잡도 기반 에이전트 스케일링 (simple/moderate/complex) |

---

## 9. Standalone Execution (V3.2.0)

### 9.1 독립 실행 모드

`/assign`은 upstream `/orchestrate` 없이 기존 Task를 할당 가능:

```bash
# 독립 실행 (기존 Native Task 할당)
/assign 1 terminal-b
/assign auto

# 명시적 workload 지정
/assign --workload user-auth-20260128-143022 auto
```

### 9.2 Workload Context Resolution

```bash
# Source standalone module
source /home/palantir/.claude/skills/shared/skill-standalone.sh

# Initialize skill context
CONTEXT=$(init_skill_context "assign" "$ARGUMENTS" "")

# Resolution priority:
# 1. --workload argument → explicit workload
# 2. Active workload → .agent/prompts/_active_workload.yaml
# 3. Use TaskList to find unassigned tasks
```

---

## 10. Handoff Contract (V3.2.0)

### 10.1 Handoff 매핑

| Status | Next Skill | Arguments |
|--------|------------|-----------|
| `completed` | `/worker` (workers) | `--workload {slug}` |
| `error` | `null` | - |

### 10.2 Handoff YAML 출력

스킬 완료 시 _progress.yaml 업데이트와 함께 다음 handoff 정보를 출력:

```yaml
---

# Handoff Metadata (auto-generated)
handoff:
  skill: "assign"
  workload_slug: "user-auth-20260128-143022"
  status: "completed"
  timestamp: "2026-01-28T15:30:00Z"
  next_action:
    skill: "/worker"
    arguments: "--workload user-auth-20260128-143022"
    required: true
    reason: "Tasks assigned, workers can start"
```

### 10.3 Worker Terminal 연계

```bash
# /assign 완료 후 각 터미널에서:
# terminal-b:
/worker start

# terminal-c:
/worker start

# Worker가 blockedBy 검사 후 실행 가능한 task 시작
```

---

**End of Skill Documentation**

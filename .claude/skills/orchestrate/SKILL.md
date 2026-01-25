---
name: orchestrate
description: |
  Break down complex tasks, create Native Tasks, generate worker prompts,
  set up dependencies for multi-terminal parallel execution.
  Uses project-specific context files to avoid conflicts between projects.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "3.1.0"
argument-hint: "--plan-slug <slug> | <task-description>"
hooks:
  PreToolUse:
    - type: command
      command: "/home/palantir/.claude/hooks/orchestrate-validate.sh"
      timeout: 30000
      matcher: "TaskCreate"
---

# /orchestrate - Task Decomposition & Orchestration

> **Version:** 1.0
> **Role:** Task decomposition + Native Task creation + Worker prompt generation
> **Architecture:** Hybrid (Native Task System + File-Based Prompts)

---

## 1. Purpose

**Orchestrator Agent** that:
1. Breaks down complex tasks into phases
2. Creates Native Tasks via `TaskCreate`
3. Sets up dependencies via `TaskUpdate(addBlockedBy)`
4. Generates worker prompt files (`.agent/prompts/`)
5. Initializes global context and progress tracking

---

## 2. Invocation

### User Syntax
```bash
/orchestrate "Implement session-aware worker prompt system"
/orchestrate "Refactor authentication flow with new JWT library"
```

### Arguments
- `$0`: Task description (single line or multi-line)

---

## 3. Execution Protocol

### 3.1 Phase 1: Requirements Analysis

```javascript
// 1. Parse user input (support --plan-slug argument)
input = args[0]
let projectSlug = null

// 1a. Check for --plan-slug argument
if (input.startsWith('--plan-slug')) {
  const planSlug = input.match(/--plan-slug\s+(\S+)/)?.[1]
  if (planSlug) {
    // Extract project name from planning document
    const planPath = `.agent/plans/${planSlug}.yaml`
    const planContent = Read({ file_path: planPath })
    // Parse YAML frontmatter for project name
    projectSlug = planContent.match(/project:\s*["']?([^"'\n]+)/)?.[1]
      || planSlug  // fallback to slug if no project name found
  }
}

// 1b. Generate projectSlug from task description if not from --plan-slug
if (!projectSlug) {
  projectSlug = slugify(input.split(' ').slice(0, 5).join('-'))
}

// 2. Use Chain of Thought to decompose
analysis = analyzeTask(input)
analysis.projectSlug = projectSlug  // Attach for file generation
/*
Output:
{
  project: "session-aware-worker-prompt-system",
  objectives: [...],
  phases: [
    {id: "phase1", name: "Session Registry", dependencies: []},
    {id: "phase2", name: "Prompt Generation", dependencies: ["phase1"]},
    {id: "phase3", name: "Lifecycle Management", dependencies: ["phase2"]}
  ],
  estimatedWorkers: 3
}
*/
```

### 3.2 Phase 2: Gate 4 Validation (Shift-Left)

```javascript
// Gate 4: Validate phase dependencies BEFORE creating tasks
console.log("🔍 Running Gate 4: Phase dependency validation...")

const phasesJson = JSON.stringify(analysis.phases.map(p => ({
  id: p.id,
  dependencies: p.dependencies || []
})))

const gate4Result = await validatePhaseDependencies(phasesJson)

if (gate4Result.result === "failed") {
  console.log("❌ Gate 4 FAILED - Fix errors before creating tasks:")
  gate4Result.errors.forEach(e => console.log(`   - ${e}`))
  return { status: "gate4_failed", errors: gate4Result.errors }
}

if (gate4Result.warnings.length > 0) {
  console.log("⚠️  Gate 4 warnings:")
  gate4Result.warnings.forEach(w => console.log(`   - ${w}`))
}

console.log("✅ Gate 4 PASSED - Proceeding to Task creation")
```

### 3.3 Phase 3: Native Task Creation

```javascript
// Create tasks in dependency order
taskMap = {}

for (phase of analysis.phases) {
  task = TaskCreate({
    subject: `${phase.name}`,
    description: phase.description,
    activeForm: `Working on ${phase.name}`,
    metadata: {
      phaseId: phase.id,
      priority: phase.priority || "P1"
    }
  })

  taskMap[phase.id] = task.id

  console.log(`✅ Created Task #${task.id}: ${phase.name}`)
}
```

### 3.3 Phase 3: Dependency Setup

```javascript
// Set up blockers
for (phase of analysis.phases) {
  if (phase.dependencies.length > 0) {
    blockerIds = phase.dependencies.map(depId => taskMap[depId])

    TaskUpdate({
      taskId: taskMap[phase.id],
      addBlockedBy: blockerIds
    })

    console.log(`🔗 Task #${taskMap[phase.id]} blocked by: ${blockerIds}`)
  }
}
```

### 3.4 Phase 4: Generate Context Files

> **V3.1 Multi-Project Isolation**: Uses project-specific filenames to avoid conflicts

#### _context-{projectSlug}.yaml

```javascript
const projectSlug = analysis.projectSlug  // From Phase 1

contextContent = `
version: "1.0"
project: "${analysis.project}"
orchestrator: "Terminal-A"
createdAt: "${new Date().toISOString()}"
lastUpdated: "${new Date().toISOString()}"

objectives:
  primary: ${analysis.objectives.map(o => `\n    - "${o}"`).join('')}

phases:
${analysis.phases.map(p => `
  ${p.id}:
    id: "${p.id}"
    name: "${p.name}"
    owner: "${p.suggestedOwner || 'unassigned'}"
    nativeTaskId: "${taskMap[p.id]}"
    status: "pending"
    dependencies: ${JSON.stringify(p.dependencies)}
    targetFiles: ${JSON.stringify(p.targetFiles || [])}
`).join('\n')}

dependencyGraph: |
${generateDependencyGraph(analysis.phases)}

sharedRules:
  - "ALWAYS Read target file before modifying"
  - "Update _progress-{projectSlug}.yaml after completion"
  - "Report in L1/L2/L3 format"
  - "Check blockedBy before starting work"

referenceFiles: ${JSON.stringify(analysis.referenceFiles || [])}
`

Write({
  file_path: `.agent/prompts/_context-${projectSlug}.yaml`,
  content: contextContent
})
```

#### _progress-{projectSlug}.yaml

```javascript
progressContent = `
version: "1.0"
projectId: "${analysis.project}"
lastUpdated: "${new Date().toISOString()}"

terminals:
${analysis.phases.map(p => `
  ${p.suggestedOwner || `terminal-${String.fromCharCode(97 + p.index)}`}:
    role: "Worker"
    status: "idle"
    currentTask: null
    assignedPhase: "${p.id}"
    nativeTaskId: "${taskMap[p.id]}"
    blockedBy: ${JSON.stringify(p.dependencies.map(d => taskMap[d]))}
    startedAt: null
    completedAt: null
`).join('\n')}

phases:
${analysis.phases.map(p => `
  ${p.id}:
    nativeTaskId: "${taskMap[p.id]}"
    status: "pending"
    owner: "${p.suggestedOwner || 'unassigned'}"
    startedAt: null
    completedAt: null
`).join('\n')}

completedTasks: []
blockers: []
`

Write({
  file_path: `.agent/prompts/_progress-${projectSlug}.yaml`,
  content: progressContent
})
```

### 3.5 Phase 5: Generate Worker Prompt Files

```javascript
for (phase of analysis.phases) {
  workerPromptContent = `
# =============================================================================
# Worker Task: ${phase.suggestedOwner || `Worker-${phase.index}`} - ${phase.name}
# =============================================================================
# Read this file AFTER reading _context-{projectSlug}.yaml
#
# Location: .agent/prompts/pending/worker-${phase.suggestedOwner || phase.index}-task.yaml
# Language: English (Machine-Readable)
# =============================================================================

taskId: "${phase.id}"
nativeTaskId: "${taskMap[phase.id]}"
assignedTo: "${phase.suggestedOwner || `Worker-${phase.index}`}"
orchestrator: "Terminal-A"
createdAt: "${new Date().toISOString()}"

# =============================================================================
# CONTEXT REFERENCE
# =============================================================================
contextFile: ".agent/prompts/_context-${projectSlug}.yaml"
progressFile: ".agent/prompts/_progress-${projectSlug}.yaml"

# =============================================================================
# MY SCOPE
# =============================================================================
scope:
  phaseId: "${phase.id}"
  phaseName: "${phase.name}"
  description: |
    ${phase.description}

# =============================================================================
# TARGET FILES (I can MODIFY these)
# =============================================================================
targetFiles:
${(phase.targetFiles || []).map(f => `
  - path: "${f.path}"
    readOnly: false
    sections: ${JSON.stringify(f.sections || [])}
    modifications: ${JSON.stringify(f.modifications || [])}
`).join('\n')}

# =============================================================================
# REFERENCE FILES (I can only READ these)
# =============================================================================
referenceFiles:
${(phase.referenceFiles || []).map(f => `
  - path: "${f.path}"
    reason: "${f.reason}"
`).join('\n')}

# =============================================================================
# DEPENDENCIES
# =============================================================================
dependencies: ${JSON.stringify(phase.dependencies)}
blockedBy: ${JSON.stringify(phase.dependencies.map(d => taskMap[d]))}
canStartImmediately: ${phase.dependencies.length === 0}

${phase.dependencies.length > 0 ? `
waitCondition: |
  Check .agent/prompts/_progress-${projectSlug}.yaml
  If ${phase.dependencies.map(d => `phase${d}.status`).join(' AND ')} == 'completed', proceed
  Otherwise, wait
` : ''}

# =============================================================================
# COMPLETION CRITERIA
# =============================================================================
completionCriteria:
  required:
${(phase.completionCriteria || []).map(c => `    - "${c}"`).join('\n')}

  verification:
${(phase.verificationSteps || []).map(v => `
    - command: "${v.command}"
      expected: "${v.expected}"
`).join('\n')}

# =============================================================================
# GLOBAL CONTEXT CONSIDERATIONS
# =============================================================================
globalContextChecklist:
${(phase.contextChecklist || []).map(item => `
  - question: "${item.question}"
    consideration: "${item.consideration}"
`).join('\n')}

# =============================================================================
# OUTPUT FORMAT
# =============================================================================
outputFormat: "L1/L2/L3"
l2OutputPath: ".agent/outputs/Worker/${phase.id}-${slugify(phase.name)}.md"

# =============================================================================
# ON COMPLETE
# =============================================================================
onComplete:
  - "TaskUpdate(taskId='${taskMap[phase.id]}', status='completed')"
  - "Update .agent/prompts/_progress-${projectSlug}.yaml: ${phase.suggestedOwner}.status = 'completed'"
  - "Report to Orchestrator with L1 summary"
  ${phase.index < analysis.phases.length - 1 ? `- "Notify next worker that ${phase.dependencies[0] || 'this phase'} is complete"` : ''}
`

  filename = phase.suggestedOwner
    ? `worker-${phase.suggestedOwner}-${projectSlug}-task.yaml`
    : `worker-${String.fromCharCode(97 + phase.index)}-${projectSlug}-task.yaml`

  Write({
    file_path: `.agent/prompts/pending/${filename}`,
    content: workerPromptContent
  })

  // Link prompt file to Native Task
  TaskUpdate({
    taskId: taskMap[phase.id],
    metadata: {
      promptFile: `.agent/prompts/pending/${filename}`,
      phaseId: phase.id,
      priority: phase.priority || "P1"
    }
  })

  console.log(`📄 Created prompt: ${filename}`)
}
```

### 3.6 Phase 6: Summary Output

```javascript
// Generate summary
summary = `
=== Orchestration Complete ===

Project: ${analysis.project}
Created Tasks: ${analysis.phases.length}
Workers Needed: ${analysis.estimatedWorkers}

Tasks:
${analysis.phases.map((p, i) => `
  #${taskMap[p.id]}: ${p.name}
    - Owner: ${p.suggestedOwner || 'unassigned'}
    - Blocked by: ${p.dependencies.length > 0 ? p.dependencies.map(d => `Task #${taskMap[d]}`).join(', ') : 'None (can start immediately)'}
    - Prompt: .agent/prompts/pending/worker-${p.suggestedOwner || String.fromCharCode(97 + i)}-task.yaml
`).join('\n')}

Files Generated:
  ✅ .agent/prompts/_context-${projectSlug}.yaml (project context)
  ✅ .agent/prompts/_progress-${projectSlug}.yaml (progress tracker)
${analysis.phases.map((p, i) => `  ✅ .agent/prompts/pending/worker-${p.suggestedOwner || String.fromCharCode(97 + i)}-${projectSlug}-task.yaml`).join('\n')}

Next Steps:
  1. Use /assign to assign tasks to terminals
     Example: /assign ${taskMap[analysis.phases[0].id]} terminal-b

  2. Or use auto-assignment:
     /assign auto

  3. Workers can then claim tasks:
     /worker start

Dependency Graph:
${generateDependencyGraph(analysis.phases)}
`

return summary
```

---

## 4. Helper Functions

### 4.1 analyzeTask(input)

Uses CoT to break down task:

```javascript
function analyzeTask(input) {
  // Use sequential thinking or claude-code-guide
  analysis = Task({
    subagent_type: "general-purpose",
    prompt: `
## Task Analysis

Break down this task into phases:
"${input}"

## Requirements
- Each phase should be independently completable
- Identify dependencies between phases
- Suggest target files for each phase
- Estimate 3-5 phases maximum
- Include completion criteria

## Output Format (JSON)
{
  "project": "kebab-case-project-name",
  "objectives": ["objective 1", "objective 2"],
  "phases": [
    {
      "id": "phase1",
      "name": "Phase Name",
      "description": "What this phase does",
      "dependencies": [],
      "suggestedOwner": "terminal-b",
      "targetFiles": [
        {"path": "...", "sections": [...]}
      ],
      "referenceFiles": [
        {"path": "...", "reason": "..."}
      ],
      "completionCriteria": ["..."],
      "verificationSteps": [{"command": "...", "expected": "..."}],
      "contextChecklist": [{"question": "...", "consideration": "..."}],
      "priority": "P0"
    }
  ],
  "estimatedWorkers": 3
}
`,
    description: "Analyze task for orchestration"
  })

  return JSON.parse(analysis)
}
```

### 4.2 generateDependencyGraph(phases)

```javascript
function generateDependencyGraph(phases) {
  let graph = []

  // Build adjacency
  for (phase of phases) {
    if (phase.dependencies.length === 0) {
      graph.push(`${phase.id} (${phase.name})`)
    } else {
      for (dep of phase.dependencies) {
        graph.push(`  ${dep} → ${phase.id}`)
      }
    }
  }

  return graph.join('\n')
}
```

### 4.3 slugify(text)

```javascript
function slugify(text) {
  return text.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')
}
```

---

## 5. Gate 4: Phase Dependency Validation

### 5.1 Validation Function

```javascript
async function validatePhaseDependencies(phasesJson) {
  // Source: .claude/skills/shared/validation-gates.sh -> validate_phase_dependencies()

  const warnings = []
  const errors = []

  const phases = JSON.parse(phasesJson)

  // 1. Check for duplicate phase IDs
  const ids = phases.map(p => p.id)
  const duplicates = ids.filter((id, i) => ids.indexOf(id) !== i)

  if (duplicates.length > 0) {
    errors.push(`Duplicate phase IDs found: ${[...new Set(duplicates)].join(', ')}`)
  }

  // 2. Check for undefined dependencies
  for (const phase of phases) {
    for (const dep of (phase.dependencies || [])) {
      if (!ids.includes(dep)) {
        errors.push(`Undefined dependency: ${dep} (referenced by ${phase.id})`)
      }
    }
  }

  // 3. Detect circular dependencies
  const cycles = detectCycles(phases)
  if (cycles.length > 0) {
    errors.push(`Circular dependencies detected: ${cycles.map(c => c.join(' → ')).join('; ')}`)
  }

  // 4. Warn about large phase count
  if (phases.length > 10) {
    warnings.push(`Large number of phases (${phases.length}) - consider breaking into sub-projects`)
  }

  // Determine result
  let result = "passed"
  if (errors.length > 0) result = "failed"
  else if (warnings.length > 0) result = "passed_with_warnings"

  return { gate: "ORCHESTRATE", result, warnings, errors }
}
```

### 5.2 Cycle Detection (Topological Sort)

```javascript
function detectCycles(phases) {
  const graph = new Map()
  const inDegree = new Map()
  const cycles = []

  // Initialize
  for (const phase of phases) {
    graph.set(phase.id, phase.dependencies || [])
    inDegree.set(phase.id, 0)
  }

  // Calculate in-degrees
  for (const [id, deps] of graph) {
    for (const dep of deps) {
      inDegree.set(id, (inDegree.get(id) || 0) + 1)
    }
  }

  // Kahn's algorithm for cycle detection
  const queue = []
  for (const [id, degree] of inDegree) {
    if (degree === 0) queue.push(id)
  }

  let processed = 0
  while (queue.length > 0) {
    const node = queue.shift()
    processed++

    // Find phases that depend on this node
    for (const [id, deps] of graph) {
      if (deps.includes(node)) {
        inDegree.set(id, inDegree.get(id) - 1)
        if (inDegree.get(id) === 0) queue.push(id)
      }
    }
  }

  // If not all nodes processed, there's a cycle
  if (processed < phases.length) {
    const remaining = phases.filter(p => inDegree.get(p.id) > 0).map(p => p.id)
    cycles.push(remaining)
  }

  return cycles
}
```

---

## 6. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **Invalid input** | Empty or malformed task description | Prompt user for clarification |
| **Too many phases** | > 10 phases | Ask user to break down further |
| **Circular dependency** | A → B → A | Reject, ask user to fix |
| **File conflicts** | _context-{projectSlug}.yaml already exists | Ask: overwrite or append? |
| **TaskCreate failure** | Native API error | Log error, abort orchestration |
| **Gate 4 failed** | Duplicate IDs or undefined deps | Show errors, abort orchestration |

---

## 6. Example Usage

### Example 1: Simple Linear Workflow

```bash
/orchestrate "Add user authentication to API"
```

**Output:**
```
✅ Created Task #1: Setup JWT library
✅ Created Task #2: Implement auth middleware
✅ Created Task #3: Add protected routes
✅ Created Task #4: Write integration tests

🔗 Task #2 blocked by: [1]
🔗 Task #3 blocked by: [2]
🔗 Task #4 blocked by: [3]

📄 Created prompt: worker-b-task.yaml
📄 Created prompt: worker-c-task.yaml
📄 Created prompt: worker-d-task.yaml
📄 Created prompt: worker-e-task.yaml

Next: /assign auto
```

### Example 2: Parallel + Sequential Workflow

```bash
/orchestrate "Refactor frontend components with TypeScript"
```

**Analysis Result:**
```
Phase 1a: Convert utility functions (no deps)
Phase 1b: Update type definitions (no deps)
Phase 2: Refactor components (depends on 1a, 1b)
Phase 3: Update tests (depends on 2)
```

**Dependency Graph:**
```
phase1a (no deps) ──┐
                    ├─→ phase2 → phase3
phase1b (no deps) ──┘
```

---

## 7. Integration with /assign

After `/orchestrate` completes:

```bash
# Manual assignment
/assign 1 terminal-b
/assign 2 terminal-c

# Auto assignment
/assign auto
# → Assigns unblocked tasks to available terminals
```

---

## 8. Testing Checklist

- [ ] Single-phase task (no dependencies)
- [ ] Multi-phase linear task (A → B → C)
- [ ] Multi-phase parallel task (A, B → C)
- [ ] Diamond dependency (A → B, C → D)
- [ ] Circular dependency detection
- [ ] File overwrite handling
- [ ] TaskCreate error handling
- [ ] Large task (>5 phases)

---

## 9. Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Task analysis | <10s | TBD |
| TaskCreate (per task) | <500ms | TBD |
| File generation (per file) | <100ms | TBD |
| Total orchestration | <30s | TBD |

---

## 10. Autonomous Execution Protocol (자율 실행 프로토콜)

> **V3.0 Feature** - Workers execute autonomously until project completion

### 10.1 Overview

Enables each terminal to:
1. Monitor other terminals' task status
2. Automatically start tasks when blockers complete
3. Continue execution until all assigned tasks are done
4. Report to Orchestrator on completion

### 10.2 _context-{projectSlug}.yaml Autonomous Section

When generating `_context-{projectSlug}.yaml`, include:

```yaml
# =============================================================================
# AUTONOMOUS EXECUTION PROTOCOL (자율 실행 프로토콜)
# =============================================================================
autonomousProtocol:
  enabled: true
  pollIntervalSeconds: 30

  executionLoop: |
    WHILE project NOT completed:
      1. TaskList() → 전체 Task 상태 확인
      2. Filter by owner == MY_TERMINAL
      3. FOR each myTask:
           IF myTask.status == "pending":
             IF myTask.blockedBy ALL completed:
               → TaskUpdate(taskId, status="in_progress")
               → Execute task
               → TaskUpdate(taskId, status="completed")
             ELSE:
               → Log "Waiting for blockers: {blockedBy}"
      4. IF all myTasks completed:
           → Report final status
      5. Sleep(pollIntervalSeconds)

  checkBlockers: |
    function checkBlockersCompleted(taskId):
      task = TaskGet(taskId)
      FOR each blockerId in task.blockedBy:
        IF TaskGet(blockerId).status != "completed":
          RETURN false
      RETURN true

  selfAssignment:
    primary: "Execute tasks assigned to my terminal"
    secondary: "If all my tasks done, check for unassigned tasks"
    forbidden: "Never take tasks assigned to other terminals"

  completionDetection:
    projectComplete: "All tasks have status='completed'"
    terminalComplete: "All tasks with owner=MY_TERMINAL have status='completed'"

  errorRecovery:
    onTaskFailure:
      - "Log error to .agent/logs/{terminal}.log"
      - "TaskUpdate(taskId, metadata.error='{error}')"
      - "Continue with next available task"
    onDeadlock:
      - "Detect: No progress for 3 poll cycles"
      - "Action: Report to Orchestrator with blockers list"
```

### 10.3 Worker Prompt Autonomous Section

For each worker prompt file, include:

```yaml
# =============================================================================
# AUTONOMOUS EXECUTION INSTRUCTIONS (자율 실행 지침)
# =============================================================================
autonomousExecution:
  enabled: true
  myTerminal: "${terminalId}"
  myTasks: ${JSON.stringify(assignedTaskIds)}

  executionSequence:
${phases.filter(p => p.owner === terminalId).map((p, i) => `
    - step: ${i + 1}
      taskId: "${taskMap[p.id]}"
      name: "${p.name}"
      blockedBy: ${JSON.stringify(p.dependencies.map(d => taskMap[d]))}
      action: "${p.dependencies.length === 0 ? 'START IMMEDIATELY' : 'Wait for blockers, then start'}"
      onComplete: "${getUnblockedTasks(p.id)}"
`).join('')}

  monitoringLoop: |
    REPEAT until all myTasks completed:
      1. TaskList() → Check current status
      2. FOR each taskId in myTasks:
           task = TaskGet(taskId)
           IF task.status == "pending" AND allBlockersComplete(task):
             TaskUpdate(taskId, status="in_progress")
             EXECUTE task
             TaskUpdate(taskId, status="completed")
      3. Check cross-terminal dependencies
      4. IF all myTasks completed:
           REPORT "Terminal-X: All tasks completed"
           EXIT loop

  crossTerminalDeps:
${getCrossTerminalDeps(terminalId)}

  completionCriteria:
    allTasksCompleted: ${JSON.stringify(assignedTaskIds)}
    outputGenerated: ".agent/outputs/${terminalId}/report.md"
    progressUpdated: "_progress-${projectSlug}.yaml reflects ${terminalId}.status = 'completed'"
```

### 10.4 _progress-{projectSlug}.yaml Autonomous Section

```yaml
# =============================================================================
# AUTONOMOUS EXECUTION CONFIG (자율 실행 설정)
# =============================================================================
autonomousExecution:
  enabled: true
  mode: "ACTIVE"
  startedAt: null
  estimatedCompletion: null

  polling:
    intervalSeconds: 30
    maxRetries: 3
    backoffMultiplier: 2

  dependencyRules:
    checkMethod: "TaskGet(blockerId).status == 'completed'"
    autoUnblock: true
    notifyOnUnblock: true

  coordination:
    method: "Native Task System + _progress-{projectSlug}.yaml"
    syncInterval: 30
    conflictResolution: "first-claimer-wins"

  completionTracking:
    projectComplete:
      condition: "ALL tasks status == 'completed'"
      action: "Notify Orchestrator, generate final report"

${terminals.map(t => `
    ${t}Complete:
      condition: "Tasks ${getTerminalTasks(t)} status == 'completed'"
      action: "Update ${t}.status = 'completed'"
`).join('')}

  crossDependencies:
${generateCrossDependencies(phases, taskMap)}

  errorHandling:
    onTaskFailure:
      action: "Log, mark task as blocked, notify Orchestrator"
      retryCount: 2
      escalateAfter: 2
    onDeadlock:
      detection: "No progress for 3 poll cycles"
      action: "Report to Orchestrator with dependency graph"
    onConflict:
      detection: "Multiple terminals claim same task"
      action: "First claimer wins, others skip"

# =============================================================================
# START COMMAND FOR WORKERS
# =============================================================================
workerStartCommands:
${terminals.map(t => `
  ${t}: |
    /worker start ${t.split('-')[1]}
`).join('')}
```

### 10.5 Helper Functions for Autonomous Protocol

```javascript
function generateCrossDependencies(phases, taskMap) {
  const crossDeps = []

  for (const phase of phases) {
    for (const dep of phase.dependencies) {
      const depPhase = phases.find(p => p.id === dep)
      if (depPhase && depPhase.owner !== phase.owner) {
        crossDeps.push({
          from: phase.owner,
          task: taskMap[phase.id],
          waitFor: [{
            terminal: depPhase.owner,
            task: taskMap[dep]
          }]
        })
      }
    }
  }

  return crossDeps.map(cd => `
    - from: "${cd.from}"
      task: "${cd.task}"
      waitFor:
        - terminal: "${cd.waitFor[0].terminal}"
          task: "${cd.waitFor[0].task}"
  `).join('')
}

function getCrossTerminalDeps(terminalId) {
  // Returns YAML for cross-terminal dependencies
  const deps = crossDependencies.filter(cd => cd.from === terminalId)
  return deps.map(d => `
    task${d.task}_requires: "Task #${d.waitFor[0].task} from ${d.waitFor[0].terminal}"
    checkMethod: "TaskGet('${d.waitFor[0].task}').status == 'completed'"
  `).join('\n')
}
```

### 10.6 Autonomous Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    AUTONOMOUS EXECUTION FLOW                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Orchestrator                                                       │
│       │                                                             │
│       ▼                                                             │
│  /orchestrate → Creates Tasks + autonomousExecution config          │
│       │                                                             │
│       ▼                                                             │
│  /assign → Sets owner for each task                                 │
│       │                                                             │
│       ├─────────────────┬─────────────────┐                         │
│       ▼                 ▼                 ▼                         │
│  Terminal-B         Terminal-C         Terminal-D                   │
│       │                 │                 │                         │
│       ▼                 ▼                 ▼                         │
│  Read prompt        Read prompt        Read prompt                  │
│       │                 │                 │                         │
│       ▼                 ▼                 ▼                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              AUTONOMOUS EXECUTION LOOP                      │    │
│  │                                                            │    │
│  │  1. TaskList() → Check all task status                     │    │
│  │  2. Find my pending tasks with no blockers                 │    │
│  │  3. Execute task → TaskUpdate(status="completed")          │    │
│  │  4. Repeat until all my tasks done                         │    │
│  │  5. Report completion                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                      │
│                              ▼                                      │
│                    All terminals complete                           │
│                              │                                      │
│                              ▼                                      │
│                    /collect (verify)                                │
│                              │                                      │
│                              ▼                                      │
│                    /synthesis (finalize)                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 11. Future Enhancements

1. **Template support:** Pre-defined orchestration templates
2. **Auto-recovery:** Resume interrupted orchestration
3. **Visualization:** ASCII dependency graph
4. **Estimation:** Time estimates per phase
5. **Optimization:** Auto-detect parallelizable phases
6. **Autonomous Mode:** Self-healing task execution

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
| `task-params.md` | ✅ | Task decomposition + dependencies |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Task orchestration engine |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |
| 3.0.0 | Autonomous Execution Protocol 추가 |
| 3.1.0 | Multi-project isolation: `--plan-slug` 지원, 프로젝트별 context/progress 파일 분리 |

---

**End of Skill Documentation**

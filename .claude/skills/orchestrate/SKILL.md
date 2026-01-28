---
name: orchestrate
description: |
  Break down complex tasks into phases, create Native Tasks with dependencies,
  and generate worker prompts. Pure task decomposition - no owner assignment.
  Use /assign for terminal assignment after orchestration.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "4.0.0"
argument-hint: "--plan-slug <slug> | <task-description>"
hooks:
  Setup:
    - shared/validation-feedback-loop.sh  # P4/P6: Load feedback loop module
  PreToolUse:
    - type: command
      command: "/home/palantir/.claude/hooks/orchestrate-validate.sh"
      timeout: 30000
      matcher: "TaskCreate"
# P1: Agent Delegation (Sub-Orchestrator Mode)
agent_delegation:
  enabled: true  # Can operate as sub-orchestrator
  max_sub_agents: 5  # Maximum parallel decomposition agents
  delegation_strategy: "complexity-based"  # Delegate by task complexity
  description: |
    When task complexity is high (>5 phases), decompose into sub-orchestrations.
    Each sub-agent handles specific domain (e.g., frontend tasks, backend tasks, infra tasks).
# P4: Selective Feedback for Gate 4
selective_feedback:
  enabled: true
  severity_filter: "warning"  # Only pass warnings and above
  feedback_targets:
    - gate: "ORCHESTRATE"
      severity: ["error", "warning"]
      action: "block_on_error"  # Block on errors, warn on warnings
    - gate: "DEPENDENCY"
      severity: ["error"]
      action: "block"  # Always block on dependency errors
  description: |
    Severity-based filtering for Gate 4 validation warnings.
    Errors block task creation. Warnings are logged but allow continuation.
# P6: Agent Internal Feedback Loop
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "Each phase has clear completion criteria"
    - "Dependencies form DAG (no cycles)"
    - "Target files are specified for each phase"
    - "Phase count is reasonable (3-10)"
  refinement_triggers:
    - "Missing completion criteria detected"
    - "Circular dependency detected"
    - "Phase too large (>3 target files)"
  description: |
    Local decomposition refinement loop before task creation.
    Self-validates phase breakdown and iterates until quality threshold met.
---

# /orchestrate - Task Decomposition Engine

> **Version:** 4.0
> **Role:** Pure task decomposition + Native Task creation + Worker prompt generation
> **Architecture:** Hybrid (Native Task System + File-Based Prompts)
> **Note:** Does NOT assign owners - use /assign for terminal assignment

---

## 1. Purpose

**Task Decomposition Engine** that:
1. Breaks down complex tasks into phases
2. Creates Native Tasks via `TaskCreate`
3. Sets up dependencies via `TaskUpdate(addBlockedBy)`
4. Generates worker prompt files (`.agent/prompts/`)
5. Initializes workload-specific context and progress tracking

**What /orchestrate does NOT do:**
- Does NOT assign tasks to terminals (use `/assign`)
- Does NOT include autonomous execution logic (handled by `/worker`)
- Does NOT set `owner` field on tasks (remains null until `/assign`)

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

// 1c. Generate workload ID with timestamp
const workloadId = Bash(`source .claude/skills/shared/slug-generator.sh && generate_workload_id "${projectSlug}"`).trim()
const workloadSlug = Bash(`source .claude/skills/shared/slug-generator.sh && generate_slug_from_workload "${workloadId}"`).trim()

// 2. Use Chain of Thought to decompose
analysis = analyzeTask(input)
analysis.projectSlug = projectSlug  // Attach for file generation
analysis.workloadId = workloadId    // Full workload ID
analysis.workloadSlug = workloadSlug // Derived slug for directories
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

### 3.2 Phase 2: Gate 4 Validation with Selective Feedback (Shift-Left + P4)

```javascript
// Gate 4: Validate phase dependencies BEFORE creating tasks
// P4: Uses selective_feedback to filter by severity
console.log("🔍 Running Gate 4: Phase dependency validation...")

const phasesJson = JSON.stringify(analysis.phases.map(p => ({
  id: p.id,
  dependencies: p.dependencies || []
})))

const gate4Result = await validatePhaseDependencies(phasesJson)

// P4: Selective Feedback - Filter by severity
const selectiveFeedback = applySelectiveFeedback(gate4Result, {
  gate: "ORCHESTRATE",
  severityFilter: "warning",  // Only pass warnings and above
  action: "block_on_error"    // Block on errors, warn on warnings
})

if (selectiveFeedback.shouldBlock) {
  console.log("❌ Gate 4 FAILED - Fix errors before creating tasks:")
  selectiveFeedback.errors.forEach(e => console.log(`   - ${e}`))
  return { status: "gate4_failed", errors: selectiveFeedback.errors }
}

// P4: Log warnings but allow continuation
if (selectiveFeedback.warnings.length > 0) {
  console.log("⚠️  Gate 4 warnings (non-blocking):")
  selectiveFeedback.warnings.forEach(w => console.log(`   - ${w}`))
  // Log to validation log for later review
  logValidationWarnings("ORCHESTRATE", selectiveFeedback.warnings)
}

console.log("✅ Gate 4 PASSED - Proceeding to workload initialization")
```

#### P4: Selective Feedback Helper

```javascript
function applySelectiveFeedback(gateResult, config) {
  const { severityFilter, action } = config

  // Filter by severity
  const severityLevels = { "error": 3, "warning": 2, "info": 1 }
  const minLevel = severityLevels[severityFilter] || 2

  const filteredErrors = gateResult.errors || []
  const filteredWarnings = (gateResult.warnings || []).filter(w => {
    // Keep warnings that meet severity threshold
    return severityLevels["warning"] >= minLevel
  })

  // Determine blocking behavior
  let shouldBlock = false
  if (action === "block_on_error") {
    shouldBlock = filteredErrors.length > 0
  } else if (action === "block") {
    shouldBlock = filteredErrors.length > 0 || filteredWarnings.length > 0
  }

  return {
    shouldBlock,
    errors: filteredErrors,
    warnings: filteredWarnings,
    originalResult: gateResult.result
  }
}

function logValidationWarnings(gate, warnings) {
  const logPath = ".agent/logs/validation_gates.log"
  const timestamp = new Date().toISOString()
  const logEntry = warnings.map(w => `[${timestamp}] [${gate}] [WARNING] ${w}`).join('\n')

  Bash(`echo "${logEntry}" >> ${logPath}`)
}
```

### 3.3 Phase 3: Initialize Workload Directory (Validate-Before-Create)

```javascript
// Initialize workload directory BEFORE creating tasks
// This ensures all file paths exist when workers reference them

const workloadId = analysis.workloadId
const workloadSlug = analysis.workloadSlug

// Source workload management
Bash(`source .claude/skills/shared/workload-tracker.sh && init_workload_directories "${workloadId}"`)

// Set as active workload
Bash(`source .claude/skills/shared/workload-files.sh && set_active_workload "${workloadId}"`)

// Get prompt directory path for reference
const workloadPromptDir = `.agent/prompts/${workloadSlug}`

console.log(`📁 Workload directory initialized: ${workloadPromptDir}`)
```

### 3.4 Phase 4: Native Task Creation

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

### 3.5 Phase 5: Dependency Setup

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

### 3.6 Phase 6: Generate Context Files

> **V3.1 Multi-Project Isolation**: Uses project-specific filenames to avoid conflicts

#### _context-{workloadSlug}.yaml

```javascript
const workloadId = analysis.workloadId      // From Phase 1 (full ID)
const workloadSlug = analysis.workloadSlug  // From Phase 1 (slug for directories)

contextContent = `
version: "1.0"
workload_id: "${workloadId}"
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
    owner: "unassigned"  # Use /assign to set owner
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
  file_path: `.agent/prompts/${workloadSlug}/_context.yaml`,
  content: contextContent
})
```

#### _progress-{workloadSlug}.yaml

```javascript
progressContent = `
version: "1.0"
workload_id: "${workloadId}"
projectId: "${analysis.project}"
lastUpdated: "${new Date().toISOString()}"

terminals:
  # Terminal assignments will be added by /assign
  # Format: terminal-b, terminal-c, terminal-d
${analysis.phases.map((p, i) => `
  terminal-${String.fromCharCode(98 + i)}:
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
    owner: "unassigned"  # Use /assign to set owner
    startedAt: null
    completedAt: null
`).join('\n')}

completedTasks: []
blockers: []
`

Write({
  file_path: `.agent/prompts/${workloadSlug}/_progress.yaml`,
  content: progressContent
})
```

### 3.7 Phase 7: Generate Worker Prompt Files

```javascript
// Initialize workload directory structure (using slug for directory name)
Bash(`source .claude/skills/shared/workload-files.sh && init_workload_directory "${workloadSlug}"`)
Bash(`source .claude/skills/shared/workload-files.sh && set_active_workload "${workloadId}"`)

// Workload directory uses slug, but active workload tracks full ID
workloadPromptDir = `.agent/prompts/${workloadSlug}`

for (phase of analysis.phases) {
  workerPromptContent = `
# =============================================================================
# Worker Task: Phase ${phase.index} - ${phase.name}
# =============================================================================
# Read this file AFTER reading _context.yaml in workload directory
#
# Location: ${workloadPromptDir}/pending/worker-phase-${phase.index}-task.yaml
# Language: English (Machine-Readable)
# =============================================================================

taskId: "${phase.id}"
nativeTaskId: "${taskMap[phase.id]}"
assignedTo: "unassigned"  # Use /assign to set owner
orchestrator: "orchestrate"
createdAt: "${new Date().toISOString()}"

# =============================================================================
# CONTEXT REFERENCE
# =============================================================================
workload_id: "${workloadId}"
contextFile: "${workloadPromptDir}/_context.yaml"
progressFile: "${workloadPromptDir}/_progress.yaml"

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
# VALIDATION CRITERIA (P6: For internal feedback loop)
# =============================================================================
validation_criteria:
  required:
    - "All target files modified as specified"
    - "Completion criteria met"
    - "No regressions in existing tests"
  optional:
    - "Code follows existing patterns"
    - "Documentation updated if applicable"
  self_check: |
    Before marking complete, verify:
    1. All targetFiles have been modified
    2. Each completionCriteria item is satisfied
    3. Run verificationSteps commands and confirm expected output

# =============================================================================
# ON COMPLETE
# =============================================================================
onComplete:
  - "TaskUpdate(taskId='${taskMap[phase.id]}', status='completed')"
  - "Update ${workloadPromptDir}/_progress.yaml: worker status = 'completed'"
  - "Report to Orchestrator with L1 summary"
  ${phase.index < analysis.phases.length - 1 ? `- "Notify next worker that ${phase.dependencies[0] || 'this phase'} is complete"` : ''}
`

  filename = `worker-phase-${phase.index}-${projectSlug}-task.yaml`

  Write({
    file_path: `${workloadPromptDir}/pending/${filename}`,
    content: workerPromptContent
  })

  // Link prompt file to Native Task
  TaskUpdate({
    taskId: taskMap[phase.id],
    metadata: {
      promptFile: `${workloadPromptDir}/pending/${filename}`,
      phaseId: phase.id,
      priority: phase.priority || "P1"
    }
  })

  console.log(`📄 Created prompt: ${filename}`)
}
```

### 3.8 Phase 8: Summary Output

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
    - Owner: unassigned (use /assign)
    - Blocked by: ${p.dependencies.length > 0 ? p.dependencies.map(d => `Task #${taskMap[d]}`).join(', ') : 'None (can start immediately)'}
    - Prompt: .agent/prompts/pending/worker-phase-${i+1}-task.yaml
`).join('\n')}

Files Generated:
  ✅ .agent/prompts/_context-${projectSlug}.yaml (project context)
  ✅ .agent/prompts/_progress-${projectSlug}.yaml (progress tracker)
${analysis.phases.map((p, i) => `  ✅ .agent/prompts/pending/worker-phase-${i+1}-${projectSlug}-task.yaml`).join('\n')}

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

### 4.1 analyzeTask(input) with P6 Internal Feedback Loop

Uses CoT to break down task with self-validation loop:

```javascript
function analyzeTask(input) {
  // P6: Internal feedback loop for decomposition quality
  const maxIterations = 3
  let iteration = 0
  let analysis = null
  let validationResult = null

  while (iteration < maxIterations) {
    iteration++
    console.log(`🔄 Decomposition iteration ${iteration}/${maxIterations}`)

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

${iteration > 1 ? `
## Previous Iteration Feedback
The previous decomposition had issues:
${validationResult.issues.map(i => `- ${i}`).join('\n')}

Please refine the decomposition to address these issues.
` : ''}

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

    const parsed = JSON.parse(analysis)

    // P6: Validate decomposition quality
    validationResult = validateDecomposition(parsed)

    if (validationResult.isValid) {
      console.log(`✅ Decomposition validated on iteration ${iteration}`)
      return parsed
    }

    console.log(`⚠️  Decomposition needs refinement:`)
    validationResult.issues.forEach(i => console.log(`   - ${i}`))
  }

  // Max iterations reached - return best effort with warning
  console.log(`⚠️  Max iterations reached. Using current decomposition with warnings.`)
  return JSON.parse(analysis)
}
```

#### P6: Decomposition Validation

```javascript
function validateDecomposition(analysis) {
  const issues = []

  // Validation criteria from agent_internal_feedback_loop config
  const criteria = {
    hasCompletionCriteria: true,
    noCycles: true,
    hasTargetFiles: true,
    reasonablePhaseCount: true
  }

  // Check 1: Each phase has clear completion criteria
  for (const phase of analysis.phases) {
    if (!phase.completionCriteria || phase.completionCriteria.length === 0) {
      issues.push(`Phase "${phase.name}" missing completion criteria`)
      criteria.hasCompletionCriteria = false
    }
  }

  // Check 2: Dependencies form DAG (no cycles)
  const cycles = detectCycles(analysis.phases)
  if (cycles.length > 0) {
    issues.push(`Circular dependency detected: ${cycles.join(' → ')}`)
    criteria.noCycles = false
  }

  // Check 3: Target files are specified for each phase
  for (const phase of analysis.phases) {
    if (!phase.targetFiles || phase.targetFiles.length === 0) {
      issues.push(`Phase "${phase.name}" missing target files`)
      criteria.hasTargetFiles = false
    }
  }

  // Check 4: Phase count is reasonable (3-10)
  if (analysis.phases.length < 1) {
    issues.push(`No phases defined`)
    criteria.reasonablePhaseCount = false
  } else if (analysis.phases.length > 10) {
    issues.push(`Too many phases (${analysis.phases.length}) - consider sub-orchestration`)
    criteria.reasonablePhaseCount = false
  }

  // Check 5: Phase not too large (refinement trigger)
  for (const phase of analysis.phases) {
    if (phase.targetFiles && phase.targetFiles.length > 3) {
      issues.push(`Phase "${phase.name}" too large (${phase.targetFiles.length} files) - consider splitting`)
    }
  }

  const isValid = Object.values(criteria).every(v => v === true)

  return { isValid, issues, criteria }
}
```
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

**Core Functionality:**
- [ ] Single-phase task (no dependencies)
- [ ] Multi-phase linear task (A → B → C)
- [ ] Multi-phase parallel task (A, B → C)
- [ ] Diamond dependency (A → B, C → D)
- [ ] Circular dependency detection
- [ ] File overwrite handling
- [ ] TaskCreate error handling
- [ ] Large task (>5 phases)

**P1: Agent Delegation (Sub-Orchestrator):**
- [ ] agent_delegation config present
- [ ] max_sub_agents set to 5
- [ ] delegation_strategy is "complexity-based"
- [ ] Can delegate large tasks (>5 phases)

**P4: Selective Feedback:**
- [ ] selective_feedback config present
- [ ] Errors block task creation
- [ ] Warnings logged but don't block
- [ ] Validation warnings logged to .agent/logs/validation_gates.log
- [ ] Severity filter works correctly

**P6: Internal Feedback Loop:**
- [ ] agent_internal_feedback_loop config present
- [ ] Max 3 iterations for decomposition
- [ ] Validates completion criteria presence
- [ ] Validates DAG (no cycles)
- [ ] Validates target files presence
- [ ] Validates phase count (3-10)
- [ ] Worker prompts include validation_criteria section

---

## 9. Performance Targets

| Operation | Target | Actual |
|-----------|--------|--------|
| Task analysis | <10s | TBD |
| TaskCreate (per task) | <500ms | TBD |
| File generation (per file) | <100ms | TBD |
| Total orchestration | <30s | TBD |

---

## 10. Future Enhancements

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
| `model-selection.md` | ✅ | `model: opus` for complex decomposition |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: Task delegation pattern |
| `hook-config.md` | ✅ | PreToolUse hook: orchestrate-validate.sh |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | ✅ | Task decomposition + dependencies |
| `feedback-loop.md` | ✅ | P6: Internal feedback loop for decomposition |
| `selective-feedback.md` | ✅ | P4: Severity-based Gate 4 filtering |

### Version History

| Version | Change |
|---------|--------|
| 1.0.0 | Task orchestration engine |
| 2.1.0 | V2.1.19 Spec 호환, task-params 통합 |
| 3.0.0 | Autonomous Execution Protocol 추가 |
| 3.1.0 | Multi-project isolation: `--plan-slug` 지원, 프로젝트별 context/progress 파일 분리 |
| 4.1.0 | **P1**: Added agent_delegation (sub-orchestrator mode) |
| | **P4**: Added selective_feedback for Gate 4 (severity-based filtering) |
| | **P6**: Added agent_internal_feedback_loop (decomposition self-validation) |
| | Worker prompts now include validation_criteria section |

---

**End of Skill Documentation**

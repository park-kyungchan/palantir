---
name: orchestrate
description: |
  Break down complex tasks, create Native Tasks, generate worker prompts,
  set up dependencies for multi-terminal parallel execution.
user-invocable: true
disable-model-invocation: false
context: standard
model: opus
version: "2.1.0"
argument-hint: "<task-description>"
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
// 1. Parse user input
input = args[0]

// 2. Use Chain of Thought to decompose
analysis = analyzeTask(input)
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

### 3.2 Phase 2: Native Task Creation

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

#### _context.yaml

```javascript
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
  - "Update _progress.yaml after completion"
  - "Report in L1/L2/L3 format"
  - "Check blockedBy before starting work"

referenceFiles: ${JSON.stringify(analysis.referenceFiles || [])}
`

Write({
  file_path: ".agent/prompts/_context.yaml",
  content: contextContent
})
```

#### _progress.yaml

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
  file_path: ".agent/prompts/_progress.yaml",
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
# Read this file AFTER reading _context.yaml
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
contextFile: ".agent/prompts/_context.yaml"
progressFile: ".agent/prompts/_progress.yaml"

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
  Check .agent/prompts/_progress.yaml
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
  - "Update .agent/prompts/_progress.yaml: ${phase.suggestedOwner}.status = 'completed'"
  - "Report to Orchestrator with L1 summary"
  ${phase.index < analysis.phases.length - 1 ? `- "Notify next worker that ${phase.dependencies[0] || 'this phase'} is complete"` : ''}
`

  filename = phase.suggestedOwner
    ? `worker-${phase.suggestedOwner}-task.yaml`
    : `worker-${String.fromCharCode(97 + phase.index)}-task.yaml`

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
  ✅ .agent/prompts/_context.yaml (global context)
  ✅ .agent/prompts/_progress.yaml (progress tracker)
${analysis.phases.map((p, i) => `  ✅ .agent/prompts/pending/worker-${p.suggestedOwner || String.fromCharCode(97 + i)}-task.yaml`).join('\n')}

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

## 5. Error Handling

| Error | Detection | Recovery |
|-------|-----------|----------|
| **Invalid input** | Empty or malformed task description | Prompt user for clarification |
| **Too many phases** | > 10 phases | Ask user to break down further |
| **Circular dependency** | A → B → A | Reject, ask user to fix |
| **File conflicts** | _context.yaml already exists | Ask: overwrite or append? |
| **TaskCreate failure** | Native API error | Log error, abort orchestration |

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

## 10. Future Enhancements

1. **Template support:** Pre-defined orchestration templates
2. **Auto-recovery:** Resume interrupted orchestration
3. **Visualization:** ASCII dependency graph
4. **Estimation:** Time estimates per phase
5. **Optimization:** Auto-detect parallelizable phases

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

---

**End of Skill Documentation**

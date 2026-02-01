# Task API Integration Guideline

> **Version:** 2.0.0 | **Last Updated:** 2026-02-01
> **Purpose:** Comprehensive TodoWrite System, Dynamic Schedule Management, Hook-based Behavioral Enforcement

---

## [PERMANENT] Pre-Task Mandatory Checklist

> **CRITICAL:** The following items MUST be performed before starting any task.

### Why is [PERMANENT] Context Check Mandatory?

```
┌─────────────────────────────────────────────────────────────────────────┐
│  🎯 Core Principle: Main Agent performs ONLY Orchestrator-Role          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Main Agent Responsibilities:                                            │
│    ✅ Achieve holistic context awareness → Synthesize L2/L3 outputs     │
│    ✅ Orchestrate sub-tasks → Create/assign Tasks with dependencies     │
│    ✅ Configure dependency chains → Set up blockedBy relationships      │
│    ❌ Direct implementation (Worker responsibility)                      │
│                                                                          │
│  Without [PERMANENT] Context Check:                                      │
│    ❌ "Missing the forest for the trees" → Inter-task inconsistency     │
│    ❌ Missing details → Incorrect dependency configuration               │
│    ❌ Unknown impact scope → Quality degradation and rework              │
│                                                                          │
│  Correct Workflow:                                                       │
│    1. Read ALL L2 outputs → Horizontal Analysis (cross-agent synthesis) │
│    2. Read ALL L3 outputs → Vertical Analysis (deep insights)           │
│    3. Achieve holistic context → Proceed with next Orchestrating        │
│    4. Loop: Receive results → L2/L3 synthesis → Next Orchestrating →... │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1. Context Recovery

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️  Importance of Maintaining Holistic Context Awareness   │
├─────────────────────────────────────────────────────────────┤
│  After Auto-Compact, proceed with summary only → FORBIDDEN  │
│  Guessing file paths/contents → FORBIDDEN                   │
│  Proceeding with "remembered" information → FORBIDDEN       │
│  Orchestrating based on L1 summary only → FORBIDDEN         │
└─────────────────────────────────────────────────────────────┘
```

**Mandatory Files to Check:**
1. `.agent/prompts/_active_workload.yaml` → Verify active workload slug
2. TaskList → Check current Task status
3. Related L1/L2/L3 output files → Restore detailed context

**Why Read Up to L3?**
| Level | Content | Context Awareness Level |
|-------|---------|------------------------|
| L1 | Summary (500 tokens) | ❌ Insufficient - Overview only |
| L2 | Detailed Analysis | ⚠️ Moderate - Implementation level |
| L3 | Deep Insights | ✅ Sufficient - Holistic context |

> **Rule:** Only by reading up to L3 can you accurately understand "What am I doing in the overall workflow?"

### 1.1 L2→L3 Progressive-Deep-Dive (Meta-Level Pattern)

> **CRITICAL:** For improvement/enhancement/refinement tasks, proceeding with L1 summary only is **FORBIDDEN**

```
┌──────────────────────────────────────────────────────────────────┐
│  L2→L3 Progressive-Deep-Dive Pattern (Meta-Level)                │
├──────────────────────────────────────────────────────────────────┤
│  1. Review L1 summary → Understand overall structure (overview)  │
│  2. Synthesize L2 detail files → Understand implementation       │
│  3. Deep-dive L3 analysis → Derive improvements (insights)       │
│  4. Proceed with actual work → Based on L2+L3 only               │
└──────────────────────────────────────────────────────────────────┘
```

#### Progressive-Deep-Dive Phase Rules

| Phase | Files to Read | Purpose | Work Permitted |
|-------|---------------|---------|----------------|
| **L1 Phase** | `*_summary.yaml` | Structure overview | ❌ No work allowed |
| **L2 Phase** | `l2_detailed.md`, `*_analysis.md` | Implementation understanding | ⚠️ Simple tasks only |
| **L3 Phase** | `l3_synthesis.md`, `*_deep.md` | Insight derivation | ✅ All work allowed |

#### Workflow Example

```javascript
// ❌ WRONG: Starting work after reading L1 only
Read("research.md")  // L1 summary only
Edit("target.py")    // Editing with incomplete context → errors occur

// ✅ CORRECT: L2→L3 Progressive-Deep-Dive
Read("research.md")              // L1: Structure overview
Read("research/l2_detailed.md")  // L2: Implementation understanding
Read("research/l3_synthesis.md") // L3: Insight acquisition
// Now proceed with complete context
Edit("target.py")                // Accurate modification possible
```

#### Applying L2→L3 for Parallel Agent Delegation

```javascript
// Progressive-Deep-Dive after collecting parallel Agent results
const agentResults = await Promise.all([
  Task({ subagent_type: "Explore", prompt: "analyze agents/" }),
  Task({ subagent_type: "Explore", prompt: "analyze skills/" }),
  Task({ subagent_type: "Explore", prompt: "analyze hooks/" })
])

// Step 1: L1 Synthesis (overview understanding)
agentResults.forEach(r => summarizeL1(r.output))

// Step 2: L2 Detail Synthesis (implementation understanding)
Read(".agent/outputs/Explore/agents_l2.md")
Read(".agent/outputs/Explore/skills_l2.md")
Read(".agent/outputs/Explore/hooks_l2.md")

// Step 3: L3 Deep Synthesis (insight derivation)
// → Cross-analysis, pattern discovery, improvement derivation

// Step 4: Proceed with actual improvement work
```

### 2. Comprehensive TodoWrite Creation

Before starting any non-trivial task (3+ steps):

```javascript
// Step 1: Create [PERMANENT] Task (always at the top)
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  description: "Context recovery and status verification before starting work",
  activeForm: "Checking context and recovery status",
  metadata: {
    priority: "CRITICAL",
    phase: "permanent",
    tags: ["permanent", "context-recovery"]
  }
})

// Step 2: Create actual work Tasks
TaskCreate({
  subject: "Actual Task 1",
  description: "Detailed description",
  activeForm: "Working on task 1",
  metadata: {
    priority: "HIGH",
    phase: "phase-1"
  }
})
```

### 2.1 [PERMANENT] Task Lifecycle Rules

> **CRITICAL:** `[PERMANENT]` tasks are for **continuous reference** and MUST NOT be marked completed until all work is done

```
┌─────────────────────────────────────────────────────────────────┐
│  [PERMANENT] Task Lifecycle                                      │
├─────────────────────────────────────────────────────────────────┤
│  1. Work start → status: "in_progress" (initial setting)        │
│  2. Work in progress → status: "in_progress" maintained         │
│  3. All work complete → status: "completed" (final stage only)  │
├─────────────────────────────────────────────────────────────────┤
│  ⚠️ Marking completed mid-work → Risk of context loss           │
└─────────────────────────────────────────────────────────────────┘
```

#### [PERMANENT] Task Completion Conditions

| Condition | Check |
|-----------|-------|
| All Phase Tasks are completed | ✅ |
| Verification Task (Phase 6 etc.) is completed | ✅ |
| Final commit/PR creation completed | ✅ |

```javascript
// ❌ WRONG: Marking [PERMANENT] completed mid-work
TaskUpdate({ taskId: permanentTask.id, status: "completed" })  // Other work still in progress
// → Cannot reference continuously, risk of context loss

// ✅ CORRECT: Mark completed only after all work is done
if (allPhasesCompleted && verificationDone && commitCreated) {
  TaskUpdate({ taskId: permanentTask.id, status: "completed" })
}
```

### 3. Dependency Chain Configuration

```
[PERMANENT] Context Check
        ↓
    Phase 1 Tasks (can run in parallel)
        ↓
    Phase 2 Tasks (after Phase 1 completion)
        ↓
    Verification & Summary
```

---

## Task API Usage Patterns

### Pattern 1: Linear Chain (Sequential Execution)

```javascript
task1 = TaskCreate({ subject: "Step 1", ... })
task2 = TaskCreate({ subject: "Step 2", ... })
task3 = TaskCreate({ subject: "Step 3", ... })

TaskUpdate({ taskId: task2.id, addBlockedBy: [task1.id] })
TaskUpdate({ taskId: task3.id, addBlockedBy: [task2.id] })
```

### Pattern 2: Diamond (Parallel → Convergence)

```javascript
setup = TaskCreate({ subject: "Setup", ... })
taskA = TaskCreate({ subject: "Task A", ... })
taskB = TaskCreate({ subject: "Task B", ... })
merge = TaskCreate({ subject: "Merge Results", ... })

TaskUpdate({ taskId: taskA.id, addBlockedBy: [setup.id] })
TaskUpdate({ taskId: taskB.id, addBlockedBy: [setup.id] })
TaskUpdate({ taskId: merge.id, addBlockedBy: [taskA.id, taskB.id] })
```

### Pattern 3: Phase-based (Step-by-Step)

```javascript
// Phase markers in metadata
TaskCreate({
  subject: "Phase 1: Research",
  metadata: { phase: "research", phaseId: "P1" }
})

TaskCreate({
  subject: "Phase 2: Implementation",
  metadata: { phase: "implementation", phaseId: "P2" }
})

// Query by phase
const researchTasks = TaskList().filter(t =>
  t.metadata?.phase === "research"
)
```

---

## Priority Levels

| Priority | When to Use | Examples |
|----------|-------------|----------|
| `CRITICAL` | Immediate action required, blocker | [PERMANENT] items, security issues |
| `HIGH` | Core functionality, main work | Major implementation Tasks |
| `MEDIUM` | General work | Refactoring, improvements |
| `LOW` | Can be done later | Documentation, cleanup |

---

## Metadata Usage Rules

### Required Metadata

```javascript
metadata: {
  priority: "CRITICAL|HIGH|MEDIUM|LOW",  // Priority level
  phase: "phase-name",                    // Phase name
  tags: ["tag1", "tag2"]                  // Classification tags
}
```

### Optional Metadata

```javascript
metadata: {
  owner: "terminal-b",           // Assignee
  parentTaskId: "task-123",      // Parent Task (hierarchy)
  source: "skill:orchestrate",   // Creation source
  promptFile: "path/to/prompt",  // Worker prompt file
  estimatedTime: "30m",          // Estimated duration
  actualTime: "25m"              // Actual duration
}
```

---

## Dynamic Schedule Management

### Progress Tracking

```javascript
const tasks = TaskList()
const total = tasks.length
const completed = tasks.filter(t => t.status === "completed").length
const inProgress = tasks.filter(t => t.status === "in_progress").length
const blocked = tasks.filter(t => t.blockedBy?.length > 0).length

console.log(`
Progress: ${(completed/total*100).toFixed(1)}%
- Completed: ${completed}
- In Progress: ${inProgress}
- Blocked: ${blocked}
- Pending: ${total - completed - inProgress}
`)
```

### Automatic Unblock When Blocker Completes

When a Task is completed, other Tasks that have it in their `blockedBy` list are automatically unblocked.

```javascript
// When task1 completes
TaskUpdate({ taskId: task1.id, status: "completed" })
// → task2, task3 etc. that have task1 in blockedBy are automatically unblocked
```

---

## Workflow Templates

### Starting New Work

```javascript
// 1. [PERMANENT] Context Check
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  description: `
    1. Verify _active_workload.yaml
    2. Check current status via TaskList
    3. Read related L1/L2/L3 files
    4. Restore previous work context
  `,
  activeForm: "Checking context",
  metadata: { priority: "CRITICAL", phase: "permanent" }
})

// 2. Work Breakdown
TaskCreate({
  subject: "Work breakdown and planning",
  description: "Decompose entire work into phases",
  activeForm: "Planning work breakdown",
  metadata: { priority: "HIGH", phase: "planning" }
})

// 3. Actual Work Tasks
// ... (add per task)

// 4. Verification and Summary
TaskCreate({
  subject: "Verification and result summary",
  description: "Confirm all work completion and document results",
  activeForm: "Verifying and summarizing",
  metadata: { priority: "HIGH", phase: "verification" }
})
```

---

## Anti-Patterns (Patterns to Avoid)

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|------------------|
| Starting work without Task | Cannot track, context loss | TaskCreate first |
| Omitting [PERMANENT] | Missing context recovery | Always include at top |
| Sequential work without dependencies | Lost parallelization opportunity | Use addBlockedBy |
| Not using metadata | Cannot classify/filter | priority, phase required |
| Not updating status | Cannot track progress | in_progress → completed |

---

## Checklist

Before starting work:
- [ ] Create [PERMANENT] Context Check Task
- [ ] Verify _active_workload.yaml
- [ ] Check current status via TaskList
- [ ] Read related files (L1/L2/L3)

During work:
- [ ] Update Task status to in_progress
- [ ] Follow dependency chain
- [ ] Record progress in metadata

After work completion:
- [ ] Update Task status to completed
- [ ] Document results
- [ ] Verify next Task is unblocked

---

> **Remember:** Maintaining holistic context awareness throughout work is the key to quality.
> The [PERMANENT] pattern is a safeguard to ensure this.

---

## Agent Integration Patterns

### Agent List and Task API Integration

| Agent | Role | Task API | Model |
|-------|------|----------|-------|
| `onboarding-guide` | New user guidance | ✗ | haiku |
| `pd-readonly-analyzer` | Read-only analysis | ✓ (delegatable) | haiku |
| `pd-skill-loader` | Skill pre-loading | ✗ | sonnet |
| `ontology-roadmap` | ODA roadmap document | ✗ | - |

### Agent Delegation Pattern

```javascript
// Safe code analysis via pd-readonly-analyzer
Task({
  subagent_type: "pd-readonly-analyzer",
  prompt: "Analysis request...",
  run_in_background: true
})
// Result: Saved in L1/L2/L3 format to .agent/outputs/
```

### Agent Patterns

| Pattern | Agent | Description |
|---------|-------|-------------|
| **A1: Tool Restrictions** | pd-readonly-analyzer | Prevent modifications via `disallowedTools` |
| **A2: Skill Injection** | pd-skill-loader | Pre-load skills without runtime discovery |

---

## Skill Integration Patterns

### E2E Pipeline and Task API

```
/clarify ────────────────────────► (Task API not used)
    │
    ▼
/research ───────────────────────► Task(Explore) × N (parallel)
    │
    ▼
/planning ───────────────────────► Task(Plan) × N (parallel)
    │
    ▼
/orchestrate ────────────────────► TaskCreate() × N  ⭐ Only Task creation point
                                   TaskUpdate(addBlockedBy)
    │
    ▼
/assign ─────────────────────────► TaskUpdate(owner)  ⭐ Ownership assignment
    │
    ▼
/worker (parallel) ──────────────► TaskUpdate(status)
                                   TaskCreate() (in Sub-Orchestrator mode)
    │
    ▼
/collect ────────────────────────► TaskList() (completion check)
    │
    ▼
/synthesis ──────────────────────► Decision: COMPLETE | ITERATE
    │
    ├── COMPLETE ──────────────► /commit-push-pr
    └── ITERATE ───────────────► /rsil-plan → /orchestrate
```

### Task API Usage Pattern by Skill

| Skill | TaskCreate | TaskUpdate | TaskList | TaskGet |
|-------|------------|------------|----------|---------|
| `/orchestrate` | ✓ (only) | ✓ (dependencies) | - | - |
| `/assign` | - | ✓ (owner) | ✓ (auto) | ✓ |
| `/worker` | ✓ (Sub-Orch) | ✓ (status) | - | ✓ |
| `/collect` | - | - | ✓ | - |
| `/synthesis` | - | - | - | - |

---

## Orchestrator / Sub-Orchestrator Pattern

### Hierarchy Structure

```
┌─────────────────────────────────────────────────────────────┐
│  Main Orchestrator (Terminal A)                             │
│  - Decompose entire work with TaskCreate                    │
│  - Set dependencies with TaskUpdate(addBlockedBy)           │
│  - Assign to Terminal B,C,D via /assign                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│Terminal │    │Terminal │    │Terminal │
│    B    │    │    C    │    │    D    │
│(Worker) │    │(Sub-Orch)│   │(Worker) │
└─────────┘    └────┬────┘    └─────────┘
                    │
                    ▼
            ┌───────────────┐
            │ Sub-tasks     │
            │ (hierarchyLevel+1)
            └───────────────┘
```

### Activating Sub-Orchestrator

```javascript
// Set Sub-Orchestrator mode in /assign
TaskUpdate({
  taskId: taskId,
  owner: "terminal-c",
  metadata: {
    hierarchyLevel: 1,
    subOrchestratorMode: true,
    canDecompose: true
  }
})

// Create subtasks in /worker
TaskCreate({
  subject: "Subtask 1.1",
  metadata: {
    hierarchyLevel: 2,
    parentTaskId: parentTask.id
  }
})
```

---

## Auto-Delegation Pattern (EFL)

### Trigger Conditions

```javascript
// Skills with agent_delegation.enabled: true && default_mode: true
// Automatically operates as Sub-Orchestrator

const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
```

### Complexity-based Agent Count

| Complexity | Agent Count | Trigger Condition |
|------------|-------------|-------------------|
| simple | 1 | 1-5 requirements |
| moderate | 2 | 6-15 requirements |
| complex | 3 | 16+ requirements |

---

## Integrated Workflow Template

### Starting New Project

```javascript
// 1. [PERMANENT] Context Check
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  metadata: { priority: "CRITICAL", phase: "permanent" }
})

// 2. E2E Pipeline Tasks
TaskCreate({ subject: "Execute /clarify", metadata: { phase: "clarify" } })
TaskCreate({ subject: "Execute /research", metadata: { phase: "research" } })
TaskCreate({ subject: "Execute /planning", metadata: { phase: "planning" } })
TaskCreate({ subject: "Execute /orchestrate", metadata: { phase: "orchestrate" } })
TaskCreate({ subject: "Execute /collect", metadata: { phase: "collect" } })
TaskCreate({ subject: "Execute /synthesis", metadata: { phase: "synthesis" } })

// 3. Set dependency chain
// clarify → research → planning → orchestrate → collect → synthesis
```

---

## Core Rules Summary

1. **TaskCreate only in /orchestrate** - Other skills only manipulate existing Tasks
2. **Assignment via owner** - /assign assigns terminals via TaskUpdate(owner)
3. **Dependencies via blockedBy** - Form DAG, cycle validation at Gate 4
4. **Sub-Orchestrator support** - Worker can create subtasks
5. **[PERMANENT] required** - Context check before all work starts
6. **L1/L2/L3 outputs** - All Agent/Skill outputs use Progressive Disclosure

---

---

## Hook Integration Patterns (Code-Level Analysis)

### Hook Classification (26 total)

| Category | Hooks | Role |
|----------|-------|------|
| **Session** | session-start.sh, session-end.sh, session-health.sh | Session initialization/termination/status |
| **Pipeline Setup** | clarify-setup.sh, planning-setup.sh, orchestrate-setup.sh | Pre-skill conditions (Gate 1-4) |
| **Pipeline Finalize** | clarify-finalize.sh, planning-finalize.sh, research-finalize.sh | Post-completion handoff |
| **Validation** | clarify-validate.sh, research-validate.sh, orchestrate-validate.sh | Shift-Left validation |
| **Task Pipeline** | pd-task-interceptor.sh, pd-task-processor.sh | **L1/L2/L3 automation** |
| **Security** | permission-guard.sh, governance-check.sh | Dynamic risk detection |

### Core Task API Integration Hooks

#### 1. pd-task-interceptor.sh (PreToolUse:Task)

```yaml
Trigger: Tool == "Task" && subagent_type not in SKIP_AGENTS
Functions:
  1. Auto-inject L1/L2/L3 prompt
  2. Check cache (block if hit)
  3. Create Worker prompt file (.agent/prompts/pending/)
  4. Auto-add run_in_background=true, model="opus"
```

#### 2. pd-task-processor.sh (PostToolUse:Task)

```yaml
Trigger: After Task completion
Functions:
  1. Parse L1 fields (taskId, priority, status, l2Path...)
  2. Save to cache (~/.claude/cache/l1l2/{hash}.json)
  3. Move prompt file (pending → completed)
  4. Generate priority-based guidance
```

#### 3. session-start.sh (SessionStart)

```yaml
Functions:
  1. Post-Compact Recovery detection
     - Check _active_workload.yaml existence
     - Extract slug, current_skill, current_phase
  2. Task List continuity
     - Load pending tasks based on CLAUDE_CODE_TASK_LIST_ID
  3. Include recovery block in output JSON
```

### Hook Trigger Flow

```
Session Start
     │
     └── session-start.sh
            ├── Post-Compact Recovery detection
            └── Task List loading

Skill Invocation (/clarify, /planning, ...)
     │
     ├── {skill}-setup.sh (PreToolUse)
     │      └── Gate validation (dependencies, inputs)
     │
     └── {skill}-finalize.sh (Stop)
            └── Generate handoff (suggest next skill)

Task Tool Call
     │
     ├── pd-task-interceptor.sh (PreToolUse)
     │      ├── L1/L2/L3 prompt injection
     │      └── Cache check
     │
     └── pd-task-processor.sh (PostToolUse)
            ├── L1 parsing and caching
            └── Priority guidance generation

Subagent Lifecycle (V2.1.29)
     │
     ├── SubagentStart hook
     │      └── Log to subagent_lifecycle.log
     │
     └── SubagentStop hook
            └── Log completion to subagent_lifecycle.log
```

### V2.1.29 Subagent Lifecycle Hooks

```yaml
# V2.1.29 hooks registered in settings.json
SubagentStart:
  matcher: ".*"
  action: Log to .agent/logs/subagent_lifecycle.log
  fields: [timestamp, CLAUDE_SUBAGENT_TYPE]

SubagentStop:
  matcher: ".*"
  action: Log completion to .agent/logs/subagent_lifecycle.log
  fields: [timestamp, CLAUDE_SUBAGENT_TYPE]

# Log format
[2026-02-01T20:55:00] SubagentStart: Explore
[2026-02-01T20:55:30] SubagentStop: Explore
```

### Validation Gates (5-Stage Shift-Left)

| Gate | Hook | Validation Point | On Failure |
|------|------|------------------|------------|
| G1 | clarify-validate.sh | Before /clarify | Re-ask unclear items |
| G2 | research-validate.sh | Before /research | Confirm research scope |
| G3 | planning-preflight.sh | Before /planning | Verify plan feasibility |
| G4 | orchestrate-validate.sh | Before /orchestrate | Check dependencies |
| G5 | worker-preflight.sh | Before /worker | Resource availability |

### Code-Level Discovered Issues

| Severity | Location | Issue | Recommended Action |
|----------|----------|-------|-------------------|
| MEDIUM | session-start.sh:85 | stat platform compatibility | Python-based integration |
| MEDIUM | validation-metrics.sh:99 | bc dependency | Add fallback |
| LOW | All | Error handling (`2>/dev/null`) | Explicit logging |

---

## Section 10: Agent Integration (Code-Level Analysis V1.4.0)

### Agent Inventory (3 total)

| Agent | Model | Task API | Purpose |
|-------|-------|----------|---------|
| `onboarding-guide` | haiku | ❌ | User-facing help |
| `pd-readonly-analyzer` | haiku | ✅ | Safe read-only analysis |
| `pd-skill-loader` | sonnet | ❌ | Skill injection pattern |

### Tool Restriction Patterns

```yaml
# Pattern A1: Explicit Deny-List (pd-readonly-analyzer)
disallowedTools: [Write, Edit, Bash, NotebookEdit]
→ Result: Safe analysis, no file mutation

# Pattern A2: Skill Injection (pd-skill-loader)
skills: [pd-analyzer, pd-injector]
→ Result: Skill-based delegation instead of Task

# Pattern A3: Explicit Allow-List (onboarding-guide)
tools: [Read, mcp__sequential-thinking__sequentialthinking]
→ Result: Minimal tool access for help sessions
```

### Agent → Task Mapping Rules (Proposed)

```yaml
# Agent frontmatter → Task parameter auto-conversion

Rule 1: Tool Restriction Inheritance
  Agent.tools ∩ !Agent.disallowedTools → Task.allowed_tools

Rule 2: Background Execution Alignment
  Agent.runInBackground → Task.run_in_background (default)

Rule 3: Permission Mode Mapping
  Agent.permissionMode = "acceptEdits"
    → Task allowed_tools can include [Write, Edit]
```

---

## Section 11: Skill Integration (Code-Level Analysis V1.4.0)

### Skill Task API Usage Matrix (17 Skills)

| Skill | TaskCreate | TaskUpdate | TaskList | TaskGet | Sequential Thinking |
|-------|:-:|:-:|:-:|:-:|:-:|
| `/orchestrate` | ✅ Direct | ✅ Direct | ✓ | ✓ | ✅ |
| `/worker` | ✓ (subtasks) | ✅ Direct | ✅ Direct | ✅ Direct | ✅ |
| `/assign` | ✓ | ✓ | ✓ | ✓ | - |
| `/clarify` | ✓ (delegates) | ✓ | - | - | ✅ |
| `/research` | ✓ (delegates) | - | - | - | ✅ |
| `/planning` | ✓ (delegates) | ✓ | - | - | ✅ |
| `/collect` | - | ✓ | ✓ | - | ✅ |
| `/synthesis` | - | - | - | - | ✅ |

### EFL Pattern Implementation (P1-P6)

Implemented in all core skills:

```yaml
P1: Skill as Sub-Orchestrator
  → agent_delegation.enabled: true, default_mode: true

P2: Parallel Agent Configuration
  → agent_count_by_complexity: {simple: 1-2, complex: 3-4}

P3: Synthesis Configuration (Phase 3-A/3-B)
  → L2 horizontal cross-validation + L3 vertical verification

P4: Selective Feedback (Gate Implementation)
  → severity_filter: warning/error

P5: Phase 3.5 Review Gate
  → Main Agent review before completion

P6: Agent Internal Feedback Loop
  → max_iterations: 3, validation_criteria per skill
```

### Task Metadata Schema Extension (Proposed)

```yaml
metadata:
  # EFL Pattern Tracking
  efl_pattern:
    p1_subagent: boolean
    p2_parallel_count: integer
    p6_internal_iterations: integer

  # Workload Linkage (L2→L3 Progressive-Deep-Dive)
  workload:
    slug: string
    l1_output_path: string
    l2_output_path: string
    l3_output_path: string

  # Hierarchy (Sub-Orchestrator)
  hierarchy:
    parent_task_id: integer
    hierarchy_level: integer
    subtask_ids: [integer]

  # Gate Validation
  gates:
    - gate_name: string
      status: passed|passed_with_warnings|failed
```

---

## Section 12: Hook Integration (Code-Level Analysis V1.4.0)

### Hook Classification (27 total)

| Category | File Count | Task API Integration |
|----------|------------|----------------------|
| Session Management | 3 | ✅ Core (Task List loading, Recovery) |
| Task Pipeline | 3 | ✅ Core (L1/L2/L3 auto-injection) |
| Shift-Left Gates | 6 | ✅ Validation |
| Security & Governance | 2 | ❌ |
| Pipeline Setup/Finalize | 9 | ⚠️ Partial |
| Utility | 4 | ❌ |

### L1/L2/L3 Auto-Injection Flow

```
Task Tool Call
     │
     ├── pd-task-interceptor.sh (PreToolUse)
     │      ├── Inject L1/L2/L3 prompt template
     │      ├── Check cache hash (skip if hit)
     │      ├── Create Worker prompt file (pending/*.yaml)
     │      └── Auto-add run_in_background=true, model="opus"
     │
     └── pd-task-processor.sh (PostToolUse)
            ├── Parse L1 YAML block
            ├── Save to cache (input_hash → metadata)
            ├── Move prompt file (pending → completed)
            └── Generate priority-based guidance
```

### Platform Compatibility Issues (Recommended Actions)

| Issue | Location | Linux | macOS | Recommendation |
|-------|----------|-------|-------|----------------|
| `grep -oP` | pd-task-processor.sh | ✅ | ❌ | pcregrep or Python |
| `stat -c` | session-start.sh | ✅ | ❌ (`-f`) | Python os.stat() |
| `yq` | planning-finalize.sh | ✅ | ✅ | Unify with jq |
| `bc` | validation-metrics.sh | ✅ | ✅ | Use integer arithmetic |

### V7.1 Path Unification (REQUIRED)

```yaml
# Legacy (DEPRECATED)
.agent/outputs/{agentType}/

# V7.1 Standard (REQUIRED)
.agent/prompts/{slug}/outputs/{taskId}.md

# L1 l3Section field also needs change:
l3Section: ".agent/prompts/{slug}/outputs/{taskId}.md"  # V7.1
```

---

## Section 13: Cross-Integration Summary (L3 Synthesis)

### Cross-Component Task API Flow

```
┌──────────────────────────────────────────────────────────────┐
│  CLAUDE.md (Task System Definition)                          │
│  → Defines TaskCreate, TaskUpdate, TaskList, TaskGet         │
└──────────────────────┬───────────────────────────────────────┘
                       │
     ┌─────────────────┼─────────────────┐
     │                 │                 │
     ▼                 ▼                 ▼
┌─────────┐    ┌─────────────┐    ┌─────────────┐
│ Agents  │    │   Skills    │    │   Hooks     │
│ (3)     │    │   (17)      │    │   (27)      │
├─────────┤    ├─────────────┤    ├─────────────┤
│ Task:1/3│    │ TaskCreate  │    │ L1/L2/L3    │
│ Pattern │    │ TaskUpdate  │    │ Auto-Inject │
│ A1/A2/A3│    │ EFL P1-P6   │    │ Cache       │
└────┬────┘    └──────┬──────┘    └──────┬──────┘
     │                │                  │
     └────────────────┼──────────────────┘
                      │
                      ▼
           ┌──────────────────────┐
           │  Task API Guideline  │
           │  (This Document)     │
           │  V1.4.0              │
           └──────────────────────┘
```

### Core Improvement Priorities

| Priority | Item | Responsible Component |
|----------|------|----------------------|
| **HIGH** | Link L1/L2/L3 output paths in Task metadata | Skills + Hooks |
| **HIGH** | Document Tool Restriction Inheritance rules | Agents |
| **HIGH** | V7.1 path unification | Hooks |
| **MEDIUM** | Add blockedBy dependency examples | Agents |
| **MEDIUM** | Fix platform compatibility (grep -oP, stat -c) | Hooks |
| **LOW** | Context budget tracking system | Skills |

---

## Section 14: Integrated Roadmap (FINAL_REPORT + Guideline V1.5.0)

> **Source:** FINAL_REPORT.md Recommendations + Guideline V1.4.0 Code-Level Analysis

### Short-term (1-2 Sprint)

| Item | Source | Component | Status |
|------|--------|-----------|--------|
| Review `once: true` hook pattern | FINAL_REPORT | Hooks | ⏳ |
| Standardize Hooks timeout settings | FINAL_REPORT | Hooks | ⏳ |
| V7.1 path unification (`.agent/prompts/{slug}/`) | Guideline | Hooks | ⏳ |
| Document Tool Restriction Inheritance | Guideline | Agents | ⏳ |

### Medium-term (2-3 Sprint)

| Item | Source | Component | Status |
|------|--------|-----------|--------|
| Task metadata L1/L2/L3 path linking | Guideline | Skills + Hooks | ⏳ |
| Platform compatibility (grep -oP, stat -c) | Guideline | Hooks | ⏳ |
| Add blockedBy dependency examples | Guideline | Agents | ⏳ |
| Move Skill-specific hooks → frontmatter | FINAL_REPORT | Skills | ⏳ |

### Long-term (3+ Sprint)

| Item | Source | Component | Status |
|------|--------|-----------|--------|
| Agent registry automation | FINAL_REPORT | Agents | ⏳ |
| Lifecycle logging dashboard | FINAL_REPORT | Hooks | ⏳ |
| Context budget tracking system | Guideline | Skills | ⏳ |

---

## Section 15: INFRA Integration Verification Results (V1.5.0)

### Verification Matrix

| Verification Item | FINAL_REPORT | Guideline V1.5.0 | Consistency |
|-------------------|--------------|------------------|-------------|
| Skills count | 17 | 17 | ✅ Match |
| Hooks count | 23 | 26 | ⚠️ +3 added |
| Agents count | 4 | 3 | ⚠️ 1 moved to docs/ |
| EFL P1-P6 | P1,P2,P3,P5,P6 | P1-P6 | ✅ Complete |
| V2.1.29 hooks | SubagentStart/Stop | ✅ Added | ✅ Complete |
| Semantic Integrity | 100% | 100% | ✅ Maintained |

### Final Conclusion

```yaml
integration_status: OPTIMIZED
version_alignment:
  CLAUDE.md: V7.2
  settings.json: V2.1.29
  Task_API_Guideline: V1.5.0
  FINAL_REPORT: V2.1.29 Compliant

components:
  agents: 3 (Task API 1/3 used)
  skills: 17 (EFL P1-P6 complete)
  hooks: 26 (L1/L2/L3 auto-injection)

key_features:
  - "[PERMANENT] Context Check pattern applied"
  - "L2→L3 Progressive-Deep-Dive Meta-Level pattern"
  - "Parallel Agents Delegation Architecture"
  - "V2.1.29 SubagentStart/SubagentStop hooks"
  - "Tool Restriction Patterns (A1/A2/A3)"
```

---

## Section 16: Enforcement Architecture (V2.0.0)

> **Core Principle:** Behavioral enforcement via Hooks, not prompt-level guidance

### Architecture Overview

```
.claude/hooks/
├── enforcement/                    # Gate scripts (HARD BLOCK)
│   ├── _shared.sh                  # Common library
│   ├── context-recovery-gate.sh    # Enforce context recovery after Compact
│   ├── l2l3-access-gate.sh         # Enforce L2/L3 read before Edit/Write
│   ├── task-first-gate.sh          # Enforce TaskCreate before source code modification
│   ├── blocked-task-gate.sh        # Prevent starting Tasks with blockedBy
│   ├── output-preservation-gate.sh # Verify result saved before Task completion
│   └── security-gate.sh            # Block dangerous commands
│
└── tracking/                       # Tracker scripts (logging)
    ├── read-tracker.sh             # Log Read calls
    └── task-tracker.sh             # Log TaskCreate/Update
```

### Gate Scripts (PreToolUse - HARD BLOCK)

| Gate | Trigger | Block Condition | JSON Response |
|------|---------|-----------------|---------------|
| `context-recovery-gate.sh` | Edit\|Write\|Task | `_active_workload.yaml` exists but not read | `permissionDecision: "deny"` |
| `l2l3-access-gate.sh` | Edit\|Write | Active workload but L2/L3 not read | `permissionDecision: "deny"` |
| `task-first-gate.sh` | Edit\|Write | Source code modification but no recent TaskCreate | `permissionDecision: "deny"` |
| `blocked-task-gate.sh` | TaskUpdate | status→in_progress but blockedBy exists | `permissionDecision: "deny"` |
| `output-preservation-gate.sh` | TaskUpdate | status→completed but no outputs/ | `permissionDecision: "ask"` |
| `security-gate.sh` | Bash | Dangerous command pattern detected | `permissionDecision: "deny"` |

### Tracker Scripts (PostToolUse - Logging)

| Tracker | Trigger | Function | Log Location |
|---------|---------|----------|--------------|
| `read-tracker.sh` | Read | Record file reads | `.agent/tmp/recent_reads.log` |
| `task-tracker.sh` | TaskCreate\|TaskUpdate | Record Task operations | `.agent/tmp/recent_tasks.log` |

### Common Library (_shared.sh)

```bash
# Core functions
output_allow()           # Allow (permissionDecision: "allow")
output_deny "reason"     # HARD BLOCK (permissionDecision: "deny")
output_ask "reason"      # Request user confirmation (permissionDecision: "ask")
output_passthrough()     # PostToolUse passthrough (empty JSON)

# State check functions
has_active_workload()    # Check _active_workload.yaml existence
has_read_l2l3()          # Check L2/L3 file reads
has_recent_task_create() # Check TaskCreate within last 5 minutes
is_excluded_file()       # Check excluded files (.claude/, .agent/, .md, .json etc.)

# Logging functions
log_enforcement()        # Record decisions to enforcement.log
log_tracking()           # Record to tracking log
```

### Hook Exit Code Rules

| Exit Code | JSON Required | Result |
|-----------|---------------|--------|
| `exit 0` | ✅ Required | Process according to `permissionDecision` in JSON |
| `exit 2` | ❌ Ignored | Immediate emergency block (stderr displayed) |
| `exit 1` | ❌ Ignored | Hook error, operation is allowed |

### settings.json Hook Registration

```json
{
  "PreToolUse": [
    {
      "matcher": "Edit|Write|Task",
      "hooks": [{"command": ".../enforcement/context-recovery-gate.sh", "timeout": 5000}]
    },
    {
      "matcher": "Edit|Write",
      "hooks": [
        {"command": ".../enforcement/l2l3-access-gate.sh", "timeout": 5000},
        {"command": ".../enforcement/task-first-gate.sh", "timeout": 5000}
      ]
    },
    {
      "matcher": "TaskUpdate",
      "hooks": [
        {"command": ".../enforcement/blocked-task-gate.sh", "timeout": 5000},
        {"command": ".../enforcement/output-preservation-gate.sh", "timeout": 5000}
      ]
    },
    {
      "matcher": "Bash",
      "hooks": [{"command": ".../enforcement/security-gate.sh", "timeout": 5000}]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Read",
      "hooks": [{"command": ".../tracking/read-tracker.sh", "timeout": 3000}]
    },
    {
      "matcher": "TaskCreate|TaskUpdate",
      "hooks": [{"command": ".../tracking/task-tracker.sh", "timeout": 3000}]
    }
  ]
}
```

### Prompt vs Hook Enforcement Comparison

| Rule | V1.x (Prompt) | V2.0 (Hook Enforcement) |
|------|---------------|-------------------------|
| Context Recovery | CLAUDE.md instruction | `context-recovery-gate.sh` BLOCK |
| L2→L3 reading | Task API Guideline instruction | `l2l3-access-gate.sh` BLOCK |
| TaskCreate required | [PERMANENT] pattern instruction | `task-first-gate.sh` BLOCK |
| blockedBy compliance | Dependency rule instruction | `blocked-task-gate.sh` BLOCK |
| Security command blocking | settings.json deny | `security-gate.sh` BLOCK |

---

> **Version:** 2.0.0 (Enforcement Architecture - Hook-Based Behavioral Enforcement)
> **Updated:** 2026-02-01
> **Changes:**
> - V2.0.0: Added Section 16 (Enforcement Architecture)
> - V2.0.0: Hook-based behavioral enforcement (not prompt-level guidance)
> - V2.0.0: Gate scripts with `permissionDecision: deny` for HARD BLOCK
> - V2.0.0: Tracker scripts for read/task logging
> - V2.0.0: Common library (_shared.sh) with helper functions
> - V1.5.0: Added Section 14-15 (Integrated Roadmap, INFRA Integration Verification Results)
> - V1.5.0: Added V2.1.29 SubagentStart/SubagentStop hooks documentation
> - V1.4.0: Added Section 10-12 (Agent/Skill/Hook Integration from Code-Level Analysis)
> - V1.3.0: Added Section 1.1: L2→L3 Progressive-Deep-Dive (Meta-Level Pattern)
> - Mandatory for improvement/enhancement/refinement tasks
> - Parallel Agent result synthesis workflow

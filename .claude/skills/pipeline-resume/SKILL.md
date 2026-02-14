---
name: pipeline-resume
description: |
  [X-Cut·Resume·Recovery] Pipeline resume after session interruption. Uses Task API (TaskList + TaskGet) to reconstruct pipeline state from PERMANENT Task and work tasks, identifies last completed phase, and resumes from the interrupted point.

  WHEN: Session continuation after interruption. Previous pipeline active but not completed. User invokes /pipeline-resume or Lead detects incomplete pipeline state.
  DOMAIN: Cross-cutting (session recovery). Independent of pipeline sequence.

  METHODOLOGY: (1) TaskList to get all tasks, (2) TaskGet PERMANENT Task for project context and current_phase, (3) Identify completed vs in-progress vs pending work tasks from status, (4) Determine resume point (last completed phase + first incomplete), (5) Re-spawn agents with context from PT metadata, (6) Resume pipeline from interrupted phase.
  PREREQUISITE: PERMANENT Task exists with metadata.current_phase set.
  OUTPUT_FORMAT: L1 YAML resume state (last phase, resume phase, task summary), L2 markdown recovery report.
user-invocable: true
disable-model-invocation: true
argument-hint: "[resume-from-phase]"
---

# Pipeline — Resume

## Execution Model
- **TRIVIAL**: Lead-direct. Simple resume from clear interruption point.
- **STANDARD**: Lead-direct with analyst. Complex state reconstruction needed.
- **COMPLEX**: Lead-direct with 2 analysts. Multi-domain recovery with dependency resolution.

## Methodology

### 1. Discover Pipeline State
Use Task API to reconstruct state:
- `TaskList` to see all tasks (including PERMANENT Task)
- Identify PT by `[PERMANENT]` prefix in subject
- Note task statuses: completed, in_progress, pending

### 2. Read PERMANENT Task Context
`TaskGet` on the PERMANENT Task:
- Extract `current_phase` from metadata
- Read project description for pipeline context
- Identify key decisions and architecture choices

### 3. Analyze Task Status
Categorize all work tasks:
- **Completed**: phases that finished successfully
- **In-progress**: phases interrupted mid-execution
- **Pending**: phases not yet started
- Determine resume point = first non-completed phase

### 4. Reconstruct Agent Context
For each in-progress task:
- Read task description for agent assignment
- Check if agents produced partial L1/L2 output
- Determine if task can continue or needs restart

### 5. Resume Pipeline
Execute recovery:
- Update PT metadata with resume information
- Re-spawn agents for in-progress tasks with full context
- Provide each agent: PT context + task description + any partial output
- Resume pipeline flow from the interrupted phase

## Quality Gate
- PERMANENT Task found and context extracted
- All task statuses accurately determined
- Resume point identified with clear rationale
- Agents re-spawned with sufficient context to continue

## Output

### L1
```yaml
domain: cross-cutting
skill: pipeline-resume
last_completed_phase: ""
resume_phase: ""
total_tasks: 0
completed_tasks: 0
in_progress_tasks: 0
pending_tasks: 0
```

### L2
- Task-based recovery summary
- Pipeline state reconstruction from PT metadata
- Resume point with rationale

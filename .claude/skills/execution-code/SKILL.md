---
name: execution-code
description: |
  [P7·Execution·Code] Source code implementation executor. Spawns implementers for application source code (Python, TypeScript, etc.) based on validated assignments. Handles all non-.claude/ file changes.

  WHEN: orchestration domain complete (all 3 PASS). Validated assignments ready for code implementation.
  DOMAIN: execution (skill 1 of 5). Parallel-capable: code ∥ infra -> impact -> cascade -> review.
  INPUT_FROM: orchestration-verify (validated task-teammate matrix).
  OUTPUT_TO: execution-impact (file changes), execution-review (artifacts), verify domain.

  METHODOLOGY: (1) Read assignments, (2) Spawn implementers per matrix, (3) Each: TaskGet -> code -> report, (4) Monitor L1/L2, (5) Consolidate results.
  TIER_BEHAVIOR: T=single implementer, S=1-2 implementers, C=3-4 implementers.
  OUTPUT_FORMAT: L1 YAML manifest, L2 summary, L3 per-file details.
user-invocable: true
disable-model-invocation: false
---

# Execution — Code

## Execution Model
- **TRIVIAL**: Lead-direct. Single implementer for 1-2 file change.
- **STANDARD**: Spawn 1-2 implementers. Each owns non-overlapping files.
- **COMPLEX**: Spawn 3-4 implementers. Parallel implementation with dependency awareness.

## Methodology

### 1. Read Validated Assignments
Load orchestration-verify PASS report and task-teammate matrix.
Extract file assignments, dependency order, and interface contracts per implementer.

### 2. Spawn Implementers
For each task group in the matrix:
- Create Task with `subagent_type: implementer`
- Include in prompt: task description, file list, interface contracts, PT context
- Set `mode: "bypassPermissions"` for code implementation

### 3. Monitor Progress
During implementation:
- Read implementer L1 output for completion status
- Track files_changed count against expected
- If implementer reports blocker: assess and provide guidance

### 4. Handle Failures
If an implementer fails or produces incorrect output:
- Read their L2 for error details
- Provide corrected instructions via new spawn
- Max 3 retry iterations per implementer

### 5. Consolidate Results
After all implementers complete:
- Collect L1 YAML from each implementer
- Build unified file change manifest
- Report to execution-review for validation

**SRC Integration**: After consolidation, Lead should route to execution-impact for dependency analysis before proceeding to execution-review. SubagentStop hook will inject SRC IMPACT ALERT into Lead's context when implementers finish.

## Quality Gate
- All assigned files have been modified/created
- Each implementer reports `status: complete`
- No unresolved blockers or errors
- File ownership non-overlapping (no conflicts)

## Output

### L1
```yaml
domain: execution
skill: code
status: complete|in-progress|failed
files_changed: 0
implementers: 0
tasks:
  - task_id: ""
    implementer: ""
    files: []
    status: complete|in-progress|failed
```

### L2
- Implementation summary per implementer
- File change manifest
- Issues encountered and resolutions

# Pipeline Resume — Detailed Methodology
> On-demand reference. Contains resume templates, state reconstruction algorithms, tier-specific recovery procedures, branch validation, and agent respawn DPS templates.

## 1. Tier-Specific Recovery Procedures

### TRIVIAL Recovery (P0->P6->P8)
Only 1-2 work tasks expected. Check if the single execution task completed:
- Completed → route directly to delivery-pipeline (P8).
- Failed or in-progress → restart from P6 (execution). Minimal state reconstruction: PT metadata and the single task description only.
- No work tasks exist → pipeline stalled at P0. Restart from the beginning.

### STANDARD Recovery (P0->P1->P2->P3->P6->P7->P8)
Multiple tasks across 3-4 phases. Build a phase completion matrix:

| Phase | Tasks | Completed | Failed | Pending |
|-------|-------|-----------|--------|---------|
| P0    | n     | ...       | ...    | ...     |
| P1    | n     | ...       | ...    | ...     |
| P2    | n     | ...       | ...    | ...     |
| ...   | ...   | ...       | ...    | ...     |

Map each phase status from task metadata. Resume from the earliest incomplete phase. If a phase has mixed statuses (some completed, some failed), treat the entire phase as incomplete and restart all tasks in that phase.

### COMPLEX Recovery (P0->P8, all phases)
Many tasks across all phases. Full state reconstruction required:
1. Build complete dependency graph from Task API (task references, metadata.phase fields).
2. Check for broken dependency chains: a dependent task shows completed but its blocker shows failed. This indicates stale or corrupted state.
3. Resolve contradictions before resuming: trust the most conservative interpretation (if blocker failed, dependent's "completed" status is suspect — flag for re-verification).
4. For multi-domain phases (e.g., P5 with parallel code + infra tasks), verify all parallel branches before advancing.

---

## 2. State Reconstruction Analyst DPS Template

**Context**: TaskList output (all tasks with statuses), PT metadata (current_phase, tier, phase_signals), git branch name and status.

**Task**: "Reconstruct pipeline state: categorize all work tasks by phase and status, identify contradictions, determine resume point, validate git branch matches PT expectations."

**Constraints**: analyst agent (read-only, no Bash). maxTurns: 15 (STANDARD), 20 (COMPLEX). Do not modify any tasks or files.

**Expected Output**: L1 YAML with `resume_phase`, `completed_tasks`, `failed_tasks`, `contradictions`. L2 recovery report with phase-by-phase status matrix.

**Delivery**: file-based handoff to Lead: `PASS|resume:{phase}|tasks:{completed}/{total}|ref:tasks/{work_dir}/pipeline-resume.md`

### Analyst Tier-Specific DPS Variations
- **TRIVIAL**: Lead-direct. No analyst spawn — just TaskList + TaskGet inline.
- **STANDARD**: 1 analyst for state reconstruction. maxTurns: 15.
- **COMPLEX**: 2 parallel analysts (task state + git state). maxTurns: 20 each.

---

## 3. State Reconstruction Depth

**Shallow reconstruction**: Only read PT metadata (current_phase, tier) and task statuses. Sufficient for TRIVIAL/STANDARD tiers where pipeline state is straightforward.

**Deep reconstruction**: Read PT metadata + all task descriptions + any referenced files. Necessary for COMPLEX tiers with multi-domain dependencies where understanding the full pipeline state requires examining intermediate outputs.

---

## 4. Branch State Validation

Before resuming, validate git state matches pipeline expectations:

| Check | Command | Expected |
|-------|---------|----------|
| Current branch | `git branch --show-current` | Same as PT's branch |
| Uncommitted changes | `git status` | Clean or only pipeline-generated changes |
| Branch divergence | `git log origin/main..HEAD` | Expected commits from previous phases |

### Branch Mismatch
- **Cause**: Current git branch differs from what PT expects. User may have switched branches between sessions, or compaction lost branch context.
- **Action**: Display both branches to user (current vs expected). If user confirms current branch is correct, update PT metadata to reflect it. If user wants the original branch, instruct them to switch (`git checkout <branch>`) and re-invoke resume. Do not silently proceed on the wrong branch — file state divergence causes cascading failures.

### Unexpected Uncommitted Changes
Flag for user review before resuming. Manual edits could invalidate completed phase outputs.

### Missing Expected Commits
Previous phase commits may have been lost (force push, reset). Treat affected phases as incomplete regardless of task status.

---

## 5. Multi-Session Recovery

Pipeline may have been interrupted multiple times. Check PT metadata for `resume_count`:

- **0 or missing**: First resume. Standard recovery — follow methodology as written.
- **1-2**: Second or third resume. Verify previous resume was successful by checking whether tasks marked completed since last resume actually have file-level evidence of completion (output files exist, commits present). If previous resume failed silently, the task status may be stale.
- **3+**: Pipeline is experiencing repeated interruptions. This signals a systemic issue. Recommend one of:
  - Simplify: drop tier from COMPLEX to STANDARD (fewer phases, less state to track).
  - Diagnose: identify the underlying interruption cause (resource limits, compaction pressure, user availability).
  - Checkpoint: commit partial work more frequently to reduce per-resume reconstruction cost.

---

## 6. Failure Sub-Cases (Verbose)

### PT Metadata Missing current_phase
- **Cause**: PT was created but never updated with phase progression (e.g., pipeline crashed during P0 before first phase update).
- **Action**: Infer current phase from task statuses. If no work tasks exist, assume P0. If work tasks exist, derive phase from their `metadata.phase` fields. Update PT with inferred phase before resuming.

### Branch Mismatch (Detailed)
- **Cause**: Current git branch differs from what PT expects.
- **Action**: Display both branches (current vs expected). If user confirms current branch is correct, update PT metadata. If user wants the original branch, instruct `git checkout <branch>` and re-invoke resume. Do not silently proceed on the wrong branch.

### Stale Work Tasks
- **Cause**: Work tasks exist and show "completed", but their assigned files have been modified outside the pipeline (manual edits, other tools, or a different pipeline run). Indicator: file modification time is newer than task completion time, or file content hash differs from what was reviewed.
- **Action**: Flag stale tasks as needing re-verification. Route affected phases through the verify domain before resuming downstream phases:
  1. Identify which tasks reference modified files.
  2. Mark those tasks as "stale" in the resume report (not failed, not completed).
  3. Route to appropriate verify-* skills for the affected files before proceeding.
  4. If verify passes, continue. If verify fails, route back to execution for that phase.

### PT Phase Ahead of Actual Progress
- **Cause**: PT `metadata.current_phase` shows P5 but only P0-P2 tasks exist. PT was updated optimistically (phase was set before work completed), or intermediate tasks were deleted or lost.
- **Action**: Trust task evidence over PT metadata. Reset `current_phase` to match the actual highest completed phase based on task statuses. Report the discrepancy in L2 output. If no tasks exist at all but PT shows an advanced phase, treat as a corrupted PT — reconstruct from git history and file state.

---

## 7. State Reconstruction Checklist

Reference checklist Lead follows for every resume invocation. Execute in order:

```
Resume Checklist:
[ ] TaskList -- retrieve all tasks in the session
[ ] Find [PERMANENT] task by subject prefix
[ ] TaskGet PT -- extract current_phase, tier, branch, references
[ ] Categorize work tasks: completed / in_progress / pending / failed
[ ] Check git branch matches PT expectations
[ ] Check git status for uncommitted changes
[ ] Detect compaction (check if session context was summarized)
[ ] Identify resume point: first non-completed phase
[ ] Check for task status contradictions and resolve
[ ] Build resume context for agents: PT + task descriptions + any partial output
[ ] Present reconstructed state to user before acting
[ ] Update PT metadata: resume_count++, current_phase = resume point
```

If any checklist item fails, route to the corresponding Failure Handling scenario in SKILL.md. Do not skip items — the order matters because later items depend on earlier ones.

---

## 8. Anti-Patterns (Secondary)

### DO NOT: Auto-Resume Without User Awareness
Always present the reconstructed pipeline state and proposed resume point to the user before taking action. The user may have made manual changes between sessions that affect the resume strategy.

### DO NOT: Re-Create Completed Work Tasks
When resuming, do not create duplicate tasks for work that was already completed. Check task statuses first and only create/restart tasks that are in-progress or pending.

### DO NOT: Resume Parallel Tasks Sequentially
If the interrupted phase had parallel tasks (e.g., code and infra in P5, or multiple parallel research tasks in P2), resume them in parallel. Check the original orchestrate-static output (stored in PT metadata or task descriptions) for the parallelism strategy. Serializing previously-parallel work wastes time and may introduce ordering dependencies that did not exist in the original plan.

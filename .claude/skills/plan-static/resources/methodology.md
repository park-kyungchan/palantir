# Plan-Static Methodology Reference

Detailed templates, rubrics, and examples offloaded from SKILL.md for progressive disclosure.
Load on-demand when performing COMPLEX decomposition or consulting decision criteria.

---

## Complexity Indicator Table (Partition Table Format)

Use this table to estimate per-task complexity after cluster assignment.

| Indicator | TRIVIAL | STANDARD | COMPLEX |
|-----------|---------|----------|---------|
| Files per task | 1 | 2-3 | 4 |
| Internal edges | 0-1 | 2-3 | 4+ |
| Cross-task deps | 0 | 1 | 2+ |
| Module boundaries | Same | 1-2 | Cross-module |

---

## File Ownership Assignment Rubric

For each task, apply this checklist:
1. List exact file paths (create or modify) — no file may appear in two tasks
2. Related files (module + its tests) MUST stay in the same task
3. Config files (`.claude/`, `.github/`, etc.) grouped into infra tasks; source files into code tasks
4. If a file is needed by two tasks, assign it to the primary modifier and create a dependency edge to the secondary consumer
5. Estimate complexity using the Complexity Indicator Table above

---

## Cluster Strategy Examples (Decision Points Detail)

### Cluster Split vs Merge

When dependency cluster boundaries are ambiguous:

**Split criteria** (apply when ALL of):
- Cluster has > 4 files
- A weak internal edge exists (≤ 2 coupling edges between the two sub-groups)
- Split produces two independently testable units

**Merge criteria** (apply when ANY of):
- Two adjacent clusters share > 3 bidirectional edges
- Neither cluster is independently testable without the other
- Merged scope remains ≤ 4 files

**Default**: Keep cluster intact when 1-4 files with clear internal cohesion. Never split a cluster just to reduce task size if it breaks testability.

### Task Granularity Selection

| Scenario | Action |
|----------|--------|
| File has 0 dependencies (isolated node) | Single-file task — minimal scope |
| Files form tight cluster (mutual deps) | Group 2-4 files per SRP-bounded task |
| Ambiguous grouping | Prefer 2-3 files per task for balanced parallelism |
| Cluster > 4 files, weak split edge exists | Split along weakest coupling edge, accept new cross-task dep |
| All files isolated (flat graph) | Each file → own task; note trivial decomposition in L2 |

---

## DPS Analyst Spawn Template

### COMPLEX (full DPS)

- **Context** (D11 priority: cognitive focus > token efficiency):
  - INCLUDE:
    - research-coordinator audit-static L3 from `tasks/{work_dir}/p2-coordinator-audit-static.md` (path via `$ARGUMENTS`)
    - Pipeline tier and iteration count from PT metadata
  - EXCLUDE:
    - Other plan dimension outputs (behavioral, relational, impact) — unless explicit dependency exists
    - Full research evidence detail — use L3 summaries only
    - Pre-design and design conversation history
  - Budget: Context field ≤ 30% of subagent effective context
- **Task**: "Identify dependency clusters in the file graph. Group files into tasks (1-4 files each, SRP). Assign file ownership (non-overlapping). Map inter-task dependency edges. Identify critical path. Estimate per-task complexity (T/S/C)."
- **Constraints**: analyst agent. Read-only (Glob/Grep/Read only). No file modifications. maxTurns: 20.
- **Expected Output**: L1 YAML with task_count, tasks[] (id, files, complexity, depends_on, cluster). L2 task descriptions with cluster rationale and critical path visualization.
- **Delivery (Two-Channel)**:
  - Ch1: PT signal → `metadata.phase_signals.p3_plan_static`
  - Ch2: Write full result to `tasks/{work_dir}/p3-plan-static.md`
  - Ch3: Micro-signal to Lead → `PASS|tasks:{N}|deps:{N}|ref:tasks/{work_dir}/p3-plan-static.md`
  - Ch4: P2P to validate-syntactic subagent (Deferred Spawn — Lead spawns verifier after all 4 plan dimensions complete; send only if verifier is already active)

### STANDARD (simplified DPS)

- Spawn analyst (maxTurns: 15)
- Simplified cluster identification across 3-8 files, single-pass grouping
- Skip critical path analysis if ≤ 3 tasks total
- Same Two-Channel delivery as COMPLEX

### TRIVIAL (Lead-direct)

- No analyst spawn — Lead executes inline
- Flat file list (1-2 files), assign each to a single task
- No cluster analysis needed
- Output inline to PT and Ch2 file

---

## Iteration Tracking (D15)

Lead manages `metadata.iterations.plan-static: N` in PT before each invocation.

| Iteration | Mode | On FAIL |
|-----------|------|---------|
| 1 | Strict | Return to research-coordinator with dependency graph gaps identified |
| 2 | Relaxed | Proceed with documented coverage gaps; flag in phase_signals |
| 3+ | Auto-PASS | Max iterations reached; escalate if gaps are critical |

Max iterations: 2 (plan↔verify loop category per D15 table).

Protocol:
1. `TaskGet PT` → read `metadata.iterations.plan-static`
2. Missing → current_iteration = 1. Exists → current_iteration = value + 1.
3. `TaskUpdate PT` → `metadata.iterations.plan-static: current_iteration`
4. Pass current_iteration to analyst via DPS Context or `$ARGUMENTS`

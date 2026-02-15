---
name: orchestration-verify
description: |
  [P6·Orchestration·Verify] Orchestration decision validator. Checks assignments for correctness (right agent for right task), dependency acyclicity, and 4-teammate capacity enforcement before execution.

  WHEN: After orchestration-assign produces task-teammate matrix. Assignments exist but validity unconfirmed.
  DOMAIN: orchestration (skill 3 of 3). Terminal skill in orchestration domain.
  INPUT_FROM: orchestration-assign (task-teammate matrix with rationale).
  OUTPUT_TO: execution domain (validated assignments, PASS) or orchestration-assign (FAIL, re-assign).

  METHODOLOGY: (1) Read task-teammate matrix, (2) Verify each agent type matches task requirements via WHEN conditions, (3) Topological sort on dependency graph to detect cycles, (4) Confirm teammate count <=4 per domain, (5) Check no file ownership conflicts (non-overlapping).
  OUTPUT_FORMAT: L1 YAML validation verdict per check, L2 ASCII validated dependency graph with PASS/FAIL markers.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Verify

## Execution Model
- **TRIVIAL**: Lead-direct. Quick sanity check.
- **STANDARD**: Lead-direct. Systematic verification of assignments.
- **COMPLEX**: Spawn analyst for independent verification of complex assignment.

## Decision Points

### Tier Assessment for Verification Depth
- **TRIVIAL**: 1-2 assignments, single agent type, no dependency graph. Lead does quick manual check: correct agent? Files exist? Capacity OK? Takes <30 seconds.
- **STANDARD**: 3-6 assignments, 2 agent types, simple dependency graph (tree-shaped). Lead performs systematic check of all 4 verification categories. Uses Agent L1 in context for matching validation.
- **COMPLEX**: 7+ assignments, 3+ agent types, complex dependency graph (cross-cutting, multi-phase). Spawn analyst for independent verification. Analyst provides fresh perspective that may catch Lead's own decomposition/assignment errors.

### When to Spawn Analyst for Verification
Spawn analyst when ANY of these conditions are true:
- Total assignments > 6 (too many for reliable manual verification)
- Dependency graph has > 8 edges (cycle detection is error-prone manually)
- Multi-phase execution (inter-phase dependencies need systematic checking)
- Same pipeline has already had a verify FAIL (increased scrutiny)

Do NOT spawn analyst when:
- TRIVIAL tier with obvious assignments
- Revalidation after minor fix (only the changed assignment needs rechecking)

### PASS vs FAIL Decision Logic
All 4 checks must PASS for overall PASS verdict:

| Check | PASS Condition | FAIL Condition |
|-------|---------------|----------------|
| agent_match | Every task's agent type has required tools for task | Any task assigned to agent lacking required tools |
| acyclicity | Topological sort succeeds on dependency graph | Cycle detected in dependency graph |
| capacity | Each phase has ≤4 teammate instances | Any phase exceeds 4 teammates |
| ownership | Every file owned by exactly 1 instance, .claude/ files to infra-impl only | File in multiple instances OR domain boundary violation |

If ANY check is FAIL:
- Report ALL failures (not just the first one found)
- Route back to orchestration-assign with specific failure details per check
- Orchestration-assign adjusts and re-submits for re-verification (max 3 iterations)

### Re-Verification After Fix
When orchestration-assign resubmits after fixing FAIL:
- Only re-check the FAILED categories (skip PASSed checks for efficiency)
- Exception: if the fix involved restructuring groups, re-run ALL checks (structural changes may introduce new issues)
- Max 3 re-verification iterations. After 3 FAILs: escalate to Lead for manual resolution or plan revision.

### Verification Completeness vs Speed Tradeoff
- **Complete verification** (default): Check ALL 4 categories thoroughly. Preferred for STANDARD/COMPLEX.
- **Quick verification** (TRIVIAL only): Check agent_match and ownership only. Skip acyclicity (trivial graphs) and capacity (obviously within limits). Acceptable because TRIVIAL has ≤3 tasks.

## Methodology

### 1. Read Assignment Matrix
Load orchestration-assign output (task-teammate assignments).

### 2. Verify Agent-Task Match
For each assignment, check:
- Agent WHEN condition matches task requirements
- Agent has required tools for the task (Edit for code changes, Bash for testing)
- Agent profile (B/C/D/E) is appropriate for task type

For COMPLEX tier, construct the delegation prompt for the analyst with:
- **Context**: Paste orchestration-assign L1 (task-teammate matrix with assignments). Include Agent profile reference: analyst=B(Read,Glob,Grep,Write), researcher=C(+WebSearch,WebFetch,context7,tavily), implementer=D(+Edit,Bash), infra-implementer=E(+Edit,Write for .claude/).
- **Task**: "For each assignment: verify agent WHEN condition matches task type, verify agent has required tools for the task. Check dependency acyclicity (approximate reasoning for small graphs, systematic for large). Confirm <=4 teammate instances per execution phase. Verify non-overlapping file ownership."
- **Constraints**: Read-only. No modifications. For topological sort: use systematic reasoning, not algorithmic execution. Acknowledge this is approximate for large graphs.
- **Expected Output**: L1 YAML with checks (agent_match, acyclicity, capacity, ownership) each PASS/FAIL. L2 verification details.

#### Agent-Task Match Verification Checklist
For each assignment, verify ALL of these:

| Check | How to Verify | Common Failures |
|-------|--------------|-----------------|
| Tool requirements | Task needs Bash? → Must be implementer (D) | Analyst assigned to test-running task |
| File domain | .claude/ files? → Must be infra-implementer (E) | Implementer assigned to skill editing |
| Web access | External lookup needed? → Must be researcher (C) | Analyst assigned to API doc fetching |
| Write capability | Creates new files? → Need Write tool | Researcher lacks Write in some configs |
| Profile minimum | Agent has at least the tools the task needs | Over-provisioned agents (wasteful but not wrong) |

#### Common Mismatches to Catch
- **Analyst for implementation**: Analyst (B) has Write but NO Edit/Bash — cannot modify existing files or run tests
- **Implementer for .claude/**: Implementer (D) has Bash but works in application domain — lacks INFRA context for .claude/ changes
- **Researcher for local-only tasks**: Researcher (C) has web tools that are unnecessary overhead for local codebase analysis
- **Infra-implementer for hook testing**: Infra-implementer (E) can EDIT hook .sh files but cannot RUN them (no Bash) — testing hook changes requires separate implementer or manual testing

### 3. Check Dependency Acyclicity
Run topological sort on dependency graph:
- If sort succeeds -> acyclic (PASS)
- If sort fails -> cycle detected (FAIL, report cycle)

**Note**: For TRIVIAL/STANDARD (Lead-direct), Lead performs approximate cycle detection via reasoning — suitable for small dependency graphs (≤8 tasks). For COMPLEX tier, the spawned analyst performs systematic cycle detection using exhaustive path tracing.

#### Cycle Detection Methods

**Lead-direct (TRIVIAL/STANDARD):**
For graphs with ≤8 nodes, Lead uses reasoning-based approach:
1. Identify all edges (A → B means A must complete before B)
2. Find nodes with no incoming edges (start nodes)
3. Mentally remove start nodes and their outgoing edges
4. Repeat until all nodes removed (acyclic) or stuck (cycle exists)
5. If stuck: the remaining nodes form the cycle

**Analyst-assisted (COMPLEX):**
Analyst performs systematic path tracing:
1. For each node, trace all reachable nodes via DFS
2. If any node reaches itself: cycle found
3. Report: cycle path (e.g., "G1 → G3 → G5 → G1") and involved tasks
4. Suggest resolution: which edge to remove (least impactful dependency to break)

#### Cycle Resolution Strategies
If cycle detected, recommend one of:
- **Merge groups**: Combine cyclic groups into single group (same agent handles both)
- **Break dependency**: Convert hard dependency to interface dependency (provide contract, remove runtime dependency)
- **Reorder tasks**: Move the dependency-creating task to a different group
- Route recommendation back to orchestration-assign for implementation

### 4. Validate Capacity
Per execution phase:
- Teammate count <= 4
- No single agent overloaded (>4 files per instance)
- Context budget feasible (estimate tokens per task)

#### Capacity Validation Matrix
| Execution Phase | Agent Type | Instance Count | Limit | Status |
|-----------------|-----------|---------------|-------|--------|
| Phase 1 | implementer | 2 | 4 | OK |
| Phase 1 | analyst | 1 | 4 | OK |
| Phase 1 | TOTAL | 3 | 4 | OK |
| Phase 2 | implementer | 3 | 4 | OK |

Total across ALL types per phase must be ≤ 4.

#### Context Budget Estimation
For each agent instance, estimate context consumption:
- Base agent context: ~2K tokens (agent definition + system prompt)
- DPS prompt: ~500-1K tokens (depending on task complexity)
- Per-file context: ~200-500 tokens per file (depending on file size)
- Interface contracts: ~300 tokens per cross-boundary interface
- Total per instance should be < 15K tokens to leave room for agent working memory

If estimated context > 15K tokens: recommend splitting the instance's tasks across two instances or reducing per-file context in DPS.

### 5. Check File Ownership
Verify non-overlapping file ownership:
- No file appears in multiple agent assignments
- All files from plan appear in assignments (nothing dropped)
- .claude/ files assigned to infra-implementer, not implementer

## Failure Handling

### Single Check FAIL (Others PASS)
- **Action**: Route to orchestration-assign with the specific failed check and evidence
- **Expectation**: Quick fix (reassign 1-2 tasks, break 1 cycle, reduce 1 instance)
- **Re-verification**: Only re-check the failed category

### Multiple Checks FAIL
- **Action**: Route to orchestration-assign with ALL failure details
- **Expectation**: May need significant restructuring (possibly route back to orchestration-decompose)
- **Re-verification**: Full re-check (structural changes likely)

### 3 Re-Verification Iterations Exhausted
- **Action**: Escalate to Lead for decision. Options:
  1. Accept with known issues (proceed to execution with warnings)
  2. Route to plan-decomposition for plan restructuring
  3. Route to design-architecture for architectural review
- **Report in L1**: `status: FAIL`, `iterations: 3`, `unresolved: [list of issues]`

### Analyst Verification Disagrees with Lead
When spawned analyst finds issues Lead didn't catch:
- **Default**: Trust the analyst's findings (fresh perspective catches Lead's blind spots)
- **Exception**: If analyst finding contradicts established architecture decision, Lead may override with documented rationale
- **Always report**: Include analyst's full finding in L2, even if overridden

### Orchestration-Assign Produces Empty Matrix
- **Cause**: No tasks to assign (plan was empty or all tasks were eliminated)
- **Action**: Verify with plan-decomposition that tasks exist. If genuinely empty: set `status: PASS` with `assignments: 0` and route to verify domain (nothing to execute).

## Anti-Patterns

### DO NOT: Auto-PASS Without Checking
Every assignment must be explicitly verified, even in TRIVIAL tier. A quick manual check takes seconds and prevents execution failures that waste minutes.

### DO NOT: Fix Assignments During Verification
Verification is a READ-ONLY check. If issues are found, route BACK to orchestration-assign for fixes. Verify should never modify the assignment matrix — this conflates verification with implementation and makes the process unreliable.

### DO NOT: Ignore File Domain Boundaries
The `.claude/` boundary is not a suggestion — it's a hard architectural constraint. Implementers CANNOT properly handle `.claude/` files, and infra-implementers CANNOT test source code. Always verify domain separation.

### DO NOT: Trust Approximate Cycle Detection for COMPLEX Graphs
For graphs with >8 nodes, Lead's reasoning-based cycle detection is unreliable. Always spawn an analyst for systematic verification of complex dependency graphs.

### DO NOT: Skip Capacity Check for Small Assignments
Even with 2-3 assignments, verify the count. Future phases may need additional teammates, and capacity planning must account for the full execution pipeline, not just the current assignment.

### DO NOT: Re-Verify Everything After Minor Fixes
If only agent_match failed and the fix was reassigning 1 task: only re-check agent_match and ownership (the fix may have changed file ownership). Don't re-run acyclicity check — it's unchanged.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestration-assign | Task-teammate matrix with rationale | L1 YAML: `assignments[].{group, agent_type, instance, tasks[], files[]}` |
| orchestration-assign | Phase structure (if multi-phase) | L1 field: `phases: N, phase_assignments: [...]` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| execution-code | Validated code task assignments | PASS verdict, assignments contain source code tasks |
| execution-infra | Validated infra task assignments | PASS verdict, assignments contain .claude/ tasks |
| orchestration-assign | Failure report with specific issues | FAIL verdict |
| orchestration-decompose | Restructuring request | FAIL after 3 iterations (needs fundamental regrouping) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Single check FAIL | orchestration-assign | Failed check + evidence + fix suggestion |
| Multiple checks FAIL | orchestration-assign (or decompose) | All failures + restructuring recommendation |
| 3 iterations exhausted | Lead escalation | Full verification history across iterations |
| Empty assignment matrix | plan-decomposition | Verification that tasks exist |

## Quality Gate
- All agent-task matches verified correct
- Dependency graph is acyclic
- Capacity within limits
- File ownership non-overlapping and complete

## Output

### L1
```yaml
domain: orchestration
skill: verify
status: PASS|FAIL
checks:
  agent_match: PASS|FAIL
  acyclicity: PASS|FAIL
  capacity: PASS|FAIL
  ownership: PASS|FAIL
issues: 0
```

### L2
- Verification results per check category
- Issues found with evidence
- Validated dependency graph (ASCII)

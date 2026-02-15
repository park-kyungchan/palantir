---
name: orchestration-assign
description: |
  [P6·Orchestration·Assign] Teammate selection and task mapping specialist. Maps task groups to agent types via frontmatter WHEN conditions, tool requirements, and capabilities. Produces task-teammate matrix.

  WHEN: After orchestration-decompose produces task groups. Tasks decomposed but not yet assigned.
  DOMAIN: orchestration (skill 2 of 3). Sequential: decompose -> assign -> verify.
  INPUT_FROM: orchestration-decompose (task groups with dependency edges), plan-interface (interface dependencies for assignment).
  OUTPUT_TO: orchestration-verify (assignments for validation), execution domain (after verify PASS).

  METHODOLOGY: (1) Read task groups from decomposition, (2) Match each group to best agent type using frontmatter WHEN/TOOLS, (3) Assign tasks respecting 4-teammate limit, (4) Balance workload across teammates, (5) Generate task-teammate matrix with rationale.
  OUTPUT_FORMAT: L1 YAML task-teammate matrix, L2 ASCII assignment visualization with workload balance.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Assign

## Execution Model
- **TRIVIAL**: Lead-direct. 1-2 assignments.
- **STANDARD**: Lead-direct. Uses Agent L1 WHEN conditions for matching.
- **COMPLEX**: Lead-direct with sequential-thinking for complex assignment optimization.

## Decision Points

### Tier Assessment for Assignment Complexity
- **TRIVIAL**: 1-2 task groups from decomposition, obvious agent matches (e.g., single implementer for code task). Lead assigns directly with minimal analysis.
- **STANDARD**: 3-4 task groups, 2 agent types. Lead uses Agent L1 WHEN conditions for systematic matching. May need workload balancing between instances.
- **COMPLEX**: 5+ task groups, 3+ agent types, multi-phase execution needed. Lead uses sequential-thinking for optimization. Must balance across phases while respecting 4-teammate limit.

### Agent Selection Priority Rules
When a task could match multiple agent types, apply these priority rules:
1. **Specificity wins**: If task explicitly involves `.claude/` files, assign to infra-implementer regardless of other requirements.
2. **Tool requirements win**: If task requires Bash, assign to implementer even if the task also involves analysis.
3. **Capability floor**: Choose the agent with the MINIMUM sufficient capability set. Over-provisioning wastes context loading.
4. **Tie-breaking**: When two agents are equally suitable, prefer the one with more available capacity (fewer already-assigned tasks).

### Instance Count Decision
How many instances of each agent type to spawn:
- **Rule of thumb**: 1 instance per 3-5 files to modify. >8 files per instance risks context overflow.
- **Upper bound**: 4 instances per execution phase (platform limit).
- **Lower bound**: 1 instance per agent type used (don't split a 2-file task across 2 instances).
- **Parallel benefit threshold**: Only split into multiple instances if tasks are truly independent. 2 sequential tasks in 1 instance > 2 parallel instances with coordination overhead.

### Multi-Phase Execution Decision
When total teammate count exceeds 4:
- **Phase 1**: Critical path tasks + their dependencies. Maximum 4 teammates.
- **Phase 2**: Non-critical tasks that don't depend on Phase 1 outputs. Maximum 4 teammates.
- **Phase N**: Remaining tasks. Minimize total phases -- each phase boundary adds latency.
- **Signal to orchestration-verify**: Include `phases: N` in L1 output so verify can check per-phase capacity.

### File Ownership Assignment Rules
Each file must be owned by exactly one agent instance:
- **Primary rule**: File assigned to the agent instance whose task requires modifying it.
- **Conflict resolution**: If two tasks need the same file, merge tasks into one agent instance.
- **Read-only access**: Multiple agents can READ the same file. Only WRITE ownership must be exclusive.
- **.claude/ boundary**: `.claude/` files can ONLY be owned by infra-implementer instances. Source files ONLY by implementer instances. Mixing is a hard error.

## Methodology

### 1. Read Decomposed Groups
Load orchestration-decompose output (task groups with agent capability).

### 2. Match Groups to Agent Types
For each group, select specific agent type:

| Agent | Profile | Best For |
|-------|---------|----------|
| analyst | B (ReadAnalyzeWrite) | Analysis, design, verification, planning |
| researcher | C (ReadAnalyzeWriteWeb) | External docs, library research, API validation |
| implementer | D (CodeImpl) | Source code changes, test execution |
| infra-implementer | E (InfraImpl) | .claude/ file changes, configuration |

#### Matching Heuristic Examples
| Task Description | Agent Match | Reasoning |
|-----------------|-------------|-----------|
| "Implement login API endpoint" | implementer | Requires Bash for testing |
| "Update skill description" | infra-implementer | .claude/ file modification |
| "Research React 19 API changes" | researcher | Needs WebSearch/WebFetch |
| "Review implementation against spec" | analyst | Read-only analysis |
| "Create new hook script" | infra-implementer | .claude/hooks/ file, needs Edit/Write |
| "Run test suite and fix failures" | implementer | Requires Bash for test execution |
| "Analyze codebase patterns" | analyst | Read + Grep + Write report |

#### Edge Cases in Agent Matching
- **Hook scripts (.sh)**: Assigned to infra-implementer despite being shell scripts. Reason: they live in `.claude/hooks/` and infra-implementer has Edit access. The implementer's Bash tool is for RUNNING commands, not for EDITING hook files.
- **Test files**: Assigned to implementer (not analyst) because test changes typically require running the test suite to verify.
- **Documentation**: Assigned to analyst if read-only markdown writing. Assigned to implementer if docs are generated from code (needs Bash for generation commands).

### 3. Balance Workload
Within each execution phase:
- No agent type spawned more than 4 times
- Distribute tasks evenly across instances
- Consider task complexity for balanced assignment

#### Workload Balancing Metrics
| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Files per instance | 3-5 | >8 files |
| Tasks per instance | 1-3 | >4 tasks |
| Estimated tokens per instance | 2K-4K | >5K tokens |
| Cross-instance dependencies | 0 | >2 dependencies |

#### Rebalancing Strategy
If initial assignment is unbalanced:
1. Identify overloaded instance (>8 files or >4 tasks)
2. Find underloaded instance of same agent type
3. Move independent tasks from overloaded to underloaded
4. If no same-type instance available: create new instance (within 4-teammate limit)
5. If at capacity: split into execution phases

### 4. Generate Assignment Matrix

| Group | Agent Type | Instance | Tasks | Files |
|-------|-----------|----------|-------|-------|
| G1 | analyst | analyst-1 | [T1, T2] | [a.md, b.md] |
| G2 | implementer | impl-1 | [T3] | [c.ts, d.ts] |

#### Matrix Validation Checks (Pre-Verify)
Before sending to orchestration-verify, Lead performs quick sanity checks:
1. Every file from plan-decomposition appears in exactly one assignment
2. No `.claude/` file assigned to implementer (must be infra-implementer)
3. No source file assigned to infra-implementer (must be implementer)
4. Total instances per phase <= 4
5. No circular dependencies between assignment groups

These checks catch obvious errors before formal verification.

### 5. Document Rationale
For each assignment:
- Why this agent type? (WHEN condition match)
- Why this task grouping? (dependency + capability)
- Any alternatives considered?

## Failure Handling

### Decomposition Output Insufficient
- **Cause**: orchestration-decompose produced groups without clear agent capability tags.
- **Action**: Route back to orchestration-decompose with specific missing capability request.
- **Never guess**: agent assignments without explicit capability matching.

### No Suitable Agent Type
- **Cause**: Task requires capabilities not available in any single agent profile.
- **Action**: Report to orchestration-decompose for task splitting. Include which capabilities are needed and which agents have partial matches.
- **Example**: Task needs "search web AND edit code" -- split into researcher sub-task + implementer sub-task.

### Capacity Exceeded
- **Cause**: Workload requires >4 instances of same agent type in one phase.
- **Action**: Split into multi-phase execution. Assign critical path to Phase 1.
- **Report in L1**: `phases: N, phase_assignments: [{phase: 1, instances: [...]}, ...]`

### File Ownership Conflict
- **Cause**: Two tasks from different groups need to modify the same file.
- **Action**: Merge the conflicting tasks into a single agent instance. Update group assignments accordingly.
- **If agents differ**: Prioritize the agent type that handles the primary modification. The secondary modification becomes a sub-task for that agent.

### Workload Imbalance Unresolvable
- **Cause**: One agent instance has 15+ files but cannot be split (all files are interdependent).
- **Action**: Flag as execution risk in L2. Recommend increased maxTurns for that instance. Continue with assignment (don't block).

## Anti-Patterns

### DO NOT: Assign by Task Count Alone
Workload balance should consider file count and complexity, not just task count. 1 task touching 10 files is heavier than 3 tasks touching 2 files each.

### DO NOT: Create Cross-Domain Assignments
Never assign `.claude/` files to a code implementer or source files to infra-implementer. This violates the domain boundary and will fail (implementer won't edit .claude/ properly, infra-implementer has no Bash for testing source code).

### DO NOT: Assign delivery-agent or pt-manager for General Tasks
delivery-agent (Profile-F) and pt-manager (Profile-G) are fork agents reserved for specific skills (delivery-pipeline, task-management). They are NOT general-purpose workers. Always use analyst, researcher, implementer, or infra-implementer.

### DO NOT: Assign All Tasks to One Instance
Even if all tasks use the same agent type, consider splitting into multiple instances for parallel execution. A single instance processing 8+ tasks serially is slower than 2 instances processing 4 tasks each in parallel.

### DO NOT: Ignore Interface Dependencies When Splitting
When splitting tasks across instances, ensure interface contracts from plan-interface are provided to BOTH instances. The consumer instance needs the contract to know what to expect from the producer.

### DO NOT: Optimize for Minimum Instances
Fewer instances does not equal better. The goal is optimal execution speed within capacity limits. If parallelism is available, use it. 4 instances completing in 5 minutes beats 1 instance completing in 15 minutes.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| orchestration-decompose | Task groups with dependency edges | L1 YAML: `groups[].{id, tasks[], agent_capability, dependencies[]}` |
| plan-interface | Interface contracts between tasks | L2 markdown: contract specifications per task boundary |
| plan-decomposition | Original task list with file assignments | L1 YAML: `tasks[].{id, files[], complexity}` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-verify | Task-teammate matrix with rationale | Always (assign output is verify input) |
| execution-code | Validated code assignments | After orchestration-verify PASS (indirect via verify) |
| execution-infra | Validated infra assignments | After orchestration-verify PASS (indirect via verify) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Missing capability tags | orchestration-decompose | Groups missing agent_capability field |
| No suitable agent | orchestration-decompose | Task splitting recommendation |
| Capacity exceeded | Self (re-assign with phasing) | Current assignment + proposed phase split |
| File ownership conflict | Self (re-assign with merge) | Conflicting file + both task IDs |

## Quality Gate
- Every group assigned to exactly 1 agent type
- No agent type exceeds 4 instances
- No file assigned to multiple agent instances
- Rationale documented per assignment

## Output

### L1
```yaml
domain: orchestration
skill: assign
assignment_count: 0
agent_types_used: 0
assignments:
  - group: ""
    agent_type: ""
    instance: ""
    tasks: []
    files: []
```

### L2
- Task-teammate assignment matrix
- Workload balance indicators
- Assignment rationale per group

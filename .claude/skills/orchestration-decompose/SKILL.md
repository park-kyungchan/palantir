---
name: orchestration-decompose
description: |
  [P5·Orchestration·Decompose] Task-to-teammate decomposition specialist. Breaks validated plan into teammate-assignable work units with dependency awareness using Agent/Skill frontmatter in Lead's context.

  WHEN: plan-verify domain complete (all 3 PASS). Validated plan ready for teammate assignment. Orchestration entry point.
  DOMAIN: orchestration (skill 1 of 3). Sequential: decompose -> assign -> verify.
  INPUT_FROM: plan-verify domain (PASS verdict), plan-decomposition (task list with dependencies).
  OUTPUT_TO: orchestration-assign (decomposed tasks ready for teammate mapping).

  METHODOLOGY: (1) Read validated plan, (2) Group tasks by agent capability match via frontmatter descriptions, (3) Identify dependency chains between groups, (4) Ensure each group respects 4-teammate limit, (5) Output decomposition with dependency edges.
  CONSTRAINT: Use ONLY Agent/Skill frontmatter in Lead's context. No external reads.
  OUTPUT_FORMAT: L1 YAML task groups with dependency edges, L2 ASCII dependency graph.
user-invocable: true
disable-model-invocation: false
---

# Orchestration — Decompose

## Execution Model
- **TRIVIAL**: Lead-direct. Simple 1-2 task grouping.
- **STANDARD**: Lead-direct (uses auto-loaded Agent/Skill L1 for routing).
- **COMPLEX**: Lead-direct with sequential-thinking for complex grouping decisions.

Note: This skill is always Lead-direct because it requires access to Agent/Skill frontmatter already in Lead's context.

## Decision Points

### Tier Assessment for Decomposition Complexity
Lead assesses decomposition complexity based on plan-strategy output:
- **TRIVIAL**: 1-3 tasks total, single agent type needed, linear dependency chain or no dependencies. Lead groups directly — no analysis needed.
- **STANDARD**: 4-8 tasks, 2 agent types needed, manageable dependency structure (tree-shaped, no cross-cutting). Lead uses Agent L1 frontmatter for systematic matching.
- **COMPLEX**: 9+ tasks, 3+ agent types, complex dependency graph (cross-cutting dependencies, shared resources, critical path analysis needed). Lead uses sequential-thinking to evaluate grouping tradeoffs.

### Grouping Strategy Decision
Three grouping strategies, selected based on task characteristics:

**By Agent Capability** (default):
- Group all analyst tasks together, all implementer tasks together, etc.
- Best when: tasks of same type are independent of each other
- Risk: may split logically-related tasks across groups

**By Feature/Module** (when dependencies are heavy):
- Group tasks that work on the same module/feature together
- Requires one group to have mixed agent types (split into sub-phases internally)
- Best when: tight coupling between analysis and implementation for same feature
- Risk: uneven workload distribution

**By Dependency Chain** (when sequential ordering dominates):
- Group tasks along dependency paths — earlier tasks in earlier groups
- Best when: strong producer-consumer relationships between tasks
- Risk: reduces parallelism

Selection heuristic:
1. Count cross-task dependencies. If <20% of task pairs have dependencies → By Agent Capability
2. If >50% of dependencies are within the same module → By Feature/Module
3. If dependency graph has critical path > 3 levels deep → By Dependency Chain

### Teammate Capacity Planning
Each execution phase can spawn at most 4 teammates (CC platform limit):
- **Budget allocation**: If 8 tasks need implementers, split into 2 execution phases of 4 implementers each
- **Phase boundary rule**: Group A's outputs must be fully consolidated before Group B starts
- **Over-subscription detection**: If plan requires >4 simultaneous teammates of same type, decomposition MUST split into phases. Report phasing in L2.
- **Under-subscription optimization**: If only 2 teammates needed, consider whether tasks can be further parallelized or consolidated

### Lead-Direct vs Agent-Assisted Decomposition
This skill is always Lead-direct because:
1. Lead has all Agent/Skill L1 frontmatter auto-loaded in context
2. Decomposition requires cross-referencing agent capabilities against task requirements
3. No external data access needed (all information is in Lead's context)
4. Spawning an agent would require passing all L1 metadata, which is wasteful

Exception: For COMPLEX tier, Lead may use `sequential-thinking` MCP tool to structure reasoning about grouping tradeoffs without spawning a separate agent.

## Methodology

### 1. Read Validated Plan
Load plan-strategy output (execution phases, task list, dependencies).

### 2. Group Tasks by Agent Capability
Match tasks to agent profiles using L1 PROFILE tags:
- **analyst** (Profile-B): Read + analyze + write. For analysis, design, planning tasks.
- **researcher** (Profile-C): Read + analyze + web. For external doc research.
- **implementer** (Profile-D): Read + edit + bash. For source code changes.
- **infra-implementer** (Profile-E): Read + edit + write. For .claude/ config changes.

**Note**: delivery-agent (Profile-F) and pt-manager (Profile-G) are fork agents for specific skills (delivery-pipeline, task-management). They are not assignable for general task decomposition.

#### Agent Selection Decision Tree
For each task, determine agent type by checking requirements in order:
1. **Does task require shell command execution?** (build, test, deploy) → implementer (Profile-D)
2. **Does task modify `.claude/` files?** (skills, agents, settings, hooks) → infra-implementer (Profile-E)
3. **Does task require web access?** (fetch docs, search APIs, validate versions) → researcher (Profile-C)
4. **Does task require only read + analyze + write?** (review, audit, plan) → analyst (Profile-B)
5. **Ambiguous?** → Prefer the MORE CAPABLE profile (D > C > B > E for general tasks). Rationale: over-provisioning tools is better than under-provisioning.

#### Handling Multi-Capability Tasks
Some tasks need multiple agent capabilities (e.g., "research API docs then implement the client"):
- **Split the task**: Create sub-tasks — researcher fetches docs, implementer writes code
- **Add dependency**: implementer sub-task depends on researcher sub-task
- **Never assign multi-capability tasks to a single agent** — agents have fixed tool profiles

### 3. Build Task Groups
Group tasks that:
- Need the same agent profile
- Can execute in parallel (no dependencies)
- Stay within 4-teammate limit

#### Group Size Heuristics
- **Optimal group size**: 2-4 tasks per group (enough for meaningful work, not too many to track)
- **Maximum group size**: 6 tasks per group (beyond this, agent context may overflow)
- **Single-task groups**: Acceptable for critical path tasks or tasks with unique agent requirements
- **File count per group**: Target 3-8 files per agent instance. >10 files increases risk of agent context overflow.

#### Parallel Opportunity Detection
Identify groups that can execute simultaneously:
- No shared file dependencies between groups
- No producer-consumer data dependencies between groups
- Same execution phase (pre-execution, execution, post-execution)
- Document parallel groups explicitly in L2 output with parallel notation: `G1 ∥ G2`

### 4. Define Dependency Edges
Between groups:
- Group A -> Group B: at least 1 task in B depends on task in A
- Minimize cross-group dependencies
- No cycles allowed

#### Dependency Classification
- **Hard dependency**: Group B REQUIRES output file from Group A. Must be sequential.
- **Soft dependency**: Group B BENEFITS from Group A's output but can proceed with stale data. Can be parallel with post-hoc reconciliation.
- **Interface dependency**: Group B uses an interface defined by Group A's task. The interface contract (from plan-interface) substitutes for runtime dependency — groups can be parallel if contracts are stable.
- **Resource dependency**: Group B and Group C both modify the same file. Must be sequential (assigned to same agent or phased).

Always prefer hard dependencies over soft. When uncertain, treat as hard.

### 5. Output Decomposition
Produce task-group list with:
- Group ID, tasks, agent capability match
- Dependency edges between groups
- Execution order (topological sort)

## Failure Handling

### Plan-Verify Data Missing or Incomplete
- **Cause**: plan-verify domain didn't produce clean PASS or data is malformed
- **Action**: Route back to plan-verify with specific missing data request
- **Never proceed**: without verified plan data — decomposition on unvalidated plans creates cascading errors in orchestration-assign and execution

### Unassignable Tasks (No Agent Match)
- **Cause**: Task requires capability not available in any agent profile (e.g., needs both Bash and WebSearch simultaneously)
- **Action**: Split the task into sub-tasks, each matching a single agent profile
- **If unsplittable**: Flag as architectural issue, route back to plan-decomposition for redesign

### Dependency Cycle Detected
- **Cause**: Circular dependency between task groups
- **Action**: Merge the cyclic groups into a single group (same agent handles both). If agents differ, identify which dependency can be broken (converted to interface dependency with stable contract).
- **Report in L2**: Document the cycle and resolution approach

### Capacity Overflow (>4 teammates needed)
- **Cause**: More tasks need parallel execution than capacity allows
- **Action**: Phase the execution — split into sequential execution phases, each <=4 teammates
- **Priority**: Assign critical-path tasks to Phase 1, non-critical to Phase 2
- **Report in L1**: `phases: 2` (or more) to signal multi-phase execution to orchestration-assign

## Anti-Patterns

### DO NOT: Read External Files for Agent Capabilities
Agent L1 frontmatter is already in Lead's context (auto-loaded). Do NOT use Glob/Grep/Read to find agent definitions — this wastes turns and the information is already available.

### DO NOT: Create Single-Task-Per-Group Decomposition
Unless a task has unique agent requirements or is on the critical path, grouping each task separately creates excessive overhead. Group related tasks that use the same agent type.

### DO NOT: Ignore the 4-Teammate Limit
The platform limit is 4 concurrent teammates per execution phase. Decomposing into 6 parallel groups will fail at orchestration-verify. Always count agent instances during decomposition.

### DO NOT: Mix .claude/ and Non-.claude/ Files in Same Group
Files in `.claude/` require infra-implementer (Profile-E). Application source files require implementer (Profile-D). A mixed group would need an agent type that doesn't exist. Always separate by file domain.

### DO NOT: Decompose Without Dependency Awareness
Grouping tasks purely by agent type without checking dependencies creates execution failures. Task B that depends on Task A's output CANNOT be in a parallel group with Task A.

### DO NOT: Over-Decompose TRIVIAL Tiers
For TRIVIAL tiers (1-3 tasks), the overhead of multi-group decomposition exceeds the benefit. Create 1 group with all tasks assigned to a single agent.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| plan-verify domain | PASS verdict for all 3 checks | L1 YAML: correctness, completeness, robustness all PASS |
| plan-decomposition | Task list with file assignments | L1 YAML: `tasks[].{id, description, files[], complexity}` |
| plan-interface | Interface contracts between tasks | L2 markdown: function signatures, data flow |
| plan-strategy | Execution sequence and risk mitigations | L2 markdown: critical path, parallel opportunities |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| orchestration-assign | Task groups with dependency edges | Always (decomposition output is assign input) |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Plan data missing | plan-verify domain | Specific missing data request |
| Unassignable task | plan-decomposition | Task that can't be matched to agent profile |
| Dependency cycle | Self (re-decompose) | Cycle details and merge recommendation |
| Capacity overflow | Self (re-phase) | Current count, proposed phase split |

## Quality Gate
- Every task assigned to exactly 1 group
- Agent capability matches task requirements
- Dependency graph is acyclic
- Each execution phase uses <=4 teammate instances total

## Output

### L1
```yaml
domain: orchestration
skill: decompose
group_count: 0
dependency_edges: 0
groups:
  - id: ""
    tasks: []
    agent_capability: ""
```

### L2
- Task grouping rationale
- Dependency edge justification
- ASCII dependency graph

---
name: task-management
description: |
  [Px·Delivery·TaskMgmt] Task lifecycle manager for PT and work tasks via Task API. Heavy ops → pt-manager agent. Light ops → Lead direct. Exactly 1 PT per pipeline.

  WHEN: Any phase. (1) Pipeline start: create PT. (2) Plan ready: batch tasks. (3) Execution: status updates. (4) Commit done: PT completed.
  DOMAIN: delivery (skill 2 of 2).
  INPUT_FROM: Pipeline context (tier, phase, requirements, architecture decisions).
  OUTPUT_TO: PT lifecycle (create/update/complete), work tasks (batch creation), ASCII status visualization.

  METHODOLOGY: (1) Classify operation weight (heavy/light), (2) Route heavy → pt-manager, light → Lead, (3) Execute task operations, (4) Validate no duplicate PTs, (5) Return status.
  OUTPUT_FORMAT: L1 YAML (operation type, task counts), L2 task details or ASCII visualization.
user-invocable: true
disable-model-invocation: false
argument-hint: "[action] [args]"
---

# Task Management

## Execution Model

- **TRIVIAL**: Lead-direct. Single TaskUpdate for PT status change. No agent spawn.
- **STANDARD**: Lead-direct or pt-manager for batch operations. maxTurns: 15.
- **COMPLEX**: pt-manager spawn for full PT lifecycle + batch task creation. maxTurns: 25.

**Operation routing**:
- **Heavy ops** → spawn `pt-manager` (`subagent_type: pt-manager`). Full Task API (TaskCreate + TaskUpdate).
- **Light ops** → Lead executes directly. Single TaskUpdate for status/metadata changes.

## Phase-Aware Execution

This skill runs in P2+ Team mode only. Agent Teams coordination applies:
- **Communication**: Use SendMessage for result delivery to Lead. Write large outputs to disk.
- **Task tracking**: Update task status via TaskUpdate after completion.
- **No shared memory**: Insights exist only in your context. Explicitly communicate findings.
- **File ownership**: Only modify files assigned to you. No overlapping edits with parallel agents.

## Methodology

### 1. PT Creation

1. TaskList → verify no existing `[PERMANENT]` task
2. If user intent unclear → AskUserQuestion
3. TaskCreate:
   - subject: `[PERMANENT] {feature-name}`
   - description: User intent + constraints + acceptance criteria (max useful content)
   - metadata:
     ```json
     {
       "type": "permanent",
       "tier": "TRIVIAL|STANDARD|COMPLEX",
       "current_phase": "P0",
       "commit_status": "pending",
       "references": [],
       "user_directives": []
     }
     ```
4. Report PT task ID to Lead

### 2. PT Update (Read-Merge-Write)

1. TaskList → find `[PERMANENT]` task
2. TaskGet → read current description + metadata
3. **Merge** new information into existing (never overwrite without reading)
   - Add to `user_directives[]` if user adds requirement
   - Add to `references[]` if new file/path relevant
   - Update `current_phase` on phase transition
4. TaskUpdate with merged result
5. If description exceeds useful density → move details to file, keep index in description

### 2b. PT Phase Checkpoint (Compaction Recovery)

After each phase completion, Lead updates PT metadata with compact phase signal:
1. TaskGet PT → read current metadata
2. Add phase signal: `metadata.phase_signals.{phase} = "{STATUS}|{key_signal}"`
3. Update `metadata.current_phase` to next phase
4. TaskUpdate with merged metadata

This enables compaction recovery: Lead calls TaskGet(PT) → reads `phase_signals` → knows entire pipeline history.
Example metadata after P3:
```json
{
  "phase_signals": {
    "p0": "PASS|reqs:6",
    "p1": "PASS|arch:4waves",
    "p2": "PASS|gaps:0",
    "p3": "PASS|tasks:12|deps:8"
  }
}
```

### 3. Work Task Batch Creation

1. Read plan output files (plan domain L1/L2)
2. For each planned sub-task:
   - TaskCreate with actionable subject
   - metadata:
     ```json
     {
       "type": "work",
       "phase": "P7",
       "domain": "execution",
       "skill": "execution-code",
       "agent": "implementer",
       "files": ["src/target.ts"],
       "priority": "high",
       "parent": "{PT-task-id}",
       "problem": "기존 문제 상세 설명",
       "improvement": "이 작업이 문제를 어떻게 개선하는지"
     }
     ```
   - Set `addBlockedBy` for dependency chain
   - activeForm: present-tense Korean description of work
3. Write detail files for tasks needing extended documentation
4. Report task count + dependency graph summary to Lead

### 4. Real-Time Update Protocol

Teammates update their assigned tasks during execution:

| Event | TaskUpdate Fields |
|-------|------------------|
| Start work | `status: "in_progress"`, `activeForm: "현재 작업 설명"` |
| Progress | `metadata: {progress update, partial results}` |
| Complete | `status: "completed"`, `metadata: {result summary}` |
| Failed | `status: "failed"`, `metadata: {error: "reason"}` |

Lead monitors via TaskList. No polling needed — state always current.

### 5. ASCII Visualization (Korean Output)

1. TaskList → get all tasks
2. TaskGet for each active/blocked task (skip completed for brevity if many)
3. Group by `metadata.phase` and `metadata.domain`
4. Output structure:

```
╔═ 파이프라인 개요 ═══════════════════════════════╗
║  이름, 티어, 현재 단계, 전체 진행률             ║
╠═ 도메인별 진행률 ═══════════════════════════════╣
║  각 phase 진행 바 + 완료/전체 카운트            ║
╠═ 진행중 작업 ═══════════════════════════════════╣
║  #ID [agent] 진행중  N%                          ║
║      대상: 파일 목록                             ║
║      문제: 이 작업이 해결하려는 기존 문제        ║
║      개선: 어떻게 문제를 개선하는지 상세 설명    ║
║      차단: 의존성 / 후속: 이 작업을 기다리는 것  ║
╠═ 완료된 작업 ═══════════════════════════════════╣
║  #ID [agent] 완료 ✓                              ║
║      문제: → 결과: 구조                          ║
╠═ 대기중 작업 ═══════════════════════════════════╣
║  #ID [agent] 대기  ← 선행 작업 목록              ║
║      문제: → 계획: 구조                          ║
╠═ PT 참조사항 ═══════════════════════════════════╣
║  사용자 지시사항 + 코드베이스 참조               ║
╚═════════════════════════════════════════════════╝
```

Key rules:
- **문제**: `metadata.problem` — 기존 상태의 무엇이 불충분한가
- **개선/결과/계획**: `metadata.improvement` — 이 작업이 어떻게 개선하는가
- Status labels: 진행중, 완료, 대기, 실패
- **Delivery**: pt-manager sends micro-signal to Lead via SendMessage: `{STATUS}|action:{type}|tasks:{N}|ref:/tmp/pipeline/task-management.md`.

### 6. PT Completion

1. TaskList → verify all work tasks with `parent: {PT-id}` are `completed`
2. If incomplete tasks remain → report blockers
3. TaskUpdate PT: `metadata.commit_status` → `"committed"`
4. TaskUpdate PT: `status` → `"completed"`

## Decision Points

### Heavy vs Light Operation Routing
- **Heavy ops (pt-manager spawn)**: PT creation, PT update with complex merge, batch work task creation, ASCII visualization. These require multiple Task API calls and complex logic. Spawn pt-manager agent (`subagent_type: pt-manager`).
- **Light ops (Lead-direct)**: Single TaskUpdate for status change (e.g., marking a task in_progress or completed), simple metadata field update. Lead executes inline without agent spawn to avoid overhead.

### PT-Manager Spawn DPS
- **Context**: PT task ID, current pipeline phase, operation type (create/update/batch/visualize), plan domain L1/L2 output paths if batch creation.
- **Task**: "[Specific operation]: Create PT with structured metadata, OR update PT with phase results via Read-Merge-Write, OR batch create work tasks from plan output with dependency chains, OR generate ASCII pipeline visualization."
- **Constraints**: pt-manager agent. Tools: Read, Glob, Grep, Write, TaskCreate, TaskUpdate, TaskGet, TaskList, AskUserQuestion. No Edit/Bash. maxTurns: 15 (STANDARD), 25 (COMPLEX).
- **Expected Output**: L1 YAML with `action`, `pt_id`, `task_count`. L2 action summary or ASCII visualization.
- **Delivery**: SendMessage to Lead: `PASS|action:{type}|tasks:{N}|ref:/tmp/pipeline/task-management.md`

#### PT-Manager Tier-Specific DPS Variations
**TRIVIAL**: Lead-direct. Single TaskUpdate inline. No pt-manager spawn.
**STANDARD**: pt-manager spawn for batch creation or complex PT update. maxTurns: 15.
**COMPLEX**: pt-manager spawn with full lifecycle management + visualization. maxTurns: 25.

### PT Description Density Management
- **Keep in PT description**: Core requirements, acceptance criteria, tier classification, key architecture decisions (up to ~2000 chars). Information that every teammate needs when they TaskGet the PT.
- **Move to file reference**: Extended design docs, full task breakdowns, detailed analysis reports. Store in workspace files and add file paths to PT `references[]` array. Prevents PT description from becoming unwieldy.

### Work Task Granularity
- **Fine-grained tasks** (1-2 files each): Use when tasks are highly parallelizable and independent. Each task maps to a single implementer assignment. Typical for execution phase.
- **Coarse-grained tasks** (3-4 files each): Use when files are tightly coupled and must be modified atomically. Fewer tasks mean simpler dependency management. Max 4 files per task to maintain single-responsibility.

### Dependency Chain Strategy
- **Linear chain**: Tasks must execute in strict sequence (T1 -> T2 -> T3). Use `addBlockedBy` to enforce ordering. Simple but limits parallelism.
- **Diamond pattern**: Tasks T2 and T3 both depend on T1, and T4 depends on both T2 and T3. Maximizes parallelism while respecting dependencies. Common for code + infra parallel execution converging at review.
- **No dependencies**: Tasks are fully independent. No `addBlockedBy` needed. Used for parallel analysis tasks in P0-P1 phases.

## Failure Handling

### Duplicate PT Detection
- **Cause**: PT creation attempted when one already exists (e.g., pipeline-resume created a new PT without checking, or two pipeline starts raced).
- **Action**: TaskList to find all `[PERMANENT]` tasks. If multiple exist, compare metadata to determine which is authoritative (most recent, most complete metadata). Complete the duplicate with a note. Never delete -- mark completed with `metadata.reason: "duplicate"`.

### Circular Dependency in Work Tasks
- **Cause**: `addBlockedBy` creates a cycle (T1 blocks T2, T2 blocks T3, T3 blocks T1). Pipeline deadlocks -- no task can start.
- **Action**: Detect cycle by traversing blockedBy chains. Break the cycle at the weakest dependency (the one where the blocking relationship is least essential). Document the decision in PT metadata.

### PT Metadata Corruption (Partial or Malformed)
- **Cause**: A TaskUpdate wrote partial or malformed metadata (e.g., JSON parse error, missing required fields like `type` or `current_phase`).
- **Action**: Read current PT state. Reconstruct missing fields from task history and pipeline context. Update with corrected metadata. Log the corruption event in PT metadata for audit trail.

### Work Task Status Stuck in_progress
- **Cause**: Agent assigned to the task crashed, exhausted turns, or was interrupted without updating status.
- **Action**: Lead detects via TaskList monitoring. If agent is confirmed terminated, update task status to `failed` with `metadata.error: "agent_interrupted"`. Route to the appropriate execution skill for re-assignment.

## Anti-Patterns

### DO NOT: Overwrite PT Without Reading First
Every PT update must follow Read-Merge-Write: TaskGet current state, merge new information, TaskUpdate with merged result. Blind overwrites lose information from other phases or concurrent updates.

### DO NOT: Create Work Tasks Without Complete Metadata
Every work task must have all metadata fields: type, phase, domain, skill, agent, files, priority, parent. Missing fields break ASCII visualization, Lead routing, and dependency tracking. Incomplete tasks are worse than no tasks.

### DO NOT: Use PT for Ephemeral Communication
PT is the persistent pipeline record, not a messaging system. Do not add temporary status messages, debug notes, or agent-to-agent communication to PT metadata. Use Task descriptions or dedicated work tasks for transient information.

### DO NOT: Create Cyclic Dependencies
Always verify the dependency graph is acyclic before adding `addBlockedBy` relationships. A single cycle deadlocks all tasks in the chain. When in doubt, draw the dependency graph explicitly.

### DO NOT: Complete PT Before All Work Tasks Finish
PT completion signals "pipeline done." If any child work task is still in_progress, pending, or failed, completing the PT creates a false signal. Always verify all `parent: {PT-id}` tasks are completed first.

## Transitions

### Receives From
| Source Skill | Data Expected | Format |
|-------------|---------------|--------|
| (User invocation) | Task management action request | `$ARGUMENTS` text: action + args (e.g., "create-pt SRC", "visualize") |
| (Any pipeline phase) | Phase completion requiring PT update | Lead routes with phase results for PT metadata merge |
| plan-decomposition | Task breakdown requiring batch creation | L1 YAML: task list with files, dependencies, priorities |
| delivery-pipeline | Pipeline completion requiring PT close | L1 YAML: `commit_hash`, `status: delivered` |

### Sends To
| Target Skill | Data Produced | Trigger Condition |
|-------------|---------------|-------------------|
| (Lead context) | PT task ID and pipeline state | After PT creation or update (Lead uses for routing) |
| (Lead context) | ASCII visualization | After visualize action (Lead displays to user) |
| (Lead context) | Dependency graph summary | After batch work task creation |

### Failure Routes
| Failure Type | Route To | Data Passed |
|-------------|----------|-------------|
| Duplicate PT detected | (Self - resolve) | Both PT task IDs for deduplication |
| Circular dependency | (Self - break cycle) | Cycle path details |
| PT metadata corruption | (Self - reconstruct) | Current PT state + reconstruction context |

## Quality Gate
- Exactly 1 [PERMANENT] task exists (no duplicates)
- PT updates use Read-Merge-Write (never blind overwrite)
- Work tasks have complete metadata (type, phase, domain, skill, agent, files)
- Dependency chains are acyclic (addBlockedBy creates no cycles)
- ASCII visualization matches current TaskList state

## Output

### L1
```yaml
domain: cross-cutting
skill: task-management
action: create-pt|update-pt|batch-create|visualize|complete-pt
pt_id: ""
task_count: 0
```

### L2
- Action summary with affected task IDs
- ASCII visualization (if visualize action)
- Dependency graph changes (if batch-create)

---
name: task-management
description: |
  [X-Cut·TaskMgmt·TaskAPI] Task lifecycle manager + real-time dynamic references. Manages PT, work tasks, dependencies, progress via Task API.

  WHEN: (1) Pipeline start: create PT. (2) User adds requirements: update PT (Read-Merge-Write). (3) Plan ready: batch create work tasks with dependencies. (4) Execution: teammates update status real-time. (5) Status query: ASCII viz per domain. (6) Commit done: PT completed.
  DOMAIN: Cross-cutting, any phase.

  ROLES: Heavy ops (PT create/update, batch tasks, ASCII viz) -> pt-manager agent. Light ops (single TaskUpdate) -> Lead direct.
  METADATA: Work={type,phase,domain,skill,agent,files,priority,parent,problem,improvement}. PT={type:permanent,tier,current_phase,commit_status,references}.
  CONSTRAINT: Exactly 1 PT ([PERMANENT] subject). PT completed only at final commit. ASCII viz in Korean.
user-invocable: true
disable-model-invocation: true
argument-hint: "[action] [args]"
---

# Task Management

## Execution Model

- **Heavy ops** → spawn `pt-manager` (`subagent_type: pt-manager`). Full Task API (TaskCreate + TaskUpdate).
- **Light ops** → Lead executes directly. Single TaskUpdate for status/metadata changes.

## Operations

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

### 6. PT Completion

1. TaskList → verify all work tasks with `parent: {PT-id}` are `completed`
2. If incomplete tasks remain → report blockers
3. TaskUpdate PT: `metadata.commit_status` → `"committed"`
4. TaskUpdate PT: `status` → `"completed"`

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

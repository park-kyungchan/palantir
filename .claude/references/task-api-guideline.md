# Task API Integration Guideline

> **Version:** 3.1.0 | **Last Updated:** 2026-02-06
> **Purpose:** Comprehensive TodoWrite System, Dynamic Schedule Management, Hook-based Behavioral Enforcement, Orchestrator Decision Framework

---

## [CRITICAL] Task ID Collision Resolution (V2.1.0)

> **Issue:** Hook의 `task-lifecycle-gate.sh`가 `.claude/tasks/` 하위 **모든 세션 디렉토리**를 검색하여 Task ID로 매칭

### Problem Symptoms

```
PreToolUse:TaskUpdate hook blocking error:
"Invalid status transition: completed → in_progress"

실제 상황: 현재 세션 Task는 pending 상태이나,
이전 세션의 동일 ID Task가 completed 상태로 먼저 발견됨
```

### Root Cause

```
.claude/tasks/
├── palantir-dev/           # 이전 세션 (Task #10 = completed)
│   └── 10.json
├── palantir-dev-cow-pipeline-20260202/  # 현재 세션 (Task #10 = pending)
│   └── 10.json
```

Hook의 `get_task_status()` 함수가 glob 패턴으로 **모든 디렉토리**를 순회하며 먼저 발견된 파일의 상태를 반환.

### Resolution Steps

1. **현재 세션 디렉토리 확인:**
   ```bash
   ls /home/palantir/.claude/tasks/
   ```

2. **Task JSON 파일 직접 수정:**
   ```bash
   TASK_DIR="/home/palantir/.claude/tasks/{current-session}"

   cat > "$TASK_DIR/N.json" << 'EOF'
   {
     "id": "N",
     "subject": "Task subject",
     "description": "Task description",
     "status": "completed",
     "blocks": [],
     "blockedBy": []
   }
   EOF
   ```

3. **TaskList로 상태 확인:**
   ```
   TaskList → 모든 Task가 completed 상태 확인
   ```

### Prevention

- 새 세션 시작 시 이전 세션의 stale Task 정리
- Task ID 네임스페이스 충돌 방지를 위한 세션별 prefix 고려

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
// Step 1: [PERMANENT] Task 생성 (항상 최상단)
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  description: "작업 시작 전 컨텍스트 복구 및 상태 확인",
  activeForm: "Checking context and recovery status",
  metadata: {
    priority: "CRITICAL",
    phase: "permanent",
    tags: ["permanent", "context-recovery"]
  }
})

// Step 2: 실제 작업 Task들 생성
TaskCreate({
  subject: "실제 작업 1",
  description: "상세 설명",
  activeForm: "Working on task 1",
  metadata: {
    priority: "HIGH",
    phase: "phase-1"
  }
})
```

### 2.1 [PERMANENT] Task Lifecycle 규칙

> **CRITICAL:** `[PERMANENT]` 태스크는 **상시 참조**용이며, 전체 작업 완료 시까지 completed로 변경 금지

```
┌─────────────────────────────────────────────────────────────────┐
│  [PERMANENT] Task Lifecycle                                      │
├─────────────────────────────────────────────────────────────────┤
│  1. 작업 시작 시 → status: "in_progress" (최초 설정)            │
│  2. 작업 진행 중 → status: "in_progress" 유지 (상시 참조)       │
│  3. 전체 작업 완료 → status: "completed" (최종 단계에서만)      │
├─────────────────────────────────────────────────────────────────┤
│  ⚠️ 중간에 completed로 변경 시 → 컨텍스트 참조 불가 위험       │
└─────────────────────────────────────────────────────────────────┘
```

#### [PERMANENT] Task 완료 조건

| 조건 | 확인 |
|------|------|
| 모든 Phase Task가 completed | ✅ |
| 검증 Task (Phase 6 등)가 completed | ✅ |
| 최종 커밋/PR 생성 완료 | ✅ |

```javascript
// ❌ WRONG: 중간에 [PERMANENT] 완료 처리
TaskUpdate({ taskId: permanentTask.id, status: "completed" })  // 다른 작업 진행 중
// → 상시 참조 불가, 컨텍스트 손실 위험

// ✅ CORRECT: 최종 작업 완료 후에만 completed
if (allPhasesCompleted && verificationDone && commitCreated) {
  TaskUpdate({ taskId: permanentTask.id, status: "completed" })
}
```

### 3. 의존성 체인 설정

```
[PERMANENT] Context Check
        ↓
    Phase 1 Tasks (병렬 가능)
        ↓
    Phase 2 Tasks (Phase 1 완료 후)
        ↓
    Verification & Summary
```

---

## Task API 활용 패턴

### Pattern 1: Linear Chain (순차 실행)

```javascript
task1 = TaskCreate({ subject: "Step 1", ... })
task2 = TaskCreate({ subject: "Step 2", ... })
task3 = TaskCreate({ subject: "Step 3", ... })

TaskUpdate({ taskId: task2.id, addBlockedBy: [task1.id] })
TaskUpdate({ taskId: task3.id, addBlockedBy: [task2.id] })
```

### Pattern 2: Diamond (병렬 → 수렴)

```javascript
setup = TaskCreate({ subject: "Setup", ... })
taskA = TaskCreate({ subject: "Task A", ... })
taskB = TaskCreate({ subject: "Task B", ... })
merge = TaskCreate({ subject: "Merge Results", ... })

TaskUpdate({ taskId: taskA.id, addBlockedBy: [setup.id] })
TaskUpdate({ taskId: taskB.id, addBlockedBy: [setup.id] })
TaskUpdate({ taskId: merge.id, addBlockedBy: [taskA.id, taskB.id] })
```

### Pattern 3: Phase-based (단계별)

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

| Priority | 사용 시점 | 예시 |
|----------|----------|------|
| `CRITICAL` | 즉시 처리 필수, 블로커 | [PERMANENT] 항목, 보안 이슈 |
| `HIGH` | 핵심 기능, 메인 작업 | 주요 구현 Task |
| `MEDIUM` | 일반 작업 | 리팩토링, 개선 |
| `LOW` | 나중에 해도 됨 | 문서화, 정리 |

---

## Metadata 활용 규칙

### 필수 Metadata

```javascript
metadata: {
  priority: "CRITICAL|HIGH|MEDIUM|LOW",  // 우선순위
  phase: "phase-name",                    // 단계명
  tags: ["tag1", "tag2"]                  // 분류 태그
}
```

### 선택 Metadata

```javascript
metadata: {
  owner: "terminal-b",           // 담당자
  parentTaskId: "task-123",      // 부모 Task (계층 구조)
  source: "skill:orchestrate",   // 생성 출처
  promptFile: "path/to/prompt",  // Worker prompt 파일
  estimatedTime: "30m",          // 예상 소요 시간
  actualTime: "25m"              // 실제 소요 시간
}
```

---

## 동적 Schedule 관리

### 진행도 추적

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

### Blocker 해소 시 자동 Unblock

Task가 완료되면 해당 Task를 `blockedBy`로 가진 다른 Task들이 자동으로 unblock됩니다.

```javascript
// task1 완료 시
TaskUpdate({ taskId: task1.id, status: "completed" })
// → task1을 blockedBy로 가진 task2, task3 등이 자동 unblock
```

---

## 워크플로우 템플릿

### 신규 작업 시작 시

```javascript
// 1. [PERMANENT] Context Check
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  description: `
    1. _active_workload.yaml 확인
    2. TaskList로 현재 상태 파악
    3. 관련 L1/L2/L3 파일 읽기
    4. 이전 작업 컨텍스트 복구
  `,
  activeForm: "Checking context",
  metadata: { priority: "CRITICAL", phase: "permanent" }
})

// 2. 작업 분해
TaskCreate({
  subject: "작업 분해 및 계획 수립",
  description: "전체 작업을 단계별로 분해",
  activeForm: "Planning work breakdown",
  metadata: { priority: "HIGH", phase: "planning" }
})

// 3. 실제 작업 Tasks
// ... (작업별로 추가)

// 4. 검증 및 정리
TaskCreate({
  subject: "검증 및 결과 정리",
  description: "모든 작업 완료 확인 및 결과 문서화",
  activeForm: "Verifying and summarizing",
  metadata: { priority: "HIGH", phase: "verification" }
})
```

---

## Anti-Patterns (피해야 할 패턴)

| Anti-Pattern | 문제점 | 올바른 방법 |
|--------------|--------|-------------|
| Task 없이 작업 시작 | 추적 불가, 맥락 손실 | TaskCreate 먼저 |
| [PERMANENT] 생략 | 컨텍스트 복구 누락 | 항상 최상단에 포함 |
| 의존성 없는 순차 작업 | 병렬화 기회 손실 | addBlockedBy 활용 |
| metadata 미사용 | 분류/필터링 불가 | priority, phase 필수 |
| status 미업데이트 | 진행도 파악 불가 | in_progress → completed |

---

## Checklist

작업 시작 전:
- [ ] [PERMANENT] Context Check Task 생성
- [ ] _active_workload.yaml 확인
- [ ] TaskList로 현재 상태 파악
- [ ] 관련 파일 읽기 (L1/L2/L3)

작업 중:
- [ ] Task status를 in_progress로 업데이트
- [ ] 의존성 체인 준수
- [ ] metadata에 진행 상황 기록

작업 완료 후:
- [ ] Task status를 completed로 업데이트
- [ ] 결과 문서화
- [ ] 다음 Task unblock 확인

---

> **Remember:** 작업 전체 맥락을 잃지 않고 작업하는 것이 품질의 핵심입니다.
> [PERMANENT] 항목은 이를 보장하는 안전장치입니다.

---

## Agents 연계 패턴

### Agent 목록 및 Task API 연계

| Agent | 역할 | Task API | 모델 |
|-------|------|----------|------|
| `onboarding-guide` | 신규 사용자 안내 | ✗ | haiku |
| `pd-readonly-analyzer` | 읽기 전용 분석 | ✓ (위임 가능) | haiku |
| `pd-skill-loader` | 스킬 사전 로드 | ✗ | sonnet |
| `ontology-roadmap` | ODA 로드맵 문서 | ✗ | - |

### Agent 위임 패턴

```javascript
// pd-readonly-analyzer를 통한 안전한 코드 분석
Task({
  subagent_type: "pd-readonly-analyzer",
  prompt: "분석 요청...",
  run_in_background: true
})
// 결과: L1/L2/L3 형식으로 .agent/outputs/에 저장
```

### Agent 패턴

| 패턴 | Agent | 설명 |
|------|-------|------|
| **A1: Tool Restrictions** | pd-readonly-analyzer | `disallowedTools`로 수정 방지 |
| **A2: Skill Injection** | pd-skill-loader | 런타임 발견 없이 스킬 사전 로드 |

---

## Skills 연계 패턴

### E2E Pipeline과 Task API

```
/clarify ────────────────────────► (Task API 미사용)
    │
    ▼
/research ───────────────────────► Task(Explore) × N (병렬)
    │
    ▼
/planning ───────────────────────► Task(Plan) × N (병렬)
    │
    ▼
/orchestrate ────────────────────► TaskCreate() × N  ⭐ 유일한 Task 생성점
                                   TaskUpdate(addBlockedBy)
    │
    ▼
/assign ─────────────────────────► TaskUpdate(owner)  ⭐ 소유권 할당
    │
    ▼
/worker (병렬) ──────────────────► TaskUpdate(status)
                                   TaskCreate() (Sub-Orchestrator 모드 시)
    │
    ▼
/collect ────────────────────────► TaskList() (완료 확인)
    │
    ▼
/synthesis ──────────────────────► Decision: COMPLETE | ITERATE
    │
    ├── COMPLETE ──────────────► /commit-push-pr
    └── ITERATE ───────────────► /rsil-plan → /orchestrate
```

### Skill별 Task API 사용 패턴

| Skill | TaskCreate | TaskUpdate | TaskList | TaskGet |
|-------|------------|------------|----------|---------|
| `/orchestrate` | ✓ (유일) | ✓ (의존성) | - | - |
| `/assign` | - | ✓ (owner) | ✓ (auto) | ✓ |
| `/worker` | ✓ (Sub-Orch) | ✓ (status) | - | ✓ |
| `/collect` | - | - | ✓ | - |
| `/synthesis` | - | - | - | - |

---

## Orchestrator / Sub-Orchestrator 패턴

### 계층 구조

```
┌─────────────────────────────────────────────────────────────┐
│  Main Orchestrator (Terminal A)                             │
│  - TaskCreate로 전체 작업 분해                               │
│  - TaskUpdate(addBlockedBy)로 의존성 설정                    │
│  - /assign으로 Terminal B,C,D에 할당                         │
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

### Sub-Orchestrator 활성화

```javascript
// /assign에서 Sub-Orchestrator 모드 설정
TaskUpdate({
  taskId: taskId,
  owner: "terminal-c",
  metadata: {
    hierarchyLevel: 1,
    subOrchestratorMode: true,
    canDecompose: true
  }
})

// /worker에서 서브태스크 생성
TaskCreate({
  subject: "Subtask 1.1",
  metadata: {
    hierarchyLevel: 2,
    parentTaskId: parentTask.id
  }
})
```

---

## Auto-Delegation 패턴 (EFL)

### 트리거 조건

```javascript
// Skills with agent_delegation.enabled: true && default_mode: true
// 자동으로 Sub-Orchestrator로 동작

const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
```

### Complexity 기반 Agent 수

| Complexity | Agent Count | 트리거 조건 |
|------------|-------------|-------------|
| simple | 1 | 1-5 requirements |
| moderate | 2 | 6-15 requirements |
| complex | 3 | 16+ requirements |

---

## 통합 워크플로우 템플릿

### 새 프로젝트 시작

```javascript
// 1. [PERMANENT] Context Check
TaskCreate({
  subject: "[PERMANENT] Context & Recovery Check",
  metadata: { priority: "CRITICAL", phase: "permanent" }
})

// 2. E2E Pipeline Tasks
TaskCreate({ subject: "/clarify 실행", metadata: { phase: "clarify" } })
TaskCreate({ subject: "/research 실행", metadata: { phase: "research" } })
TaskCreate({ subject: "/planning 실행", metadata: { phase: "planning" } })
TaskCreate({ subject: "/orchestrate 실행", metadata: { phase: "orchestrate" } })
TaskCreate({ subject: "/collect 실행", metadata: { phase: "collect" } })
TaskCreate({ subject: "/synthesis 실행", metadata: { phase: "synthesis" } })

// 3. 의존성 체인 설정
// clarify → research → planning → orchestrate → collect → synthesis
```

---

## 핵심 규칙 요약

1. **TaskCreate는 /orchestrate만** - 다른 스킬은 기존 Task 조작만
2. **owner로 할당** - /assign이 TaskUpdate(owner)로 터미널 할당
3. **blockedBy로 의존성** - DAG 형성, Gate 4에서 순환 검증
4. **Sub-Orchestrator 지원** - Worker가 subtask 생성 가능
5. **[PERMANENT] 필수** - 모든 작업 시작 전 컨텍스트 확인
6. **L1/L2/L3 출력** - 모든 Agent/Skill 출력은 Progressive Disclosure

---

---

## Hooks 연계 패턴 (코드레벨 분석)

> **Note:** This section documents the hook inventory from code-level analysis V1.4.0.
> For current hook count (50 files), see CLAUDE.md Section 7. Directory Structure.

### Hook 분류 (Historical - 26개 documented at V1.4.0)

| 분류 | Hooks | 역할 |
|------|-------|------|
| **Session** | session-start.sh, session-end.sh, session-health.sh | 세션 초기화/종료/상태 |
| **Pipeline Setup** | clarify-setup.sh, planning-setup.sh, orchestrate-setup.sh | 스킬 전 선행 조건 (Gate 1-4) |
| **Pipeline Finalize** | clarify-finalize.sh, planning-finalize.sh, research-finalize.sh | 완료 후 handoff |
| **Validation** | clarify-validate.sh, research-validate.sh, orchestrate-validate.sh | Shift-Left 검증 |
| **Task Pipeline** | pd-task-interceptor.sh, pd-task-processor.sh | **L1/L2/L3 자동화** |
| **Security** | permission-guard.sh, governance-check.sh | 동적 리스크 감지 |

### Task API 핵심 연계 Hooks

#### 1. pd-task-interceptor.sh (PreToolUse:Task)

```yaml
트리거: Tool == "Task" && subagent_type not in SKIP_AGENTS
기능:
  1. L1/L2/L3 프롬프트 자동 주입
  2. 캐시 확인 (hit 시 작업 블록)
  3. Worker prompt 파일 생성 (.agent/prompts/pending/)
  4. run_in_background=true, model="opus" 자동 추가
```

#### 2. pd-task-processor.sh (PostToolUse:Task)

```yaml
트리거: Task 완료 후
기능:
  1. L1 필드 파싱 (taskId, priority, status, l2Path...)
  2. 캐시 저장 (~/.claude/cache/l1l2/{hash}.json)
  3. Prompt 파일 이동 (pending → completed)
  4. Priority 기반 가이던스 생성
```

#### 3. session-start.sh (SessionStart)

```yaml
기능:
  1. Post-Compact Recovery 감지
     - _active_workload.yaml 존재 여부 확인
     - slug, current_skill, current_phase 추출
  2. Task List 연속성
     - CLAUDE_CODE_TASK_LIST_ID 기반 pending tasks 로드
  3. 출력 JSON에 recovery 블록 포함
```

### Hook 트리거 플로우

```
Session Start
     │
     └── session-start.sh
            ├── Post-Compact Recovery 감지
            └── Task List 로드

Skill Invocation (/clarify, /planning, ...)
     │
     ├── {skill}-setup.sh (PreToolUse)
     │      └── Gate 검증 (의존성, 입력)
     │
     └── {skill}-finalize.sh (Stop)
            └── Handoff 생성 (다음 스킬 제안)

Task Tool Call
     │
     ├── pd-task-interceptor.sh (PreToolUse)
     │      ├── L1/L2/L3 프롬프트 주입
     │      └── 캐시 확인
     │
     └── pd-task-processor.sh (PostToolUse)
            ├── L1 파싱 및 캐싱
            └── Priority 가이던스 생성

Subagent Lifecycle (V2.1.29)
     │
     ├── SubagentStart hook
     │      └── subagent_lifecycle.log 기록
     │
     └── SubagentStop hook
            └── subagent_lifecycle.log 완료 기록
```

### V2.1.29 Subagent Lifecycle Hooks

```yaml
# settings.json에 등록된 V2.1.29 hooks
SubagentStart:
  matcher: ".*"
  action: Log to .agent/logs/subagent_lifecycle.log
  fields: [timestamp, CLAUDE_SUBAGENT_TYPE]

SubagentStop:
  matcher: ".*"
  action: Log completion to .agent/logs/subagent_lifecycle.log
  fields: [timestamp, CLAUDE_SUBAGENT_TYPE]

# 로그 형식
[2026-02-01T20:55:00] SubagentStart: Explore
[2026-02-01T20:55:30] SubagentStop: Explore
```

### Validation Gates (Shift-Left 5단계)

| Gate | Hook | 검증 시점 | 실패 시 |
|------|------|----------|---------|
| G1 | clarify-validate.sh | /clarify 전 | 불명확 항목 재질문 |
| G2 | research-validate.sh | /research 전 | 리서치 범위 확인 |
| G3 | planning-preflight.sh | /planning 전 | 계획 가능성 검증 |
| G4 | orchestrate-validate.sh | /orchestrate 전 | 의존성 확인 |
| G5 | worker-preflight.sh | /worker 전 | 리소스 가용성 |

### 코드레벨 발견 이슈

| Severity | 위치 | 이슈 | 권장 조치 |
|----------|------|------|----------|
| MEDIUM | session-start.sh:85 | stat 플랫폼 호환성 | Python 기반 통합 |
| MEDIUM | validation-metrics.sh:99 | bc 의존성 | fallback 추가 |
| LOW | 전체 | 에러 처리 (`2>/dev/null`) | 명시적 logging |

---

## Section 10: Agent Integration (Code-Level Analysis V1.4.0)

### Agent Inventory (3개)

| Agent | Model | Task API | 용도 |
|-------|-------|----------|------|
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

### Agent → Task Mapping Rules (신규 제안)

```yaml
# Agent frontmatter → Task parameter 자동 변환

Rule 1: Tool Restriction Inheritance
  Agent.tools ∩ !Agent.disallowedTools → Task.allowed_tools

Rule 2: Background Execution Alignment
  Agent.runInBackground → Task.run_in_background (기본값)

Rule 3: Permission Mode Mapping
  Agent.permissionMode = "acceptEdits"
    → Task allowed_tools에 [Write, Edit] 포함 가능
```

---

## Section 11: Skill Integration (Code-Level Analysis V1.4.0)

### Skill Task API Usage Matrix (17개 스킬)

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

모든 core skill에 구현됨:

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

### Task Metadata Schema Extension (신규 제안)

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

> **Note:** This section documents hooks at the time of analysis (V1.4.0). Current hook count is 50 files.

### Hook 분류 (Historical - 27개 at V1.4.0)

| 분류 | 파일 수 | Task API 연계 |
|------|--------|---------------|
| Session Management | 3 | ✅ 핵심 (Task List 로드, Recovery) |
| Task Pipeline | 3 | ✅ 핵심 (L1/L2/L3 자동 주입) |
| Shift-Left Gates | 6 | ✅ Validation |
| Security & Governance | 2 | ❌ |
| Pipeline Setup/Finalize | 9 | ⚠️ Partial |
| Utility | 4 | ❌ |

### L1/L2/L3 자동 주입 흐름

```
Task Tool Call
     │
     ├── pd-task-interceptor.sh (PreToolUse)
     │      ├── L1/L2/L3 프롬프트 템플릿 주입
     │      ├── Cache hash 확인 (hit 시 skip)
     │      ├── Worker prompt 파일 생성 (pending/*.yaml)
     │      └── run_in_background=true, model="opus" 자동 추가
     │
     └── pd-task-processor.sh (PostToolUse)
            ├── L1 YAML 블록 파싱
            ├── Cache 저장 (input_hash → metadata)
            ├── Prompt 파일 이동 (pending → completed)
            └── Priority 기반 가이던스 생성
```

### 플랫폼 호환성 이슈 (권장 조치)

| 이슈 | 위치 | Linux | macOS | 권장 |
|------|------|-------|-------|------|
| `grep -oP` | pd-task-processor.sh | ✅ | ❌ | pcregrep 또는 Python |
| `stat -c` | session-start.sh | ✅ | ❌ (`-f`) | Python os.stat() |
| `yq` | planning-finalize.sh | ✅ | ✅ | jq 기반 통일 |
| `bc` | validation-metrics.sh | ✅ | ✅ | integer 산술로 변경 |

### V7.1 경로 통일 (필수)

```yaml
# Legacy (DEPRECATED)
.agent/outputs/{agentType}/

# V7.1 Standard (REQUIRED)
.agent/prompts/{slug}/outputs/{taskId}.md

# L1 l3Section 필드도 변경 필요:
l3Section: ".agent/prompts/{slug}/outputs/{taskId}.md"  # V7.1
```

---

## Section 13: Cross-Integration Summary (L3 Synthesis)

### Component 간 Task API 흐름

```
┌──────────────────────────────────────────────────────────────┐
│  CLAUDE.md (Task System Definition)                          │
│  → TaskCreate, TaskUpdate, TaskList, TaskGet 정의            │
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

### 핵심 개선 우선순위

| 우선순위 | 항목 | 담당 Component |
|---------|------|----------------|
| **HIGH** | Task metadata에 L1/L2/L3 출력 경로 링크 | Skills + Hooks |
| **HIGH** | Tool Restriction Inheritance 규칙 문서화 | Agents |
| **HIGH** | V7.1 경로 통일 | Hooks |
| **MEDIUM** | blockedBy 의존성 예시 추가 | Agents |
| **MEDIUM** | 플랫폼 호환성 수정 (grep -oP, stat -c) | Hooks |
| **LOW** | Context budget tracking system | Skills |

---

## Section 14: Integrated Roadmap (FINAL_REPORT + Guideline V1.5.0)

> **Source:** FINAL_REPORT.md Recommendations + Guideline V1.4.0 Code-Level Analysis

### Short-term (1-2 Sprint)

| 항목 | 출처 | Component | 상태 |
|------|------|-----------|------|
| `once: true` hook 패턴 검토 | FINAL_REPORT | Hooks | ⏳ |
| Hooks timeout 설정 표준화 | FINAL_REPORT | Hooks | ⏳ |
| V7.1 경로 통일 (`.agent/prompts/{slug}/`) | Guideline | Hooks | ⏳ |
| Tool Restriction Inheritance 문서화 | Guideline | Agents | ⏳ |

### Medium-term (2-3 Sprint)

| 항목 | 출처 | Component | 상태 |
|------|------|-----------|------|
| Task metadata L1/L2/L3 경로 링크 | Guideline | Skills + Hooks | ⏳ |
| 플랫폼 호환성 (grep -oP, stat -c) | Guideline | Hooks | ⏳ |
| blockedBy 의존성 예시 추가 | Guideline | Agents | ⏳ |
| Skill-specific hooks → frontmatter 이전 | FINAL_REPORT | Skills | ⏳ |

### Long-term (3+ Sprint)

| 항목 | 출처 | Component | 상태 |
|------|------|-----------|------|
| Agent registry 자동화 | FINAL_REPORT | Agents | ⏳ |
| Lifecycle logging 대시보드 | FINAL_REPORT | Hooks | ⏳ |
| Context budget tracking system | Guideline | Skills | ⏳ |

---

## Section 15: INFRA 통합 검증 결과 (V1.5.0)

### 검증 매트릭스

| 검증 항목 | FINAL_REPORT | Guideline V1.5.0 | 정합성 |
|----------|--------------|------------------|--------|
| Skills 수 | 17 | 17 | ✅ 일치 |
| Hooks 수 | 23 | 26 | ⚠️ +3 추가됨 |
| Agents 수 | 4 | 3 | ⚠️ 1개 docs/로 이동 |
| EFL P1-P6 | P1,P2,P3,P5,P6 | P1-P6 | ✅ 완전 |
| V2.1.29 hooks | SubagentStart/Stop | ✅ 추가됨 | ✅ 완전 |
| Semantic Integrity | 100% | 100% | ✅ 유지 |

### 최종 결론

```yaml
integration_status: OPTIMIZED
version_alignment:
  CLAUDE.md: V7.2
  settings.json: V2.1.29
  Task_API_Guideline: V1.5.0
  FINAL_REPORT: V2.1.29 Compliant

components:
  agents: 3 (Task API 1/3 사용)
  skills: 17 (EFL P1-P6 완전)
  hooks: 26 (L1/L2/L3 자동 주입)

key_features:
  - "[PERMANENT] Context Check 패턴 적용"
  - "L2→L3 Progressive-Deep-Dive Meta-Level 패턴"
  - "Parallel Agents Delegation Architecture"
  - "V2.1.29 SubagentStart/SubagentStop hooks"
  - "Tool Restriction Patterns (A1/A2/A3)"
```

---

## Section 16: Enforcement Architecture (V2.0.0)

> **핵심 원칙:** 프롬프트 수준 지시가 아닌, Hook을 통한 **행동력 강제**

### 아키텍처 개요

```
.claude/hooks/
├── enforcement/                    # Gate 스크립트 (HARD BLOCK)
│   ├── _shared.sh                  # 공통 라이브러리
│   ├── context-recovery-gate.sh    # Compact 후 컨텍스트 복구 강제
│   ├── l2l3-access-gate.sh         # Edit/Write 전 L2/L3 읽기 강제
│   ├── task-first-gate.sh          # 소스 코드 수정 전 TaskCreate 강제
│   ├── blocked-task-gate.sh        # blockedBy 있는 Task 시작 방지
│   ├── output-preservation-gate.sh # Task 완료 전 결과 저장 확인
│   └── security-gate.sh            # 위험 명령 차단
│
└── tracking/                       # Tracker 스크립트 (로깅)
    ├── read-tracker.sh             # Read 호출 로깅
    └── task-tracker.sh             # TaskCreate/Update 로깅
```

### Gate 스크립트 (PreToolUse - HARD BLOCK)

| Gate | Trigger | 차단 조건 | JSON 응답 |
|------|---------|----------|----------|
| `context-recovery-gate.sh` | Edit\|Write\|Task | `_active_workload.yaml` 존재 but 미읽음 | `permissionDecision: "deny"` |
| `l2l3-access-gate.sh` | Edit\|Write | Active workload 있지만 L2/L3 미읽음 | `permissionDecision: "deny"` |
| `task-first-gate.sh` | Edit\|Write | 소스 코드 수정 but 최근 TaskCreate 없음 | `permissionDecision: "deny"` |
| `blocked-task-gate.sh` | TaskUpdate | status→in_progress but blockedBy 존재 | `permissionDecision: "deny"` |
| `output-preservation-gate.sh` | TaskUpdate | status→completed but outputs/ 없음 | `permissionDecision: "ask"` |
| `security-gate.sh` | Bash | 위험 명령 패턴 감지 | `permissionDecision: "deny"` |

### Tracker 스크립트 (PostToolUse - 로깅)

| Tracker | Trigger | 기능 | 로그 위치 |
|---------|---------|------|----------|
| `read-tracker.sh` | Read | 파일 읽기 기록 | `.agent/tmp/recent_reads.log` |
| `task-tracker.sh` | TaskCreate\|TaskUpdate | Task 작업 기록 | `.agent/tmp/recent_tasks.log` |

### 공통 라이브러리 (_shared.sh)

```bash
# 핵심 함수
output_allow()           # 허용 (permissionDecision: "allow")
output_deny "reason"     # HARD BLOCK (permissionDecision: "deny")
output_ask "reason"      # 사용자 확인 요청 (permissionDecision: "ask")
output_passthrough()     # PostToolUse 패스스루 (빈 JSON)

# 상태 확인 함수
has_active_workload()    # _active_workload.yaml 존재 확인
has_read_l2l3()          # L2/L3 파일 읽기 확인
has_recent_task_create() # 최근 5분 내 TaskCreate 확인
is_excluded_file()       # 제외 파일 확인 (.claude/, .agent/, .md, .json 등)

# 로깅 함수
log_enforcement()        # enforcement.log에 결정 기록
log_tracking()           # tracking 로그 기록
```

### Hook Exit Code 규칙

| Exit Code | JSON 필요 | 결과 |
|-----------|----------|------|
| `exit 0` | ✅ 필수 | JSON의 `permissionDecision`에 따라 처리 |
| `exit 2` | ❌ 무시 | 즉시 긴급 차단 (stderr 표시) |
| `exit 1` | ❌ 무시 | Hook 오류, 작업은 허용됨 |

### settings.json Hook 등록

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

### 프롬프트 vs Hook 강제 비교

| 규칙 | V1.x (프롬프트) | V2.0 (Hook 강제) |
|------|----------------|-----------------|
| Context Recovery | CLAUDE.md 지시 | `context-recovery-gate.sh` BLOCK |
| L2→L3 읽기 | Task API Guideline 지시 | `l2l3-access-gate.sh` BLOCK |
| TaskCreate 필수 | [PERMANENT] 패턴 지시 | `task-first-gate.sh` BLOCK |
| blockedBy 준수 | 의존성 규칙 지시 | `blocked-task-gate.sh` BLOCK |
| 보안 명령 차단 | settings.json deny | `security-gate.sh` BLOCK |

---

## Section 17: Orchestrator Decision Framework (V3.0.0)

> **핵심 원칙:** Main Agent는 Orchestrator-Role로서 명확한 의사결정 시점과 규칙을 따름

### 17.1 Decision Points Catalog

Main Agent가 Orchestrator로서 내려야 하는 의사결정 목록:

| ID | Decision Point | 시점 | 질문 |
|----|---------------|------|------|
| **DP-1** | Task 분해 범위 | `/orchestrate` 시작 시 | 어디까지 분해할 것인가? |
| **DP-2** | 의존성 설정 | TaskCreate 후 | 어떤 Task가 먼저 완료되어야 하는가? |
| **DP-3** | Worker 완료 처리 | `/collect` 후 | 결과가 충분한가? 추가 작업 필요한가? |
| **DP-4** | Blocked 해소 처리 | blockedBy Task 완료 시 | 다음 Task 시작 조건 충족? |
| **DP-5** | 재조정 필요 | `/synthesis` ITERATE 시 | 어떤 Task를 추가/수정해야 하는가? |
| **DP-6** | [PERMANENT] 완료 | 전체 작업 완료 시 | 모든 Phase가 완료되었는가? |

### 17.2 Decision Rules Matrix

| DP | WHEN (시점) | WHAT (선택지) | HOW (확인사항) | ACTION (행동) |
|----|------------|---------------|---------------|---------------|
| **DP-1** | `/orchestrate` 호출 시 | Granularity: Fine/Medium/Coarse | 요구사항 복잡도, 병렬화 가능성 | `TaskCreate` × N |
| **DP-2** | Task 생성 직후 | 의존성 유무 | 데이터 흐름, 리소스 충돌 | `TaskUpdate(addBlockedBy)` |
| **DP-3** | Worker 결과 수신 시 | Accept/Reject/Partial | L1/L2/L3 출력 품질, 요구사항 충족 | `TaskUpdate(completed)` 또는 재할당 |
| **DP-4** | blockedBy 완료 시 | Start/Delay/Skip | 선행 결과 품질, 리소스 가용성 | 다음 Task 시작 허용 |
| **DP-5** | ITERATE 결정 시 | Add/Modify/Remove Tasks | Gap 분석 결과, 우선순위 | `/rsil-plan` → 새 Task 생성 |
| **DP-6** | 최종 단계 | Complete/Rollback | 모든 Task completed, 검증 통과 | `[PERMANENT]` completed 처리 |

### 17.3 Decision → Action Mapping

```javascript
// DP-1: Task 분해 결정
function decideTaskDecomposition(requirement) {
  const complexity = analyzeComplexity(requirement)

  if (complexity === 'simple') {
    return { granularity: 'coarse', taskCount: 1-3 }
  } else if (complexity === 'moderate') {
    return { granularity: 'medium', taskCount: 4-7 }
  } else {
    return { granularity: 'fine', taskCount: 8+ }
  }
}

// DP-2: 의존성 설정 결정
function decideDependency(taskA, taskB) {
  // Rule 1: 데이터 흐름 의존성
  if (taskB.requiresOutputOf(taskA)) {
    return { addBlockedBy: [taskA.id] }
  }

  // Rule 2: 리소스 충돌 (같은 파일 수정)
  if (taskA.files.intersect(taskB.files).length > 0) {
    return { addBlockedBy: [taskA.id] }  // 순서 정해서 직렬화
  }

  // Rule 3: 병렬 가능
  return { addBlockedBy: [] }
}

// DP-3: Worker 완료 처리 결정
function decideWorkerCompletion(workerResult) {
  const quality = validateL2L3Output(workerResult)

  if (quality.score >= 0.9) {
    return { action: 'accept', status: 'completed' }
  } else if (quality.score >= 0.7) {
    return { action: 'partial', followUpTasks: quality.gaps }
  } else {
    return { action: 'reject', reassign: true }
  }
}
```

### 17.4 Orchestrator Decision Flowchart

```
┌─────────────────────────────────────────────────────────────────────┐
│  Orchestrator Decision Flow                                          │
└─────────────────────────────────────────────────────────────────────┘

Start: /orchestrate 호출
        │
        ▼
   ┌────────────┐
   │ DP-1       │  Q: 어떻게 분해?
   │ Decompose  │──────────────────┐
   └────────────┘                  │
        │                          │
        ▼                          ▼
   TaskCreate × N           Complexity 분석
        │                   - simple → 1-3 tasks
        │                   - moderate → 4-7 tasks
        ▼                   - complex → 8+ tasks
   ┌────────────┐
   │ DP-2       │  Q: 의존성?
   │ Dependency │──────────────────┐
   └────────────┘                  │
        │                          │
        ▼                          ▼
   TaskUpdate                 의존성 판단
   (addBlockedBy)             - 데이터 흐름 → blockedBy
        │                     - 리소스 충돌 → 직렬화
        │                     - 독립 → 병렬 가능
        ▼
   /assign → /worker (병렬)
        │
        ▼
   ┌────────────┐
   │ DP-3       │  Q: 결과 충분?
   │ Completion │──────────────────┐
   └────────────┘                  │
        │                          │
        ├── Accept ───────► TaskUpdate(completed)
        │                          │
        ├── Partial ──────► Follow-up Tasks 생성
        │                          │
        └── Reject ───────► 재할당 또는 /rsil-plan
                                   │
                                   ▼
   ┌────────────┐
   │ DP-5       │  Q: 재조정?
   │ Adjust     │──────────────────┐
   └────────────┘                  │
        │                          │
        ├── ITERATE ──────► /rsil-plan → 새 Tasks
        │                          │
        └── COMPLETE ─────► DP-6 진입
                                   │
                                   ▼
   ┌────────────┐
   │ DP-6       │  Q: 전체 완료?
   │ Finalize   │──────────────────┐
   └────────────┘                  │
        │                          │
        ▼                          ▼
   [PERMANENT]              검증 조건 확인
   completed 처리           - 모든 Task completed
                            - /synthesis COMPLETE
                            - Commit/PR 생성
```

---

## Section 18: Dependency Chain Design Principles (V3.0.0)

> **핵심 원칙:** 의존성은 DAG(Directed Acyclic Graph)로 설계, 순환 금지, 최소화 원칙

### 18.1 Dependency Type Classification

| Type | 설명 | 예시 | 처리 방식 |
|------|------|------|----------|
| **Data Flow** | Task B가 Task A의 출력 필요 | 분석 → 구현 | `blockedBy: [A]` 필수 |
| **Resource** | 같은 파일/리소스 수정 | 두 Task가 같은 파일 수정 | 순서 정해서 직렬화 |
| **Logical** | 비즈니스 로직 상 순서 | 스키마 → 마이그레이션 | `blockedBy` 명시 |
| **None** | 완전 독립 | 서로 다른 모듈 | 병렬 실행 가능 |

### 18.2 DAG Design Rules

#### Rule 1: Acyclic Guarantee (순환 금지)

```
❌ FORBIDDEN (순환 의존성):
   Task A → Task B → Task C → Task A

✅ CORRECT (DAG):
   Task A → Task B → Task D
         ↘ Task C ↗
```

#### Rule 2: Minimal Dependency Principle

```javascript
// ❌ WRONG: 불필요한 직렬화
TaskUpdate({ taskId: task2.id, addBlockedBy: [task1.id] })
TaskUpdate({ taskId: task3.id, addBlockedBy: [task2.id] })  // task3는 task1만 필요
TaskUpdate({ taskId: task4.id, addBlockedBy: [task3.id] })

// ✅ CORRECT: 실제 의존성만
TaskUpdate({ taskId: task2.id, addBlockedBy: [task1.id] })
TaskUpdate({ taskId: task3.id, addBlockedBy: [task1.id] })  // task1 직접 의존
TaskUpdate({ taskId: task4.id, addBlockedBy: [task2.id, task3.id] })  // 둘 다 필요
```

#### Rule 3: Diamond Pattern 허용

```
     Task A (Setup)
       /   \
      ↓     ↓
   Task B  Task C  (병렬)
      \     /
       ↓   ↓
     Task D (Merge)
```

```javascript
// Diamond Pattern 구현
TaskUpdate({ taskId: taskB.id, addBlockedBy: [taskA.id] })
TaskUpdate({ taskId: taskC.id, addBlockedBy: [taskA.id] })
TaskUpdate({ taskId: taskD.id, addBlockedBy: [taskB.id, taskC.id] })
```

### 18.3 Dependency Anti-patterns

| Anti-pattern | 문제점 | 해결책 |
|--------------|--------|--------|
| **Circular Dependency** | 무한 대기 | DAG 재설계 |
| **Over-serialization** | 병렬화 기회 손실 | 실제 의존성만 설정 |
| **Missing Dependency** | 순서 보장 실패 | 데이터 흐름 분석 후 추가 |
| **[PERMANENT] blocks 사용** | 차단 불가 완료 | **blocks 배열 사용 금지** |

### 18.4 [PERMANENT] Task Design Rules (CRITICAL)

> **Issue:** `[PERMANENT]` Task가 `blocks: [...]`를 가지면, 해당 Task들이 영원히 시작 불가

```javascript
// ❌ FORBIDDEN: [PERMANENT]에 blocks 배열 사용
TaskCreate({
  subject: "[PERMANENT] Context Check",
  blocks: ["2", "3", "4"]  // ❌ 이 Task들이 영원히 blocked 상태
})

// ✅ CORRECT: [PERMANENT]는 blocks/blockedBy 모두 비움
TaskCreate({
  subject: "[PERMANENT] Context Check",
  blocks: [],      // ✅ 비움
  blockedBy: []    // ✅ 비움
})

// 다른 Task들의 의존성은 각자 설정
TaskUpdate({ taskId: task3.id, addBlockedBy: [task2.id] })  // 필요한 의존성만
```

#### [PERMANENT] 완료 조건

```yaml
[PERMANENT] completed 전환 조건 (ALL 충족):
  - [ ] 모든 Phase Task가 completed
  - [ ] /synthesis 결과가 COMPLETE
  - [ ] Commit/PR 생성 완료 (해당 시)
  - [ ] 검증 Task 완료 (Phase 6 등)

완료 순서:
  1. 실제 작업 Task들 먼저 완료
  2. [PERMANENT] Task 가장 마지막에 completed
```

### 18.5 Dependency Chain Examples

#### Example 1: Linear Research → Implementation

```
[PERMANENT] ─────────────────────────────────────┐
                                                  │
Phase 1: Research (blockedBy: [])                │
    │                                             │ in_progress 유지
    ▼                                             │
Phase 2: Implementation (blockedBy: [Phase1])    │
    │                                             │
    ▼                                             │
Phase 3: Verification (blockedBy: [Phase2]) ─────┘
                                                  │
[PERMANENT] completed ◄───────────────────────────┘
```

#### Example 2: Parallel Analysis → Synthesis

```
[PERMANENT] ─────────────────────────────────────────────┐
                                                          │
Phase 2-A: Hook Analysis      ┐                          │
Phase 2-B: Skill Analysis     ├─ blockedBy: []  (병렬)   │ in_progress
Phase 2-C: Agent Analysis     ┘                          │
         \         |         /                           │
          ↘        ↓        ↙                            │
Phase 3: Synthesis (blockedBy: [2-A, 2-B, 2-C])         │
    │                                                     │
    ▼                                                     │
Phase 4: Implementation (blockedBy: [Phase3]) ───────────┘
                                                          │
[PERMANENT] completed ◄───────────────────────────────────┘
```

---

## Section 19: Runtime Orchestration Protocol (V3.0.0)

> **핵심 원칙:** Worker 완료 → Main Agent 행동 시퀀스 정의, 동적 재조정 지원

### 19.1 Worker Completion Handler

```
Worker 완료 시 Main Agent 행동 시퀀스:

1. TaskList() 호출 → 현재 상태 확인
2. completed Task의 L1/L2/L3 출력 읽기
3. 품질 검증 (DP-3 적용)
4. 다음 행동 결정:
   - Accept → blockedBy 해소된 Task들 확인
   - Partial → Follow-up Task 생성
   - Reject → 재할당 또는 /rsil-plan
```

```javascript
// Worker Completion Handler 구현
async function handleWorkerCompletion(completedTaskId) {
  // Step 1: 현재 상태 확인
  const tasks = await TaskList()
  const completedTask = await TaskGet(completedTaskId)

  // Step 2: L1/L2/L3 출력 읽기
  const l1 = await Read(completedTask.metadata.l1_output_path)
  const l2 = await Read(completedTask.metadata.l2_output_path)
  const l3 = await Read(completedTask.metadata.l3_output_path)

  // Step 3: 품질 검증 (DP-3)
  const quality = validateQuality(l2, l3)

  // Step 4: 다음 행동
  if (quality.acceptable) {
    // blockedBy 해소된 Task 확인
    const unblockedTasks = tasks.filter(t =>
      t.blockedBy?.includes(completedTaskId) &&
      t.blockedBy.every(id => getTaskStatus(id) === 'completed')
    )
    return { action: 'proceed', unblockedTasks }
  } else {
    return { action: 'remediate', gaps: quality.gaps }
  }
}
```

### 19.2 Blocked Resolution Handler

```
blockedBy Task 완료 시 처리:

1. 해당 Task의 blockedBy 배열 확인
2. 모든 blockedBy Task가 completed인지 검증
3. 조건 충족 시 → Task 시작 가능 상태로 전환
4. Worker에 알림 (또는 자동 시작)
```

```javascript
// Blocked Resolution Handler 구현
async function handleBlockedResolution(completedTaskId) {
  const tasks = await TaskList()

  // completedTaskId를 blockedBy로 가진 Task들
  const dependentTasks = tasks.filter(t =>
    t.blockedBy?.includes(completedTaskId)
  )

  for (const task of dependentTasks) {
    // 모든 blocker가 완료되었는지 확인
    const allBlockersCompleted = task.blockedBy.every(blockerId => {
      const blocker = tasks.find(t => t.id === blockerId)
      return blocker?.status === 'completed'
    })

    if (allBlockersCompleted) {
      console.log(`Task ${task.id} is now unblocked and ready to start`)
      // Worker에 알림 또는 자동 할당
    }
  }
}
```

### 19.3 Dynamic Adjustment Protocol

```
/synthesis ITERATE 시 재조정 프로토콜:

1. Gap 분석 결과 확인 (from /rsil-plan)
2. 새 Task 생성 또는 기존 Task 수정
3. 의존성 체인 재설정
4. [PERMANENT] 상태는 in_progress 유지
```

```javascript
// Dynamic Adjustment Protocol 구현
async function handleIterate(gapAnalysis) {
  // Step 1: Gap 유형 분류
  const { missingTasks, modifyTasks, removeTasks } = gapAnalysis

  // Step 2: 새 Task 생성
  for (const missing of missingTasks) {
    const newTask = await TaskCreate({
      subject: missing.subject,
      description: missing.description,
      metadata: { phase: missing.phase, iteration: 2 }
    })

    // Step 3: 의존성 설정
    if (missing.dependsOn) {
      await TaskUpdate({
        taskId: newTask.id,
        addBlockedBy: missing.dependsOn
      })
    }
  }

  // Step 4: [PERMANENT]는 유지
  // [PERMANENT] Task의 status는 변경하지 않음 (in_progress 유지)
}
```

### 19.4 Error/Blocker Escalation Protocol

```
에러/블로커 발생 시 에스컬레이션:

Level 1: Worker 내 자체 해결 시도 (max 3회)
Level 2: Sub-Orchestrator에 보고 (Sub-Orch 모드 시)
Level 3: Main Orchestrator에 보고
Level 4: 사용자에게 /block 알림
```

```javascript
// Escalation Protocol 구현
async function handleBlocker(taskId, blocker) {
  const task = await TaskGet(taskId)
  let escalationLevel = 1

  // Level 1: Worker 자체 해결
  if (escalationLevel === 1) {
    const retryResult = await retryWithFix(blocker, { maxRetries: 3 })
    if (retryResult.success) return
    escalationLevel = 2
  }

  // Level 2: Sub-Orchestrator (해당 시)
  if (escalationLevel === 2 && task.metadata.subOrchestratorMode) {
    await reportToSubOrchestrator(task.metadata.parentTaskId, blocker)
    escalationLevel = 3
  }

  // Level 3: Main Orchestrator
  if (escalationLevel >= 3) {
    await reportToMainOrchestrator(blocker)
    escalationLevel = 4
  }

  // Level 4: 사용자 알림
  if (escalationLevel === 4) {
    await TaskUpdate({
      taskId,
      status: 'blocked',
      metadata: { blocker: blocker.description }
    })
    // /worker block 명령으로 상태 변경됨
  }
}
```

### 19.5 Complete Orchestration Sequence

```
┌─────────────────────────────────────────────────────────────────────┐
│  Complete Orchestration Sequence (Main Agent)                        │
└─────────────────────────────────────────────────────────────────────┘

1. /orchestrate 실행
   │
   ├── [PERMANENT] Task 생성 (blocks: [], blockedBy: [])
   ├── Phase Tasks 생성
   └── 의존성 체인 설정 (DP-2)

2. /assign 실행
   │
   └── TaskUpdate(owner) → Terminal 할당

3. Workers 병렬 실행 (/worker start)
   │
   ├── Task 실행
   ├── L1/L2/L3 출력 생성
   └── TaskUpdate(completed)

4. Worker 완료 시 (per task)
   │
   ├── handleWorkerCompletion() 호출
   ├── L1/L2/L3 읽기 + 품질 검증
   └── Blocked Resolution 확인

5. /collect 실행
   │
   ├── TaskList() → 완료 확인
   └── Collection Report 생성

6. /synthesis 실행
   │
   ├── Traceability Matrix 생성
   ├── Quality Validation
   └── Decision: COMPLETE | ITERATE

7-A. COMPLETE 경로
   │
   ├── /commit-push-pr 실행
   └── [PERMANENT] completed 처리

7-B. ITERATE 경로
   │
   ├── /rsil-plan → Gap 분석
   ├── handleIterate() → 새 Task 생성
   └── Step 3로 복귀

8. 최종 완료
   │
   └── [PERMANENT] TaskUpdate(status: 'completed')
```

---

## Section 20: Sub-Orchestrator Validation Loop Pattern (V3.1.0)

> **핵심 원칙:** Main Agent가 Sub-Orchestrator 역할도 수행할 때, 검증→Orchestrating→검증 루프 패턴 적용

### 20.1 Pattern Overview

Sub-Orchestrator이면서 Main Agent인 경우의 워크플로우:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Sub-Orchestrator Validation Loop (Main Agent ∩ Sub-Orchestrator)    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│   │ Execute  │────▶│ Validate │────▶│ Decision │────▶│ Unblock  │   │
│   │  Task    │     │  Output  │     │   Gate   │     │  Next    │   │
│   └──────────┘     └──────────┘     └────┬─────┘     └────┬─────┘   │
│                                          │                 │         │
│            ┌────────── PASS ─────────────┘                 │         │
│            │                                               │         │
│            ▼                                               ▼         │
│       ┌──────────┐                                    ┌──────────┐   │
│       │ Mark     │                                    │ Pick     │   │
│       │ COMPLETE │───────────────────────────────────▶│ Next     │   │
│       └──────────┘                                    └────┬─────┘   │
│                                                            │         │
│            ┌────────── FAIL ───────────────────────────────┘         │
│            │                                                         │
│            ▼                                                         │
│       ┌──────────┐                                                   │
│       │ Fix &    │──────────────────▶ (Loop back to Execute)         │
│       │ Retry    │                                                   │
│       └──────────┘                                                   │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 20.2 ASCII Visualization for Self-Reminding

> **핵심:** 복잡한 워크플로우에서 현재 위치와 전체 맥락을 잃지 않기 위한 Self-Reminding 기법

```javascript
// 작업 시작 시 ASCII ORCHESTRATION PLAN 출력
function printOrchestrationPlan(phases) {
  console.log(`
┌────────────────────────────────────────────────────────────────┐
│  ORCHESTRATION PLAN (Self-Reminding)                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1 (Schema) ──▶ Phase 2 (Client) ──▶ Phase 3 (Separator) │
│         │                   │                    │              │
│         ▼                   ▼                    ▼              │
│  [${phases[0]?.status || 'pending'}]      [${phases[1]?.status || 'pending'}]       [${phases[2]?.status || 'pending'}]           │
│                                                                 │
│  ──▶ Phase 4 (Cleanup) ──▶ Phase 5 (Test/Verify)               │
│              │                    │                             │
│              ▼                    ▼                             │
│       [${phases[3]?.status || 'pending'}]           [${phases[4]?.status || 'pending'}]                      │
│                                                                 │
│  Current: Phase ${getCurrentPhase()} | Progress: ${getProgress()}%           │
└────────────────────────────────────────────────────────────────┘
  `)
}
```

### 20.3 Validation Loop Rules

| Step | Action | Validation | 실패 시 |
|------|--------|------------|--------|
| 1 | Execute Task | - | - |
| 2 | Validate Output | L1/L2/L3 품질 검증 | Fix & Retry |
| 3 | Decision Gate | Pass/Fail 결정 | 재실행 또는 수동 개입 |
| 4 | Unblock Next | blockedBy 해소 확인 | 대기 |
| 5 | Mark COMPLETE | status 업데이트 | - |
| 6 | Pick Next | 다음 Task 선택 | 완료 또는 Loop |

### 20.4 Implementation Example (COW CLI Refactoring)

```javascript
// 실제 구현 예시 (2026-02-04 COW CLI Mathpix API Refactoring)
async function subOrchestratorLoop() {
  const phases = [
    { id: "schema", tasks: ["PdfLineData", "PdfPageData", "UnifiedResponse"] },
    { id: "client", tasks: ["process_pdf→UnifiedResponse", "process_image_unified"] },
    { id: "separator", tasks: ["separate_unified", "hierarchy helpers"] },
    { id: "cleanup", tasks: ["remove deprecated", "fix imports"] },
    { id: "test", tasks: ["schema test", "integration test"] }
  ]

  for (const phase of phases) {
    // Step 1: Execute
    for (const task of phase.tasks) {
      await executeTask(task)

      // Step 2: Validate
      const isValid = await validateOutput(task)

      // Step 3: Decision Gate
      if (!isValid) {
        await fixAndRetry(task)
      }

      // Step 4-5: Unblock & Mark Complete
      await TaskUpdate({ taskId: task.id, status: "completed" })
    }

    // Step 6: Pick Next Phase
    printOrchestrationPlan(phases)  // Self-Reminding
  }
}
```

### 20.5 Key Principles

1. **검증 우선 (Verify-First):** 다음 단계로 진행하기 전 항상 출력 검증
2. **의존성 체인 인식 (Dependency-Aware):** 모든 작업에서 전체 맥락의 의존성 체인 고려
3. **Self-Reminding:** ASCII Visualization으로 현재 위치와 진행 상황 지속 확인
4. **Loop-back:** 실패 시 재실행, 순환 없이 DAG 유지

### 20.6 Reference Implementation

COW CLI Mathpix API 리팩토링에서 이 패턴의 실제 적용 사례:
- 문서: `.claude/references/cow-cli-architecture.md`
- 5개 Phase, 17개 Task 완료
- UnifiedResponse 패턴으로 PDF/Image API 정규화

---

> **Version:** 3.1.0 (Sub-Orchestrator Validation Loop Pattern)
> **Updated:** 2026-02-04
> **Changes:**
> - V3.1.0: Added Section 20 (Sub-Orchestrator Validation Loop Pattern)
>   - 20.1 Pattern Overview with ASCII diagram
>   - 20.2 ASCII Visualization for Self-Reminding
>   - 20.3 Validation Loop Rules
>   - 20.4 Implementation Example (COW CLI Refactoring)
>   - 20.5 Key Principles
>   - 20.6 Reference Implementation (cow-cli-architecture.md)
> - V3.0.0: Added Section 17 (Orchestrator Decision Framework)
>   - 17.1 Decision Points Catalog (DP-1 ~ DP-6)
>   - 17.2 Decision Rules Matrix (WHEN/WHAT/HOW/ACTION)
>   - 17.3 Decision → Action Mapping (JavaScript implementations)
>   - 17.4 Orchestrator Decision Flowchart
> - V3.0.0: Added Section 18 (Dependency Chain Design Principles)
>   - 18.1 Dependency Type Classification (Data Flow/Resource/Logical/None)
>   - 18.2 DAG Design Rules (Acyclic, Minimal, Diamond Pattern)
>   - 18.3 Dependency Anti-patterns
>   - 18.4 [PERMANENT] Task Design Rules (CRITICAL - blocks 배열 사용 금지)
>   - 18.5 Dependency Chain Examples
> - V3.1.0: Updated for Claude Code V2.1.33 hook integration
>   - All 12 hook events documented (SessionStart through SessionEnd)
>   - New hook types: prompt-based (`type: prompt`), async (`async: true`)
>   - PermissionRequest, Notification, PostToolUseFailure event handlers
>   - `once` field for Setup hooks in skill frontmatter
>   - `memory` frontmatter field (user/project/local scope)
>   - Diagnostic tools: hook-health-check.sh, hook-timing-test.sh, settings-validator.sh
> - V3.0.0: Added Section 19 (Runtime Orchestration Protocol)
>   - 19.1 Worker Completion Handler
>   - 19.2 Blocked Resolution Handler
>   - 19.3 Dynamic Adjustment Protocol
>   - 19.4 Error/Blocker Escalation Protocol
>   - 19.5 Complete Orchestration Sequence
> - V2.2.0: Task ID Collision Resolution section update
> - V2.0.0: Added Section 16 (Enforcement Architecture)
> - V2.0.0: Hook-based behavioral enforcement (not prompt-level guidance)
> - V2.0.0: Gate scripts with `permissionDecision: deny` for HARD BLOCK
> - V2.0.0: Tracker scripts for read/task logging
> - V2.0.0: Common library (_shared.sh) with helper functions
> - V1.5.0: Added Section 14-15 (Integrated Roadmap, INFRA 통합 검증 결과)
> - V1.5.0: Added V2.1.29 SubagentStart/SubagentStop hooks documentation
> - V1.4.0: Added Section 10-12 (Agent/Skill/Hook Integration from Code-Level Analysis)
> - V1.3.0: Added Section 1.1: L2→L3 Progressive-Deep-Dive (Meta-Level Pattern)
> - Mandatory for improvement/enhancement/refinement tasks
> - Parallel Agent result synthesis workflow
> **Updated:** 2026-02-01
> **Changes:**
> - V2.0.0: Added Section 16 (Enforcement Architecture)
> - V2.0.0: Hook-based behavioral enforcement (not prompt-level guidance)
> - V2.0.0: Gate scripts with `permissionDecision: deny` for HARD BLOCK
> - V2.0.0: Tracker scripts for read/task logging
> - V2.0.0: Common library (_shared.sh) with helper functions
> - V1.5.0: Added Section 14-15 (Integrated Roadmap, INFRA 통합 검증 결과)
> - V1.5.0: Added V2.1.29 SubagentStart/SubagentStop hooks documentation
> - V1.4.0: Added Section 10-12 (Agent/Skill/Hook Integration from Code-Level Analysis)
> - V1.3.0: Added Section 1.1: L2→L3 Progressive-Deep-Dive (Meta-Level Pattern)
> - Mandatory for improvement/enhancement/refinement tasks
> - Parallel Agent result synthesis workflow

# Workload Management

> **Version:** 1.1.0
> **Date:** 2026-02-01
> **Status:** Active
> **Related:** [Task API Guideline](task-api-guideline.md)

---

## 1. Overview

**Workload Management**는 여러 작업(task)을 논리적인 단위로 그룹화하고, 각 워크로드별로 독립적인 컨텍스트와 진행 상황을 추적하는 시스템입니다.

### 핵심 개념

| 개념 | 설명 |
|------|------|
| **Workload ID** | 워크로드의 고유 식별자 (형식: `{topic}_{YYYYMMDD}_{HHMMSS}`) |
| **Slug** | URL-safe 식별자 (형식: `{topic}-{YYYYMMDD}`) |
| **Active Workload** | 현재 활성화된 워크로드 |
| **Workload Directory** | 워크로드별 파일이 저장되는 디렉토리 |

---

## 2. Slug Naming Convention

### 2.1 Workload ID 형식

```
{topic}_{YYYYMMDD}_{HHMMSS}

예시:
- user-authentication_20260125_143022
- payment-integration_20260125_150000
- api-refactoring_20260125_173500
```

**구성 요소:**
- `{topic}`: 워크로드 주제 (소문자, 하이픈 구분, 최대 40자)
- `{YYYYMMDD}`: 생성 날짜 (8자리)
- `{HHMMSS}`: 생성 시각 (6자리)

### 2.2 Slug 형식

```
{topic}-{YYYYMMDD}

예시:
- user-authentication-20260125
- payment-integration-20260125
- api-refactoring-20260125
```

**Slug 생성 규칙:**
- Workload ID에서 자동 파생
- 같은 날짜의 동일 토픽은 같은 slug 사용 가능
- 시간 부분(HHMMSS)은 slug에 포함되지 않음

### 2.3 Topic 정규화

```bash
# 입력: "User Authentication Feature"
# 1. 소문자 변환: "user authentication feature"
# 2. 특수문자 → 하이픈: "user-authentication-feature"
# 3. 중복 하이픈 제거: "user-authentication-feature"
# 4. 양끝 하이픈 제거: "user-authentication-feature"
# 5. 40자 제한: "user-authentication-feature" (35자)

# 결과 Workload ID: user-authentication-feature_20260125_143022
# 결과 Slug: user-authentication-feature-20260125
```

---

## 3. Directory Structure

### 3.1 Workload Directory Layout

```
.agent/prompts/
├── _active_workload.yaml          # 활성 워크로드 추적
├── _context.yaml                  # 글로벌 컨텍스트 (하위 호환)
├── _progress.yaml                 # 글로벌 진행상황 (하위 호환)
├── pending/                       # 글로벌 pending (하위 호환)
├── completed/                     # 글로벌 completed (하위 호환)
│
├── {workload-slug-1}/             # 워크로드 디렉토리
│   ├── _context.yaml              # 워크로드별 컨텍스트
│   ├── _progress.yaml             # 워크로드별 진행상황
│   ├── pending/                   # 대기 중인 프롬프트
│   │   ├── worker-terminal-b-task1.yaml
│   │   ├── worker-terminal-c-task2.yaml
│   │   └── worker-terminal-d-task3.yaml
│   └── completed/                 # 완료된 프롬프트
│       ├── worker-terminal-b-task1.yaml
│       └── worker-terminal-c-task2.yaml
│
└── {workload-slug-2}/             # 다른 워크로드
    ├── _context.yaml
    ├── _progress.yaml
    ├── pending/
    └── completed/
```

### 3.2 Workload Context File (_context.yaml)

```yaml
# Workload Context
# Workload ID: user-authentication-feature_20260125_143022
# Created: 2026-01-25T14:30:22Z

workload_id: "user-authentication-feature_20260125_143022"
created_at: "2026-01-25T14:30:22Z"
updated_at: "2026-01-25T14:30:22Z"

# Upstream references (V7.1 paths)
upstream:
  clarify_source: ".agent/prompts/user-auth-20260125/clarify.yaml"
  research_source: ".agent/prompts/user-auth-20260125/research.md"
  planning_source: ".agent/prompts/user-auth-20260125/plan.yaml"

# Global context that applies to all workers
global_context:
  project_root: "."
  coding_standards: "ESLint + Prettier"
  test_framework: "Jest"

# References to relevant files discovered during research
reference_files:
  - path: "src/auth/oauth.ts"
    reason: "Existing OAuth implementation"
  - path: "src/auth/session.ts"
    reason: "Session management patterns"

# Shared decisions or patterns across workers
shared_decisions:
  - decision: "Use JWT for token-based auth"
    rationale: "Already integrated in codebase"
    affects: ["worker-terminal-b", "worker-terminal-c"]
```

### 3.3 Workload Progress File (_progress.yaml)

```yaml
# Workload Progress
# Workload ID: user-authentication-feature_20260125_143022
# Created: 2026-01-25T14:30:22Z

workload_id: "user-authentication-feature_20260125_143022"
started_at: "2026-01-25T14:30:22Z"
updated_at: "2026-01-25T15:45:00Z"
status: "active"  # active | paused | completed | cancelled

# Worker progress tracking
workers:
  terminal-b:
    assigned_tasks: ["1", "4"]
    current_task: "1"
    completed_tasks: []
    status: "working"
    startedAt: "2026-01-25T14:35:00Z"
    completedAt: null

  terminal-c:
    assigned_tasks: ["2", "5"]
    current_task: null
    completed_tasks: []
    status: "idle"
    startedAt: null
    completedAt: null

  terminal-d:
    assigned_tasks: ["3", "6"]
    current_task: null
    completed_tasks: []
    status: "idle"
    startedAt: null
    completedAt: null

# Blockers reported by workers
blockers: []

# Overall progress metrics
metrics:
  total_tasks: 6
  completed_tasks: 0
  in_progress_tasks: 1
  blocked_tasks: 0
  progress_percent: 0
```

---

## 4. Workload Lifecycle

### 4.1 Workload Creation

```bash
# 1. /clarify에서 워크로드 시작
/clarify "Implement user authentication"
# → Workload ID: user-authentication_20260125_143022
# → Slug: user-authentication-20260125

# 2. /research에서 워크로드 재사용 또는 독립 시작
/research --clarify-slug user-authentication-20260125 "OAuth patterns"
# → 같은 Workload ID 재사용

/research "New independent research"
# → 새 Workload ID 생성

# 3. /planning에서 워크로드 상속
/planning --research-slug user-authentication-20260125
# → Workload ID 상속

# 4. /orchestrate에서 워크로드 디렉토리 초기화
/orchestrate --plan-slug user-authentication-20260125
# → .agent/prompts/user-authentication-20260125/ 생성
# → _context.yaml, _progress.yaml 생성
# → pending/, completed/ 디렉토리 생성
```

### 4.2 Active Workload Management

```bash
# 활성 워크로드 조회
source .claude/skills/shared/workload-files.sh
get_active_workload
# → user-authentication_20260125_143022

# 활성 워크로드 설정
set_active_workload "payment-integration_20260125_150000"
# → .agent/prompts/_active_workload.yaml 업데이트

# 워크로드 전환
switch_workload "api-refactoring-20260125"
# → 워크로드 존재 확인 후 활성화

# 모든 워크로드 목록
list_workloads
# → user-authentication-20260125
# → payment-integration-20260125
# → api-refactoring-20260125
```

### 4.3 Worker Execution

```bash
# Worker가 활성 워크로드의 프롬프트 자동 인식
/worker start b
# → findPromptFile()이 활성 워크로드 디렉토리 검색
# → .agent/prompts/user-authentication-20260125/pending/ 조회

# Worker 완료 시 같은 워크로드 디렉토리로 이동
/worker done
# → pending/ → completed/ 이동 (같은 워크로드 내)
```

---

## 5. Backward Compatibility

### 5.1 Legacy Global Files

기존 시스템과의 호환성을 위해 글로벌 파일을 유지합니다:

| Legacy Path | Workload Path |
|-------------|---------------|
| `.agent/prompts/_context.yaml` | `.agent/prompts/{slug}/_context.yaml` |
| `.agent/prompts/_progress.yaml` | `.agent/prompts/{slug}/_progress.yaml` |
| `.agent/prompts/pending/` | `.agent/prompts/{slug}/pending/` |
| `.agent/prompts/completed/` | `.agent/prompts/{slug}/completed/` |

### 5.2 Fallback Behavior

```javascript
// 활성 워크로드가 없을 때 글로벌 경로 사용
function get_workload_context_path(workload_id) {
  if (!workload_id) {
    workload_id = get_active_workload()
  }

  if (!workload_id) {
    // Fallback to global _context.yaml
    return ".agent/prompts/_context.yaml"
  }

  return `.agent/prompts/${slug}/_context.yaml`
}
```

---

## 6. API Reference

### 6.1 Slug Generator (slug-generator.sh)

| Function | Args | Output |
|----------|------|--------|
| `generate_workload_id` | topic | Workload ID |
| `generate_slug_from_workload` | workload_id | Slug |
| `extract_workload_from_slug` | slug | JSON (topic, date, pattern) |
| `init_workload` | workload_id, skill, description | Creates workload context |
| `get_current_workload` | - | Current workload JSON |
| `set_workload_context` | field, value | Updates workload field |

### 6.2 Workload Tracker (workload-tracker.sh)

| Function | Args | Output |
|----------|------|--------|
| `get_workload_prompt_dir` | workload_id/slug | Prompt directory path |
| `get_workload_context_file` | workload_id/slug | _context.yaml path |
| `get_workload_progress_file` | workload_id/slug | _progress.yaml path |
| `init_workload_directories` | workload_id/slug | Creates directory structure |
| `get_worker_prompt_file` | workload_id, worker_id, task_desc, status | Worker prompt path |
| `list_workload_prompts` | workload_id, status_filter | List of prompt files |
| `move_prompt_to_completed` | prompt_file | Moves to completed/ |
| `get_workload_from_prompt_path` | prompt_path | Workload slug |

### 6.3 Workload Files (workload-files.sh)

| Function | Args | Output |
|----------|------|--------|
| `init_workload_directory` | workload_id | Initializes directory + files |
| `get_workload_context_path` | workload_id (optional) | Context file path |
| `get_workload_progress_path` | workload_id (optional) | Progress file path |
| `set_active_workload` | workload_id | Sets active workload |
| `get_active_workload` | - | Active workload ID |
| `list_workloads` | - | List of workload slugs |
| `switch_workload` | workload_id/slug | Switches active workload |

---

## 7. Example Workflows

### 7.1 Complete E2E Workflow

```bash
# Step 1: Clarify requirements
/clarify "Implement user authentication with OAuth"
# → Workload ID: user-authentication_20260125_143022
# → Output: .agent/prompts/user-authentication-20260125/clarify.yaml

# Step 2: Research (reuse workload)
/research --clarify-slug user-authentication-20260125 "OAuth2 best practices"
# → Output: .agent/prompts/user-authentication-20260125/research.md

# Step 3: Planning (inherit workload)
/planning --research-slug user-authentication-20260125
# → Output: .agent/prompts/user-authentication-20260125/plan.yaml

# Step 4: Orchestrate (initialize workload directory)
/orchestrate --plan-slug user-authentication-20260125
# → Creates: .agent/prompts/user-authentication-20260125/
# → _context.yaml, _progress.yaml, pending/, completed/
# → Worker prompts in pending/

# Step 5: Workers execute
/worker start b  # Terminal B
# → Finds: .agent/prompts/user-authentication-20260125/pending/worker-terminal-b-*.yaml
# → Executes task

/worker done  # Terminal B completes
# → Moves: pending/worker-terminal-b-*.yaml → completed/

# Step 6: Collect and synthesize
/collect
/synthesis
```

### 7.2 Multi-Workload Management

```bash
# Start first workload
/clarify "Payment integration"
# → Workload ID: payment-integration_20260125_150000

# Switch to second workload
/clarify "User dashboard redesign"
# → Workload ID: user-dashboard-redesign_20260125_151000

# List all workloads
source .claude/skills/shared/workload-files.sh
list_workloads
# → payment-integration-20260125
# → user-dashboard-redesign-20260125

# Switch back to first workload
switch_workload "payment-integration-20260125"

# Worker continues first workload
/worker start b
# → Uses payment-integration-20260125 prompts
```

---

## 8. Best Practices

### 8.1 Workload Naming

**Good:**
- `user-authentication-20260125`
- `payment-refactor-20260125`
- `api-migration-20260125`

**Avoid:**
- `proj1-20260125` (너무 짧음)
- `implement-new-feature-for-user-management-system-20260125` (너무 김)
- `UserAuth-20260125` (대문자 사용)

### 8.2 Workload Lifecycle

1. **시작**: /clarify 또는 /research에서 워크로드 생성
2. **확장**: /planning, /orchestrate에서 워크로드 상속
3. **실행**: /worker가 활성 워크로드 인식
4. **완료**: /synthesis에서 워크로드 마무리
5. **보관**: completed/ 디렉토리로 이동, status = "completed"

### 8.3 Context Sharing

- **Global Context**: 모든 워커가 공유해야 하는 정보 (_context.yaml)
- **Worker-Specific**: 개별 워커 프롬프트 파일에 포함
- **Shared Decisions**: _context.yaml의 shared_decisions 섹션 사용

---

## 9. Troubleshooting

### 9.1 워크로드를 찾을 수 없음

```bash
# 증상: Worker가 프롬프트 파일을 찾지 못함
# 원인: 활성 워크로드가 설정되지 않음

# 해결:
source .claude/skills/shared/workload-files.sh
list_workloads  # 존재하는 워크로드 확인
switch_workload "user-authentication-20260125"  # 워크로드 활성화
```

### 9.2 글로벌 파일과 충돌

```bash
# 증상: 워크로드별 파일과 글로벌 파일이 혼재
# 원인: 기존 시스템에서 마이그레이션 중

# 해결:
# 1. 글로벌 파일을 워크로드 디렉토리로 이동
mkdir -p .agent/prompts/{slug}/pending
mv .agent/prompts/pending/worker-*.yaml .agent/prompts/{slug}/pending/

# 2. 글로벌 _context.yaml을 워크로드별로 복사
cp .agent/prompts/_context.yaml .agent/prompts/{slug}/_context.yaml
```

### 9.3 Slug 충돌

```bash
# 증상: 같은 날짜에 동일 토픽으로 여러 워크로드 생성
# 원인: Slug는 날짜까지만 포함 (시간 제외)

# 해결:
# 1. Workload ID는 고유 (시간 포함)
# 2. 디렉토리는 slug 사용하므로 시간 정보 손실
# 3. 같은 토픽은 다른 날짜에 생성하거나 토픽명 차별화
```

---

## 10. Migration Guide

### 10.1 From Global to Workload-Based

```bash
# 1. 기존 프롬프트 파일 식별
ls .agent/prompts/pending/*.yaml

# 2. 워크로드 생성
source .claude/skills/shared/slug-generator.sh
workload_id=$(generate_workload_id "migration-$(date +%Y%m%d)")
slug=$(generate_slug_from_workload "$workload_id")

# 3. 워크로드 디렉토리 초기화
source .claude/skills/shared/workload-files.sh
init_workload_directory "$workload_id"

# 4. 파일 이동
mv .agent/prompts/pending/*.yaml .agent/prompts/${slug}/pending/
mv .agent/prompts/completed/*.yaml .agent/prompts/${slug}/completed/

# 5. 활성 워크로드 설정
set_active_workload "$workload_id"
```

---

**End of Workload Management Documentation**

# Claude Code Agent

> **Version:** 7.0 | **Role:** Main Agent Orchestrator
> **Architecture:** Task-Centric Hybrid (Native Task + File-Based Prompts)

---

## 1. Core Identity

```
SHIFT-LEFT     → Validate/check as EARLY as possible in pipeline
               → Catch errors at /clarify, not /synthesis
               → Pre-flight checks before execution, not post-mortem
VERIFY-FIRST   → Verify files/imports before ANY mutation
TASK-DRIVEN    → Use Native Task System for ALL workflow tracking
DELEGATE       → Use Task subagents for complex operations
AUDIT-TRAIL    → Track files_viewed for all operations
```

### Shift Left Philosophy
> **Principle:** Detect issues as early as possible in the development lifecycle

| Pipeline Phase | Validation Gate |
|----------------|-----------------|
| `/clarify` | Requirement feasibility check |
| `/research` | Scope access validation |
| `/planning` | Pre-flight checks (files, dependencies) |
| `/orchestrate` | Phase dependency validation |
| `/worker` | Pre-execution gate |

### Workspace
```yaml
workspace_root: /home/palantir
workload_management: .claude/references/workload-management.md
```

### Workload Management
> **Unified Slug Naming Convention** (2026-01-25)

All skills use centralized workload management:
- **Workload ID**: `{topic}_{YYYYMMDD}_{HHMMSS}`
- **Slug**: `{topic}-{YYYYMMDD}`
- **Directory**: `.agent/prompts/{slug}/`

See [Workload Management Guide](.claude/references/workload-management.md) for details.

### Post-Compact Recovery Protocol (CRITICAL)

> **ABSOLUTE RULE:** Auto-Compact 후 요약 정보만으로 작업 진행 **절대 금지**

#### Detection
Compact 감지 조건: 대화 시작에 `"This session is being continued from a previous conversation"` 표시

#### Recovery Procedure (MANDATORY)

```
1. Read `.agent/prompts/_active_workload.yaml` → Get active slug
2. Read all L1/L2/L3 outputs for current workload
3. Restore full context BEFORE any action
4. NEVER proceed with summarized/remembered information only
```

#### Required File Reads by Skill

| Skill | Must Read After Compact |
|-------|------------------------|
| `/clarify` | `.agent/prompts/{slug}/clarify.yaml` |
| `/research` | `.agent/prompts/{slug}/research.md` + `research/l2_detailed.md` + `research/l3_synthesis.md` |
| `/planning` | `.agent/prompts/{slug}/plan.yaml` |
| `/orchestrate` | `.agent/prompts/{slug}/_context.yaml` |
| `/collect` | `.agent/prompts/{slug}/collection_report.md` |
| `/synthesis` | `.agent/prompts/{slug}/synthesis/synthesis_report.md` |

#### NEVER After Compact

- ❌ 요약된 컨텍스트만으로 코드 수정
- ❌ 파일 경로/내용 추측
- ❌ 이전 대화에서 "기억"한 내용으로 진행
- ❌ L1 요약만 읽고 상세 작업 진행 (L2/L3도 읽어야 함)

See [Post-Compact Recovery Module](.claude/skills/shared/post-compact-recovery.md) for implementation details.

---

## 2. Task System

> Native Task API for dependency-aware task management

| Tool | Purpose |
|------|---------|
| `TaskCreate` | Create task with subject, description, activeForm |
| `TaskUpdate` | Update status (pending→in_progress→completed) |
| `TaskList` | View all tasks |
| `TaskGet` | Get task details before starting |

### Lifecycle
```
pending → in_progress → completed
            ↓
         blocked → wait for blockers
```

### Dependency Rules
- `blockedBy`: Tasks that MUST complete first
- Worker MUST check `blockedBy` is empty before starting

---

## 3. E2E Pipeline

```
/clarify          Requirements + Design Recording
    │
    ▼
/research         Deep Codebase + External Analysis
    │
    ▼
/planning         YAML Planning + Plan Agent Review
    │
    ▼
/orchestrate      Task Decomposition + Dependencies
    │
    ▼
/assign           Worker Assignment (owner field)
    │
    ▼
┌───┴───┬───────┐
▼       ▼       ▼
Worker  Worker  Worker    Parallel Execution
B       C       D
└───────┼───────┘
        ▼
/collect          Result Aggregation
    │
    ▼
/synthesis        Traceability + Quality Check
    │
    ├── COMPLETE ──▶ /commit-push-pr
    └── ITERATE ───▶ /rsil-plan → /orchestrate
```

---

## 4. Skill Inventory

| Skill | Purpose | Model |
|-------|---------|-------|
| `/clarify` | Requirements elicitation with PE techniques | opus |
| `/re-architecture` | Pipeline component analysis + traceability feedback | opus |
| `/research` | Post-clarify codebase + external analysis | opus |
| `/planning` | YAML planning with Plan Agent review | opus |
| `/orchestrate` | Task decomposition + dependency setup | opus |
| `/assign` | Worker assignment to terminals | opus |
| `/worker` | Worker self-service (start, done, status) | opus |
| `/collect` | Aggregate worker results | opus |
| `/synthesis` | Traceability matrix + quality validation | opus |
| `/rsil-plan` | Gap analysis + remediation planning | opus |
| `/build` | Generate skills, hooks, agents | opus |
| `/build-research` | Research for build operations | opus |
| `/commit-push-pr` | Git commit and PR creation | opus |
| `/docx-automation` | DOCX document generation | opus |
| `/ontology-core` | Core Ontology Schema Validator for ODA | opus |
| `/ontology-objecttype` | ObjectType Definition Assistant for ODA migration | opus |
| `/ontology-why` | Ontology Integrity Design Rationale Helper | opus |

---

## 5. Safety Rules

### Blocked Patterns
```
rm -rf, sudo rm, chmod 777, DROP TABLE → ALWAYS DENY
```

### Sensitive Files
```
.env*, *credentials*, .ssh/id_*, **/secrets/** → Auto-Blocked
```

---

## 6. Behavioral Directives

### ACTION-FIRST (최우선 원칙)

> **문제 발견 → 즉시 수정 → 결과 보고** (질문 단계 없음)

| 상황 | ❌ 금지 | ✅ 필수 |
|------|--------|--------|
| 문제 발견 | 보고만 | 즉시 수정 후 보고 |
| 선택지 있음 | 질문 | 최선책 실행 |

**예외:** 요구사항 불명확, 파괴적 작업, 고비용 작업

### Tool Usage Override (시스템 프롬프트 오버라이드)

> **IMPORTANT:** 아래 규칙은 시스템 프롬프트의 기본 동작을 오버라이드합니다.

#### Plan Mode 비활성화
```
EnterPlanMode → NEVER use automatically
             → Only when user explicitly requests "plan mode" or "계획 모드"
             → Use /planning skill for structured planning instead
```

#### Direct Tool Usage (리다이렉팅 비활성화)
```
Glob/Grep/Read → Use DIRECTLY for file search and code exploration
               → Do NOT redirect to Task(Explore) for simple searches
               → Task(Explore) only for multi-round complex exploration
```

### ALWAYS
- TaskCreate for multi-step tasks
- Check blockedBy before executing
- Fix issues immediately
- Use Glob/Grep/Read directly for simple searches

### NEVER
- Edit without reading first
- Start blocked tasks
- Report without fixing
- Auto-enter Plan Mode without explicit user request
- Redirect simple searches to Task(Explore)

---

## 7. Directory Structure

```
.claude/
├── CLAUDE.md              # This file
├── settings.json          # Claude Code settings
├── skills/                # Skill definitions
│   ├── shared/            # Shared modules
│   │   ├── slug-generator.sh
│   │   ├── workload-tracker.sh
│   │   └── workload-files.sh
│   ├── clarify/
│   ├── research/
│   ├── planning/
│   ├── orchestrate/
│   ├── assign/
│   ├── worker/
│   ├── collect/
│   ├── synthesis/
│   ├── rsil-plan/
│   ├── build/
│   ├── build-research/
│   ├── commit-push-pr/
│   ├── docx-automation/
│   ├── re-architecture/
│   ├── ontology-core/
│   ├── ontology-objecttype/
│   └── ontology-why/
├── hooks/                 # Lifecycle hooks
│   ├── session-start.sh
│   ├── session-end.sh
│   ├── clarify-finalize.sh
│   ├── research-finalize.sh
│   └── planning-finalize.sh
├── agents/                # Custom agents
│   ├── onboarding-guide.md
│   ├── pd-readonly-analyzer.md
│   └── pd-skill-loader.md
└── references/            # Documentation
    ├── pd-patterns.md
    ├── skill-access-matrix.md
    └── workload-management.md

.agent/
├── prompts/                          # Workload-based outputs (V7.1)
│   ├── _active_workload.yaml         # Active workload pointer
│   │
│   └── {workload-slug}/              # Per-workload directory
│       ├── _context.yaml             # Orchestration context
│       ├── _progress.yaml            # Progress tracking
│       ├── pending/                  # Worker task prompts
│       ├── completed/                # Completed task prompts
│       │
│       ├── research.md               # /research output
│       ├── plan.yaml                 # /planning output
│       ├── collection_report.md      # /collect output
│       │
│       ├── outputs/                  # Worker outputs
│       │   ├── terminal-b/           # Per-terminal outputs
│       │   ├── terminal-c/
│       │   └── terminal-d/
│       │
│       └── synthesis/                # /synthesis output
│           └── synthesis_report.md
│
├── logs/                             # Validation logs
├── tmp/                              # Temporary files
└── outputs/                          # Global outputs (DEPRECATED)
```

### Workload Output Paths (V7.1)

| Skill | Output Path |
|-------|-------------|
| `/clarify` | `.agent/prompts/{slug}/clarify.yaml` |
| `/research` | `.agent/prompts/{slug}/research.md` |
| `/planning` | `.agent/prompts/{slug}/plan.yaml` |
| `/orchestrate` | `.agent/prompts/{slug}/_context.yaml` |
| `/worker` | `.agent/prompts/{slug}/outputs/{terminal}/` |
| `/collect` | `.agent/prompts/{slug}/collection_report.md` |
| `/synthesis` | `.agent/prompts/{slug}/synthesis/synthesis_report.md` |

---

## 8. Skill Frontmatter (V2.1.19)

| Field | Required | Default |
|-------|----------|---------|
| `name` | Yes | - |
| `description` | Yes | - |
| `user-invocable` | No | true |
| `model` | No | sonnet |
| `allowed-tools` | No | all |
| `hooks` | No | - |

---

## 9. MCP Tool Requirements

### Sequential Thinking (MANDATORY)

> **CRITICAL RULE:** Main Agent, 모든 Subagents, Worker terminals는 복잡한 reasoning 작업에서 **반드시** `mcp__sequential-thinking__sequentialthinking` 도구를 사용해야 합니다.

#### 사용 필수 상황

| 상황 | Sequential Thinking 필수 |
|------|-------------------------|
| Task decomposition (5+ steps) | ✅ 필수 |
| Planning & Design decisions | ✅ 필수 |
| Debugging complex issues | ✅ 필수 |
| Multi-path decision making | ✅ 필수 |
| Architecture analysis | ✅ 필수 |
| Simple file read/edit | ❌ 불필요 |

#### 호출 패턴

```javascript
// Before complex analysis, ALWAYS invoke:
mcp__sequential-thinking__sequentialthinking({
  thought: "분석 시작: [작업 내용]",
  thoughtNumber: 1,
  totalThoughts: N,  // 예상 단계 수
  nextThoughtNeeded: true
})
```

#### Skill/Agent 적용

모든 스킬과 에이전트의 `allowed-tools`에 `mcp__sequential-thinking__sequentialthinking` 포함 필수:

```yaml
allowed-tools:
  - Read
  - Grep
  - Glob
  - mcp__sequential-thinking__sequentialthinking  # MANDATORY
  - Task
```

---

> **v7.2 (2026-01-29):** Sequential Thinking Integration
> - Added Section 9: MCP Tool Requirements
> - All skills/agents must include sequential-thinking in allowed-tools
> - Mandatory for complex reasoning tasks (5+ steps)
>
> **v7.1 (2026-01-25):** Workload-Scoped Outputs
> - All skill outputs now stored in `.agent/prompts/{workload-slug}/`
> - Deprecated global paths: `.agent/research/`, `.agent/plans/`, `.agent/outputs/`
> - Updated Directory Structure with per-workload output paths
> - Added Workload Output Paths table
>
> **v7.0 (2026-01-24):** Enhanced Pipeline
> - Added /research, /planning, /rsil-plan skills
> - Directory structure documentation
> - Skill inventory with model specifications
> - Removed deprecated files and redundant sections

# Claude Code Agent

> **Version:** 7.8 | **Role:** Main Agent Orchestrator
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
task_api_guideline: .claude/references/task-api-guideline.md
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
| `/plan-draft` | `.agent/prompts/{slug}/plan-draft.yaml` |
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

### Task ID Collision Resolution (V7.4)

> **Problem:** Hook의 `get_task_status()`가 `.claude/tasks/` 하위 **모든 디렉토리**를 검색하여 같은 ID의 태스크를 먼저 찾음

**증상:**
- `completed → in_progress` 전환 거부 (실제로는 pending)
- 이전 세션의 stale 태스크가 현재 세션 태스크를 차단

**해결책:**
```bash
# 현재 세션의 태스크 디렉토리 확인
ls /home/palantir/.claude/tasks/

# 충돌하는 태스크 파일 직접 수정 (status를 completed로)
cat > /home/palantir/.claude/tasks/{session}/N.json << 'EOF'
{
  "id": "N",
  "subject": "Task subject",
  "status": "completed",
  "blocks": [],
  "blockedBy": []
}
EOF
```

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

### Pipeline Skills (E2E Workflow)

| Skill | Purpose | Model |
|-------|---------|-------|
| `/clarify` | Requirements elicitation with PE techniques | sonnet* |
| `/research` | Post-clarify codebase + external analysis | sonnet* |
| `/planning` | YAML planning with Plan Agent review | sonnet* |
| `/plan-draft` | Quick planning drafts for smaller tasks | opus |
| `/orchestrate` | Task decomposition + dependency setup | opus |
| `/assign` | Worker assignment to terminals | opus |
| `/worker` | Worker self-service (start, done, status) | opus |
| `/collect` | Aggregate worker results | opus |
| `/synthesis` | Traceability matrix + quality validation | opus |
| `/rsil-plan` | Gap analysis + remediation planning | opus |

> *Note: Skills marked with * use default model (sonnet) as no explicit model is specified in SKILL.md

### Utility Skills

| Skill | Purpose | Model |
|-------|---------|-------|
| `/build` | Generate skills, hooks, agents | opus |
| `/build-research` | Research for build operations | sonnet* |
| `/commit-push-pr` | Git commit and PR creation | opus |
| `/docx-automation` | DOCX document generation | opus |
| `/re-architecture` | Pipeline component analysis + traceability feedback | opus |

### Ontology Skills (ODA)

| Skill | Purpose | Model |
|-------|---------|-------|
| `/ontology-core` | Core Ontology Schema Validator | opus |
| `/ontology-objecttype` | ObjectType Definition Assistant | opus |
| `/ontology-why` | Ontology Integrity Design Rationale | opus |

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
├── CLAUDE.md              # This file (main configuration)
├── settings.json          # Claude Code settings
├── rules/                 # Modular rule files
│   ├── coding-style.md
│   ├── git-workflow.md
│   ├── ontology.md
│   └── security.md
├── skills/                # Skill definitions (18 skills)
│   ├── shared/            # Shared modules
│   │   ├── post-compact-recovery.md
│   │   ├── l1-l2-l3-standard.md
│   │   ├── auto-delegation.md
│   │   └── efl-template.md
│   ├── clarify/           # Requirements elicitation
│   ├── research/          # Codebase analysis
│   ├── planning/          # YAML planning
│   ├── plan-draft/        # Quick planning drafts
│   ├── orchestrate/       # Task decomposition
│   ├── assign/            # Worker assignment
│   ├── worker/            # Worker self-service
│   ├── collect/           # Result aggregation
│   ├── synthesis/         # Quality validation
│   ├── rsil-plan/         # Gap remediation
│   ├── build/             # Skill/hook/agent generation
│   ├── build-research/    # Build research
│   ├── commit-push-pr/    # Git operations
│   ├── docx-automation/   # Document generation
│   ├── re-architecture/   # Pipeline analysis
│   ├── ontology-core/     # ODA core validation
│   ├── ontology-objecttype/ # ODA object types
│   └── ontology-why/      # ODA design rationale
├── hooks/                 # Lifecycle hooks (57 files)
│   ├── enforcement/       # Gate hooks (15 files)
│   │   ├── _shared.sh
│   │   ├── blocked-task-gate.sh
│   │   ├── context-recovery-gate.sh
│   │   ├── l2l3-access-gate.sh
│   │   ├── orchestrating-l2l3-synthesis-gate.sh
│   │   ├── output-preservation-gate.sh
│   │   ├── pipeline-order-gate.sh
│   │   ├── plan-mode-gate.sh
│   │   ├── read-before-edit-gate.sh
│   │   ├── security-gate.sh
│   │   ├── sensitive-files-gate.sh
│   │   ├── sequential-thinking-gate.sh
│   │   ├── task-first-gate.sh
│   │   ├── task-lifecycle-gate.sh
│   │   └── workload-path-gate.sh
│   ├── tracking/          # Tracking hooks
│   │   ├── read-tracker.sh
│   │   └── task-tracker.sh
│   ├── task-pipeline/     # Task processing
│   │   ├── pd-context-injector.sh
│   │   ├── pd-task-interceptor.sh
│   │   └── pd-task-processor.sh
│   ├── progressive-disclosure/ # PD validators
│   │   └── post_task_validator.py
│   ├── config/            # Hook configuration
│   │   ├── bypass_list.yaml
│   │   ├── enforcement_config.yaml
│   │   └── output_preservation_config.yaml
│   ├── session-start.sh
│   ├── session-end.sh
│   ├── subagent-stop.sh       # V2.1.33: SubagentStop event
│   ├── pre-compact-save.sh    # V2.1.33: PreCompact context save
│   ├── tool-failure-handler.sh # V2.1.33: PostToolUseFailure handler
│   ├── permission-request-handler.sh # V2.1.33: PermissionRequest audit
│   ├── user-prompt-submit.sh  # V2.1.33: UserPromptSubmit
│   ├── notification-router.sh # V2.1.33: Notification routing
│   ├── async-test-runner.sh   # V2.1.33: Async PostToolUse template
│   ├── clarify-*.sh       # Clarify lifecycle
│   ├── research-*.sh      # Research lifecycle
│   ├── planning-*.sh      # Planning lifecycle
│   ├── orchestrate-*.sh   # Orchestrate lifecycle
│   ├── synthesis-finalize.sh
│   ├── collect-finalize.sh
│   ├── output_preservation_hook.py
│   └── mcp-sequential-*.sh # MCP integration
├── scripts/               # Diagnostic tools (V7.8)
│   └── diagnostics/
│       ├── hook-health-check.sh
│       ├── hook-timing-test.sh
│       └── settings-validator.sh
├── agents/                # Custom agents (6 agents)
│   ├── onboarding-guide.md
│   ├── pd-readonly-analyzer.md
│   ├── pd-skill-loader.md
│   ├── plan.md
│   ├── explore.md
│   └── claude-code-guide.md
└── references/            # Documentation (7 docs)
    ├── pd-patterns.md
    ├── skill-access-matrix.md
    ├── workload-management.md
    ├── task-api-guideline.md
    ├── hierarchical-orchestration-guide.md
    ├── ontology-roadmap.md
    └── cow-cli-architecture.md  # COW CLI Mathpix Pipeline (V7.5)

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

## 8. Skill Frontmatter (V2.1.33)

| Field | Required | Default | Since |
|-------|----------|---------|-------|
| `name` | Yes | - | V2.1.19 |
| `description` | Yes | - | V2.1.19 |
| `user-invocable` | No | true | V2.1.19 |
| `model` | No | sonnet | V2.1.19 |
| `allowed-tools` | No | all | V2.1.19 |
| `hooks` | No | - | V2.1.19 |
| `memory` | No | - | V2.1.32 |
| `once` | No | false | V2.1.33 |
| `context` | No | standard | V2.1.19 |
| `version` | No | - | V2.1.19 |

### Memory Frontmatter (V2.1.32+)

| Scope | Persistence | Use Case |
|-------|-------------|----------|
| `user` | Across all projects | User preferences, onboarding state |
| `project` | Within project | Architecture decisions, codebase patterns |
| `local` | Session-local only | Temporary context, ephemeral state |

### Hook Types in Frontmatter (V2.1.33)

| Type | Field | Behavior |
|------|-------|----------|
| `command` | `type: command` | Execute shell command |
| `prompt` | `type: prompt` | LLM-evaluated decision |
| `once` | `once: true` | Run Setup hooks only once per session |
| `async` | `async: true` | Run in background, deliver result next turn |

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

> **v7.8 (2026-02-06):** INFRA-UPDATE V2.1.33 Full Hook Coverage
> - All 12 V2.1.33 hook events registered in settings.json
> - 7 new hook scripts: subagent-stop, pre-compact-save, tool-failure-handler, permission-request-handler, user-prompt-submit, notification-router, async-test-runner
> - Prompt hook for Stop event (LLM-evaluated task completion check)
> - Async hook support for PostToolUse Write|Edit (background test runner)
> - `memory` frontmatter added to all 6 agents (user/project/local scope)
> - `once: true` field added to Setup hooks in 7 key skills
> - 3 diagnostic tools: hook-health-check.sh, hook-timing-test.sh, settings-validator.sh
> - Updated Skill Frontmatter section to V2.1.33 (memory, once, async fields)
> - Directory structure updated with new files
> - 19 tasks completed with full dependency chain
>
> **v7.7 (2026-02-05):** Ontology Definition Enhancement
> - Phase 1 Core Primitives: ObjectType, Property, SharedProperty definitions
> - 6 documentation files (6,226 lines): ObjectType.md, Property.md, SharedProperty.md, DEFINITIONS.md, TAXONOMY.md, NAMING_AUDIT.md
> - 11-section template with formal_definition (NC/SC/BC)
> - Quantitative decision matrix with thresholds
> - WF-1 Gap Report: 10 gaps identified (G1-G10)
>
> **v7.6 (2026-02-04):** PDF Reconstruction Pipeline Implementation
> - Added `cow_cli/pdf/` module (MMDMerger, MathpixPDFConverter, ReconstructionValidator)
> - 4 new MCP tools: merge_to_mmd, convert_to_pdf, validate_reconstruction, get_reconstruction_status
> - Claude Assistor role defined (Orchestrator/Validator/Recommender, NOT Performer)
> - Quality thresholds: Text ≥90%, Math ≥85%, Layout ≥95%
> - 56 test functions across 14 test classes
> - Updated `cow-cli-architecture.md` to v2.0
> - Completed 11 tasks (#12-#22) with full traceability
>
> **v7.5 (2026-02-04):** COW CLI Mathpix API Architecture Refactoring
> - Added `cow-cli-architecture.md` reference document
> - Documented UnifiedResponse pattern (PDF/Image API normalization)
> - Sub-Orchestrator validation loop pattern (검증→Orchestrating→Loop)
> - ASCII ORCHESTRATION PLAN for self-reminding in complex workflows
> - Dependency chain awareness for all task orchestration
> - 17 tasks completed with full traceability
>
> **v7.4.1 (2026-02-02):** Self-Reference Consistency Audit
> - Fixed hooks count: 48 -> 50 files
> - Added missing directories: progressive-disclosure/, config/
> - Added output_preservation_hook.py to directory structure
> - Fixed Skill Inventory model accuracy (clarify, research, planning, build-research use default sonnet)
>
> **v7.4 (2026-02-02):** Task System Enhancement & Cow Pipeline
> - Added Task ID Collision Resolution section in Task System
> - Documented hook cache conflict issue and workaround
> - Round-trip YAML Export Pipeline implemented (PR #44)
> - E2E test validation with Parallel Agents Delegation
>
> **v7.3 (2026-02-01):** Infrastructure Improvement
> - Updated Directory Structure to reflect actual files (50 hooks, 18 skills, 6 agents)
> - Added `.claude/rules/` modular rule files documentation
> - Reorganized Skill Inventory into categories (Pipeline, Utility, Ontology)
> - Added `/plan-draft` skill to inventory
> - Updated agents list: added plan.md, explore.md, claude-code-guide.md
> - Updated references list: added task-api-guideline.md, hierarchical-orchestration-guide.md, ontology-roadmap.md
> - Added hooks/enforcement/ detailed structure (15 gate hooks)
> - Added hooks/tracking/ and hooks/task-pipeline/ subdirectories
> - Added task_api_guideline reference to Workspace section
>
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

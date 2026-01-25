# Claude Code Agent

> **Version:** 7.0 | **Role:** Main Agent Orchestrator
> **Architecture:** Task-Centric Hybrid (Native Task + File-Based Prompts)

---

## 1. Core Identity

```
VERIFY-FIRST   → Verify files/imports before ANY mutation
TASK-DRIVEN    → Use Native Task System for ALL workflow tracking
DELEGATE       → Use Task subagents for complex operations
AUDIT-TRAIL    → Track files_viewed for all operations
```

### Workspace
```yaml
workspace_root: /home/palantir
task_list_id: ${CLAUDE_CODE_TASK_LIST_ID}
```

### Multi-Terminal Execution
```bash
cc <task-list-id>       # All terminals use same ID
cc palantir-dev         # Example: shared task list
```

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
| `/research` | Post-clarify codebase + external analysis | opus |
| `/planning` | YAML planning with Plan Agent review | opus |
| `/orchestrate` | Task decomposition + dependency setup | sonnet |
| `/assign` | Worker assignment to terminals | sonnet |
| `/worker` | Worker self-service (start, done, status) | sonnet |
| `/collect` | Aggregate worker results | sonnet |
| `/synthesis` | Traceability matrix + quality validation | opus |
| `/rsil-plan` | Gap analysis + remediation planning | opus |
| `/build` | Generate skills, hooks, agents | sonnet |
| `/build-research` | Research for build operations | sonnet |
| `/commit-push-pr` | Git commit and PR creation | sonnet |
| `/docx-automation` | DOCX document generation | sonnet |

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

### ALWAYS
- TaskCreate for multi-step tasks
- Check blockedBy before executing
- Fix issues immediately

### NEVER
- Edit without reading first
- Start blocked tasks
- Report without fixing

---

## 7. Directory Structure

```
.claude/
├── CLAUDE.md              # This file
├── settings.json          # Claude Code settings
├── skills/                # Skill definitions
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
│   └── docx-automation/
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
    └── skill-access-matrix.md

.agent/
├── prompts/               # Worker prompts
│   ├── _context.yaml      # Global context
│   ├── _progress.yaml     # Progress tracking
│   └── pending/           # Worker task files
├── research/              # Research outputs
├── plans/                 # Planning documents
├── clarify/               # Clarification records
└── outputs/               # Worker outputs
```

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

> **v7.0 (2026-01-24):** Enhanced Pipeline
> - Added /research, /planning, /rsil-plan skills
> - Directory structure documentation
> - Skill inventory with model specifications
> - Removed deprecated files and redundant sections

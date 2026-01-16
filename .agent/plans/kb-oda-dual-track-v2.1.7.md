# Multi-Track Workflow: KB System + ODA Quality Audit

> **Version:** V2.1.7-Enhanced
> **Generated:** 2026-01-16
> **Thinking Mode:** ULTRATHINK (64K budget for deep analysis)
> **Execution:** Parallel (Track A ∥ Track B)
> **Context Management:** Auto-Compact aware, resume-enabled

---

## Metadata

```yaml
plan_id: kb-oda-dual-track-v2.1.7
status: pending
created: 2026-01-16
tracks:
  - name: Track A
    purpose: KB System for Dev/Delta job families
    scope: /home/palantir/park-kyungchan/palantir/coding/
  - name: Track B
    purpose: ODA SubModule Quality Management
    scope: /home/palantir/park-kyungchan/palantir/
governance:
  protocol: ODA 3-Stage (SCAN → TRACE → VERIFY)
  evidence_required: true
  proposal_workflow: hazardous actions only
```

---

## Phase 0: Preflight & Decomposition (MANDATORY)

### 0.1 Context Budget Check (V2.1.7)

```python
# ContextBudgetManager ensures effective context window management
# ULTRATHINK mode: 64K max output → 136K effective window

from lib.oda.planning.context_budget_manager import (
    ContextBudgetManager,
    ThinkingMode,
    DelegationDecision,
)

manager = ContextBudgetManager(thinking_mode=ThinkingMode.ULTRATHINK)

# Check before each delegation
def check_delegation(subagent_type: str, estimated_tokens: int):
    decision = manager.check_before_delegation(subagent_type, estimated_tokens)

    if decision == DelegationDecision.PROCEED:
        return "safe_to_delegate"
    elif decision == DelegationDecision.REDUCE_SCOPE:
        return "apply_task_decomposer"
    elif decision == DelegationDecision.DEFER:
        return "run_compact_first"
    else:  # ABORT
        return "critical_context_usage"
```

### 0.2 TaskDecomposer for Large Scope Operations (V2.1.7)

```python
from lib.oda.planning.task_decomposer import (
    TaskDecomposer,
    SubagentType,
    should_decompose_task,
    decompose_task,
)

# Scope keyword detection (자동 감지)
SCOPE_KEYWORDS = {
    "korean": ["전체", "모든", "완전한", "전부"],
    "english": ["all", "entire", "complete", "whole", "full", "every"]
}

# Check if decomposition needed
if should_decompose_task(
    task="Analyze entire codebase for Dev/Delta tech stacks",
    scope="/home/palantir/park-kyungchan/palantir/coding/"
):
    subtasks = decompose_task(
        task="...",
        scope="...",
        subagent_type=SubagentType.EXPLORE
    )
    # Deploy parallel subagents
    for subtask in subtasks:
        Task(**subtask.to_task_params(), run_in_background=True)
```

### 0.3 TodoWrite Initialization (Auto-Compact Recovery 필수)

```python
# MANDATORY: 최소 3개 이상 TodoWrite로 진행 상황 추적
# Auto-Compact 발생 시 Plan File + TodoWrite = 완전한 복구

TodoWrite(todos=[
    {
        "content": "Phase 0: Preflight checks and decomposition",
        "activeForm": "Running preflight checks",
        "status": "completed"
    },
    {
        "content": "Track A: KB System - Stage A/B/C",
        "activeForm": "Building KB system for job families",
        "status": "in_progress"
    },
    {
        "content": "Track B: ODA Quality - Stage A/B/C",
        "activeForm": "Auditing ODA schema and workflows",
        "status": "in_progress"
    },
    {
        "content": "Phase 4: Synthesis and final report",
        "activeForm": "Generating consolidated report with evidence",
        "status": "pending"
    }
])
```

---

## Workspace Specification

```yaml
workspace:
  root: /home/palantir/park-kyungchan/palantir

  track_a:
    scope: coding/
    kb_output: coding/knowledge_bases/
    purpose: "KB 중심 학습 시스템 - Dev/Delta 직군별 언어/스택"

  track_b:
    scope: lib/oda/, .agent/
    submodule_output: lib/oda/quality/
    purpose: "ODA SubModule - Foundry/AIP 모방 품질 관리"
```

---

## Common Principles (반드시 준수)

| # | Principle | Enforcement |
|---|-----------|-------------|
| 1 | **네트워크 연결 상태에서 진행** | WebSearch로 외부 공식 문서/채용공고 실제 검색·검증 (로컬 추측 금지) |
| 2 | **외부 고품질 자료 전부 저장** | KB에 요약/핵심 제약/용어/URL/조회일 포함하여 재사용 가능 형태로 저장 |
| 3 | **3-Stage Protocol로 점검** | Stage A(SCAN) → B(TRACE) → C(VERIFY) 순서 엄수, `files_viewed` 없으면 INVALID |
| 4 | **크로스언어 연결은 아티팩트 기반** | 런타임 RPC가 아닌 dependencies, CI/빌드/배포 workflow artifact로 연결 |
| 5 | **토큰화는 런타임 계산만** | 프롬프트 토큰/특징량 저장/영속화 금지, 런타임에서만 사용 |
| 6 | **1인 규모 + 확장 가능** | 모듈 경계 명확히, 향후 사람/LLM/모듈 확장 고려 |

---

## Track A: KB System (Dev/Delta 언어/스택 업데이트)

### Purpose

`coding/`은 "KB 중심 학습 시스템"이며, Palantir Dev(PD) 및 Delta(FDE/FDSE) 직군이 실제로 필요로 하는 프로그래밍 언어/스택을 KB 전체 관점에서 업데이트한다.

### Requirements

1. **Dev/Delta 직군 구분을 정확 용어로 반영**
   - Dev(PD) = Product Development
   - Delta(FDE) = Forward Deployed Engineer / FDSE = Forward Deployed Software Engineer
   - KB에서 혼동 없이 유지/정정

2. **네트워크 기반 언어/스택 확정**
   - Palantir 공식 문서/공식 채용 공고(직군별)
   - 개발자 커뮤니티, 인터뷰 후기, 블로그
   - 광범위한 소스에서 실시간 검증

3. **KB 전반 업데이트 (애자일+동적 설계 방식 유지)**
   - 언어/스택 서술 부정확/근거 약한 부분 수정
   - 깨진 링크/불명확한 예시 코드 공식 근거로 수정

4. **외부자료 저장 (참고 링크만 남기기 금지)**
   - 요약 + 핵심 제약 + 용어 + URL + 조회일 포함

### Stage A: Source Discovery (SCAN)

```python
# Parallel background execution (V2.1.7 패턴)
Task(
    subagent_type="Explore",
    description="Discover Dev/Delta tech stack sources",
    prompt="""
## Context
Operating under ODA governance with ULTRATHINK mode (15K output budget).
Track A Stage A: Source Discovery for KB System.

## Task
네트워크 검색으로 Palantir Dev(PD) / Delta(FDE/FDSE) 직군의 언어/스택 정보 수집:

### 1. 공식 소스
- Palantir Careers 페이지 (직군별 채용공고)
- Palantir Engineering Blog
- Palantir GitHub repositories
- Foundry/AIP 공식 문서

### 2. 커뮤니티 소스 (광범위 검색)
- Glassdoor/Blind 인터뷰 후기
- Reddit r/cscareerquestions
- LinkedIn 개발자 프로필
- Medium/Dev.to 기술 블로그

### Search Queries
```
"Palantir software engineer tech stack 2025 2026"
"Palantir FDE interview programming languages"
"Palantir product development Python Java TypeScript"
"Palantir Delta engineer skills requirements"
"Palantir Foundry developer experience"
```

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 15K TOKENS.
Return ONLY:
- Source URLs (grouped by type)
- Key language/stack findings per role
- Verification status (official/community/unverified)

## Required Evidence
```yaml
stage_a_evidence:
  files_viewed: []  # N/A for network research
  sources_discovered:
    official:
      - url: ""
        type: "careers|blog|docs|github"
        verified: true
        retrieved_date: "2026-01-16"
    community:
      - url: ""
        type: "interview|blog|forum"
        credibility: "high|medium|low"
        retrieved_date: "2026-01-16"
  language_findings:
    dev_pd:
      required: []
      preferred: []
      evidence_urls: []
    delta_fde:
      required: []
      preferred: []
      evidence_urls: []
  complexity: "medium"
```
    """,
    run_in_background=True,
    context="fork"
)

# Parallel WebSearch calls
WebSearch(query="Palantir software engineer tech stack 2025 2026")
WebSearch(query="Palantir FDE forward deployed engineer interview languages")
WebSearch(query="Palantir product development Python Java requirements")
```

### Stage B: KB Structure Design (TRACE)

```python
Task(
    subagent_type="Plan",
    description="Design KB structure for Dev/Delta",
    prompt="""
## Context
Operating under ODA governance. Sources validated in Stage A.
Track A Stage B: KB Structure Design.

## Task
Stage A에서 수집한 소스를 바탕으로 KB 구조 설계:

### 1. 파일 구조 설계
```
coding/knowledge_bases/
├── job_families/
│   ├── dev_pd/
│   │   ├── languages/
│   │   │   ├── python.md
│   │   │   ├── java.md
│   │   │   └── typescript.md
│   │   └── stacks/
│   │       └── foundry_development.md
│   └── delta_fde/
│       ├── languages/
│       └── stacks/
├── external_sources/
│   ├── official/
│   │   └── palantir_careers_2026.md
│   └── community/
│       └── interview_experiences.md
└── _index.md  # Navigation and cross-references
```

### 2. KB Entry Schema (YAML Frontmatter)
```yaml
---
type: kb_entry
role: "dev_pd|delta_fde"
category: "language|stack|tool"
name: ""
sources:
  - url: ""
    type: "official|community"
    retrieved: "YYYY-MM-DD"
    credibility: "high|medium|low"
tags: []
last_updated: ""
---
```

### 3. 크로스언어 연결 방식
- Python ↔ TypeScript: Package.json dependencies, pyproject.toml
- CI/CD artifacts: .github/workflows/*.yml
- 런타임 RPC 대신 파일 의존성 그래프로 연결

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 10K TOKENS.

## Required Evidence
```yaml
stage_b_evidence:
  imports_verified:
    - "pathlib for file operations"
    - "yaml for frontmatter parsing"
  signatures_matched:
    - "def create_kb_entry(role, category, sources) -> KBEntry"
  file_structure_plan:
    directories: []
    files: []
  tagging_schema:
    required_fields: []
    optional_fields: []
  test_strategy: "Unit tests for KB entry validation"
```

DO NOT implement, planning only.
    """,
    run_in_background=True
)
```

### Stage C: KB Population & Verification (VERIFY)

```python
# Execute after Stage A/B complete
Task(
    subagent_type="general-purpose",
    description="Populate KB with validated entries",
    prompt="""
## Context
Operating under ODA governance. Execute Stage C with evidence.
Track A Stage C: KB Population.

## Task
Stage B에서 설계한 구조로 KB 생성:

### 1. KB 엔트리 생성 (Proposal Workflow)
- 검증된 소스만 사용 (Stage A evidence 참조)
- 각 엔트리는 YAML frontmatter + Markdown body
- 소스 URL, 조회일, 신뢰도 반드시 포함

### 2. 외부자료 저장 규칙
```markdown
# External Source: [Source Name]

## Metadata
- URL: [full URL]
- Retrieved: 2026-01-16
- Type: official|community
- Credibility: high|medium|low

## Summary
[핵심 내용 요약 - 2-3 paragraphs]

## Key Constraints
- [제약조건 1]
- [제약조건 2]

## Terminology
| Term | Definition |
|------|------------|
| ... | ... |

## Raw Excerpts (for LLM reference)
[코드/문서 발췌 - 필요시]
```

### 3. 품질 검증
- Frontmatter schema validation
- URL reachability check (if possible)
- Cross-reference consistency

## Safety
- Use Proposal workflow for file creation (hazardous)
- Verify each entry with schema validation

## Required Evidence
```yaml
stage_c_evidence:
  quality_checks:
    - name: "frontmatter_validation"
      status: "passed|failed"
    - name: "url_verification"
      status: "passed|failed|skipped"
    - name: "cross_reference_check"
      status: "passed|failed"
  kb_files_created:
    - path: ""
      role: ""
      category: ""
  external_sources_saved:
    - path: ""
      source_url: ""
      retrieved_date: ""
  findings_summary:
    CRITICAL: 0
    ERROR: 0
    WARNING: 0
```
    """
)
```

### Track A Agent Registry (for Resume)

```yaml
# .agent/plans/kb-oda-dual-track-v2.1.7.md
track_a_agents:
  stage_a:
    agent_id: ""  # To be filled after execution
    subagent_type: "Explore"
    status: "pending"
  stage_b:
    agent_id: ""
    subagent_type: "Plan"
    status: "pending"
  stage_c:
    agent_id: ""
    subagent_type: "general-purpose"
    status: "pending"
```

---

## Track B: ODA SubModule (Foundry/AIP 모방 품질 관리)

### Purpose

repo 루트는 Palantir AIP/Foundry를 모방해 만든 ODA이며, SubModule은:
- ObjectTypes, LinkTypes, ActionTypes, Schema/Migrations, Proposals/Approval 등을
- "새롭게 정의" / "기존 정의 개선" / "E2E 품질 관리"하는 모듈

### SubModule Requirements (Foundry/AIP 모방)

| # | Requirement | Description |
|---|-------------|-------------|
| 1 | **정의/스펙 계층** | ObjectTypes/LinkTypes/ActionTypes/Functions/Interfaces/Dynamic Security를 "정의 가능한 스펙"으로 표현 |
| 2 | **검증/정합성** | 스펙 간 참조 무결성, schema migration 제약, 충돌/중복 탐지 |
| 3 | **Schema/Migrations** | 스키마 변경과 마이그레이션 제약/정책 모델링, E2E 흐름에서 누락 없이 처리 |
| 4 | **Proposals/Approval** | 코드 변경 + 온톨로지 변경 모두 "Proposal→Approval→Apply" 흐름으로 통합 |
| 5 | **LLM-독립 (E2E)** | Claude/Gemini/Codex 등 어떤 LLM이든 동일한 스키마/검증/거버넌스로 작동 |
| 6 | **충돌/중복 격리** | 기존 ODA와 충돌 시 어댑터/네임스페이스로 격리하여 SubModule로 운영 |

### Stage A: Schema Discovery (SCAN)

```python
Task(
    subagent_type="Explore",
    description="Discover all ODA schema definitions",
    prompt="""
## Context
Operating under ODA governance with ULTRATHINK mode (15K output budget).
Track B Stage A: Schema Discovery.

## Task
`lib/oda/` 및 관련 디렉토리에서 모든 스키마 정의 발견:

### 1. ObjectType 정의
```bash
rg -n "class.*ObjectType|BaseModel" lib/oda/
rg -n "@dataclass" lib/oda/
rg -n "class.*Schema" lib/oda/
```

### 2. LinkType 정의
```bash
rg -n "LinkType|ForeignKey|relationship" lib/oda/
```

### 3. ActionType 등록
```bash
rg -n "@register_action|ActionType|hazardous" lib/oda/
rg -n "def.*action|async def.*action" lib/oda/
```

### 4. Schema/Migrations
```bash
rg -n "migration|alembic|version" lib/oda/
ls -la lib/oda/**/migrations/ 2>/dev/null
```

### 5. Proposal 워크플로우
```bash
rg -n "Proposal|approve|reject|execute_proposal" lib/oda/
```

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 15K TOKENS.
Return: File paths + line numbers + brief description only.

## Required Evidence
```yaml
stage_a_evidence:
  files_viewed:
    - path: ""
      lines: []
  object_types_found:
    - name: ""
      file: ""
      line: 0
      has_pydantic: true|false
  link_types_found:
    - name: ""
      file: ""
      line: 0
  action_types_found:
    - name: ""
      file: ""
      line: 0
      hazardous: true|false
  schema_migrations:
    - file: ""
      type: "alembic|custom|none"
  proposal_workflow:
    - component: ""
      file: ""
      status: "implemented|partial|missing"
  complexity: "large"
```
    """,
    run_in_background=True,
    context="fork"
)

# Parallel: Search Foundry/AIP official patterns
WebSearch(query="Palantir Foundry ObjectType LinkType ActionType schema 2025")
WebSearch(query="Palantir Ontology SDK schema migration patterns")
WebSearch(query="Palantir AIP governance approval workflow")
```

### Stage B: Foundry/AIP Compliance Check (TRACE)

```python
Task(
    subagent_type="Plan",
    description="Verify Foundry-like quality patterns",
    prompt="""
## Context
Operating under ODA governance. Schema inventory from Stage A.
Track B Stage B: Compliance Verification.

## Task
Stage A에서 발견한 스키마들의 Foundry/AIP 패턴 준수 검증:

### 1. Type System Compliance
- [ ] 모든 ObjectTypes가 Pydantic validators 사용
- [ ] 필드 타입 명시적 정의 (Any 사용 최소화)
- [ ] Optional 필드 vs Required 필드 명확히 구분

### 2. Schema Versioning Compliance
- [ ] Migration 파일 존재 여부
- [ ] Version tracking 메커니즘
- [ ] Backward compatibility 정책

### 3. Governance Compliance
- [ ] 모든 hazardous actions가 Proposal 요구
- [ ] Approval gate 존재 확인
- [ ] Audit trail 로깅

### 4. LLM Independence Check
- [ ] ActionTypes 내 직접 LLM 호출 없음
- [ ] Schema가 JSON export 가능
- [ ] 실행 로직이 LLM-agnostic

### 5. 충돌/중복 분석
기존 ODA 코어와 새 SubModule 간:
- 네임스페이스 충돌 가능성
- 중복 정의 탐지
- 어댑터 필요 여부

## Verification Strategy
1. Cross-reference with `.agent/config/agent_registry.yaml`
2. Check Proposal workflow integration in MCP tools
3. Verify LLM-independent execution paths

## Constraint: Output Budget
YOUR OUTPUT MUST NOT EXCEED 10K TOKENS.

## Required Evidence
```yaml
stage_b_evidence:
  compliance_checks:
    - pattern: "Pydantic validation"
      status: "compliant|partial|non_compliant"
      files_checked: []
      issues: []
    - pattern: "Schema versioning"
      status: ""
      files_checked: []
      issues: []
    - pattern: "Governance (Proposal workflow)"
      status: ""
      files_checked: []
      issues: []
    - pattern: "LLM independence"
      status: ""
      files_checked: []
      issues: []
  conflict_analysis:
    namespace_conflicts: []
    duplicate_definitions: []
    adapter_requirements: []
  imports_verified:
    - "pydantic for validation"
    - "sqlite3 for persistence"
  test_strategy: "E2E workflow test with non-hazardous action"
```

DO NOT implement, planning only.
    """,
    run_in_background=True
)
```

### Stage C: E2E Workflow Test (VERIFY)

```python
Task(
    subagent_type="general-purpose",
    description="Run E2E Proposal workflow test",
    prompt="""
## Context
Operating under ODA governance. Execute full Proposal lifecycle.
Track B Stage C: E2E Verification.

## Task
Proposal 워크플로우 E2E 테스트 실행:

### 1. Non-Hazardous Action Test
```python
# Safe test with stage_c.verify (non-hazardous)
mcp__oda_ontology__execute_action(
    api_name="stage_c.verify",
    params={"target": "lib/oda/", "checks": ["lint", "type"]}
)
```

### 2. Hazardous Action Test (Simulated)
```python
# Create proposal for file.modify (hazardous)
result = mcp__oda_ontology__create_proposal(
    action_type="file.modify",
    payload={
        "path": "lib/oda/quality/__init__.py",
        "content": "# ODA Quality SubModule\n",
        "reason": "Initialize quality submodule"
    },
    submit=True,
    validate=True
)

# Approve (in test/development mode)
mcp__oda_ontology__approve_proposal(
    proposal_id=result["proposal_id"],
    comment="E2E test approval"
)

# Execute
mcp__oda_ontology__execute_proposal(
    proposal_id=result["proposal_id"]
)
```

### 3. LLM Independence Verification
- ActionType 실행 시 LLM 호출 없이 완료되는지 확인
- Schema export가 JSON으로 가능한지 확인
- 다른 LLM (Gemini, Codex) 관점에서 동일하게 실행 가능한지 검토

### 4. Schema Export Test
```python
# Export all schemas to JSON for LLM reference
mcp__oda_ontology__list_actions(include_hazardous_only=False)
# → JSON schema output 생성
```

## Safety
- 실제 파일 수정은 최소화 (테스트 파일만)
- Proposal 테스트 후 cleanup

## Required Evidence
```yaml
stage_c_evidence:
  quality_checks:
    - name: "non_hazardous_action_test"
      status: "passed|failed"
      command: "mcp__oda_ontology__execute_action"
      result: ""
    - name: "proposal_workflow_test"
      status: "passed|failed"
      steps:
        - "create_proposal": "passed|failed"
        - "approve_proposal": "passed|failed"
        - "execute_proposal": "passed|failed"
    - name: "llm_independence_test"
      status: "verified|issues"
      proof: ""
    - name: "schema_export_test"
      status: "passed|failed"
      output_format: "json"
  findings:
    CRITICAL: []
    ERROR: []
    WARNING: []
  submodule_status:
    initialized: true|false
    e2e_verified: true|false
    ready_for_production: true|false
```
    """
)
```

### Track B Agent Registry (for Resume)

```yaml
track_b_agents:
  stage_a:
    agent_id: ""
    subagent_type: "Explore"
    status: "pending"
  stage_b:
    agent_id: ""
    subagent_type: "Plan"
    status: "pending"
  stage_c:
    agent_id: ""
    subagent_type: "general-purpose"
    status: "pending"
```

---

## Phase 4: Synthesis & Reporting

### 4.1 Evidence Aggregation

```python
# Collect all evidence from Track A and Track B
final_evidence = {
    "track_a": {
        "stage_a": stage_a_evidence,
        "stage_b": stage_b_evidence,
        "stage_c": stage_c_evidence,
    },
    "track_b": {
        "stage_a": stage_a_evidence,
        "stage_b": stage_b_evidence,
        "stage_c": stage_c_evidence,
    }
}
```

### 4.2 Report Template (Markdown + YAML Evidence)

```markdown
# KB System + ODA Quality Audit Report

## Executive Summary
- **Generated:** 2026-01-16
- **Thinking Mode:** ULTRATHINK
- **Execution:** Parallel (Track A ∥ Track B)

## Track A Summary: KB System

### Sources Validated
| Type | Count | Status |
|------|-------|--------|
| Official | X | Verified |
| Community | Y | Mixed |

### KB Entries Created
| Path | Role | Category |
|------|------|----------|
| coding/knowledge_bases/job_families/dev_pd/... | dev_pd | language |

### External Sources Saved
| Source | URL | Retrieved | Credibility |
|--------|-----|-----------|-------------|
| ... | ... | 2026-01-16 | high |

## Track B Summary: ODA Quality

### Schema Compliance
| Pattern | Status | Issues |
|---------|--------|--------|
| Pydantic validation | ✓ Compliant | 0 |
| Schema versioning | ⚠ Partial | 2 |
| Governance | ✓ Compliant | 0 |
| LLM independence | ✓ Verified | 0 |

### E2E Workflow Test
| Step | Status | Evidence |
|------|--------|----------|
| create_proposal | ✓ Passed | proposal_id: xxx |
| approve_proposal | ✓ Passed | approved_at: ... |
| execute_proposal | ✓ Passed | result: ... |

### SubModule Status
- Initialized: ✓
- E2E Verified: ✓
- Ready for Production: ⚠ (pending schema versioning fixes)

## Evidence Attachments

### Track A Evidence (YAML)
```yaml
# Full evidence here
```

### Track B Evidence (YAML)
```yaml
# Full evidence here
```

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## Next Steps
- [ ] Address schema versioning gaps
- [ ] Complete KB entries for remaining tech stacks
- [ ] Production deployment checklist
```

### 4.3 Plan File Update

```python
# Update this plan file with completion status
plan_update = {
    "status": "completed",
    "completed_at": "2026-01-16",
    "track_a_status": "completed",
    "track_b_status": "completed",
    "agent_ids": {
        "track_a": {...},
        "track_b": {...}
    },
    "outstanding_issues": []
}
```

---

## Resume Protocol (Auto-Compact Recovery)

### After Auto-Compact

```python
# 1. Read plan file to restore context
plan_content = Read(".agent/plans/kb-oda-dual-track-v2.1.7.md")

# 2. Check agent registry for resumable agents
track_a_agent_id = plan_content["track_a_agents"]["stage_a"]["agent_id"]
track_b_agent_id = plan_content["track_b_agents"]["stage_a"]["agent_id"]

# 3. Resume interrupted agents
if track_a_agent_id and manager.can_resume(track_a_agent_id):
    Task(
        subagent_type="Explore",
        prompt="Continue Track A Stage A analysis",
        description="Resume Track A",
        resume=track_a_agent_id
    )

# 4. Check TodoWrite for progress
# TodoWrite automatically restored from .claude/todos/
```

---

## Acceptance Criteria (완료 기준)

### Track A (coding/)
- [ ] Dev/Delta 언어/스택이 네트워크 근거 기반으로 KB에 반영
- [ ] 외부자료 요약이 repo에 저장 (URL + 조회일 + 신뢰도)
- [ ] KB Entry schema validation 통과

### Track B (root ODA/)
- [ ] SubModule이 ObjectTypes/LinkTypes/ActionTypes/Schema/Migrations/Proposals/Approval 품질 관리
- [ ] E2E로 정의→검증→제안→승인→적용 흐름 동작 확인
- [ ] LLM-독립 실행 검증 완료

### Common
- [ ] 전체 작업에서 외부 자료 저장됨
- [ ] 추측/미검증 주장 없이 근거 기반 업데이트
- [ ] 3-Stage Protocol 모든 단계에서 evidence 포함

---

## Safety & Governance

### Blocked Operations
```
rm -rf          → ALWAYS DENY
sudo rm         → ALWAYS DENY
DROP TABLE      → ALWAYS DENY
eval(           → ALWAYS DENY
Direct LLM call in ActionType → ALWAYS DENY
```

### Proposal Required
- KB file creation (file.write)
- Schema modifications
- ActionType registration
- Security-sensitive changes

### Evidence Validation
ALL stages MUST include `files_viewed` or `sources_discovered` evidence.
Stages without evidence are INVALID.

---

## Execution Checklist

```
[ ] Phase 0: Preflight
    [ ] ContextBudgetManager initialized (ULTRATHINK)
    [ ] TaskDecomposer checked for large scopes
    [ ] TodoWrite initialized (min 3 tasks)

[ ] Track A: KB System (Parallel)
    [ ] Stage A: Sources discovered and validated
    [ ] Stage B: KB structure designed
    [ ] Stage C: KB populated with evidence

[ ] Track B: ODA Quality (Parallel)
    [ ] Stage A: Schema inventory complete
    [ ] Stage B: Foundry compliance verified
    [ ] Stage C: E2E workflow tested

[ ] Phase 4: Synthesis
    [ ] Evidence aggregated
    [ ] Report generated (Markdown + YAML)
    [ ] Plan file updated
    [ ] Acceptance criteria verified
```

---

> **V2.1.7 Features Applied:**
> - ContextBudgetManager with ULTRATHINK mode (64K thinking budget)
> - TaskDecomposer for large scope operations
> - Parallel execution (Track A ∥ Track B) with run_in_background=True
> - Resume parameter for Auto-Compact recovery
> - Plan file persistence for context preservation
> - Evidence schemas for anti-hallucination compliance

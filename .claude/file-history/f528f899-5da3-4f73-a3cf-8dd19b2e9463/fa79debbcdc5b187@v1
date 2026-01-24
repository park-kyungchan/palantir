# 새 세션용 최종 요구사항 (V2.1.7 Enhanced - 복붙용)

> **Copy this entire prompt to start a new session**

---

## 0) Metadata & Context

```yaml
version: V2.1.7-Enhanced
thinking_mode: ULTRATHINK  # 64K output budget for deep analysis
execution: parallel        # Track A ∥ Track B simultaneously
workspace:
  root: /home/palantir/park-kyungchan/palantir
  track_a: coding/         # KB 중심 학습 시스템
  track_b: lib/oda/        # ODA SubModule 품질 관리
plan_file: .agent/plans/kb-oda-dual-track-v2.1.7.md  # For Auto-Compact recovery
```

---

## 1) 공통 원칙 (반드시 준수)

| # | Principle | Enforcement |
|---|-----------|-------------|
| 1 | 네트워크 연결 상태에서 진행 | WebSearch로 외부 자료 실제 검색·검증 (로컬 추측 금지) |
| 2 | 외부 자료 전부 저장 | KB에 요약+제약+용어+URL+조회일 포함, 재사용 가능 형태 |
| 3 | 3-Stage Protocol | Stage A(SCAN)→B(TRACE)→C(VERIFY), `files_viewed` 없으면 INVALID |
| 4 | 크로스언어 연결 | 런타임 RPC 아닌 dependencies/CI workflow artifact 기반 |
| 5 | 토큰화 런타임만 | 토큰/특징량 저장 금지, 런타임에서만 사용 |
| 6 | 확장 가능 설계 | 1인 운영 but 모듈 경계 명확, 향후 확장 고려 |

---

## 2) Track A: KB System (coding/)

### 목적
Palantir Dev(PD) / Delta(FDE/FDSE) 직군별 언어/스택을 네트워크 검증 기반으로 KB 업데이트

### 해야 할 일

1. **Dev/Delta 직군 구분 정확히**
   - Dev(PD) = Product Development
   - Delta(FDE) = Forward Deployed Engineer

2. **네트워크 기반 언어/스택 확정**
   - 공식: Palantir Careers, Engineering Blog, GitHub, Foundry/AIP docs
   - 커뮤니티: Glassdoor/Blind 인터뷰, Reddit, LinkedIn, Medium (광범위 검색)

3. **KB 전반 업데이트** (애자일+동적 설계 유지)

4. **외부자료 저장** (참고 링크만 남기기 금지)

### 산출물
- `coding/knowledge_bases/job_families/dev_pd/` - 언어/스택 KB
- `coding/knowledge_bases/job_families/delta_fde/` - 언어/스택 KB
- `coding/knowledge_bases/external_sources/` - 검증된 외부자료 저장

### Execution (3-Stage)

```python
# Stage A: Parallel source discovery
Task(subagent_type="Explore", description="Discover Dev/Delta sources",
     prompt="...", run_in_background=True, context="fork")
WebSearch(query="Palantir software engineer tech stack 2025 2026")
WebSearch(query="Palantir FDE interview programming languages")

# Stage B: KB structure design
Task(subagent_type="Plan", description="Design KB structure",
     prompt="...", run_in_background=True)

# Stage C: Populate with Proposal workflow
Task(subagent_type="general-purpose", description="Populate KB entries",
     prompt="...")
```

---

## 3) Track B: ODA SubModule (root/)

### 목적
Foundry/AIP 모방 품질 관리 SubModule - ObjectTypes/LinkTypes/ActionTypes/Schema/Proposals 품질 보증

### SubModule 기능 요구

| # | Feature | Description |
|---|---------|-------------|
| 1 | 정의/스펙 계층 | ObjectTypes/LinkTypes/ActionTypes 정의 가능한 스펙 표현 |
| 2 | 검증/정합성 | 참조 무결성, migration 제약, 충돌/중복 탐지 |
| 3 | Schema/Migrations | 스키마 변경/마이그레이션 정책 모델링 |
| 4 | Proposals/Approval | Proposal→Approval→Apply 통합, hazardous 승인 게이트 |
| 5 | LLM-독립 | Claude/Gemini/Codex 어떤 LLM이든 동일 거버넌스 |
| 6 | 충돌 격리 | 기존 ODA와 어댑터/네임스페이스로 격리 |

### 산출물
- SubModule 코드/스키마/검증 (E2E 동작 확인)
- Foundry/AIP 공식 자료 KB 저장

### Execution (3-Stage)

```python
# Stage A: Schema discovery
Task(subagent_type="Explore", description="Discover ODA schemas",
     prompt="rg ObjectType/LinkType/ActionType...", run_in_background=True)
WebSearch(query="Palantir Foundry ObjectType schema patterns")

# Stage B: Compliance check
Task(subagent_type="Plan", description="Verify Foundry compliance",
     prompt="...", run_in_background=True)

# Stage C: E2E workflow test
Task(subagent_type="general-purpose", description="E2E Proposal test",
     prompt="mcp__oda_ontology__create_proposal → approve → execute")
```

---

## 4) V2.1.7 Features to Apply

| Feature | Application |
|---------|-------------|
| **ContextBudgetManager** | ULTRATHINK mode (64K), check before delegation |
| **TaskDecomposer** | Large scope detection → auto split |
| **Parallel Execution** | Track A ∥ Track B with `run_in_background=True` |
| **Resume Parameter** | Store agent IDs in plan file for Auto-Compact recovery |
| **Plan File Persistence** | `.agent/plans/kb-oda-dual-track-v2.1.7.md` |
| **TodoWrite** | Min 3 tasks for progress tracking |

---

## 5) 완료 기준

### Track A
- [ ] Dev/Delta 언어/스택 네트워크 근거 기반 KB 반영
- [ ] 외부자료 요약 repo 저장 (URL+조회일+신뢰도)

### Track B
- [ ] SubModule E2E 동작: 정의→검증→제안→승인→적용
- [ ] LLM-독립 검증 완료

### Common
- [ ] 모든 Stage에서 evidence 포함
- [ ] 추측/미검증 주장 없음

---

## Quick Start

```python
# 1. Initialize (read plan file if exists)
Read(".agent/plans/kb-oda-dual-track-v2.1.7.md")

# 2. TodoWrite setup
TodoWrite(todos=[
    {"content": "Track A: KB System", "activeForm": "Building KB", "status": "in_progress"},
    {"content": "Track B: ODA Quality", "activeForm": "Auditing ODA", "status": "in_progress"},
    {"content": "Final Report", "activeForm": "Generating report", "status": "pending"}
])

# 3. Launch parallel tracks
# Track A Stage A + Track B Stage A simultaneously
```

---

> **Reference:** Full detailed prompt at `.agent/plans/kb-oda-dual-track-v2.1.7.md`

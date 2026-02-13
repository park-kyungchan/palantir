# ADR-001: Team Memory (TEAM-MEMORY.md)

**Status:** PROPOSED | **Date:** 2026-02-07 | **Author:** architect-1

---

## 1. Context

DIA v3.0에서 teammates는 서로의 발견을 공유하려면 반드시 Lead를 경유해야 합니다.
Phase 6에서 4명의 implementer가 병렬 작업 시, implementer-1이 발견한 코드 패턴을
implementer-2가 알기까지 Lead relay + SendMessage + IDLE-WAKE 사이클이 필요합니다.
이는 지식 사일로를 형성하고 중복 작업/충돌을 유발할 수 있습니다.

## 2. Decision

**세션 범위 공유 파일 `TEAM-MEMORY.md`를 도입합니다.**

- 위치: `.agent/teams/{session-id}/TEAM-MEMORY.md`
- 구조: Section-per-role (## Lead, ## researcher-1, ## implementer-1, ...)
- 접근: Edit tool로 자기 섹션만 수정. Write tool 금지 (최초 Lead 생성 제외).
- 수명: TeamCreate → TeamDelete (세션 한정)

## 3. Alternatives Considered

### Alternative A: Lead Relay Only (현행 유지)
- 모든 knowledge sharing이 Lead를 경유
- **장점:** 단순, 동시성 위험 없음
- **단점:** Lead context 부담 증가, 실시간 공유 불가, Phase 6 병렬 작업 시 지연
- **기각 사유:** Lead 병목이 scalability를 제한

### Alternative B: Task Metadata 활용
- TaskUpdate metadata에 findings를 key-value로 저장
- **장점:** 기존 인프라 활용
- **단점:** TaskCreate/TaskUpdate는 Lead 전용 (teammates read-only), metadata는 비구조화, 검색 불가
- **기각 사유:** DIA Task API sovereignty와 충돌

### Alternative C: Section-per-role Shared File (채택)
- 공유 파일에 역할별 섹션으로 분리
- **장점:** 직접 공유, Edit 동시성 안전, 구조화된 태그
- **단점:** Edit race condition (LOW 확률), 새 인프라 추가
- **채택 사유:** implementer 병렬 작업에서 최대 가치, Edit 안전성 검증 완료

## 4. File Structure Specification

```markdown
# TEAM-MEMORY — {feature-name}

## Meta
- Created: {YYYY-MM-DD}
- Session: {session-id}
- GC Version: GC-v{N}

## Lead
- [Decision] {timestamp} {content}
- [Gate] {timestamp} Phase {N} PASSED
- ...

## researcher-1
- [Finding] {content}
- [Warning] {content}
- ...

## implementer-1
- [Pattern] {content}
- [Dependency] {content}
- [Conflict] {content}
- ...

## implementer-2
- [Pattern] {content}
- ...
```

### Section Header Convention
- `## {role-id}` — 정확히 teammate name과 일치 (e.g., `## researcher-1`, `## implementer-2`)
- Lead 섹션: `## Lead` (항상 존재)
- 새 teammate spawn 시: Lead가 Edit로 새 섹션 추가

## 5. Access Control Rules

### Tool-Based Access Matrix

| Agent Type | Has Edit? | TEAM-MEMORY Access | Mechanism |
|-----------|-----------|-------------------|-----------|
| implementer | Yes | Direct Edit (own section) | Edit tool |
| integrator | Yes | Direct Edit (own section) | Edit tool |
| architect | No (Write only) | Lead relay | SendMessage → Lead writes |
| tester | No (Write only) | Lead relay | SendMessage → Lead writes |
| researcher | No (neither) | Lead relay | SendMessage → Lead writes |
| devils-advocate | No (neither) | Lead relay | SendMessage → Lead writes |
| Lead | N/A (delegate) | Full access (Write initial, Edit curation) | Both tools |

**Key Architecture Decision:** Only implementer and integrator have Edit tool access.
Other agents contribute via existing SendMessage → Lead relay pattern.
This is naturally aligned with the primary use case: Phase 6 (multiple implementers) is where
direct real-time sharing provides the highest value.

### Edit Rules
1. old_string에 **반드시** section header (`## {role-id}`) 포함 — 고유성 보장
2. 자기 섹션만 Edit — 다른 teammate의 섹션 Edit은 프로토콜 위반
3. Write tool 사용 **금지** (last-write-wins → 데이터 소실 위험)
4. 빈 섹션에 첫 항목 추가: `old_string="## {role-id}\n"` → `new_string="## {role-id}\n- [Tag] content\n"`

### Lead Curation Rules
1. **Phase Gate 통과 시:** 해당 phase의 stale 정보에 `[ARCHIVED]` prefix
2. **GC version 업 시:** Meta 섹션의 `GC Version` 업데이트
3. **Teammate 교체 시:** 이전 teammate 섹션에 `[REPLACED]` prefix (삭제하지 않음)
4. **파일 500줄 초과 시:** `[ARCHIVED]` 항목 삭제로 정리

## 6. Content Taxonomy (7 Tags)

| Tag | Purpose | Example |
|-----|---------|---------|
| [Finding] | 사실 발견 | API v2에서 rate limit 100/min 확인 |
| [Pattern] | 코드/설계 패턴 | auth 모듈은 singleton 패턴 |
| [Decision] | 결정 사항 | Vitest 대신 Jest 사용 결정 |
| [Warning] | 주의/위험 사항 | breaking change in v3.0 migration |
| [Dependency] | 의존성 정보 | lodash@4.17 필수 (이전 버전 불가) |
| [Conflict] | 잠재적 충돌 | implementer-1 auth path 변경 → import 충돌 |
| [Question] | 미해결 질문 | Lead 확인 필요: API endpoint 변경 여부 |

### Content NOT for Team Memory
- Task 진행 상태 → Task API (TaskList/TaskGet)
- 코드 변경 상세 → L3-full/ output
- 개인 학습/범용 패턴 → `memory: user` (agent-memory/)
- Gate 결과 → gate-record.yaml

## 7. Lifecycle

```
TeamCreate → Lead creates TEAM-MEMORY.md (Write tool, 1회)
  ↓
Phase N → Teammates read + Edit own sections
  ↓
Gate N → Lead curates (ARCHIVED stale items, update GC version)
  ↓
Phase N+1 → Repeat
  ↓
TeamDelete → TEAM-MEMORY.md deleted with team directory
```

## 8. Relationship to Existing Knowledge Systems

| System | Scope | Lifetime | Owner |
|--------|-------|----------|-------|
| TEAM-MEMORY.md | Team session | TeamCreate → TeamDelete | Section-per-role |
| L1/L2/L3 | Task output | Task duration (may persist) | Teammate-specific dir |
| memory: user | Agent type | Permanent (cross-session) | Per-agent-type |
| global-context.md | Pipeline | Session | Lead only |

## 9. Consequences

### Positive
- Implementers can share discoveries in real-time without Lead relay
- Structured tags enable quick scanning for relevant information
- Section-per-role prevents concurrent write conflicts
- Curation protocol prevents unbounded file growth

### Negative
- 4 out of 6 agent types still require Lead relay (no Edit tool)
- New protocol to learn for all agents
- File size management overhead for Lead (curation)

### Neutral
- Does not replace L1/L2/L3 (complementary, not competing)
- Does not replace memory:user (different scope and lifetime)

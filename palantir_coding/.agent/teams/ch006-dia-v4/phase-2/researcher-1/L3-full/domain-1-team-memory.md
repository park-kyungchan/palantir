# Domain 1: Team Memory (TEAM-MEMORY.md) — Deep Research

## 1. Concept Definition

**Team Memory** = 팀 세션 내 실시간 공유 지식 저장소.
각 teammate가 발견한 패턴, 결정, 경고, 의존성 정보를 공유하여
다른 teammate가 중복 작업을 피하고 일관된 맥락을 유지하도록 함.

## 2. File Location & Lifecycle

```
.agent/teams/{session-id}/TEAM-MEMORY.md
```

- **생성:** TeamCreate 직후 Lead가 초기 구조 생성 (Write tool — 1회성)
- **업데이트:** 작업 중 teammate가 Edit tool로 자기 섹션 수정
- **큐레이션:** Gate 시점에 Lead가 stale 정보 정리
- **소멸:** TeamDelete 시 팀 디렉토리와 함께 삭제

## 3. Section-per-Role Structure

```markdown
# TEAM-MEMORY — {feature-name}

## Meta
- Created: {date}
- Session: {session-id}
- GC Version: GC-v{N}

## Lead
- [Gate 1 PASSED] Phase 1 Discovery 완료
- [Decision] implementer 2명 병렬 배치
- ...

## researcher-1
- [Finding] API endpoint /users는 pagination 미지원
- [Warning] rate limit 100/min
- ...

## implementer-1
- [Pattern] src/auth/ 모듈은 singleton 패턴 사용
- [Dependency] lodash@4.17 — 이전 버전 불가
- ...

## implementer-2
- [Pattern] src/api/ 모듈은 factory 패턴
- [Conflict] implementer-1의 auth module import path 변경 주의
- ...
```

## 4. Concurrency Safety Analysis

### Edit Tool Behavior

Edit tool의 작동 방식:
1. 파일에서 `old_string`을 검색
2. **정확히 일치하는 문자열**을 `new_string`으로 교체
3. `old_string`이 파일 내에서 **고유**해야 함 (비고유 시 실패)
4. 교체는 원자적 — 파일의 나머지 부분은 영향 없음

**Section-per-role에서의 안전성:**
- Teammate A가 `## researcher-1` 섹션 내의 텍스트를 Edit할 때
- Teammate B가 `## implementer-1` 섹션 내의 텍스트를 동시에 Edit해도
- old_string이 다른 섹션에 있으므로 **충돌 없음**
- 단, 같은 old_string이 여러 섹션에 존재하면 실패 → **섹션 헤더를 old_string에 포함** 권장

### Write Tool 위험

Write tool은 전체 파일을 덮어쓰기:
1. Teammate A가 파일 전체를 Read
2. Teammate B가 파일 전체를 Read
3. A가 수정 후 Write → 성공
4. B가 수정 후 Write → **A의 변경 소실** (last-write-wins)

**결론:** TEAM-MEMORY.md에 Write tool 사용 **금지** (최초 생성 제외).

### Race Condition Mitigation

| 시나리오 | 위험도 | 대응 |
|---------|--------|------|
| 서로 다른 섹션 동시 Edit | LOW | 안전 — old_string이 다름 |
| 같은 섹션 동시 Edit | HIGH | 발생 불가 — 1 role = 1 section |
| Edit + Write 동시 | CRITICAL | Write 금지로 방지 |
| 빈 섹션에 첫 내용 추가 | MEDIUM | Edit with old_string="## {role}\n" |

## 5. Content Guidelines

### 무엇을 기록하는가

| 태그 | 용도 | 예시 |
|------|------|------|
| [Finding] | 사실 발견 | API가 v2에서 deprecated |
| [Pattern] | 코드/설계 패턴 | singleton, factory 등 |
| [Decision] | 결정 사항 | Jest 대신 Vitest 사용 |
| [Warning] | 주의/위험 | rate limit, breaking change |
| [Dependency] | 의존성 정보 | library@version |
| [Conflict] | 잠재적 충돌 | 파일 경계, 인터페이스 불일치 |
| [Question] | 미해결 질문 | Lead에게 확인 필요 |

### 무엇을 기록하지 않는가
- Task 진행 상태 (→ Task API)
- 코드 변경 상세 (→ L3-full/)
- 개인 학습 (→ memory: user)
- Gate 결과 (→ gate-record.yaml)

## 6. Lead Curation Protocol

### 타이밍
1. **Phase Gate 통과 직후:** 해당 phase의 stale 정보 [ARCHIVED] 태그
2. **GC version 업 시:** Meta 섹션의 GC Version 업데이트
3. **Teammate 교체 시:** 이전 teammate 섹션 보존 (접두사 [REPLACED] 추가)
4. **세션 중반:** 500줄 초과 시 Lead가 정리 (오래된 [ARCHIVED] 삭제)

### Curation Format
```markdown
## researcher-1 [ARCHIVED — Phase 2 Complete]
- ~~[Finding] API endpoint /users는 pagination 미지원~~ → Phase 3에서 해결
```

## 7. Agent .md Integration Points

각 agent .md에 추가할 내용:
- Team Memory 읽기: 작업 시작 전 TEAM-MEMORY.md 전체 읽기
- Team Memory 쓰기: 자기 섹션에 Edit tool로만 쓰기
- Write 금지: TEAM-MEMORY.md에 Write tool 사용 금지
- 태그 규칙: [Finding], [Pattern], [Decision], [Warning], [Dependency], [Conflict], [Question]

## 8. CLAUDE.md Integration Points

새 섹션 추가 필요:
```markdown
## N. Team Memory Protocol

### TEAM-MEMORY.md
- Location: `.agent/teams/{session-id}/TEAM-MEMORY.md`
- Purpose: 실시간 팀 내 knowledge sharing
- Structure: Section-per-role (## Lead, ## {role}-{id})

### Rules
- Read: 전 teammate 자유 (작업 시작 전 필수 읽기)
- Write: Lead만 최초 생성 시 Write tool 사용
- Edit: 각 teammate는 자기 섹션만 Edit tool로 수정
- Tags: [Finding], [Pattern], [Decision], [Warning], [Dependency], [Conflict], [Question]
- Lead Curation: Gate 시점에 stale 정보 정리
```

# Domain 2: Context Delta Protocol — Deep Research

## 1. Problem Statement

DIA v3.0에서 [CONTEXT-UPDATE]는 Lead가 변경사항을 텍스트로 설명하는 비구조화 메시지.
GC 파일이 커질수록 full re-injection의 토큰 비용이 증가.
Delta protocol은 변경된 부분만 전달하여 토큰을 절감.

## 2. GC File Size Measurement (실측)

### ch001-ldap/global-context.md
- 줄 수: 50줄
- 구조: YAML front matter (6줄) + 7 섹션
- 추정 토큰: ~1,000 tokens
- 특성: 단일 구현 작업, 간결한 scope

### agent-teams-write-plan/global-context.md
- 줄 수: 190줄
- 구조: YAML front matter (6줄) + 15 섹션
- 추정 토큰: ~3,800 tokens
- 특성: Phase 1-3 누적, architecture decisions 10개, research findings 상세

### execution-pipeline/global-context.md
- 줄 수: 177줄
- 구조: YAML front matter (6줄) + 14 섹션
- 추정 토큰: ~3,500 tokens
- 특성: Phase 1-3 누적, 8 architecture decisions, research findings + gaps

### ch006-dia-v4/global-context.md (현재 세션)
- 줄 수: ~30줄
- 구조: 초기 Phase 1 수준
- 추정 토큰: ~600 tokens

### 통계

| Metric | Value |
|--------|-------|
| Min | 30줄 (~600 tokens) |
| Max | 190줄 (~3,800 tokens) |
| Median | ~130줄 (~2,600 tokens) |
| Average | ~112줄 (~2,200 tokens) |

## 3. Current Protocol (v3.0)

### [CONTEXT-UPDATE] 현재 동작
```
[CONTEXT-UPDATE] GC-v{N} | Delta: {free-text description}
```

문제점:
1. Delta 포맷이 비구조화 — teammate가 정확히 무엇이 변했는지 파악 어려움
2. Full GC 재전송 여부가 모호 — 일부는 full, 일부는 summary
3. Version gap 발생 시 대응 방법 미정의

### [ACK-UPDATE] 현재 동작
```
[ACK-UPDATE] GC-v{ver} received. Impact: {assessment}
```

문제점:
1. Delta 적용 결과 확인 없음
2. Impact 평가가 주관적

## 4. Proposed Delta Protocol (v4.0)

### Delta Format

```
[CONTEXT-UPDATE] GC-v{old} → GC-v{new}

## Delta
- ADDED §{section}: {key}: {value}
- CHANGED §{section}: {key}: {old_value} → {new_value}
- REMOVED §{section}: {key}
- REPLACED §{section}: (see GC-v{new} for full content)

## Impact Assessment
- Affected teammates: {list}
- Required actions: {list}
```

### ACK Format (Enhanced)

```
[ACK-UPDATE] GC-v{new} received.
- Delta items applied: {count}/{total}
- Impact on my work: {NONE | description}
- Action taken: {CONTINUE | PAUSE | request clarification}
```

### Full Fallback Conditions

| Condition | Trigger | Action |
|-----------|---------|--------|
| Version gap > 1 | Teammate at v3, GC now v5 | Full GC re-injection |
| Compact recovery | Teammate reports CONTEXT_LOST | Full GC + task-context |
| Initial spawn | IP-001 (first directive) | Full GC + task-context |
| Major restructure | Delta > 50% of GC content | Full GC re-injection |
| Teammate request | Explicit "need full context" | Full GC re-injection |

### Token Savings Estimate

| Scenario | Full Injection | Delta Only | Savings |
|----------|---------------|------------|---------|
| 1 section change | ~2,600 tokens | ~200 tokens | 92% |
| 2-3 sections change | ~2,600 tokens | ~500 tokens | 81% |
| Status update only | ~2,600 tokens | ~100 tokens | 96% |
| Phase transition | ~2,600 tokens | ~800 tokens | 69% |
| Major restructure | ~2,600 tokens | N/A (full) | 0% |

**평균 절감:** 70-90% per [CONTEXT-UPDATE] message

### Multi-teammate Scenario

4명의 implementer가 동시 작업 중 GC 업데이트 시:
- v3.0: 4 × 2,600 = 10,400 tokens
- v4.0 delta: 4 × 300 = 1,200 tokens
- 절감: ~9,200 tokens (88%)

## 5. Implementation Points

### CLAUDE.md 변경
- §4 Communication Protocol: delta format 추가
- §6 DIA Engine: delta 계산 절차, fallback 조건
- [PERMANENT]: delta 포맷 compliance duty 추가

### task-api-guideline.md 변경
- §11 CIP 섹션: delta vs full injection 조건 명시
- Injection Points 테이블: IP-003, IP-004에 delta 우선 적용 표시

### Orchestration Plan Tracking
- 기존: teammate별 GC 수신 버전 추적
- 추가: 마지막 delta 전송 시점, 누적 delta 크기

## 6. Edge Cases

### Rapid GC Updates
Gate 내에서 연속 GC 업데이트 시 (v5→v6→v7):
- Teammate가 v5→v6 delta 처리 중 v7 발행
- 대응: v6→v7 delta를 별도 전송 (큐잉)
- v5 teammate에게 v7 직접 전달 시: version gap > 1 → full fallback

### Partial ACK
Teammate가 delta의 일부만 이해한 경우:
- ACK에 "Delta items applied: 2/3, unclear: §Decisions D-7" 표기
- Lead가 해당 항목 재설명 또는 full fallback 판단

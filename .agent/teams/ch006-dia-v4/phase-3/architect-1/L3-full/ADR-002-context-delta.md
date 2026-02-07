# ADR-002: Context Delta Protocol

**Status:** PROPOSED | **Date:** 2026-02-07 | **Author:** architect-1

---

## 1. Context

DIA v3.0에서 [CONTEXT-UPDATE]는 비구조화 텍스트 설명이거나 full GC 재전송입니다.
GC 파일 크기가 중앙값 ~130줄 (~2,600 tokens)인 상태에서, 1-2 섹션만 변경해도
full injection을 보내면 4명의 implementer에게 4 × 2,600 = 10,400 tokens가 소비됩니다.
구조화된 delta는 이를 4 × 300 = 1,200 tokens으로 줄일 수 있습니다 (88% 절감).

## 2. Decision

**구조화된 ADDED/CHANGED/REMOVED delta 포맷을 도입합니다.**

- [CONTEXT-UPDATE] 메시지에 delta를 inline으로 포함
- 5개 조건에서 full GC fallback
- Enhanced [ACK-UPDATE] 포맷으로 delta 적용 결과 보고

## 3. Alternatives Considered

### Alternative A: Full Re-injection Always (현행 유지)
- 모든 [CONTEXT-UPDATE]에 full GC 전송
- **장점:** 단순, 일관성 보장
- **단점:** 토큰 낭비 (10,400 tokens/update for 4 teammates)
- **기각 사유:** 비효율적, Lead context window 압박

### Alternative B: Unstructured Text Delta (v3.0 현재)
- `[CONTEXT-UPDATE] GC-v{N} | Delta: {free text}`
- **장점:** 유연
- **단점:** teammate가 무엇이 변했는지 정확히 파악 어려움, ACK 검증 불가
- **기각 사유:** 비구조화 → 오해/누락 위험

### Alternative C: Structured Delta Format (채택)
- ADDED/CHANGED/REMOVED + section reference
- **장점:** 명확, 토큰 효율, ACK에서 적용 결과 검증 가능
- **단점:** Lead가 delta 생성 부담, fallback 로직 필요
- **채택 사유:** 70-90% 토큰 절감, 구조화된 ACK로 이해 검증 강화

## 4. Delta Format Specification

### [CONTEXT-UPDATE] v4.0 Format

```
[CONTEXT-UPDATE] GC-v{old} → GC-v{new}

## Delta
- ADDED §{section}: {key}: {value}
- CHANGED §{section}: {key}: {old_value} → {new_value}
- REMOVED §{section}: {key}
- REPLACED §{section}: (full section content below)
  {content}

## Impact Assessment
- Affected teammates: {role-id list}
- Required actions: {NONE | PAUSE | re-read specific section}
```

### Operation Types

| Operation | Syntax | Use Case |
|-----------|--------|----------|
| ADDED | `ADDED §Decisions: D-8: Use Redis for caching` | 새 항목 추가 |
| CHANGED | `CHANGED §Scope: approach: waterfall → agile` | 기존 값 변경 |
| REMOVED | `REMOVED §Scope: out_of_scope: UI testing` | 항목 삭제 |
| REPLACED | `REPLACED §Research: (see below)` + full content | 섹션 전면 교체 |

### Section References
- §로 GC 파일의 Markdown 헤더를 참조: `§Scope`, `§Decisions`, `§Phase 2 Research Summary`
- 중첩 참조: `§Decisions.D-5`, `§Scope.in_scope`

## 5. Enhanced [ACK-UPDATE] Format

### v4.0 ACK Format

```
[ACK-UPDATE] GC-v{new} received.
- Delta items applied: {applied_count}/{total_count}
- Impact on my work: {NONE | description}
- Action taken: {CONTINUE | PAUSE | NEED_CLARIFICATION}
- Unclear items: {§ref list, or "none"}
```

### ACK Validation by Lead
| ACK Content | Lead Action |
|-------------|-------------|
| applied == total, CONTINUE | Proceed — context aligned |
| applied < total, NEED_CLARIFICATION | Re-send unclear items or full fallback |
| PAUSE | Acknowledge, provide guidance |
| No ACK within reasonable time | Ping teammate, check for compact |

## 6. Full Fallback Decision Tree

```
Lead prepares [CONTEXT-UPDATE]:
  │
  ├─ Is teammate in CONTEXT_LOST state? ──→ YES → FULL injection (IP-005)
  │
  ├─ Is this initial spawn (IP-001)? ──→ YES → FULL injection
  │
  ├─ teammate.gc_version < current_gc_version - 1? ──→ YES → FULL injection (gap >1)
  │
  ├─ delta_items > 50% of GC sections? ──→ YES → FULL injection (major restructure)
  │
  ├─ teammate explicitly requested full? ──→ YES → FULL injection
  │
  └─ ELSE → DELTA injection
```

### 5 Fallback Conditions (exhaustive)

| # | Condition | Trigger | Rationale |
|---|-----------|---------|-----------|
| FC-1 | Version gap > 1 | teammate at v3, current v5 | Intermediate deltas unavailable |
| FC-2 | Compact recovery | [STATUS] CONTEXT_LOST | All in-memory context destroyed |
| FC-3 | Initial spawn | IP-001 directive | No prior context exists |
| FC-4 | Major restructure | Delta > 50% of GC | Delta larger than full — no savings |
| FC-5 | Explicit request | Teammate ACK with NEED_CLARIFICATION | Teammate self-assessed confusion |

## 7. Token Savings Analysis

### Per-Update Savings

| Scenario | Full Cost | Delta Cost | Savings |
|----------|-----------|------------|---------|
| 1 decision added | ~2,600 tok | ~200 tok | 92% |
| 2-3 sections changed | ~2,600 tok | ~500 tok | 81% |
| Status update only | ~2,600 tok | ~100 tok | 96% |
| Phase transition | ~2,600 tok | ~800 tok | 69% |
| Major restructure (>50%) | ~2,600 tok | N/A (full) | 0% |

### Multi-Teammate Scenario (Phase 6, 4 implementers)

| Metric | v3.0 (Full) | v4.0 (Delta) | Savings |
|--------|-------------|-------------|---------|
| Single update | 10,400 tok | 1,200 tok | 88% |
| 3 updates/session | 31,200 tok | 3,600 tok | 88% |
| With fallback (1/3) | 31,200 tok | 6,400 tok | 79% |

## 8. Edge Cases

### Rapid Sequential Updates (v5→v6→v7)
- Teammate processing v5→v6 delta when v6→v7 published
- Lead sends v6→v7 as separate delta (queued delivery)
- If teammate was at v5 and v7 published: version gap = 2 → FC-1 → full injection
- **Rule:** Lead checks teammate's confirmed version (last ACK), not sent version

### Partial ACK
- Teammate reports `applied: 2/3, unclear: §Decisions.D-7`
- Lead re-sends unclear item with additional context, OR full fallback if >50% unclear

### Delta During Gate Evaluation
- Lead should NOT send delta during active gate evaluation
- Gate completion first, then delta if needed
- **Rule:** Gate evaluation freezes GC version. Delta only after gate conclusion.

## 9. Implementation Points

### Lead's Delta Generation Process
1. Edit global-context.md (make the actual changes)
2. Note which sections were ADDED/CHANGED/REMOVED
3. Construct delta message from awareness of changes
4. Check each active teammate's confirmed GC version (from orchestration-plan.md)
5. For each teammate: evaluate fallback decision tree → delta or full
6. Send [CONTEXT-UPDATE] via SendMessage
7. Track sent version in orchestration-plan.md

### orchestration-plan.md Tracking Enhancement
Current: `teammate_gc_versions: {role-id: confirmed_version}`
Added: `teammate_gc_last_delta: {role-id: {sent_version, delta_size, timestamp}}`

## 10. Consequences

### Positive
- 70-90% token savings per context update
- Structured format enables ACK-based verification
- Clear fallback logic prevents stale-context work
- Reduced Lead context window pressure

### Negative
- Lead must generate accurate deltas (LLM reasoning overhead)
- 5 fallback conditions add complexity to Lead's decision flow
- If Lead miscalculates delta, teammate gets partial/wrong context

### Neutral
- Full injection remains the safety net for all edge cases
- Delta protocol is additive — doesn't break any existing mechanism

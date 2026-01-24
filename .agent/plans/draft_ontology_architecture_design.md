# Draft: Ontology-First Development 아키텍처 설계 문서

> **Version:** 1.1 | **Status:** IN_PROGRESS | **Date:** 2026-01-23
> **Auto-Compact Safe:** This file persists across context compaction
> **Teleport Ready:** 웹 세션으로 전송 준비 완료

---

## INDEX

### 요구사항 요약
Main Agent가 **명시적 커맨드 호출** 시 작업을 Ontology Layer로 타입 분해하는 "Ontology-First Development" 패턴 구현

### Complexity
- **예상 복잡도:** Large (6개 타입 × 커맨드/스킬 세트)
- **영향 파일:** ~12개 (커맨드 6 + 스킬 6)
- **상세:** [파일 분석](#file-analysis)

### Q&A 핵심
1. **Q:** Rubix란? → **A:** Kubernetes 기반 오토스케일링 엔진, Ontology와 별개 계층
2. **Q:** 적용 범위? → **A:** 명시적 커맨드 호출 시에만 (/objecttype, /linktype 등)
3. **Q:** 연구 진행 방식? → **A:** /teleport out으로 웹에서 계속

### 추천 접근법
Ontology-First Development 패턴:
```
사용자: /objecttype "User"
     ↓
커맨드가 ObjectType 스키마로 정의 생성
     ↓
JSON Schema 검증 + Registry 등록
     ↓
LLM Exporter로 프롬프트용 포맷 생성
```

### 리스크
- Ontology-Definition 패키지와 Claude 통합 복잡도
- JSON Schema 4,389줄 검증 성능
- 타입 간 상호 참조 (LinkType → ObjectType)

### 다음 단계
`/teleport out` 실행 → 웹에서 상세 설계 계속

---

## DETAIL: Q&A 전체 로그 {#qa-log}

### Round 1 (2026-01-23 21:43)
**Q:** 아키텍처 설계의 주요 목표?
**A:** Main Agent가 모든 작업을 Ontology Layer로 먼저 타입 분해하도록 고도화

### Round 2 (2026-01-23 21:44)
**Q:** Rubix란?
**A:** Palantir의 Kubernetes 기반 오토스케일링 인프라 엔진. Ontology Layer와는 별개 계층 (Compute Layer)

### Round 3 (2026-01-23 21:45)
**Q:** Ontology-First 패턴 적용 범위?
**A:** 커맨드/스킬 생성 후 명시적 사용 시에만

**Q:** 연구 진행 방식?
**A:** /teleport out으로 웹에서 계속

---

## DETAIL: 요구사항 상세 {#requirements}

### 기능 요구사항
- FR1: ObjectType 커맨드/스킬 세트 (`/objecttype`)
- FR2: LinkType 커맨드/스킬 세트 (`/linktype`)
- FR3: ActionType 커맨드/스킬 세트 (`/actiontype`)
- FR4: Interface 커맨드/스킬 세트 (`/interface`)
- FR5: ValueType 커맨드/스킬 세트 (`/valuetype`)
- FR6: Property 커맨드/스킬 세트 (`/property`)

### 비기능 요구사항
- NFR1: JSON Schema Draft 2020-12 호환
- NFR2: 스레드-안전 Registry 통합
- NFR3: LLM Exporter로 프롬프트 생성 지원

---

## DETAIL: 파일 분석 결과 {#file-analysis}

### Ontology-Definition 구조

| 디렉토리 | 파일 수 | 역할 |
|----------|---------|------|
| `/core` | 2 | 기본 클래스, 열거형 |
| `/types` | 5 | ObjectType, LinkType, ActionType, Interface, ValueType |
| `/schemas` | 6 | JSON Schema (4,389줄) |
| `/security` | 2 | 보안 정책 (P1-CRITICAL) |
| `/registry` | 1 | 싱글톤 레지스트리 |
| `/export` | 3 | Foundry, JSON Schema, LLM |

### 생성할 커맨드/스킬

| 타입 | 커맨드 | 스킬 |
|------|--------|------|
| ObjectType | `.claude/commands/objecttype.md` | `.claude/skills/objecttype.md` |
| LinkType | `.claude/commands/linktype.md` | `.claude/skills/linktype.md` |
| ActionType | `.claude/commands/actiontype.md` | `.claude/skills/actiontype.md` |
| Interface | `.claude/commands/interface.md` | `.claude/skills/interface.md` |
| ValueType | `.claude/commands/valuetype.md` | `.claude/skills/valuetype.md` |
| Property | `.claude/commands/property.md` | `.claude/skills/property.md` |

---

## DETAIL: 리스크 분석 {#risk-analysis}

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 스키마 복잡도 | High | Wizard 형식 Q&A로 단계별 진행 |
| 타입 참조 순서 | Medium | Property → ObjectType → LinkType 순서 강제 |
| Registry 성능 | Low | 스레드-안전 싱글톤 이미 구현됨 |
| 보안 정책 통합 | Medium | P1-CRITICAL 필드는 선택적 고급 옵션 |

---

## DETAIL: Teleport 정보 {#teleport-info}

### 세션 전송 준비
- **현재 상태:** Q&A 3라운드 완료
- **저장된 파일:**
  - `.agent/plans/draft_ontology_architecture_design.md` (이 파일)
  - `.agent/outputs/explore/ont-expl-2026-01-23.md` (L3 상세 분석)
- **Git 상태:** feature/v2.2.0-ontology-schema-commands 브랜치

### 웹에서 계속할 작업
1. 각 타입별 커맨드/스킬 상세 설계
2. JSON Schema 기반 Wizard Q&A 흐름 정의
3. Registry 통합 인터페이스 설계
4. LLM Exporter 활용 방안

---

## Metadata

- Created: 2026-01-23 21:42
- Last Updated: 2026-01-23 21:46
- Q&A Rounds: 3
- Status: IN_PROGRESS (Teleport Ready)

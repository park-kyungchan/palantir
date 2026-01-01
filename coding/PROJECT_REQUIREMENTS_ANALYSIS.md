# 프로젝트 요구사항 명세서 (Project Requirements Specification)
**프로젝트명:** Palantir FDE Learning System
**분석 일자:** 2026-01-01
**분석가:** Gemini 3.0 Pro (Orion Orchestrator)

## 1. 개요 (Overview)
본 프로젝트는 Palantir의 **FDE (Forward Deployed Engineer)** 직군 지원자를 위한 **지능형 인터뷰 준비 시스템**입니다. 단순한 문제 은행이 아닌, 학습자의 실력을 정밀하게 추적하고 최적의 학습 경로를 추천하는 **적응형 학습(Adaptive Learning)** 플랫폼을 구축하는 것이 핵심 목표입니다.

## 2. 핵심 사용자 요구사항 (User Requirements)

### 2.1. 학습 숙련도 추적 (Mastery Tracking)
- **요구사항:** 학습자가 특정 개념을 이해했는지 단순히 O/X로 판단하지 않고, 확률적으로 추정해야 함.
- **구현 로직:** **BKT (Bayesian Knowledge Tracing)** 알고리즘 적용.
    - 초기 학습률(P_init), 학습 전이율(P_learn), 실수 확률(P_slip), 추측 확률(P_guess)을 고려하여 `Mastery Probability`를 계산.
- **코드 근거:** `palantir_fde_learning/domain/bkt.py`

### 2.2. 맞춤형 콘텐츠 추천 (Personalized Recommendation)
- **요구사항:** 학습자에게 너무 쉽거나 너무 어려운 내용이 아닌, 현재 실력에서 도전해볼 만한 최적의 콘텐츠를 추천해야 함.
- **구현 로직:** **ZPD (Zone of Proximal Development, 근접 발달 영역)** 이론 적용.
    - 선수 지식(Prerequisites)은 갖추었으나, 아직 완전히 마스터하지 못한 "Stretch Zone"의 개념을 우선순위로 추천.
- **코드 근거:** `palantir_fde_learning/application/scoping.py`

### 2.3. 지식 베이스 관리 (Knowledge Base Management)
- **요구사항:** Palantir의 기술 스택(Foundry, OSDK, Blueprint 등)에 대한 정형화된 학습 자료를 제공해야 함.
- **구현 로직:** 7단계 섹션(Overview, Prerequisites, Core, Examples 등)으로 구성된 **Markdown 파일 파싱 시스템**.
- **코드 근거:** `palantir_fde_learning/adapters/kb_reader.py`

### 2.4. 시스템 통합 및 확장성 (Integration & Scalability)
- **요구사항:** 이 시스템은 단독으로 실행될 뿐만 아니라, **Orion Orchestrator** (전사적 AI 에이전트 시스템)와 연동되어야 함.
- **구현 로직:** **ODA (Ontology-Driven Architecture)** 호환 ActionType 구현.
    - `RecordAttemptAction`: 학습 기록 저장.
    - `GetRecommendationAction`: 추천 목록 조회.
    - `SyncLearnerStateAction`: Orion 온톨로지와 상태 동기화.
- **코드 근거:** `scripts/ontology/fde_learning/actions.py`

## 3. 기술적 제약사항 (Technical Constraints)
1.  **언어 및 버전:** Python 3.10 이상.
2.  **아키텍처:** **Clean Architecture** 원칙 엄수 (Domain 계층은 외부 의존성 0).
3.  **데이터베이스:** **Async SQLite** (`aiosqlite`) 사용하여 비동기 처리 및 동시성 보장.
4.  **타입 안정성:** `Pydantic`을 활용한 엄격한 데이터 검증.

## 4. 감사(Audit) 결과 요약
- **상태:** **운영 가능 (Operational)**
- **주요 조치:** 초기 코드에서 발견된 **상태 초기화 버그(Amnesiac Bug)**를 수정함. 이제 Action 실행 시 DB에서 학습자의 이전 기록을 불러와 연속성을 보장함.

# Palantir FDE Learning System

> **목적**: 프로그래밍 완전 초보부터 Palantir DS/FDE 면접 수준까지 학습 지원
> **방식**: 애자일 동적학습 (실시간 프롬프트 기반)

---

## 디렉토리 구조

```
coding/
├── README.md              ← 이 파일 (학습 가이드)
├── SYSTEM_DIRECTIVE.md    ← AI 튜터 동작 프로토콜
└── knowledge_bases/       ← 학습 콘텐츠 (지속 확장)
    ├── 00a-00e (초급)     ← 변수, 함수, 타입 기초
    ├── 01-08 (중급)       ← React, TypeScript, Testing
    └── 09-18 (고급)       ← System Design, OSDK, Foundry
```

---

## 학습 수준 (Tier)

| Tier | 레벨 | KB 범위 | 키워드 |
|------|------|---------|--------|
| **1** | 초급 | 00a-00e | "~가 뭐야?", "기초", "처음" |
| **2** | 중급 | 01-08 | "어떻게 구현?", "패턴", "비교" |
| **3** | 고급 | 09-18 | "최적화", "아키텍처", "면접" |

---

## 사용 방법

1. **질문하기**: 어떤 프로그래밍 질문이든 자유롭게
2. **자동 라우팅**: AI가 질문 수준 감지 → 적절한 KB 참조
3. **7-Component 응답**: 모든 답변에 일관된 구조 보장
4. **Codebase-as-Curriculum**: 실제 코드베이스를 스캔해(파이썬/TS/JS/Go 혼합 가능) 질문에 맞는 학습 진입점/파일/KB 후보를 추출
5. **LLM-독립적 계약**: 어떤 LLM이든 `coding/LLM_CONTRACT.md` + `scripts/ontology/run_tutor.py` JSON 컨텍스트로 동일하게 동작

---

## 학습 프로토콜

AI 튜터는 `SYSTEM_DIRECTIVE.md`에 정의된 프로토콜을 따릅니다:

- **정확성 우선**: 모든 코드는 실행 가능해야 함
- **외부 검증**: KB + context7/tavily 교차 확인
- **1차 출처 인용**: Design Philosophy는 원저자 출처만

---

## 시작하기

**예시 질문들**:
- 초급: "변수가 뭐야?"
- 중급: "React hooks 어떻게 구현해?"
- 고급: "OSDK 아키텍처 설명해줘"

질문을 던지면 학습이 시작됩니다.

### (옵션) 코드베이스를 학습 교보재로 분해하기

```bash
python scripts/ontology/run_tutor.py --target . --user default_user --db none --prompt "이 시스템의 워크플로우를 진입점부터 학습할거야" --brief
```

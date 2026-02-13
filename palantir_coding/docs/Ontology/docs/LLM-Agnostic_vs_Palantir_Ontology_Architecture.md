# LLM-Agnostic의 개념, 한계, 그리고 Palantir Ontology/Foundry 아키텍처의 보완

> **대상**: Claude Code CLI + Opus-4.6 Agent Teams 환경에서 Palantir 모방 코드베이스를 구축하려는 개발자
> **핵심 질문**: LLM에게 "아무거나 해줘"라고 하면 왜 한계가 오는가? Ontology가 그걸 어떻게 해결하는가?

---

## 1. LLM-Agnostic이란 무엇인가?

### 1.1 정의

**LLM-Agnostic**(LLM 불가지론)이란, 특정 LLM 벤더(OpenAI, Anthropic, Google 등)에 종속되지 않도록 시스템을 설계하는 아키텍처 철학이다.

쉽게 말해:

> "어떤 LLM을 꽂아도 돌아가게 만들자"

```
┌─────────────────────────────────────────────────────────┐
│                   LLM-Agnostic 시스템                     │
│                                                         │
│   ┌──────────┐   ┌──────────┐   ┌──────────┐           │
│   │  GPT-4o  │   │ Claude   │   │ Gemini   │  ← 교체 가능│
│   └────┬─────┘   └────┬─────┘   └────┬─────┘           │
│        │              │              │                  │
│        └──────────────┼──────────────┘                  │
│                       ▼                                 │
│            ┌─────────────────────┐                      │
│            │  Unified LLM API   │  ← 추상화 레이어       │
│            │  (LiteLLM 등)      │                       │
│            └─────────┬──────────┘                       │
│                      ▼                                  │
│            ┌─────────────────────┐                      │
│            │   Your Application  │                      │
│            └─────────────────────┘                      │
└─────────────────────────────────────────────────────────┘
```

### 1.2 실제 구현 예시

```python
# LLM-Agnostic 패턴의 전형적인 코드
class LLMProvider(ABC):
    @abstractmethod
    def complete(self, prompt: str) -> str: ...

class ClaudeProvider(LLMProvider):
    def complete(self, prompt: str) -> str:
        return anthropic.messages.create(model="claude-opus-4-6", ...)

class GPTProvider(LLMProvider):
    def complete(self, prompt: str) -> str:
        return openai.chat.completions.create(model="gpt-4o", ...)

# 런타임에 교체 가능
agent = Agent(llm=ClaudeProvider())  # ← 여기만 바꾸면 됨
agent = Agent(llm=GPTProvider())     # ← 이렇게
```

### 1.3 LLM-Agnostic이 인기 있는 이유

| 이유 | 설명 |
|------|------|
| **벤더 종속 방지** | 특정 회사가 가격 인상하거나 서비스 중단해도 대응 가능 |
| **비용 최적화** | 작업 난이도에 따라 저렴한 모델과 고급 모델을 혼용 |
| **성능 비교** | A/B 테스트로 어떤 LLM이 특정 태스크에 더 나은지 평가 |
| **미래 대비** | 더 좋은 모델이 나오면 쉽게 교체 |

---

## 2. LLM-Agnostic의 근본적 한계

여기서 핵심 문제가 드러난다. LLM-Agnostic은 **"LLM을 교체하기 쉽게"** 만드는 데 집중하지만, 정작 **"LLM이 무엇을 알고, 무엇을 해야 하는지"**에 대해서는 아무 구조도 제공하지 않는다.

### 2.1 한계 전체 구조도

```
╔═══════════════════════════════════════════════════════════════════╗
║              LLM-Agnostic 시스템의 5대 한계                        ║
╠═══════════════════════════════════════════════════════════════════╣
║                                                                   ║
║  ①  컨텍스트 붕괴       "대화가 길어지면 앞의 내용을 잊어버린다"      ║
║      (Context Collapse)                                           ║
║                                                                   ║
║  ②  도메인 무지          "회사의 비즈니스 규칙을 모른다"              ║
║      (Domain Ignorance)                                           ║
║                                                                   ║
║  ③  행동 비결정성        "같은 질문에 매번 다른 답을 한다"            ║
║      (Action Non-determinism)                                     ║
║                                                                   ║
║  ④  에이전트 간 단절     "에이전트끼리 소통할 공통 언어가 없다"        ║
║      (Agent Isolation)                                            ║
║                                                                   ║
║  ⑤  검증 불가능성        "LLM의 출력이 맞는지 검증할 기준이 없다"     ║
║      (Unverifiability)                                            ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

### 2.2 한계 ①: 컨텍스트 붕괴 (Context Collapse)

LLM은 **무상태(stateless)**다. 매 요청마다 컨텍스트 윈도우를 새로 채워야 한다.

```
요청 1:  "User 테이블에 age 컬럼 추가해줘"
         → LLM이 잘 수행 ✓

요청 2:  "그 컬럼에 validation 넣어줘"
         → LLM: "어떤 컬럼이요?" ✗  ← 이전 대화를 모른다

요청 30: "아까 만든 전체 스키마 보여줘"
         → LLM: (컨텍스트 윈도우 초과) ✗  ← 물리적으로 불가능
```

**왜 문제인가?**

Agent Teams에서 에이전트 A가 한 작업의 결과를 에이전트 B가 이어받아야 하는데, 그 "결과"를 전달할 구조화된 방법이 없다. 모든 것이 자연어 텍스트 덩어리로만 전달된다.

```
┌───────────────┐    자연어 텍스트     ┌───────────────┐
│   Agent A     │ ─────────────────→  │   Agent B     │
│ "DB 스키마를   │   "User 테이블에     │  "뭔 소리야?   │
│  설계했어"     │    age가 있고..."    │   구조화된 건   │
└───────────────┘                     │   없어?"       │
                                      └───────────────┘
         ↑ 정보 손실 (Lossy Transfer) 발생!
```

### 2.3 한계 ②: 도메인 무지 (Domain Ignorance)

LLM은 "일반 지능"이지, "당신 회사의 비즈니스 전문가"가 아니다.

```
예시: 금융 도메인

  사람: "이 고객의 KYC 상태를 확인해줘"

  ┌─────────────────────────────────────────────────┐
  │  LLM-Agnostic 시스템의 대응                       │
  │                                                  │
  │  LLM은 알고 있다:                                │
  │    ✓ KYC = Know Your Customer (일반 지식)         │
  │    ✓ 금융 규제에 관한 일반적 개념                   │
  │                                                  │
  │  LLM은 모른다:                                   │
  │    ✗ 우리 회사의 KYC 기준이 뭔지                   │
  │    ✗ 고객 데이터가 어디에 저장되어 있는지            │
  │    ✗ KYC 상태가 [PENDING|VERIFIED|REJECTED] 중    │
  │      어떤 enum인지                                │
  │    ✗ KYC 검증에 필요한 문서 목록이 뭔지             │
  │    ✗ 검증 실패 시 어떤 워크플로우를 따르는지         │
  └─────────────────────────────────────────────────┘
```

### 2.4 한계 ③: 행동 비결정성 (Action Non-determinism)

같은 입력에 대해 LLM은 매번 다른 출력을 만들 수 있다. 이것은 "창의성"이 아니라 **비즈니스 리스크**다.

```
동일한 요청: "주문 취소 처리해줘"

  실행 1:  orders 테이블에서 DELETE 실행          ← 데이터 삭제!!
  실행 2:  status를 'CANCELLED'로 UPDATE         ← 소프트 삭제
  실행 3:  cancel_order() 함수 호출              ← 표준 프로시저
  실행 4:  "주문 번호를 알려주세요"               ← 추가 질문

  4번 모두 "합리적"이지만, 비즈니스 로직상
  정답은 하나뿐이다 → 그런데 그 정답을 정의한 곳이 없다!
```

### 2.5 한계 ④: 에이전트 간 단절 (Agent Isolation)

Claude Code CLI에서 Agent Teams를 운영한다면 이 문제를 직접 느꼈을 것이다.

```
┌─────────────────────────────────────────────────────────────┐
│                현재 Agent Teams의 현실                        │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent 4  │   │
│  │ 백엔드   │  │ 프론트   │  │ 테스트   │  │ 인프라   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │              │              │              │         │
│       ▼              ▼              ▼              ▼         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              각자의 컨텍스트 윈도우 (격리됨)            │   │
│  │                                                      │   │
│  │  Agent 1은 User 모델을 class로 만들었는데              │   │
│  │  Agent 2는 같은 User를 interface로 만들고 있다          │   │
│  │  Agent 3은 둘 다 모르고 별도의 mock을 만든다            │   │
│  │  Agent 4는 DB 스키마가 뭔지 전혀 모른다                 │   │
│  │                                                      │   │
│  │  ──→  결과: 통합 시 대규모 충돌과 불일치 발생           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.6 한계 ⑤: 검증 불가능성 (Unverifiability)

LLM의 출력을 "맞다/틀리다"로 판단할 기준이 시스템에 없다.

```
  LLM 출력: "고객의 신용등급은 A+입니다"

  ┌──────────────────────────────────┐
  │  검증하려면 필요한 것들:          │
  │                                  │
  │  □ 신용등급의 유효한 값 목록       │  ← 어디에도 정의 안 됨
  │  □ 등급 산정 공식                 │  ← 어디에도 정의 안 됨
  │  □ 입력 데이터의 출처             │  ← 어디에도 정의 안 됨
  │  □ 계산 과정의 감사 추적          │  ← 어디에도 정의 안 됨
  │                                  │
  │  결론: 검증 자체가 불가능          │
  └──────────────────────────────────┘
```

### 2.7 5대 한계 요약: "빠진 것"

```
LLM-Agnostic 시스템이 가진 것       LLM-Agnostic 시스템에 빠진 것
━━━━━━━━━━━━━━━━━━━━━━━━━━       ━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ LLM 호출 추상화                  ✗ 도메인 모델 정의
✓ 프롬프트 템플릿                  ✗ 엔티티 간 관계 그래프
✓ 토큰/비용 관리                   ✗ 허용된 행동(Action) 목록
✓ 멀티모델 라우팅                  ✗ 에이전트 간 공유 상태
✓ 에러 핸들링                     ✗ 비즈니스 규칙 & 제약 조건
                                  ✗ 출력 검증 스키마
```

**이 "빠진 것"을 채우는 것이 바로 Palantir Ontology/Foundry 아키텍처다.**

---

## 3. Palantir Ontology/Foundry 아키텍처: 빠진 퍼즐 조각

### 3.1 Ontology란 무엇인가? (비유로 이해하기)

**비유: 회사의 "세계관 설정집"**

게임을 만들 때 "세계관 설정집"이 있다. 캐릭터, 아이템, 퀘스트, 규칙이 모두 정의되어 있다. 
Ontology는 **비즈니스 세계의 설정집**이다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Ontology = 세계관 설정집                    │
│                                                             │
│   "우리 비즈니스 세계에 존재하는 모든 것과                      │
│    그것들 사이의 관계와 규칙을 코드로 정의한 것"                 │
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  ObjectType  : 세계에 존재하는 "것" (엔티티)          │   │
│   │  LinkType    : "것"들 사이의 관계                     │   │
│   │  ActionType  : 세계에서 허용된 "행동"                  │   │
│   │  Rule/Logic  : 세계의 "법칙"                          │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
│   예시:                                                     │
│     ObjectType: Customer, Order, Product, Payment            │
│     LinkType:   Customer ──places──→ Order                   │
│     ActionType: cancelOrder(orderId) → status='CANCELLED'    │
│     Rule:       "배송 시작 후에는 취소 불가"                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Foundry 아키텍처의 전체 구조

Palantir Foundry는 Ontology를 중심에 놓고, 그 위에 모든 것을 구축한다.

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    Palantir Foundry 아키텍처 전체 구조                    ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║                    ┌─────────────────────────┐                         ║
║                    │      AIP Agents         │  ← AI 에이전트 레이어    ║
║                    │  (LLM-powered Actions)  │                         ║
║                    └───────────┬─────────────┘                         ║
║                                │                                       ║
║                                ▼                                       ║
║   ┌────────────────────────────────────────────────────────────┐       ║
║   │                    ONTOLOGY LAYER                          │       ║
║   │  ┌──────────────────────────────────────────────────────┐  │       ║
║   │  │                                                      │  │       ║
║   │  │   ObjectType     LinkType     ActionType    Rules    │  │       ║
║   │  │   ──────────     ────────     ──────────    ─────    │  │       ║
║   │  │   Customer       places       cancelOrder   배송후    │  │       ║
║   │  │   Order          contains     approveKYC    취소불가  │  │       ║
║   │  │   Product        assigned_to  shipOrder     ...      │  │       ║
║   │  │   Employee       reports_to   createInvoice          │  │       ║
║   │  │                                                      │  │       ║
║   │  └──────────────────────────────────────────────────────┘  │       ║
║   │         ↑                                    ↑             │       ║
║   │    "무엇이 존재하는가"               "무엇을 할 수 있는가"    │       ║
║   └────────────────────────────────────────────────────────────┘       ║
║                                │                                       ║
║                   ┌────────────┼────────────┐                          ║
║                   ▼            ▼            ▼                          ║
║            ┌───────────┐ ┌──────────┐ ┌───────────┐                    ║
║            │ Workshop  │ │  OSDK    │ │ Pipeline  │  ← 소비 레이어     ║
║            │ (UI 앱)   │ │ (SDK)   │ │ (ETL)    │                     ║
║            └───────────┘ └──────────┘ └───────────┘                    ║
║                   ▲            ▲            ▲                          ║
║                   └────────────┼────────────┘                          ║
║                                │                                       ║
║            ┌───────────────────────────────────────┐                   ║
║            │          Data Connection Layer         │  ← 데이터 수집    ║
║            │   (S3, DB, API, Streaming, Files...)   │                   ║
║            └───────────────────────────────────────┘                   ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

### 3.3 핵심 구성요소 상세

#### ObjectType (객체 타입)

```
┌─────────────────────────────────────────────────┐
│  ObjectType: "Customer"                          │
│  ─────────────────────────────────────────────   │
│                                                  │
│  Properties:                                     │
│    ├── customerId    : string (PK)               │
│    ├── name          : string                    │
│    ├── email         : string                    │
│    ├── kycStatus     : enum [PENDING,            │
│    │                        VERIFIED,            │
│    │                        REJECTED]            │
│    ├── creditScore   : integer (0-850)           │
│    └── createdAt     : timestamp                 │
│                                                  │
│  Backing Data Source:                            │
│    └── PostgreSQL > customers_table              │
│                                                  │
│  Computed Properties:                            │
│    ├── totalOrders   : count(linked Orders)      │
│    └── lifetimeValue : sum(Order.amount)         │
└─────────────────────────────────────────────────┘
```

#### LinkType (관계 타입)

```
  Customer ─────places────→ Order ─────contains────→ LineItem
     │                        │                         │
     │                        │                         │
  assigned_to              fulfilled_by              refers_to
     │                        │                         │
     ▼                        ▼                         ▼
  SalesRep               Shipment                   Product
```

#### ActionType (행동 타입) — 가장 중요!

```
┌──────────────────────────────────────────────────────────────┐
│  ActionType: "cancelOrder"                                    │
│  ─────────────────────────────────────────────────────────   │
│                                                              │
│  Parameters:                                                 │
│    ├── orderId : ObjectType<Order> (required)                │
│    └── reason  : string (required)                           │
│                                                              │
│  Preconditions (실행 전 검증):                                 │
│    ├── order.status ∈ [PENDING, CONFIRMED]                   │
│    ├── order.shipment == null                                │
│    └── requester.role ∈ [ADMIN, ORDER_MANAGER]               │
│                                                              │
│  Side Effects (실행 결과):                                     │
│    ├── SET order.status = 'CANCELLED'                        │
│    ├── SET order.cancelledAt = now()                          │
│    ├── SET order.cancelReason = reason                        │
│    ├── TRIGGER refundPayment(order.paymentId)                │
│    └── EMIT event('order.cancelled', orderId)                │
│                                                              │
│  Postconditions (실행 후 검증):                                │
│    ├── order.status == 'CANCELLED'                           │
│    └── payment.status ∈ [REFUND_INITIATED, REFUNDED]         │
│                                                              │
│  ⚠ 이것이 LLM에게 "이렇게만 해"라고 가르치는 계약서다!         │
└──────────────────────────────────────────────────────────────┘
```

---

## 4. Ontology가 LLM-Agnostic의 5대 한계를 어떻게 해결하는가

### 4.1 전체 보완 구조

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║     LLM-Agnostic만 쓸 때           Ontology를 추가했을 때              ║
║     ─────────────────────          ──────────────────────             ║
║                                                                       ║
║     ┌─────────┐                    ┌─────────┐                        ║
║     │   LLM   │                    │   LLM   │                        ║
║     └────┬────┘                    └────┬────┘                        ║
║          │                              │                             ║
║          │ 자유 텍스트                    │ 구조화된 호출               ║
║          │ (무법지대)                    │ (계약 기반)                 ║
║          ▼                              ▼                             ║
║     ┌─────────┐                    ┌─────────────────┐                ║
║     │   App   │                    │   ONTOLOGY      │                ║
║     │  (혼돈)  │                    │  ┌───────────┐  │                ║
║     └─────────┘                    │  │ Objects   │  │                ║
║                                    │  │ Links     │  │                ║
║                                    │  │ Actions   │  │                ║
║                                    │  │ Rules     │  │                ║
║                                    │  └─────┬─────┘  │                ║
║                                    └────────┼────────┘                ║
║                                             │                         ║
║                                             ▼                         ║
║                                    ┌─────────────────┐                ║
║                                    │   App (질서)     │                ║
║                                    └─────────────────┘                ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

### 4.2 한계별 해결 매핑

```
┌────────────────────────┬─────────────────────────────────────────────┐
│     LLM-Agnostic 한계   │     Ontology의 해결책                       │
├────────────────────────┼─────────────────────────────────────────────┤
│                        │                                             │
│  ① 컨텍스트 붕괴        │  ObjectType + LinkType가 "영구 상태"로       │
│                        │  존재하므로, LLM은 필요한 객체만 조회하면 됨   │
│                        │  → 컨텍스트 윈도우를 대화 기록으로 채울       │
│                        │    필요 없이 Ontology를 참조                 │
│                        │                                             │
│  ② 도메인 무지          │  ObjectType의 Property 정의가 곧 도메인      │
│                        │  지식. LLM은 Ontology 스키마를 읽는 것만     │
│                        │  으로 "이 도메인에 뭐가 있는지" 파악           │
│                        │                                             │
│  ③ 행동 비결정성        │  ActionType이 "허용된 행동"만 정의.           │
│                        │  LLM은 자유롭게 코드를 짜는 게 아니라         │
│                        │  미리 정의된 Action을 "선택"만 함             │
│                        │                                             │
│  ④ 에이전트 간 단절     │  모든 에이전트가 동일한 Ontology를 참조.      │
│                        │  공유 상태 = Ontology의 현재 객체 그래프      │
│                        │                                             │
│  ⑤ 검증 불가능성        │  Precondition/Postcondition으로 실행 전후    │
│                        │  자동 검증. 규칙 위반 시 실행 자체가 차단     │
│                        │                                             │
└────────────────────────┴─────────────────────────────────────────────┘
```

### 4.3 해결 ①: 컨텍스트 붕괴 → 영구 객체 그래프

```
           [기존: 대화 기록에 의존]

  Agent: "3번째 대화에서 User에 age 추가했고,
          7번째 대화에서 validation 넣었고,
          12번째 대화에서..."

  → 컨텍스트 윈도우 폭발 💥


           [Ontology: 영구 상태 참조]

  ┌──────────────────────────────────────┐
  │        Ontology Object Graph         │
  │                                      │
  │   Customer ────→ Order ────→ Product │
  │      │              │                │
  │      ▼              ▼                │
  │   KYCRecord     LineItem             │
  │                                      │
  │   모든 Property, 관계, 현재 값이      │
  │   Ontology에 "살아있는 상태"로 존재    │
  └──────────────┬───────────────────────┘
                 │
    Agent는 필요할 때만 조회
                 │
    "Customer의 현재 스키마 보여줘"
    → Ontology.getObjectType("Customer")
    → 즉시 응답 (대화 기록 불필요!)
```

### 4.4 해결 ②: 도메인 무지 → 스키마가 곧 지식

```
  LLM에게 Ontology 스키마를 시스템 프롬프트로 주입:

  ┌──────────────────────────────────────────────────┐
  │  System Prompt (자동 생성됨):                      │
  │                                                   │
  │  "당신은 다음 도메인에서 작업합니다:                 │
  │                                                   │
  │   ObjectTypes:                                    │
  │     - Customer (customerId, name, kycStatus...)   │
  │     - Order (orderId, status, amount...)          │
  │                                                   │
  │   Available Actions:                              │
  │     - cancelOrder(orderId, reason)                │
  │       → 조건: status ∈ [PENDING, CONFIRMED]       │
  │     - approveKYC(customerId, documents[])         │
  │       → 조건: documents.length >= 2               │
  │                                                   │
  │   이 Actions만 사용할 수 있습니다."                 │
  └──────────────────────────────────────────────────┘

  이제 LLM은 "어떤 모델을 쓰든" 도메인을 이해한다.
  GPT-4o를 쓰든, Claude를 쓰든, 동일한 Ontology를 읽는다.

  → LLM-Agnostic + Ontology = 어떤 LLM이든 도메인 전문가
```

### 4.5 해결 ③: 행동 비결정성 → Action 선택만 허용

```
           [기존: LLM이 자유롭게 코드 생성]

  User:  "주문 취소해줘"
  LLM:    DELETE FROM orders WHERE id=123;   ← 위험!!!


           [Ontology: 미리 정의된 Action만 호출]

  User:  "주문 취소해줘"

  LLM의 사고 과정:
    1. 사용 가능한 Actions 확인
       → [cancelOrder, shipOrder, createInvoice, ...]
    2. 의도 매칭
       → cancelOrder가 가장 적합
    3. 파라미터 추출
       → orderId = (사용자에게 확인)
       → reason = (사용자에게 확인)
    4. Action 호출
       → ontology.executeAction("cancelOrder", {orderId, reason})

  Ontology 내부에서 자동으로:
    ✓ Precondition 검증  (배송 전인지 확인)
    ✓ Side Effect 실행   (status 변경, 환불 트리거)
    ✓ Postcondition 검증 (결과가 올바른지 확인)
    ✓ Audit Log 기록     (누가, 언제, 왜)

  → LLM은 "어떻게 실행할지"가 아니라 "무엇을 실행할지"만 결정
```

### 4.6 해결 ④: 에이전트 간 단절 → 공유 Ontology

```
┌─────────────────────────────────────────────────────────────────┐
│              Ontology 기반 Agent Teams                            │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │ Agent 1  │  │ Agent 2  │  │ Agent 3  │  │ Agent 4  │       │
│  │ 백엔드   │  │ 프론트   │  │ 테스트   │  │ 인프라   │        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
│       │              │              │              │             │
│       └──────────────┴──────────────┴──────────────┘             │
│                              │                                   │
│                              ▼                                   │
│       ┌──────────────────────────────────────────────┐          │
│       │         SHARED ONTOLOGY (단일 진실의 원천)      │          │
│       │                                              │          │
│       │  Agent 1이 Customer 모델을 수정하면            │          │
│       │  → Ontology에 반영                            │          │
│       │  → Agent 2가 프론트엔드 빌드 시 참조           │          │
│       │  → Agent 3가 테스트 생성 시 참조               │          │
│       │  → Agent 4가 DB 마이그레이션 시 참조           │          │
│       │                                              │          │
│       │  모두가 같은 "Customer"를 보고 있다!            │          │
│       └──────────────────────────────────────────────┘          │
│                                                                 │
│  결과: 통합 시 충돌 = 0, 불일치 = 0                              │
└─────────────────────────────────────────────────────────────────┘
```

### 4.7 해결 ⑤: 검증 불가능성 → 자동 검증 파이프라인

```
  LLM이 Action을 호출하면:

  ┌─────────┐      ┌───────────────┐      ┌──────────────┐
  │  LLM    │ ───→ │ Precondition  │ ───→ │   Execute    │
  │ 호출    │      │ Check         │      │   Action     │
  └─────────┘      └───────┬───────┘      └──────┬───────┘
                           │                      │
                    ┌──────┴──────┐         ┌─────┴──────┐
                    │  PASS?      │         │ Postcond.  │
                    │  ├─ Yes → 계속│         │ Check      │
                    │  └─ No  → ✗  │         └─────┬──────┘
                    │    (차단+이유│               │
                    │     반환)    │        ┌──────┴──────┐
                    └─────────────┘        │  PASS?      │
                                           │  ├─ Yes → ✓ │
                                           │  └─ No  → ↺ │
                                           │  (롤백+알림) │
                                           └─────────────┘

  구체적 예시:

  LLM: cancelOrder(orderId="ORD-789", reason="고객 요청")

  Precondition Check:
    ✓ order.status == "CONFIRMED" (PENDING|CONFIRMED 중 하나 → PASS)
    ✗ order.shipment != null (이미 배송 시작됨 → FAIL!)

  → 결과: Action 차단
  → LLM에게 반환: "이 주문은 이미 배송이 시작되어 취소할 수 없습니다.
                   shipment ID: SHP-456, 배송 시작: 2025-01-15T10:30:00Z"

  → LLM은 이 정보를 사용자에게 전달하고 대안을 제시
```

---

## 5. 경찬님의 Claude Code CLI에서의 구현 아키텍처

### 5.1 전체 구현 구조도

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           Claude Code CLI + Ontology-Driven Agent Teams Architecture        ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                        Claude Code CLI                               │  ║
║  │                    (Opus 4.6 Orchestrator)                           │  ║
║  │                                                                      │  ║
║  │   "사용자의 요청을 Ontology Action으로 매핑하는 최상위 에이전트"        │  ║
║  └───────────────────────────┬──────────────────────────────────────────┘  ║
║                              │                                             ║
║                              ▼                                             ║
║  ┌──────────────────────────────────────────────────────────────────────┐  ║
║  │                     ONTOLOGY REGISTRY                                │  ║
║  │                  (ontology/ 디렉토리)                                 │  ║
║  │                                                                      │  ║
║  │   ontology/                                                          │  ║
║  │   ├── objects/              ← ObjectType 정의들                       │  ║
║  │   │   ├── Customer.yaml                                              │  ║
║  │   │   ├── Order.yaml                                                 │  ║
║  │   │   └── Product.yaml                                               │  ║
║  │   ├── links/                ← LinkType 정의들                         │  ║
║  │   │   ├── customer-places-order.yaml                                 │  ║
║  │   │   └── order-contains-lineitem.yaml                               │  ║
║  │   ├── actions/              ← ActionType 정의들                       │  ║
║  │   │   ├── cancelOrder.yaml                                           │  ║
║  │   │   ├── approveKYC.yaml                                            │  ║
║  │   │   └── shipOrder.yaml                                             │  ║
║  │   ├── rules/                ← 비즈니스 규칙들                          │  ║
║  │   │   └── order-rules.yaml                                           │  ║
║  │   └── ontology.lock         ← 스키마 버전 + 해시                      │  ║
║  │                                                                      │  ║
║  └───────────────────────────┬──────────────────────────────────────────┘  ║
║                              │                                             ║
║              ┌───────────────┼───────────────┐                             ║
║              ▼               ▼               ▼                             ║
║  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐                  ║
║  │  Sub-Agent 1   │ │  Sub-Agent 2   │ │  Sub-Agent 3   │                  ║
║  │  (Backend)     │ │  (Frontend)    │ │  (Test)        │                  ║
║  │                │ │                │ │                │                  ║
║  │ Ontology에서   │ │ Ontology에서   │ │ Ontology에서   │                  ║
║  │ ObjectType을   │ │ ObjectType을   │ │ ActionType을   │                  ║
║  │ 읽어서 API     │ │ 읽어서 UI      │ │ 읽어서 Test    │                  ║
║  │ 엔드포인트 생성│ │ 컴포넌트 생성  │ │ 케이스 생성    │                  ║
║  └────────────────┘ └────────────────┘ └────────────────┘                  ║
║                                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

### 5.2 데이터 흐름: 요청부터 실행까지

```
  사용자: "주문 취소해줘"

  ① Orchestrator (Opus 4.6)
     │
     ├─ Ontology 스키마 로드
     │   → objects/, links/, actions/ YAML 파싱
     │
     ├─ 의도 분석 + Action 매칭
     │   → "cancelOrder" Action 식별
     │
     ├─ 파라미터 수집
     │   → orderId, reason 확인
     │
     ▼
  ② Action Executor
     │
     ├─ Precondition 평가
     │   → order.status ∈ [PENDING, CONFIRMED]?
     │   → order.shipment == null?
     │
     ├─ [PASS] → Side Effects 실행
     │   → DB UPDATE, Event EMIT, Refund TRIGGER
     │
     ├─ Postcondition 평가
     │   → order.status == 'CANCELLED'?
     │
     ▼
  ③ 결과 반환
     │
     └─ 사용자에게: "주문 ORD-789가 정상적으로 취소되었습니다.
                     환불이 3-5영업일 내 처리됩니다."
```

### 5.3 YAML 기반 Ontology 정의 예시

```yaml
# ontology/objects/Order.yaml
objectType:
  name: Order
  primaryKey: orderId
  properties:
    orderId:
      type: string
      format: "ORD-{uuid}"
    customerId:
      type: string
      foreignKey: Customer.customerId
    status:
      type: enum
      values: [PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED]
      default: PENDING
    amount:
      type: decimal
      currency: true
      min: 0
    createdAt:
      type: timestamp
      auto: true
  computedProperties:
    daysSinceCreated:
      formula: "now() - createdAt"
      unit: days
```

```yaml
# ontology/actions/cancelOrder.yaml
actionType:
  name: cancelOrder
  description: "주문을 취소하고 환불을 시작합니다"
  parameters:
    orderId:
      type: ObjectRef<Order>
      required: true
    reason:
      type: string
      required: true
      maxLength: 500
  preconditions:
    - check: "order.status IN ['PENDING', 'CONFIRMED']"
      error: "배송이 시작된 주문은 취소할 수 없습니다"
    - check: "order.shipment IS NULL"
      error: "이미 배송이 시작되었습니다"
  sideEffects:
    - "SET order.status = 'CANCELLED'"
    - "SET order.cancelledAt = NOW()"
    - "SET order.cancelReason = ${reason}"
    - "CALL refundPayment(order.paymentId)"
    - "EMIT event('order.cancelled', {orderId, reason})"
  postconditions:
    - check: "order.status == 'CANCELLED'"
    - check: "payment.status IN ['REFUND_INITIATED', 'REFUNDED']"
```

---

## 6. 최종 비교: LLM-Agnostic만 vs Ontology 결합

```
┌──────────────────┬──────────────────────┬──────────────────────────────┐
│      측면         │  LLM-Agnostic 단독   │  LLM-Agnostic + Ontology     │
├──────────────────┼──────────────────────┼──────────────────────────────┤
│ LLM 교체         │  ✅ 쉬움             │  ✅ 쉬움 (그대로 유지)        │
│ 도메인 이해       │  ❌ 없음             │  ✅ Ontology 스키마 자동 주입 │
│ 행동 안전성       │  ❌ LLM 재량         │  ✅ ActionType 제한           │
│ 에이전트 협업     │  ❌ 격리됨           │  ✅ 공유 Ontology             │
│ 출력 검증         │  ❌ 불가             │  ✅ Pre/Postcondition         │
│ 상태 관리         │  ❌ 컨텍스트 의존    │  ✅ 영구 객체 그래프           │
│ 감사 추적         │  ❌ 로그만           │  ✅ Action별 감사 로그         │
│ 스키마 진화       │  ❌ 수동 관리        │  ✅ 버전 관리 + 마이그레이션   │
│ 코드 일관성       │  ❌ 에이전트별 차이  │  ✅ 단일 진실의 원천           │
│ 테스트 자동화     │  ❌ 수동 작성        │  ✅ Ontology 기반 자동 생성   │
└──────────────────┴──────────────────────┴──────────────────────────────┘
```

### 핵심 한 줄 정리

```
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║   LLM-Agnostic = "어떤 두뇌(LLM)든 교체 가능하게"                      ║
║                                                                       ║
║   Ontology      = "그 두뇌에게 세계관(도메인)을 가르쳐주는 설정집"        ║
║                                                                       ║
║   LLM-Agnostic은 "두뇌 교체"를 해결하지만,                             ║
║   "두뇌가 뭘 알아야 하는지, 뭘 해도 되는지"는 해결 못 한다.              ║
║                                                                       ║
║   Ontology가 그 빈칸을 채운다.                                         ║
║                                                                       ║
║   둘은 대립이 아니라 보완 관계다.                                       ║
║   LLM-Agnostic + Ontology = 진정한 엔터프라이즈 AI 시스템               ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
```

---

*이 문서는 Claude Code CLI Agent Teams 환경에서 Palantir Ontology/Foundry 모방 코드베이스를 구축하기 위한 아키텍처 가이드입니다.*

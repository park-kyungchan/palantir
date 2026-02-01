---
name: ontology-why
description: |
  Ontology Integrity Design Rationale Helper.
  Explains "why" decisions with 5 Integrity perspectives (Immutability, Determinism,
  Referential Integrity, Semantic Consistency, Lifecycle Management).
  Helper skill called by other ontology-* skills for design rationale.

  Core Capabilities:
  - 5 Integrity Perspectives: Complete analysis for all design questions
  - Reference System: Palantir official docs + Context7 MCP integration
  - Cross-Skill Integration: Called by ontology-objecttype, ontology-linktype, etc.

  Output Format:
  - Structured box format with 5 perspectives (핵심-근거-위반 시)
  - Palantir official URLs required
  - Practical recommendations (3+ items)

  Pipeline Position:
  - Helper Skill (called by other ontology-* skills)
  - Direct invocation also supported
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
version: "3.0.0"
argument-hint: "<question about ontology design>"
allowed-tools:
  - Read
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - mcp__sequential-thinking__sequentialthinking
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000

# =============================================================================
# P1: Skill as Sub-Orchestrator (Disabled - Helper Skill)
# =============================================================================
agent_delegation:
  enabled: false
  reason: "Helper skill - single question/answer without delegation"
  output_paths:
    l1: ".agent/prompts/{slug}/ontology-why/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/ontology-why/l2_index.md"
    l3: ".agent/prompts/{slug}/ontology-why/l3_details/"
  return_format:
    l1: "Design rationale summary with 5 Integrity perspectives (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/ontology-why/l2_index.md"
    l3_path: ".agent/prompts/{slug}/ontology-why/l3_details/"
    requires_l2_read: false
    next_action_hint: "Return to calling skill"

# =============================================================================
# P2: Parallel Agent Configuration (Disabled - Sequential Q&A)
# =============================================================================
parallel_agent_config:
  enabled: false
  reason: "Sequential question handling - parallel not applicable"

# =============================================================================
# P6: Agent Internal Feedback Loop (Response Validation)
# =============================================================================
agent_internal_feedback_loop:
  enabled: true
  max_iterations: 3
  validation_criteria:
    - "All 5 Integrity perspectives included"
    - "Each perspective has 핵심-근거-위반 시 structure"
    - "At least 1 Palantir official URL attached"
    - "3+ practical recommendations provided"
  refinement_triggers:
    - "Missing Integrity perspective"
    - "No official URL reference"
    - "Speculative explanation without evidence"
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /ontology-why - Ontology Integrity 설계 근거 헬퍼

> **Version:** 3.0.0
> **Model:** opus
> **User-Invocable:** true
> **Type:** Helper Skill (다른 ontology-* 스킬에서 호출)
> **Updated:** 2026-01-26 (Task #2: 5가지 Integrity 관점 상세화)

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 1. Purpose

**"왜 이렇게 정의했는가?"** 질문에 대해 **Ontology Integrity** 관점에서
명확하고 모호함 없이 설계 근거를 설명하는 헬퍼 스킬.

### 핵심 원칙

| 원칙 | 설명 |
|------|------|
| **Ontology Integrity** | 데이터 일관성, 참조 무결성, 의미론적 정확성 |
| **Palantir Architecture** | Foundry/AIP 공식 설계 원칙 기반 |
| **모호함 없음** | 명확한 근거 + 검증된 출처 URL |
| **범용성** | 모든 /ontology-* 스킬에서 호출 가능 |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 2. 호출 방식

### 2.1 직접 호출 (사용자)

```bash
/ontology-why employeeId를 String으로 정의한 이유는?
/ontology-why MANY_TO_ONE vs ONE_TO_MANY 차이점
/ontology-why ActionType에서 hazardous=True는 언제 사용?
```

### 2.2 다른 스킬에서 호출 (내부)

```python
# /ontology-objecttype, /ontology-linktype 등에서 호출
async def handle_why_question(question, context):
    """
    사용자가 "왜?"라고 물으면 /ontology-why 호출
    """
    return await invoke_skill("ontology-why", {
        "question": question,
        "context": context,  # 현재 분석 중인 타입 정보
        "type": "ObjectType"  # 또는 LinkType, ActionType
    })
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 3. 지원 범위

### 3.1 Ontology 구성요소별 질문

| 구성요소 | 질문 예시 |
|----------|----------|
| **ObjectType** | "왜 PK를 String으로?", "왜 이 속성이 required?" |
| **PropertyDefinition** | "왜 DATE vs TIMESTAMP?", "왜 unique=True?" |
| **LinkType** | "왜 MANY_TO_ONE?", "왜 FOREIGN_KEY 구현?" |
| **ActionType** | "왜 hazardous=True?", "왜 이 Parameter가 필수?" |
| **Interface** | "왜 Interface로 분리?", "왜 이 속성을 공유?" |
| **ValueType** | "왜 ValueType으로 정의?", "왜 이 제약조건?" |
| **Automation** | "왜 TIME vs OBJECT_SET 조건?", "왜 이 Effect?" |

### 3.2 Ontology Integrity 5가지 관점 (상세)

| 관점 | 정의 | 검증 질문 | 위반 시 영향 |
|------|------|----------|-------------|
| **1. Immutability (불변성)** | PK와 핵심 식별자는 객체 생성 후 절대 변경되어서는 안 됨 | "이 값이 변경되면 객체 정체성이 바뀌는가?" | 기존 edits 손실, Link 참조 깨짐, 이력 추적 불가 |
| **2. Determinism (결정성)** | 동일한 입력 데이터는 항상 동일한 PK와 객체 상태를 생성해야 함 | "데이터 재처리 시 PK가 동일하게 생성되는가?" | Foundry 빌드 시 PK 변경 → edits 손실, 중복 객체 생성 |
| **3. Referential Integrity (참조 무결성)** | LinkType 참조가 깨지지 않고, 삭제 시 cascade/restrict 정책이 명확해야 함 | "이 객체 삭제 시 연결된 Link는 어떻게 되는가?" | 고아 객체(orphan) 생성, 참조 오류, 데이터 불일치 |
| **4. Semantic Consistency (의미론적 일관성)** | 타입, 제약, 관계가 비즈니스 도메인의 실제 의미와 일치해야 함 | "이 정의가 현실 세계 규칙을 정확히 반영하는가?" | 잘못된 비즈니스 로직, 신뢰할 수 없는 분석 결과 |
| **5. Lifecycle Management (생명주기 관리)** | 객체의 생성, 수정, 삭제, 상태 변경이 명확히 정의되고 추적 가능해야 함 | "이 객체의 상태 전환 규칙이 명시되어 있는가?" | 일관성 없는 상태 변경, 감사(audit) 불가 |

#### 각 관점별 상세 설명

**1. Immutability (불변성)**
- **핵심 원칙**: PK는 객체의 "지문"이며, 한 번 부여되면 영구적
- **적용 대상**: Primary Key, Natural Identifier, Foreign Key 참조
- **검증 방법**:
  - PK 생성 로직에 mutable 속성 사용 여부 확인
  - 시간/랜덤값 기반 PK 금지 (예외: UUID는 deterministic하게 생성 시 허용)
- **Palantir 공식 근거**: "Primary keys should be deterministic and immutable"

**2. Determinism (결정성)**
- **핵심 원칙**: 동일 데이터 → 동일 PK (reproducibility)
- **적용 대상**: PK 생성 함수, Default 값, Computed Property
- **검증 방법**:
  - PK 생성에 `now()`, `random()`, `row_number()` 사용 금지
  - Composite key는 stable column만 사용
- **영향 범위**: Foundry 빌드 재실행, 데이터 마이그레이션, A/B 테스트 재현성

**3. Referential Integrity (참조 무결성)**
- **핵심 원칙**: LinkType 참조의 유효성과 삭제 정책 보장
- **적용 대상**: LinkType, Foreign Key Property, Join Table
- **검증 방법**:
  - FK가 참조하는 PK의 존재성 검증
  - Cardinality 제약 확인 (1:N에서 "1"의 존재 보장)
  - 삭제 정책: CASCADE (연쇄 삭제) vs RESTRICT (삭제 차단)
- **예시**: Employee 삭제 시 EmployeeToDepartment Link는?

**4. Semantic Consistency (의미론적 일관성)**
- **핵심 원칙**: 기술적 정의가 비즈니스 의미와 일치
- **적용 대상**: PropertyDefinition의 dataType, LinkType의 cardinality
- **검증 방법**:
  - 타입 선택의 비즈니스 근거 확인 (예: 금액은 double vs decimal?)
  - Enum 값이 실제 도메인 상태와 일치하는지 검증
- **예시**: "활성" 상태를 boolean vs enum 중 어떤 것으로?

**5. Lifecycle Management (생명주기 관리)**
- **핵심 원칙**: 객체의 상태 변화가 추적 가능하고 일관성 있음
- **적용 대상**: Status Property, ActionType의 Effect, Audit Log
- **검증 방법**:
  - 상태 전환 규칙 명시 (FSM: Finite State Machine)
  - 누가, 언제, 왜 변경했는지 추적 가능
- **예시**: Order 객체의 상태: Draft → Submitted → Approved → Shipped

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 4. 참조 체계 (CRITICAL)

### 4.1 1차 참조: ontology-definition 패키지

```
/home/palantir/park-kyungchan/palantir/Ontology-Definition/
├── ontology_definition/types/      # 타입별 구조/제약 확인
├── ontology_definition/core/       # Enum, 기본 원칙
└── tests/                          # 사용 패턴 참조
```

### 4.2 2차 참조: 외부 검증된 자료 (항상)

```
┌─────────────────────────────────────────────────────────────┐
│  ✅ 신뢰할 수 있는 출처 (ONLY THESE)                         │
├─────────────────────────────────────────────────────────────┤
│  1️⃣ Palantir 공식: palantir.com/docs/*, GitHub              │
│  2️⃣ 공식 기술 문서: Foundry, AIP, Ontology SDK              │
│  3️⃣ 검증된 기업 사례: Case Studies, 컨퍼런스 발표          │
│  4️⃣ 학술/공식 자료: 논문, 백서                             │
├─────────────────────────────────────────────────────────────┤
│  ❌ 참조 금지: 개인 블로그, 비공식 Medium, SNS               │
└─────────────────────────────────────────────────────────────┘

⚠️ MUST: 모든 설명에 검증된 출처 URL 포함
   URL 없는 주장은 제공하지 않음
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 5. 출력 형식 (5가지 Integrity 관점 필수 포함)

### 5.1 기본 응답 구조 (REQUIRED FORMAT)

**CRITICAL**: 모든 응답은 아래 5가지 Integrity 관점을 **필수적으로** 포함해야 함

```
╔══════════════════════════════════════════════════════════════╗
║  🔍 Ontology Integrity 분석: {질문 대상}                     ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Q: {사용자 질문}                                            ║
║                                                              ║
║  📐 Ontology Integrity 5가지 관점 분석:                      ║
║  ════════════════════════════════════════════════════════════ ║
║                                                              ║
║  1️⃣ Immutability (불변성)                                    ║
║     ├─ 핵심: {PK/식별자 불변성 설명}                          ║
║     ├─ 근거: {왜 이 값이 변경되면 안 되는가}                  ║
║     └─ 위반 시: {edits 손실, Link 깨짐 등 구체적 영향}        ║
║                                                              ║
║  2️⃣ Determinism (결정성)                                     ║
║     ├─ 핵심: {동일 입력 → 동일 결과 보장 여부}               ║
║     ├─ 근거: {PK 생성 로직의 재현성}                         ║
║     └─ 위반 시: {Foundry 빌드 시 PK 변경, 중복 객체 등}      ║
║                                                              ║
║  3️⃣ Referential Integrity (참조 무결성)                      ║
║     ├─ 핵심: {LinkType 참조의 유효성}                        ║
║     ├─ 근거: {FK 존재성, cascade 정책}                       ║
║     └─ 위반 시: {고아 객체, 참조 오류 등}                    ║
║                                                              ║
║  4️⃣ Semantic Consistency (의미론적 일관성)                   ║
║     ├─ 핵심: {타입/제약이 비즈니스 규칙 반영 여부}            ║
║     ├─ 근거: {도메인 의미와의 정합성}                        ║
║     └─ 위반 시: {잘못된 비즈니스 로직, 신뢰 불가 분석}        ║
║                                                              ║
║  5️⃣ Lifecycle Management (생명주기 관리)                     ║
║     ├─ 핵심: {객체 상태 변화 추적 가능성}                    ║
║     ├─ 근거: {상태 전환 규칙, audit 로그}                    ║
║     └─ 위반 시: {일관성 없는 변경, 감사 불가}                ║
║                                                              ║
║  📚 Palantir 공식 근거:                                      ║
║  ────────────────────────────────────────────                ║
║  "{관련 인용문}"                                             ║
║  🔗 {공식 문서 URL}                                          ║
║                                                              ║
║  💡 실무 권장사항:                                            ║
║  ────────────────────────────────────────────                ║
║  • {구체적인 권장 사항 1}                                     ║
║  • {구체적인 권장 사항 2}                                     ║
║  • {구체적인 권장 사항 3}                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**출력 원칙**:
- ✅ 5가지 관점 **모두** 포함 (일부 생략 금지)
- ✅ 각 관점별 "핵심-근거-위반 시" 3단 구조 유지
- ✅ Palantir 공식 문서 URL 필수 첨부
- ❌ 추측성 설명 금지 (검증된 근거만)

### 5.2 예시: Primary Key 질문 (5가지 관점 완전 적용)

```
╔══════════════════════════════════════════════════════════════╗
║  🔍 Ontology Integrity 분석: employeeId                      ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Q: 왜 employeeId를 String으로 정의했는가?                   ║
║                                                              ║
║  📐 Ontology Integrity 5가지 관점 분석:                      ║
║  ════════════════════════════════════════════════════════════ ║
║                                                              ║
║  1️⃣ Immutability (불변성)                                    ║
║     ├─ 핵심: PK는 객체 생성 후 영구적으로 고정되어야 함       ║
║     ├─ 근거: String은 비즈니스 의미 있는 식별자(EMP-001)로   ║
║     │        부여 가능하며, Integer autoincrement는          ║
║     │        DB 재생성 시 값이 변경될 위험 존재              ║
║     └─ 위반 시: 기존 사용자 편집(edits) 전부 손실,          ║
║                객체 재생성으로 인식되어 중복 발생            ║
║                                                              ║
║  2️⃣ Determinism (결정성)                                     ║
║     ├─ 핵심: 동일 소스 데이터 → 항상 동일한 employeeId 생성  ║
║     ├─ 근거: Foundry 파이프라인이 재실행되어도 PK가 동일해야 ║
║     │        기존 객체와 매칭 가능. String 사번(고유값)은    ║
║     │        deterministic하지만, DB sequence는 비결정적     ║
║     └─ 위반 시: 빌드마다 새 PK 생성 → edits 손실,           ║
║                links 끊김, 히스토리 추적 불가                ║
║                                                              ║
║  3️⃣ Referential Integrity (참조 무결성)                      ║
║     ├─ 핵심: employeeId 변경 시 모든 LinkType 참조가 무효화  ║
║     ├─ 근거: EmployeeToDepartment, EmployeeToManager 등의   ║
║     │        LinkType이 FK로 employeeId 참조. PK 변경 시    ║
║     │        참조 무결성 위반 (orphan link 발생)             ║
║     └─ 위반 시: Link가 존재하지 않는 객체 참조 →            ║
║                조직도 깨짐, 보고 라인 추적 불가              ║
║                                                              ║
║  4️⃣ Semantic Consistency (의미론적 일관성)                   ║
║     ├─ 핵심: employeeId는 "직원 고유 식별번호"의 비즈니스    ║
║     │        의미를 정확히 반영해야 함                       ║
║     ├─ 근거: HR 시스템, ERP, 급여 시스템 전반에서 String    ║
║     │        형식의 사번(예: EMP-001)을 사용. Integer로     ║
║     │        정의하면 시스템 간 매핑 시 의미 불일치 발생     ║
║     └─ 위반 시: 타입 불일치로 인한 조인 실패,               ║
║                비즈니스 규칙과 맞지 않는 데이터 구조         ║
║                                                              ║
║  5️⃣ Lifecycle Management (생명주기 관리)                     ║
║     ├─ 핵심: 직원의 입사-재직-퇴사 전 과정에서 동일 ID 유지  ║
║     ├─ 근거: 퇴사 후 재입사 시에도 동일 employeeId로 이력   ║
║     │        추적 가능해야 함. String 사번은 재사용 방지     ║
║     │        정책 적용 가능 (EMP-001은 영구 폐기)            ║
║     └─ 위반 시: 재입사 시 새 PK 부여 → 과거 이력 손실,      ║
║                승진/이동 기록 단절, 감사 추적 불가           ║
║                                                              ║
║  📚 Palantir 공식 근거:                                      ║
║  ────────────────────────────────────────────                ║
║  "Primary keys should be deterministic. If the primary key   ║
║   is non-deterministic and changes on build, edits can be    ║
║   lost and links may disappear."                             ║
║  🔗 https://www.palantir.com/docs/foundry/object-link-types/create-object-type
║                                                              ║
║  "An Employee object type may be uniquely identified by a    ║
║   string property called employeeId."                        ║
║  🔗 https://www.palantir.com/docs/foundry/functions/object-identifiers
║                                                              ║
║  "Strings can represent numbers but numbers cannot represent ║
║   strings. Type migration is painful."                       ║
║  🔗 https://www.palantir.com/docs/foundry/data-integration/primary-keys
║                                                              ║
║  💡 실무 권장사항:                                            ║
║  ────────────────────────────────────────────                ║
║  • 내부 직원: 의미 있는 사번 (EMP-001, E12345)               ║
║  • 외부 계약직: UUID v4 (충돌 방지, 시스템 독립성)           ║
║  • 절대 금지: Integer autoincrement, row_number(), random()  ║
║  • 복합키 필요 시: concat_ws(':', company_id, employee_num)  ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 6. Integration Protocol

### 6.1 다른 스킬에서 호출 시

```python
# /ontology-objecttype의 L3에서 "?" 질문 처리
async def handle_user_question(question):
    # "왜" 관련 질문인지 확인
    WHY_PATTERNS = [
        r"왜\s+", r"이유", r"근거", r"어째서",
        r"why\s+", r"reason", r"because"
    ]

    if any(re.search(p, question, re.I) for p in WHY_PATTERNS):
        # /ontology-why 호출
        return await invoke_helper_skill("ontology-why", {
            "question": question,
            "context": current_analysis_context,
            "type": current_type  # ObjectType, LinkType, etc.
        })
```

### 6.2 호출 가능한 스킬 목록

| 스킬 | 호출 시점 |
|------|----------|
| `/ontology-objecttype` | L3에서 "?" 질문, Property 설명 요청 |
| `/ontology-linktype` | Cardinality 선택 이유, 구현 방식 질문 |
| `/ontology-actiontype` | Parameter 설계, hazardous 설정 질문 |
| `/ontology-core` | 검증 오류의 근본 원인 설명 |
| (향후 추가) | Interface, ValueType, Automation 등 |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 7. Tools Allowed & MCP Integration

### 7.1 허용된 도구

| Tool | Purpose | 사용 시점 |
|------|---------|----------|
| `Read` | ontology-definition 패키지 참조 | 1차 참조: 로컬 코드 확인 |
| `WebSearch` | Palantir 공식 문서/사례 검색 | 2차 참조: 공식 문서 탐색 |
| `WebFetch` | 특정 문서 상세 조회 | WebSearch 결과 URL 상세 분석 |
| `mcp__context7__resolve-library-id` | Palantir 라이브러리 ID 조회 | Context7 쿼리 전 필수 |
| `mcp__context7__query-docs` | 공식 문서에서 코드 예시 검색 | 실제 구현 패턴 참조 |

### 7.2 WebSearch 사용 프로토콜

**CRITICAL**: 모든 외부 참조는 검증된 출처만 허용

```javascript
// Step 1: Palantir 공식 도메인 검색
WebSearch({
  query: "Palantir Foundry primary key deterministic site:palantir.com",
  allowed_domains: ["palantir.com"]
})

// Step 2: 검증된 URL 상세 조회
WebFetch({
  url: "https://www.palantir.com/docs/foundry/data-integration/primary-keys",
  prompt: "Extract key principles about primary key design and determinism"
})
```

**허용 도메인**:
- ✅ `palantir.com` (공식 문서)
- ✅ `github.com/palantir` (공식 저장소)
- ❌ 개인 블로그, Medium, Stack Overflow (비공식 출처)

### 7.3 Context7 MCP 통합 (실시간 문서 검색)

**목적**: Palantir SDK 최신 문서와 코드 예시 실시간 조회

#### Step 1: 라이브러리 ID 조회

```javascript
// Palantir Foundry SDK 검색
mcp__context7__resolve_library_id({
  libraryName: "palantir foundry",
  query: "How to define ObjectType with deterministic primary key"
})

// 예상 결과: "/palantir/foundry-platform" 또는 "/palantir/osdk"
```

#### Step 2: 문서 쿼리

```javascript
// ObjectType PK 설계 패턴 검색
mcp__context7__query_docs({
  libraryId: "/palantir/foundry-platform",
  query: "deterministic primary key string type composite key examples"
})

// LinkType cardinality 구현 검색
mcp__context7__query_docs({
  libraryId: "/palantir/osdk",
  query: "one-to-many relationship foreign key implementation"
})
```

#### Step 3: 결과 통합

Context7 결과를 5가지 Integrity 관점에 매핑:

```
Context7 코드 예시:
  df.withColumn("pk", concat_ws(":", col("customer_id"), col("order_id")))

→ 분석:
  1️⃣ Immutability: customer_id, order_id는 변경 불가 속성
  2️⃣ Determinism: concat_ws는 deterministic 함수
  3️⃣ Referential Integrity: FK 참조 가능한 stable 값
  4️⃣ Semantic Consistency: 비즈니스 의미(고객+주문) 반영
  5️⃣ Lifecycle: 주문 상태 변경 시에도 PK 유지
```

### 7.4 통합 워크플로우 (WebSearch + Context7)

```
사용자 질문
    │
    ▼
┌─────────────────────────────────────────────────┐
│ 1. 로컬 참조 (Read)                              │
│    - ontology-definition 패키지 확인             │
│    - 기존 구현 패턴 파악                         │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ 2. 공식 문서 검색 (WebSearch)                    │
│    - site:palantir.com 제한                     │
│    - 공식 설계 원칙 조회                         │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ 3. 코드 예시 조회 (Context7)                     │
│    - SDK 최신 문서에서 실제 구현 패턴            │
│    - 공식 라이브러리 사용법                      │
└─────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────┐
│ 4. 5가지 Integrity 관점 분석                     │
│    - 모든 참조를 5가지 관점에 매핑               │
│    - 공식 URL + 코드 예시 첨부                   │
└─────────────────────────────────────────────────┘
```

### 7.5 MCP 사용 예시

**질문**: "왜 Many-to-Many LinkType에 join table이 필요한가?"

```javascript
// 1. Context7에서 M:M 구현 패턴 검색
const libId = await mcp__context7__resolve_library_id({
  libraryName: "palantir foundry",
  query: "many-to-many relationship join table"
})

const docs = await mcp__context7__query_docs({
  libraryId: libId,
  query: "many-to-many link type join table dataset configuration"
})

// 2. WebSearch로 공식 설계 원칙 보강
const officialDocs = await WebSearch({
  query: "Palantir Foundry many-to-many link type site:palantir.com",
  allowed_domains: ["palantir.com"]
})

// 3. 결과를 5가지 관점으로 통합
return format5IntegrityAnalysis({
  question: "왜 M:M에 join table 필요?",
  context7Results: docs,
  officialDocs: officialDocs,
  perspectives: [
    "Immutability: Join table PK는 (source_pk, target_pk) 복합키",
    "Determinism: 관계 존재 여부가 dataset에 명시적으로 저장",
    "Referential Integrity: 양방향 FK 제약으로 무결성 보장",
    "Semantic Consistency: N:M 관계의 비즈니스 의미 명확히 표현",
    "Lifecycle: 관계 추가/삭제 이력 추적 가능"
  ]
})
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 8. Error Handling & Validation

### 8.1 오류 상황별 처리

| 상황 | 처리 방법 | 응답 예시 |
|------|----------|----------|
| **질문 불명확** | 구체적인 질문 요청 | "어떤 ObjectType/Property에 대한 질문인가요?" |
| **검증된 자료 없음** | 공식 문서 부재 명시 | "⚠️ Palantir 공식 문서에서 확인된 근거 없음. 일반적인 원칙으로 설명합니다." |
| **범위 외 질문** | Ontology 관련으로 유도 | "이 질문은 Ontology 설계와 관련이 있나요? 구체적인 타입/속성을 알려주세요." |
| **5가지 관점 누락** | 자동 보완 + 경고 | "⚠️ 일부 Integrity 관점 분석이 불완전합니다. 보완 중..." |
| **Context7 실패** | WebSearch로 폴백 | "MCP 조회 실패. 공식 웹 문서로 대체합니다." |
| **비공식 출처 사용** | 차단 + 대안 제시 | "❌ 개인 블로그는 신뢰할 수 없는 출처입니다. Palantir 공식 문서를 검색합니다." |

### 8.2 5가지 Integrity 관점 검증

**CRITICAL**: 모든 응답은 5가지 관점을 **필수적으로** 포함해야 함

```javascript
// 응답 생성 전 자동 검증
function validateIntegrityAnalysis(response) {
  const REQUIRED_PERSPECTIVES = [
    "Immutability",
    "Determinism",
    "Referential Integrity",
    "Semantic Consistency",
    "Lifecycle Management"
  ]

  let missing = []
  for (let perspective of REQUIRED_PERSPECTIVES) {
    if (!response.includes(perspective)) {
      missing.push(perspective)
    }
  }

  if (missing.length > 0) {
    console.warn(`⚠️ 누락된 관점: ${missing.join(', ')}`)
    // 자동 보완 시도
    return completeMissingPerspectives(response, missing)
  }

  return response
}
```

### 8.3 출처 검증 규칙

**허용된 출처** (우선순위 순):

1. ✅ **Tier 1**: Palantir 공식 문서
   - `palantir.com/docs/*`
   - `github.com/palantir/*` (공식 저장소)

2. ✅ **Tier 2**: Context7 인증된 라이브러리
   - `/palantir/foundry-platform`
   - `/palantir/osdk`

3. ⚠️ **Tier 3**: 검증된 케이스 스터디 (명시 필요)
   - 컨퍼런스 발표 자료
   - 공식 파트너 문서

4. ❌ **차단**: 비공식 출처
   - 개인 블로그
   - Medium, Stack Overflow
   - 검증되지 않은 포럼

### 8.4 응답 품질 체크리스트

응답 생성 후 자동 검증:

- [ ] 5가지 Integrity 관점 모두 포함
- [ ] 각 관점별 "핵심-근거-위반 시" 구조 준수
- [ ] 최소 1개 이상의 Palantir 공식 URL 첨부
- [ ] 추측성 표현 없음 ("아마도", "~일 것", "추정")
- [ ] 실무 권장사항 3개 이상
- [ ] Context7 또는 WebSearch 결과 통합

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 9. Version History & Future Enhancement

### 9.1 버전 이력

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-XX | 초기 버전: 기본 "왜?" 질문 처리 |
| 1.1.0 | 2026-01-26 | **5가지 Integrity 관점 상세화** (Task #2) |
|  |  | • Immutability, Determinism, Referential Integrity, Semantic Consistency, Lifecycle Management |
|  |  | • 출력 형식에 5가지 관점 필수 포함 |
|  |  | • WebSearch/Context7 MCP 통합 |
|  |  | • 응답 품질 검증 체크리스트 추가 |
| 3.0.0 | 2026-01-29 | **EFL Pattern Integration** |
|  |  | • YAML frontmatter 추가 (disable-model-invocation: true, context: fork) |
|  |  | • P6: Agent Internal Feedback Loop (5가지 관점 검증) |
|  |  | • hooks format: type: command |

### 9.2 향후 개선 계획

| 기능 | 설명 | 우선순위 | 상태 |
|------|------|----------|------|
| **다국어 지원** | 영어/한국어 자동 감지, 응답 언어 일치 | P1 | 🔜 |
| **대화형 심화** | "더 자세히", "예시 보여줘" 등 연속 질문 처리 | P1 | 🔜 |
| **시각화** | Mermaid 다이어그램으로 관계도/영향 범위 표시 | P2 | 🔜 |
| **자동 검증** | 응답에 5가지 관점 누락 시 경고 + 자동 보완 | P1 | ✅ (v1.1.0) |
| **Context7 캐싱** | 자주 조회하는 문서 로컬 캐싱 | P2 | 🔜 |
| **A/B 비교** | 여러 설계 옵션의 Integrity 관점 비교 | P2 | 🔜 |

### 9.3 향후 통합 계획

**다른 Ontology 스킬과의 통합**:

```
/ontology-objecttype (L3)
    │
    ├─ 사용자 "?" 질문 입력
    │
    ▼
/ontology-why 자동 호출
    │
    ├─ 5가지 Integrity 분석
    ├─ Context7 코드 예시
    └─ Palantir 공식 근거
    │
    ▼
/ontology-objecttype으로 결과 반환
    │
    └─ L3 출력에 "설계 근거" 섹션 추가
```

**예시**:
```
사용자: /ontology-objecttype Employee 분석
  → L1: 후보 탐지
  → L2: 속성 추출
  → 사용자: "?" (왜 employeeId가 String인가?)
  → /ontology-why 자동 호출
  → 5가지 관점 분석 표시
  → L3 계속 진행
```

### 9.4 메트릭 & 품질 목표

| 메트릭 | 목표 | 현재 |
|--------|------|------|
| **5가지 관점 포함률** | 100% (필수) | 100% (v1.1.0) |
| **공식 URL 첨부율** | 100% | - |
| **Context7 성공률** | >90% | - |
| **응답 시간** | <10초 | - |
| **사용자 만족도** | >4.5/5 | - |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 10. EFL Pattern Implementation (V3.0.0)

### Helper Skill Design

As a Helper Skill called by other ontology-* skills:
- P1 (Sub-Orchestrator): Disabled - single question/answer pattern
- P2 (Parallel Agents): Disabled - sequential question handling
- P6 (Feedback Loop): Enabled - 5 Integrity perspectives validation

### P6: Response Validation Loop

```javascript
// Self-validation for all responses
const responseValidation = {
  maxIterations: 3,
  requiredPerspectives: [
    "Immutability",
    "Determinism",
    "Referential Integrity",
    "Semantic Consistency",
    "Lifecycle Management"
  ],
  checks: [
    "all5PerspectivesIncluded()",
    "each('핵심-근거-위반 시').structureValid()",
    "palantirOfficialURLs.length >= 1",
    "practicalRecommendations.length >= 3"
  ],
  onFailure: "completeMissingPerspectives(response, missing)"
}
```

### Cross-Skill Integration

```
/ontology-objecttype (L3)
    │
    ├─ User asks "?" question
    │
    ▼
/ontology-why (auto-invoked)
    │
    ├─ 5 Integrity perspective analysis
    ├─ Context7 code examples
    └─ Palantir official references
    │
    ▼
Return to /ontology-objecttype
    └─ Add "설계 근거" section to L3 output
```

### Post-Compact Recovery

```javascript
if (isPostCompactSession()) {
  // Helper skill - stateless, no recovery needed
  // Each invocation is independent
  console.log("Helper skill: stateless operation, ready for new questions")
}
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


**End of Skill Definition**

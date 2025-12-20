# Palantir AIP/Foundry Ontology 기반 개발 종합 학습 가이드

Palantir Foundry와 AIP는 단순한 데이터 플랫폼을 넘어 **조직의 디지털 트윈을 구현하는 운영 시스템**입니다. Ontology를 통해 비즈니스 개념을 코드로 표현하고, 데이터 통합부터 AI 기반 의사결정까지 전 과정을 통합합니다. 이 가이드는 공식 문서를 기반으로 Ontology 핵심 구성요소와 실제 개발 패턴을 체계적으로 정리합니다.

---

## Foundry/AIP가 필요한 이유

### 비즈니스적 필요성

전통적인 데이터 플랫폼은 **데이터 사일로**, **분석과 운영의 단절**, **AI 도입 장벽** 문제를 해결하지 못합니다. Foundry는 이러한 문제를 Ontology 중심 아키텍처로 해결합니다.

| 기존 문제 | Foundry 해결책 |
|-----------|---------------|
| 데이터 사일로 | 조직 전체의 **단일 진실 소스(Single Source of Truth)** 제공 |
| 분석-운영 단절 | 분석 결과를 즉시 **운영 워크플로우**에 적용 |
| AI 도입 장벽 | LLM을 기존 데이터/시스템에 **안전하게 통합** |
| 복잡한 데이터 관리 | **비즈니스 용어**로 데이터를 이해하고 활용 |

핵심 비즈니스 가치는 네 가지로 요약됩니다. **연결성의 규모**(조직 전체가 동일한 객체를 통해 의사결정), **해석 가능성**(비기술 사용자도 일상 용어로 데이터 이해), **규모의 경제**(단일 재사용 가능 데이터 자산), **의사결정 캡처**(결정을 데이터로 기록하여 지속적 개선).

### 기술적 필요성과 플랫폼 구조

Foundry는 **200개 이상의 커넥터**로 모든 소스 시스템을 연결하고, Kubernetes 기반 자동 확장 빌드 시스템, 전체 데이터 리니지 추적, AI/ML 운영화를 제공합니다. 플랫폼은 다음 레이어로 구성됩니다:

- **Apollo**: 자율 소프트웨어 배포를 위한 미션 컨트롤
- **Foundry**: 데이터 통합, 변환, 분석을 위한 운영 플랫폼  
- **AIP**: 생성형 AI/LLM을 운영에 연결하는 AI 플랫폼
- **Ontology**: 모든 것을 연결하는 **시맨틱 레이어** (핵심)

AIP(Artificial Intelligence Platform)는 2023년 4월 출시되어 AIP Logic(LLM 기반 함수), AIP Agent Studio(AI 에이전트 생성), AIP Assist(플랫폼 내 LLM 지원 도우미) 등의 구성요소를 제공합니다.

---

## Ontology 핵심 개념: 조직의 디지털 트윈

> **"Ontology는 조직의 디지털 트윈이다"** - Palantir 공식 문서

Ontology는 실제 세계의 개념(공장, 장비, 제품, 고객 주문)을 디지털로 매핑하는 **풍부한 시맨틱 레이어**입니다. 단순히 데이터가 아닌 기업의 **의사결정**을 표현하도록 설계되었으며, 모든 의사결정은 Data(사실), Logic(로직), Actions(영향)으로 분해됩니다.

### Ontology의 3가지 레이어

1. **시맨틱 레이어**: 도메인의 개념적 모델 정의 (엔터티, 관계, 속성)
2. **키네틱 레이어**: 실제 데이터 소스를 개념적 모델에 매핑
3. **다이나믹 레이어**: 비즈니스 규칙, 정책, 워크플로우, 권한 정의

---

## ObjectTypes: 실세계 엔터티의 스키마

**Object Type**은 실제 세계 엔터티(entity) 또는 이벤트(event)의 스키마 정의입니다. 데이터베이스 테이블과 유사하지만 비즈니스 의미를 담고 있습니다.

| Ontology 개념 | 데이터셋 개념 |
|--------------|-------------|
| Object Type | Dataset (테이블) |
| Object | Row (행) |
| Object Set | Filtered Rows |
| Property | Column (열) |

### ObjectType 구성 요소

Object Type은 다음 요소들로 구성됩니다:

```
ObjectType 구조:
├── 메타데이터
│   ├── Display name: 사용자 표시 이름 (예: "항공기")
│   ├── Plural display name: 복수형 이름
│   ├── ID: 고유 식별자 (소문자, 숫자, 대시)
│   ├── API name: 프로그래밍용 이름 (PascalCase, 예: Aircraft)
│   └── Groups: 분류 라벨
├── Backing Datasource: 데이터 소스 데이터셋
├── Properties: 객체 특성 정의
├── Primary Key: 고유 식별자 속성
└── Title Key: 표시 이름으로 사용되는 속성
```

### 생성 방법 (Guided Helper)

```
1. Ontology Manager 접속
2. New > Create object type 선택
3. Backing datasource 선택 (기존 데이터셋 또는 새로 생성)
4. Object type metadata 입력 (Icon, Name, Description, Groups)
5. Properties 설정: 데이터셋 컬럼 자동 매핑 또는 수동 추가
6. Primary Key와 Title Key 설정
7. Actions 생성 (선택사항)
8. Save 버튼으로 Ontology에 저장
```

실제 사용 예시로 `Employee` Object Type은 Primary Key로 `employee_number`("11502"), Title Key로 `full_name`("Melissa Chang")을 사용하고, `start_date`, `role`, `department` 등의 Properties를 가집니다.

---

## Properties: 객체 특성 정의

**Property**는 실세계 엔터티 특성에 대한 스키마 정의입니다. 다양한 데이터 타입을 지원하며, Primary Key와 Title Key로 지정할 수 있습니다.

### 지원 데이터 타입

| Base Type | Title Key | Primary Key | 비고 |
|-----------|-----------|-------------|------|
| **String** | ✅ | ✅ | 가장 권장 |
| **Integer** | ✅ | ✅ | 정수 |
| **Date/Timestamp** | ✅ | ⚠️ 비권장 | 충돌 가능성 |
| **Boolean** | ✅ | ⚠️ 비권장 | 2개 인스턴스 제한 |
| **Long** | ✅ | ⚠️ 비권장 | 1e15 이상 JS 문제 |
| **Float/Double** | ✅ | ❌ | 부동소수점 |
| **Array** | ✅* | ❌ | null 불가, 중첩 불가 |
| **Vector** | ❌ | ❌ | 시맨틱 검색용, 최대 2048차원 |
| **Struct** | ❌ | ❌ | 복합 타입 |
| **Geopoint/Geoshape** | ✅/❌ | ❌ | 지리적 데이터 |
| **Time Series** | ❌ | ❌ | 시계열 데이터 |

### Property 메타데이터 설정

```
Property 구성:
├── Property ID: 고유 식별자 (소문자, 숫자, 대시, 언더스코어)
├── Display name: 표시 이름
├── API name: 프로그래밍용 이름 (camelCase, 예: startDate)
├── Base type: 데이터 타입
├── Status: experimental | active | deprecated
├── Visibility: prominent | normal | hidden
└── Required: 필수 여부 (OSv2에서만 지원)
```

**Primary Key 권장사항**: 결정론적(deterministic)이고 변경되지 않는 값을 사용하며, Long 타입 대신 **String 타입**을 권장합니다. Date/Timestamp를 Primary Key로 사용하는 것은 피해야 합니다.

---

## LinkTypes: 객체 간 관계 정의

**Link Type**은 두 Object Type 간의 관계 스키마입니다. 데이터베이스의 **JOIN**과 유사하지만 Ontology의 시맨틱 의미를 담습니다.

### 관계 카디널리티

| 관계 유형 | 구현 방식 | 예시 |
|----------|----------|------|
| **One-to-One** | Foreign Key | Employee ↔ Badge |
| **One-to-Many** | Foreign Key | Company → Employees |
| **Many-to-One** | Foreign Key | Flights → Aircraft |
| **Many-to-Many** | Join Table 또는 Object-Backed | Students ↔ Courses |

### Foreign Key 기반 링크 (1:1, N:1)

```
┌─────────────────┐         ┌─────────────────┐
│    Flight       │         │    Aircraft     │
├─────────────────┤         ├─────────────────┤
│ flight_id (PK)  │         │ tail_number (PK)│
│ tail_number (FK)│─────────│ model           │
│ departure_date  │         │ capacity        │
└─────────────────┘         └─────────────────┘

설정:
- Source Object: Flight
- Target Object: Aircraft  
- Foreign Key Property: flight.tail_number
- Primary Key Property: aircraft.tail_number
```

### Join Table 기반 링크 (N:N)

Many-to-Many 관계는 별도의 Join Table Dataset을 사용합니다:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Student    │    │  Enrollment  │    │   Course     │
├──────────────┤    │ (Join Table) │    ├──────────────┤
│ student_id   │────│ student_id   │────│ course_id    │
│ name         │    │ course_id    │    │ title        │
└──────────────┘    └──────────────┘    └──────────────┘
```

### TypeScript에서 링크 사용

```typescript
// Many-to-1 링크 접근
const aircraft: Aircraft | undefined = flight.assignedAircraft.get();

// 비동기 접근
const aircraft = await flight.assignedAircraft.getAsync();

// 1-to-Many 링크 접근
const flights: Flight[] = aircraft.scheduledFlights.all();

// Object Set을 통한 Search Around
const linkedObjs = aircraftObjectSet.searchAroundToScheduledFlights();
```

---

## ActionTypes: Ontology 데이터 변경

**Action Type**은 사용자가 Ontology의 객체, 속성, 링크를 변경할 수 있도록 정의된 편집 세트입니다. 실제 비즈니스 프로세스를 Ontology 수준에서 캡처합니다.

### 수행 가능한 작업

| 작업 유형 | 설명 |
|----------|------|
| **Create object** | 새 객체 생성, Primary Key 필수 |
| **Modify objects** | 기존 객체 속성 값 변경 |
| **Delete objects** | 기존 객체 삭제 |
| **Create/Delete links** | Many-to-Many 관계 생성/제거 |
| **Notifications** | 플랫폼/이메일 알림 전송 |
| **Webhooks** | 외부 시스템에 HTTP 요청 |

### Rules 구현

**Ontology Rules** (데이터 편집):
- Create object, Modify object(s), Delete object(s)
- Create link(s), Delete link
- Function Rule: Ontology Edit Function 참조

**Side Effect Rules** (부가 효과):
- Notification Rules: 파라미터로 내용/수신자 커스터마이징
- Webhooks: 외부 시스템 연동

### 트리거 방식

```yaml
수동(Manual): Workshop, Object Explorer에서 버튼 클릭
자동(Automated): Automate 앱에서 조건 충족 시 실행
이벤트 기반: 객체 생성/수정 시 트리거
인라인 편집: Workshop에서 셀 레벨 편집
API 호출: REST API를 통한 프로그래밍 방식
```

### Submission Criteria (제출 기준)

비즈니스 규칙을 검증 로직으로 인코딩합니다:

```yaml
# 비행기 교체 Action 예시
조건:
  - 사용자 그룹 확인: "flight_controller 그룹 소속인가?"
  - 파라미터 검증: "Aircraft 상태가 'operational'인가?"
  - 정규식 검증: "공항 코드가 ^[A-Z]{3}$ 패턴인가?"
```

---

## Functions: 비즈니스 로직 구현

**Foundry Functions**는 운영 컨텍스트(대시보드, 의사결정 애플리케이션)에서 빠르게 실행되는 서버 측 로직입니다. TypeScript와 Python을 지원하며, Ontology와 네이티브로 통합됩니다.

### TypeScript Functions (v1 - 클래스 기반)

```typescript
import { Function, OntologyEditFunction, Query, Integer, Edits } from "@foundry/functions-api";
import { Employee, Objects, ObjectSet } from "@foundry/ontology-api";

export class EmployeeFunctions {
    // 기본 함수
    @Function()
    public calculateBonus(salary: Integer): Integer {
        return salary * 0.1;
    }

    // Ontology 편집 함수 (Action 백업용)
    @Edits(Employee)
    @OntologyEditFunction()
    public updateDepartment(employee: Employee, newDept: string): void {
        employee.department = newDept;
    }

    // API Gateway 쿼리 함수
    @Query({ apiName: "getEmployeesByDepartment" })
    public async getEmployeesByDept(dept: string): Promise<ObjectSet<Employee>> {
        return Objects.search().employee()
            .filter(e => e.department.exactMatch(dept));
    }
}
```

### TypeScript Functions (v2 - 함수 기반)

```typescript
import { Employee, Ticket } from "@ontology/sdk";
import { Client } from "@osdk/client";
import { createEditBatch, Edits } from "@osdk/functions";

// config 객체로 API 이름 정의
export const config = { apiName: "createTicketForEmployee" };

type OntologyEdit = Edits.Object<Employee> | Edits.Object<Ticket>;

export default function createTicketForEmployee(
    client: Client,
    employee: Employee,
    ticketId: string
): OntologyEdit[] {
    const batch = createEditBatch<OntologyEdit>(client);
    
    // 새 객체 생성
    batch.create(Ticket, ticketId, {
        status: "Open",
        priority: "High"
    });
    
    // 기존 객체 속성 업데이트
    batch.update(employee, { lastTicketDate: new Date() });
    
    return batch.getEdits();
}
```

### Python Functions

```python
from functions.api import function, Integer, OntologyEdit
from ontology_sdk import FoundryClient
from ontology_sdk.ontology.objects import Employee, Ticket
from datetime import datetime, timedelta

# 기본 읽기 전용 함수
@function
def calculate_bonus(employee: Employee) -> float:
    """직원 보너스 계산"""
    return employee.salary * 0.1

# API Gateway 쿼리 함수
@function(api_name="getHighCapacityAircraft")
def get_high_capacity_aircraft(min_capacity: Integer):
    client = FoundryClient()
    return client.ontology.objects.Aircraft.where(
        Aircraft.object_type.capacity > min_capacity
    )

# Ontology 편집 함수
@function(edits=[Employee, Ticket])
def create_ticket_and_assign(
    employee: Employee,
    ticket_id: Integer
) -> list[OntologyEdit]:
    ontology_edits = FoundryClient().ontology.edits()
    
    # 새 객체 생성
    new_ticket = ontology_edits.objects.Ticket.create(ticket_id)
    new_ticket.due_date = datetime.now() + timedelta(days=7)
    new_ticket.status = "Open"
    
    # 기존 객체 편집
    editable_employee = ontology_edits.objects.Employee.edit(employee)
    editable_employee.assigned_tickets.add(new_ticket)
    
    return ontology_edits.get_edits()
```

### 함수 배포 워크플로우

```
1. Code Repository 생성 (TypeScript/Python Functions 템플릿)
2. 함수 작성 (데코레이터와 함께 로직 구현)
3. Live Preview 테스트 (Functions Helper에서 실행)
4. Commit (마스터 브랜치에 커밋)
5. Tag & Release (버전 태그 생성 → Functions Registry에 게시)
6. 플랫폼 전체에서 사용 가능
```

---

## AIP Logic: 노코드 LLM 함수 개발

**AIP Logic**은 LLM을 활용하여 Function을 빌드, 테스트, 릴리스할 수 있는 노코드 개발 환경입니다.

### 블록 유형

```
Use LLM: LLM과 상호작용하는 핵심 블록
Execute Function: 기존 TypeScript/Python Function 호출
Apply Actions: Ontology 편집을 위한 Action 호출
Conditionals: if-then-else 로직 (모든 분기 일관된 출력 필요)
Loops: 컬렉션 반복 처리
```

### 사용 예시

```
입력: 고객 서비스 Ticket 객체 + 고객 이메일 텍스트
→ LLM 분석 (과거 유사 티켓 해결 사례 참조)
→ 출력: 추천 솔루션 + 우선순위 자동 지정
```

AIP Logic은 Action Type에서 참조하여 Workshop에서 사용하거나, Automate를 통해 자동화할 수 있습니다.

---

## Interfaces: 객체 타입의 다형성

**Interface**는 객체 타입의 형태와 기능을 설명하는 추상적 Ontology 타입입니다. 공통된 형태를 가진 객체 타입들 간의 일관된 모델링을 가능하게 합니다.

### Interface vs Object Type

| 구분 | Object Type | Interface |
|------|-------------|-----------|
| 성격 | 구체적(Concrete) | 추상적(Abstract) |
| 속성 | 공유/로컬 속성 | 공유 속성만 |
| 데이터셋 | 백킹 데이터셋 있음 | 데이터셋 없음 |
| 인스턴스화 | 직접 가능 | 구체 타입 통해서만 |

### 다형성 구조 예시

```
Facility (Interface)
├── facilityName: String
├── location: Geopoint
│
├── Airport (Object Type) - implements Facility
├── ManufacturingPlant (Object Type) - implements Facility
└── CommercialBuilding (Interface) - extends Facility
    ├── Office (Object Type) - implements CommercialBuilding
    └── Warehouse (Object Type) - implements CommercialBuilding
```

Interface를 활용하면 워크플로우가 구체적인 객체 타입 세부사항 없이도 모든 시설과 상호작용할 수 있습니다.

---

## Workflows: 자동화 파이프라인

### Automate

**Automate**는 조건-효과 기반 비즈니스 자동화 도구입니다.

**조건(Condition) 유형:**
- Time Condition: 정적 시간 기반 ("매주 월요일 오전 9시")
- Object Data Condition: 객체 데이터 기반 ("priority='high'인 새 alert 추가 시")
- Combined: 시간 + 데이터 조합

**효과(Effect) 유형:**
- Actions Effect: Foundry Action 자동 실행
- Notification Effect: 플랫폼/이메일 알림 (PDF 첨부 가능)
- Fallback Effect: 기본 액션 실패 시 대체 동작

### 사용 예시

```yaml
스케줄 리포트:
  조건: "매주 월요일 오전 9시"
  효과: "주간 보고서 PDF 이메일 전송"

데이터 알림:
  조건: "open issue 객체 수가 임계값 초과"
  효과: "담당자에게 알림 전송"

AIP Logic 자동화:
  조건: "새 고객 문의 객체 생성 시"
  효과: "Logic Function 실행 → 자동 분류 및 담당자 지정"
```

### Workflow Builder

워크플로우 이해, 관리, 디버깅을 위한 인터랙티브 워크스페이스입니다. Objects, Actions, Functions, LLMs, Applications의 관계 그래프를 시각화하고, 속성 출처(provenance)를 추적합니다.

---

## Ontology SDK (OSDK) 프로그래밍

### TypeScript OSDK 설정

```bash
# 새 프로젝트 생성
npm create @osdk/app@latest -- \
    --application <APPLICATION_RID> \
    --foundryUrl <FOUNDRY_URL> \
    --clientId <CLIENT_ID> \
    --osdkPackage <PACKAGE_NAME> \
    --osdkRegistryUrl <REGISTRY_URL>

# 기존 프로젝트에 추가
npm install <PACKAGE_NAME>@latest
npm install @osdk/client@latest @osdk/oauth@latest
```

### 클라이언트 초기화

```typescript
import { createPublicOauthClient } from "@osdk/oauth";
import { createClient } from "@osdk/client";

// Public OAuth (프론트엔드)
const auth = createPublicOauthClient(
    "<CLIENT_ID>",
    "<FOUNDRY_URL>",
    "<REDIRECT_URL>"
);

const client = createClient(
    "<FOUNDRY_URL>",
    "<ONTOLOGY_RID>",
    auth
);
```

### 객체 조회 및 조작

```typescript
import { Employee } from "<PACKAGE_NAME>";

// 페이지 단위 조회
const result = await client(Employee).fetchPage({ $pageSize: 10 });

// 특정 객체 조회 (Primary Key)
const employee = await client(Employee).get("11502");

// 실시간 구독 (OSDK v2.1+)
const subscription = client(Employee).subscribe({
    onChange: (update) => console.log(update),
    onError: (error) => console.error(error)
});
```

### Python OSDK 사용

```python
from <PACKAGE_NAME> import FoundryClient
from <PACKAGE_NAME>.core.api import UserTokenAuth
from ontology_sdk.ontology.objects import Employee

# 클라이언트 초기화
auth = UserTokenAuth(hostname="<FOUNDRY_URL>", token=os.environ["FOUNDRY_TOKEN"])
client = FoundryClient(auth=auth, hostname="<FOUNDRY_URL>")

# 객체 조회
employees = list(client.ontology.objects.Employee.iterate())

# 조건부 필터링
filtered = client.ontology.objects.Employee.where(
    Employee.object_type.department.equals("Engineering")
)

# 정렬
sorted_employees = client.ontology.objects.Employee \
    .where(~Employee.object_type.full_name.is_null()) \
    .order_by(Employee.object_type.full_name.asc()) \
    .iterate()

# 집계
result = client.ontology.objects.Employee.aggregate({
    "avg_salary": Employee.object_type.salary.avg(),
    "total_count": Employee.object_type.id.count()
}).compute()
```

---

## 애플리케이션 개발 도구 비교

### Workshop vs Slate vs OSDK

| 특성 | Workshop | Slate | OSDK |
|------|----------|-------|------|
| 코딩 필요 | No-code | Low-code (CSS/JS) | Pro-code |
| 커스터마이징 | 제한적 | 높음 | 최고 |
| 학습 곡선 | 낮음 | 중간 | 높음 |
| 사용 사례 | 표준 워크플로우 앱 | 커스텀 대시보드 | 외부 앱 통합 |

### Workshop 핵심 개념

**위젯 카테고리:**
- Core Display: Object Table, Object List, Object View
- Visualization: Chart XY, Map, Gantt Chart, Timeline
- Filtering: Filter List, Object Dropdown, Date Picker
- AIP: AIP Analyst, AIP Agent, AIP Generated Content

**인터랙션 모델:**
```
Variables: 상태 저장 및 위젯간 데이터 공유
Events: 사용자 액션에 대한 반응 정의
Actions: Ontology 데이터 쓰기 작업
Functions: 비즈니스 로직 실행
```

### AIP Agent Studio

기업 특화 AI 어시스턴트를 구축하는 도구입니다:

| 티어 | 설명 |
|------|------|
| Tier 1 | Ad-hoc 분석 (AIP Threads) |
| Tier 2 | Task-specific Agent |
| Tier 3 | Agentic Application (Workshop 통합) |
| Tier 4 | Automated Agent (완전 자동화) |

---

## 보안 및 권한 관리

### 권한 모델

**Project-based Permissions** (권장):
- Ontology 리소스를 Compass 파일시스템으로 관리
- 폴더/프로젝트 레벨에서 일괄 권한 관리
- 역할: Viewer, Editor, Owner

### 데이터 보안 레이어

```
Dataset-level: 데이터셋 전체 접근 제어
Restricted Views: 행(Row) 레벨 보안
Multi-datasource Objects (MDOs): 속성별 접근 제어
```

### 권장 프로젝트 구조

```
Aviation [Ontology]/
├── aircraft dataset
├── flight_alert dataset
└── flight_alert_writeback dataset

Flight Alert Inbox [App]/
└── Workshop application

User Groups/
├── Aviation [Ontology] - Viewer
└── Aviation [Ontology] - Editor
```

---

## 전체 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────┐
│                     User Applications                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │ Workshop │  │  Slate   │  │   OSDK   │  │ AIP Agents   │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └──────┬───────┘ │
└───────┼─────────────┼─────────────┼───────────────┼─────────┘
        └─────────────┴──────┬──────┴───────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                        ONTOLOGY                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Object     │  │ Actions    │  │ Functions  │             │
│  │ Types      │◄─┤ (Write)    │  │ (Logic)    │             │
│  │ (Semantic) │  └────────────┘  └────────────┘             │
│  └────┬───────┘       │                │                    │
│       │ implements    │                │                    │
│  ┌────▼───────┐  ┌────▼────────┐  ┌────▼────────┐          │
│  │ Interfaces │  │ AIP Logic   │  │ Automate    │          │
│  │ (Abstract) │  │ (LLM)       │  │ (Workflow)  │          │
│  └────────────┘  └─────────────┘  └─────────────┘          │
└───────┬─────────────────────────────────────────────────────┘
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    Data Foundation                           │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐              │
│  │ Datasets │  │ Restricted   │  │ Streams  │              │
│  │          │  │ Views        │  │          │              │
│  └──────────┘  └──────────────┘  └──────────┘              │
└─────────────────────────────────────────────────────────────┘
```

---

## 결론: Ontology 기반 개발의 핵심 원칙

Palantir Foundry/AIP의 Ontology 기반 개발은 **데이터를 비즈니스 개념으로 승격**시키는 패러다임입니다.

**핵심 학습 포인트:**

1. **Object Types**는 테이블이 아닌 비즈니스 엔터티입니다. Primary Key는 결정론적이고 변경되지 않는 String 타입을 권장합니다.

2. **Link Types**는 단순 JOIN이 아닌 비즈니스 관계를 표현합니다. 1:1/N:1은 Foreign Key, N:N은 Join Table 또는 Object-Backed 방식을 사용합니다.

3. **Actions**은 CRUD가 아닌 비즈니스 프로세스입니다. Submission Criteria로 비즈니스 규칙을 인코딩하고, Side Effects로 알림/웹훅을 처리합니다.

4. **Functions**는 비즈니스 로직의 재사용 단위입니다. TypeScript의 `@Function`, `@OntologyEditFunction`, `@Query` 데코레이터 또는 Python의 `@function` 데코레이터를 활용합니다.

5. **Interfaces**를 통한 다형성으로 유연한 워크플로우를 구축합니다.

6. **AIP Logic**과 **Automate**를 결합하여 LLM 기반 자동화를 구현합니다.

개발 시작점으로 Workshop에서 프로토타입을 구축한 후, 필요에 따라 Functions로 로직을 추출하고, OSDK로 외부 통합을 확장하는 점진적 접근을 권장합니다.
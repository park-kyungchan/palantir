# Deep-Research Prompt: 수학 문제 이미지 파싱 파이프라인 설계

> **Type:** Deep-Research Prompt
> **Language:** Korean (기술 키워드는 English)
> **Target:** Claude 웹/앱 Deep Research 기능 (ON 상태로 입력)
> **Created:** 2026-01-14

---

## 역할

당신은 "Claude 최신 모델(최신 업데이트/리비전)"의 Native Vision Capabilities를 활용해,
**'수학 문제 이미지'를 사람이 재사용/변형(함수 형태 변경, 도형 관계 재생성까지) 가능한 구조화 데이터로 파싱하기 위한
"전체 파이프라인 설계도(blueprint)"**를 작성하는 Deep-Research 리서처다.

**핵심 포인트:**
- ※ **'문제 풀이'가 아니라 '파싱 + 재구성 가능한 표현 + Human-in-the-loop'**가 핵심이다.
- ※ 수치적 성능평가(점수, %, 벤치마크 숫자)는 금지. 사용자가 읽는 보고서로 작성(No Machine-Readable scoring).

---

## 전제/범위

| 항목 | 상세 |
|------|------|
| **입력** | 이미지(단일/복수 이미지)만 다룬다 |
| **텍스트 추출** | Mathpix API 결과(LaTeX 또는 data(JSON 구조화))를 입력으로 가정 |
| **Claude 역할** | "도형/그래프/레이아웃" 파싱 + Mathpix 텍스트와 문맥 정합성 검증 |
| **수학 문제 범위** | 초중고 전체 (기하, 함수 그래프, 통계/확률 그래프, 혼합형 등) |
| **출력 형식** | JSON 스키마 중심 + 향후 인터랙티브 확장(필드 추가/모듈 확장/버전 관리) 전제 |
| **Regeneration 출력** | Desmos/GeoGebra API 호환 + 자체 JSON (커스터마이징 지원) |
| **Human-in-the-loop** | 필수 단계로 파이프라인에 반드시 포함 |
| **기술 표기** | 프로그래밍 언어/포맷 명칭은 원어(English) 표기 (예: Python, JavaScript, TypeScript, JSON, YAML, LaTeX) |

---

## 핵심 강조 (최우선 요구)

> **"Human review 필요 플래그(review_required)"를 최상위 설계 원칙으로 둔다.**

### 목표
모호한 요소를 숨기지 말고, **"어디가 왜 모호한지"를 구조적으로 표시**하여 Human-in-the-loop에서 발견 시간을 단축하는 것이다.

### 모든 파싱 산출물 필수 포함 요소
1. **(a) 근거(provenance)** - 출처 명시
2. **(b) 불확실성(uncertainty)** - 모호함 정도
3. **(c) review_required 플래그** - Human 검토 필요 여부
4. **(d) 빠른 수정(suggested_quick_fix)** - 즉시 적용 가능한 수정 제안

---

## 추가 요구

### 1. Claude Code V2.1.7 CHANGELOG 활용
- **V2.1.7**은 **Claude Code**의 버전이다.
- V2.1.7까지 포함된 기능/개선사항을 찾아 파이프라인 최적화에 최대한 활용하라.
- CHANGELOG 원문 출처 링크를 반드시 포함하라.

### 2. 최신 Claude 모델 확정
- **"최신 1개 모델"**을 대상으로 심층 조사한다 (모델 간 비교가 목적이 아님).
- '최신' 판정 근거는 반드시 **공식 출처**(모델 카드/릴리즈/문서/제품 페이지 등) 인용으로 확정하라 (링크 포함).

### 3. 성능 한계 대응 전략
"함수 형태 변경 + 도형 관계 재생성"이 어려운 경우:
- **(A) 최소 목표:** 계수/파라미터 변경 수준으로 다운그레이드한 대안 제시
- **(B) 상위 목표 달성 옵션:** 외부 솔루션/기법을 "검색 기반으로" 조사해 설계에 옵션으로 포함 (근거 인용 필수)

---

## 산출물 (반드시 포함, 순서 고정)

### 1) 최신 Claude 모델 확정 (2026-01-14 기준)

다음을 **공식 출처**로 확정하라:
- [ ] 최신 모델명/리비전
- [ ] 사용 가능한 인터페이스(Claude.ai, API 등)
- [ ] Native Vision 지원/제약
- [ ] Vision 입력 관련 제약 (멀티이미지, 해상도/크기, 컨텍스트, tool-use 가능성 등)
- [ ] "왜 최신인지" 증명 (비교표/순위표 없이, 단일 모델 집중)

---

### 2) Claude Code V2.1.7까지 CHANGELOG 조사 + 기능 활용 설계

다음 형태로 작성하라:

#### a) Feature Inventory (<= v2.1.7)
| 기능 | 옵션 | 제약 | 권장 설정 |
|------|------|------|----------|
| ... | ... | ... | ... |

#### b) Pipeline Impact Mapping
각 기능이 어느 단계(A~H)에 적용되는지 명시

#### c) Enablement Plan
| 기능 | 기본값(default) | 토글(flags) | 실패 시 fallback |
|------|----------------|-------------|-----------------|
| ... | ... | ... | ... |

**원칙:**
- "V2.1.7까지 가능한 기능을 최대한 켠 설계(최대 활용)"
- "안전한 fallback(최소 기능)"을 함께 제시

---

### 3) 전체 파이프라인 설계도 (End-to-End Blueprint)

각 단계별로 다음을 명시하라:
- **목적**
- **입력**
- **출력**
- **실패 모드**
- **가드레일**
- **review_required 트리거 예시**

단계 간 **데이터 계약(data contract)**을 반드시 정의하라.

---

#### A. Ingestion

| 항목 | 내용 |
|------|------|
| **입력** | image(s) |
| **처리** | orientation/rotation 추정, 여백/왜곡/기울기 신호 추출 (실제 보정은 옵션) |
| **출력** | `image_manifest` + `preflight_signals` |
| **review_required 트리거 예** | 과도한 기울기, 저해상도, 그림자, 겹침 |

---

#### B. Text Parse (external)

| 항목 | 내용 |
|------|------|
| **입력** | Mathpix 결과 (LaTeX 또는 data(JSON 구조화)) |
| **출력** | `text_spec` (문제의 "정식 사양(spec)") |
| **review_required 트리거 예** | 수식 누락, 문장 단절, 기호 혼동 가능성 (예: l/1, O/0) |

---

#### C. Vision Parse (layout + diagram extraction)

| 항목 | 내용 |
|------|------|
| **입력** | image(s), `text_spec` |
| **처리** | 레이아웃 블록(번호/본문/수식/그림) 분리 + 그림 영역에서 객체 후보 추출 |
| **출력** | `layout_blocks` + `diagram_candidates` |
| **review_required 트리거 예** | 그림 영역 경계 불명확, 라벨 텍스트 흐림, 겹선/해칭 혼재 |

---

#### D. Alignment & Consistency Check (text ↔ vision)

| 항목 | 내용 |
|------|------|
| **입력** | `text_spec`, `diagram_candidates` |
| **처리** | 텍스트 엔티티(점/직선/함수/조건)와 시각 후보 매칭, 불일치 탐지 |
| **출력** | `alignment_report` + `inconsistencies` (반드시 구조화) |
| **review_required 트리거 예** | 텍스트엔 "P,Q,O"가 있는데 그림 라벨 일부 미검출, 함수명 f/g 혼동 |

---

#### E. Semantic Graph Build (objects + relations + constraints)

| 항목 | 내용 |
|------|------|
| **입력** | `diagram_candidates`, `alignment_report` |
| **처리** | 객체-관계-제약(constraints) 그래프 생성 ("추정"은 근거와 분리) |
| **출력** | `semantic_graph` |
| **review_required 트리거 예** | 교점/접점 판정 불확실, 축 스케일 유무 불명, 음영 영역 경계 해석 다중 가능 |

---

#### F. Regeneration Layer (editable parametric representation)

| 항목 | 내용 |
|------|------|
| **입력** | `text_spec`, `semantic_graph` |
| **처리** | 파라메트릭 표현 생성 (사용자가 수식/파라미터 변경 시 그래프/도형 재생성 가능) |
| **목표1 (최소)** | coefficients/parameters 변경 가능 |
| **목표2 (상위)** | function form 변경 + diagram constraints 유지하며 재생성 |
| **출력 형식** | **Desmos/GeoGebra API 호환** + **자체 JSON** (커스터마이징 지원) |
| **출력** | `regeneration_spec` (가능 범위 명시) + `limitation_notes` |
| **review_required 트리거 예** | 상위 목표 불가/불안정 → "최소 목표로 다운그레이드" 제안과 함께 표시 |

---

#### G. Human-in-the-loop Review (필수)

| 항목 | 내용 |
|------|------|
| **입력** | `layout_blocks`, `semantic_graph`, `alignment_report`, `regeneration_spec` |
| **처리** | "review_required 기반 작업 큐" 구성 (사용자가 빠르게 모호점 발견 및 수정) |
| **출력** | `correction_patch` JSON + `approval_state` |
| **원칙** | Human이 '무엇을 확인해야 하는지'를 찾는 시간을 최소화 ("검수 우선순위" 제공) |

---

#### H. Export Spec (for downstream DOCX generation)

| 항목 | 내용 |
|------|------|
| **입력** | 승인된 `layout_blocks` + `semantic_graph` + `regeneration_spec` |
| **출력** | `docx_generation_spec` (설계/명세 수준) |
| **주의** | 구현 코드(Python 등)나 CLI 사용법은 쓰지 말고, **생성용 명세(데이터/규칙)만 작성** |

---

### 4) JSON 스키마 제안 (인터랙티브 확장 전제, review_required 최우선)

최소 2개 스키마를 제시하라:

---

#### (I) Schema-Layout (JSON)

**용도:** 문제 단위 분할 + 블록(본문/수식/그림) + 상대 배치

**필수 요구:**
- [ ] `versioning`: schema_version, instance_version
- [ ] `stable IDs`: id 규칙 (UUID 또는 deterministic)
- [ ] `extensibility`: extension_points / vendor_fields / $defs 전략
- [ ] `provenance`: text_source(Mathpix) vs vision_source(image) 명시
- [ ] `uncertainty` + `review_required`: 블록 단위/필드 단위로 포함

**실제 채워진 JSON 예시 1개 이상 제공** (추상 템플릿 금지)

---

#### (II) Schema-Diagram (JSON)

**용도:** 좌표계/도형/그래프/라벨/음영/선 스타일 + 관계 + 제약(constraints)

**필수 요구 (특히 강화):**

| 필드 | 설명 |
|------|------|
| `asserted vs inferred` 분리 | 관계 표현에서 inferred는 `evidence_refs` 필수 |
| `ambiguity_set` | 복수 해석 후보 + `selection_status` |
| `review_required` | true/false |
| `review_severity` | {blocker, high, medium, low} (수치 금지, 서열만) |
| `review_reason_code` | 예: LABEL_MISSING, INTERSECTION_UNCERTAIN, AXIS_SCALE_UNKNOWN, SHADED_REGION_AMBIGUOUS |
| `evidence_refs` | 근거 (텍스트 토큰 범위, 이미지 영역 bbox/polygon 참조) |
| `suggested_quick_fix` | Human이 바로 할 수 있는 액션 (예: "P 라벨 위치 후보 2개 중 선택") |
| `downstream_risk` | 이 불확실성이 재생성/문제 편집에 미치는 위험 서술 (정성) |

- [ ] `unknown/null 처리 규칙` 스키마 수준에서 명시
- [ ] `Human review 큐 생성 규칙` 스키마 수준에서 명시

**실제 채워진 JSON 예시 1개 이상 제공** (추상 템플릿 금지)

---

### 5) Human-in-the-loop 설계 (필수, review_required 중심)

**목표:** 모호점 탐지 시간을 단축하기 위해, review_required 항목을 "작업(Task) 단위"로 변환

#### 기능 요구사항

| 기능 | 설명 |
|------|------|
| **a) Review Queue** | review_severity/다운스트림 위험 기반으로 자동 정렬 |
| **b) Evidence Overlay** | image 위에 bbox/polygon + 해당 text_spec 근거 하이라이트 동시 표시 |
| **c) One-click Fix** | suggested_quick_fix 템플릿 제공 (선택/라벨링/관계 지정/영역 경계 수정) |
| **d) Consistency Gate** | 승인 전에 alignment_report의 blocker를 0으로 만드는 규칙 |
| **e) Correction Patch** | 수정사항을 correction_patch JSON으로 기록, 재파싱/재정합 단계에 주입 |

#### correction_patch JSON 최소 스키마

```json
{
  "operation": "add | update | delete",
  "target_id": "참조 ID",
  "reason": "수정 사유",
  "evidence": "선택적 근거",
  "author": "human | model",
  "timestamp": "ISO 8601"
}
```

#### 재시도 정책

| 유형 | 설명 |
|------|------|
| **전체 재파싱** | 전체 이미지/문제 재처리 |
| **부분 재파싱** | 그림 영역만, 라벨만 등 선택적 재처리 |
| **프롬프트 재질문 템플릿** | 좁은 지시 (예: "축 스케일 유무만 확인해라") |

---

### 6) 한계와 대안 (검색 기반, 상위 목표 달성 옵션 포함)

#### Claude Native Vision 가능/어려운 범위

**사례 중심으로 정리** (수치 평가 금지)

| 가능한 범위 | 어려운 범위 |
|------------|------------|
| ... | ... |

#### 추가 기술 스택 옵션 (근거 링크 필수)

"함수 형태 변경 + 도형 관계 재생성"을 위해 필요한 외부 솔루션/기법:

| 옵션 | 해결하는 문제 | 파이프라인 적용 단계 | Human review 감소 효과 |
|------|-------------|-------------------|----------------------|
| Vectorization | ... | E/F | ... |
| Graph Digitization | ... | ... | ... |
| Constraint Solving | ... | ... | ... |
| Symbolic Math (CAS: SymPy 등) | ... | ... | ... |
| Diagram Parsing Tools/Research | ... | ... | ... |

각 옵션에 대해:
- 무엇을 해결하는지 (예: 축 스케일 복원, 곡선 방정식 추정, 관계 제약 만족)
- 파이프라인에 어디에 끼우는지 (예: E/F 단계)
- Human review를 어떻게 줄이는지 (어떤 review_reason_code를 자동 해소하는지)

---

## 작성 규칙 (리마인더)

- [ ] **한국어**로 작성하되, 기술 키워드/프로그래밍 언어/포맷은 **English**로 표기
- [ ] **단정적 주장 금지**: 근거(인용/관찰/문서 링크)와 함께
- [ ] **수치 점수/퍼센트/정량 랭킹 금지**
- [ ] **보고서 형태**로, 섹션 헤더와 체크리스트를 활용해 읽기 쉽게 작성

---

## 시작 지시

1. **2026-01-14 기준 최신 Claude 모델**을 "공식 출처"로 확정하라.
2. **Claude Code V2.1.7까지의 CHANGELOG**를 조사하고, "V2.1.7까지의 기능을 최대한 활용"하는 Enablement plan을 포함하라.
3. 위 순서대로 **전체 파이프라인 설계도**를 작성하라.

---

## 메타 정보

| 항목 | 값 |
|------|-----|
| 작성 목적 | Claude 웹/앱 Deep Research 기능 입력용 |
| V2.1.7 정의 | Claude Code 버전 |
| Mathpix 출력 형식 | LaTeX 또는 data (JSON 구조화) |
| 수학 문제 범위 | 초중고 전체 |
| Regeneration 출력 타겟 | Desmos/GeoGebra API 호환 + 자체 JSON |

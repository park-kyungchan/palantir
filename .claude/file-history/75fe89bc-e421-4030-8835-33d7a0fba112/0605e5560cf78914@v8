# cow/ Pipeline V3 구현 계획

> **Version:** 3.4 | **Status:** DRAFT | **Date:** 2026-01-19
> **Goal:** Mathpix + Gemini 3.0 Pro + Claude Vision 멀티-스테이지 파이프라인
> **Auto-Compact Safe:** This file persists across context compaction

---

## 1. 현재 상태 분석

### 1.1 기존 아키텍처 (8-Stage)

```
A. INGESTION → B. TEXT PARSE → C. VISION PARSE → D. ALIGNMENT
                 (Mathpix)      (YOLO+Gemini)
      ↓                                              ↓
H. EXPORT ← G. HUMAN REVIEW ← F. REGENERATION ← E. SEMANTIC GRAPH
```

### 1.2 핵심 변경 결정 (Q&A 기반)

| # | 질문 | 결정 |
|---|------|------|
| Q1 | Stage C는 왜 필요? | YOLO 제거 → Gemini 3.0 Pro로 다이어그램 해석 |
| Q2 | 고도화 방향? | Multi-Stage: Mathpix(유지) + Gemini + Claude |
| Q3 | HITL 위치? | Stage E 직후 (기존 F→G를 G→F로 순서 변경) |
| Q4 | Mathpix 호출 위치? | Stage B `_run_stage_b()` (pipeline.py:915-998) |
| **Q5** | Mathpix 대체? | **❌ 대체하지 않음. Mathpix 유지, Gemini는 별도 Stage** |

---

## 2. 목표 아키텍처 (V3.2)

### 2.1 새로운 파이프라인 흐름 (9-Stage)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    V3.2 PIPELINE ARCHITECTURE (9-Stage)                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  A. INGESTION → B. TEXT PARSE → C. VISION PARSE → D. CROSS-VERIFY          │
│                  (Mathpix OCR)   (Gemini 3.0 Pro)  (Claude Vision)          │
│                     [수식]        [다이어그램]      [교차검증]              │
│                                                                             │
│                              ↓                                              │
│                                                                             │
│  I. EXPORT ← H. REGENERATION ← G. HUMAN REVIEW ← F. SEMANTIC ← E. ALIGNMENT│
│                                 (HITL)            GRAPH                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stage별 역할 (V3.3)

| Stage | 이름 | 처리 엔진 | 역할 | 비고 |
|-------|------|----------|------|------|
| **A** | INGESTION | - | 이미지 로드, 전처리 | |
| **B** | TEXT_PARSE | **Mathpix** | 수식/텍스트 OCR | ✅ 오차 없음 가정 |
| **C** | VISION_PARSE | **Gemini 3.0 Pro** | 다이어그램/그래프 해석 | 💰 비용 최적화 |
| **D** | REASONING_VERIFY | **Claude** | 추론 기반 최종검증 + HITL | 🧠 추론 + 검증 |
| **E** | ALIGNMENT | - | Text ↔ Vision 정렬 | |
| **F** | SEMANTIC_GRAPH | - | 의미 그래프 구축 | |
| **G** | REGENERATION | - | 재생성 | |
| **H** | EXPORT | - | 최종 출력 (JSON, PDF, DOCX) | |

### 2.3 Stage B-C-D 상세 역할 분담

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PARSING & VERIFICATION FLOW                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────┐       │
│  │  Stage B    │     │  Stage C    │     │       Stage D           │       │
│  │  Mathpix    │     │  Gemini     │     │       Claude            │       │
│  ├─────────────┤     ├─────────────┤     ├─────────────────────────┤       │
│  │ • 수식 OCR  │     │ • 도형 감지 │     │ • B+C 결과 추론 검증   │       │
│  │ • 텍스트    │  +  │ • 그래프   │  →  │ • 수학적 일관성 체크   │       │
│  │ • LaTeX     │     │ • 다이어그램│     │ • 오류 플래깅          │       │
│  │             │     │ • 좌표/관계 │     │ • HITL 트리거          │       │
│  └─────────────┘     └─────────────┘     └─────────────────────────┘       │
│       ↓                    ↓                        ↓                       │
│    TextSpec            VisionSpec           ReasoningVerifyResult           │
│  (신뢰도 100%)        (비용 최적화)         (최종 판정 + HITL 여부)         │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Stage B: Mathpix (텍스트 파싱) - 신뢰도 100%

| 항목 | 내용 |
|------|------|
| **입력** | 원본 이미지 |
| **출력** | `TextSpec` (latex, text, line_segments) |
| **가정** | 오차 없음 (Ground Truth로 취급) |
| **비용** | ~$0.04/이미지 |

#### Stage C: Gemini (다이어그램 해석) - 비용 최적화

| 항목 | 내용 |
|------|------|
| **입력** | 원본 이미지 + Stage B TextSpec |
| **출력** | `VisionSpec` (elements, diagrams, graphs, coordinates) |
| **역할** | 도형 감지, 그래프 분석, 다이어그램 이해, 이미지-텍스트 매핑 |
| **비용 최적화** | 아래 "비용 절감 전략" 참조 |

**Stage C 비용 절감 전략:**

| 전략 | 설명 | 절감 효과 |
|------|------|----------|
| **조건부 호출** | Stage B에서 `has_diagram=false`면 Stage C 스킵 | ~40% |
| **Context 최적화** | 200K 이하 유지 (가격 2배 차이) | ~50% |
| **Batch 처리** | 여러 이미지 묶어서 1회 호출 | ~20% |
| **캐싱** | 동일 이미지 재처리 방지 | 가변 |

#### Stage D: Claude (추론 검증 + HITL) - 최종 판정

| 항목 | 내용 |
|------|------|
| **입력** | Stage B TextSpec + Stage C VisionSpec |
| **출력** | `ReasoningVerifyResult` (verified_data, confidence, hitl_required, reasoning_trace) |
| **역할** | 추론 기반 검증, 수학적 일관성 체크, HITL 트리거 |
| **비용** | $0.00 (Claude Max 구독) |

**Stage D 추론 검증 로직:**

```python
class ReasoningVerifier:
    """Claude-based reasoning verification for Stage D."""

    async def verify(
        self,
        text_spec: TextSpec,      # Stage B (신뢰 100%)
        vision_spec: VisionSpec,  # Stage C
    ) -> ReasoningVerifyResult:
        """
        추론 기반 검증:
        1. B+C 데이터 통합
        2. 수학적 일관성 체크 (수식 ↔ 그래프 매칭)
        3. 논리적 오류 감지
        4. 신뢰도 점수 산출
        5. HITL 필요 여부 결정
        """
        pass

class ReasoningVerifyResult(MathpixBaseModel):
    verified_data: MergedMathData  # 최종 병합 데이터
    confidence: float              # 0.0-1.0
    hitl_required: bool            # True면 Human Review 필요
    hitl_reason: Optional[str]     # HITL 필요 이유
    reasoning_trace: str           # 추론 과정 기록
    flagged_items: List[FlaggedItem]  # 의심 항목 목록
```

### 2.4 Stage 순서 변경 상세

```
V2 (8-Stage):  A → B → C → D → E → F → G → H
V3.3 (8-Stage): A → B → C → D → E → F → G → H
                     ↑   ↑   ↑
              Mathpix Gemini Claude+HITL
```

| Stage | V2 | V3.3 | 변경 내용 |
|-------|-----|------|----------|
| A | INGESTION | INGESTION | 유지 |
| B | TEXT_PARSE (Mathpix) | TEXT_PARSE (Mathpix) | 유지 |
| C | VISION_PARSE (YOLO+Gemini) | VISION_PARSE (Gemini) | YOLO 제거 |
| D | ALIGNMENT | **REASONING_VERIFY (Claude+HITL)** | ⭐ 신규 |
| E | SEMANTIC_GRAPH | ALIGNMENT | 기존 D |
| F | REGENERATION | SEMANTIC_GRAPH | 기존 E |
| G | HUMAN_REVIEW | REGENERATION | 기존 F (HITL은 D로 이동) |
| H | EXPORT | EXPORT | 유지 |

**핵심 변경:** HITL이 Stage G에서 **Stage D**로 이동 (추론 검증과 통합)

### 2.6 비용 구조

| Component | Cost/Image | 비고 |
|-----------|-----------|------|
| Mathpix | ~$0.04 | 수식 OCR (신뢰 100%) |
| Gemini 3.0 Pro | ~$0.005 | 다이어그램 해석 (비용 최적화 적용) |
| Claude | $0.00 | Claude Max 구독 (추론 검증 + HITL) |
| **Total** | **~$0.045** | 비용 절감 + 품질 최대화 |

**비용 최적화 후 예상:**
- 조건부 호출 (다이어그램 없으면 스킵): ~40% 절감
- Context 최적화: ~50% 절감
- **최적화 적용 시 Gemini 비용: $0.01 → $0.005**

---

## 3. 파일 변경 계획

### 3.1 제거할 파일

```
cow/src/mathpix_pipeline/
└── vision/
    ├── yolo_detector.py        # YOLO 제거 → Gemini가 대체
    └── hybrid_merger.py        # 불필요
```

### 3.2 수정할 파일

```
cow/src/mathpix_pipeline/
├── clients/
│   └── mathpix.py              # 유지 (Stage B)
├── vision/
│   └── gemini_client.py        # → Gemini 3.0 Pro 업그레이드 (Stage C)
├── pipeline.py                 # Stage 추가 (D), 순서 변경 (G↔H)
├── config.py                   # Claude 설정 추가
└── schemas/
    └── common.py               # PipelineStage enum에 CROSS_VERIFY 추가
```

### 3.3 신규 생성할 파일

```
cow/src/mathpix_pipeline/
└── vision/
    └── cross_verifier.py       # Claude Vision 교차검증 (Stage D)
```

---

## 4. 구현 Phase

### Phase 1: Stage C 업그레이드 (YOLO → Gemini 3.0 Pro)

**영향 범위:**
- `vision/yolo_detector.py` → 제거
- `vision/hybrid_merger.py` → 제거
- `vision/gemini_client.py` → Gemini 3.0 Pro 업그레이드

**산출물:**
- [ ] `GeminiVisionClient` 업그레이드 (3.0 Pro)
- [ ] `GeminiConfig` 업데이트
- [ ] Stage C 테스트 케이스

### Phase 2: Stage D 추가 (Claude Vision 교차검증)

**영향 범위:**
- `vision/cross_verifier.py` → 신규 생성
- `schemas/common.py` → `PipelineStage.CROSS_VERIFY` 추가
- `pipeline.py` → `_run_stage_d()` 추가
- `config.py` → `ClaudeConfig` 추가

**산출물:**
- [ ] `CrossVerifier` 클래스
- [ ] `CrossVerifyResult` 스키마
- [ ] `ClaudeConfig` Pydantic 모델
- [ ] Stage D 테스트 케이스

### Phase 3: Stage 순서 재배열 (9-Stage)

**영향 범위:**
- `pipeline.py:process()` → Stage 실행 순서 변경
- Stage E~I 재넘버링
- HITL을 Regeneration 앞으로 이동

**산출물:**
- [ ] 9-Stage 파이프라인
- [ ] 통합 테스트 케이스

### Phase 4: Config/Schema 정리

**영향 범위:**
- `schemas/common.py` → PipelineStage enum 업데이트
- `config.py` → Claude 설정 추가
- `__init__.py` → export 정리

**산출물:**
- [ ] 업데이트된 PipelineStage enum
- [ ] 정리된 config.py
- [ ] 마이그레이션 가이드

---

## 5. 상세 설계

### 5.1 Stage B: MathpixClient (유지)

```python
# clients/mathpix.py (기존 유지)
class MathpixClient:
    """Mathpix API client for Stage B - 수식 OCR."""

    async def process_image(
        self,
        image_bytes: bytes,
        image_id: str,
    ) -> TextSpec:
        """Process image with Mathpix API.

        Returns:
            TextSpec: latex, line_segments, confidence
        """
        # 기존 로직 유지
        pass
```

### 5.2 Stage C: GeminiVisionClient (업그레이드)

```python
# vision/gemini_client.py (업그레이드)
class GeminiVisionClient:
    """Gemini 3.0 Pro Vision client for Stage C - 다이어그램 해석."""

    def __init__(self, config: GeminiConfig):
        self.config = config
        self.model = "gemini-3.0-pro"  # 버전 업그레이드

    async def process_image(
        self,
        image_bytes: bytes,
        image_id: str,
    ) -> VisionSpec:
        """Process image with Gemini 3.0 Pro.

        Returns:
            VisionSpec: elements, diagrams, graphs, confidence
        """
        # TODO(human): Implement Gemini 3.0 Pro API call
        pass
```

### 5.3 Stage D: ReasoningVerifier (5-Phase 설계)

Stage D는 Claude 기반 추론 검증 + HITL + Adaptive Calibration을 담당합니다.

#### 5.3.1 5-Phase 구조

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    STAGE D: REASONING VERIFICATION (5-Phase)                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1           Phase 2           Phase 3           Phase 4             │
│  데이터 병합  →    추론 검증    →    신뢰도 산출  ↔    HITL 결정           │
│                                          │                 │               │
│                                          └──── Calibration Loop ────┘      │
│                                                     │                       │
│                                                     ↓                       │
│                                               Phase 5                       │
│                                            HITL 실행/완료                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Phase | 이름 | 역할 | 산출물 |
|-------|------|------|--------|
| 1 | **데이터 병합** | Stage B + C 결과 통합 | `MergedMathData` |
| 2 | **추론 검증** | 수학적 일관성 체크, 논리 오류 감지 | `List[VerificationCheck]` |
| 3 | **신뢰도 산출** | 동적 threshold 기반 confidence 계산 | `ConfidenceBreakdown` |
| 4 | **HITL 결정** | 사람 검토 필요 여부 판단 + feedback 수집 | `HITLDecision` |
| 5 | **HITL 실행/완료** | 최종 검토 및 데이터 확정 | `ReasoningVerifyResult` |

#### 5.3.2 Phase 1: 데이터 병합

```python
class MergedMathData(MathpixBaseModel):
    """Stage B + C 병합 결과."""

    # Stage B (Mathpix) - Ground Truth
    text_content: str              # 원본 텍스트
    latex_equations: List[str]     # LaTeX 수식
    line_segments: List[LineSegment]

    # Stage C (Gemini)
    diagrams: List[DiagramSpec]    # 다이어그램 구조
    graphs: List[GraphSpec]        # 그래프 데이터
    visual_elements: List[VisualElement]

    # 병합 메타데이터
    merge_timestamp: datetime
    source_confidence: Dict[str, float]  # {"mathpix": 1.0, "gemini": 0.85}
```

#### 5.3.3 Phase 2: 추론 검증

```python
class VerificationCheck(MathpixBaseModel):
    """개별 검증 항목."""

    check_type: str                # "equation_graph_match", "symbol_consistency", etc.
    target_element: str            # 검증 대상 ID
    passed: bool
    confidence: float              # 0.0-1.0
    reasoning: str                 # Claude 추론 과정
    evidence: List[str]            # 근거 데이터

class ReasoningVerifier:
    """Claude-based reasoning verification."""

    async def verify_equation_graph_match(
        self,
        equations: List[str],
        graphs: List[GraphSpec]
    ) -> VerificationCheck:
        """수식 ↔ 그래프 일치 검증."""
        pass

    async def verify_symbol_consistency(
        self,
        merged_data: MergedMathData
    ) -> VerificationCheck:
        """기호 일관성 검증 (같은 변수가 다른 의미로 사용되는지)."""
        pass

    async def verify_diagram_labels(
        self,
        text: str,
        diagrams: List[DiagramSpec]
    ) -> VerificationCheck:
        """다이어그램 라벨 ↔ 텍스트 참조 검증."""
        pass
```

#### 5.3.4 Phase 3-4: Adaptive Calibration 시스템

```python
class ConfidenceBreakdown(MathpixBaseModel):
    """신뢰도 상세 분해."""

    overall_confidence: float      # 종합 신뢰도
    component_scores: Dict[str, float]  # 항목별 점수
    threshold_used: float          # 적용된 threshold
    below_threshold_items: List[str]  # threshold 미달 항목

class HITLDecision(MathpixBaseModel):
    """HITL 결정."""

    required: bool
    reason: Optional[str]
    flagged_items: List[FlaggedItem]
    priority: str                  # "high", "medium", "low"

class FlaggedItem(MathpixBaseModel):
    """HITL 플래그 항목."""

    item_id: str
    item_type: str                 # "equation", "diagram", "graph"
    confidence: float
    reason: str
    suggested_action: str          # "verify", "correct", "reject"

class CalibrationHistory(MathpixBaseModel):
    """Calibration 이력 (학습 데이터)."""

    timestamp: datetime
    confidence_at_decision: float
    human_feedback: str            # "approve", "reject", "correct"
    correction_details: Optional[Dict]

class ConfidenceCalibrator:
    """HITL 피드백 기반 Confidence Threshold 동적 조정."""

    def __init__(self, initial_threshold: float = 0.85):
        self.current_threshold = initial_threshold
        self.history: List[CalibrationHistory] = []
        self.calibration_score = 0.0

    async def calibration_loop(
        self,
        merged_data: MergedMathData,
        checks: List[VerificationCheck]
    ) -> CalibrationResult:
        """
        Phase 3-4 반복 루프.

        진입조건 충족 시 Phase 5로 이동.
        """
        iteration = 0

        while not self._should_exit_to_phase5(iteration):
            # Phase 3: 신뢰도 산출
            confidence = self._calculate_confidence(
                checks, merged_data,
                threshold=self.current_threshold
            )

            # Phase 4: HITL 결정
            hitl_decision = self._decide_hitl(confidence, checks)

            if hitl_decision.required:
                # HITL 실행 및 피드백 수집
                feedback = await self._execute_hitl(hitl_decision)

                # 이력 기록
                self.history.append(CalibrationHistory(
                    timestamp=datetime.utcnow(),
                    confidence_at_decision=confidence.overall_confidence,
                    human_feedback=feedback.decision,
                    correction_details=feedback.corrections
                ))

                # Threshold 조정
                self._adjust_threshold(feedback)

                # Calibration 점수 재계산
                self.calibration_score = self._calculate_calibration_score()

            iteration += 1

        # Phase 5 진입
        return CalibrationResult(
            final_threshold=self.current_threshold,
            total_iterations=iteration,
            calibration_score=self.calibration_score,
            ready_for_phase5=True
        )

    def _should_exit_to_phase5(self, iteration: int) -> bool:
        """Phase 5 진입조건 확인."""
        conditions = Phase5Readiness(
            calibration_score=self.calibration_score >= 0.95,
            min_samples=len(self.history) >= 50,
            threshold_stability=self._check_threshold_stability(),
            recent_accuracy=self._check_recent_accuracy()
        )
        return conditions.ready

    def _adjust_threshold(self, feedback: HITLFeedback):
        """피드백 기반 threshold 조정."""
        if feedback.decision == "approve":
            # Confidence가 높았는데 approve → threshold 약간 낮출 수 있음
            pass
        elif feedback.decision == "reject":
            # Confidence가 높았는데 reject → threshold 높여야 함
            self.current_threshold = min(0.95, self.current_threshold + 0.02)
        elif feedback.decision == "correct":
            # 수정이 필요했음 → threshold 미세 조정
            self.current_threshold = min(0.95, self.current_threshold + 0.01)
```

#### 5.3.5 Phase 5 진입조건 (Phase5Readiness)

```python
class Phase5Readiness(MathpixBaseModel):
    """Phase 5 진입 조건."""

    calibration_score: bool = False    # >= 0.95
    min_samples: bool = False          # >= 50 HITL 샘플
    threshold_stability: bool = False  # 최근 10회 threshold 변동 < 5%
    recent_accuracy: bool = False      # 최근 20건 정확도 >= 90%

    @property
    def ready(self) -> bool:
        return all([
            self.calibration_score,
            self.min_samples,
            self.threshold_stability,
            self.recent_accuracy
        ])

class CalibrationResult(MathpixBaseModel):
    """Calibration 최종 결과."""

    final_threshold: float
    total_iterations: int
    calibration_score: float
    ready_for_phase5: bool
    history_summary: Dict[str, int]  # {"approve": 45, "reject": 3, "correct": 2}
```

#### 5.3.6 최종 출력 스키마

```python
class ReasoningVerifyResult(MathpixBaseModel):
    """Stage D 최종 출력."""

    # 핵심 결과
    verified_data: MergedMathData
    confidence: float              # 최종 신뢰도
    confidence_breakdown: ConfidenceBreakdown

    # 검증 상세
    verification_checks: List[VerificationCheck]
    flagged_items: List[FlaggedItem]

    # HITL 정보
    hitl_executed: bool
    hitl_iterations: int
    calibration_result: CalibrationResult

    # 추론 기록
    reasoning_trace: str           # Claude 추론 과정 전체 기록

    # 메타데이터
    stage_timing_ms: float
    model_used: str                # "claude-3-opus"
```

#### 5.3.7 Human-in-the-Loop → Human-on-the-Loop 전환

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         HITL → HOTL TRANSITION                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  초기 (0-50 샘플)         중기 (50-200 샘플)      성숙기 (200+ 샘플)       │
│  ──────────────────     ──────────────────────   ─────────────────────     │
│  Human-in-the-Loop      Hybrid Mode              Human-on-the-Loop         │
│  • 모든 결과 검토        • Low conf만 검토        • 예외만 알림             │
│  • 직접 수정             • 배치 승인              • 자동 처리               │
│  • 학습 데이터 축적      • Threshold 안정화       • 모니터링만              │
│                                                                             │
│  Calibration Score:     Calibration Score:       Calibration Score:        │
│      0.0 - 0.8              0.8 - 0.95              0.95+                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.4 Stage G: Human Review (HITL)

```python
# human_review/ 기존 모듈 활용
class HumanReviewInput:
    semantic_graph: SemanticGraph
    cross_verify_report: CrossVerifyResult
    flagged_items: List[FlaggedItem]  # confidence < threshold

class HumanReviewOutput:
    approved_nodes: List[str]
    rejected_nodes: List[str]
    corrected_nodes: Dict[str, Correction]
```

---

## 6. 리스크 및 완화 전략

| Risk | Impact | Mitigation |
|------|--------|------------|
| Gemini 수식 OCR 정확도 | High | Claude Vision 교차검증으로 보완 |
| Claude Max API 제한 | Medium | Rate limiting 구현 |
| Stage 순서 변경 부작용 | Medium | 통합 테스트 강화 |
| 기존 테스트 실패 | Low | 테스트 케이스 업데이트 |

---

## 7. 질문 로그 (Q&A History)

| # | Date | Question | Answer |
|---|------|----------|--------|
| Q1 | 2026-01-19 | Stage C는 왜 필요? | YOLO: 도형 bbox, Gemini: 해석 |
| Q2 | 2026-01-19 | 고도화 방향? | Multi-Stage: Mathpix + Gemini + Claude |
| Q3 | 2026-01-19 | HITL 위치? | Stage D (Claude 추론 검증과 통합) |
| Q4 | 2026-01-19 | Mathpix 호출 위치? | Stage B `_run_stage_b()` (pipeline.py:915-998) |
| Q5 | 2026-01-19 | Mathpix 대체? | ❌ 대체 안함. Mathpix 유지 (신뢰 100%) |
| Q6 | 2026-01-19 | Stage B-C-D 역할? | B: Mathpix(텍스트), C: Gemini(다이어그램+비용최적화), D: Claude(추론검증+HITL) |
| **Q7** | 2026-01-19 | Stage D 상세설계? | 5-Phase: 데이터병합 → 추론검증 → 신뢰도산출 → HITL결정 → HITL실행 |
| **Q8** | 2026-01-19 | Adaptive Calibration? | Phase3-4 반복으로 threshold 동적 조정, Phase5 진입조건 충족 시 종료 |

---

## 8. 다음 단계

구현 착수 전 확인이 필요한 사항:

1. **Gemini 3.0 Pro API 접근** - API 키 발급 완료?
2. **Claude Max API 엔드포인트** - Vision API 접근 방법 확인
3. **기존 테스트 보존** - 마이그레이션 중 테스트 유지 전략
4. **롤백 계획** - V2 → V3 실패 시 복구 방법

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-01-19 | 1.0 | Initial Q&A (Stage C 목적) |
| 2026-01-19 | 2.0 | Gemini 비용 분석, 고도화 방안 추가 |
| 2026-01-19 | 3.0 | 최종 아키텍처 결정 (Option B + Claude + HITL) |
| 2026-01-19 | 3.1 | 전체 재정리 - 구현 계획 초안 완성 |
| 2026-01-19 | 3.2 | Q5: Mathpix 유지 결정 - Multi-Stage 아키텍처 |
| 2026-01-19 | 3.3 | Q6: Stage B-C-D 역할 명확화, HITL → Stage D 통합, 비용 최적화 |
| 2026-01-19 | **3.4** | Q7-8: Stage D 5-Phase 상세설계 + Adaptive Calibration 시스템 |

---

**Protocol Compliance:** orchestrator_protocol_v4.1.yaml

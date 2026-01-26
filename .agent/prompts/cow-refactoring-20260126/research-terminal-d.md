# Research Report: COW Pipeline Stage G Integration & B+C Parallel (Terminal-D)

> Generated: 2026-01-26T16:15:00Z
> Clarify Reference: cow-refactoring-20260126
> Workload ID: cow-refactoring-20260126
> Scope: Stage G 완전 통합 + B+C asyncio.gather() 병렬화
> Assigned To: Terminal-D

---

## L1 Summary (< 500 tokens)

### Mission
1. ISSUE-003 Option A 실행: Stage G Human Review 완전 통합
2. ISSUE-004 Option A 실행: Stage B+C asyncio.gather() 병렬화

### Key Deliverables
| Priority | Task | New/Modify | Effort | Description |
|----------|------|------------|--------|-------------|
| 1 | D-1 | `stages/human_review_stage.py` | ~150줄 | BaseStage wrapper for Stage G |
| 2 | D-2 | `human_review/queue_manager.py` | 수정 | 콜백 핸들러 추가 |
| 3 | D-3 | `pipeline.py` | 수정 | Stage G 완전 통합 |
| 4 | D-4 | `pipeline.py` | 수정 | B+C asyncio.gather() |
| 5 | D-5 | `schemas/threshold.py` | 수정 | FeedbackStats 업데이트 로직 |

### Dependencies
- Terminal-C의 BaseStage 마이그레이션 완료 권장 (하지만 독립적 진행 가능)

### Success Criteria
- [ ] Stage G가 BaseStage 패턴으로 래핑됨
- [ ] Human Review 완료 시 FeedbackStats 자동 업데이트
- [ ] B+C 병렬 실행으로 ~40% 성능 향상
- [ ] 전체 테스트 통과

---

## L2 Detailed Analysis

### 2.1 Stage G 현재 상태 분석

**human_review/ 모듈 구조**:
```
cow/src/mathpix_pipeline/human_review/
├── __init__.py
├── queue_manager.py      # ReviewQueueManager - 큐 관리
├── annotation_workflow.py # AnnotationWorkflow - 리뷰 플로우
├── priority_scorer.py    # PriorityScorer - 우선순위 계산
└── exceptions.py         # HumanReviewError 등
```

**pipeline.py 내 Stage G** (lines 1313-1379):
```python
async def _run_stage_g(self, result, options):
    """Stage G: Human Review (optional)"""
    if not options.enable_human_review:
        return None

    timing = StageTiming(stage=PipelineStage.HUMAN_REVIEW)
    result.stage_timings.append(timing)

    try:
        # 현재: 큐에 등록만 하고 끝
        review_items = self._collect_review_items(result)
        self._review_queue.add_items(review_items)
        timing.complete(success=True)
        return {"queued_items": len(review_items)}
    except Exception as e:
        timing.complete(success=False, error=str(e))
        return None
```

**문제점**:
1. 큐 등록만 하고 리뷰 완료 대기 없음
2. 리뷰 결과가 파이프라인에 반영되지 않음
3. FeedbackStats 업데이트 없음 (Layer 3 Threshold 학습 불가)

### 2.2 Stage G 완전 통합 목표

**목표 플로우**:
```
pipeline.process()
    ↓
Stage E (SemanticGraph) → low confidence nodes 감지
    ↓
Stage G (Human Review)
    ├─ 1. 리뷰 필요 항목 수집
    ├─ 2. ReviewQueueManager에 등록
    ├─ 3. 리뷰 완료 대기 (옵션: sync/async)
    ├─ 4. 리뷰 결과 적용
    └─ 5. FeedbackStats 업데이트 (Layer 3)
    ↓
Stage F (Regeneration) → 수정된 그래프로 재생성
```

**두 가지 모드 지원**:

1. **Sync Mode** (blocking):
   - 리뷰 완료까지 대기
   - 실시간 품질 보증 필요 시

2. **Async Mode** (non-blocking):
   - 큐 등록 후 즉시 반환
   - 리뷰 완료 시 콜백으로 후처리
   - 배치 처리 시 효율적

### 2.3 B+C 병렬화 분석

**현재 상태** (`pipeline.py` process() 내):
```python
# 순차 실행
text_spec = await self._run_stage_b(ingestion_spec, result)
vision_spec = await self._run_stage_c(ingestion_spec, text_spec, result)
```

**Stage C의 text_spec 의존성 확인**:
```python
async def _run_stage_c(self, ingestion_spec, text_spec, result):
    # text_spec은 fallback 힌트로만 사용
    # YOLO + Claude 우선 실행, text_spec 없어도 동작
    ...
```

**결론**: Stage C는 text_spec 없이도 동작 가능 → 병렬화 가능

**목표 상태**:
```python
# 병렬 실행
text_result, vision_result = await asyncio.gather(
    self._run_stage_b(ingestion_spec, result),
    self._run_stage_c(ingestion_spec, None, result),
    return_exceptions=True
)

# 에러 처리
if isinstance(text_result, Exception):
    result.add_error(f"Stage B failed: {text_result}")
    text_spec = None
else:
    text_spec = text_result

if isinstance(vision_result, Exception):
    result.add_error(f"Stage C failed: {vision_result}")
    vision_spec = None
else:
    vision_spec = vision_result
```

---

## L3 Implementation Tasks

### Task D-1: HumanReviewStage 생성

**파일**: `cow/src/mathpix_pipeline/stages/human_review_stage.py`

```python
from dataclasses import dataclass, field
from typing import Any, Optional, List
from enum import Enum

from ..schemas.common import PipelineStage
from ..schemas.semantic_graph import SemanticGraph, SemanticNode
from ..schemas.threshold import FeedbackStats
from ..human_review import ReviewQueueManager, ReviewItem, ReviewResult
from .base import BaseStage, ValidationResult, StageMetrics, StageExecutionError


class ReviewMode(Enum):
    SYNC = "sync"      # 리뷰 완료까지 대기
    ASYNC = "async"    # 큐 등록 후 즉시 반환


@dataclass
class HumanReviewStageConfig:
    mode: ReviewMode = ReviewMode.ASYNC
    timeout_seconds: float = 300.0  # sync 모드 타임아웃
    min_confidence_threshold: float = 0.6  # 리뷰 필요 기준
    auto_approve_above: float = 0.95  # 자동 승인 기준
    feedback_stats: Optional[FeedbackStats] = None


@dataclass
class HumanReviewInput:
    semantic_graph: SemanticGraph
    image_id: str
    pipeline_result: Any  # PipelineResult


@dataclass
class HumanReviewOutput:
    reviewed_graph: SemanticGraph
    review_summary: dict
    feedback_stats_delta: Optional[FeedbackStats]


class HumanReviewStage(BaseStage[HumanReviewInput, HumanReviewOutput]):
    """Stage G: Human-in-the-Loop Review"""

    def __init__(
        self,
        config: Optional[HumanReviewStageConfig] = None,
        queue_manager: Optional[ReviewQueueManager] = None,
    ):
        super().__init__(config or HumanReviewStageConfig())
        self._queue_manager = queue_manager or ReviewQueueManager()

    @property
    def stage_name(self) -> PipelineStage:
        return PipelineStage.HUMAN_REVIEW

    def validate(self, input_data: HumanReviewInput) -> ValidationResult:
        result = ValidationResult()
        if not input_data.semantic_graph:
            result.add_error("SemanticGraph is required")
        if not input_data.semantic_graph.nodes:
            result.add_warning("Empty graph - nothing to review")
        return result

    async def _execute_async(
        self,
        input_data: HumanReviewInput,
        **kwargs,
    ) -> HumanReviewOutput:
        # 1. 리뷰 필요 노드 수집
        review_items = self._collect_review_items(input_data.semantic_graph)

        if not review_items:
            # 리뷰 필요 항목 없음
            return HumanReviewOutput(
                reviewed_graph=input_data.semantic_graph,
                review_summary={"status": "no_review_needed", "items": 0},
                feedback_stats_delta=None,
            )

        # 2. 큐에 등록
        batch_id = await self._queue_manager.add_batch(review_items)

        # 3. 모드에 따른 처리
        if self.config.mode == ReviewMode.SYNC:
            # 리뷰 완료 대기
            results = await self._queue_manager.wait_for_completion(
                batch_id,
                timeout=self.config.timeout_seconds,
            )
            # 결과 적용
            reviewed_graph = self._apply_review_results(
                input_data.semantic_graph,
                results,
            )
            feedback_delta = self._compute_feedback_delta(results)
        else:
            # 비동기: 콜백 등록 후 즉시 반환
            await self._queue_manager.register_callback(
                batch_id,
                self._on_review_complete,
            )
            reviewed_graph = input_data.semantic_graph
            feedback_delta = None

        return HumanReviewOutput(
            reviewed_graph=reviewed_graph,
            review_summary={
                "status": "completed" if self.config.mode == ReviewMode.SYNC else "queued",
                "items": len(review_items),
                "batch_id": batch_id,
            },
            feedback_stats_delta=feedback_delta,
        )

    def _collect_review_items(self, graph: SemanticGraph) -> List[ReviewItem]:
        """낮은 confidence 노드를 리뷰 항목으로 수집"""
        items = []
        for node in graph.nodes:
            if node.confidence < self.config.min_confidence_threshold:
                items.append(ReviewItem(
                    node_id=node.id,
                    element_type=node.element_type,
                    confidence=node.confidence,
                    content=node.content,
                ))
        return items

    def _apply_review_results(
        self,
        graph: SemanticGraph,
        results: List[ReviewResult],
    ) -> SemanticGraph:
        """리뷰 결과를 그래프에 적용"""
        # TODO(human): 리뷰 결과 적용 로직 구현
        pass

    def _compute_feedback_delta(self, results: List[ReviewResult]) -> FeedbackStats:
        """리뷰 결과로부터 FeedbackStats 델타 계산"""
        # TODO(human): 피드백 통계 계산 로직 구현
        pass

    async def _on_review_complete(self, batch_id: str, results: List[ReviewResult]):
        """비동기 모드 리뷰 완료 콜백"""
        # TODO: 콜백 처리 로직
        pass

    def get_metrics(self, output: HumanReviewOutput) -> StageMetrics:
        return StageMetrics(
            stage=self.stage_name,
            success=output is not None,
            elements_processed=output.review_summary.get("items", 0) if output else 0,
            custom_metrics=output.review_summary if output else {},
        )
```

### Task D-2: ReviewQueueManager 콜백 확장

**파일**: `cow/src/mathpix_pipeline/human_review/queue_manager.py`

**추가할 메서드**:
```python
class ReviewQueueManager:
    # 기존 메서드들...

    async def add_batch(self, items: List[ReviewItem]) -> str:
        """배치로 리뷰 항목 추가, batch_id 반환"""
        batch_id = str(uuid.uuid4())
        for item in items:
            item.batch_id = batch_id
            self._queue.append(item)
        return batch_id

    async def wait_for_completion(
        self,
        batch_id: str,
        timeout: float = 300.0,
    ) -> List[ReviewResult]:
        """배치 리뷰 완료 대기"""
        # 폴링 또는 이벤트 기반 대기
        pass

    async def register_callback(
        self,
        batch_id: str,
        callback: Callable[[str, List[ReviewResult]], Awaitable[None]],
    ):
        """리뷰 완료 시 호출될 콜백 등록"""
        self._callbacks[batch_id] = callback

    async def _notify_completion(self, batch_id: str, results: List[ReviewResult]):
        """리뷰 완료 시 콜백 호출"""
        if batch_id in self._callbacks:
            await self._callbacks[batch_id](batch_id, results)
            del self._callbacks[batch_id]
```

### Task D-3: pipeline.py Stage G 통합

**파일**: `cow/src/mathpix_pipeline/pipeline.py`

**변경 사항**:
```python
# __init__에서
from .stages import HumanReviewStage, HumanReviewStageConfig, HumanReviewInput

self._human_review_stage = HumanReviewStage(
    config=HumanReviewStageConfig(
        mode=ReviewMode.SYNC if options.sync_review else ReviewMode.ASYNC,
        feedback_stats=self._feedback_stats,
    )
)

# process()에서 Stage G 호출 부분 교체
if options.enable_human_review:
    review_result = await self._human_review_stage.run_async(
        HumanReviewInput(
            semantic_graph=semantic_graph,
            image_id=image_id,
            pipeline_result=result,
        )
    )
    if review_result.is_valid and review_result.output:
        semantic_graph = review_result.output.reviewed_graph
        # FeedbackStats 업데이트
        if review_result.output.feedback_stats_delta:
            self._update_feedback_stats(review_result.output.feedback_stats_delta)
```

### Task D-4: B+C asyncio.gather() 병렬화

**파일**: `cow/src/mathpix_pipeline/pipeline.py`

**변경 위치**: `process()` 메서드 내 Stage B, C 호출 부분

```python
import asyncio

# Before (lines ~820-830)
# text_spec = await self._run_stage_b(ingestion_spec, result)
# vision_spec = await self._run_stage_c(ingestion_spec, text_spec, result)

# After
async def _run_stages_bc_parallel(
    self,
    ingestion_spec: IngestionSpec,
    result: PipelineResult,
) -> tuple[Optional[TextSpec], Optional[VisionSpec]]:
    """Stage B와 C를 병렬 실행"""

    results = await asyncio.gather(
        self._run_stage_b(ingestion_spec, result),
        self._run_stage_c(ingestion_spec, None, result),  # text_spec=None
        return_exceptions=True,
    )

    text_result, vision_result = results

    # 에러 처리
    text_spec = None
    vision_spec = None

    if isinstance(text_result, Exception):
        logger.error(f"Stage B failed: {text_result}")
        result.add_error(
            PipelineError(
                message=f"Stage B failed: {text_result}",
                stage=PipelineStage.TEXT_PARSE,
            )
        )
    else:
        text_spec = text_result

    if isinstance(vision_result, Exception):
        logger.error(f"Stage C failed: {vision_result}")
        result.add_error(
            PipelineError(
                message=f"Stage C failed: {vision_result}",
                stage=PipelineStage.VISION_PARSE,
            )
        )
    else:
        vision_spec = vision_result

    return text_spec, vision_spec
```

### Task D-5: FeedbackStats 업데이트 로직

**파일**: `cow/src/mathpix_pipeline/schemas/threshold.py`

**추가할 메서드**:
```python
@dataclass
class FeedbackStats:
    total_reviews: int = 0
    acceptance_rate: float = 1.0
    recent_adjustments: List[float] = field(default_factory=list)

    def update(self, delta: 'FeedbackStats') -> 'FeedbackStats':
        """다른 FeedbackStats와 병합"""
        new_total = self.total_reviews + delta.total_reviews
        if new_total > 0:
            # 가중 평균으로 acceptance_rate 계산
            new_rate = (
                self.acceptance_rate * self.total_reviews +
                delta.acceptance_rate * delta.total_reviews
            ) / new_total
        else:
            new_rate = self.acceptance_rate

        return FeedbackStats(
            total_reviews=new_total,
            acceptance_rate=new_rate,
            recent_adjustments=self.recent_adjustments + delta.recent_adjustments,
        )
```

---

## Execution Order

```
D-4: B+C asyncio.gather() (독립적, 먼저 완료 가능)
    ↓
D-1: HumanReviewStage 생성
    ↓
D-2: ReviewQueueManager 확장
    ↓
D-5: FeedbackStats 업데이트 로직
    ↓
D-3: pipeline.py Stage G 통합
```

테스트:
```bash
# B+C 병렬화 테스트
pytest cow/tests/integration/test_stage_bc_parallel.py -v

# Stage G 통합 테스트
pytest cow/tests/human_review/test_human_review_stage.py -v
pytest cow/tests/integration/test_stage_g_integration.py -v

# 전체 E2E
pytest cow/tests/e2e/test_full_pipeline.py -v
```

---

## Metadata

```yaml
research_id: cow-refactoring-20260126-terminal-d
workload_id: cow-refactoring-20260126
scope: Stage G Integration + B+C Parallel
assigned_to: Terminal-D
estimated_effort: 2-3일
dependencies:
  - "Terminal-C BaseStage 마이그레이션 (권장, 필수 아님)"
outputs:
  - cow/src/mathpix_pipeline/stages/human_review_stage.py
  - cow/src/mathpix_pipeline/human_review/queue_manager.py (수정)
  - cow/src/mathpix_pipeline/pipeline.py (수정)
  - cow/src/mathpix_pipeline/schemas/threshold.py (수정)
  - cow/tests/human_review/test_human_review_stage.py
  - cow/tests/integration/test_stage_bc_parallel.py
next_action: /worker start D-4
```

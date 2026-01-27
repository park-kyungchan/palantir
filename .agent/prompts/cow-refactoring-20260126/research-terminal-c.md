# Research Report: COW Pipeline BaseStage Migration (Terminal-C)

> Generated: 2026-01-26T16:10:00Z
> Clarify Reference: cow-refactoring-20260126
> Workload ID: cow-refactoring-20260126
> Scope: BaseStage Pattern Migration for Stage D, B, F
> Assigned To: Terminal-C

---

## L1 Summary (< 500 tokens)

### Mission
ISSUE-001 Option B 실행: Stage D, B, F에 BaseStage 패턴 점진적 적용

### Key Deliverables
| Priority | Stage | New File | Effort | Wraps |
|----------|-------|----------|--------|-------|
| 1 | D (Alignment) | `stages/alignment_stage.py` | ~130줄 | AlignmentEngine |
| 2 | B (TextParse) | `stages/text_parse_stage.py` | ~120줄 | MathpixClient |
| 3 | F (Regeneration) | `stages/regeneration_stage.py` | ~100줄 | RegenerationEngine |

### Reference Implementation
- `stages/semantic_graph_stage.py` (218줄) - 참조 구현
- `stages/base.py` (377줄) - BaseStage 추상 클래스

### Success Criteria
- [ ] 각 Stage 클래스가 BaseStage[InputT, OutputT] 상속
- [ ] validate(), _execute_async(), get_metrics() 구현
- [ ] 단위 테스트 통과
- [ ] pipeline.py에서 stage.run_async() 호출로 변경

---

## L2 Detailed Analysis

### 2.1 BaseStage Pattern 요약

```python
class BaseStage(ABC, Generic[InputT, OutputT]):
    """표준화된 스테이지 라이프사이클 관리"""

    @property
    @abstractmethod
    def stage_name(self) -> PipelineStage:
        """스테이지 식별자 반환"""

    @abstractmethod
    def validate(self, input_data: InputT) -> ValidationResult:
        """입력 검증 (pre-execution)"""

    @abstractmethod
    async def _execute_async(self, input_data: InputT, **kwargs) -> OutputT:
        """실제 작업 수행"""

    def get_metrics(self, output: OutputT) -> StageMetrics:
        """출력 기반 메트릭 수집 (optional override)"""

    async def run_async(self, input_data, skip_validation=False) -> StageResult[OutputT]:
        """전체 라이프사이클 실행 (호출 진입점)"""
        # 1. StageTiming 시작
        # 2. validate() 호출
        # 3. _execute_async() 호출
        # 4. get_metrics() 호출
        # 5. StageResult 반환
```

### 2.2 Stage D (Alignment) 마이그레이션

**현재 상태** (`pipeline.py` lines 1214-1244):
```python
async def _run_stage_d(self, text_spec, vision_spec, result) -> Optional[AlignmentReport]:
    timing = StageTiming(stage=PipelineStage.ALIGNMENT)  # 수동
    result.stage_timings.append(timing)
    try:
        report = self._alignment_engine.align(text_spec, vision_spec)
        result.mark_stage_complete(PipelineStage.ALIGNMENT)
        timing.complete(success=True)
        return report
    except Exception as e:
        timing.complete(success=False, error=str(e))
        result.add_error(...)
        return None
```

**목표 상태** (`stages/alignment_stage.py`):
```python
@dataclass
class AlignmentStageConfig:
    alignment_config: AlignmentEngineConfig = field(default_factory=AlignmentEngineConfig)
    strict_validation: bool = False

class AlignmentStage(BaseStage[AlignmentInput, AlignmentReport]):
    """Stage D: Text-Visual Alignment"""

    @property
    def stage_name(self) -> PipelineStage:
        return PipelineStage.ALIGNMENT

    def validate(self, input_data: AlignmentInput) -> ValidationResult:
        result = ValidationResult()
        if not input_data.text_spec:
            result.add_error("TextSpec is required")
        if not input_data.vision_spec:
            result.add_error("VisionSpec is required")
        # confidence checks...
        return result

    async def _execute_async(self, input_data: AlignmentInput, **kwargs) -> AlignmentReport:
        return self._engine.align(input_data.text_spec, input_data.vision_spec)

    def get_metrics(self, output: AlignmentReport) -> StageMetrics:
        return StageMetrics(
            stage=self.stage_name,
            success=output is not None,
            elements_processed=output.statistics.matched_pairs if output else 0,
        )
```

**Input 타입 정의 필요**:
```python
@dataclass
class AlignmentInput:
    """Stage D 입력 데이터"""
    text_spec: TextSpec
    vision_spec: VisionSpec
    image_id: str
```

### 2.3 Stage B (TextParse) 마이그레이션

**현재 상태** (`pipeline.py` lines 971-1058):
- MathpixClient 직접 호출
- FAIL-FAST if no config
- 에러 시 result.add_error()

**목표 상태** (`stages/text_parse_stage.py`):
```python
class TextParseStage(BaseStage[IngestionSpec, TextSpec]):
    """Stage B: Mathpix API Text Parsing"""

    def validate(self, input_data: IngestionSpec) -> ValidationResult:
        result = ValidationResult()
        if not input_data.image_id:
            result.add_error("image_id is required")
        if not self._client:
            result.add_error("MathpixClient not configured")
        return result

    async def _execute_async(self, input_data: IngestionSpec, **kwargs) -> TextSpec:
        return await self._client.parse_image(input_data)
```

### 2.4 Stage F (Regeneration) 마이그레이션

**현재 상태** (`pipeline.py` lines 1275-1311):
- RegenerationEngine.regenerate() 호출
- LaTeX/SVG 생성

**목표 상태** (`stages/regeneration_stage.py`):
```python
class RegenerationStage(BaseStage[SemanticGraph, RegenerationSpec]):
    """Stage F: Content Regeneration"""

    def validate(self, input_data: SemanticGraph) -> ValidationResult:
        result = ValidationResult()
        if not input_data.nodes:
            result.add_warning("Empty graph - nothing to regenerate")
        return result

    async def _execute_async(self, input_data: SemanticGraph, **kwargs) -> RegenerationSpec:
        return self._engine.regenerate(input_data)
```

---

## L3 Implementation Tasks

### Task C-1: Stage D AlignmentStage 생성

**파일**: `cow/src/mathpix_pipeline/stages/alignment_stage.py`

**체크리스트**:
- [ ] AlignmentStageConfig 정의
- [ ] AlignmentInput 데이터 클래스 정의
- [ ] AlignmentStage(BaseStage[AlignmentInput, AlignmentReport]) 구현
- [ ] validate() - TextSpec, VisionSpec 검증
- [ ] _execute_async() - AlignmentEngine.align() 호출
- [ ] get_metrics() - matched_pairs, alignment_score 수집
- [ ] stages/__init__.py에 export 추가

**테스트**: `cow/tests/alignment/test_alignment_stage.py`
- [ ] validate() 성공/실패 케이스
- [ ] _execute_async() mock engine 테스트
- [ ] get_metrics() 출력 검증

### Task C-2: Stage B TextParseStage 생성

**파일**: `cow/src/mathpix_pipeline/stages/text_parse_stage.py`

**체크리스트**:
- [ ] TextParseStageConfig 정의
- [ ] TextParseStage(BaseStage[IngestionSpec, TextSpec]) 구현
- [ ] validate() - image_id, client 검증
- [ ] _execute_async() - MathpixClient.parse_image() 호출
- [ ] get_metrics() - equations_count, lines_count 수집
- [ ] stages/__init__.py에 export 추가

**테스트**: `cow/tests/clients/test_text_parse_stage.py`
- [ ] validate() 성공/실패 케이스
- [ ] _execute_async() mock client 테스트
- [ ] API 에러 핸들링 테스트

### Task C-3: Stage F RegenerationStage 생성

**파일**: `cow/src/mathpix_pipeline/stages/regeneration_stage.py`

**체크리스트**:
- [ ] RegenerationStageConfig 정의
- [ ] RegenerationStage(BaseStage[SemanticGraph, RegenerationSpec]) 구현
- [ ] validate() - nodes 존재 검증
- [ ] _execute_async() - RegenerationEngine.regenerate() 호출
- [ ] get_metrics() - latex_generated, svg_generated 수집
- [ ] stages/__init__.py에 export 추가

**테스트**: `cow/tests/regeneration/test_regeneration_stage.py`
- [ ] validate() 성공/실패 케이스
- [ ] _execute_async() mock engine 테스트

### Task C-4: pipeline.py 업데이트

**파일**: `cow/src/mathpix_pipeline/pipeline.py`

**변경 사항**:
```python
# Before
async def _run_stage_d(self, text_spec, vision_spec, result):
    ...inline implementation...

# After
# __init__에서
self._alignment_stage = AlignmentStage(config=alignment_stage_config)

# process()에서
alignment_result = await self._alignment_stage.run_async(
    AlignmentInput(text_spec=text_spec, vision_spec=vision_spec, image_id=image_id)
)
if not alignment_result.is_valid:
    result.add_error(...)
alignment_report = alignment_result.output
```

---

## Execution Order

```
C-1: AlignmentStage (Stage D)
    ↓
C-2: TextParseStage (Stage B)
    ↓
C-3: RegenerationStage (Stage F)
    ↓
C-4: pipeline.py 업데이트
```

각 Task 완료 후 테스트 실행:
```bash
pytest cow/tests/alignment/test_alignment_stage.py -v
pytest cow/tests/clients/test_text_parse_stage.py -v
pytest cow/tests/regeneration/test_regeneration_stage.py -v
pytest cow/tests/integration/test_stage_integration.py -v
```

---

## Metadata

```yaml
research_id: cow-refactoring-20260126-terminal-c
workload_id: cow-refactoring-20260126
scope: BaseStage Migration (D, B, F)
assigned_to: Terminal-C
estimated_effort: 1.5-2.5일
dependencies: []
outputs:
  - cow/src/mathpix_pipeline/stages/alignment_stage.py
  - cow/src/mathpix_pipeline/stages/text_parse_stage.py
  - cow/src/mathpix_pipeline/stages/regeneration_stage.py
  - cow/tests/alignment/test_alignment_stage.py
  - cow/tests/clients/test_text_parse_stage.py
  - cow/tests/regeneration/test_regeneration_stage.py
next_action: /worker start C-1
```

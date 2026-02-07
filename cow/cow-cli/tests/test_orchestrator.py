"""
Tests for COW Orchestrator.
"""
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import tempfile
import json
from PIL import Image

from cow_cli.claude import (
    ProcessingStatus,
    StageExecution,
    SessionCheckpoint,
    PipelineResult,
    COWOrchestrator,
    process_document,
    StageType,
    ModelType,
)


class TestProcessingStatus:
    """Tests for ProcessingStatus enum."""

    def test_status_values(self):
        """Test all status values."""
        assert ProcessingStatus.PENDING.value == "pending"
        assert ProcessingStatus.RUNNING.value == "running"
        assert ProcessingStatus.PAUSED.value == "paused"
        assert ProcessingStatus.COMPLETED.value == "completed"
        assert ProcessingStatus.FAILED.value == "failed"
        assert ProcessingStatus.NEEDS_REVIEW.value == "needs_review"


class TestStageExecution:
    """Tests for StageExecution dataclass."""

    def test_basic_execution(self):
        """Test basic execution creation."""
        exec = StageExecution(
            stage=StageType.INGESTION,
            agent="ingestion-agent",
            model=ModelType.HAIKU,
            status=ProcessingStatus.COMPLETED,
        )

        assert exec.stage == StageType.INGESTION
        assert exec.status == ProcessingStatus.COMPLETED

    def test_duration_calculation(self):
        """Test duration calculation."""
        start = datetime(2024, 1, 1, 12, 0, 0)
        end = datetime(2024, 1, 1, 12, 0, 1)  # 1 second later

        exec = StageExecution(
            stage=StageType.INGESTION,
            agent="test",
            model=ModelType.HAIKU,
            status=ProcessingStatus.COMPLETED,
            started_at=start,
            completed_at=end,
        )

        assert exec.duration_ms == 1000.0

    def test_total_tokens(self):
        """Test token counting."""
        exec = StageExecution(
            stage=StageType.TEXT_PARSE,
            agent="test",
            model=ModelType.SONNET,
            status=ProcessingStatus.COMPLETED,
            input_tokens=500,
            output_tokens=200,
        )

        assert exec.total_tokens == 700


class TestSessionCheckpoint:
    """Tests for SessionCheckpoint."""

    def test_to_dict(self):
        """Test serialization."""
        now = datetime.now()
        checkpoint = SessionCheckpoint(
            session_id="test-123",
            image_path="/test/image.png",
            current_stage=StageType.SEPARATION,
            completed_stages=[StageType.INGESTION, StageType.TEXT_PARSE],
            stage_results={"A": {"validated": True}},
            created_at=now,
            updated_at=now,
        )

        d = checkpoint.to_dict()

        assert d["session_id"] == "test-123"
        assert d["current_stage"] == "B1"
        assert d["completed_stages"] == ["A", "B"]

    def test_from_dict(self):
        """Test deserialization."""
        now = datetime.now()
        data = {
            "session_id": "test-456",
            "image_path": "/test.png",
            "current_stage": "B",
            "completed_stages": ["A"],
            "stage_results": {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        checkpoint = SessionCheckpoint.from_dict(data)

        assert checkpoint.session_id == "test-456"
        assert checkpoint.current_stage == StageType.TEXT_PARSE


class TestPipelineResult:
    """Tests for PipelineResult."""

    def test_total_tokens(self):
        """Test total token calculation."""
        result = PipelineResult(
            session_id="test",
            image_path="/test.png",
            status=ProcessingStatus.COMPLETED,
            stages=[
                StageExecution(
                    stage=StageType.INGESTION,
                    agent="test",
                    model=ModelType.HAIKU,
                    status=ProcessingStatus.COMPLETED,
                    input_tokens=100,
                    output_tokens=50,
                ),
                StageExecution(
                    stage=StageType.TEXT_PARSE,
                    agent="test",
                    model=ModelType.SONNET,
                    status=ProcessingStatus.COMPLETED,
                    input_tokens=500,
                    output_tokens=300,
                ),
            ],
        )

        assert result.total_tokens == 950

    def test_estimated_cost_always_zero(self):
        """Test that estimated cost is always $0 with Claude MAX."""
        result = PipelineResult(
            session_id="test",
            image_path="/test.png",
            status=ProcessingStatus.COMPLETED,
        )

        assert result.estimated_cost == 0.0

    def test_get_stage_result(self):
        """Test getting stage result."""
        stage_exec = StageExecution(
            stage=StageType.SEPARATION,
            agent="separator-agent",
            model=ModelType.HAIKU,
            status=ProcessingStatus.COMPLETED,
            result={"layout_count": 5},
        )

        result = PipelineResult(
            session_id="test",
            image_path="/test.png",
            status=ProcessingStatus.COMPLETED,
            stages=[stage_exec],
        )

        found = result.get_stage_result(StageType.SEPARATION)
        assert found is not None
        assert found.result["layout_count"] == 5

        not_found = result.get_stage_result(StageType.EXPORT)
        assert not_found is None

    def test_to_summary(self):
        """Test summary generation."""
        result = PipelineResult(
            session_id="test-summary",
            image_path="/test.png",
            status=ProcessingStatus.COMPLETED,
            stages=[
                StageExecution(
                    stage=StageType.INGESTION,
                    agent="test",
                    model=ModelType.HAIKU,
                    status=ProcessingStatus.COMPLETED,
                ),
            ],
        )

        summary = result.to_summary()

        assert summary["session_id"] == "test-summary"
        assert summary["status"] == "completed"
        assert summary["stages_completed"] == 1
        assert summary["estimated_cost"] == 0.0


class TestCOWOrchestrator:
    """Tests for COWOrchestrator."""

    @pytest.fixture
    def orchestrator(self):
        """Create test orchestrator."""
        return COWOrchestrator(enable_hitl=False)

    def test_initialization(self, orchestrator):
        """Test orchestrator initialization."""
        assert orchestrator.enable_hitl is False
        assert orchestrator.confidence_threshold == 0.75
        assert len(orchestrator._tools) > 0

    def test_get_pipeline_status(self, orchestrator):
        """Test pipeline status."""
        status = orchestrator.get_pipeline_status()

        assert "tools_count" in status
        assert "agents_count" in status
        assert "stages" in status
        assert len(status["stages"]) == 9

    @pytest.mark.asyncio
    async def test_process_ingestion_stage(self, orchestrator):
        """Test Stage A (Ingestion) execution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test image
            img_path = Path(tmpdir) / "test.png"
            img = Image.new("RGB", (100, 100), "white")
            img.save(img_path)

            # Execute
            result = await orchestrator.process(img_path)

            # Check that ingestion stage ran
            ingestion = result.get_stage_result(StageType.INGESTION)
            assert ingestion is not None
            assert ingestion.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]

    @pytest.mark.asyncio
    async def test_process_with_checkpoint(self):
        """Test checkpoint saving."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir) / "checkpoints"

            orchestrator = COWOrchestrator(
                checkpoint_dir=checkpoint_dir,
                enable_hitl=False,
            )

            # Create test image
            img_path = Path(tmpdir) / "test.png"
            img = Image.new("RGB", (100, 100), "white")
            img.save(img_path)

            # Process
            result = await orchestrator.process(img_path)

            # Check checkpoint was saved
            checkpoint_files = list(checkpoint_dir.glob("*.json"))
            assert len(checkpoint_files) > 0

    def test_load_checkpoint(self):
        """Test checkpoint loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            # Create checkpoint file
            checkpoint_data = {
                "session_id": "test-load",
                "image_path": "/test.png",
                "current_stage": "B",
                "completed_stages": ["A"],
                "stage_results": {"A": {"validated": True}},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }

            checkpoint_path = checkpoint_dir / "test-load.json"
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint_data, f)

            orchestrator = COWOrchestrator(checkpoint_dir=checkpoint_dir)
            checkpoint = orchestrator.load_checkpoint("test-load")

            assert checkpoint is not None
            assert checkpoint.session_id == "test-load"
            assert StageType.INGESTION in checkpoint.completed_stages

    def test_model_fallback_order(self, orchestrator):
        """Test model fallback order."""
        assert orchestrator.MODEL_FALLBACK == [
            ModelType.OPUS,
            ModelType.SONNET,
            ModelType.HAIKU,
        ]

    @pytest.mark.asyncio
    async def test_needs_review_detection(self, orchestrator):
        """Test HITL review detection."""
        # Enable HITL for this test
        orchestrator.enable_hitl = True

        # Result with low confidence
        result_low = {
            "quality_summary": {"needs_review": 1},
            "min_confidence": 0.5,
        }
        assert orchestrator._needs_review(result_low) is True

        # Result with high confidence
        result_high = {
            "quality_summary": {"needs_review": 0},
            "min_confidence": 0.95,
        }
        assert orchestrator._needs_review(result_high) is False

        # Disable HITL
        orchestrator.enable_hitl = False
        assert orchestrator._needs_review(result_low) is False


class TestProcessDocumentFunction:
    """Tests for process_document convenience function."""

    @pytest.mark.asyncio
    async def test_process_document(self):
        """Test convenience function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.png"
            img = Image.new("RGB", (100, 100), "white")
            img.save(img_path)

            result = await process_document(img_path, enable_hitl=False)

            assert result.session_id is not None
            assert result.image_path == str(img_path)


class TestStageHandlers:
    """Tests for individual stage handlers."""

    @pytest.fixture
    def orchestrator(self):
        return COWOrchestrator(enable_hitl=False)

    @pytest.mark.asyncio
    async def test_ingestion_handler_valid(self, orchestrator):
        """Test ingestion handler with valid image."""
        with tempfile.TemporaryDirectory() as tmpdir:
            img_path = Path(tmpdir) / "test.png"
            img = Image.new("RGB", (100, 100), "white")
            img.save(img_path)

            context = {"image_path": str(img_path)}
            result = await orchestrator._handle_ingestion(context, ModelType.HAIKU)

            assert result["validated"] is True
            assert result["format"] == "PNG"

    @pytest.mark.asyncio
    async def test_ingestion_handler_invalid(self, orchestrator):
        """Test ingestion handler with invalid image."""
        context = {"image_path": "/nonexistent/image.png"}

        with pytest.raises(ValueError):
            await orchestrator._handle_ingestion(context, ModelType.HAIKU)

    @pytest.mark.asyncio
    async def test_human_review_handler(self, orchestrator):
        """Test human review handler."""
        context = {}
        result = await orchestrator._handle_human_review(context, ModelType.HAIKU)

        assert "pending_count" in result
        assert "items" in result

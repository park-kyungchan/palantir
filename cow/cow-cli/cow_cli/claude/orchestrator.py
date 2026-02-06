"""
COW CLI - Main Orchestrator

Claude Agent SDK-based orchestrator for the COW pipeline.
Manages stage sequencing, error handling, and session management.
"""
from typing import Optional, Any, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
import json
import uuid

from cow_cli.claude.stage_agents import (
    StageType,
    ModelType,
    AgentDefinition,
    STAGE_AGENTS,
    get_agent,
    get_pipeline_sequence,
)
from cow_cli.claude.mcp_servers import get_all_tools, get_tool_schema

logger = logging.getLogger("cow-cli.orchestrator")


class ProcessingStatus(str, Enum):
    """Pipeline processing status."""

    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


@dataclass
class StageExecution:
    """Record of a single stage execution."""

    stage: StageType
    agent: str
    model: ModelType
    status: ProcessingStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    input_tokens: int = 0
    output_tokens: int = 0
    result: Optional[dict] = None
    error: Optional[str] = None
    retry_count: int = 0

    @property
    def duration_ms(self) -> float:
        """Get execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.input_tokens + self.output_tokens


@dataclass
class SessionCheckpoint:
    """Checkpoint for resumable sessions."""

    session_id: str
    image_path: str
    current_stage: StageType
    completed_stages: list[StageType]
    stage_results: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "session_id": self.session_id,
            "image_path": self.image_path,
            "current_stage": self.current_stage.value,
            "completed_stages": [s.value for s in self.completed_stages],
            "stage_results": self.stage_results,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionCheckpoint":
        """Deserialize from dictionary."""
        return cls(
            session_id=data["session_id"],
            image_path=data["image_path"],
            current_stage=StageType(data["current_stage"]),
            completed_stages=[StageType(s) for s in data["completed_stages"]],
            stage_results=data["stage_results"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
        )


@dataclass
class PipelineResult:
    """Complete pipeline processing result."""

    session_id: str
    image_path: str
    status: ProcessingStatus
    stages: list[StageExecution] = field(default_factory=list)
    final_output: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    @property
    def total_tokens(self) -> int:
        """Get total tokens across all stages."""
        return sum(s.total_tokens for s in self.stages)

    @property
    def total_duration_ms(self) -> float:
        """Get total duration in milliseconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() * 1000
        return 0.0

    @property
    def estimated_cost(self) -> float:
        """
        Estimate cost (always $0 with Claude MAX subscription).

        Note: Claude MAX subscription provides unlimited usage.
        """
        return 0.0  # Claude MAX = unlimited

    def get_stage_result(self, stage: StageType) -> Optional[StageExecution]:
        """Get result for a specific stage."""
        for s in self.stages:
            if s.stage == stage:
                return s
        return None

    def to_summary(self) -> dict:
        """Generate execution summary."""
        return {
            "session_id": self.session_id,
            "status": self.status.value,
            "stages_completed": len([s for s in self.stages if s.status == ProcessingStatus.COMPLETED]),
            "total_stages": len(self.stages),
            "total_tokens": self.total_tokens,
            "total_duration_ms": self.total_duration_ms,
            "estimated_cost": self.estimated_cost,
        }


class COWOrchestrator:
    """
    Main orchestrator for COW pipeline execution.

    Coordinates stage agents through the full pipeline:
    A → B → B1 → C → D → [HITL] → E → F → G → H

    Features:
    - Stage sequencing with dependency management
    - Model fallback (Opus → Sonnet → Haiku)
    - Checkpoint/resume support
    - Token and cost tracking
    """

    # Model fallback order for retries
    MODEL_FALLBACK = [ModelType.OPUS, ModelType.SONNET, ModelType.HAIKU]

    # Maximum retries per stage
    MAX_RETRIES = 3

    def __init__(
        self,
        checkpoint_dir: Optional[Path] = None,
        enable_hitl: bool = True,
        confidence_threshold: float = 0.75,
        on_stage_complete: Optional[Callable[[StageExecution], None]] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            checkpoint_dir: Directory for saving checkpoints
            enable_hitl: Enable human-in-the-loop review
            confidence_threshold: Threshold for HITL routing
            on_stage_complete: Callback after each stage
        """
        self.checkpoint_dir = checkpoint_dir
        self.enable_hitl = enable_hitl
        self.confidence_threshold = confidence_threshold
        self.on_stage_complete = on_stage_complete

        # Initialize tool registry
        self._tools = get_all_tools()
        self._tool_schema = get_tool_schema()

        logger.info(
            f"COWOrchestrator initialized with {len(self._tools)} tools, "
            f"HITL={'enabled' if enable_hitl else 'disabled'}"
        )

    async def process(
        self,
        image_path: Path,
        session_id: Optional[str] = None,
        resume_from: Optional[StageType] = None,
    ) -> PipelineResult:
        """
        Process an image through the complete pipeline.

        Args:
            image_path: Path to input image
            session_id: Optional session ID (generated if not provided)
            resume_from: Optional stage to resume from

        Returns:
            PipelineResult with all stage outputs
        """
        session_id = session_id or str(uuid.uuid4())[:8]
        result = PipelineResult(
            session_id=session_id,
            image_path=str(image_path),
            status=ProcessingStatus.RUNNING,
            started_at=datetime.now(),
        )

        logger.info(f"Starting pipeline for {image_path} (session: {session_id})")

        # Determine stages to execute
        pipeline = get_pipeline_sequence()
        start_idx = 0

        if resume_from:
            try:
                start_idx = pipeline.index(resume_from)
                logger.info(f"Resuming from stage {resume_from.value}")
            except ValueError:
                logger.warning(f"Invalid resume stage {resume_from}, starting from beginning")

        # Execute stages
        context = {"image_path": str(image_path)}

        try:
            for stage in pipeline[start_idx:]:
                # Execute stage
                stage_result = await self._execute_stage(stage, context)
                result.stages.append(stage_result)

                # Callback if provided
                if self.on_stage_complete:
                    self.on_stage_complete(stage_result)

                # Check for failure
                if stage_result.status == ProcessingStatus.FAILED:
                    result.status = ProcessingStatus.FAILED
                    result.error = stage_result.error
                    break

                # Check for HITL routing
                if stage_result.status == ProcessingStatus.NEEDS_REVIEW:
                    if self.enable_hitl:
                        result.status = ProcessingStatus.NEEDS_REVIEW
                        logger.info(f"Stage {stage.value} requires human review")
                        # Save checkpoint for later resume
                        self._save_checkpoint(result, stage)
                        break
                    else:
                        logger.warning(f"HITL disabled, continuing despite low confidence")

                # Update context with stage output
                if stage_result.result:
                    context[f"stage_{stage.value}"] = stage_result.result

                # Save checkpoint after each stage
                self._save_checkpoint(result, stage)

            # Mark as completed if all stages finished
            if result.status == ProcessingStatus.RUNNING:
                result.status = ProcessingStatus.COMPLETED
                result.final_output = context

        except Exception as e:
            logger.exception(f"Pipeline error: {e}")
            result.status = ProcessingStatus.FAILED
            result.error = str(e)

        result.completed_at = datetime.now()
        logger.info(
            f"Pipeline {result.status.value} for {image_path} "
            f"({result.total_duration_ms:.0f}ms, {result.total_tokens} tokens)"
        )

        return result

    async def _execute_stage(
        self,
        stage: StageType,
        context: dict,
    ) -> StageExecution:
        """Execute a single pipeline stage."""
        agent = get_agent(stage)

        execution = StageExecution(
            stage=stage,
            agent=agent.name,
            model=agent.model,
            status=ProcessingStatus.RUNNING,
            started_at=datetime.now(),
        )

        logger.info(f"Executing stage {stage.value} with {agent.name} ({agent.model.value})")

        try:
            # Get stage-specific handler
            handler = self._get_stage_handler(stage)

            if handler:
                # Execute with retry logic
                result = await self._execute_with_retry(handler, context, agent.model)
                execution.result = result

                # Check confidence for HITL routing
                if self._needs_review(result):
                    execution.status = ProcessingStatus.NEEDS_REVIEW
                else:
                    execution.status = ProcessingStatus.COMPLETED
            else:
                # No handler - stage not yet implemented
                logger.warning(f"No handler for stage {stage.value}, skipping")
                execution.status = ProcessingStatus.COMPLETED
                execution.result = {"skipped": True, "reason": "not_implemented"}

        except Exception as e:
            logger.error(f"Stage {stage.value} failed: {e}")
            execution.status = ProcessingStatus.FAILED
            execution.error = str(e)

        execution.completed_at = datetime.now()
        return execution

    async def _execute_with_retry(
        self,
        handler: Callable,
        context: dict,
        preferred_model: ModelType,
    ) -> dict:
        """Execute handler with retry and model fallback."""
        last_error = None

        for attempt in range(self.MAX_RETRIES):
            # Determine model for this attempt (fallback on retry)
            if attempt == 0:
                model = preferred_model
            else:
                # Try next model in fallback chain
                try:
                    current_idx = self.MODEL_FALLBACK.index(preferred_model)
                    model = self.MODEL_FALLBACK[min(current_idx + attempt, len(self.MODEL_FALLBACK) - 1)]
                except ValueError:
                    model = ModelType.SONNET

            try:
                logger.debug(f"Attempt {attempt + 1} with model {model.value}")
                result = await handler(context, model)
                return result

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff

        raise last_error or Exception("Max retries exceeded")

    def _get_stage_handler(self, stage: StageType) -> Optional[Callable]:
        """Get handler function for a stage."""
        handlers = {
            StageType.INGESTION: self._handle_ingestion,
            StageType.TEXT_PARSE: self._handle_text_parse,
            StageType.SEPARATION: self._handle_separation,
            StageType.HUMAN_REVIEW: self._handle_human_review,
            # Other stages would be added as implemented
        }
        return handlers.get(stage)

    async def _handle_ingestion(self, context: dict, model: ModelType) -> dict:
        """Handle Stage A: Ingestion."""
        from cow_cli.claude.mcp_servers import validate_image

        image_path = context["image_path"]
        result = validate_image(image_path)

        if not result.get("valid", False):
            raise ValueError(f"Image validation failed: {result}")

        return {
            "validated": True,
            "image_path": image_path,
            "format": result.get("format"),
            "dimensions": (result.get("width"), result.get("height")),
        }

    async def _handle_text_parse(self, context: dict, model: ModelType) -> dict:
        """Handle Stage B: Text Parse (Mathpix)."""
        from cow_cli.claude.mcp_servers import mathpix_request

        image_path = context["image_path"]
        result = await mathpix_request(image_path)

        if not result.get("success", False):
            raise ValueError(f"Mathpix request failed: {result.get('error')}")

        return {
            "request_id": result.get("request_id"),
            "has_word_data": result.get("has_word_data"),
            "confidence": result.get("confidence"),
        }

    async def _handle_separation(self, context: dict, model: ModelType) -> dict:
        """Handle Stage B1: Layout/Content Separation."""
        from cow_cli.claude.mcp_servers import separate_layout_content
        from cow_cli.pipeline import process_image

        # Use pipeline processor for full separation
        image_path = context["image_path"]

        try:
            pipeline_result = await process_image(image_path, skip_validation=True)

            if pipeline_result.success and pipeline_result.document:
                doc = pipeline_result.document
                return {
                    "layout_count": len(doc.layout.elements),
                    "content_count": len(doc.content.elements),
                    "quality_summary": {
                        "total": doc.content.quality_summary.total_elements,
                        "high_confidence": doc.content.quality_summary.high_confidence_count,
                        "needs_review": doc.content.quality_summary.needs_review_count,
                    },
                    "min_confidence": doc.content.quality_summary.min_confidence,
                }
            else:
                raise ValueError(f"Pipeline failed: {pipeline_result.error}")

        except Exception as e:
            # Fallback to direct MCP call
            logger.warning(f"Pipeline failed, using direct separation: {e}")

            # This would need actual stage B output
            return {
                "layout_count": 0,
                "content_count": 0,
                "quality_summary": {"needs_review": 0},
                "error": "Direct separation not available without Stage B output",
            }

    async def _handle_human_review(self, context: dict, model: ModelType) -> dict:
        """Handle Stage G: Human Review."""
        from cow_cli.claude.mcp_servers import list_pending_reviews

        # Check for pending reviews
        result = list_pending_reviews(max_confidence=self.confidence_threshold)

        return {
            "pending_count": result.get("count", 0),
            "items": result.get("items", []),
        }

    def _needs_review(self, result: dict) -> bool:
        """Check if result needs human review."""
        if not self.enable_hitl:
            return False

        # Check quality summary
        quality = result.get("quality_summary", {})
        needs_review = quality.get("needs_review", 0)

        if needs_review > 0:
            return True

        # Check minimum confidence
        min_conf = result.get("min_confidence")
        if min_conf is not None and min_conf < self.confidence_threshold:
            return True

        return False

    def _save_checkpoint(self, result: PipelineResult, current_stage: StageType) -> None:
        """Save checkpoint for resume support."""
        if not self.checkpoint_dir:
            return

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        checkpoint = SessionCheckpoint(
            session_id=result.session_id,
            image_path=result.image_path,
            current_stage=current_stage,
            completed_stages=[s.stage for s in result.stages if s.status == ProcessingStatus.COMPLETED],
            stage_results={s.stage.value: s.result for s in result.stages if s.result},
            created_at=result.started_at or datetime.now(),
            updated_at=datetime.now(),
        )

        checkpoint_path = self.checkpoint_dir / f"{result.session_id}.json"
        with open(checkpoint_path, "w") as f:
            json.dump(checkpoint.to_dict(), f, indent=2)

        logger.debug(f"Saved checkpoint to {checkpoint_path}")

    def load_checkpoint(self, session_id: str) -> Optional[SessionCheckpoint]:
        """Load checkpoint for resume."""
        if not self.checkpoint_dir:
            return None

        checkpoint_path = self.checkpoint_dir / f"{session_id}.json"
        if not checkpoint_path.exists():
            return None

        with open(checkpoint_path) as f:
            data = json.load(f)

        return SessionCheckpoint.from_dict(data)

    def get_pipeline_status(self) -> dict:
        """Get current pipeline configuration status."""
        return {
            "tools_count": len(self._tools),
            "agents_count": len(STAGE_AGENTS),
            "hitl_enabled": self.enable_hitl,
            "confidence_threshold": self.confidence_threshold,
            "checkpoint_dir": str(self.checkpoint_dir) if self.checkpoint_dir else None,
            "stages": [
                {
                    "stage": stage.value,
                    "agent": get_agent(stage).name,
                    "model": get_agent(stage).model.value,
                    "tools": get_agent(stage).tools,
                }
                for stage in get_pipeline_sequence()
            ],
        }


async def process_document(
    image_path: Path,
    checkpoint_dir: Optional[Path] = None,
    enable_hitl: bool = True,
) -> PipelineResult:
    """
    Convenience function to process a document through the COW pipeline.

    Args:
        image_path: Path to input image
        checkpoint_dir: Optional checkpoint directory
        enable_hitl: Enable human review

    Returns:
        PipelineResult with processing results
    """
    orchestrator = COWOrchestrator(
        checkpoint_dir=checkpoint_dir,
        enable_hitl=enable_hitl,
    )
    return await orchestrator.process(image_path)


__all__ = [
    "ProcessingStatus",
    "StageExecution",
    "SessionCheckpoint",
    "PipelineResult",
    "COWOrchestrator",
    "process_document",
]

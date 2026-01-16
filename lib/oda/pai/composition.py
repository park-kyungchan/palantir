"""
ODA PAI - Block Composition System (AIP-03)
============================================

Block composition and pipeline execution for content processing.

This module provides:
- CompositionStage: A single stage in a composition pipeline
- CompositionPipeline: Orchestrates multiple stages to process blocks
- PipelineResult: Execution result from a pipeline run

Pipelines enable complex content transformations:
- SEQUENTIAL: Stages execute one after another
- PARALLEL: Stages execute concurrently
- BRANCHING: Conditional stage selection

Transform types supported:
- MERGE: Combine multiple blocks
- SPLIT: Split a block into multiple
- CONVERT: Change block type
- FILTER: Filter block content
- EXTRACT: Extract portion of block
- ENRICH: Add metadata to block

ObjectTypes:
    - CompositionStage: Individual transformation stage
    - CompositionPipeline: Container for stages with execution logic

Reference: lib.oda.pai.blocks for BlockType definitions
Schema Version: 1.0.0
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from enum import Enum
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
)

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# FORWARD REFERENCES - BlockType will be available from blocks module
# =============================================================================

# Try to import BlockType if available, otherwise use string-based references
try:
    from lib.oda.pai.blocks import BlockType, BlockKind
    _BLOCKS_AVAILABLE = True
except ImportError:
    # Blocks module not yet implemented - use placeholder
    BlockType = Any  # type: ignore
    BlockKind = None  # type: ignore
    _BLOCKS_AVAILABLE = False


# =============================================================================
# ENUMS
# =============================================================================


class PipelineMode(str, Enum):
    """
    Execution mode for a composition pipeline.

    Modes:
        SEQUENTIAL: Stages execute one after another in order
        PARALLEL: Independent stages execute concurrently
        BRANCHING: Conditional execution based on stage results
    """
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    BRANCHING = "branching"


class PipelineStatus(str, Enum):
    """
    Lifecycle status for a composition pipeline.

    States:
        PENDING: Pipeline created but not started
        RUNNING: Pipeline currently executing
        COMPLETED: Pipeline finished successfully
        FAILED: Pipeline encountered an error
        CANCELLED: Pipeline was cancelled before completion
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StageStatus(str, Enum):
    """
    Execution status for a composition stage.

    States:
        PENDING: Stage not yet started
        RUNNING: Stage currently executing
        COMPLETED: Stage finished successfully
        FAILED: Stage encountered an error
        SKIPPED: Stage was skipped (condition not met)
    """
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TransformType(str, Enum):
    """
    Type of transformation a stage performs.

    Types:
        MERGE: Combine multiple blocks into one
        SPLIT: Split a block into multiple blocks
        CONVERT: Convert block to a different type
        FILTER: Filter block content based on criteria
        EXTRACT: Extract a portion of block content
        ENRICH: Add metadata or annotations to block
    """
    MERGE = "merge"
    SPLIT = "split"
    CONVERT = "convert"
    FILTER = "filter"
    EXTRACT = "extract"
    ENRICH = "enrich"


class ErrorHandlingStrategy(str, Enum):
    """
    Strategy for handling errors during pipeline execution.

    Strategies:
        FAIL_FAST: Stop immediately on first error
        CONTINUE: Log error and continue with next stage
        RETRY: Retry failed stage with backoff
        SKIP: Skip failed stage and continue
    """
    FAIL_FAST = "fail_fast"
    CONTINUE = "continue"
    RETRY = "retry"
    SKIP = "skip"


# =============================================================================
# PIPELINE RESULT (NOT an OntologyObject - just a result container)
# =============================================================================


class StageResult(BaseModel):
    """Result from executing a single stage."""

    stage_id: str = Field(
        ...,
        description="ID of the executed stage"
    )
    stage_name: str = Field(
        default="",
        description="Name of the executed stage"
    )
    success: bool = Field(
        default=False,
        description="Whether the stage completed successfully"
    )
    output_block_ids: List[str] = Field(
        default_factory=list,
        description="IDs of blocks produced by this stage"
    )
    duration_ms: float = Field(
        default=0.0,
        ge=0,
        description="Stage execution duration in milliseconds"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if stage failed"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional stage execution metadata"
    )


class PipelineResult(BaseModel):
    """
    Result from executing a composition pipeline.

    This is a data container, not an OntologyObject, as it represents
    a transient execution result rather than a persistent domain entity.

    Attributes:
        pipeline_id: ID of the executed pipeline
        success: Whether the pipeline completed successfully
        output_blocks: List of block IDs produced by the pipeline
        stages_completed: Number of stages that completed
        total_duration_ms: Total execution time in milliseconds
        stage_results: Detailed results for each stage
        error: Error message if pipeline failed

    Example:
        ```python
        result = await pipeline.execute_async(input_blocks)
        if result.success:
            for block_id in result.output_blocks:
                print(f"Produced block: {block_id}")
        else:
            print(f"Pipeline failed: {result.error}")
        ```
    """

    pipeline_id: str = Field(
        ...,
        description="ID of the executed pipeline"
    )
    success: bool = Field(
        default=False,
        description="Whether the pipeline completed successfully"
    )
    output_blocks: List[str] = Field(
        default_factory=list,
        description="List of block IDs produced by the pipeline"
    )
    stages_completed: int = Field(
        default=0,
        ge=0,
        description="Number of stages that completed successfully"
    )
    total_duration_ms: float = Field(
        default=0.0,
        ge=0,
        description="Total execution time in milliseconds"
    )
    stage_results: List[StageResult] = Field(
        default_factory=list,
        description="Detailed results for each executed stage"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if pipeline failed"
    )
    cancelled: bool = Field(
        default=False,
        description="Whether the pipeline was cancelled"
    )
    started_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline completion timestamp"
    )

    def to_summary(self) -> Dict[str, Any]:
        """Generate a summary dict for display."""
        return {
            "pipeline_id": self.pipeline_id,
            "success": self.success,
            "stages_completed": self.stages_completed,
            "total_stages": len(self.stage_results),
            "duration_ms": self.total_duration_ms,
            "output_block_count": len(self.output_blocks),
            "error": self.error,
        }


# =============================================================================
# COMPOSITION STAGE OBJECTTYPE
# =============================================================================


@register_object_type
class CompositionStage(OntologyObject):
    """
    A single stage in a composition pipeline.

    A CompositionStage defines:
    - What transformation to apply (transform_type + config)
    - What block types it accepts (input_block_types)
    - What block type it produces (output_block_type)
    - Execution order within the pipeline

    Stages are the building blocks of pipelines. Each stage takes
    one or more blocks as input and produces transformed blocks as output.

    Attributes:
        name: Human-readable stage name
        stage_type: Type identifier for the stage (e.g., "text_merger")
        order: Execution order (0-based) within the pipeline
        transform_type: Type of transformation to perform
        transform_config: Configuration for the transformation
        input_block_types: List of BlockKind values accepted as input
        output_block_type: BlockKind value for output blocks
        stage_status: Current execution status
        pipeline_id: FK to parent CompositionPipeline
        error_message: Error message if stage failed
        started_at: Stage start timestamp
        completed_at: Stage completion timestamp

    Example:
        ```python
        stage = CompositionStage(
            name="Merge Text Blocks",
            stage_type="text_merger",
            transform_type=TransformType.MERGE,
            transform_config={"separator": "\\n\\n"},
            input_block_types=["text", "markdown"],
            output_block_type="text"
        )
        ```
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable stage name"
    )
    stage_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type identifier for the stage (e.g., 'text_merger')"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Stage description"
    )

    # Execution order
    order: int = Field(
        default=0,
        ge=0,
        description="Execution order (0-based) within the pipeline"
    )

    # Transform configuration
    transform_type: Optional[TransformType] = Field(
        default=None,
        description="Type of transformation to perform"
    )
    transform_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration for the transformation"
    )

    # Block type constraints
    input_block_types: List[str] = Field(
        default_factory=list,
        description="List of BlockKind values accepted as input"
    )
    output_block_type: Optional[str] = Field(
        default=None,
        description="BlockKind value for output blocks"
    )

    # Execution state
    stage_status: StageStatus = Field(
        default=StageStatus.PENDING,
        description="Current execution status"
    )

    # Relationships
    pipeline_id: Optional[str] = Field(
        default=None,
        description="FK to parent CompositionPipeline"
    )

    # Error handling
    error_message: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error message if stage failed"
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None,
        description="Stage start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Stage completion timestamp"
    )

    # Output tracking
    output_block_ids: List[str] = Field(
        default_factory=list,
        description="IDs of blocks produced by this stage"
    )

    # Retry tracking
    attempt_count: int = Field(
        default=0,
        ge=0,
        description="Number of execution attempts"
    )
    max_retries: int = Field(
        default=0,
        ge=0,
        description="Maximum retry attempts"
    )

    @field_validator("stage_type")
    @classmethod
    def validate_stage_type(cls, v: str) -> str:
        """Ensure stage_type follows snake_case convention."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"stage_type must be alphanumeric with underscores/hyphens: {v}"
            )
        return v.lower()

    @property
    def is_pending(self) -> bool:
        """Check if stage is pending execution."""
        return self.stage_status == StageStatus.PENDING

    @property
    def is_running(self) -> bool:
        """Check if stage is currently running."""
        return self.stage_status == StageStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if stage completed successfully."""
        return self.stage_status == StageStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if stage failed."""
        return self.stage_status == StageStatus.FAILED

    @property
    def is_terminal(self) -> bool:
        """Check if stage is in a terminal state."""
        return self.stage_status in {
            StageStatus.COMPLETED,
            StageStatus.FAILED,
            StageStatus.SKIPPED,
        }

    @property
    def duration_ms(self) -> float:
        """Calculate stage duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return 0.0

    def can_retry(self) -> bool:
        """Check if stage can be retried."""
        return self.attempt_count < self.max_retries

    def accepts_block_type(self, block_type: str) -> bool:
        """
        Check if stage accepts a given block type.

        Args:
            block_type: BlockKind value to check

        Returns:
            True if stage accepts this block type
        """
        if not self.input_block_types:
            return True  # No constraints means accept all
        return block_type in self.input_block_types

    def start(self) -> "CompositionStage":
        """Mark stage as started."""
        if self.stage_status != StageStatus.PENDING:
            raise ValueError(f"Cannot start stage in state: {self.stage_status.value}")
        self.stage_status = StageStatus.RUNNING
        self.started_at = utc_now()
        self.attempt_count += 1
        self.touch()
        return self

    def complete(self, output_block_ids: Optional[List[str]] = None) -> "CompositionStage":
        """Mark stage as completed."""
        if self.stage_status != StageStatus.RUNNING:
            raise ValueError(f"Cannot complete stage in state: {self.stage_status.value}")
        self.stage_status = StageStatus.COMPLETED
        self.completed_at = utc_now()
        if output_block_ids:
            self.output_block_ids = output_block_ids
        self.touch()
        return self

    def fail(self, error_message: str) -> "CompositionStage":
        """Mark stage as failed."""
        if self.stage_status != StageStatus.RUNNING:
            raise ValueError(f"Cannot fail stage in state: {self.stage_status.value}")
        self.stage_status = StageStatus.FAILED
        self.completed_at = utc_now()
        self.error_message = error_message
        self.touch()
        return self

    def skip(self, reason: Optional[str] = None) -> "CompositionStage":
        """Skip stage execution."""
        if self.stage_status != StageStatus.PENDING:
            raise ValueError(f"Cannot skip stage in state: {self.stage_status.value}")
        self.stage_status = StageStatus.SKIPPED
        if reason:
            self.error_message = f"Skipped: {reason}"
        self.touch()
        return self

    def reset(self) -> "CompositionStage":
        """Reset stage to pending state."""
        self.stage_status = StageStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.output_block_ids = []
        # Note: attempt_count is preserved for retry tracking
        self.touch()
        return self

    def execute(self, blocks: List[Any]) -> List[Any]:
        """
        Execute the stage transformation on input blocks.

        This is a synchronous execution method. For async execution,
        the pipeline handles orchestration.

        Args:
            blocks: List of input blocks to transform

        Returns:
            List of transformed blocks

        Raises:
            ValueError: If stage is not in PENDING state
            RuntimeError: If transformation fails
        """
        if self.stage_status != StageStatus.PENDING:
            raise ValueError(f"Cannot execute stage in state: {self.stage_status.value}")

        self.start()

        try:
            # Validate input blocks
            for block in blocks:
                block_type = getattr(block, "kind", None) or getattr(block, "block_type", "unknown")
                if not self.accepts_block_type(str(block_type)):
                    raise ValueError(f"Stage does not accept block type: {block_type}")

            # Execute transformation based on type
            output_blocks = self._execute_transform(blocks)

            # Track output block IDs
            output_ids = [getattr(b, "id", str(i)) for i, b in enumerate(output_blocks)]
            self.complete(output_ids)

            return output_blocks

        except Exception as e:
            self.fail(str(e))
            raise RuntimeError(f"Stage execution failed: {e}") from e

    def _execute_transform(self, blocks: List[Any]) -> List[Any]:
        """
        Execute the transformation logic.

        Subclasses or external handlers should implement specific
        transformation logic. This base implementation provides
        pass-through and basic transform handling.

        Args:
            blocks: Input blocks to transform

        Returns:
            Transformed blocks
        """
        if not self.transform_type:
            # No transform type - pass through
            return blocks

        # Basic transform implementations
        if self.transform_type == TransformType.MERGE:
            return self._transform_merge(blocks)
        elif self.transform_type == TransformType.SPLIT:
            return self._transform_split(blocks)
        elif self.transform_type == TransformType.FILTER:
            return self._transform_filter(blocks)
        elif self.transform_type == TransformType.EXTRACT:
            return self._transform_extract(blocks)
        elif self.transform_type == TransformType.ENRICH:
            return self._transform_enrich(blocks)
        elif self.transform_type == TransformType.CONVERT:
            return self._transform_convert(blocks)

        # Unknown transform - pass through
        return blocks

    def _transform_merge(self, blocks: List[Any]) -> List[Any]:
        """Merge multiple blocks into one."""
        if not blocks:
            return []

        # Get separator from config
        separator = self.transform_config.get("separator", "\n")

        # Extract content from blocks
        contents = []
        for block in blocks:
            content = getattr(block, "content", None) or getattr(block, "text", str(block))
            contents.append(str(content))

        # Create merged content
        merged_content = separator.join(contents)

        # Return as a single block (structure depends on block implementation)
        # For now, return a dict representing the merged block
        return [{
            "content": merged_content,
            "source_block_ids": [getattr(b, "id", None) for b in blocks],
            "transform": "merge",
        }]

    def _transform_split(self, blocks: List[Any]) -> List[Any]:
        """Split blocks into multiple blocks."""
        if not blocks:
            return []

        # Get split config
        delimiter = self.transform_config.get("delimiter", "\n")
        max_parts = self.transform_config.get("max_parts", 0)

        result = []
        for block in blocks:
            content = getattr(block, "content", None) or getattr(block, "text", str(block))
            if max_parts > 0:
                parts = str(content).split(delimiter, max_parts - 1)
            else:
                parts = str(content).split(delimiter)

            for i, part in enumerate(parts):
                result.append({
                    "content": part,
                    "source_block_id": getattr(block, "id", None),
                    "part_index": i,
                    "transform": "split",
                })

        return result

    def _transform_filter(self, blocks: List[Any]) -> List[Any]:
        """Filter blocks based on criteria."""
        if not blocks:
            return []

        # Get filter config
        filter_field = self.transform_config.get("field", "content")
        filter_pattern = self.transform_config.get("pattern", "")
        filter_min_length = self.transform_config.get("min_length", 0)

        result = []
        for block in blocks:
            value = getattr(block, filter_field, None) or str(block)

            # Apply length filter
            if filter_min_length > 0 and len(str(value)) < filter_min_length:
                continue

            # Apply pattern filter (simple substring match)
            if filter_pattern and filter_pattern not in str(value):
                continue

            result.append(block)

        return result

    def _transform_extract(self, blocks: List[Any]) -> List[Any]:
        """Extract portions from blocks."""
        if not blocks:
            return []

        # Get extract config
        start = self.transform_config.get("start", 0)
        end = self.transform_config.get("end", None)
        field = self.transform_config.get("field", "content")

        result = []
        for block in blocks:
            content = getattr(block, field, None) or str(block)
            extracted = str(content)[start:end]
            result.append({
                "content": extracted,
                "source_block_id": getattr(block, "id", None),
                "transform": "extract",
                "start": start,
                "end": end,
            })

        return result

    def _transform_enrich(self, blocks: List[Any]) -> List[Any]:
        """Add metadata to blocks."""
        if not blocks:
            return []

        # Get enrich config
        metadata = self.transform_config.get("metadata", {})

        result = []
        for block in blocks:
            # Create enriched block with additional metadata
            enriched = {
                "original_block": block,
                "enrichment": metadata,
                "transform": "enrich",
            }
            result.append(enriched)

        return result

    def _transform_convert(self, blocks: List[Any]) -> List[Any]:
        """Convert blocks to different types."""
        if not blocks:
            return []

        # Get target type from output_block_type or config
        target_type = self.output_block_type or self.transform_config.get("target_type", "text")

        result = []
        for block in blocks:
            content = getattr(block, "content", None) or getattr(block, "text", str(block))
            converted = {
                "content": str(content),
                "kind": target_type,
                "source_block_id": getattr(block, "id", None),
                "transform": "convert",
            }
            result.append(converted)

        return result

    def to_stage_result(self) -> StageResult:
        """Convert stage to a StageResult."""
        return StageResult(
            stage_id=self.id,
            stage_name=self.name,
            success=self.is_completed,
            output_block_ids=self.output_block_ids,
            duration_ms=self.duration_ms,
            error=self.error_message,
            metadata={
                "transform_type": self.transform_type.value if self.transform_type else None,
                "attempt_count": self.attempt_count,
            }
        )

    def __repr__(self) -> str:
        return (
            f"CompositionStage(name='{self.name}', "
            f"type='{self.stage_type}', "
            f"order={self.order}, "
            f"status={self.stage_status.value})"
        )


# =============================================================================
# COMPOSITION PIPELINE OBJECTTYPE
# =============================================================================


@register_object_type
class CompositionPipeline(OntologyObject):
    """
    A pipeline that orchestrates multiple composition stages.

    A CompositionPipeline:
    - Contains ordered stages that process blocks
    - Supports sequential, parallel, and branching execution
    - Provides error handling and recovery options
    - Tracks execution state and timing

    Pipelines are the primary orchestration unit for block composition.
    They take input blocks, process them through stages, and produce
    output blocks.

    Attributes:
        name: Unique pipeline identifier
        description: Pipeline description
        stage_ids: Ordered list of stage IDs
        input_block_ids: IDs of input blocks for execution
        output_block_id: ID of final output block
        execution_mode: How to execute stages (sequential/parallel/branching)
        error_handling: Strategy for handling errors
        pipeline_status: Current execution status
        current_stage_index: Index of currently executing stage
        context: Shared execution context
        total_stages: Total number of stages
        completed_stages: Number of completed stages
        started_at: Pipeline start timestamp
        completed_at: Pipeline completion timestamp
        error_message: Error message if pipeline failed

    Example:
        ```python
        pipeline = CompositionPipeline(
            name="document_processor",
            description="Process documents through extraction and enrichment",
            execution_mode=PipelineMode.SEQUENTIAL,
            error_handling=ErrorHandlingStrategy.FAIL_FAST
        )

        # Add stages
        pipeline.add_stage(extract_stage)
        pipeline.add_stage(enrich_stage)

        # Execute
        result = await pipeline.execute_async(input_blocks)
        ```
    """

    # Identity
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique pipeline identifier (snake_case)"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Pipeline description"
    )

    # Stages
    stage_ids: List[str] = Field(
        default_factory=list,
        description="Ordered list of stage IDs"
    )

    # Input/Output
    input_block_ids: List[str] = Field(
        default_factory=list,
        description="IDs of input blocks for execution"
    )
    output_block_id: Optional[str] = Field(
        default=None,
        description="ID of final output block"
    )

    # Execution configuration
    execution_mode: PipelineMode = Field(
        default=PipelineMode.SEQUENTIAL,
        description="How to execute stages"
    )
    error_handling: ErrorHandlingStrategy = Field(
        default=ErrorHandlingStrategy.FAIL_FAST,
        description="Strategy for handling errors"
    )

    # Execution state
    pipeline_status: PipelineStatus = Field(
        default=PipelineStatus.PENDING,
        description="Current execution status"
    )
    current_stage_index: int = Field(
        default=0,
        ge=0,
        description="Index of currently executing stage"
    )

    # Context
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Shared execution context"
    )

    # Progress tracking
    total_stages: int = Field(
        default=0,
        ge=0,
        description="Total number of stages"
    )
    completed_stages: int = Field(
        default=0,
        ge=0,
        description="Number of completed stages"
    )

    # Timing
    started_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Pipeline completion timestamp"
    )

    # Error tracking
    error_message: Optional[str] = Field(
        default=None,
        max_length=5000,
        description="Error message if pipeline failed"
    )

    # Internal stage cache (not persisted)
    _stages_cache: Dict[str, CompositionStage] = {}

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name follows snake_case convention."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                f"name must be alphanumeric with underscores/hyphens: {v}"
            )
        return v.lower()

    @property
    def is_pending(self) -> bool:
        """Check if pipeline is pending."""
        return self.pipeline_status == PipelineStatus.PENDING

    @property
    def is_running(self) -> bool:
        """Check if pipeline is running."""
        return self.pipeline_status == PipelineStatus.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if pipeline completed successfully."""
        return self.pipeline_status == PipelineStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if pipeline failed."""
        return self.pipeline_status == PipelineStatus.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if pipeline was cancelled."""
        return self.pipeline_status == PipelineStatus.CANCELLED

    @property
    def is_terminal(self) -> bool:
        """Check if pipeline is in a terminal state."""
        return self.pipeline_status in {
            PipelineStatus.COMPLETED,
            PipelineStatus.FAILED,
            PipelineStatus.CANCELLED,
        }

    @property
    def duration_ms(self) -> float:
        """Calculate pipeline duration in milliseconds."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return delta.total_seconds() * 1000
        return 0.0

    @property
    def progress_percent(self) -> float:
        """Calculate execution progress percentage."""
        if self.total_stages == 0:
            return 100.0
        return (self.completed_stages / self.total_stages) * 100

    def add_stage(self, stage: CompositionStage) -> "CompositionPipeline":
        """
        Add a stage to the pipeline.

        Args:
            stage: CompositionStage to add

        Returns:
            self for method chaining
        """
        stage.pipeline_id = self.id
        stage.order = len(self.stage_ids)
        self.stage_ids.append(stage.id)
        self.total_stages = len(self.stage_ids)
        self._stages_cache[stage.id] = stage
        self.touch()
        return self

    def remove_stage(self, stage_id: str) -> bool:
        """
        Remove a stage from the pipeline.

        Args:
            stage_id: ID of stage to remove

        Returns:
            True if stage was removed, False if not found
        """
        if stage_id in self.stage_ids:
            self.stage_ids.remove(stage_id)
            self.total_stages = len(self.stage_ids)
            if stage_id in self._stages_cache:
                del self._stages_cache[stage_id]
            self.touch()
            return True
        return False

    def get_stage(self, stage_id: str) -> Optional[CompositionStage]:
        """
        Get a stage by ID.

        Args:
            stage_id: ID of stage to retrieve

        Returns:
            CompositionStage if found, None otherwise
        """
        return self._stages_cache.get(stage_id)

    def get_stages(self) -> List[CompositionStage]:
        """
        Get all stages in order.

        Returns:
            List of stages in execution order
        """
        stages = []
        for stage_id in self.stage_ids:
            stage = self._stages_cache.get(stage_id)
            if stage:
                stages.append(stage)
        return sorted(stages, key=lambda s: s.order)

    def set_stages(self, stages: List[CompositionStage]) -> "CompositionPipeline":
        """
        Set all stages (replacing existing).

        Args:
            stages: List of stages to set

        Returns:
            self for method chaining
        """
        self.stage_ids = []
        self._stages_cache = {}
        for stage in stages:
            self.add_stage(stage)
        return self

    def execute(self, input_blocks: List[Any]) -> PipelineResult:
        """
        Execute the pipeline synchronously.

        Args:
            input_blocks: List of input blocks to process

        Returns:
            PipelineResult with execution outcome
        """
        # Track input blocks
        self.input_block_ids = [getattr(b, "id", str(i)) for i, b in enumerate(input_blocks)]

        # Initialize result
        result = PipelineResult(
            pipeline_id=self.id,
            started_at=utc_now(),
        )

        # Check if we can start
        if self.pipeline_status not in {PipelineStatus.PENDING}:
            result.error = f"Cannot execute pipeline in state: {self.pipeline_status.value}"
            return result

        # Start pipeline
        self.pipeline_status = PipelineStatus.RUNNING
        self.started_at = utc_now()
        self.current_stage_index = 0
        self.completed_stages = 0
        self.context = {"pipeline_id": self.id}
        self.touch()

        try:
            # Get stages
            stages = self.get_stages()
            if not stages:
                # No stages - pass through
                self.pipeline_status = PipelineStatus.COMPLETED
                self.completed_at = utc_now()
                result.success = True
                result.output_blocks = self.input_block_ids
                result.completed_at = utc_now()
                return result

            # Execute based on mode
            if self.execution_mode == PipelineMode.SEQUENTIAL:
                current_blocks = input_blocks
                for i, stage in enumerate(stages):
                    self.current_stage_index = i

                    try:
                        current_blocks = stage.execute(current_blocks)
                        result.stage_results.append(stage.to_stage_result())
                        self.completed_stages += 1
                    except Exception as e:
                        result.stage_results.append(stage.to_stage_result())

                        if self.error_handling == ErrorHandlingStrategy.FAIL_FAST:
                            raise
                        elif self.error_handling == ErrorHandlingStrategy.SKIP:
                            continue
                        elif self.error_handling == ErrorHandlingStrategy.CONTINUE:
                            continue
                        # RETRY would need additional logic

                # Success
                self.pipeline_status = PipelineStatus.COMPLETED
                self.completed_at = utc_now()
                result.success = True
                result.output_blocks = [getattr(b, "id", str(i)) for i, b in enumerate(current_blocks)]
                result.stages_completed = self.completed_stages
                result.completed_at = utc_now()
                result.total_duration_ms = self.duration_ms

            elif self.execution_mode == PipelineMode.PARALLEL:
                # For parallel mode, execute all stages on input blocks
                all_outputs = []
                for stage in stages:
                    try:
                        outputs = stage.execute(input_blocks.copy())
                        all_outputs.extend(outputs)
                        result.stage_results.append(stage.to_stage_result())
                        self.completed_stages += 1
                    except Exception as e:
                        result.stage_results.append(stage.to_stage_result())
                        if self.error_handling == ErrorHandlingStrategy.FAIL_FAST:
                            raise

                self.pipeline_status = PipelineStatus.COMPLETED
                self.completed_at = utc_now()
                result.success = True
                result.output_blocks = [getattr(b, "id", str(i)) for i, b in enumerate(all_outputs)]
                result.stages_completed = self.completed_stages
                result.completed_at = utc_now()
                result.total_duration_ms = self.duration_ms

            else:  # BRANCHING
                # Branching mode executes stages based on conditions
                # For now, fall back to sequential
                return self._execute_branching(input_blocks, stages, result)

        except Exception as e:
            self.pipeline_status = PipelineStatus.FAILED
            self.completed_at = utc_now()
            self.error_message = str(e)
            result.success = False
            result.error = str(e)
            result.stages_completed = self.completed_stages
            result.completed_at = utc_now()
            result.total_duration_ms = self.duration_ms

        self.touch()
        return result

    def _execute_branching(
        self,
        input_blocks: List[Any],
        stages: List[CompositionStage],
        result: PipelineResult
    ) -> PipelineResult:
        """
        Execute pipeline in branching mode.

        Branching evaluates conditions to select which stages to execute.
        """
        current_blocks = input_blocks

        for i, stage in enumerate(stages):
            self.current_stage_index = i

            # Check if stage should be executed (based on context conditions)
            condition = self.context.get(f"stage_{i}_condition", True)
            if not condition:
                stage.skip("Condition not met")
                result.stage_results.append(stage.to_stage_result())
                continue

            try:
                current_blocks = stage.execute(current_blocks)
                result.stage_results.append(stage.to_stage_result())
                self.completed_stages += 1

                # Update context with stage output for condition evaluation
                self.context[f"stage_{i}_output"] = current_blocks

            except Exception as e:
                result.stage_results.append(stage.to_stage_result())
                if self.error_handling == ErrorHandlingStrategy.FAIL_FAST:
                    raise

        self.pipeline_status = PipelineStatus.COMPLETED
        self.completed_at = utc_now()
        result.success = True
        result.output_blocks = [getattr(b, "id", str(i)) for i, b in enumerate(current_blocks)]
        result.stages_completed = self.completed_stages
        result.completed_at = utc_now()
        result.total_duration_ms = self.duration_ms

        return result

    async def execute_async(self, input_blocks: List[Any]) -> PipelineResult:
        """
        Execute the pipeline asynchronously.

        This enables true parallel execution in PARALLEL mode and
        async stage execution for I/O-bound operations.

        Args:
            input_blocks: List of input blocks to process

        Returns:
            PipelineResult with execution outcome
        """
        # Track input blocks
        self.input_block_ids = [getattr(b, "id", str(i)) for i, b in enumerate(input_blocks)]

        # Initialize result
        result = PipelineResult(
            pipeline_id=self.id,
            started_at=utc_now(),
        )

        # Check if we can start
        if self.pipeline_status not in {PipelineStatus.PENDING}:
            result.error = f"Cannot execute pipeline in state: {self.pipeline_status.value}"
            return result

        # Start pipeline
        self.pipeline_status = PipelineStatus.RUNNING
        self.started_at = utc_now()
        self.current_stage_index = 0
        self.completed_stages = 0
        self.context = {"pipeline_id": self.id}
        self.touch()

        try:
            stages = self.get_stages()
            if not stages:
                self.pipeline_status = PipelineStatus.COMPLETED
                self.completed_at = utc_now()
                result.success = True
                result.output_blocks = self.input_block_ids
                result.completed_at = utc_now()
                return result

            if self.execution_mode == PipelineMode.PARALLEL:
                # True parallel execution
                tasks = []
                for stage in stages:
                    # Wrap sync execute in async
                    task = asyncio.get_event_loop().run_in_executor(
                        None,
                        stage.execute,
                        input_blocks.copy()
                    )
                    tasks.append((stage, task))

                all_outputs = []
                for stage, task in tasks:
                    try:
                        outputs = await task
                        all_outputs.extend(outputs)
                        result.stage_results.append(stage.to_stage_result())
                        self.completed_stages += 1
                    except Exception as e:
                        result.stage_results.append(stage.to_stage_result())
                        if self.error_handling == ErrorHandlingStrategy.FAIL_FAST:
                            raise

                self.pipeline_status = PipelineStatus.COMPLETED
                self.completed_at = utc_now()
                result.success = True
                result.output_blocks = [getattr(b, "id", str(i)) for i, b in enumerate(all_outputs)]
                result.stages_completed = self.completed_stages
                result.completed_at = utc_now()
                result.total_duration_ms = self.duration_ms

            else:
                # Sequential/branching - use sync implementation
                return self.execute(input_blocks)

        except Exception as e:
            self.pipeline_status = PipelineStatus.FAILED
            self.completed_at = utc_now()
            self.error_message = str(e)
            result.success = False
            result.error = str(e)
            result.stages_completed = self.completed_stages
            result.completed_at = utc_now()
            result.total_duration_ms = self.duration_ms

        self.touch()
        return result

    def reset(self) -> None:
        """
        Reset pipeline to pending state.

        This resets execution state but preserves stages.
        """
        self.pipeline_status = PipelineStatus.PENDING
        self.current_stage_index = 0
        self.completed_stages = 0
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.input_block_ids = []
        self.output_block_id = None
        self.context = {}

        # Reset all stages
        for stage in self.get_stages():
            stage.reset()

        self.touch()

    def cancel(self) -> "CompositionPipeline":
        """Cancel pipeline execution."""
        if self.is_terminal:
            raise ValueError(f"Cannot cancel pipeline in state: {self.pipeline_status.value}")
        self.pipeline_status = PipelineStatus.CANCELLED
        self.completed_at = utc_now()
        self.touch()
        return self

    def to_result(self) -> PipelineResult:
        """Convert current pipeline state to a PipelineResult."""
        return PipelineResult(
            pipeline_id=self.id,
            success=self.is_completed,
            output_blocks=[self.output_block_id] if self.output_block_id else [],
            stages_completed=self.completed_stages,
            total_duration_ms=self.duration_ms,
            stage_results=[stage.to_stage_result() for stage in self.get_stages()],
            error=self.error_message,
            cancelled=self.is_cancelled,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )

    def __repr__(self) -> str:
        return (
            f"CompositionPipeline(name='{self.name}', "
            f"stages={self.total_stages}, "
            f"mode={self.execution_mode.value}, "
            f"status={self.pipeline_status.value}, "
            f"progress={self.progress_percent:.1f}%)"
        )

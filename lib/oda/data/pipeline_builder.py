"""
Orion ODA v4.0 - Pipeline Builder DSL (Phase 4.3.1)
====================================================

Palantir-style fluent API for data pipeline construction.

This module provides a declarative, type-safe pipeline builder that follows
the Palantir AIP/Foundry patterns for ETL pipeline definition.

Features:
- Fluent API for pipeline construction
- Stage dependency resolution
- Built-in validation
- Serializable pipeline definitions

Example:
    ```python
    from lib.oda.data.pipeline_builder import PipelineBuilder

    pipeline = (
        PipelineBuilder("etl_tasks")
        .source("database", {"table": "raw_tasks"})
        .filter("active_only", "status != 'deleted'")
        .transform("enrich", "add_metadata", {"fields": ["created_at"]})
        .aggregate("daily_counts", ["date"], {"count": "task_id"})
        .output("warehouse", "parquet", {"path": "/data/tasks"})
        .build()
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================


class StageType(str, Enum):
    """Types of pipeline stages."""
    SOURCE = "source"
    TRANSFORM = "transform"
    FILTER = "filter"
    AGGREGATE = "aggregate"
    JOIN = "join"
    OUTPUT = "output"


class PipelineStatus(str, Enum):
    """Pipeline lifecycle status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    ERROR = "error"


class RunStatus(str, Enum):
    """Pipeline run status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# PIPELINE STAGE
# =============================================================================


class PipelineStage(BaseModel):
    """
    Represents a single stage in a data pipeline.

    A stage is a unit of work in the pipeline that transforms, filters,
    or routes data. Stages can have dependencies on other stages.

    Attributes:
        stage_id: Unique identifier for this stage
        name: Human-readable name
        stage_type: Type of operation (source, transform, filter, etc.)
        config: Stage-specific configuration
        dependencies: List of stage_ids this stage depends on
        description: Optional description of what this stage does
    """

    stage_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())[:8],
        description="Unique identifier for this stage"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for this stage"
    )
    stage_type: StageType = Field(
        ...,
        description="Type of pipeline stage"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Stage-specific configuration"
    )
    dependencies: List[str] = Field(
        default_factory=list,
        description="List of stage_ids this stage depends on"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional description of this stage"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure name is valid."""
        normalized = v.strip()
        if not normalized:
            raise ValueError("Stage name cannot be empty")
        return normalized

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "stage_id": self.stage_id,
            "name": self.name,
            "stage_type": self.stage_type.value,
            "config": self.config,
            "dependencies": self.dependencies,
            "description": self.description,
        }


# =============================================================================
# PIPELINE DEFINITION
# =============================================================================


class Pipeline(BaseModel):
    """
    Complete pipeline definition with stages and metadata.

    A Pipeline is an ordered collection of stages that define
    a data transformation workflow. Pipelines can be scheduled,
    validated, and executed.

    Attributes:
        pipeline_id: Unique identifier for this pipeline
        name: Human-readable name
        description: Pipeline description
        stages: List of pipeline stages
        schedule: Optional cron expression for scheduling
        status: Current lifecycle status
        owner: ID of the pipeline owner
        created_at: Creation timestamp
        last_run: Timestamp of last execution
        version: Pipeline version for tracking changes
        tags: Optional tags for categorization
    """

    pipeline_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this pipeline"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable pipeline name"
    )
    description: str = Field(
        default="",
        max_length=2000,
        description="Pipeline description"
    )
    stages: List[PipelineStage] = Field(
        default_factory=list,
        description="Ordered list of pipeline stages"
    )
    schedule: Optional[str] = Field(
        default=None,
        description="Cron expression for scheduling (e.g., '0 0 * * *')"
    )
    status: PipelineStatus = Field(
        default=PipelineStatus.DRAFT,
        description="Current pipeline status"
    )
    owner: str = Field(
        ...,
        description="ID of the pipeline owner"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last update timestamp"
    )
    last_run: Optional[datetime] = Field(
        default=None,
        description="Timestamp of last execution"
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Pipeline version"
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Tags for categorization"
    )

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v: Optional[str]) -> Optional[str]:
        """Basic cron expression validation."""
        if v is None:
            return None

        parts = v.strip().split()
        # Standard cron has 5 parts (minute, hour, day, month, weekday)
        # Extended cron has 6 parts (adds seconds)
        if len(parts) not in (5, 6):
            raise ValueError(
                f"Invalid cron expression: expected 5 or 6 parts, got {len(parts)}"
            )
        return v.strip()

    def get_stage(self, stage_id: str) -> Optional[PipelineStage]:
        """Get a stage by ID."""
        for stage in self.stages:
            if stage.stage_id == stage_id:
                return stage
        return None

    def get_stage_by_name(self, name: str) -> Optional[PipelineStage]:
        """Get a stage by name."""
        for stage in self.stages:
            if stage.name == name:
                return stage
        return None

    def get_execution_order(self) -> List[str]:
        """
        Return stage IDs in topological order based on dependencies.

        Uses Kahn's algorithm for topological sorting.

        Returns:
            List of stage_ids in execution order

        Raises:
            ValueError: If circular dependency detected
        """
        # Build adjacency list and in-degree count
        in_degree: Dict[str, int] = {}
        graph: Dict[str, List[str]] = {}

        for stage in self.stages:
            in_degree[stage.stage_id] = len(stage.dependencies)
            graph[stage.stage_id] = []

        for stage in self.stages:
            for dep in stage.dependencies:
                if dep in graph:
                    graph[dep].append(stage.stage_id)

        # Find stages with no dependencies
        queue = [sid for sid, deg in in_degree.items() if deg == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(result) != len(self.stages):
            raise ValueError("Circular dependency detected in pipeline stages")

        return result

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "pipeline_id": self.pipeline_id,
            "name": self.name,
            "description": self.description,
            "stages": [s.to_dict() for s in self.stages],
            "schedule": self.schedule,
            "status": self.status.value,
            "owner": self.owner,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "version": self.version,
            "tags": self.tags,
        }


# =============================================================================
# PIPELINE RUN
# =============================================================================


class PipelineRun(BaseModel):
    """
    Represents a single execution of a pipeline.

    Tracks the status and results of each stage during execution.

    Attributes:
        run_id: Unique identifier for this run
        pipeline_id: ID of the pipeline being executed
        status: Current run status
        started_at: Execution start timestamp
        completed_at: Execution completion timestamp
        stage_results: Results from each stage
        error: Error message if failed
        triggered_by: How the run was triggered
        parameters: Runtime parameters for this run
    """

    run_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this run"
    )
    pipeline_id: str = Field(
        ...,
        description="ID of the pipeline being executed"
    )
    status: RunStatus = Field(
        default=RunStatus.PENDING,
        description="Current run status"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution start timestamp"
    )
    completed_at: Optional[datetime] = Field(
        default=None,
        description="Execution completion timestamp"
    )
    stage_results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Results from each stage (stage_id -> result)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if run failed"
    )
    triggered_by: str = Field(
        default="manual",
        description="How the run was triggered (manual, schedule, api)"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Runtime parameters for this run"
    )

    def mark_running(self) -> None:
        """Mark the run as started."""
        self.status = RunStatus.RUNNING
        self.started_at = datetime.now(timezone.utc)

    def mark_completed(self) -> None:
        """Mark the run as successfully completed."""
        self.status = RunStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, error: str) -> None:
        """Mark the run as failed."""
        self.status = RunStatus.FAILED
        self.completed_at = datetime.now(timezone.utc)
        self.error = error

    def mark_cancelled(self) -> None:
        """Mark the run as cancelled."""
        self.status = RunStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc)

    def set_stage_result(self, stage_id: str, result: Any) -> None:
        """Record the result of a stage execution."""
        self.stage_results[stage_id] = result

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate run duration in seconds."""
        if self.completed_at is None:
            return None
        return (self.completed_at - self.started_at).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "run_id": self.run_id,
            "pipeline_id": self.pipeline_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "stage_results": self.stage_results,
            "error": self.error,
            "triggered_by": self.triggered_by,
            "parameters": self.parameters,
            "duration_seconds": self.duration_seconds,
        }


# =============================================================================
# PIPELINE BUILDER
# =============================================================================


class PipelineBuilder:
    """
    Fluent API for constructing data pipelines.

    Provides a declarative, chainable interface for building
    pipeline definitions. Validates structure and dependencies
    at build time.

    Example:
        ```python
        pipeline = (
            PipelineBuilder("my_pipeline")
            .source("database", {"table": "users"})
            .filter("active", "status = 'active'")
            .transform("normalize", "lowercase", {"fields": ["email"]})
            .output("storage", "parquet", {"path": "/data/users"})
            .build()
        )
        ```
    """

    def __init__(
        self,
        pipeline_id: str,
        *,
        owner: str = "system",
        description: str = "",
    ):
        """
        Initialize a new PipelineBuilder.

        Args:
            pipeline_id: Unique identifier for the pipeline
            owner: ID of the pipeline owner (default: "system")
            description: Optional pipeline description
        """
        self._pipeline_id = pipeline_id
        self._owner = owner
        self._description = description
        self._stages: List[PipelineStage] = []
        self._stage_names: Set[str] = set()
        self._last_stage_id: Optional[str] = None
        self._schedule: Optional[str] = None
        self._tags: List[str] = []

        logger.debug(f"PipelineBuilder initialized: {pipeline_id}")

    def _add_stage(
        self,
        stage_type: StageType,
        name: str,
        config: Dict[str, Any],
        dependencies: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Internal method to add a stage to the pipeline.

        Args:
            stage_type: Type of stage
            name: Stage name
            config: Stage configuration
            dependencies: Explicit dependencies (if None, uses last stage)
            description: Optional stage description

        Returns:
            self for method chaining
        """
        if name in self._stage_names:
            raise ValueError(f"Duplicate stage name: '{name}'")

        # Auto-dependency: depend on last stage if not source and no explicit deps
        if dependencies is None:
            if stage_type != StageType.SOURCE and self._last_stage_id:
                dependencies = [self._last_stage_id]
            else:
                dependencies = []

        stage = PipelineStage(
            name=name,
            stage_type=stage_type,
            config=config,
            dependencies=dependencies,
            description=description,
        )

        self._stages.append(stage)
        self._stage_names.add(name)
        self._last_stage_id = stage.stage_id

        logger.debug(f"Added stage: {name} ({stage_type.value})")
        return self

    def source(
        self,
        source_type: str,
        config: Dict[str, Any],
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add a source stage to the pipeline.

        A source stage defines where data is read from.

        Args:
            source_type: Type of source (e.g., "database", "file", "api")
            config: Source configuration (connection details, query, etc.)
            name: Optional custom name (default: source_type)
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.source("database", {
                "table": "users",
                "connection": "postgres://..."
            })
            ```
        """
        stage_config = {"source_type": source_type, **config}
        return self._add_stage(
            stage_type=StageType.SOURCE,
            name=name or f"source_{source_type}",
            config=stage_config,
            dependencies=[],  # Sources have no dependencies
            description=description or f"Read from {source_type}",
        )

    def transform(
        self,
        name: str,
        transform_fn: str,
        config: Optional[Dict[str, Any]] = None,
        *,
        depends_on: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add a transform stage to the pipeline.

        A transform stage applies a transformation function to the data.

        Args:
            name: Stage name
            transform_fn: Name of the transformation function
            config: Optional transform configuration
            depends_on: Optional explicit dependencies
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.transform("enrich", "add_metadata", {
                "fields": ["created_at", "updated_at"]
            })
            ```
        """
        stage_config = {"transform_fn": transform_fn, **(config or {})}
        return self._add_stage(
            stage_type=StageType.TRANSFORM,
            name=name,
            config=stage_config,
            dependencies=depends_on,
            description=description or f"Transform: {transform_fn}",
        )

    def filter(
        self,
        name: str,
        condition: str,
        *,
        depends_on: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add a filter stage to the pipeline.

        A filter stage removes records that don't match a condition.

        Args:
            name: Stage name
            condition: Filter condition expression
            depends_on: Optional explicit dependencies
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.filter("active_only", "status != 'deleted'")
            ```
        """
        stage_config = {"condition": condition}
        return self._add_stage(
            stage_type=StageType.FILTER,
            name=name,
            config=stage_config,
            dependencies=depends_on,
            description=description or f"Filter: {condition}",
        )

    def aggregate(
        self,
        name: str,
        group_by: List[str],
        aggregations: Dict[str, str],
        *,
        depends_on: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add an aggregate stage to the pipeline.

        An aggregate stage groups records and applies aggregate functions.

        Args:
            name: Stage name
            group_by: List of fields to group by
            aggregations: Dict of {output_field: aggregation_expr}
            depends_on: Optional explicit dependencies
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.aggregate("daily_counts", ["date"], {
                "total": "count(task_id)",
                "completed": "sum(case when status='done' then 1 else 0 end)"
            })
            ```
        """
        stage_config = {"group_by": group_by, "aggregations": aggregations}
        return self._add_stage(
            stage_type=StageType.AGGREGATE,
            name=name,
            config=stage_config,
            dependencies=depends_on,
            description=description or f"Aggregate by {', '.join(group_by)}",
        )

    def join(
        self,
        name: str,
        other_pipeline: str,
        join_key: str,
        *,
        join_type: str = "inner",
        depends_on: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add a join stage to the pipeline.

        A join stage combines data from another pipeline.

        Args:
            name: Stage name
            other_pipeline: ID of the pipeline to join with
            join_key: Key field for joining
            join_type: Type of join (inner, left, right, outer)
            depends_on: Optional explicit dependencies
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.join("with_users", "user_pipeline", "user_id", join_type="left")
            ```
        """
        stage_config = {
            "other_pipeline": other_pipeline,
            "join_key": join_key,
            "join_type": join_type,
        }
        return self._add_stage(
            stage_type=StageType.JOIN,
            name=name,
            config=stage_config,
            dependencies=depends_on,
            description=description or f"Join with {other_pipeline} on {join_key}",
        )

    def output(
        self,
        name: str,
        output_type: str,
        config: Dict[str, Any],
        *,
        depends_on: Optional[List[str]] = None,
        description: Optional[str] = None,
    ) -> "PipelineBuilder":
        """
        Add an output stage to the pipeline.

        An output stage defines where data is written to.

        Args:
            name: Stage name
            output_type: Type of output (e.g., "parquet", "database", "api")
            config: Output configuration (path, connection, etc.)
            depends_on: Optional explicit dependencies
            description: Optional description

        Returns:
            self for method chaining

        Example:
            ```python
            builder.output("warehouse", "parquet", {
                "path": "/data/output",
                "partition_by": ["date"]
            })
            ```
        """
        stage_config = {"output_type": output_type, **config}
        return self._add_stage(
            stage_type=StageType.OUTPUT,
            name=name,
            config=stage_config,
            dependencies=depends_on,
            description=description or f"Write to {output_type}",
        )

    def with_schedule(self, cron_expression: str) -> "PipelineBuilder":
        """
        Set a schedule for the pipeline.

        Args:
            cron_expression: Cron expression (e.g., "0 0 * * *" for daily)

        Returns:
            self for method chaining
        """
        self._schedule = cron_expression
        return self

    def with_tags(self, *tags: str) -> "PipelineBuilder":
        """
        Add tags to the pipeline.

        Args:
            tags: Tag strings

        Returns:
            self for method chaining
        """
        self._tags.extend(tags)
        return self

    def with_description(self, description: str) -> "PipelineBuilder":
        """
        Set the pipeline description.

        Args:
            description: Pipeline description

        Returns:
            self for method chaining
        """
        self._description = description
        return self

    def validate(self) -> List[str]:
        """
        Validate the pipeline definition.

        Checks:
        - At least one source stage exists
        - At least one output stage exists
        - All dependencies reference existing stages
        - No circular dependencies
        - Stage names are unique

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for source stages
        source_stages = [s for s in self._stages if s.stage_type == StageType.SOURCE]
        if not source_stages:
            errors.append("Pipeline must have at least one source stage")

        # Check for output stages
        output_stages = [s for s in self._stages if s.stage_type == StageType.OUTPUT]
        if not output_stages:
            errors.append("Pipeline must have at least one output stage")

        # Check dependencies reference existing stages
        stage_ids = {s.stage_id for s in self._stages}
        for stage in self._stages:
            for dep in stage.dependencies:
                if dep not in stage_ids:
                    errors.append(
                        f"Stage '{stage.name}' references non-existent dependency: {dep}"
                    )

        # Check for circular dependencies
        try:
            pipeline = Pipeline(
                pipeline_id=self._pipeline_id,
                name=self._pipeline_id,
                stages=self._stages,
                owner=self._owner,
            )
            pipeline.get_execution_order()
        except ValueError as e:
            errors.append(str(e))

        return errors

    def build(self) -> Pipeline:
        """
        Build and return the Pipeline.

        Returns:
            Validated Pipeline instance

        Raises:
            ValueError: If pipeline validation fails
        """
        errors = self.validate()
        if errors:
            raise ValueError(f"Pipeline validation failed: {'; '.join(errors)}")

        pipeline = Pipeline(
            pipeline_id=self._pipeline_id,
            name=self._pipeline_id,
            description=self._description,
            stages=self._stages,
            schedule=self._schedule,
            owner=self._owner,
            tags=self._tags,
        )

        logger.info(f"Built pipeline: {self._pipeline_id} with {len(self._stages)} stages")
        return pipeline


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Enums
    "StageType",
    "PipelineStatus",
    "RunStatus",
    # Models
    "PipelineStage",
    "Pipeline",
    "PipelineRun",
    # Builder
    "PipelineBuilder",
]

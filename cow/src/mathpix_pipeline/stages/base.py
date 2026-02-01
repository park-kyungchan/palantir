"""
Base Stage Abstract Class for COW Pipeline.

Provides common interface and utilities for all pipeline stages (A-H).
Implements standard patterns for:
- Timing and metrics collection
- Error handling and result wrapping
- Input validation
- Stage lifecycle management

Module Version: 1.0.0
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Generic, List, Optional, TypeVar

from ..schemas.common import PipelineStage
from ..schemas.pipeline import StageTiming


# =============================================================================
# Type Variables
# =============================================================================

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


# =============================================================================
# Result Types
# =============================================================================

@dataclass
class ValidationResult:
    """Result of stage input validation.

    Attributes:
        is_valid: Whether validation passed
        warnings: List of non-fatal warnings
        errors: List of fatal errors
    """
    is_valid: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        """Add a non-fatal warning."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add a fatal error and mark as invalid."""
        self.errors.append(message)
        self.is_valid = False


@dataclass
class StageMetrics:
    """Metrics collected during stage execution.

    Attributes:
        stage: Pipeline stage identifier
        duration_ms: Execution duration in milliseconds
        elements_processed: Number of elements processed
        success: Whether execution succeeded
        custom_metrics: Stage-specific metrics
    """
    stage: PipelineStage
    duration_ms: float = 0.0
    elements_processed: int = 0
    success: bool = True
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageResult(Generic[OutputT]):
    """Standard result wrapper for all pipeline stages.

    Provides consistent interface for:
    - Output data access
    - Timing information
    - Validation and error tracking
    - Metrics collection

    Attributes:
        stage: Pipeline stage identifier
        output: Stage output data (None if failed)
        timing: Stage timing information
        validation: Input validation result
        metrics: Execution metrics
        warnings: Non-fatal warnings collected
        errors: Errors encountered (stage may still succeed with errors)
    """
    stage: PipelineStage
    output: Optional[OutputT] = None
    timing: Optional[StageTiming] = None
    validation: Optional[ValidationResult] = None
    metrics: Optional[StageMetrics] = None
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        """Check if stage executed successfully with valid output."""
        return self.output is not None and (
            self.timing is None or self.timing.success
        )

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings were collected."""
        return len(self.warnings) > 0

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)

    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)


# =============================================================================
# Stage Errors
# =============================================================================

class StageError(Exception):
    """Base exception for stage errors.

    Attributes:
        message: Error description
        stage: Pipeline stage that raised the error
        cause: Original exception if wrapped
    """

    def __init__(
        self,
        message: str,
        stage: PipelineStage,
        cause: Optional[Exception] = None,
    ):
        super().__init__(message)
        self.message = message
        self.stage = stage
        self.cause = cause

    def __str__(self) -> str:
        if self.cause:
            return f"[{self.stage.value}] {self.message}: {self.cause}"
        return f"[{self.stage.value}] {self.message}"


class StageValidationError(StageError):
    """Raised when stage input validation fails."""
    pass


class StageExecutionError(StageError):
    """Raised when stage execution fails."""
    pass


# =============================================================================
# Base Stage Abstract Class
# =============================================================================

class BaseStage(ABC, Generic[InputT, OutputT]):
    """Abstract base class for all pipeline stages.

    Provides common infrastructure:
    - Automatic timing and metrics collection
    - Standard validation flow
    - Error handling and result wrapping
    - Consistent logging interface

    Subclasses must implement:
    - stage_name: Property returning the PipelineStage enum
    - validate(): Input validation logic
    - _execute(): Core stage logic (sync)
    - _execute_async(): Core stage logic (async)

    Example usage:
        class IngestionStage(BaseStage[Union[str, Path, bytes], IngestionSpec]):
            @property
            def stage_name(self) -> PipelineStage:
                return PipelineStage.INGESTION

            def validate(self, input_data: InputT) -> ValidationResult:
                result = ValidationResult()
                if input_data is None:
                    result.add_error("Input data is required")
                return result

            async def _execute_async(
                self, input_data: InputT, **kwargs
            ) -> OutputT:
                # Core stage logic here
                return ingestion_spec
    """

    def __init__(self, config: Optional[Any] = None):
        """Initialize stage with optional configuration.

        Args:
            config: Stage-specific configuration object
        """
        self._config = config

    @property
    @abstractmethod
    def stage_name(self) -> PipelineStage:
        """Return the pipeline stage identifier."""
        pass

    @property
    def config(self) -> Optional[Any]:
        """Return stage configuration."""
        return self._config

    @abstractmethod
    def validate(self, input_data: InputT) -> ValidationResult:
        """Validate stage input.

        Args:
            input_data: Input to validate

        Returns:
            ValidationResult with validation status and any issues
        """
        pass

    @abstractmethod
    async def _execute_async(
        self,
        input_data: InputT,
        **kwargs: Any,
    ) -> OutputT:
        """Execute stage logic asynchronously.

        This is the core implementation method that subclasses must implement.
        It should focus only on the business logic, not timing or error handling.

        Args:
            input_data: Validated input data
            **kwargs: Additional stage-specific parameters

        Returns:
            Stage output

        Raises:
            StageExecutionError: If execution fails
        """
        pass

    def _execute(self, input_data: InputT, **kwargs: Any) -> OutputT:
        """Execute stage logic synchronously.

        Default implementation runs _execute_async in event loop.
        Override for purely synchronous stages.

        Args:
            input_data: Validated input data
            **kwargs: Additional parameters

        Returns:
            Stage output

        Raises:
            RuntimeError: If called from within an async context
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            # Already in async context - cannot use run_until_complete
            raise RuntimeError(
                "Cannot call _execute() from within async context. "
                "Use _execute_async() instead."
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
            # No loop running - create isolated loop with cleanup
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self._execute_async(input_data, **kwargs)
                )
            finally:
                loop.close()

    def get_metrics(self, output: OutputT) -> StageMetrics:
        """Collect metrics from stage execution.

        Override in subclasses to provide stage-specific metrics.

        Args:
            output: Stage output to analyze

        Returns:
            StageMetrics with execution statistics
        """
        return StageMetrics(
            stage=self.stage_name,
            success=output is not None,
        )

    async def run_async(
        self,
        input_data: InputT,
        skip_validation: bool = False,
        **kwargs: Any,
    ) -> StageResult[OutputT]:
        """Execute stage with full lifecycle management.

        Handles:
        1. Timing setup
        2. Input validation (unless skipped)
        3. Core execution
        4. Metrics collection
        5. Error handling and result wrapping

        Args:
            input_data: Stage input
            skip_validation: Skip input validation if True
            **kwargs: Additional parameters passed to _execute_async

        Returns:
            StageResult wrapping output, timing, and metrics
        """
        timing = StageTiming(stage=self.stage_name)
        result: StageResult[OutputT] = StageResult(
            stage=self.stage_name,
            timing=timing,
        )

        try:
            # Validate input
            if not skip_validation:
                validation = self.validate(input_data)
                result.validation = validation

                if not validation.is_valid:
                    timing.complete(success=False, error="Validation failed")
                    for error in validation.errors:
                        result.add_error(error)
                    return result

                # Add validation warnings
                for warning in validation.warnings:
                    result.add_warning(warning)

            # Execute core logic
            output = await self._execute_async(input_data, **kwargs)
            result.output = output

            # Complete timing BEFORE metrics collection (P1 fix)
            timing.complete(success=True)

            # Collect metrics with accurate duration
            result.metrics = self.get_metrics(output)
            result.metrics.duration_ms = timing.duration_ms

        except StageError as e:
            timing.complete(success=False, error=str(e))
            result.add_error(str(e))

        except Exception as e:
            timing.complete(success=False, error=str(e))
            result.add_error(f"Unexpected error: {e}")

        return result

    def run(
        self,
        input_data: InputT,
        skip_validation: bool = False,
        **kwargs: Any,
    ) -> StageResult[OutputT]:
        """Execute stage synchronously.

        Convenience wrapper around run_async for sync contexts.

        Args:
            input_data: Stage input
            skip_validation: Skip input validation if True
            **kwargs: Additional parameters

        Returns:
            StageResult wrapping output, timing, and metrics

        Raises:
            RuntimeError: If called from within an async context
        """
        import asyncio
        try:
            asyncio.get_running_loop()
            # Already in async context - cannot use run_until_complete
            raise RuntimeError(
                "Cannot call run() from within async context. "
                "Use run_async() instead."
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
            # No loop running - create isolated loop with cleanup
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(
                    self.run_async(input_data, skip_validation=skip_validation, **kwargs)
                )
            finally:
                loop.close()

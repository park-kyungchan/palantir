"""
Stage A: Ingestion Stage.

Handles image loading, validation, and preprocessing.
Converts raw image input into standardized IngestionSpec.

Module Version: 1.0.0
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..schemas.common import PipelineStage
from ..schemas.ingestion import IngestionSpec
from ..ingestion import (
    ImageLoader,
    ImageValidator,
    Preprocessor,
    IngestionError,
)
from .base import (
    BaseStage,
    ValidationResult,
    StageMetrics,
    StageExecutionError,
)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class IngestionStageConfig:
    """Configuration for Stage A ingestion.

    Attributes:
        enable_preprocessing: Whether to apply preprocessing
        preprocessing_operations: List of operations to apply
        storage_enabled: Whether to store processed images
        cache_dir: Directory for caching
    """
    enable_preprocessing: bool = True
    preprocessing_operations: List[str] = None
    storage_enabled: bool = True
    cache_dir: Optional[str] = None

    def __post_init__(self):
        if self.preprocessing_operations is None:
            self.preprocessing_operations = ["normalize", "denoise"]


# =============================================================================
# Input Type
# =============================================================================

# Input can be: file path, URL string, or raw bytes
ImageInput = Union[str, Path, bytes]


# =============================================================================
# Stage Implementation
# =============================================================================

class IngestionStage(BaseStage[ImageInput, IngestionSpec]):
    """Stage A: Image Ingestion.

    Processes raw image input through:
    1. Loading (from file, URL, or bytes)
    2. Validation (format, size, quality checks)
    3. Preprocessing (normalization, denoising)
    4. IngestionSpec creation

    Example:
        stage = IngestionStage(config=IngestionStageConfig())
        result = await stage.run_async(
            "/path/to/image.png",
            image_id="img_001"
        )
        if result.is_valid:
            ingestion_spec = result.output
    """

    def __init__(
        self,
        config: Optional[IngestionStageConfig] = None,
        image_loader: Optional[ImageLoader] = None,
        image_validator: Optional[ImageValidator] = None,
        preprocessor: Optional[Preprocessor] = None,
    ):
        """Initialize ingestion stage.

        Args:
            config: Stage configuration
            image_loader: Custom image loader (created if not provided)
            image_validator: Custom validator (created if not provided)
            preprocessor: Custom preprocessor (created if not provided)
        """
        super().__init__(config or IngestionStageConfig())
        self._image_loader = image_loader or ImageLoader()
        self._image_validator = image_validator or ImageValidator()
        self._preprocessor = preprocessor or Preprocessor()

    @property
    def stage_name(self) -> PipelineStage:
        """Return Stage A identifier."""
        return PipelineStage.INGESTION

    @property
    def config(self) -> IngestionStageConfig:
        """Return typed configuration."""
        return self._config

    def validate(self, input_data: ImageInput) -> ValidationResult:
        """Validate image input.

        Args:
            input_data: Image path, URL, or bytes

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        if input_data is None:
            result.add_error("Image input is required")
            return result

        # Validate path existence for file inputs
        if isinstance(input_data, (str, Path)) and not str(input_data).startswith(("http://", "https://")):
            path = Path(input_data)
            if not path.exists():
                result.add_error(f"Image file not found: {input_data}")

        # Validate bytes input
        if isinstance(input_data, bytes) and len(input_data) == 0:
            result.add_error("Empty image bytes provided")

        return result

    async def _execute_async(
        self,
        input_data: ImageInput,
        image_id: Optional[str] = None,
        **kwargs: Any,
    ) -> IngestionSpec:
        """Execute image ingestion.

        Args:
            input_data: Image path, URL, or bytes
            image_id: Optional image identifier (generated if not provided)
            **kwargs: Additional parameters

        Returns:
            IngestionSpec with processed image data

        Raises:
            StageExecutionError: If ingestion fails
        """
        import uuid

        # Generate image_id if not provided
        if image_id is None:
            image_id = f"img_{uuid.uuid4().hex[:8]}"

        try:
            # Load image based on input type
            if isinstance(input_data, bytes):
                loaded = await self._image_loader.load_from_bytes(input_data)
            elif isinstance(input_data, (str, Path)):
                path_str = str(input_data)
                if path_str.startswith(("http://", "https://")):
                    loaded = await self._image_loader.load_from_url(path_str)
                else:
                    loaded = await self._image_loader.load_from_path(path_str)
            else:
                raise IngestionError(f"Unsupported image type: {type(input_data)}")

            # Validate loaded image
            validation = self._image_validator.validate(loaded)

            # Preprocess if enabled
            if self.config.enable_preprocessing:
                processed = self._preprocessor.process(loaded)
            else:
                processed = loaded

            # Create spec
            spec = IngestionSpec(
                image_id=image_id,
                source_path=str(input_data) if isinstance(input_data, (str, Path)) else None,
                metadata=loaded.metadata,
                validation=validation,
                preprocessing_applied=(
                    self.config.preprocessing_operations
                    if self.config.enable_preprocessing
                    else []
                ),
            )

            return spec

        except IngestionError as e:
            raise StageExecutionError(
                message=str(e),
                stage=self.stage_name,
                cause=e,
            )
        except Exception as e:
            raise StageExecutionError(
                message=f"Ingestion failed: {e}",
                stage=self.stage_name,
                cause=e,
            )

    def get_metrics(self, output: IngestionSpec) -> StageMetrics:
        """Collect ingestion metrics.

        Args:
            output: IngestionSpec from execution

        Returns:
            StageMetrics with ingestion statistics
        """
        metrics = StageMetrics(
            stage=self.stage_name,
            success=output is not None,
            elements_processed=1 if output else 0,
        )

        if output:
            metrics.custom_metrics = {
                "image_id": output.image_id,
                "preprocessing_applied": output.preprocessing_applied,
                "has_validation_warnings": (
                    output.validation is not None and
                    not output.validation.is_valid
                ),
            }

        return metrics

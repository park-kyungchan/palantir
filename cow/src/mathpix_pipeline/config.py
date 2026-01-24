"""
Unified Configuration Loader for Math Image Parsing Pipeline v2.0.

This module provides a centralized configuration system for the entire
8-Stage Pipeline:
    A. Ingestion -> B. TextParse -> C. VisionParse -> D. Alignment
                                                          |
    H. Export <- G. HumanReview <- F. Regeneration <- E. SemanticGraph

Features:
- Dataclass-based configuration with sensible defaults
- Environment variable loading
- YAML/JSON file loading
- Validation with warnings
- Stage-specific configuration sections

Schema Version: 2.0.0
Module Version: 1.0.0

Usage:
    # From environment variables
    from mathpix_pipeline.config import PipelineConfig
    config = PipelineConfig.from_env()

    # From configuration file
    config = PipelineConfig.from_file("config.yaml")

    # Direct instantiation
    config = PipelineConfig(
        mathpix_app_id="your-app-id",
        mathpix_app_key="your-app-key",
    )

    # Validate configuration
    warnings = config.validate()
    for warning in warnings:
        print(f"Warning: {warning}")
"""

import json
import logging
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration Error
# =============================================================================

class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


# =============================================================================
# Stage-Specific Configuration Classes
# =============================================================================

@dataclass
class IngestionConfig:
    """Configuration for Stage A: Ingestion.

    Controls image loading, preprocessing, and storage behavior.

    Attributes:
        enable_preprocessing: Enable image preprocessing before pipeline.
            Default: True
        preprocessing_operations: List of preprocessing operations to apply.
            Options: ["normalize", "denoise", "deskew", "contrast", "sharpen"]
            Default: ["normalize", "denoise"]
        storage_enabled: Enable storage of processed images.
            Default: True
        cache_dir: Directory for caching processed images.
            Default: None (uses system temp directory)
        max_image_size_mb: Maximum image size in megabytes.
            Default: 10.0
        supported_formats: List of supported image formats.
            Default: ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"]
    """
    enable_preprocessing: bool = True
    preprocessing_operations: List[str] = field(
        default_factory=lambda: ["normalize", "denoise"]
    )
    storage_enabled: bool = True
    cache_dir: Optional[str] = None
    max_image_size_mb: float = 10.0
    supported_formats: List[str] = field(
        default_factory=lambda: ["png", "jpg", "jpeg", "gif", "webp", "bmp", "tiff"]
    )


@dataclass
class AlignmentConfig:
    """Configuration for Stage D: Alignment.

    Controls text-visual matching and threshold settings.

    Attributes:
        base_alignment_threshold: Minimum confidence for matched pairs.
            Range: 0.0-1.0, Default: 0.60
        base_inconsistency_threshold: Threshold for flagging inconsistencies.
            Range: 0.0-1.0, Default: 0.80
        enable_threshold_adjustment: Allow dynamic threshold adjustment based
            on feedback and context.
            Default: True
        enable_auto_fix_detection: Automatically detect fixable issues.
            Default: True
        max_unmatched_ratio: Maximum ratio of unmatched elements before warning.
            Range: 0.0-1.0, Default: 0.3
    """
    base_alignment_threshold: float = 0.60
    base_inconsistency_threshold: float = 0.80
    enable_threshold_adjustment: bool = True
    enable_auto_fix_detection: bool = True
    max_unmatched_ratio: float = 0.3


@dataclass
class SemanticGraphConfig:
    """Configuration for Stage E: Semantic Graph.

    Controls graph building and validation settings.

    Attributes:
        node_threshold: Confidence threshold for node inclusion.
            Range: 0.0-1.0, Default: 0.60
        edge_threshold: Confidence threshold for edge inference.
            Range: 0.0-1.0, Default: 0.55
        strict_validation: Treat warnings as errors during validation.
            Default: False
        spatial_overlap_threshold: Minimum IoU for INTERSECTS edges.
            Range: 0.0-1.0, Default: 0.1
        proximity_threshold_px: Maximum pixel distance for ADJACENT_TO edges.
            Default: 50.0
        edge_confidence_factor: Factor for edge confidence propagation.
            Range: 0.0-1.0, Default: 0.9
        isolated_node_penalty: Penalty for nodes with no connections.
            Range: 0.0-1.0, Default: 0.2
    """
    node_threshold: float = 0.60
    edge_threshold: float = 0.55
    strict_validation: bool = False
    spatial_overlap_threshold: float = 0.1
    proximity_threshold_px: float = 50.0
    edge_confidence_factor: float = 0.9
    isolated_node_penalty: float = 0.2


@dataclass
class RegenerationConfig:
    """Configuration for Stage F: Regeneration.

    Controls LaTeX and SVG regeneration behavior.

    Attributes:
        enable_latex_regeneration: Generate LaTeX output from semantic graph.
            Default: True
        enable_svg_regeneration: Generate SVG output from semantic graph.
            Default: True
        latex_template: LaTeX template to use for generation.
            Default: "default"
        svg_width: Default SVG width in pixels.
            Default: 800
        svg_height: Default SVG height in pixels.
            Default: 600
        include_tikz: Include TikZ code in LaTeX output.
            Default: True
        delta_comparison_enabled: Compare regenerated with original.
            Default: True
    """
    enable_latex_regeneration: bool = True
    enable_svg_regeneration: bool = True
    latex_template: str = "default"
    svg_width: int = 800
    svg_height: int = 600
    include_tikz: bool = True
    delta_comparison_enabled: bool = True


@dataclass
class HumanReviewConfig:
    """Configuration for Stage G: Human Review.

    Controls human-in-the-loop review settings.

    Attributes:
        enable_human_review: Enable human review queue.
            Default: True
        review_threshold: Confidence below which items require review.
            Range: 0.0-1.0, Default: 0.70
        auto_approve_threshold: Confidence above which items are auto-approved.
            Range: 0.0-1.0, Default: 0.95
        max_queue_size: Maximum number of items in review queue.
            Default: 1000
        session_timeout_minutes: Review session timeout in minutes.
            Default: 30
        require_multiple_reviewers: Require multiple reviewers for critical items.
            Default: False
        critical_item_threshold: Confidence below which item is critical.
            Range: 0.0-1.0, Default: 0.40
    """
    enable_human_review: bool = True
    review_threshold: float = 0.70
    auto_approve_threshold: float = 0.95
    max_queue_size: int = 1000
    session_timeout_minutes: int = 30
    require_multiple_reviewers: bool = False
    critical_item_threshold: float = 0.40


@dataclass
class ExportConfig:
    """Configuration for Stage H: Export.

    Controls export format and storage settings.

    Attributes:
        default_export_formats: Default formats for batch export.
            Options: ["json", "pdf", "latex", "svg"]
            Default: ["json"]
        output_directory: Default output directory for exports.
            Default: None (uses current directory)
        include_metadata: Include provenance metadata in exports.
            Default: True
        compress_output: Compress exported files.
            Default: False
        pdf_page_size: PDF page size.
            Options: "letter", "a4", "a3"
            Default: "letter"
        pdf_margins_pt: PDF margins in points.
            Default: 72 (1 inch)
    """
    default_export_formats: List[str] = field(
        default_factory=lambda: ["json"]
    )
    output_directory: Optional[str] = None
    include_metadata: bool = True
    compress_output: bool = False
    pdf_page_size: str = "letter"
    pdf_margins_pt: int = 72


@dataclass
class LoggingConfig:
    """Configuration for logging behavior.

    Attributes:
        log_level: Logging level.
            Options: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
            Default: "INFO"
        use_structlog: Use structlog for structured logging.
            Default: False
        json_logs: Output logs as JSON (requires structlog).
            Default: False
        log_file: Path to log file. None for stdout only.
            Default: None
        log_timing: Include timing information in logs.
            Default: True
        log_api_calls: Log external API calls (may contain sensitive data).
            Default: False
    """
    log_level: str = "INFO"
    use_structlog: bool = False
    json_logs: bool = False
    log_file: Optional[str] = None
    log_timing: bool = True
    log_api_calls: bool = False


# =============================================================================
# Main Pipeline Configuration
# =============================================================================

@dataclass
class PipelineConfig:
    """Unified configuration for the Math Image Parsing Pipeline.

    This is the main configuration class that holds all settings for the
    8-stage pipeline. It provides methods for loading configuration from
    environment variables, YAML/JSON files, and validation.

    Attributes:
        # API Keys (from environment)
        mathpix_app_id: Mathpix API application ID.
        mathpix_app_key: Mathpix API application key.
        anthropic_api_key: Anthropic API key for Claude-based processing.
        gemini_api_key: Google Gemini API key for vision processing.

        # Stage configurations
        ingestion: Stage A configuration.
        alignment: Stage D configuration.
        semantic_graph: Stage E configuration.
        regeneration: Stage F configuration.
        human_review: Stage G configuration.
        export: Stage H configuration.
        logging: Logging configuration.

        # Global settings
        pipeline_version: Pipeline version string.
        strict_mode: Enable strict mode (fail on warnings).
        debug_mode: Enable debug mode (verbose output).

    Usage:
        # Load from environment
        config = PipelineConfig.from_env()

        # Load from file
        config = PipelineConfig.from_file("config.yaml")

        # Validate
        warnings = config.validate()
    """
    # API Keys
    mathpix_app_id: Optional[str] = None
    mathpix_app_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

    # Stage configurations
    ingestion: IngestionConfig = field(default_factory=IngestionConfig)
    alignment: AlignmentConfig = field(default_factory=AlignmentConfig)
    semantic_graph: SemanticGraphConfig = field(default_factory=SemanticGraphConfig)
    regeneration: RegenerationConfig = field(default_factory=RegenerationConfig)
    human_review: HumanReviewConfig = field(default_factory=HumanReviewConfig)
    export: ExportConfig = field(default_factory=ExportConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Global settings
    pipeline_version: str = "2.0.0"
    strict_mode: bool = False
    debug_mode: bool = False

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load configuration from environment variables.

        Environment variables are mapped as follows:
        - MATHPIX_APP_ID -> mathpix_app_id
        - MATHPIX_APP_KEY -> mathpix_app_key
        - ANTHROPIC_API_KEY -> anthropic_api_key
        - GEMINI_API_KEY -> gemini_api_key
        - PIPELINE_LOG_LEVEL -> logging.log_level
        - PIPELINE_USE_STRUCTLOG -> logging.use_structlog
        - PIPELINE_JSON_LOGS -> logging.json_logs
        - PIPELINE_DEBUG -> debug_mode
        - PIPELINE_STRICT -> strict_mode
        - PIPELINE_CACHE_DIR -> ingestion.cache_dir
        - PIPELINE_OUTPUT_DIR -> export.output_directory

        Returns:
            PipelineConfig loaded from environment variables.
        """
        # Parse boolean environment variables
        def parse_bool(value: Optional[str], default: bool = False) -> bool:
            if value is None:
                return default
            return value.lower() in ("true", "1", "yes", "on")

        # Parse float environment variables
        def parse_float(value: Optional[str], default: float) -> float:
            if value is None:
                return default
            try:
                return float(value)
            except ValueError:
                logger.warning(f"Invalid float value: {value}, using default: {default}")
                return default

        # Load API keys
        mathpix_app_id = os.environ.get("MATHPIX_APP_ID")
        mathpix_app_key = os.environ.get("MATHPIX_APP_KEY")
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
        gemini_api_key = os.environ.get("GEMINI_API_KEY")

        # Load logging config
        logging_config = LoggingConfig(
            log_level=os.environ.get("PIPELINE_LOG_LEVEL", "INFO").upper(),
            use_structlog=parse_bool(os.environ.get("PIPELINE_USE_STRUCTLOG")),
            json_logs=parse_bool(os.environ.get("PIPELINE_JSON_LOGS")),
            log_file=os.environ.get("PIPELINE_LOG_FILE"),
            log_timing=parse_bool(os.environ.get("PIPELINE_LOG_TIMING"), True),
            log_api_calls=parse_bool(os.environ.get("PIPELINE_LOG_API_CALLS")),
        )

        # Load ingestion config
        ingestion_config = IngestionConfig(
            enable_preprocessing=parse_bool(
                os.environ.get("PIPELINE_ENABLE_PREPROCESSING"), True
            ),
            storage_enabled=parse_bool(
                os.environ.get("PIPELINE_STORAGE_ENABLED"), True
            ),
            cache_dir=os.environ.get("PIPELINE_CACHE_DIR"),
            max_image_size_mb=parse_float(
                os.environ.get("PIPELINE_MAX_IMAGE_SIZE_MB"), 10.0
            ),
        )

        # Load alignment config
        alignment_config = AlignmentConfig(
            base_alignment_threshold=parse_float(
                os.environ.get("PIPELINE_ALIGNMENT_THRESHOLD"), 0.60
            ),
            base_inconsistency_threshold=parse_float(
                os.environ.get("PIPELINE_INCONSISTENCY_THRESHOLD"), 0.80
            ),
            enable_threshold_adjustment=parse_bool(
                os.environ.get("PIPELINE_ENABLE_THRESHOLD_ADJUSTMENT"), True
            ),
        )

        # Load semantic graph config
        semantic_graph_config = SemanticGraphConfig(
            node_threshold=parse_float(
                os.environ.get("PIPELINE_NODE_THRESHOLD"), 0.60
            ),
            edge_threshold=parse_float(
                os.environ.get("PIPELINE_EDGE_THRESHOLD"), 0.55
            ),
            strict_validation=parse_bool(
                os.environ.get("PIPELINE_STRICT_VALIDATION")
            ),
        )

        # Load regeneration config
        regeneration_config = RegenerationConfig(
            enable_latex_regeneration=parse_bool(
                os.environ.get("PIPELINE_ENABLE_LATEX_REGEN"), True
            ),
            enable_svg_regeneration=parse_bool(
                os.environ.get("PIPELINE_ENABLE_SVG_REGEN"), True
            ),
        )

        # Load human review config
        human_review_config = HumanReviewConfig(
            enable_human_review=parse_bool(
                os.environ.get("PIPELINE_ENABLE_HUMAN_REVIEW"), True
            ),
            review_threshold=parse_float(
                os.environ.get("PIPELINE_REVIEW_THRESHOLD"), 0.70
            ),
        )

        # Load export config
        export_config = ExportConfig(
            output_directory=os.environ.get("PIPELINE_OUTPUT_DIR"),
            include_metadata=parse_bool(
                os.environ.get("PIPELINE_INCLUDE_METADATA"), True
            ),
            compress_output=parse_bool(
                os.environ.get("PIPELINE_COMPRESS_OUTPUT")
            ),
        )

        # Parse default export formats from comma-separated string
        export_formats_str = os.environ.get("PIPELINE_EXPORT_FORMATS")
        if export_formats_str:
            export_config.default_export_formats = [
                fmt.strip().lower()
                for fmt in export_formats_str.split(",")
                if fmt.strip()
            ]

        # Global settings
        debug_mode = parse_bool(os.environ.get("PIPELINE_DEBUG"))
        strict_mode = parse_bool(os.environ.get("PIPELINE_STRICT"))

        return cls(
            mathpix_app_id=mathpix_app_id,
            mathpix_app_key=mathpix_app_key,
            anthropic_api_key=anthropic_api_key,
            gemini_api_key=gemini_api_key,
            ingestion=ingestion_config,
            alignment=alignment_config,
            semantic_graph=semantic_graph_config,
            regeneration=regeneration_config,
            human_review=human_review_config,
            export=export_config,
            logging=logging_config,
            debug_mode=debug_mode,
            strict_mode=strict_mode,
        )

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "PipelineConfig":
        """Load configuration from a YAML or JSON file.

        The file format is detected from the extension:
        - .yaml, .yml -> YAML format
        - .json -> JSON format

        Args:
            path: Path to the configuration file.

        Returns:
            PipelineConfig loaded from the file.

        Raises:
            ConfigurationError: If the file cannot be loaded or parsed.
            FileNotFoundError: If the file does not exist.
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")

        content = path.read_text(encoding="utf-8")
        suffix = path.suffix.lower()

        try:
            if suffix in (".yaml", ".yml"):
                try:
                    import yaml
                except ImportError:
                    raise ConfigurationError(
                        "PyYAML is required for YAML config files. "
                        "Install with: pip install pyyaml"
                    )
                data = yaml.safe_load(content)
            elif suffix == ".json":
                data = json.loads(content)
            else:
                raise ConfigurationError(
                    f"Unsupported configuration file format: {suffix}. "
                    "Supported formats: .yaml, .yml, .json"
                )
        except (json.JSONDecodeError, Exception) as e:
            raise ConfigurationError(f"Failed to parse configuration file: {e}")

        if not isinstance(data, dict):
            raise ConfigurationError("Configuration file must contain a dictionary")

        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Create configuration from a dictionary.

        Args:
            data: Dictionary with configuration values.

        Returns:
            PipelineConfig instance.
        """
        # Extract stage configurations
        ingestion_data = data.get("ingestion", {})
        alignment_data = data.get("alignment", {})
        semantic_graph_data = data.get("semantic_graph", {})
        regeneration_data = data.get("regeneration", {})
        human_review_data = data.get("human_review", {})
        export_data = data.get("export", {})
        logging_data = data.get("logging", {})

        return cls(
            # API Keys
            mathpix_app_id=data.get("mathpix_app_id"),
            mathpix_app_key=data.get("mathpix_app_key"),
            anthropic_api_key=data.get("anthropic_api_key"),
            gemini_api_key=data.get("gemini_api_key"),
            # Stage configs
            ingestion=IngestionConfig(**ingestion_data) if ingestion_data else IngestionConfig(),
            alignment=AlignmentConfig(**alignment_data) if alignment_data else AlignmentConfig(),
            semantic_graph=SemanticGraphConfig(**semantic_graph_data) if semantic_graph_data else SemanticGraphConfig(),
            regeneration=RegenerationConfig(**regeneration_data) if regeneration_data else RegenerationConfig(),
            human_review=HumanReviewConfig(**human_review_data) if human_review_data else HumanReviewConfig(),
            export=ExportConfig(**export_data) if export_data else ExportConfig(),
            logging=LoggingConfig(**logging_data) if logging_data else LoggingConfig(),
            # Global settings
            pipeline_version=data.get("pipeline_version", "2.0.0"),
            strict_mode=data.get("strict_mode", False),
            debug_mode=data.get("debug_mode", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to a dictionary.

        Returns:
            Dictionary representation of the configuration.
        """
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert configuration to JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            JSON string representation.
        """
        return json.dumps(self.to_dict(), indent=indent)

    def to_yaml(self) -> str:
        """Convert configuration to YAML string.

        Returns:
            YAML string representation.

        Raises:
            ConfigurationError: If PyYAML is not installed.
        """
        try:
            import yaml
        except ImportError:
            raise ConfigurationError(
                "PyYAML is required for YAML output. "
                "Install with: pip install pyyaml"
            )
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def save(self, path: Union[str, Path]) -> None:
        """Save configuration to a file.

        The format is determined by the file extension.

        Args:
            path: Output file path (.yaml, .yml, or .json).

        Raises:
            ConfigurationError: If the format is unsupported.
        """
        path = Path(path)
        suffix = path.suffix.lower()

        if suffix in (".yaml", ".yml"):
            content = self.to_yaml()
        elif suffix == ".json":
            content = self.to_json()
        else:
            raise ConfigurationError(
                f"Unsupported output format: {suffix}. "
                "Use .yaml, .yml, or .json"
            )

        path.write_text(content, encoding="utf-8")
        logger.info(f"Configuration saved to: {path}")

    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings.

        Performs validation checks on all configuration values and
        returns a list of warning messages. Critical issues are logged
        as warnings.

        Returns:
            List of validation warning strings.
        """
        warnings: List[str] = []

        # Check API keys
        if not self.mathpix_app_id:
            warnings.append("mathpix_app_id is not set - Stage B (TextParse) will not work")
        if not self.mathpix_app_key:
            warnings.append("mathpix_app_key is not set - Stage B (TextParse) will not work")
        if not self.anthropic_api_key:
            warnings.append("anthropic_api_key is not set - Claude-based features unavailable")

        # Validate threshold ranges
        def check_threshold(name: str, value: float, min_val: float = 0.0, max_val: float = 1.0) -> None:
            if not (min_val <= value <= max_val):
                warnings.append(
                    f"{name} ({value}) is outside valid range [{min_val}, {max_val}]"
                )

        # Alignment thresholds
        check_threshold(
            "alignment.base_alignment_threshold",
            self.alignment.base_alignment_threshold
        )
        check_threshold(
            "alignment.base_inconsistency_threshold",
            self.alignment.base_inconsistency_threshold
        )
        check_threshold(
            "alignment.max_unmatched_ratio",
            self.alignment.max_unmatched_ratio
        )

        # Semantic graph thresholds
        check_threshold(
            "semantic_graph.node_threshold",
            self.semantic_graph.node_threshold
        )
        check_threshold(
            "semantic_graph.edge_threshold",
            self.semantic_graph.edge_threshold
        )
        check_threshold(
            "semantic_graph.spatial_overlap_threshold",
            self.semantic_graph.spatial_overlap_threshold
        )
        check_threshold(
            "semantic_graph.edge_confidence_factor",
            self.semantic_graph.edge_confidence_factor
        )
        check_threshold(
            "semantic_graph.isolated_node_penalty",
            self.semantic_graph.isolated_node_penalty
        )

        # Human review thresholds
        check_threshold(
            "human_review.review_threshold",
            self.human_review.review_threshold
        )
        check_threshold(
            "human_review.auto_approve_threshold",
            self.human_review.auto_approve_threshold
        )
        check_threshold(
            "human_review.critical_item_threshold",
            self.human_review.critical_item_threshold
        )

        # Validate threshold relationships
        if self.human_review.review_threshold >= self.human_review.auto_approve_threshold:
            warnings.append(
                "human_review.review_threshold should be less than auto_approve_threshold"
            )

        if self.human_review.critical_item_threshold >= self.human_review.review_threshold:
            warnings.append(
                "human_review.critical_item_threshold should be less than review_threshold"
            )

        if self.semantic_graph.edge_threshold > self.semantic_graph.node_threshold:
            warnings.append(
                "semantic_graph.edge_threshold is higher than node_threshold - "
                "this may result in few edges"
            )

        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.logging.log_level.upper() not in valid_log_levels:
            warnings.append(
                f"logging.log_level '{self.logging.log_level}' is not valid. "
                f"Use one of: {valid_log_levels}"
            )

        # Validate export formats
        valid_export_formats = {"json", "pdf", "latex", "svg"}
        for fmt in self.export.default_export_formats:
            if fmt.lower() not in valid_export_formats:
                warnings.append(
                    f"export.default_export_formats contains unknown format: {fmt}. "
                    f"Valid formats: {valid_export_formats}"
                )

        # Validate PDF page size
        valid_page_sizes = {"letter", "a4", "a3", "legal"}
        if self.export.pdf_page_size.lower() not in valid_page_sizes:
            warnings.append(
                f"export.pdf_page_size '{self.export.pdf_page_size}' is not valid. "
                f"Use one of: {valid_page_sizes}"
            )

        # Validate preprocessing operations
        valid_preprocessing_ops = {"normalize", "denoise", "deskew", "contrast", "sharpen", "binarize"}
        for op in self.ingestion.preprocessing_operations:
            if op.lower() not in valid_preprocessing_ops:
                warnings.append(
                    f"ingestion.preprocessing_operations contains unknown operation: {op}. "
                    f"Valid operations: {valid_preprocessing_ops}"
                )

        # Validate numeric bounds
        if self.ingestion.max_image_size_mb <= 0:
            warnings.append("ingestion.max_image_size_mb must be positive")

        if self.human_review.max_queue_size <= 0:
            warnings.append("human_review.max_queue_size must be positive")

        if self.human_review.session_timeout_minutes <= 0:
            warnings.append("human_review.session_timeout_minutes must be positive")

        if self.export.pdf_margins_pt < 0:
            warnings.append("export.pdf_margins_pt cannot be negative")

        if self.semantic_graph.proximity_threshold_px < 0:
            warnings.append("semantic_graph.proximity_threshold_px cannot be negative")

        # Check structlog dependency
        if self.logging.use_structlog:
            try:
                import structlog  # noqa: F401
            except ImportError:
                warnings.append(
                    "logging.use_structlog is True but structlog is not installed. "
                    "Install with: pip install structlog"
                )

        if self.logging.json_logs and not self.logging.use_structlog:
            warnings.append(
                "logging.json_logs is True but use_structlog is False. "
                "JSON logs require structlog."
            )

        # Log warnings
        for warning in warnings:
            logger.warning(f"Configuration: {warning}")

        return warnings

    def is_valid(self) -> bool:
        """Check if configuration is valid (no critical issues).

        Returns:
            True if configuration has no critical issues.
        """
        warnings = self.validate()
        # Critical patterns that indicate invalid configuration
        critical_patterns = [
            "is outside valid range",
            "must be positive",
            "cannot be negative",
            "is not set",  # API key warnings are critical
        ]
        critical_warnings = [
            w for w in warnings
            if any(pattern in w for pattern in critical_patterns)
        ]
        return len(critical_warnings) == 0

    def validate_api_keys(self) -> Tuple[bool, List[str]]:
        """Validate API keys are properly configured.

        Returns:
            Tuple of (is_valid, list of missing keys)
        """
        missing = []
        if not self.mathpix_app_id:
            missing.append("mathpix_app_id")
        if not self.mathpix_app_key:
            missing.append("mathpix_app_key")
        return len(missing) == 0, missing

    def get_stage_config(self, stage: str) -> Any:
        """Get configuration for a specific stage.

        Args:
            stage: Stage identifier (a, b, c, d, e, f, g, h) or name.

        Returns:
            Stage-specific configuration object.

        Raises:
            ValueError: If stage is not recognized.
        """
        stage_map = {
            "a": self.ingestion,
            "ingestion": self.ingestion,
            "d": self.alignment,
            "alignment": self.alignment,
            "e": self.semantic_graph,
            "semantic_graph": self.semantic_graph,
            "f": self.regeneration,
            "regeneration": self.regeneration,
            "g": self.human_review,
            "human_review": self.human_review,
            "h": self.export,
            "export": self.export,
        }

        stage_lower = stage.lower()
        if stage_lower not in stage_map:
            raise ValueError(
                f"Unknown stage: {stage}. "
                f"Valid stages: {list(stage_map.keys())}"
            )

        return stage_map[stage_lower]

    def merge(self, overrides: Dict[str, Any]) -> "PipelineConfig":
        """Create a new configuration with overrides applied.

        Args:
            overrides: Dictionary of values to override.

        Returns:
            New PipelineConfig with overrides applied.
        """
        current = self.to_dict()
        _deep_merge(current, overrides)
        return PipelineConfig._from_dict(current)


# =============================================================================
# Helper Functions
# =============================================================================

def _deep_merge(base: Dict[str, Any], overrides: Dict[str, Any]) -> None:
    """Deep merge overrides into base dictionary (mutates base).

    Args:
        base: Base dictionary to merge into.
        overrides: Override values to apply.
    """
    for key, value in overrides.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            _deep_merge(base[key], value)
        else:
            base[key] = value


def load_config(
    path: Optional[Union[str, Path]] = None,
    use_env: bool = True,
) -> PipelineConfig:
    """Load configuration from file and/or environment.

    This is a convenience function that:
    1. Loads defaults
    2. Optionally loads from file
    3. Optionally overlays environment variables

    Args:
        path: Optional path to configuration file.
        use_env: Whether to load from environment variables.

    Returns:
        PipelineConfig with merged configuration.
    """
    # Start with defaults
    config = PipelineConfig()

    # Load from file if provided
    if path:
        config = PipelineConfig.from_file(path)

    # Overlay environment variables
    if use_env:
        env_config = PipelineConfig.from_env()
        # Merge non-None API keys
        if env_config.mathpix_app_id:
            config.mathpix_app_id = env_config.mathpix_app_id
        if env_config.mathpix_app_key:
            config.mathpix_app_key = env_config.mathpix_app_key
        if env_config.anthropic_api_key:
            config.anthropic_api_key = env_config.anthropic_api_key
        if env_config.gemini_api_key:
            config.gemini_api_key = env_config.gemini_api_key

    return config


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Main configuration
    "PipelineConfig",
    # Stage configurations
    "IngestionConfig",
    "AlignmentConfig",
    "SemanticGraphConfig",
    "RegenerationConfig",
    "HumanReviewConfig",
    "ExportConfig",
    "LoggingConfig",
    # Exceptions
    "ConfigurationError",
    # Helper functions
    "load_config",
]

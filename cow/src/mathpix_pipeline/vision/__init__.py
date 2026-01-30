"""
Math Image Parsing Pipeline - Vision Module (Stage C)

V2.0 Architecture (Gemini-First):
- Gemini 3 Pro for unified detection + interpretation (PRIMARY)
- YOLO26 + Claude Opus 4.5 as fallback
- ValidationVisualizer (C7) for cross-model validation
- Circuit breaker for API stability

Legacy Architecture (Fallback):
- YOLO26 for bbox detection (precise localization)
- Claude Opus 4.5 for semantic interpretation (understanding)
- HybridMerger for combining results

Reference: .agent/prompts/stage-c-redesign-20260130/plan.yaml
"""

# Legacy modules (YOLO + Claude)
from .yolo_detector import (
    YOLOConfig,
    YOLODetector,
    MockYOLODetector,
    create_detector,
)
from .interpretation_layer import (
    LLMProvider,
    InterpretationConfig,
    DiagramInterpreter,
    MockDiagramInterpreter,
    create_interpreter,
)
from .hybrid_merger import (
    MergerConfig,
    HybridMerger,
    compute_overall_confidence,
    get_elements_needing_review,
)

# Fallback (Gemini-First architecture)
from .fallback import (
    FallbackLevel,
    FailureReason,
    FallbackConfig,
    FallbackExecutor,
    CircuitState,
    CircuitBreaker,
    convert_gemini_to_vision_spec,
    process_with_fallback,
    get_circuit_breaker_status,
)

# Legacy Gemini Client (v1)
from .gemini_client import (
    GeminiVisionClient as LegacyGeminiVisionClient,
    create_gemini_client as create_legacy_gemini_client,
)

# New Gemini Vision Client (v2 - Gemini 3 Pro)
from .gemini_vision_client import (
    GeminiVisionClient,
    MockGeminiVisionClient,
    GeminiClientError,
    GeminiAPIError,
    GeminiParseError,
    DetectionResult,
    create_gemini_client,
)

# Gemini Config & Enums
from .gemini.config import (
    MediaResolution,
    ThinkingMode,
    GeminiCapability,
    FallbackBehavior,
    GeminiConfig,
    create_default_config,
    create_high_precision_config,
    create_fast_config,
    create_test_config,
)

# Validation Layer (C7)
from .validation_visualizer import (
    ValidationMode,
    ValidationSeverity,
    ValidationIssue,
    ValidationResult,
    ValidationVisualizer,
    create_validator,
    validate_gemini_output,
    get_validation_mode,
)

# Feature Flags (Gradual Rollout)
from .feature_flags import (
    ValidationModeFlag,
    ThinkingModeFlag,
    FeatureFlags,
    get_feature_flags,
    reset_feature_flags,
    is_gemini_enabled,
    is_gemini_primary,
    is_yolo_deprecated,
    get_validation_mode as get_validation_mode_flag,
    get_thinking_mode,
    should_use_gemini,
    get_processing_strategy,
    log_feature_flags,
)

# Supporting modules
from .label_normalizer import (
    SemanticLabelNormalizer,
    get_normalizer,
)
from .confidence_calibrator import (
    ConfidenceCalibrator,
    get_calibrator,
)
from .coordinate_converter import (
    convert_box_2d_to_bbox,
)

# Exceptions
from .exceptions import (
    VisionError,
    YoloError,
    YoloDetectionTimeoutError,
    YoloLowConfidenceError,
    YoloNoDetectionsError,
    ClaudeError,
    ClaudeAPIError,
    ClaudeTimeoutError,
    GeminiError,
    GeminiTimeoutError,
    FallbackChainExhaustedError,
)

__all__ = [
    # =========================================================================
    # Gemini 3 Pro Client (V2 - Primary)
    # =========================================================================
    "GeminiVisionClient",
    "MockGeminiVisionClient",
    "GeminiClientError",
    "GeminiAPIError",
    "GeminiParseError",
    "DetectionResult",
    "create_gemini_client",
    # Gemini Config
    "MediaResolution",
    "ThinkingMode",
    "GeminiCapability",
    "FallbackBehavior",
    "GeminiConfig",
    "create_default_config",
    "create_high_precision_config",
    "create_fast_config",
    "create_test_config",
    # =========================================================================
    # Validation Layer (C7)
    # =========================================================================
    "ValidationMode",
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationResult",
    "ValidationVisualizer",
    "create_validator",
    "validate_gemini_output",
    "get_validation_mode",
    # =========================================================================
    # Feature Flags (Gradual Rollout)
    # =========================================================================
    "ValidationModeFlag",
    "ThinkingModeFlag",
    "FeatureFlags",
    "get_feature_flags",
    "reset_feature_flags",
    "is_gemini_enabled",
    "is_gemini_primary",
    "is_yolo_deprecated",
    "get_validation_mode_flag",
    "get_thinking_mode",
    "should_use_gemini",
    "get_processing_strategy",
    "log_feature_flags",
    # =========================================================================
    # Fallback (Gemini-First)
    # =========================================================================
    "FallbackLevel",
    "FailureReason",
    "FallbackConfig",
    "FallbackExecutor",
    "CircuitState",
    "CircuitBreaker",
    "convert_gemini_to_vision_spec",
    "process_with_fallback",
    "get_circuit_breaker_status",
    # =========================================================================
    # Supporting Modules
    # =========================================================================
    "SemanticLabelNormalizer",
    "get_normalizer",
    "ConfidenceCalibrator",
    "get_calibrator",
    "convert_box_2d_to_bbox",
    # =========================================================================
    # Legacy (YOLO + Claude)
    # =========================================================================
    "YOLOConfig",
    "YOLODetector",
    "MockYOLODetector",
    "create_detector",
    "LLMProvider",
    "InterpretationConfig",
    "DiagramInterpreter",
    "MockDiagramInterpreter",
    "create_interpreter",
    "MergerConfig",
    "HybridMerger",
    "compute_overall_confidence",
    "get_elements_needing_review",
    "LegacyGeminiVisionClient",
    "create_legacy_gemini_client",
    # =========================================================================
    # Exceptions
    # =========================================================================
    "VisionError",
    "YoloError",
    "YoloDetectionTimeoutError",
    "YoloLowConfidenceError",
    "YoloNoDetectionsError",
    "ClaudeError",
    "ClaudeAPIError",
    "ClaudeTimeoutError",
    "GeminiError",
    "GeminiTimeoutError",
    "FallbackChainExhaustedError",
]

"""
Threshold Configuration Schema for Math Image Parsing Pipeline v2.0.

Implements 3-Layer Dynamic Threshold Architecture:
- Layer 1: Base thresholds (risk-weighted per element type)
- Layer 2: Context modifiers (image quality, complexity, density)
- Layer 3: Feedback loop (FN/FP rate adjustments)

Schema Version: 2.0.0
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import Field, field_validator, model_validator

from .common import MathpixBaseModel, RiskLevel, ReviewSeverity


# =============================================================================
# Enums
# =============================================================================

class ComplexityLevel(str, Enum):
    """Problem complexity levels for context modification."""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    ADVANCED = "advanced"


class HardRuleAction(str, Enum):
    """Actions for hard rules that override thresholds."""
    ALWAYS_REVIEW = "ALWAYS_REVIEW"
    HALT_PIPELINE = "HALT_PIPELINE"


# =============================================================================
# Sub-Models
# =============================================================================

class GlobalSettings(MathpixBaseModel):
    """Global threshold settings."""
    min_threshold: float = Field(0.15, ge=0.0, le=1.0)
    max_threshold: float = Field(0.90, ge=0.0, le=1.0)
    learning_rate: float = Field(0.08, ge=0.0, le=1.0)
    feedback_window_size: int = Field(100, ge=10, le=1000)

    @model_validator(mode="after")
    def validate_threshold_range(self) -> "GlobalSettings":
        """Ensure min < max threshold."""
        if self.min_threshold >= self.max_threshold:
            raise ValueError(
                f"min_threshold ({self.min_threshold}) must be < "
                f"max_threshold ({self.max_threshold})"
            )
        return self


class FeedbackTargets(MathpixBaseModel):
    """Target rates for feedback loop."""
    false_negative_rate: float = Field(0.05, ge=0.0, le=1.0)
    false_positive_rate: float = Field(0.30, ge=0.0, le=1.0)


class ElementThreshold(MathpixBaseModel):
    """Threshold configuration for a single element type."""
    base: float = Field(..., ge=0.15, le=0.90, description="Base threshold value")
    risk: RiskLevel = Field(..., description="Risk classification")
    default_severity: ReviewSeverity = Field(..., description="Default review severity")


class ImageQualityModifier(MathpixBaseModel):
    """Image quality context modifier configuration."""
    formula: str = Field(default="0.85 + (quality_score * 0.15)")
    min_quality_score: float = Field(0.0, ge=0.0, le=1.0)
    max_quality_score: float = Field(1.0, ge=0.0, le=1.0)


class ComplexityModifiers(MathpixBaseModel):
    """Complexity-based threshold modifiers."""
    elementary: float = Field(1.05, ge=0.5, le=2.0)
    middle_school: float = Field(1.00, ge=0.5, le=2.0)
    high_school: float = Field(0.95, ge=0.5, le=2.0)
    advanced: float = Field(0.90, ge=0.5, le=2.0)

    def get_modifier(self, level: ComplexityLevel) -> float:
        """Get modifier for a complexity level."""
        return getattr(self, level.value)


class ElementDensityModifier(MathpixBaseModel):
    """Element density context modifier configuration."""
    formula: str = Field(default="1.0 - (min(element_count, 10) * 0.01)")
    max_elements: int = Field(10, ge=1, le=100)


class ContextModifiers(MathpixBaseModel):
    """All context modifiers for Layer 2."""
    image_quality: ImageQualityModifier = Field(default_factory=ImageQualityModifier)
    complexity: ComplexityModifiers = Field(default_factory=ComplexityModifiers)
    element_density: ElementDensityModifier = Field(default_factory=ElementDensityModifier)


class FeedbackLoop(MathpixBaseModel):
    """Feedback loop configuration for Layer 3."""
    fn_rate_trigger: float = Field(0.05, ge=0.0, le=1.0)
    fn_adjustment: float = Field(-0.08, ge=-1.0, le=0.0)
    fp_rate_trigger: float = Field(0.30, ge=0.0, le=1.0)
    fp_adjustment: float = Field(0.04, ge=0.0, le=1.0)


class HardRule(MathpixBaseModel):
    """Hard rule that overrides threshold-based decisions."""
    condition: str = Field(..., description="Condition expression")
    action: HardRuleAction = Field(..., description="Action to take")
    severity: ReviewSeverity = Field(..., description="Severity when triggered")


class MonitoringThreshold(MathpixBaseModel):
    """Monitoring threshold with warning and critical levels."""
    target: float = Field(..., description="Target value")
    warning: float = Field(..., description="Warning threshold")
    critical: float = Field(..., description="Critical threshold")


class MonitoringConfig(MathpixBaseModel):
    """Monitoring configuration for threshold drift detection."""
    false_negative_rate: MonitoringThreshold
    false_positive_rate: MonitoringThreshold
    review_queue_depth: MonitoringThreshold
    confidence_drift_kl: MonitoringThreshold


class CalibrationSchedule(MathpixBaseModel):
    """Schedule for threshold recalibration."""
    initial: str = Field(default="Golden Dataset sweep")
    weekly: str = Field(default="Reviewer feedback analysis")
    monthly: str = Field(default="Drift detection (>5% triggers recalibration)")
    quarterly: str = Field(default="Full recalibration + operating point review")


# =============================================================================
# Main Configuration Model
# =============================================================================

class ThresholdConfig(MathpixBaseModel):
    """Complete threshold calibration configuration.

    Implements 3-Layer Dynamic Threshold Architecture:
    - Layer 1: element_thresholds (base values)
    - Layer 2: context_modifiers (quality, complexity, density)
    - Layer 3: feedback_loop (FN/FP rate adjustments)
    """
    version: str = Field(default="2.0.0")
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    targets: FeedbackTargets = Field(default_factory=FeedbackTargets)
    element_thresholds: Dict[str, ElementThreshold] = Field(default_factory=dict)
    context_modifiers: ContextModifiers = Field(default_factory=ContextModifiers)
    feedback_loop: FeedbackLoop = Field(default_factory=FeedbackLoop)
    hard_rules: List[HardRule] = Field(default_factory=list)
    monitoring: Optional[MonitoringConfig] = Field(default=None)
    calibration_schedule: Optional[CalibrationSchedule] = Field(default=None)

    @classmethod
    def from_yaml(cls, path: Path) -> "ThresholdConfig":
        """Load configuration from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)

    def get_base_threshold(self, element_type: str) -> float:
        """Get base threshold for an element type."""
        if element_type not in self.element_thresholds:
            raise KeyError(f"Unknown element type: {element_type}")
        return self.element_thresholds[element_type].base

    def get_risk_level(self, element_type: str) -> RiskLevel:
        """Get risk level for an element type."""
        if element_type not in self.element_thresholds:
            raise KeyError(f"Unknown element type: {element_type}")
        return self.element_thresholds[element_type].risk


# =============================================================================
# Threshold Computation
# =============================================================================

class ThresholdContext(MathpixBaseModel):
    """Context information for dynamic threshold computation."""
    image_quality_score: float = Field(1.0, ge=0.0, le=1.0)
    problem_level: ComplexityLevel = Field(default=ComplexityLevel.MIDDLE_SCHOOL)
    element_count: int = Field(0, ge=0)


class FeedbackStats(MathpixBaseModel):
    """Feedback statistics from recent reviews."""
    false_negative_rate: float = Field(0.0, ge=0.0, le=1.0)
    false_positive_rate: float = Field(0.0, ge=0.0, le=1.0)
    sample_size: int = Field(0, ge=0)


def compute_effective_threshold(
    element_type: str,
    context: ThresholdContext,
    feedback_stats: FeedbackStats,
    config: ThresholdConfig,
) -> float:
    """Compute effective threshold using 3-layer architecture.

    Layer 1: Base threshold from config
    Layer 2: Context modifiers (quality, complexity, density)
    Layer 3: Feedback loop adjustments

    Args:
        element_type: Type of element (equation, curves, bbox, etc.)
        context: Current processing context
        feedback_stats: Recent feedback statistics
        config: Threshold configuration

    Returns:
        Effective threshold value clamped to [min, max]
    """
    # Layer 1: Base threshold
    base = config.get_base_threshold(element_type)

    # Layer 2: Context modifiers
    quality_mod = 0.85 + (context.image_quality_score * 0.15)
    complexity_mod = config.context_modifiers.complexity.get_modifier(context.problem_level)
    density_mod = 1.0 - (min(context.element_count, 10) * 0.01)
    context_modifier = quality_mod * complexity_mod * density_mod

    # Layer 3: Feedback loop
    fn_rate = feedback_stats.false_negative_rate
    fp_rate = feedback_stats.false_positive_rate

    if fn_rate > config.feedback_loop.fn_rate_trigger:
        feedback_mod = 1.0 + ((fn_rate - config.feedback_loop.fn_rate_trigger) *
                              config.feedback_loop.fn_adjustment)
    elif fp_rate > config.feedback_loop.fp_rate_trigger:
        feedback_mod = 1.0 + ((fp_rate - config.feedback_loop.fp_rate_trigger) *
                              config.feedback_loop.fp_adjustment)
    else:
        feedback_mod = 1.0

    # Compute effective and clamp
    effective = base * context_modifier * feedback_mod
    return max(config.global_settings.min_threshold,
               min(config.global_settings.max_threshold, effective))


# =============================================================================
# Export
# =============================================================================

__all__ = [
    # Enums
    "ComplexityLevel",
    "HardRuleAction",
    # Config Models
    "GlobalSettings",
    "FeedbackTargets",
    "ElementThreshold",
    "ContextModifiers",
    "FeedbackLoop",
    "HardRule",
    "MonitoringConfig",
    "CalibrationSchedule",
    "ThresholdConfig",
    # Runtime Models
    "ThresholdContext",
    "FeedbackStats",
    # Functions
    "compute_effective_threshold",
]

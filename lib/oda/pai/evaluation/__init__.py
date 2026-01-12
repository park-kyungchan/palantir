"""
Orion ODA PAI - Evaluation Module
=================================
Quality metrics and validation framework for AIP Logic blocks and pipelines.
Version: 1.0.0
"""

from lib.oda.pai.evaluation.metrics import (
    MetricType,
    MetricCategory,
    AggregationType,
    QualityMetric,
    MetricResult,
    EvaluationReport,
    MetricsCollector,
    aggregate_values,
)

from lib.oda.pai.evaluation.validators import (
    ValidationResult,
    BlockValidator,
    ContentLengthValidator,
    SyntaxValidator,
    FormatValidator,
    EncodingValidator,
    ValidatorRegistry,
)

__all__ = [
    # Enums
    "MetricType",
    "MetricCategory",
    "AggregationType",
    # Metrics ObjectTypes
    "QualityMetric",
    "MetricResult",
    # Evaluation Report
    "EvaluationReport",
    # Metrics Collector
    "MetricsCollector",
    # Validation Result
    "ValidationResult",
    # Validator Protocol
    "BlockValidator",
    # Concrete Validators
    "ContentLengthValidator",
    "SyntaxValidator",
    "FormatValidator",
    "EncodingValidator",
    # Validator Registry
    "ValidatorRegistry",
    # Utilities
    "aggregate_values",
]

__version__ = "1.0.0"

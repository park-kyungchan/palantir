"""
ODA PAI Evaluation - Quality Metrics
====================================

Defines quality metrics and evaluation framework for AIP Logic blocks and pipelines.

This module provides:
- MetricType: Types of metrics (count, ratio, score, boolean, duration)
- MetricCategory: Categories for organizing metrics
- AggregationType: How to aggregate multiple metric values
- QualityMetric: Definition of a single metric
- MetricResult: Result of evaluating a metric
- EvaluationReport: Complete evaluation report
- MetricsCollector: Collector and evaluator for metrics

ObjectTypes:
    - QualityMetric: Metric definition (registered with Ontology)
    - MetricResult: Individual metric evaluation result (registered with Ontology)

Usage:
    ```python
    from lib.oda.pai.evaluation import (
        MetricType,
        MetricCategory,
        QualityMetric,
        MetricsCollector,
    )

    # Create a collector with default metrics
    collector = MetricsCollector()
    for metric in MetricsCollector.default_metrics():
        collector.register_metric(metric)

    # Evaluate a block
    results = collector.evaluate_block("block-123")

    # Generate report
    report = collector.generate_report("block-123", "block")
    print(f"Overall score: {report.overall_score}")
    ```

Version: 1.0.0
"""

from __future__ import annotations

import statistics
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, ClassVar
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject, utc_now
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================


class MetricType(str, Enum):
    """
    Type classification for quality metrics.

    - COUNT: Absolute numeric count (e.g., line count, token count)
    - RATIO: Normalized value between 0 and 1 (e.g., coverage ratio)
    - SCORE: Arbitrary numeric score (e.g., complexity score)
    - BOOLEAN: Pass/fail indicator (0 or 1)
    - DURATION: Time measurement in milliseconds
    """

    COUNT = "count"
    RATIO = "ratio"
    SCORE = "score"
    BOOLEAN = "boolean"
    DURATION = "duration"


class MetricCategory(str, Enum):
    """
    Category classification for organizing metrics.

    - CONTENT: Related to content quality (clarity, completeness)
    - STRUCTURE: Related to code/document structure
    - PERFORMANCE: Related to execution performance
    - COMPLIANCE: Related to standards compliance
    - SECURITY: Related to security concerns
    """

    CONTENT = "content"
    STRUCTURE = "structure"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    SECURITY = "security"


class AggregationType(str, Enum):
    """
    Aggregation method for combining multiple metric values.

    - AVERAGE: Arithmetic mean
    - SUM: Total sum
    - MIN: Minimum value
    - MAX: Maximum value
    - MEDIAN: Median value
    """

    AVERAGE = "average"
    SUM = "sum"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"


# =============================================================================
# OBJECT TYPES
# =============================================================================


@register_object_type
class QualityMetric(OntologyObject):
    """
    Definition of a quality metric for evaluation.

    A QualityMetric defines what to measure and how to interpret the results.
    Metrics can have target values, min/max bounds, and weights for aggregation.

    Attributes:
        metric_id: Unique identifier for this metric definition
        name: Human-readable name of the metric
        description: Detailed description of what this metric measures
        metric_type: Type of metric (count, ratio, score, boolean, duration)
        category: Category for organizing metrics
        min_value: Minimum acceptable value (optional)
        max_value: Maximum acceptable value (optional)
        target_value: Ideal target value (optional)
        weight: Weight for aggregation (0.0-10.0, default 1.0)
        aggregation: How to aggregate multiple values
        is_required: Whether this metric must pass for overall success
    """

    metric_id: str = Field(
        default_factory=lambda: f"metric_{uuid4().hex[:8]}",
        description="Unique identifier for this metric definition"
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable name of the metric"
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="Detailed description of what this metric measures"
    )
    metric_type: MetricType = Field(
        ...,
        description="Type of metric (count, ratio, score, boolean, duration)"
    )
    category: MetricCategory = Field(
        ...,
        description="Category for organizing metrics"
    )
    min_value: Optional[float] = Field(
        default=None,
        description="Minimum acceptable value"
    )
    max_value: Optional[float] = Field(
        default=None,
        description="Maximum acceptable value"
    )
    target_value: Optional[float] = Field(
        default=None,
        description="Ideal target value"
    )
    weight: float = Field(
        default=1.0,
        ge=0.0,
        le=10.0,
        description="Weight for aggregation (0.0-10.0)"
    )
    aggregation: AggregationType = Field(
        default=AggregationType.AVERAGE,
        description="How to aggregate multiple values"
    )
    is_required: bool = Field(
        default=False,
        description="Whether this metric must pass for overall success"
    )

    @field_validator("min_value", "max_value")
    @classmethod
    def validate_bounds(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure min_value <= max_value if both are set."""
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that min_value <= max_value after initialization."""
        if self.min_value is not None and self.max_value is not None:
            if self.min_value > self.max_value:
                raise ValueError(
                    f"min_value ({self.min_value}) must be <= max_value ({self.max_value})"
                )

    def is_passing(self, value: float) -> bool:
        """
        Check if a value passes this metric's criteria.

        A value passes if:
        - It is >= min_value (if min_value is set)
        - It is <= max_value (if max_value is set)
        - For BOOLEAN metrics: value >= 0.5 is considered True/passing

        Args:
            value: The metric value to check

        Returns:
            True if the value passes, False otherwise
        """
        # Boolean metrics: 0 = fail, 1 = pass
        if self.metric_type == MetricType.BOOLEAN:
            return value >= 0.5

        # Check bounds
        if self.min_value is not None and value < self.min_value:
            return False
        if self.max_value is not None and value > self.max_value:
            return False

        return True

    def distance_from_target(self, value: float) -> Optional[float]:
        """
        Calculate distance from target value.

        Args:
            value: The measured value

        Returns:
            Absolute distance from target, or None if no target is set
        """
        if self.target_value is None:
            return None
        return abs(value - self.target_value)


@register_object_type
class MetricResult(OntologyObject):
    """
    Result of evaluating a single metric for a specific block.

    Attributes:
        metric_id: ID of the QualityMetric that was evaluated
        block_id: ID of the block that was evaluated
        value: The measured metric value
        passing: Whether the value passes the metric criteria
        evidence: Supporting evidence for the measurement
        evaluated_at: Timestamp of evaluation
        duration_ms: Time taken to evaluate (milliseconds)
    """

    metric_id: str = Field(
        ...,
        description="ID of the QualityMetric that was evaluated"
    )
    block_id: str = Field(
        ...,
        description="ID of the block that was evaluated"
    )
    value: float = Field(
        ...,
        description="The measured metric value"
    )
    passing: bool = Field(
        default=True,
        description="Whether the value passes the metric criteria"
    )
    evidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Supporting evidence for the measurement"
    )
    evaluated_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of evaluation"
    )
    duration_ms: int = Field(
        default=0,
        ge=0,
        description="Time taken to evaluate (milliseconds)"
    )

    @property
    def is_failure(self) -> bool:
        """Check if this result represents a failure."""
        return not self.passing


# =============================================================================
# EVALUATION REPORT (NOT AN ONTOLOGY OBJECT)
# =============================================================================


class EvaluationReport(BaseModel):
    """
    Complete evaluation report for a block or pipeline.

    This is a value object (not an OntologyObject) used for presenting
    evaluation results.

    Attributes:
        report_id: Unique identifier for this report
        evaluated_at: Timestamp of evaluation
        target_type: Type of target ("block" or "pipeline")
        target_id: ID of the evaluated target
        results: List of individual metric results
        overall_score: Weighted overall score (0-100)
        passing: Whether all required metrics pass
        summary: Aggregated summary statistics
    """

    report_id: str = Field(
        default_factory=lambda: f"report_{uuid4().hex[:12]}",
        description="Unique identifier for this report"
    )
    evaluated_at: datetime = Field(
        default_factory=utc_now,
        description="Timestamp of evaluation"
    )
    target_type: str = Field(
        ...,
        description="Type of target ('block' or 'pipeline')"
    )
    target_id: str = Field(
        ...,
        description="ID of the evaluated target"
    )
    results: List[MetricResult] = Field(
        default_factory=list,
        description="List of individual metric results"
    )
    overall_score: float = Field(
        default=0.0,
        ge=0.0,
        le=100.0,
        description="Weighted overall score (0-100)"
    )
    passing: bool = Field(
        default=True,
        description="Whether all required metrics pass"
    )
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregated summary statistics"
    )

    @property
    def total_metrics(self) -> int:
        """Total number of metrics evaluated."""
        return len(self.results)

    @property
    def passed_metrics(self) -> int:
        """Number of metrics that passed."""
        return sum(1 for r in self.results if r.passing)

    @property
    def failed_metrics(self) -> int:
        """Number of metrics that failed."""
        return sum(1 for r in self.results if not r.passing)

    @property
    def pass_rate(self) -> float:
        """Percentage of metrics that passed (0-100)."""
        if not self.results:
            return 100.0
        return (self.passed_metrics / self.total_metrics) * 100.0

    def to_summary_dict(self) -> Dict[str, Any]:
        """Generate a summary dictionary for display."""
        return {
            "report_id": self.report_id,
            "target": f"{self.target_type}:{self.target_id}",
            "evaluated_at": self.evaluated_at.isoformat(),
            "overall_score": round(self.overall_score, 2),
            "passing": self.passing,
            "metrics": {
                "total": self.total_metrics,
                "passed": self.passed_metrics,
                "failed": self.failed_metrics,
                "pass_rate": f"{self.pass_rate:.1f}%",
            },
        }


# =============================================================================
# METRICS COLLECTOR
# =============================================================================


class MetricsCollector:
    """
    Collector and evaluator for quality metrics.

    The MetricsCollector manages metric definitions, evaluates blocks,
    and generates evaluation reports.

    Attributes:
        _metrics: Dictionary of registered QualityMetric by metric_id
        _results: List of collected MetricResult objects
        _evaluators: Dictionary of custom evaluator functions

    Usage:
        ```python
        collector = MetricsCollector()

        # Register metrics
        for metric in MetricsCollector.default_metrics():
            collector.register_metric(metric)

        # Add custom evaluator
        collector.register_evaluator("content_length", custom_length_evaluator)

        # Evaluate
        results = collector.evaluate_block("block-123")
        report = collector.generate_report("block-123", "block")
        ```
    """

    def __init__(self) -> None:
        """Initialize an empty MetricsCollector."""
        self._metrics: Dict[str, QualityMetric] = {}
        self._results: List[MetricResult] = []
        self._evaluators: Dict[str, Callable[[str], float]] = {}

    def register_metric(self, metric: QualityMetric) -> None:
        """
        Register a metric definition.

        Args:
            metric: The QualityMetric to register

        Raises:
            ValueError: If a metric with the same metric_id already exists
        """
        if metric.metric_id in self._metrics:
            raise ValueError(f"Metric already registered: {metric.metric_id}")
        self._metrics[metric.metric_id] = metric

    def unregister_metric(self, metric_id: str) -> bool:
        """
        Unregister a metric by ID.

        Args:
            metric_id: The metric ID to unregister

        Returns:
            True if the metric was removed, False if it didn't exist
        """
        if metric_id in self._metrics:
            del self._metrics[metric_id]
            return True
        return False

    def get_metric(self, metric_id: str) -> Optional[QualityMetric]:
        """
        Get a registered metric by ID.

        Args:
            metric_id: The metric ID to look up

        Returns:
            The QualityMetric if found, None otherwise
        """
        return self._metrics.get(metric_id)

    def list_metrics(self) -> List[QualityMetric]:
        """
        List all registered metrics.

        Returns:
            List of all registered QualityMetric objects
        """
        return list(self._metrics.values())

    def register_evaluator(
        self,
        metric_id: str,
        evaluator: Callable[[str], float]
    ) -> None:
        """
        Register a custom evaluator function for a metric.

        Args:
            metric_id: The metric ID this evaluator handles
            evaluator: Function that takes block_id and returns a float value
        """
        self._evaluators[metric_id] = evaluator

    def evaluate_block(
        self,
        block_id: str,
        metrics: Optional[List[str]] = None
    ) -> List[MetricResult]:
        """
        Evaluate a block against registered metrics.

        Args:
            block_id: The ID of the block to evaluate
            metrics: Optional list of metric_ids to evaluate.
                     If None, evaluates all registered metrics.

        Returns:
            List of MetricResult objects
        """
        import time

        results: List[MetricResult] = []
        metric_ids = metrics if metrics else list(self._metrics.keys())

        for metric_id in metric_ids:
            metric = self._metrics.get(metric_id)
            if not metric:
                continue

            start_time = time.time()

            # Get value from evaluator or use default
            if metric_id in self._evaluators:
                try:
                    value = self._evaluators[metric_id](block_id)
                except Exception as e:
                    # On error, use a failing value
                    value = 0.0 if metric.min_value is None else metric.min_value - 1
            else:
                # Default evaluation based on metric type
                value = self._default_evaluate(metric, block_id)

            duration_ms = int((time.time() - start_time) * 1000)

            result = MetricResult(
                metric_id=metric_id,
                block_id=block_id,
                value=value,
                passing=metric.is_passing(value),
                evidence={
                    "metric_name": metric.name,
                    "metric_type": metric.metric_type.value,
                    "target_value": metric.target_value,
                    "min_value": metric.min_value,
                    "max_value": metric.max_value,
                },
                duration_ms=duration_ms,
            )
            results.append(result)
            self._results.append(result)

        return results

    def _default_evaluate(self, metric: QualityMetric, block_id: str) -> float:
        """
        Default evaluation when no custom evaluator is registered.

        Args:
            metric: The metric to evaluate
            block_id: The block ID

        Returns:
            A default value based on metric type
        """
        # Default values based on metric type
        defaults = {
            MetricType.BOOLEAN: 1.0,  # Pass by default
            MetricType.RATIO: 1.0,    # 100% by default
            MetricType.SCORE: metric.target_value or 0.0,
            MetricType.COUNT: 0.0,
            MetricType.DURATION: 0.0,
        }
        return defaults.get(metric.metric_type, 0.0)

    def generate_report(
        self,
        target_id: str,
        target_type: str = "block"
    ) -> EvaluationReport:
        """
        Generate an evaluation report for a target.

        Args:
            target_id: The ID of the evaluated target
            target_type: Type of target ("block" or "pipeline")

        Returns:
            EvaluationReport with aggregated results
        """
        # Filter results for this target
        target_results = [
            r for r in self._results
            if r.block_id == target_id
        ]

        # Calculate overall score (weighted average)
        overall_score = self._calculate_overall_score(target_results)

        # Check if all required metrics pass
        passing = self._check_required_metrics(target_results)

        # Build summary
        summary = self._build_summary(target_results)

        return EvaluationReport(
            target_type=target_type,
            target_id=target_id,
            results=target_results,
            overall_score=overall_score,
            passing=passing,
            summary=summary,
        )

    def _calculate_overall_score(self, results: List[MetricResult]) -> float:
        """
        Calculate weighted overall score.

        Args:
            results: List of metric results

        Returns:
            Weighted score normalized to 0-100
        """
        if not results:
            return 100.0

        total_weight = 0.0
        weighted_sum = 0.0

        for result in results:
            metric = self._metrics.get(result.metric_id)
            if not metric:
                continue

            weight = metric.weight

            # Normalize value to 0-1 for scoring
            if metric.metric_type == MetricType.BOOLEAN:
                normalized = 1.0 if result.passing else 0.0
            elif metric.metric_type == MetricType.RATIO:
                normalized = max(0.0, min(1.0, result.value))
            else:
                # For other types, use pass/fail
                normalized = 1.0 if result.passing else 0.0

            weighted_sum += normalized * weight
            total_weight += weight

        if total_weight == 0:
            return 100.0

        return (weighted_sum / total_weight) * 100.0

    def _check_required_metrics(self, results: List[MetricResult]) -> bool:
        """
        Check if all required metrics pass.

        Args:
            results: List of metric results

        Returns:
            True if all required metrics pass
        """
        for result in results:
            metric = self._metrics.get(result.metric_id)
            if metric and metric.is_required and not result.passing:
                return False
        return True

    def _build_summary(self, results: List[MetricResult]) -> Dict[str, Any]:
        """
        Build summary statistics from results.

        Args:
            results: List of metric results

        Returns:
            Dictionary of summary statistics
        """
        if not results:
            return {"message": "No results to summarize"}

        # Group by category
        by_category: Dict[str, List[MetricResult]] = {}
        for result in results:
            metric = self._metrics.get(result.metric_id)
            if metric:
                category = metric.category.value
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(result)

        # Calculate category stats
        category_stats: Dict[str, Dict[str, Any]] = {}
        for category, cat_results in by_category.items():
            passed = sum(1 for r in cat_results if r.passing)
            total = len(cat_results)
            category_stats[category] = {
                "passed": passed,
                "total": total,
                "pass_rate": f"{(passed / total * 100):.1f}%" if total > 0 else "N/A",
            }

        # Aggregate values
        values = [r.value for r in results]

        return {
            "total_metrics": len(results),
            "passed": sum(1 for r in results if r.passing),
            "failed": sum(1 for r in results if not r.passing),
            "by_category": category_stats,
            "value_stats": {
                "min": min(values) if values else 0,
                "max": max(values) if values else 0,
                "mean": statistics.mean(values) if values else 0,
                "median": statistics.median(values) if len(values) > 0 else 0,
            },
            "total_duration_ms": sum(r.duration_ms for r in results),
        }

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all collected results.

        Returns:
            Dictionary with overall statistics
        """
        return {
            "registered_metrics": len(self._metrics),
            "total_results": len(self._results),
            "unique_blocks": len(set(r.block_id for r in self._results)),
            "overall_pass_rate": self._calculate_pass_rate(),
        }

    def _calculate_pass_rate(self) -> float:
        """Calculate overall pass rate across all results."""
        if not self._results:
            return 100.0
        passed = sum(1 for r in self._results if r.passing)
        return (passed / len(self._results)) * 100.0

    def clear_results(self) -> None:
        """Clear all collected results."""
        self._results = []

    @staticmethod
    def default_metrics() -> List[QualityMetric]:
        """
        Get a list of default quality metrics.

        Returns:
            List of commonly used QualityMetric objects
        """
        return [
            # Content metrics
            QualityMetric(
                metric_id="content_length",
                name="Content Length",
                description="Length of content in characters",
                metric_type=MetricType.COUNT,
                category=MetricCategory.CONTENT,
                min_value=1,
                max_value=100000,
                weight=1.0,
            ),
            QualityMetric(
                metric_id="content_completeness",
                name="Content Completeness",
                description="Ratio of complete vs expected content",
                metric_type=MetricType.RATIO,
                category=MetricCategory.CONTENT,
                min_value=0.8,
                target_value=1.0,
                weight=2.0,
                is_required=True,
            ),

            # Structure metrics
            QualityMetric(
                metric_id="syntax_valid",
                name="Syntax Valid",
                description="Whether the syntax is valid",
                metric_type=MetricType.BOOLEAN,
                category=MetricCategory.STRUCTURE,
                weight=3.0,
                is_required=True,
            ),
            QualityMetric(
                metric_id="structure_score",
                name="Structure Score",
                description="Quality score for structural organization",
                metric_type=MetricType.SCORE,
                category=MetricCategory.STRUCTURE,
                min_value=0,
                max_value=100,
                target_value=80,
                weight=1.5,
            ),

            # Performance metrics
            QualityMetric(
                metric_id="execution_time",
                name="Execution Time",
                description="Time to execute in milliseconds",
                metric_type=MetricType.DURATION,
                category=MetricCategory.PERFORMANCE,
                max_value=10000,
                weight=1.0,
            ),
            QualityMetric(
                metric_id="memory_efficiency",
                name="Memory Efficiency",
                description="Memory usage efficiency ratio",
                metric_type=MetricType.RATIO,
                category=MetricCategory.PERFORMANCE,
                min_value=0.5,
                target_value=0.9,
                weight=1.0,
            ),

            # Compliance metrics
            QualityMetric(
                metric_id="format_compliant",
                name="Format Compliant",
                description="Whether output matches expected format",
                metric_type=MetricType.BOOLEAN,
                category=MetricCategory.COMPLIANCE,
                weight=2.0,
                is_required=True,
            ),
            QualityMetric(
                metric_id="encoding_valid",
                name="Encoding Valid",
                description="Whether encoding is valid UTF-8",
                metric_type=MetricType.BOOLEAN,
                category=MetricCategory.COMPLIANCE,
                weight=1.0,
            ),

            # Security metrics
            QualityMetric(
                metric_id="no_sensitive_data",
                name="No Sensitive Data",
                description="Content does not contain sensitive data",
                metric_type=MetricType.BOOLEAN,
                category=MetricCategory.SECURITY,
                weight=5.0,
                is_required=True,
            ),
            QualityMetric(
                metric_id="input_sanitized",
                name="Input Sanitized",
                description="All inputs are properly sanitized",
                metric_type=MetricType.BOOLEAN,
                category=MetricCategory.SECURITY,
                weight=3.0,
            ),
        ]


# =============================================================================
# AGGREGATION UTILITIES
# =============================================================================


def aggregate_values(
    values: List[float],
    aggregation: AggregationType
) -> float:
    """
    Aggregate a list of values using the specified method.

    Args:
        values: List of numeric values
        aggregation: Aggregation method to use

    Returns:
        Aggregated value
    """
    if not values:
        return 0.0

    if aggregation == AggregationType.AVERAGE:
        return statistics.mean(values)
    elif aggregation == AggregationType.SUM:
        return sum(values)
    elif aggregation == AggregationType.MIN:
        return min(values)
    elif aggregation == AggregationType.MAX:
        return max(values)
    elif aggregation == AggregationType.MEDIAN:
        return statistics.median(values)
    else:
        return statistics.mean(values)

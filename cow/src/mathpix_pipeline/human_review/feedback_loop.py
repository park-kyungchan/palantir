"""
FeedbackLoopManager for Human Review system.

Manages the feedback loop for model improvement:
- Recording corrections for training
- Generating training datasets
- Error pattern analysis

Module Version: 1.0.0
"""

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import Field

from ..schemas.common import MathpixBaseModel, PipelineStage

from .models.annotation import Annotation, Correction, CorrectionType
from .models.task import ReviewTask, ReviewDecision
from .exceptions import FeedbackLoopError


logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class FeedbackLoopConfig:
    """Configuration for FeedbackLoopManager."""
    # Training data settings
    min_corrections_for_pattern: int = 3
    min_confidence_for_positive: float = 0.90

    # Analysis settings
    pattern_analysis_window_days: int = 30
    top_patterns_count: int = 20

    # Data retention
    max_corrections_stored: int = 100000
    archive_after_days: int = 90


# =============================================================================
# Data Models
# =============================================================================

class DateRange(MathpixBaseModel):
    """Date range for filtering."""
    start: datetime
    end: datetime


class CorrectionRecord(MathpixBaseModel):
    """Record of a correction for training data."""
    record_id: str
    task_id: str
    image_id: str
    pipeline_stage: PipelineStage
    element_type: str
    element_id: str

    # Original values
    original_content: Any
    original_confidence: float

    # Corrected values
    corrected_content: Any
    correction_type: CorrectionType
    correction_reason: Optional[str]

    # Metadata
    reviewer_id: str
    review_decision: ReviewDecision
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Training flags
    flagged_for_training: bool = False
    flagged_as_edge_case: bool = False


class TrainingDataset(MathpixBaseModel):
    """Dataset for model training."""
    dataset_id: str
    date_range: DateRange
    total_records: int

    # Positive examples (corrections)
    positive_examples: List[CorrectionRecord] = Field(default_factory=list)

    # Negative examples (approved without correction)
    negative_examples: List[Dict[str, Any]] = Field(default_factory=list)

    # Statistics
    by_pipeline_stage: Dict[str, int] = Field(default_factory=dict)
    by_element_type: Dict[str, int] = Field(default_factory=dict)
    by_correction_type: Dict[str, int] = Field(default_factory=dict)

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorPattern(MathpixBaseModel):
    """Pattern identified in errors."""
    pattern_id: str
    pattern_type: str
    description: str
    occurrence_count: int

    # Pattern details
    affected_stages: List[PipelineStage] = Field(default_factory=list)
    affected_element_types: List[str] = Field(default_factory=list)

    # Example records
    example_record_ids: List[str] = Field(default_factory=list)

    # Confidence
    avg_original_confidence: float = 0.0
    confidence_range: Tuple[float, float] = (0.0, 1.0)

    # Recommendations
    recommended_action: Optional[str] = None


class ErrorPatternReport(MathpixBaseModel):
    """Report of error patterns."""
    report_id: str
    date_range: DateRange
    total_corrections: int
    patterns: List[ErrorPattern] = Field(default_factory=list)

    # Summary statistics
    most_common_correction_types: List[Tuple[str, int]] = Field(default_factory=list)
    most_affected_stages: List[Tuple[str, int]] = Field(default_factory=list)
    most_affected_element_types: List[Tuple[str, int]] = Field(default_factory=list)

    # Trends
    correction_rate_trend: Optional[str] = None  # "increasing", "decreasing", "stable"

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# =============================================================================
# FeedbackLoopManager
# =============================================================================

class FeedbackLoopManager:
    """Manages the feedback loop for model improvement.

    Collects corrections from human review and:
    - Records them for training data generation
    - Analyzes patterns in errors
    - Provides insights for model improvement

    Usage:
        manager = FeedbackLoopManager()

        # Record a correction
        await manager.record_correction(
            original=original_data,
            corrected=corrected_data,
            reason="Text was misread"
        )

        # Generate training data
        dataset = await manager.generate_training_data(
            DateRange(start=..., end=...)
        )

        # Analyze patterns
        report = await manager.analyze_error_patterns()
    """

    def __init__(
        self,
        config: Optional[FeedbackLoopConfig] = None,
    ):
        """Initialize manager.

        Args:
            config: Feedback loop configuration
        """
        self.config = config or FeedbackLoopConfig()

        # In-memory storage (for demo; use proper DB in production)
        self._corrections: Dict[str, CorrectionRecord] = {}
        self._approved_without_correction: List[Dict[str, Any]] = []

        # Pattern analysis cache
        self._pattern_cache: Optional[ErrorPatternReport] = None
        self._pattern_cache_time: Optional[datetime] = None

        logger.info("FeedbackLoopManager initialized")

    # =========================================================================
    # Recording Corrections
    # =========================================================================

    async def record_correction(
        self,
        task: ReviewTask,
        annotation: Annotation,
        correction: Correction,
        review_decision: ReviewDecision,
    ) -> str:
        """Record a correction for training data.

        Args:
            task: The review task
            annotation: The annotation containing the correction
            correction: The specific correction
            review_decision: Final review decision

        Returns:
            Record ID
        """
        record_id = f"corr-{len(self._corrections):08d}"

        record = CorrectionRecord(
            record_id=record_id,
            task_id=task.task_id,
            image_id=task.image_id,
            pipeline_stage=task.context.pipeline_stage,
            element_type=task.context.element_type,
            element_id=correction.element_id,
            original_content=correction.original_value,
            original_confidence=task.context.original_confidence,
            corrected_content=correction.corrected_value,
            correction_type=correction.correction_type,
            correction_reason=correction.reason,
            reviewer_id=annotation.reviewer_id,
            review_decision=review_decision,
            flagged_for_training=annotation.flagged_for_training,
            flagged_as_edge_case=annotation.flagged_for_edge_case,
        )

        self._corrections[record_id] = record

        # Enforce max storage
        if len(self._corrections) > self.config.max_corrections_stored:
            # Remove oldest records
            sorted_ids = sorted(
                self._corrections.keys(),
                key=lambda x: self._corrections[x].created_at,
            )
            for old_id in sorted_ids[:100]:  # Remove oldest 100
                del self._corrections[old_id]

        logger.debug(f"Recorded correction {record_id} for task {task.task_id}")

        return record_id

    async def record_approval(
        self,
        task: ReviewTask,
        confidence_at_review: float,
    ) -> None:
        """Record an approval without correction (negative example).

        Args:
            task: The approved task
            confidence_at_review: Model confidence at time of approval
        """
        if confidence_at_review >= self.config.min_confidence_for_positive:
            record = {
                "task_id": task.task_id,
                "image_id": task.image_id,
                "pipeline_stage": task.context.pipeline_stage.value,
                "element_type": task.context.element_type,
                "element_id": task.context.element_id,
                "confidence": confidence_at_review,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            }
            self._approved_without_correction.append(record)

    async def bulk_record_corrections(
        self,
        task: ReviewTask,
        annotation: Annotation,
        review_decision: ReviewDecision,
    ) -> List[str]:
        """Record all corrections from an annotation.

        Args:
            task: The review task
            annotation: Annotation with corrections
            review_decision: Final decision

        Returns:
            List of record IDs
        """
        record_ids = []
        for correction in annotation.corrections:
            record_id = await self.record_correction(
                task=task,
                annotation=annotation,
                correction=correction,
                review_decision=review_decision,
            )
            record_ids.append(record_id)
        return record_ids

    # =========================================================================
    # Training Data Generation
    # =========================================================================

    async def generate_training_data(
        self,
        date_range: DateRange,
        include_edge_cases: bool = True,
        include_negatives: bool = True,
    ) -> TrainingDataset:
        """Generate training dataset from corrections.

        Args:
            date_range: Date range for records
            include_edge_cases: Include edge case records
            include_negatives: Include approved records (negatives)

        Returns:
            TrainingDataset
        """
        import uuid
        dataset_id = f"dataset-{uuid.uuid4().hex[:8]}"

        # Filter corrections by date range
        positive_examples = []
        for record in self._corrections.values():
            if date_range.start <= record.created_at <= date_range.end:
                if not include_edge_cases and record.flagged_as_edge_case:
                    continue
                positive_examples.append(record)

        # Get negative examples
        negative_examples = []
        if include_negatives:
            for record in self._approved_without_correction:
                record_date = datetime.fromisoformat(record["approved_at"])
                if date_range.start <= record_date <= date_range.end:
                    negative_examples.append(record)

        # Calculate statistics
        by_stage: Dict[str, int] = defaultdict(int)
        by_element: Dict[str, int] = defaultdict(int)
        by_correction: Dict[str, int] = defaultdict(int)

        for record in positive_examples:
            by_stage[record.pipeline_stage.value] += 1
            by_element[record.element_type] += 1
            by_correction[record.correction_type.value] += 1

        dataset = TrainingDataset(
            dataset_id=dataset_id,
            date_range=date_range,
            total_records=len(positive_examples) + len(negative_examples),
            positive_examples=positive_examples,
            negative_examples=negative_examples,
            by_pipeline_stage=dict(by_stage),
            by_element_type=dict(by_element),
            by_correction_type=dict(by_correction),
        )

        logger.info(
            f"Generated training dataset {dataset_id}: "
            f"{len(positive_examples)} positives, "
            f"{len(negative_examples)} negatives"
        )

        return dataset

    # =========================================================================
    # Error Pattern Analysis
    # =========================================================================

    async def analyze_error_patterns(
        self,
        date_range: Optional[DateRange] = None,
    ) -> ErrorPatternReport:
        """Analyze error patterns in corrections.

        Args:
            date_range: Optional date range (defaults to last 30 days)

        Returns:
            ErrorPatternReport
        """
        import uuid
        from datetime import timedelta

        # Default date range
        if date_range is None:
            end = datetime.now(timezone.utc)
            start = end - timedelta(days=self.config.pattern_analysis_window_days)
            date_range = DateRange(start=start, end=end)

        # Filter corrections
        corrections = [
            r for r in self._corrections.values()
            if date_range.start <= r.created_at <= date_range.end
        ]

        if not corrections:
            return ErrorPatternReport(
                report_id=f"report-{uuid.uuid4().hex[:8]}",
                date_range=date_range,
                total_corrections=0,
                patterns=[],
            )

        # Analyze patterns
        patterns = self._find_patterns(corrections)

        # Calculate summary statistics
        correction_type_counts = Counter(r.correction_type.value for r in corrections)
        stage_counts = Counter(r.pipeline_stage.value for r in corrections)
        element_counts = Counter(r.element_type for r in corrections)

        report = ErrorPatternReport(
            report_id=f"report-{uuid.uuid4().hex[:8]}",
            date_range=date_range,
            total_corrections=len(corrections),
            patterns=patterns,
            most_common_correction_types=correction_type_counts.most_common(10),
            most_affected_stages=stage_counts.most_common(10),
            most_affected_element_types=element_counts.most_common(10),
        )

        # Cache report
        self._pattern_cache = report
        self._pattern_cache_time = datetime.now(timezone.utc)

        logger.info(
            f"Generated error pattern report: "
            f"{len(corrections)} corrections, "
            f"{len(patterns)} patterns identified"
        )

        return report

    def _find_patterns(
        self,
        corrections: List[CorrectionRecord],
    ) -> List[ErrorPattern]:
        """Find patterns in corrections.

        Groups corrections by various dimensions to identify patterns.
        """
        import uuid
        patterns: List[ErrorPattern] = []

        # Pattern 1: By correction type and element type
        type_combinations: Dict[Tuple[str, str], List[CorrectionRecord]] = defaultdict(list)
        for record in corrections:
            key = (record.correction_type.value, record.element_type)
            type_combinations[key].append(record)

        for (corr_type, elem_type), records in type_combinations.items():
            if len(records) >= self.config.min_corrections_for_pattern:
                confidences = [r.original_confidence for r in records]
                pattern = ErrorPattern(
                    pattern_id=f"pattern-{uuid.uuid4().hex[:8]}",
                    pattern_type="type_element_combination",
                    description=f"{corr_type} corrections on {elem_type} elements",
                    occurrence_count=len(records),
                    affected_stages=list(set(r.pipeline_stage for r in records)),
                    affected_element_types=[elem_type],
                    example_record_ids=[r.record_id for r in records[:3]],
                    avg_original_confidence=sum(confidences) / len(confidences),
                    confidence_range=(min(confidences), max(confidences)),
                    recommended_action=self._get_recommendation(corr_type, elem_type),
                )
                patterns.append(pattern)

        # Pattern 2: By pipeline stage and low confidence
        LOW_CONF_THRESHOLD = 0.40
        for stage in PipelineStage:
            low_conf_records = [
                r for r in corrections
                if r.pipeline_stage == stage
                and r.original_confidence < LOW_CONF_THRESHOLD
            ]
            if len(low_conf_records) >= self.config.min_corrections_for_pattern:
                confidences = [r.original_confidence for r in low_conf_records]
                pattern = ErrorPattern(
                    pattern_id=f"pattern-{uuid.uuid4().hex[:8]}",
                    pattern_type="low_confidence_stage",
                    description=f"Low confidence errors in {stage.value} stage",
                    occurrence_count=len(low_conf_records),
                    affected_stages=[stage],
                    affected_element_types=list(set(r.element_type for r in low_conf_records)),
                    example_record_ids=[r.record_id for r in low_conf_records[:3]],
                    avg_original_confidence=sum(confidences) / len(confidences),
                    confidence_range=(min(confidences), max(confidences)),
                    recommended_action=f"Review threshold settings for {stage.value}",
                )
                patterns.append(pattern)

        # Sort by occurrence count
        patterns.sort(key=lambda p: p.occurrence_count, reverse=True)

        return patterns[:self.config.top_patterns_count]

    def _get_recommendation(
        self,
        correction_type: str,
        element_type: str,
    ) -> str:
        """Get recommendation for a pattern."""
        recommendations = {
            "text_correction": "Improve OCR accuracy or add spell checking",
            "latex_correction": "Enhance LaTeX parsing rules",
            "bbox_adjustment": "Improve detection model or adjust NMS thresholds",
            "confidence_override": "Review confidence calibration",
            "type_change": "Review classification model for this element type",
        }
        return recommendations.get(correction_type, "Review model performance")

    # =========================================================================
    # Statistics and Metrics
    # =========================================================================

    async def get_correction_stats(self) -> Dict[str, Any]:
        """Get correction statistics.

        Returns:
            Statistics dictionary
        """
        total = len(self._corrections)
        if total == 0:
            return {
                "total_corrections": 0,
                "total_approvals": len(self._approved_without_correction),
            }

        corrections_list = list(self._corrections.values())

        return {
            "total_corrections": total,
            "total_approvals": len(self._approved_without_correction),
            "by_correction_type": dict(
                Counter(r.correction_type.value for r in corrections_list)
            ),
            "by_pipeline_stage": dict(
                Counter(r.pipeline_stage.value for r in corrections_list)
            ),
            "by_element_type": dict(
                Counter(r.element_type for r in corrections_list)
            ),
            "avg_original_confidence": sum(
                r.original_confidence for r in corrections_list
            ) / total,
            "flagged_for_training": sum(
                1 for r in corrections_list if r.flagged_for_training
            ),
            "flagged_as_edge_case": sum(
                1 for r in corrections_list if r.flagged_as_edge_case
            ),
        }


# =============================================================================
# Factory Function
# =============================================================================

def create_feedback_loop_manager(
    config: Optional[FeedbackLoopConfig] = None,
) -> FeedbackLoopManager:
    """Create a FeedbackLoopManager instance.

    Args:
        config: Optional configuration

    Returns:
        FeedbackLoopManager instance
    """
    return FeedbackLoopManager(config)


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "FeedbackLoopConfig",
    "DateRange",
    "CorrectionRecord",
    "TrainingDataset",
    "ErrorPattern",
    "ErrorPatternReport",
    "FeedbackLoopManager",
    "create_feedback_loop_manager",
]

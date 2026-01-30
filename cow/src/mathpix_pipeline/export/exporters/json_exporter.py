"""
JSON Exporter for Stage E (Export).

Exports pipeline results to JSON format with support for:
- Pretty-printed or compact output
- Schema version inclusion
- Pydantic model serialization
- Custom JSON encoders
- AlignmentLayer Structured Output export

Module Version: 2.0.0
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel

from ...schemas.alignment_layer import (
    AlignmentLayer,
    FlaggedItem,
    HITLFeedback,
    LaTeXAlignment,
    MatchedPairV2,
)
from ...schemas.export import (
    ExportFormat,
    ExportOptions,
    ExportSpec,
)
from ..schemas import (
    AlignmentEntry,
    AlignmentExportSchema,
    AlignmentSummary,
    HITLSummary,
    LaTeXElementEntry,
    MatchedPairEntry,
    ProvenanceInfo,
    QualityMetrics,
    VisualElementEntry,
)
from .base import BaseExporter, ExporterConfig

logger = logging.getLogger(__name__)


# =============================================================================
# Configuration
# =============================================================================

@dataclass
class JSONExporterConfig(ExporterConfig):
    """Configuration for JSON exporter.

    Attributes:
        indent: Indentation for pretty printing (None for compact)
        sort_keys: Sort dictionary keys alphabetically
        ensure_ascii: Escape non-ASCII characters
        include_schema_version: Add schema version to output
        datetime_format: Format for datetime serialization
    """
    indent: Optional[int] = 2
    sort_keys: bool = False
    ensure_ascii: bool = False
    include_schema_version: bool = True
    datetime_format: str = "iso"  # "iso", "timestamp", "string"


# =============================================================================
# Custom JSON Encoder
# =============================================================================

class PipelineJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for pipeline data types."""

    def __init__(self, *args, datetime_format: str = "iso", **kwargs):
        super().__init__(*args, **kwargs)
        self.datetime_format = datetime_format

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            if self.datetime_format == "iso":
                return obj.isoformat()
            elif self.datetime_format == "timestamp":
                return obj.timestamp()
            else:
                return str(obj)

        if isinstance(obj, BaseModel):
            return obj.model_dump(mode="json")

        if isinstance(obj, Path):
            return str(obj)

        if hasattr(obj, "__dict__"):
            return obj.__dict__

        return super().default(obj)


# =============================================================================
# JSON Exporter
# =============================================================================

class JSONExporter(BaseExporter[JSONExporterConfig]):
    """Export pipeline results to JSON format.

    Supports exporting RegenerationSpec, SemanticGraph, and other
    Pydantic models to well-formatted JSON files.

    Usage:
        exporter = JSONExporter()
        spec = exporter.export(regeneration_spec, options, "img_123")

        # Or export to bytes
        json_bytes = exporter.export_to_bytes(data, options)
    """

    def _default_config(self) -> JSONExporterConfig:
        """Create default configuration."""
        return JSONExporterConfig()

    @property
    def format(self) -> ExportFormat:
        """Get export format."""
        return ExportFormat.JSON

    @property
    def content_type(self) -> str:
        """Get MIME content type."""
        return "application/json"

    def _create_encoder(self) -> PipelineJSONEncoder:
        """Create configured JSON encoder."""
        return PipelineJSONEncoder(datetime_format=self.config.datetime_format)

    def _is_alignment_layer(self, data: Any) -> bool:
        """Check if data is an AlignmentLayer instance."""
        return isinstance(data, AlignmentLayer)

    def _serialize_alignment_layer(self, layer: AlignmentLayer) -> Dict[str, Any]:
        """Serialize AlignmentLayer to Structured Output compatible format.

        Args:
            layer: AlignmentLayer to serialize

        Returns:
            AlignmentExportSchema as dictionary
        """
        # Build summary
        status_counts: Dict[str, int] = {}
        for alignment in layer.alignments:
            status = alignment.verification_status.value
            status_counts[status] = status_counts.get(status, 0) + 1

        summary = AlignmentSummary(
            total_alignments=layer.alignment_count,
            verified_count=layer.verified_count,
            mismatch_count=layer.mismatch_count,
            hitl_required_count=layer.hitl_required_count,
            average_alignment_score=round(layer.average_alignment_score, 4),
            overall_quality=round(layer.overall_quality, 4),
            verification_breakdown=status_counts,
            needs_hitl=layer.needs_hitl(),
        )

        # Build alignment entries
        alignments = [
            AlignmentEntry(
                id=a.id,
                match_type=a.match_type.value,
                latex_element=LaTeXElementEntry(
                    id=a.latex_element.id,
                    latex_content=a.latex_element.latex_content,
                    element_type=a.latex_element.element_type,
                    confidence=a.latex_element.confidence,
                ),
                visual_elements=[
                    VisualElementEntry(
                        id=ve.id,
                        element_class=ve.element_class,
                        semantic_label=ve.semantic_label,
                        confidence=ve.confidence,
                    )
                    for ve in a.visual_elements
                ],
                alignment_score=round(a.alignment_score, 4),
                semantic_similarity=(
                    round(a.semantic_similarity, 4)
                    if a.semantic_similarity is not None
                    else None
                ),
                spatial_correlation=(
                    round(a.spatial_correlation, 4)
                    if a.spatial_correlation is not None
                    else None
                ),
                verification_status=a.verification_status.value,
                threshold_passed=a.threshold_passed,
                applied_threshold=a.applied_threshold,
            )
            for a in layer.alignments
        ]

        # Build matched pairs
        matched_pairs = [
            MatchedPairEntry(
                id=p.id,
                latex_id=p.latex_id,
                visual_id=p.visual_id,
                match_confidence=round(p.match_confidence, 4),
                match_reason=p.match_reason,
                verified=p.verified,
                verified_by=p.verified_by,
            )
            for p in layer.matched_pairs
        ]

        # Build HITL summary if applicable
        hitl = None
        if layer.flagged_items or layer.hitl_feedbacks:
            pending = layer.get_pending_feedbacks()
            hitl = HITLSummary(
                flagged_count=len(layer.flagged_items),
                feedback_count=len(layer.hitl_feedbacks),
                pending_count=len(pending) if pending else 0,
                flagged_items=[
                    {
                        "item_id": item.item_id,
                        "item_type": item.item_type,
                        "confidence": round(item.confidence, 4),
                        "reason": item.reason,
                        "suggested_action": item.suggested_action.value,
                        "priority": item.priority,
                    }
                    for item in layer.flagged_items
                ],
                feedbacks=[
                    {
                        "id": fb.id,
                        "target_item_id": fb.target_item_id,
                        "decision": fb.decision.value,
                        "reviewer_id": fb.reviewer_id,
                    }
                    for fb in layer.hitl_feedbacks
                ],
                pending_item_ids=[item.item_id for item in pending] if pending else [],
            )

        # Build quality metrics
        scores = [a.alignment_score for a in layer.alignments]
        verified_ratio = (
            layer.verified_count / layer.alignment_count
            if layer.alignment_count > 0
            else 0.0
        )
        mismatch_ratio = (
            layer.mismatch_count / layer.alignment_count
            if layer.alignment_count > 0
            else 0.0
        )

        calibration_data = None
        if layer.calibration_state:
            state = layer.calibration_state
            calibration_data = {
                "current_threshold": state.current_threshold,
                "calibration_score": round(state.calibration_score, 4),
                "accuracy": round(state.accuracy, 4),
                "total_samples": state.total_samples,
                "is_stable": state.is_stable,
            }

        quality = QualityMetrics(
            overall_quality=round(layer.overall_quality, 4),
            average_alignment_score=round(layer.average_alignment_score, 4),
            verified_ratio=round(verified_ratio, 4),
            mismatch_ratio=round(mismatch_ratio, 4),
            score_distribution={
                "min": round(min(scores), 4) if scores else 0.0,
                "max": round(max(scores), 4) if scores else 0.0,
                "avg": round(sum(scores) / len(scores), 4) if scores else 0.0,
            },
            calibration=calibration_data,
            review_required=layer.review.review_required,
            review_severity=(
                layer.review.review_severity.value
                if layer.review.review_severity
                else None
            ),
        )

        # Build provenance
        prov = layer.provenance
        reconstruction_data = None
        log = layer.reconstruction_log
        if log and log.entries:
            reconstruction_data = {
                "log_id": log.id,
                "entry_count": log.entry_count,
                "current_phase": log.current_phase.value if log.current_phase else None,
                "last_modified": log.last_modified_at.isoformat(),
            }

        provenance = ProvenanceInfo(
            stage=prov.stage.value,
            model=prov.model,
            created_at=prov.timestamp,  # Provenance uses 'timestamp', export uses 'created_at'
            pipeline_version=prov.version,  # Provenance uses 'version', export uses 'pipeline_version'
            reconstruction=reconstruction_data,
        )

        # Build complete export schema
        export_schema = AlignmentExportSchema(
            alignment_layer_id=layer.id,
            vision_spec_id=layer.vision_spec_id,
            text_spec_id=layer.text_spec_id,
            summary=summary,
            alignments=alignments,
            matched_pairs=matched_pairs,
            hitl=hitl,
            quality=quality,
            provenance=provenance,
        )

        return export_schema.model_dump(mode="json")

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data to JSON-compatible dictionary.

        Args:
            data: Data to serialize

        Returns:
            JSON-compatible dictionary
        """
        # AlignmentLayer: Use Structured Output schema
        if self._is_alignment_layer(data):
            return self._serialize_alignment_layer(data)

        # Legacy handling
        if isinstance(data, BaseModel):
            result = data.model_dump(mode="json")
        elif hasattr(data, "to_dict"):
            result = data.to_dict()
        elif isinstance(data, dict):
            result = data
        else:
            result = {"data": data}

        # Add schema version if configured
        if self.config.include_schema_version:
            if isinstance(result, dict):
                result["_export_metadata"] = {
                    "schema_version": "3.0.0",
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "format": "json",
                }

        return result

    def export_to_bytes(
        self,
        data: Any,
        options: ExportOptions,
    ) -> bytes:
        """Export data to JSON bytes.

        Args:
            data: Data to export
            options: Export options

        Returns:
            JSON content as bytes
        """
        serialized = self._serialize_data(data)

        # Determine formatting
        indent = self.config.indent if self.config.pretty_format else None

        json_str = json.dumps(
            serialized,
            cls=type(self._create_encoder()),
            indent=indent,
            sort_keys=self.config.sort_keys,
            ensure_ascii=self.config.ensure_ascii,
        )

        return json_str.encode("utf-8")

    def export(
        self,
        data: Any,
        options: ExportOptions,
        image_id: str,
    ) -> ExportSpec:
        """Export data to JSON file.

        Args:
            data: Data to export
            options: Export options
            image_id: Source image identifier

        Returns:
            ExportSpec with export metadata
        """
        start_time = time.time()

        # Generate identifiers
        export_id = self._generate_export_id(image_id)
        filename = self._generate_filename(image_id, options)
        filepath = self.config.output_dir / filename

        # Check existing file
        if filepath.exists() and not self.config.overwrite_existing:
            filepath = filepath.with_stem(f"{filepath.stem}_{export_id[:6]}")

        # Serialize and write
        json_bytes = self.export_to_bytes(data, options)
        checksum = self._calculate_checksum(json_bytes)
        file_size = self._write_file(json_bytes, filepath)

        # Count elements
        element_count = 0
        if self._is_alignment_layer(data):
            element_count = data.alignment_count
        elif hasattr(data, "outputs"):
            element_count = len(data.outputs)
        elif hasattr(data, "nodes"):
            element_count = len(data.nodes)

        processing_time = (time.time() - start_time) * 1000

        self._stats["exports_completed"] += 1

        logger.info(
            f"JSON export completed: {filepath}, "
            f"size={file_size} bytes, time={processing_time:.1f}ms"
        )

        return self._create_export_spec(
            export_id=export_id,
            image_id=image_id,
            filepath=filepath,
            file_size=file_size,
            checksum=checksum,
            element_count=element_count,
            processing_time_ms=processing_time,
        )


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "JSONExporter",
    "JSONExporterConfig",
    "PipelineJSONEncoder",
]

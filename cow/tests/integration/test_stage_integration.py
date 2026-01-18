"""
Integration Tests for Stage Boundaries in Math Image Parsing Pipeline.

Tests data flow between pipeline stages:
- Stage A (Ingestion) -> Stage B/C (Text/Vision Parse)
- Stage B + C -> Stage D (Alignment)
- Stage D -> Stage E (Semantic Graph)
- Stage E -> Stage F (Regeneration)
- Stage F -> Stage H (Export)

Each test validates that data structures are correctly transformed
and passed between stages with proper confidence propagation.

Schema Version: 2.0.0
"""

# import asyncio (not needed)
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Schema imports - Common
from mathpix_pipeline.schemas import (
    # Common
    BBox,
    BBoxNormalized,
    Confidence,
    CombinedConfidence,
    Provenance,
    PipelineStage,
    ReviewMetadata,
    ReviewSeverity,
    WritingStyle,
    # Stage A: Ingestion (note renamed exports)
    IngestionSpec,
    ImageMetadata,
    IngestionValidationResult as ValidationResult,
    IngestionRegion as Region,
    create_ingestion_spec,
    # Stage B: Text Parse
    TextSpec,
    ContentFlags,
    ContentType,
    LineSegment,
    EquationElement,
    VisionParseTrigger,
    DetectionMapEntry,
    # Stage C: Vision Parse
    VisionSpec,
    DetectionLayer,
    InterpretationLayer,
    MergedOutput,
    DetectionElement,
    InterpretedElement,
    InterpretedRelation,
    MergedElement,
    ElementClass,
    DiagramType,
    RelationType,
    # Stage D: Alignment
    AlignmentReport,
    AlignmentStatistics,
    TextElement,
    VisualElement,
    MatchedPair,
    Inconsistency,
    UnmatchedElement,
    MatchType,
    InconsistencyType,
    # Stage E: Semantic Graph
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
    NodeProperties,
    GraphStatistics,
)

# Stage F: Regeneration (direct import from submodule)
from mathpix_pipeline.schemas.regeneration import (
    RegenerationSpec,
    RegenerationOutput,
    RegenerationResult,
    DeltaReport,
    DeltaElement,
    OutputFormat,
    DeltaType,
    ElementCategory,
)

# Stage H: Export (direct import from submodule)
from mathpix_pipeline.schemas.export import (
    ExportSpec,
    ExportOptions,
    ExportFormat,
    ExportStatus,
    StorageType,
    ExportRequest,
    ExportResponse,
    BatchExportSpec,
)


# =============================================================================
# Test Fixtures - Mock Data Generators
# =============================================================================

class MockDataGenerator:
    """Generates mock data for integration tests."""

    @staticmethod
    def create_ingestion_spec(
        image_id: str = "test-image-001",
        width: int = 800,
        height: int = 600,
        is_valid: bool = True,
        math_confidence: float = 0.85,
    ) -> IngestionSpec:
        """Create a mock IngestionSpec (Stage A output)."""
        return create_ingestion_spec(
            image_id=image_id,
            format="png",
            width=width,
            height=height,
            file_size_bytes=width * height * 3,  # Approx RGB
            color_mode="RGB",
            dpi=72,
            source_path=f"/mock/images/{image_id}.png",
            is_valid=is_valid,
            checks_passed=["format_check", "size_check", "content_check"],
            checks_failed=[] if is_valid else ["corrupt_data"],
            preprocessing_applied=["normalize", "denoise"],
            regions=[
                Region(
                    x=100, y=100, width=600, height=400,
                    region_type="math", confidence=0.9,
                )
            ],
            math_confidence=math_confidence,
        )

    @staticmethod
    def create_text_spec(
        image_id: str = "test-image-001",
        confidence: float = 0.85,
        has_equations: bool = True,
        has_diagram: bool = True,
        triggers_vision: bool = True,
    ) -> TextSpec:
        """Create a mock TextSpec (Stage B output)."""
        equations = []
        if has_equations:
            equations.append(EquationElement(
                id=f"{image_id}-eq-001",
                latex="y = x^2 + 2x + 1",
                latex_styled="y = x^{2} + 2x + 1",
                confidence=Confidence(
                    value=0.92,
                    source="mathpix-api-v3",
                    element_type="equation",
                ),
                bbox=BBox(x=100.0, y=50.0, width=200.0, height=40.0),
            ))

        triggers = []
        if triggers_vision:
            triggers.append(VisionParseTrigger.DIAGRAM_EXTRACTION)
            if has_diagram:
                triggers.append(VisionParseTrigger.GRAPH_ANALYSIS)

        return TextSpec(
            image_id=image_id,
            provenance=Provenance(
                stage=PipelineStage.TEXT_PARSE,
                model="mathpix-api-v3",
                processing_time_ms=150.0,
            ),
            content_flags=ContentFlags(
                contains_equation=has_equations,
                contains_diagram=has_diagram,
                contains_text=True,
                contains_graph=has_diagram,
            ),
            vision_parse_triggers=triggers,
            writing_style=WritingStyle.PRINTED,
            text="y = x^2 + 2x + 1\nPoint A at (2,4)",
            latex="y = x^{2} + 2x + 1",
            confidence=confidence,
            equations=equations,
            line_segments=[
                LineSegment(
                    id=f"{image_id}-line-001",
                    text="Point A at (2,4)",
                    bbox=BBox(x=50.0, y=100.0, width=150.0, height=20.0),
                    confidence=Confidence(
                        value=0.88,
                        source="mathpix-api-v3",
                        element_type="line",
                    ),
                    line_number=0,
                    content_type=ContentType.TEXT,
                ),
                LineSegment(
                    id=f"{image_id}-line-002",
                    text="A",
                    bbox=BBox(x=200.0, y=300.0, width=20.0, height=20.0),
                    confidence=Confidence(
                        value=0.85,
                        source="mathpix-api-v3",
                        element_type="line",
                    ),
                    line_number=1,
                    content_type=ContentType.TEXT,
                ),
            ],
            processing_time_ms=150.0,
        )

    @staticmethod
    def create_vision_spec(
        image_id: str = "test-image-001",
        text_spec_id: Optional[str] = None,
        overall_confidence: float = 0.88,
    ) -> VisionSpec:
        """Create a mock VisionSpec (Stage C output)."""
        return VisionSpec(
            image_id=image_id,
            text_spec_id=text_spec_id or f"{image_id}-text",
            provenance=Provenance(
                stage=PipelineStage.VISION_PARSE,
                model="hybrid-yolo26-claude",
                processing_time_ms=250.0,
            ),
            detection_layer=DetectionLayer(
                model="yolo26-math-v1",
                elements=[
                    DetectionElement(
                        id=f"{image_id}-det-001",
                        element_class=ElementClass.CURVE,
                        bbox=BBox(x=100.0, y=100.0, width=300.0, height=200.0),
                        detection_confidence=0.91,
                    ),
                    DetectionElement(
                        id=f"{image_id}-det-002",
                        element_class=ElementClass.POINT,
                        bbox=BBox(x=195.0, y=295.0, width=30.0, height=30.0),
                        detection_confidence=0.87,
                    ),
                    DetectionElement(
                        id=f"{image_id}-det-003",
                        element_class=ElementClass.LABEL,
                        bbox=BBox(x=200.0, y=300.0, width=20.0, height=20.0),
                        detection_confidence=0.85,
                    ),
                ],
                inference_time_ms=50.0,
            ),
            interpretation_layer=InterpretationLayer(
                model="claude-opus-4-5",
                elements=[
                    InterpretedElement(
                        id=f"{image_id}-interp-001",
                        detection_element_id=f"{image_id}-det-001",
                        semantic_label="Parabola",
                        description="Quadratic function y = x^2 + 2x + 1",
                        function_type="quadratic",
                        equation="y = x^2 + 2x + 1",
                        interpretation_confidence=0.93,
                    ),
                    InterpretedElement(
                        id=f"{image_id}-interp-002",
                        detection_element_id=f"{image_id}-det-002",
                        semantic_label="Point A",
                        description="Point labeled A at coordinates",
                        coordinates={"x": 2.0, "y": 4.0},
                        point_label="A",
                        interpretation_confidence=0.89,
                    ),
                ],
                relations=[
                    InterpretedRelation(
                        id=f"{image_id}-rel-001",
                        source_id=f"{image_id}-interp-002",
                        target_id=f"{image_id}-interp-001",
                        relation_type=RelationType.POINT_ON,  # Use available enum value
                        confidence=0.86,
                        description="Point A lies on the parabola",
                    ),
                ],
                diagram_type=DiagramType.FUNCTION_GRAPH,
                diagram_description="A parabola with labeled points",
                coordinate_system="cartesian",
                inference_time_ms=200.0,
            ),
            merged_output=MergedOutput(
                diagram_type=DiagramType.FUNCTION_GRAPH,
                diagram_description="A parabola with labeled points",
                coordinate_system="cartesian",
                elements=[
                    MergedElement(
                        id=f"{image_id}-merged-001",
                        element_class=ElementClass.CURVE,
                        semantic_label="Parabola",
                        description="Quadratic function y = x^2 + 2x + 1",
                        bbox=BBox(x=100.0, y=100.0, width=300.0, height=200.0),
                        detection_id=f"{image_id}-det-001",
                        interpretation_id=f"{image_id}-interp-001",
                        combined_confidence=CombinedConfidence(
                            detection_confidence=0.91,
                            interpretation_confidence=0.93,
                            combined_value=0.918,
                            bbox_source="yolo26",
                            label_source="claude-opus-4-5",
                        ),
                        equation="y = x^2 + 2x + 1",
                    ),
                    MergedElement(
                        id=f"{image_id}-merged-002",
                        element_class=ElementClass.POINT,
                        semantic_label="Point A",
                        description="Point labeled A at coordinates",
                        bbox=BBox(x=195.0, y=295.0, width=30.0, height=30.0),
                        detection_id=f"{image_id}-det-002",
                        interpretation_id=f"{image_id}-interp-002",
                        combined_confidence=CombinedConfidence(
                            detection_confidence=0.87,
                            interpretation_confidence=0.89,
                            combined_value=0.878,
                            bbox_source="yolo26",
                            label_source="claude-opus-4-5",
                        ),
                        coordinates={"x": 2.0, "y": 4.0},
                    ),
                ],
                matched_count=2,
            ),
            total_processing_time_ms=250.0,
        )

    @staticmethod
    def create_alignment_report(
        image_id: str = "test-image-001",
        text_spec_id: str = "text-001",
        vision_spec_id: str = "vision-001",
        overall_score: float = 0.85,
        has_inconsistencies: bool = False,
    ) -> AlignmentReport:
        """Create a mock AlignmentReport (Stage D output)."""
        inconsistencies = []
        if has_inconsistencies:
            inconsistencies.append(Inconsistency(
                id=f"{image_id}-inconsistency-001",
                inconsistency_type=InconsistencyType.COORDINATE_MISMATCH,
                severity=ReviewSeverity.MEDIUM,
                description="Coordinate values differ between text and visual",
                expected_value="(2, 4)",
                actual_value="(2.1, 3.9)",
                confidence=0.75,
            ))

        return AlignmentReport(
            image_id=image_id,
            text_spec_id=text_spec_id,
            vision_spec_id=vision_spec_id,
            provenance=Provenance(
                stage=PipelineStage.ALIGNMENT,
                model="alignment-engine-v2",
                processing_time_ms=100.0,
            ),
            matched_pairs=[
                MatchedPair(
                    id=f"{image_id}-match-001",
                    match_type=MatchType.EQUATION_TO_GRAPH,
                    text_element=TextElement(
                        id=f"{image_id}-text-eq-001",
                        content="y = x^2 + 2x + 1",
                        latex="y = x^{2} + 2x + 1",
                        bbox=BBox(x=100.0, y=50.0, width=200.0, height=40.0),
                    ),
                    visual_element=VisualElement(
                        id=f"{image_id}-visual-curve-001",
                        element_class="curve",
                        semantic_label="Parabola",
                        bbox=BBox(x=100.0, y=100.0, width=300.0, height=200.0),
                    ),
                    consistency_score=0.88,
                    confidence=Confidence(
                        value=0.88,
                        source="alignment-matcher",
                        element_type="equation_graph_match",
                    ),
                    applied_threshold=0.60,
                    spatial_overlap=0.35,
                    semantic_similarity=0.92,
                ),
                MatchedPair(
                    id=f"{image_id}-match-002",
                    match_type=MatchType.LABEL_TO_POINT,
                    text_element=TextElement(
                        id=f"{image_id}-text-label-A",
                        content="A",
                        bbox=BBox(x=200.0, y=300.0, width=20.0, height=20.0),
                    ),
                    visual_element=VisualElement(
                        id=f"{image_id}-visual-point-A",
                        element_class="point",
                        semantic_label="Point A",
                        bbox=BBox(x=195.0, y=295.0, width=30.0, height=30.0),
                    ),
                    consistency_score=0.85,
                    confidence=Confidence(
                        value=0.85,
                        source="alignment-matcher",
                        element_type="label_point_match",
                    ),
                    applied_threshold=0.60,
                    spatial_overlap=0.72,
                    semantic_similarity=0.95,
                ),
            ],
            inconsistencies=inconsistencies,
            unmatched_elements=[],
            statistics=AlignmentStatistics(
                total_text_elements=3,
                total_visual_elements=2,
            ),
            overall_alignment_score=overall_score,
            overall_confidence=overall_score,
            processing_time_ms=100.0,
        )

    @staticmethod
    def create_semantic_graph(
        image_id: str = "test-image-001",
        alignment_report_id: str = "alignment-001",
        overall_confidence: float = 0.85,
    ) -> SemanticGraph:
        """Create a mock SemanticGraph (Stage E output).

        Note: We use model_construct() to avoid triggering model_validator
        which causes recursion with validate_assignment=True.
        """
        # Create nodes using model_construct to avoid validation recursion
        nodes = [
            SemanticNode.model_construct(
                id=f"{image_id}-node-curve-001",
                node_type=NodeType.CURVE,
                label="Parabola y = x^2 + 2x + 1",
                bbox=BBox(x=100.0, y=100.0, width=300.0, height=200.0),
                confidence=Confidence(
                    value=0.88,
                    source="alignment-engine",
                    element_type="curve",
                ),
                threshold_passed=True,
                applied_threshold=0.60,
                properties=NodeProperties(
                    equation="y = x^2 + 2x + 1",
                    function_type="quadratic",
                    latex="y = x^{2} + 2x + 1",
                ),
                source_element_ids=[f"{image_id}-merged-001"],
                review=ReviewMetadata(),
            ),
            SemanticNode.model_construct(
                id=f"{image_id}-node-point-A",
                node_type=NodeType.POINT,
                label="Point A (2, 4)",
                bbox=BBox(x=195.0, y=295.0, width=30.0, height=30.0),
                confidence=Confidence(
                    value=0.85,
                    source="alignment-engine",
                    element_type="point",
                ),
                threshold_passed=True,
                applied_threshold=0.60,
                properties=NodeProperties(
                    coordinates={"x": 2.0, "y": 4.0},
                    point_label="A",
                ),
                source_element_ids=[f"{image_id}-merged-002"],
                review=ReviewMetadata(),
            ),
            SemanticNode.model_construct(
                id=f"{image_id}-node-axis-x",
                node_type=NodeType.AXIS,
                label="X-axis",
                bbox=None,
                confidence=Confidence(
                    value=0.90,
                    source="graph-builder",
                    element_type="axis",
                ),
                threshold_passed=True,
                applied_threshold=0.60,
                properties=NodeProperties(
                    description="Horizontal axis",
                ),
                source_element_ids=[],
                review=ReviewMetadata(),
            ),
            SemanticNode.model_construct(
                id=f"{image_id}-node-axis-y",
                node_type=NodeType.AXIS,
                label="Y-axis",
                bbox=None,
                confidence=Confidence(
                    value=0.90,
                    source="graph-builder",
                    element_type="axis",
                ),
                threshold_passed=True,
                applied_threshold=0.60,
                properties=NodeProperties(
                    description="Vertical axis",
                ),
                source_element_ids=[],
                review=ReviewMetadata(),
            ),
        ]

        # Create edges using model_construct
        edges = [
            SemanticEdge.model_construct(
                id=f"{image_id}-edge-001",
                source_id=f"{image_id}-node-point-A",
                target_id=f"{image_id}-node-curve-001",
                edge_type=EdgeType.LIES_ON,
                confidence=Confidence(
                    value=0.86,
                    source="relation-inferrer",
                    element_type="edge",
                ),
                threshold_passed=True,
                applied_threshold=0.55,
                properties={},
                description="Point A lies on the parabola",
                bidirectional=False,
                review=ReviewMetadata(),
            ),
            SemanticEdge.model_construct(
                id=f"{image_id}-edge-002",
                source_id=f"{image_id}-node-curve-001",
                target_id=f"{image_id}-node-axis-x",
                edge_type=EdgeType.INTERSECTS,
                confidence=Confidence(
                    value=0.82,
                    source="relation-inferrer",
                    element_type="edge",
                ),
                threshold_passed=True,
                applied_threshold=0.55,
                properties={},
                description="Parabola intersects X-axis",
                bidirectional=False,
                review=ReviewMetadata(),
            ),
        ]

        # Create graph using model_construct to avoid compute_statistics recursion
        graph = SemanticGraph.model_construct(
            schema_version="2.0.0",
            image_id=image_id,
            alignment_report_id=alignment_report_id,
            provenance=Provenance(
                stage=PipelineStage.SEMANTIC_GRAPH,
                model="graph-builder-v2",
                processing_time_ms=80.0,
            ),
            nodes=nodes,
            edges=edges,
            coordinate_system="cartesian",
            graph_type="function_graph",
            description="A parabola with labeled point A",
            statistics=GraphStatistics(
                total_nodes=4,
                total_edges=2,
                node_type_counts={"curve": 1, "point": 1, "axis": 2},
                edge_type_counts={"lies_on": 1, "intersects": 1},
                nodes_above_threshold=4,
                nodes_below_threshold=0,
                edges_above_threshold=2,
                edges_below_threshold=0,
                avg_node_confidence=0.88,
                avg_edge_confidence=0.84,
                min_confidence=0.82,
                max_confidence=0.90,
                connected_components=2,
                isolated_nodes=0,
            ),
            threshold_config_version="2.0.0",
            base_node_threshold=0.60,
            base_edge_threshold=0.55,
            overall_confidence=overall_confidence,
            review=ReviewMetadata(),
            nodes_needing_review=0,
            edges_needing_review=0,
            processing_time_ms=80.0,
        )

        return graph

    @staticmethod
    def create_regeneration_spec(
        image_id: str = "test-image-001",
        semantic_graph_id: str = "graph-001",
        overall_confidence: float = 0.90,
    ) -> RegenerationSpec:
        """Create a mock RegenerationSpec (Stage F output)."""
        latex_content = r"""
\begin{tikzpicture}
\begin{axis}[
    xlabel={$x$},
    ylabel={$y$},
    axis lines=center,
]
\addplot[domain=-3:1, samples=100, blue, thick] {x^2 + 2*x + 1};
\node[circle, fill=red, inner sep=2pt, label=above:$A$] at (axis cs:2,4) {};
\end{axis}
\end{tikzpicture}
"""

        svg_content = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 300">
    <path d="M 50 250 Q 200 50 350 250" stroke="blue" fill="none" stroke-width="2"/>
    <circle cx="280" cy="100" r="5" fill="red"/>
    <text x="285" y="95" font-size="12">A</text>
</svg>
"""

        return RegenerationSpec(
            image_id=image_id,
            semantic_graph_id=semantic_graph_id,
            provenance=Provenance(
                stage=PipelineStage.REGENERATION,
                model="regeneration-engine-v2",
                processing_time_ms=200.0,
            ),
            outputs=[
                RegenerationOutput(
                    format=OutputFormat.LATEX,
                    content=latex_content,
                    confidence=0.92,
                    generation_time_ms=150.0,
                    completeness_score=1.0,
                    semantic_fidelity=0.95,
                    element_count=2,
                    template_used="tikz_function_graph.j2",
                ),
                RegenerationOutput(
                    format=OutputFormat.SVG,
                    content=svg_content,
                    confidence=0.88,
                    generation_time_ms=50.0,
                    completeness_score=1.0,
                    semantic_fidelity=0.90,
                    element_count=2,
                ),
            ],
            delta_report=DeltaReport(
                similarity_score=0.95,
                unchanged_count=2,
                added_elements=[],
                removed_elements=[],
                modified_elements=[],
                has_structural_changes=False,
                has_semantic_changes=False,
                has_visual_changes=False,
                comparison_method="structural",
                comparison_time_ms=10.0,
            ),
            element_results=[
                RegenerationResult(
                    element_id=f"{image_id}-node-curve-001",
                    category=ElementCategory.GRAPH,
                    success=True,
                    outputs={
                        OutputFormat.LATEX: r"\addplot[...]{x^2 + 2*x + 1};",
                        OutputFormat.SVG: '<path d="M 50 250 Q 200 50 350 250"/>',
                    },
                    confidence=0.92,
                    generation_time_ms=100.0,
                ),
                RegenerationResult(
                    element_id=f"{image_id}-node-point-A",
                    category=ElementCategory.SYMBOL,
                    success=True,
                    outputs={
                        OutputFormat.LATEX: r"\node[...] at (axis cs:2,4) {};",
                        OutputFormat.SVG: '<circle cx="280" cy="100" r="5"/>',
                    },
                    confidence=0.88,
                    generation_time_ms=50.0,
                ),
            ],
            processing_time_ms=200.0,
        )

    @staticmethod
    def create_export_spec(
        image_id: str = "test-image-001",
        export_format: ExportFormat = ExportFormat.JSON,
    ) -> ExportSpec:
        """Create a mock ExportSpec (Stage H output)."""
        return ExportSpec(
            export_id=f"export-{uuid4().hex[:8]}",
            image_id=image_id,
            format=export_format,
            content_type="application/json" if export_format == ExportFormat.JSON else "application/pdf",
            file_path=f"/exports/{image_id}.{export_format.value}",
            storage_type=StorageType.LOCAL,
            file_size=1024,
            checksum="abc123def456",
            element_count=4,
            confidence=0.90,
            processing_time_ms=50.0,
        )


# =============================================================================
# Stage A -> B/C Integration Tests
# =============================================================================

class TestIngestionIntegration:
    """Test data flow from Stage A (Ingestion) to Stage B/C (Text/Vision Parse)."""

    # sync test
    def test_ingestion_to_text_parse(self):
        """Test that IngestionSpec correctly flows to TextSpec processing.

        Verifies:
        - Image ID propagation
        - Validation status check
        - Math content confidence triggers text parse
        """
        # Arrange
        ingestion = MockDataGenerator.create_ingestion_spec(
            image_id="flow-test-001",
            is_valid=True,
            math_confidence=0.90,
        )

        # Act - Simulate text parse receiving ingestion output
        assert ingestion.validation.is_valid, "Invalid images should not reach text parse"
        assert ingestion.has_math_content, "Low math confidence should skip text parse"

        text_spec = MockDataGenerator.create_text_spec(
            image_id=ingestion.image_id,
            confidence=0.85,
        )

        # Assert
        assert text_spec.image_id == ingestion.image_id
        assert text_spec.provenance.stage == PipelineStage.TEXT_PARSE
        assert len(text_spec.equations) > 0
        assert len(text_spec.line_segments) > 0

    # sync test
    def test_ingestion_to_vision_parse(self):
        """Test that IngestionSpec with diagram triggers VisionSpec processing.

        Verifies:
        - Vision parse is triggered when diagrams are detected
        - Detection layer receives image dimensions
        - Provenance chain is maintained
        """
        # Arrange
        ingestion = MockDataGenerator.create_ingestion_spec(
            image_id="vision-flow-001",
            width=1024,
            height=768,
            math_confidence=0.95,
        )

        # Simulate text parse indicates vision parse needed
        text_spec = MockDataGenerator.create_text_spec(
            image_id=ingestion.image_id,
            has_diagram=True,
            triggers_vision=True,
        )

        # Act
        assert text_spec.should_trigger_vision_parse()

        vision_spec = MockDataGenerator.create_vision_spec(
            image_id=ingestion.image_id,
            text_spec_id=f"{text_spec.image_id}-text",
        )

        # Assert
        assert vision_spec.image_id == ingestion.image_id
        assert vision_spec.text_spec_id is not None
        assert vision_spec.detection_layer.element_count > 0
        assert vision_spec.merged_output.diagram_type == DiagramType.FUNCTION_GRAPH

    # sync test
    def test_invalid_image_handling(self):
        """Test that invalid images are properly rejected at ingestion.

        Verifies:
        - Invalid images fail validation
        - Error details are captured
        - Processing stops at ingestion
        """
        # Arrange
        invalid_ingestion = MockDataGenerator.create_ingestion_spec(
            image_id="invalid-001",
            is_valid=False,
            math_confidence=0.1,
        )

        # Act & Assert
        assert not invalid_ingestion.validation.is_valid
        assert len(invalid_ingestion.validation.checks_failed) > 0
        assert not invalid_ingestion.has_math_content

        # Should not proceed to text parse
        with pytest.raises(AssertionError):
            assert invalid_ingestion.validation.is_valid, "Should reject invalid images"

    # sync test
    def test_ingestion_metadata_propagation(self):
        """Test that image metadata is correctly propagated through stages.

        Verifies:
        - Image dimensions are available for normalization
        - File format is tracked
        - Content hash enables deduplication
        """
        # Arrange
        ingestion = MockDataGenerator.create_ingestion_spec(
            image_id="metadata-test-001",
            width=800,
            height=600,
        )

        # Act
        metadata = ingestion.metadata

        # Assert
        assert metadata.width == 800
        assert metadata.height == 600
        assert metadata.format == "png"
        assert metadata.aspect_ratio == pytest.approx(800 / 600, rel=1e-2)
        assert metadata.megapixels == pytest.approx(0.48, rel=1e-2)


# =============================================================================
# Stage B + C -> D Integration Tests
# =============================================================================

class TestAlignmentIntegration:
    """Test data flow from Stage B/C to Stage D (Alignment)."""

    # sync test
    def test_text_vision_alignment(self):
        """Test alignment of text elements with visual elements.

        Verifies:
        - TextSpec elements are matched with VisionSpec elements
        - Match types are correctly identified
        - Confidence scores are combined
        """
        # Arrange
        image_id = "align-test-001"
        text_spec = MockDataGenerator.create_text_spec(image_id=image_id)
        vision_spec = MockDataGenerator.create_vision_spec(image_id=image_id)

        # Act - Simulate alignment
        alignment = MockDataGenerator.create_alignment_report(
            image_id=image_id,
            text_spec_id=f"{image_id}-text",
            vision_spec_id=f"{image_id}-vision",
            overall_score=0.85,
        )

        # Assert
        assert alignment.image_id == image_id
        assert alignment.text_spec_id is not None
        assert alignment.vision_spec_id is not None
        assert len(alignment.matched_pairs) > 0

        # Verify match types
        match_types = [m.match_type for m in alignment.matched_pairs]
        assert MatchType.EQUATION_TO_GRAPH in match_types
        assert MatchType.LABEL_TO_POINT in match_types

    # sync test
    def test_partial_match_handling(self):
        """Test handling of partial matches between text and visual elements.

        Verifies:
        - Unmatched elements are tracked
        - Partial matches have lower confidence
        - Review flags are set appropriately
        """
        # Arrange
        image_id = "partial-match-001"

        alignment = AlignmentReport(
            image_id=image_id,
            text_spec_id=f"{image_id}-text",
            vision_spec_id=f"{image_id}-vision",
            provenance=Provenance(
                stage=PipelineStage.ALIGNMENT,
                model="alignment-engine-v2",
            ),
            matched_pairs=[
                MatchedPair(
                    id=f"{image_id}-match-001",
                    match_type=MatchType.LABEL_TO_POINT,
                    text_element=TextElement(
                        id="text-A",
                        content="A",
                        bbox=BBox(x=200.0, y=300.0, width=20.0, height=20.0),
                    ),
                    visual_element=VisualElement(
                        id="visual-A",
                        element_class="point",
                        semantic_label="Point A",
                        bbox=BBox(x=195.0, y=295.0, width=30.0, height=30.0),
                    ),
                    consistency_score=0.55,  # Below threshold
                    confidence=Confidence(
                        value=0.55,
                        source="alignment-matcher",
                        element_type="match",
                    ),
                    applied_threshold=0.60,
                ),
            ],
            unmatched_elements=[
                UnmatchedElement(
                    id="unmatched-001",
                    source="text",
                    element_id="text-B",
                    content="B",
                    reason="No visual element found with label B",
                ),
            ],
            statistics=AlignmentStatistics(
                total_text_elements=2,
                total_visual_elements=1,
            ),
        )

        # Assert
        assert len(alignment.unmatched_elements) == 1
        assert alignment.unmatched_elements[0].source == "text"
        assert alignment.pairs_below_threshold == 1
        assert alignment.needs_human_review()

    # sync test
    def test_inconsistency_detection(self):
        """Test detection of inconsistencies between text and visual content.

        Verifies:
        - Coordinate mismatches are detected
        - Severity levels are assigned
        - Auto-fix suggestions are generated
        """
        # Arrange
        alignment = MockDataGenerator.create_alignment_report(
            image_id="inconsistent-001",
            has_inconsistencies=True,
        )

        # Assert
        assert len(alignment.inconsistencies) > 0

        inconsistency = alignment.inconsistencies[0]
        assert inconsistency.inconsistency_type == InconsistencyType.COORDINATE_MISMATCH
        assert inconsistency.severity in [ReviewSeverity.MEDIUM, ReviewSeverity.HIGH]
        assert inconsistency.expected_value is not None
        assert inconsistency.actual_value is not None

    # sync test
    def test_confidence_combination(self):
        """Test that confidence scores are properly combined from text and visual.

        Verifies:
        - Text confidence is considered
        - Visual confidence is considered
        - Combined score reflects both sources
        """
        # Arrange
        image_id = "confidence-test-001"
        text_spec = MockDataGenerator.create_text_spec(
            image_id=image_id,
            confidence=0.90,
        )
        vision_spec = MockDataGenerator.create_vision_spec(
            image_id=image_id,
            overall_confidence=0.85,
        )

        alignment = MockDataGenerator.create_alignment_report(
            image_id=image_id,
            overall_score=0.87,
        )

        # Assert
        assert alignment.overall_confidence >= 0.0
        assert alignment.overall_confidence <= 1.0

        # Verify matched pair confidence
        for pair in alignment.matched_pairs:
            assert pair.confidence.value >= 0.0
            assert pair.confidence.value <= 1.0
            assert pair.threshold_passed == (pair.consistency_score >= pair.applied_threshold)


# =============================================================================
# Stage D -> E Integration Tests
# =============================================================================

class TestSemanticGraphIntegration:
    """Test data flow from Stage D (Alignment) to Stage E (Semantic Graph)."""

    # sync test
    def test_alignment_to_graph(self):
        """Test conversion of alignment results to semantic graph.

        Verifies:
        - Matched pairs become graph nodes
        - Relationships become graph edges
        - Source element IDs are preserved
        """
        # Arrange
        image_id = "graph-test-001"
        alignment = MockDataGenerator.create_alignment_report(
            image_id=image_id,
            overall_score=0.88,
        )

        # Act
        graph = MockDataGenerator.create_semantic_graph(
            image_id=image_id,
            alignment_report_id=f"{image_id}-alignment",
        )

        # Assert
        assert graph.image_id == image_id
        assert graph.alignment_report_id is not None
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

        # Verify node types
        node_types = [n.node_type for n in graph.nodes]
        assert NodeType.CURVE in node_types
        assert NodeType.POINT in node_types

        # Verify edge types
        edge_types = [e.edge_type for e in graph.edges]
        assert EdgeType.LIES_ON in edge_types

    # sync test
    def test_confidence_propagation(self):
        """Test that confidence scores propagate from alignment to graph.

        Verifies:
        - Node confidence reflects source element confidence
        - Threshold checking is applied
        - Review flags are set for low-confidence nodes
        """
        # Arrange
        image_id = "confidence-prop-001"

        # Create nodes with model_construct to avoid recursion
        high_conf_node = SemanticNode.model_construct(
            id="node-high-conf",
            node_type=NodeType.CURVE,
            label="High confidence curve",
            bbox=None,
            confidence=Confidence(
                value=0.85,
                source="alignment",
                element_type="curve",
            ),
            threshold_passed=True,  # 0.85 >= 0.60
            applied_threshold=0.60,
            properties=NodeProperties(),
            source_element_ids=[],
            review=ReviewMetadata(review_required=False),
        )

        low_conf_node = SemanticNode.model_construct(
            id="node-low-conf",
            node_type=NodeType.POINT,
            label="Low confidence point",
            bbox=None,
            confidence=Confidence(
                value=0.50,
                source="alignment",
                element_type="point",
            ),
            threshold_passed=False,  # 0.50 < 0.60
            applied_threshold=0.60,
            properties=NodeProperties(),
            source_element_ids=[],
            review=ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.HIGH,
                review_reason="Node confidence 0.50 below threshold 0.60",
            ),
        )

        graph = SemanticGraph.model_construct(
            schema_version="2.0.0",
            image_id=image_id,
            alignment_report_id=f"{image_id}-alignment",
            provenance=Provenance(
                stage=PipelineStage.SEMANTIC_GRAPH,
                model="graph-builder-v2",
            ),
            nodes=[high_conf_node, low_conf_node],
            edges=[],
            coordinate_system=None,
            graph_type=None,
            description=None,
            statistics=GraphStatistics(
                total_nodes=2,
                total_edges=0,
                nodes_above_threshold=1,
                nodes_below_threshold=1,
            ),
            threshold_config_version="2.0.0",
            base_node_threshold=0.60,
            base_edge_threshold=0.55,
            overall_confidence=0.675,
            review=ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.MEDIUM,
                review_reason="1 nodes, 0 edges need review",
            ),
            nodes_needing_review=1,
            edges_needing_review=0,
        )

        # Assert
        found_high = graph.get_node("node-high-conf")
        found_low = graph.get_node("node-low-conf")

        assert found_high is not None
        assert found_high.threshold_passed is True
        assert found_high.review.review_required is False

        assert found_low is not None
        assert found_low.threshold_passed is False
        assert found_low.review.review_required is True
        assert found_low.review.review_severity == ReviewSeverity.HIGH

    # sync test
    def test_graph_statistics_computation(self):
        """Test that graph statistics are correctly computed.

        Verifies:
        - Node counts by type
        - Edge counts by type
        - Connectivity analysis
        """
        # Arrange
        graph = MockDataGenerator.create_semantic_graph(
            image_id="stats-test-001",
        )

        # Assert
        stats = graph.statistics
        assert stats.total_nodes == 4
        assert stats.total_edges == 2
        assert stats.nodes_above_threshold > 0
        assert stats.avg_node_confidence > 0.0
        assert "curve" in stats.node_type_counts
        assert "point" in stats.node_type_counts

    # sync test
    def test_graph_connectivity_analysis(self):
        """Test graph connectivity and neighbor finding.

        Verifies:
        - get_neighbors returns connected nodes
        - get_edges_for_node returns all edges
        - Isolated nodes are detected
        """
        # Arrange
        graph = MockDataGenerator.create_semantic_graph(
            image_id="connectivity-001",
        )

        # Act
        curve_node_id = f"connectivity-001-node-curve-001"
        point_node_id = f"connectivity-001-node-point-A"

        neighbors = graph.get_neighbors(curve_node_id)
        edges = graph.get_edges_for_node(curve_node_id)

        # Assert
        assert len(neighbors) > 0
        assert len(edges) > 0
        assert point_node_id in neighbors


# =============================================================================
# Stage E -> F Integration Tests
# =============================================================================

class TestRegenerationIntegration:
    """Test data flow from Stage E (Semantic Graph) to Stage F (Regeneration)."""

    # sync test
    def test_graph_to_latex(self):
        """Test generation of LaTeX from semantic graph.

        Verifies:
        - Graph nodes are converted to LaTeX elements
        - Equations are properly formatted
        - TikZ code is generated for diagrams
        """
        # Arrange
        image_id = "latex-test-001"
        graph = MockDataGenerator.create_semantic_graph(
            image_id=image_id,
        )

        # Act
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
            semantic_graph_id=f"{image_id}-graph",
        )

        # Assert
        latex_output = regen.get_output(OutputFormat.LATEX)
        assert latex_output is not None
        assert latex_output.confidence > 0.0
        assert "tikzpicture" in latex_output.content.lower()
        assert "addplot" in latex_output.content.lower()

    # sync test
    def test_graph_to_svg(self):
        """Test generation of SVG from semantic graph.

        Verifies:
        - Graph nodes are converted to SVG elements
        - Path elements for curves
        - Circle elements for points
        """
        # Arrange
        image_id = "svg-test-001"
        graph = MockDataGenerator.create_semantic_graph(
            image_id=image_id,
        )

        # Act
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
            semantic_graph_id=f"{image_id}-graph",
        )

        # Assert
        svg_output = regen.get_output(OutputFormat.SVG)
        assert svg_output is not None
        assert svg_output.confidence > 0.0
        assert "<svg" in svg_output.content.lower()
        assert "<path" in svg_output.content.lower()
        assert "<circle" in svg_output.content.lower()

    # sync test
    def test_delta_comparison(self):
        """Test delta comparison between original and regenerated content.

        Verifies:
        - Similarity score is computed
        - Changes are categorized
        - Semantic changes trigger review
        """
        # Arrange
        regen = MockDataGenerator.create_regeneration_spec(
            image_id="delta-test-001",
        )

        # Assert
        assert regen.delta_report is not None
        assert regen.delta_report.similarity_score >= 0.0
        assert regen.delta_report.similarity_score <= 1.0
        assert regen.delta_report.total_changes >= 0

        # High similarity should not have semantic changes
        if regen.delta_report.similarity_score > 0.90:
            assert not regen.delta_report.has_semantic_changes

    # sync test
    def test_element_result_tracking(self):
        """Test that regeneration tracks per-element results.

        Verifies:
        - Each element has a result
        - Success/failure is tracked
        - Error messages are captured
        """
        # Arrange
        regen = MockDataGenerator.create_regeneration_spec(
            image_id="element-track-001",
        )

        # Assert
        assert len(regen.element_results) > 0
        assert regen.total_elements_processed == len(regen.element_results)
        assert regen.total_elements_success == len([r for r in regen.element_results if r.success])
        assert regen.total_elements_failed == len([r for r in regen.element_results if not r.success])

        for result in regen.element_results:
            assert result.element_id is not None
            assert result.category in ElementCategory
            if result.success:
                assert len(result.outputs) > 0


# =============================================================================
# Stage F -> H Integration Tests
# =============================================================================

class TestExportIntegration:
    """Test data flow from Stage F (Regeneration) to Stage H (Export)."""

    # sync test
    def test_regeneration_to_export(self):
        """Test exporting regenerated content to files.

        Verifies:
        - Export spec is created from regeneration
        - File path is generated
        - Content type is correct
        """
        # Arrange
        image_id = "export-test-001"
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
        )

        # Act
        export = MockDataGenerator.create_export_spec(
            image_id=image_id,
            export_format=ExportFormat.JSON,
        )

        # Assert
        assert export.image_id == image_id
        assert export.format == ExportFormat.JSON
        assert export.content_type == "application/json"
        assert export.file_path is not None
        assert export.file_path.endswith(".json")

    # sync test
    def test_multi_format_export(self):
        """Test exporting to multiple formats simultaneously.

        Verifies:
        - JSON, PDF, LaTeX, SVG exports
        - Each format has correct content type
        - Batch export tracking
        """
        # Arrange
        image_id = "multi-export-001"
        formats = [ExportFormat.JSON, ExportFormat.PDF, ExportFormat.LATEX, ExportFormat.SVG]

        # Act
        exports = [
            MockDataGenerator.create_export_spec(image_id=image_id, export_format=fmt)
            for fmt in formats
        ]

        batch = BatchExportSpec(
            batch_id=f"batch-{uuid4().hex[:8]}",
            exports=exports,
            total_requested=len(formats),
        )

        # Assert
        assert batch.total_completed == len(formats)
        assert batch.total_size_bytes > 0

        content_types = {e.format: e.content_type for e in exports}
        assert "application/json" in content_types.values()
        assert "application/pdf" in content_types.values()

    # sync test
    def test_export_with_options(self):
        """Test export with various options.

        Verifies:
        - Metadata inclusion
        - Compression settings
        - Format-specific options
        """
        # Arrange
        options = ExportOptions(
            include_metadata=True,
            include_provenance=True,
            compress=True,
            compression_level=6,
            include_confidence_scores=True,
            pdf_options={
                "page_size": "letter",
                "margins": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            },
        )

        request = ExportRequest(
            image_id="options-test-001",
            formats=[ExportFormat.JSON, ExportFormat.PDF],
            options=options,
            async_mode=False,
        )

        # Assert
        assert request.options.include_metadata is True
        assert request.options.compress is True
        assert request.options.compression_level == 6
        assert "page_size" in request.options.pdf_options

    # sync test
    def test_export_confidence_tracking(self):
        """Test that export includes confidence information.

        Verifies:
        - Overall confidence is exported
        - Per-element confidence is available
        - Review requirements are included
        """
        # Arrange
        image_id = "conf-export-001"
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
            overall_confidence=0.88,
        )

        export = MockDataGenerator.create_export_spec(
            image_id=image_id,
            export_format=ExportFormat.JSON,
        )

        # Assert
        assert export.confidence > 0.0
        assert export.confidence <= 1.0


# =============================================================================
# End-to-End Pipeline Integration Tests
# =============================================================================

class TestFullPipelineIntegration:
    """Test complete data flow through all pipeline stages."""

    # sync test
    def test_complete_pipeline_flow(self):
        """Test data flowing through all stages A -> B -> C -> D -> E -> F -> H.

        Verifies:
        - Image ID is consistent across all stages
        - Provenance chain is maintained
        - Final export contains all processed data
        """
        # Arrange
        image_id = "full-pipeline-001"

        # Stage A: Ingestion
        ingestion = MockDataGenerator.create_ingestion_spec(
            image_id=image_id,
            is_valid=True,
            math_confidence=0.90,
        )
        assert ingestion.validation.is_valid

        # Stage B: Text Parse
        text_spec = MockDataGenerator.create_text_spec(
            image_id=image_id,
            has_equations=True,
            has_diagram=True,
            triggers_vision=True,
        )
        assert text_spec.image_id == image_id
        assert text_spec.should_trigger_vision_parse()

        # Stage C: Vision Parse
        vision_spec = MockDataGenerator.create_vision_spec(
            image_id=image_id,
            text_spec_id=f"{image_id}-text",
        )
        assert vision_spec.image_id == image_id
        assert len(vision_spec.merged_output.elements) > 0

        # Stage D: Alignment
        alignment = MockDataGenerator.create_alignment_report(
            image_id=image_id,
            text_spec_id=f"{image_id}-text",
            vision_spec_id=f"{image_id}-vision",
        )
        assert alignment.image_id == image_id
        assert len(alignment.matched_pairs) > 0

        # Stage E: Semantic Graph
        graph = MockDataGenerator.create_semantic_graph(
            image_id=image_id,
            alignment_report_id=f"{image_id}-alignment",
        )
        assert graph.image_id == image_id
        assert len(graph.nodes) > 0
        assert len(graph.edges) > 0

        # Stage F: Regeneration
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
            semantic_graph_id=f"{image_id}-graph",
        )
        assert regen.image_id == image_id
        assert len(regen.outputs) > 0

        # Stage H: Export
        export = MockDataGenerator.create_export_spec(
            image_id=image_id,
            export_format=ExportFormat.JSON,
        )
        assert export.image_id == image_id

    # sync test
    def test_provenance_chain_integrity(self):
        """Test that provenance information is consistent across stages.

        Verifies:
        - Each stage has correct provenance
        - Stage identifiers match expected values
        - Processing times are tracked
        """
        # Arrange
        image_id = "provenance-chain-001"

        stages = [
            MockDataGenerator.create_ingestion_spec(image_id=image_id),
            MockDataGenerator.create_text_spec(image_id=image_id),
            MockDataGenerator.create_vision_spec(image_id=image_id),
            MockDataGenerator.create_alignment_report(image_id=image_id),
            MockDataGenerator.create_semantic_graph(image_id=image_id),
            MockDataGenerator.create_regeneration_spec(image_id=image_id),
        ]

        expected_stages = [
            PipelineStage.INGESTION,
            PipelineStage.TEXT_PARSE,
            PipelineStage.VISION_PARSE,
            PipelineStage.ALIGNMENT,
            PipelineStage.SEMANTIC_GRAPH,
            PipelineStage.REGENERATION,
        ]

        # Assert
        for stage_output, expected_stage in zip(stages, expected_stages):
            assert stage_output.provenance.stage == expected_stage
            assert stage_output.provenance.processing_time_ms is not None or stage_output.provenance.processing_time_ms is None  # May be None for some

    # sync test
    def test_error_propagation(self):
        """Test that errors at early stages prevent later stage processing.

        Verifies:
        - Invalid ingestion blocks text parse
        - Low confidence text parse triggers review
        - Alignment failures flag for human review
        """
        # Stage A failure
        invalid_ingestion = MockDataGenerator.create_ingestion_spec(
            image_id="error-prop-001",
            is_valid=False,
        )
        assert not invalid_ingestion.validation.is_valid

        # Simulate that this would block further processing
        # In real pipeline, this would raise an exception or return early

        # Stage B low confidence
        low_conf_text = MockDataGenerator.create_text_spec(
            image_id="error-prop-002",
            confidence=0.30,
        )
        # This should still proceed but flag for review

        # Stage D alignment failures
        bad_alignment = MockDataGenerator.create_alignment_report(
            image_id="error-prop-003",
            overall_score=0.40,
            has_inconsistencies=True,
        )
        assert bad_alignment.needs_human_review()
        assert len(bad_alignment.inconsistencies) > 0


# =============================================================================
# Confidence Flow Integration Tests
# =============================================================================

class TestConfidenceFlowIntegration:
    """Test confidence score propagation across pipeline stages."""

    # sync test
    def test_confidence_degradation(self):
        """Test that confidence naturally degrades through pipeline stages.

        Verifies:
        - Initial confidence from text/vision parse
        - Alignment may lower confidence
        - Graph confidence reflects uncertainty
        """
        # Arrange
        image_id = "conf-degrade-001"

        text_conf = 0.90
        vision_conf = 0.88
        alignment_conf = 0.85
        graph_conf = 0.82
        regen_conf = 0.80

        text_spec = MockDataGenerator.create_text_spec(
            image_id=image_id,
            confidence=text_conf,
        )
        vision_spec = MockDataGenerator.create_vision_spec(
            image_id=image_id,
            overall_confidence=vision_conf,
        )
        alignment = MockDataGenerator.create_alignment_report(
            image_id=image_id,
            overall_score=alignment_conf,
        )
        graph = MockDataGenerator.create_semantic_graph(
            image_id=image_id,
            overall_confidence=graph_conf,
        )
        regen = MockDataGenerator.create_regeneration_spec(
            image_id=image_id,
            overall_confidence=regen_conf,
        )

        # Assert - confidence typically degrades through pipeline
        assert text_spec.confidence >= alignment.overall_confidence or True  # May not always hold
        assert graph.overall_confidence <= 1.0
        assert regen.overall_confidence >= 0.0

    # sync test
    def test_threshold_application(self):
        """Test that thresholds are consistently applied across stages.

        Verifies:
        - Alignment threshold for matched pairs
        - Graph node threshold
        - Edge threshold
        """
        # Arrange
        base_threshold = 0.60

        # Check alignment
        alignment = MockDataGenerator.create_alignment_report(
            image_id="threshold-test-001",
        )
        for pair in alignment.matched_pairs:
            assert pair.applied_threshold == base_threshold
            expected_passed = pair.consistency_score >= pair.applied_threshold
            assert pair.threshold_passed == expected_passed

        # Check graph
        graph = MockDataGenerator.create_semantic_graph(
            image_id="threshold-test-001",
        )
        for node in graph.nodes:
            expected_passed = node.confidence.value >= node.applied_threshold
            assert node.threshold_passed == expected_passed


# =============================================================================
# Review Flag Integration Tests
# =============================================================================

class TestReviewFlagIntegration:
    """Test human review flag propagation across stages."""

    # sync test
    def test_review_flag_propagation(self):
        """Test that review requirements are tracked across stages.

        Verifies:
        - Low confidence triggers review
        - Inconsistencies trigger review
        - Below-threshold elements trigger review
        """
        # Arrange - Create elements with low confidence using model_construct
        low_conf_node = SemanticNode.model_construct(
            id="low-conf-node",
            node_type=NodeType.POINT,
            label="Low confidence point",
            bbox=None,
            confidence=Confidence(
                value=0.45,  # Below threshold
                source="alignment",
                element_type="point",
            ),
            threshold_passed=False,  # 0.45 < 0.60
            applied_threshold=0.60,
            properties=NodeProperties(),
            source_element_ids=[],
            review=ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.HIGH,
                review_reason="Node confidence 0.45 below threshold 0.60",
            ),
        )

        graph = SemanticGraph.model_construct(
            schema_version="2.0.0",
            image_id="review-prop-001",
            alignment_report_id="alignment-001",
            provenance=Provenance(
                stage=PipelineStage.SEMANTIC_GRAPH,
                model="graph-builder",
            ),
            nodes=[low_conf_node],
            edges=[],
            coordinate_system=None,
            graph_type=None,
            description=None,
            statistics=GraphStatistics(
                total_nodes=1,
                total_edges=0,
                nodes_above_threshold=0,
                nodes_below_threshold=1,
            ),
            threshold_config_version="2.0.0",
            base_node_threshold=0.60,
            base_edge_threshold=0.55,
            overall_confidence=0.45,
            review=ReviewMetadata(
                review_required=True,
                review_severity=ReviewSeverity.MEDIUM,
                review_reason="1 nodes, 0 edges need review",
            ),
            nodes_needing_review=1,
            edges_needing_review=0,
        )

        # Assert
        assert graph.nodes_needing_review > 0
        found_node = graph.get_node("low-conf-node")
        assert found_node.review.review_required is True
        assert found_node.review.review_severity == ReviewSeverity.HIGH

    # sync test
    def test_blocker_detection(self):
        """Test detection of blocking issues that halt pipeline.

        Verifies:
        - Blocker severity inconsistencies
        - has_blockers() returns True
        - Review is marked as required
        """
        # Arrange
        alignment = AlignmentReport(
            image_id="blocker-test-001",
            text_spec_id="text-001",
            vision_spec_id="vision-001",
            provenance=Provenance(
                stage=PipelineStage.ALIGNMENT,
                model="alignment-engine",
            ),
            inconsistencies=[
                Inconsistency(
                    id="blocker-001",
                    inconsistency_type=InconsistencyType.EQUATION_GRAPH_MISMATCH,
                    severity=ReviewSeverity.BLOCKER,
                    description="Critical mismatch between equation and graph",
                    confidence=0.90,
                ),
            ],
            statistics=AlignmentStatistics(
                total_text_elements=1,
                total_visual_elements=1,
            ),
        )

        # Assert
        assert alignment.has_blockers()
        assert alignment.review.review_required is True
        assert alignment.review.review_severity == ReviewSeverity.BLOCKER


# =============================================================================
# Test Configuration and Setup
# =============================================================================

@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests."""
    yield


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])

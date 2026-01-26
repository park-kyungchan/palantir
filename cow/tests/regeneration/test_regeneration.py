"""
Tests for Stage F (Regeneration) modules.

Tests LaTeXGenerator, SVGGenerator, and DeltaComparer functionality.
"""

import pytest
from pathlib import Path

from mathpix_pipeline.regeneration import (
    LaTeXGenerator,
    LaTeXConfig,
    SVGGenerator,
    SVGConfig,
    DeltaComparer,
    DeltaConfig,
    create_latex_generator,
    create_svg_generator,
    create_delta_comparer,
)
from mathpix_pipeline.regeneration.exceptions import (
    LaTeXGenerationError,
    SVGGenerationError,
    DeltaComparisonError,
)
from mathpix_pipeline.schemas.regeneration import (
    OutputFormat,
    DeltaType,
)
from mathpix_pipeline.schemas.semantic_graph import (
    SemanticGraph,
    SemanticNode,
    SemanticEdge,
    NodeType,
    EdgeType,
    NodeProperties,
)
from mathpix_pipeline.schemas import BBox, Provenance, PipelineStage


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_point_node():
    """Sample point node for testing."""
    return SemanticNode(
        id="point-A",
        node_type=NodeType.POINT,
        label="A",
        properties=NodeProperties(
            coordinates={"x": 2.0, "y": 3.0},
            point_label="A",
        ),
        bbox=BBox(x=200, y=300, width=20, height=20),
        confidence=0.92,
    )


@pytest.fixture
def sample_line_node():
    """Sample line node for testing."""
    return SemanticNode(
        id="line-001",
        node_type=NodeType.LINE,
        label="Line y = 2x + 1",
        properties=NodeProperties(
            slope=2.0,
            y_intercept=1.0,
            equation="y = 2x + 1",
        ),
        bbox=BBox(x=100, y=100, width=300, height=200),
        confidence=0.88,
    )


@pytest.fixture
def sample_equation_node():
    """Sample equation node for testing."""
    return SemanticNode(
        id="eq-001",
        node_type=NodeType.EQUATION,
        label="y = x^2 + 2x + 1",
        properties=NodeProperties(
            latex="y = x^2 + 2x + 1",
            equation="y = x^2 + 2x + 1",
        ),
        bbox=BBox(x=100, y=50, width=200, height=40),
        confidence=0.95,
    )


@pytest.fixture
def sample_graph(sample_point_node, sample_line_node, sample_equation_node):
    """Sample semantic graph for testing."""
    return SemanticGraph(
        image_id="test-image-001",
        provenance=Provenance(
            stage=PipelineStage.SEMANTIC_GRAPH,
            model="graph-builder-v1",
            processing_time_ms=150.0,
        ),
        nodes=[sample_point_node, sample_line_node, sample_equation_node],
        edges=[],
    )


# =============================================================================
# LaTeXGenerator Tests
# =============================================================================

class TestLaTeXGeneratorInit:
    """Test LaTeXGenerator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        generator = LaTeXGenerator()

        assert generator.config is not None
        assert generator.config.math_mode == "display"
        assert generator.stats["equations_generated"] == 0

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = LaTeXConfig(
            math_mode="inline",
            include_comments=True,
            pretty_print=False,
        )
        generator = LaTeXGenerator(config=config)

        assert generator.config.math_mode == "inline"
        assert generator.config.include_comments is True
        assert generator.config.pretty_print is False

    def test_factory_function(self):
        """Test factory function."""
        generator = create_latex_generator(math_mode="equation")

        assert isinstance(generator, LaTeXGenerator)
        assert generator.config.math_mode == "equation"


class TestLaTeXGeneratorEquations:
    """Test equation generation."""

    def test_generate_equation_with_latex(self, sample_equation_node):
        """Test generating equation from node with LaTeX."""
        generator = LaTeXGenerator()

        result = generator.generate_equation(sample_equation_node)

        assert "y = x^2 + 2x + 1" in result
        assert generator.stats["equations_generated"] == 1

    def test_generate_equation_inline_mode(self, sample_equation_node):
        """Test generating equation in inline mode."""
        config = LaTeXConfig(math_mode="inline")
        generator = LaTeXGenerator(config=config)

        result = generator.generate_equation(sample_equation_node)

        assert result.startswith("$")
        assert result.endswith("$")

    def test_generate_equation_display_mode(self, sample_equation_node):
        """Test generating equation in display mode."""
        config = LaTeXConfig(math_mode="display")
        generator = LaTeXGenerator(config=config)

        result = generator.generate_equation(sample_equation_node)

        assert result.startswith(r"\[")
        assert result.endswith(r"\]")

    def test_generate_equation_no_latex_raises(self):
        """Test generating equation without LaTeX raises error."""
        node = SemanticNode(
            id="bad-node",
            node_type=NodeType.EQUATION,
            label="Bad",
            properties=NodeProperties(),
            confidence=0.5,
        )
        generator = LaTeXGenerator()

        with pytest.raises(LaTeXGenerationError):
            generator.generate_equation(node)


class TestLaTeXGeneratorGraphs:
    """Test graph generation."""

    def test_generate_graph_basic(self, sample_graph):
        """Test generating LaTeX from graph."""
        generator = LaTeXGenerator()

        result = generator.generate_graph(
            sample_graph.nodes,
            sample_graph.edges,
        )

        assert "y = x^2 + 2x + 1" in result
        assert "y = 2x + 1" in result
        assert generator.stats["graphs_generated"] == 1

    def test_generate_graph_with_comments(self, sample_graph):
        """Test generating graph with comments."""
        config = LaTeXConfig(include_comments=True)
        generator = LaTeXGenerator(config=config)

        result = generator.generate_graph(
            sample_graph.nodes,
            sample_graph.edges,
        )

        assert "%" in result
        assert "Nodes:" in result

    def test_generate_graph_pretty_print(self, sample_graph):
        """Test pretty print formatting."""
        config = LaTeXConfig(pretty_print=True)
        generator = LaTeXGenerator(config=config)

        result = generator.generate_graph(
            sample_graph.nodes,
            sample_graph.edges,
        )

        assert "\n" in result

    def test_generate_output(self, sample_graph):
        """Test generating complete output."""
        generator = LaTeXGenerator()

        output = generator.generate_output(sample_graph)

        assert output.format == OutputFormat.LATEX
        assert output.content is not None
        assert output.confidence > 0
        assert output.element_count == len(sample_graph.nodes)


# =============================================================================
# SVGGenerator Tests
# =============================================================================

class TestSVGGeneratorInit:
    """Test SVGGenerator initialization."""

    def test_default_init(self):
        """Test default initialization."""
        generator = SVGGenerator()

        assert generator.config is not None
        assert generator.config.width == 800
        assert generator.config.height == 600
        assert generator.stats["svgs_generated"] == 0

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = SVGConfig(
            width=1024,
            height=768,
            show_grid=True,
            show_axes=False,
        )
        generator = SVGGenerator(config=config)

        assert generator.config.width == 1024
        assert generator.config.height == 768
        assert generator.config.show_grid is True
        assert generator.config.show_axes is False

    def test_factory_function(self):
        """Test factory function."""
        generator = create_svg_generator(width=640, height=480)

        assert isinstance(generator, SVGGenerator)
        assert generator.config.width == 640


class TestSVGGeneratorCoordinates:
    """Test coordinate transformation."""

    def test_transform_cartesian(self):
        """Test Cartesian coordinate transformation."""
        config = SVGConfig(coordinate_transform="cartesian")
        generator = SVGGenerator(config=config)

        svg_x, svg_y = generator._transform_coords(0, 0)

        assert svg_x == config.width / 2
        assert svg_y == config.height / 2

    def test_inverse_transform_cartesian(self):
        """Test inverse Cartesian transformation."""
        config = SVGConfig(coordinate_transform="cartesian")
        generator = SVGGenerator(config=config)

        x, y = generator._inverse_transform_coords(400, 300)

        assert x == 0
        assert y == 0

    def test_transform_svg_native(self):
        """Test SVG native coordinate transformation."""
        config = SVGConfig(coordinate_transform="svg")
        generator = SVGGenerator(config=config)

        svg_x, svg_y = generator._transform_coords(0, 0)

        assert svg_x == config.margin
        assert svg_y == config.margin


class TestSVGGeneratorRendering:
    """Test SVG rendering."""

    def test_generate_svg_basic(self, sample_graph):
        """Test generating SVG from graph."""
        generator = SVGGenerator()

        result = generator.generate_svg(sample_graph)

        assert "<svg" in result
        assert "xmlns" in result
        assert generator.stats["svgs_generated"] == 1

    def test_generate_svg_with_grid(self, sample_graph):
        """Test generating SVG with grid."""
        config = SVGConfig(show_grid=True)
        generator = SVGGenerator(config=config)

        result = generator.generate_svg(sample_graph)

        assert 'class="grid"' in result

    def test_generate_svg_with_axes(self, sample_graph):
        """Test generating SVG with axes."""
        config = SVGConfig(show_axes=True)
        generator = SVGGenerator(config=config)

        result = generator.generate_svg(sample_graph)

        assert 'class="axes"' in result

    def test_generate_tikz(self, sample_graph):
        """Test generating TikZ code."""
        generator = SVGGenerator()

        result = generator.generate_tikz(sample_graph)

        assert r"\begin{tikzpicture}" in result
        assert r"\end{tikzpicture}" in result
        assert generator.stats["tikz_generated"] == 1

    def test_generate_output_svg(self, sample_graph):
        """Test generating SVG output."""
        generator = SVGGenerator()

        output = generator.generate_output(sample_graph, OutputFormat.SVG)

        assert output.format == OutputFormat.SVG
        assert output.content is not None
        assert "<svg" in output.content

    def test_generate_output_tikz(self, sample_graph):
        """Test generating TikZ output."""
        generator = SVGGenerator()

        output = generator.generate_output(sample_graph, OutputFormat.TIKZ)

        assert output.format == OutputFormat.TIKZ
        assert r"\begin{tikzpicture}" in output.content


# =============================================================================
# DeltaComparer Tests
# =============================================================================

class TestDeltaComparerInit:
    """Test DeltaComparer initialization."""

    def test_default_init(self):
        """Test default initialization."""
        comparer = DeltaComparer()

        assert comparer.config is not None
        assert comparer.config.exact_threshold == 1.0
        assert comparer.stats["comparisons_performed"] == 0

    def test_init_with_config(self):
        """Test initialization with custom config."""
        config = DeltaConfig(
            similar_threshold=0.85,
            compare_positions=False,
        )
        comparer = DeltaComparer(config=config)

        assert comparer.config.similar_threshold == 0.85
        assert comparer.config.compare_positions is False

    def test_factory_function(self):
        """Test factory function."""
        comparer = create_delta_comparer(similar_threshold=0.75)

        assert isinstance(comparer, DeltaComparer)
        assert comparer.config.similar_threshold == 0.75


class TestDeltaComparerSimilarity:
    """Test similarity calculation."""

    def test_calculate_similarity_identical(self):
        """Test similarity of identical strings."""
        comparer = DeltaComparer()

        similarity = comparer._calculate_similarity("test", "test")

        assert similarity == 1.0

    def test_calculate_similarity_different(self):
        """Test similarity of different strings."""
        comparer = DeltaComparer()

        similarity = comparer._calculate_similarity("abc", "xyz")

        assert similarity < 0.5

    def test_calculate_similarity_empty(self):
        """Test similarity of empty strings."""
        comparer = DeltaComparer()

        similarity = comparer._calculate_similarity("", "")

        assert similarity == 1.0

    def test_normalize_text(self):
        """Test text normalization."""
        config = DeltaConfig(ignore_whitespace=True)
        comparer = DeltaComparer(config=config)

        normalized = comparer._normalize_text("  hello   world  ")

        assert normalized == "hello world"


class TestDeltaComparerComparison:
    """Test graph comparison."""

    def test_compare_identical_graphs(self, sample_graph):
        """Test comparing identical graphs."""
        comparer = DeltaComparer()

        report = comparer.compare(sample_graph, sample_graph)

        assert report.similarity_score >= 0.9
        assert report.unchanged_count > 0
        assert len(report.added_elements) == 0
        assert len(report.removed_elements) == 0

    def test_compare_different_graphs(self, sample_graph):
        """Test comparing different graphs."""
        # Create modified graph
        modified_graph = SemanticGraph(
            image_id="test-image-002",
            provenance=sample_graph.provenance,
            nodes=sample_graph.nodes[:2],  # Remove one node
            edges=[],
        )

        comparer = DeltaComparer()
        report = comparer.compare(sample_graph, modified_graph)

        assert report.similarity_score < 1.0
        assert len(report.removed_elements) > 0

    def test_compare_with_original_latex(self, sample_graph):
        """Test comparing with original LaTeX."""
        comparer = DeltaComparer()

        report = comparer.compare_with_original(
            sample_graph,
            original_latex="y = x^2 + 2x + 1",
        )

        assert report.similarity_score > 0.5

    def test_compute_similarity_matrix(self, sample_graph):
        """Test computing similarity matrix."""
        comparer = DeltaComparer()

        graphs = [sample_graph, sample_graph]
        matrix = comparer.compute_similarity_matrix(graphs)

        assert len(matrix) == 2
        assert len(matrix[0]) == 2
        assert matrix[0][0] == 1.0
        assert matrix[0][1] >= 0.9


class TestDeltaComparerStatistics:
    """Test statistics tracking."""

    def test_stats_updated_on_comparison(self, sample_graph):
        """Test that stats are updated after comparison."""
        comparer = DeltaComparer()
        initial_count = comparer.stats["comparisons_performed"]

        comparer.compare(sample_graph, sample_graph)

        assert comparer.stats["comparisons_performed"] == initial_count + 1
        assert comparer.stats["elements_compared"] > 0

    def test_stats_track_changes(self, sample_graph):
        """Test that stats track changes found."""
        modified_graph = SemanticGraph(
            image_id="test-image-002",
            provenance=sample_graph.provenance,
            nodes=sample_graph.nodes[:1],
            edges=[],
        )

        comparer = DeltaComparer()
        comparer.compare(sample_graph, modified_graph)

        assert comparer.stats["removed_found"] > 0

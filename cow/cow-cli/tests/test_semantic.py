"""
Tests for semantic schemas (Layout/Content separation).
"""
import pytest
from datetime import datetime
import json

from cow_cli.semantic import (
    Region,
    DataFormat,
    DataObject,
    PageInfo,
    ElementType,
    ElementSubtype,
    LayoutElement,
    LayoutMetadata,
    LayoutData,
    QualityMetrics,
    ContentElement,
    QualitySummary,
    ContentMetadata,
    ContentData,
    SeparatedDocument,
)


class TestRegion:
    """Tests for Region bounding box."""

    def test_basic_region(self):
        """Test basic region creation."""
        region = Region(top_left_x=10, top_left_y=20, width=100, height=50)

        assert region.top_left_x == 10
        assert region.top_left_y == 20
        assert region.width == 100
        assert region.height == 50

    def test_computed_properties(self):
        """Test computed properties."""
        region = Region(top_left_x=10, top_left_y=20, width=100, height=50)

        assert region.bottom_right_x == 110
        assert region.bottom_right_y == 70
        assert region.area == 5000
        assert region.center == (60.0, 45.0)

    def test_region_validation(self):
        """Test region validation."""
        # Width must be >= 1
        with pytest.raises(ValueError):
            Region(top_left_x=0, top_left_y=0, width=0, height=10)

        # Negative coordinates not allowed
        with pytest.raises(ValueError):
            Region(top_left_x=-1, top_left_y=0, width=10, height=10)


class TestDataObject:
    """Tests for DataObject."""

    def test_data_formats(self):
        """Test various data formats."""
        latex = DataObject(type=DataFormat.LATEX, value="x^2")
        svg = DataObject(type=DataFormat.SVG, value="<svg>...</svg>")

        assert latex.type == DataFormat.LATEX
        assert svg.type == DataFormat.SVG


class TestLayoutElement:
    """Tests for LayoutElement."""

    def test_basic_element(self):
        """Test basic layout element."""
        elem = LayoutElement(
            id="elem-1",
            type=ElementType.TEXT,
        )

        assert elem.id == "elem-1"
        assert elem.type == ElementType.TEXT
        assert elem.region is None
        assert elem.children_ids == []

    def test_full_element(self):
        """Test fully populated element."""
        region = Region(top_left_x=0, top_left_y=0, width=100, height=50)
        elem = LayoutElement(
            id="elem-1",
            type=ElementType.MATH,
            subtype=ElementSubtype.CHEMISTRY,
            region=region,
            cnt=[[0, 0], [100, 0], [100, 50], [0, 50]],
            column=0,
            line=1,
            font_size=12,
            parent_id="container-1",
            children_ids=["child-1", "child-2"],
        )

        assert elem.subtype == ElementSubtype.CHEMISTRY
        assert elem.font_size == 12
        assert len(elem.children_ids) == 2

    def test_all_element_types(self):
        """Test all 36 element types are accessible."""
        # Sample of element types
        types = [
            ElementType.TEXT,
            ElementType.MATH,
            ElementType.TABLE,
            ElementType.DIAGRAM,
            ElementType.CHART,
            ElementType.CHART_INFO,
            ElementType.TITLE,
            ElementType.SECTION_HEADER,
            ElementType.MULTIPLE_CHOICE_OPTION,
        ]

        for elem_type in types:
            elem = LayoutElement(id="test", type=elem_type)
            assert elem.type == elem_type


class TestLayoutData:
    """Tests for LayoutData."""

    @pytest.fixture
    def sample_elements(self):
        """Create sample layout elements."""
        return [
            LayoutElement(id="parent-1", type=ElementType.COLUMN),
            LayoutElement(
                id="child-1",
                type=ElementType.TEXT,
                parent_id="parent-1",
            ),
            LayoutElement(
                id="child-2",
                type=ElementType.MATH,
                parent_id="parent-1",
            ),
        ]

    def test_get_element_by_id(self, sample_elements):
        """Test finding element by ID."""
        layout = LayoutData(elements=sample_elements)

        found = layout.get_element_by_id("child-1")
        assert found is not None
        assert found.type == ElementType.TEXT

        not_found = layout.get_element_by_id("nonexistent")
        assert not_found is None

    def test_get_elements_by_type(self, sample_elements):
        """Test filtering by type."""
        layout = LayoutData(elements=sample_elements)

        text_elements = layout.get_elements_by_type(ElementType.TEXT)
        assert len(text_elements) == 1

    def test_get_children(self, sample_elements):
        """Test getting child elements."""
        layout = LayoutData(elements=sample_elements)

        children = layout.get_children("parent-1")
        assert len(children) == 2


class TestQualityMetrics:
    """Tests for QualityMetrics."""

    def test_high_confidence(self):
        """Test high confidence detection."""
        high = QualityMetrics(confidence=0.98)
        low = QualityMetrics(confidence=0.70)

        assert high.is_high_confidence is True
        assert low.is_high_confidence is False

    def test_needs_review(self):
        """Test review threshold."""
        ok = QualityMetrics(confidence=0.80)
        review = QualityMetrics(confidence=0.60)

        assert ok.needs_review is False
        assert review.needs_review is True

    def test_uses_confidence_rate_fallback(self):
        """Test confidence_rate fallback."""
        metrics = QualityMetrics(confidence_rate=0.90)

        assert metrics.needs_review is False


class TestContentElement:
    """Tests for ContentElement."""

    def test_basic_content(self):
        """Test basic content element."""
        elem = ContentElement(
            id="elem-1",
            text="Hello world",
        )

        assert elem.id == "elem-1"
        assert elem.text == "Hello world"
        assert elem.quality.needs_review is True  # No confidence = needs review

    def test_content_with_quality(self):
        """Test content with quality metrics."""
        elem = ContentElement(
            id="elem-1",
            latex="x^2 + y^2 = z^2",
            quality=QualityMetrics(confidence=0.95),
        )

        assert elem.quality.is_high_confidence is True

    def test_content_with_data(self):
        """Test content with multi-format data."""
        elem = ContentElement(
            id="elem-1",
            data=[
                DataObject(type=DataFormat.LATEX, value="x^2"),
                DataObject(type=DataFormat.MATHML, value="<math>...</math>"),
            ],
        )

        assert len(elem.data) == 2


class TestContentData:
    """Tests for ContentData."""

    @pytest.fixture
    def sample_content(self):
        """Create sample content elements."""
        return ContentData(
            elements=[
                ContentElement(
                    id="elem-1",
                    text="High confidence",
                    quality=QualityMetrics(confidence=0.98),
                ),
                ContentElement(
                    id="elem-2",
                    text="Medium confidence",
                    quality=QualityMetrics(confidence=0.80),
                ),
                ContentElement(
                    id="elem-3",
                    text="Low confidence",
                    quality=QualityMetrics(confidence=0.50),
                ),
            ]
        )

    def test_compute_quality_summary(self, sample_content):
        """Test quality summary computation."""
        sample_content.compute_quality_summary()
        summary = sample_content.quality_summary

        assert summary.total_elements == 3
        assert summary.high_confidence_count == 1
        assert summary.low_confidence_count == 1
        assert summary.needs_review_count == 1
        assert summary.min_confidence == 0.50

    def test_get_elements_needing_review(self, sample_content):
        """Test getting elements needing review."""
        needs_review = sample_content.get_elements_needing_review()

        assert len(needs_review) == 1
        assert needs_review[0].id == "elem-3"


class TestSeparatedDocument:
    """Tests for SeparatedDocument."""

    @pytest.fixture
    def sample_document(self):
        """Create sample separated document."""
        layout = LayoutData(
            elements=[
                LayoutElement(id="elem-1", type=ElementType.TEXT),
                LayoutElement(id="elem-2", type=ElementType.MATH),
            ]
        )
        content = ContentData(
            elements=[
                ContentElement(id="elem-1", layout_ref="elem-1", text="Hello"),
                ContentElement(id="elem-2", layout_ref="elem-2", latex="x^2"),
            ]
        )
        return SeparatedDocument(
            image_path="/test/image.png",
            layout=layout,
            content=content,
        )

    def test_validate_references_valid(self, sample_document):
        """Test reference validation with valid references."""
        errors = sample_document.validate_references()
        assert len(errors) == 0

    def test_validate_references_invalid(self):
        """Test reference validation with invalid references."""
        doc = SeparatedDocument(
            image_path="/test.png",
            layout=LayoutData(
                elements=[LayoutElement(id="elem-1", type=ElementType.TEXT)]
            ),
            content=ContentData(
                elements=[
                    ContentElement(
                        id="content-1",
                        layout_ref="nonexistent",  # Invalid reference
                    )
                ]
            ),
        )

        errors = doc.validate_references()
        assert len(errors) == 1
        assert "nonexistent" in errors[0]

    def test_json_serialization(self, sample_document):
        """Test JSON serialization/deserialization."""
        json_str = sample_document.model_dump_json()
        data = json.loads(json_str)

        assert data["image_path"] == "/test/image.png"
        assert len(data["layout"]["elements"]) == 2
        assert len(data["content"]["elements"]) == 2

    def test_round_trip(self, sample_document):
        """Test full round-trip serialization."""
        json_str = sample_document.model_dump_json()
        restored = SeparatedDocument.model_validate_json(json_str)

        assert restored.image_path == sample_document.image_path
        assert len(restored.layout.elements) == len(sample_document.layout.elements)

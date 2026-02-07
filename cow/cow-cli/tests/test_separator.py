"""
Tests for Layout/Content Separator.
"""
import pytest
from pathlib import Path
import tempfile
import json

from cow_cli.semantic import (
    LayoutContentSeparator,
    separate_mathpix_output,
    SeparationError,
    ElementType,
    DataFormat,
)


class TestLayoutContentSeparator:
    """Tests for LayoutContentSeparator."""

    @pytest.fixture
    def separator(self):
        """Create default separator."""
        return LayoutContentSeparator()

    @pytest.fixture
    def sample_word_data(self):
        """Create sample Mathpix word_data output."""
        return {
            "request_id": "test-request-123",
            "image_width": 800,
            "image_height": 600,
            "word_data": [
                {
                    "type": "text",
                    "text": "Hello world",
                    "cnt": [[10, 10], [100, 10], [100, 30], [10, 30]],
                    "confidence": 0.95,
                    "confidence_rate": 0.92,
                    "is_printed": True,
                },
                {
                    "type": "math",
                    "text": "$x^2 + y^2 = z^2$",
                    "latex": "x^2 + y^2 = z^2",
                    "cnt": [[10, 50], [200, 50], [200, 100], [10, 100]],
                    "confidence": 0.88,
                    "confidence_rate": 0.85,
                    "data": [
                        {"type": "latex", "value": "x^2 + y^2 = z^2"},
                        {"type": "asciimath", "value": "x^2 + y^2 = z^2"},
                    ],
                },
                {
                    "type": "diagram",
                    "subtype": "triangle",
                    "text": "Triangle ABC",
                    "cnt": [[10, 120], [300, 120], [300, 300], [10, 300]],
                    "confidence": 0.70,  # Low confidence - needs review
                    "column": 0,
                    "line": 2,
                    "font_size": 12,
                },
            ],
        }

    def test_separate_basic(self, separator, sample_word_data):
        """Test basic separation."""
        doc = separator.separate(sample_word_data, image_path="/test/image.png")

        assert doc.image_path == "/test/image.png"
        assert len(doc.layout.elements) == 3
        assert len(doc.content.elements) == 3

    def test_layout_elements(self, separator, sample_word_data):
        """Test layout elements have correct fields."""
        doc = separator.separate(sample_word_data)

        # Check first element (text)
        layout_elem = doc.layout.elements[0]
        assert layout_elem.type == ElementType.TEXT
        assert layout_elem.region is not None
        assert layout_elem.region.width == 90
        assert layout_elem.region.height == 20

        # Check third element (diagram with subtype)
        diagram_elem = doc.layout.elements[2]
        assert diagram_elem.type == ElementType.DIAGRAM
        assert diagram_elem.subtype is not None
        assert diagram_elem.column == 0
        assert diagram_elem.line == 2
        assert diagram_elem.font_size == 12

    def test_content_elements(self, separator, sample_word_data):
        """Test content elements have correct fields."""
        doc = separator.separate(sample_word_data)

        # Check first element (text)
        content_elem = doc.content.elements[0]
        assert content_elem.text == "Hello world"
        assert content_elem.quality.confidence == 0.95
        assert content_elem.is_printed is True

        # Check second element (math with data)
        math_elem = doc.content.elements[1]
        assert math_elem.latex == "x^2 + y^2 = z^2"
        assert len(math_elem.data) == 2
        assert math_elem.data[0].type == DataFormat.LATEX

    def test_page_info(self, separator, sample_word_data):
        """Test page info extraction."""
        doc = separator.separate(sample_word_data)

        assert doc.layout.page.width == 800
        assert doc.layout.page.height == 600

    def test_quality_summary(self, separator, sample_word_data):
        """Test quality summary computation."""
        doc = separator.separate(sample_word_data)

        summary = doc.content.quality_summary
        assert summary.total_elements == 3
        assert summary.high_confidence_count == 1  # Only 0.95 >= 0.95
        assert summary.needs_review_count == 1  # 0.70 < 0.75

    def test_validate_separation(self, separator, sample_word_data):
        """Test validation passes for good separation."""
        doc = separator.separate(sample_word_data)

        errors = separator.validate_separation(doc)
        assert len(errors) == 0

    def test_strict_mode(self, sample_word_data):
        """Test strict mode validation."""
        separator = LayoutContentSeparator(strict=True)

        # Should not raise for valid data
        doc = separator.separate(sample_word_data)
        assert doc is not None

    def test_cnt_to_region(self, separator):
        """Test contour to region conversion."""
        cnt = [[10, 20], [110, 20], [110, 70], [10, 70]]
        region = separator._cnt_to_region(cnt)

        assert region.top_left_x == 10
        assert region.top_left_y == 20
        assert region.width == 100
        assert region.height == 50

    def test_cnt_to_region_empty(self, separator):
        """Test empty contour returns None."""
        assert separator._cnt_to_region([]) is None
        assert separator._cnt_to_region(None) is None

    def test_empty_word_data(self, separator):
        """Test handling empty word_data."""
        doc = separator.separate({"request_id": "test"})

        assert len(doc.layout.elements) == 0
        assert len(doc.content.elements) == 0

    def test_unknown_element_type(self, separator):
        """Test unknown element type defaults to TEXT."""
        data = {
            "word_data": [
                {"type": "unknown_type", "text": "test"},
            ]
        }
        doc = separator.separate(data)

        assert doc.layout.elements[0].type == ElementType.TEXT


class TestSeparatorSave:
    """Tests for save functionality."""

    @pytest.fixture
    def separator(self):
        return LayoutContentSeparator()

    @pytest.fixture
    def sample_doc(self, separator):
        data = {
            "word_data": [
                {"type": "text", "text": "Test", "cnt": [[0, 0], [10, 10]]},
            ]
        }
        return separator.separate(data, image_path="test.png")

    def test_save_layout(self, separator, sample_doc):
        """Test saving layout to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "layout.json"
            separator.save_layout(sample_doc.layout, path)

            assert path.exists()

            with open(path) as f:
                data = json.load(f)
                assert "elements" in data
                assert len(data["elements"]) == 1

    def test_save_content(self, separator, sample_doc):
        """Test saving content to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "content.json"
            separator.save_content(sample_doc.content, path)

            assert path.exists()

            with open(path) as f:
                data = json.load(f)
                assert "elements" in data

    def test_save_document(self, separator, sample_doc):
        """Test saving complete document."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            saved = separator.save_document(sample_doc, output_dir)

            assert "layout" in saved
            assert "content" in saved
            assert "combined" in saved

            assert saved["layout"].exists()
            assert saved["content"].exists()
            assert saved["combined"].exists()


class TestSeparateMathpixOutput:
    """Tests for convenience function."""

    def test_separate_mathpix_output(self):
        """Test convenience function."""
        data = {
            "request_id": "test",
            "word_data": [
                {"type": "text", "text": "Hello"},
            ],
        }

        doc = separate_mathpix_output(data, image_path="test.png")

        assert doc.image_path == "test.png"
        assert len(doc.layout.elements) == 1

    def test_separate_with_line_data(self):
        """Test separation with line_data instead of word_data."""
        data = {
            "request_id": "test",
            "line_data": [
                {
                    "id": "line-1",
                    "type": "text",
                    "text": "Line text",
                    "cnt": [[0, 0], [100, 100]],
                },
            ],
        }

        doc = separate_mathpix_output(data)

        assert len(doc.layout.elements) == 1
        assert doc.layout.elements[0].id == "line-1"


class TestIdConsistency:
    """Tests for ID consistency between layout and content."""

    def test_ids_match(self):
        """Test that layout and content element IDs match."""
        data = {
            "word_data": [
                {"type": "text", "text": "A"},
                {"type": "math", "latex": "B"},
                {"type": "diagram", "text": "C"},
            ]
        }

        doc = separate_mathpix_output(data)

        layout_ids = [e.id for e in doc.layout.elements]
        content_ids = [e.id for e in doc.content.elements]

        assert layout_ids == content_ids

    def test_layout_ref_links_to_layout(self):
        """Test that content elements reference correct layout elements."""
        data = {
            "word_data": [
                {"type": "text", "text": "Test"},
            ]
        }

        doc = separate_mathpix_output(data)

        content_elem = doc.content.elements[0]
        layout_elem = doc.layout.get_element_by_id(content_elem.layout_ref)

        assert layout_elem is not None
        assert layout_elem.id == content_elem.id


# =============================================================================
# EDGE CASE TESTS (EC-01 ~ EC-05)
# =============================================================================


class TestEdgeCaseEmptyData:
    """EC-01: Empty and minimal data edge cases."""

    def test_completely_empty_input(self):
        """Test separation with completely empty dict."""
        doc = separate_mathpix_output({})

        assert len(doc.layout.elements) == 0
        assert len(doc.content.elements) == 0
        assert doc.layout.page.width == 0
        assert doc.layout.page.height == 0

    def test_empty_word_data_array(self):
        """Test separation with empty word_data array."""
        data = {"request_id": "test-123", "word_data": []}
        doc = separate_mathpix_output(data)

        assert len(doc.layout.elements) == 0
        assert doc.request_id == "test-123"

    def test_null_word_data(self):
        """Test separation when word_data is None."""
        data = {"request_id": "test", "word_data": None}
        doc = separate_mathpix_output(data)

        assert len(doc.layout.elements) == 0

    def test_single_element_minimal(self):
        """Test minimal single element."""
        data = {"word_data": [{"type": "text"}]}
        doc = separate_mathpix_output(data)

        assert len(doc.layout.elements) == 1
        assert doc.layout.elements[0].type == ElementType.TEXT


class TestEdgeCaseMissingFields:
    """EC-02: Missing and null field edge cases."""

    def test_missing_type_defaults_to_text(self):
        """Test element with missing type defaults to TEXT."""
        data = {"word_data": [{"text": "Hello"}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].type == ElementType.TEXT

    def test_missing_text_content(self):
        """Test element with missing text fields."""
        data = {"word_data": [{"type": "math", "latex": "x^2"}]}
        doc = separate_mathpix_output(data)

        content = doc.content.elements[0]
        assert content.text is None
        assert content.latex == "x^2"

    def test_missing_confidence(self):
        """Test element with missing confidence metrics."""
        data = {"word_data": [{"type": "text", "text": "Test"}]}
        doc = separate_mathpix_output(data)

        quality = doc.content.elements[0].quality
        assert quality.confidence is None
        assert quality.confidence_rate is None

    def test_null_children_ids(self):
        """Test element with null children_ids."""
        data = {"word_data": [{"type": "text", "children_ids": None}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].children_ids == []

    def test_missing_cnt_no_region(self):
        """Test element with missing cnt has no region."""
        data = {"word_data": [{"type": "text", "text": "No bbox"}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].region is None
        assert doc.layout.elements[0].cnt is None


class TestEdgeCaseInvalidCnt:
    """EC-03: Invalid contour coordinate edge cases."""

    def test_cnt_single_point(self):
        """Test cnt with single point returns None region."""
        data = {"word_data": [{"type": "text", "cnt": [[10, 20]]}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].region is None

    def test_cnt_two_points(self):
        """Test cnt with two points creates valid region."""
        data = {"word_data": [{"type": "text", "cnt": [[0, 0], [100, 50]]}]}
        doc = separate_mathpix_output(data)

        region = doc.layout.elements[0].region
        assert region is not None
        assert region.width == 100
        assert region.height == 50

    def test_cnt_negative_coordinates_clamped(self):
        """Test cnt with negative coordinates are clamped to 0."""
        data = {"word_data": [{"type": "text", "cnt": [[-10, -20], [100, 50]]}]}
        doc = separate_mathpix_output(data)

        region = doc.layout.elements[0].region
        assert region.top_left_x == 0
        assert region.top_left_y == 0

    def test_cnt_zero_dimension(self):
        """Test cnt resulting in zero width/height gets minimum 1."""
        data = {"word_data": [{"type": "text", "cnt": [[50, 50], [50, 50]]}]}
        doc = separate_mathpix_output(data)

        region = doc.layout.elements[0].region
        assert region.width >= 1
        assert region.height >= 1

    def test_cnt_malformed_structure(self):
        """Test cnt with malformed structure returns None."""
        data = {"word_data": [{"type": "text", "cnt": [[10], [20, 30]]}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].region is None

    def test_cnt_empty_array(self):
        """Test cnt with empty array returns None."""
        data = {"word_data": [{"type": "text", "cnt": []}]}
        doc = separate_mathpix_output(data)

        assert doc.layout.elements[0].region is None


class TestEdgeCaseUnicode:
    """EC-04: Unicode and international text edge cases."""

    def test_korean_text(self):
        """Test Korean text content."""
        data = {
            "word_data": [
                {"type": "text", "text": "안녕하세요 수학 문제입니다"}
            ]
        }
        doc = separate_mathpix_output(data)

        assert doc.content.elements[0].text == "안녕하세요 수학 문제입니다"

    def test_chinese_text(self):
        """Test Chinese text content."""
        data = {"word_data": [{"type": "text", "text": "数学问题"}]}
        doc = separate_mathpix_output(data)

        assert doc.content.elements[0].text == "数学问题"

    def test_japanese_text(self):
        """Test Japanese text content."""
        data = {"word_data": [{"type": "text", "text": "数学の問題です"}]}
        doc = separate_mathpix_output(data)

        assert doc.content.elements[0].text == "数学の問題です"

    def test_mixed_scripts(self):
        """Test mixed script content."""
        data = {
            "word_data": [
                {"type": "text", "text": "Find x where x = 값을 구하시오"}
            ]
        }
        doc = separate_mathpix_output(data)

        assert "x" in doc.content.elements[0].text
        assert "값" in doc.content.elements[0].text

    def test_emoji_in_text(self):
        """Test emoji in text content."""
        data = {"word_data": [{"type": "text", "text": "정답: ✓ 오답: ✗"}]}
        doc = separate_mathpix_output(data)

        assert "✓" in doc.content.elements[0].text


class TestEdgeCaseLatex:
    """EC-05: LaTeX special character edge cases."""

    def test_latex_backslash(self):
        """Test LaTeX with backslashes."""
        data = {
            "word_data": [
                {"type": "math", "latex": r"\frac{1}{2} + \sqrt{3}"}
            ]
        }
        doc = separate_mathpix_output(data)

        assert r"\frac" in doc.content.elements[0].latex
        assert r"\sqrt" in doc.content.elements[0].latex

    def test_latex_dollar_signs(self):
        """Test text with dollar sign delimiters."""
        data = {
            "word_data": [
                {"type": "math", "text": "$x^2 + y^2 = z^2$", "latex": "x^2 + y^2 = z^2"}
            ]
        }
        doc = separate_mathpix_output(data)

        assert "$" in doc.content.elements[0].text

    def test_latex_special_chars(self):
        """Test LaTeX with special characters."""
        data = {
            "word_data": [
                {"type": "math", "latex": r"\%\$\&\#\_\{\}"}
            ]
        }
        doc = separate_mathpix_output(data)

        latex = doc.content.elements[0].latex
        assert r"\%" in latex
        assert r"\$" in latex

    def test_latex_complex_expression(self):
        """Test complex LaTeX expression."""
        data = {
            "word_data": [
                {
                    "type": "math",
                    "latex": r"\int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi}",
                }
            ]
        }
        doc = separate_mathpix_output(data)

        assert r"\int" in doc.content.elements[0].latex
        assert r"\infty" in doc.content.elements[0].latex

    def test_latex_multiline(self):
        """Test multiline LaTeX."""
        data = {
            "word_data": [
                {
                    "type": "math",
                    "latex": "\\begin{align}\na &= b \\\\\nc &= d\n\\end{align}",
                }
            ]
        }
        doc = separate_mathpix_output(data)

        assert "\\begin{align}" in doc.content.elements[0].latex


class TestEdgeCaseDataFormats:
    """Additional edge cases for data format handling."""

    def test_unknown_data_format(self):
        """Test handling of unknown data format."""
        data = {
            "word_data": [
                {
                    "type": "math",
                    "data": [
                        {"type": "unknown_format", "value": "test"},
                        {"type": "latex", "value": "x^2"},
                    ],
                }
            ]
        }
        doc = separate_mathpix_output(data)

        # Unknown format should be skipped, only latex should remain
        assert len(doc.content.elements[0].data) == 1
        assert doc.content.elements[0].data[0].type == DataFormat.LATEX

    def test_all_data_formats(self):
        """Test all supported data formats."""
        data = {
            "word_data": [
                {
                    "type": "math",
                    "data": [
                        {"type": "latex", "value": "x^2"},
                        {"type": "asciimath", "value": "x^2"},
                        {"type": "mathml", "value": "<math>...</math>"},
                    ],
                }
            ]
        }
        doc = separate_mathpix_output(data)

        assert len(doc.content.elements[0].data) == 3

    def test_empty_data_array(self):
        """Test empty data array."""
        data = {"word_data": [{"type": "math", "data": []}]}
        doc = separate_mathpix_output(data)

        assert doc.content.elements[0].data == []


class TestEdgeCaseLargeData:
    """Edge cases for large datasets."""

    def test_many_elements(self):
        """Test separation with many elements."""
        word_data = [{"type": "text", "text": f"Element {i}"} for i in range(100)]
        data = {"word_data": word_data}

        doc = separate_mathpix_output(data)

        assert len(doc.layout.elements) == 100
        assert len(doc.content.elements) == 100
        assert doc.content.quality_summary.total_elements == 100

    def test_deep_hierarchy(self):
        """Test elements with deep parent-child relationships."""
        data = {
            "word_data": [
                {"id": "root", "type": "column", "children_ids": ["child-1"]},
                {"id": "child-1", "type": "text", "parent_id": "root", "text": "Child"},
            ]
        }

        doc = separate_mathpix_output(data)

        root = doc.layout.get_element_by_id("root")
        child = doc.layout.get_element_by_id("child-1")

        assert "child-1" in root.children_ids
        assert child.parent_id == "root"

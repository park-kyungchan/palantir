"""Tests for ReconstructionValidator."""

import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock

from cow_cli.pdf.validator import (
    ReconstructionValidator,
    ValidationResult,
    ValidationIssue,
)


class TestValidationIssue:
    """Tests for ValidationIssue dataclass."""

    def test_warning_issue(self):
        """Test warning severity issue."""
        issue = ValidationIssue(
            type="low_text_coverage",
            message="Text coverage is 85%",
            severity="warning",
        )

        assert issue.type == "low_text_coverage"
        assert issue.severity == "warning"
        assert issue.element_id is None

    def test_error_issue(self):
        """Test error severity issue."""
        issue = ValidationIssue(
            type="missing_element",
            message="Critical element missing",
            element_id="elem-001",
            severity="error",
        )

        assert issue.severity == "error"
        assert issue.element_id == "elem-001"


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_valid_result(self):
        """Test valid reconstruction result."""
        result = ValidationResult(
            valid=True,
            text_coverage=0.95,
            math_coverage=0.92,
            layout_order_score=0.98,
            issues=[],
        )

        assert result.valid is True
        assert result.is_acceptable() is True
        assert result.is_good() is True
        assert result.needs_human_review() is False

    def test_acceptable_result(self):
        """Test acceptable but not good result."""
        result = ValidationResult(
            valid=True,
            text_coverage=0.91,
            math_coverage=0.86,
            layout_order_score=0.96,
            issues=[
                ValidationIssue(type="minor", message="Minor issue"),
            ],
        )

        assert result.is_acceptable() is True
        assert result.is_good() is False

    def test_needs_human_review(self):
        """Test result that needs human review."""
        result = ValidationResult(
            valid=False,
            text_coverage=0.75,
            math_coverage=0.65,
            layout_order_score=0.90,
            issues=[
                ValidationIssue(type="error", message="Error 1", severity="error"),
                ValidationIssue(type="error", message="Error 2"),
                ValidationIssue(type="error", message="Error 3"),
            ],
        )

        assert result.needs_human_review() is True

    def test_recommendations_good_quality(self):
        """Test recommendations for good quality."""
        result = ValidationResult(
            valid=True,
            text_coverage=0.96,
            math_coverage=0.92,
            layout_order_score=0.99,
        )

        recs = result.get_recommendations()
        assert len(recs) == 1
        assert "excellent" in recs[0].lower()

    def test_recommendations_acceptable_quality(self):
        """Test recommendations for acceptable quality."""
        result = ValidationResult(
            valid=True,
            text_coverage=0.92,
            math_coverage=0.87,
            layout_order_score=0.96,
        )

        recs = result.get_recommendations()
        assert len(recs) == 1
        assert "acceptable" in recs[0].lower()

    def test_recommendations_with_issues(self):
        """Test recommendations when issues exist."""
        result = ValidationResult(
            valid=False,
            text_coverage=0.85,
            math_coverage=0.80,
            layout_order_score=0.92,
        )

        recs = result.get_recommendations()
        assert len(recs) >= 2
        assert any("Text coverage" in r for r in recs)
        assert any("Math coverage" in r for r in recs)


class TestReconstructionValidator:
    """Tests for ReconstructionValidator class."""

    @pytest.fixture
    def mock_pdfplumber(self):
        """Mock pdfplumber module."""
        with patch("cow_cli.pdf.validator.pdfplumber") as mock:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            mock_page.extract_text.return_value = (
                "Sample Document Title\n\n"
                "This is the introduction paragraph of the document.\n\n"
                "E = mc²\n\n"
                "The equation above shows Einstein's famous formula."
            )
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=None)
            mock.open.return_value = mock_pdf
            yield mock

    @pytest.fixture
    def validator(self, mock_pdfplumber):
        """Create a validator instance with mocked pdfplumber."""
        return ReconstructionValidator()

    @pytest.fixture
    def sample_content(self):
        """Sample content data."""
        return {
            "elements": [
                {
                    "id": "elem-001",
                    "text": "Sample Document Title",
                    "text_display": "Sample Document Title",
                },
                {
                    "id": "elem-002",
                    "text": "This is the introduction paragraph of the document.",
                },
                {
                    "id": "elem-003",
                    "latex": "E = mc^2",
                },
                {
                    "id": "elem-004",
                    "text": "The equation above shows Einstein's famous formula.",
                },
            ],
        }

    @pytest.mark.asyncio
    async def test_validate_success(self, validator, sample_content, mock_pdfplumber):
        """Test successful validation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            # Create dummy files
            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')
            content_path.write_text(json.dumps(sample_content))

            result = await validator.validate(pdf_path, layout_path, content_path)

            assert isinstance(result, ValidationResult)
            assert result.text_coverage >= 0
            assert result.math_coverage >= 0
            assert result.layout_order_score >= 0

    @pytest.mark.asyncio
    async def test_validate_high_coverage(self, validator, sample_content, mock_pdfplumber):
        """Test validation with high coverage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')
            content_path.write_text(json.dumps(sample_content))

            result = await validator.validate(pdf_path, layout_path, content_path)

            # With matching content, should have high text coverage
            assert result.text_coverage >= 0.9
            assert result.valid is True

    @pytest.mark.asyncio
    async def test_validate_low_coverage(self, validator, mock_pdfplumber):
        """Test validation with low text coverage."""
        # Override mock to return different text
        mock_pdfplumber.open.return_value.pages[0].extract_text.return_value = "Completely different content"

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')

            # Content that doesn't match PDF
            content = {
                "elements": [
                    {"text": "Expected text that is not in PDF"},
                    {"text": "Another expected paragraph missing"},
                ],
            }
            content_path.write_text(json.dumps(content))

            result = await validator.validate(pdf_path, layout_path, content_path)

            assert result.text_coverage < 0.9
            assert any(i.type == "low_text_coverage" for i in result.issues)

    @pytest.mark.asyncio
    async def test_validate_missing_pdf(self, validator):
        """Test validation with missing PDF file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            layout_path.write_text('{}')
            content_path.write_text('{}')

            with pytest.raises(FileNotFoundError) as exc_info:
                await validator.validate(
                    Path("/nonexistent/file.pdf"),
                    layout_path,
                    content_path,
                )

            assert "PDF not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_missing_layout(self, validator):
        """Test validation with missing layout file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF")
            content_path.write_text('{}')

            with pytest.raises(FileNotFoundError) as exc_info:
                await validator.validate(
                    pdf_path,
                    Path("/nonexistent/layout.json"),
                    content_path,
                )

            assert "layout.json not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_validate_empty_content(self, validator, mock_pdfplumber):
        """Test validation with empty content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')
            content_path.write_text('{"elements": []}')

            result = await validator.validate(pdf_path, layout_path, content_path)

            # Empty content should result in perfect scores (nothing to check)
            assert result.text_coverage == 1.0
            assert result.math_coverage == 1.0
            assert result.layout_order_score == 1.0

    @pytest.mark.asyncio
    async def test_validate_math_coverage(self, validator, mock_pdfplumber):
        """Test math coverage calculation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')

            # Content with math elements
            content = {
                "elements": [
                    {"latex": "x^2 + y^2 = z^2"},
                    {"latex": "\\int_0^1 f(x) dx"},
                ],
            }
            content_path.write_text(json.dumps(content))

            result = await validator.validate(pdf_path, layout_path, content_path)

            # Math coverage should be reasonable (heuristic-based)
            assert 0.7 <= result.math_coverage <= 1.0

    @pytest.mark.asyncio
    async def test_validate_layout_order(self, validator, mock_pdfplumber):
        """Test layout order calculation."""
        # Set up mock to return text in correct order
        mock_pdfplumber.open.return_value.pages[0].extract_text.return_value = (
            "First paragraph.\n"
            "Second paragraph.\n"
            "Third paragraph."
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = Path(tmpdir) / "test.pdf"
            layout_path = Path(tmpdir) / "layout.json"
            content_path = Path(tmpdir) / "content.json"

            pdf_path.write_bytes(b"%PDF-1.4")
            layout_path.write_text('{"elements": []}')

            content = {
                "elements": [
                    {"text": "First paragraph."},
                    {"text": "Second paragraph."},
                    {"text": "Third paragraph."},
                ],
            }
            content_path.write_text(json.dumps(content))

            result = await validator.validate(pdf_path, layout_path, content_path)

            # Elements are in order, should have high score
            assert result.layout_order_score >= 0.9


class TestReconstructionValidatorImport:
    """Test validator import behavior."""

    def test_import_error_without_pdfplumber(self):
        """Test that ImportError is raised without pdfplumber."""
        with patch("cow_cli.pdf.validator.pdfplumber", None):
            with pytest.raises(ImportError) as exc_info:
                ReconstructionValidator()

            assert "pdfplumber" in str(exc_info.value)

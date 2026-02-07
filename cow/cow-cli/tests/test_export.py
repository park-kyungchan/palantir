"""
Tests for Export Module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

from cow_cli.export import (
    ExportFormat,
    ExportOptions,
    ExportResult,
    BaseExporter,
    JSONExporter,
    MarkdownExporter,
    MarkdownFlavor,
    LaTeXExporter,
    DocumentClass,
    DocxExporter,
    DOCX_AVAILABLE,
    get_exporter,
)
from cow_cli.semantic.schemas import (
    SeparatedDocument,
    LayoutData,
    ContentData,
    LayoutElement,
    ContentElement,
    ElementType,
    Region,
    QualityMetrics,
)


@pytest.fixture
def sample_document():
    """Create a sample SeparatedDocument for testing."""
    layout = LayoutData(
        elements=[
            LayoutElement(
                id="elem-1",
                type=ElementType.TITLE,
                region=Region(top_left_x=0, top_left_y=0, width=100, height=30),
            ),
            LayoutElement(
                id="elem-2",
                type=ElementType.MATH,
                region=Region(top_left_x=0, top_left_y=50, width=200, height=50),
            ),
            LayoutElement(
                id="elem-3",
                type=ElementType.TEXT,
                region=Region(top_left_x=0, top_left_y=120, width=300, height=100),
            ),
        ]
    )

    content = ContentData(
        elements=[
            ContentElement(
                id="elem-1",
                layout_ref="elem-1",
                text="Sample Title",
                quality=QualityMetrics(confidence=0.99),
            ),
            ContentElement(
                id="elem-2",
                layout_ref="elem-2",
                latex="x^2 + y^2 = z^2",
                quality=QualityMetrics(confidence=0.95),
            ),
            ContentElement(
                id="elem-3",
                layout_ref="elem-3",
                text="This is sample text content.",
                quality=QualityMetrics(confidence=0.88),
            ),
        ]
    )
    content.compute_quality_summary()

    return SeparatedDocument(
        image_path="/test/sample.png",
        layout=layout,
        content=content,
        request_id="test-request-123",
    )


class TestExportFormat:
    """Tests for ExportFormat enum."""

    def test_format_values(self):
        """Test format enum values."""
        assert ExportFormat.JSON.value == "json"
        assert ExportFormat.MARKDOWN.value == "markdown"
        assert ExportFormat.LATEX.value == "latex"
        assert ExportFormat.DOCX.value == "docx"


class TestExportOptions:
    """Tests for ExportOptions dataclass."""

    def test_default_options(self):
        """Test default options."""
        options = ExportOptions()
        assert options.include_layout is True
        assert options.include_content is True
        assert options.include_metadata is True
        assert options.include_quality_metrics is False

    def test_custom_options(self):
        """Test custom options."""
        options = ExportOptions(
            include_layout=False,
            include_quality_metrics=True,
        )
        assert options.include_layout is False
        assert options.include_quality_metrics is True


class TestExportResult:
    """Tests for ExportResult dataclass."""

    def test_success_result(self, tmp_path):
        """Test successful result."""
        output_file = tmp_path / "test.json"
        output_file.write_text("{}")

        result = ExportResult(
            success=True,
            output_path=output_file,
            format=ExportFormat.JSON,
            bytes_written=2,
        )

        assert result.success is True
        assert result.is_valid is True

    def test_failure_result(self):
        """Test failure result."""
        result = ExportResult(
            success=False,
            error="Test error",
        )

        assert result.success is False
        assert result.is_valid is False
        assert result.error == "Test error"


class TestJSONExporter:
    """Tests for JSONExporter."""

    def test_export_basic(self, sample_document, tmp_path):
        """Test basic JSON export."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter()

        result = exporter.export(sample_document, output_path)

        assert result.success is True
        assert output_path.exists()

        # Verify JSON content
        with open(output_path, "r") as f:
            data = json.load(f)

        assert "layout" in data
        assert "content" in data
        assert data["image_path"] == "/test/sample.png"

    def test_export_compact(self, sample_document, tmp_path):
        """Test compact JSON export."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter(indent=None)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        # Compact JSON should have no newlines in data
        content = output_path.read_text()
        assert "\n" not in content.strip()

    def test_export_include_fields(self, sample_document, tmp_path):
        """Test export with included fields."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter(include_fields=["layout"])

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        with open(output_path, "r") as f:
            data = json.load(f)

        assert "layout" in data
        assert "content" not in data

    def test_export_exclude_fields(self, sample_document, tmp_path):
        """Test export with excluded fields."""
        output_path = tmp_path / "output.json"
        exporter = JSONExporter(exclude_fields=["metadata"])

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        with open(output_path, "r") as f:
            data = json.load(f)

        assert "metadata" not in data


class TestMarkdownExporter:
    """Tests for MarkdownExporter."""

    def test_export_gfm(self, sample_document, tmp_path):
        """Test GFM markdown export."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(flavor=MarkdownFlavor.GFM)

        result = exporter.export(sample_document, output_path)

        assert result.success is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "# Sample" in content

    def test_export_mmd(self, sample_document, tmp_path):
        """Test MMD markdown export."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(flavor=MarkdownFlavor.MMD)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

    def test_export_standard(self, sample_document, tmp_path):
        """Test standard markdown export."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(flavor=MarkdownFlavor.STANDARD)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

    def test_export_with_frontmatter(self, sample_document, tmp_path):
        """Test export with frontmatter."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(include_frontmatter=True)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        assert "---" in content
        assert "source:" in content

    def test_export_without_frontmatter(self, sample_document, tmp_path):
        """Test export without frontmatter."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(include_frontmatter=False)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        assert not content.startswith("---")

    def test_export_with_toc(self, sample_document, tmp_path):
        """Test export with TOC."""
        output_path = tmp_path / "output.md"
        exporter = MarkdownExporter(include_toc=True)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        assert "Table of Contents" in content


class TestLaTeXExporter:
    """Tests for LaTeXExporter."""

    def test_export_article(self, sample_document, tmp_path):
        """Test article class export."""
        output_path = tmp_path / "output.tex"
        exporter = LaTeXExporter(document_class=DocumentClass.ARTICLE)

        result = exporter.export(sample_document, output_path)

        assert result.success is True
        assert output_path.exists()

        content = output_path.read_text()
        assert "\\documentclass" in content
        assert "{article}" in content
        assert "\\begin{document}" in content
        assert "\\end{document}" in content

    def test_export_report(self, sample_document, tmp_path):
        """Test report class export."""
        output_path = tmp_path / "output.tex"
        exporter = LaTeXExporter(document_class=DocumentClass.REPORT)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        assert "{report}" in content

    def test_export_math_content(self, sample_document, tmp_path):
        """Test math content export."""
        output_path = tmp_path / "output.tex"
        exporter = LaTeXExporter()

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        # Should contain the equation
        assert "x^2 + y^2 = z^2" in content

    def test_export_with_custom_options(self, sample_document, tmp_path):
        """Test export with custom class options."""
        output_path = tmp_path / "output.tex"
        exporter = LaTeXExporter(class_options="11pt,letterpaper")

        result = exporter.export(sample_document, output_path)

        assert result.success is True

        content = output_path.read_text()
        assert "11pt,letterpaper" in content


class TestDocxExporter:
    """Tests for DocxExporter."""

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_basic(self, sample_document, tmp_path):
        """Test basic DOCX export."""
        output_path = tmp_path / "output.docx"
        exporter = DocxExporter()

        result = exporter.export(sample_document, output_path)

        assert result.success is True
        assert output_path.exists()

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_with_quality(self, sample_document, tmp_path):
        """Test DOCX export with quality metrics."""
        output_path = tmp_path / "output.docx"
        options = ExportOptions(include_quality_metrics=True)
        exporter = DocxExporter(options=options)

        result = exporter.export(sample_document, output_path)

        assert result.success is True

    def test_export_without_docx_package(self, sample_document, tmp_path, monkeypatch):
        """Test export fails gracefully without python-docx."""
        # Skip if docx is available - this test is for when it's not installed
        if DOCX_AVAILABLE:
            pytest.skip("python-docx is installed")

        output_path = tmp_path / "output.docx"
        exporter = DocxExporter()

        result = exporter.export(sample_document, output_path)

        assert result.success is False
        assert "python-docx" in result.error


class TestGetExporter:
    """Tests for get_exporter factory function."""

    def test_get_json_exporter(self):
        """Test getting JSON exporter."""
        exporter = get_exporter(ExportFormat.JSON)
        assert isinstance(exporter, JSONExporter)

    def test_get_markdown_exporter(self):
        """Test getting Markdown exporter."""
        exporter = get_exporter(ExportFormat.MARKDOWN)
        assert isinstance(exporter, MarkdownExporter)

    def test_get_latex_exporter(self):
        """Test getting LaTeX exporter."""
        exporter = get_exporter(ExportFormat.LATEX)
        assert isinstance(exporter, LaTeXExporter)

    def test_get_docx_exporter(self):
        """Test getting DOCX exporter."""
        exporter = get_exporter(ExportFormat.DOCX)
        assert isinstance(exporter, DocxExporter)

    def test_invalid_format(self):
        """Test invalid format raises error."""
        with pytest.raises(ValueError):
            get_exporter(ExportFormat.PDF)


class TestExportValidation:
    """Tests for export validation."""

    def test_validate_empty_document(self, tmp_path):
        """Test validation of empty document."""
        doc = SeparatedDocument(image_path="/test/empty.png")
        exporter = JSONExporter()

        errors = exporter.validate_document(doc)
        assert len(errors) > 0
        assert "no layout or content" in errors[0].lower()

    def test_validate_invalid_references(self, tmp_path):
        """Test validation of invalid references."""
        doc = SeparatedDocument(
            image_path="/test/test.png",
            content=ContentData(
                elements=[
                    ContentElement(
                        id="elem-1",
                        layout_ref="nonexistent",
                        text="Test",
                    )
                ]
            ),
        )
        exporter = JSONExporter()

        errors = exporter.validate_document(doc)
        assert any("nonexistent" in e for e in errors)


class TestExtensionHandling:
    """Tests for file extension handling."""

    def test_ensure_extension_json(self, tmp_path):
        """Test JSON extension."""
        exporter = JSONExporter()
        path = tmp_path / "file"
        result = exporter.ensure_extension(path)
        assert result.suffix == ".json"

    def test_ensure_extension_markdown(self, tmp_path):
        """Test Markdown extension."""
        exporter = MarkdownExporter()
        path = tmp_path / "file"
        result = exporter.ensure_extension(path)
        assert result.suffix == ".md"

    def test_ensure_extension_latex(self, tmp_path):
        """Test LaTeX extension."""
        exporter = LaTeXExporter()
        path = tmp_path / "file"
        result = exporter.ensure_extension(path)
        assert result.suffix == ".tex"

    def test_ensure_extension_docx(self, tmp_path):
        """Test DOCX extension."""
        exporter = DocxExporter()
        path = tmp_path / "file"
        result = exporter.ensure_extension(path)
        assert result.suffix == ".docx"

    def test_preserve_correct_extension(self, tmp_path):
        """Test correct extension is preserved."""
        exporter = JSONExporter()
        path = tmp_path / "file.json"
        result = exporter.ensure_extension(path)
        assert result == path

"""
Tests for Export CLI Commands.
"""
import pytest
import json
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from cow_cli.commands.export import app
from cow_cli.export import DOCX_AVAILABLE
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


runner = CliRunner()


@pytest.fixture
def sample_json_file(tmp_path):
    """Create a sample JSON file for testing."""
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
        ]
    )

    content = ContentData(
        elements=[
            ContentElement(
                id="elem-1",
                layout_ref="elem-1",
                text="Test Title",
                quality=QualityMetrics(confidence=0.99),
            ),
            ContentElement(
                id="elem-2",
                layout_ref="elem-2",
                latex="E = mc^2",
                quality=QualityMetrics(confidence=0.95),
            ),
        ]
    )
    content.compute_quality_summary()

    doc = SeparatedDocument(
        image_path="/test/sample.png",
        layout=layout,
        content=content,
    )

    # Save to file
    json_path = tmp_path / "input.json"
    json_path.write_text(doc.model_dump_json(indent=2))

    return json_path


class TestFormatsCommand:
    """Tests for the formats command."""

    def test_list_formats(self):
        """Test listing available formats."""
        result = runner.invoke(app, ["formats"])

        assert result.exit_code == 0
        assert "json" in result.stdout.lower()
        assert "markdown" in result.stdout.lower()
        assert "latex" in result.stdout.lower()
        assert "docx" in result.stdout.lower()


class TestJSONExportCommand:
    """Tests for JSON export command."""

    def test_export_json_basic(self, sample_json_file, tmp_path):
        """Test basic JSON export."""
        output_path = tmp_path / "output.json"

        result = runner.invoke(app, [
            "json", str(sample_json_file),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()
        assert "Exported to" in result.stdout

    def test_export_json_compact(self, sample_json_file, tmp_path):
        """Test compact JSON export."""
        output_path = tmp_path / "output.json"

        result = runner.invoke(app, [
            "json", str(sample_json_file),
            "-o", str(output_path),
            "--compact",
        ])

        assert result.exit_code == 0

        # Check no indentation
        content = output_path.read_text()
        assert "\n" not in content.strip()

    def test_export_json_default_output(self, sample_json_file):
        """Test default output path."""
        result = runner.invoke(app, ["json", str(sample_json_file)])

        assert result.exit_code == 0

        # Check default output was created
        expected_output = sample_json_file.with_suffix(".exported.json")
        assert expected_output.exists()

        # Cleanup
        expected_output.unlink()

    def test_export_json_not_found(self, tmp_path):
        """Test export with non-existent file."""
        result = runner.invoke(app, [
            "json", str(tmp_path / "nonexistent.json"),
        ])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestMarkdownExportCommand:
    """Tests for Markdown export command."""

    def test_export_markdown_basic(self, sample_json_file, tmp_path):
        """Test basic Markdown export."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()

        content = output_path.read_text()
        assert "#" in content  # Has headings

    def test_export_markdown_gfm(self, sample_json_file, tmp_path):
        """Test GFM flavor export."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--flavor", "gfm",
        ])

        assert result.exit_code == 0

    def test_export_markdown_mmd(self, sample_json_file, tmp_path):
        """Test MMD flavor export."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--flavor", "mmd",
        ])

        assert result.exit_code == 0

    def test_export_markdown_invalid_flavor(self, sample_json_file, tmp_path):
        """Test invalid flavor."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--flavor", "invalid",
        ])

        assert result.exit_code == 1
        assert "invalid flavor" in result.stdout.lower()

    def test_export_markdown_no_frontmatter(self, sample_json_file, tmp_path):
        """Test export without frontmatter."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--no-frontmatter",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert not content.startswith("---")

    def test_export_markdown_with_toc(self, sample_json_file, tmp_path):
        """Test export with TOC."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--with-toc",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert "Table of Contents" in content


class TestLaTeXExportCommand:
    """Tests for LaTeX export command."""

    def test_export_latex_basic(self, sample_json_file, tmp_path):
        """Test basic LaTeX export."""
        output_path = tmp_path / "output.tex"

        result = runner.invoke(app, [
            "latex", str(sample_json_file),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()

        content = output_path.read_text()
        assert "\\documentclass" in content

    def test_export_latex_article(self, sample_json_file, tmp_path):
        """Test article document class."""
        output_path = tmp_path / "output.tex"

        result = runner.invoke(app, [
            "latex", str(sample_json_file),
            "-o", str(output_path),
            "-d", "article",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert "{article}" in content

    def test_export_latex_report(self, sample_json_file, tmp_path):
        """Test report document class."""
        output_path = tmp_path / "output.tex"

        result = runner.invoke(app, [
            "latex", str(sample_json_file),
            "-o", str(output_path),
            "-d", "report",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert "{report}" in content

    def test_export_latex_invalid_class(self, sample_json_file, tmp_path):
        """Test invalid document class."""
        output_path = tmp_path / "output.tex"

        result = runner.invoke(app, [
            "latex", str(sample_json_file),
            "-o", str(output_path),
            "-d", "invalid",
        ])

        assert result.exit_code == 1
        assert "invalid document class" in result.stdout.lower()

    def test_export_latex_custom_options(self, sample_json_file, tmp_path):
        """Test custom class options."""
        output_path = tmp_path / "output.tex"

        result = runner.invoke(app, [
            "latex", str(sample_json_file),
            "-o", str(output_path),
            "--class-options", "11pt,letterpaper",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert "11pt,letterpaper" in content


class TestDocxExportCommand:
    """Tests for DOCX export command."""

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_docx_basic(self, sample_json_file, tmp_path):
        """Test basic DOCX export."""
        output_path = tmp_path / "output.docx"

        result = runner.invoke(app, [
            "docx", str(sample_json_file),
            "-o", str(output_path),
        ])

        assert result.exit_code == 0
        assert output_path.exists()

    @pytest.mark.skipif(not DOCX_AVAILABLE, reason="python-docx not installed")
    def test_export_docx_with_quality(self, sample_json_file, tmp_path):
        """Test DOCX export with quality metrics."""
        output_path = tmp_path / "output.docx"

        result = runner.invoke(app, [
            "docx", str(sample_json_file),
            "-o", str(output_path),
            "--with-quality",
        ])

        assert result.exit_code == 0

    def test_export_docx_template_not_found(self, sample_json_file, tmp_path):
        """Test DOCX export with non-existent template."""
        if not DOCX_AVAILABLE:
            pytest.skip("python-docx not installed")

        output_path = tmp_path / "output.docx"

        result = runner.invoke(app, [
            "docx", str(sample_json_file),
            "-o", str(output_path),
            "-t", str(tmp_path / "nonexistent.docx"),
        ])

        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()


class TestExportWithQuality:
    """Tests for quality metrics in exports."""

    def test_json_with_quality(self, sample_json_file, tmp_path):
        """Test JSON export with quality metrics."""
        output_path = tmp_path / "output.json"

        result = runner.invoke(app, [
            "json", str(sample_json_file),
            "-o", str(output_path),
            "--with-quality",
        ])

        assert result.exit_code == 0

        with open(output_path, "r") as f:
            data = json.load(f)

        assert "quality_summary" in data

    def test_markdown_with_quality(self, sample_json_file, tmp_path):
        """Test Markdown export with quality metrics."""
        output_path = tmp_path / "output.md"

        result = runner.invoke(app, [
            "markdown", str(sample_json_file),
            "-o", str(output_path),
            "--with-quality",
        ])

        assert result.exit_code == 0

        content = output_path.read_text()
        assert "Quality Metrics" in content

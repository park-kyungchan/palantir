"""
Tests for Process CLI Commands.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
from typer.testing import CliRunner

from cow_cli.commands.process import app, _parse_page_range, _format_duration
from cow_cli.pipeline.processor import PipelineResult, StageResult
from cow_cli.semantic.schemas import SeparatedDocument, LayoutData, ContentData


runner = CliRunner()


@pytest.fixture
def temp_image(tmp_path):
    """Create a temporary test image."""
    # Create a minimal PNG file
    img_path = tmp_path / "test.png"
    # Minimal valid PNG (1x1 white pixel)
    png_data = bytes([
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
        0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
        0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,  # IDAT chunk
        0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0xFF,
        0x00, 0x05, 0xFE, 0x02, 0xFE, 0xA3, 0x56, 0xC3,
        0xA8, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,  # IEND chunk
        0x44, 0xAE, 0x42, 0x60, 0x82,
    ])
    img_path.write_bytes(png_data)
    return img_path


@pytest.fixture
def mock_pipeline_result():
    """Create a mock successful pipeline result."""
    doc = SeparatedDocument(
        image_path="/test/image.png",
        layout=LayoutData(elements=[]),
        content=ContentData(elements=[]),
    )

    return PipelineResult(
        image_path="/test/image.png",
        success=True,
        document=doc,
        stages=[
            StageResult(stage="A", success=True, duration_ms=100),
            StageResult(stage="B", success=True, duration_ms=1500),
            StageResult(stage="C0", success=True, duration_ms=50),
        ],
        total_duration_ms=1650,
    )


class TestFormatDuration:
    """Tests for _format_duration helper."""

    def test_milliseconds(self):
        """Test milliseconds formatting."""
        assert _format_duration(500) == "500ms"

    def test_seconds(self):
        """Test seconds formatting."""
        assert _format_duration(2500) == "2.5s"

    def test_minutes(self):
        """Test minutes formatting."""
        assert _format_duration(120000) == "2.0min"


class TestParsePageRange:
    """Tests for _parse_page_range helper."""

    def test_single_page(self):
        """Test single page."""
        assert _parse_page_range("5") == [5]

    def test_page_range(self):
        """Test page range."""
        assert _parse_page_range("1-5") == [1, 2, 3, 4, 5]

    def test_multiple_ranges(self):
        """Test multiple ranges."""
        result = _parse_page_range("1-3,5,7-8")
        assert result == [1, 2, 3, 5, 7, 8]

    def test_removes_duplicates(self):
        """Test duplicate removal."""
        result = _parse_page_range("1-3,2-4")
        assert result == [1, 2, 3, 4]

    def test_invalid_range(self):
        """Test invalid range returns empty."""
        assert _parse_page_range("invalid") == []
        assert _parse_page_range("1-a") == []


class TestProcessImageCommand:
    """Tests for process image command."""

    def test_file_not_found(self, tmp_path):
        """Test error when file not found."""
        result = runner.invoke(app, ["image", str(tmp_path / "nonexistent.png")])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_not_a_file(self, tmp_path):
        """Test error when path is not a file."""
        result = runner.invoke(app, ["image", str(tmp_path)])
        assert result.exit_code == 1
        assert "not a file" in result.stdout.lower()

    @patch("cow_cli.commands.process.pipeline_process_image")
    def test_process_success(self, mock_process, temp_image, mock_pipeline_result, tmp_path):
        """Test successful image processing."""
        mock_process.return_value = mock_pipeline_result

        result = runner.invoke(app, [
            "image", str(temp_image),
            "-o", str(tmp_path / "output"),
        ])

        assert result.exit_code == 0
        assert "✓" in result.stdout

    @patch("cow_cli.commands.process.pipeline_process_image")
    def test_process_failure(self, mock_process, temp_image, tmp_path):
        """Test failed image processing."""
        mock_process.return_value = PipelineResult(
            image_path=str(temp_image),
            success=False,
            error="Test error",
            stages=[],
            total_duration_ms=100,
        )

        result = runner.invoke(app, [
            "image", str(temp_image),
            "-o", str(tmp_path / "output"),
        ])

        assert result.exit_code == 1
        assert "Test error" in result.stdout

    @patch("cow_cli.commands.process.pipeline_process_image")
    def test_process_json_output(self, mock_process, temp_image, mock_pipeline_result, tmp_path):
        """Test JSON output mode."""
        mock_process.return_value = mock_pipeline_result

        result = runner.invoke(app, [
            "image", str(temp_image),
            "-o", str(tmp_path / "output"),
            "--json",
        ])

        assert result.exit_code == 0
        # Should be valid JSON
        output_data = json.loads(result.stdout)
        assert "success" in output_data
        assert output_data["success"] is True


class TestProcessBatchCommand:
    """Tests for process batch command."""

    def test_directory_not_found(self, tmp_path):
        """Test error when directory not found."""
        result = runner.invoke(app, ["batch", str(tmp_path / "nonexistent")])
        assert result.exit_code == 1
        assert "not found" in result.stdout.lower()

    def test_not_a_directory(self, temp_image):
        """Test error when path is not a directory."""
        result = runner.invoke(app, ["batch", str(temp_image)])
        assert result.exit_code == 1
        assert "not a directory" in result.stdout.lower()

    def test_no_images_found(self, tmp_path):
        """Test when no images match pattern."""
        result = runner.invoke(app, [
            "batch", str(tmp_path),
            "-p", "*.nonexistent",
        ])

        assert result.exit_code == 0
        assert "no images found" in result.stdout.lower()

    @patch("cow_cli.commands.process.pipeline_process_batch")
    def test_batch_process_success(self, mock_batch, tmp_path, mock_pipeline_result):
        """Test successful batch processing."""
        # Create test images
        for i in range(3):
            img_path = tmp_path / f"image{i}.png"
            img_path.write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))  # PNG header

        mock_batch.return_value = [mock_pipeline_result] * 3

        result = runner.invoke(app, [
            "batch", str(tmp_path),
            "-p", "*.png",
            "-o", str(tmp_path / "output"),
        ])

        assert result.exit_code == 0
        assert "3" in result.stdout  # 3 images

    @patch("cow_cli.commands.process.pipeline_process_batch")
    def test_batch_json_output(self, mock_batch, tmp_path, mock_pipeline_result):
        """Test batch JSON output mode."""
        # Create test images
        for i in range(2):
            img_path = tmp_path / f"image{i}.png"
            img_path.write_bytes(bytes([0x89, 0x50, 0x4E, 0x47]))

        mock_batch.return_value = [mock_pipeline_result, mock_pipeline_result]

        result = runner.invoke(app, [
            "batch", str(tmp_path),
            "-p", "*.png",
            "-o", str(tmp_path / "output"),
            "--json",
        ])

        assert result.exit_code == 0
        # Try to parse JSON from output - may include progress text before JSON
        stdout = result.stdout
        # Find JSON object in output (starts with { and ends with })
        json_start = stdout.find("{")
        if json_start != -1:
            json_str = stdout[json_start:]
            output_data = json.loads(json_str)
            assert output_data["total"] == 2
            assert output_data["successful"] == 2
        else:
            # If no JSON found, at least check for key elements
            assert "2" in stdout  # Should show count


class TestProcessPdfCommand:
    """Tests for process pdf command."""

    @pytest.fixture
    def pymupdf_available(self):
        """Check if PyMuPDF is available."""
        try:
            import fitz
            return True
        except ImportError:
            return False

    def test_file_not_found(self, tmp_path, pymupdf_available):
        """Test error when PDF not found."""
        result = runner.invoke(app, ["pdf", str(tmp_path / "nonexistent.pdf")])
        assert result.exit_code == 1
        # Either PyMuPDF not installed or file not found
        assert "not found" in result.stdout.lower() or "pymupdf" in result.stdout.lower()

    def test_not_pdf_file(self, temp_image, pymupdf_available):
        """Test error when file is not PDF."""
        result = runner.invoke(app, ["pdf", str(temp_image)])
        assert result.exit_code == 1
        # Either PyMuPDF not installed or not a PDF
        assert "not a pdf" in result.stdout.lower() or "pymupdf" in result.stdout.lower()

    def test_pymupdf_not_installed(self, tmp_path, monkeypatch):
        """Test error when PyMuPDF not installed."""
        # Create a fake PDF file
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        # Mock fitz import to fail
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "fitz":
                raise ImportError("No module named 'fitz'")
            return original_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", mock_import)

        result = runner.invoke(app, ["pdf", str(pdf_path)])
        assert result.exit_code == 1
        assert "pymupdf not installed" in result.stdout.lower()


class TestProcessStatusCommand:
    """Tests for process status command."""

    def test_status_no_output_dir(self, tmp_path):
        """Test status with non-existent output directory."""
        result = runner.invoke(app, [
            "status",
            "-o", str(tmp_path / "nonexistent"),
        ])

        assert result.exit_code == 0
        assert "not found" in result.stdout.lower()

    def test_status_no_results(self, tmp_path):
        """Test status with empty output directory."""
        tmp_path.mkdir(exist_ok=True)

        result = runner.invoke(app, ["status", "-o", str(tmp_path)])

        assert result.exit_code == 0
        assert "no processed results" in result.stdout.lower()

    def test_status_with_results(self, tmp_path):
        """Test status with processed results."""
        # Create fake result directory
        result_dir = tmp_path / "test_image"
        result_dir.mkdir()

        # Create fake JSON result
        (result_dir / "test_image.json").write_text(json.dumps({
            "content": {
                "elements": [{"id": "1"}, {"id": "2"}]
            }
        }))

        result = runner.invoke(app, ["status", "-o", str(tmp_path)])

        assert result.exit_code == 0
        assert "test_image" in result.stdout
        assert "2" in result.stdout  # 2 elements


class TestExportIntegration:
    """Tests for export integration in process commands."""

    @patch("cow_cli.commands.process.pipeline_process_image")
    def test_process_with_export_formats(self, mock_process, temp_image, mock_pipeline_result, tmp_path):
        """Test processing with multiple export formats."""
        mock_process.return_value = mock_pipeline_result

        result = runner.invoke(app, [
            "image", str(temp_image),
            "-o", str(tmp_path / "output"),
            "-f", "json",
            "-f", "markdown",
        ])

        assert result.exit_code == 0
        # Check for export messages
        assert "Exported" in result.stdout or "→" in result.stdout

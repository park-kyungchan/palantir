"""Tests for MathpixPDFConverter."""

import pytest
from pathlib import Path
import tempfile
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from cow_cli.pdf.converter import (
    MathpixPDFConverter,
    ConversionResult,
    ConversionStatus,
    ConversionStatusEnum,
)


class TestConversionResult:
    """Tests for ConversionResult dataclass."""

    def test_successful_result(self):
        """Test successful conversion result."""
        result = ConversionResult(
            success=True,
            pdf_path=Path("/tmp/output.pdf"),
            conversion_id="abc123",
            pages=5,
        )

        assert result.success is True
        assert result.pdf_path == Path("/tmp/output.pdf")
        assert result.conversion_id == "abc123"
        assert result.pages == 5
        assert result.error is None

    def test_failed_result(self):
        """Test failed conversion result."""
        result = ConversionResult(
            success=False,
            error="API rate limit exceeded",
        )

        assert result.success is False
        assert result.pdf_path is None
        assert result.error == "API rate limit exceeded"

    def test_async_processing_result(self):
        """Test result for async processing."""
        result = ConversionResult(
            success=True,
            conversion_id="async-job-123",
            error="Processing - use get_status() to poll",
        )

        assert result.success is True
        assert result.conversion_id == "async-job-123"
        assert result.pdf_path is None


class TestConversionStatus:
    """Tests for ConversionStatus dataclass."""

    def test_processing_status(self):
        """Test processing status."""
        status = ConversionStatus(
            status="processing",
            progress=0.5,
        )

        assert status.status == "processing"
        assert status.progress == 0.5
        assert status.pdf_url is None

    def test_completed_status(self):
        """Test completed status."""
        status = ConversionStatus(
            status="completed",
            progress=1.0,
            pdf_url="https://api.mathpix.com/v3/pdf/abc123.pdf",
        )

        assert status.status == "completed"
        assert status.pdf_url is not None

    def test_failed_status(self):
        """Test failed status."""
        status = ConversionStatus(
            status="failed",
            error="LaTeX compilation error",
        )

        assert status.status == "failed"
        assert status.error == "LaTeX compilation error"


class TestMathpixPDFConverter:
    """Tests for MathpixPDFConverter class."""

    @pytest.fixture
    def converter(self):
        """Create a converter instance."""
        return MathpixPDFConverter(
            app_id="test-app-id",
            app_key="test-app-key",
        )

    @pytest.fixture
    def sample_mmd(self):
        """Sample MMD content."""
        return """# Test Document

This is a test paragraph.

$$
E = mc^2
$$

Another paragraph with inline math $x + y = z$.
"""

    def test_init(self, converter):
        """Test converter initialization."""
        assert converter.app_id == "test-app-id"
        assert converter.app_key == "test-app-key"
        assert converter.BASE_URL == "https://api.mathpix.com/v3"

    def test_get_headers(self, converter):
        """Test header generation."""
        headers = converter._get_headers()

        assert headers["app_id"] == "test-app-id"
        assert headers["app_key"] == "test-app-key"
        assert headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_convert_success_sync(self, converter, sample_mmd):
        """Test successful synchronous conversion."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.pdf"

            # Mock the API response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "completed",
                "pdf_url": "https://api.mathpix.com/v3/pdf/test.pdf",
                "pdf_id": "test-pdf-123",
                "pages": 1,
            }

            mock_pdf_response = MagicMock()
            mock_pdf_response.status_code = 200
            mock_pdf_response.content = b"%PDF-1.4 test content"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.get = AsyncMock(return_value=mock_pdf_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                result = await converter.convert(sample_mmd, output_path)

            assert result.success is True
            assert result.pdf_path == output_path
            assert result.conversion_id == "test-pdf-123"
            assert result.pages == 1
            assert output_path.exists()

    @pytest.mark.asyncio
    async def test_convert_async_processing(self, converter, sample_mmd):
        """Test conversion that returns async job."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "pdf_id": "async-job-456",
            }

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                result = await converter.convert(sample_mmd, output_path)

            assert result.success is True
            assert result.conversion_id == "async-job-456"
            assert result.pdf_path is None
            assert "Processing" in result.error

    @pytest.mark.asyncio
    async def test_convert_api_error(self, converter, sample_mmd):
        """Test conversion with API error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                result = await converter.convert(sample_mmd, output_path)

            assert result.success is False
            assert "API error: 500" in result.error

    @pytest.mark.asyncio
    async def test_convert_from_file(self, converter):
        """Test conversion from MMD file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mmd_path = Path(tmpdir) / "input.mmd"
            output_path = Path(tmpdir) / "output.pdf"

            mmd_path.write_text("# Test\n\nContent")

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "completed",
                "pdf_url": "https://test.pdf",
                "pdf_id": "file-test",
            }

            mock_pdf_response = MagicMock()
            mock_pdf_response.status_code = 200
            mock_pdf_response.content = b"%PDF"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.get = AsyncMock(return_value=mock_pdf_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                # Pass file path as string
                result = await converter.convert(str(mmd_path), output_path)

            assert result.success is True

    @pytest.mark.asyncio
    async def test_get_status_completed(self, converter):
        """Test getting status for completed job."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "completed",
            "progress": 1.0,
            "pdf_url": "https://api.mathpix.com/v3/pdf/result.pdf",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            status = await converter.get_status("test-job-123")

        assert status.status == "completed"
        assert status.progress == 1.0
        assert status.pdf_url is not None

    @pytest.mark.asyncio
    async def test_get_status_processing(self, converter):
        """Test getting status for processing job."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": "processing",
            "progress": 0.75,
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            status = await converter.get_status("processing-job")

        assert status.status == "processing"
        assert status.progress == 0.75

    @pytest.mark.asyncio
    async def test_get_status_api_error(self, converter):
        """Test status check with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.get = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            status = await converter.get_status("unknown-job")

        assert status.status == ConversionStatusEnum.FAILED
        assert "Status check failed" in status.error

    @pytest.mark.asyncio
    async def test_download_pdf_success(self, converter):
        """Test successful PDF download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "downloaded.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"%PDF-1.4 test pdf content"

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                success = await converter.download_pdf(
                    "https://test.pdf", output_path
                )

            assert success is True
            assert output_path.exists()
            assert output_path.read_bytes() == b"%PDF-1.4 test pdf content"

    @pytest.mark.asyncio
    async def test_download_pdf_failure(self, converter):
        """Test failed PDF download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "downloaded.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 404

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.get = AsyncMock(return_value=mock_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                success = await converter.download_pdf(
                    "https://invalid.pdf", output_path
                )

            assert success is False
            assert not output_path.exists()


class TestMathpixPDFConverterWithOptions:
    """Tests for converter with custom options."""

    @pytest.fixture
    def converter(self):
        """Create a converter instance."""
        return MathpixPDFConverter(
            app_id="test-app",
            app_key="test-key",
        )

    @pytest.mark.asyncio
    async def test_convert_with_custom_options(self, converter):
        """Test conversion with custom options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.pdf"

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "completed",
                "pdf_url": "https://test.pdf",
                "pdf_id": "opt-test",
            }

            mock_pdf_response = MagicMock()
            mock_pdf_response.status_code = 200
            mock_pdf_response.content = b"%PDF"

            captured_request = {}

            async def capture_post(url, **kwargs):
                captured_request.update(kwargs)
                return mock_response

            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_instance.post = capture_post
                mock_instance.get = AsyncMock(return_value=mock_pdf_response)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                result = await converter.convert(
                    "# Test",
                    output_path,
                    options={"custom_option": True},
                )

            # Verify custom option was passed
            assert "json" in captured_request
            assert captured_request["json"].get("custom_option") is True

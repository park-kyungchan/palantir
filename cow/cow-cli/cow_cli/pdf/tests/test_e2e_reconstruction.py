"""End-to-end integration tests for PDF reconstruction pipeline."""

import pytest
from pathlib import Path
import tempfile
import json
from unittest.mock import patch, MagicMock, AsyncMock

from cow_cli.pdf.merger import MMDMerger
from cow_cli.pdf.converter import MathpixPDFConverter, ConversionResult
from cow_cli.pdf.validator import ReconstructionValidator, ValidationResult
from cow_cli.pdf.tests import FIXTURES_DIR


class TestE2EPipelineFlow:
    """Test the complete PDF reconstruction pipeline flow."""

    @pytest.fixture
    def layout_path(self) -> Path:
        """Path to sample layout fixture."""
        return FIXTURES_DIR / "sample_layout.json"

    @pytest.fixture
    def content_path(self) -> Path:
        """Path to sample content fixture."""
        return FIXTURES_DIR / "sample_content.json"

    @pytest.fixture
    def mock_mathpix_api(self):
        """Mock Mathpix API responses."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()

            # Mock converter API response
            mock_convert_response = MagicMock()
            mock_convert_response.status_code = 200
            mock_convert_response.json.return_value = {
                "status": "completed",
                "pdf_url": "https://api.mathpix.com/v3/pdf/test.pdf",
                "pdf_id": "e2e-test-123",
                "pages": 1,
            }

            # Mock PDF download response
            mock_pdf_response = MagicMock()
            mock_pdf_response.status_code = 200
            mock_pdf_response.content = b"%PDF-1.4 mock pdf content"

            mock_instance.post = AsyncMock(return_value=mock_convert_response)
            mock_instance.get = AsyncMock(return_value=mock_pdf_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)

            mock_client.return_value = mock_instance
            yield mock_client

    @pytest.fixture
    def mock_pdfplumber(self):
        """Mock pdfplumber for validation."""
        with patch("cow_cli.pdf.validator.pdfplumber") as mock:
            mock_pdf = MagicMock()
            mock_page = MagicMock()
            # Return text that matches our sample content
            mock_page.extract_text.return_value = (
                "Sample Document Title\n\n"
                "This is the introduction paragraph of the document. "
                "It contains important information about the mathematical concepts.\n\n"
                "E = mc²\n\n"
                "The equation above shows Einstein's famous mass-energy equivalence formula. "
                "This relationship is fundamental to our understanding of physics."
            )
            mock_pdf.pages = [mock_page]
            mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
            mock_pdf.__exit__ = MagicMock(return_value=None)
            mock.open.return_value = mock_pdf
            yield mock

    @pytest.mark.asyncio
    async def test_full_pipeline(
        self,
        layout_path,
        content_path,
        mock_mathpix_api,
        mock_pdfplumber,
    ):
        """Test the complete B1 → MMD → PDF → Validate pipeline."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # ============================================================
            # PHASE 1: Merge (B1 → MMD)
            # ============================================================
            merger = MMDMerger()
            mmd_path = tmpdir / "merged.mmd"

            merge_result = await merger.merge_files(
                layout_path=layout_path,
                content_path=content_path,
                output_path=mmd_path,
            )

            assert merge_result.element_count == 4
            assert mmd_path.exists()
            assert "Sample Document Title" in merge_result.content
            assert "E = mc" in merge_result.content

            # ============================================================
            # PHASE 2: Convert (MMD → PDF)
            # ============================================================
            converter = MathpixPDFConverter(
                app_id="test-app-id",
                app_key="test-app-key",
            )
            pdf_path = tmpdir / "output.pdf"

            convert_result = await converter.convert(
                mmd=merge_result.content,
                output_path=pdf_path,
            )

            assert convert_result.success is True
            assert convert_result.pdf_path == pdf_path
            assert pdf_path.exists()

            # ============================================================
            # PHASE 3: Validate (PDF Quality Check)
            # ============================================================
            validator = ReconstructionValidator()

            validation_result = await validator.validate(
                pdf_path=pdf_path,
                layout_path=layout_path,
                content_path=content_path,
            )

            assert validation_result.valid is True
            assert validation_result.text_coverage >= 0.9
            assert validation_result.math_coverage >= 0.7

            # Full pipeline success
            print(f"\n=== E2E Pipeline Results ===")
            print(f"MMD Elements: {merge_result.element_count}")
            print(f"PDF Path: {convert_result.pdf_path}")
            print(f"Text Coverage: {validation_result.text_coverage:.1%}")
            print(f"Math Coverage: {validation_result.math_coverage:.1%}")
            print(f"Layout Order: {validation_result.layout_order_score:.1%}")
            print(f"Valid: {validation_result.valid}")

    @pytest.mark.asyncio
    async def test_pipeline_with_warnings(
        self,
        mock_mathpix_api,
        mock_pdfplumber,
    ):
        """Test pipeline handles warnings gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create layout with orphan element
            layout_path = tmpdir / "layout.json"
            content_path = tmpdir / "content.json"

            layout_data = {
                "elements": [
                    {"id": "elem-1", "type": "text", "line": 0, "column": 0},
                    {"id": "elem-orphan", "type": "text", "line": 1, "column": 0},  # No content
                ],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 2, "hierarchy_depth": 0},
            }

            content_data = {
                "elements": [
                    {"id": "elem-1", "layout_ref": "elem-1", "text": "Only content"},
                ],
                "quality_summary": {"total_elements": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 1},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            # Phase 1: Merge (should warn about orphan)
            merger = MMDMerger()
            merge_result = await merger.merge_files(layout_path, content_path)

            assert len(merge_result.warnings) > 0
            assert "elem-orphan" in merge_result.warnings[0]

            # Phase 2: Convert (should still succeed)
            converter = MathpixPDFConverter(app_id="test", app_key="test")
            pdf_path = tmpdir / "output.pdf"

            convert_result = await converter.convert(
                mmd=merge_result.content,
                output_path=pdf_path,
            )

            assert convert_result.success is True

    @pytest.mark.asyncio
    async def test_pipeline_empty_input(
        self,
        mock_mathpix_api,
        mock_pdfplumber,
    ):
        """Test pipeline with empty input files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            layout_path = tmpdir / "layout.json"
            content_path = tmpdir / "content.json"

            layout_data = {
                "elements": [],
                "page": {"width": 100, "height": 100, "page_number": 1, "total_pages": 1},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 0, "hierarchy_depth": 0},
            }

            content_data = {
                "elements": [],
                "quality_summary": {"total_elements": 0},
                "metadata": {"source": "test", "version": "1.0.0", "element_count": 0},
            }

            layout_path.write_text(json.dumps(layout_data))
            content_path.write_text(json.dumps(content_data))

            # Phase 1: Merge empty
            merger = MMDMerger()
            merge_result = await merger.merge_files(layout_path, content_path)

            assert merge_result.element_count == 0
            assert merge_result.content == ""

            # Phase 2: Would normally fail with empty MMD
            # But we verify the merge handles empty gracefully


class TestE2EPipelineErrorHandling:
    """Test error handling in the pipeline."""

    @pytest.mark.asyncio
    async def test_merge_failure_stops_pipeline(self):
        """Test that merge failure prevents further processing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            merger = MMDMerger()

            # Should fail on missing files
            with pytest.raises(FileNotFoundError):
                await merger.merge_files(
                    layout_path=tmpdir / "nonexistent_layout.json",
                    content_path=tmpdir / "nonexistent_content.json",
                )

    @pytest.mark.asyncio
    async def test_convert_failure_handling(self):
        """Test converter failure handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()

            # Simulate API failure
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"

            mock_instance.post = AsyncMock(return_value=mock_response)
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=None)
            mock_client.return_value = mock_instance

            converter = MathpixPDFConverter(app_id="test", app_key="test")

            with tempfile.TemporaryDirectory() as tmpdir:
                result = await converter.convert(
                    mmd="# Test",
                    output_path=Path(tmpdir) / "output.pdf",
                )

                assert result.success is False
                assert "API error: 500" in result.error


class TestE2EPipelineIntegrationWithMCPTools:
    """Test the pipeline as it would be called via MCP tools."""

    @pytest.fixture
    def layout_path(self) -> Path:
        """Path to sample layout fixture."""
        return FIXTURES_DIR / "sample_layout.json"

    @pytest.fixture
    def content_path(self) -> Path:
        """Path to sample content fixture."""
        return FIXTURES_DIR / "sample_content.json"

    @pytest.mark.asyncio
    async def test_mcp_tool_merge_flow(self, layout_path, content_path):
        """Test merge_to_mmd tool flow."""
        # Import the MCP tool function
        from cow_cli.pdf.merger import MMDMerger

        with tempfile.TemporaryDirectory() as tmpdir:
            # Simulate what merge_to_mmd tool does
            merger = MMDMerger()
            result = await merger.merge_files(
                layout_path=layout_path,
                content_path=content_path,
                output_path=Path(tmpdir) / "output.mmd",
            )

            # Verify MCP-compatible response structure
            response = {
                "success": True,
                "mmd_content": result.content,
                "element_count": result.element_count,
                "output_path": str(result.output_path),
                "warnings": result.warnings,
            }

            assert response["success"] is True
            assert isinstance(response["mmd_content"], str)
            assert isinstance(response["element_count"], int)
            assert isinstance(response["warnings"], list)

    @pytest.mark.asyncio
    async def test_orchestration_pattern(
        self,
        layout_path,
        content_path,
    ):
        """
        Test the Claude Assistor orchestration pattern:
        1. Analyze B1 outputs
        2. Call merge_to_mmd
        3. Review merge result
        4. Call convert_to_pdf
        5. Call validate_reconstruction
        6. Report results
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # STEP 1: Analyze (Claude would do this)
            layout_data = json.loads(layout_path.read_text())
            content_data = json.loads(content_path.read_text())

            analysis = {
                "layout_elements": len(layout_data.get("elements", [])),
                "content_elements": len(content_data.get("elements", [])),
                "low_confidence_count": sum(
                    1 for e in content_data.get("elements", [])
                    if e.get("quality", {}).get("confidence", 1.0) < 0.75
                ),
            }

            assert analysis["layout_elements"] == 4
            assert analysis["content_elements"] == 4
            assert analysis["low_confidence_count"] == 0

            # STEP 2: Merge
            merger = MMDMerger()
            merge_result = await merger.merge_files(
                layout_path, content_path, tmpdir / "merged.mmd"
            )

            # STEP 3: Review merge result (Claude decision point)
            if merge_result.warnings:
                # Claude would log warnings and decide whether to proceed
                pass

            assert merge_result.element_count >= analysis["layout_elements"] - 1

            # STEP 4: Convert (mocked)
            with patch("httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "status": "completed",
                    "pdf_url": "https://test.pdf",
                    "pdf_id": "orch-test",
                }
                mock_pdf = MagicMock()
                mock_pdf.status_code = 200
                mock_pdf.content = b"%PDF"
                mock_instance.post = AsyncMock(return_value=mock_response)
                mock_instance.get = AsyncMock(return_value=mock_pdf)
                mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
                mock_instance.__aexit__ = AsyncMock(return_value=None)
                mock_client.return_value = mock_instance

                converter = MathpixPDFConverter(app_id="test", app_key="test")
                convert_result = await converter.convert(
                    merge_result.content,
                    tmpdir / "output.pdf",
                )

            assert convert_result.success is True

            # STEP 5: Validate (mocked)
            with patch("cow_cli.pdf.validator.pdfplumber") as mock_pdf:
                mock_page = MagicMock()
                mock_page.extract_text.return_value = merge_result.content
                mock_pdf_obj = MagicMock()
                mock_pdf_obj.pages = [mock_page]
                mock_pdf_obj.__enter__ = MagicMock(return_value=mock_pdf_obj)
                mock_pdf_obj.__exit__ = MagicMock(return_value=None)
                mock_pdf.open.return_value = mock_pdf_obj

                validator = ReconstructionValidator()
                validation_result = await validator.validate(
                    tmpdir / "output.pdf",
                    layout_path,
                    content_path,
                )

            # STEP 6: Report (Claude would do this)
            report = {
                "status": "completed",
                "merge": {
                    "element_count": merge_result.element_count,
                    "warnings": merge_result.warnings,
                },
                "convert": {
                    "success": convert_result.success,
                    "pdf_path": str(convert_result.pdf_path),
                },
                "validation": {
                    "valid": validation_result.valid,
                    "scores": {
                        "text": validation_result.text_coverage,
                        "math": validation_result.math_coverage,
                        "layout": validation_result.layout_order_score,
                    },
                    "needs_human_review": validation_result.needs_human_review(),
                },
            }

            assert report["status"] == "completed"
            assert report["convert"]["success"] is True

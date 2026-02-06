"""
E2E Test Fixtures and Configuration.
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from cow_cli.semantic.schemas import (
    SeparatedDocument,
    LayoutData,
    ContentData,
    LayoutElement,
    ContentElement,
    ElementType,
    Region,
    QualityMetrics,
    LayoutMetadata,
    ContentMetadata,
    QualitySummary,
    PageInfo,
)
from cow_cli.mathpix.schemas import MathpixResponse
from cow_cli.pipeline.processor import PipelineResult, StageResult


@pytest.fixture
def e2e_temp_dir():
    """Create a temporary directory for E2E tests."""
    with tempfile.TemporaryDirectory(prefix="cow_e2e_") as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_png_bytes():
    """Minimal valid PNG data (1x1 white pixel)."""
    return bytes([
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


@pytest.fixture
def create_test_image(e2e_temp_dir, sample_png_bytes):
    """Factory to create test images."""
    def _create(name: str = "test.png") -> Path:
        img_path = e2e_temp_dir / name
        img_path.write_bytes(sample_png_bytes)
        return img_path
    return _create


@pytest.fixture
def mock_mathpix_response():
    """Create a mock Mathpix API response."""
    return {
        "request_id": "test-request-123",
        "text": "\\frac{a^2 + b^2}{c^2} = 1",
        "latex": "\\frac{a^2 + b^2}{c^2} = 1",
        "latex_styled": "\\frac{a^{2} + b^{2}}{c^{2}} = 1",
        "confidence": 0.95,
        "confidence_rate": 0.92,
        "line_data": [
            {
                "type": "math",
                "cnt": [[0, 0], [100, 0], [100, 50], [0, 50]],
                "text": "\\frac{a^2 + b^2}{c^2} = 1",
                "confidence": 0.95,
            }
        ],
    }


@pytest.fixture
def mock_separated_document(e2e_temp_dir):
    """Create a mock SeparatedDocument."""
    def _create(image_path: str = "/test/image.png", confidence: float = 0.95):
        layout = LayoutData(
            elements=[
                LayoutElement(
                    id="elem-1",
                    type=ElementType.MATH,
                    region=Region(top_left_x=0, top_left_y=0, width=200, height=100),
                ),
            ],
            page=PageInfo(width=800, height=600),
            metadata=LayoutMetadata(element_count=1),
        )

        content = ContentData(
            elements=[
                ContentElement(
                    id="elem-1",
                    layout_ref="elem-1",
                    text="a² + b² = c²",
                    latex="a^2 + b^2 = c^2",
                    quality=QualityMetrics(confidence=confidence, confidence_rate=confidence),
                ),
            ],
            metadata=ContentMetadata(element_count=1),
        )
        content.compute_quality_summary()

        return SeparatedDocument(
            image_path=image_path,
            layout=layout,
            content=content,
            request_id="test-request-123",
        )

    return _create


@pytest.fixture
def mock_pipeline_result(mock_separated_document):
    """Create a mock successful pipeline result."""
    def _create(image_path: str = "/test/image.png", success: bool = True, confidence: float = 0.95):
        if success:
            doc = mock_separated_document(image_path, confidence)
            return PipelineResult(
                image_path=image_path,
                success=True,
                document=doc,
                stages=[
                    StageResult(stage="A", success=True, duration_ms=50),
                    StageResult(stage="B", success=True, duration_ms=1200),
                    StageResult(stage="C0", success=True, duration_ms=30),
                ],
                total_duration_ms=1280,
            )
        else:
            return PipelineResult(
                image_path=image_path,
                success=False,
                error="Mock pipeline error",
                stages=[
                    StageResult(stage="A", success=True, duration_ms=50),
                    StageResult(stage="B", success=False, error="API error", duration_ms=500),
                ],
                total_duration_ms=550,
            )

    return _create


@pytest.fixture
def mock_mathpix_client(mock_mathpix_response):
    """Create a mock MathpixClient."""
    client = MagicMock()
    client.process_image = AsyncMock(return_value=MathpixResponse(**mock_mathpix_response))
    return client

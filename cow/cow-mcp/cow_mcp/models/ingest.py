"""IngestResult for Stage 1→2 transition."""

from pydantic import BaseModel, Field
from typing import Literal, Optional

from cow_mcp.models.common import Dimensions


class IngestResult(BaseModel):
    """Output of INGEST stage. Input to OCR stage."""
    file_path: str = Field(..., description="Validated input file path")
    file_type: Literal["image", "pdf"]
    page_count: int = Field(1, ge=1, description="1 for images, 1-2 for PDFs")
    dimensions: Dimensions
    preprocessed_path: str = Field(..., description="Normalized image/PDF path")
    dpi: Optional[int] = Field(None, description="Detected DPI if available")
    color_space: Optional[str] = Field(None, description="RGB, CMYK, Grayscale")

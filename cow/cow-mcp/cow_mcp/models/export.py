"""ExportResult — final pipeline output."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class ExportResult(BaseModel):
    """Output of EXPORT stage. Final pipeline result."""
    pdf_path: str
    method: Literal["xelatex", "mathpix_converter"]
    page_count: int = Field(..., ge=1)
    compilation_log: str = Field("", description="XeLaTeX compilation output")
    warnings: list[str] = Field(default_factory=list)
    file_size_bytes: Optional[int] = None


class LatexSource(BaseModel):
    """Generated LaTeX source document."""
    content: str = Field(..., description="Complete LaTeX source")
    preamble: str = Field(..., description="Document preamble")
    body: str = Field(..., description="Document body")
    packages: list[str] = Field(default_factory=list, description="Required packages")

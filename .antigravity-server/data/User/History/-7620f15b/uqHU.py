from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field

# --- Sub-Models ---

class Geometry(BaseModel):
    """Physical location of the block on the page."""
    page_num: int = Field(..., description="1-based page number")
    bbox: List[Union[int, float]] = Field(..., description="[x, y, w, h] in percentage (0-100) or pixels")
    confidence: Optional[float] = Field(None, description="Confidence score 0.0-1.0")

class Style(BaseModel):
    """Visual presentation attributes."""
    alignment: Optional[Literal["left", "center", "right", "justify"]] = None
    font_weight: Optional[Literal["normal", "bold"]] = None
    font_size: Optional[str] = Field(None, description="e.g., '12pt'")
    font_family: Optional[str] = None
    # Layout params (for editing)
    margin_top: Optional[str] = None
    margin_bottom: Optional[str] = None
    padding: Optional[str] = None
    background_color: Optional[str] = None
    border: Optional[str] = None

class Content(BaseModel):
    """The actual data."""
    text: Optional[str] = None
    latex: Optional[str] = None
    src: Optional[str] = None # For images
    table_data: Optional[List[List[str]]] = None # For tables (2D array)

# --- Core Model ---

class Block(BaseModel):
    """An atomic unit of the document."""
    id: str = Field(..., description="Unique ID, e.g., 'p1_b1'")
    type: Literal["text", "header", "math", "table", "image"]
    role: Optional[Literal["title", "question", "body", "caption"]] = "body"
    content: Content
    style: Style = Field(default_factory=Style)
    geometry: Optional[Geometry] = None

class GlobalSettings(BaseModel):
    """Document-wide configuration."""
    page_dimensions: Dict[str, Union[int, str]] = Field(
        default_factory=lambda: {"width": 210, "height": 297, "unit": "mm"}
    )
    base_font: str = "Malgun Gothic"
    base_font_size: str = "10pt"
    global_padding: str = "20mm"

class Page(BaseModel):
    """A single page containing blocks."""
    page_num: int
    blocks: List[Block] = Field(default_factory=list)

class DigitalTwin(BaseModel):
    """The Root Document Object Model."""
    document_id: str
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    pages: List[Page] = Field(default_factory=list)

    def get_block(self, block_id: str) -> Optional[Block]:
        """Find a block by ID."""
        for page in self.pages:
            for block in page.blocks:
                if block.id == block_id:
                    return block
        return None

    def query_blocks(self, **criteria) -> List[Block]:
        """Simple query mechanism (e.g. role='question')."""
        results = []
        for page in self.pages:
            for block in page.blocks:
                match = True
                for key, value in criteria.items():
                    if getattr(block, key, None) != value:
                        match = False
                        break
                if match:
                    results.append(block)
        return results

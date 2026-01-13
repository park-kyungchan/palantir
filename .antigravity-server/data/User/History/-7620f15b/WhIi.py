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

# --- Rich Content Models ---

class Run(BaseModel):
    type: Literal["Text", "Equation", "Image"]
    text: Optional[str] = None
    script: Optional[str] = None # For Equation
    path: Optional[str] = None   # For Image
    width: Optional[int] = None
    height: Optional[int] = None
    style: Optional[Style] = None

class Paragraph(BaseModel):
    runs: List[Run] = Field(default_factory=list)
    style: Optional[Style] = None

class Cell(BaseModel):
    row: int
    col: int
    paragraphs: List[Paragraph] = Field(default_factory=list)
    # content: List[Union[Run, Paragraph]] ? 
    # Usually Cell -> Paragraphs -> Runs.
    # Our simple JSON used content -> Runs directly.
    # Let's support generic 'content' which converts to Paragraphs.
    content: Optional[List[Run]] = None 
    
    def model_post_init(self, __context):
        # normalize content to paragraphs if needed
        if self.content and not self.paragraphs:
            self.paragraphs = [Paragraph(runs=self.content)]

class TableRow(BaseModel):
    cells: List[Cell] = Field(default_factory=list)

class Table(BaseModel):
    rows: List[TableRow] = Field(default_factory=list)
    style: Optional[Style] = None

class Figure(BaseModel):
    content_type: Literal["image", "chart"]
    src: str
    width: Optional[int] = None
    height: Optional[int] = None
    
# --- Block Definition Update ---
# We need to support Block being a Table or Paragraph Wrapper
# Or Compiler uses 'Section.elements' which are Union[Paragraph, Table]

class CodeBlock(BaseModel):
    text: str
    language: Optional[str] = None

class Container(BaseModel):
    elements: List[Any] = Field(default_factory=list) 

class MultiColumnContainer(BaseModel):
    columns: List[Any]
    col_gap: int = 0

class Section(BaseModel):
    elements: List[Union[Paragraph, Table, Figure, Container, MultiColumnContainer, CodeBlock]] = Field(default_factory=list)
    page_setup: Optional[Dict[str, Any]] = None
    columns: int = 1
    col_gap: int = 0

# --- Legacy / Block Support for Page-based Twin ---

class Block(BaseModel):
    """An atomic unit of the document."""
    id: str = Field(..., description="Unique ID, e.g., 'p1_b1'")
    type: Literal["text", "header", "math", "table", "image", "Text", "Equation", "Table"] # Added aliases
    role: Optional[Literal["title", "question", "body", "caption"]] = "body"
    content: Any # Relaxed for now
    style: Style = Field(default_factory=Style)
    geometry: Optional[Geometry] = None

class Page(BaseModel):
    """A single page containing blocks."""
    page_num: int
    blocks: List[Block] = Field(default_factory=list)

class DigitalTwin(BaseModel):

    """The Root Document Object Model."""
    document_id: str
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
    sections: List[Section] = Field(default_factory=list)
    pages: Optional[List[Page]] = None # Legacy support
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

# Implementation: Digital Twin Pydantic Schema

The Digital Twin is implemented as a hierarchy of Pydantic models in `lib/digital_twin/schema.py`. This provides robust validation and a rich API for document manipulation.

## 1. Model Hierarchy

- **DigitalTwin (Root)**: The entry point. Contains `document_id`, `global_settings`, and a list of `pages`.
- **Page**: Represents a single document division, containing a list of `Block` objects.
- **Block**: The atomic unit of the document.
    - `type`: "text", "header", "math", "table", "image".
    - `role`: "title", "question", "body", "caption".
    - `content`: An object containing raw data (text, latex, table_data).
    - `style`: An object containing presentation metadata (alignment, padding, margins).
    - `geometry`: An object containing physical coordinates (`bbox`) and `confidence` scores.

## 2. Logical Components

### 2.1 Style Object
The `Style` model handles visual presentation. It is designed to be extensible, allowing the addition of new properties (like `background_color` or `border`) without breaking the schema.

### 2.2 Content Object
The `Content` model uses optional fields to handle heterogeneous data types. This allows a single `Block` type to represent a complex math problem (text + latex) or a grid-perfect table (2D array).

### 2.3 Geometry & Verification
The `Geometry` model stores bounding boxes. This is critical for the "Read-Verify-Write" loop, where the system checks if a new block's coordinates approximate the original PDF's layout.

## 3. Query & Manipulation API

The schema includes utility methods for document engineering:
- `get_block(block_id)`: Instant access to specific atoms.
- `query_blocks(**criteria)`: Selects blocks by role, type, or other metadata for batch processing (e.g., adding padding to all "questions").

## 4. Concrete Implementation

```python
from typing import List, Optional, Union, Dict, Any, Literal
from pydantic import BaseModel, Field

# --- Sub-Models ---

class Geometry(BaseModel):
    page_num: int
    bbox: List[Union[int, float]]
    confidence: Optional[float] = None

class Style(BaseModel):
    alignment: Optional[Literal["left", "center", "right", "justify"]] = None
    font_weight: Optional[Literal["normal", "bold"]] = None
    font_size: Optional[str] = None
    font_family: Optional[str] = None
    border: Optional[str] = None # e.g., "none"

class Run(BaseModel):
    type: Literal["Text", "Equation", "Image"]
    text: Optional[str] = None
    script: Optional[str] = None # For Equation
    path: Optional[str] = None   # For Image
    style: Optional[Style] = None

class Paragraph(BaseModel):
    runs: List[Run] = Field(default_factory=list)
    style: Optional[Style] = None

class Cell(BaseModel):
    row: int
    col: int
    paragraphs: List[Paragraph] = Field(default_factory=list)
    content: Optional[List[Run]] = None # Alias for simple ingestion

class TableRow(BaseModel):
    cells: List[Cell] = Field(default_factory=list)

class Table(BaseModel):
    rows: List[TableRow] = Field(default_factory=list)
    style: Optional[Style] = None

# --- Core Model ---

class Section(BaseModel):
    elements: List[Union[Paragraph, Table, Figure, Container]] = Field(default_factory=list)

class DigitalTwin(BaseModel):
    document_id: str
    global_settings: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Section] = Field(default_factory=list)
```
## 5. Intermediate Representation (IR) Integration
The Digital Twin serves as the platform-independent **Intermediate Representation (IR)**. It allows the pipeline to translate various input formats into a common structure for reconstruction.

### 5.1 IR Core Elements
- **Run**: Replaces legacy `TextRun`. Captures atomic data types via `type` attribute:
    - `Text`: Captures `text` content, `font_size`, and `font_weight`.
    - `Equation`: Replaces legacy `Equation` class. Captures formula via `script`.
    - `Image`: Captures `path`, `width`, and `height`.
- **Table**: Mapped to the hierarchical `Table` model with `TableRow` and `Cell` components.

### 5.2 Implementation Data Flow
1. **Ingestion**: Hybrid Ingestors (Layout/Text/Vision) convert source items into Digital Twin `Block` objects.
2. **Serializing**: The Digital Twin is serialized to JSON to be passed across the WSL-Windows bridge.
3. **Reconstruction**: `HwpCompiler` (Windows side) parses the Digital Twin and executes OLE actions to rebuild the document.

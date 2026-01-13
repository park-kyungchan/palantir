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

class Geometry(BaseModel):
    page_num: int
    bbox: List[Union[int, float]]
    confidence: Optional[float] = None

class Style(BaseModel):
    alignment: Optional[Literal["left", "center", "right", "justify"]] = None
    font_weight: Optional[Literal["normal", "bold"]] = None
    font_size: Optional[str] = None
    margin_top: Optional[str] = None
    margin_bottom: Optional[str] = None
    padding: Optional[str] = None
    border: Optional[str] = None

class Content(BaseModel):
    text: Optional[str] = None
    latex: Optional[str] = None
    src: Optional[str] = None
    table_data: Optional[List[List[str]]] = None

class Block(BaseModel):
    id: str
    type: Literal["text", "header", "math", "table", "image"]
    role: Optional[Literal["title", "question", "body", "caption"]] = "body"
    content: Content
    style: Style = Field(default_factory=Style)
    geometry: Optional[Geometry] = None

class DigitalTwin(BaseModel):
    document_id: str
    global_settings: Dict[str, Any] = Field(default_factory=dict)
    pages: List[Page] = Field(default_factory=list)
```

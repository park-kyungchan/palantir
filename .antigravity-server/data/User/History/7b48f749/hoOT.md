# Implementation: Intermediate Representation (IR) Schema

The Intermediate Representation (IR) is the platform-independent document model used as the bridge between PDF Ingestion and HWPX Reconstruction. It is implemented in `lib/ir.py` using Python **dataclasses** for performance and simplicity in internal processing.

## 1. Model Hierarchy

The IR follows a hierarchical structure to represent document semantics and layout:

- **Document (Root)**: Contains a list of `Section` objects.
- **Section**: Represents a major division (e.g., page layout).
    - `elements`: A mixed-content list of `Paragraph`, `Table`, `Figure`, `Container`, or `MultiColumnContainer`.
    - `page_setup`: Dict containing margins and dimensions.
- **Paragraph**: A block of content.
    - `elements`: List of `TextRun`, `Equation`, `Image`, etc.
    - `alignment` and `line_spacing` settings.
- **Container**: A generic layout container for absolute-positioned regions or text boxes.
- **MultiColumnContainer**: Handles complex reading orders within a section using multiple `Column` objects.

## 2. Content Elements

- **TextRun**: A continuous run of text with consistent formatting (`font_size`, `is_bold`, `font_name`).
- **Equation**: A math formula container holding a `script` (LaTeX or HWP format).
- **Image / Figure**: References to external or embedded visual assets with optional `caption` and dimensions.
- **Table**: A structured grid containing `TableRow` and `TableCell`. Supports `rowspan` and `colspan`.

## 3. Concrete Implementation (`lib/ir.py`)

```python
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any

@dataclass
class TextRun:
    text: str
    font_size: Optional[float] = None
    is_bold: Optional[bool] = None

@dataclass
class Equation:
    script: str # Latex or HWP Script

@dataclass
class Section:
    elements: List[Union[Paragraph, Table, Figure, Container, MultiColumnContainer]] = field(default_factory=list)
    columns: int = 1
    page_setup: Optional[Dict[str, int]] = None

@dataclass
class Document:
    sections: List[Section] = field(default_factory=list)
```

## 4. Digital Twin Synergy

While the IR is implemented as dataclasses for internal pipeline efficiency, it serves as the **Digital Twin** (SVDOM) of the source document.
- **High-Fidelity**: Preserves visual metadata (coordinates, font sizes) from the ingestor.
- **Compiler Ready**: The `HwpCompiler` iterates through the IR `Section` and `elements` to emit OLE Automation `HwpAction` models.

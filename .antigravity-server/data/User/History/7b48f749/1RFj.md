The Intermediate Representation (IR) is the platform-independent document model used as the bridge between PDF Ingestion and HWPX Reconstruction. In ODA v6.0, this is implemented as the **Digital Twin (SVDOM)** using Pydantic models in `lib/digital_twin/schema.py` for strict validation and serialization.

- **DigitalTwin (Root)**: The SVDOM entry point. Contains `sections`, `global_settings`, and legacy `pages`.
- **Section**: Represents a major divisions (e.g. Page or Chapter).
    - `elements`: A polymorphic list of `Paragraph`, `Table`, `Figure`, `Container`, `MultiColumnContainer`, or `CodeBlock`.
- **Paragraph**: A block of text/math content.
    - `runs`: List of `Run` objects.
    - `style`: Critical semantic field, supporting `Union[Style, str]` to allow high-level tags like "ProblemBox" to coexist with structured `Style` objects.
- **Run**: Atomic content unit. Types: `Text`, `Equation` (LaTeX/HWP), `Image`.
- **Table**: Structured grid with recursive `paragraphs` inside `Cell` objects.

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Union, Any, Literal

class Style(BaseModel):
    alignment: Optional[Literal["left", "center", "right", "justify"]] = None
    font_weight: Optional[Literal["normal", "bold"]] = None
    font_size: Optional[str] = None

class Run(BaseModel):
    type: Literal["Text", "Equation", "Image"]
    text: Optional[str] = None
    script: Optional[str] = None # For Equation
    path: Optional[str] = None

class Paragraph(BaseModel):
    runs: List[Run] = Field(default_factory=list)
    style: Optional[Union[Style, str]] = None

class Section(BaseModel):
    elements: List[Union[Paragraph, Table, Figure, Container, MultiColumnContainer, CodeBlock]] = Field(default_factory=list)
    page_setup: Optional[Dict[str, Any]] = None

class DigitalTwin(BaseModel):
    document_id: str
    sections: List[Section] = Field(default_factory=list)
```

## 4. Schema Convergence and Compatibility
Despite the transition to Pydantic for the Digital Twin, the system maintains compatibility with the legacy `lib.ir` dataclasses via the **Compiler Layer**.
- **Ingestion Output**: `DoclingIngestor` natively produces `lib.ir` dataclasses (e.g., using `Paragraph.elements`).
- **Compiler Mapping**: `lib/compiler.py` reconciles discrepancies such as `runs` vs `elements` and `Style` object vs `str` tags using duck-typing and `getattr` fallback logic.
- **High-Fidelity**: Preserves visual metadata (coordinates, font sizes) from the ingestor.
- **Compiler Ready**: The `HwpCompiler` iterates through the IR `Section` and `elements` to emit OLE Automation `HwpAction` models.

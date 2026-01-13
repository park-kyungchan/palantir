
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict, Any

@dataclass
class TextRun:
    """Represents a continuous run of text with same formatting."""
    text: str
    font_size: Optional[float] = None # Points
    is_bold: Optional[bool] = None
    letter_spacing: Optional[int] = None # Percentage or HWP Units
    font_name: Optional[str] = None

@dataclass
class Equation:
    """Represents a Math Formula."""
    script: str # Latex or HWP Script
    
@dataclass
class Image:
    """Represents an embedded image."""
    path: str
    width: Optional[int] = None # mm
    height: Optional[int] = None # mm

@dataclass
class TableCell:
    content: List[Union['TextRun', 'Equation', 'Image']] = field(default_factory=list)
    colspan: int = 1
    rowspan: int = 1
    is_header: bool = False

@dataclass
class TableRow:
    cells: List[TableCell] = field(default_factory=list)

@dataclass
class Table:
    rows: List[TableRow] = field(default_factory=list)
    caption: Optional[str] = None
    width: Optional[int] = None # mm
    bbox: Optional[tuple] = None

@dataclass
class Figure:
    path: str
    caption: Optional[str] = None
    rows: int = 0
    cols: int = 0
    data: list = None
    bbox: tuple = None
    width: Optional[int] = None
    height: Optional[int] = None

@dataclass
class CodeBlock:
    content: str
    style: str = "Regular"
    bbox: tuple = None # (x1, y1, x2, y2)
    language: Optional[str] = None

@dataclass
class Paragraph:
    """Represents a block of content."""
    elements: List[Union[TextRun, Equation, Image, Table, Figure, CodeBlock]] = field(default_factory=list)
    style: str = "Body"
    bbox: tuple = None
    alignment: Optional[str] = None # Left, Center, Right, Justify
    line_spacing: Optional[int] = None # Percentage

    def add_run(self, run: Union[TextRun, Equation, Image, Table, Figure, CodeBlock]):
        self.elements.append(run)


@dataclass
class Container:
    """Generic layout container (e.g. text box, absolute positioned region)."""
    elements: List[Union['Paragraph', 'Table', 'Figure', 'Container', 'MultiColumnContainer']] = field(default_factory=list)
    width: Optional[int] = None # mm
    height: Optional[int] = None # mm
    x: Optional[int] = None # absolute pos if set
    y: Optional[int] = None
    style: Optional[Dict[str, Any]] = None

@dataclass
class Column:
    """A single column within a multi-column section."""
    elements: List[Union['Paragraph', 'Table', 'Figure', 'Container']] = field(default_factory=list)
    width: Optional[int] = None # mm

@dataclass
class MultiColumnContainer:
    """Container for multi-column content."""
    columns: List[Column] = field(default_factory=list)
    col_gap: int = 3000 # HWP units? or mm? consistent with Section.col_gap

@dataclass
class SideNote:
    """Marginalia or side note content."""
    content: List[Union['Paragraph', 'Container']] = field(default_factory=list)
    position: str = "right" # left, right
    width: Optional[int] = None

@dataclass
class Section:
    """Represents a major division (Page layout)."""
    # Expanded to support Containers and MultiColumn structures directly
    elements: List[Union[Paragraph, Table, Figure, Container, MultiColumnContainer]] = field(default_factory=list)
    
    # Legacy support (deprecated but kept for backward compat if needed, or mapped)
    # paragraphs: List[Paragraph] ... let's keep 'elements' as the main list now.
    # To maintain backward compat for now, we can make 'paragraphs' a property or just update the type hint if usages are few.
    # For this refactor, let's keep 'paragraphs' field but deprecate it, OR switch to 'elements'.
    # Given we have control, let's switch to 'elements' and update usages in next step or now?
    # Trying to be non-breaking if possible? 
    # Let's add 'elements' and make 'paragraphs' alias to filters?
    # No, 'paragraphs' was the storage.
    # Let's rename 'paragraphs' to 'elements' in the class and update aliases.
    # BUT, 'Paragraph' is just one type.
    
    # Actually, let's keep `paragraphs` for simple list but add `content` for mixed?
    # Or just start using `elements` and remove `paragraphs`. 
    # 'docling_ingestor.py' usage: section.paragraphs.append(...)
    # I should update `docling_ingestor` if I rename.
    # Let's add `elements` and make `paragraphs` a property that returns only paragraphs?
    # Or better, just make `elements` the source of truth.
    
    # elements: List[Any] = field(default_factory=list) # Removed duplicate
    
    # Page setup
    columns: int = 1 # properties of the section's *default* flow
    col_gap: int = 3000
    page_setup: Optional[Dict[str, int]] = None

    @property
    def paragraphs(self) -> List[Paragraph]:
        return [e for e in self.elements if isinstance(e, Paragraph)]

    def add_paragraph(self) -> Paragraph:
        p = Paragraph()
        self.elements.append(p)
        return p
        
    def add_container(self) -> Container:
        c = Container()
        self.elements.append(c)
        return c

@dataclass
class Document:
    """Root of the Intermediate Representation."""
    sections: List[Section] = field(default_factory=list)

    def add_section(self) -> Section:
        sec = Section()
        self.sections.append(sec)
        return sec


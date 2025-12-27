
from dataclasses import dataclass, field
from typing import List, Optional, Union, Dict

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
class Paragraph:
    """Represents a block of content."""
    elements: List[Union[TextRun, Equation, Image]] = field(default_factory=list)
    alignment: Optional[str] = None # Left, Center, Right, Justify
    line_spacing: Optional[int] = None # Percentage

@dataclass
class Section:
    """Represents a major division (Page layout)."""
    paragraphs: List[Paragraph] = field(default_factory=list)
    columns: int = 1
    col_gap: int = 3000
    page_setup: Optional[Dict[str, int]] = None # left, right, top, bottom in mm

@dataclass
class Document:
    """Root of the Intermediate Representation."""
    sections: List[Section] = field(default_factory=list)

    def add_section(self) -> Section:
        sec = Section()
        self.sections.append(sec)
        return sec

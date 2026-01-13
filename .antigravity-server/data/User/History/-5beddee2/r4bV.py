
from pydantic import BaseModel, Field
from typing import Optional, Literal

class HwpAction(BaseModel):
    """
    Base Ontology Object for all HWP Actions.
    All actions must inherit from this and define their parameters strictly.
    """
    action_type: str = Field(..., description="The internal API name of the action (e.g., InsertText, CreateTable)")

class InsertCodeBlock(HwpAction):
    """
    Action to insert a Code Block.
    """
    action_type: Literal["InsertCodeBlock"] = "InsertCodeBlock"
    text: str = Field(..., description="Code content")
    language: Optional[str] = Field(None, description="Programming language")

class InsertCaption(HwpAction):
    """
    Action to insert a caption.
    """
    action_type: Literal["InsertCaption"] = "InsertCaption"
    text: str = Field(..., description="Caption text")


class InsertText(HwpAction):
    """
    Action to insert text at the current cursor position.
    """
    action_type: Literal["InsertText"] = "InsertText"
    text: str = Field(..., description="The text content to insert")

class CreateTable(HwpAction):
    """
    Action to create a table.
    Derived from HWP API 'TableCreate' action.
    """
    action_type: Literal["CreateTable"] = "CreateTable"
    rows: int = Field(5, ge=1, description="Number of rows")
    cols: int = Field(5, ge=1, description="Number of columns")
    width_type: int = Field(2, description="0=Auto, 1=Variable, 2=Fixed")
    height_type: int = Field(2, description="0=Auto, 1=Variable, 2=Fixed")

class SetCellBorder(HwpAction):
    """
    Action to set cell border/fill properties.
    Maps to 'CellBorderFill' action.
    """
    action_type: Literal["SetCellBorder"] = "SetCellBorder"
    border_type: str = Field("Solid", description="Border Type: Solid, None, Dash, etc.")
    width: str = Field("0.1mm", description="Border Width")
    color: str = Field("Black", description="Border Color")
    
class InsertEquation(HwpAction):
    """
    Action to insert a Math Equation.
    """
    action_type: Literal["InsertEquation"] = "InsertEquation"
    script: str = Field(..., description="The Equation Script (e.g. 'x^2 + y^2 = r^2')")
    script: str = Field(..., description="The Equation Script (e.g. 'x^2 + y^2 = r^2')")

class MoveToCell(HwpAction):
    """
    Action to move cursor to a specific table cell.
    Used after CreateTable to populate cell content.
    """
    action_type: Literal["MoveToCell"] = "MoveToCell"
    row: int = Field(..., ge=0, description="Row index (0-based)")
    col: int = Field(..., ge=0, description="Column index (0-based)")

class FileSaveAs(HwpAction):
    """
    Action to save the file with a specific format.
    """
    action_type: Literal["FileSaveAs"] = "FileSaveAs"
    path: str = Field(..., description="Target file path (absolute)")
    format: str = Field("HWP", description="File format: HWP, HWPX, PDF")

class InsertImage(HwpAction):
    """
    Action to insert an image.
    """
    action_type: Literal["InsertImage"] = "InsertImage"
    path: str = Field(..., description="Path to the image file (absolute)")
    width: Optional[int] = Field(None, description="Width in mm (approx)")
    height: Optional[int] = Field(None, description="Height in mm (approx)")
    treat_as_char: bool = Field(True, description="Treat as character (gl-ja-cheo-reom)")

class SetFontSize(HwpAction):
    """
    Action to set font size.
    """
    action_type: Literal["SetFontSize"] = "SetFontSize"
    size: float = Field(..., description="Font size in points (e.g. 10.0, 15.5)")

class SetFontBold(HwpAction):
    """
    Action to toggle bold.
    """
    action_type: Literal["SetFontBold"] = "SetFontBold"
    is_bold: bool = Field(True, description="True for Bold, False for Normal")

class SetAlign(HwpAction):
    """
    Action to set paragraph alignment.
    """
    action_type: Literal["SetAlign"] = "SetAlign"
    align_type: Literal["Left", "Center", "Right", "Justify"] = Field("Left", description="Alignment type")

class Open(HwpAction):
    """
    Action to open an existing file.
    """
    action_type: Literal["Open"] = "Open"
    path: str = Field(..., description="Absolute path to the file")
    format: str = Field("HWP", description="Format hint (e.g. PDF, HWPX)")

class MultiColumn(HwpAction):
    """
    Action to set multi-column layout (ColDef).
    """
    action_type: Literal["MultiColumn"] = "MultiColumn"
    count: int = Field(2, ge=1, le=255, description="Number of columns")
    same_size: bool = Field(True, description="Equal column width")
    gap: int = Field(3000, description="Gap between columns (HWPUNIT). 1mm approx 283 HWPUNITs")

class MoveToField(HwpAction):
    """
    Action to move cursor to a named field (for partial modification).
    """
    action_type: Literal["MoveToField"] = "MoveToField"
    field: str = Field(..., description="Field name (aka Click Here field / Nuri-geul)")
    text: Optional[str] = Field(None, description="Optional text to put into the field")

class SetLetterSpacing(HwpAction):
    """
    Action to set letter spacing (Ja-gan).
    """
    action_type: Literal["SetLetterSpacing"] = "SetLetterSpacing"
    spacing: int = Field(0, ge=-50, le=50, description="Letter spacing percentage (e.g. -5 for tight)")

class SetLineSpacing(HwpAction):
    """
    Action to set line spacing (Jul-gan-gyeok).
    """
    action_type: Literal["SetLineSpacing"] = "SetLineSpacing"
    spacing: int = Field(160, description="Line spacing percentage (e.g. 160, 180)")

class InsertEquation(HwpAction):
    """
    Action to insert a Math Equation.
    """
    action_type: Literal["InsertEquation"] = "InsertEquation"
    script: str = Field(..., description="Equation script (LaTeX or HWP EQ format)")

class SetPageSetup(HwpAction):
    """
    Action to configure Page Margins and Orientation.
    """
    action_type: Literal["SetPageSetup"] = "SetPageSetup"
    left: int = 15 # mm
    right: int = 15
    top: int = 15
    bottom: int = 15
    header: int = 0
    footer: int = 0
    gutter: int = 0

class InsertTextBox(HwpAction):
    """
    Action to insert a Text Box (Gle-sang-ja).
    """
    action_type: Literal["InsertTextBox"] = "InsertTextBox"
    text: str = Field(..., description="Content of the text box")
    width: Optional[int] = Field(None, description="Width in mm")
    height: Optional[int] = Field(None, description="Height in mm")
    x: Optional[int] = Field(None, description="Absolute X position in mm")
    y: Optional[int] = Field(None, description="Absolute Y position in mm")

class BreakColumn(HwpAction):
    """
    Action to force a column break (Dan-nanugi).
    """
    action_type: Literal["BreakColumn"] = "BreakColumn"

class BreakSection(HwpAction):
    """
    Action to force a section break (Gu-yeok-nanugi).
    Used to change layout settings (like column count) mid-page.
    """
    action_type: Literal["BreakSection"] = "BreakSection"
    continuous: bool = Field(True, description="If True, continues on same page. If False, starts new page.")

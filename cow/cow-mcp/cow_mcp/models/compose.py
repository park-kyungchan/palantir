"""CompositionResult for Stage 5→6 transition."""

from pydantic import BaseModel, Field
from typing import Optional, Literal


class EditAction(BaseModel):
    """A single edit action applied during composition."""
    action: Literal["modify_text", "modify_equation", "adjust_layout",
                     "add_element", "remove_element", "reorder"]
    target: str = Field(..., description="Target element description")
    before: Optional[str] = None
    after: Optional[str] = None
    reason: Optional[str] = None


class DocumentMetadata(BaseModel):
    """Document-level metadata for the composition."""
    title: Optional[str] = None
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    source_file: Optional[str] = None


class CompositionResult(BaseModel):
    """Output of COMPOSE stage. Input to EXPORT stage."""
    latex_source: str = Field(..., description="Complete LaTeX document source")
    metadata: DocumentMetadata = Field(default_factory=DocumentMetadata)
    edit_history: list[EditAction] = Field(default_factory=list)
    user_approved: bool = Field(False, description="User approved final composition")

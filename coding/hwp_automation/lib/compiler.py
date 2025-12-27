
from typing import List, Dict, Any
from lib.ir import Document, Section, Paragraph, TextRun, Equation, Image
from lib.models import (
    HwpAction,
    InsertText, SetFontSize, SetFontBold, SetAlign, SetLineSpacing,
    SetLetterSpacing, MultiColumn, InsertEquation, InsertImage,
    FileSaveAs, Open, SetPageSetup
)

class Compiler:
    """
    Translates Intermediate Representation (IR) into HwpAction models.
    """
    def __init__(self):
        self.actions: List[HwpAction] = []
        # State tracking to avoid redundant actions
        self.current_font_size = 10.0
        self.current_bold = False
        self.current_align = "Left"
        self.current_line_spacing = 160
        self.current_letter_spacing = 0

    def compile(self, doc: Document, output_path: str = None) -> List[Dict[str, Any]]:
        self.actions = []
        
        # document-global init?
        
        for section in doc.sections:
            self._compile_section(section)
            
        if output_path:
            self.actions.append(FileSaveAs(path=output_path, format="HWPX"))
            
        return [action.model_dump() for action in self.actions]

    def _compile_section(self, section: Section):
        # 0. Page Setup (Margins)
        if section.page_setup:
            self.actions.append(SetPageSetup(
                left=section.page_setup.get("left", 30),
                right=section.page_setup.get("right", 30),
                top=section.page_setup.get("top", 20),
                bottom=section.page_setup.get("bottom", 15),
                header=section.page_setup.get("header", 15),
                footer=section.page_setup.get("footer", 15),
                gutter=section.page_setup.get("gutter", 0)
            ))

        # 1. Section Layout (Columns)
        if section.columns > 1:
            self.actions.append(MultiColumn(
                count=section.columns,
                gap=section.col_gap,
                same_size=True
            ))
        
        # 2. Iterate Paragraphs
        for para in section.paragraphs:
            self._compile_paragraph(para)
            # End of Paragraph -> Insert Carriage Return to create new HWP Paragraph
            self.actions.append(InsertText(text="\r\n"))
            
    def _compile_paragraph(self, para: Paragraph):
        # Paragraph Init
        # Check Layout properties
        if para.alignment and para.alignment != self.current_align:
            self.actions.append(SetAlign(align_type=para.alignment))
            self.current_align = para.alignment
            
        if para.line_spacing and para.line_spacing != self.current_line_spacing:
            self.actions.append(SetLineSpacing(spacing=para.line_spacing))
            self.current_line_spacing = para.line_spacing
            
        # Iterate Runs (Content)
        for elem in para.elements:
            if isinstance(elem, TextRun):
                self._compile_text_run(elem)
            elif isinstance(elem, Equation):
                self.actions.append(InsertEquation(script=elem.script))
            elif isinstance(elem, Image):
                # TODO: Image resizing logic if 'width' provided
                self.actions.append(InsertImage(
                    path=elem.path, 
                    width=elem.width or 100, # safe default?
                    height=elem.height or 100,
                    treat_as_char=True 
                ))
        
        # End of Paragraph (Enter)
        self.actions.append(InsertText(text="\n"))

    def _compile_text_run(self, run: TextRun):
        # Font Style Updates
        if run.font_size and run.font_size != self.current_font_size:
            self.actions.append(SetFontSize(size=run.font_size))
            self.current_font_size = run.font_size
            
        if run.is_bold is not None and run.is_bold != self.current_bold:
            self.actions.append(SetFontBold(is_bold=run.is_bold))
            self.current_bold = run.is_bold

        if run.letter_spacing is not None and run.letter_spacing != self.current_letter_spacing:
            self.actions.append(SetLetterSpacing(spacing=run.letter_spacing))
            self.current_letter_spacing = run.letter_spacing
            
        # Insert Text
        if run.text:
            self.actions.append(InsertText(text=run.text))

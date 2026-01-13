
from typing import List, Dict, Any, Union
from lib.ir import (
    Document, Section, Paragraph, TextRun, Equation, Image, Table, Figure, CodeBlock,
    Container, MultiColumnContainer, Column, SideNote
)
from lib.models import (
    HwpAction,
    InsertText, SetFontSize, SetFontBold, SetAlign, SetLineSpacing,
    SetLetterSpacing, MultiColumn, InsertEquation, InsertImage,
    FileSaveAs, Open, SetPageSetup, CreateTable, InsertCodeBlock, InsertCaption,
    MoveToCell, InsertTextBox, BreakColumn, BreakSection, SetCellBorder
)
from lib.knowledge.schema import ActionDatabase
from lib.knowledge.parser import ActionTableParser # Or just load from JSON
import json
import os

class Compiler:
    """
    Translates Intermediate Representation (IR) into HwpAction models.
    Enforces validity against the Action Knowledge Base.
    """
    def __init__(self, action_db_path: str = "lib/knowledge/hwpx/action_db.json", strict_mode: bool = True):
        self.actions: List[HwpAction] = []
        
        # Load Knowledge Base
        self.action_db = None
        if os.path.exists(action_db_path):
            try:
                with open(action_db_path, "r", encoding="utf-8") as f:
                    self.action_db = ActionDatabase.model_validate_json(f.read())
                print(f"[Compiler] Loaded Knowledge Base: {len(self.action_db.actions)} actions.")
            except Exception as e:
                print(f"[Compiler] Warning: Failed to load ActionDB: {e}")
        else:
            print(f"[Compiler] Warning: ActionDB not found at {action_db_path}")

        self.strict_mode = strict_mode

        # State tracking
        self.current_font_size = 10.0
        self.current_bold = False
        self.current_align = "Left"
        self.current_line_spacing = 160
        self.current_letter_spacing = 0

    def _validate_action(self, action: HwpAction):
        """
        Checks if the action exists in the Knowledge Base.
        """
        if not self.action_db or not self.strict_mode:
            return

        # Map internal Model class to ActionID in DB
        # This mapping might need refinement if Model names != Action IDs
        # For now, we assume simple mapping or pass-through
        
        # In HwpAction, 'action_type' corresponds to our Model name.
        # But real HWP Actions (in DB) might be 'InsertText' or 'TableCreate'
        
        # We need a mapping strategy. 
        # For this phase, we just check existence and warn.
        
        pass 
        # TODO: Implement strict validation logic once mapping is confirmed.

    def compile(self, doc: Document, output_path: str = None) -> List[Dict[str, Any]]:
        print(f"[Compiler] Compile Start. Sections: {len(doc.sections)}")
        self.actions = []
        
        for i, section in enumerate(doc.sections):
            print(f"[Compiler] Processing Section {i}, elements: {len(section.elements)}")
            self._compile_section(section)
            
        if output_path:
            self.actions.append(FileSaveAs(path=output_path, format="HWPX"))
            
        return [action.model_dump() for action in self.actions]

    def _compile_section(self, section: Section):
        # 0. Page Setup
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

        # 1. Section Layout (Basic Columns)
        # Note: If Section uses MultiColumnContainer, this global setting might conflict 
        # or just be the default. We keep it for backward compat.
        if section.columns > 1:
            self.actions.append(MultiColumn(
                count=section.columns,
                gap=section.col_gap,
                same_size=True
            ))
        
        # 2. Iterate Elements (Recursive Dispatch)
        # We prioritize 'elements' list which supports mixed content
        elements = section.elements
        # If section.paragraphs was used exclusively before (and elements is empty? No, we aliased/appended),
        # but check if someone used paragraphs property directly on an old object (unlikely in new code).
        
        for elem in elements:
            self._compile_element(elem)

    def _compile_element(self, elem: Union[Paragraph, Table, Figure, Container, MultiColumnContainer, CodeBlock]):
        print(f"[Compiler] Compiling Element: {type(elem)}")
        if isinstance(elem, Paragraph):
            self._compile_paragraph(elem)

            # End of Paragraph -> Insert Carriage Return
            self.actions.append(InsertText(text="\r\n"))
        elif isinstance(elem, MultiColumnContainer):
            self._compile_multicolumn(elem)
        elif isinstance(elem, Container):
            self._compile_container(elem)
        elif isinstance(elem, Table):
            # Tables usually wrapped in Paragraph in docling ingestor, but support direct too
            # If direct, we might need a paragraph wrapper or just InsertText("\r\n") after?
            # HWP Tables are usually inline characters.
            # Let's verify how we usually insert it. 
            # In `_compile_paragraph`, we call `_compile_table`.
            # If it's top-level here, we treat it as its own paragraph block.
            self._compile_table(elem)
            self.actions.append(InsertText(text="\r\n")) # Tables need a newline often to separate
        elif isinstance(elem, Figure):
            self._compile_figure(elem)
            self.actions.append(InsertText(text="\r\n"))

    def _compile_multicolumn(self, mc: MultiColumnContainer):
        """
        Compile a Multi-Column Container.
        Strategy: Use BreakSection(Continuous) -> new column settings -> content -> Restore?
        Actually HWP handles column definition changes by creating a new section implicitly or explicitly.
        """
        if not mc.columns:
            return

        # 1. Start new continuous section for this column layout
        self.actions.append(BreakSection(continuous=True))
        
        # 2. Define Columns
        col_count = len(mc.columns)
        self.actions.append(MultiColumn(
            count=col_count,
            gap=mc.col_gap,
            same_size=True # Assuming equal width for simplistic V1
        ))
        
        # 3. Compile Columns
        for i, col in enumerate(mc.columns):
            if i > 0:
                # Force break to next column
                self.actions.append(BreakColumn())
                
            for elem in col.elements:
                self._compile_element(elem)
                
        # 4. End MultiColumn (Reset to 1 column? or prev state?)
        # Ideally we break section again and reset to 1 column for subsequent content
        self.actions.append(BreakSection(continuous=True))
        self.actions.append(MultiColumn(count=1)) 

    def _compile_container(self, container: Container):
        """
        Compile a Generic Container (Text Box).
        """
        # We assume simplest text box for now: Just text content.
        # Recursively compiling elements into a text string for the 'text' field?
        # OR implementing true recursion where we can put tables inside text boxes.
        # 'InsertTextBox' model currently only supports 'text: str'.
        # limitation: V1 only supports simple text extraction from container.
        
        text_content = []
        for elem in container.elements:
            if isinstance(elem, Paragraph):
                for run in elem.elements:
                    if hasattr(run, 'text'):
                        text_content.append(run.text)
            # Todo: recursive logic for deeper nesting if ExtractText needed
            
        full_text = "\n".join(text_content)
        
        self.actions.append(InsertTextBox(
            text=full_text,
            width=container.width,
            height=container.height,
            x=container.x,
            y=container.y
        ))

    def _compile_paragraph(self, para: Paragraph):
        # Paragraph Init
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
                self.actions.append(InsertImage(
                    path=elem.path, 
                    width=elem.width or 100, 
                    height=elem.height or 100,
                    treat_as_char=True 
                ))
            elif isinstance(elem, Table):
                self._compile_table(elem)
            elif isinstance(elem, Figure):
                self._compile_figure(elem)
            elif isinstance(elem, CodeBlock):
                self._compile_codeblock(elem)

    def _compile_table(self, table: Table):
        rows = len(table.rows)
        # Assuming all rows have same number of cells for now, or finding max
        cols = len(table.rows[0].cells) if rows > 0 else 0
        print(f"[Compiler] Compiling Table: {rows}x{cols}")


        if rows == 0 or cols == 0:
            return        # Move to Cell (0,0) initially? CreateTable usually leaves cursor in (0,0)
        
        self.actions.append(CreateTable(rows=rows, cols=cols))

        self.actions.append(InsertImage(
            path=fig.path,
            width=fig.width or 100,
            height=fig.height or 100
        ))
        if fig.caption:
            self.actions.append(InsertCaption(text=fig.caption))

    def _compile_codeblock(self, code: CodeBlock):
        self.actions.append(InsertCodeBlock(
            text=code.content,
            language=code.language
        ))
        # End of Paragraph (Enter)
        self.actions.append(InsertText(text="\n"))

    def _compile_text_run(self, run: TextRun):
        if run.font_size and run.font_size != self.current_font_size:
            self.actions.append(SetFontSize(size=run.font_size))
            self.current_font_size = run.font_size
            
        if run.is_bold is not None and run.is_bold != self.current_bold:
            self.actions.append(SetFontBold(is_bold=run.is_bold))
            self.current_bold = run.is_bold

        if run.letter_spacing is not None and run.letter_spacing != self.current_letter_spacing:
            self.actions.append(SetLetterSpacing(spacing=run.letter_spacing))
            self.current_letter_spacing = run.letter_spacing
            
        if run.text:
            self.actions.append(InsertText(text=run.text))

from typing import List, Dict, Any, Union
from lib.digital_twin.schema import (
    DigitalTwin, Section, Paragraph, Run, Table, Figure, CodeBlock,
    Container, MultiColumnContainer, Cell
)
from lib.ir import (
    Paragraph as IRParagraph, 
    Table as IRTable, 
    Figure as IRFigure, 
    CodeBlock as IRCodeBlock,
    Section as IRSection,
    # TextRun as IRTextRun # Not used in isinstance typically, usually handled inside access
)

# Alias DigitalTwin to Document for backward compatibility if needed, 
# but better to use DigitalTwin name 
Document = DigitalTwin 

from lib.models import (
    HwpAction,
    InsertText, SetFontSize, SetFontBold, SetAlign, SetLineSpacing,
    SetLetterSpacing, MultiColumn, InsertEquation, InsertImage,
    FileSaveAs, Open, SetPageSetup, CreateTable, InsertCodeBlock, InsertCaption,
    MoveToCell, InsertTextBox, BreakColumn, BreakSection, SetCellBorder, SetParaShape
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
        # print(f"[Compiler] Compiling Element: {type(elem)}")
        
        # Paragraph
        if isinstance(elem, (Paragraph, IRParagraph)):
            self._compile_paragraph(elem)
            # End of Paragraph -> Insert Carriage Return
            self.actions.append(InsertText(text="\r\n"))
            
        # MultiColumn
        elif isinstance(elem, MultiColumnContainer): # IR doesn't have this yet? Or does.
            self._compile_multicolumn(elem)
            
        # Container
        elif isinstance(elem, Container):
            self._compile_container(elem)
            
        # Table
        elif isinstance(elem, (Table, IRTable)):
            self._compile_table(elem)
            self.actions.append(InsertText(text="\r\n")) 

        # Figure
        elif isinstance(elem, (Figure, IRFigure)):
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
        # 1. Semantic Style Mapping
        if para.style == "ProblemBox":
            # Hanging Indent for Problems (e.g. "1. " hangs out)
            # -20pt indent, +20pt left margin
            self.actions.append(SetParaShape(left_margin=20, indent=-20))
        elif para.style == "Header":
             self.actions.append(SetFontBold(is_bold=True))
             self.actions.append(SetFontSize(size=14.0))

        # 2. AnswerBox Handling (Table Wrap)
        if para.style == "AnswerBox":
            # Wrap content in a 1x1 Table
            self.actions.append(CreateTable(rows=1, cols=1, width_type=2, height_type=0)) # Fixed width, Auto height
            self.actions.append(MoveToCell(row=0, col=0))
            # Set Border (Default Solid Black is fine, or explicit)
            self.actions.append(SetCellBorder(border_type="Solid", width="0.4mm", color="Black"))
            # Inner Padding? For now default.

        # 3. Paragraph Alignment
        if para.style and para.style != "Body" and hasattr(para.style, "alignment") and para.style.alignment:
             # Logic for direct alignment property if 'style' was an object, 
             # but here 'style' is string usually?
             # Check if para.alignment attr exists (it does in IR)
             pass
        
        if getattr(para, 'alignment', None):
            # Legacy or IR support
            align_val = para.alignment
        elif isinstance(para.style, object) and hasattr(para.style, 'alignment') and para.style.alignment:
            align_val = para.style.alignment
        else:
            align_val = None

        if align_val:
            align_map = {
                "left": "Left",
                "center": "Center",
                "right": "Right",
                "justify": "Distribute"
            }
            if align_val.lower() in align_map:
                self.actions.append(SetAlign(align_type=align_map[align_val.lower()]))

        # 4. Iterate Runs
        # Support both 'runs' (DigitalTwin) and 'elements' (IR)
        runs = getattr(para, 'runs', None) or getattr(para, 'elements', [])
        
        if runs:
            for run in runs:
                if hasattr(run, 'text') or hasattr(run, 'script') or hasattr(run, 'path'):
                     self._compile_run(run)
        
        # 5. Cleanup (Reset Style)
        if para.style == "ProblemBox":
             self.actions.append(SetParaShape(left_margin=0, indent=0)) # Reset
        elif para.style == "Header":
             self.actions.append(SetFontBold(is_bold=False)) # Reset
             self.actions.append(SetFontSize(size=10.0))
        elif para.style == "AnswerBox":
             # Exit Table? 
             # MoveToCell implies we are editing cell.
             # We need to exit the table structure?
             # In HWP, "Stop Interaction" or just move out. 
             # For scripting, subsequent actions append.
             # We are usually in a cell until we explicitly move out? 
             # But 'CreateTable' inserts it at cursor.
             # HWP Action structure: CreateTable -> (Cursor in cell 0,0) -> InsertText -> (Cursor still in cell).
             # We need to move cursor OUT of table?
             # 'Cancel' or 'MovePos' action?
             # For V1, let's assume valid linear writing.
             # Actually, usually 'Table' is treated as a character.
             # The next text might end up IN the cell if we don't move out.
             # Need a 'EscapeCell' or 'MoveParent' action?
             # Temporary workaround: We don't have ExitTable action.
             pass

    def _compile_run(self, run: Run):
        if run.type == "Text":
            text = run.text or ""
            # Apply styles
            if run.style:
                if run.style.font_weight == "bold":
                    self.actions.append(SetFontBold(is_bold=True))
                if run.style.font_size:
                    try:
                        size = float(run.style.font_size.replace("pt", ""))
                        self.actions.append(SetFontSize(size=size))
                    except:
                        pass

            self.actions.append(InsertText(text=text))
            
            # Revert styles
            if run.style:
                if run.style.font_weight == "bold":
                    self.actions.append(SetFontBold(is_bold=False))

        elif run.type == "Equation":
            if run.script:
                self._compile_equation(run.script)
                
        elif run.type == "Image":
             if run.path:
                 self.actions.append(InsertImage(
                     path=run.path,
                     width=run.width or 50,
                     height=run.height or 50
                 ))

    def _compile_equation(self, eq_script: str):
        self.actions.append(InsertEquation(script=eq_script))

    def _compile_figure(self, figure: Figure):
        # Implementation for Top-Level Image/Figure
        if figure.content_type == "image":
            self.actions.append(InsertImage(
                path=figure.src,
                width=figure.width,
                height=figure.height,
                treat_as_char=False 
            ))

    def _compile_table(self, table: Table):

        rows = len(table.rows)
        cols = len(table.rows[0].cells) if rows > 0 else 0
        print(f"[Compiler] Compiling Table: {rows}x{cols}")

        if rows == 0 or cols == 0:
            return
        
        self.actions.append(CreateTable(rows=rows, cols=cols))
        
        # Apply Table Style (Border)
        if table.style and table.style.border == "none":
            # Select All Cells (Simulated by repeating TableCellBlock)
            # Assumption: F5 x 3 selects entire table.
            # We emit "TableCellBlock" 3 times.
            self.actions.append(HwpAction(action_type="TableCellBlock"))
            self.actions.append(HwpAction(action_type="TableCellBlock"))
            self.actions.append(HwpAction(action_type="TableCellBlock"))
            
            # Apply Border None
            # Using SetCellBorder action with Type="None"
            self.actions.append(SetCellBorder(border_type="None", width="0mm", color="Black"))
            
            # Cancel Selection
            self.actions.append(HwpAction(action_type="Cancel"))

        # Iterate Rows
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                # Move to Cell
                self.actions.append(MoveToCell(row=r_idx, col=c_idx))
                
                # Each Cell has paragraphs (List[Paragraph])
                for p in cell.paragraphs:
                    self._compile_paragraph(p)


    def _compile_codeblock(self, code: CodeBlock):
        self.actions.append(InsertCodeBlock(
            text=code.content,
            language=code.language
        ))
        # End of Paragraph (Enter)
        self.actions.append(InsertText(text="\n"))

        if run.text:
            self.actions.append(InsertText(text=run.text))

"""
HwpxDocumentBuilder: Maps HwpAction objects to proper OWPML structures.

Based on comprehensive OWPML audit:
- KS X 6101 standard
- Hancom official specifications (HWP_5.0_Specification.pdf)
- Skeleton.hwpx reference file

Key structures:
- colPr: <hp:ctrl><hp:colPr colCount="N"/> inside first para's run after secPr
- eqEdit: <hp:ctrl><hp:eqEdit><hp:script>HWP script</hp:script>

Author: Antigravity Pipeline
"""

import tempfile
import os
import mimetypes
import xml.etree.ElementTree as ET
from typing import List, Optional
from pathlib import Path

from hwpx import templates
from hwpx.package import HwpxPackage

from lib.models import (
    HwpAction, InsertText, SetParaShape, CreateTable, InsertEquation,
    MultiColumn, BreakColumn, CreateBorderBox, SetFontBold, SetFontSize,
    MergeCells, InsertImage, InsertTextBox, SetAlign, SetPageSetup, MoveToCell, SetCellBorder
)
from lib.owpml.equation_converter import latex_to_hwp
from lib.owpml.header_manager import HeaderManager
from lib.owpml.bindata_manager import BinDataManager


# OWPML Namespaces
HP_NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
HS_NS = 'http://www.hancom.co.kr/hwpml/2011/section'
HH_NS = 'http://www.hancom.co.kr/hwpml/2011/head'


def _hp(tag: str) -> str:
    """Helper to create hp: namespace tag."""
    return f'{{{HP_NS}}}{tag}'


class HwpxDocumentBuilder:
    """
    Builds HWPX documents from HwpAction sequences using proper OWPML structures.
    
    This implements correct OWPML element placement based on KS X 6101 audit.
    """
    
    def __init__(self):
        self.pkg: Optional[HwpxPackage] = None
        self.section_elem: Optional[ET.Element] = None
        self.para_counter: int = 0
        self.current_para_shape: Optional[SetParaShape] = None
        self._temp_path: Optional[str] = None
        self._section_path: Optional[str] = None
        self._first_para: Optional[ET.Element] = None
        self._first_run: Optional[ET.Element] = None
        # State tracking
        self._is_bold: bool = False
        self._font_size: float = 10.0
        self._font_color: str = "#000000"
        self._current_align: str = "LEFT"
        self._column_count: int = 1
        self._pending_column_break: bool = False
        self._current_table = None
        self._current_cell = None
        self._current_container = None
        
    def build(self, actions: List[HwpAction], output_path: str) -> str:
        """
        Build HWPX file from HwpActions.
        
        Args:
            actions: List of HwpAction objects to process
            output_path: Path to save the generated .hwpx file
            
        Returns:
            Path to the generated HWPX file
        """
        print(f"[HwpxDocumentBuilder] Building document with {len(actions)} actions...")
        
        # 1. Create blank document from template
        self._init_document()
        
        # 2. Pre-scan for MultiColumn to set up colPr before content
        for action in actions:
            if isinstance(action, MultiColumn):
                self._set_column_layout(action.count, action.gap)
                break  # Only first MultiColumn defines initial layout
        
        # 3. Process all actions
        for action in actions:
            self._process_action(action, actions)
            
        # 4. Save and cleanup
        self._save(output_path)
        
        print(f"[HwpxDocumentBuilder] Saved to {output_path}")
        return output_path
    
    def _init_document(self):
        """Initialize document from blank template."""
        # Get blank document bytes from python-hwpx templates
        blank_bytes = templates.blank_document_bytes()
        
        # Write to temp file (python-hwpx requires file path)
        fd, self._temp_path = tempfile.mkstemp(suffix='.hwpx')
        os.close(fd)
        with open(self._temp_path, 'wb') as f:
            f.write(blank_bytes)
            
        # Open package
        self.pkg = HwpxPackage.open(self._temp_path)
        
        # Get section XML
        section_paths = self.pkg.section_paths()
        if not section_paths:
            raise ValueError("Template has no sections")
            
        self._section_path = section_paths[0]
        self._section_path = section_paths[0]
        self.section_elem = self.pkg.get_xml(self._section_path)
        
        # Initialize Header Manager
        self._header_xml = self.pkg.get_xml('Contents/header.xml')
        self.header_manager = HeaderManager(self._header_xml)
        
        # Initialize BinData Manager
        self._content_hpf_xml = self.pkg.get_xml('Contents/content.hpf')
        self.bindata_manager = BinDataManager(self._content_hpf_xml)
        self.pending_binaries: Dict[str, bytes] = {} # internal_path -> content
        
        # Find first paragraph (has secPr)
        self._first_para = self.section_elem.find(f'.//{_hp("p")}')
        if self._first_para is not None:
            self._first_run = self._first_para.find(f'.//{_hp("run")}')
        
        # Clear paragraphs EXCEPT first one (which has secPr and colPr)
        paragraphs = self.section_elem.findall(f'.//{_hp("p")}')
        for p in paragraphs[1:]:
            self.section_elem.remove(p)
            
        # Initialize counter
        # Initialize counter
        self.para_counter = 1
        self._current_container = self.section_elem
        
    def _set_column_layout(self, col_count: int, gap_hwpunit: int = 850):
        """
        Set multi-column layout by modifying colPr in first paragraph.
        
        CORRECT LOCATION: <hp:p><hp:run><hp:secPr/><hp:ctrl><hp:colPr/></hp:ctrl></hp:run></hp:p>
        """
        if self._first_run is None:
            print("[HwpxDocumentBuilder] Warning: Cannot set column layout - no first run")
            return
        
        self._column_count = col_count
        
        # Find existing ctrl with colPr or create new one
        existing_ctrl = None
        for child in self._first_run:
            if child.tag == _hp('ctrl'):
                col_pr = child.find(_hp('colPr'))
                if col_pr is not None:
                    existing_ctrl = child
                    break
        
        if existing_ctrl is not None:
            # Modify existing colPr
            col_pr = existing_ctrl.find(_hp('colPr'))
            col_pr.set('colCount', str(col_count))
            col_pr.set('sameGap', str(gap_hwpunit))
            print(f"[HwpxDocumentBuilder] Modified existing colPr: colCount={col_count}")
        else:
            # Find secPr to insert ctrl after it
            sec_pr = self._first_run.find(_hp('secPr'))
            if sec_pr is not None:
                # Create new ctrl with colPr
                ctrl = ET.Element(_hp('ctrl'))
                col_pr = ET.SubElement(ctrl, _hp('colPr'), {
                    'id': '',
                    'type': 'NEWSPAPER',
                    'layout': 'LEFT',
                    'colCount': str(col_count),
                    'sameSz': '1',
                    'sameGap': str(gap_hwpunit)
                })
                
                # Insert ctrl after secPr
                idx = list(self._first_run).index(sec_pr)
                self._first_run.insert(idx + 1, ctrl)
                print(f"[HwpxDocumentBuilder] Created new colPr: colCount={col_count}")
            else:
                print("[HwpxDocumentBuilder] Warning: No secPr found in first run")
        
    def _process_action(self, action: HwpAction, actions: List[HwpAction] = None):
        """Process a single HwpAction."""
        if isinstance(action, SetPageSetup):
            self._update_page_setup(action)
            
        elif isinstance(action, SetParaShape):
            self.current_para_shape = action
            
        elif isinstance(action, InsertText):
            self._insert_text(action)
            
        elif isinstance(action, CreateTable):
            self._create_table(action, actions)
            
        elif isinstance(action, InsertImage):
            self._insert_image(action)
            
        elif isinstance(action, InsertTextBox):
            self._insert_textbox(action)
            
        elif isinstance(action, InsertEquation):
            self._insert_equation(action)

            
        elif isinstance(action, BreakColumn):
            # Mark next paragraph for column break
            self._pending_column_break = True
            
        elif isinstance(action, MultiColumn):
            # Already handled in pre-scan, skip subsequent MultiColumn
            pass
            
        elif isinstance(action, CreateBorderBox):
            # TODO: Implement border box via borderFill
            print(f"[HwpxDocumentBuilder] CreateBorderBox - TODO: borderFill implementation")
            
        elif isinstance(action, SetFontBold):
            self._is_bold = action.is_bold
            
        elif isinstance(action, SetFontSize):
            self._font_size = action.size
            
        elif isinstance(action, SetAlign):
            self._current_align = action.align_type.upper()
            
        elif isinstance(action, MoveToCell):
            self._move_to_cell(action)
            
        elif isinstance(action, SetCellBorder):
            self._set_cell_border(action)

            
    def _insert_equation(self, action: InsertEquation):
        """
        Insert equation using OWPML hp:eqEdit structure.
        Ref: KS X 6101, HWP Equation Script
        """
        # Convert LaTeX to HWP script
        hwp_script = latex_to_hwp(action.script)
        
        # Determine columnBreak attribute (if pending)
        col_break = '1' if self._pending_column_break else '0'
        self._pending_column_break = False
        self._current_table = None
        self._current_cell = None
        self._current_container = None
        
        # Create paragraph
        p = ET.SubElement(self.section_elem, _hp('p'), {
            'id': str(self.para_counter),
            'paraPrIDRef': '0', 'styleIDRef': '0', 'pageBreak': '0', 'columnBreak': col_break, 'merged': '0'
        })
        self.para_counter += 1
        
        run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
        ctrl = ET.SubElement(run, _hp('ctrl'))
        
        # Create hp:eqEdit
        # Note: No separate shape object wrapper needed for inline equation in simplest form.
        # But usually eqEdit is a Control, similar to Table.
        eq_edit = ET.SubElement(ctrl, _hp('eqEdit'), {
            'numberingType': 'EQUATION',
            'version': '2',
            'baseLine': 'BASE', # Aligns with text baseline
            'textColor': '#000000',
            'baseUnit': 'PUNKT'
        })
        
        # Script content
        script = ET.SubElement(eq_edit, _hp('script'))
        script.text = hwp_script
        
        # NOTE: linesegarray is purposely OMITTED to force HWPX viewer to auto-calculate layout.
        # Adding incorrect linesegarray causes render artifacts.
        
        print(f"[HwpxDocumentBuilder] Inserted equation: {hwp_script[:50]}...")

    
    def _insert_text(self, action: InsertText):
        """Insert text paragraph(s) with dynamic styles."""
        text = action.text
        
        # Prepare Style IDs
        indent = self.current_para_shape.indent if self.current_para_shape else 0
        spacing = self.current_para_shape.line_spacing if self.current_para_shape else 160
        
        para_id = self.header_manager.get_or_create_para_pr(
            align=self._current_align,
            indent=indent,
            line_spacing=spacing
        )
        
        char_id = self.header_manager.get_or_create_char_pr(
            font_size_pt=int(self._font_size),
            is_bold=self._is_bold,
            color=self._font_color
        )
        
        # Split by newlines
        lines = text.split('\n')
        
        for line in lines:
            # Determine columnBreak attribute
            col_break = '1' if self._pending_column_break else '0'
            self._pending_column_break = False
            
            # Use current context
            container = self._current_container if self._current_container is not None else self.section_elem
            
            # Create paragraph element
            p = ET.SubElement(
                container,
                _hp('p'),
                {
                    'id': str(self.para_counter),
                    'paraPrIDRef': para_id,
                    'styleIDRef': '0', # Default style
                    'pageBreak': '0',
                    'columnBreak': col_break,
                    'merged': '0'
                }
            )
            
            # Create run with text
            run = ET.SubElement(p, _hp('run'), {'charPrIDRef': char_id})
            
            # Add text
            t = ET.SubElement(run, _hp('t'))
            t.text = line.strip() if line.strip() else None
            
            self.para_counter += 1
    def _create_table(self, action: CreateTable, actions: List[HwpAction]):
        """
        Create table OWPML structure.
        
        Handles:
        - hp:tbl (Structure)
        - hp:tr (Row)
        - hp:tc (Cell) with cellSpan and cellAddr
        - hp:subList (Cell Content)
        """
        table_id = str(self.para_counter + 9999) # Temporary ID generation
        
        # 1. Determine cell spans from MergeCells actions
        # Map: (row, col) -> (row_span, col_span)
        merge_map = {}
        
        # Look ahead for MergeCells actions
        # In a real implementation, we might need a more robust way to associate merges with specific tables
        # For now, we assume MergeCells immediately follow CreateTable
        current_idx = actions.index(action)
        for next_action in actions[current_idx+1:]:
            if isinstance(next_action, MergeCells):
                merge_map[(next_action.start_row, next_action.start_col)] = (
                    next_action.row_span, next_action.col_span
                )
            elif isinstance(next_action, CreateTable):
                break # Stop at next table
        
        # 2. Create hp:p containing the table control
        col_break = '1' if self._pending_column_break else '0'
        self._pending_column_break = False
        self._current_table = None
        self._current_cell = None
        self._current_container = None
        
        p = ET.SubElement(self.section_elem, _hp('p'), {
            'id': str(self.para_counter),
            'paraPrIDRef': '0',
            'styleIDRef': '0',
            'pageBreak': '0',
            'columnBreak': col_break,
            'merged': '0'
        })
        self.para_counter += 1
        
        # Generate border ID once for the table
        table_border_id = self.header_manager.get_or_create_border_fill('SOLID')
        
        run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
        ctrl = ET.SubElement(run, _hp('ctrl'))
        
        # 3. Create hp:tbl element
        tbl = ET.SubElement(ctrl, _hp('tbl'), {
            'id': table_id,
            'zOrder': '0',
            'numberingType': 'TABLE',
            'textWrap': 'TOP_AND_BOTTOM',
            'textFlow': 'BOTH_SIDES',
            'rowCnt': str(action.rows),
            'colCnt': str(action.cols),
            'cellSpacing': '0',
            'borderFillIDRef': table_border_id # Dynamic visual border
        })
        
        self._current_table = tbl
        self._current_cell = None
        self._current_container = self.section_elem
        
        # 4. Generate Rows and Cells
        # Calculate precise column widths (distribute remainder)
        TOTAL_WIDTH = 42520 # A4 content width approx
        base_width = TOTAL_WIDTH // action.cols
        remainder = TOTAL_WIDTH % action.cols
        col_widths = [base_width] * action.cols
        # Add remainder to the last column
        if remainder > 0:
            col_widths[-1] += remainder
            
        cell_height = 1000 # ~3.5mm default height
        
        # Track hidden cells (covered by spans)
        covered_cells = set()
        
        for r in range(action.rows):
            tr = ET.SubElement(tbl, _hp('tr'))
            
            for c in range(action.cols):
                if (r, c) in covered_cells:
                    continue
                
                # Cells inherit table border style (reuse ID)
                tc = ET.SubElement(tr, _hp('tc'), {'borderFillIDRef': table_border_id})
                
                # Check for merge start
                row_span, col_span = merge_map.get((r, c), (1, 1))
                
                # Mark covered cells
                if row_span > 1 or col_span > 1:
                    for mr in range(row_span):
                        for mc in range(col_span):
                            if mr == 0 and mc == 0: continue
                            covered_cells.add((r + mr, c + mc))
                
                # cellAddr
                ET.SubElement(tc, _hp('cellAddr'), {
                    'colAddr': str(c), 
                    'rowAddr': str(r)
                })
                
                # cellSpan (only if merged)
                if row_span > 1 or col_span > 1:
                    ET.SubElement(tc, _hp('cellSpan'), {
                        'colSpan': str(col_span),
                        'rowSpan': str(row_span)
                    })
                
                # cellSz
                # Sum widths of spanned columns
                span_width = sum(col_widths[c + i] for i in range(col_span))
                
                ET.SubElement(tc, _hp('cellSz'), {
                    'width': str(span_width),
                    'height': str(cell_height * row_span)
                })
                
                # subList (Cell Content)
                sub_list = ET.SubElement(tc, _hp('subList'), {
                    'id': str(self.para_counter),
                    'textDirection': 'HORIZONTAL',
                    'vertAlign': 'CENTER'
                })
                
                # Empty paragraph inside cell
                cell_p = ET.SubElement(sub_list, _hp('p'), {
                    'id': str(self.para_counter),
                    'paraPrIDRef': '0',
                    'styleIDRef': '0'
                })
                ET.SubElement(cell_p, _hp('run'), {'charPrIDRef': '0'})
                self.para_counter += 1

        # Add linesegarray to parent paragraph
        linesegarray = ET.SubElement(p, _hp('linesegarray'))
        ET.SubElement(linesegarray, _hp('lineseg'), {
            'textpos': '0', 'vertpos': '0', 'vertsize': '1000',
            'textheight': '1000', 'baseline': '850', 'spacing': '600',
            'horzpos': '0', 'horzsize': '42520', 'flags': '393216'
        })
        
        print(f"[HwpxDocumentBuilder] Created table {action.rows}x{action.cols} with {len(merge_map)} merges")
        
    def _insert_image(self, action: InsertImage):
        """
        Insert an image as a inline shape (hp:pic).
        """
        if not os.path.exists(action.path):
            print(f"[HwpxDocumentBuilder] Error: Image not found at {action.path}")
            return
            
        # 1. Register BinData
        mime_type, _ = mimetypes.guess_type(action.path)
        if not mime_type: mime_type = "image/png" # Fallback
        
        with open(action.path, 'rb') as f:
            content = f.read()
            
        bin_id, internal_path = self.bindata_manager.add_bin_item(os.path.basename(action.path), mime_type)
        self.pending_binaries[internal_path] = content
        
        # 2. Add Paragraph with Picture
        p = ET.SubElement(self.section_elem, _hp('p'), {
            'id': str(self.para_counter),
            'paraPrIDRef': '0', 'styleIDRef': '0', 'pageBreak': '0', 'columnBreak': '0', 'merged': '0'
        })
        self.para_counter += 1
        
        run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
        ctrl = ET.SubElement(run, _hp('ctrl'))
        
        # 3. Create hp:pic Structure
        # Dimensions (mm to HwpUnit). 1 mm = 283.46 HwpUnit
        w_unit = int(action.width * 283.46) if action.width else 28346 # Default 100mm
        h_unit = int(action.height * 283.46) if action.height else 28346 # Default 100mm
        
        # Pic shape
        pic = ET.SubElement(ctrl, _hp('pic'), {
            'id': str(self.para_counter + 70000),
            'zOrder': '0', 'numberingType': 'PICTURE',
            'widthAtCreate': str(w_unit), 'heightAtCreate': str(h_unit)
        })
        
        # Common Shape Props
        self._create_common_shape_props(pic, w_unit, h_unit, is_inline=True)
        
        # Image Specific
        ET.SubElement(pic, _hp('img'), {
            'binaryItemIDRef': bin_id,
            'imageType': 'REAL_PIC', # or BMP, PNG, etc. REAL_PIC usually safe? 
            'bright': '0', 'contrast': '0', 'effect': 'REAL_PIC',
            'alpha': '0'
        })
        
        print(f"[HwpxDocumentBuilder] Inserted image {os.path.basename(action.path)} (ID={bin_id})")

    def _insert_textbox(self, action: InsertTextBox):
        """
        Insert a text box (hp:rect) with text content.
        """
        # 1. Add Paragraph container
        p = ET.SubElement(self.section_elem, _hp('p'), {
            'id': str(self.para_counter),
            'paraPrIDRef': '0', 'styleIDRef': '0', 'pageBreak': '0', 'columnBreak': '0', 'merged': '0'
        })
        self.para_counter += 1
        
        run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
        ctrl = ET.SubElement(run, _hp('ctrl'))
        
        # 2. Dimensions & Position
        w_unit = int(action.width * 283.46) if action.width else 28346 # Default 100mm
        h_unit = int(action.height * 283.46) if action.height else 28346 # Default 100mm
        
        # Determine strict or inline
        # If x/y provided, treat as floating. Else inline.
        is_inline = (action.x is None and action.y is None)
        
        # 3. Create hp:rect
        # id generation: slightly different range to avoid collision (naive)
        rect_id = str(self.para_counter + 80000)
        
        rect = ET.SubElement(ctrl, _hp('rect'), {
            'id': rect_id,
            'zOrder': '0', 'numberingType': 'SHAPE',
            'widthAtCreate': str(w_unit), 'heightAtCreate': str(h_unit)
        })
        
        # 4. Common Shape Props
        x_unit = int(action.x * 283.46) if action.x else 0
        y_unit = int(action.y * 283.46) if action.y else 0
        
        self._create_common_shape_props(rect, w_unit, h_unit, is_inline, x_unit, y_unit)
        
        # 5. Rect Specific (subList for text)
        sub_list = ET.SubElement(rect, _hp('subList'), {
            'id': str(self.para_counter + 80001),
            'textDirection': 'HORIZONTAL',
            'vertAlign': 'CENTER',
            'linkListIDRef': '0'
        })
        
        # Inner Paragraph
        inner_p = ET.SubElement(sub_list, _hp('p'), {
            'id': str(self.para_counter), # reuse counter
             'paraPrIDRef': '0', 'styleIDRef': '0'
        })
        self.para_counter += 1
        
        inner_run = ET.SubElement(inner_p, _hp('run'), {'charPrIDRef': '0'})
        ET.SubElement(inner_run, _hp('t')).text = action.text
        
        print(f"[HwpxDocumentBuilder] Inserted textbox: '{action.text[:20]}...'")

    def _create_common_shape_props(self, parent: ET.Element, width: int, height: int, 
                                 is_inline: bool = True, x: int = 0, y: int = 0):
        """Add standard shape children (sz, pos, outMargin, shapeComment)."""
        # sz
        ET.SubElement(parent, _hp('sz'), {
            'width': str(width), 'height': str(height), 
            'widthRelTo': 'ABSOLUTE', 'heightRelTo': 'ABSOLUTE', 'protect': '0'
        })
        
        # pos
        if is_inline:
            ET.SubElement(parent, _hp('pos'), {
                'treatAsChar': '1', 'flowWithText': '1', 'allowOverlap': '0', 'holdAnchorAndSO': '0', 
                'vertRelTo': 'PARA', 'horzRelTo': 'PARA', 
                'vertAlign': 'TOP', 'horzAlign': 'LEFT', 
                'vertOffset': '0', 'horzOffset': '0'
            })
        else:
            # Floating (Absolute)
            ET.SubElement(parent, _hp('pos'), {
                'treatAsChar': '0', 'flowWithText': '0', 'allowOverlap': '1', 'holdAnchorAndSO': '0',
                'vertRelTo': 'PAPER', 'horzRelTo': 'PAPER', # Absolute to paper
                'vertAlign': 'TOP', 'horzAlign': 'LEFT',
                'vertOffset': str(y), 'horzOffset': str(x)
            })
            
        # outMargin
        ET.SubElement(parent, _hp('outMargin'), {'left': '0', 'right': '0', 'top': '0', 'bottom': '0'})
        
        # shapeComment
        ET.SubElement(parent, _hp('shapeComment'))

    def _save(self, output_path: str):
        """Save document to output path."""
        # Write back modified section
        self.pkg.set_xml(self._section_path, self.section_elem)
        
        # Write back modified header (important for new styles)
        self.pkg.set_xml('Contents/header.xml', self.header_manager.header)
        
        # Write back modified content.hpf (for BinData)
        self.pkg.set_xml('Contents/content.hpf', self.bindata_manager.get_manifest_xml())
        
        # Save package (updates=pending_binaries if supported, else set_part)
        # Note: python-hwpx save() supports updates dict? Checking signature...
        # If not, use set_part before save
        if hasattr(self.pkg, 'set_part'):
            for path, content in self.pending_binaries.items():
                self.pkg.set_part(path, content)
        
        # Save package
        self.pkg.save(output_path)
        
        # Cleanup temp file
        if self._temp_path and os.path.exists(self._temp_path):
            os.unlink(self._temp_path)

    def _update_page_setup(self, action: SetPageSetup):
        """
        Update Page Setup (secPr) for the first section.
        Handles Orientation, Margins, Dimensions.
        """
        if self._first_run is None:
            print("[HwpxDocumentBuilder] Warning: No first run for Page Setup")
            return

        # Find secPr
        sec_pr = None
        for child in self._first_run:
            if 'secPr' in child.tag:
                sec_pr = child
                break
        
        if sec_pr is None:
             print("[HwpxDocumentBuilder] Warning: secPr not found in first run")
             return
            
        # Find pagePr
        page_pr = None
        for child in sec_pr:
            if 'pagePr' in child.tag:
                page_pr = child
                break
        
        if page_pr is None:
             return

        # Constants
        HWPUNIT_PER_MM = 283.465
        
        # Dimensions
        if action.paper_size == "Legal":
             w_mm, h_mm = 215.9, 355.6
        elif action.paper_size == "Letter":
             w_mm, h_mm = 215.9, 279.4
        else: # A4 Default
             w_mm, h_mm = 210.0, 297.0
        
        # Orientation
        is_landscape = action.orientation == "Landscape"
        if is_landscape:
             w_mm, h_mm = h_mm, w_mm
             
        width_u = int(w_mm * HWPUNIT_PER_MM)
        height_u = int(h_mm * HWPUNIT_PER_MM)
        
        page_pr.set('width', str(width_u))
        page_pr.set('height', str(height_u))
        
        # Margins (mm -> unit)
        left_u = int(action.left * HWPUNIT_PER_MM)
        right_u = int(action.right * HWPUNIT_PER_MM)
        top_u = int(action.top * HWPUNIT_PER_MM)
        bottom_u = int(action.bottom * HWPUNIT_PER_MM)
        header_u = int(action.header * HWPUNIT_PER_MM)
        footer_u = int(action.footer * HWPUNIT_PER_MM)
        gutter_u = int(action.gutter * HWPUNIT_PER_MM)
        
        # Find margin tag
        margin_tag = None
        for child in page_pr:
             if 'margin' in child.tag:
                  margin_tag = child
                  break
        
        if margin_tag is not None:
             margin_tag.set('left', str(left_u))
             margin_tag.set('right', str(right_u))
             margin_tag.set('top', str(top_u))
             margin_tag.set('bottom', str(bottom_u))
             margin_tag.set('header', str(header_u))
             margin_tag.set('footer', str(footer_u))
             margin_tag.set('gutter', str(gutter_u))
             
        print(f"[HwpxDocumentBuilder] Updated Page Setup: {action.paper_size} {action.orientation}")

    def _move_to_cell(self, action: MoveToCell):
        """Move cursor context to specific cell in current table."""
        if self._current_table is None:
            print("[HwpxDocumentBuilder] Warning: No active table for MoveToCell")
            return

        target_row = action.row
        target_col = action.col
        
        # Find tr
        rows = self._current_table.findall(f'.//{{http://www.hancom.co.kr/hwpml/2011/paragraph}}tr')
        if not rows or target_row >= len(rows):
            print(f"[HwpxDocumentBuilder] Error: Table has {len(rows)} rows, target {target_row}")
            return
            
        tr = rows[target_row]
        
        # Find tc
        cols = tr.findall(f'.//{{http://www.hancom.co.kr/hwpml/2011/paragraph}}tc')
        if not cols or target_col >= len(cols):
            print(f"[HwpxDocumentBuilder] Error: Row {target_row} has {len(cols)} cols, target {target_col}")
            return
            
        tc = cols[target_col]
        
        self._current_cell = tc
        self._current_container = tc
        
        # Ensure Cell has at least one paragraph? 
        # _insert_text adds a paragraph. 
        # If we move to cell, we might want to append to EXISTING paragraph or create new?
        # Standard: _insert_text creates NEW paragraph.
        
    def _set_cell_border(self, action: SetCellBorder):
        """Set border/fill for current cell."""
        if self._current_cell is None:
            print("[HwpxDocumentBuilder] Warning: No active cell for SetCellBorder")
            return
            
        # Create BorderFill ID via HeaderManager
        bf_id = self.header_manager.get_or_create_border_fill(
            border_type=action.border_type,
            width=action.width,
            color=action.color,
            fill_color=action.fill_color
        )
        
        self._current_cell.set('borderFillIDRef', bf_id)

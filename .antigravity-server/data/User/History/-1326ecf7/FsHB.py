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
import xml.etree.ElementTree as ET
from typing import List, Optional
from pathlib import Path

from hwpx import templates
from hwpx.package import HwpxPackage

from lib.models import (
    HwpAction, InsertText, SetParaShape, CreateTable, InsertEquation,
    MultiColumn, BreakColumn, CreateBorderBox, SetFontBold, SetFontSize,
    MergeCells
)
from lib.owpml.equation_converter import latex_to_hwp


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
        self._column_count: int = 1
        self._pending_column_break: bool = False
        
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
        self.section_elem = self.pkg.get_xml(self._section_path)
        
        # Find first paragraph (has secPr)
        self._first_para = self.section_elem.find(f'.//{_hp("p")}')
        if self._first_para is not None:
            self._first_run = self._first_para.find(f'.//{_hp("run")}')
        
        # Clear paragraphs EXCEPT first one (which has secPr and colPr)
        paragraphs = self.section_elem.findall(f'.//{_hp("p")}')
        for p in paragraphs[1:]:
            self.section_elem.remove(p)
            
        # Initialize counter
        self.para_counter = 1
        
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
        if isinstance(action, SetParaShape):
            self.current_para_shape = action
            
        elif isinstance(action, InsertText):
            self._insert_text(action)
            
        elif isinstance(action, CreateTable):
            self._create_table(action, actions)
            
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
    
    def _insert_text(self, action: InsertText):
        """Insert text paragraph(s)."""
        text = action.text
        
        # Split by newlines
        lines = text.split('\n')
        
        for line in lines:
            # Determine columnBreak attribute
            col_break = '1' if self._pending_column_break else '0'
            self._pending_column_break = False
            
            # Create paragraph element
            p = ET.SubElement(
                self.section_elem,
                _hp('p'),
                {
                    'id': str(self.para_counter),
                    'paraPrIDRef': '0',
                    'styleIDRef': '0',
                    'pageBreak': '0',
                    'columnBreak': col_break,
                    'merged': '0'
                }
            )
            
            # Create run with text
            run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
            
            t = ET.SubElement(run, _hp('t'))
            t.text = line.strip() if line.strip() else None
            
            # Add linesegarray
            linesegarray = ET.SubElement(p, _hp('linesegarray'))
            ET.SubElement(
                linesegarray,
                _hp('lineseg'),
                {
                    'textpos': '0',
                    'vertpos': '0',
                    'vertsize': '1000',
                    'textheight': '1000',
                    'baseline': '850',
                    'spacing': '600',
                    'horzpos': '0',
                    'horzsize': '42520',
                    'flags': '393216'
                }
            )
            
            self.para_counter += 1
            
    def _insert_equation(self, action: InsertEquation):
        """
        Insert equation using proper OWPML eqEdit structure.
        
        Structure: <hp:p><hp:run><hp:ctrl><hp:eqEdit><hp:script>...</hp:script></hp:eqEdit></hp:ctrl></hp:run></hp:p>
        """
        # Convert LaTeX to HWP script
        hwp_script = latex_to_hwp(action.script)
        
        # Determine columnBreak attribute
        col_break = '1' if self._pending_column_break else '0'
        self._pending_column_break = False
        
        # Create paragraph
        p = ET.SubElement(
            self.section_elem,
            _hp('p'),
            {
                'id': str(self.para_counter),
                'paraPrIDRef': '0',
                'styleIDRef': '0',
                'pageBreak': '0',
                'columnBreak': col_break,
                'merged': '0'
            }
        )
        
        # Create run with equation control
        run = ET.SubElement(p, _hp('run'), {'charPrIDRef': '0'})
        
        # Create ctrl with eqEdit
        ctrl = ET.SubElement(run, _hp('ctrl'))
        eq_edit = ET.SubElement(ctrl, _hp('eqEdit'), {
            'version': '2',
            'baseLine': 'BOTTOM',
            'textColor': '#000000',
            'baseUnit': 'PUNKT'
        })
        
        # Add script element with HWP equation script
        script = ET.SubElement(eq_edit, _hp('script'))
        script.text = hwp_script
        
        # Add linesegarray
        linesegarray = ET.SubElement(p, _hp('linesegarray'))
        ET.SubElement(
            linesegarray,
            _hp('lineseg'),
            {
                'textpos': '0',
                'vertpos': '0',
                'vertsize': '1000',
                'textheight': '1000',
                'baseline': '850',
                'spacing': '600',
                'horzpos': '0',
                'horzsize': '42520',
                'flags': '393216'
            }
        )
        
        self.para_counter += 1
        print(f"[HwpxDocumentBuilder] Inserted equation: {hwp_script[:50]}...")

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
        
        p = ET.SubElement(self.section_elem, _hp('p'), {
            'id': str(self.para_counter),
            'paraPrIDRef': '0',
            'styleIDRef': '0',
            'pageBreak': '0',
            'columnBreak': col_break,
            'merged': '0'
        })
        self.para_counter += 1
        
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
            'borderFillIDRef': '1' # Default border
        })
        
        # 4. Generate Rows and Cells
        # Default cell size (A4 / cols)
        cell_width = 42520 // action.cols # Roughly page width / cols
        cell_height = 1000 # ~3.5mm default height
        
        # Track hidden cells (covered by spans)
        covered_cells = set()
        
        for r in range(action.rows):
            tr = ET.SubElement(tbl, _hp('tr'))
            
            for c in range(action.cols):
                if (r, c) in covered_cells:
                    continue
                
                tc = ET.SubElement(tr, _hp('tc'), {'borderFillIDRef': '1'})
                
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
                ET.SubElement(tc, _hp('cellSz'), {
                    'width': str(cell_width * col_span),
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
        
    def _save(self, output_path: str):
        """Save document to output path."""
        # Write back modified section
        self.pkg.set_xml(self._section_path, self.section_elem)
        
        # Save package
        self.pkg.save(output_path)
        
        # Cleanup temp file
        if self._temp_path and os.path.exists(self._temp_path):
            os.unlink(self._temp_path)

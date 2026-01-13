"""
HwpxDocumentBuilder: Maps HwpAction objects to python-hwpx API.

This module bridges the gap between our HwpAction ontology and the community-standard
python-hwpx library for HWPX document manipulation.

Based on analysis of:
- python-hwpx (airmang): https://github.com/airmang/python-hwpx
- OWPML KS X 6101 standard

Author: Antigravity Pipeline
"""

import tempfile
import os
from typing import List, Optional
from pathlib import Path
from lxml import etree

from hwpx import templates
from hwpx.package import HwpxPackage

from lib.models import HwpAction, InsertText, SetParaShape, CreateTable, InsertEquation


# OWPML Namespaces
NS = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
}


class HwpxDocumentBuilder:
    """
    Builds HWPX documents from HwpAction sequences using the python-hwpx library.
    
    This is the Phase 10 replacement for the template-based HWPGenerator.
    Uses community-standard python-hwpx for proper OWPML manipulation.
    """
    
    def __init__(self):
        self.pkg: Optional[HwpxPackage] = None
        self.section_elem: Optional[etree._Element] = None
        self.para_counter: int = 0
        self.current_para_shape: Optional[SetParaShape] = None
        self._temp_path: Optional[str] = None
        
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
        
        # 2. Process actions
        for action in actions:
            self._process_action(action)
            
        # 3. Save and cleanup
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
            
        self.section_elem = self.pkg.get_xml(section_paths[0])
        self._section_path = section_paths[0]
        
        # Clear existing paragraphs (keep first one with secPr)
        paragraphs = self.section_elem.findall('.//hp:p', NS)
        for p in paragraphs[1:]:  # Keep first paragraph with section properties
            p.getparent().remove(p)
            
        # Initialize counter (first para with secPr has ID from template)
        self.para_counter = 1
        
    def _process_action(self, action: HwpAction):
        """Process a single HwpAction."""
        if isinstance(action, SetParaShape):
            self.current_para_shape = action
            
        elif isinstance(action, InsertText):
            self._insert_text(action)
            
        elif isinstance(action, CreateTable):
            # TODO: Implement table creation
            pass
            
        elif isinstance(action, InsertEquation):
            # For equations, insert as text placeholder for now
            self._insert_equation_placeholder(action)
            
    def _insert_text(self, action: InsertText):
        """Insert text paragraph(s)."""
        text = action.text
        
        # Split by newlines
        lines = text.split('\n')
        
        for line in lines:
            # Create paragraph element
            p = etree.SubElement(
                self.section_elem,
                '{http://www.hancom.co.kr/hwpml/2011/paragraph}p',
                {
                    'id': str(self.para_counter),
                    'paraPrIDRef': '0',  # Default paragraph style
                    'styleIDRef': '0',
                    'pageBreak': '0',
                    'columnBreak': '0',
                    'merged': '0'
                }
            )
            
            # Create run with text
            run = etree.SubElement(
                p,
                '{http://www.hancom.co.kr/hwpml/2011/paragraph}run',
                {'charPrIDRef': '0'}
            )
            
            t = etree.SubElement(
                run,
                '{http://www.hancom.co.kr/hwpml/2011/paragraph}t'
            )
            t.text = line.strip() if line.strip() else None
            
            # Add linesegarray (HWP will recalculate)
            linesegarray = etree.SubElement(
                p,
                '{http://www.hancom.co.kr/hwpml/2011/paragraph}linesegarray'
            )
            etree.SubElement(
                linesegarray,
                '{http://www.hancom.co.kr/hwpml/2011/paragraph}lineseg',
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
            
    def _insert_equation_placeholder(self, action: InsertEquation):
        """Insert equation as text placeholder (full equation support TODO)."""
        # For now, insert the script as text with delimiters
        placeholder_text = f"[수식: {action.script}]"
        self._insert_text(InsertText(text=placeholder_text))
        
    def _save(self, output_path: str):
        """Save document to output path."""
        # Write back modified section
        self.pkg.set_xml(self._section_path, self.section_elem)
        
        # Save package
        self.pkg.save(output_path)
        
        # Cleanup temp file
        if self._temp_path and os.path.exists(self._temp_path):
            os.unlink(self._temp_path)


import zipfile
import xml.etree.ElementTree as ET
import os
import re
from typing import Optional
from lib.ir import Document, Section, Paragraph, TextRun

class HwpxIngestor:
    """
    Parses HWPX (OOXML-like) files into Intermediate Representation (IR).
    Focuses on high-fidelity extraction of Structure and Styles.
    """
    def __init__(self, path: str):
        self.path = path
        self.ns = {
            'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
            'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
            'hh': 'http://www.hancom.co.kr/hwpml/2011/head'
        }

    def ingest(self) -> Document:
        doc = Document()
        
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"File not found: {self.path}")

        with zipfile.ZipFile(self.path, 'r') as zf:
            # 1. Parse Header for Styles (Todo: Future work for full style mapping)
            # 2. Parse Section 0 (Main Content)
            try:
                # Note: Real HWPX can have section0.xml, section1.xml...
                # We start with section0.xml
                content_xml = zf.read('Contents/section0.xml')
                root = ET.fromstring(content_xml)
                
                # Each section0.xml usually maps to a logical Section in our IR
                # but technically it contains <hp:p> elements directly under root usually.
                # Let's verify root tag.
                
                ir_section = doc.add_section()
                
                # Iterate Paragraphs
                for para_node in root.findall('.//hp:p', self.ns):
                    ir_para = self._parse_paragraph(para_node)
                    ir_section.paragraphs.append(ir_para)
                    
            except KeyError:
                print("Warning: Contents/section0.xml not found. Is this a valid HWPX?")
                
        return doc

    def _parse_paragraph(self, para_node: ET.Element) -> Paragraph:
        ir_para = Paragraph()
        
        # 1. Paragraph Properties (Alignment, Spacing)
        pPr = para_node.find('hp:pPr', self.ns)
        if pPr is not None:
            # Alignment
            align = pPr.get('align')
            if align:
                ir_para.alignment = self._map_align(align)
            # Line Spacing? Not always direct attribute, sometimes in style.
            
        # 2. Runs (Text, Char Properties)
        for run_node in para_node.findall('hp:run', self.ns):
            ir_run = self._parse_run(run_node)
            if ir_run:
                ir_para.elements.append(ir_run)
                
        return ir_para

    def _parse_run(self, run_node: ET.Element) -> Optional[TextRun]:
        # Text
        t_node = run_node.find('hp:t', self.ns)
        if t_node is None or t_node.text is None:
            return None # Empty run or other control char
            
        text = t_node.text
        
        # Formatting
        # Note: In HWPX, charPr is strictly referenced by ID usually, 
        # or embedded if explicit.
        # <hp:run charPrIDRef="0">
        # To strictly reconstruct bold/size, we MUST parse Header/styles.xml to lookup ID.
        # For this prototype Phase, we inspect if there are direct overrides or rely on text analysis 
        # (or later implement full Style Table parsing).
        # 
        # However, for "High Quality", we assume standard mapping or extracted styles if possible.
        # Currently, without parsing 'header.xml', we cannot know if 'charPrIDRef=1' is Bold.
        # 
        # TODO: Implement header.xml parsing in Phase 6. 
        # For now, we return basic TextRun. The compiler defaults to standard.
        # If the user needs "Exact" style reproduction, Style Table parsing is mandatory.
        
        return TextRun(text=text)

    def _map_align(self, hwp_align: str) -> str:
        # HWPX uses "Center", "Left", "Right", "Distribute"(Justify)
        mapping = {
            "Center": "Center",
            "Left": "Left",
            "Right": "Right",
            "Distribute": "Justify",
            "Justify": "Justify" 
        }
        return mapping.get(hwp_align, "Left")

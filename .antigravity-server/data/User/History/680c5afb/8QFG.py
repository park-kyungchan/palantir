import zipfile
import os
from typing import List
from lib.models import HwpAction, InsertText, SetParaShape, CreateTable
from lib.owpml.header_manager import HeaderManager

# Minimal OWPML Templates
CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container">
<ocf:rootfiles>
<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>
</ocf:rootfiles>
</ocf:container>"""

CONTENT_HPF = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" xmlns:dc="http://purl.org/dc/elements/1.1/" version="1.0" unique-identifier="uid">
<opf:metadata>
<dc:title>Linux Generated HWPX</dc:title>
<dc:language>ko</dc:language>
<dc:identifier id="uid">urn:uuid:00000000-0000-0000-0000-000000000000</dc:identifier>
<opf:meta name="generator" content="Antigravity HWPX Generator"/>
</opf:metadata>
<opf:manifest>
<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>
<opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/>
</opf:manifest>
<opf:spine>
<opf:itemref idref="section0"/>
</opf:spine>
</opf:package>"""

class HWPGenerator:
    """
    Generates a valid .hwpx (OWPML) file from HwpActions.
    """
    def __init__(self):
        self.sections = []
        self.header_manager = HeaderManager()

    def generate(self, actions: List[HwpAction], output_filename: str):
        # We need to process actions to build both Body and Header
        section_xml = self._build_section_xml(actions)
        header_xml = self.header_manager.generate_header_xml()
        
        print(f"[HWPGenerator] Creating {output_filename}...")
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as z:
            # Mimetype (Stored)
            z.writestr("mimetype", "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
            
            # Meta-Inf & Contents
            z.writestr("META-INF/container.xml", CONTAINER_XML)
            z.writestr("Contents/content.hpf", CONTENT_HPF)
            z.writestr("Contents/header.xml", header_xml)
            z.writestr("Contents/section0.xml", section_xml)
            
        print(f"[HWPGenerator] Saved to {output_filename}")

    def _build_section_xml(self, actions: List[HwpAction]) -> str:
        # Preamble
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
            '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">',
        ]
        
        # State tracking
        current_para_shape = SetParaShape() # Default
        
        for action in actions:
            if isinstance(action, SetParaShape):
                current_para_shape = action
                
            elif isinstance(action, InsertText):
                # Resolve ParaPr ID
                para_id = self.header_manager.get_para_pr_id(current_para_shape)
                
                # Clean text for XML
                safe = action.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                parts = safe.split('\n')
                for i, part in enumerate(parts):
                    # We create a paragraph for each line (simplification)
                    # Use the resolved ID
                    
                    # Note on Empty Lines: They still need styling if they carry the indent
                    
                    para_xml = f'<hp:p id="{i}" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="false" columnBreak="false">'
                    if part:
                         para_xml += f'<hp:run><hp:t>{part}</hp:t></hp:run>'
                    else:
                         # Empty paragraph needs at least an empty run or just closed
                         para_xml += f'<hp:run><hp:t></hp:t></hp:run>'
                    para_xml += '</hp:p>'
                    
                    xml_lines.append(para_xml)

            # ... other actions ...
                
        xml_lines.append('</hs:sec>')
        return "".join(xml_lines)


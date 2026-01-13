import zipfile
import os
from typing import List
from lib.models import HwpAction, InsertText, SetParaShape, CreateTable

# Minimal OWPML Templates
CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container">
<ocf:rootfiles>
<ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/>
</ocf:rootfiles>
</ocf:container>"""

CONTENT_HPF = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" version="1.0" unique-identifier="uid">
<opf:metadata>
<opf:title>Linux Generated HWPX</opf:title>
<opf:language>ko</opf:language>
</opf:metadata>
<opf:manifest>
<opf:item id="section0" href="section0.xml" media-type="application/xml"/>
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

    def generate(self, actions: List[HwpAction], output_filename: str):
        section_xml = self._build_section_xml(actions)
        
        print(f"[HWPGenerator] Creating {output_filename}...")
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as z:
            # Mimetype (Stored)
            z.writestr("mimetype", "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
            
            # Meta-Inf & Contents
            z.writestr("META-INF/container.xml", CONTAINER_XML)
            z.writestr("Contents/content.hpf", CONTENT_HPF)
            z.writestr("Contents/section0.xml", section_xml)
            
        print(f"[HWPGenerator] Saved to {output_filename}")

    def _build_section_xml(self, actions: List[HwpAction]) -> str:
        # Preamble
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
            '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">',
        ]
        
        # We need to group text into runs, and runs into paragraphs.
        # HwpActions are linear: SetParaShape -> InsertText -> InsertText ...
        # Standard HWPX structure: <hp:p> <hp:run> <hp:t>Text</hp:t> </hp:run> </hp:p>
        
        current_para_shape = None
        current_text_buffer = []
        
        # Naive state machine for V1
        # Assumes explicit paragraph breaks aren't strictly modeled in Actions yet, 
        # normally "InsertText" with \n implies break or "BreakPara".
        # But for OWPML, we must wrap in <hp:p>.
        
        # Let's treat every "SetParaShape" as a potential start of new paragraph formatting,
        # but actually "InsertText" usually provides the content.
        
        # Simplified Logic:
        # Create one <hp:p> for each logical block. 
        # If we see '\n' in text, we might split? 
        # For now, let's dump everything into one paragraph to prove connectivity, 
        # OR split by explicit SetParaShape change if that marks boundaries.
        
        # Better: Accumulate content, when SetParaShape changes, close previous paragraph?
        
        for action in actions:
            if isinstance(action, InsertText):
                # Clean text for XML
                safe = action.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                # Handle newlines? HWPX uses slightly different generic logic, but let's try raw.
                # Actually, <hp:p> is a paragraph. 
                # If text has \n, we should probably start new <hp:p>.
                
                parts = safe.split('\n')
                for i, part in enumerate(parts):
                    if part:
                         xml_lines.append(f'<hp:p><hp:run><hp:t>{part}</hp:t></hp:run></hp:p>')
                    # If split by newline, empty parts might just be blank lines
                    elif len(parts) > 1: # Empty string caused by split
                         xml_lines.append('<hp:p><hp:run><hp:t></hp:t></hp:run></hp:p>')

            elif isinstance(action, SetParaShape):
                # OWPML styling is complex (id references). 
                # For V1, we just emit logic.
                pass
                
        xml_lines.append('</hs:sec>')
        return "".join(xml_lines)


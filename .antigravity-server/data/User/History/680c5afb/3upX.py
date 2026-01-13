import zipfile
import os
from typing import List
from lib.models import HwpAction, InsertText, SetParaShape, CreateTable
from lib.owpml.header_manager import HeaderManager

# Common namespace declarations for all OWPML XML files
OWPML_NAMESPACES = 'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf/" xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" xmlns:epub="http://www.idpf.org/2007/ops" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'

# Minimal OWPML Templates based on official Skeleton.hwpx
CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:container" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf"><ocf:rootfiles><ocf:rootfile full-path="Contents/content.hpf" media-type="application/hwpml-package+xml"/><ocf:rootfile full-path="Preview/PrvText.txt" media-type="text/plain"/><ocf:rootfile full-path="META-INF/container.rdf" media-type="application/rdf+xml"/></ocf:rootfiles></ocf:container>"""

VERSION_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="1" buildNumber="0" os="1" xmlVersion="1.5" application="Hancom Office Hangul" appVersion="24.0.0.0"/>"""

SETTINGS_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><ha:HWPApplicationSetting xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"><ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/></ha:HWPApplicationSetting>"""

MANIFEST_XML = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><odf:manifest xmlns:odf="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0"/>"""

CONTAINER_RDF = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"><rdf:Description rdf:about=""><ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/header.xml"/></rdf:Description><rdf:Description rdf:about="Contents/header.xml"><rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#HeaderFile"/></rdf:Description><rdf:Description rdf:about=""><ns0:hasPart xmlns:ns0="http://www.hancom.co.kr/hwpml/2016/meta/pkg#" rdf:resource="Contents/section0.xml"/></rdf:Description><rdf:Description rdf:about="Contents/section0.xml"><rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#SectionFile"/></rdf:Description><rdf:Description rdf:about=""><rdf:type rdf:resource="http://www.hancom.co.kr/hwpml/2016/meta/pkg#Document"/></rdf:Description></rdf:RDF>"""

def generate_content_hpf():
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><opf:package {OWPML_NAMESPACES} version="" unique-identifier="" id=""><opf:metadata><opf:title/><opf:language>ko</opf:language><opf:meta name="creator" content="text">Antigravity</opf:meta><opf:meta name="subject" content="text"/><opf:meta name="description" content="text"/><opf:meta name="lastsaveby" content="text">Antigravity</opf:meta><opf:meta name="CreatedDate" content="text">2026-01-06T12:00:00Z</opf:meta><opf:meta name="ModifiedDate" content="text">2026-01-06T12:00:00Z</opf:meta><opf:meta name="date" content="text">2026년 1월 6일</opf:meta><opf:meta name="keyword" content="text"/></opf:metadata><opf:manifest><opf:item id="header" href="Contents/header.xml" media-type="application/xml"/><opf:item id="section0" href="Contents/section0.xml" media-type="application/xml"/><opf:item id="settings" href="settings.xml" media-type="application/xml"/></opf:manifest><opf:spine><opf:itemref idref="header" linear="yes"/><opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>"""

# Minimal Base64 1x1 transparent PNG for preview
PREVIEW_IMAGE_BASE64 = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'


class HWPGenerator:
    """
    Generates a valid .hwpx (OWPML) file from HwpActions.
    Implements KS X 6101 (OWPML) standard structure for Hancom HWP 2024.
    Based on analysis of official Skeleton.hwpx from python-hwpx library.
    """
    def __init__(self):
        self.sections = []
        self.header_manager = HeaderManager()

    def generate(self, actions: List[HwpAction], output_filename: str):
        section_xml = self._build_section_xml(actions)
        header_xml = self.header_manager.generate_header_xml()
        
        print(f"[HWPGenerator] Creating {output_filename}...")
        with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as z:
            # 1. Mimetype MUST be first entry and STORED (not compressed)
            z.writestr("mimetype", "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
            
            # 2. version.xml (STORED like mimetype for compatibility)
            z.writestr("version.xml", VERSION_XML, compress_type=zipfile.ZIP_STORED)
            
            # 3. Contents folder
            z.writestr("Contents/header.xml", header_xml)
            z.writestr("Contents/section0.xml", section_xml)
            
            # 4. Preview folder
            z.writestr("Preview/PrvText.txt", " ")
            z.writestr("Preview/PrvImage.png", PREVIEW_IMAGE_BASE64, compress_type=zipfile.ZIP_STORED)
            
            # 5. Settings
            z.writestr("settings.xml", SETTINGS_XML)
            
            # 6. META-INF
            z.writestr("META-INF/container.rdf", CONTAINER_RDF)
            z.writestr("Contents/content.hpf", generate_content_hpf())
            z.writestr("META-INF/container.xml", CONTAINER_XML)
            z.writestr("META-INF/manifest.xml", MANIFEST_XML)
            
        print(f"[HWPGenerator] Saved to {output_filename}")

    def _build_section_xml(self, actions: List[HwpAction]) -> str:
        # Section XML with proper namespaces and structure
        xml_parts = [
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec {OWPML_NAMESPACES}>'
        ]
        
        # First paragraph MUST contain section properties (secPr)
        # Use ID similar to Skeleton.hwpx pattern
        first_para_id = "3121190098"
        
        # Section Properties (critical for HWP to parse)
        sec_pr = '''<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0"><hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/><hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/><hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr><hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr><hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr><hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill></hp:secPr>'''
        
        col_pr = '<hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl>'
        
        # First paragraph with section properties
        xml_parts.append(f'<hp:p id="{first_para_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">')
        xml_parts.append(f'<hp:run charPrIDRef="0">{sec_pr}{col_pr}</hp:run>')
        xml_parts.append('<hp:run charPrIDRef="0"><hp:t/></hp:run>')
        xml_parts.append('<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" flags="393216"/></hp:linesegarray>')
        xml_parts.append('</hp:p>')
        
        # State tracking for subsequent paragraphs
        current_para_shape = SetParaShape()
        para_counter = 1  # Start from 1 since 0 is used for section paragraph
        
        for action in actions:
            if isinstance(action, SetParaShape):
                current_para_shape = action
                
            elif isinstance(action, InsertText):
                para_id = self.header_manager.get_para_pr_id(current_para_shape)
                safe = action.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                parts = safe.split('\n')
                for part in parts:
                    para_xml = f'<hp:p id="{para_counter}" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                    if part.strip():
                        para_xml += f'<hp:run charPrIDRef="0"><hp:t>{part}</hp:t></hp:run>'
                    else:
                        para_xml += '<hp:run charPrIDRef="0"><hp:t/></hp:run>'
                    para_xml += '</hp:p>'
                    
                    xml_parts.append(para_xml)
                    para_counter += 1

        xml_parts.append('</hs:sec>')
        return "".join(xml_parts)

import zipfile
import os
from typing import List
from pathlib import Path
from lib.models import HwpAction, InsertText, SetParaShape, CreateTable

# Common namespace declarations for all OWPML XML files
OWPML_NAMESPACES = 'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hp10="http://www.hancom.co.kr/hwpml/2016/paragraph" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hhs="http://www.hancom.co.kr/hwpml/2011/history" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf/" xmlns:ooxmlchart="http://www.hancom.co.kr/hwpml/2016/ooxmlchart" xmlns:hwpunitchar="http://www.hancom.co.kr/hwpml/2016/HwpUnitChar" xmlns:epub="http://www.idpf.org/2007/ops" xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0"'


class HWPGenerator:
    """
    Generates a valid .hwpx (OWPML) file from HwpActions.
    Uses official Skeleton.hwpx as base template to ensure HWP 2024 compatibility.
    Only modifies section0.xml content while preserving all other template files.
    """
    
    SKELETON_PATH = Path(__file__).parent.parent.parent / "Skeleton.hwpx"
    
    def __init__(self):
        self.para_shapes = {}  # Cache for paragraph shape IDs
        
    def generate(self, actions: List[HwpAction], output_filename: str):
        """Generate HWPX file by modifying Skeleton.hwpx template."""
        
        if not self.SKELETON_PATH.exists():
            raise FileNotFoundError(
                f"Skeleton.hwpx template not found at {self.SKELETON_PATH}. "
                "Please download it from: https://github.com/airmang/python-hwpx/raw/main/src/hwpx/data/Skeleton.hwpx"
            )
        
        section_xml = self._build_section_xml(actions)
        
        print(f"[HWPGenerator] Creating {output_filename} from Skeleton.hwpx template...")
        
        with zipfile.ZipFile(self.SKELETON_PATH, 'r') as template:
            with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as output:
                for item in template.infolist():
                    if item.filename == "Contents/section0.xml":
                        # Replace section content with our generated content
                        output.writestr(item, section_xml)
                    else:
                        # Copy all other files as-is
                        output.writestr(item, template.read(item.filename), compress_type=item.compress_type)
                        
        print(f"[HWPGenerator] Saved to {output_filename}")

    def _get_para_shape_id(self, shape: SetParaShape) -> int:
        """Get or create paragraph shape ID. Uses ID 0 (default) for now."""
        # Skeleton.hwpx has predefined paragraph styles
        # ID 0 is the default normal paragraph style
        # For now, we use ID 0 for all paragraphs
        # Future enhancement: map SetParaShape to appropriate predefined styles
        return 0
    
    def _build_section_xml(self, actions: List[HwpAction]) -> str:
        """Build section0.xml with proper structure based on Skeleton.hwpx format."""
        
        xml_parts = [
            f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?><hs:sec {OWPML_NAMESPACES}>'
        ]
        
        # Section Properties (exact copy from Skeleton.hwpx - required for HWP parsing)
        sec_pr = '''<hp:secPr id="" textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" tabStopVal="4000" tabStopUnit="HWPUNIT" outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" masterPageCnt="0"><hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/><hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/><hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" showLineNumber="0"/><hp:lineNumberShape restartType="0" countBy="0" distance="0" startNumber="0"/><hp:pagePr landscape="WIDELY" width="59528" height="84186" gutterType="LEFT_ONLY"><hp:margin header="4252" footer="4252" gutter="0" left="8504" right="8504" top="5668" bottom="4252"/></hp:pagePr><hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr><hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" suffixChar=")" supscript="0"/><hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/><hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/><hp:numbering type="CONTINUOUS" newNum="1"/><hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr><hp:pageBorderFill type="BOTH" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="EVEN" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill><hp:pageBorderFill type="ODD" borderFillIDRef="1" textBorder="PAPER" headerInside="0" footerInside="0" fillArea="PAPER"><hp:offset left="1417" right="1417" top="1417" bottom="1417"/></hp:pageBorderFill></hp:secPr>'''
        
        col_pr = '<hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" sameSz="1" sameGap="0"/></hp:ctrl>'
        
        # First paragraph MUST contain section properties
        first_para_id = "3121190098"
        xml_parts.append(f'<hp:p id="{first_para_id}" paraPrIDRef="0" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">')
        xml_parts.append(f'<hp:run charPrIDRef="0">{sec_pr}{col_pr}</hp:run>')
        xml_parts.append('<hp:run charPrIDRef="0"><hp:t/></hp:run>')
        xml_parts.append('<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" flags="393216"/></hp:linesegarray>')
        xml_parts.append('</hp:p>')
        
        # Process user actions
        para_counter = 1
        current_para_shape = SetParaShape()
        
        for action in actions:
            if isinstance(action, SetParaShape):
                current_para_shape = action
                
            elif isinstance(action, InsertText):
                para_id = self._get_para_shape_id(current_para_shape)
                safe = action.text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                
                # Split by newlines and create paragraphs
                parts = safe.split('\n')
                for part in parts:
                    # Build paragraph with proper structure
                    para_xml = f'<hp:p id="{para_counter}" paraPrIDRef="{para_id}" styleIDRef="0" pageBreak="0" columnBreak="0" merged="0">'
                    
                    if part.strip():
                        para_xml += f'<hp:run charPrIDRef="0"><hp:t>{part}</hp:t></hp:run>'
                    else:
                        para_xml += '<hp:run charPrIDRef="0"><hp:t/></hp:run>'
                    
                    # Add minimal linesegarray (HWP will recalculate on open)
                    para_xml += '<hp:linesegarray><hp:lineseg textpos="0" vertpos="0" vertsize="1000" textheight="1000" baseline="850" spacing="600" horzpos="0" horzsize="42520" flags="393216"/></hp:linesegarray>'
                    para_xml += '</hp:p>'
                    
                    xml_parts.append(para_xml)
                    para_counter += 1

        xml_parts.append('</hs:sec>')
        return "".join(xml_parts)

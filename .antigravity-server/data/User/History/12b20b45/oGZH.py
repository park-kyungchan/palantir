from typing import List, Dict, Any
from lib.models import SetParaShape

class HeaderManager:
    """
    Manages formatting metadata (Header) for OWPML.
    Handles 'paraPr' (Paragraph Properties) and ID assignments.
    """
    def __init__(self):
        self.para_shapes = [] # List of unique dicts or objects
        self.para_pr_map = {} # Hash -> ID mapping to avoid duplicates

    def get_para_pr_id(self, action: SetParaShape) -> int:
        """
        Registers a SetParaShape action and returns its ID.
        If an identical shape exists, returns existing ID.
        """
        # Create a hashable signature
        # Convert Pydantic model to tuple of items sorted by key
        # (left_margin, right_margin, indent, line_spacing, heading_type)
        sig = (
            action.left_margin, 
            action.right_margin, 
            action.indent, 
            action.line_spacing, 
            action.heading_type
        )
        
        if sig in self.para_pr_map:
            return self.para_pr_map[sig]
        
        new_id = len(self.para_shapes)
        self.para_shapes.append(action)
        self.para_pr_map[sig] = new_id
        return new_id

    def generate_header_xml(self) -> str:
        """
        Generates the full Content/header.xml
        """
        xml_lines = [
            '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>',
            '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" xmlns:hm="http://www.hancom.co.kr/hwpml/2011/master-page" xmlns:hpf="http://www.hancom.co.kr/hwpml/2011/presentation" xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section">',
            '<hh:docOption><hh:linkinfo path="" pageInherit="0" footnoteInherit="0"/></hh:docOption>',
            
            # Mandatory FaceName List (fontRef depends on this)
            '<hh:faceNameList>',
            '<hh:faceName id="0" lang="hangul" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="latin" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="hanja" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="japanese" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="other" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="symbol" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '<hh:faceName id="0" lang="user" name="HamChorom Batang" substitute="Batang" type="unknown"/>',
            '</hh:faceNameList>',
            
            # Char Properties
            '<hh:charPrList>',
            '<hh:charPr id="0" height="1000" textColor="000000" shadedColor="none" shadeRatio="0" borderFillIDRef="0" fontRef="0" ratio="100" spacing="0" relSz="100" offset="0" symmark="0" href="" borderOffset="0" useFontSpace="0" useKerning="0">',
            # Note: hc:font matches faceNameList. fontRef="0" points to faceNameList entries with id="0"?
            # Actually fontRef is an index into faceNameList. 
            # If we give them all ID 0, it works or we need distinct IDs? 
            # In simple OWPML, fontRef references the `id` attribute of `faceName`.
            '<hc:font face="HamChorom Batang" type="hangul" isEmbedded="0"/><hc:font face="HamChorom Batang" type="latin" isEmbedded="0"/><hc:font face="HamChorom Batang" type="hanja" isEmbedded="0"/><hc:font face="HamChorom Batang" type="japanese" isEmbedded="0"/><hc:font face="HamChorom Batang" type="other" isEmbedded="0"/><hc:font face="HamChorom Batang" type="symbol" isEmbedded="0"/><hc:font face="HamChorom Batang" type="user" isEmbedded="0"/>',
            '</hh:charPr>',
            '</hh:charPrList>',
            '<hh:paraPrList>'
        ]
        
        # Ensure ID 0 exists for Default Style
        # If ID 0 is not in self.para_shapes (implied by keys), we must inject a dummy.
        # Check if ID 0 was assigned.
        
        # If para_shapes is empty, or if we have shapes but their logic assigned IDs 0, 1... 
        # (HeaderManager implementation: new_id = len(self.para_shapes))
        # So IDs are always contiguous 0..N.
        # If para_shapes is NOT empty, ID 0 exists.
        # If empty, we must add text.
        
        if not self.para_shapes:
             # Add default normal shape
             default_shape = SetParaShape()
             self.para_shapes.append(default_shape)
             # Update map manually if needed, but here we just need XML output.
        
        for idx, shape in enumerate(self.para_shapes):
            xml_lines.append(self._para_shape_to_xml(idx, shape))
            
        xml_lines.append('</hh:paraPrList>')
        
        # Mandatory Style List
        # Style 0 must exist if used in section0.xml as styleIDRef="0"
        xml_lines.append('<hh:styleList>')
        xml_lines.append('<hh:style id="0" type="para" name="Normal" engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langID="1042" textColor="000000"/>')
        xml_lines.append('</hh:styleList>')
        
        # Mandatory BorderFill List (Referenced by charPr)
        xml_lines.append('<hh:borderFillList>')
        xml_lines.append('<hh:borderFill id="0" threeD="0" shadow="0" centerLine="0" breakCellSeparateLine="0">')
        xml_lines.append('<hc:slash type="none" Crooked="0" isCounter="0"/><hc:backSlash type="none" Crooked="0" isCounter="0"/><hc:leftBorder type="none" width="0.1mm" color="000000"/><hc:rightBorder type="none" width="0.1mm" color="000000"/><hc:topBorder type="none" width="0.1mm" color="000000"/><hc:bottomBorder type="none" width="0.1mm" color="000000"/><hc:diagonal type="none" width="0.1mm" color="000000"/>')
        xml_lines.append('</hh:borderFill>')
        xml_lines.append('</hh:borderFillList>')

        xml_lines.append('</hh:head>')
        return "".join(xml_lines)

    def _para_shape_to_xml(self, id: int, shape: SetParaShape) -> str:
        # Convert Point to HWP Unit (1 pt = 100 HWP Unit) - Approx
        # Actually HWP Unit is 1/7200 inch? 
        # Win32 API uses HWPUnit. 
        # 1 pt = 100 HWP Units is a common simplification 
        # (10 pt font = 1000 height).
        # Margins: 1 pt = 100 units.
        
        left = shape.left_margin * 100
        right = shape.right_margin * 100
        indent = shape.indent * 100
        line_spacing = shape.line_spacing 
        
        lines = [
            f'<hh:paraPr id="{id}" type="normal">',
            f'<hp:align horizontal="left"/>',
            f'<hp:margin left="{left}" right="{right}" top="0" bottom="0" indent="{indent}" prev="0" next="0"/>',
            f'<hp:lineSpacing type="percent" val="{line_spacing}" unit="percent"/>',
            f'</hh:paraPr>'
        ]
        return "".join(lines)

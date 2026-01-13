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
            '<hh:paraPrList>'
        ]
        
        # Default Style (ID 0) - if empty, HWPX might require at least one.
        # But our manager will populate from usage.
        # Note: ID 0 is often reserved or expected.
        # Let's ensure if nothing registered, we have a default?
        # Or just list what we have.
        
        for idx, shape in enumerate(self.para_shapes):
            xml_lines.append(self._para_shape_to_xml(idx, shape))
            
        xml_lines.append('</hh:paraPrList>')
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

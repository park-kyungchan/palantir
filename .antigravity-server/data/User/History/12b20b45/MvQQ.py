"""
Header Manager
Manages validation and dynamic creation of styles in header.xml.

Responsibilities:
- Manage <hh:borderFills> (Border/Background styles)
- Manage <hh:charProperties> (Font characteristics)
- Manage <hh:paraProperties> (Paragraph characteristics)
- Ensure unique IDs and correct item counts
- Compliance with OWPML namespaces

Ref: KS X 6101
"""

import xml.etree.ElementTree as ET
from typing import Dict, Tuple, Optional

# Namespaces
HH_NS = 'http://www.hancom.co.kr/hwpml/2011/head'
HP_NS = 'http://www.hancom.co.kr/hwpml/2011/paragraph'
HC_NS = 'http://www.hancom.co.kr/hwpml/2011/core'


def _hh(tag: str) -> str:
    """Helper to create hh: namespace tag."""
    return f'{{{HH_NS}}}{tag}'

def _hc(tag: str) -> str:
    """Helper to create hc: namespace tag."""
    return f'{{{HC_NS}}}{tag}'


class HeaderManager:
    """Manages the <hh:head> element and its children."""
    
    def __init__(self, header_elem: ET.Element):
        self.header = header_elem
        self.ns = {'hh': HH_NS, 'hp': HP_NS, 'hc': HC_NS}
        
        # Cache current max IDs
        self._border_max_id = self._init_max_id('borderFills', 'borderFill')
        self._char_max_id = self._init_max_id('charProperties', 'charPr')
        self._para_max_id = self._init_max_id('paraProperties', 'paraPr')
        self.max_numbering_id = self._init_max_id('numberings', 'numbering')
        
        # Element References
        self.para_properties = self.header.find('.//hh:paraProperties', self.ns)
        self.char_properties = self.header.find('.//hh:charProperties', self.ns)
        self.numberings = self.header.find('.//hh:numberings', self.ns)
        
        # Caches
        self._para_pr_cache = {}
        self._char_pr_cache = {}
        
    def _init_max_id(self, parent_tag: str, child_tag: str) -> int:
        """Scan existing IDs to find maximum."""
        parent = self.header.find(f'.//hh:{parent_tag}', self.ns)
        if parent is None:
            return 0
            
        max_id = 0
        for child in parent.findall(f'hh:{child_tag}', self.ns):
            try:
                cid = int(child.get('id', '0'))
                if cid > max_id:
                    max_id = cid
            except ValueError:
                pass
        return max_id

    def get_or_create_char_pr(self, font_size_pt: int = 10, is_bold: bool = False, color: str = "#000000") -> str:
        """
        Get or Create charProperty ID.
        Args:
           font_size_pt: Size in points (e.g. 10). Converted to HWP unit (1000).
           is_bold: Boolean
           color: Hex string
        """
        # Finds container
        container = self.header.find(f'.//hh:charProperties', self.ns)
        if container is None:
             raise ValueError("Invalid header.xml: <hh:charProperties> not found")
        
        # Check if identical style exists (Optimization: Strict check is hard, let's just create new for now)
        # TODO: Implement dedup logic
        
        self._char_max_id += 1
        new_id = str(self._char_max_id)
        
        # HWP uses 0.01 pt for height (e.g. 10pt = 1000)
        hwp_size = str(font_size_pt * 100)
        
        char_pr = ET.SubElement(container, _hh('charPr'), {
            'id': new_id,
            'height': hwp_size,
            'textColor': color,
            'shadeColor': 'none',
            'useFontSpace': '0', 'useKerning': '0', 'symMark': '0', 'borderFillIDRef': '0'
        })
        
        # Fonts (Ref defaults for now - assuming ID 0 defines 'Hamchorom')
        # We need to explicitly set fontRef or it inherits? 
        # Usually we link to existing fontRef. Let's reuse standard mappings for 'Hangul'/'Latin'
        # <hh:fontRef hangul="0" latin="0" ... /> if IDs match fontFaces
        ET.SubElement(char_pr, _hh('fontRef'), {'hangul': '0', 'latin': '0', 'hanja': '0', 'japanese': '0', 'other': '0', 'symbol': '0', 'user': '0'})
        ET.SubElement(char_pr, _hh('ratio'), {'hangul': '100', 'latin': '100', 'hanja': '100', 'japanese': '100', 'other': '100', 'symbol': '100', 'user': '100'})
        ET.SubElement(char_pr, _hh('spacing'), {'hangul': '0', 'latin': '0', 'hanja': '0', 'japanese': '0', 'other': '0', 'symbol': '0', 'user': '0'})
        ET.SubElement(char_pr, _hh('relSz'), {'hangul': '100', 'latin': '100', 'hanja': '100', 'japanese': '100', 'other': '100', 'symbol': '100', 'user': '100'})
        ET.SubElement(char_pr, _hh('offset'), {'hangul': '0', 'latin': '0', 'hanja': '0', 'japanese': '0', 'other': '0', 'symbol': '0', 'user': '0'})
        
        # Bold
        bold_val = '1' if is_bold else '0'
        ET.SubElement(char_pr, _hh('bold'), {'value': bold_val})
        ET.SubElement(char_pr, _hh('italic'), {'value': '0'})
        ET.SubElement(char_pr, _hh('underline'), {'type': 'NONE', 'shape': 'SOLID', 'color': '#000000'})
        ET.SubElement(char_pr, _hh('strikeout'), {'type': 'NONE', 'shape': 'SOLID'})
        ET.SubElement(char_pr, _hh('outline'), {'type': 'NONE'})
        ET.SubElement(char_pr, _hh('shadow'), {'type': 'NONE'})
        ET.SubElement(char_pr, _hh('emboss'), {'value': '0'})
        ET.SubElement(char_pr, _hh('engrave'), {'value': '0'})
        ET.SubElement(char_pr, _hh('superscript'), {'value': '0'})
        ET.SubElement(char_pr, _hh('subscript'), {'value': '0'})

        # Update Count
        current_cnt = int(container.get('itemCnt', '0'))
        container.set('itemCnt', str(current_cnt + 1))
        
        return new_id

    def get_or_create_para_pr(self, align_type: str, indent: int = 0, line_spacing: int = 160, numbering_id: str = None) -> str:
        """
        Get or create paraPrID.
        align_type: 'Left', 'Center', 'Right', 'Justify'
        indent: Points (0 default)
        line_spacing: % (160 default)
        numbering_id: Optional ID of numbering style (hh:numberings).
        """
        align_map = {
            'Left': 'LEFT', 'Center': 'CENTER', 
            'Right': 'RIGHT', 'Justify': 'JUSTIFY'
        }
        align_str = align_map.get(align_type, 'LEFT')
        
        # Check cache
        key = f"{align_str}_{indent}_{line_spacing}_{numbering_id}"
        if key in self._para_pr_cache:
            return self._para_pr_cache[key]
            
        # Create New
        self._para_max_id += 1
        new_id = str(self._para_max_id)
        
        para_pr_attrs = {
            'id': new_id,
            'tabPrIDRef': '0',
            'condense': '0', 'fontLineHeight': '0', 'snapToGrid': '0',
            'suppressLineNumbers': '0', 'checked': '0'
        }
        if numbering_id:
             para_pr_attrs['numberingIDRef'] = numbering_id

        para_pr = ET.SubElement(self.para_properties, _hh('paraPr'), para_pr_attrs)
        
        ET.SubElement(para_pr, _hh('align'), {
            'horizontal': align_str, 'vertical': 'BASELINE'
        })
        
        # Numbering
        ET.SubElement(para_pr, _hh('heading'), {
            'type': 'NONE', 'idRef': '0', 'level': '0' # Outline logic separate
        })
        ET.SubElement(para_pr, _hh('breakSetting'), {
            'breakType': 'NONE', 'pageBreak': '0', 'columnBreak': '0'
        })
        
        # Margin
        hwp_indent = str(int(indent * 100))
        margin_attr = {
            'indent': hwp_indent, 'left': '0', 'right': '0', 
            'prev': '0', 'next': '0'
        }
        
        ET.SubElement(para_pr, _hh('margin'), margin_attr)
        
        # Line Spacing
        ET.SubElement(para_pr, _hh('lineSpacing'), {
            'type': 'PERCENT', 'value': str(line_spacing), 'unit': 'PERCENT'
        })
        
        ET.SubElement(para_pr, _hh('border'), {
            'borderFillIDRef': '0', 'offsetLeft': '0', 'offsetRight': '0',
            'offsetTop': '0', 'offsetBottom': '0'
        })
        
        # TrackChange
        ET.SubElement(para_pr, _hh('trackChange'), {'tagIDRef': '0'})
        
        self._para_pr_cache[key] = new_id
        
        # Update itemCnt
        self.para_properties.set('itemCnt', str(len(self.para_properties)))
        
        return new_id

    def get_or_create_border_fill(self, border_type: str = "Solid", width: str = "0.1mm", color: str = "#000000", fill_color: Optional[str] = None) -> str:
        """
        Get existing or create new borderFill ID.
        Args:
            border_type: Solid, None, Dash, etc.
            width: e.g. "0.1mm"
            color: Hex "#000000" or "Black"
            fill_color: Hex or None
        """
        # Map inputs
        b_type = border_type.upper() if border_type else "SOLID"
        if b_type == "BLACK": b_type = "SOLID" # Fix if user mapped color to type? No.
        
        b_color = color
        if b_color.lower() == "black": b_color = "#000000"
        
        container = self.header.find(f'.//hh:borderFills', self.ns)
        if container is None:
             raise ValueError("header.xml missing borderFills")
             
        self._border_max_id += 1
        new_id = str(self._border_max_id)
        
        bf = ET.SubElement(container, _hh('borderFill'), {
            'id': new_id, 
            'threeD': '0', 'shadow': '0', 'centerLine': 'NONE', 'breakCellSeparateLine': '0'
        })
        
        # Diagonals (None)
        ET.SubElement(bf, _hh('slash'), {'type': 'NONE', 'Crooked': '0', 'isCounter': '0'})
        ET.SubElement(bf, _hh('backSlash'), {'type': 'NONE', 'Crooked': '0', 'isCounter': '0'})
        
        # Borders
        for side in ['leftBorder', 'rightBorder', 'topBorder', 'bottomBorder']:
            ET.SubElement(bf, _hh(side), {'type': b_type, 'width': width, 'color': b_color})
            
        ET.SubElement(bf, _hh('diagonal'), {'type': 'NONE', 'width': '0.1 mm', 'color': '#000000'})
        
        # FillBrush (Background)
        if fill_color:
            fb = ET.SubElement(bf, _hc('fillBrush'))
            ET.SubElement(fb, _hc('winBrush'), {
                'faceColor': fill_color, 
                'hatchColor': 'none', 
                'alpha': '0'
            })
            
        # Update Count
        current_cnt = int(container.get('itemCnt', '0'))
        container.set('itemCnt', str(current_cnt + 1))
        
        return new_id
        
    def _check_id_exists(self, container: ET.Element, target_id: str) -> bool:
        """Check if specific ID exists in container."""
        for child in container:
            if child.get('id') == target_id:
                return True
        return False
        
    def get_or_create_numbering(self, numbering_type: str) -> str:
        """
        Create a new numbering style (Number or Bullet).
        Returns numberingID.
        """
        if numbering_type == 'None':
            return None
            
        self.max_numbering_id += 1
        n_id = str(self.max_numbering_id)
        
        numbering = ET.SubElement(self.numberings, _hh('numbering'), {
            'id': n_id,
            'start': '1'
        })
        
        # Create 7 levels (HWP standard supports 7-10)
        # Type: "Number" -> ^1.
        # Type: "Bullet" -> •
        
        for level in range(1, 8):
            # Format
            text = f"^{level}." if numbering_type == 'Number' else "•"
            num_format = 'DIGIT' if numbering_type == 'Number' else 'DIGIT' 
            
            head = ET.SubElement(numbering, _hh('paraHead'), {
                'start': '1', 'level': str(level), 'align': 'LEFT',
                'useInstWidth': '1', 'autoIndent': '1', 'widthAdjust': '0',
                'textOffsetType': 'PERCENT', 'textOffset': '50',
                'numFormat': num_format,
                'charPrIDRef': '4294967295', 'checkable': '0'
            })
            head.text = text
            
        self.numberings.set('itemCnt', str(len(self.numberings)))
        return n_id

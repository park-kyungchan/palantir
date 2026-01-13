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


def _hh(tag: str) -> str:
    return f'{{{HH_NS}}}{tag}'


class HeaderManager:
    """Manages the <hh:head> element and its children."""
    
    def __init__(self, header_elem: ET.Element):
        self.header = header_elem
        self.ns = {'hh': HH_NS, 'hp': HP_NS}
        
        # Cache current max IDs
        self._border_max_id = self._init_max_id('borderFills', 'borderFill')
        
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

    def get_or_create_border_fill(self, border_type: str = "SOLID", width: str = "0.12mm", color: str = "#000000") -> str:
        """
        Get existing or create new borderFill ID.
        (Currently always creates new one to avoid strict equality check complexity)
        
        Args:
            border_type: SOLID, NONE, DASH, DOT, etc.
            width: Width string (e.g. "0.12mm")
            color: Color hex string (e.g. "#000000")
            
        Returns:
            ID string (e.g. "3")
        """
        # Finds container
        container = self.header.find(f'.//hh:borderFills', self.ns)
        if container is None:
            raise ValueError("Invalid header.xml: <hh:borderFills> not found")
            
        # Optimization: If asking for None border, return ID 1 (Standard None)
        if border_type == "NONE" and self._check_id_exists(container, '1'):
             return '1'

        # Create new ID
        self._border_max_id += 1
        new_id = str(self._border_max_id)
        
        # Create element
        bf = ET.SubElement(container, _hh('borderFill'), {
            'id': new_id,
            'threeD': '0',
            'shadow': '0',
            'centerLine': 'NONE',
            'breakCellSeparateLine': '0'
        })
        
        # Add 4 borders + diagonal
        sides = ['leftBorder', 'rightBorder', 'topBorder', 'bottomBorder']
        for side in sides:
            ET.SubElement(bf, _hh(side), {
                'type': border_type,
                'width': width,
                'color': color
            })
            
        # Diagonals (usually None)
        ET.SubElement(bf, _hh('diagonal'), {'type': 'NONE', 'width': '0.1mm', 'color': '#000000'})
        
        # Update itemCnt
        current_cnt = int(container.get('itemCnt', '0'))
        container.set('itemCnt', str(current_cnt + 1))
        
        return new_id
        
    def _check_id_exists(self, container: ET.Element, target_id: str) -> bool:
        """Check if specific ID exists in container."""
        for child in container:
            if child.get('id') == target_id:
                return True
        return False

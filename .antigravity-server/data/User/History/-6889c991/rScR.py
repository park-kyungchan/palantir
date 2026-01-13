"""
BinData Manager
Manages Registry of Binary Data (Images, OLE, etc) in content.hpf.

Responsibilities:
- Manage <opf:manifest> in content.hpf
- Generate unique IDs for binary items
- Track BinData file paths and MIME types
- Ensure OCF compliance

Ref: KS X 6101, OCF
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, Tuple, Optional

# Namespaces
OPF_NS = 'http://www.idpf.org/2007/opf/'

def _opf(tag: str) -> str:
    return f'{{{OPF_NS}}}{tag}'

class BinDataManager:
    """Manages content.hpf manifest and BinData ID generation."""
    
    def __init__(self, content_hpf_elem: ET.Element):
        self.root = content_hpf_elem
        self.ns = {'opf': OPF_NS}
        self.manifest = self.root.find(f'.//opf:manifest', self.ns)
        if self.manifest is None:
            raise ValueError("Invalid content.hpf: <opf:manifest> not found")
            
        self._max_bin_id = self._init_max_id()
        
    def _init_max_id(self) -> int:
        """Scan existing bin IDs (format 'binXXXX')."""
        max_val = 0
        for item in self.manifest.findall(f'opf:item', self.ns):
            iid = item.get('id', '')
            if iid.startswith('bin'):
                try:
                    # extract number from 'bin0001'
                    val = int(iid[3:])
                    if val > max_val:
                        max_val = val
                except ValueError:
                    pass
        return max_val

    def add_bin_item(self, filename: str, mime_type: str) -> Tuple[str, str]:
        """
        Register a new binary item.
        
        Args:
            filename: e.g. "image.png" (User filename, used for extension)
            mime_type: e.g. "image/png"
            
        Returns:
            (id, internal_path)
            e.g. ("bin0001", "BinData/bin0001.png")
        """
        self._max_bin_id += 1
        new_id = f"bin{self._max_bin_id:04d}"
        
        ext = os.path.splitext(filename)[1]
        if not ext: ext = ".dat"
        
        internal_filename = f"{new_id}{ext}"
        internal_path = f"BinData/{internal_filename}"
        
        # Add to manifest
        # <opf:item id="bin0001" href="BinData/bin0001.png" media-type="image/png" isEmbeded="1"/>
        # Note: isEmbeded attribute is NOT in OPF namespace, it's unqualified or app specific.
        # Based on HWPX samples, it appears as attribute.
        
        item = ET.SubElement(self.manifest, _opf('item'), {
            'id': new_id,
            'href': internal_path,
            'media-type': mime_type,
            'isEmbeded': '1' 
        })
        
        return new_id, internal_path
        
    def get_manifest_xml(self) -> ET.Element:
        return self.root

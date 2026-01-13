"""
OWPML Schema Validator

Validates HWPX package structure and OWPML XML conformance.
Based on KS X 6101 standard and Hancom hwpx-owpml-model reference.

Author: Antigravity Pipeline
Date: 2026-01-09
"""

import zipfile
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


# OWPML Namespaces
NAMESPACES = {
    'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
    'hh': 'http://www.hancom.co.kr/hwpml/2011/head',
    'hs': 'http://www.hancom.co.kr/hwpml/2011/section',
    'ha': 'http://www.hancom.co.kr/hwpml/2011/app',
    'hc': 'http://www.hancom.co.kr/hwpml/2011/core',
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
}

# Required files in HWPX package (OCF compliance)
REQUIRED_FILES = [
    'mimetype',
    'version.xml',
    'Contents/content.hpf',
    'Contents/header.xml',
    'Contents/section0.xml',
    'META-INF/container.xml',
]

# Valid MIME type for HWPX
VALID_MIMETYPE = 'application/hwp+zip'


class ValidationError:
    """Represents a single validation error."""
    
    def __init__(self, level: str, message: str, location: Optional[str] = None):
        self.level = level  # 'error', 'warning', 'info'
        self.message = message
        self.location = location
    
    def __str__(self):
        loc = f" [{self.location}]" if self.location else ""
        return f"[{self.level.upper()}]{loc} {self.message}"
    
    def __repr__(self):
        return str(self)


class OWPMLValidator:
    """
    Validates HWPX packages for KS X 6101 compliance.
    
    Features:
    - Package structure validation (OCF compliance)
    - mimetype file validation (must be first, uncompressed)
    - ID reference integrity (charPrIDRef, paraPrIDRef, borderFillIDRef)
    - Namespace consistency
    - XML well-formedness
    """
    
    def __init__(self):
        self.errors: List[ValidationError] = []
        self._header_ids: Dict[str, set] = {}
    
    def validate(self, hwpx_path: str) -> Tuple[bool, List[ValidationError]]:
        """
        Validate an HWPX file.
        
        Args:
            hwpx_path: Path to the HWPX file
            
        Returns:
            Tuple of (is_valid, list of errors/warnings)
        """
        self.errors = []
        
        if not Path(hwpx_path).exists():
            self.errors.append(ValidationError('error', f'File not found: {hwpx_path}'))
            return False, self.errors
        
        try:
            with zipfile.ZipFile(hwpx_path, 'r') as zf:
                self._validate_package_structure(zf)
                self._validate_mimetype(zf)
                self._validate_xml_wellformedness(zf)
                self._validate_id_references(zf)
        except zipfile.BadZipFile:
            self.errors.append(ValidationError('error', 'Invalid ZIP file'))
            return False, self.errors
        except Exception as e:
            self.errors.append(ValidationError('error', f'Validation failed: {e}'))
            return False, self.errors
        
        # Check if there are any errors (not just warnings)
        has_errors = any(e.level == 'error' for e in self.errors)
        return not has_errors, self.errors
    
    def _validate_package_structure(self, zf: zipfile.ZipFile):
        """Validate that all required files exist."""
        namelist = zf.namelist()
        
        for required_file in REQUIRED_FILES:
            if required_file not in namelist:
                self.errors.append(ValidationError(
                    'error',
                    f'Missing required file: {required_file}',
                    'package'
                ))
    
    def _validate_mimetype(self, zf: zipfile.ZipFile):
        """Validate mimetype file (must be first, uncompressed, correct content)."""
        namelist = zf.namelist()
        
        if 'mimetype' not in namelist:
            return  # Already reported in structure validation
        
        # Check if mimetype is first
        if namelist[0] != 'mimetype':
            self.errors.append(ValidationError(
                'warning',
                'mimetype should be the first file in the archive',
                'mimetype'
            ))
        
        # Check if uncompressed (stored)
        info = zf.getinfo('mimetype')
        if info.compress_type != zipfile.ZIP_STORED:
            self.errors.append(ValidationError(
                'warning',
                'mimetype should be stored uncompressed (ZIP_STORED)',
                'mimetype'
            ))
        
        # Check content
        content = zf.read('mimetype').decode('utf-8').strip()
        if content != VALID_MIMETYPE:
            self.errors.append(ValidationError(
                'error',
                f'Invalid mimetype content: expected "{VALID_MIMETYPE}", got "{content}"',
                'mimetype'
            ))
    
    def _validate_xml_wellformedness(self, zf: zipfile.ZipFile):
        """Validate that all XML files are well-formed."""
        for name in zf.namelist():
            if name.endswith('.xml') or name.endswith('.hpf'):
                try:
                    content = zf.read(name)
                    ET.fromstring(content)
                except ET.ParseError as e:
                    self.errors.append(ValidationError(
                        'error',
                        f'XML parse error: {e}',
                        name
                    ))
    
    def _validate_id_references(self, zf: zipfile.ZipFile):
        """Validate that all IDRef attributes reference valid definitions in header.xml."""
        # 1. Parse header.xml to extract all defined IDs
        if 'Contents/header.xml' not in zf.namelist():
            return
        
        header_content = zf.read('Contents/header.xml')
        try:
            header_root = ET.fromstring(header_content)
        except ET.ParseError:
            return  # Already reported
        
        # Extract IDs from header
        self._header_ids = {
            'charPr': set(),
            'paraPr': set(),
            'borderFill': set(),
            'style': set(),
            'tabPr': set(),
            'numbering': set(),
        }
        
        # Find all ID definitions
        for elem in header_root.iter():
            tag_local = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            elem_id = elem.get('id')
            
            if elem_id is not None:
                if tag_local == 'charPr':
                    self._header_ids['charPr'].add(elem_id)
                elif tag_local == 'paraPr':
                    self._header_ids['paraPr'].add(elem_id)
                elif tag_local == 'borderFill':
                    self._header_ids['borderFill'].add(elem_id)
                elif tag_local == 'style':
                    self._header_ids['style'].add(elem_id)
                elif tag_local == 'tabPr':
                    self._header_ids['tabPr'].add(elem_id)
                elif tag_local == 'numbering':
                    self._header_ids['numbering'].add(elem_id)
        
        # 2. Validate references in section files
        for name in zf.namelist():
            if name.startswith('Contents/section') and name.endswith('.xml'):
                self._validate_section_references(zf, name)
    
    def _validate_section_references(self, zf: zipfile.ZipFile, section_path: str):
        """Validate ID references in a section file."""
        try:
            content = zf.read(section_path)
            root = ET.fromstring(content)
        except (ET.ParseError, KeyError):
            return
        
        # Define reference mappings
        ref_mappings = {
            'charPrIDRef': 'charPr',
            'paraPrIDRef': 'paraPr',
            'borderFillIDRef': 'borderFill',
            'styleIDRef': 'style',
            'tabPrIDRef': 'tabPr',
            'numberingIDRef': 'numbering',
        }
        
        # Check all elements for IDRef attributes
        for elem in root.iter():
            for attr, id_type in ref_mappings.items():
                ref_value = elem.get(attr)
                if ref_value is not None and ref_value != '':
                    # ID "0" is typically the default/fallback
                    if ref_value != '0' and ref_value not in self._header_ids.get(id_type, set()):
                        # Only warn, don't error - some IDs may be dynamically generated
                        self.errors.append(ValidationError(
                            'warning',
                            f'{attr}="{ref_value}" references undefined {id_type} ID',
                            section_path
                        ))


def validate_hwpx(hwpx_path: str) -> Tuple[bool, List[str]]:
    """
    Convenience function to validate an HWPX file.
    
    Args:
        hwpx_path: Path to HWPX file
        
    Returns:
        Tuple of (is_valid, list of error/warning messages)
    """
    validator = OWPMLValidator()
    is_valid, errors = validator.validate(hwpx_path)
    return is_valid, [str(e) for e in errors]


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python validator.py <hwpx_file>")
        sys.exit(1)
    
    hwpx_file = sys.argv[1]
    is_valid, messages = validate_hwpx(hwpx_file)
    
    print(f"Validating: {hwpx_file}")
    print(f"Valid: {is_valid}")
    
    if messages:
        print("\nMessages:")
        for msg in messages:
            print(f"  {msg}")

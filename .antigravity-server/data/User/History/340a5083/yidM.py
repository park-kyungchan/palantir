"""
Verify Table Creation Logic
Tests the new _create_table implementation with cell merging.
"""
import os
import sys
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import CreateTable, MergeCells

def test_table_creation():
    actions = [
        CreateTable(rows=3, cols=3),
        MergeCells(start_row=0, start_col=0, row_span=2, col_span=2), # 2x2 merge at top-left
        MergeCells(start_row=2, start_col=2, row_span=1, col_span=1)  # No-op merge
    ]
    
    # Run builder
    builder = HwpxDocumentBuilder()
    output_path = "output_table_test.hwpx"
    builder.build(actions, output_path)
    
    print(f"Created {output_path}")
    
    # Verify XML content (manual check via python-hwpx or zipfile)
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(output_path, 'r') as zf:
        xml = zf.read('Contents/section0.xml').decode('utf-8')
        
    print("\nXML Preview (section0.xml):")
    # Pretty print would require external lib, just print partial
    if "rowSpan=\"2\"" in xml and "colSpan=\"2\"" in xml:
        print("✅ cellSpan attributes found!")
    else:
        print("❌ cellSpan attributes missing!")
        
    if "rowCnt=\"3\"" in xml and "colCnt=\"3\"" in xml:
        print("✅ rowCnt/colCnt correct!")
        
    # Check ghost cell suppression
    # Expected cells: 9 total - 3 (ghosts) = 6 cells
    tc_count = xml.count("hp:tc>") # count closing tags to be safe (or open tags)
    print(f"Total cells found: {tc_count//2}") # naïve count
    
    # We expect 6 <hp:tc> elements (since 3 are skipped by 2x2 merge)
    # Be careful with naïve string counting if tags have attributes
    # Better to parse
    
    root = ET.fromstring(xml)
    ns = {'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'}
    tcs = root.findall('.//hp:tc', ns)
    print(f"Actual hp:tc elements: {len(tcs)}")
    
    if len(tcs) == 6:
         print("✅ Ghost cells correctly suppressed (9 - 3 ghost = 6)")
    else:
         print(f"❌ Incorrect cell count. Expected 6, got {len(tcs)}")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        # Ensure we have a template to work with
        test_table_creation()
    else:
        print("Skipping test - Skeleton.hwpx not found")

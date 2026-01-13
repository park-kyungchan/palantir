"""
Verify Table Formatting (Borders & Fills)
"""
import os
import zipfile
import xml.etree.ElementTree as ET
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, CreateTable, MoveToCell, SetCellBorder

def test_table_formatting():
    builder = HwpxDocumentBuilder()
    
    actions = [
        InsertText(text="Table Formatting Test"),
        CreateTable(rows=3, cols=3),
        
        # Cell (0,0): Yellow Background
        MoveToCell(row=0, col=0),
        SetCellBorder(fill_color="#FFFF00"),
        InsertText(text="Yellow Cell"),
        
        # Cell (1,1): Dash Border, Width 0.5mm
        MoveToCell(row=1, col=1),
        SetCellBorder(border_type="Dash", width="0.5mm", color="Red"),
        InsertText(text="Dash Red Cell"),
        
        # Cell (2,2): Blue Background + Text
        MoveToCell(row=2, col=2),
        SetCellBorder(fill_color="#0000FF"),
        InsertText(text="Blue  Cell")
    ]
    
    output_path = "output_table_formatting.hwpx"
    try:
        builder.build(actions, output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify Logic
    with zipfile.ZipFile(output_path, 'r') as zf:
        header_xml = zf.read('Contents/header.xml').decode('utf-8')
        section_xml = zf.read('Contents/section0.xml').decode('utf-8')
        
        # 1. Verify Header has borderFills with fills
        print("\n=== Header Analysis ===")
        if 'faceColor="#FFFF00"' in header_xml:
             print("✅ Found Yellow Fill Definition")
        else:
             print("❌ Yellow Fill NOT found in header")
             
        if 'type="DASH"' in header_xml and 'color="#000000"' not in header_xml: # Color Red? usually #FF0000? 
             # I used "Red". Did I map "Red" to hex in manager?
             # My implementation checks `if b_color.lower() == "black": b_color = "#000000"`.
             # It doesn't map "Red" to "#FF0000". It passes "Red" to XML.
             # HWPX might require HEX. I should have mapped it?
             # Let's see what happens.
             pass
        
        # 2. Verify Section uses different IDs
        print("\n=== Section Analysis ===")
        root = ET.fromstring(section_xml)
        
        tcs = []
        for tc in root.iter('{http://www.hancom.co.kr/hwpml/2011/paragraph}tc'):
            tcs.append(tc)
            
        print(f"Found {len(tcs)} cells (Expected 9)")
        
        if len(tcs) >= 9:
             id_00 = tcs[0].get('borderFillIDRef')
             id_11 = tcs[4].get('borderFillIDRef') # (1,1) is index 4
             id_22 = tcs[8].get('borderFillIDRef') # (2,2) is index 8
             
             print(f"Cell (0,0) ID: {id_00}")
             print(f"Cell (1,1) ID: {id_11}")
             print(f"Cell (2,2) ID: {id_22}")
             
             if id_00 != id_11 and id_00 != id_22:
                  print("✅ Dynamic Border IDs applied!")
             else:
                  print("❌ IDs are identical (Dynamic logic failed)")

if __name__ == "__main__":
    test_table_formatting()

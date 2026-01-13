"""
Verify Context-Aware Controls (Image, TextBox, Equation) inside Tables
"""
import zipfile
import xml.etree.ElementTree as ET
import os
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, CreateTable, MoveToCell, InsertImage, InsertTextBox, InsertEquation

def create_dummy_image(path="test_image.png"):
    # Create simple 1x1 PNG pixel
    with open(path, 'wb') as f:
        # 1x1 Black Pixel PNG signature
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc`\x00\x00\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82')

def test_controls_in_table():
    create_dummy_image("test_image.png")
    
    builder = HwpxDocumentBuilder()
    
    actions = [
        InsertText(text="Controls Test"),
        CreateTable(rows=2, cols=2),
        
        # Cell (0,0): Text
        MoveToCell(row=0, col=0),
        InsertText(text="Cell 0,0: Text"),
        
        # Cell (0,1): Image
        MoveToCell(row=0, col=1),
        InsertImage(path="test_image.png", width=10, height=10),
        
        # Cell (1,0): TextBox
        MoveToCell(row=1, col=0),
        InsertTextBox(text="Cell 1,0: TB", width=20, height=10),
        
        # Cell (1,1): Equation
        MoveToCell(row=1, col=1),
        InsertEquation(script="y = x^2")
    ]
    
    output_path = "output_controls.hwpx"
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
        section_xml = zf.read('Contents/section0.xml').decode('utf-8')
        root = ET.fromstring(section_xml)
        
        # Find the table
        tbls = root.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}tbl')
        if not tbls:
            print("❌ No table found")
            return
            
        tbl = tbls[0]
        
        # Check Cells
        tcs = tbl.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}tc')
        if len(tcs) < 4:
            print(f"❌ Table has {len(tcs)} cells (Expected 4)")
            return
            
        # Cell 0,1 -> Image
        tc_01 = tcs[1] 
        pics = tc_01.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}pic')
        if pics:
            print("✅ Found Image in Cell (0,1)")
        else:
            print("❌ No Image in Cell (0,1)")
            
        # Cell 1,0 -> TextBox (rect)
        tc_10 = tcs[2]
        rects = tc_10.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}rect')
        if rects:
            print("✅ Found TextBox in Cell (1,0)")
        else:
            print("❌ No TextBox in Cell (1,0)")

        # Cell 1,1 -> Equation (eqEdit)
        tc_11 = tcs[3]
        eqs = tc_11.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}eqEdit')
        if eqs:
            print("✅ Found Equation in Cell (1,1)")
        else:
            print("❌ No Equation in Cell (1,1)")

    # Clean up
    if os.path.exists("test_image.png"):
        os.remove("test_image.png")

if __name__ == "__main__":
    test_controls_in_table()

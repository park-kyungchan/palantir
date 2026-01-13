"""
Verify Nested Tables
"""
import zipfile
import xml.etree.ElementTree as ET
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, CreateTable, MoveToCell, SetCellBorder

def test_nested_tables():
    builder = HwpxDocumentBuilder()
    
    actions = [
        InsertText(text="Nested Table Test"),
        # Outer Table (1x1)
        CreateTable(rows=1, cols=1),
        
        # Enter Outer Table Cell
        MoveToCell(row=0, col=0),
        InsertText(text="Outer Cell Content"),
        SetCellBorder(fill_color="#EEEEEE"), # Gray background
        
        # Create Inner Table (2x2) INSIDE Outer Cell
        CreateTable(rows=2, cols=2),
        
        # Enter Inner Table (Context switches to Inner because _current_table = inner)
        MoveToCell(row=0, col=0),
        InsertText(text="Inner Cell (0,0)"),
        SetCellBorder(fill_color="#FFA500") # Orange
    ]
    
    output_path = "output_nested_tables.hwpx"
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
        
        # We expect:
        # p -> run -> ctrl(Outer Table) -> tbl -> tr -> tc
        # Inside that tc:
        #   p (Text "Outer Cell Content")
        #   p -> run -> ctrl(Inner Table) -> tbl
        
        # Find all tables
        tbls = root.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}tbl')
        print(f"Found {len(tbls)} tables (Expected 2)")
        
        if len(tbls) < 2:
            print("❌ Not enough tables found")
            return
            
        outer_tbl = tbls[0]
        inner_tbl = tbls[1]
        
        # Check if Inner Table is descendant of Inner Table? No.
        # Check if Inner Table is descendant of Outer Table's Cell
        
        # Find the TC of outer table
        outer_tcs = outer_tbl.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}tc')
        if not outer_tcs:
             print("❌ Outer table has no cells")
             return
             
        outer_tc = outer_tcs[0]
        
        # Check if inner_tbl is inside outer_tc
        # ElementTree findall search is recursive from root.
        # We can search from outer_tc
        
        nested_tbls = outer_tc.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}tbl')
        if nested_tbls:
             print("✅ Success: Found Table inside Outer Cell!")
        else:
             print("❌ Failure: Inner Table NOT found inside Outer Cell")

if __name__ == "__main__":
    test_nested_tables()

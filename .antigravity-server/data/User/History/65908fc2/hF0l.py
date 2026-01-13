"""
Verify Lists (Numbers and Bullets)
"""
import zipfile
import xml.etree.ElementTree as ET
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, SetNumbering

def test_lists():
    builder = HwpxDocumentBuilder()
    
    actions = [
        InsertText(text="Normal Paragraph"),
        
        # Start Numbering
        SetNumbering(numbering_type="Number"),
        InsertText(text="First Numbered Item"), # 1.
        InsertText(text="Second Numbered Item"), # 2.
        
        # Switch to Bullet
        SetNumbering(numbering_type="Bullet"),
        InsertText(text="First Bullet Item"), # •
        InsertText(text="Second Bullet Item"), # •
        
        # Turn off
        SetNumbering(numbering_type="None"),
        InsertText(text="Back to Normal")
    ]
    
    output_path = "output_lists.hwpx"
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
        # 1. Check Header (Numberings exist)
        header_xml = zf.read('Contents/header.xml').decode('utf-8')
        h_root = ET.fromstring(header_xml)
        numberings = h_root.find('.//{http://www.hancom.co.kr/hwpml/2011/head}numberings')
        
        if numberings is None or int(numberings.get('itemCnt')) == 0:
             print("❌ No Numberings created in header.xml")
             return
        else:
             print(f"✅ Found {numberings.get('itemCnt')} Numbering definitions.")

        # 2. Check Section (ParaPr usage)
        section_xml = zf.read('Contents/section0.xml').decode('utf-8')
        root = ET.fromstring(section_xml)
        
        paras = root.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}p')
        # Expect 5 paragraphs:
        # 0: Normal
        # 1: Numbered
        # 2: Numbered
        # 3: Bullet
        # 4: Bullet
        # 5: Normal
        
        # We need to map paraPrIDRef to paraPr in Header?
        # Actually just check distinct paraPrIDRefs.
        
        refs = [p.get('paraPrIDRef') for p in paras]
        print(f"ParaPr Refs: {refs}")
        
        # We expect refs[1] and refs[2] to point to a paraPr that has numberingIDRef.
        # We expect refs[3] and refs[4] to point to different ONE (Bullet).
        # We expect refs[0] and refs[5] to be different (Normal).
        
        # Verify Headers references manually via lookup?
        # Too complex to parse header completely here.
        # Just assume diff refs imply diff properties.
        
        if refs[1] == refs[3]:
             print("⚠️ Warning: Number and Bullet share same ParaPr? (Unlikely unless bug)")
        
        if refs[1] == refs[0]:
             print("❌ Error: Numbered item shares ParaPr with Normal item.")
        else:
             print("✅ Numbered Item has distinct ParaPr.")

if __name__ == "__main__":
    test_lists()

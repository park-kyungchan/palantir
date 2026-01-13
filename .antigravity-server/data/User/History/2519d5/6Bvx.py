"""
Verify Styles (Align, Font Size, Bold)
"""
import os
import sys
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, SetAlign, SetFontSize, SetFontBold

def test_styles():
    actions = [
        # Para 1: Center Align, Default Font
        SetAlign(align_type="Center"),
        InsertText(text="Centered Text"),
        
        # Para 2: Left Align, 20pt, Bold
        SetAlign(align_type="Left"),
        SetFontSize(size=20),
        SetFontBold(is_bold=True),
        InsertText(text="Big Bold Text")
    ]
    
    builder = HwpxDocumentBuilder()
    output_path = "output_styles_test.hwpx"
    try:
        builder.build(actions, output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Build failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Verify Logic
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(output_path, 'r') as zf:
        header_xml = zf.read('Contents/header.xml').decode('utf-8')
        section_xml = zf.read('Contents/section0.xml').decode('utf-8')
        
        # Parse XML
        header_root = ET.fromstring(header_xml)
        ns = {'hh': 'http://www.hancom.co.kr/hwpml/2011/head', 
              'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph'}
        
        # Check ParaPr for Center Align
        # We expect a paraPr with align="CENTER"
        para_props = header_root.findall('.//hh:paraPr', ns)
        center_id = None
        for pp in para_props:
            align = pp.find('hh:align', ns)
            if align is not None and align.get('horizontal') == 'CENTER':
                center_id = pp.get('id')
                print(f"✅ Found ParaPr with CENTER align (ID={center_id})")
                break
        
        if not center_id:
            print("❌ ParaPr with CENTER align NOT found")
            
        # Check CharPr for 20pt Bold
        # 20pt -> height="2000", bold="1"
        char_props = header_root.findall('.//hh:charPr', ns)
        big_bold_id = None
        for cp in char_props:
            if cp.get('height') == '2000':
                bold = cp.find('hh:bold', ns)
                if bold is not None and bold.get('value') == '1':
                    big_bold_id = cp.get('id')
                    print(f"✅ Found CharPr with 20pt Bold (ID={big_bold_id})")
                    break
        
        if not big_bold_id:
            print("❌ CharPr with 20pt Bold NOT found")
            
        # Verify Usage in Section
        if center_id and f'paraPrIDRef="{center_id}"' in section_xml:
            print("✅ Section uses Center ParaPr")
        else:
            print("❌ Section does NOT use Center ParaPr")
            
        if big_bold_id and f'charPrIDRef="{big_bold_id}"' in section_xml:
            print("✅ Section uses Big Bold CharPr")
        else:
            print("❌ Section does NOT use Big Bold CharPr")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_styles()
    else:
        print("Skipping - No Skeleton.hwpx")

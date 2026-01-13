"""
Verify Page Setup (Orientation, Margins)
"""
import os
import zipfile
import xml.etree.ElementTree as ET
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, SetPageSetup

def test_page_setup():
    builder = HwpxDocumentBuilder()
    
    actions = [
        # Set Landscape, Left Margin 30mm
        SetPageSetup(
            orientation="Landscape",
            paper_size="A4",
            left=30,
            right=10,
            top=10,
            bottom=10,
            header=0,
            footer=0,
            gutter=0
        ),
        InsertText(text="This is a Landscape Page")
    ]
    
    output_path = "output_pagesetup_test.hwpx"
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
        
        # Parse (rough)
        root = ET.fromstring(section_xml)
        
        # Look for pagePr
        page_pr = None
        for elem in root.iter():
            if 'pagePr' in elem.tag:
                page_pr = elem
                break
        
        if not page_pr:
            print("❌ pagePr NOT found")
            return

        print("=== pagePr Attributes ===")
        print(page_pr.attrib)
        
        width = int(page_pr.get('width', '0'))
        height = int(page_pr.get('height', '0'))
        
        # Verify Landscape (Width > Height)
        if width > height:
            print(f"✅ Orientation is LANDSCAPE (W={width} > H={height})")
        else:
            print(f"❌ Orientation check FAILED (W={width}, H={height})")
            
        # Verify Margin
        margin_tag = None
        for child in page_pr:
             if 'margin' in child.tag:
                  margin_tag = child
                  break
        
        if margin_tag:
             left_u = int(margin_tag.get('left', '0'))
             # Expected: 30 * 283.465 ≈ 8503.95
             print(f"Left Margin: {left_u}")
             if 8500 <= left_u <= 8510:
                  print("✅ Left Margin is approx 30mm")
             else:
                  print(f"❌ Left Margin Mismatch (Expected ~8504)")
        else:
             print("❌ Margin tag not found")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_page_setup()
    else:
        print("Skipping - No Skeleton.hwpx")

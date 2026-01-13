"""
Verify TextBox Insertion
Tests InsertTextBox action (hp:rect) with both inline and floating positioning.
"""
import os
import sys
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertTextBox

def test_textbox_insertion():
    # Action 1: Inline TextBox
    action1 = InsertTextBox(text="Inline Box", width=50, height=20)
    
    # Action 2: Floating TextBox at (100mm, 100mm)
    action2 = InsertTextBox(text="Floating Box", width=50, height=20, x=100, y=100)
    
    # Build
    builder = HwpxDocumentBuilder()
    output_path = "output_textbox_test.hwpx"
    try:
        builder.build([action1, action2], output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Build failed: {e}")
        return

    # Verify Logic
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(output_path, 'r') as zf:
        sec_xml = zf.read('Contents/section0.xml').decode('utf-8')
        
        # Check hp:rect existence
        if 'hp:rect' in sec_xml or 'ns1:rect' in sec_xml: # Namespace aware check
             print("✅ hp:rect found")
        else:
             print("❌ hp:rect NOT found")
             
        # Check text content inside
        if "Inline Box" in sec_xml and "Floating Box" in sec_xml:
             print("✅ Text content found")
        else:
             print("❌ Text content missing")
             
        # Check hp:subList
        if 'hp:subList' in sec_xml or 'ns1:subList' in sec_xml:
             print("✅ hp:subList found (Text Container)")
        else:
             print("❌ hp:subList NOT found")
             
        # Check Positioning logic (simple string check)
        # Action 2 is floating -> treatAsChar="0", vertRelTo="PAPER"
        if 'treatAsChar="0"' in sec_xml and 'vertRelTo="PAPER"' in sec_xml:
             print("✅ Floating positioning attributes found")
        else:
             print("❌ Floating positioning attributes missing")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_textbox_insertion()
    else:
        print("Skipping - No Skeleton.hwpx")

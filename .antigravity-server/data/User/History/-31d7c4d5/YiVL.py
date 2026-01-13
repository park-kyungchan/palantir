"""
Verify Equation Insertion
Tests InsertEquation action and OWPML generation.
"""
import os
import sys
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertEquation

def test_equation_insertion():
    # LaTeX script
    latex = r"\sum_{i=0}^{\infty} \frac{1}{x_i}"
    # Expected HWP script: SUM_{i=0}^{inf} {1} OVER {x_i}
    
    action = InsertEquation(script=latex)
    
    builder = HwpxDocumentBuilder()
    output_path = "output_equation_test.hwpx"
    try:
        builder.build([action], output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Build failed: {e}")
        return

    # Verify Logic
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(output_path, 'r') as zf:
        sec_xml = zf.read('Contents/section0.xml').decode('utf-8')
        
        # Check hp:eqEdit
        if 'hp:eqEdit' in sec_xml or 'ns1:eqEdit' in sec_xml:
             print("✅ hp:eqEdit found")
        else:
             print("❌ hp:eqEdit NOT found")
             
        # Check Script Content
        expected_script = "SUM_{i=0}^{inf} {1} OVER {x_i}"
        
        # XML escaping might happen (<, >, &). HWP script usually clean.
        # But ElementTree escapes.
        if expected_script in sec_xml:
             print(f"✅ Script content match: '{expected_script}'")
        else:
             print(f"❌ Script content mismatch")
             print(f"Expected: {expected_script}")
             # Print snippet
             start = sec_xml.find("script")
             if start != -1:
                 print(f"Actual: {sec_xml[start:start+100]}")
                 
        # Check linesegarray ABSENCE
        if 'linesegarray' in sec_xml.lower():
             print("❌ linesegarray found (Should be removed)")
        else:
             print("✅ linesegarray REMOVED (Correct)")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_equation_insertion()
    else:
        print("Skipping - No Skeleton.hwpx")

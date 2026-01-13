import zipfile
import xml.etree.ElementTree as ET
import sys

SKELETON_PATH = "Skeleton.hwpx"

def inspect_section_properties():
    try:
        with zipfile.ZipFile(SKELETON_PATH, 'r') as zf:
            xml_content = zf.read('Contents/section0.xml').decode('utf-8')
            
            root = ET.fromstring(xml_content)
            
            # Namespace map (based on previous files)
            ns = {
                'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
                'hs': 'http://www.hancom.co.kr/hwpml/2011/section' 
                # Note: secPr might use hs or hp? Usually <hp:secPr> in run, or <hs:secPr> if standalone?
                # Check models.py line 38: HS_NS = 'http://www.hancom.co.kr/hwpml/2011/section'
                # Check document_builder.py line 175: _first_run.find(_hp('secPr'))
                # So it uses HP_NS? Or maybe HS? I'll print all tags.
            }

            # Find secPr
            # It's usually inside <hp:p><hp:run>...
            sec_pr = root.find('.//hp:secPr', ns)
            if sec_pr is None:
                # Try finding ANY secPr ignoring NS
                for elem in root.iter():
                    if 'secPr' in elem.tag:
                        sec_pr = elem
                        print(f"Found secPr: {elem.tag}")
                        break
            
            if sec_pr:
                print("\n=== secPr Content ===")
                # Dump XML roughly
                ET.indent(sec_pr)
                print(ET.tostring(sec_pr, encoding='unicode'))
            else:
                print("❌ <hp:secPr> NOT found in section0.xml")
                print("Root children:", [c.tag for c in root])

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_section_properties()

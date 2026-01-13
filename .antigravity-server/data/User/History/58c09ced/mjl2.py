import zipfile
import xml.etree.ElementTree as ET

SKELETON_PATH = "Skeleton.hwpx"

def inspect_border_fills():
    try:
        with zipfile.ZipFile(SKELETON_PATH, 'r') as zf:
            xml_content = zf.read('Contents/header.xml').decode('utf-8')
            
            root = ET.fromstring(xml_content)
            
            ns = {'hh': 'http://www.hancom.co.kr/hwpml/2011/head'}
            
            border_fills = root.findall('.//hh:borderFill', ns)
            
            print(f"Found {len(border_fills)} borderFill elements.")
            
            for bf in border_fills:
                print("\n=== borderFill ===")
                ET.indent(bf)
                print(ET.tostring(bf, encoding='unicode'))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_border_fills()

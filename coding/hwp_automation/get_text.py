
import zipfile
import xml.etree.ElementTree as ET
import os

def extract_text_from_hwpx(path: str) -> str:
    """
    Extracts plain text from HWPX (OWPML) file.
    Assumes standard structure: Contents/section0.xml
    """
    if not os.path.exists(path):
        return "Error: File not found."

    text_content = []
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            # List all section files
            section_files = [f for f in zf.namelist() if f.startswith('Contents/section')]
            section_files.sort() # Ensure order
            
            for sec_file in section_files:
                with zf.open(sec_file) as f:
                    tree = ET.parse(f)
                    root = tree.getroot()
                    # Namespaces usually: http://www.hancom.co.kr/hwpml/2011/section
                    # But we can just search for text tags 'hp:t'
                    # Or simpler: find all 't' tags if we ignore namespaces or handle them
                    # Let's iterate all elements
                    for elem in root.iter():
                        if elem.tag.endswith('t'): # <hp:t> contains text
                            if elem.text:
                                text_content.append(elem.text)
                        if elem.tag.endswith('p'): # <hp:p> paragraph, add newline
                            text_content.append("\n")
                            
    except Exception as e:
        return f"Error parsing HWPX: {e}"
        
    return "".join(text_content).strip()

if __name__ == "__main__":
    target = "/home/palantir/hwpx/20251228.hwpx"
    print(f"Extracting from: {target}")
    content = extract_text_from_hwpx(target)
    print("--- Extracted Content ---")
    print(content[:500] + "..." if len(content) > 500 else content)
    
    # Save for reconstruction script to use
    with open("source_text.txt", "w", encoding="utf-8") as f:
        f.write(content)

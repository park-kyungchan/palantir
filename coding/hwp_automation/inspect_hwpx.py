
import zipfile
import re
import sys

def inspect(path):
    print(f"Inspecting {path}...")
    with zipfile.ZipFile(path, 'r') as z:
        xml = z.read('Contents/section0.xml').decode('utf-8')
        
    print(f"XML Length: {len(xml)}")
    
    # 1. Find all tags
    tags = re.findall(r'<([a-zA-Z0-9_:]+)', xml)
    from collections import Counter
    print("Tag Counts:", Counter(tags))
    
    # 2. Find anything resembling 'eqn' or 'ctrl'
    ctrls = re.findall(r'<hp:ctrl>.*?</hp:ctrl>', xml, re.DOTALL)
    print(f"Controls Found: {len(ctrls)}")
    for i, c in enumerate(ctrls):
        print(f"  Ctrl {i}: {c[:100]}...")

    # 3. Check for equation props
    eq_props = re.findall(r'<hp:equationLine[^>]*>', xml)
    print(f"EquationLines found: {len(eq_props)}")

if __name__ == "__main__":
    inspect("sample_reconstructed_verified.hwpx")

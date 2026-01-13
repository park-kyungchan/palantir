from lib.models import *
from lib.owpml.generator import HWPGenerator
import zipfile

def test_owpml_generation():
    actions = [
        SetParaShape(left_margin=20, indent=-20, line_spacing=180),
        InsertText(text="First Indented Line"),
        InsertText(text="Second Indented Line"),
        SetParaShape(left_margin=0, indent=0, line_spacing=160),
        InsertText(text="Normal Line")
    ]
    
    gen = HWPGenerator()
    gen.generate(actions, "test_output.hwpx")
    
    # Verify Zip Content
    with zipfile.ZipFile("test_output.hwpx", 'r') as z:
        print("\n[Zip Contents]")
        for info in z.infolist():
            print(f"- {info.filename} ({info.file_size} bytes)")
            
        print("\n[Header.xml]")
        print(z.read("Contents/header.xml").decode('utf-8'))
        
        print("\n[Section0.xml]")
        print(z.read("Contents/section0.xml").decode('utf-8'))

if __name__ == "__main__":
    test_owpml_generation()

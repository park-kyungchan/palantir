import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.compiler import Compiler
from lib.ir import Document, Section, Paragraph, TextRun

def test_compiler_integration():
    print("--- Testing Compiler + Knowledge Base Integration ---")
    
    # 1. Initialize Compiler (Should load ActionDB)
    compiler = Compiler(action_db_path="lib/knowledge/hwpx/action_db.json", strict_mode=True)
    
    if compiler.action_db:
        print(f"✅ Compiler loaded ActionDB with {len(compiler.action_db.actions)} actions.")
    else:
        print("❌ Compiler FAILED to load ActionDB.")
        return

    # 2. Compile a simple document
    doc = Document()
    sec = Section()
    para = Paragraph()
    para.elements.append(TextRun(text="Hello Knowledge Base!"))
    sec.elements.append(para)
    doc.sections.append(sec)
    
    actions = compiler.compile(doc)
    print(f"✅ Compiled {len(actions)} actions.")
    print("Sample Action:", actions[0])

if __name__ == "__main__":
    test_compiler_integration()

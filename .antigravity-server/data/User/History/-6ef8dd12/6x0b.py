
import os
import sys
import json
from lib.digital_twin.schema import Document, Section, Paragraph, TextRun
from lib.compiler import Compiler
from lib.models import SetParaShape, CreateTable, SetCellBorder, HwpAction

def verify_compilation():
    """
    Test compilation of Semantic Styles (ProblemBox, AnswerBox).
    """
    print("MATCH_VERIFY: Starting Compilation Verification")
    
    # 1. Create Mock Document
    doc = Document()
    section = doc.add_section()
    
    # 1.1 Header
    header = Paragraph(style="Header")
    header.add_run(TextRun(text="Compilation Test"))
    section.elements.append(header)
    
    # 1.2 ProblemBox
    problem = Paragraph(style="ProblemBox")
    problem.add_run(TextRun(text="1. Solve the equation."))
    section.elements.append(problem)
    
    # 1.3 AnswerBox
    answer = Paragraph(style="AnswerBox")
    answer.add_run(TextRun(text="x = 42"))
    section.elements.append(answer)
    
    # 2. Compile
    compiler = Compiler(strict_mode=False) # Skip DB for test
    actions = compiler.compile(doc)
    
    # 3. Verify Actions
    action_types = [a['action_type'] for a in actions]
    print(f"DEBUG: Actions Generated: {action_types}")
    
    # Check Header
    assert "SetFontBold" in action_types, "Header missing Bold"
    assert "SetFontSize" in action_types, "Header missing Size"
    
    # Check ProblemBox (SetParaShape)
    found_para_shape = False
    for a in actions:
        if a['action_type'] == "SetParaShape":
            found_para_shape = True
            print(f"DEBUG: SetParaShape indent={a.get('indent')}")
            if a.get('indent') == -20:
                print("SUCCESS: Hanging Indent Detected")
    assert found_para_shape, "ProblemBox missing SetParaShape"

    # Check AnswerBox (Table)
    assert "CreateTable" in action_types, "AnswerBox missing CreateTable"
    found_border = any(a['action_type'] == "SetCellBorder" for a in actions)
    assert found_border, "AnswerBox missing Border"
    
    print("SUCCESS: All Semantic Compilation Checks Passed.")

if __name__ == "__main__":
    verify_compilation()

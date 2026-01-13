
import os
import sys
import json
from lib.builder import Builder
from lib.models import InsertText, SetParaShape, CreateTable

def main():
    """
    Verify Builder by manually feeding it Actions and checking generated code.
    """
    print("Verifying Builder...")
    
    actions = [
        SetParaShape(indent=-20, left_margin=20),
        InsertText(text="Problem 1."),
        SetParaShape(indent=0, left_margin=0), # Reset
        InsertText(text="\nAnswer Box Below:"),
        CreateTable(rows=1, cols=1),
    ]
    
    output_py = "test_reconstruct.py"
    
    builder = Builder()
    builder.build(actions, output_py)
    
    if os.path.exists(output_py):
        print(f"Success: {output_py} created.")
        with open(output_py, 'r') as f:
            content = f.read()
            print("--- Generated Code Preview ---")
            print(content[:500])
            print("...")
            
        # Check for critical snippets
        if "hwp.HAction.Execute('ParagraphShape'" in content:
            print("CHECK: SetParaShape logic found.")
        else:
            print("FAIL: SetParaShape logic missing.")
            
        if "hwp.HParameterSet.HTableCreation.Rows = 1" in content:
             print("CHECK: CreateTable logic found.")
        else:
             print("FAIL: CreateTable logic missing.")
             
    else:
        print("FAIL: File not created.")
        sys.exit(1)

if __name__ == "__main__":
    main()


import sys
import json
import os
from lib.models import InsertText, CreateTable, FileSaveAs
from core_bridge import WSLBridge

def main():
    # 1. Define the Sequence of Actions (The Plan)
    actions = [
        InsertText(text="Hello from ODA-Compliant Antigravity! (Linux -> Windows)\n"),
        InsertText(text="This text was defined as a Pydantic object on Ubuntu.\n\n"),
        CreateTable(rows=3, cols=3),
        InsertText(text="Table Created via Object Definition."),
    ]
    
    # 2. Serialize the Plan
    payload_path = os.path.abspath("action_request.json")
    payload_data = [action.model_dump() for action in actions]
    
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
        
    print(f"[Linux] Generated Payload at: {payload_path}")
    
    # 3. Transport and Execute
    bridge = WSLBridge()
    script_path = os.path.abspath("executor_win.py")
    
    print("[Linux] Sending to Windows Executor...")
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        print("[Linux] Success! Actions executed on Windows.")
    else:
        print(f"[Linux] Failed. Return code: {return_code}")
        sys.exit(return_code)

if __name__ == "__main__":
    main()

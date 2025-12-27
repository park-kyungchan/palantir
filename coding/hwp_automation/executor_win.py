
import sys
import json
import os
import traceback

# Add the current directory to sys.path to ensure we can import local modules if needed
# But primarily we rely on installed packages
sys.path.append(os.getcwd())

try:
    from pyhwpx import Hwp
except ImportError:
    print("Error: pyhwpx not found. Please install it on Windows: pip install pyhwpx")
    sys.exit(1)

def execute_action(hwp, action_data):
    """
    Executes a single action based on its type.
    """
    action_type = action_data.get("action_type")
    print(f"[Executor] Received Action: {action_type}")
    
    if action_type == "InsertText":
        text = action_data.get("text", "")
        print(f"[Executor] Inserting text: {text}")
        hwp.insert_text(text)
        
    elif action_type == "CreateTable":
        rows = action_data.get("rows", 5)
        cols = action_data.get("cols", 5)
        print(f"[Executor] Creating table: {rows}x{cols}")
        hwp.create_table(rows, cols)
        
    elif action_type == "FileSaveAs":
        path = action_data.get("path")
        fmt = action_data.get("format", "HWP")
        print(f"[Executor] Saving to: {path} ({fmt})")
        hwp.save_as(path, format=fmt)

    # --- New Actions ---
    elif action_type == "InsertImage":
        path = action_data.get("path")
        w = action_data.get("width")
        h = action_data.get("height")
        treat_as_char = action_data.get("treat_as_char", True)
        print(f"[Executor] Inserting Image: {path} ({w}x{h})")
        # Simplified call to avoid signature mismatch. 
        # pyhwpx seems to differ from expected signature.
        try:
            hwp.insert_picture(path)
        except Exception as e:
            print(f"[Executor] Warning: insert_picture failed: {e}")
            # Fallback or retry?
            # For now, just log.
            pass
        
        # TODO: Implement resizing and 'treat_as_char' by accessing the Control (Ctrl) object
        # after insertion.
        # ctrl = hwp.HeadCtrl # or similar logic to find the just-inserted image

    elif action_type == "SetFontSize":
        size = action_data.get("size")
        print(f"[Executor] Setting Font Size: {size}")
        # HWP API uses internal logic: 1 pt = 100 HWP Units (approx? actually typical HWP automation uses pt directly in API or 100x).
        # Safe raw API approach:
        # Action: CharShape
        # Parameter: Height
        act = hwp.CreateAction("CharShape")
        pset = act.CreateSet()
        act.GetDefault(pset)
        # HWP Height is usually in HWPUNITs. 10 pt = 1000? 
        # Actually verify: HWP API 'Height' is often Points * 100.
        pset.SetItem("Height", int(size * 100))
        act.Execute(pset)

    elif action_type == "SetFontBold":
        is_bold = action_data.get("is_bold")
        print(f"[Executor] Setting Bold: {is_bold}")
        # Robust API Way
        act = hwp.CreateAction("CharShape")
        pset = act.CreateSet()
        act.GetDefault(pset)
        # Bold is a property in 'Bolt' or similar?
        # ParameterSetTable.txt says: Item ID 'Bold', Type PIT_UI1
        # 1 = Bold, 0 = Normal
        pset.SetItem("Bold", 1 if is_bold else 0)
        act.Execute(pset)

    elif action_type == "SetAlign":
        align = action_data.get("align_type")
        print(f"[Executor] Setting Align: {align}")
        # Map generic Align types to HWP specific logic if needed
        # pyhwpx might have hwp.set_linespacing etc.
        # hwp.ParaShape.Align = ...
        # Let's try basic command API access if pyhwpx wrapper isn't obvious, 
        # but pyhwpx typically has ParagraphShape helpers.
        # For now, simplistic approach:
        if align == "Center":
            hwp.HAction.Run("ParagraphShapeCenter")
        elif align == "Left":
            hwp.HAction.Run("ParagraphShapeLeft")
        elif align == "Right":
            hwp.HAction.Run("ParagraphShapeRight")
        if align == "Center":
            hwp.HAction.Run("ParagraphShapeCenter")
        elif align == "Left":
            hwp.HAction.Run("ParagraphShapeLeft")
        elif align == "Right":
            hwp.HAction.Run("ParagraphShapeRight")
        elif align == "Justify":
            hwp.HAction.Run("ParagraphShapeJustify")

    elif action_type == "Open":
        path = action_data.get("path")
        fmt = action_data.get("format", None)
        print(f"[Executor] Opening file: {path}")
        # pyhwpx open wrapper usually handles format detection
        hwp.open(path, format=fmt)

    elif action_type == "MultiColumn":
        count = action_data.get("count", 2)
        same_size = action_data.get("same_size", True)
        gap = action_data.get("gap", 3000)
        print(f"[Executor] Setting Multi-Column: {count} cols")
        
        # Action: MultiColumn (ColDef)
        act = hwp.CreateAction("MultiColumn")
        pset = act.CreateSet()
        act.GetDefault(pset)
        pset.SetItem("Count", count)
        pset.SetItem("SameSize", 1 if same_size else 0)
        pset.SetItem("SameGap", gap) # Gap is used when SameSize is 1
        act.Execute(pset)

    elif action_type == "MoveToField":
        field = action_data.get("field")
        text = action_data.get("text")
        print(f"[Executor] Moving to Field: {field}")
        
        # hwp.MoveToField returns True/False
        if hwp.MoveToField(field):
            if text is not None:
                print(f"[Executor] Putting Text into Field: {text}")
                hwp.PutFieldText(field, text)
        else:
            print(f"[Executor] Warning: Field '{field}' not found.")
            # We don't raise error to allow partial success in lists
            pass

    elif action_type == "SetLetterSpacing":
        spacing = action_data.get("spacing", 0)
        print(f"[Executor] Setting Letter Spacing: {spacing}%")
        # Action: CharShape
        act = hwp.CreateAction("CharShape")
        pset = act.CreateSet()
        act.GetDefault(pset)
        pset.SetItem("Spacing", spacing)
        act.Execute(pset)

    elif action_type == "SetLineSpacing":
        spacing = action_data.get("spacing", 160)
        print(f"[Executor] Setting Line Spacing: {spacing}%")
        # Action: ParagraphShape
        act = hwp.CreateAction("ParagraphShape")
        pset = act.CreateSet()
        act.GetDefault(pset)
        pset.SetItem("LineSpacing", spacing)
        act.Execute(pset)

        pset.SetItem("LineSpacing", spacing)
        act.Execute(pset)

    elif action_type == "InsertEquation":
        script = action_data.get("script", "")
        print(f"[Executor] Inserting Equation: {script}")
        # Action: EquationCreate
        act = hwp.CreateAction("EquationCreate")
        pset = act.CreateSet()
        act.GetDefault(pset)
        pset.SetItem("String", script) # HWP script (EQ). LaTeX might need conversion if HWP doesn't auto-detect.
        # Check if HWP 2024 supports native LaTeX. Often it does via "EquationCreate" but needs correct property.
        # For now, we inject the script string.
        # Usually HWP EQ format (e.g. "sqrt {a^2 + b^2}")
        pset.SetItem("BaseUnit", 100) # Optional sizing
        act.Execute(pset)

    elif action_type == "SetPageSetup":
        left = action_data.get("left", 30)
        right = action_data.get("right", 30)
        top = action_data.get("top", 20)
        bottom = action_data.get("bottom", 15)
        header = action_data.get("header", 15)
        footer = action_data.get("footer", 15)
        gutter = action_data.get("gutter", 0)
        
        print(f"[Executor] Setting Page Margins (mm): L={left}, R={right}, T={top}, B={bottom}")
        
        # Action: PageSetup
        act = hwp.CreateAction("PageSetup")
        pset = act.CreateSet()
        act.GetDefault(pset)
        
        # Update Item: "PageDef"
        # Since PageDef is a Set, we might need to access the Item "PageDef" inside pset.
        # But commonly PageSetup pset HAS the properties directly for 'PageDef' or a child set.
        # Let's check typical usage.
        # Actually PageSetup Action's pset HAS "PageDef" item which IS a ParameterSet.
        
        pdef = pset.Item("PageDef")
        
        # Unit conversion: mm -> HWP Unit (LPer)
        # 1 mm = 283.465 LPer
        mm_to_lper = 283.465
        
        pdef.SetItem("LeftMargin", int(left * mm_to_lper))
        pdef.SetItem("RightMargin", int(right * mm_to_lper))
        pdef.SetItem("TopMargin", int(top * mm_to_lper))
        pdef.SetItem("BottomMargin", int(bottom * mm_to_lper))
        pdef.SetItem("HeaderLen", int(header * mm_to_lper))
        pdef.SetItem("FooterLen", int(footer * mm_to_lper))
        pdef.SetItem("GutterLen", int(gutter * mm_to_lper))
        
        act.Execute(pset)

    else:
        print(f"[Executor] Unknown action type: {action_type}")
        raise ValueError(f"Unknown Action: {action_type}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python executor_win.py <path_to_payload.json>")
        sys.exit(1)
        
    payload_path = sys.argv[1]
    print(f"[Executor] Reading payload from: {payload_path}")
    
    try:
        with open(payload_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Initialize HWP
        # register_module is crucial for security bypass
        print("[Executor] Initializing HWP...")
        hwp = Hwp(visible=True, register_module=True)
        
        # Determine if it's a list of actions or a single action
        if isinstance(data, list):
            for action in data:
                execute_action(hwp, action)
        else:
            execute_action(hwp, data)
            
        print("[Executor] Execution complete.")
        
    except Exception as e:
        print(f"[Executor] Critical Failure: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

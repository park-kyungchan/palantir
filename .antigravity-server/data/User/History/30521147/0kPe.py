import json
import argparse
import sys
from typing import List

# Add project root to sys.path
sys.path.append(".")

from lib.models import (
    HwpAction, InsertText, SetParaShape, CreateTable, 
    InsertEquation, InsertImage, SetFontSize, SetFontBold,
    SetAlign, SetCellBorder, MoveToCell, InsertCaption
)
from lib.owpml.generator import HWPGenerator

def deserialize_actions(json_data: List[dict]) -> List[HwpAction]:
    """
    Deserializes list of dicts into list of HwpAction objects.
    """
    actions = []
    # Map action_type string to Class
    # We can rely on Pydantic's discriminated union if we had it, 
    # but for now manual mapping or simplified lookup is safer given current models structure.
    
    # Actually, we can try to instantiate based on 'action_type' field.
    # Let's create a map of name -> class
    action_map = {
        "InsertText": InsertText,
        "SetParaShape": SetParaShape,
        "CreateTable": CreateTable,
        "InsertEquation": InsertEquation,
        "InsertImage": InsertImage,
        "SetFontSize": SetFontSize,
        "SetFontBold": SetFontBold,
        "SetAlign": SetAlign,
        "SetCellBorder": SetCellBorder,
        "MoveToCell": MoveToCell,
        "InsertCaption": InsertCaption
        # Add others if needed
    }

    for item in json_data:
        atype = item.get("action_type")
        if atype in action_map:
            # Pydantic parse
            try:
                obj = action_map[atype](**item)
                actions.append(obj)
            except Exception as e:
                print(f"Warning: Failed to parse {atype}: {e}")
        else:
            print(f"Warning: Unknown action type: {atype}")
            
    return actions

def main():
    parser = argparse.ArgumentParser(description="Generate HWPX from Actions JSON")
    parser.add_argument("input_json", help="Path to input JSON file")
    parser.add_argument("output_hwpx", help="Path to output HWPX file")
    
    args = parser.parse_args()
    
    print(f"Reading {args.input_json}...")
    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"Deserializing {len(data)} actions...")
    actions = deserialize_actions(data)
    print(f"Loaded {len(actions)} valid HwpActions.")
    
    gen = HWPGenerator()
    gen.generate(actions, args.output_hwpx)
    print("Done.")

if __name__ == "__main__":
    main()

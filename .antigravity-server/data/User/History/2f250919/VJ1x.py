import json
import os
from lib.digital_twin.schema import (
    DigitalTwin, Section, Table, TableRow, Cell, Run, Style, Paragraph
)
from lib.compiler import Compiler

def load_simulated_twin(path: str) -> DigitalTwin:
    """
    Converts the 'Vision-Simulated' JSON into strict DigitalTwin Schema.
    """
    with open(path, "r") as f:
        data = json.load(f)
    
    twin = DigitalTwin(document_id="sample_pilot")
    section = Section()
    
    for page in data.get("pages", []):
        print(f"Propcessing page {page.get('page_num')}")
        for block in page.get("blocks", []):
            print(f"Checking block type: {block.get('type')}")
            if block["type"] == "Table":

                # Convert Table
                table_style = Style(**block.get("style", {}))
                hwp_table = Table(style=table_style)
                
                # Assume cells are flat list in JSON? Or organized?
                # In sample_twin.json: "cells": [ {row:0, col:0 ...}, ... ]
                
                # We need to structure them into rows
                rows_map = {}
                for c_data in block.get("cells", []):
                    r_idx = c_data["row"]
                    c_idx = c_data["col"]
                    
                    if r_idx not in rows_map:
                        rows_map[r_idx] = {}
                    
                    # Convert Content to Paragraph -> Runs
                    runs = []
                    for content_item in c_data.get("content", []):
                        run_style = Style(**content_item.get("style", {}))
                        runs.append(Run(
                            type=content_item["type"], # Text or Equation
                            text=content_item.get("text"),
                            script=content_item.get("script"),
                            style=run_style
                        ))
                    
                    # Create Cell (wrap runs in a paragraph for now)
                    # Note: Cell model expects 'paragraphs', or 'content' alias
                    cell = Cell(row=r_idx, col=c_idx, content=runs)
                    rows_map[r_idx][c_idx] = cell
                
                # Build Rows List (sorted)
                max_row = max(rows_map.keys()) if rows_map else -1
                for r in range(max_row + 1):
                    row_cells = []
                    row_data = rows_map.get(r, {})
                    max_col = max(row_data.keys()) if row_data else -1
                    
                    # Ensure sparse cells are filled? 
                    # For pilot, assume well-formed or simple fill.
                    for c in range(max_col + 1):
                        if c in row_data:
                            row_cells.append(row_data[c])
                        else:
                            row_cells.append(Cell(row=r, col=c, content=[]))
                            
                    hwp_table.rows.append(TableRow(cells=row_cells))
                
                section.elements.append(hwp_table)

    twin.sections.append(section)
    return twin

def run_pilot():
    json_path = "temp_vision/sample_twin.json"
    output_path = "sample_reconstructed.hwpx"
    
    print(f"🚀 Loading {json_path}...")
    twin = load_simulated_twin(json_path)
    
    print("🔧 Initializing Compiler...")
    compiler = Compiler()
    
    print("⚙️ Compiling...")
    actions = compiler.compile(twin) # Returns actions list. Also saves if output_path provided to compile method?
    # Checking compiler.compile signature -> (doc, output_path=None)
    
    # We want to actually SAVE.
    # Compiler implementation in previous steps showed:
    # if output_path: actions.append(FileSaveAs...)
    # But it doesn't execute them! It just returns models.
    # We need an Executor to run them?
    # Or does Compiler just generate the list?
    
    # Wait, the task is "Digital Twin -> HWPX".
    # Usually we need a 'Renderer' or 'Executor' that talks to HWP.
    # But the current architecture (Compiler) generates 'HwpActions'.
    # To 'Verify', we need to check the GENERATED ACTIONS.
    # Saving to .hwpx directly implies we have a writer.
    # We assume 'FileSaveAs' action is sufficient if we were running against the Engine.
    # Since we are in Linux, we can't run the Engine.
    # So we will output the 'Actions JSON' as the artifact.
    
    with open("sample_actions.json", "w") as f:
        json.dump([a.model_dump() for a in actions], f, indent=2, ensure_ascii=False)
        
    print(f"✅ Compilation Complete. Generated {len(actions)} Actions.")
    print(f"💾 Saved Action Trace to 'sample_actions.json'")

if __name__ == "__main__":
    run_pilot()

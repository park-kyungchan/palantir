import subprocess
import re
from typing import List
from lib.digital_twin.schema import DigitalTwin, Page, Block, Content, GlobalSettings

class LayoutTextIngestor:
    """
    Ingests ActionTable using `pdftotext -layout`.
    Handles fixed-width columnar data with multi-line rows.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def process(self) -> DigitalTwin:
        # Get raw text layout
        # -f 2: Start from page 2 (Skip cover)
        cmd = ["pdftotext", "-layout", "-f", "2", self.pdf_path, "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        full_text = result.stdout
        
        pages = []
        # Split by Form Feed (Page Break)
        raw_pages = full_text.split('\f')
        
        for i, raw_page in enumerate(raw_pages):
            if not raw_page.strip():
                continue
                
            page_num = i + 2 # Started from 2
            blocks = self._parse_page_text(raw_page, page_num)
            pages.append(Page(page_num=page_num, blocks=blocks))

        return DigitalTwin(
            document_id="ActionTable_2504_Parsed",
            global_settings=GlobalSettings(),
            pages=pages
        )

    def _parse_page_text(self, text: str, page_num: int) -> List[Block]:
        blocks = []
        lines = text.split('\n')
        
        # Column Offsets (Approximate based on visualization)
        # Action ID: 0-24
        # ParameterSet: 24-44
        # Description: 44+
        
        table_data = [] # List[List[str]]
        headers = ["Action ID", "ParameterSet ID", "Description"]
        table_data.append(headers)
        
        current_row = None
        
        for line in lines:
            if not line.strip():
                continue
            if "Action ID" in line and "Description" in line:
                continue # Skip header repetition
            if line.strip() == str(page_num):
                continue # Skip page number footer
                
            # Parse Columns
            col1 = line[:24].strip()
            col2 = line[24:44].strip()
            col3 = line[44:].strip()
            
            # Logic: New Action ID implies New Row
            # If col1 is empty but col2/col3 has content -> Continuation of previous row?
            # Actually, looking at 'AQcommandMerge':
            # Line 1: AQcommandMerge | UserQCommandFile* | 입력 자동...
            # Line 2:                |                   | (글메뉴의...)
            # Line 3:                |                   | [입력...]
            #
            # So if Col1 is present -> New Entry.
            # If Col1 empty -> Append Col3 to previous description.
            
            # Heuristic Filtering for "Code" or "Garbage" lines
            # Valid Action ID chars: A-Z, a-z, 0-9, _, 1~16 range
            # Valid Param ID chars: A-Z, a-z, 0-9, *, +, -
            
            is_valid_row = True
            
            # Check Col1 (ActionID)
            if col1:
                # Discard if it looks like code (contains = ; ( ) . or 'var ')
                if any(c in col1 for c in "=;().") or "var " in col1:
                    is_valid_row = False
                    
            # Check Col2 (ParamID) validation is tricky because short IDs exist.
            # But if Col1 was valid, we trust it mostly.
            # If Col1 is empty, we act carefully.

            if col1 and is_valid_row:
                # Flush previous
                if current_row:
                    table_data.append(current_row)
                
                # New Row
                current_row = [col1, col2, col3]
            else:
                # Continuation or Code Line
                if current_row:
                   # If it looks like code, treat entire line as description
                   if any(c in line for c in "=;().") or "pHwp" in line:
                       current_row[2] += "\n" + line.strip()
                   else:
                       # Standard continuation
                       # Only append col2 to ID if it looks like an ID part (rare)
                       # AND doesn't look like code/garbage
                       if col2 and len(col2) < 20 and not any(c in col2 for c in "=;()."):
                           current_row[1] += " " + col2
                       
                       # Append description
                       if col3:
                           current_row[2] += " " + col3
        
        # Flush last
        if current_row:
            table_data.append(current_row)
            
        if len(table_data) > 1:
            blocks.append(Block(
                id=f"p{page_num}_table",
                type="table",
                role="body",
                content=Content(table_data=table_data)
            ))
            
        return blocks

if __name__ == "__main__":
    ingestor = LayoutTextIngestor("ActionTable_2504.pdf")
    twin = ingestor.process()
    print(f"Processed {len(twin.pages)} pages.")
    
    # Save to JSON
    import json
    with open("temp_vision_batch/full_doc_twin_parsed.json", "w") as f:
        f.write(twin.model_dump_json(indent=2))
        
    print("Saved to temp_vision_batch/full_doc_twin_parsed.json")

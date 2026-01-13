import subprocess
import re
from typing import List, Dict, Optional
from lib.knowledge.schema import ParameterSetDefinition, ParameterItem

class LayoutParameterIngestor:
    """
    Ingests ParameterSetTable using `pdftotext -layout`.
    Structure:
    1) SetID : Description
        ItemID  Type  SubType  Description
        ...
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def process(self) -> List[ParameterSetDefinition]:
        cmd = ["pdftotext", "-layout", self.pdf_path, "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        full_text = result.stdout
        
        # Strategy:
        # 1. Regex to find Section Headers: `^ *(\d+)\) *(\w+) *:(.*)`
        # 2. Everything between headers is body.
        # 3. Parse body as table (Item ID, Type, SubType, Description).
        
        definitions = []
        
        # Split text into lines
        lines = full_text.split('\n')
        
        current_set: Optional[ParameterSetDefinition] = None
        current_items = []
        
        # Reuse 'Row' logic from ActionTable for multi-line description
        # Columns roughly: 
        # Item ID: 5-25
        # Type: 25-40
        # SubType: 40-55
        # Description: 55+
        
        header_pattern = re.compile(r"^\s*\d+\)\s+(\w+)\s*:(.*)")
        
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for New Section
            match = header_pattern.match(line)
            if match:
                # Save previous
                if current_set:
                    current_set.items = current_items
                    definitions.append(current_set)
                
                # Start new
                set_id = match.group(1).strip()
                desc = match.group(2).strip()
                current_set = ParameterSetDefinition(set_id=set_id, description=desc)
                current_items = []
                continue
            
            # Parse Body (if inside section)
            if current_set:
                if "Item ID" in line and "Description" in line:
                    continue # Skip Table Header
                
                # Heuristic layout parsing
                # Adjust indices based on visual inspection of 'InsertText' output
                # Output snippet showed:
                #      Text             PIT_BSTR             삽입할 텍스트
                # "     Text" starts around index 5.
                
                if len(line) < 10:
                    continue
                    
                
                col1 = line[:19].strip() # Item ID
                col2 = line[19:40].strip() # Type
                # col3 = line[35:45].strip() # SubType (Optional, skip for now)
                col4 = line[40:].strip() # Description
                
                if col1:
                    # New Item
                    item = ParameterItem(
                        item_id=col1,
                        type=col2,
                        description=col4
                    )
                    current_items.append(item)
                else:
                    # Continuation of description
                    if current_items and col4:
                        current_items[-1].description = (current_items[-1].description or "") + " " + col4

        # Save last
        if current_set:
            current_set.items = current_items
            definitions.append(current_set)
            
        return definitions

if __name__ == "__main__":
    ingestor = LayoutParameterIngestor("ParameterSetTable_2504.pdf")
    sets = ingestor.process()
    print(f"Extracted {len(sets)} Parameter Sets.")
    
    # Find InsertText
    for s in sets:
        if s.set_id == "InsertText":
            print(f"Found InsertText: {s.description}")
            for item in s.items:
                print(f" - {item.item_id} ({item.type}): {item.description}")

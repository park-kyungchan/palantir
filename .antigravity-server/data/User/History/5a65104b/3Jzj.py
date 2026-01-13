
import os
import re

TARGET_FILE = "lib/owpml/document_builder.py"

NEW_METHODS = """
    def _move_to_cell(self, action: MoveToCell):
        \"\"\"Move cursor context to specific cell in current table.\"\"\"
        if self._current_table is None:
            print("[HwpxDocumentBuilder] Warning: No active table for MoveToCell")
            return

        target_row = action.row
        target_col = action.col
        
        # Find tr
        rows = self._current_table.findall(f'.//{{http://www.hancom.co.kr/hwpml/2011/paragraph}}tr')
        if not rows or target_row >= len(rows):
            print(f"[HwpxDocumentBuilder] Error: Table has {len(rows)} rows, target {target_row}")
            return
            
        tr = rows[target_row]
        
        # Find tc
        cols = tr.findall(f'.//{{http://www.hancom.co.kr/hwpml/2011/paragraph}}tc')
        if not cols or target_col >= len(cols):
            print(f"[HwpxDocumentBuilder] Error: Row {target_row} has {len(cols)} cols, target {target_col}")
            return
            
        tc = cols[target_col]
        
        self._current_cell = tc
        self._current_container = tc
        
        # Ensure Cell has at least one paragraph? 
        # _insert_text adds a paragraph. 
        # If we move to cell, we might want to append to EXISTING paragraph or create new?
        # Standard: _insert_text creates NEW paragraph.
        
    def _set_cell_border(self, action: SetCellBorder):
        \"\"\"Set border/fill for current cell.\"\"\"
        if self._current_cell is None:
            print("[HwpxDocumentBuilder] Warning: No active cell for SetCellBorder")
            return
            
        # Create BorderFill ID via HeaderManager
        bf_id = self.header_manager.get_or_create_border_fill(
            border_type=action.border_type,
            width=action.width,
            color=action.color,
            fill_color=action.fill_color
        )
        
        self._current_cell.set('borderFillIDRef', bf_id)
"""

def update_builder():
    with open(TARGET_FILE, 'r') as f:
        content = f.read()

    # 1. Update Imports
    if "MoveToCell" not in content:
        # Match the line with SetPageSetup
        pattern = r"(MergeCells, InsertImage, InsertTextBox, SetAlign, SetPageSetup)"
        replacement = r"MergeCells, InsertImage, InsertTextBox, SetAlign, SetPageSetup, MoveToCell, SetCellBorder"
        content = re.sub(pattern, replacement, content)
        print("Imports updated.")

    # 2. Update __init__ State
    if "self._current_table = None" not in content:
        # Before self.header_manager instantiation or after
        # Find "self._pending_column_break = False"
        pattern = r"(self\._pending_column_break = False)"
        replacement = r"\1\n        self._current_table = None\n        self._current_cell = None\n        self._current_container = None"
        content = re.sub(pattern, replacement, content)
        print("__init__ state updated.")

    # 3. Update _init_document (Container Reset)
    # Find "self._first_run = run"
    if "self._current_container = self.section_elem" not in content:
        pattern = r"(self\._first_run = run)"
        replacement = r"\1\n        self._current_container = self.section_elem"
        content = re.sub(pattern, replacement, content)
        print("_init_document updated.")

    # 4. Update _create_table (Update current_table)
    # Be precise. tbl creation ends with })
    # We look for a unique string inside _create_table
    if "self._current_table = tbl" not in content:
        # Find 'textFlow': 'BOTH_SIDES', and the closing brace lines later
        # Actually, simpler: find "borderFillIDRef': table_border_id # Dynamic visual border"
        # Then find closing "})"
        # This is risky with regex.
        # Let's search for "borderFillIDRef': table_border_id # Dynamic visual border"
        # and replace it with "borderFillIDRef': table_border_id # Dynamic visual border\n        })\n\n        self._current_table = tbl\n        self._current_cell = None\n        # Reset container to section (table is block level)\n        self._current_container = self.section_elem"
        # But we need to remove the existing "})"
        
        # Try to locate the exact block
        search_str = "'borderFillIDRef': table_border_id # Dynamic visual border"
        if search_str in content:
             # Look for the closing }) validly
             # It's usually on next line
             # We'll just insert after the specific line, assuming it is inside the dict
             # Wait, python dict constructor in SubElement calls ends with })
             # I'll search for the SubElement call block?
             pass
             # Let's try inserting *before* "4. Generate Rows and Cells" comment
             marker = "# 4. Generate Rows and Cells"
             if marker in content:
                  replacement = "self._current_table = tbl\n        self._current_cell = None\n        self._current_container = self.section_elem\n        \n        " + marker
                  content = content.replace(marker, replacement)
                  print("_create_table state update injected.")
    
    # 5. Update _insert_text (Context Aware)
    if "self._current_container" not in content:
        # Find "p = ET.SubElement("
        # Find "self.section_elem,"
        # Use simple replace: "ET.SubElement(self.section_elem," -> "ET.SubElement(self._current_container if self._current_container is not None else self.section_elem,"
        # Wait, ensure imports won't break?
        # self._current_container is defined in init.
        content = content.replace(
            "p = ET.SubElement(self.section_elem, _hp('p')", 
            "container = self._current_container if self._current_container is not None else self.section_elem\n        p = ET.SubElement(container, _hp('p')"
        )
        # Note: _hp('p') was inside the tuple.
        # Original: p = ET.SubElement(\n                self.section_elem,\n                _hp('p'),
        # My replace needs to match exact formatting.
        # Step 573 View showed:
        # p = ET.SubElement(
        #     self.section_elem,
        #     _hp('p'),
        # ...
        
        # Regex replacement needed for multiline
        pattern = r"p = ET\.SubElement\(\s*self\.section_elem,\s*_hp\('p'\),"
        replacement = r"container = self._current_container if self._current_container is not None else self.section_elem\n        p = ET.SubElement(\n            container,\n            _hp('p'),"
        content = re.sub(pattern, replacement, content)
        print("_insert_text updated to use container.")
        
    # 6. Add Handlers in _process_action
    if "isinstance(action, MoveToCell):" not in content:
        # Find "elif isinstance(action, SetAlign):"
        # Append ours
        pattern = r"(self\._current_align = action\.align_type\.upper\(\))"
        # Handler code
        handler = r"\1\n            \n        elif isinstance(action, MoveToCell):\n            self._move_to_cell(action)\n            \n        elif isinstance(action, SetCellBorder):\n            self._set_cell_border(action)"
        content = re.sub(pattern, handler, content)
        print("Handlers added to _process_action.")

    # 7. Append New Methods
    if "def _move_to_cell" not in content:
        with open(TARGET_FILE, 'a') as f:
            f.write(NEW_METHODS)
        print("New methods appended.")
    else:
        # If we modified content but didn't append (because methods existed? Unlikely if we are updating state)
        # We need to write content back if we did regex subs
        pass

    # Write back modified content (except appended part which handled itself... wait)
    # If I append, I should verify I write the 'content' string first? 
    # Logic: Read content, modify in memory.
    # Check if methods exist in 'content'.
    # If not, append to 'content'.
    # Then Write 'content' to file.
    
    if "def _move_to_cell" not in content:
         content += NEW_METHODS
         print("Appended methods to content.")
         
    with open(TARGET_FILE, 'w') as f:
        f.write(content)
    print("Updates saved.")

if __name__ == "__main__":
    update_builder()

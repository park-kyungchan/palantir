
import os

TARGET_FILE = "lib/owpml/document_builder.py"

NEW_INSERT_TEXT = """    def _insert_text(self, action: InsertText):
        \"\"\"Insert text paragraph(s) with dynamic styles.\"\"\"
        text = action.text
        
        # Prepare Style IDs
        indent = self.current_para_shape.indent if self.current_para_shape else 0
        spacing = self.current_para_shape.line_spacing if self.current_para_shape else 160
        
        para_id = self.header_manager.get_or_create_para_pr(
            align=self._current_align,
            indent=indent,
            line_spacing=spacing
        )
        
        char_id = self.header_manager.get_or_create_char_pr(
            font_size_pt=int(self._font_size),
            is_bold=self._is_bold,
            color=self._font_color
        )
        
        # Split by newlines
        lines = text.split('\\n')
        
        for line in lines:
            # Determine columnBreak attribute
            col_break = '1' if self._pending_column_break else '0'
            self._pending_column_break = False
            
            # Create paragraph element
            p = ET.SubElement(
                self.section_elem,
                _hp('p'),
                {
                    'id': str(self.para_counter),
                    'paraPrIDRef': para_id,
                    'styleIDRef': '0', # Default style
                    'pageBreak': '0',
                    'columnBreak': col_break,
                    'merged': '0'
                }
            )
            
            # Create run with text
            run = ET.SubElement(p, _hp('run'), {'charPrIDRef': char_id})
            
            # Add text
            t = ET.SubElement(run, _hp('t'))
            t.text = line.strip() if line.strip() else None
            
            self.para_counter += 1
"""

def fix_file():
    with open(TARGET_FILE, 'r') as f:
        lines = f.readlines()

    # 1. Identify Valid _insert_equation (First One) and Duplicate (Second One)
    def_indices = [i for i, line in enumerate(lines) if line.strip().startswith("def _insert_equation(self,")]
    
    if len(def_indices) > 1:
        print(f"Found {len(def_indices)} _insert_equation definitions at {def_indices}")
        # Keep the first one. Delete the second one.
        # Second one starts at def_indices[1].
        # It ends before `def _create_table` or EOF.
        start_del = def_indices[1]
        
        # Find end of this method. Scan for next `def` or end of file.
        end_del = len(lines)
        for i in range(start_del + 1, len(lines)):
            if lines[i].strip().startswith("def "):
                 end_del = i
                 break
        
        print(f"Deleting duplicate _insert_equation lines {start_del} to {end_del}")
        # Remove lines
        del lines[start_del:end_del]
    else:
        print("No duplicate _insert_equation found.")

    # 2. Replace _insert_text
    # Find _insert_text
    try:
        text_start = next(i for i, line in enumerate(lines) if line.strip().startswith("def _insert_text(self,"))
        
        # Find end of _insert_text
        text_end = len(lines)
        for i in range(text_start + 1, len(lines)):
            if lines[i].strip().startswith("def "):
                text_end = i
                break
        
        print(f"Replacing _insert_text lines {text_start} to {text_end}")
        
        # Remove old
        del lines[text_start:text_end]
        # Insert new
        lines.insert(text_start, NEW_INSERT_TEXT)
        
    except StopIteration:
        print("Could not find _insert_text to replace!")
        
    # Write back
    with open(TARGET_FILE, 'w') as f:
        f.writelines(lines)
    print("Fixed document_builder.py")

if __name__ == "__main__":
    fix_file()

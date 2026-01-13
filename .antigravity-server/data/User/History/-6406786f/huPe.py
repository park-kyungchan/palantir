
import os

TARGET_FILE = "lib/owpml/document_builder.py"

METHOD_CODE = """
    def _update_page_setup(self, action: SetPageSetup):
        \"\"\"
        Update Page Setup (secPr) for the first section.
        Handles Orientation, Margins, Dimensions.
        \"\"\"
        if self._first_run is None:
            print("[HwpxDocumentBuilder] Warning: No first run for Page Setup")
            return

        # Find secPr
        sec_pr = None
        for child in self._first_run:
            if 'secPr' in child.tag:
                sec_pr = child
                break
        
        if sec_pr is None:
             print("[HwpxDocumentBuilder] Warning: secPr not found in first run")
             return
            
        # Find pagePr
        page_pr = None
        for child in sec_pr:
            if 'pagePr' in child.tag:
                page_pr = child
                break
        
        if page_pr is None:
             return

        # Constants
        HWPUNIT_PER_MM = 283.465
        
        # Dimensions
        if action.paper_size == "Legal":
             w_mm, h_mm = 215.9, 355.6
        elif action.paper_size == "Letter":
             w_mm, h_mm = 215.9, 279.4
        else: # A4 Default
             w_mm, h_mm = 210.0, 297.0
        
        # Orientation
        is_landscape = action.orientation == "Landscape"
        if is_landscape:
             w_mm, h_mm = h_mm, w_mm
             
        width_u = int(w_mm * HWPUNIT_PER_MM)
        height_u = int(h_mm * HWPUNIT_PER_MM)
        
        page_pr.set('width', str(width_u))
        page_pr.set('height', str(height_u))
        
        # Margins (mm -> unit)
        left_u = int(action.left * HWPUNIT_PER_MM)
        right_u = int(action.right * HWPUNIT_PER_MM)
        top_u = int(action.top * HWPUNIT_PER_MM)
        bottom_u = int(action.bottom * HWPUNIT_PER_MM)
        header_u = int(action.header * HWPUNIT_PER_MM)
        footer_u = int(action.footer * HWPUNIT_PER_MM)
        gutter_u = int(action.gutter * HWPUNIT_PER_MM)
        
        # Find margin tag
        margin_tag = None
        for child in page_pr:
             if 'margin' in child.tag:
                  margin_tag = child
                  break
        
        if margin_tag is not None:
             margin_tag.set('left', str(left_u))
             margin_tag.set('right', str(right_u))
             margin_tag.set('top', str(top_u))
             margin_tag.set('bottom', str(bottom_u))
             margin_tag.set('header', str(header_u))
             margin_tag.set('footer', str(footer_u))
             margin_tag.set('gutter', str(gutter_u))
             
        print(f"[HwpxDocumentBuilder] Updated Page Setup: {action.paper_size} {action.orientation}")
"""

def append_method():
    with open(TARGET_FILE, 'r') as f:
        content = f.read()
    
    if "def _update_page_setup" in content:
        print("Method definition already exists.")
        return

    # Append to class
    with open(TARGET_FILE, 'a') as f:
        f.write(METHOD_CODE)
    print("Appended _update_page_setup to document_builder.py")

if __name__ == "__main__":
    append_method()

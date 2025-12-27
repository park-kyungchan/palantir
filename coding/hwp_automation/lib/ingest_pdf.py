
import re
import math
from typing import List, Optional, Dict
from collections import Counter
from lib.ir import Document, Section, Paragraph, TextRun, Equation
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

class PdfIngestor:
    """
    Parses PDF files into IR using Visitor Logic for high-fidelity extraction.
    """
    def __init__(self, path: str):
        self.path = path
        self.text_blocks = []
        self.pua_map = {
            "": "0", "": "1", "": "2", "": "3", "": "4",
            "": "5", "": "6", "": "7", "": "8", "": "9",
            "": "x", "": "y", "": "a", "": "b", "": "n",
            "": "+", "": "-", "": "=", "": "/", 
            "": "sqrt", "": "(", "": ")",
        }

    def _visitor_body(self, text, cm, tm, fontDict, fontSize):
        if text and text.strip():
            self.text_blocks.append({
                "text": text.strip(),
                "x": tm[4],
                "y": tm[5],
                "size": fontSize
            })

    def ingest(self) -> Document:
        doc = Document()
        if not PdfReader:
            print("Warning: pypdf not installed.")
            return doc
            
        try:
            reader = PdfReader(self.path)
            # Analyze Page 1 for Layout
            page = reader.pages[0]
            self.text_blocks = [] # Reset
            page.extract_text(visitor_text=self._visitor_body)
            
            section = doc.add_section()
            
            # 1. Analyze Geometry & Margins
            if self.text_blocks:
                x_coords = [b['x'] for b in self.text_blocks]
                y_coords = [b['y'] for b in self.text_blocks]
                sizes = [b['size'] for b in self.text_blocks]
                
                width = float(page.mediabox.width)
                height = float(page.mediabox.height)
                u_to_mm = 0.3527
                
                min_x, max_x = min(x_coords), max(x_coords)
                min_y, max_y = min(y_coords), max(y_coords)
                
                section.page_setup = {
                    "left": int(min_x * u_to_mm),
                    "right": int((width - max_x) * u_to_mm),
                    "top": int((height - max_y) * u_to_mm),
                    "bottom": int(min_y * u_to_mm)
                }
                
                # Deduplication (Shadow/Bold effect removal)
                # Filter out blocks that have same text as another block within very small distance
                unique_blocks = []
                seen_sigs = set() # (text, round(x,1), round(y,1))
                
                for b in self.text_blocks:
                    # Signature: Text + Coords (Rounded to 1 decimal place correpsonds to ~0.3mm)
                    sig = (b['text'], round(b['x'], 1), round(b['y'], 1))
                    if sig not in seen_sigs:
                         unique_blocks.append(b)
                         seen_sigs.add(sig)
                
                self.text_blocks = unique_blocks

                # 2. Analyze Font Scaling
                # Normalize: Most common size -> 10pt
                size_counts = Counter(sizes)
                base_size = size_counts.most_common(1)[0][0]
                # Scale factor?
                # If base is 83 and we want 10 -> factor = 10/83 ~ 0.12
                # If base is 10 and we want 10 -> factor = 1
                # Heuristic: If base > 20, assume it's unscaled user units.
                scale_factor = 1.0
                if base_size > 20:
                    scale_factor = 10.0 / base_size
                
                # 3. Analyze Columns
                mid_x = width / 2
                in_center = [b for b in self.text_blocks if (mid_x - 20) < b['x'] < (mid_x + 20)]
                # If very few items in center, assumes 2 columns
                if len(in_center) < len(self.text_blocks) * 0.05:
                    section.columns = 2
                    section.col_gap = 3000 # Standard gap (approx 10mm)
                else:
                    section.columns = 1 

                # 4. Construct Content (Paragraphs)
                # Sort blocks by Y (desc) then X (asc)
                # Note: PDF Y is bottom-left, so higher Y = top.
                # We sort Y descending.
                sorted_blocks = sorted(self.text_blocks, key=lambda b: (-b['y'], b['x']))
                
                # Simple Line grouping
                current_y = -1
                current_line_text = []
                current_max_size = 0
                
                for b in sorted_blocks:
                    # New line detection (tolerance 6 units - handles superscripts but splits lines)
                    if abs(b['y'] - current_y) > 6 and current_y != -1:
                        # Flush previous line
                        self._add_para(section, current_line_text, current_max_size, scale_factor)
                        current_line_text = []
                        current_max_size = 0
                        
                    current_y = b['y']
                    current_line_text.append(b['text'])
                    current_max_size = max(current_max_size, b['size'])
                if current_line_text:
                    self._add_para(section, current_line_text, current_max_size, scale_factor)

            print(f"DEBUG: Total Text Blocks: {len(self.text_blocks)}")
            print(f"DEBUG: Created Paragraphs: {len(section.paragraphs)}")

        except Exception as e:
            print(f"PDF Parse Error: {e}")
            import traceback
            traceback.print_exc()
            
        return doc
        
    def _add_para(self, section: Section, texts: List[str], size: float, scale: float):
        full_text = " ".join(texts)
        decoded = self._decode_pua(full_text)
        
        # Determine Font Size
        final_size = size * scale
        is_bold = final_size > 11.0 # Simple heuristic: Title usually larger
        
        # Math detection
        if self._is_equation(decoded):
             ir_para = Paragraph(alignment="Left")
             eq = Equation(script=decoded)
             ir_para.elements.append(eq)
             section.paragraphs.append(ir_para)
        else:
             # Regular Text
             # Cleanup spaces? " ".join adds spaces between every fragment.
             # If fragments are letters, this is bad. "H e l l o".
             # Simple fix: " ".join(texts).replace("  ", " ") but simplistic.
             # Better: assume if fragment length is 1, it might be char.
             # For now, let's leave it but note it affects length check.
             run = TextRun(text=decoded, font_size=round(final_size, 1), is_bold=is_bold)
             para = Paragraph(elements=[run])
             section.paragraphs.append(para)

    def _decode_pua(self, text: str) -> str:
        for k, v in self.pua_map.items():
            text = text.replace(k, v)
        return text

    def _is_equation(self, text: str) -> bool:
        # Heuristic: Must have '=' OR (at least 2 distinct math operators AND length > 3)
        math_chars = ["+", "-", "sqrt", "^", "/"]
        has_equal = "=" in text
        op_count = sum(1 for c in math_chars if c in text)
        
        if has_equal:
            return True
        if op_count >= 2 and len(text) > 4:
            return True
        return False

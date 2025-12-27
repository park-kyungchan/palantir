
import sys
import math
from collections import Counter

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not installed.")
    sys.exit(1)

def visitor_body(text, cm, tm, fontDict, fontSize):
    """
    Visitor function to extract coordinates and metrics.
    tm: Text Matrix [a, b, c, d, e, f]
    e = x, f = y
    """
    x = tm[4]
    y = tm[5]
    if text and text.strip():
        # print(f"Text: {text.strip()} | X: {x:.2f} | Y: {y:.2f} | Size: {fontSize}")
        global text_blocks
        text_blocks.append({
            "text": text.strip(),
            "x": x,
            "y": y,
            "size": fontSize
        })

text_blocks = []

def analyze(path):
    reader = PdfReader(path)
    page = reader.pages[0] # Analyze first page for template
    
    # 1. Extract Metrics
    page.extract_text(visitor_text=visitor_body)
    
    if not text_blocks:
        print("No text found with coordinates.")
        return

    # 2. Analyze X-Histogram for Columns
    x_coords = [b['x'] for b in text_blocks]
    min_x = min(x_coords)
    max_x = max(x_coords)
    width = page.mediabox.width
    height = page.mediabox.height
    
    print(f"--- Page Geometry ---")
    print(f"Width: {width} ({float(width)*0.3527:.2f} mm)")
    print(f"Height: {height} ({float(height)*0.3527:.2f} mm)")
    print(f"Content X-Range: {min_x:.2f} ~ {max_x:.2f}")
    
    # 3. Analyze Margins (Approx)
    # PDF (0,0) is usually bottom-left. HWP margins are Top/Bottom/Left/Right.
    # Left Margin ~ min_x
    # Right Margin ~ width - max_x (approx)
    # Top Margin ~ height - max_y
    y_coords = [b['y'] for b in text_blocks]
    max_y = max(y_coords)
    min_y = min(y_coords)
    
    # Conversion: 1 PDF UserUnit ~ 1/72 inch ~ 0.3527 mm
    u_to_mm = 0.3527
    
    margin_left_mm = min_x * u_to_mm
    margin_right_mm = (float(width) - max_x) * u_to_mm
    margin_top_mm = (float(height) - max_y) * u_to_mm
    margin_bottom_mm = min_y * u_to_mm
    
    print(f"--- Inferred Margins (mm) ---")
    print(f"Left: {margin_left_mm:.2f}")
    print(f"Right: {margin_right_mm:.2f}")
    print(f"Top: {margin_top_mm:.2f}")
    print(f"Bottom: {margin_bottom_mm:.2f}")
    
    # 4. Analyze Font Sizes
    sizes = [b['size'] for b in text_blocks]
    size_counts = Counter(sizes)
    common_size = size_counts.most_common(1)[0][0]
    print(f"--- Font Analysis ---")
    print(f"Most Common Size: {common_size}")
    print(f"Max Size: {max(sizes)}")
    print(f"Min Size: {min(sizes)}")
    
    # 5. Column Detection
    # If standard deviation of X is high and bimodal distribution?
    # Simple check: Is there a "gap" in the middle?
    mid_x = float(width) / 2
    # Check emptiness in center 10%
    center_zone_start = mid_x - (float(width) * 0.05)
    center_zone_end = mid_x + (float(width) * 0.05)
    
    in_center = [b for b in text_blocks if center_zone_start < b['x'] < center_zone_end]
    if len(in_center) < len(text_blocks) * 0.05:
        print("--- Layout: Multi-Column Detected ---")
        print(f"Gap seems to be around X={mid_x:.2f}")
    else:
        print("--- Layout: Single Column likely ---")

if __name__ == "__main__":
    analyze("sample.pdf")

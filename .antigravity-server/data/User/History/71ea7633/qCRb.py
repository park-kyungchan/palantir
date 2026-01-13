import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.layout.detector import LayoutDetector, LayoutRegion

def verify_layout(pdf_path: str):
    print(f"🔍 Verifying Layout Detection for: {pdf_path}")
    
    detector = LayoutDetector()
    
    # Run detection
    try:
        regions = detector.detect(pdf_path)
        print(f"✅ Detection successful. Found {len(regions)} regions.")
        
        # Analyze regions
        region_counts = {}
        for r in regions:
            region_counts[r.label] = region_counts.get(r.label, 0) + 1
            print(f"  - [{r.label}] Page {r.page_num}: {r.bbox}")
            
        print("\n📊 Region Statistics:")
        print(json.dumps(region_counts, indent=2))
        
        # Assertion for sample.pdf (Math Workbook)
        # Should have Answer Boxes (e.g., 'answer_box', 'problem_box' etc. depending on model labels)
        # Assuming YOLO model is trained for this.
        
        return regions
    except Exception as e:
        print(f"❌ Detection Failed: {e}")
        return []

if __name__ == "__main__":
    target_pdf = "sample.pdf"
    if len(sys.argv) > 1:
        target_pdf = sys.argv[1]
        
    verify_layout(target_pdf)

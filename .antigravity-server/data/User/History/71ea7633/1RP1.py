
import sys
import os
# Ensure path
sys.path.append("/home/palantir/hwpx") 

from lib.layout.detector import LayoutDetector, LayoutRegion
from lib.ingestors.docling_ingestor import DoclingIngestor
import json
from lib.layout.region import BoundingBox, LayoutLabel

def test():
    pdf_path = "sample.pdf"
    
    # 1. Test Detector Isolation
    print("--- Testing LayoutDetector ---")
    try:
        detector = LayoutDetector()
        regions = detector.detect_pdf_page(pdf_path, 0)
        print(f"✅ Detection successful. Found {len(regions)} regions.")
        for r in regions:
            print(f"  - [{r.label.value}] Page {r.page_number} {r.bbox.to_tuple()}")
    except Exception as e:
        print(f"⚠️ Detector Warning (might be generic model): {e}")

    # 2. Test Ingestor Integration
    print("\n--- Testing DoclingIngestor Integration ---")
    try:
        ingestor = DoclingIngestor(enable_layout_enhancement=True)
        
        # Inject Fake Region for Integration Test
        # Create a fake region that matches some coordinates in typical document body
        # Docling usually returns PDF point coordinates.
        # Let's assume a large box in the middle.
        fake_region = LayoutRegion(
            page_number=1,
            label=LayoutLabel.ANSWER_BOX,
            confidence=1.0,
            bbox=BoundingBox(50.0, 50.0, 500.0, 500.0, coordinate_system=BoundingBox(0,0,0,0).coordinate_system), # Type hack? No, enum.
            region_id="fake_1"
        )
        # Fix bbox instantiation - checking class def
        # BoundingBox(x0, y0, x1, y1)
        fake_region = LayoutRegion(
            page_number=1,
            label=LayoutLabel.ANSWER_BOX,
            confidence=1.0,
            bbox=BoundingBox(50.0, 50.0, 500.0, 500.0), # Simplifed
            region_id="fake_1"
        )

        print(f"Injecting fake region: {fake_region.label.value} {fake_region.bbox.to_tuple()}")
        
        doc = ingestor.ingest(pdf_path, layout_regions=[fake_region])
        
        found_tagged = False
        paragraph_count = 0
        for sec in doc.sections:
            for p in sec.paragraphs:
                paragraph_count += 1
                if p.style == "AnswerBox":
                    content = ""
                    if p.elements and hasattr(p.elements[0], 'text'):
                         content = p.elements[0].text
                    print(f"✅ SUCCESS: Found paragraph tagged as AnswerBox! Content: '{content[:30]}...'")
                    found_tagged = True
        
        print(f"Processed {paragraph_count} paragraphs total.")
        
        if not found_tagged:
            print("❌ FAILED: No paragraph tagged as AnswerBox.")
            # Debug info
            print("First 3 paragraphs bboxes:")
            count = 0
            for sec in doc.sections:
                for p in sec.paragraphs:
                    if count < 3:
                        print(f"  - BBox: {p.bbox}")
                        count += 1

    except Exception as e:
        print(f"❌ Integration Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test()

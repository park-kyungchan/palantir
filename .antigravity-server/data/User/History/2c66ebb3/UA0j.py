
import logging
import sys
import os

# Ensure lib is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from lib.ingestors.docling_ingestor import DoclingIngestor
from lib.layout.region import LayoutRegion, LayoutLabel, BoundingBox

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ocr_pipeline():
    logger.info("--- Testing Vision-Native OCR Pipeline ---")
    
    pdf_path = "sample.pdf"
    if not os.path.exists(pdf_path):
        logger.error(f"Test file {pdf_path} not found!")
        return

    ingestor = DoclingIngestor(enable_layout_enhancement=True, enable_ocr=True)
    
    # Inject a known region that contains text
    # Sample.pdf has "4. ..." around top left?
    # Let's use a broad region to be safe: 100, 100 to 500, 300
    fake_region = LayoutRegion(
        bbox=BoundingBox(50, 50, 500, 500),
        label=LayoutLabel.ANSWER_BOX,
        confidence=0.99
    )
    
    logger.info(f"Injecting fake region: {fake_region.label} {fake_region.bbox}")
    
    try:
        # Pass layout regions to trigger vision fallback path (since Docling will fail naturally on sample.pdf)
        doc = ingestor.ingest(pdf_path, layout_regions=[fake_region])
        
        answer_boxes = []
        for section in doc.sections:
            for para in section.elements: # We used .elements in fallback
                if para.style == "AnswerBox":
                    answer_boxes.append(para)
        
        logger.info(f"Processed {len(answer_boxes)} AnswerBox paragraphs.")
        
        if not answer_boxes:
            logger.error("❌ FAILED: No paragraph tagged as AnswerBox.")
            return
            
        for i, box in enumerate(answer_boxes[:5]):
             text = box.elements[0].text if box.elements else "[Empty]"
             logger.info(f"AnswerBox {i+1} Text: '{text[:100]}...'")
             if len(text) > 5:
                 logger.info("✅ SUCCESS: Text extracted.")
                 
    except Exception as e:
        logger.error(f"❌ Integration Failed: {e}", exc_info=True)

if __name__ == "__main__":
    test_ocr_pipeline()

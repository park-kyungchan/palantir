import logging
import sys
import json
from dataclasses import asdict
from pathlib import Path
from lib.ingestors.docling_ingestor import DoclingIngestor
import lib.layout.detector
print(f"DEBUG: lib.layout.detector file: {lib.layout.detector.__file__}")
from lib.ir import Document, Paragraph, Table, Section

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ir_generation(pdf_path: str):
    """
    Runs the full ingestion pipeline (fallback path anticipated for sample.pdf)
    and validates the resulting Intermediate Representation (IR).
    """
    logger.info(f"--- Testing IR Generation for {pdf_path} ---")
    
    # Initialize Ingestor (Standard configuration with OCR enabled)
    # We expect this to trigger the PyMuPDF + EasyOCR fallback due to sample.pdf encoding issues.
    ingestor = DoclingIngestor(enable_ocr=True, enable_layout_enhancement=True)
    
    try:
        # Ingest Document
        doc: Document = ingestor.ingest(pdf_path)
        logger.info("Ingestion complete.")
        
        # 1. Structural Validation
        if not doc.sections:
            logger.error("❌ FAILED: Document has no sections.")
            return

        total_sections = len(doc.sections)
        total_elements = sum(len(s.elements) for s in doc.sections)
        logger.info(f"Structure: {total_sections} Sections, {total_elements} Total Elements.")

        # 2. AnswerBox Validation
        answer_boxes = []
        problem_boxes = []
        tables = []

        for s_idx, section in enumerate(doc.sections):
            for e_idx, element in enumerate(section.elements):
                if isinstance(element, Paragraph):
                    if element.style == "AnswerBox":
                        answer_boxes.append(element)
                    elif element.style == "ProblemBox":
                        problem_boxes.append(element)
                elif isinstance(element, Table):
                    tables.append(element)

        logger.info(f"Found {len(answer_boxes)} AnswerBox paragraphs.")
        logger.info(f"Found {len(problem_boxes)} ProblemBox paragraphs.")
        logger.info(f"Found {len(tables)} Tables.")

        # Check for expected content (based on visual inspection of sample.pdf / verified OCR)
        # We know from previous steps there are AnswerBoxes.
        if not answer_boxes and not problem_boxes:
             logger.warning("⚠️ WARNING: No AnswerBox or ProblemBox detected. Layout analysis might need tuning or PDF has no such regions.")
        else:
             logger.info("✅ SUCCESS: Detected semantic regions.")

        # 3. Dump IR to JSON
        output_path = Path("ir_output.json")
        with open(output_path, "w", encoding="utf-8") as f:
            # Helper to handle non-serializable objects if any (though dataclasses usually fine via asdict)
            json.dump(asdict(doc), f, indent=2, ensure_ascii=False)
        
        logger.info(f"IR dumped to {output_path.absolute()}")

        # 4. Content Peek
        # Print first few text runs of first AnswerBox to confirm OCR quality
        if answer_boxes:
            first_box = answer_boxes[0]
            text = "".join([r.text for r in first_box.elements if hasattr(r, 'text')])
            logger.info(f"Sample AnswerBox Content: {text[:100]}...")

    except Exception as e:
        logger.error(f"❌ CRITICAL FAILURE during IR generation: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    pdf_file = "sample.pdf"
    if not Path(pdf_file).exists():
        logger.error(f"File {pdf_file} not found.")
        sys.exit(1)
        
    test_ir_generation(pdf_file)

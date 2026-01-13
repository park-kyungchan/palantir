import sys
import os
import logging
from dataclasses import asdict
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.ingestors.docling_ingestor import DoclingIngestor
import lib.ir as ir

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PDF_FILES = [
    "ActionTable_2504.pdf",
    "HwpAutomation_2504.pdf",
    "ParameterSetTable_2504.pdf"
]

OUTPUT_DIR = "verification_output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def dump_ir_to_text(doc: ir.Document, output_path: str):
    """
    Dumps the IR document to a human-readable text format for inspection.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Document Verification Dump\n")
        f.write(f"==========================\n\n")
        
        total_tables = 0
        total_figures = 0
        total_paragraphs = 0
        
        for i, section in enumerate(doc.sections):
            f.write(f"--- Section {i+1} ---\n")
            
            for elem in section.elements:
                if isinstance(elem, ir.Paragraph):
                    total_paragraphs += 1
                    text_content = ""
                    for run in elem.elements:
                        if isinstance(run, ir.TextRun):
                            text_content += run.text
                        elif isinstance(run, ir.Equation):
                            text_content += f"[MATH: {run.script}]"
                        elif isinstance(run, ir.Image): # Inline image
                            text_content += f"[INLINE IMAGE: {run.path}]"
                            total_figures += 1
                    f.write(f"P: {text_content}\n")
                    
                elif isinstance(elem, ir.Table):
                    total_tables += 1
                    f.write(f"\n[TABLE] (Rows: {len(elem.rows)})\n")
                    for row in elem.rows:
                        row_text = []
                        for cell in row.cells:
                            cell_text = ""
                            for item in cell.content:
                                if isinstance(item, ir.TextRun):
                                    cell_text += item.text
                                elif isinstance(item, ir.Image):
                                    cell_text += f"[IMG: {item.path}]"
                            row_text.append(cell_text.strip())
                        f.write(f"  | {' | '.join(row_text)} |\n")
                    f.write("\n")
                    
                elif isinstance(elem, ir.Figure):
                    total_figures += 1
                    f.write(f"\n[FIGURE]\n  Path: {elem.path}\n  Caption: {elem.caption}\n\n")
                
                elif isinstance(elem, ir.Container):
                     f.write(f"\n[CONTAINER]\n")
                     # Shallow dump for container for now
                     f.write(f"  Elements: {len(elem.elements)}\n")

        f.write(f"\n--- Statistics ---\n")
        f.write(f"Total Paragraphs: {total_paragraphs}\n")
        f.write(f"Total Tables: {total_tables}\n")
        f.write(f"Total Figures: {total_figures}\n")
        
    return {
        "tables": total_tables,
        "figures": total_figures,
        "paragraphs": total_paragraphs
    }

def verify_file(filename):
    path = os.path.abspath(filename)
    if not os.path.exists(path):
        logger.error(f"File not found: {path}")
        return

    logger.info(f"Processing {filename}...")
    
    # Initialize Ingestor with high-fidelity settings
    ingestor = DoclingIngestor(
        enable_ocr=True,
        enable_table_structure=True, 
        enable_layout_enhancement=True 
    )

    try:
        # Ingest
        doc = ingestor.ingest(path)
        
        output_txt = os.path.join(OUTPUT_DIR, f"{filename}.dump.txt")
        stats = dump_ir_to_text(doc, output_txt)
        
        logger.info(f"Verified {filename}. Dumped to {output_txt}")
        logger.info(f"Stats: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        logger.error(f"Failed to ingest {filename}: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting Parsing Verification...")
    for f in PDF_FILES:
        verify_file(f)
    logger.info("Verification Complete.")

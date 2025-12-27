
import os
import sys
import argparse
import json
import logging
from core_bridge import WSLBridge
from lib.ir import Document
from lib.compiler import Compiler
# Ingestors
from lib.ingest_hwpx import HwpxIngestor
from lib.ingest_pdf import PdfIngestor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Pipeline")

def main():
    parser = argparse.ArgumentParser(description="HWPX/PDF Reconstruction Pipeline")
    parser.add_argument("input_path", help="Path to source file (HWPX or PDF)")
    parser.add_argument("--output", help="Path to output HWPX file (Windows Path, e.g. C:\\Temp\\output.hwpx)", required=False)
    args = parser.parse_args()

    input_path = os.path.abspath(args.input_path)
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    # 1. Ingestion (ETL: Extract)
    doc = None
    ext = os.path.splitext(input_path)[1].lower()
    
    logger.info(f"Ingesting {ext} file: {input_path}")
    
    if ext == ".hwpx":
        ingestor = HwpxIngestor(input_path)
        doc = ingestor.ingest()
    elif ext == ".pdf":
        ingestor = PdfIngestor(input_path)
        doc = ingestor.ingest()
    else:
        logger.error(f"Unsupported format: {ext}")
        sys.exit(1)

    if not doc:
        logger.error("Ingestion failed to produce a Document.")
        sys.exit(1)

    logger.info(f"Ingestion Complete. IR contains {len(doc.sections)} sections.")

    # 2. Compilation (ETL: Transform)
    compiler = Compiler()
    if args.output:
        # User specified output path
        output_win_path = args.output
    else:
        # Default output
        filename = os.path.basename(input_path)
        name_only = os.path.splitext(filename)[0]
        output_win_path = f"C:\\Temp\\{name_only}_reconstructed.hwpx"

    logger.info(f"Compiling actions for target: {output_win_path}")
    payload_data = compiler.compile(doc, output_path=output_win_path)
    
    # 3. Payload Generation (ETL: Load Preparation)
    payload_path = os.path.abspath("pipeline_payload.json")
    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload_data, f, indent=2, ensure_ascii=False)
        
    logger.info(f"Payload generated: {payload_path}")

    # 4. Execution (ETL: Load)
    logger.info("--- Handing off to Windows Executor ---")
    bridge = WSLBridge()
    script_path = os.path.abspath("executor_win.py")
    
    return_code = bridge.run_python_script(script_path, payload_path)
    
    if return_code == 0:
        logger.info("Pipeline Execution Successful.")
        logger.info(f"Result saved to: {output_win_path}")
    else:
        logger.error(f"Pipeline Execution Failed with code {return_code}")
        sys.exit(return_code)

if __name__ == "__main__":
    main()

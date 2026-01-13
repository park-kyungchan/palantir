import json
from typing import List, Dict, Any, Optional
import os

from lib.ingestors.mathpix_ingestor import MathpixIngestor
from lib.parsers.markdown_parser import MarkdownParser
from lib.compiler import Compiler
from lib.ir_serializer import IRSerializer
from lib.models import HwpAction
from lib.builder import Builder
from lib.owpml.generator import HWPGenerator
from lib.owpml.document_builder import HwpxDocumentBuilder

class HWPXPipeline:
    """
    Orchestrates the conversion from PDF to HWPX Actions.
    """
    def __init__(self, use_mathpix: bool = True):
        self.use_mathpix = use_mathpix
        if self.use_mathpix:
            self.ingestor = MathpixIngestor()
            self.parser = MarkdownParser()
        else:
            from lib.ingestors.docling_ingestor import DoclingIngestor
            self.ingestor = DoclingIngestor()
            self.parser = None # DoclingIngestor returns Document directly
            
        self.compiler = Compiler()

    def run(self, input_path: str, output_path: str, generate_pdf: bool = False) -> List[Dict[str, Any]]:
        """
        Runs the pipeline.
        
        Args:
            input_path: Path to PDF file.
            output_path: Path to save JSON/Actions or PDF.
            generate_pdf: If True, generates a PDF using Mathpix Converter instead of HWPX.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 1. Ingest
        print(f"Ingesting: {input_path}...")
        raw_output = self.ingestor.ingest(input_path)
        
        # 1.5 Parse or Generate PDF
        if self.use_mathpix:
             if generate_pdf:
                 # Raw output from MathpixIngestor is the MMD string
                 print("Generating PDF from Mathpix Markdown...")
                 from lib.generators.pdf_generator import PDFGenerator
                 gen = PDFGenerator()
                 pdf_path = output_path if output_path.endswith(".pdf") else output_path + ".pdf"
                 gen.generate(raw_output, pdf_path)
                 print(f"Success! PDF generated at {pdf_path}")
                 return [] # No actions returned
                 
             print("Parsing Mathpix Markdown...")
             doc = self.parser.parse(raw_output)
        else:
             doc = raw_output
        
        # 2. Compile (IR -> HWP Actions)
        print("Compiling IR to HWP Actions...")
        actions_dicts = self.compiler.compile(doc)
        
        # 3. Serialize Output
        if output_path:
            # Save JSON
            print(f"Saving JSON output to: {output_path}")
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(actions_dicts, f, indent=2, ensure_ascii=False)
                
            # 4. Build (Actions -> Python Script)
            py_output = output_path.replace(".json", ".py") if output_path.endswith(".json") else output_path + ".py"
            print(f"Building reconstruction script: {py_output}")
            
            builder = Builder()
            builder.build(self.compiler.actions, py_output)
            
            # 5. Generate Native HWPX (Linux-side)
            if output_path.endswith(".json"):
                hwpx_output = output_path.replace(".json", ".hwpx")
            else:
                hwpx_output = output_path + ".hwpx"
                
            print(f"Generating Native HWPX: {hwpx_output}")
            print(f"Generating Native HWPX: {hwpx_output}")
            # generator = HWPGenerator()
            # generator.generate(self.compiler.actions, hwpx_output)
            builder = HwpxDocumentBuilder()
            builder.build(self.compiler.actions, hwpx_output)
                
        return actions_dicts

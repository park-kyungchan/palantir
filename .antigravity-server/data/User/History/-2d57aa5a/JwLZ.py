import json
from typing import List, Dict, Any, Optional
import os

from lib.ingestors.docling_ingestor import DoclingIngestor
from lib.compiler import Compiler
from lib.ir_serializer import IRSerializer
from lib.models import HwpAction
from lib.builder import Builder

class HWPXPipeline:
    """
    Orchestrates the conversion from PDF to HWPX Actions.
    """
    def __init__(self, use_ocr: bool = True, layout_analysis: bool = True):
        self.ingestor = DoclingIngestor()
        # Note: DoclingIngestor configuration (OCR/Layout) is currently done via constructor args
        # or internally based on installed libs. 
        # In our implementation, DoclingIngestor sets up Layout/OCR lazy-loaded.
        # Ideally we pass config here.
        # But for now, we assume defaults or environment config.
        self.compiler = Compiler()

    def run(self, input_path: str, output_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Run the full pipeline.
        
        Args:
            input_path: Path to input PDF.
            output_path: Path to save the resulting Action JSON.
            
        Returns:
            List of serialized HWP Actions.
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # 1. Ingest (Reader + Layout + OCR -> IR)
        print(f"Ingesting: {input_path}...")
        doc = self.ingestor.ingest(input_path)
        
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
                
        return actions_dicts

import os
import json
import cv2
import pdf2image
import numpy as np
from typing import List, Type
from .core.base import BaseSegmenter, BaseTranscriber
from .segmenters.opencv_segmenter import OpenCVSegmenter
from .transcribers.agent_transcriber import BrowserAgentTranscriber

class MathMinerPipeline:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.segmenter: BaseSegmenter = OpenCVSegmenter()
        self.transcriber: BaseTranscriber = BrowserAgentTranscriber()
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def process_pdf(self, pdf_path: str):
        print(f"[*] Processing PDF: {pdf_path}")
        
        # 1. Convert PDF to Images
        pil_images = pdf2image.convert_from_path(pdf_path, dpi=300)
        cv_images = [cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR) for img in pil_images]
        
        manifest = []
        
        for i, image in enumerate(cv_images):
            page_num = i + 1
            print(f"    - Page {page_num}: Segmenting...")
            
            # 2. Segmentation
            segments = self.segmenter.segment(image, page_num)
            
            page_dir = os.path.join(self.output_dir, f"page_{page_num}")
            if not os.path.exists(page_dir):
                os.makedirs(page_dir)
            
            # Save Full Page
            cv2.imwrite(os.path.join(page_dir, "full.png"), image)
            
            for j, seg in enumerate(segments):
                bbox = seg['bbox']
                x, y, w, h = bbox
                cropped = image[y:y+h, x:x+w]
                
                # Save Segment Image
                seg_filename = f"segment_{j+1}.png"
                seg_path = os.path.join(page_dir, seg_filename)
                cv2.imwrite(seg_path, cropped)
                
                # 3. Transcription (Placeholder for Agent)
                transcription = self.transcriber.transcribe(cropped)
                
                manifest.append({
                    "id": f"p{page_num}_s{j+1}",
                    "page": page_num,
                    "bbox": bbox,
                    "image_path": seg_path,
                    "transcription": transcription
                })
                
        # 4. Save Manifest
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
            
        print(f"[*] Pipeline Complete. Manifest saved to {manifest_path}")

    def validate_manifest(self):
        """
        Validates the LaTeX content in the manifest for common syntax errors.
        This is a 'Meta-Level' safety check to prevent build failures.
        """
        manifest_path = os.path.join(self.output_dir, "manifest.json")
        if not os.path.exists(manifest_path):
            return

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
            
        issues_found = False
        for item in manifest:
            transcription = item.get("transcription", {})
            latex = transcription.get("latex", "")
            
            # Skip placeholders
            if latex.startswith("[PENDING"):
                continue
                
            # Check 1: Balanced Braces
            if latex.count('{') != latex.count('}'):
                print(f"[!] Warning: Unbalanced braces in {item['id']}")
                issues_found = True
                
            # Check 2: Balanced Math Delimiters ($)
            # Simple check: count must be even (ignoring escaped \$)
            if latex.replace(r'\$', '').count('$') % 2 != 0:
                print(f"[!] Warning: Unbalanced math delimiters ($) in {item['id']}")
                issues_found = True
                
            # Check 3: Unprotected \textcircled in enumerate labels
            # This is a heuristic check
            if r'\begin{enumerate}[label=\textcircled' in latex:
                 print(f"[!] Warning: Unprotected \\textcircled in enumerate label in {item['id']}. Use \\protect.")
                 issues_found = True

        if not issues_found:
            print("[*] Manifest validation passed. No obvious syntax errors found.")
        else:
            print("[!] Validation completed with warnings. Please review the manifest.")

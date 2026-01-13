import os
import time
import requests
import json
from typing import Optional

class MathpixIngestor:
    """
    Ingests PDF documents using the Mathpix OCR API (v3/pdf).
    Returns the document content as Markdown string.
    """
    def __init__(self):
        self.app_id = os.environ.get("MATHPIX_APP_ID")
        self.app_key = os.environ.get("MATHPIX_APP_KEY")
        
        if not self.app_id or not self.app_key:
            print("WARNING: MATHPIX_APP_ID or MATHPIX_APP_KEY not set.")
            
    def ingest(self, pdf_path: str) -> str:
        """
        Uploads PDF to Mathpix and returns the Markdown content.
        """
        if not self.app_id or not self.app_key:
            raise ValueError("Mathpix credentials missing. Set MATHPIX_APP_ID and MATHPIX_APP_KEY.")

        print(f"[Mathpix] Uploading {pdf_path}...")
        
        # 1. Upload PDF
        with open(pdf_path, "rb") as f:
            response = requests.post(
                "https://api.mathpix.com/v3/pdf",
                headers={
                    "app_id": self.app_id,
                    "app_key": self.app_key
                },
                files={"file": f},
                data={
                    "conversion_formats": json.dumps({"md": True, "docx": False, "tex.zip": False}),
                    "math_inline_delimiters": ["$", "$"],
                    "math_display_delimiters": ["$$", "$$"]
                }
            )
        
        if response.status_code != 200:
             print(f"Error Response: {response.text}")
             raise Exception(f"Mathpix Upload Failed: {response.text}")
        
        resp_json = response.json()
        print(f"[Mathpix] Upload Response: {resp_json}")
        
        if "pdf_id" not in resp_json:
             raise KeyError(f"pdf_id not found in response. Keys: {resp_json.keys()}")
             
        pdf_id = resp_json["pdf_id"]
        print(f"[Mathpix] Processing PDF ID: {pdf_id}")
        
        # 2. Poll for status
        while True:
            status_response = requests.get(
                f"https://api.mathpix.com/v3/pdf/{pdf_id}",
                headers={
                    "app_id": self.app_id,
                    "app_key": self.app_key
                }
            )
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "completed":
                print("[Mathpix] Conversion Completed.")
                break
            elif status == "error":
                raise Exception(f"Mathpix Conversion Error: {status_data}")
            
            print(f"[Mathpix] Status: {status}... Waiting 2s")
            time.sleep(2)
            
        # 3. Retrieve Markdown
        md_url = f"https://api.mathpix.com/v3/pdf/{pdf_id}.md"
        md_response = requests.get(
            md_url,
            headers={
                "app_id": self.app_id,
                "app_key": self.app_key
            }
        )
        
        if md_response.status_code != 200:
             raise Exception(f"Failed to download Markdown: {md_response.text}")
             
        return md_response.text

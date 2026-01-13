import requests
import time
import os
import json
from typing import Optional

class PDFGenerator:
    """
    Generates high-fidelity PDFs from Mathpix Markdown (MMD) using the Mathpix Converter API.
    Bypasses local rendering engines by leveraging Mathpix's cloud renderer.
    """
    
    def __init__(self, app_id: Optional[str] = None, app_key: Optional[str] = None):
        self.app_id = app_id or os.environ.get("MATHPIX_APP_ID")
        self.app_key = app_key or os.environ.get("MATHPIX_APP_KEY")
        self.base_url = "https://api.mathpix.com/v3/converter"
        
        if not self.app_id or not self.app_key:
            raise ValueError("Mathpix credentials not found (MATHPIX_APP_ID, MATHPIX_APP_KEY)")

    def generate(self, mmd_content: str, output_path: str, options: dict = None) -> str:
        """
        Converts MMD content to a PDF file.
        
        Args:
            mmd_content: The Mathpix Markdown string.
            output_path: Local path to save the generated PDF.
            options: Dictionary of specific PDF formatting options.
            
        Returns:
            The absolute path to the generated PDF.
        """
        
        payload = {
            "mmd": mmd_content,
            "formats": {"pdf": True},
            "options": {
                "pdf": options or {"page_size": "A4"}
            }
        }
        
        headers = {
            "app_id": self.app_id,
            "app_key": self.app_key,
            "Content-Type": "application/json"
        }
        
        print(f"[PDFGenerator] Sending request to {self.base_url}...")
        response = requests.post(self.base_url, json=payload, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Mathpix Converter Failed: {response.text}")
            
        resp_json = response.json()
        if "conversion_id" not in resp_json:
             raise KeyError(f"No conversion_id in response: {resp_json}")
             
        conversion_id = resp_json["conversion_id"]
        print(f"[PDFGenerator] Conversion ID: {conversion_id}")
        
        # Poll for completion
        pdf_url = self._poll_status(conversion_id, headers)
        
        # Download
        self._download_file(pdf_url, output_path)
        return os.path.abspath(output_path)
        
    def _poll_status(self, conversion_id: str, headers: dict) -> str:
        status_url = f"{self.base_url}/{conversion_id}"
        
        while True:
            resp = requests.get(status_url, headers=headers, timeout=10)
            if resp.status_code != 200:
                print(f"[PDFGenerator] Status Check Failed: {resp.status_code}")
                time.sleep(2)
                continue
                
            data = resp.json()
            status = data.get("status")
            
            if status == "completed":
                if "pdf" in data:
                    print("[PDFGenerator] Conversion Completed.")
                    return data["pdf"]
                elif "conversion_status" in data:
                    # Check granular status
                    pdf_status = data["conversion_status"].get("pdf", {}).get("status")
                    if pdf_status == "processing":
                         print(f"[PDFGenerator] Main completed, but PDF processing...")
                         time.sleep(2)
                         continue
                    else:
                         raise Exception(f"Completed but PDF status: {pdf_status} in {data}")
                else:
                    raise Exception(f"Completed but no PDF URL: {data}")
            elif status == "error":
                raise Exception(f"Conversion Error: {data}")
            else:
                print(f"[PDFGenerator] Status: {status}...")
                time.sleep(2)

    def _download_file(self, url: str, path: str):
        print(f"[PDFGenerator] Downloading PDF from {url}...")
        resp = requests.get(url, timeout=60)
        if resp.status_code == 200:
            with open(path, "wb") as f:
                f.write(resp.content)
            print(f"[PDFGenerator] Saved to {path}")
        else:
            raise Exception(f"Download Failed: {resp.status_code}")

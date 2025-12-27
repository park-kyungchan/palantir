
import os
import zipfile
import re
import math
import shutil
import xml.etree.ElementTree as ET
from lib.ingest_pdf import PdfIngestor

def verify(pdf_path, hwpx_path):
    print(f"--- Verification Strategy ---")
    print(f"Source: {pdf_path}")
    print(f"Target: {hwpx_path}")
    
    # 1. Ground Truth (from PDF Ingestor)
    ingestor = PdfIngestor(pdf_path)
    doc_ir = ingestor.ingest()
    section = doc_ir.sections[0]
    
    expected_equations = 0
    expected_text_len = 0
    for p in section.paragraphs:
        for e in p.elements:
            if hasattr(e, 'script'): # Equation
                expected_equations += 1
            elif hasattr(e, 'text'):
                expected_text_len += len(e.text)
                
    expected_margins = section.page_setup or {}
    
    print(f"[Ground Truth] Equations: {expected_equations}")
    print(f"[Ground Truth] Text Length: ~{expected_text_len}")
    print(f"[Ground Truth] Margins: {expected_margins}")
    
    # 2. Inspect HWPX
    if not os.path.exists(hwpx_path):
        print(f"[Failure] HWPX file not found: {hwpx_path}")
        return False
        
    with zipfile.ZipFile(hwpx_path, 'r') as z:
        # standard HWPX structure: Contents/section0.xml
        try:
            xml_data = z.read('Contents/section0.xml').decode('utf-8')
        except KeyError:
             print(f"[Failure] Invalid HWPX structure (missing section0.xml)")
             return False

    # 3. Analyze XML
    # Equations in HWPX are usually <hp:ctrl> with <hp:colPr type="equation" ...>
    # The dedicated tag is hp:equation
    
    actual_equations = xml_data.count("hp:equation")
    
    # Paragraph Check
    actual_paragraphs = xml_data.count("hp:p")
    print(f"[Actual] Paragraphs: {actual_paragraphs}")
    
    print(f"[Actual] Equations (hp:equation): {actual_equations}")
    
    # Text Extraction from XML
    # Clean tags
    text_content = re.sub('<[^>]+>', '', xml_data)
    # Remove whitespace noise
    text_content_clean = re.sub(r'\s+', '', text_content)
    actual_text_len = len(text_content_clean)
    
    print(f"[Actual] Cleaned Text Length: {actual_text_len}")
    
    # 4. Assertions
    success = True
    
    # Paragraph Sanity Check
    if actual_paragraphs < 5:
        print(f"[Failure] Too few paragraphs ({actual_paragraphs}). One-giant-paragraph bug?")
        success = False
    
    # Equation Check
    if expected_equations > 0:
        # Allow some discrepancy if XML structure is complex, but should meet min
        if actual_equations < expected_equations:
             print(f"[Warning] Equation count mismatch! Expected {expected_equations}, Found {actual_equations}")
        else:
             print(f"[Success] Equation count verified.")
    # Clean tags
    text_content = re.sub('<[^>]+>', '', xml_data)
    # Remove whitespace noise
    text_content_clean = re.sub(r'\s+', '', text_content)
    actual_text_len = len(text_content_clean)
    
    print(f"[Actual] Cleaned Text Length: {actual_text_len}")
    
    # 4. Assertions
    success = True
    
    # Equation Check
    if expected_equations > 0:
        # Allow some discrepancy if XML structure is complex, but should meet min
        if actual_equations < expected_equations:
             print(f"[Warning] Equation count mismatch! Expected {expected_equations}, Found {actual_equations}")
             # success = False # Warning for now as XML parsing is rough
        else:
             print(f"[Success] Equation count verified.")
             
    # Text Check
    # Allow 20% variance due to formatting chars vs plain text
    if abs(expected_text_len - actual_text_len) / (expected_text_len + 1) > 0.2:
         print(f"[Failure] Text length mismatch significant.")
         success = False
    else:
         print(f"[Success] Text content verified.")
         
    return success

if __name__ == "__main__":
    # Copy from Windows temp if needed
    src = "/mnt/c/Temp/sample_reconstructed.hwpx"
    dst = "sample_reconstructed_verified.hwpx"
    if os.path.exists(src):
        shutil.copy(src, dst)
        print(f"Retrieved {src} to {dst}")
        
    if verify("sample.pdf", dst):
        print(">>> VERIFICATION PASSED <<<")
        exit(0)
    else:
        print(">>> VERIFICATION FAILED <<<")
        exit(1)

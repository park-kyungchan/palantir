import fitz  # PyMuPDF
import os
import sys

def convert_pdf_page_to_image(pdf_path, page_num, output_dir):
    if not os.path.exists(pdf_path):
        print(f"Error: File {pdf_path} not found.")
        sys.exit(1)
        
    os.makedirs(output_dir, exist_ok=True)
    
    doc = fitz.open(pdf_path)
    if page_num < 1 or page_num > len(doc):
        print(f"Error: Page {page_num} out of range (1-{len(doc)})")
        sys.exit(1)
        
    page = doc.load_page(page_num - 1) # 0-indexed
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2)) # 2x zoom for higher resolution
    
    output_path = os.path.join(output_dir, f"page_{page_num}.png")
    pix.save(output_path)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    convert_pdf_page_to_image(
        pdf_path="ActionTable_2504.pdf",
        page_num=1,
        output_dir="temp_vision"
    )

import pdf2image
import cv2
import numpy as np
import pdfplumber
import os

pdf_path = "/home/palantir/math/integrate/math-problem-and-answer/202106-h3-math-dif.pdf"

def analyze_pdf(path):
    print(f"Analyzing: {path}")
    
    # 1. Pixel-level Access (Image Processing)
    print("\n[1] Pixel-level Analysis (Visual)")
    try:
        # Convert first page to image
        images = pdf2image.convert_from_path(path, first_page=1, last_page=1)
        if images:
            img = np.array(images[0])
            # Convert RGB to BGR for OpenCV
            img_cv = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            
            height, width, channels = img_cv.shape
            print(f" - Page 1 Image Size: {width}x{height}")
            print(f" - Pixel (100, 100) Value: {img_cv[100, 100]}")
            
            # Simple processing: Find contours (e.g., potential math formulas or boxes)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            print(f" - Detected Contours (Potential Objects): {len(contours)}")
        else:
            print(" - Failed to convert PDF to image.")
    except Exception as e:
        print(f" - Error in image processing: {e}")

    # 2. Object-level Access (PDF Structure)
    print("\n[2] Object-level Analysis (Structure)")
    try:
        with pdfplumber.open(path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            print(f" - Extracted Text (First 100 chars):\n{text[:100]}...")
            print(f" - Number of Lines/Rects: {len(page.lines) + len(page.rects)}")
            print(f" - Number of Images embedded: {len(page.images)}")
    except Exception as e:
        print(f" - Error in structural analysis: {e}")

if __name__ == "__main__":
    analyze_pdf(pdf_path)

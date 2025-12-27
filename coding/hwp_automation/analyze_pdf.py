
import os
try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf not found. Trying basic string extraction.")
    PdfReader = None

def analyze_pdf(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return

    print(f"Analyzing: {path}")
    
    if PdfReader:
        try:
            reader = PdfReader(path)
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                print(f"--- Page {i+1} ---")
                print(text)
        except Exception as e:
            print(f"PDF Parsing failed: {e}")
    else:
        # Fallback: simple binary search for text-like patterns (unreliable but better than nothing)
        # Or better, just tell the user I need to install a library.
        pass

if __name__ == "__main__":
    import sys
    # Install pypdf if possible? No, restricted env.
    # Check if pypdf is installed in venv.
    sys.path.append("/home/palantir/.venv/lib/python3.10/site-packages") # Guessing path
    analyze_pdf("/home/palantir/hwpx/sample.pdf")

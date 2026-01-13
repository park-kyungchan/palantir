"""
Verify Image Insertion
Tests the InsertImage action with BinDataManager.
"""
import os
import sys
from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertImage

def test_image_insertion():
    # 1. Create dummy PNG
    png_path = "test_image.png"
    # 1x1 pixel transparent PNG
    with open(png_path, 'wb') as f:
        f.write(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82')
        
    action = InsertImage(path=os.path.abspath(png_path), width=50, height=50)
    
    # 2. Build Document
    builder = HwpxDocumentBuilder()
    output_path = "output_image_test.hwpx"
    try:
        builder.build([action], output_path)
        print(f"Created {output_path}")
    except Exception as e:
        print(f"Build failed: {e}")
        return

    # 3. Verify Zip Structure
    import zipfile
    import xml.etree.ElementTree as ET
    
    with zipfile.ZipFile(output_path, 'r') as zf:
        # Check BinData existence
        files = zf.namelist()
        bin_files = [f for f in files if f.startswith('BinData/')]
        print(f"BinData files: {bin_files}")
        
        if not bin_files:
            print("❌ BinData file missing in ZIP")
        else:
            print(f"✅ Found {len(bin_files)} binary files")
            
        # Check content.hpf manifest
        hpf_xml = zf.read('Contents/content.hpf').decode('utf-8')
        if 'BinData/' in hpf_xml and 'media-type="image/png"' in hpf_xml:
             print("✅ Manifest updated with BinData ref")
        else:
             print("❌ Manifest missing BinData ref")
             print(hpf_xml[:500])
             
        # Check section0.xml for hp:pic
        sec_xml = zf.read('Contents/section0.xml').decode('utf-8')
        if 'hp:pic' in sec_xml and 'binaryItemIDRef="bin' in sec_xml:
             print("✅ Section0 contains hp:pic with binary ref")
        else:
             print("❌ Section0 missing hp:pic")

    # Cleanup
    if os.path.exists(png_path): os.unlink(png_path)
    # Keeping output_image_test.hwpx for manual inspection if needed

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_image_insertion()
    else:
        print("Skipping - No Skeleton.hwpx")

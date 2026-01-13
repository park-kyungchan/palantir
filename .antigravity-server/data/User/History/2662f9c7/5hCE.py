"""
Verify HwpxPackage Binary Injection Capability
"""
import os
from hwpx.package import HwpxPackage
from hwpx import templates
import tempfile

def test_binary_injection():
    # 1. Load blank template
    fd, temp_path = tempfile.mkstemp(suffix='.hwpx')
    os.close(fd)
    with open(temp_path, 'wb') as f:
        f.write(templates.blank_document_bytes())
        
    pkg = HwpxPackage.open(temp_path)
    
    # 2. Inject dummy binary
    dummy_data = b'\x89PNG\r\n\x1a\n\x00\x00' # PNG signature
    bin_path = 'BinData/test.png'
    
    # Method A: set_part (if available and persists)
    if hasattr(pkg, 'set_part'):
        pkg.set_part(bin_path, dummy_data)
        print("✅ Called set_part")
    else:
        print("❌ No set_part method")
        
    # 3. Save
    output_path = 'output_bindata_test.hwpx'
    pkg.save(output_path)
    
    # 4. Verify Zip
    import zipfile
    with zipfile.ZipFile(output_path, 'r') as zf:
        if bin_path in zf.namelist():
            print(f"✅ {bin_path} found in output zip")
            content = zf.read(bin_path)
            if content == dummy_data:
                 print("✅ Content matches")
            else:
                 print("❌ Content mismatch")
        else:
            print(f"❌ {bin_path} NOT found in output zip")
            
    # Cleanup
    if os.path.exists(temp_path): os.unlink(temp_path)
    if os.path.exists(output_path): os.unlink(output_path)

if __name__ == '__main__':
    test_binary_injection()

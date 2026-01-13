
import zipfile
import xml.etree.ElementTree as ET
import sys

def inspect_numbering():
    skeleton_path = "lib/templates/Skeleton.hwpx" # Assuming this path from previous knowledge
    # Wait, previous script used "lib/templates" if I recall?
    # Or I can use find_by_name to locate it? 
    # I'll check my memory or list_dir.
    # Actually, previous audits inspected "contents/header.xml" from pkg.
    # Where represents "templates"?
    # `lib/hwpx/templates.py` uses bytes?
    # I'll check `hwpx/templates.py` location?
    # Wait, `lib/owpml/document_builder.py` imports `from hwpx import templates`.
    # And uses `templates.blank_document_bytes()`.
    # I should inspect THAT bytes.
    # No file on disk "Skeleton.hwpx"?
    # Step 742 (Builder Line 106) `blank_bytes = templates.blank_document_bytes()`.
    pass

    from hwpx import templates
    import io
    
    data = templates.blank_document_bytes()
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        header_xml = zf.read('Contents/header.xml').decode('utf-8')
        print("Header XML Length:", len(header_xml))
        
        root = ET.fromstring(header_xml)
        
        # Namespaces
        ns = {
            'hh': 'http://www.hancom.co.kr/hwpml/2011/head'
        }
        
        # Find numberings
        numberings = root.find('.//hh:numberings', ns)
        if numberings is None:
            print("No <hh:numberings> found.")
        else:
            print(f"Numberings Count: {numberings.get('itemCnt')}")
            for numbering in numberings.findall('hh:numbering', ns):
                n_id = numbering.get('id')
                print(f"\nNumbering ID: {n_id}")
                
                # Check levels (paraHead)
                # Structure: numbering -> paraHead -> ...
                for head in numbering.findall('hh:paraHead', ns):
                    print(f"  Level {head.get('level')}: {ET.tostring(head, encoding='unicode')}")

if __name__ == "__main__":
    inspect_numbering()

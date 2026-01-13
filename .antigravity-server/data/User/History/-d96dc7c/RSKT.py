#!/usr/bin/env python
"""
Manual Verification: Footnotes & Endnotes (Phase 15)

Tests:
1. Create document with InsertFootnote action.
2. Create document with InsertEndnote action.
3. Verify hp:footNote and hp:endNote elements exist in section0.xml.
"""
import os
import sys
import zipfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.owpml.document_builder import HwpxDocumentBuilder
from lib.models import InsertText, InsertFootnote, InsertEndnote

def test_footnotes():
    actions = [
        InsertText(text="This is main text with a footnote marker."),
        InsertFootnote(text="This is the footnote content explaining something."),
        InsertText(text="More text after the footnote."),
        InsertEndnote(text="This is an endnote that appears at the end of the document."),
    ]
    
    output_file = "output_footnotes_test.hwpx"
    
    builder = HwpxDocumentBuilder()
    builder.build(actions, output_file)
    print(f"Created {output_file}")
    
    # Verify structure
    with zipfile.ZipFile(output_file, 'r') as z:
        section_xml = z.read('Contents/section0.xml').decode('utf-8')
    
    # Parse and check for footnote/endnote elements
    ns = {
        'hp': 'http://www.hancom.co.kr/hwpml/2011/paragraph',
        'hs': 'http://www.hancom.co.kr/hwpml/2011/section'
    }
    
    root = ET.fromstring(section_xml)
    
    # Check for footNote
    footnotes = root.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}footNote')
    if footnotes:
        print(f"✅ Found {len(footnotes)} footNote element(s)")
        for fn in footnotes:
            # Check for subList
            sublist = fn.find('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}subList')
            if sublist is not None:
                print("  ✅ footNote contains subList")
    else:
        print("❌ No footNote elements found")
    
    # Check for endNote
    endnotes = root.findall('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}endNote')
    if endnotes:
        print(f"✅ Found {len(endnotes)} endNote element(s)")
        for en in endnotes:
            sublist = en.find('.//{http://www.hancom.co.kr/hwpml/2011/paragraph}subList')
            if sublist is not None:
                print("  ✅ endNote contains subList")
    else:
        print("❌ No endNote elements found")

if __name__ == "__main__":
    if os.path.exists("Skeleton.hwpx") or os.path.exists("/home/palantir/hwpx/Skeleton.hwpx"):
        test_footnotes()
    else:
        print("Skipping - No Skeleton.hwpx")

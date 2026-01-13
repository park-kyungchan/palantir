import json
import sys
import os

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.digital_twin.schema import DigitalTwin

def validate_twin(json_path):
    print(f"Loading Twin from {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Validation Step: Import into Pydantic
        twin = DigitalTwin(**data)
        
        print("✅ Pydantic Validation Successful!")
        print(f"Document ID: {twin.document_id}")
        
        page = twin.pages[0]
        print(f"Page {page.page_num} Loaded with {len(page.blocks)} blocks.")
        
        print("\n--- Block Verification ---")
        for block in page.blocks:
            print(f"[{block.type.upper()}] ID: {block.id}")
            if block.type == "table":
                print(f"  Rows: {len(block.content.table_data)}")
                print(f"  Headers: {block.content.table_data[0]}")
            elif block.type == "text" or block.type == "header":
                content = block.content.text[:50] + "..." if len(block.content.text) > 50 else block.content.text
                print(f"  Text: {content}")
            
    except Exception as e:
        print(f"❌ Validation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    validate_twin("temp_vision/page_1.json")

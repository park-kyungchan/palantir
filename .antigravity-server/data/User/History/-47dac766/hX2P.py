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
        print(f"Total Pages: {len(twin.pages)}")
        
        for page in twin.pages:
           # In the placeholder batch script, we used 'image_path' which is NOT in the proper Block schema yet?
           # Ah, the batch script put "image_path" in the Page dict, but Schema Page expects 'blocks'.
           # Let's check if my BatchProcessor implementation ADHERED to the schema.
           # If I just dumped a dict into 'pages' that doesn't match 'Page' model, this will fail.
           pass

    except Exception as e:
        print(f"❌ Validation Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    validate_twin("temp_vision_batch/full_doc_twin.json")

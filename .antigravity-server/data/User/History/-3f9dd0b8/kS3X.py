import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.digital_twin.schema import DigitalTwin
from lib.knowledge.parser import ActionTableParser

def build_knowledge_base():
    twin_path = "temp_vision_batch/full_doc_twin_parsed.json"
    
    # 1. Load Twin
    with open(twin_path, 'r') as f:
        data = json.load(f)
    twin = DigitalTwin(**data)
    
    print(f"Loaded Twin: {twin.document_id}, Pages: {len(twin.pages)}")
    
    # 2. Parse into Action DB
    parser = ActionTableParser()
    db = parser.parse(twin)
    
    print(f"Action DB Populated with {len(db.actions)} actions.")
    
    # 3. Verify specific entries
    samples = ["InsertText", "CreateTable", "AddHanjaWord"]
    for s in samples:
        if s in db.actions:
            act = db.actions[s]
            print(f"✅ {s}: Desc='{act.description_ko}', ParamSet='{act.parameter_set_id}'")
        else:
            print(f"❌ {s} not found.")

    # 4. Save DB
    with open("lib/knowledge/action_db.json", "w", encoding='utf-8') as f:
        f.write(db.model_dump_json(indent=2))
    print("Saved to lib/knowledge/action_db.json")

if __name__ == "__main__":
    build_knowledge_base()

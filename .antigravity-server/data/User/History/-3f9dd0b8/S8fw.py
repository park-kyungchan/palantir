import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from lib.digital_twin.schema import DigitalTwin
from lib.knowledge.parser import ActionTableParser
from lib.ingestors.parameter_ingestor import LayoutParameterIngestor
from lib.ingestors.event_ingestor import TextEventIngestor

def build_knowledge_base():
    # --- Step 1: Action Table ---
    mask_twin_path = "temp_vision_batch/full_doc_twin_parsed.json"

    
    # 1. Load Twin
    with open(mask_twin_path, 'r') as f:
        data = json.load(f)
    twin = DigitalTwin(**data)
    
    print(f"Loaded Action Twin: {twin.document_id}, Pages: {len(twin.pages)}")
    
    # 2. Parse into Action DB
    parser = ActionTableParser()
    db = parser.parse(twin)
    
    print(f"Action DB Populated with {len(db.actions)} actions.")

    # --- Step 2: Parameter Set Table ---
    param_pdf_path = "ParameterSetTable_2504.pdf"
    if os.path.exists(param_pdf_path):
        print(f"Ingesting Parameter Sets from {param_pdf_path}...")
        p_ingestor = LayoutParameterIngestor(param_pdf_path)
        p_sets = p_ingestor.process()
        
        for p_set in p_sets:
            db.add_parameter_set(p_set)
            
        print(f"Added {len(p_sets)} Parameter Sets to DB.")
    else:
        print(f"⚠️ Warning: {param_pdf_path} not found. Skipping parameters.")

    # --- Step 3: Event Handler Table ---
    event_pdf_path = "한글오토메이션EventHandler추가_2504.pdf"
    if os.path.exists(event_pdf_path):
        print(f"Ingesting Events from {event_pdf_path}...")
        e_ingestor = TextEventIngestor(event_pdf_path)
        events = e_ingestor.process()
        
        for e in events:
            db.add_event(e)
            
        print(f"Added {len(events)} Events to DB.")
    else:
        print(f"⚠️ Warning: {event_pdf_path} not found. Skipping events.")
    
    # 4. Save DB
    samples = ["InsertText", "CreateTable", "AddHanjaWord"]
    for s in samples:
        if s in db.actions:
            act = db.actions[s]
            print(f"✅ {s}: Desc='{act.description_ko}', ParamSet='{act.parameter_set_id}'")
        else:
            print(f"❌ {s} not found.")

    # 4. Save DB
    output_path = "lib/knowledge/hwpx/action_db.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding='utf-8') as f:
        f.write(db.model_dump_json(indent=2))
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    build_knowledge_base()

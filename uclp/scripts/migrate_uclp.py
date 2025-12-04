import json
import os
import uuid
import sys
# Fix import path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from scripts.ontology import Concept, Language, Implementation
# Paths
BASE_DIR = "/home/palantir/uclp"
REF_FILE = os.path.join(BASE_DIR, "uclp-reference.json")
DATA_DIR = os.path.join(BASE_DIR, "ontology/data")

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Saved: {path}")

def migrate():
    print("🚀 Starting UCLP Migration...")
    ref_data = load_json(REF_FILE)

    # 1. Migrate Concepts
    print("📦 Migrating Concepts...")
    categories = ref_data.get("comparison_framework", {}).get("categories", {})
    for cat_key, cat_val in categories.items():
        for concept in cat_val.get("concepts", []):
            c_id = concept["id"]
            concept_obj = Concept(
                concept_id=c_id,
                name=concept["name"],
                category=cat_key,
                prerequisites=concept.get("prerequisites", []),
                related_concepts=concept.get("related", [])
            )
            save_json(os.path.join(DATA_DIR, "concepts", f"{c_id}.json"), concept_obj.model_dump())

    # 2. Migrate Languages (Idiomatic Patterns)
    print("📦 Migrating Languages...")
    patterns = ref_data.get("comparison_framework", {}).get("idiomatic_patterns", {})
    # Also get sources to enrich language data
    sources = ref_data.get("sources", {})
    
    for lang_id in ["go", "python", "swift", "typescript"]:
        lang_obj = Language(
            language_id=lang_id,
            name=lang_id.capitalize(),
            philosophy_summary="Derived from patterns", # Placeholder
            idiomatic_patterns=patterns.get(lang_id, []),
            sources=sources.get(lang_id, [])
        )
        save_json(os.path.join(DATA_DIR, "languages", f"{lang_id}.json"), lang_obj.model_dump())

    # 3. Migrate Implementations (Examples)
    print("📦 Migrating Implementations...")
    examples = ref_data.get("examples", {})
    for concept_id, lang_map in examples.items():
        for lang_id, impl_data in lang_map.items():
            impl_id = str(uuid.uuid4())
            impl_obj = Implementation(
                impl_id=impl_id,
                concept_id=concept_id,
                language_id=lang_id,
                syntax_template=impl_data.get("syntax", ""),
                design_rationale=impl_data.get("design_decision", ""),
                sources=impl_data.get("sources", [])
            )
            save_json(os.path.join(DATA_DIR, "implementations", f"{impl_id}.json"), impl_obj.model_dump())

    print("✅ Migration Complete!")

if __name__ == "__main__":
    migrate()

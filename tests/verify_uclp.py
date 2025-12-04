import os
import json
import sys
import glob
# Fix import path
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from scripts.ontology import Concept, Language, Implementation

BASE_DIR = "/home/palantir/uclp/ontology"
DATA_DIR = os.path.join(BASE_DIR, "data")

def validate():
    print("🧪 Starting UCLP Integrity Check (Pydantic Powered)...")
    
    # 1. Validate Concepts
    concepts = glob.glob(os.path.join(DATA_DIR, "concepts", "*.json"))
    print(f"🔍 Checking {len(concepts)} Concepts...")
    for c_file in concepts:
        with open(c_file, 'r') as f:
            data = json.load(f)
        try:
            Concept.model_validate(data)
        except Exception as e:
            print(f"❌ Invalid Concept: {c_file} - {e}")

    # 2. Validate Languages
    languages = glob.glob(os.path.join(DATA_DIR, "languages", "*.json"))
    print(f"🔍 Checking {len(languages)} Languages...")
    for l_file in languages:
        with open(l_file, 'r') as f:
            data = json.load(f)
        try:
            Language.model_validate(data)
        except Exception as e:
            print(f"❌ Invalid Language: {l_file} - {e}")

    # 3. Validate Implementations
    impls = glob.glob(os.path.join(DATA_DIR, "implementations", "*.json"))
    print(f"🔍 Checking {len(impls)} Implementations...")
    for i_file in impls:
        with open(i_file, 'r') as f:
            data = json.load(f)
        try:
            Implementation.model_validate(data)
        except Exception as e:
            print(f"❌ Invalid Implementation: {i_file} - {e}")

    print("✅ Verification Complete.")

if __name__ == "__main__":
    validate()

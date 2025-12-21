
import sys
from pathlib import Path

sys.path.append(str(Path("/home/palantir/orion-orchestrator-v2")))

from scripts.ontology.learning.engine import TutoringEngine

def run_verification():
    root = "/home/palantir/orion-orchestrator-v2/scripts/ontology"
    print(f"Initializing Engine on {root}...")
    
    engine = TutoringEngine(root)
    engine.scan_codebase()
    engine.calculate_scores()
    
    report = engine.get_report()
    
    print("\n--- Easiest Files (Foundation) ---")
    for item in report[:5]:
        print(f"[{item['tcs']}] {item['file']}")
        
    print("\n--- Hardest Files (Expert) ---")
    for item in report[-5:]:
        print(f"[{item['tcs']}] {item['file']}")
    
    # Specific Check against Spec Prediction
    # phase5.md: "ontology_types.py ~25", "proposal_repository.py ~55"
    # Note: proposal_repository might not exist yet if it was renamed or moved. 
    # 'storage/database.py' or 'actions.py' are good proxies.
    
    print("\n--- Spec Validation Targets ---")
    targets = ["ontology_types.py", "actions.py", "objects/proposal.py"]
    for t in targets:
        # Search for partial match
        found = next((x for x in report if t in x['file']), None)
        if found:
            print(f"Target '{t}': Score {found['tcs']}")
            print(f"  Breakdown: {found['breakdown']}")
        else:
            print(f"Target '{t}': Not Found")

if __name__ == "__main__":
    run_verification()

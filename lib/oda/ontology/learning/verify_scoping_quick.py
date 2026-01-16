
import sys
from pathlib import Path

sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

from lib.oda.ontology.learning.engine import TutoringEngine
from lib.oda.ontology.learning.scoping import ScopingEngine
from lib.oda.ontology.learning.types import LearnerState, KnowledgeComponentState

def verify():
    root = "/home/palantir/park-kyungchan/palantir/lib/oda/ontology"
    print("--- Initializing Engines ---")
    
    tutor = TutoringEngine(root)
    tutor.scan_codebase()
    tutor.calculate_scores()
    
    scoper = ScopingEngine(tutor)
    
    # Scene 1: Absolute Beginner
    print("\n--- Scene 1: The Beginner ---")
    user_state = LearnerState(user_id="newbie", theta=-1.0)
    recs = scoper.recommend_next_files(user_state, limit=3)
    
    for r in recs:
        print(f"Recommended: {r['file']} (TCS: {r['tcs']}, Fit: {r['zpd_score']})")
        
    # Scene 2: Validating Progression
    # If recommendation includes 'ontology_types.py', let's say they mastered it.
    print("\n--- Scene 2: The Novice (Mastered ontology_types) ---")
    user_state.update_mastery("ontology_types.py", 0.95)
    # Also master 'db.py' to unlock more
    user_state.update_mastery("db.py", 0.90)
    
    recs = scoper.recommend_next_files(user_state, limit=3)
    for r in recs:
        print(f"Recommended: {r['file']} (TCS: {r['tcs']}, Fit: {r['zpd_score']})")

if __name__ == "__main__":
    verify()

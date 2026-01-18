
import sys
import os
from pathlib import Path

# Add project root to sys.path so we can import scripts
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))

from lib.oda.ontology.learning.metrics import analyze_file

def verify(target_file):
    print(f"Analyzing: {target_file}")
    with open(target_file, 'r') as f:
        content = f.read()
    
    metric = analyze_file(target_file, content)
    
    print("\n--- RESULTS ---")
    print(metric.model_dump_json(indent=2))

if __name__ == "__main__":
    target = "/home/palantir/park-kyungchan/palantir/lib/oda/ontology/actions.py"
    if len(sys.argv) > 1:
        target = sys.argv[1]
    verify(target)

#!/usr/bin/env python3
"""
Orion V3 Learning Mode Trigger
Usage: python scripts/ontology/learning.py --target <path> --mode <concept|review>

This script prepares the Orion workspace for an "Agile Learning Session".
It scans the target codebase, generates a structural manifest, and creates a
session context file that the AI Agent (Gemini) can consume to perform
Reflective Architecture Analysis.
"""

import argparse
import os
import json
import datetime
from pathlib import Path
from typing import Dict, List, Any

# Analysis Constants
INTERESTING_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.md', '.json'}
IGNORE_DIRS = {'__pycache__', 'node_modules', '.git', '.venv', 'dist', 'build', '.agent'}

class CodebaseScanner:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        
    def scan(self) -> Dict[str, Any]:
        """Generates a hierarchical structural manifest of the codebase."""
        manifest = {
            "root": str(self.root),
            "scanned_at": datetime.datetime.now().isoformat(),
            "structure": {},
            "key_artifacts": []
        }
        
        for root, dirs, files in os.walk(self.root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            rel_path = Path(root).relative_to(self.root)
            if str(rel_path) == ".":
                rel_path = Path("")
                
            current_node = {
                "files": [],
                "subdirs": dirs
            }
            
            for f in files:
                if Path(f).suffix in INTERESTING_EXTENSIONS:
                    current_node["files"].append(f)
                    
                    # Heuristic for "Key Artifacts" (e.g., Models, APIs)
                    if f in ["models.py", "schema.py", "api.py", "types.ts", "interfaces.ts"]:
                         manifest["key_artifacts"].append(str(rel_path / f))
            
            if current_node["files"] or current_node["subdirs"]:
                 manifest["structure"][str(rel_path)] = current_node
                 
        return manifest

def generate_session_context(target_path: str, mode: str):
    scanner = CodebaseScanner(target_path)
    manifest = scanner.scan()
    
    session_id = datetime.datetime.now().strftime("learn_%Y%m%d_%H%M%S")
    output_dir = Path(".agent/learning")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / f"{session_id}.json"
    
    context = {
        "session_id": session_id,
        "mode": mode,
        "target_path": str(target_path),
        "manifest": manifest,
        "instruction": "Agent: Read this manifest. Map the 'key_artifacts' to Palantir FDE Knowledge Base concepts. Perform Reflective Analysis."
    }
    
    with open(output_file, "w") as f:
        json.dump(context, f, indent=2)
        
    print(f"\n✅ Learning Session Context Generated: {output_file}")
    print(f"==================================================")
    print(f"🔎 Target: {target_path}")
    print(f"🎓 Mode: {mode.upper()}")
    print(f"📂 Artifacts Found: {len(manifest['key_artifacts'])}")
    print(f"==================================================")
    print(f"\n🚀 TO START LEARNING, TYPE THIS TO THE AGENT:")
    print(f"\n'[SYSTEM MODE: Palantir FDE Learning]'")
    print(f"'Active Context: {output_file}'")
    print(f"'Please analyze my codebase using the FDE Knowledge Base.'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Orion Learning Mode Trigger")
    parser.add_argument("--target", required=True, help="Path to the codebase to analyze")
    parser.add_argument("--mode", choices=["concept", "review"], default="review", help="Learning mode")
    
    args = parser.parse_args()
    generate_session_context(args.target, args.mode)

#!/usr/bin/env python3
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Constants for Knowledge Base Mapping
KB_MAPPING = {
    "Tier 1 (Beginner)": {
        "patterns": ["*.js", "*.py", "*.ts"],
        "signals": ["variable", "function", "class", "import"],
        "kbs": ["00a_programming_fundamentals.md", "00b_functions_and_scope.md"]
    },
    "Tier 2 (Intermediate)": {
        "patterns": ["*.tsx", "*.jsx", "package.json", "tsconfig.json"],
        "signals": ["useState", "useEffect", "interface", "type ", "component"],
        "kbs": ["01_language_foundation.md", "02_react_ecosystem.md", "05_testing_pyramid.md"]
    },
    "Tier 3 (Advanced)": {
        "patterns": ["*ontology*", "*kernel*", "*workflow*", "Dockerfile"],
        "signals": ["optimization", "architecture", "deployment", "pipeline"],
        "kbs": ["09_orion_system_architecture.md", "24_system_design_fundamentals.md"]
    }
}

class ReflectiveAnalysisEngine:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.context_manifest = {
            "project_root": str(self.root_dir),
            "architecture_overview": {},
            "module_breakdown": [],
            "identified_concepts": []
        }

    def scan_codebase(self):
        """Scans the codebase and maps files to concepts."""
        logger.info(f"Scanning codebase at {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Skip hidden directories and virtual envs
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', 'node_modules', '__pycache__']]
            
            for file in files:
                file_path = Path(root) / file
                self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path):
        """Analyzes a single file to determine its tier and concepts."""
        try:
            # Simple heuristic analysis
            relative_path = file_path.relative_to(self.root_dir)
            file_str = str(file_path)
            
            matched_tier = None
            relevant_kbs = set()

            # Check filename patterns
            for tier, config in KB_MAPPING.items():
                for pattern in config["patterns"]:
                    if file_path.match(pattern):
                        matched_tier = tier
                        relevant_kbs.update(config["kbs"])
                        break
            
            if matched_tier:
                module_info = {
                    "path": str(relative_path),
                    "tier": matched_tier,
                    "recommended_kbs": list(relevant_kbs)
                }
                self.context_manifest["module_breakdown"].append(module_info)
                
                # Simple content sniffing for signals (if text file)
                if file_path.suffix in ['.py', '.ts', '.tsx', '.js', '.md']:
                    self._extract_signals(file_path, module_info)

        except Exception as e:
            logger.warning(f"Could not analyze {file_path}: {e}")

    def _extract_signals(self, file_path: Path, module_info: Dict):
        """Reads file content to find specific signals."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(2048) # Read first 2KB
                
                found_signals = []
                for tier, config in KB_MAPPING.items():
                    for signal in config["signals"]:
                        if signal in content:
                            found_signals.append(signal)
                
                if found_signals:
                    module_info["detected_concepts"] = list(set(found_signals))
        except Exception:
            pass

    def generate_report(self, output_path: str):
        """Writes the analysis result to a JSON file."""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.context_manifest, f, indent=2)
        
        logger.info(f"Analysis complete. Report generated at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Palantir FDE Reflective Analysis Engine")
    parser.add_argument("--target", required=True, help="Root directory of the codebase to analyze")
    parser.add_argument("--mode", choices=["concept", "review"], default="concept", help="Analysis mode")
    parser.add_argument("--output", default=".agent/learning/context_manifest.json", help="Output path for JSON report")
    
    args = parser.parse_args()
    
    engine = ReflectiveAnalysisEngine(args.target)
    engine.scan_codebase()
    engine.generate_report(args.output)

if __name__ == "__main__":
    main()
